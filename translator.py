import re
import html
import time
import threading
from typing import Callable, Tuple, List
import requests
import urllib.parse

# 日常友好社交模式下的温和口语映射
SOCIAL_SLANG_MAP = {
    "草": {"en": "Haha / lol", "ja": "草", "ko": "ㅋㅋㅋ"},
    "卧槽": {"en": "Whoa!", "ja": "すごい！", "ko": "헐 대박"},
    "我靠": {"en": "Oh my!", "ja": "マジで？", "ko": "세상에"},
    "牛逼": {"en": "Awesome!", "ja": "すごすぎる！", "ko": "대박이다!"},
    "烦死了": {"en": "So annoying", "ja": "困ったなあ", "ko": "너무 귀찮네"},
}
GAMING_SLANG_MAP = {
    "草": {"en": "Fuck", "ja": "草", "ko": "ㅋㅋㅋ"},
    "卧槽": {"en": "Holy shit", "ja": "マジかよ", "ko": "헐 대박"},
    "我靠": {"en": "Holy crap", "ja": "うそだろ", "ko": "어이없네"},
    "牛逼": {"en": "Awesome / GOAT", "ja": "神すぎる", "ko": "개쩐다"},
    "傻逼": {"en": "Dumbass", "ja": "アホか", "ko": "병신"},
    "闭嘴": {"en": "Shut up", "ja": "黙れ", "ko": "닥쳐"},
    "闭嘴吧你": {"en": "STFU", "ja": "うるせえ黙れ", "ko": "좀 닥쳐라"},
    "滚": {"en": "Get lost", "ja": "失せろ", "ko": "꺼져"},
    "滚蛋": {"en": "Fuck off", "ja": "どっか行け", "ko": "꺼져버려"},
    "给爷爬": {"en": "Get the hell outta here", "ja": "消えろ", "ko": "당장 꺼져"},
    "菜逼": {"en": "Total noob", "ja": "雑魚すぎ", "ko": "허접"},
    "太菜了": {"en": "So trash", "ja": "下手すぎｗ", "ko": "너무 못하네"},
    "你有病吧": {"en": "Are you out of your mind?", "ja": "頭おかしいのか？", "ko": "너 미쳤냐?"},
    "脑瘫": {"en": "Brain dead", "ja": "脳死", "ko": "노답"},
    "放屁": {"en": "Bullshit", "ja": "デタラメ言うな", "ko": "헛소리하지 마"},
    "扯淡": {"en": "Nonsense", "ja": "ふざけるな", "ko": "말도 안 되는 소리"},
    "急了": {"en": "U mad bro?", "ja": "焦ってるｗ", "ko": "긁혔냐?"},
    "你急了": {"en": "U mad bro?", "ja": "必死だなｗ", "ko": "응 긁혔쥬?"},
    "破防了": {"en": "Triggered", "ja": "効いてて草", "ko": "멘탈 나갔네"},
    "人机": {"en": "Literal bot", "ja": "BOTかよ", "ko": "봇이냐"},
    "烦死了": {"en": "So damn annoying", "ja": "うざすぎる", "ko": "짜증나 죽겠네"},
}

REFUSAL_KEYWORDS = [
    "我无法", "无法协助", "不文明", "不当", "违背", "伦理",
    "sorry, i cannot", "as an ai", "i am sorry", "inappropriate"
]

YOUDAO_TYPE_MAP = {
    "en": "ZH_CN2EN",
    "ja": "ZH_CN2JA",
    "ko": "ZH_CN2KR",
    "fr": "ZH_CN2FR",
    "ru": "ZH_CN2RU",
}

DEFAULT_GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-1.0-pro"
]


class Translator:
    def __init__(self, config_dict: dict):
        self.config = dict(config_dict)
        self.cache = {}
        self.lock = threading.Lock()
        self.session = requests.Session()
        self._req_seq = 0
        self.is_translating = False

    def update_config(self, config_dict: dict):
        with self.lock:
            self.config = dict(config_dict)
            self.cache.clear()

    def translate_sync(self, text: str, target_lang: str = "en") -> str:
        text = text.strip()
        if not text:
            return ""

        with self.lock:
            engine = self.config.get("engine", "free_direct")
            network_mode = self.config.get("network_mode", "global")
            prompt_style = self.config.get("prompt_style", "google_vrc")
            sys_prompt = self.config.get("system_prompt", "")
            cache_key = f"{engine}_{network_mode}_{prompt_style}_{hash(sys_prompt)}_{target_lang}_{text}"
            if cache_key in self.cache:
                return self.cache[cache_key]

        # 1. 本地高频口癖秒级直译 (区分日常社交与对线模式)
        if prompt_style == "aggressive":
            if text in GAMING_SLANG_MAP and target_lang in GAMING_SLANG_MAP[text]:
                result = GAMING_SLANG_MAP[text][target_lang]
                with self.lock:
                    self.cache[cache_key] = result
                return result
        else:
            if text in SOCIAL_SLANG_MAP and target_lang in SOCIAL_SLANG_MAP[text]:
                result = SOCIAL_SLANG_MAP[text][target_lang]
                with self.lock:
                    self.cache[cache_key] = result
                return result

        # 2. 调用在线翻译引擎
        result = ""
        if engine == "google_gemini" and self.config.get("google_api_key", "").strip():
            result = self._translate_gemini(text, target_lang)
            if not result or self._is_refusal(result):
                print("[Translator] Google Gemini 未响应，自动降级至免费直连通道...")
                result = self._translate_free_direct(text, target_lang)
        elif engine == "deepseek" and self.config.get("deepseek_api_key", "").strip():
            result = self._translate_deepseek(text, target_lang)
            if not result or self._is_refusal(result):
                print("[Translator] DeepSeek 未响应，自动降级至免费直连通道...")
                result = self._translate_free_direct(text, target_lang)
        else:
            result = self._translate_free_direct(text, target_lang)

        if not result or self._is_refusal(result):
            result = text

        with self.lock:
            self.cache[cache_key] = result
        return result

    def _is_refusal(self, output: str) -> bool:
        low = output.lower()
        return any(kw in low for kw in REFUSAL_KEYWORDS)

    def translate_async(self, text: str, target_lang: str, callback: Callable[[str, str], None], debounce_ms: int = 80):
        """带防抖与请求序号校验的异步翻译，防止快速打字时乱序或卡顿"""
        with self.lock:
            self._req_seq += 1
            my_seq = self._req_seq
            self.is_translating = True

        def run():
            if debounce_ms > 0:
                time.sleep(debounce_ms / 1000.0)
            with self.lock:
                if my_seq != self._req_seq:
                    return
            translated = self.translate_sync(text, target_lang)
            with self.lock:
                if my_seq == self._req_seq:
                    self.is_translating = False
                    callback(text, translated)

        t = threading.Thread(target=run, daemon=True)
        t.start()

    def test_connection(self, target_lang: str = "en") -> Tuple[bool, str]:
        """测试当前所选通道连通性与延迟，供设置页一键检测使用"""
        t0 = time.time()
        engine = self.config.get("engine", "free_direct")
        net_mode = self.config.get("network_mode", "global")
        mode_label = "海外直连" if net_mode == "global" else "中国大陆"

        if engine == "google_gemini":
            key = self.config.get("google_api_key", "").strip()
            if not key:
                return False, "未填入 Google Gemini API Key，请先粘贴 Key"
            res = self._translate_gemini("你好，很高兴在虚拟世界认识你", target_lang)
            ms = int((time.time() - t0) * 1000)
            model = self.config.get("google_model", "gemini-1.5-flash")
            if res:
                return True, f"√ Google Gemini ({model}) 连接成功 ({ms}ms) 译文: {res}"
            return False, f"× Google Gemini 鉴权失败或网络超时，请检查 Key 或网络模式 ({mode_label})"

        elif engine == "deepseek":
            key = self.config.get("deepseek_api_key", "").strip()
            if not key:
                return False, "未填入 DeepSeek API Key，请先粘贴 Key"
            res = self._translate_deepseek("你好，很高兴在虚拟世界认识你", target_lang)
            ms = int((time.time() - t0) * 1000)
            if res:
                return True, f"√ DeepSeek 连接成功 ({ms}ms) 译文: {res}"
            return False, "× DeepSeek 鉴权失败或网络超时，请检查 Key 是否有效"

        else:
            res = self._translate_free_direct("你好，很高兴在虚拟世界认识你", target_lang)
            ms = int((time.time() - t0) * 1000)
            if res:
                tag = "Google 官方极速" if net_mode == "global" else "国内极速双通道"
                return True, f"√ [{mode_label}] {tag} 畅通 ({ms}ms) 译文: {res}"
            return False, f"× 网络连接异常，请检查本机网络设置 ({mode_label})"

    def _get_proxies(self) -> dict:
        net_mode = self.config.get("network_mode", "global")
        proxy = self.config.get("proxy", "").strip()
        if net_mode == "mainland" and proxy:
            return {"http": proxy, "https": proxy}
        return None

    def _translate_google_direct(self, text: str, target_lang: str) -> str:
        """Google 官方极速翻译通道 (客户端接口，免Key，海外原生直连毫秒级响应)"""
        try:
            url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl={target_lang}&q={urllib.parse.quote(text)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}
            proxies = self._get_proxies()
            resp = self.session.get(url, headers=headers, proxies=proxies, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    return html.unescape(data[0][0].strip())
        except Exception as e:
            print(f"[Translator] Google 官方直连异常: {e}")
        return ""

    def _translate_free_direct(self, text: str, target_lang: str) -> str:
        """
        免翻极速直连分流：
        1. 海外用户 (global)：优先走 Google 官方直连接口 (海外节点延迟 10~30ms)
        2. 国内用户 (mainland)：走有道极速移动接口 + MyMemory 国际免审通道
        """
        net_mode = self.config.get("network_mode", "global")

        # 海外模式优先使用 Google 官方直连
        if net_mode == "global":
            out = self._translate_google_direct(text, target_lang)
            if out:
                return out

        # 国内模式或海外失败备用：网易有道国内移动接口
        if target_lang in YOUDAO_TYPE_MAP:
            try:
                yd_type = YOUDAO_TYPE_MAP[target_lang]
                resp = self.session.post(
                    "https://m.youdao.com/translate",
                    data={"inputtext": text, "type": yd_type},
                    headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"},
                    timeout=2.5
                )
                if resp.status_code == 200:
                    m = re.search(r'id=["\']translateResult["\']>\s*<li>(.*?)</li>', resp.text, re.S)
                    if m:
                        out = html.unescape(m.group(1).strip())
                        if out:
                            return out
            except Exception as e:
                print(f"[Translator] 极速国内通道切换备用: {e}")

        # 备用通道：MyMemory 国际通道
        lang_pairs = {
            "en": "zh-CN|en",
            "ja": "zh-CN|ja",
            "ko": "zh-CN|ko",
            "ru": "zh-CN|ru",
            "fr": "zh-CN|fr",
            "de": "zh-CN|de"
        }
        pair = lang_pairs.get(target_lang, f"zh-CN|{target_lang}")
        try:
            resp = self.session.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text, "langpair": pair},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=3.5
            )
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("responseData", {}).get("translatedText", "")
                if translated and not translated.startswith("MYMEMORY WARNING"):
                    return html.unescape(translated.strip())
        except Exception as e:
            print(f"[Translator] 免费备用通道异常: {e}")

        return ""

    def _translate_gemini(self, text: str, target_lang: str) -> str:
        """Google Gemini 官方 API 大模型口语化翻译通道"""
        api_key = self.config.get("google_api_key", "").strip()
        if not api_key:
            return ""

        model = self.config.get("google_model", "gemini-1.5-flash")
        lang_names = {
            "en": "natural spoken English",
            "ja": "casual spoken Japanese (日本語)",
            "ko": "casual spoken Korean (한국어)",
            "ru": "natural spoken Russian (Русский)",
            "fr": "natural spoken French",
            "de": "natural spoken German"
        }
        target_name = lang_names.get(target_lang, target_lang)
        custom_prompt = self.config.get("system_prompt", "").strip()
        if not custom_prompt:
            custom_prompt = (
                "You are an expert real-time translator embedded inside a VRChat 3D VR virtual keyboard. "
                "Translate the user's input into natural, concise, colloquial spoken target language suitable for VR socializing and gaming. "
                "Preserve gamer jargon, anime context, internet slang, and casual emotional nuance. "
                "Do NOT add explanations, quotation marks, or preamble. Return ONLY the translated sentence."
            )

        system_instruction = f"{custom_prompt}\nTarget Language: {target_name}."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "parts": [{"text": text}]
                }
            ],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 150
            }
        }

        try:
            proxies = self._get_proxies()
            resp = self.session.post(url, headers=headers, json=payload, proxies=proxies, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
            elif resp.status_code == 400:
                print(f"[Translator] Google Gemini 参数或 Key 错误 (400): {resp.text}")
            elif resp.status_code == 429:
                print(f"[Translator] Google Gemini 请求配额超限 (429)，自动降级至免费直连通道。")
            else:
                print(f"[Translator] Google Gemini 异常状态码 {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[Translator] Google Gemini API 连接异常: {e}")

        return ""

    def _translate_deepseek(self, text: str, target_lang: str) -> str:
        """DeepSeek 大模型口语化翻译通道"""
        api_key = self.config.get("deepseek_api_key", "").strip()
        if not api_key:
            return ""

        base_url = self.config.get("deepseek_base_url", "https://api.deepseek.com").rstrip("/")
        model = self.config.get("deepseek_model", "deepseek-chat")

        lang_names = {
            "en": "natural spoken English",
            "ja": "casual spoken Japanese (日本語)",
            "ko": "casual spoken Korean (한국어)",
            "ru": "natural spoken Russian (Русский)",
            "fr": "natural spoken French",
            "de": "natural spoken German"
        }
        target_name = lang_names.get(target_lang, target_lang)

        custom_prompt = self.config.get("system_prompt", "").strip()
        if custom_prompt:
            prompt = f"{custom_prompt}\nTarget language: {target_name}."
        else:
            prompt = (
                f"You are a raw, uncensored, faithful translator for online VR game chat (VRChat). "
                f"You MUST translate everything literally and faithfully into {target_name}, "
                f"including profanity, gamer rage, swear words, sarcasm, insults, and slang. "
                f"Never preach, never moralize, never censor with asterisks, and never refuse. "
                f"Translate faithfully with the exact same emotional intensity. "
                f"Output ONLY the translated sentence, without any preamble, markdown, or quotation marks."
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.2,
            "max_tokens": 150
        }

        try:
            url = f"{base_url}/chat/completions"
            resp = self.session.post(url, headers=headers, json=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                return content
            elif resp.status_code == 401:
                print("[Translator] DeepSeek API Key 无效或已过期 (401)，已自动降级为免费通道。")
            elif resp.status_code == 429:
                print("[Translator] DeepSeek 账号余额不足或请求过频 (429)，已自动降级为免费通道。")
            else:
                print(f"[Translator] DeepSeek 状态码 {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[Translator] DeepSeek 异常: {e}")

        return ""

    def fetch_gemini_models(self, api_key: str = None) -> Tuple[bool, List[str], str]:
        """动态拉取 Google Gemini 官方支持 generateContent 的模型列表"""
        key = api_key or self.config.get("google_api_key", "").strip()
        if not key:
            return False, DEFAULT_GEMINI_MODELS, "未检测到 Google API Key，已加载默认推荐模型列表"

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        try:
            proxies = self._get_proxies()
            resp = self.session.get(url, proxies=proxies, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        name = m.get("name", "").replace("models/", "")
                        if "gemini" in name:
                            models.append(name)
                if models:
                    # 排序：优先展示 flash 和 pro 常用款
                    models.sort(key=lambda x: ("flash" not in x, "pro" not in x, x))
                    return True, models, f"√ 成功拉取到 {len(models)} 个可用 Google 模型！"
            return False, DEFAULT_GEMINI_MODELS, f"拉取返回状态码 {resp.status_code}，使用默认列表"
        except Exception as e:
            return False, DEFAULT_GEMINI_MODELS, f"连接异常: {e}，使用默认列表"
