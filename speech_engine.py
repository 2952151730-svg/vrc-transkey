import array
import base64
import io
import json
import math
import threading
import time
import wave
from typing import Callable, Optional

import requests

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    pyaudio = None


VAD_THRESHOLDS = {
    "low": 220.0,      # 灵敏（安静环境）
    "medium": 480.0,   # 标准
    "high": 950.0,     # 抗噪（防背景音误触发）
}


def _calc_rms(pcm_bytes: bytes) -> float:
    """Compute RMS amplitude of 16-bit signed PCM audio."""
    if not pcm_bytes:
        return 0.0
    samples = array.array("h")
    samples.frombytes(pcm_bytes[: len(pcm_bytes) - (len(pcm_bytes) % 2)])
    n = len(samples)
    if n == 0:
        return 0.0
    total = 0
    for s in samples:
        total += s * s
    return math.sqrt(total / n)


def _to_mono_16k(pcm_bytes: bytes, src_rate: int, src_channels: int) -> bytes:
    """Convert 16-bit PCM of arbitrary rate/channels into 16kHz mono 16-bit PCM."""
    samples = array.array("h")
    samples.frombytes(pcm_bytes[: len(pcm_bytes) - (len(pcm_bytes) % 2)])
    if not samples:
        return b""

    if src_channels > 1:
        mono = array.array("h")
        step = src_channels
        for i in range(0, len(samples) - step + 1, step):
            acc = 0
            for c in range(step):
                acc += samples[i + c]
            mono.append(int(acc / step))
    else:
        mono = samples

    if src_rate == 16000 or not mono:
        return mono.tobytes()

    ratio = src_rate / 16000.0
    out_len = max(1, int(len(mono) / ratio))
    resampled = array.array("h")
    max_idx = len(mono) - 1
    for i in range(out_len):
        pos = i * ratio
        idx = int(pos)
        frac = pos - idx
        s0 = mono[idx]
        s1 = mono[min(idx + 1, max_idx)]
        resampled.append(int(s0 + (s1 - s0) * frac))
    return resampled.tobytes()


def _pcm_to_wav_bytes(pcm_16k_mono: bytes) -> bytes:
    """Wrap 16kHz mono 16-bit PCM into an in-memory WAV byte buffer."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(pcm_16k_mono)
    return buf.getvalue()


class SpeechEngine:
    """Dual-stream speech capture (Mic + WASAPI Loopback) with cloud STT & translation."""

    def __init__(
        self,
        voice_cfg: dict,
        trans_cfg: dict,
        translator,
        on_self_result: Callable[[str, str], None],
        on_other_result: Callable[[str, str], None],
        on_status: Optional[Callable[[str, str], None]] = None,
    ):
        self.voice_cfg = dict(voice_cfg or {})
        self.trans_cfg = dict(trans_cfg or {})
        self.translator = translator
        self.on_self_result = on_self_result
        self.on_other_result = on_other_result
        self.on_status = on_status

        self.session = requests.Session()
        self._lock = threading.Lock()
        self._mic_stop: Optional[threading.Event] = None
        self._loop_stop: Optional[threading.Event] = None
        self._mic_thread: Optional[threading.Thread] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._last_err_ts = 0.0

    def update_config(self, voice_cfg: dict, trans_cfg: dict):
        with self._lock:
            self.voice_cfg = dict(voice_cfg or {})
            self.trans_cfg = dict(trans_cfg or {})
        self.sync_workers()

    def sync_workers(self):
        """Start or stop Mic and WASAPI Loopback threads based on current flags."""
        mic_on = bool(self.voice_cfg.get("mic_enabled", False))
        loop_on = bool(self.voice_cfg.get("loopback_enabled", False))

        if mic_on and (self._mic_thread is None or not self._mic_thread.is_alive()):
            if pyaudio is None:
                self._emit_status("缺少 PyAudioWPatch 音频组件，无法启用语音采集", "warning")
            else:
                self._mic_stop = threading.Event()
                self._mic_thread = threading.Thread(
                    target=self._capture_loop,
                    args=("mic", self._mic_stop),
                    daemon=True,
                )
                self._mic_thread.start()
        elif not mic_on and self._mic_stop is not None:
            self._mic_stop.set()
            self._mic_stop = None

        if loop_on and (self._loop_thread is None or not self._loop_thread.is_alive()):
            if pyaudio is None:
                self._emit_status("缺少 PyAudioWPatch 音频组件，无法启用游戏语音捕获", "warning")
            else:
                self._loop_stop = threading.Event()
                self._loop_thread = threading.Thread(
                    target=self._capture_loop,
                    args=("loopback", self._loop_stop),
                    daemon=True,
                )
                self._loop_thread.start()
        elif not loop_on and self._loop_stop is not None:
            self._loop_stop.set()
            self._loop_stop = None

    def stop_all(self):
        if self._mic_stop:
            self._mic_stop.set()
            self._mic_stop = None
        if self._loop_stop:
            self._loop_stop.set()
            self._loop_stop = None

    def _emit_status(self, msg: str, level: str = "info"):
        now = time.time()
        if level == "warning" and now - self._last_err_ts < 4.0:
            return
        if level == "warning":
            self._last_err_ts = now
        if self.on_status:
            try:
                self.on_status(msg, level)
            except Exception:
                pass

    def _get_proxies(self) -> dict:
        if self.trans_cfg.get("network_mode", "global") == "direct":
            return {}
        proxy_url = (self.trans_cfg.get("proxy") or "").strip()
        if proxy_url:
            return {"http": proxy_url, "https": proxy_url}
        return {}

    def _capture_loop(self, role: str, stop_ev: threading.Event):
        pa = None
        stream = None
        try:
            pa = pyaudio.PyAudio()
            if role == "loopback":
                wasapi_info = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
                default_speakers = pa.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                if not default_speakers.get("isLoopbackDevice", False):
                    dev_info = None
                    for loopback in pa.get_loopback_device_info_generator():
                        if default_speakers["name"] in loopback["name"]:
                            dev_info = loopback
                            break
                    if dev_info is None:
                        for loopback in pa.get_loopback_device_info_generator():
                            dev_info = loopback
                            break
                    if dev_info is None:
                        self._emit_status("未找到 WASAPI 回环输出设备", "warning")
                        return
                else:
                    dev_info = default_speakers
            else:
                dev_info = pa.get_default_input_device_info()

            rate = int(dev_info.get("defaultSampleRate", 48000))
            channels = max(1, min(2, int(dev_info.get("maxInputChannels", 1))))
            chunk_frames = max(512, int(rate * 0.04))  # 40ms frames

            stream = pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=dev_info["index"],
                frames_per_buffer=chunk_frames,
            )

            print(f"[SpeechEngine] {role} 已就绪: {dev_info['name']} ({rate}Hz, {channels}ch)")

            speech_chunks = []
            in_speech = False
            speech_start = 0.0
            last_voice = 0.0

            while not stop_ev.is_set():
                try:
                    data = stream.read(chunk_frames, exception_on_overflow=False)
                except Exception:
                    time.sleep(0.02)
                    continue

                now = time.time()
                with self._lock:
                    sens = self.voice_cfg.get("vad_sensitivity", "medium")
                thresh = VAD_THRESHOLDS.get(sens, 480.0)
                if role == "loopback":
                    thresh *= 0.85

                rms = _calc_rms(data)
                if rms >= thresh:
                    if not in_speech:
                        in_speech = True
                        speech_start = now
                        speech_chunks = []
                    speech_chunks.append(data)
                    last_voice = now
                elif in_speech:
                    speech_chunks.append(data)
                    silence_dur = now - last_voice
                    total_dur = now - speech_start
                    if silence_dur >= 0.75 or total_dur >= 8.0:
                        raw_pcm = b"".join(speech_chunks)
                        speech_chunks = []
                        in_speech = False
                        if total_dur >= 0.45:
                            threading.Thread(
                                target=self._process_utterance,
                                args=(role, raw_pcm, rate, channels),
                                daemon=True,
                            ).start()
        except Exception as e:
            print(f"[SpeechEngine] {role} 采集异常: {e}")
            self._emit_status(f"{'游戏语音' if role == 'loopback' else '麦克风'}采集异常: {e}", "warning")
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            if pa is not None:
                try:
                    pa.terminate()
                except Exception:
                    pass

    def _process_utterance(self, role: str, raw_pcm: bytes, rate: int, channels: int):
        pcm_16k = _to_mono_16k(raw_pcm, rate, channels)
        if len(pcm_16k) < 16000 * 2 * 0.35:
            return

        with self._lock:
            vcfg = dict(self.voice_cfg)
            tcfg = dict(self.trans_cfg)

        stt_engine = vcfg.get("stt_engine", "gemini")
        if role == "mic":
            src_lang = tcfg.get("source_lang", "zh")
            tgt_lang = tcfg.get("target_lang", "en")
        else:
            src_lang = vcfg.get("other_source_lang", "en")
            tgt_lang = vcfg.get("hud_target_lang", "zh")

        orig, trans = "", ""
        if stt_engine == "gemini":
            orig, trans = self._stt_translate_gemini(pcm_16k, src_lang, tgt_lang, vcfg, tcfg, role)
        elif stt_engine == "groq":
            orig, trans = self._stt_translate_groq(pcm_16k, src_lang, tgt_lang, vcfg, tcfg, role)
        else:
            orig, trans = self._stt_translate_google_free(pcm_16k, src_lang, tgt_lang, role)

        orig = (orig or "").strip()
        trans = (trans or "").strip()
        if not orig and not trans:
            return
        if not trans:
            trans = orig

        if role == "mic":
            self.on_self_result(orig, trans)
        else:
            self.on_other_result(orig, trans)

    def _stt_translate_gemini(
        self, pcm_16k: bytes, src_lang: str, tgt_lang: str, vcfg: dict, tcfg: dict, role: str
    ):
        api_key = (tcfg.get("google_api_key") or "").strip()
        if not api_key:
            self._emit_status("请先在【翻译引擎】填入 Google Gemini API Key", "warning")
            return "", ""

        model = (tcfg.get("google_model") or "gemini-2.5-flash-lite").strip()
        wav_b64 = base64.b64encode(_pcm_to_wav_bytes(pcm_16k)).decode("ascii")

        lang_hint = "any spoken language" if role == "loopback" else src_lang
        prompt = (
            f"Listen to this short VRChat voice clip (speaker language hint: {lang_hint}). "
            f"1) Transcribe what was actually spoken into 'orig'. "
            f"2) Translate it naturally and colloquially into target language code '{tgt_lang}' as 'trans'. "
            f"If the clip is only background noise, breathing, or unintelligible, return {{\"orig\":\"\",\"trans\":\"\"}}. "
            f"Return ONLY valid JSON: {{\"orig\": \"...\", \"trans\": \"...\"}}."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "audio/wav", "data": wav_b64}},
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 180},
        }
        try:
            resp = self.session.post(url, json=payload, proxies=self._get_proxies(), timeout=8.0)
            if resp.status_code == 200:
                cands = resp.json().get("candidates", [])
                if cands:
                    text = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                    data = json.loads(text)
                    return data.get("orig", ""), data.get("trans", "")
            elif resp.status_code == 429:
                self._emit_status("Gemini 语音额度限流 (429)，可切换模型或稍候", "warning")
            else:
                self._emit_status(f"Gemini 语音识别异常 ({resp.status_code})", "warning")
        except Exception as e:
            print(f"[SpeechEngine] Gemini 异常: {e}")
        return "", ""

    def _stt_translate_groq(
        self, pcm_16k: bytes, src_lang: str, tgt_lang: str, vcfg: dict, tcfg: dict, role: str
    ):
        api_key = (vcfg.get("groq_api_key") or "").strip()
        if not api_key:
            self._emit_status("请先在【语音与HUD】填入 Groq API Key", "warning")
            return "", ""

        wav_bytes = _pcm_to_wav_bytes(pcm_16k)
        files = {"file": ("speech.wav", wav_bytes, "audio/wav")}
        data = {"model": "whisper-large-v3-turbo", "response_format": "json"}
        if role == "mic" and src_lang:
            data["language"] = src_lang.split("-")[0]

        try:
            resp = self.session.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files=files,
                data=data,
                proxies=self._get_proxies(),
                timeout=8.0,
            )
            if resp.status_code == 200:
                orig = (resp.json().get("text") or "").strip()
                if not orig:
                    return "", ""
                eff_src = "auto" if role == "loopback" else src_lang
                trans = self.translator.translate_sync(orig, target_lang=tgt_lang, source_lang=eff_src)
                return orig, trans
            elif resp.status_code == 429:
                self._emit_status("Groq Whisper 限流 (429)", "warning")
            else:
                self._emit_status(f"Groq Whisper 异常 ({resp.status_code})", "warning")
        except Exception as e:
            print(f"[SpeechEngine] Groq 异常: {e}")
        return "", ""

    def _stt_translate_google_free(self, pcm_16k: bytes, src_lang: str, tgt_lang: str, role: str):
        lang_map = {
            "zh": "zh-CN",
            "zh-TW": "zh-TW",
            "en": "en-US",
            "ja": "ja-JP",
            "ko": "ko-KR",
            "ru": "ru-RU",
            "fr": "fr-FR",
            "de": "de-DE",
            "es": "es-ES",
        }
        rec_lang = lang_map.get(src_lang, src_lang or "en-US")
        try:
            resp = self.session.post(
                f"https://www.google.com/speech-api/v2/recognize?output=json&lang={rec_lang}&client=chromium",
                headers={"Content-Type": "audio/l16; rate=16000"},
                data=pcm_16k,
                proxies=self._get_proxies(),
                timeout=6.0,
            )
            if resp.status_code == 200:
                orig = ""
                for line in resp.text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        alts = obj.get("result", [{}])[0].get("alternative", [])
                        if alts:
                            orig = alts[0].get("transcript", "").strip()
                            if orig:
                                break
                    except Exception:
                        continue
                if not orig:
                    return "", ""
                eff_src = "auto" if role == "loopback" else src_lang
                trans = self.translator.translate_sync(orig, target_lang=tgt_lang, source_lang=eff_src)
                return orig, trans
        except Exception as e:
            print(f"[SpeechEngine] Google 免Key语音异常: {e}")
        return "", ""
