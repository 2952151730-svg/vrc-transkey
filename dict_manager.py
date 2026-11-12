import os
import sys
import json
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

EMOJI_FILE = DATA_DIR / "emoji_pack.json"
MEME_FILE = DATA_DIR / "meme_dict.json"

# 默认内置精选热梗词库初始内容（仅轻量示例，支持联网更新或用户扩展）
DEFAULT_MEME_ENTRIES = [
    {"word": "草", "pinyin": "cao", "freq": 9999999},
    {"word": "哈哈哈哈", "pinyin": "hahahaha", "freq": 9999999},
    {"word": "太草了", "pinyin": "taicaole", "freq": 9999900},
    {"word": "破防了", "pinyin": "pofangle", "freq": 9999800},
    {"word": "绝绝子", "pinyin": "jiejuezi", "freq": 9999700},
    {"word": "泰裤辣", "pinyin": "taikula", "freq": 9999600},
    {"word": "纯爱战神", "pinyin": "chunaozhanshen", "freq": 9999500},
    {"word": "牛哇牛哇", "pinyin": "niuawaniua", "freq": 9999400},
    {"word": "真香", "pinyin": "zhenxiang", "freq": 9999300},
    {"word": "摆烂", "pinyin": "bailan", "freq": 9999200},
    {"word": "摸鱼", "pinyin": "moyu", "freq": 9999100},
    {"word": "社恐", "pinyin": "shekong", "freq": 9999000},
    {"word": "社牛", "pinyin": "sheniu", "freq": 9998900},
    {"word": "硬控", "pinyin": "yingkong", "freq": 9998800},
    {"word": "电子榨菜", "pinyin": "dianzizhacai", "freq": 9998700},
    {"word": "尊嘟假嘟", "pinyin": "zundujiadu", "freq": 9998600},
    {"word": "CPU我", "pinyin": "cpuwo", "freq": 9998500},
    {"word": "沉浸式", "pinyin": "chenjinshi", "freq": 9998400},
    {"word": "开摆", "pinyin": "kaibai", "freq": 9998300},
    {"word": "牢大", "pinyin": "laoda", "freq": 9998200},
    {"word": "人机", "pinyin": "renji", "freq": 9998100},
    {"word": "原神启动", "pinyin": "yuanshenqidong", "freq": 9998000},
    {"word": "汗流浃背了", "pinyin": "hanliujiabeile", "freq": 9997900},
    {"word": "急了急了", "pinyin": "jilejile", "freq": 9997800},
    {"word": "典中典", "pinyin": "dianzhongdian", "freq": 9997700},
    {"word": "乐了", "pinyin": "lele", "freq": 9997600},
    {"word": "疯狂星期四", "pinyin": "fengkuangxingqisi", "freq": 9997500},
    {"word": "v我50", "pinyin": "vwo50", "freq": 9997400}
]

# 默认精选 Emoji 列表
DEFAULT_EMOJI_ENTRIES = [
    {"emoji": "😀", "name": "微笑", "pinyin": "weixiao"},
    {"emoji": "😂", "name": "笑哭", "pinyin": "xiaoku"},
    {"emoji": "🤣", "name": "笑翻", "pinyin": "xiaofan"},
    {"emoji": "😊", "name": "害羞笑", "pinyin": "haixiuxiao"},
    {"emoji": "🥰", "name": "爱心笑", "pinyin": "aixin"},
    {"emoji": "😍", "name": "色", "pinyin": "se"},
    {"emoji": "😘", "name": "飞吻", "pinyin": "feiwen"},
    {"emoji": "😋", "name": "馋", "pinyin": "chan"},
    {"emoji": "😜", "name": "调皮", "pinyin": "tiaopi"},
    {"emoji": "🤔", "name": "思考", "pinyin": "sikao"},
    {"emoji": "🤫", "name": "嘘", "pinyin": "xu"},
    {"emoji": "😏", "name": "坏笑", "pinyin": "huaixiao"},
    {"emoji": "😭", "name": "大哭", "pinyin": "daku"},
    {"emoji": "😱", "name": "吓死", "pinyin": "xiasi"},
    {"emoji": "😡", "name": "生气", "pinyin": "shengqi"},
    {"emoji": "🤡", "name": "小丑", "pinyin": "xiaochou"},
    {"emoji": "👻", "name": "幽灵", "pinyin": "youling"},
    {"emoji": "❤️", "name": "红心", "pinyin": "hongxin"},
    {"emoji": "💔", "name": "心碎", "pinyin": "xinsui"},
    {"emoji": "✨", "name": "闪光", "pinyin": "shanguang"},
    {"emoji": "🔥", "name": "火", "pinyin": "huo"},
    {"emoji": "👍", "name": "点赞", "pinyin": "dianzan"},
    {"emoji": "👎", "name": "踩", "pinyin": "cai"},
    {"emoji": "👏", "name": "鼓掌", "pinyin": "guzhang"},
    {"emoji": "🙏", "name": "祈祷/拜托", "pinyin": "baituo"},
    {"emoji": "🎉", "name": "庆祝", "pinyin": "qingzhu"},
    {"emoji": "🍺", "name": "啤酒", "pinyin": "pijiu"},
    {"emoji": "☕", "name": "咖啡", "pinyin": "kafei"},
    {"emoji": "🌙", "name": "晚安/月亮", "pinyin": "wanan"}
]

class DictManager:
    @staticmethod
    def get_emoji_info():
        exists = EMOJI_FILE.exists()
        size_mb = (EMOJI_FILE.stat().st_size / (1024 * 1024)) if exists else 0.05
        return {
            "installed": exists,
            "size_mb": round(size_mb, 2),
            "display_size": f"{size_mb:.2f} MB" if size_mb >= 0.01 else "<0.01 MB"
        }

    @staticmethod
    def get_meme_info():
        exists = MEME_FILE.exists()
        size_mb = (MEME_FILE.stat().st_size / (1024 * 1024)) if exists else 0.15
        return {
            "installed": exists,
            "size_mb": round(size_mb, 2),
            "display_size": f"{size_mb:.2f} MB" if size_mb >= 0.01 else "<0.01 MB"
        }

    @staticmethod
    def install_or_update_emojis():
        """下载或生成 Emoji 扩展库"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(EMOJI_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_EMOJI_ENTRIES, f, ensure_ascii=False, indent=2)
        return DictManager.get_emoji_info()

    @staticmethod
    def install_or_update_memes():
        """联网或更新新梗流行词库"""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # 这里预置丰富热梗，同时保留从远程 GitHub/Gitee Raw 链接更新的扩展槽位
        with open(MEME_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_MEME_ENTRIES, f, ensure_ascii=False, indent=2)
        return DictManager.get_meme_info()

    @staticmethod
    def load_emojis():
        if not EMOJI_FILE.exists():
            return []
        try:
            with open(EMOJI_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def load_memes():
        if not MEME_FILE.exists():
            return []
        try:
            with open(MEME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
