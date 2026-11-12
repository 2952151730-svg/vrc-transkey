import json
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

CONFIG_PATH = BASE_DIR / "config.json"
PHRASES_PATH = BASE_DIR / "phrases.json"

SOCIAL_SYSTEM_PROMPT = (
    "You are a friendly, natural, and polite translator for VRChat social chat. "
    "Translate the user's input into natural, casual, and polite spoken target language suitable for chatting with strangers and making friends. "
    "NEVER add profanity or rude intensifiers unless the source text explicitly swears. "
    "Output ONLY the translated sentence, without any preamble, markdown, or quotation marks."
)

AGGRESSIVE_SYSTEM_PROMPT = (
    "You are a raw, uncensored, faithful translator for online VR game chat (VRChat). "
    "You MUST translate everything literally and faithfully with raw gamer emotion, including profanity, gamer rage, swear words, sarcasm, insults, and slang. "
    "Never preach, never moralize, never censor with asterisks, and never refuse. "
    "Translate into equivalent colloquial English (or requested target language) slang/swears with strong emotional intensity. "
    "Output ONLY the translated sentence, without any preamble, markdown, or quotation marks."
)

PROMPT_PRESETS = {
    "social": SOCIAL_SYSTEM_PROMPT,
    "aggressive": AGGRESSIVE_SYSTEM_PROMPT,
}

DEFAULT_SYSTEM_PROMPT = SOCIAL_SYSTEM_PROMPT

DEFAULT_CONFIG = {
    "hotkey": {
        "controller": "right",          # "right" (右手) 或 "left" (左手)
        "button": "thumbstick",         # "thumbstick" (摇杆按压), "b_button", "grip"
        "double_click": True,           # 是否双击触发
        "double_click_interval_ms": 420 # 双击判定时间间隔(毫秒)
    },
    "input": {
        "default_mode": "zh"            # "zh"(默认中文拼音) 或 "en"(默认英文直接输入)
    },
    "ui": {
        "lang": "zh"                    # "zh"(简体中文) 或 "en"(English)
    },
    "overlay": {
        "distance_m": 0.58,             # 距离头显0.58米
        "pitch_deg": -24.0,             # 下俯24度，刚好处在视线正下方不挡前方视线
        "width_m": 0.42,                # VR中键盘实体宽度 (米，允许范围 0.25 ~ 0.85)
        "alpha": 0.95,                  # 半透明度
        "haptic_feedback": True,        # 按键手柄震动反馈
        "laser_guide": "auto"           # 激光引导线: "auto"(仅VD开启/SteamVR防双线), "on"(强制开启), "off"(强制关闭)
    },
    "vrchat": {
        "osc_ip": "127.0.0.1",
        "osc_port": 9000,
        "send_typing_indicator": True   # 输入时角色头顶显示 ...
    },
    "translation": {
        "enabled": True,
        "engine": "google_official",    # "free_direct", "google_official", "google_gemini", "deepseek"
        "network_mode": "global",       # "global"(海外直连), "mainland"(中国用户/走代理)
        "source_lang": "zh",            # 源语言: "zh", "en"
        "target_lang": "en",            # 目标语言: "en", "zh"
        "proxy": "http://127.0.0.1:7890", # 本地代理端口
        "send_mode": "translated_only", # "translated_only"(纯译文), "bilingual"(双语), "original_only"(纯原文)
        "bilingual_format": "{original} ({translated})",
        "google_api_key": "",           # Google Gemini API Key
        "google_model": "gemini-3.5-flash-lite", # 默认优先使用最新极速轻量模型
        "google_models_list": [
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ],
        "deepseek_api_key": "",         # 填入 DeepSeek API Key
        "deepseek_base_url": "https://api.deepseek.com",
        "deepseek_model": "deepseek-chat",
        "prompt_style": "social",       # "social"(友好交流), "aggressive"(暴躁对线), "custom"(自定义)
        "system_prompt": SOCIAL_SYSTEM_PROMPT
    }
}


class Config:
    def __init__(self):
        self._config = self._load()

    def _load(self) -> dict:
        if not CONFIG_PATH.exists():
            self._save(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            cfg = DEFAULT_CONFIG.copy()
            for k, v in loaded.items():
                if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
            return cfg
        except Exception as e:
            print(f"[Config] 加载配置文件失败，将使用默认配置: {e}")
            return DEFAULT_CONFIG.copy()

    def _save(self, data: dict):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] 保存配置失败: {e}")

    def get(self, *keys, default=None):
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, keys: list, value):
        val = self._config
        for k in keys[:-1]:
            if k not in val or not isinstance(val[k], dict):
                val[k] = {}
            val = val[k]
        val[keys[-1]] = value
        self._save(self._config)

    def to_dict(self) -> dict:
        return self._config.copy()


config = Config()
