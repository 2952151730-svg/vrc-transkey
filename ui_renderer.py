import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Any

WIDTH = 1000
HEIGHT = 560

# 现代极简深色磨砂配色体系 (Slate & Glass Dark UI)
COLOR_BG = (14, 17, 24, 248)            # 主背景：深邃暗夜蓝黑
COLOR_BG_BORDER = (44, 52, 68, 255)     # 外框微光边线
COLOR_SURFACE = (21, 26, 37, 255)       # 卡片容器表面
COLOR_SURFACE_INNER = (16, 20, 29, 255) # 内嵌深色槽
COLOR_DIVIDER = (36, 44, 60, 255)       # 柔和分割线
COLOR_BORDER = (46, 56, 76, 255)        # 常规描边
COLOR_BORDER_ACTIVE = (68, 148, 255, 255) # 激活态科技蓝描边

# 键帽层次配色
COLOR_KEY_SHADOW = (9, 12, 18, 255)     # 键帽底部立体投影
COLOR_KEY = (35, 42, 57, 255)           # 主字母键帽
COLOR_KEY_BORDER = (50, 60, 80, 255)    # 字母键微光上沿
COLOR_KEY_FUNC = (26, 32, 44, 255)      # 功能键帽
COLOR_KEY_FUNC_BORDER = (40, 49, 66, 255)

# 语义强调色
COLOR_PRIMARY = (42, 118, 246, 255)     # 科技蓝 (发送译文 / 主操作)
COLOR_PRIMARY_BORDER = (82, 152, 255, 255)
COLOR_PRIMARY_SOFT = (30, 64, 118, 255) # 柔和蓝底 (首选候选词 / 语言胶囊)

COLOR_SUCCESS = (32, 162, 88, 255)      # 翡翠绿 (发送中文)
COLOR_SUCCESS_BORDER = (66, 198, 118, 255)

COLOR_DANGER = (210, 56, 68, 255)       # 珊瑚红 (警告/高亮删)
COLOR_DANGER_SOFT = (52, 28, 36, 255)   # 柔和关闭按钮底色

# 优雅暗红键帽配色 (删除键：不刺眼、高级磨砂暗红)
COLOR_DELETE_BG = (58, 24, 32, 255)
COLOR_DELETE_BORDER = (112, 44, 56, 255)
COLOR_DELETE_TEXT = (255, 196, 202, 255)

# 文本层级色
COLOR_TEXT_MAIN = (242, 246, 252, 255)  # 主文字：纯净柔白
COLOR_TEXT_SUB = (172, 184, 204, 255)   # 次级文字
COLOR_TEXT_MUTED = (112, 124, 148, 255) # 占位/弱提示文字
COLOR_TEXT_ACCENT = (108, 182, 255, 255)# 科技蓝高亮字
COLOR_TEXT_TRANS = (132, 238, 162, 255) # 译文薄荷绿字

LANG_DISPLAY_MAP = {
    "en": "中 > 英",
    "ja": "中 > 日",
    "ko": "中 > 韩",
    "ru": "中 > 俄",
    "fr": "中 > 法",
    "de": "中 > 德"
}

QUICK_IDLE_CHIPS = ["哈哈", "好的", "稍等", "谢谢", "听不见", "不便开麦", "？", "！"]


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

    def _add_button(self, rect: Tuple[int, int, int, int], action: str, data: Any = None):
        self.cached_clickables.append((rect, action, data))

    def _draw_centered_text(self, draw: ImageDraw.Draw, rect: Tuple[int, int, int, int], text: str, font, fill):
        """数学级精准居中绘制文字"""
        cx = (rect[0] + rect[2]) // 2
        cy = (rect[1] + rect[3]) // 2
        try:
            draw.text((cx, cy), text, font=font, fill=fill, anchor="mm")
        except Exception:
            bbox = font.getbbox(text) if hasattr(font, "getbbox") else (0, 0, len(text) * 10, 16)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((cx - tw // 2, cy - th // 2 - 2), text, font=font, fill=fill)

    def _draw_left_text(self, draw: ImageDraw.Draw, x: int, cy: int, text: str, font, fill):
        """垂直居中、水平左对齐绘制文字"""
        try:
            draw.text((x, cy), text, font=font, fill=fill, anchor="lm")
        except Exception:
            draw.text((x, cy - 10), text, font=font, fill=fill)

    def _draw_keycap(
        self,
        draw: ImageDraw.Draw,
        rect: Tuple[int, int, int, int],
        label: str,
        font=None,
        fill=COLOR_KEY,
        border=COLOR_KEY_BORDER,
        text_color=COLOR_TEXT_MAIN,
        radius: int = 12,
        sub_label: str = "",
        underline: bool = False,
        shadow: bool = True
    ):
        """绘制具有立体微投影与细腻边框的现代键帽"""
        x1, y1, x2, y2 = rect
        if shadow:
            draw.rounded_rectangle((x1, y1 + 2, x2, y2 + 2), radius=radius, fill=COLOR_KEY_SHADOW)
        draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=border, width=1)

        use_font = font or self.font_key
        self._draw_centered_text(draw, rect, label, use_font, text_color)

        if sub_label:
            try:
                draw.text((x2 - 10, y1 + 8), sub_label, font=self.font_tiny, fill=COLOR_TEXT_MUTED, anchor="rt")
            except Exception:
                pass

        if underline:
            # F / J 盲打定位横线或空格底标
            cx = (x1 + x2) // 2
            draw.line([(cx - 8, y2 - 10), (cx + 8, y2 - 10)], fill=COLOR_TEXT_ACCENT, width=2)

    def _truncate_left_to_fit(self, text: str, font, max_width: int) -> str:
        """当文本超长时保留末尾最新输入的部分"""
        if not text:
            return ""
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

        # 面板外框与顶部精致指示条 (无需文字，极简风格)
        draw.rounded_rectangle([(1, 1), (WIDTH - 2, HEIGHT - 2)], radius=18, outline=COLOR_BG_BORDER, width=2)
        draw.rounded_rectangle([(WIDTH // 2 - 42, 5), (WIDTH // 2 + 42, 9)], radius=2, fill=(56, 68, 90, 200))

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
        """第一行 (y: 14..64)：语言胶囊 + 实时译文预览 + 发送译文 + 常用语/设置/关闭"""
        y1, y2 = 14, 64
        cy = (y1 + y2) // 2

        # 1. 语言切换胶囊 [ 中 > 英 ]
        target_lang = state.get("target_lang", "en")
        lang_text = LANG_DISPLAY_MAP.get(target_lang, f"中 > {target_lang.upper()}")
        lang_rect = (16, y1, 118, y2)
        self._draw_keycap(
            draw, lang_rect, lang_text, font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE,
            text_color=COLOR_TEXT_ACCENT, radius=11, shadow=False
        )
        self._add_button(lang_rect, "cycle_lang")

        # 2. 中间：实时译文显示舱
        trans_rect = (126, y1, 666, y2)
        trans_text = state.get("translated_text", "").strip()
        draw.rounded_rectangle(trans_rect, radius=11, fill=COLOR_SURFACE, outline=COLOR_BORDER)

        # 状态指示圆点
        dot_color = COLOR_SUCCESS_BORDER if trans_text else (72, 84, 108, 255)
        draw.ellipse((140, cy - 4, 148, cy + 4), fill=dot_color)

        if trans_text:
            fitted_trans = self._truncate_left_to_fit(trans_text, self.font_trans, 500)
            self._draw_left_text(draw, 158, cy, fitted_trans, self.font_trans, COLOR_TEXT_TRANS)
        else:
            engine = state.get("engine", "free_direct")
            if engine == "google_gemini":
                eng_tag = "Google Gemini AI"
            elif engine == "deepseek":
                eng_tag = "DeepSeek AI"
            else:
                eng_tag = "极速免翻直连"
            self._draw_left_text(draw, 158, cy, f"实时译文预览 ({eng_tag} · 输入中文自动翻译)", self.font_key_sm, COLOR_TEXT_MUTED)

        # 3. [ 发送译文 ] 主按钮
        send_trans_rect = (674, y1, 790, y2)
        self._draw_keycap(
            draw, send_trans_rect, "发送译文", font=self.font_key_sm,
            fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER,
            text_color=(255, 255, 255, 255), radius=11
        )
        self._add_button(send_trans_rect, "send_translated")

        # 4. 右侧功能胶囊：常用语 / 设置 / 关闭
        active_modal = state.get("active_modal")

        phrase_rect = (798, y1, 870, y2)
        is_ph = (active_modal == "phrases")
        self._draw_keycap(
            draw, phrase_rect, "常用语", font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_ph else COLOR_SURFACE,
            border=COLOR_PRIMARY_BORDER if is_ph else COLOR_BORDER,
            text_color=(255, 255, 255, 255) if is_ph else COLOR_TEXT_SUB,
            radius=11, shadow=False
        )
        self._add_button(phrase_rect, "toggle_modal", "phrases")

        settings_rect = (878, y1, 938, y2)
        is_st = (active_modal == "settings")
        self._draw_keycap(
            draw, settings_rect, "设置", font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_st else COLOR_SURFACE,
            border=COLOR_PRIMARY_BORDER if is_st else COLOR_BORDER,
            text_color=(255, 255, 255, 255) if is_st else COLOR_TEXT_SUB,
            radius=11, shadow=False
        )
        self._add_button(settings_rect, "toggle_modal", "settings")

        close_rect = (946, y1, 984, y2)
        self._draw_keycap(
            draw, close_rect, "×", font=self.font_key,
            fill=COLOR_DANGER_SOFT, border=(110, 48, 58, 255),
            text_color=(255, 110, 120, 255), radius=11, shadow=False
        )
        self._add_button(close_rect, "hide_overlay")

    def _render_unified_input_card(self, draw: ImageDraw.Draw, state: dict):
        """
        第二行一体化卡片 (y: 72..188)：
        上半层 (y: 72..130): 原文输入框 + 内联拼音胶囊 + [粘贴] [上句] [清空]
        下半层 (y: 130..188): 候选词胶囊栏 (空闲时自动变为高频快捷词条栏)
        """
        card_rect = (16, 72, WIDTH - 16, 188)
        committed_text = state.get("committed_text", "")
        pinyin_buffer = state.get("pinyin_buffer", "")
        has_content = bool(committed_text or pinyin_buffer)

        draw.rounded_rectangle(
            card_rect, radius=14, fill=COLOR_SURFACE,
            outline=COLOR_BORDER_ACTIVE if has_content else COLOR_BORDER, width=1
        )
        # 中间柔和分割线
        draw.line([(28, 130), (WIDTH - 28, 130)], fill=COLOR_DIVIDER, width=1)

        # --- 上半层：原文输入行 (y: 72..130, cy=101) ---
        icy = 101
        # 左侧装饰呼吸竖条
        bar_col = COLOR_PRIMARY if has_content else (64, 76, 98, 255)
        draw.rounded_rectangle((28, 88, 32, 114), radius=2, fill=bar_col)

        cur_x = 44
        if has_content:
            if committed_text:
                fitted_orig = self._truncate_left_to_fit(committed_text, self.font_preview, 540)
                self._draw_left_text(draw, cur_x, icy, fitted_orig, self.font_preview, COLOR_TEXT_MAIN)
                bbox = self.font_preview.getbbox(fitted_orig)
                cur_x += (bbox[2] - bbox[0]) + 8

            if pinyin_buffer:
                # 渲染精致的内联拼音胶囊 (支持点击直接将英文字母原样上屏)
                py_bbox = self.font_key_md.getbbox(pinyin_buffer)
                pw = (py_bbox[2] - py_bbox[0]) + 20
                pill_rect = (cur_x, icy - 15, cur_x + pw, icy + 15)
                draw.rounded_rectangle(pill_rect, radius=7, fill=COLOR_PRIMARY_SOFT, outline=COLOR_BORDER_ACTIVE)
                self._draw_centered_text(draw, pill_rect, pinyin_buffer, self.font_key_md, COLOR_TEXT_ACCENT)
                self._add_button(pill_rect, "key_enter")
                cur_x += pw + 6

            # 光标竖线
            draw.line([(cur_x, icy - 13), (cur_x, icy + 13)], fill=COLOR_BORDER_ACTIVE, width=2)
        else:
            is_zh = state.get("input_mode", "zh") == "zh"
            placeholder = "点击按键或敲击键盘输入中文拼音..." if is_zh else "当前为英文直输模式 (English Mode)..."
            self._draw_left_text(draw, cur_x, icy, placeholder, self.font_key_md, COLOR_TEXT_MUTED)
            draw.line([(cur_x, icy - 12), (cur_x, icy + 12)], fill=(75, 90, 115, 255), width=2)

        # 右侧快捷内嵌按钮: [粘贴] [上句] [清空]
        paste_rect = (760, 82, 824, 120)
        self._draw_keycap(
            draw, paste_rect, "粘贴", font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_SUB, radius=8, shadow=False
        )
        self._add_button(paste_rect, "paste_clipboard")

        hist_rect = (832, 82, 900, 120)
        self._draw_keycap(
            draw, hist_rect, "上句", font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False
        )
        self._add_button(hist_rect, "recall_history")

        clear_rect = (908, 82, 972, 120)
        self._draw_keycap(
            draw, clear_rect, "清空", font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_MUTED, radius=8, shadow=False
        )
        self._add_button(clear_rect, "clear_text")

        # --- 下半层：候选词与快捷词条栏 (y: 130..188, cy=159) ---
        ccy = 159
        candidates = state.get("candidates", [])
        has_prev = state.get("has_prev_page", False)
        has_next = state.get("has_next_page", False)

        if pinyin_buffer and candidates:
            # 智能弹性排版：计算所有候选词的基础宽度，并将右侧多余空白均匀分配给各个按键，饱满铺满整栏
            start_x = 28
            max_end_x = WIDTH - 134  # 翻页按钮前留白至 866px
            avail_w = max_end_x - start_x
            base_gap = 8

            raw_widths = []
            for i, cand in enumerate(candidates):
                tag = f"{i + 1}. {cand}"
                tb = self.font_cand.getbbox(tag)
                tw = tb[2] - tb[0]
                base_w = max(74, tw + 24)
                raw_widths.append(base_w)

            n = len(raw_widths)
            total_needed = sum(raw_widths) + (n - 1) * base_gap

            # 若有富余宽度且有多个候选词，适度扩展各个按钮让候选栏视觉饱满铺满 (单键最多扩宽 22px)
            if total_needed < avail_w and n > 0:
                extra_per_btn = min(22, (avail_w - total_needed) // n)
            else:
                extra_per_btn = 0

            offset_x = start_x
            for i, cand in enumerate(candidates):
                btn_w = raw_widths[i] + extra_per_btn
                if offset_x + btn_w > WIDTH - 126:
                    break
                cand_rect = (offset_x, 139, offset_x + btn_w, 179)
                tag = f"{i + 1}. {cand}"
                is_first = (i == 0)
                self._draw_keycap(
                    draw, cand_rect, tag, font=self.font_cand,
                    fill=COLOR_PRIMARY_SOFT if is_first else COLOR_KEY,
                    border=COLOR_BORDER_ACTIVE if is_first else COLOR_KEY_BORDER,
                    text_color=(255, 255, 255, 255) if is_first else COLOR_TEXT_MAIN,
                    radius=9, shadow=False
                )
                self._add_button(cand_rect, "select_candidate", i)
                offset_x += btn_w + base_gap

            # 翻页按钮
            prev_rect = (WIDTH - 122, 139, WIDTH - 76, 179)
            self._draw_keycap(
                draw, prev_rect, "‹", font=self.font_key,
                fill=COLOR_KEY if has_prev else COLOR_SURFACE_INNER,
                border=COLOR_KEY_BORDER if has_prev else COLOR_DIVIDER,
                text_color=COLOR_TEXT_MAIN if has_prev else COLOR_TEXT_MUTED,
                radius=9, shadow=False
            )
            if has_prev:
                self._add_button(prev_rect, "cand_prev")

            next_rect = (WIDTH - 70, 139, WIDTH - 24, 179)
            self._draw_keycap(
                draw, next_rect, "›", font=self.font_key,
                fill=COLOR_KEY if has_next else COLOR_SURFACE_INNER,
                border=COLOR_KEY_BORDER if has_next else COLOR_DIVIDER,
                text_color=COLOR_TEXT_MAIN if has_next else COLOR_TEXT_MUTED,
                radius=9, shadow=False
            )
            if has_next:
                self._add_button(next_rect, "cand_next")
        else:
            # 空闲状态：展示一键高频快捷词条 Chips
            self._draw_left_text(draw, 30, ccy, "快捷词:", self.font_key_sm, COLOR_TEXT_MUTED)
            offset_x = 92
            for chip in QUICK_IDLE_CHIPS:
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
        else:
            self._render_letters_panel(draw, state)

    def _render_letters_panel(self, draw: ImageDraw.Draw, state: dict):
        """主键盘：清爽黄金比例 26 键布局 (y: 198..542)"""
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

        # --- Row 1: Q - P (带右上角轻量数字角标) ---
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

        # --- Row 2: A - L (居中对齐 + F/J 盲打定位线) ---
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

        # --- Row 3: [大写] + Z - M + [退格] + [回车] ---
        y += key_h + gap
        caps_w = 98
        caps_rect = (16, y, 16 + caps_w, y + key_h)
        caps_active = is_caps or is_shift
        self._draw_keycap(
            draw, caps_rect, "大写", font=self.font_key_md,
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
        # 优雅对称布局：左边大写(98px) + 中间7键 + 右边删除(82px)与回车(82px)，完美左右16px对称
        bksp_w = 82
        bksp_rect = (bksp_x, y, bksp_x + bksp_w, y + key_h)
        self._draw_keycap(
            draw, bksp_rect, "删除", font=self.font_key_md,
            fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT
        )
        self._add_button(bksp_rect, "key_press", "Backspace")

        enter_x = bksp_x + bksp_w + gap
        enter_rect = (enter_x, y, WIDTH - 16, y + key_h)
        enter_label = "回车(英)" if has_pinyin else "回车"
        self._draw_keycap(
            draw, enter_rect, enter_label, font=self.font_key_sm if has_pinyin else self.font_key_md,
            fill=COLOR_PRIMARY if has_pinyin else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if has_pinyin else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if has_pinyin else COLOR_TEXT_MAIN
        )
        self._add_button(enter_rect, "key_enter")

        # --- Row 4: [123] [符] [，] [空格] [。] [中/EN] [发送中文] ---
        y += key_h + gap

        # 1. [123]
        r_123 = (16, y, 106, y + key_h)
        self._draw_keycap(
            draw, r_123, "123", font=self.font_key_md,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB
        )
        self._add_button(r_123, "switch_keyboard", "numbers")

        # 2. [符]
        r_sym = (116, y, 206, y + key_h)
        self._draw_keycap(
            draw, r_sym, "#+= 符", font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB
        )
        self._add_button(r_sym, "switch_keyboard", "symbols")

        # 3. [，]
        r_comma = (216, y, 294, y + key_h)
        self._draw_keycap(draw, r_comma, "，", font=self.font_key)
        self._add_button(r_comma, "insert_char", "，")

        # 4. [空格]
        r_space = (304, y, 646, y + key_h)
        space_label = "空格 (选首选词)" if has_pinyin else "空  格"
        self._draw_keycap(
            draw, r_space, space_label, font=self.font_key_md,
            fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE if has_pinyin else COLOR_KEY_BORDER,
            text_color=COLOR_TEXT_ACCENT if has_pinyin else COLOR_TEXT_MUTED
        )
        self._add_button(r_space, "key_space")

        # 5. [。]
        r_dot = (656, y, 734, y + key_h)
        self._draw_keycap(draw, r_dot, "。", font=self.font_key)
        self._add_button(r_dot, "insert_char", "。")

        # 6. [中 / EN]
        r_ime = (744, y, 844, y + key_h)
        ime_label = "中 / 英" if is_zh else "EN / 中"
        self._draw_keycap(
            draw, r_ime, ime_label, font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT if is_zh else COLOR_KEY_FUNC,
            border=COLOR_BORDER_ACTIVE if is_zh else COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_ACCENT if is_zh else COLOR_TEXT_SUB
        )
        self._add_button(r_ime, "toggle_ime")

        # 7. [发送中文]
        r_send_zh = (854, y, WIDTH - 16, y + key_h)
        self._draw_keycap(
            draw, r_send_zh, "发送中文", font=self.font_key_md,
            fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER,
            text_color=(255, 255, 255, 255)
        )
        self._add_button(r_send_zh, "send_original")

    def _render_sub_panel_grid(self, draw: ImageDraw.Draw, rows: List[List[str]], switch_btn_text: str, switch_target: str):
        """通用数字/符号子键盘网格渲染器"""
        key_h = 78
        gap = 10
        start_y = 198
        w_key = 88

        for r_idx, r_list in enumerate(rows):
            y = start_y + r_idx * (key_h + gap)
            start_x = 16
            for c_idx, sym in enumerate(r_list):
                x = start_x + c_idx * (w_key + gap)
                rect = (x, y, x + w_key, y + key_h)
                self._draw_keycap(draw, rect, sym, font=self.font_key)
                self._add_button(rect, "insert_char", sym)

        # 底部导航栏
        y = start_y + 3 * (key_h + gap)
        ret_rect = (16, y, 160, y + key_h)
        self._draw_keycap(
            draw, ret_rect, "返回 ABC", font=self.font_key_sm,
            fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255)
        )
        self._add_button(ret_rect, "switch_keyboard", "letters")

        sw_rect = (170, y, 294, y + key_h)
        self._draw_keycap(
            draw, sw_rect, switch_btn_text, font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB
        )
        self._add_button(sw_rect, "switch_keyboard", switch_target)

        sp_rect = (304, y, 594, y + key_h)
        self._draw_keycap(
            draw, sp_rect, "空  格", font=self.font_key_md,
            fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_MUTED
        )
        self._add_button(sp_rect, "key_space")

        enter_sub_rect = (604, y, 704, y + key_h)
        self._draw_keycap(
            draw, enter_sub_rect, "回车", font=self.font_key_md,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_MAIN
        )
        self._add_button(enter_sub_rect, "key_enter")

        bk_rect = (714, y, 844, y + key_h)
        self._draw_keycap(
            draw, bk_rect, "删除", font=self.font_key_md,
            fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT
        )
        self._add_button(bk_rect, "key_press", "Backspace")

        snd_rect = (854, y, WIDTH - 16, y + key_h)
        self._draw_keycap(
            draw, snd_rect, "发送中文", font=self.font_key_md,
            fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER, text_color=(255, 255, 255, 255)
        )
        self._add_button(snd_rect, "send_original")

    def _render_symbols_panel(self, draw: ImageDraw.Draw, state: dict):
        rows = [
            ["！", "？", "～", "、", "：", "；", "“", "”", "‘", "’"],
            ["（", "）", "【", "】", "《", "》", "…", "—", "·", "/"],
            ["@", "#", "$", "%", "&", "*", "+", "=", "^", "\\"]
        ]
        self._render_sub_panel_grid(draw, rows, "123 数字", "numbers")

    def _render_numbers_panel(self, draw: ImageDraw.Draw, state: dict):
        rows = [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["+", "-", "*", "/", "=", "%", ".", ",", ":", ";"],
            ["(", ")", "[", "]", "{", "}", "<", ">", "_", "~"]
        ]
        self._render_sub_panel_grid(draw, rows, "#+= 符号", "symbols")

    def _render_phrases_modal(self, draw: ImageDraw.Draw, state: dict):
        """常用语快捷面板：支持点击填入输入框、一键直接发译文或发中文、以及管理删除"""
        panel_rect = (16, 72, WIDTH - 16, HEIGHT - 14)
        draw.rounded_rectangle(panel_rect, radius=14, fill=COLOR_SURFACE, outline=COLOR_BORDER)

        is_delete_mode = state.get("is_delete_phrase_mode", False)
        title = "常用语管理 [点击右侧红色按钮删除]" if is_delete_mode else "常用语快捷面板 (点击词条填入，或点右侧直发)"
        self._draw_left_text(draw, 36, 98, title, self.font_key_md, COLOR_DANGER if is_delete_mode else COLOR_TEXT_ACCENT)

        add_rect = (520, 80, 680, 116)
        self._draw_keycap(
            draw, add_rect, "+ 存入当前输入/剪贴板", font=self.font_key_sm,
            fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER, text_color=(255, 255, 255, 255),
            radius=8, shadow=False
        )
        self._add_button(add_rect, "add_new_phrase")

        del_mode_rect = (690, 80, 810, 116)
        self._draw_keycap(
            draw, del_mode_rect, "完成管理" if is_delete_mode else "管理删除", font=self.font_key_sm,
            fill=COLOR_DANGER if is_delete_mode else COLOR_KEY_FUNC,
            border=COLOR_DANGER if is_delete_mode else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255), radius=8, shadow=False
        )
        self._add_button(del_mode_rect, "toggle_delete_phrase_mode")

        back_rect = (820, 80, 964, 116)
        self._draw_keycap(
            draw, back_rect, "返回键盘", font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(back_rect, "toggle_modal", None)

        draw.line([(32, 126), (WIDTH - 32, 126)], fill=COLOR_DIVIDER, width=1)

        phrases_data = state.get("phrases_data", {})
        cats = list(phrases_data.keys())
        cur_cat = state.get("phrase_cat", cats[0] if cats else "")

        # 左侧分类导航
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

        # 右侧词条列表
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
                    draw, del_btn_rect, "删除", font=self.font_key_sm,
                    fill=COLOR_DANGER, border=COLOR_DANGER, text_color=(255, 255, 255, 255),
                    radius=9, shadow=False
                )
                self._add_button(del_btn_rect, "delete_phrase_item", (cur_cat, i))
            else:
                item_rect = (198, item_y, WIDTH - 208, item_y + 46)
                draw.rounded_rectangle(item_rect, radius=9, fill=COLOR_KEY, outline=COLOR_KEY_BORDER)
                self._draw_left_text(draw, 214, cy, self._truncate_left_to_fit(text, self.font_key_md, 540), self.font_key_md, COLOR_TEXT_MAIN)
                self._add_button(item_rect, "fill_phrase", text)

                # [发译文]
                trans_btn = (WIDTH - 198, item_y, WIDTH - 118, item_y + 46)
                self._draw_keycap(
                    draw, trans_btn, "发译文", font=self.font_key_sm,
                    fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255),
                    radius=9, shadow=False
                )
                self._add_button(trans_btn, "send_phrase_translated", text)

                # [发原文]
                orig_btn = (WIDTH - 110, item_y, WIDTH - 32, item_y + 46)
                self._draw_keycap(
                    draw, orig_btn, "发原文", font=self.font_key_sm,
                    fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER, text_color=(255, 255, 255, 255),
                    radius=9, shadow=False
                )
                self._add_button(orig_btn, "send_phrase_direct", text)

            item_y += 54

    def _render_settings_modal(self, draw: ImageDraw.Draw, state: dict):
        """设置面板：清爽无重叠排版 + 一键测试连接 + VR 舒适度调节"""
        panel_rect = (16, 72, WIDTH - 16, HEIGHT - 14)
        draw.rounded_rectangle(panel_rect, radius=14, fill=COLOR_SURFACE, outline=COLOR_BORDER)

        self._draw_left_text(draw, 36, 98, "系统与翻译引擎设置 (自动保存并同步至 VR 模式)", self.font_main, COLOR_TEXT_ACCENT)

        # 一键测试连接按钮
        test_btn = (660, 80, 810, 116)
        self._draw_keycap(
            draw, test_btn, "测试翻译连接", font=self.font_key_sm,
            fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(test_btn, "test_translation_api")

        # 网络模式切换按钮 (海外直连 vs 大陆加速)
        net_mode = state.get("network_mode", "global")
        is_global = (net_mode == "global")
        net_btn = (590, 80, 804, 116)
        self._draw_keycap(
            draw, net_btn, "● 🌍 海外直连模式" if is_global else "● 🇨🇳 大陆加速模式",
            font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT if is_global else (40, 36, 28, 255),
            border=COLOR_BORDER_ACTIVE if is_global else (120, 95, 45, 255),
            text_color=COLOR_TEXT_ACCENT if is_global else (255, 210, 120, 255),
            radius=8, shadow=False
        )
        self._add_button(net_btn, "toggle_network_mode")

        back_rect = (820, 80, 964, 116)
        self._draw_keycap(
            draw, back_rect, "保存返回", font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(back_rect, "toggle_modal", None)

        draw.line([(32, 126), (WIDTH - 32, 126)], fill=COLOR_DIVIDER, width=1)

        cur_engine = state.get("engine", "free_direct")
        is_free = (cur_engine == "free_direct")
        is_gemini = (cur_engine == "google_gemini")
        is_ds = (cur_engine == "deepseek")

        self._draw_left_text(draw, 36, 154, "翻译引擎:", self.font_key_md, COLOR_TEXT_SUB)

        btn_free = (120, 134, 380, 174)
        self._draw_keycap(
            draw, btn_free, "● 免翻极速直连" if is_free else "免翻极速直连",
            font=self.font_key_sm,
            fill=COLOR_SUCCESS if is_free else COLOR_KEY_FUNC,
            border=COLOR_SUCCESS_BORDER if is_free else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if is_free else COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(btn_free, "set_engine", "free_direct")

        btn_gemini = (394, 134, 664, 174)
        self._draw_keycap(
            draw, btn_gemini, "● Google Gemini AI" if is_gemini else "Google Gemini AI",
            font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_gemini else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if is_gemini else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if is_gemini else COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(btn_gemini, "set_engine", "google_gemini")

        btn_ds = (678, 134, 948, 174)
        self._draw_keycap(
            draw, btn_ds, "● DeepSeek 大模型" if is_ds else "DeepSeek 大模型",
            font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_ds else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if is_ds else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if is_ds else COLOR_TEXT_SUB,
            radius=9, shadow=False
        )
        self._add_button(btn_ds, "set_engine", "deepseek")

        # 状态提示栏 (独立右对齐区域或专属通知横幅，绝不与标题重叠)
        settings_tip = state.get("settings_tip", "")
        if settings_tip:
            is_ok = ("√" in settings_tip or "成功" in settings_tip or "恢复" in settings_tip)
            tip_col = COLOR_TEXT_TRANS if is_ok else (255, 185, 90, 255)
            self._draw_left_text(draw, 36, 194, settings_tip, self.font_key_sm, tip_col)

        card_rect = (32, 206, WIDTH - 32, 474)
        draw.rounded_rectangle(card_rect, radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)

        if is_free:
            if is_global:
                self._draw_left_text(draw, 56, 238, "已启用【Google 官方极速直连通道】", self.font_main, COLOR_TEXT_TRANS)
                self._draw_left_text(draw, 56, 276, "• 专为海外用户打造：Google 全球官方接口直连，免Key零配置，毫秒级响应。", self.font_key_md, COLOR_TEXT_MAIN)
            else:
                self._draw_left_text(draw, 56, 238, "已启用【中国大陆极速免翻双引擎通道 (有道极速 + MyMemory 国际互备)】", self.font_main, COLOR_TEXT_TRANS)
                self._draw_left_text(draw, 56, 276, "• 专为大陆网络优化：无需注册、无需 API Key、无需开启代理加速器，开箱即用。", self.font_key_md, COLOR_TEXT_MAIN)

            self._draw_left_text(draw, 56, 310, "• 毫秒级响应速度：打字选词完毕毫秒级出译文，直接通过 OSC 广播至 VRChat。", self.font_key_md, COLOR_TEXT_MAIN)
            self._draw_left_text(draw, 56, 344, "• 激光瞄准与握持移动：手柄指到键盘自动出激光线，按住【握持键 Grip】即可在 VR 中随意拖拽放置。", self.font_key_md, COLOR_TEXT_ACCENT)

            draw.line([(56, 378), (WIDTH - 56, 378)], fill=COLOR_DIVIDER, width=1)

            # 清空个人自学习词频
            rst_dict_rect = (56, 396, 286, 438)
            self._draw_keycap(
                draw, rst_dict_rect, "重置个人输入法记忆", font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB, radius=8, shadow=False
            )
            self._add_button(rst_dict_rect, "reset_user_dict")

            # 激光引导线模式设置 (防 SteamVR 原生双线)
            laser_mode = state.get("laser_guide", "auto")
            is_vd = state.get("is_vd_active", False)
            if laser_mode == "auto":
                laser_lbl = "引导线: 智能(VD生效)" if is_vd else "引导线: 智能(SteamVR隐藏)"
                l_fill = COLOR_PRIMARY_SOFT if is_vd else COLOR_KEY_FUNC
                l_border = COLOR_BORDER_ACTIVE if is_vd else COLOR_KEY_FUNC_BORDER
                l_tc = COLOR_TEXT_ACCENT if is_vd else COLOR_TEXT_SUB
            elif laser_mode == "on":
                laser_lbl = "● 引导线: 强制开启"
                l_fill = COLOR_PRIMARY
                l_border = COLOR_PRIMARY_BORDER
                l_tc = (255, 255, 255, 255)
            else:
                laser_lbl = "○ 引导线: 强制关闭"
                l_fill = COLOR_KEY_FUNC
                l_border = COLOR_KEY_FUNC_BORDER
                l_tc = COLOR_TEXT_MUTED

            laser_mode_rect = (306, 396, 626, 438)
            self._draw_keycap(
                draw, laser_mode_rect, laser_lbl, font=self.font_key_sm,
                fill=l_fill, border=l_border, text_color=l_tc, radius=8, shadow=False
            )
            self._add_button(laser_mode_rect, "cycle_laser_mode")

        elif is_gemini:
            self._draw_left_text(draw, 56, 224, "1. Google Gemini API Key (复制后点击下方框体或粘贴按钮，直接导入 Key):", self.font_key_sm, COLOR_TEXT_SUB)
            g_key = state.get("google_api_key", "").strip()
            if g_key:
                masked = f"{g_key[:6]}••••••••{g_key[-4:]}" if len(g_key) > 10 else g_key
                key_display = f"已配置 Google Key: {masked}  (点击此框可重新粘贴替换)"
            else:
                key_display = "未填入 Key — 请在 Google AI Studio 复制 Key 后直接点击此处粘贴"

            key_box_rect = (56, 240, 650, 278)
            draw.rounded_rectangle(key_box_rect, radius=8, fill=COLOR_BG, outline=COLOR_BORDER_ACTIVE if g_key else COLOR_BORDER)
            self._draw_left_text(draw, 72, 259, key_display, self.font_key_sm, COLOR_TEXT_TRANS if g_key else COLOR_TEXT_MUTED)
            self._add_button(key_box_rect, "paste_google_key")

            paste_key_btn = (664, 240, 814, 278)
            self._draw_keycap(draw, paste_key_btn, "粘贴 Google Key", font=self.font_key_sm, fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255), radius=8, shadow=False)
            self._add_button(paste_key_btn, "paste_google_key")

            clear_key_btn = (826, 240, 936, 278)
            self._draw_keycap(draw, clear_key_btn, "清空Key", font=self.font_key_sm, fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_MUTED, radius=8, shadow=False)
            self._add_button(clear_key_btn, "clear_google_key")

            # 2. 模型切换与拉取
            cur_model = state.get("google_model", "gemini-1.5-flash")
            self._draw_left_text(draw, 56, 304, f"2. 当前模型: 【{cur_model}】", self.font_key_sm, COLOR_TEXT_MAIN)

            cycle_model_btn = (330, 286, 550, 322)
            self._draw_keycap(draw, cycle_model_btn, "⇄ 切换下一个模型", font=self.font_key_sm, fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False)
            self._add_button(cycle_model_btn, "cycle_google_model")

            fetch_model_btn = (564, 286, 820, 322)
            self._draw_keycap(draw, fetch_model_btn, "☁ 一键拉取可用模型列表", font=self.font_key_sm, fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER, text_color=(255, 255, 255, 255), radius=8, shadow=False)
            self._add_button(fetch_model_btn, "fetch_google_models")

            # 3. 提示词风格
            prompt_style = state.get("prompt_style", "google_vrc")
            is_gv = (prompt_style == "google_vrc")
            is_social = (prompt_style == "social")
            is_aggr = (prompt_style == "aggressive")

            self._draw_left_text(draw, 56, 350, "3. 翻译语气风格:", self.font_key_sm, COLOR_TEXT_SUB)

            gv_btn = (200, 334, 440, 370)
            self._draw_keycap(draw, gv_btn, "● VRC 游戏特调" if is_gv else "VRC 游戏特调", font=self.font_key_sm, fill=COLOR_PRIMARY if is_gv else COLOR_KEY_FUNC, border=COLOR_PRIMARY_BORDER if is_gv else COLOR_KEY_FUNC_BORDER, text_color=(255, 255, 255, 255) if is_gv else COLOR_TEXT_SUB, radius=8, shadow=False)
            self._add_button(gv_btn, "set_prompt_style", "google_vrc")

            social_btn = (454, 334, 680, 370)
            self._draw_keycap(draw, social_btn, "● 日常友好社交" if is_social else "日常友好社交", font=self.font_key_sm, fill=COLOR_SUCCESS if is_social else COLOR_KEY_FUNC, border=COLOR_SUCCESS_BORDER if is_social else COLOR_KEY_FUNC_BORDER, text_color=(255, 255, 255, 255) if is_social else COLOR_TEXT_SUB, radius=8, shadow=False)
            self._add_button(social_btn, "set_prompt_style", "social")

            aggr_btn = (694, 334, 936, 370)
            self._draw_keycap(draw, aggr_btn, "● 暴躁对线 / 俚语" if is_aggr else "暴躁对线 / 俚语", font=self.font_key_sm, fill=COLOR_DANGER if is_aggr else COLOR_KEY_FUNC, border=(255, 110, 120, 255) if is_aggr else COLOR_KEY_FUNC_BORDER, text_color=(255, 255, 255, 255) if is_aggr else COLOR_TEXT_SUB, radius=8, shadow=False)
            self._add_button(aggr_btn, "set_prompt_style", "aggressive")

            # 4. 横幅说明
            example_rect = (56, 386, WIDTH - 56, 446)
            draw.rounded_rectangle(example_rect, radius=8, fill=(20, 28, 42, 255), outline=COLOR_DIVIDER)
            self._draw_left_text(draw, 70, 404, "Google Gemini 官方大模型多模态语境 · 专为 3D 虚拟空间人际社交优化", self.font_tiny, COLOR_TEXT_ACCENT)
            self._draw_left_text(draw, 70, 426, "「这里有个人在跳舞」 ➔ \"Someone is breakdancing over here!\"  |  支持国内代理与海外直连", self.font_key_sm, COLOR_TEXT_TRANS)

        elif is_ds:
            self._draw_left_text(draw, 56, 224, "1. DeepSeek API Key (官网复制后，直接点击下方框体或按 Ctrl+V 即可粘贴):", self.font_key_sm, COLOR_TEXT_SUB)

            key_val = state.get("deepseek_api_key", "").strip()
            if key_val:
                masked = f"{key_val[:7]}••••••••{key_val[-4:]}" if len(key_val) > 12 else key_val
                key_display = f"已配置 Key: {masked}  (点击此框可重新粘贴替换)"
            else:
                key_display = "未填入 Key — 请复制 sk-... 后直接点击此处粘贴"

            key_box_rect = (56, 240, 650, 278)
            draw.rounded_rectangle(
                key_box_rect, radius=8, fill=COLOR_BG,
                outline=COLOR_BORDER_ACTIVE if key_val else COLOR_BORDER
            )
            self._draw_left_text(draw, 72, 259, key_display, self.font_key_sm, COLOR_TEXT_TRANS if key_val else COLOR_TEXT_MUTED)
            self._add_button(key_box_rect, "paste_api_key")

            paste_key_btn = (664, 240, 814, 278)
            self._draw_keycap(
                draw, paste_key_btn, "粘贴剪贴板Key", font=self.font_key_sm,
                fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255),
                radius=8, shadow=False
            )
            self._add_button(paste_key_btn, "paste_api_key")

            clear_key_btn = (826, 240, 936, 278)
            self._draw_keycap(
                draw, clear_key_btn, "清空Key", font=self.font_key_sm,
                fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_MUTED,
                radius=8, shadow=False
            )
            self._add_button(clear_key_btn, "clear_api_key")

            # --- 2. 翻译语气风格一键切换开关 ---
            prompt_style = state.get("prompt_style", "social")
            is_social = (prompt_style == "social")
            is_aggr = (prompt_style == "aggressive")
            is_custom = (prompt_style == "custom")

            self._draw_left_text(draw, 56, 304, "2. 翻译语气风格:", self.font_key_sm, COLOR_TEXT_SUB)

            social_btn = (190, 286, 456, 322)
            self._draw_keycap(
                draw, social_btn,
                "● 日常正常社交 (礼貌自然)" if is_social else "日常正常社交 (礼貌自然)",
                font=self.font_key_sm,
                fill=COLOR_SUCCESS if is_social else COLOR_KEY_FUNC,
                border=COLOR_SUCCESS_BORDER if is_social else COLOR_KEY_FUNC_BORDER,
                text_color=(255, 255, 255, 255) if is_social else COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(social_btn, "set_prompt_style", "social")

            aggr_btn = (468, 286, 744, 322)
            self._draw_keycap(
                draw, aggr_btn,
                "● 暴躁对线 / 喷人 (俚语无审查)" if is_aggr else "暴躁对线 / 喷人 (俚语无审查)",
                font=self.font_key_sm,
                fill=COLOR_DANGER if is_aggr else COLOR_KEY_FUNC,
                border=(255, 110, 120, 255) if is_aggr else COLOR_KEY_FUNC_BORDER,
                text_color=(255, 255, 255, 255) if is_aggr else COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(aggr_btn, "set_prompt_style", "aggressive")

            custom_btn = (756, 286, 936, 322)
            self._draw_keycap(
                draw, custom_btn,
                "● 粘贴自定义词" if is_custom else "粘贴自定义提示词",
                font=self.font_key_sm,
                fill=COLOR_PRIMARY if is_custom else COLOR_KEY_FUNC,
                border=COLOR_PRIMARY_BORDER if is_custom else COLOR_KEY_FUNC_BORDER,
                text_color=(255, 255, 255, 255) if is_custom else COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(custom_btn, "paste_custom_prompt")

            # --- 3. 实时风格效果对比示例横幅 ---
            example_rect = (56, 330, WIDTH - 56, 374)
            draw.rounded_rectangle(example_rect, radius=8, fill=(20, 28, 42, 255), outline=COLOR_DIVIDER)
            if is_social:
                ex_title = "当前风格效果示例 [日常社交 · 温和得体，绝不乱加粗口]:"
                ex_body = "「什么东西飘过去了？」 ->  \"What just floated by?\"    |    「你在干嘛？」 ->  \"What are you up to?\""
                ex_col = COLOR_TEXT_TRANS
            elif is_aggr:
                ex_title = "当前风格效果示例 [暴躁对线 · 美式俚语拉满，硬核无审查]:"
                ex_body = "「什么东西飘过去了？」 ->  \"What the hell just floated by?\"    |    「烦死了」 ->  \"So fucking annoying.\""
                ex_col = (255, 138, 148, 255)
            else:
                ex_title = "当前风格 [用户自定义 System Prompt]:"
                ex_body = "点击下方提示词框或上方按钮可随时切换回预设风格"
                ex_col = COLOR_TEXT_ACCENT

            self._draw_left_text(draw, 70, 342, ex_title, self.font_tiny, COLOR_TEXT_MUTED)
            self._draw_left_text(draw, 70, 360, ex_body, self.font_key_sm, ex_col)

            # --- 4. 内置提示词预览框 ---
            self._draw_left_text(draw, 56, 388, "3. 当前生效系统提示词 Prompt (点击框体可粘贴自定义):", self.font_tiny, COLOR_TEXT_MUTED)

            cur_prompt = state.get("system_prompt", "").strip()
            prompt_box_rect = (56, 402, WIDTH - 56, 464)
            draw.rounded_rectangle(prompt_box_rect, radius=8, fill=COLOR_BG, outline=COLOR_BORDER)

            wrapped_lines = textwrap.wrap(cur_prompt, width=86)[:2]
            for idx, line_str in enumerate(wrapped_lines):
                if idx == 1 and len(cur_prompt) > 165:
                    line_str = line_str[:82] + "..."
                self._draw_left_text(draw, 72, 420 + idx * 22, line_str, self.font_code, COLOR_TEXT_SUB)
            self._add_button(prompt_box_rect, "paste_custom_prompt")

        # --- 底部常驻栏：VR 键盘尺寸调节 + 激光引导线模式切换 (防SteamVR双线) + 呼出热键切换 ---
        vr_bar_rect = (32, 482, WIDTH - 32, 536)
        draw.rounded_rectangle(vr_bar_rect, radius=10, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)

        cur_w = float(state.get("overlay_width_m", 0.42))
        cur_w = max(0.25, min(0.85, cur_w))
        pct = int(round((cur_w / 0.42) * 100))
        self._draw_left_text(draw, 44, 509, f"大小:{cur_w:.2f}m", self.font_tiny, COLOR_TEXT_ACCENT)

        # [- 缩小] 按钮
        minus_rect = (136, 491, 186, 527)
        self._draw_keycap(
            draw, minus_rect, "- 缩小", font=self.font_tiny,
            fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_MAIN, radius=7, shadow=False
        )
        self._add_button(minus_rect, "adjust_vr_width", -0.04)

        # 可拖拽尺寸滑块轨道 (x: 196..416, 对应 0.25m ~ 0.85m)
        slider_x1, slider_x2 = 196, 416
        slider_cy = 509
        track_rect = (slider_x1, slider_cy - 6, slider_x2, slider_cy + 6)
        draw.rounded_rectangle(track_rect, radius=6, fill=COLOR_BG, outline=COLOR_BORDER)

        ratio = (cur_w - 0.25) / (0.85 - 0.25)
        knob_x = int(slider_x1 + ratio * (slider_x2 - slider_x1))
        if knob_x > slider_x1 + 4:
            draw.rounded_rectangle((slider_x1, slider_cy - 6, knob_x, slider_cy + 6), radius=6, fill=COLOR_PRIMARY)
        # 滑块圆柄
        draw.ellipse((knob_x - 11, slider_cy - 11, knob_x + 11, slider_cy + 11), fill=(255, 255, 255, 255), outline=COLOR_PRIMARY_BORDER, width=3)
        self._add_button((slider_x1 - 8, 486, slider_x2 + 8, 532), "vr_size_slider", (slider_x1, slider_x2))

        # [+ 放大] 按钮
        plus_rect = (426, 491, 476, 527)
        self._draw_keycap(
            draw, plus_rect, "+ 放大", font=self.font_tiny,
            fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_MAIN, radius=7, shadow=False
        )
        self._add_button(plus_rect, "adjust_vr_width", 0.04)

        # [标准]
        reset_w_rect = (486, 491, 546, 527)
        self._draw_keycap(
            draw, reset_w_rect, "标准", font=self.font_tiny,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB, radius=7, shadow=False
        )
        self._add_button(reset_w_rect, "set_vr_width_exact", 0.42)

        # [激光引导线切换：防 SteamVR 原生双线]
        laser_mode = state.get("laser_guide", "auto")
        is_vd = state.get("is_vd_active", False)
        if laser_mode == "auto":
            laser_lbl = "引导: 智能(VD生效)" if is_vd else "引导: 智能(SteamVR隐藏)"
            l_fill = COLOR_PRIMARY_SOFT if is_vd else COLOR_KEY_FUNC
            l_border = COLOR_BORDER_ACTIVE if is_vd else COLOR_KEY_FUNC_BORDER
            l_tc = COLOR_TEXT_ACCENT if is_vd else COLOR_TEXT_SUB
        elif laser_mode == "on":
            laser_lbl = "● 引导: 强制开启"
            l_fill = COLOR_PRIMARY
            l_border = COLOR_PRIMARY_BORDER
            l_tc = (255, 255, 255, 255)
        else:
            laser_lbl = "○ 引导: 强制关闭"
            l_fill = COLOR_KEY_FUNC
            l_border = COLOR_KEY_FUNC_BORDER
            l_tc = COLOR_TEXT_MUTED

        laser_rect = (556, 491, 746, 527)
        self._draw_keycap(
            draw, laser_rect, laser_lbl, font=self.font_tiny,
            fill=l_fill, border=l_border, text_color=l_tc, radius=7, shadow=False
        )
        self._add_button(laser_rect, "cycle_laser_mode")

        # [VR 呼出热键手势切换]
        cur_hand = state.get("hotkey_controller", "right")
        hand_map = {"right": "右手摇杆双击", "left": "左手摇杆双击"}
        hand_label = hand_map.get(cur_hand, "右手摇杆双击")
        h_rect = (756, 491, 956, 527)
        self._draw_keycap(
            draw, h_rect, f"呼出: {hand_label}", font=self.font_tiny,
            fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_MAIN, radius=7, shadow=False
        )
        self._add_button(h_rect, "toggle_vr_hand")
