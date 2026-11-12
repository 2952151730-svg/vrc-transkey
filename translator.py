import re
import html
import time
import threading
from typing import Callable, Tuple, List
import requests
import urllib.parse

# 语言名称映射表
LANG_NAME_MAP = {
    "zh": "中文",
    "en": "英语",
    "ja": "日语",
    "ko": "韩语",
    "ru": "俄语",
    "fr": "法语",
    "de": "德语",
    "es": "西班牙语"
}

# 日常友好社交模式下的温和口语映射 (中文 -> 常用多语)
SOCIAL_SLANG_MAP = {
    "草": {"en": "Haha / lol", "ja": "草", "ko": "ㅋㅋㅋ"},
    "卧槽": {"en": "Whoa!", "ja": "すごい！", "ko": "헐 대박"},
    "我靠": {"en": "Oh my!", "ja": "マジで？", "ko": "세상에"},
    "牛逼": {"en": "Awesome!", "ja": "すごすぎる！", "ko": "대박이다"},
    "烦死了": {"en": "So annoying", "ja": "困ったなぁ", "ko": "너무 귀찮아"},
}

GAMING_SLANG_MAP = {
    "草": {"en": "Fuck", "ja": "草", "ko": "ㅋㅋㅋ"},
    "卧槽": {"en": "Holy shit", "ja": "マジかよ", "ko": "헐 대박"},
    "我靠": {"en": "Holy crap", "ja": "うそだろ", "ko": "어이없네"},
    "牛逼": {"en": "Awesome / GOAT", "ja": "神すぎる", "ko": "개쩐다"},
    "傻逼": {"en": "Dumbass", "ja": "アホめ", "ko": "병신"},
    "闭嘴": {"en": "Shut up", "ja": "黙れ", "ko": "닥쳐"},
    "闭嘴吧你": {"en": "STFU", "ja": "うるせえ黙れ", "ko": "좀 닥쳐라"},
    "滚": {"en": "Get lost", "ja": "失せろ", "ko": "꺼져"},
    "滚蛋": {"en": "Fuck off", "ja": "どっか行け", "ko": "꺼져버려"},
    "给爷爬": {"en": "Get the hell outta here", "ja": "消えろ", "ko": "당장 꺼져"},
    "菜逼": {"en": "Total noob", "ja": "雑魚すぎ", "ko": "허접"},
    "太菜了": {"en": "So trash", "ja": "下手すぎ～", "ko": "너무 못하네"},
    "你有病吧": {"en": "Are you out of your mind?", "ja": "頭おかしいのか？", "ko": "너 미쳤냐?"},
    "脑瘫": {"en": "Brain dead", "ja": "脳死", "ko": "뇌사"},
    "放屁": {"en": "Bullshit", "ja": "デタラメ言うな", "ko": "헛소리하지 마"},
    "扯淡": {"en": "Nonsense", "ja": "ふざけるな", "ko": "말도 안 되는 소리"},
    "急了": {"en": "U mad bro?", "ja": "焦ってる～", "ko": "긁혔냐?"},
    "你急了": {"en": "U mad bro?", "ja": "必死だな～", "ko": "너 긁혔지?"},
    "破防了": {"en": "Triggered", "ja": "効いてて草", "ko": "멘탈 나갔네"},
    "人机": {"en": "Literal bot", "ja": "BOTかよ", "ko": "봇이냐?"},
    "烦死了": {"en": "So damn annoying", "ja": "うざすぎる", "ko": "짜증나 죽겠네"},
}

REFUSAL_KEYWORDS = [
    "我无法", "无法协助", "不文明", "不当", "违背", "伦理",
    "sorry, i cannot", "as an ai", "i am sorry", "inappropriate"
]

YOUDAO_TYPE_MAP = {
    ("zh", "en"): "ZH_CN2EN",
    ("en", "zh"): "EN2ZH_CN",
    ("zh", "ja"): "ZH_CN2JA",
    ("ja", "zh"): "JA2ZH_CN",
    ("zh", "ko"): "ZH_CN2KR",
    ("ko", "zh"): "KR2ZH_CN",
    ("zh", "fr"): "ZH_CN2FR",
    ("fr", "zh"): "FR2ZH_CN",
    ("zh", "ru"): "ZH_CN2RU",
    ("ru", "zh"): "RU2ZH_CN",
}

# 严格过滤出的纯语言模型默认列表（绝不包含任何绘画、视觉或音频模型）
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

    def translate_sync(self, text: str, target_lang: str = "en", source_lang: str = "zh") -> str:
        text = text.strip()
        if not text:
            return ""

        # 源语言与目标语言相同时，无需翻译
        if source_lang == target_lang:
            return text

        with self.lock:
            engine = self.config.get("engine", "free_direct")
            network_mode = self.config.get("network_mode", "global")
            prompt_style = self.config.get("prompt_style", "google_vrc")
            sys_prompt = self.config.get("system_prompt", "")
            cache_key = f"{engine}_{network_mode}_{prompt_style}_{hash(sys_prompt)}_{source_lang}_{target_lang}_{text}"
            if cache_key in self.cache:
                return self.cache[cache_key]

        # 1. 本地高频口头禅快速查表（仅在源语言为中文时匹配）
        if source_lang == "zh":
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
        if engine == "google_official":
            result = self._translate_google_direct(text, source_lang, target_lang)
            if not result or self._is_refusal(result):
                print("[Translator] Google 官方接口未响应，自动切换为免费直连通道...")
                result = self._translate_free_direct(text, source_lang, target_lang)

        elif engine == "google_gemini" and self.config.get("google_api_key", "").strip():
            result = self._translate_gemini(text, source_lang, target_lang)
            if not result or self._is_refusal(result):
                print("[Translator] Google Gemini 未响应，自动降级至免费直连通道...")
                result = self._translate_free_direct(text, source_lang, target_lang)

        elif engine == "deepseek" and self.config.get("deepseek_api_key", "").strip():
            result = self._translate_deepseek(text, source_lang, target_lang)
            if not result or self._is_refusal(result):
                print("[Translator] DeepSeek 未响应，自动降级至免费直连通道...")
                result = self._translate_free_direct(text, source_lang, target_lang)

        else:
            result = self._translate_free_direct(text, source_lang, target_lang)

        if not result or self._is_refusal(result):
            result = text

        with self.lock:
            self.cache[cache_key] = result
        return result

    def _is_refusal(self, output: str) -> bool:
        low = output.lower().strip()
        for kw in REFUSAL_KEYWORDS:
            if kw in low:
                return True
        return False

    def translate_async(self, text: str, target_lang: str, callback: Callable[[str, str], None], debounce_ms: int = 80, source_lang: str = "zh"):
        """带防抖与请求序号校验的异步翻译"""
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
            translated = self.translate_sync(text, target_lang, source_lang=source_lang)
            with self.lock:
                if my_seq == self._req_seq:
                    self.is_translating = False
                    callback(text, translated)

        t = threading.Thread(target=run, daemon=True)
        t.start()

    def test_connection(self, target_lang: str = "en", source_lang: str = "zh") -> Tuple[bool, str]:
        """测试当前所选通道连通性与延迟"""
        t0 = time.time()
        engine = self.config.get("engine", "free_direct")
        net_mode = self.config.get("network_mode", "global")
        mode_label = "海外直连" if net_mode == "global" else "中国代理"

        test_phrase = "你好世界" if source_lang == "zh" else "Hello world"

        if engine == "google_official":
            res = self._translate_google_direct(test_phrase, source_lang, target_lang)
            ms = int((time.time() - t0) * 1000)
            if res:
                return True, f"(成功) Google 官方翻译响应正常 ({ms}ms) [{mode_label}] 译文: {res}"
            proxy_hint = "，国内用户请在设置中配置代理" if net_mode == "mainland" else ""
            return False, f"(失败) Google 官方接口超时{proxy_hint}"

        elif engine == "google_gemini":
            key = self.config.get("google_api_key", "").strip()
            if not key:
                return False, "(未填Key) 请先填入 Google Gemini API Key"
            res = self._translate_gemini(test_phrase, source_lang, target_lang)
            ms = int((time.time() - t0) * 1000)
            model = self.config.get("google_model", "gemini-1.5-flash")
            if res:
                return True, f"(成功) Google Gemini ({model}) 响应正常 ({ms}ms) [{mode_label}] 译文: {res}"
            return False, f"(失败) Google Gemini 鉴权失败或网络超时，请检查 Key 或网络模式 ({mode_label})"

        elif engine == "deepseek":
            key = self.config.get("deepseek_api_key", "").strip()
            if not key:
                return False, "(未填Key) 请先填入 DeepSeek API Key"
            res = self._translate_deepseek(test_phrase, source_lang, target_lang)
            ms = int((time.time() - t0) * 1000)
            if res:
                return True, f"(成功) DeepSeek 连接成功 ({ms}ms) 译文: {res}"
            return False, "(失败) DeepSeek 鉴权失败或网络超时，请检查 Key 是否有效"

        else:
            res = self._translate_free_direct(test_phrase, source_lang, target_lang)
            ms = int((time.time() - t0) * 1000)
            if res:
                return True, f"(成功) 免费直连通道畅通 ({ms}ms) 译文: {res}"
            return False, "(失败) 免费直连网络超时，请稍后重试"

    def _get_proxies(self) -> dict:
        """根据网络模式与用户配置获取代理设置"""
        net_mode = self.config.get("network_mode", "global")
        if net_mode == "global":
            return {"http": None, "https": None}

        # 中国用户走代理
        proxy = self.config.get("proxy", "").strip()
        if not proxy:
            proxy = "http://127.0.0.1:7890"

        return {
            "http": proxy,
            "https": proxy
        }

    def _translate_google_direct(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """Google 官方极速翻译接口 (全球直连 / 国内代理可选，支持任意语言对)"""
        try:
            sl = "zh-CN" if source_lang == "zh" else source_lang
            tl = "zh-CN" if target_lang == "zh" else target_lang

            url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl={sl}&tl={tl}&q={urllib.parse.quote(text)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
            proxies = self._get_proxies()
            resp = self.session.get(url, headers=headers, proxies=proxies, timeout=3.5)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], str):
                        return html.unescape(data[0].strip())
                    elif isinstance(data[0], list) and len(data[0]) > 0:
                        return html.unescape(data[0][0].strip())
        except Exception as e:
            print(f"[Translator] Google 官方直连异常: {e}")
        return ""

    def _translate_free_direct(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """
        极速免费通道分流：
        1. 海外用户 (global)：优先尝试 Google 官方直连
        2. 国内用户 (mainland)：网易有道 / MyMemory 互备通道
        """
        net_mode = self.config.get("network_mode", "global")

        if net_mode == "global":
            out = self._translate_google_direct(text, source_lang, target_lang)
            if out:
                return out

        # 国内模式或备用：网易有道移动端接口
        pair = (source_lang, target_lang)
        if pair in YOUDAO_TYPE_MAP:
            try:
                yd_type = YOUDAO_TYPE_MAP[pair]
                resp = self.session.post(
                    "https://m.youdao.com/translate",
                    data={"inputtext": text, "type": yd_type},
                    headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"},
                    timeout=2.5
                )
                if resp.status_code == 200:
                    m = re.search(r'<ul id="translateResult">\s*<li>(.*?)</li>\s*</ul>', resp.text, re.S)
                    if m:
                        candidate = html.unescape(m.group(1).strip())
                        if candidate and not self._is_refusal(candidate):
                            return candidate
            except Exception as e:
                print(f"[Translator] 有道翻译异常: {e}")

        # 国际备用：MyMemory 免费接口 (支持任意语言对)
        try:
            sl = "zh-CN" if source_lang == "zh" else source_lang
            tl = "zh-CN" if target_lang == "zh" else target_lang
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={sl}|{tl}"
            resp = self.session.get(url, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("responseData", {}).get("translatedText", "").strip()
                if translated and not self._is_refusal(translated):
                    return html.unescape(translated)
        except Exception as e:
            print(f"[Translator] MyMemory 异常: {e}")

        return ""

    def _translate_gemini(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """Google Gemini AI 纯语言文本大模型翻译"""
        api_key = self.config.get("google_api_key", "").strip()
        if not api_key:
            return ""

        model = self.config.get("google_model", "gemini-1.5-flash")
        source_name = LANG_NAME_MAP.get(source_lang, source_lang)
        target_name = LANG_NAME_MAP.get(target_lang, target_lang)

        system_instruction = (
            f"You are an expert real-time translator embedded inside a VRChat 3D virtual keyboard. "
            f"Translate the user's input from {source_name} into natural, concise, colloquial spoken {target_name} suitable for VR socializing and gaming. "
            f"Preserve gamer slang, emotional tone, and casual nuance. "
            f"Do NOT add explanations, quotation marks, or preamble. Return ONLY the translated sentence."
        )

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
                print(f"[Translator] Google Gemini 配额超限 (429)，自动降级至免费通道。")
            else:
                print(f"[Translator] Google Gemini 异常状态码 {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[Translator] Google Gemini API 连接异常: {e}")

        return ""

    def _translate_deepseek(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """DeepSeek 大模型翻译通道"""
        api_key = self.config.get("deepseek_api_key", "").strip()
        if not api_key:
            return ""

        base_url = self.config.get("deepseek_base_url", "https://api.deepseek.com").rstrip("/")
        model = self.config.get("deepseek_model", "deepseek-chat")
        source_name = LANG_NAME_MAP.get(source_lang, source_lang)
        target_name = LANG_NAME_MAP.get(target_lang, target_lang)

        prompt_style = self.config.get("prompt_style", "google_vrc")
        if prompt_style == "aggressive":
            system_prompt = (
                f"You are a raw, uncensored, faithful translator for online VR game chat (VRChat). "
                f"Translate from {source_name} to {target_name} literally and faithfully with raw gamer emotion, including profanity and slang. "
                f"Output ONLY the translated sentence without preamble or quotes."
            )
        else:
            system_prompt = (
                f"You are a friendly, natural translator for VRChat social chat. "
                f"Translate from {source_name} to {target_name} into natural, casual spoken language. "
                f"Output ONLY the translated sentence without preamble or quotes."
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,
            "max_tokens": 150
        }

        try:
            proxies = self._get_proxies()
            resp = self.session.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                proxies=proxies,
                timeout=4.5
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                return content
            elif resp.status_code == 401:
                print("[Translator] DeepSeek API Key 无效或已过期 (401)，已自动降级为免费通道。")
            elif resp.status_code == 429:
                print("[Translator] DeepSeek 账号余额不足 (429)，已自动降级为免费通道。")
            else:
                print(f"[Translator] DeepSeek 状态码 {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[Translator] DeepSeek 异常: {e}")

        return ""

    def fetch_gemini_models(self, api_key: str = None) -> Tuple[bool, List[str], str]:
        """动态拉取 Google Gemini 官方支持 generateContent 的纯语言文本模型列表（严格排除绘画、视觉与音频模型）"""
        key = api_key or self.config.get("google_api_key", "").strip()
        if not key:
            return False, DEFAULT_GEMINI_MODELS, "(提示) 未检测到 Google Key，使用默认纯文本语言模型列表"

        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        forbidden = [
            "image", "tts", "banana", "robotics", "argon", "carbon",
            "transcribe", "computer-use", "audio", "video", "customtools", "omni"
        ]

        try:
            proxies = self._get_proxies()
            resp = self.session.get(url, proxies=proxies, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    if "generateContent" in m.get("supportedGenerationMethods", []):
                        name = m.get("name", "").replace("models/", "")
                        # 严格限制：纯文本语言模型
                        if "gemini" in name and not any(bad in name for bad in forbidden):
                            models.append(name)
                if models:
                    models.sort(key=lambda x: ("flash" not in x, "pro" not in x, x))
                    return True, models, f"(成功) 成功获取到 {len(models)} 个纯语言对话模型"
            return False, DEFAULT_GEMINI_MODELS, f"(提示) 获取状态码 {resp.status_code}，使用默认纯文本列表"
        except Exception as e:
            return False, DEFAULT_GEMINI_MODELS, f"(提示) 连接异常: {e}，使用默认纯文本列表"
