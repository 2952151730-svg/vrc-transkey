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

GOOGLE_VRC_PROMPT = (
    "You are an expert real-time translator embedded inside a VRChat 3D VR virtual keyboard. "
    "Translate the user's input into natural, concise, colloquial spoken target language suitable for VR socializing and gaming. "
    "Preserve gamer jargon, anime context, internet slang, and casual emotional nuance. "
    "Do NOT add explanations, quotation marks, or preamble. Return ONLY the translated sentence."
)

SOCIAL_SYSTEM_PROMPT = (
    "You are a friendly, natural, and polite translator for VRChat social chat. "
    "Translate the user's Chinese input into natural, casual, and polite spoken target language suitable for chatting with strangers and making friends. "
    "NEVER add profanity or rude intensifiers (such as 'what the hell', 'damn', or 'wtf') unless the source text explicitly swears. "
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
    "google_vrc": GOOGLE_VRC_PROMPT,
    "social": SOCIAL_SYSTEM_PROMPT,
    "aggressive": AGGRESSIVE_SYSTEM_PROMPT,
}

DEFAULT_SYSTEM_PROMPT = GOOGLE_VRC_PROMPT

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
    "overlay": {
        "distance_m": 0.58,             # 距离头显0.58米
        "pitch_deg": -24.0,             # 下俯24度，刚好在视线正下方不挡前方视线
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
        "network_mode": "global",       # "global"(海外直连模式), "mainland"(中国大陆模式)
        "engine": "free_direct",        # "free_direct"(极速免费), "google_gemini"(谷歌Gemini), "deepseek"(DeepSeek)
        "target_lang": "en",            # 目标语言: "en", "ja", "ko", "ru" 等
        "send_mode": "translated_only", # "translated_only"(纯英文), "bilingual"(双语), "original_only"(纯中文)
        "bilingual_format": "{original} ({translated})",
        "google_api_key": "",           # Google Gemini API Key
        "google_model": "gemini-1.5-flash",
        "google_models_list": [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro"
        ],
        "deepseek_api_key": "",         # 填入 DeepSeek API Key
        "deepseek_base_url": "https://api.deepseek.com",
        "deepseek_model": "deepseek-chat",
        "prompt_style": "google_vrc",   # "google_vrc", "social", "aggressive", "custom"
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "proxy": ""                     # 如: "http://127.0.0.1:7890" (大陆模式下访问Google时使用)
    },
    "ui": {
        "sound_feedback": False,
        "theme": "dark_glass"
    }
}

class Config:
    def __init__(self):
        self.data = self.load()

    def load(self):
        if not CONFIG_PATH.exists():
            self.save(DEFAULT_CONFIG)
            return dict(DEFAULT_CONFIG)
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            for k, v in loaded.items():
                if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                    merged[k].update(v)
                else:
                    merged[k] = v
            return merged
        except Exception as e:
            print(f"[Config] 加载配置文件失败，使用默认配置: {e}")
            return dict(DEFAULT_CONFIG)

    def save(self, data=None):
        if data is not None:
            self.data = data
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] 保存配置失败: {e}")

    def get(self, *keys, default=None):
        if not keys:
            return self.data
        cur = self.data
        for k in keys:
            if isinstance(k, dict):
                return cur if cur is not None else k
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                return default
        return cur

    def set(self, keys, value):
        cur = self.data
        for k in keys[:-1]:
            cur = cur.setdefault(k, {})
        cur[keys[-1]] = value
        self.save()

config = Config()
