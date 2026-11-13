import os
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Any, Optional

WIDTH = 1000
HEIGHT = 560

# ==============================================================================
# Spatial Cyber-Glass 配色体系 (高对比立体质感 + 柔和护眼暗色调)
# ==============================================================================
COLOR_BG = (8, 10, 17, 252)              # 深空夜幕底色 (#080a11)
COLOR_BG_BORDER = (46, 62, 92, 255)      # 外框玻璃微光边线
COLOR_BG_INNER_RIM = (26, 36, 56, 200)   # 内层玻璃折射边

COLOR_SURFACE = (15, 20, 34, 248)        # 主卡片容器 (#0f1422)
COLOR_SURFACE_LIGHT = (21, 28, 46, 255)  # 浅层卡片 (#151c2e)
COLOR_SURFACE_INNER = (10, 13, 23, 255)  # 内嵌深槽 (#0a0d17)
COLOR_DIVIDER = (30, 40, 62, 255)        # 柔和分割线
COLOR_BORDER = (40, 52, 78, 255)         # 常规描边
COLOR_BORDER_ACTIVE = (56, 189, 248, 255)# 激活态天青蓝 (#38bdf8)

# 立体键帽层次配色
COLOR_KEY_SHADOW = (4, 6, 10, 255)       # 键帽实体底座阴影
COLOR_KEY = (25, 33, 52, 255)            # 主字母键帽 (#192134)
COLOR_KEY_BORDER = (48, 63, 94, 255)     # 键帽边缘描边
COLOR_KEY_FUNC = (17, 23, 38, 255)       # 功能键帽 (#111726)
COLOR_KEY_FUNC_BORDER = (36, 48, 74, 255)

# 语义强调色
COLOR_PRIMARY = (29, 132, 224, 255)      # 科技天青蓝 (#1d84e0)
COLOR_PRIMARY_BORDER = (82, 198, 255, 255)
COLOR_PRIMARY_SOFT = (18, 44, 78, 255)   # 柔和天青蓝底

COLOR_SUCCESS = (16, 172, 120, 255)      # 翡翠薄荷绿 (#10ac78)
COLOR_SUCCESS_BORDER = (52, 219, 162, 255)
COLOR_SUCCESS_SOFT = (14, 52, 42, 255)

COLOR_WARNING = (230, 155, 45, 255)      # 琥珀暖橙
COLOR_WARNING_SOFT = (52, 36, 16, 255)

COLOR_DANGER = (215, 48, 82, 255)        # 珊瑚红 (#d73052)
COLOR_DANGER_SOFT = (50, 20, 30, 255)

# 优雅暗红键帽配色 (删除键)
COLOR_DELETE_BG = (54, 21, 31, 255)
COLOR_DELETE_BORDER = (118, 44, 60, 255)
COLOR_DELETE_TEXT = (255, 188, 198, 255)

# 文本层级色
COLOR_TEXT_MAIN = (248, 250, 252, 255)   # 主文字：纯白
COLOR_TEXT_SUB = (162, 179, 206, 255)    # 次级文字
COLOR_TEXT_MUTED = (108, 124, 150, 255)  # 弱提示文字
COLOR_TEXT_ACCENT = (76, 198, 255, 255)  # 天青蓝高亮字
COLOR_TEXT_TRANS = (58, 222, 162, 255)   # 译文薄荷绿字

LANG_SHORT_NAME_MAP = {
    "zh": "中", "en": "英", "ja": "日", "ko": "韩",
    "ru": "俄", "fr": "法", "de": "德", "es": "西"
}

LANG_FULL_NAME_MAP = {
    "zh": "中文", "en": "英语", "ja": "日语", "ko": "韩语",
    "ru": "俄语", "fr": "法语", "de": "德语", "es": "西语"
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
    "卖萌": "Cute",
    "开心": "Happy",
    "难过": "Sad",
    "生气/对线": "Angry",
    "问候/告别": "Hello",
    "摸鱼/日常": "Relax"
}

UI_STRINGS = {
    "zh": {
        "send_trans": "发送译文",
        "phrases": "常用语",
        "settings": "设置",
        "back": "返回",
        "save_return": "完成返回",
        "test_conn": "测试连接",
        "settings_title": "系统与控制中心",
        "tab_engine": "翻译引擎",
        "tab_engine_sub": "通道 · 代理 · 口吻",
        "tab_input": "语言与输入",
        "tab_input_sub": "互译 · 发送 · 词库",
        "tab_vr": "空间与引导",
        "tab_vr_sub": "尺寸 · 激光 · 热键",
        "ui_lang_btn": "界面: 简体中文",
        "net_global": "海外直连 (免代理)",
        "net_mainland": "中国大陆 (走代理)",
        "eng_free": "免费极速通道",
        "eng_google": "Google 官方翻译",
        "eng_gemini": "Google Gemini AI",
        "eng_deepseek": "DeepSeek 大模型",
        "lang_pair_title": "互译方向",
        "zh2en": "中 → 英 (EN)",
        "zh2ja": "中 → 日 (JA)",
        "zh2ko": "中 → 韩 (KO)",
        "zh2ru": "中 → 俄 (RU)",
        "en2zh": "英 → 中 (ZH)",
        "send_mode_title": "发送译文模式",
        "send_trans_only": "仅发译文",
        "send_bilingual": "双语对照",
        "send_orig_only": "仅发原文",
        "reset_dict": "重置输入记忆",
        "init_zh": "默认输入: 中文拼音",
        "init_en": "默认输入: 英文直出",
        "zoom_in": "+ 放大",
        "zoom_out": "- 缩小",
        "zoom_std": "标准 0.42m",
        "guide_auto": "智能识别 (VD开启/原生隐藏)",
        "guide_on": "强制开启引导线",
        "guide_off": "强制关闭引导线",
        "call_key_r": "呼出热键: 右手摇杆双击",
        "call_key_l": "呼出热键: 左手摇杆双击",
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
        "symbols": "#+= 符",
        "numbers": "123",
        "paste_key": "粘贴 Key",
        "clear_key": "清除 Key",
        "cycle_model": "切换模型",
        "fetch_model": "拉取官方列表",
        "cycle_ds_model": "切换模型",
        "style_title": "AI 口吻风格",
        "style_social": "友好社交",
        "style_aggro": "游戏对线",
        "style_custom": "自定义",
        "paste_custom": "粘贴提示词",
        "reset_default": "恢复默认",
        "placeholder_zh": "点按键盘或直接敲击输入中文拼音...",
        "placeholder_en": "当前为直接输入模式 (英文直出)...",
        "preview_empty": "实时译文预览",
        "quick": "快捷词",
        "phrases_title": "常用语快捷面板 (点击词条填入，或点击右侧直发)",
        "save_current": "+ 存入当前",
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
        "save_return": "Done & Back",
        "test_conn": "Test API",
        "settings_title": "Control Center",
        "tab_engine": "Translation",
        "tab_engine_sub": "Engine · Proxy · Tone",
        "tab_input": "Language & Input",
        "tab_input_sub": "Pairs · Send · Dict",
        "tab_vr": "VR & Display",
        "tab_vr_sub": "Scale · Laser · Hotkey",
        "ui_lang_btn": "UI: English",
        "net_global": "Global Direct",
        "net_mainland": "China Proxy",
        "eng_free": "Free Direct",
        "eng_google": "Google Translate",
        "eng_gemini": "Google Gemini AI",
        "eng_deepseek": "DeepSeek AI",
        "lang_pair_title": "Language Pair",
        "zh2en": "ZH → EN",
        "zh2ja": "ZH → JA",
        "zh2ko": "ZH → KO",
        "zh2ru": "ZH → RU",
        "en2zh": "EN → ZH",
        "send_mode_title": "Send Output Mode",
        "send_trans_only": "Trans Only",
        "send_bilingual": "Bilingual",
        "send_orig_only": "Orig Only",
        "reset_dict": "Reset User Dict",
        "init_zh": "Default: Pinyin (ZH)",
        "init_en": "Default: Direct (EN)",
        "zoom_in": "+ Larger",
        "zoom_out": "- Smaller",
        "zoom_std": "Std 0.42m",
        "guide_auto": "Smart (VD On / Native Off)",
        "guide_on": "Force Laser On",
        "guide_off": "Force Laser Off",
        "call_key_r": "Hotkey: Double-Click R-Stick",
        "call_key_l": "Hotkey: Double-Click L-Stick",
        "caps": "Caps",
        "bksp": "Del",
        "enter": "Enter",
        "enter_en": "Enter(EN)",
        "space": "Space",
        "space_cand": "Space (Select #1)",
        "send_orig": "Send Orig",
        "history": "Last",
        "paste": "Paste",
        "clear": "Clear",
        "letters": "Letters",
        "letters_long": "Back to Letters",
        "symbols": "#+=",
        "numbers": "123",
        "paste_key": "Paste Key",
        "clear_key": "Clear Key",
        "cycle_model": "Switch Model",
        "fetch_model": "Fetch Models",
        "cycle_ds_model": "Switch Model",
        "style_title": "AI Tone Style",
        "style_social": "Friendly",
        "style_aggro": "Sarcastic",
        "style_custom": "Custom",
        "paste_custom": "Paste Prompt",
        "reset_default": "Reset",
        "placeholder_zh": "Type Pinyin or tap keys below...",
        "placeholder_en": "Direct Typing Mode (English)...",
        "preview_empty": "Live Translation Preview",
        "quick": "Quick",
        "phrases_title": "Phrases Panel (Tap to insert, or send directly)",
        "save_current": "+ Save Current",
        "manage_phrases": "Manage",
        "done_manage": "Done",
        "send_trans_sm": "Trans",
        "send_orig_sm": "Orig",
        "back_kb": "Back to Keys",
    }
}


def _clamp_rgb(v: int) -> int:
    return 0 if v < 0 else (255 if v > 255 else v)


def _shift_color(rgba: Tuple[int, int, int, int], delta: int) -> Tuple[int, int, int, int]:
    return (
        _clamp_rgb(rgba[0] + delta),
        _clamp_rgb(rgba[1] + delta),
        _clamp_rgb(rgba[2] + delta),
        rgba[3] if len(rgba) > 3 else 255
    )


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
                self.font_title = ImageFont.truetype(chosen_font, 18)
                self.font_main = ImageFont.truetype(chosen_font, 19)
                self.font_key = ImageFont.truetype(chosen_font, 23)
                self.font_key_md = ImageFont.truetype(chosen_font, 17)
                self.font_key_sm = ImageFont.truetype(chosen_font, 15)
                self.font_tiny = ImageFont.truetype(chosen_font, 13)
                self.font_preview = ImageFont.truetype(chosen_font, 22)
                self.font_trans = ImageFont.truetype(chosen_font, 18)
                self.font_cand = ImageFont.truetype(chosen_font, 18)
                self.font_code = ImageFont.truetype(chosen_font, 14)
            else:
                raise FileNotFoundError("No chinese font found")
        except Exception:
            default_f = ImageFont.load_default()
            self.font_title = self.font_main = self.font_key = self.font_key_md = self.font_key_sm = self.font_tiny = self.font_preview = self.font_trans = self.font_cand = self.font_code = default_f

        self.cached_clickables: List[Tuple[Tuple[int, int, int, int], str, Any]] = []
        self._hover_rect: Optional[Tuple[int, int, int, int]] = None
        self._pressed_rect: Optional[Tuple[int, int, int, int]] = None
        self._bg_cache = self._build_background_cache()

    def _build_background_cache(self) -> Image.Image:
        """预渲染高质感渐变底图与空间光晕 (仅在初始化执行一次，运行时零开销)"""
        bg = Image.new("RGBA", (WIDTH, HEIGHT), COLOR_BG)
        px = bg.load()
        # 纵向渐变 (#0b0f1b -> #070911)
        for y in range(HEIGHT):
            t = y / float(HEIGHT - 1)
            r = int(12 - 5 * t)
            g = int(16 - 7 * t)
            b = int(28 - 12 * t)
            for x in range(WIDTH):
                px[x, y] = (r, g, b, 252)

        # 叠加柔和空间极光微光 (左上天青蓝 + 右下翡翠青)
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for i in range(12, 0, -1):
            rad_x = i * 32
            rad_y = i * 16
            alpha = int(3 * (13 - i) / 12)
            gd.ellipse((140 - rad_x, 30 - rad_y, 140 + rad_x, 30 + rad_y), fill=(38, 160, 245, alpha))
            gd.ellipse((WIDTH - 140 - rad_x, HEIGHT - 30 - rad_y, WIDTH - 140 + rad_x, HEIGHT - 30 + rad_y), fill=(16, 185, 135, alpha))
        bg = Image.alpha_composite(bg, glow)

        # 玻璃外框双层描边 + 顶部空间抓取把手
        d = ImageDraw.Draw(bg)
        d.rounded_rectangle([(1, 1), (WIDTH - 2, HEIGHT - 2)], radius=18, outline=COLOR_BG_BORDER, width=2)
        d.rounded_rectangle([(3, 3), (WIDTH - 4, HEIGHT - 4)], radius=16, outline=COLOR_BG_INNER_RIM, width=1)

        # 顶部中央抓取把手 + 两侧微光点
        d.rounded_rectangle([(WIDTH // 2 - 48, 5), (WIDTH // 2 + 48, 9)], radius=2, fill=(72, 168, 235, 180))
        d.ellipse((WIDTH // 2 - 60, 5, WIDTH // 2 - 56, 9), fill=(56, 189, 248, 130))
        d.ellipse((WIDTH // 2 + 56, 5, WIDTH // 2 + 60, 9), fill=(56, 189, 248, 130))
        return bg

    def _t(self, state: dict, key: str, default: str = "") -> str:
        lang = state.get("ui_lang", "zh") if isinstance(state, dict) else "zh"
        return UI_STRINGS.get(lang, {}).get(key, default or key)

    def _add_button(self, rect: Tuple[int, int, int, int], action: str, data: Any = None):
        self.cached_clickables.append((rect, action, data))

    def _draw_centered_text(self, draw: ImageDraw.Draw, rect: Tuple[int, int, int, int], text: str, font, fill):
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
        sub_label: str = None, underline: bool = False,
        led_active: Optional[bool] = None
    ):
        """绘制 3D 机械玻璃态键帽，自动响应悬停高亮与物理按压下沉反馈"""
        is_pressed = (self._pressed_rect == rect)
        is_hovered = (self._hover_rect == rect) and not is_pressed

        x1, y1, x2, y2 = rect
        draw_fill = fill
        draw_border = border
        border_w = 1

        if is_pressed:
            # 物理按压：键帽下沉 2px，阴影变薄，高光闪烁
            y1 += 2
            y2 += 2
            draw_fill = _shift_color(fill, 28)
            draw_border = (130, 222, 255, 255)
            border_w = 2
            shadow_off = 2
        elif is_hovered:
            # 激光/鼠标悬停：键帽提亮，天青蓝发光边框
            draw_fill = _shift_color(fill, 15)
            draw_border = (78, 204, 255, 255)
            border_w = 2
            shadow_off = 4
        else:
            shadow_off = 4

        # 1. 实体键帽底座阴影
        if shadow:
            draw.rounded_rectangle([(x1, y1 + shadow_off), (x2, y2 + shadow_off)], radius=radius, fill=COLOR_KEY_SHADOW)

        # 2. 键帽主体
        draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=radius, fill=draw_fill, outline=draw_border, width=border_w)

        # 3. 顶部高光折射边线 (1px 玻璃感)
        if x2 - x1 > radius * 2 + 8:
            hl_col = (190, 235, 255, 95) if (is_hovered or is_pressed) else (255, 255, 255, 34)
            draw.line([(x1 + radius, y1 + 1), (x2 - radius, y1 + 1)], fill=hl_col, width=1)

        # 4. 居中主标签
        self._draw_centered_text(draw, (x1, y1, x2, y2), label, font, text_color)

        # 5. 右上角微缩数字角标 (淡青色更清晰)
        if sub_label:
            self._draw_centered_text(draw, (x2 - 17, y1 + 7, x2 - 5, y1 + 19), sub_label, self.font_tiny, (118, 165, 205, 200))

        # 6. F / J 定位发光条
        if underline:
            cx = (x1 + x2) // 2
            draw.rounded_rectangle([(cx - 11, y2 - 11), (cx + 11, y2 - 8)], radius=1, fill=COLOR_BORDER_ACTIVE)

        # 7. Caps / 状态指示灯小圆点
        if led_active is not None:
            led_col = (72, 235, 185, 255) if led_active else (55, 68, 92, 255)
            draw.ellipse((x1 + 10, y1 + 10, x1 + 17, y1 + 17), fill=led_col)

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
            return text
        except Exception:
            return text

    def render(self, state: dict) -> Tuple[Image.Image, List[Tuple[Tuple[int, int, int, int], str, Any]]]:
        """渲染完整键盘画面并返回可点击热区列表"""
        img = self._bg_cache.copy()
        draw = ImageDraw.Draw(img)
        self.cached_clickables = []
        self._hover_rect = state.get("_hover_rect")
        self._pressed_rect = state.get("_pressed_rect")

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

        # 全局瞬时 Toast 反馈浮层
        toast_msg = state.get("_toast_msg", "")
        if toast_msg:
            self._render_toast(draw, toast_msg, state.get("_toast_type", "info"))

        return img, self.cached_clickables

    def _render_toast(self, draw: ImageDraw.Draw, msg: str, toast_type: str = "info"):
        """顶部优雅悬浮状态提示条"""
        if toast_type == "success":
            bg, bd, tc = (14, 56, 42, 245), COLOR_SUCCESS_BORDER, (215, 255, 238, 255)
        elif toast_type == "warn":
            bg, bd, tc = (58, 38, 16, 245), COLOR_WARNING, (255, 225, 165, 255)
        else:
            bg, bd, tc = (16, 44, 78, 245), COLOR_BORDER_ACTIVE, (215, 242, 255, 255)

        tb = self.font_key_sm.getbbox(msg)
        tw = (tb[2] - tb[0]) + 40
        tw = max(180, min(680, tw))
        x1 = (WIDTH - tw) // 2
        x2 = x1 + tw
        rect = (x1, 12, x2, 48)
        draw.rounded_rectangle([(x1, 14), (x2, 50)], radius=18, fill=(0, 0, 0, 140))
        draw.rounded_rectangle(rect, radius=18, fill=bg, outline=bd, width=2)
        self._draw_centered_text(draw, rect, msg, self.font_key_sm, tc)

    def _render_top_bar(self, draw: ImageDraw.Draw, state: dict):
        """第一行 (y: 16..64)：双向语言胶囊 + 实时译文预览 + 发送译文 + 常用语 / 设置 / 关闭"""
        y1, y2 = 16, 64
        cy = (y1 + y2) // 2

        source_lang = state.get("source_lang", "zh")
        target_lang = state.get("target_lang", "en")
        s_name = LANG_SHORT_NAME_MAP.get(source_lang, source_lang.upper())
        t_name = LANG_SHORT_NAME_MAP.get(target_lang, target_lang.upper())
        lang_text = f"{s_name} → {t_name}"

        lang_rect = (16, y1, 124, y2)
        self._draw_keycap(
            draw, lang_rect, lang_text, font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE,
            text_color=COLOR_TEXT_ACCENT, radius=11, shadow=True
        )
        self._add_button(lang_rect, "cycle_lang_pair")

        # 实时译文显示舱
        trans_rect = (132, y1, 666, y2)
        trans_text = state.get("translated_text", "").strip()
        draw.rounded_rectangle(trans_rect, radius=11, fill=COLOR_SURFACE_INNER, outline=COLOR_SUCCESS_BORDER if trans_text else COLOR_BORDER, width=1)

        dot_color = COLOR_SUCCESS_BORDER if trans_text else (64, 78, 104, 255)
        draw.ellipse((146, cy - 4, 154, cy + 4), fill=dot_color)

        if trans_text:
            fitted_trans = self._truncate_left_to_fit(trans_text, self.font_trans, 492)
            self._draw_left_text(draw, 164, cy, fitted_trans, self.font_trans, COLOR_TEXT_TRANS)
        else:
            engine = state.get("engine", "google_official")
            eng_names = {
                "google_official": "Google 官方" if state.get("ui_lang", "zh") == "zh" else "Google",
                "google_gemini": "Gemini AI",
                "deepseek": "DeepSeek AI",
                "free_direct": "免费极速" if state.get("ui_lang", "zh") == "zh" else "Free Direct"
            }
            eng_tag = eng_names.get(engine, engine)
            preview_hint = self._t(state, "preview_empty", "实时译文预览")
            self._draw_left_text(draw, 164, cy, f"{preview_hint} · {eng_tag}", self.font_key_sm, COLOR_TEXT_MUTED)

        # 发送译文主按钮
        send_trans_rect = (674, y1, 790, y2)
        self._draw_keycap(
            draw, send_trans_rect, self._t(state, "send_trans", "发送译文"), font=self.font_key_sm,
            fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER,
            text_color=(255, 255, 255, 255), radius=11, shadow=True
        )
        self._add_button(send_trans_rect, "send_translated")

        active_modal = state.get("active_modal")

        phrase_rect = (798, y1, 870, y2)
        is_ph = (active_modal == "phrases")
        self._draw_keycap(
            draw, phrase_rect, self._t(state, "phrases", "常用语"), font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_ph else COLOR_SURFACE_LIGHT,
            border=COLOR_PRIMARY_BORDER if is_ph else COLOR_BORDER,
            text_color=(255, 255, 255, 255) if is_ph else COLOR_TEXT_SUB,
            radius=11, shadow=True
        )
        self._add_button(phrase_rect, "toggle_modal", "phrases")

        settings_rect = (878, y1, 938, y2)
        is_st = (active_modal == "settings")
        self._draw_keycap(
            draw, settings_rect, self._t(state, "settings", "设置"), font=self.font_key_sm,
            fill=COLOR_PRIMARY if is_st else COLOR_SURFACE_LIGHT,
            border=COLOR_PRIMARY_BORDER if is_st else COLOR_BORDER,
            text_color=(255, 255, 255, 255) if is_st else COLOR_TEXT_SUB,
            radius=11, shadow=True
        )
        self._add_button(settings_rect, "toggle_modal", "settings")

        close_rect = (946, y1, 984, y2)
        self._draw_keycap(
            draw, close_rect, "×", font=self.font_key,
            fill=COLOR_DANGER_SOFT, border=(122, 46, 62, 255),
            text_color=(255, 130, 145, 255), radius=11, shadow=True
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

        icy = 101
        bar_col = COLOR_BORDER_ACTIVE if has_content else (56, 70, 96, 255)
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
                pw = (py_bbox[2] - py_bbox[0]) + 22
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
                placeholder = self._t(state, "placeholder_zh", "点按键盘或直接敲击输入中文拼音...")
            else:
                placeholder = self._t(state, "placeholder_en", f"直接输入模式 ({LANG_FULL_NAME_MAP.get(source_lang, '原文')})")
            self._draw_left_text(draw, cur_x, icy, placeholder, self.font_key_md, COLOR_TEXT_MUTED)
            draw.line([(cur_x, icy - 12), (cur_x, icy + 12)], fill=(70, 88, 115, 255), width=2)

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
                    text_color=(255, 255, 255, 255) if is_first else COLOR_TEXT_MAIN,
                    radius=9, shadow=False
                )
                self._add_button(cand_rect, "select_candidate", i)
                cur_cx += item_w + gap

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
            offset_x = 112 if ui_lang == "en" else 92
            idle_chips = QUICK_IDLE_CHIPS_EN if ui_lang == "en" else QUICK_IDLE_CHIPS
            for chip in idle_chips:
                cb = self.font_key_sm.getbbox(chip)
                cw = max(56, (cb[2] - cb[0]) + 30)
                if offset_x + cw > WIDTH - 28:
                    break
                chip_rect = (offset_x, 141, offset_x + cw, 177)
                self._draw_keycap(
                    draw, chip_rect, chip, font=self.font_key_sm,
                    fill=COLOR_KEY, border=COLOR_KEY_BORDER,
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
        """主键盘：立体 26 键布局 (y: 198..542)"""
        is_shift = state.get("is_shift", False)
        is_caps = state.get("is_caps", False)
        has_pinyin = bool(state.get("pinyin_buffer", ""))

        row1 = ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"]
        row1_nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        row2 = ["a", "s", "d", "f", "g", "h", "j", "k", "l"]
        row3 = ["z", "x", "c", "v", "b", "n", "m"]

        key_h = 77
        gap = 10
        start_y = 198
        w_key = 88

        # Row 1: Q - P
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

        # Row 2: A - L
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

        # Row 3: [大写] + Z - M + [删除] + [回车]
        y += key_h + gap
        caps_w = 98
        caps_rect = (16, y, 16 + caps_w, y + key_h)
        caps_active = is_caps or is_shift
        self._draw_keycap(
            draw, caps_rect, self._t(state, "caps", "大写"), font=self.font_key_md,
            fill=COLOR_PRIMARY_SOFT if caps_active else COLOR_KEY_FUNC,
            border=COLOR_PRIMARY_BORDER if caps_active else COLOR_KEY_FUNC_BORDER,
            text_color=(255, 255, 255, 255) if caps_active else COLOR_TEXT_SUB,
            led_active=caps_active
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

        # Row 4
        y += key_h + gap
        r_123 = (16, y, 96, y + key_h)
        self._draw_keycap(
            draw, r_123, self._t(state, "numbers", "123"), font=self.font_key_md,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB
        )
        self._add_button(r_123, "switch_keyboard", "numbers")

        r_sym = (104, y, 184, y + key_h)
        self._draw_keycap(
            draw, r_sym, self._t(state, "symbols", "#+= 符"), font=self.font_key_sm,
            fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB
        )
        self._add_button(r_sym, "switch_keyboard", "symbols")

        r_kao = (192, y, 276, y + key_h)
        self._draw_keycap(
            draw, r_kao, "(^_^)", font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT
        )
        self._add_button(r_kao, "switch_keyboard", "kaomoji")

        r_comma = (284, y, 340, y + key_h)
        self._draw_keycap(draw, r_comma, "，", font=self.font_key)
        self._add_button(r_comma, "insert_char", "，")

        r_space = (348, y, 618, y + key_h)
        space_label = self._t(state, "space_cand", "空格 (选首选词)") if has_pinyin else self._t(state, "space", "空  格")
        self._draw_keycap(
            draw, r_space, space_label, font=self.font_key_md,
            fill=COLOR_PRIMARY_SOFT if has_pinyin else COLOR_KEY,
            border=COLOR_BORDER_ACTIVE if has_pinyin else COLOR_KEY_BORDER,
            text_color=COLOR_TEXT_ACCENT if has_pinyin else COLOR_TEXT_SUB
        )
        self._add_button(r_space, "key_space")

        r_dot = (626, y, 682, y + key_h)
        self._draw_keycap(draw, r_dot, "。", font=self.font_key)
        self._add_button(r_dot, "insert_char", "。")

        r_ime = (690, y, 826, y + key_h)
        cur_src = state.get("source_lang", "zh")
        cur_tgt = state.get("target_lang", "en")
        ui_l = state.get("ui_lang", "zh")
        if cur_src == "zh":
            t_short = LANG_SHORT_NAME_MAP.get(cur_tgt, cur_tgt.upper()) if ui_l == "zh" else cur_tgt.upper()
            ime_label = f"中 → {t_short}"
        else:
            ime_label = "英 → 中" if ui_l == "zh" else "EN → ZH"
        self._draw_keycap(
            draw, r_ime, ime_label, font=self.font_key_md,
            fill=COLOR_PRIMARY_SOFT if cur_src == "zh" else COLOR_KEY_FUNC,
            border=COLOR_BORDER_ACTIVE if cur_src == "zh" else COLOR_KEY_FUNC_BORDER,
            text_color=COLOR_TEXT_ACCENT if cur_src == "zh" else COLOR_TEXT_SUB
        )
        self._add_button(r_ime, "cycle_lang_pair")

        r_send_orig = (834, y, WIDTH - 16, y + key_h)
        self._draw_keycap(
            draw, r_send_orig, self._t(state, "send_orig", "发原文"), font=self.font_key_md,
            fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER,
            text_color=(255, 255, 255, 255)
        )
        self._add_button(r_send_orig, "send_original")

    def _render_numbers_panel(self, draw: ImageDraw.Draw, state: dict):
        self._render_grid_panel(draw, state, [
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            ["-", "/", ":", ";", "(", ")", "$", "&", "@", "\""],
            [".", ",", "?", "!", "'", "%", "+", "=", "*", "_"],
            ["返回字母", "空格", "删除", "回车"]
        ])

    def _render_symbols_panel(self, draw: ImageDraw.Draw, state: dict):
        self._render_grid_panel(draw, state, [
            ["[", "]", "{", "}", "#", "%", "^", "*", "+", "="],
            ["_", "\\", "|", "~", "<", ">", "$", "￥", "€", "·"],
            ["“", "”", "‘", "’", "《", "》", "【", "】", "…", "—"],
            ["返回字母", "空格", "删除", "回车"]
        ])

    def _render_grid_panel(self, draw: ImageDraw.Draw, state: dict, rows: list):
        key_h = 77
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
        r_back = (16, y, 190, y + key_h)
        self._draw_keycap(draw, r_back, self._t(state, "letters_long", "返回字母键盘"), font=self.font_key_sm, fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_ACCENT)
        self._add_button(r_back, "switch_keyboard", "letters")

        r_kao = (198, y, 290, y + key_h)
        self._draw_keycap(draw, r_kao, "(^_^)", font=self.font_key_sm, fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT)
        self._add_button(r_kao, "switch_keyboard", "kaomoji")

        r_space = (298, y, 650, y + key_h)
        self._draw_keycap(draw, r_space, self._t(state, "space", "空  格"), font=self.font_key_md, fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_SUB)
        self._add_button(r_space, "key_space")

        r_del = (658, y, 810, y + key_h)
        self._draw_keycap(draw, r_del, self._t(state, "bksp", "删除"), font=self.font_key_md, fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT)
        self._add_button(r_del, "key_press", "Backspace")

        r_enter = (818, y, WIDTH - 16, y + key_h)
        self._draw_keycap(draw, r_enter, self._t(state, "enter", "回车"), font=self.font_key_md, fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255))
        self._add_button(r_enter, "key_enter")

    def _render_kaomoji_panel(self, draw: ImageDraw.Draw, state: dict):
        cats = list(KAOMOJI_CATEGORIES.keys())
        cur_cat = state.get("kaomoji_cat", cats[0] if cats else "卖萌")
        if cur_cat not in KAOMOJI_CATEGORIES:
            cur_cat = cats[0] if cats else "卖萌"
        ui_lang = state.get("ui_lang", "zh")

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
                radius=9, shadow=True
            )
            self._add_button(cat_rect, "select_kaomoji_cat", cat)
            cat_y += cat_h + cat_gap

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
                text_color=COLOR_TEXT_MAIN, radius=9, shadow=True
            )
            self._add_button(kao_rect, "insert_char", kao)

        by = 450
        bh = 74
        b_back = (186, by, 320, by + bh)
        self._draw_keycap(draw, b_back, self._t(state, "letters_long", "返回字母"), font=self.font_key_sm, fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_ACCENT, radius=9)
        self._add_button(b_back, "switch_keyboard", "letters")

        b_123 = (328, by, 408, by + bh)
        self._draw_keycap(draw, b_123, "123", font=self.font_key_md, fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB, radius=9)
        self._add_button(b_123, "switch_keyboard", "numbers")

        b_sym = (416, by, 496, by + bh)
        self._draw_keycap(draw, b_sym, "#+=", font=self.font_key_md, fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER, text_color=COLOR_TEXT_SUB, radius=9)
        self._add_button(b_sym, "switch_keyboard", "symbols")

        b_space = (504, by, 720, by + bh)
        self._draw_keycap(draw, b_space, self._t(state, "space", "空  格"), font=self.font_key_md, fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_SUB, radius=9)
        self._add_button(b_space, "key_space")

        b_del = (728, by, 846, by + bh)
        self._draw_keycap(draw, b_del, self._t(state, "bksp", "删除"), font=self.font_key_md, fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT, radius=9)
        self._add_button(b_del, "key_press", "Backspace")

        b_enter = (854, by, WIDTH - 16, by + bh)
        self._draw_keycap(draw, b_enter, self._t(state, "enter", "回车"), font=self.font_key_md, fill=COLOR_PRIMARY, border=COLOR_PRIMARY_BORDER, text_color=(255, 255, 255, 255), radius=9)
        self._add_button(b_enter, "key_enter")

    def _render_phrases_modal(self, draw: ImageDraw.Draw, state: dict):
        """常用语面板"""
        panel_rect = (16, 72, WIDTH - 16, HEIGHT - 14)
        draw.rounded_rectangle(panel_rect, radius=14, fill=COLOR_SURFACE, outline=COLOR_BORDER)

        is_delete_mode = state.get("phrase_delete_mode", False)
        title = "常用语管理模式 [点击右侧红色按钮删除]" if is_delete_mode else self._t(state, "phrases_title", "常用语快捷面板 (点击词条填入，或点击右侧直发)")
        self._draw_left_text(draw, 36, 98, title, self.font_key_md, COLOR_DANGER if is_delete_mode else COLOR_TEXT_ACCENT)

        add_rect = (520, 80, 680, 116)
        self._draw_keycap(
            draw, add_rect, self._t(state, "save_current", "+ 存入当前"), font=self.font_key_sm,
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

    # ==========================================================================
    # 全新规划：双栏模块化设置与控制中心 (左侧导航 Tabs + 右侧宽敞卡片区)
    # ==========================================================================
    def _render_settings_modal(self, draw: ImageDraw.Draw, state: dict):
        panel_rect = (16, 72, WIDTH - 16, HEIGHT - 14)
        draw.rounded_rectangle(panel_rect, radius=14, fill=COLOR_SURFACE, outline=COLOR_BORDER)

        ui_lang = state.get("ui_lang", "zh")
        cur_tab = state.get("settings_tab", "engine")  # "engine", "input", "vr"

        # 1. 顶部标题与全局快捷操作栏 (y: 78..120)
        draw.rounded_rectangle((32, 86, 37, 112), radius=2, fill=COLOR_BORDER_ACTIVE)
        self._draw_left_text(draw, 48, 99, self._t(state, "settings_title", "系统与控制中心"), self.font_main, COLOR_TEXT_MAIN)

        ui_btn = (530, 81, 696, 117)
        self._draw_keycap(
            draw, ui_btn, self._t(state, "ui_lang_btn", "界面: 简体中文"), font=self.font_key_sm,
            fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_ACCENT,
            radius=9, shadow=False
        )
        self._add_button(ui_btn, "toggle_ui_lang")

        test_btn = (706, 81, 826, 117)
        self._draw_keycap(
            draw, test_btn, self._t(state, "test_conn", "测试连接"), font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=9, shadow=False
        )
        self._add_button(test_btn, "test_translation_api")

        back_rect = (836, 81, 968, 117)
        self._draw_keycap(
            draw, back_rect, self._t(state, "save_return", "完成返回"), font=self.font_key_sm,
            fill=COLOR_SUCCESS, border=COLOR_SUCCESS_BORDER, text_color=(255, 255, 255, 255),
            radius=9, shadow=False
        )
        self._add_button(back_rect, "toggle_modal", None)

        draw.line([(28, 126), (WIDTH - 28, 126)], fill=COLOR_DIVIDER, width=1)

        # 2. 左侧导航栏 (x: 28..214, y: 138..486)
        tabs = [
            ("engine", self._t(state, "tab_engine", "翻译引擎"), self._t(state, "tab_engine_sub", "通道 · 代理 · 口吻")),
            ("input", self._t(state, "tab_input", "语言与输入"), self._t(state, "tab_input_sub", "互译 · 发送 · 词库")),
            ("vr", self._t(state, "tab_vr", "空间与引导"), self._t(state, "tab_vr_sub", "尺寸 · 激光 · 热键")),
            ("voice", self._t(state, "tab_voice", "语音与HUD"), self._t(state, "tab_voice_sub", "听写 · 字幕 · 挂载")),
        ]
        ty = 138
        for tab_id, t_title, t_sub in tabs:
            t_rect = (28, ty, 212, ty + 56)
            is_act = (cur_tab == tab_id)
            is_hov = (self._hover_rect == t_rect)
            bg = COLOR_PRIMARY_SOFT if is_act else (_shift_color(COLOR_SURFACE_INNER, 10) if is_hov else COLOR_SURFACE_INNER)
            bd = COLOR_BORDER_ACTIVE if (is_act or is_hov) else COLOR_BORDER
            draw.rounded_rectangle(t_rect, radius=11, fill=bg, outline=bd, width=2 if is_act else 1)
            if is_act:
                draw.rounded_rectangle((32, ty + 11, 37, ty + 45), radius=2, fill=COLOR_BORDER_ACTIVE)
            self._draw_left_text(draw, 48, ty + 19, t_title, self.font_key_md, (255, 255, 255, 255) if is_act else COLOR_TEXT_MAIN)
            self._draw_left_text(draw, 48, ty + 41, t_sub, self.font_tiny, COLOR_TEXT_ACCENT if is_act else COLOR_TEXT_MUTED)
            self._add_button(t_rect, "set_settings_tab", tab_id)
            ty += 64

        # 左侧底部运行状态卡片
        stat_rect = (28, 400, 212, 486)
        draw.rounded_rectangle(stat_rect, radius=11, fill=COLOR_SURFACE_INNER, outline=COLOR_DIVIDER)
        is_vd = state.get("is_vd_active", False)
        env_txt = "VD 串流" if is_vd else "SteamVR / 桌面"
        self._draw_left_text(draw, 42, 418, "运行状态" if ui_lang == "zh" else "Runtime", self.font_tiny, COLOR_TEXT_MUTED)
        draw.ellipse((42, 439, 49, 446), fill=COLOR_SUCCESS_BORDER)
        self._draw_left_text(draw, 56, 443, env_txt, self.font_key_sm, COLOR_TEXT_SUB)
        self._draw_left_text(draw, 42, 468, "词库: 10万+ 雾凇" if ui_lang == "zh" else "Dict: 100k+ Ice", self.font_tiny, COLOR_TEXT_ACCENT)

        # 3. 右侧内容区 (x: 226..968, y: 138..486)
        if cur_tab == "engine":
            self._render_settings_tab_engine(draw, state)
        elif cur_tab == "input":
            self._render_settings_tab_input(draw, state)
        elif cur_tab == "voice":
            self._render_settings_tab_voice(draw, state)
        else:
            self._render_settings_tab_vr(draw, state)

        # 4. 底部实时反馈状态条 (y: 496..534)
        tip_rect = (28, 496, WIDTH - 28, 534)
        settings_tip = state.get("settings_tip", "")
        if settings_tip:
            is_ok = ("成功" in settings_tip or "恢复" in settings_tip or "Success" in settings_tip or "已" in settings_tip)
            tip_bg = COLOR_SUCCESS_SOFT if is_ok else COLOR_WARNING_SOFT
            tip_bd = COLOR_SUCCESS_BORDER if is_ok else COLOR_WARNING
            tip_col = COLOR_TEXT_TRANS if is_ok else (255, 205, 115, 255)
            draw.rounded_rectangle(tip_rect, radius=10, fill=tip_bg, outline=tip_bd)
            self._draw_left_text(draw, 46, 515, settings_tip, self.font_key_sm, tip_col)
        else:
            draw.rounded_rectangle(tip_rect, radius=10, fill=COLOR_SURFACE_INNER, outline=COLOR_DIVIDER)
            idle_tip = "提示：所有设置修改后自动实时保存，可点击右上角【测试连接】验证翻译通道。" if ui_lang == "zh" else "Tip: All changes are auto-saved. Tap [Test API] to verify translation."
            self._draw_left_text(draw, 46, 515, idle_tip, self.font_key_sm, COLOR_TEXT_MUTED)

    def _render_settings_tab_engine(self, draw: ImageDraw.Draw, state: dict):
        ui_lang = state.get("ui_lang", "zh")
        cur_engine = state.get("engine", "google_official")
        net_mode = state.get("network_mode", "global")
        is_global = (net_mode == "global")

        # 2x2 引擎选择大卡片
        engines = [
            ("free_direct", self._t(state, "eng_free", "免费极速通道"), "免Key · 多线自动容灾" if ui_lang == "zh" else "Zero-config fastpath", (226, 138, 590, 196)),
            ("google_official", self._t(state, "eng_google", "Google 官方翻译"), "直连/代理 · 毫秒级响应" if ui_lang == "zh" else "Fast & reliable official", (602, 138, 968, 196)),
            ("google_gemini", self._t(state, "eng_gemini", "Google Gemini AI"), "大模型 · 自然语境翻译" if ui_lang == "zh" else "LLM context-aware", (226, 206, 590, 264)),
            ("deepseek", self._t(state, "eng_deepseek", "DeepSeek 大模型"), "高性价比 · 口语化强" if ui_lang == "zh" else "Chat-native AI model", (602, 206, 968, 264)),
        ]
        for eng_id, title, sub, rect in engines:
            is_act = (cur_engine == eng_id)
            is_hov = (self._hover_rect == rect)
            is_free_act = is_act and eng_id == "free_direct"
            fill = COLOR_SUCCESS_SOFT if is_free_act else (COLOR_PRIMARY_SOFT if is_act else (_shift_color(COLOR_KEY, 12) if is_hov else COLOR_KEY))
            bd = COLOR_SUCCESS_BORDER if is_free_act else (COLOR_BORDER_ACTIVE if (is_act or is_hov) else COLOR_KEY_BORDER)
            draw.rounded_rectangle(rect, radius=11, fill=fill, outline=bd, width=2 if is_act else 1)

            dot_col = (COLOR_SUCCESS_BORDER if is_free_act else COLOR_BORDER_ACTIVE) if is_act else (60, 72, 98, 255)
            draw.ellipse((rect[0] + 16, rect[1] + 16, rect[0] + 26, rect[1] + 26), fill=dot_col)
            self._draw_left_text(draw, rect[0] + 36, rect[1] + 21, title, self.font_key_md, (255, 255, 255, 255) if is_act else COLOR_TEXT_MAIN)
            self._draw_left_text(draw, rect[0] + 36, rect[1] + 43, sub, self.font_tiny, COLOR_TEXT_ACCENT if is_act else COLOR_TEXT_MUTED)
            self._add_button(rect, "set_engine", eng_id)

        # 下方引擎详细配置卡 (x: 226..968, y: 276..486)
        cfg_rect = (226, 276, 968, 486)
        draw.rounded_rectangle(cfg_rect, radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)

        if cur_engine in ("free_direct", "google_official"):
            title = "网络线路与代理配置" if ui_lang == "zh" else "Network & Proxy Configuration"
            self._draw_left_text(draw, 248, 304, title, self.font_key_md, COLOR_TEXT_ACCENT)

            b_glob = (248, 328, 500, 372)
            self._draw_keycap(
                draw, b_glob, ("● " if is_global else "") + self._t(state, "net_global", "海外直连 (免代理)"),
                font=self.font_key_sm,
                fill=COLOR_PRIMARY if is_global else COLOR_KEY,
                border=COLOR_PRIMARY_BORDER if is_global else COLOR_KEY_BORDER,
                text_color=(255, 255, 255, 255) if is_global else COLOR_TEXT_SUB,
                radius=9, shadow=False
            )
            self._add_button(b_glob, "set_network_mode", "global")

            b_ml = (512, 328, 764, 372)
            self._draw_keycap(
                draw, b_ml, ("● " if not is_global else "") + self._t(state, "net_mainland", "中国大陆 (走代理)"),
                font=self.font_key_sm,
                fill=COLOR_PRIMARY if not is_global else COLOR_KEY,
                border=COLOR_PRIMARY_BORDER if not is_global else COLOR_KEY_BORDER,
                text_color=(255, 255, 255, 255) if not is_global else COLOR_TEXT_SUB,
                radius=9, shadow=False
            )
            self._add_button(b_ml, "set_network_mode", "mainland")

            proxy_str = state.get("proxy", "http://127.0.0.1:7890")
            b_proxy = (248, 386, 620, 428)
            self._draw_keycap(
                draw, b_proxy, f"代理端口 (点击轮换): {proxy_str}" if ui_lang == "zh" else f"Proxy (Tap): {proxy_str}",
                font=self.font_key_sm, fill=COLOR_KEY_FUNC, border=COLOR_KEY_FUNC_BORDER,
                text_color=COLOR_TEXT_ACCENT, radius=9, shadow=False
            )
            self._add_button(b_proxy, "toggle_proxy_preset")

            hint = "说明：海外或已开 TUN 全局加速可直接使用【海外直连】；国内若使用 Clash/v2ray 请选【走代理】。" if ui_lang == "zh" else "Note: Use Global Direct if outside China or using TUN mode; otherwise select China Proxy."
            self._draw_left_text(draw, 248, 456, hint, self.font_tiny, COLOR_TEXT_MUTED)

        else:
            is_gem = (cur_engine == "google_gemini")
            raw_key = state.get("google_api_key" if is_gem else "deepseek_api_key", "").strip()
            k_disp = f"API Key: {raw_key[:8]}...{raw_key[-4:]}" if len(raw_key) > 12 else ("API Key: 未配置 (请点击粘贴)" if ui_lang == "zh" else "API Key: Not Set")
            self._draw_left_text(draw, 248, 306, k_disp, self.font_key_md, COLOR_TEXT_TRANS if raw_key else (255, 185, 80, 255))

            b_paste = (640, 288, 790, 326)
            self._draw_keycap(draw, b_paste, self._t(state, "paste_key", "粘贴 Key"), font=self.font_key_sm, fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False)
            self._add_button(b_paste, "paste_google_key" if is_gem else "paste_deepseek_key")

            b_clr = (800, 288, 944, 326)
            self._draw_keycap(draw, b_clr, self._t(state, "clear_key", "清除 Key"), font=self.font_key_sm, fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT, radius=8, shadow=False)
            self._add_button(b_clr, "clear_google_key" if is_gem else "clear_deepseek_key")

            # 模型行
            cur_m = state.get("google_model" if is_gem else "deepseek_model", "")
            self._draw_left_text(draw, 248, 356, f"模型: {cur_m}", self.font_key_sm, COLOR_TEXT_MAIN)

            b_cyc = (640, 338, 790, 376)
            self._draw_keycap(draw, b_cyc, self._t(state, "cycle_model", "切换模型"), font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False)
            self._add_button(b_cyc, "cycle_gemini_model" if is_gem else "cycle_deepseek_model")

            if is_gem:
                b_fetch = (800, 338, 944, 376)
                self._draw_keycap(draw, b_fetch, self._t(state, "fetch_model", "拉取列表"), font=self.font_key_sm, fill=COLOR_KEY_FUNC, border=COLOR_BORDER, text_color=COLOR_TEXT_SUB, radius=8, shadow=False)
                self._add_button(b_fetch, "fetch_gemini_models")

            # 口吻风格 3选1 胶囊 + 自定义
            cur_style = state.get("prompt_style", "social")
            self._draw_left_text(draw, 248, 404, self._t(state, "style_title", "AI 口吻风格"), self.font_key_sm, COLOR_TEXT_SUB)

            b_soc = (248, 424, 398, 466)
            self._draw_keycap(draw, b_soc, self._t(state, "style_social", "友好社交"), font=self.font_key_sm, fill=COLOR_PRIMARY if cur_style == "social" else COLOR_KEY, border=COLOR_PRIMARY_BORDER if cur_style == "social" else COLOR_BORDER, text_color=(255, 255, 255, 255) if cur_style == "social" else COLOR_TEXT_SUB, radius=8, shadow=False)
            self._add_button(b_soc, "set_prompt_style", "social")

            b_agg = (408, 424, 558, 466)
            self._draw_keycap(draw, b_agg, self._t(state, "style_aggro", "游戏对线"), font=self.font_key_sm, fill=COLOR_DANGER if cur_style == "aggressive" else COLOR_KEY, border=(255, 110, 130, 255) if cur_style == "aggressive" else COLOR_BORDER, text_color=(255, 255, 255, 255) if cur_style == "aggressive" else COLOR_TEXT_SUB, radius=8, shadow=False)
            self._add_button(b_agg, "set_prompt_style", "aggressive")

            b_cus = (568, 424, 756, 466)
            self._draw_keycap(draw, b_cus, self._t(state, "paste_custom", "粘贴自定义提示词"), font=self.font_key_sm, fill=COLOR_PRIMARY_SOFT if cur_style == "custom" else COLOR_KEY_FUNC, border=COLOR_BORDER_ACTIVE if cur_style == "custom" else COLOR_BORDER, text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False)
            self._add_button(b_cus, "paste_custom_prompt")

            b_rst = (766, 424, 944, 466)
            self._draw_keycap(draw, b_rst, self._t(state, "reset_default", "恢复默认"), font=self.font_key_sm, fill=COLOR_KEY_FUNC, border=COLOR_BORDER, text_color=COLOR_TEXT_MUTED, radius=8, shadow=False)
            self._add_button(b_rst, "reset_default_prompt")

    def _render_settings_tab_input(self, draw: ImageDraw.Draw, state: dict):
        ui_lang = state.get("ui_lang", "zh")
        cur_src = state.get("source_lang", "zh")
        cur_tgt = state.get("target_lang", "en")

        # 区块 1: 互译方向 (y: 138..264)
        draw.rounded_rectangle((226, 138, 968, 264), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        self._draw_left_text(draw, 246, 160, self._t(state, "lang_pair_title", "互译方向"), self.font_key_md, COLOR_TEXT_ACCENT)

        pairs = [
            ("zh", "en", "zh2en", (246, 182, 382, 244)),
            ("zh", "ja", "zh2ja", (392, 182, 528, 244)),
            ("zh", "ko", "zh2ko", (538, 182, 674, 244)),
            ("zh", "ru", "zh2ru", (684, 182, 820, 244)),
            ("en", "zh", "en2zh", (830, 182, 950, 244)),
        ]
        for p_src, p_tgt, sk, rect in pairs:
            is_act = (cur_src == p_src and cur_tgt == p_tgt)
            lbl = ("● " if is_act else "") + self._t(state, sk, f"{p_src}→{p_tgt}")
            self._draw_keycap(
                draw, rect, lbl, font=self.font_key_sm,
                fill=COLOR_PRIMARY if is_act else COLOR_KEY,
                border=COLOR_PRIMARY_BORDER if is_act else COLOR_KEY_BORDER,
                text_color=(255, 255, 255, 255) if is_act else COLOR_TEXT_SUB,
                radius=9, shadow=False
            )
            self._add_button(rect, "set_lang_pair", (p_src, p_tgt))

        # 区块 2: 发送译文输出模式 (y: 276..376)
        draw.rounded_rectangle((226, 276, 968, 376), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        self._draw_left_text(draw, 246, 298, self._t(state, "send_mode_title", "发送译文输出模式 (点【发送译文】时的格式)"), self.font_key_md, COLOR_TEXT_ACCENT)

        cur_sm = state.get("send_mode", "translated_only")
        sm_opts = [
            ("translated_only", self._t(state, "send_trans_only", "仅发译文"), (246, 318, 476, 362)),
            ("bilingual", self._t(state, "send_bilingual", "双语对照 (译文+原文)"), (488, 318, 728, 362)),
            ("original_only", self._t(state, "send_orig_only", "仅发原文"), (740, 318, 950, 362)),
        ]
        for sm_id, sm_lbl, rect in sm_opts:
            is_act = (cur_sm == sm_id)
            self._draw_keycap(
                draw, rect, ("● " if is_act else "") + sm_lbl, font=self.font_key_sm,
                fill=COLOR_SUCCESS if is_act else COLOR_KEY,
                border=COLOR_SUCCESS_BORDER if is_act else COLOR_KEY_BORDER,
                text_color=(255, 255, 255, 255) if is_act else COLOR_TEXT_SUB,
                radius=9, shadow=False
            )
            self._add_button(rect, "set_send_mode", sm_id)

        # 区块 3: 默认输入模式 & 词库记忆 (y: 388..486)
        draw.rounded_rectangle((226, 388, 968, 486), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        init_mode = state.get("input_mode", "zh")
        init_btn = (246, 412, 580, 462)
        init_lbl = self._t(state, "init_zh", "默认输入: 中文拼音") if init_mode == "zh" else self._t(state, "init_en", "默认输入: 英文直出")
        self._draw_keycap(
            draw, init_btn, init_lbl, font=self.font_key_md,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=10, shadow=False
        )
        self._add_button(init_btn, "toggle_input_mode")

        reset_btn = (600, 412, 950, 462)
        self._draw_keycap(
            draw, reset_btn, self._t(state, "reset_dict", "重置个人输入记忆 (清空学习词频)"), font=self.font_key_sm,
            fill=COLOR_DELETE_BG, border=COLOR_DELETE_BORDER, text_color=COLOR_DELETE_TEXT,
            radius=10, shadow=False
        )
        self._add_button(reset_btn, "clear_user_history")

    def _render_settings_tab_vr(self, draw: ImageDraw.Draw, state: dict):
        ui_lang = state.get("ui_lang", "zh")

        # 区块 1: 交互式 VR 尺寸滑块 (y: 138..264)
        draw.rounded_rectangle((226, 138, 968, 264), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        overlay_w = state.get("overlay_width_m", 0.42)
        pct = int(round((overlay_w / 0.42) * 100))
        sz_title = f"VR 键盘物理宽度: {overlay_w:.2f} 米 ({pct}%)" if ui_lang == "zh" else f"VR Panel Width: {overlay_w:.2f}m ({pct}%)"
        self._draw_left_text(draw, 246, 164, sz_title, self.font_key_md, COLOR_TEXT_ACCENT)

        # 滑轨 (x: 248..700, cy=218)
        sx1, sx2 = 250, 690
        scy = 218
        ratio = max(0.0, min(1.0, (overlay_w - 0.25) / (0.85 - 0.25)))
        knob_x = int(sx1 + ratio * (sx2 - sx1))

        draw.rounded_rectangle((sx1, scy - 5, sx2, scy + 5), radius=5, fill=(32, 42, 66, 255))
        draw.rounded_rectangle((sx1, scy - 5, max(sx1 + 8, knob_x), scy + 5), radius=5, fill=COLOR_BORDER_ACTIVE)
        draw.ellipse((knob_x - 12, scy - 12, knob_x + 12, scy + 12), fill=(255, 255, 255, 255), outline=COLOR_BORDER_ACTIVE, width=3)
        self._add_button((sx1 - 12, scy - 20, sx2 + 12, scy + 20), "vr_size_slider", (sx1, sx2))

        b_sub = (712, 198, 782, 238)
        self._draw_keycap(draw, b_sub, "- 缩小", font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=8, shadow=False)
        self._add_button(b_sub, "adjust_scale", -0.04)

        b_std = (790, 198, 876, 238)
        self._draw_keycap(draw, b_std, "标准", font=self.font_key_sm, fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False)
        self._add_button(b_std, "reset_scale")

        b_add = (884, 198, 952, 238)
        self._draw_keycap(draw, b_add, "+ 放大", font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=8, shadow=False)
        self._add_button(b_add, "adjust_scale", 0.04)

        # 区块 2: 3D 激光引导线模式 (y: 276..376)
        draw.rounded_rectangle((226, 276, 968, 376), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        lg_title = "3D 激光引导线与落点准星 (SteamVR 原生可自动隐藏防双线)" if ui_lang == "zh" else "3D Laser Guide Mode"
        self._draw_left_text(draw, 246, 298, lg_title, self.font_key_md, COLOR_TEXT_ACCENT)

        lg_mode = state.get("laser_guide", "auto")
        lg_opts = [
            ("auto", self._t(state, "guide_auto", "智能 (VD开启/原生隐藏)"), (246, 318, 530, 362)),
            ("on", self._t(state, "guide_on", "强制开启"), (542, 318, 742, 362)),
            ("off", self._t(state, "guide_off", "强制关闭"), (754, 318, 952, 362)),
        ]
        for mode_id, mode_lbl, rect in lg_opts:
            is_act = (lg_mode == mode_id)
            self._draw_keycap(
                draw, rect, ("● " if is_act else "") + mode_lbl, font=self.font_key_sm,
                fill=COLOR_PRIMARY if is_act else COLOR_KEY,
                border=COLOR_PRIMARY_BORDER if is_act else COLOR_KEY_BORDER,
                text_color=(255, 255, 255, 255) if is_act else COLOR_TEXT_SUB,
                radius=9, shadow=False
            )
            self._add_button(rect, "set_laser_guide", mode_id)

        # 区块 3: 呼出热键与操作指南 (y: 388..486)
        draw.rounded_rectangle((226, 388, 968, 486), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        hk_ctrl = state.get("hotkey_controller", "right")
        hk_lbl = self._t(state, "call_key_r", "呼出热键: 右手摇杆双击") if hk_ctrl == "right" else self._t(state, "call_key_l", "呼出热键: 左手摇杆双击")
        b_hk = (246, 412, 560, 462)
        self._draw_keycap(
            draw, b_hk, hk_lbl, font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=10, shadow=False
        )
        self._add_button(b_hk, "toggle_vr_hand")

        guide_txt = "操作说明：食指扳机 Trigger 点击 · 中指握把 Grip 任意拖拽移动" if ui_lang == "zh" else "Controls: Trigger to Click · Grip anywhere to Drag"
        self._draw_left_text(draw, 580, 437, guide_txt, self.font_tiny, COLOR_TEXT_SUB)

    def _render_settings_tab_voice(self, draw: ImageDraw.Draw, state: dict):
        ui_lang = state.get("ui_lang", "zh")

        # 区块 1: 双路语音开关与识别引擎 (y: 138..224)
        draw.rounded_rectangle((226, 138, 968, 224), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        mic_on = state.get("voice_mic_enabled", False)
        loop_on = state.get("voice_loopback_enabled", False)
        stt_eng = state.get("voice_stt_engine", "gemini")

        b_mic = (240, 148, 430, 182)
        self._draw_keycap(
            draw, b_mic, ("● 自己语音直发: 开" if mic_on else "○ 自己语音直发: 关") if ui_lang == "zh" else ("● Mic Send: ON" if mic_on else "○ Mic Send: OFF"),
            font=self.font_tiny,
            fill=COLOR_SUCCESS if mic_on else COLOR_KEY,
            border=COLOR_SUCCESS_BORDER if mic_on else COLOR_KEY_BORDER,
            text_color=(255, 255, 255, 255) if mic_on else COLOR_TEXT_SUB,
            radius=8, shadow=False
        )
        self._add_button(b_mic, "toggle_voice_mic")

        b_loop = (440, 148, 652, 182)
        self._draw_keycap(
            draw, b_loop, ("● 游戏语音HUD: 开" if loop_on else "○ 游戏语音HUD: 关") if ui_lang == "zh" else ("● Game Voice HUD: ON" if loop_on else "○ Game Voice HUD: OFF"),
            font=self.font_tiny,
            fill=COLOR_SUCCESS if loop_on else COLOR_KEY,
            border=COLOR_SUCCESS_BORDER if loop_on else COLOR_KEY_BORDER,
            text_color=(255, 255, 255, 255) if loop_on else COLOR_TEXT_SUB,
            radius=8, shadow=False
        )
        self._add_button(b_loop, "toggle_voice_loopback")

        # 右上角引擎辅助按钮
        if stt_eng == "groq":
            has_gkey = bool(state.get("groq_key_set", False))
            b_aux = (662, 148, 954, 182)
            aux_txt = ("粘贴 Groq Key (已配置)" if has_gkey else "粘贴 Groq Key (未填)") if ui_lang == "zh" else ("Paste Groq Key (Set)" if has_gkey else "Paste Groq Key")
            self._draw_keycap(
                draw, b_aux, aux_txt, font=self.font_tiny,
                fill=COLOR_PRIMARY_SOFT if has_gkey else COLOR_WARNING_SOFT,
                border=COLOR_BORDER_ACTIVE if has_gkey else COLOR_WARNING,
                text_color=COLOR_TEXT_ACCENT if has_gkey else (255, 210, 120, 255),
                radius=8, shadow=False
            )
            self._add_button(b_aux, "paste_groq_key")
        elif stt_eng == "google_free":
            b_aux = (662, 148, 954, 182)
            olang = state.get("voice_other_source_lang", "en-US")
            self._draw_keycap(
                draw, b_aux, f"对方语种(免Key): {olang}" if ui_lang == "zh" else f"Listen Lang: {olang}",
                font=self.font_tiny, fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE,
                text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False
            )
            self._add_button(b_aux, "cycle_other_src_lang")
        else:
            has_gem = bool(state.get("google_key_set", False))
            b_aux = (662, 148, 954, 182)
            aux_txt = ("Gemini Key 已就绪 (自动多语)" if has_gem else "需先在【翻译引擎】填 Gemini Key") if ui_lang == "zh" else ("Gemini Key Ready" if has_gem else "Set Gemini Key in Engine Tab")
            self._draw_keycap(
                draw, b_aux, aux_txt, font=self.font_tiny,
                fill=COLOR_PRIMARY_SOFT if has_gem else COLOR_WARNING_SOFT,
                border=COLOR_BORDER_ACTIVE if has_gem else COLOR_WARNING,
                text_color=COLOR_TEXT_ACCENT if has_gem else (255, 210, 120, 255),
                radius=8, shadow=False
            )
            self._add_button(b_aux, "set_settings_tab", "engine")

        # 识别引擎三选一 (y: 188..216)
        eng_opts = [
            ("gemini", "Gemini 多模态(最准/便宜)", (240, 188, 480, 216)),
            ("groq", "Groq Whisper(免费高额)", (490, 188, 720, 216)),
            ("google_free", "Google 免Key(单语)", (730, 188, 954, 216)),
        ]
        for eid, elbl, er in eng_opts:
            is_act = (stt_eng == eid)
            self._draw_keycap(
                draw, er, ("● " if is_act else "") + elbl, font=self.font_tiny,
                fill=COLOR_PRIMARY if is_act else COLOR_KEY,
                border=COLOR_PRIMARY_BORDER if is_act else COLOR_KEY_BORDER,
                text_color=(255, 255, 255, 255) if is_act else COLOR_TEXT_SUB,
                radius=7, shadow=False
            )
            self._add_button(er, "set_stt_engine", eid)

        # 区块 2: HUD 挂载位置、译文语言与显示时长 (y: 232..312)
        draw.rounded_rectangle((226, 232, 968, 312), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        anchor = state.get("hud_anchor", "hmd")
        anchor_opts = [
            ("hmd", "头显抬头 HUD", (240, 242, 396, 274)),
            ("left", "绑定左手", (404, 242, 514, 274)),
            ("right", "绑定右手", (522, 242, 632, 274)),
        ]
        for aid, albl, ar in anchor_opts:
            is_act = (anchor == aid)
            self._draw_keycap(
                draw, ar, ("● " if is_act else "") + albl, font=self.font_tiny,
                fill=COLOR_PRIMARY if is_act else COLOR_KEY,
                border=COLOR_PRIMARY_BORDER if is_act else COLOR_KEY_BORDER,
                text_color=(255, 255, 255, 255) if is_act else COLOR_TEXT_SUB,
                radius=8, shadow=False
            )
            self._add_button(ar, "set_hud_anchor", aid)

        hud_tgt = state.get("hud_target_lang", "zh")
        tgt_names = {"zh": "简体中文", "en": "English", "ja": "日本語", "ko": "한국어", "zh-TW": "繁體中文"}
        b_htgt = (644, 242, 816, 274)
        self._draw_keycap(
            draw, b_htgt, f"HUD译成: {tgt_names.get(hud_tgt, hud_tgt)}", font=self.font_tiny,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT, radius=8, shadow=False
        )
        self._add_button(b_htgt, "cycle_hud_target_lang")

        hud_dur = float(state.get("hud_duration_s", 6.0))
        b_hdur = (824, 242, 954, 274)
        self._draw_keycap(
            draw, b_hdur, f"停留: {int(hud_dur)}秒", font=self.font_tiny,
            fill=COLOR_KEY, border=COLOR_KEY_BORDER, text_color=COLOR_TEXT_MAIN, radius=8, shadow=False
        )
        self._add_button(b_hdur, "cycle_hud_duration")

        # 辅助选项行 (y: 280..306)
        sens = state.get("vad_sensitivity", "medium")
        sens_lbl = {"low": "灵敏(安静)", "medium": "标准", "high": "抗噪(高门限)"}.get(sens, "标准")
        b_sens = (240, 279, 444, 306)
        self._draw_keycap(draw, b_sens, f"收音门限: {sens_lbl}", font=self.font_tiny, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=7, shadow=False)
        self._add_button(b_sens, "cycle_vad_sensitivity")

        smode = state.get("voice_self_send_mode", "direct")
        b_smode = (454, 279, 646, 306)
        self._draw_keycap(
            draw, b_smode, "自己语音: 直接发送" if smode == "direct" else "自己语音: 填入输入框",
            font=self.font_tiny, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=7, shadow=False
        )
        self._add_button(b_smode, "toggle_self_send_mode")

        show_orig = state.get("hud_show_original", True)
        b_horig = (656, 279, 824, 306)
        self._draw_keycap(
            draw, b_horig, "HUD: 原文+译文" if show_orig else "HUD: 仅显示译文",
            font=self.font_tiny, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=7, shadow=False
        )
        self._add_button(b_horig, "toggle_hud_original")

        b_htest = (834, 279, 954, 306)
        self._draw_keycap(
            draw, b_htest, "测试 HUD", font=self.font_tiny,
            fill=COLOR_SUCCESS_SOFT, border=COLOR_SUCCESS_BORDER, text_color=COLOR_TEXT_TRANS, radius=7, shadow=False
        )
        self._add_button(b_htest, "test_voice_hud")

        # 区块 3: HUD 大小、远近与高低调节 (y: 320..486)
        draw.rounded_rectangle((226, 320, 968, 486), radius=12, fill=COLOR_SURFACE_INNER, outline=COLOR_BORDER)
        hw = float(state.get("hud_width_m", 0.48))
        hd = float(state.get("hud_distance_m", 1.25))
        hy = float(state.get("hud_y_offset_m", -0.18))

        self._draw_left_text(draw, 242, 344, f"HUD 大小 (宽度): {hw:.2f} 米", self.font_key_sm, COLOR_TEXT_ACCENT)
        self._draw_keycap(draw, (650, 328, 792, 362), "- 缩小", font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=8, shadow=False)
        self._add_button((650, 328, 792, 362), "adjust_hud_width", -0.05)
        self._draw_keycap(draw, (804, 328, 948, 362), "+ 放大", font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=8, shadow=False)
        self._add_button((804, 328, 948, 362), "adjust_hud_width", 0.05)

        self._draw_left_text(draw, 242, 398, f"HUD 远近 (距离): {hd:.2f} 米", self.font_key_sm, COLOR_TEXT_ACCENT)
        b_hreset = (486, 382, 634, 416)
        self._draw_keycap(
            draw, b_hreset, "重置默认", font=self.font_key_sm,
            fill=COLOR_PRIMARY_SOFT, border=COLOR_BORDER_ACTIVE, text_color=COLOR_TEXT_ACCENT,
            radius=8, shadow=False
        )
        self._add_button(b_hreset, "reset_hud_pose")
        self._draw_keycap(draw, (650, 382, 792, 416), "- 拉近", font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=8, shadow=False)
        self._add_button((650, 382, 792, 416), "adjust_hud_distance", -0.15)
        self._draw_keycap(draw, (804, 382, 948, 416), "+ 推远", font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=8, shadow=False)
        self._add_button((804, 382, 948, 416), "adjust_hud_distance", 0.15)

        self._draw_left_text(draw, 242, 452, f"HUD 上下偏移: {hy:+.2f} 米", self.font_key_sm, COLOR_TEXT_ACCENT)
        self._draw_keycap(draw, (650, 436, 792, 470), "↓ 往下", font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=8, shadow=False)
        self._add_button((650, 436, 792, 470), "adjust_hud_y", -0.04)
        self._draw_keycap(draw, (804, 436, 948, 470), "↑ 往上", font=self.font_key_sm, fill=COLOR_KEY, border=COLOR_KEY_BORDER, radius=8, shadow=False)
        self._add_button((804, 436, 948, 470), "adjust_hud_y", 0.04)

    def render_hud(self, hud_state: dict) -> Image.Image:
        """渲染 800x180 空间半透明抬头显示字幕条 (HUD Overlay)"""
        w, h = 800, 180
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        speaker = hud_state.get("speaker", "other")  # "self" | "other"
        orig = (hud_state.get("original") or "").strip()
        trans = (hud_state.get("translated") or "").strip()
        show_orig = hud_state.get("show_original", True)

        # 玻璃拟态底板
        bd_col = (56, 189, 248, 190) if speaker == "other" else (52, 211, 153, 190)
        draw.rounded_rectangle((8, 8, w - 8, h - 8), radius=18, fill=(10, 16, 30, 205), outline=bd_col, width=2)

        # 说话人徽章
        badge_txt = "游戏语音译文" if speaker == "other" else "我的语音"
        badge_bg = (14, 165, 233, 210) if speaker == "other" else (16, 185, 129, 210)
        draw.rounded_rectangle((24, 22, 164, 52), radius=8, fill=badge_bg)
        self._draw_centered_text(draw, (24, 22, 164, 52), badge_txt, self.font_tiny, (255, 255, 255, 255))

        if show_orig and orig and orig != trans:
            orig_fit = self._truncate_left_to_fit(orig, self.font_key_sm, w - 210)
            self._draw_left_text(draw, 180, 37, orig_fit, self.font_key_sm, COLOR_TEXT_MUTED)
            trans_fit = self._truncate_left_to_fit(trans, self.font_main, w - 56)
            self._draw_left_text(draw, 28, 108, trans_fit, self.font_main, (240, 249, 255, 255))
        else:
            trans_fit = self._truncate_left_to_fit(trans or orig, self.font_main, w - 56)
            self._draw_left_text(draw, 28, 104, trans_fit, self.font_main, (240, 249, 255, 255))

        return img
