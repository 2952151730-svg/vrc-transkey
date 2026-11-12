import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Any

WIDTH = 1000
HEIGHT = 560

# 现代极简暗黑 Slate & Glass UI 配色体系 (精确匹配 transkeyvr.top 官网视觉)
COLOR_BG = (9, 10, 15, 252)             # 深邃黑夜蓝黑 (#090a0f)
COLOR_BG_BORDER = (36, 46, 68, 255)     # 外框微光边线
COLOR_SURFACE = (16, 21, 35, 255)       # 卡片容器表面 (#101523)
COLOR_SURFACE_INNER = (11, 14, 24, 255) # 内嵌深色槽 (#0b0e18)
COLOR_DIVIDER = (26, 34, 52, 255)       # 柔和分割线
COLOR_BORDER = (38, 48, 72, 255)        # 常规描边
COLOR_BORDER_ACTIVE = (56, 189, 248, 255) # 激活态天青蓝高亮 (#38bdf8)

# 键帽层次配色
COLOR_KEY_SHADOW = (7, 9, 14, 255)      # 键帽微投影
COLOR_KEY = (22, 28, 44, 255)           # 主字母键帽 (#161c2c)
COLOR_KEY_BORDER = (38, 50, 75, 255)    # 键帽微光上沿
COLOR_KEY_FUNC = (16, 21, 33, 255)      # 功能键帽 (#101521)
COLOR_KEY_FUNC_BORDER = (32, 42, 64, 255)

# 语义强调色
COLOR_PRIMARY = (38, 140, 230, 255)     # 天青蓝 (#38bdf8 渐进科技蓝)
COLOR_PRIMARY_BORDER = (56, 189, 248, 255)
COLOR_PRIMARY_SOFT = (20, 44, 76, 255)  # 柔和天青蓝底

COLOR_SUCCESS = (16, 185, 129, 255)      # 翠薄荷绿 (#10b981)
COLOR_SUCCESS_BORDER = (52, 211, 153, 255)

COLOR_DANGER = (225, 45, 80, 255)       # 珊瑚红 (#f43f5e)
COLOR_DANGER_SOFT = (48, 20, 28, 255)   # 柔和关闭底色

# 优雅暗红键帽配色 (删除键)
COLOR_DELETE_BG = (52, 22, 30, 255)
COLOR_DELETE_BORDER = (105, 40, 52, 255)
COLOR_DELETE_TEXT = (255, 185, 195, 255)

# 文本层级色 (高对比清晰无锯齿)
COLOR_TEXT_MAIN = (248, 250, 252, 255)  # 主文字：纯白 (#f8fafc)
COLOR_TEXT_SUB = (155, 172, 198, 255)   # 次级文字 (#9bb0c6)
COLOR_TEXT_MUTED = (105, 120, 145, 255) # 占位/弱提示文字 (#697891)
COLOR_TEXT_ACCENT = (56, 189, 248, 255) # 天青蓝高亮字 (#38bdf8)
COLOR_TEXT_TRANS = (52, 211, 153, 255)  # 译文薄荷绿字 (#34d399)

LANG_SHORT_NAME_MAP = {
    "zh": "中",
    "en": "英",
    "ja": "日",
    "ko": "韩",
    "ru": "俄",
    "fr": "法",
    "de": "德",
    "es": "西"
}

LANG_FULL_NAME_MAP = {
    "zh": "中文",
    "en": "英语",
    "ja": "日语",
    "ko": "韩语",
    "ru": "俄语",
    "fr": "法语",
    "de": "德语",
    "es": "西语"
}

QUICK_IDLE_CHIPS = ["哈哈", "好的", "稍等", "谢谢", "听不见", "不便开麦", "?", "!"]
QUICK_IDLE_CHIPS_EN = ["Haha", "OK", "Wait", "Thanks", "Can't hear", "Mute", "?", "!"]

KAOMOJI_CATEGORIES = {
    "卖萌": [
        "(*/ω＼*)", "(≧▽≦)/", "(o^▽^o)", "(*^▽^*)",
        "(〃'▽'〃)", "(=^･ω･^=)", "(/ω＼)", "(^・ω・^ )",
        "(・ω< )★", "(*≧ω≦)", "(*ﾉ▽ﾉ)", "(^з^)-☆"
    ],
    "开心": [
        "(＾▽＾)", "＼(＾O＾)／", "(⌒▽⌒)", "o(≧v≦)o",
        "(*ﾟ▽ﾟ*)", "ヾ(≧▽≦*)o", "(b^_^)b", "╰(*°▽°*)╯",
        "(^o^)/", "(★^O^★)", "(☆▽☆)", "(⌒▽⌒)☆"
    ],
    "难过": [
        "(；´д｀)ゞ", "(T_T)", "(ノへ￣、)", "(TдT)",
        "(╥﹏╥)", "(T-T)", "(；_；)", "(´；ω；`)",
        "o(TヘTo)", "(；′⌒`)", "(>_<)", "/(ㄒoㄒ)/~~"
    ],
    "生气/对线": [
        "(╯°□°）╯", "(￣ヘ￣#)", "(｀Д´)", "(；￣Д￣)",
        "凸(｀⌒´メ)凸", "(｀⌒´メ)", "(¬_¬)", "(╬▔皿▔)",
        "(▼ヘ▼#)", "(艹皿艹)", "(ノ｀Д´)ノ", "(ノ-_-)ノ~┻━┻"
    ],
    "问候/告别": [
        "(・ω・)ノ", "(o_ _)o", "(*￣▽￣)d", "ヾ(￣▽￣)Bye~",
        "(・ω・)ﾉ", "(・_・)ノ", "(=ﾟωﾟ)ﾉ", "(^o^)/~",
        "ヾ(・ω・*)", "(￣▽￣)ﾉ", "(^O^)/", "Bye (￣▽￣)ﾉ"
    ],
    "摸鱼/日常": [
        "_(:з」∠)_", "(￣o￣) . z Z", "(～￣▽￣)～", "(・_・;)",
        "╮(╯▽╰)╭", "(￣▽￣)~*", "(°ー°〃)", "┑(￣Д ￣)┍",
        "(。-ω-)zzz", "躺平 _(:3」∠)_", "(⊙_⊙)?", "( ´_ゝ｀)"
    ]
}

KAOMOJI_CATEGORY_NAMES_EN = {
    "卖萌": "Cute 🌸",
    "开心": "Happy 😊",
    "难过": "Sad 😭",
    "生气/对线": "Angry 💢",
    "问候/告别": "Hello 👋",
    "摸鱼/日常": "Relax 💤"
}

UI_STRINGS = {
    "zh": {
        "send_trans": "发送译文",
        "phrases": "常用语",
        "settings": "设置",
        "back": "返回",
        "save_return": "保存返回",
        "test_conn": "测试连接",
        "settings_title": "系统与翻译引擎设置",
        "ui_lang_btn": "● 界面: 简体中文",
        "net_global": "● 海外直连 (免代理)",
        "net_mainland": "● 中国用户 (走代理)",
        "eng_free": "免费通道",
        "eng_google": "Google 官方翻译",
        "eng_gemini": "Google Gemini AI",
        "eng_deepseek": "DeepSeek 大模型",
        "lang_pair_title": "互译模式:",
        "zh2en": "● 中文拼音 → 英语 (中→英)",
        "en2zh": "● 英文直接 → 中文 (英→中)",
        "swap_lang": "一键互换中英",
        "reset_dict": "重置输入记忆",
        "init_zh": "初始: ● 中文拼音",
        "init_en": "初始: ● 英文直出",
        "zoom_in": "+ 放大",
        "zoom_out": "- 缩小",
        "zoom_std": "标准",
        "guide_auto": "引导: 智能(SteamVR隐藏)",
        "guide_on": "引导: 强制开启",
        "guide_off": "引导: 强制关闭",
        "call_key": "呼出: 右手摇杆双击",
        "caps": "大写",
        "bksp": "删除",
        "enter": "回车",
        "enter_en": "回车(英)",
        "space": "空  格",
        "space_cand": "空格 (选首选词)",
        "send_orig": "发原文",
        "history": "上句",
        "paste": "粘贴",
        "clear": "清空",
        "letters": "返回字母",
        "letters_long": "返回字母键盘",
        "kaomoji": "(^_^) 颜文字",
        "symbols": "#+= 符",
        "numbers": "123",
        "paste_key": "粘贴 Key",
        "clear_key": "清除 Key",
        "cycle_model": "切换纯语言模型",
        "fetch_model": "拉取官方模型",
        "cycle_ds_model": "切换模型",
        "style_title": "口吻风格:",
        "style_social": "友好交流 (礼貌日常)",
        "style_aggro": "暴躁粗口 (对线游戏)",
        "style_custom": "自定义提示词",
        "toggle_style": "切换口吻风格",
        "paste_custom": "粘贴自定义提示词",
        "reset_default": "恢复默认",
        "placeholder_zh": "点击按键或敲击键盘输入中文拼音...",
        "placeholder_en": "当前为直接输入模式 (英文直接打字)...",
        "preview_empty": "实时译文预览 (自动双向翻译)",
        "quick": "快捷词",
        "phrases_title": "常用语快捷面板 (点击词条填入，或点右侧直发)",
        "save_current": "+ 存入当前输入",
        "manage_phrases": "管理删除",
        "done_manage": "完成管理",
        "send_trans_sm": "发译文",
        "send_orig_sm": "发原文",
        "back_kb": "返回键盘",
    },
    "en": {
        "send_trans": "Send Trans",
        "phrases": "Phrases",
        "settings": "Settings",
        "back": "Back",
        "save_return": "Save & Return",
        "test_conn": "Test Conn",
        "settings_title": "Settings & Translation Engines",
        "ui_lang_btn": "● UI: English",
        "net_global": "● Global Direct",
        "net_mainland": "● China (Proxy)",
        "eng_free": "Free Direct",
        "eng_google": "Google Translate",
        "eng_gemini": "Google Gemini AI",
        "eng_deepseek": "DeepSeek AI",
        "lang_pair_title": "Mode:",
        "zh2en": "● Chinese → English (ZH→EN)",
        "en2zh": "● English → Chinese (EN→ZH)",
        "swap_lang": "Swap Languages",
        "reset_dict": "Reset Dict",
        "init_zh": "Init: ● Chinese IME",
        "init_en": "Init: ● Direct English",
        "zoom_in": "+ Enlarge",
        "zoom_out": "- Shrink",
        "zoom_std": "Reset",
        "guide_auto": "Laser: Smart Auto",
        "guide_on": "Laser: Forced On",
        "guide_off": "Laser: Forced Off",
        "call_key": "Call: R-Stick Double",
        "caps": "Caps",
        "bksp": "Del",
        "enter": "Enter",
        "enter_en": "Enter (EN)",
        "space": "Space",
        "space_cand": "Space (Select 1st)",
        "send_orig": "Send Orig",
        "history": "History",
        "paste": "Paste",
        "clear": "Clear",
        "quick": "Quick Words",
        "letters": "Letters",
        "letters_long": "Back to Letters",
        "kaomoji": "(^_^) Kaomoji",
        "symbols": "#+= Sym",
        "numbers": "123",
        "paste_key": "Paste Key",
        "clear_key": "Clear Key",
        "cycle_model": "Cycle Model",
        "fetch_model": "Fetch Models",
        "cycle_ds_model": "Switch Model",
        "style_title": "Tone Style:",
        "style_social": "Polite & Casual",
        "style_aggro": "Gamer Rage / Slang",
        "style_custom": "Custom Prompt",
        "toggle_style": "Toggle Tone",
        "paste_custom": "Paste Custom Prompt",
        "reset_default": "Reset Default",
        "placeholder_zh": "Type Pinyin or tap keys to input Chinese...",
        "placeholder_en": "Direct input mode (Type English)...",
        "preview_empty": "Real-time Translation Preview",
        "phrases_title": "Phrases Panel (Tap to insert, or send directly)",
        "save_current": "+ Save Current",
        "manage_phrases": "Manage",
        "done_manage": "Done",
        "send_trans_sm": "Trans",
        "send_orig_sm": "Orig",
        "back_kb": "Back to Keys",
    }
}


class UIRenderer:
    def __init__(self):
        font_candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "msyh.ttc",
            "simhei.ttf"
        ]
        chosen_font = None
        for fp in font_candidates:
            if os.path.exists(fp):
                chosen_font = fp
                break

        try:
            if chosen_font:
                self.font_title = ImageFont.truetype(chosen_font, 17)
                self.font_main = ImageFont.truetype(chosen_font, 19)
                self.font_key = ImageFont.truetype(chosen_font, 23)
                self.font_key_md = ImageFont.truetype(chosen_font, 17)
                self.font_key_sm = ImageFont.truetype(chosen_font, 15)
                self.font_tiny = ImageFont.truetype(chosen_font, 12)
                self.font_preview = ImageFont.truetype(chosen_font, 22)
                self.font_trans = ImageFont.truetype(chosen_font, 18)
                self.font_cand = ImageFont.truetype(chosen_font, 18)
                self.font_code = ImageFont.truetype(chosen_font, 14)
            else:
                raise FileNotFoundError("No chinese font found")
        except Exception:
            default_f = ImageFont.load_default()
            self.font_title = self.font_main = self.font_key = self.font_key_md = self.font_key_sm = self.font_tiny = self.font_preview = self.font_trans = self.font_cand = self.font_code = default_f

        self.cached_clickables = []

    def _t(self, state: dict, key: str, default: str = "") -> str:
        lang = state.get("ui_lang", "zh") if isinstance(state, dict) else "zh"
        return UI_STRINGS.get(lang, {}).get(key, default or key)

    def _add_button(self, rect: Tuple[int, int, int, int], action: str, data: Any = None):
        self.cached_clickables.append((rect, action, data))

    def _draw_centered_text(self, draw: ImageDraw.Draw, rect: Tuple[int, int, int, int], text: str, font, fill):
        """精准居中绘制文字"""
        cx = (rect[0] + rect[2]) // 2
        cy = (rect[1] + rect[3]) // 2
        try:
            draw.text((cx, cy), text, font=font, fill=fill, anchor="mm")
        except Exception:
            bbox = font.getbbox(text) if hasattr(font, "getbbox") else (0, 0, len(text) * 10, 16)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((cx - tw // 2, cy - th // 2), text, font=font, fill=fill)

    def _draw_left_text(self, draw: ImageDraw.Draw, x: int, cy: int, text: str, font, fill):
        try:
            draw.text((x, cy), text, font=font, fill=fill, anchor="lm")
        except Exception:
            bbox = font.getbbox(text) if hasattr(font, "getbbox") else (0, 0, len(text) * 10, 16)
            th = bbox[3] - bbox[1]
            draw.text((x, cy - th // 2), text, font=font, fill=fill)

    def _draw_keycap(
        self, draw: ImageDraw.Draw, rect: Tuple[int, int, int, int],
        label: str, font, fill=COLOR_KEY, border=COLOR_KEY_BORDER,
        text_color=COLOR_TEXT_MAIN, radius=10, shadow=True,
        sub_label: str = None, underline: bool = False
    ):
        x1, y1, x2, y2 = rect

        if shadow:
            draw.rounded_rectangle([(x1, y1 + 3), (x2, y2 + 3)], radius=radius, fill=COLOR_KEY_SHADOW)

        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=radius, fill=fill, outline=border, width=1)

        self._draw_centered_text(draw, (x1, y1, x2, y2), label, font, text_color)

        if sub_label:
            self._draw_centered_text(draw, (x2 - 16, y1 + 8, x2 - 4, y1 + 20), sub_label, self.font_tiny, COLOR_TEXT_MUTED)

        if underline:
            cx = (x1 + x2) // 2
            draw.line([(cx - 10, y2 - 11), (cx + 10, y2 - 11)], fill=COLOR_BORDER_ACTIVE, width=2)

    def _truncate_left_to_fit(self, text: str, font, max_width: int) -> str:
        try:
            bbox = font.getbbox(text)
            if (bbox[2] - bbox[0]) <= max_width:
                return text
            while len(text) > 1:
                text = text[1:]
                cand = "..." + text
                b = font.getbbox(cand)
                if (b[2] - b[0]) <= max_width:
                    return cand
        except Exception:
            pass
        return text

    def render(self, state: dict) -> Tuple[Image.Image, List[Tuple[Tuple[int, int, int, int], str, Any]]]:
        """渲染完整键盘画面并返回可点击热区列表"""
        img = Image.new("RGBA", (WIDTH, HEIGHT), COLOR_BG)
        draw = ImageDraw.Draw(img)
        self.cached_clickables = []

        # 面板外框与顶部精致指示条 (极简 Slate 风格)
        draw.rounded_rectangle([(1, 1), (WIDTH - 2, HEIGHT - 2)], radius=18, outline=COLOR_BG_BORDER, width=2)
        draw.rounded_rectangle([(WIDTH // 2 - 42, 5), (WIDTH // 2 + 42, 9)], radius=2, fill=(40, 52, 75, 200))

        active_modal = state.get("active_modal", None)
        if active_modal == "phrases":
            self._render_top_bar(draw, state)
            self._render_phrases_modal(draw, state)
        elif active_modal == "settings":
            self._render_top_bar(draw, state)
            self._render_settings_modal(draw, state)
        else:
            self._render_top_bar(draw, state)
            self._render_unified_input_card(draw, state)
            self._render_mobile_keyboard(draw, state)

        return img, self.cached_clickables

    def _render_top_bar(self, draw: ImageDraw.Draw, state: dict):
        """第一行 (y: 14..64)：双向语言胶囊 + 实时译文预览 + 发送译文 + 常用语 / 设置 / 关闭"""
        y1, y2 = 14, 64
        cy = (y1 + y2) // 2

        # 1. 语言切换胶囊 [ 源 → 目标 ] (支持任意两两互译，点击循环切换常用配对)
        source_lang = state.get("source_lang", "zh")
        target_lang = state.get("target_lang", "en")
        s_name = LANG_SHORT_NAME_MAP.get(source_lang, source_lang.upper())
        t_name = LANG_SHORT_NAME_MAP.get(target_lang, target_lang.upper())
        lang_text = f"{s_name} → {t_name}"

        lang_rect = (16, y1, 126, y2)
        self._draw_keycap(
            draw, lang_rect, lang_text, font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE,
            text_color=COLOR_TEXT_ACCENT, radius=11, shadow=False
        )
        self._add_button(lang_rect, "cycle_lang_pair")

        # 2. 中间：实时译文显示舱
        trans_rect = (134, y1, 666, y2)
        trans_text = state.get("translated_text", "").strip()
        draw.rounded_rectangle(trans_rect, radius=11, fill=COLOR_SURFACE, outline=COLOR_BORDER)

        # 状态指示圆点
        dot_color = COLOR_SUCCESS_BORDER if trans_text else (60, 72, 96, 255)
        draw.ellipse((148, cy - 4, 156, cy + 4), fill=dot_color)

        if trans_text:
            fitted_trans = self._truncate_left_to_fit(trans_text, self.font_trans, 490)
            self._draw_left_text(draw, 166, cy, fitted_trans, self.font_trans, COLOR_TEXT_TRANS)
        else:
            engine = state.get("engine", "google_official")
            if engine == "google_official":
                eng_tag = "Google 官方翻译"
            elif engine == "google_gemini":
                eng_tag = "Google Gemini AI"
            elif engine == "deepseek":
                eng_tag = "DeepSeek AI"
            else:
                eng_tag = "免费极速通道" if state.get("ui_lang", "zh") == "zh" else "Free Direct"
            preview_hint = self._t(state, "preview_empty", "实时译文预览 (自动双向翻译)")
            self._draw_left_text(draw, 166, cy, f"{preview_hint} ({eng_tag})", self.font_key_sm, COLOR_TEXT_MUTED)

        # 3. [ 发送译文 ] 主操作按钮 (天青蓝官网质感)
        send_trans_rect = (674, y1, 790, y2)
        self._draw_keycap(
            draw, send_trans_rect, self._t(state, "send_trans", "发送译文"), font=self.font_key_sm,
            fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER,
            text_color=(255, 255, 255, 255), radius=11
        )
        self._add_button(send_trans_rect, "send_translated")

        # 4. 右侧功能胶囊：常用语 / 设置 / 关闭
        active_modal = state.get("active_modal")

        phrase_rect = (798, y1, 870, y2)
        is_ph = (active_modal == "phrases")
        self._draw_keycap(
            draw, phrase_rect, self._t(state, "phrases", "常用语"), font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_ph else COLOR_SURFACE,
            border=COLOR_PRIMARY_BORDER if is_ph else COLOR_BORDER,
            text_color=(255, 255, 255, 255) if is_ph else COLOR_TEXT_SUB,
            radius=11, shadow=False
        )
        self._add_button(phrase_rect, "toggle_modal", "phrases")

        settings_rect = (878, y1, 938, y2)
        is_st = (active_modal == "settings")
        self._draw_keycap(
            draw, settings_rect, self._t(state, "settings", "设置"), font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_st else COLOR_SURFACE,
            border=COLOR_PRIMARY_BORDER if is_st else COLOR_BORDER,
            text_color=(255, 255, 255, 255) if is_st else COLOR_TEXT_SUB,
            radius=11, shadow=False
        )
        self._add_button(settings_rect, "toggle_modal", "settings")

        close_rect = (946, y1, 984, y2)
        self._draw_keycap(
            draw, close_rect, "×", font=self.font_key,
            fill=COLOR_DANGER_SOFT, border=(100, 42, 54, 255),
            text_color=(255, 120, 130, 255), radius=11, shadow=False
        )
        self._add_button(close_rect, "hide_overlay")

    def _render_unified_input_card(self, draw: ImageDraw.Draw, state: dict):
        """第二行一体化输入卡片 (y: 72..188)"""
        card_rect = (16, 72, WIDTH - 16, 188)
        committed_text = state.get("committed_text", "")
        pinyin_buffer = state.get("pinyin_buffer", "")
        has_content = bool(committed_text or pinyin_buffer)

        draw.rounded_rectangle(
            card_rect, radius=14, fill=COLOR_SURFACE,
            outline=COLOR_BORDER_ACTIVE if has_content else COLOR_BORDER, width=1
        )
        draw.line([(28, 130), (WIDTH - 28, 130)], fill=COLOR_DIVIDER, width=1)

        # --- 上半层：原文输入行 ---
        icy = 101
        bar_col = COLOR_PRIMARY if has_content else (52, 64, 86, 255)
        draw.rounded_rectangle((28, 88, 32, 114), radius=2, fill=bar_col)

        cur_x = 44
        if has_content:
            if committed_text:
                fitted_orig = self._truncate_left_to_fit(committed_text, self.font_preview, 540)
                self._draw_left_text(draw, cur_x, icy, fitted_orig, self.font_preview, COLOR_TEXT_MAIN)
                bbox = self.font_preview.getbbox(fitted_orig)
                cur_x += (bbox[2] - bbox[0]) + 8

            if pinyin_buffer:
                py_bbox = self.font_key_md.getbbox(pinyin_buffer)
                pw = (py_bbox[2] - py_bbox[0]) + 20
                pill_rect = (cur_x, icy - 15, cur_x + pw, icy + 15)
                draw.rounded_rectangle(pill_rect, radius=7, fill=COLOR_PRIMARY_SOFT, outline=COLOR_BORDER_ACTIVE)
                self._draw_centered_text(draw, pill_rect, pinyin_buffer, self.font_key_md, COLOR_TEXT_ACCENT)
                self._add_button(pill_rect, "key_enter")
                cur_x += pw + 6

            draw.line([(cur_x, icy - 13), (cur_x, icy + 13)], fill=COLOR_BORDER_ACTIVE, width=2)
        else:
            is_zh = state.get("input_mode", "zh") == "zh"
            source_lang = state.get("source_lang", "zh")
            if is_zh and source_lang == "zh":
                placeholder = self._t(state, "placeholder_zh", "点击按键或敲击键盘输入中文拼音...")
            else:
                placeholder = self._t(state, "placeholder_en", f"当前为直接输入模式 (输入 {LANG_FULL_NAME_MAP.get(source_lang, '原文')})...")
            self._draw_left_text(draw, cur_x, icy, placeholder, self.font_key_md, COLOR_TEXT_MUTED)
            draw.line([(cur_x, icy - 12), (cur_x, icy + 12)], fill=(65, 80, 105, 255), width=2)

        # 右侧快捷按钮: [粘贴] [上句] [清空]
        paste_rect = (760, 82, 824, 120)
        self._draw_keycap(
            draw, paste_rect, self._t(state, "paste", "粘贴"), font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_SUB, radius=8, shadow=False
        )
        self._add_button(paste_rect, "paste_clipboard")

        hist_rect = (832, 82, 900, 120)
        self._draw_keycap(
            draw, hist_rect, self._t(state, "history", "上句"), font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False
        )
        self._add_button(hist_rect, "recall_history")

        clear_rect = (908, 82, 972, 120)
        self._draw_keycap(
            draw, clear_rect, self._t(state, "clear", "清空"), font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_MUTED, radius=8, shadow=False
        )
        self._add_button(clear_rect, "clear_text")

        # --- 下半层：候选词或快捷词条条 ---
        ccy = 159
        candidates = state.get("candidates", [])
        has_prev = state.get("has_prev_page", False)
        has_next = state.get("has_next_page", False)

        if pinyin_buffer and candidates:
            cand_items = []
            for i, cand in enumerate(candidates):
                label = f"{i+1}.{cand}"
                bbox = self.font_cand.getbbox(label)
                base_w = (bbox[2] - bbox[0]) + 30
                cand_items.append((cand, label, base_w))

            total_base_w = sum(w for _, _, w in cand_items)
            cand_start_x = 76
            avail_w = (WIDTH - 76) - cand_start_x
            n_items = len(cand_items)
            gap = 8
            extra_per_item = max(0, (avail_w - total_base_w - gap * (n_items - 1)) // n_items) if n_items > 0 else 0

            cur_cx = cand_start_x
            for i, (cand, label, base_w) in enumerate(cand_items):
                item_w = base_w + extra_per_item
                cand_rect = (cur_cx, 139, cur_cx + item_w, 179)
                is_first = (i == 0)
                self._draw_keycap(
                    draw, cand_rect, label, font=self.font_cand,
                    fill=COLOR_PRIMARY_SOFT if is_first else COLOR_KEY,
                    border=COLOR_BORDER_ACTIVE if is_first else COLOR_KEY_BORDER,
                    text_color=COLOR_TEXT_MAIN, radius=9, shadow=False
                )
                self._add_button(cand_rect, "select_candidate", i)
                cur_cx += item_w + gap

            # 翻页按钮
            prev_rect = (20, 139, 66, 179)
            self._draw_keycap(
                draw, prev_rect, "←", font=self.font_key,
                fill=COLOR_KEY if has_prev else COLOR_SURFACE_INNER,
                border=COLOR_KEY_BORDER if has_prev else COLOR_DIVIDER,
                text_color=COLOR_TEXT_MAIN if has_prev else COLOR_TEXT_MUTED,
                radius=9, shadow=False
            )
            if has_prev:
                self._add_button(prev_rect, "cand_prev")

            next_rect = (WIDTH - 70, 139, WIDTH - 24, 179)
            self._draw_keycap(
                draw, next_rect, "→", font=self.font_key,
                fill=COLOR_KEY if has_next else COLOR_SURFACE_INNER,
                border=COLOR_KEY_BORDER if has_next else COLOR_DIVIDER,
                text_color=COLOR_TEXT_MAIN if has_next else COLOR_TEXT_MUTED,
                radius=9, shadow=False
            )
            if has_next:
                self._add_button(next_rect, "cand_next")
        else:
            ui_lang = state.get("ui_lang", "zh")
            self._draw_left_text(draw, 30, ccy, self._t(state, "quick", "快捷词"), self.font_key_sm, COLOR_TEXT_MUTED)
            offset_x = 126 if ui_lang == "en" else 92
            idle_chips = QUICK_IDLE_CHIPS_EN if ui_lang == "en" else QUICK_IDLE_CHIPS
            for chip in idle_chips:
                cb = self.font_key_sm.getbbox(chip)
                cw = max(54, (cb[2] - cb[0]) + 28)
                if offset_x + cw > WIDTH - 28:
                    break
                chip_rect = (offset_x, 141, offset_x + cw, 177)
                self._draw_keycap(
                    draw, chip_rect, chip, font=self.font_key_sm,
                    fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER,
                    text_color=COLOR_TEXT_SUB, radius=9, shadow=False
                )
                self._add_button(chip_rect, "insert_char", chip)
                offset_x += cw + 10

    def _render_mobile_keyboard(self, draw: ImageDraw.Draw, state: dict):
        sub_kb = state.get("sub_keyboard", "letters")
        if sub_kb == "numbers":
            self._render_numbers_panel(draw, state)
        elif sub_kb == "symbols":
            self._render_symbols_panel(draw, state)
        elif sub_kb == "kaomoji":
            self._render_kaomoji_panel(draw, state)
        else:
            self._render_letters_panel(draw, state)

    def _render_letters_panel(self, draw: ImageDraw.Draw, state: dict):
        """主键盘：清爽极简 26 键布局 (y: 198..542)"""
        is_shift = state.get("is_shift", False)
        is_caps = state.get("is_caps", False)
        is_zh = state.get("input_mode", "zh") == "zh"
        has_pinyin = bool(state.get("pinyin_buffer", ""))

        row1 = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]
        row1_nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        row2 = ["a", "s", "d", "f", "g", "h", "j", "k", "l"]
        row3 = ["z", "x", "c", "v", "b", "n", "m"]

        key_h = 78
        gap = 10
        start_y = 198
        w_key = 88

        # --- Row 1: Q - P ---
        y = start_y
        start_x1 = 16
        for i, key in enumerate(row1):
            x = start_x1 + i * (w_key + gap)
            rect = (x, y, x + w_key, y + key_h)
            display_char = key.upper() if (is_caps ^ is_shift) else key
            self._draw_keycap(
                draw, rect, display_char, font=self.font_key,
                sub_label=row1_nums[i]
            )
            self._add_button(rect, "key_press", display_char)

        # --- Row 2: A - L ---
        y += key_h + gap
        start_x2 = 65
        for i, key in enumerate(row2):
            x = start_x2 + i * (w_key + gap)
            rect = (x, y, x + w_key, y + key_h)
            display_char = key.upper() if (is_caps ^ is_shift) else key
            self._draw_keycap(
                draw, rect, display_char, font=self.font_key,
                underline=(key in ("f", "j"))
            )
            self._add_button(rect, "key_press", display_char)

        # --- Row 3: [大写] + Z - M + [删除] + [回车] ---
        y += key_h + gap
        caps_w = 98
        caps_rect = (16, y, 16 + caps_w, y + key_h)
        caps_active = is_caps or is_shift
        self._draw_keycap(
            draw, caps_rect, self._t(state, "caps", "大写"), font=self.font_key_md,
            fill=COLOR_PRIMARY if caps_active else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if caps_active else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if caps_active else COLOR_TEXT_SUB
        )
        self._add_button(caps_rect, "toggle_caps")

        start_x3 = 16 + caps_w + gap
        for i, key in enumerate(row3):
            x = start_x3 + i * (w_key + gap)
            rect = (x, y, x + w_key, y + key_h)
            display_char = key.upper() if (is_caps ^ is_shift) else key
            self._draw_keycap(draw, rect, display_char, font=self.font_key)
            self._add_button(rect, "key_press", display_char)

        bksp_x = start_x3 + len(row3) * (w_key + gap)
        bksp_w = 82
        bksp_rect = (bksp_x, y, bksp_x + bksp_w, y + key_h)
        self._draw_keycap(
            draw, bksp_rect, self._t(state, "bksp", "删除"), font=self.font_key_md,
            fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT
        )
        self._add_button(bksp_rect, "key_press", "Backspace")

        enter_x = bksp_x + bksp_w + gap
        enter_rect = (enter_x, y, WIDTH - 16, y + key_h)
        enter_label = self._t(state, "enter_en", "回车(英)") if has_pinyin else self._t(state, "enter", "回车")
        self._draw_keycap(
            draw, enter_rect, enter_label, font=self.font_key_sm if has_pinyin else self.font_key_md,
            fill=COLOR_PRIMARY if has_pinyin else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if has_pinyin else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if has_pinyin else COLOR_TEXT_MAIN
        )
        self._add_button(enter_rect, "key_enter")

        # --- Row 4: [123] [符] [(^_^)] [，] [空格] [。] [中/EN] [发送原文] ---
        y += key_h + gap

        # 1. [123]
        r_123 = (16, y, 96, y + key_h)
        self._draw_keycap(
            draw, r_123, self._t(state, "numbers", "123"), font=self.font_key_md,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB
        )
        self._add_button(r_123, "switch_keyboard", "numbers")

        # 2. [#+= 符]
        r_sym = (104, y, 184, y + key_h)
        self._draw_keycap(
            draw, r_sym, self._t(state, "symbols", "#+= 符"), font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB
        )
        self._add_button(r_sym, "switch_keyboard", "symbols")

        # 3. [(^_^)] 颜文字专区
        r_kao = (192, y, 276, y + key_h)
        self._draw_keycap(
            draw, r_kao, "(^_^)", font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT
        )
        self._add_button(r_kao, "switch_keyboard", "kaomoji")

        # 4. [，]
        r_comma = (284, y, 340, y + key_h)
        self._draw_keycap(draw, r_comma, "，", font=self.font_key)
        self._add_button(r_comma, "insert_char", "，")

        # 5. [空格]
        r_space = (348, y, 618, y + key_h)
        space_label = self._t(state, "space_cand", "空格 (选首选词)") if has_pinyin else self._t(state, "space", "空  格")
        self._draw_keycap(
            draw, r_space, space_label, font=self.font_key_md,
            fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE if has_pinyin else COLOR_KEY_BORDER,
            text_color=COLOR_TEXT_ACCENT if has_pinyin else COLOR_TEXT_MUTED
        )
        self._add_button(r_space, "key_space")

        # 6. [。]
        r_dot = (626, y, 682, y + key_h)
        self._draw_keycap(draw, r_dot, "。", font=self.font_key)
        self._add_button(r_dot, "insert_char", "。")

        # 7. [中 → 英 / 英 → 中] 语言切换键
        r_ime = (690, y, 826, y + key_h)
        cur_src = state.get("source_lang", "zh")
        ime_label = "中 → 英" if cur_src == "zh" else "EN → ZH"
        self._draw_keycap(
            draw, r_ime, ime_label, font=self.font_key_md,
            fill=COLOR_PRIMARY_SOFT if cur_src == "zh" else COLOR_KEY_FUNC,
            border=COLOR_BORDER_ACTIVE if cur_src == "zh" else COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_ACCENT if cur_src == "zh" else COLOR_TEXT_SUB
        )
        self._add_button(r_ime, "swap_lang")

        # 8. [发送原文]
        r_send_orig = (834, y, WIDTH - 16, y + key_h)
        self._draw_keycap(
            draw, r_send_orig, self._t(state, "send_orig", "发原文"), font=self.font_key_md,
            fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER,
            text_color=(255, 255, 255, 255)
        )
        self._add_button(r_send_orig, "send_original")

    def _render_numbers_panel(self, draw: ImageDraw.Draw, state: dict):
        """数字面板"""
        self._render_grid_panel(draw, state, [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["-", "/", ":", ";", "(", ")", "$", "&", "@", "\""],
            [".", ",", "?", "!", "'", "%", "+", "=", "*", "_"],
            ["返回字母", "空格", "删除", "回车"]
        ])

    def _render_symbols_panel(self, draw: ImageDraw.Draw, state: dict):
        """特殊符号面板"""
        self._render_grid_panel(draw, state, [
            ["[", "]", "{", "}", "#", "%", "^", "*", "+", "="],
            ["_", "\\", "|", "~", "<", ">", "$", "￥", "€", "·"],
            ["“", "”", "‘", "’", "《", "》", "【", "】", "…", "—"],
            ["返回字母", "空格", "删除", "回车"]
        ])

    def _render_grid_panel(self, draw: ImageDraw.Draw, state: dict, rows: list):
        key_h = 78
        gap = 10
        start_y = 198
        w_key = 88

        for r_idx, row in enumerate(rows[:3]):
            y = start_y + r_idx * (key_h + gap)
            start_x = 16
            for c_idx, ch in enumerate(row):
                x = start_x + c_idx * (w_key + gap)
                rect = (x, y, x + w_key, y + key_h)
                self._draw_keycap(draw, rect, ch, font=self.font_key)
                self._add_button(rect, "insert_char", ch)

        y = start_y + 3 * (key_h + gap)
        # [返回字母]
        r_back = (16, y, 190, y + key_h)
        self._draw_keycap(draw, r_back, self._t(state, "letters_long", "返回字母键盘"), font=self.font_key_sm, fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_ACCENT)
        self._add_button(r_back, "switch_keyboard", "letters")

        # [(^_^)] 颜文字入口
        r_kao = (198, y, 290, y + key_h)
        self._draw_keycap(draw, r_kao, "(^_^)", font=self.font_key_sm, fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT)
        self._add_button(r_kao, "switch_keyboard", "kaomoji")

        # [空格]
        r_space = (298, y, 650, y + key_h)
        self._draw_keycap(draw, r_space, self._t(state, "space", "空  格"), font=self.font_key_md, fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_MUTED)
        self._add_button(r_space, "key_space")

        # [删除]
        r_del = (658, y, 810, y + key_h)
        self._draw_keycap(draw, r_del, self._t(state, "bksp", "删除"), font=self.font_key_md, fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT)
        self._add_button(r_del, "key_press", "Backspace")

        # [回车]
        r_enter = (818, y, WIDTH - 16, y + key_h)
        self._draw_keycap(draw, r_enter, self._t(state, "enter", "回车"), font=self.font_key_md, fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255))
        self._add_button(r_enter, "key_enter")

    def _render_kaomoji_panel(self, draw: ImageDraw.Draw, state: dict):
        """颜文字独立列表面板：分类标签 + 12 宫格颜文字 + 底部控制条"""
        cats = list(KAOMOJI_CATEGORIES.keys())
        cur_cat = state.get("kaomoji_cat", cats[0] if cats else "卖萌")
        if cur_cat not in KAOMOJI_CATEGORIES:
            cur_cat = cats[0] if cats else "卖萌"

        ui_lang = state.get("ui_lang", "zh")

        # 左侧 6 个分类标签 (x: 16..176, y: 198..524)
        cat_y = 198
        cat_h = 48
        cat_gap = 6
        for cat in cats[:6]:
            cat_rect = (16, cat_y, 176, cat_y + cat_h)
            is_active = (cat == cur_cat)
            cat_disp = KAOMOJI_CATEGORY_NAMES_EN.get(cat, cat) if ui_lang == "en" else cat
            self._draw_keycap(
                draw, cat_rect, cat_disp, font=self.font_key_sm,
                fill=COLOR_PRIMARY if is_active else COLOR_SURFACE_INNER,
                border=COLOR_PRIMARY_BORDER if is_active else COLOR_BORDER,
                text_color=(255, 255, 255, 255) if is_active else COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(cat_rect, "select_kaomoji_cat", cat)
            cat_y += cat_h + cat_gap

        # 右侧颜文字网格 (x: 186..984, y: 198..440) -> 3 行 x 4 列
        kaos = KAOMOJI_CATEGORIES.get(cur_cat, [])
        grid_x_start = 186
        grid_w = (WIDTH - 16) - grid_x_start
        col_w = (grid_w - 3 * 8) // 4
        grid_row_h = 74
        grid_row_gap = 8

        for idx, kao in enumerate(kaos[:12]):
            r = idx // 4
            c = idx % 4
            kx = grid_x_start + c * (col_w + 8)
            ky = 198 + r * (grid_row_h + grid_row_gap)
            kao_rect = (kx, ky, kx + col_w, ky + grid_row_h)
            self._draw_keycap(
                draw, kao_rect, kao, font=self.font_key_sm,
                fill=COLOR_KEY, border=COLOR_KEY_BORDER,
                text_color=COLOR_TEXT_MAIN, radius=9, shadow=False
            )
            self._add_button(kao_rect, "insert_char", kao)

        # 底部控制条 (y: 450..524)
        by = 450
        bh = 74

        # 返回字母
        b_back = (186, by, 320, by + bh)
        self._draw_keycap(
            draw, b_back, self._t(state, "letters_long", "返回字母"), font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_ACCENT,
            radius=9, shadow=False
        )
        self._add_button(b_back, "switch_keyboard", "letters")

        # 123
        b_123 = (328, by, 408, by + bh)
        self._draw_keycap(
            draw, b_123, "123", font=self.font_key_md,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(b_123, "switch_keyboard", "numbers")

        # #+=
        b_sym = (416, by, 496, by + bh)
        self._draw_keycap(
            draw, b_sym, "#+=", font=self.font_key_md,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(b_sym, "switch_keyboard", "symbols")

        # 空格
        b_space = (504, by, 720, by + bh)
        self._draw_keycap(
            draw, b_space, self._t(state, "space", "空  格"), font=self.font_key_md,
            fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_MUTED,
            radius=9, shadow=False
        )
        self._add_button(b_space, "key_space")

        # 删除
        b_del = (728, by, 846, by + bh)
        self._draw_keycap(
            draw, b_del, self._t(state, "bksp", "删除"), font=self.font_key_md,
            fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT,
            radius=9, shadow=False
        )
        self._add_button(b_del, "key_press", "Backspace")

        # 回车
        b_enter = (854, by, WIDTH - 16, by + bh)
        self._draw_keycap(
            draw, b_enter, self._t(state, "enter", "回车"), font=self.font_key_md,
            fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255),
            radius=9, shadow=False
        )
        self._add_button(b_enter, "key_enter")

    def _render_phrases_modal(self, draw: ImageDraw.Draw, state: dict):
        """常用语面板"""
        panel_rect = (16, 72, WIDTH - 16, HEIGHT - 14)
        draw.rounded_rectangle(panel_rect, radius=14, fill=COLOR_SURFACE, outline=COLOR_BORDER)

        is_delete_mode = state.get("phrase_delete_mode", False)
        title = "常用语管理模式 [点击右侧红色按钮删除]" if is_delete_mode else self._t(state, "phrases_title", "常用语快捷面板 (点击词条填入，或点右侧直发)")
        self._draw_left_text(draw, 36, 98, title, self.font_key_md, COLOR_DANGER if is_delete_mode else COLOR_TEXT_ACCENT)

        add_rect = (520, 80, 680, 116)
        self._draw_keycap(
            draw, add_rect, self._t(state, "save_current", "+ 存入当前输入"), font=self.font_key_sm,
            fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER, text_color=(255, 255, 255, 255),
            radius=8, shadow=False
        )
        self._add_button(add_rect, "add_new_phrase")

        del_mode_rect = (690, 80, 810, 116)
        del_label = self._t(state, "done_manage", "完成管理") if is_delete_mode else self._t(state, "manage_phrases", "管理删除")
        self._draw_keycap(
            draw, del_mode_rect, del_label, font=self.font_key_sm,
            fill=COLOR_DANGER if is_delete_mode else COLOR_KEY_FUNC,
            border=COLOR_DANGER if is_delete_mode else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255), radius=8, shadow=False
        )
        self._add_button(del_mode_rect, "toggle_delete_phrase_mode")

        back_rect = (820, 80, 964, 116)
        self._draw_keycap(
            draw, back_rect, self._t(state, "back_kb", "返回键盘"), font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(back_rect, "toggle_modal", None)

        draw.line([(32, 126), (WIDTH - 32, 126)], fill=COLOR_DIVIDER, width=1)

        phrases_data = state.get("phrases_data", {})
        cats = list(phrases_data.keys())
        cur_cat = state.get("phrase_cat", cats[0] if cats else "")

        cat_y = 138
        for cat in cats[:7]:
            cat_rect = (32, cat_y, 182, cat_y + 46)
            is_active = (cat == cur_cat)
            self._draw_keycap(
                draw, cat_rect, cat, font=self.font_key_md,
                fill=COLOR_PRIMARY if is_active else COLOR_SURFACE_INNER,
                border=COLOR_PRIMARY_BORDER if is_active else COLOR_BORDER,
                text_color=(255, 255, 255, 255) if is_active else COLOR_TEXT_SUB,
                radius=9, shadow=False
            )
            self._add_button(cat_rect, "select_phrase_cat", cat)
            cat_y += 54

        items = phrases_data.get(cur_cat, [])
        item_y = 138
        for i, text in enumerate(items[:7]):
            cy = item_y + 23
            if is_delete_mode:
                item_rect = (198, item_y, WIDTH - 124, item_y + 46)
                draw.rounded_rectangle(item_rect, radius=9, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
                self._draw_left_text(draw, 214, cy, self._truncate_left_to_fit(text, self.font_key_md, 620), self.font_key_md, COLOR_TEXT_MAIN)

                del_btn_rect = (WIDTH - 114, item_y, WIDTH - 32, item_y + 46)
                self._draw_keycap(
                    draw, del_btn_rect, self._t(state, "bksp", "删除"), font=self.font_key_sm,
                    fill=COLOR_DANGER, border=COLOR_DANGER, text_color=(255, 255, 255, 255),
                    radius=9, shadow=False
                )
                self._add_button(del_btn_rect, "delete_phrase_item", (cur_cat, i))
            else:
                item_rect = (198, item_y, WIDTH - 208, item_y + 46)
                draw.rounded_rectangle(item_rect, radius=9, fill=COLOR_KEY, outline=COLOR_KEY_BORDER)
                self._draw_left_text(draw, 214, cy, self._truncate_left_to_fit(text, self.font_key_md, 540), self.font_key_md, COLOR_TEXT_MAIN)
                self._add_button(item_rect, "fill_phrase", text)

                trans_btn = (WIDTH - 198, item_y, WIDTH - 118, item_y + 46)
                self._draw_keycap(
                    draw, trans_btn, self._t(state, "send_trans_sm", "发译文"), font=self.font_key_sm,
                    fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255),
                    radius=9, shadow=False
                )
                self._add_button(trans_btn, "send_phrase_translated", text)

                orig_btn = (WIDTH - 110, item_y, WIDTH - 32, item_y + 46)
                self._draw_keycap(
                    draw, orig_btn, self._t(state, "send_orig_sm", "发原文"), font=self.font_key_sm,
                    fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER, text_color=(255, 255, 255, 255),
                    radius=9, shadow=False
                )
                self._add_button(orig_btn, "send_phrase_direct", text)

            item_y += 54

    def _render_settings_modal(self, draw: ImageDraw.Draw, state: dict):
        """设置面板：极简科技感 + 四大引擎清晰分流 + 双向多语言切换 + VR体验微调"""
        panel_rect = (16, 72, WIDTH - 16, HEIGHT - 14)
        draw.rounded_rectangle(panel_rect, radius=14, fill=COLOR_SURFACE, outline=COLOR_BORDER)

        # 顶部标题栏
        self._draw_left_text(draw, 36, 98, self._t(state, "settings_title", "系统与翻译引擎设置"), self.font_main, COLOR_TEXT_ACCENT)

        # 界面显示语言切换按钮 (中文 / English)
        ui_lang = state.get("ui_lang", "zh")
        ui_btn = (370, 80, 536, 116)
        ui_label = "● 界面: 简体中文" if ui_lang == "zh" else "● UI: English"
        self._draw_keycap(
            draw, ui_btn, ui_label, font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(ui_btn, "toggle_ui_lang")

        # 顶部网络模式切换 (海外直连 vs 中国代理)
        net_mode = state.get("network_mode", "global")
        is_global = (net_mode == "global")
        net_btn = (546, 80, 720, 116)
        net_label = self._t(state, "net_global", "● 海外直连 (免代理)") if is_global else self._t(state, "net_mainland", "● 中国用户 (走代理)")
        self._draw_keycap(
            draw, net_btn, net_label,
            font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT if is_global else (42, 34, 22, 255),
            border=COLOR_BORDER_ACTIVE if is_global else (150, 110, 45, 255),
            text_color=COLOR_TEXT_ACCENT if is_global else (255, 210, 120, 255),
            radius=8, shadow=False
        )
        self._add_button(net_btn, "toggle_network_mode")

        # 测试连接按钮
        test_btn = (730, 80, 836, 116)
        self._draw_keycap(
            draw, test_btn, self._t(state, "test_conn", "测试连接"), font=self.font_key_sm,
            fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(test_btn, "test_translation_api")

        # 保存返回
        back_rect = (846, 80, 964, 116)
        self._draw_keycap(
            draw, back_rect, self._t(state, "save_return", "保存返回"), font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(back_rect, "toggle_modal", None)

        draw.line([(32, 126), (WIDTH - 32, 126)], fill=COLOR_DIVIDER, width=1)

        # 4大翻译引擎切换按钮
        cur_engine = state.get("engine", "google_official")
        is_free = (cur_engine == "free_direct")
        is_google = (cur_engine == "google_official")
        is_gemini = (cur_engine == "google_gemini")
        is_ds = (cur_engine == "deepseek")

        btn_free = (32, 134, 256, 174)
        lbl_free = ("● " if is_free else "") + self._t(state, "eng_free", "免费通道")
        self._draw_keycap(
            draw, btn_free, lbl_free,
            font=self.font_key_sm,
            fill=COLOR_SUCCESS if is_free else COLOR_KEY_FUNC,
            border=COLOR_SUCCESS_BORDER if is_free else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if is_free else COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(btn_free, "set_engine", "free_direct")

        btn_google = (268, 134, 492, 174)
        lbl_google = ("● " if is_google else "") + self._t(state, "eng_google", "Google 官方翻译")
        self._draw_keycap(
            draw, btn_google, lbl_google,
            font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_google else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if is_google else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if is_google else COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(btn_google, "set_engine", "google_official")

        btn_gemini = (504, 134, 728, 174)
        lbl_gemini = ("● " if is_gemini else "") + self._t(state, "eng_gemini", "Google Gemini AI")
        self._draw_keycap(
            draw, btn_gemini, lbl_gemini,
            font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_gemini else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if is_gemini else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if is_gemini else COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(btn_gemini, "set_engine", "google_gemini")

        btn_ds = (740, 134, 964, 174)
        lbl_ds = ("● " if is_ds else "") + self._t(state, "eng_deepseek", "DeepSeek 大模型")
        self._draw_keycap(
            draw, btn_ds, lbl_ds,
            font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_ds else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if is_ds else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if is_ds else COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(btn_ds, "set_engine", "deepseek")

        # 状态提示条
        settings_tip = state.get("settings_tip", "")
        if settings_tip:
            is_ok = ("成功" in settings_tip or "恢复" in settings_tip or "Success" in settings_tip)
            tip_col = COLOR_TEXT_TRANS if is_ok else (255, 185, 90, 255)
            self._draw_left_text(draw, 36, 192, settings_tip, self.font_key_sm, tip_col)

        # 引擎专属配置卡片 (y: 204..376)
        card_rect = (32, 204, WIDTH - 32, 376)
        draw.rounded_rectangle(card_rect, radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)

        if is_google:
            g_title = "已启用【Google 官方极速翻译】" if ui_lang == "zh" else "Active: [Google Translate API]"
            self._draw_left_text(draw, 52, 230, g_title, self.font_main, COLOR_TEXT_TRANS)

            # 模式切换
            g_global_btn = (52, 252, 240, 290)
            g_gl_lbl = ("● " if is_global else "") + (self._t(state, "net_global", "海外直连 (免代理)"))
            self._draw_keycap(
                draw, g_global_btn, g_gl_lbl,
                font=self.font_key_sm,
                fill=COLOR_PRIMARY if is_global else COLOR_KEY,
                border=COLOR_PRIMARY_BORDER if is_global else COLOR_BORDER,
                text_color=(255, 255, 255, 255) if is_global else COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(g_global_btn, "set_network_mode", "global")

            g_mainland_btn = (252, 252, 450, 290)
            g_ml_lbl = ("● " if not is_global else "") + (self._t(state, "net_mainland", "中国用户 (走代理)"))
            self._draw_keycap(
                draw, g_mainland_btn, g_ml_lbl,
                font=self.font_key_sm,
                fill=COLOR_PRIMARY if not is_global else COLOR_KEY,
                border=COLOR_PRIMARY_BORDER if not is_global else COLOR_BORDER,
                text_color=(255, 255, 255, 255) if not is_global else COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(g_mainland_btn, "set_network_mode", "mainland")

            proxy_str = state.get("proxy", "http://127.0.0.1:7890")
            proxy_btn = (462, 252, 700, 290)
            self._draw_keycap(
                draw, proxy_btn, f"Proxy: {proxy_str}",
                font=self.font_code,
                fill=COLOR_KEY_FUNC,
                border=COLOR_KEY_FUNC_BORDER,
                text_color=COLOR_TEXT_ACCENT,
                radius=8, shadow=False
            )
            self._add_button(proxy_btn, "toggle_proxy_preset")

            if is_global:
                desc1 = "· 专为海外用户打造：直连 Google 官方全球服务器，零配置免Key，毫秒级快速响应。" if ui_lang == "zh" else "· Built for global users: Direct connect to Google global network, zero config, millisecond latency."
            else:
                desc1 = "· 专为中国大陆用户打造：配合本地 Clash/V2Ray 代理使用原生 Google 官方翻译能力。" if ui_lang == "zh" else "· Built for Mainland China: Seamlessly works with local Clash/V2Ray proxy."
            desc2 = "· 支持中文、英语、日语、韩语、俄语等任意语种双向互译，选词完毕毫秒级出译文。" if ui_lang == "zh" else "· Supports Chinese, English, Japanese, Korean, Russian, etc. Instant translation preview."
            self._draw_left_text(draw, 52, 314, desc1, self.font_key_sm, COLOR_TEXT_MAIN)
            self._draw_left_text(draw, 52, 344, desc2, self.font_key_sm, COLOR_TEXT_ACCENT)

        elif is_gemini:
            gem_title = "已启用【Google Gemini 纯语言大模型】" if ui_lang == "zh" else "Active: [Google Gemini AI Translation]"
            self._draw_left_text(draw, 52, 226, gem_title, self.font_main, COLOR_TEXT_TRANS)

            # Key 配置行
            g_key = state.get("google_api_key", "").strip()
            key_text = f"API Key: {g_key[:8]}...{g_key[-4:]}" if g_key else ("API Key: 未配置 (请点击右侧按钮粘贴)" if ui_lang == "zh" else "API Key: Not configured (Tap paste)")
            self._draw_left_text(draw, 52, 258, key_text, self.font_key_md, COLOR_TEXT_MAIN if g_key else (255, 175, 80, 255))

            g_paste_btn = (460, 242, 590, 278)
            self._draw_keycap(
                draw, g_paste_btn, self._t(state, "paste_key", "粘贴 Key"), font=self.font_key_sm,
                fill=COLOR_PRIMARY_SOFT, border=COLOR_PRIMARY_BORDER, text_color=COLOR_TEXT_ACCENT,
                radius=8, shadow=False
            )
            self._add_button(g_paste_btn, "paste_google_key")

            g_clear_btn = (600, 242, 700, 278)
            self._draw_keycap(
                draw, g_clear_btn, self._t(state, "clear_key", "清除 Key"), font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_MUTED,
                radius=8, shadow=False
            )
            self._add_button(g_clear_btn, "clear_google_key")

            # 模型选择行
            cur_model = state.get("google_model", "gemini-3.5-flash-lite")
            model_lbl = f"语言模型: {cur_model}" if ui_lang == "zh" else f"Model: {cur_model}"
            self._draw_left_text(draw, 52, 298, model_lbl, self.font_key_md, COLOR_TEXT_MAIN)

            g_cycle_btn = (330, 282, 510, 318)
            self._draw_keycap(
                draw, g_cycle_btn, self._t(state, "cycle_model", "切换模型"), font=self.font_key_sm,
                fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
                radius=8, shadow=False
            )
            self._add_button(g_cycle_btn, "cycle_gemini_model")

            g_fetch_btn = (520, 282, 690, 318)
            self._draw_keycap(
                draw, g_fetch_btn, self._t(state, "fetch_model", "拉取官方模型"), font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_BORDER, text_color=COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(g_fetch_btn, "fetch_gemini_models")

            # 口吻风格行
            cur_style = state.get("prompt_style", "social")
            if cur_style == "social":
                style_name = self._t(state, "style_social", "友好交流 (礼貌日常)")
            elif cur_style == "aggressive":
                style_name = self._t(state, "style_aggro", "暴躁粗口 (对线游戏)")
            else:
                style_name = self._t(state, "style_custom", "自定义提示词")
            style_lbl = f"{self._t(state, 'style_title', '口吻风格:')} {style_name}"
            self._draw_left_text(draw, 52, 340, style_lbl, self.font_key_md, COLOR_TEXT_MAIN)

            g_style_btn = (330, 324, 480, 360)
            self._draw_keycap(
                draw, g_style_btn, self._t(state, "toggle_style", "切换口吻风格"), font=self.font_key_sm,
                fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
                radius=8, shadow=False
            )
            self._add_button(g_style_btn, "toggle_prompt_style")

            g_custom_btn = (490, 324, 660, 360)
            self._draw_keycap(
                draw, g_custom_btn, self._t(state, "paste_custom", "粘贴自定义提示词"), font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_BORDER, text_color=COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(g_custom_btn, "paste_custom_prompt")

            g_reset_btn = (670, 324, 780, 360)
            self._draw_keycap(
                draw, g_reset_btn, self._t(state, "reset_default", "恢复默认"), font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_BORDER, text_color=COLOR_TEXT_MUTED,
                radius=8, shadow=False
            )
            self._add_button(g_reset_btn, "reset_default_prompt")

        elif is_free:
            free_title = "已启用【零门槛免费极速通道】" if ui_lang == "zh" else "Active: [Free Direct Translation Fastpath]"
            self._draw_left_text(draw, 52, 230, free_title, self.font_main, COLOR_TEXT_TRANS)
            d1 = "· 开箱即用：无需任何账号注册，无需填写 API Key，无需开启本地代理软件。" if ui_lang == "zh" else "· Out of the box: Zero setup, no registration, no API key required."
            d2 = "· 多线互备：海外节点直连 Google 全球节点，国内节点走有道/国际互备通道，稳定防断。" if ui_lang == "zh" else "· Redundant routing: Direct to Google global node, automatic fallback for China mainland."
            d3 = "· 适合无需大模型复杂推理、追求零门槛极速打字发话的用户。" if ui_lang == "zh" else "· Perfect for instant zero-friction chatting without complex LLM reasoning."
            self._draw_left_text(draw, 52, 272, d1, self.font_key_sm, COLOR_TEXT_MAIN)
            self._draw_left_text(draw, 52, 306, d2, self.font_key_sm, COLOR_TEXT_MAIN)
            self._draw_left_text(draw, 52, 340, d3, self.font_key_sm, COLOR_TEXT_ACCENT)

        elif is_ds:
            ds_title = "已启用【DeepSeek 大模型口语化通道】" if ui_lang == "zh" else "Active: [DeepSeek AI Chat Translation]"
            self._draw_left_text(draw, 52, 226, ds_title, self.font_main, COLOR_TEXT_TRANS)

            ds_key = state.get("deepseek_api_key", "").strip()
            key_text = f"API Key: {ds_key[:8]}...{ds_key[-4:]}" if ds_key else ("API Key: 未配置 (请点击右侧按钮粘贴)" if ui_lang == "zh" else "API Key: Not configured (Tap paste)")
            self._draw_left_text(draw, 52, 258, key_text, self.font_key_md, COLOR_TEXT_MAIN if ds_key else (255, 175, 80, 255))

            ds_paste_btn = (460, 242, 590, 278)
            self._draw_keycap(
                draw, ds_paste_btn, self._t(state, "paste_key", "粘贴 Key"), font=self.font_key_sm,
                fill=COLOR_PRIMARY_SOFT, border=COLOR_PRIMARY_BORDER, text_color=COLOR_TEXT_ACCENT,
                radius=8, shadow=False
            )
            self._add_button(ds_paste_btn, "paste_deepseek_key")

            ds_clear_btn = (600, 242, 700, 278)
            self._draw_keycap(
                draw, ds_clear_btn, self._t(state, "clear_key", "清除 Key"), font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_MUTED,
                radius=8, shadow=False
            )
            self._add_button(ds_clear_btn, "clear_deepseek_key")

            # 模型显示
            ds_model = state.get("deepseek_model", "deepseek-chat")
            model_lbl = f"模型: {ds_model}" if ui_lang == "zh" else f"Model: {ds_model}"
            self._draw_left_text(draw, 52, 298, model_lbl, self.font_key_md, COLOR_TEXT_MAIN)

            ds_model_btn = (330, 282, 510, 318)
            self._draw_keycap(
                draw, ds_model_btn, self._t(state, "cycle_ds_model", "切换模型"), font=self.font_key_sm,
                fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
                radius=8, shadow=False
            )
            self._add_button(ds_model_btn, "cycle_deepseek_model")

            # 口吻风格行
            cur_style = state.get("prompt_style", "social")
            if cur_style == "social":
                style_name = self._t(state, "style_social", "友好交流 (礼貌日常)")
            elif cur_style == "aggressive":
                style_name = self._t(state, "style_aggro", "暴躁粗口 (对线游戏)")
            else:
                style_name = self._t(state, "style_custom", "自定义提示词")
            style_lbl = f"{self._t(state, 'style_title', '口吻风格:')} {style_name}"
            self._draw_left_text(draw, 52, 340, style_lbl, self.font_key_md, COLOR_TEXT_MAIN)

            style_btn = (330, 324, 480, 360)
            self._draw_keycap(
                draw, style_btn, self._t(state, "toggle_style", "切换口吻风格"), font=self.font_key_sm,
                fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
                radius=8, shadow=False
            )
            self._add_button(style_btn, "toggle_prompt_style")

            ds_custom_btn = (490, 324, 660, 360)
            self._draw_keycap(
                draw, ds_custom_btn, self._t(state, "paste_custom", "粘贴自定义提示词"), font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_BORDER, text_color=COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(ds_custom_btn, "paste_custom_prompt")

            ds_reset_btn = (670, 324, 780, 360)
            self._draw_keycap(
                draw, ds_reset_btn, self._t(state, "reset_default", "恢复默认"), font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_BORDER, text_color=COLOR_TEXT_MUTED,
                radius=8, shadow=False
            )
            self._add_button(ds_reset_btn, "reset_default_prompt")

        # ------------------------------------------------------------------
        # 双向语言选择区域 (y: 388..472)：专注中英双向，清爽无遮挡
        # ------------------------------------------------------------------
        draw.line([(32, 386), (WIDTH - 32, 386)], fill=COLOR_DIVIDER, width=1)

        cur_src = state.get("source_lang", "zh")
        cur_tgt = state.get("target_lang", "en")
        is_zh2en = (cur_src == "zh" and cur_tgt == "en")
        is_en2zh = (cur_src == "en" and cur_tgt == "zh")

        self._draw_left_text(draw, 36, 430, self._t(state, "lang_pair_title", "语言互译模式:"), self.font_key_md, COLOR_TEXT_MAIN)

        # 选项 1: 中文拼音 -> 英语
        btn_zh2en = (180, 408, 480, 452)
        lbl_zh2en = ("● " if is_zh2en else "") + self._t(state, "zh2en", "中文拼音 → 英语 (中→英)").replace("● ", "")
        self._draw_keycap(
            draw, btn_zh2en, lbl_zh2en,
            font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_zh2en else COLOR_KEY,
            border=COLOR_PRIMARY_BORDER if is_zh2en else COLOR_BORDER,
            text_color=(255, 255, 255, 255) if is_zh2en else COLOR_TEXT_SUB,
            radius=8, shadow=False
        )
        self._add_button(btn_zh2en, "set_lang_pair", ("zh", "en"))

        # 选项 2: 英文直接 -> 中文
        btn_en2zh = (490, 408, 770, 452)
        lbl_en2zh = ("● " if is_en2zh else "") + self._t(state, "en2zh", "英文直接 → 中文 (英→中)").replace("● ", "")
        self._draw_keycap(
            draw, btn_en2zh, lbl_en2zh,
            font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_en2zh else COLOR_KEY,
            border=COLOR_PRIMARY_BORDER if is_en2zh else COLOR_BORDER,
            text_color=(255, 255, 255, 255) if is_en2zh else COLOR_TEXT_SUB,
            radius=8, shadow=False
        )
        self._add_button(btn_en2zh, "set_lang_pair", ("en", "zh"))

        # 选项 3: 一键互换中英
        swap_btn = (780, 408, 964, 452)
        self._draw_keycap(
            draw, swap_btn, self._t(state, "swap_lang", "一键互换中英"), font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(swap_btn, "swap_lang")

        # ------------------------------------------------------------------
        # 底部控制栏 (y: 480..536)
        # ------------------------------------------------------------------
        draw.line([(32, 478), (WIDTH - 32, 478)], fill=COLOR_DIVIDER, width=1)

        # 重置输入记忆
        reset_btn = (36, 492, 160, 528)
        self._draw_keycap(
            draw, reset_btn, self._t(state, "reset_dict", "重置输入记忆"), font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB,
            radius=8, shadow=False
        )
        self._add_button(reset_btn, "clear_user_history")

        # 初始模式切换 (中文拼音 vs 英文直出)
        init_mode = state.get("input_mode", "zh")
        init_mode_btn = (170, 492, 340, 528)
        init_lbl = self._t(state, "init_zh", "初始: ● 中文拼音") if init_mode == "zh" else self._t(state, "init_en", "初始: ● 英文直出")
        self._draw_keycap(
            draw, init_mode_btn, init_lbl,
            font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT if init_mode == "zh" else COLOR_KEY,
            border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(init_mode_btn, "toggle_input_mode")

        # VR 键盘尺寸微调
        overlay_w = state.get("overlay_width_m", 0.42)
        sz_text = f"大小:{overlay_w:.2f}m" if ui_lang == "zh" else f"Size:{overlay_w:.2f}m"
        self._draw_left_text(draw, 355, 510, sz_text, self.font_tiny, COLOR_TEXT_MUTED)

        shrink_btn = (420, 496, 465, 524)
        self._draw_keycap(draw, shrink_btn, self._t(state, "zoom_out", "- 缩小"), font=self.font_tiny, fill=COLOR_KEY, border=COLOR_BORDER, radius=6, shadow=False)
        self._add_button(shrink_btn, "adjust_scale", -0.04)

        expand_btn = (472, 496, 517, 524)
        self._draw_keycap(draw, expand_btn, self._t(state, "zoom_in", "+ 放大"), font=self.font_tiny, fill=COLOR_KEY, border=COLOR_BORDER, radius=6, shadow=False)
        self._add_button(expand_btn, "adjust_scale", 0.04)

        reset_sz_btn = (524, 496, 560, 524)
        self._draw_keycap(draw, reset_sz_btn, self._t(state, "zoom_std", "标准"), font=self.font_tiny, fill=COLOR_KEY, border=COLOR_BORDER, radius=6, shadow=False)
        self._add_button(reset_sz_btn, "reset_scale")

        # 激光引导模式
        lg_mode = state.get("laser_guide", "auto")
        if lg_mode == "auto":
            lg_label = self._t(state, "guide_auto", "引导: 智能(SteamVR隐藏)")
        elif lg_mode == "on":
            lg_label = self._t(state, "guide_on", "引导: 强制开启")
        else:
            lg_label = self._t(state, "guide_off", "引导: 强制关闭")
        lg_btn = (570, 492, 740, 528)
        self._draw_keycap(
            draw, lg_btn, lg_label, font=self.font_tiny,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB,
            radius=8, shadow=False
        )
        self._add_button(lg_btn, "cycle_laser_guide")

        # 呼出方式提示
        hk_label = self._t(state, "call_key", "呼出: 右手摇杆双击")
        self._draw_keycap(
            draw, (750, 492, 964, 528), hk_label, font=self.font_tiny,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_MUTED,
            radius=8, shadow=False
        )
