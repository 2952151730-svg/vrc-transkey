import os
import sys
import time
import json
import ctypes
import threading
from pathlib import Path

# 保证 Windows 控制台 UTF-8 正确显示
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from config import config, PHRASES_PATH, DEFAULT_SYSTEM_PROMPT, PROMPT_PRESETS, SOCIAL_SYSTEM_PROMPT, AGGRESSIVE_SYSTEM_PROMPT
from pinyin_engine import PinyinEngine
from translator import Translator
from osc_client import VRCOSCClient
from ui_renderer import UIRenderer, WIDTH, HEIGHT


def get_clipboard_text() -> str:
    """读取 Windows 剪贴板文本 (严格适配 64 位系统指针与多程序并发防锁)"""
    try:
        from ctypes import wintypes
        u32 = ctypes.windll.user32
        k32 = ctypes.windll.kernel32

        u32.OpenClipboard.argtypes = [wintypes.HWND]
        u32.OpenClipboard.restype = wintypes.BOOL

        u32.CloseClipboard.argtypes = []
        u32.CloseClipboard.restype = wintypes.BOOL

        u32.GetClipboardData.argtypes = [wintypes.UINT]
        u32.GetClipboardData.restype = wintypes.HANDLE

        k32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        k32.GlobalLock.restype = wintypes.LPVOID

        k32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        k32.GlobalUnlock.restype = wintypes.BOOL

        CF_UNICODETEXT = 13

        opened = False
        for _ in range(5):
            if u32.OpenClipboard(None):
                opened = True
                break
            time.sleep(0.02)

        if not opened:
            return ""

        try:
            handle = u32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            ptr = k32.GlobalLock(handle)
            if not ptr:
                return ""
            try:
                text = ctypes.c_wchar_p(ptr).value
                return text or ""
            finally:
                k32.GlobalUnlock(handle)
        finally:
            u32.CloseClipboard()
    except Exception as e:
        print(f"[Clipboard] 读取剪贴板异常: {e}")
        return ""


class VRCTransKeyApp:
    def __init__(self, desktop_mode: bool = False):
        self.desktop_mode = desktop_mode
        self.pinyin = PinyinEngine()
        self.translator = Translator(config.get("translation", default={}))
        self.osc = VRCOSCClient(
            ip=config.get("vrchat", "osc_ip", default="127.0.0.1"),
            port=config.get("vrchat", "osc_port", default=9000)
        )
        self.renderer = UIRenderer()
        self.phrases_data = self.load_phrases()
        self.history = []

        # 键盘全局状态
        self.state = {
            "committed_text": "",
            "pinyin_buffer": "",
            "candidates": [],
            "candidate_spans": [],
            "candidate_page": 0,
            "has_prev_page": False,
            "has_next_page": False,
            "translated_text": "",
            "input_mode": config.get("input", "default_mode", default="zh"),
            "is_shift": False,
            "is_caps": False,
            "target_lang": config.get("translation", "target_lang", default="en"),
            "send_mode": config.get("translation", "send_mode", default="translated_only"),
            "engine": config.get("translation", "engine", default="free_direct"),
            "network_mode": config.get("translation", "network_mode", default="global"),
            "google_api_key": config.get("translation", "google_api_key", default=""),
            "google_model": config.get("translation", "google_model", default="gemini-1.5-flash"),
            "google_models_list": config.get("translation", "google_models_list", default=["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]),
            "deepseek_api_key": config.get("translation", "deepseek_api_key", default=""),
            "prompt_style": config.get("translation", "prompt_style", default="social"),
            "system_prompt": config.get("translation", "system_prompt", default=DEFAULT_SYSTEM_PROMPT),
            "proxy": config.get("translation", "proxy", default=""),
            "overlay_width_m": config.get("overlay", "width_m", default=0.42),
            "laser_guide": config.get("overlay", "laser_guide", default="auto"),
            "is_vd_active": False,
            "hotkey_controller": config.get("hotkey", "controller", default="right"),
            "active_modal": None,          # None, "phrases", "settings"
            "sub_keyboard": "letters",     # "letters", "numbers", "symbols"
            "is_delete_phrase_mode": False,
            "phrase_cat": list(self.phrases_data.keys())[0] if self.phrases_data else "",
            "phrases_data": self.phrases_data,
            "settings_tip": ""
        }

        self.dirty = True
        self.current_clickables = []

        if not self.desktop_mode:
            from vr_overlay import VROverlayManager
            self.overlay_mgr = VROverlayManager()
            self.state["is_vd_active"] = getattr(self.overlay_mgr, "is_vd_active", False)
        else:
            self.overlay_mgr = None

    def load_phrases(self):
        default_phrases = {
            "打招呼": ["你好呀！很高兴认识你~", "Hello there! Nice to meet you!", "大家好呀~", "晚上好！", "可以加个好友吗？"],
            "状态说明": ["在听的，稍等我在打字~", "抱歉我现在不便开麦，用文字交流", "去洗手间/倒水，马上回来 (AFK)", "刚才网络有点卡顿，抱歉"],
            "社交互动": ["你的模型好可爱呀！", "这个世界真好看，很漂亮", "哈哈哈太草了", "赞同，完全同意！", "没问题，交给我吧"],
            "告别": ["时间不早啦，我先下线休息了", "大家晚安，下次再一起玩！", "我先去其他房间找朋友啦，回聊~", "See you next time! Good night!"]
        }
        if not PHRASES_PATH.exists():
            try:
                with open(PHRASES_PATH, "w", encoding="utf-8") as f:
                    json.dump(default_phrases, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return default_phrases
        try:
            with open(PHRASES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_phrases

    def save_phrases(self):
        try:
            with open(PHRASES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.phrases_data, f, ensure_ascii=False, indent=2)
            self.state["phrases_data"] = self.phrases_data
            self.dirty = True
        except Exception as e:
            print(f"[App] 保存常用语失败: {e}")

    def get_dynamic_candidate_pages(self, all_cands, max_w: int = 838, max_per_page: int = 8):
        """根据候选词文本宽度智能切分页，确保每一页都能排满 7~8 个词，无空白且绝不截断"""
        if not all_cands:
            return []
        font = getattr(self.renderer, "font_cand", None)
        pages = []
        i = 0
        n = len(all_cands)
        base_gap = 8
        while i < n:
            start = i
            total_w = 0
            while i < n and (i - start) < max_per_page:
                cand, _ = all_cands[i]
                tag = f"{i - start + 1}. {cand}"
                if font:
                    tb = font.getbbox(tag)
                    btn_w = max(74, (tb[2] - tb[0]) + 24)
                else:
                    btn_w = 84
                needed = btn_w if (i == start) else (btn_w + base_gap)
                if total_w + needed > max_w:
                    if i == start:
                        i += 1
                    break
                total_w += needed
                i += 1
            pages.append((start, i))
        return pages

    def update_candidates(self):
        buf = self.state["pinyin_buffer"]
        if not buf:
            self.state["candidates"] = []
            self.state["candidate_spans"] = []
            self.state["has_prev_page"] = False
            self.state["has_next_page"] = False
            self.state["candidate_page"] = 0
            self.state["_cand_pages"] = []
            return

        all_cands = self.pinyin.search_with_span(buf, max_results=50)
        pages = self.get_dynamic_candidate_pages(all_cands)
        self.state["_cand_pages"] = pages

        page_idx = self.state.get("candidate_page", 0)
        if pages:
            page_idx = max(0, min(page_idx, len(pages) - 1))
        else:
            page_idx = 0
        self.state["candidate_page"] = page_idx

        if pages and page_idx < len(pages):
            s, e = pages[page_idx]
            cur_paged = all_cands[s:e]
            self.state["candidates"] = [w for w, _ in cur_paged]
            self.state["candidate_spans"] = [c for _, c in cur_paged]
            self.state["has_prev_page"] = (page_idx > 0)
            self.state["has_next_page"] = (page_idx < len(pages) - 1)
        else:
            self.state["candidates"] = []
            self.state["candidate_spans"] = []
            self.state["has_prev_page"] = False
            self.state["has_next_page"] = False

    def _commit_candidate(self, idx: int):
        """执行候选词上屏，支持长句分步选词 (仅消耗对应音节长度)"""
        cands = self.state["candidates"]
        spans = self.state.get("candidate_spans", [])
        buf = self.state["pinyin_buffer"]
        if 0 <= idx < len(cands):
            selected = cands[idx]
            consumed = spans[idx] if idx < len(spans) else len(buf)
            consumed = max(1, min(len(buf), consumed))
            matched_py = buf[:consumed]
            if matched_py:
                self.pinyin.record_choice(matched_py, selected)
            self.state["committed_text"] += selected
            self.state["pinyin_buffer"] = buf[consumed:]
            self.state["candidate_page"] = 0
            self.update_candidates()
            self.trigger_translation()

    def trigger_translation(self):
        """触发异步实时翻译"""
        text = self.state["committed_text"].strip()
        if not text:
            self.state["translated_text"] = ""
            self.dirty = True
            return

        target_lang = self.state["target_lang"]

        def on_translated(original, translated):
            if original == self.state["committed_text"].strip():
                self.state["translated_text"] = translated
                self.dirty = True

        self.translator.translate_async(text, target_lang, on_translated)

    def handle_action(self, action: str, data: any = None, controller_idx: int = None):
        """处理界面交互动作"""
        if self.overlay_mgr and controller_idx is not None:
            self.overlay_mgr.trigger_haptic(controller_idx, 1400)

        if config.get("vrchat", "send_typing_indicator", default=True) and action != "hide_overlay":
            self.osc.set_typing_status(True)

        if action == "hide_overlay":
            if self.overlay_mgr:
                self.overlay_mgr.hide()
            self.osc.set_typing_status(False)
            return

        elif action == "cycle_lang":
            langs = ["en", "ja", "ko", "ru", "fr", "de"]
            idx = (langs.index(self.state["target_lang"]) + 1) % len(langs) if self.state["target_lang"] in langs else 0
            self.state["target_lang"] = langs[idx]
            config.set(["translation", "target_lang"], langs[idx])
            self.trigger_translation()

        elif action == "set_target_lang":
            lang = str(data)
            self.state["target_lang"] = lang
            config.set(["translation", "target_lang"], lang)
            lang_names = {"en": "英语 (EN)", "ja": "日语 (JA)", "ko": "韩语 (KO)", "ru": "俄语 (RU)", "fr": "法语 (FR)", "de": "德语 (DE)"}
            self.state["settings_tip"] = f"√ 目标翻译语种已设为: {lang_names.get(lang, lang)}"
            self.trigger_translation()

        elif action == "set_default_input_mode":
            mode = str(data)
            self.state["input_mode"] = mode
            config.set(["input", "default_mode"], mode)
            mode_name = "默认中文拼音" if mode == "zh" else "默认英文直接输入"
            self.state["settings_tip"] = f"√ 初始输入语言已设为: 【{mode_name}】"

        elif action == "switch_keyboard":
            self.state["sub_keyboard"] = str(data)

        elif action == "insert_char":
            char_to_insert = str(data)
            if self.state["pinyin_buffer"]:
                if self.state["candidates"]:
                    self._commit_candidate(0)
                else:
                    self.state["committed_text"] += self.state["pinyin_buffer"]
                    self.state["pinyin_buffer"] = ""
                    self.update_candidates()
            self.state["committed_text"] += char_to_insert
            self.trigger_translation()

        elif action == "toggle_ime":
            if self.state["pinyin_buffer"]:
                self.state["committed_text"] += self.state["pinyin_buffer"]
                self.state["pinyin_buffer"] = ""
                self.update_candidates()
                self.trigger_translation()
            self.state["input_mode"] = "en" if self.state["input_mode"] == "zh" else "zh"

        elif action == "toggle_caps":
            self.state["is_caps"] = not self.state["is_caps"]

        elif action == "toggle_shift":
            self.state["is_shift"] = not self.state["is_shift"]

        elif action == "toggle_modal":
            cur = self.state["active_modal"]
            self.state["active_modal"] = None if cur == data else data
            if self.state["active_modal"] == "phrases":
                self.state["phrases_data"] = self.load_phrases()
                self.state["is_delete_phrase_mode"] = False
            elif self.state["active_modal"] == "settings":
                self.state["settings_tip"] = ""

        elif action == "select_phrase_cat":
            self.state["phrase_cat"] = data

        elif action == "fill_phrase":
            phrase_text = str(data)
            self.state["committed_text"] = phrase_text
            self.state["pinyin_buffer"] = ""
            self.state["active_modal"] = None
            self.update_candidates()
            self.trigger_translation()

        elif action == "send_phrase_direct":
            phrase_text = str(data)
            self.state["committed_text"] = phrase_text
            self.state["active_modal"] = None
            self._do_send_message(send_type="original")

        elif action == "send_phrase_translated":
            phrase_text = str(data)
            self.state["committed_text"] = phrase_text
            self.state["translated_text"] = ""
            self.state["active_modal"] = None
            self._do_send_message(send_type="translated")

        elif action == "toggle_delete_phrase_mode":
            self.state["is_delete_phrase_mode"] = not self.state.get("is_delete_phrase_mode", False)

        elif action == "add_new_phrase":
            text_to_add = self.state["committed_text"].strip()
            if not text_to_add:
                text_to_add = get_clipboard_text().strip()
            if text_to_add:
                cat = self.state["phrase_cat"]
                if cat not in self.phrases_data:
                    self.phrases_data[cat] = []
                if text_to_add not in self.phrases_data[cat]:
                    self.phrases_data[cat].insert(0, text_to_add)
                    self.save_phrases()

        elif action == "delete_phrase_item":
            cat, idx = data
            if cat in self.phrases_data and 0 <= idx < len(self.phrases_data[cat]):
                self.phrases_data[cat].pop(idx)
                self.save_phrases()

        # --- 设置页面操作 ---
        elif action == "toggle_network_mode":
            cur_net = self.state.get("network_mode", "global")
            nxt_net = "mainland" if cur_net == "global" else "global"
            self.state["network_mode"] = nxt_net
            config.set(["translation", "network_mode"], nxt_net)
            self.translator.update_config(config.get("translation"))
            tip = "√ 已切换为【🌍 海外直连模式】(Google免翻秒通)" if nxt_net == "global" else "√ 已切换为【🇨🇳 中国大陆模式】(国内加速/按需代理)"
            self.state["settings_tip"] = tip
            self.trigger_translation()

        elif action == "set_engine":
            eng = str(data)
            self.state["engine"] = eng
            eng_names = {
                "free_direct": "免翻极速直连通道",
                "google_gemini": "Google Gemini 官方大模型",
                "deepseek": "DeepSeek 大模型"
            }
            self.state["settings_tip"] = f"√ 已切换为 {eng_names.get(eng, eng)}"
            config.set(["translation", "engine"], eng)
            self.translator.update_config(config.get("translation"))
            self.trigger_translation()

        elif action == "paste_google_key":
            clip = get_clipboard_text().strip()
            if clip:
                self.state["google_api_key"] = clip
                self.state["settings_tip"] = "√ Google API Key 已粘贴保存！可点击【拉取可用模型】或【测试连接】"
                config.set(["translation", "google_api_key"], clip)
                self.translator.update_config(config.get("translation"))
                print(f"[Settings] Google API Key 已更新: {clip[:6]}...{clip[-4:] if len(clip) > 10 else ''}")
            else:
                self.state["settings_tip"] = "提示：剪贴板为空，请先复制 Google Gemini API Key"

        elif action == "clear_google_key":
            self.state["google_api_key"] = ""
            self.state["settings_tip"] = "已清空 Google API Key"
            config.set(["translation", "google_api_key"], "")
            self.translator.update_config(config.get("translation"))

        elif action == "cycle_google_model":
            models = self.state.get("google_models_list", ["gemini-1.5-flash", "gemini-2.0-flash"])
            cur_m = self.state.get("google_model", "gemini-1.5-flash")
            if cur_m in models:
                idx = (models.index(cur_m) + 1) % len(models)
            else:
                idx = 0
            nxt_m = models[idx]
            self.state["google_model"] = nxt_m
            config.set(["translation", "google_model"], nxt_m)
            self.translator.update_config(config.get("translation"))
            self.state["settings_tip"] = f"√ 当前 Google 模型已切换为: {nxt_m}"

        elif action == "fetch_google_models":
            self.state["settings_tip"] = "正在向 Google 云端接口请求可用模型列表..."
            self.dirty = True

            def _fetch_run():
                ok, models, msg = self.translator.fetch_gemini_models()
                if ok and models:
                    self.state["google_models_list"] = models
                    if self.state.get("google_model") not in models:
                        self.state["google_model"] = models[0]
                        config.set(["translation", "google_model"], models[0])
                    config.set(["translation", "google_models_list"], models)
                self.state["settings_tip"] = msg
                self.dirty = True

            threading.Thread(target=_fetch_run, daemon=True).start()

        elif action == "test_translation_api":
            self.state["settings_tip"] = "正在测试翻译通道连接与延迟..."
            self.dirty = True

            def _run_test():
                ok, msg = self.translator.test_connection(self.state["target_lang"])
                self.state["settings_tip"] = msg
                self.dirty = True

            threading.Thread(target=_run_test, daemon=True).start()

        elif action == "adjust_vr_width":
            delta = float(data)
            cur_w = float(self.state.get("overlay_width_m", 0.42))
            nxt = round(max(0.25, min(0.85, cur_w + delta)), 2)
            self._apply_vr_width(nxt)

        elif action == "set_vr_width_exact":
            nxt = round(max(0.25, min(0.85, float(data))), 2)
            self._apply_vr_width(nxt)

        elif action == "vr_size_slider":
            # data 为 (slider_x1, slider_x2, click_x) 或 (slider_x1, slider_x2)
            if isinstance(data, tuple) and len(data) == 3:
                sx1, sx2, cx = data
                ratio = max(0.0, min(1.0, (cx - sx1) / max(1.0, float(sx2 - sx1))))
                nxt = round(0.25 + ratio * (0.85 - 0.25), 2)
                self._apply_vr_width(nxt)

        elif action == "toggle_vr_hand":
            cur_h = self.state.get("hotkey_controller", "right")
            nxt_h = "left" if cur_h == "right" else "right"
            self.state["hotkey_controller"] = nxt_h
            config.set(["hotkey", "controller"], nxt_h)
            names = {"right": "右手摇杆双击", "left": "左手摇杆双击"}
            self.state["settings_tip"] = f"√ VR 呼出键已切换为：{names[nxt_h]}"

        elif action == "cycle_laser_mode":
            cur_mode = self.state.get("laser_guide", "auto")
            mode_cycle = {"auto": "on", "on": "off", "off": "auto"}
            nxt_mode = mode_cycle.get(cur_mode, "auto")
            self.state["laser_guide"] = nxt_mode
            config.set(["overlay", "laser_guide"], nxt_mode)
            if self.overlay_mgr:
                self.overlay_mgr.set_laser_mode(nxt_mode)
            mode_names = {
                "auto": "智能检测 (仅VD开启，SteamVR原生隐藏防双线)",
                "on": "强制开启 (始终显示 3D 发光引导线)",
                "off": "强制关闭 (完全隐藏第三方引导线，由SteamVR原生接管)"
            }
            self.state["settings_tip"] = f"√ 激光引导线已切换为：{mode_names[nxt_mode]}"

        elif action == "reset_user_dict":
            self.pinyin.user_history = {}
            self.pinyin.word_total_count = {}
            self.pinyin.save_user_dict()
            self.state["settings_tip"] = "√ 已重置个人输入法自适应词频记忆"

        elif action == "paste_api_key":
            clip = get_clipboard_text().strip()
            if clip:
                self.state["deepseek_api_key"] = clip
                self.state["settings_tip"] = "√ API Key 已成功粘贴并保存！可点击右上角【测试翻译连接】验证"
                config.set(["translation", "deepseek_api_key"], clip)
                self.translator.update_config(config.get("translation"))
                print(f"[Settings] DeepSeek API Key 已更新: {clip[:6]}...{clip[-4:] if len(clip) > 10 else ''}")
            else:
                self.state["settings_tip"] = "提示：剪贴板为空，请先在网页复制 API Key"

        elif action == "clear_api_key":
            self.state["deepseek_api_key"] = ""
            self.state["settings_tip"] = "已清空 API Key"
            config.set(["translation", "deepseek_api_key"], "")
            self.translator.update_config(config.get("translation"))

        elif action == "set_prompt_style":
            style = str(data)
            if style in PROMPT_PRESETS:
                new_prompt = PROMPT_PRESETS[style]
                self.state["prompt_style"] = style
                self.state["system_prompt"] = new_prompt
                style_name = "日常友好社交 (礼貌自然)" if style == "social" else "暴躁对线 / 俚语强化 (喷人无审查)"
                self.state["settings_tip"] = f"√ 已切换为【{style_name}】模式，实时生效！"
                config.set(["translation", "prompt_style"], style)
                config.set(["translation", "system_prompt"], new_prompt)
                self.translator.update_config(config.get("translation"))
                self.trigger_translation()

        elif action == "paste_custom_prompt":
            clip = get_clipboard_text().strip()
            if clip:
                self.state["prompt_style"] = "custom"
                self.state["system_prompt"] = clip
                self.state["settings_tip"] = "√ 自定义提示词已更新并保存！"
                config.set(["translation", "prompt_style"], "custom")
                config.set(["translation", "system_prompt"], clip)
                self.translator.update_config(config.get("translation"))
                self.trigger_translation()
            else:
                self.state["settings_tip"] = "提示：剪贴板为空，请先复制提示词内容"

        elif action == "reset_default_prompt":
            self.state["prompt_style"] = "social"
            self.state["system_prompt"] = SOCIAL_SYSTEM_PROMPT
            self.state["settings_tip"] = "√ 已恢复默认【日常友好社交】提示词"
            config.set(["translation", "prompt_style"], "social")
            config.set(["translation", "system_prompt"], SOCIAL_SYSTEM_PROMPT)
            self.translator.update_config(config.get("translation"))
            self.trigger_translation()

        # --- 输入栏快捷按键 ---
        elif action == "recall_history":
            if self.history:
                self.state["committed_text"] = self.history[-1]
                self.state["pinyin_buffer"] = ""
                self.update_candidates()
                self.trigger_translation()

        elif action == "clear_text":
            self.state["committed_text"] = ""
            self.state["pinyin_buffer"] = ""
            self.state["translated_text"] = ""
            self.update_candidates()
            self.osc.set_typing_status(False)

        elif action == "paste_clipboard":
            clip = get_clipboard_text().strip()
            if clip:
                self.state["committed_text"] += clip
                self.trigger_translation()

        elif action == "cand_next":
            if self.state["has_next_page"]:
                self.state["candidate_page"] += 1
                self.update_candidates()

        elif action == "cand_prev":
            if self.state["candidate_page"] > 0:
                self.state["candidate_page"] -= 1
                self.update_candidates()

        elif action == "select_candidate":
            self._commit_candidate(int(data))

        elif action == "key_space":
            if self.state["pinyin_buffer"]:
                if self.state["candidates"]:
                    self._commit_candidate(0)
                else:
                    self.state["committed_text"] += self.state["pinyin_buffer"]
                    self.state["pinyin_buffer"] = ""
                    self.update_candidates()
                    self.trigger_translation()
            else:
                self.state["committed_text"] += " "
                self.trigger_translation()

        elif action == "key_enter":
            if self.state["pinyin_buffer"]:
                # 将当前拼音缓冲区的英文字母直接原样上屏 (解决打英文如 bug, vrc, ok, fps 等需求)
                self.state["committed_text"] += self.state["pinyin_buffer"]
                self.state["pinyin_buffer"] = ""
                self.state["candidate_page"] = 0
                self.update_candidates()
                self.trigger_translation()
            else:
                self.state["committed_text"] += " "
                self.trigger_translation()

        elif action == "key_press":
            key_char = str(data)
            if key_char == "Backspace":
                if self.state["pinyin_buffer"]:
                    self.state["pinyin_buffer"] = self.state["pinyin_buffer"][:-1]
                    self.state["candidate_page"] = 0
                    self.update_candidates()
                elif self.state["committed_text"]:
                    self.state["committed_text"] = self.state["committed_text"][:-1]
                    self.trigger_translation()
            elif self.state["pinyin_buffer"] and key_char in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                cand_idx = int(key_char) - 1
                if cand_idx < len(self.state["candidates"]):
                    self._commit_candidate(cand_idx)
            else:
                if self.state["input_mode"] == "zh" and key_char.isalpha() and len(key_char) == 1 and key_char.islower():
                    self.state["pinyin_buffer"] += key_char
                    self.state["candidate_page"] = 0
                    self.update_candidates()
                else:
                    self.state["committed_text"] += key_char
                    self.trigger_translation()
                    if self.state["is_shift"]:
                        self.state["is_shift"] = False

        elif action == "send_translated":
            self._do_send_message(send_type="translated")

        elif action == "send_original" or action == "send_message":
            self._do_send_message(send_type="original")

        self.dirty = True

    def _do_send_message(self, send_type: str = "translated"):
        """执行发送到 VRChat Chatbox (独立发送外语译文或发送中文)"""
        # 若拼音缓冲区还有未上屏的词，自动将首选词上屏后再发送
        if self.state["pinyin_buffer"]:
            if self.state["candidates"]:
                self._commit_candidate(0)
            else:
                self.state["committed_text"] += self.state["pinyin_buffer"]
                self.state["pinyin_buffer"] = ""

        orig = self.state["committed_text"].strip()
        trans = self.state["translated_text"].strip()
        if not orig:
            return

        if not self.history or self.history[-1] != orig:
            self.history.append(orig)
            if len(self.history) > 15:
                self.history.pop(0)

        if send_type == "translated":
            if not trans:
                trans = self.translator.translate_sync(orig, self.state["target_lang"])
            send_text = trans if trans else orig
        else:
            send_text = orig

        self.osc.send_chatbox(send_text, direct_send=True)
        self.osc.set_typing_status(False)

        self.state["committed_text"] = ""
        self.state["pinyin_buffer"] = ""
        self.state["translated_text"] = ""
        self.update_candidates()
        self.dirty = True

    def _apply_vr_width(self, nxt: float):
        """统一应用并限制 VR 键盘物理宽度在 [0.25m, 0.85m] 安全范围内"""
        nxt = round(max(0.25, min(0.85, float(nxt))), 2)
        self.state["overlay_width_m"] = nxt
        config.set(["overlay", "width_m"], nxt)
        if self.overlay_mgr:
            self.overlay_mgr.set_width_meters(nxt)
        pct = int(round((nxt / 0.42) * 100))
        self.state["settings_tip"] = f"√ VR 键盘大小已调节为 {nxt:.2f}米 ({pct}%，已开启最小0.25m防消失保护)"
        self.dirty = True

    def process_mouse_click(self, x: float, y: float, controller_idx: int = None, is_drag_hold: bool = False):
        px = int(x)
        py = int(y)

        for rect, action, data in self.current_clickables:
            rx1, ry1, rx2, ry2 = rect
            if rx1 <= px <= rx2 and ry1 <= py <= ry2:
                if action == "vr_size_slider" and isinstance(data, tuple) and len(data) == 2:
                    self.handle_action("vr_size_slider", (data[0], data[1], px), controller_idx=None if is_drag_hold else controller_idx)
                elif not is_drag_hold:
                    self.handle_action(action, data, controller_idx)
                break

    def run_vr_loop(self):
        if not self.overlay_mgr or not self.overlay_mgr.vr_system:
            print("\n" + "!" * 54)
            print("  [提示] 未检测到运行中的 SteamVR！")
            print("  请先启动 SteamVR 并戴好头显，然后再启动 VR 模式。")
            print("  如果只想在电脑桌面上调试界面、打字与测试翻译，请运行：")
            print("  >> 【启动_桌面预览模式.bat】 <<")
            print("!" * 54 + "\n")
            try:
                input("请按回车键退出...")
            except Exception:
                pass
            return

        print("\n" + "=" * 58)
        print("  VRC-TransKey 启动成功 (VR 激光交互模式)！")
        print("  - 呼出/收起: 左或右手柄【摇杆双击按下】")
        print("  - 激光瞄准: 手柄指向键盘自动发射 3D 激光线与落点准星")
        print("  - 扳机点击: 激光对准按键，按【食指扳机键 Trigger】点击")
        print("  - 任意拖动: 激光指在键盘任意位置，按住【侧握键 Grip】即可拖动")
        print("=" * 58 + "\n")

        # 启动时先预渲染并上传初始贴图
        img, clickables = self.renderer.render(self.state)
        self.current_clickables = clickables
        self.overlay_mgr.upload_texture(img.tobytes(), WIDTH, HEIGHT)
        self.dirty = False

        self.overlay_mgr.show()
        last_is_visible = True

        while True:
            ui_events = self.overlay_mgr.step_vr_interaction()
            for ev_type, px, py, ctrl_idx in ui_events:
                if ev_type == "click":
                    self.process_mouse_click(px, py, ctrl_idx, is_drag_hold=False)
                elif ev_type == "drag_hold":
                    self.process_mouse_click(px, py, ctrl_idx, is_drag_hold=True)

            cur_vis = self.overlay_mgr.is_visible
            if cur_vis and not last_is_visible:
                self.dirty = True
            last_is_visible = cur_vis

            if self.dirty and self.overlay_mgr.is_visible:
                img, clickables = self.renderer.render(self.state)
                self.current_clickables = clickables
                self.overlay_mgr.upload_texture(img.tobytes(), WIDTH, HEIGHT)
                self.dirty = False

            time.sleep(0.011)

    def run_desktop_preview(self):
        import tkinter as tk
        from PIL import ImageTk

        root = tk.Tk()
        root.title("VRC-TransKey 灵动翻译键盘 [桌面预览 / 物理键盘直打模式]")
        root.geometry(f"{WIDTH}x{HEIGHT}")
        root.resizable(False, False)
        root.configure(bg="#0e1118")

        canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#0e1118", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        photo_ref = [None]

        def refresh_canvas():
            img, clickables = self.renderer.render(self.state)
            self.current_clickables = clickables
            photo = ImageTk.PhotoImage(img)
            photo_ref[0] = photo
            canvas.delete("all")
            canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            self.dirty = False

        def on_click(event):
            self.process_mouse_click(event.x, event.y, is_drag_hold=False)
            refresh_canvas()

        def on_drag_motion(event):
            self.process_mouse_click(event.x, event.y, is_drag_hold=True)
            if self.dirty:
                refresh_canvas()

        def on_motion(event):
            px, py = int(event.x), int(event.y)
            hovered = False
            for rect, action, _ in self.current_clickables:
                if action == "drag_handle":
                    continue
                rx1, ry1, rx2, ry2 = rect
                if rx1 <= px <= rx2 and ry1 <= py <= ry2:
                    hovered = True
                    break
            canvas.config(cursor="hand2" if hovered else "")

        def on_paste_shortcut(event):
            if self.state.get("active_modal") == "settings":
                self.handle_action("paste_api_key", None)
            else:
                self.handle_action("paste_clipboard", None)
            refresh_canvas()
            return "break"

        def on_key_press(event):
            # 支持电脑实体键盘直接打字、选词、回车发送译文
            if event.state & 0x4:  # Control 键按下时交给快捷键处理
                return
            if self.state.get("active_modal") is not None:
                if event.keysym == "Escape":
                    self.handle_action("toggle_modal", None)
                    refresh_canvas()
                return

            ks = event.keysym
            ch = event.char
            if ks == "BackSpace":
                self.handle_action("key_press", "Backspace")
            elif ks == "space":
                self.handle_action("key_space")
            elif ks == "Return":
                if self.state["pinyin_buffer"]:
                    self.handle_action("key_enter")
                elif event.state & 0x1:  # Shift + Enter 发送中文原文
                    self.handle_action("send_original")
                else:                  # Enter 直接发送译文
                    self.handle_action("send_translated")
            elif ks == "Escape":
                if self.state["pinyin_buffer"]:
                    self.state["pinyin_buffer"] = ""
                    self.update_candidates()
                    self.dirty = True
                else:
                    self.handle_action("clear_text")
            elif ks in ("minus", "Prior", "Up"):
                self.handle_action("cand_prev")
            elif ks in ("equal", "Next", "Down"):
                self.handle_action("cand_next")
            elif ch and len(ch) == 1 and ch.isprintable():
                if ch == "," and self.state["input_mode"] == "zh":
                    self.handle_action("insert_char", "，")
                elif ch == "." and self.state["input_mode"] == "zh":
                    self.handle_action("insert_char", "。")
                elif ch == "?" and self.state["input_mode"] == "zh":
                    self.handle_action("insert_char", "？")
                elif ch == "!" and self.state["input_mode"] == "zh":
                    self.handle_action("insert_char", "！")
                else:
                    self.handle_action("key_press", ch)
            refresh_canvas()

        canvas.bind("<Button-1>", on_click)
        canvas.bind("<B1-Motion>", on_drag_motion)
        canvas.bind("<Motion>", on_motion)
        root.bind("<Control-v>", on_paste_shortcut)
        root.bind("<Control-V>", on_paste_shortcut)
        root.bind("<Key>", on_key_press)
        refresh_canvas()

        def periodic_check():
            if self.dirty:
                refresh_canvas()
            root.after(30, periodic_check)

        root.after(30, periodic_check)
        print("[Desktop] 桌面测试窗口已打开！支持鼠标点击虚拟按键，也支持直接使用电脑物理键盘打字 (Enter发译文 / Shift+Enter发中文)！")
        root.mainloop()


if __name__ == "__main__":
    is_desktop = "--desktop" in sys.argv or "-d" in sys.argv
    app = VRCTransKeyApp(desktop_mode=is_desktop)
    if is_desktop:
        app.run_desktop_preview()
    else:
        app.run_vr_loop()
