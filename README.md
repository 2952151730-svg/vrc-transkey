# VRC-TransKey (灵动轻量 VR 空间翻译输入法)

> **[English](#english-summary) | [简体中文](#简体中文说明)**  
> 专为 **VRChat** 与 **SteamVR** 量身定制的超轻量空间 3D 虚拟键盘与 AI 实时双向翻译系统。  
> 具备深度中文拼音词库优化、首字母简拼联想、Google AI 与 DeepSeek 双引擎支持，以及针对海外与国内用户的全球智能网络路由。

---

<a id="简体中文说明"></a>
## 🌟 核心亮点与技术突破

### 1. 彻底解决 VR 行业痛点：超越传统键盘与外部工具
* **对比海外虚拟键盘（如 Papi Keyboard 等）**：
  * 海外方案大多仅针对英文 26 键布局设计，**严重缺乏对中文拼音输入的底层支持**，中文输入体验极度破碎甚至直接乱码。
  * **VRC-TransKey** 专为中文母语用户深度重构，内置超 **57 万条高频中文词库矩阵**，支持全拼、**首字母缩写简拼（如 `wsm` ➔ `为什么`、`yyds`、`v50` ➔ `v我50` 等）**，大幅缩短在 VR 空间中抬手选词的疲劳度。
* **对比外部翻译工具（如 VRCT 等）**：
  * 传统翻译工具多数依赖头显外部桌面窗口或麦克风语音抓取，玩家在 VRChat 中打字沟通时往往需要频繁切屏或脱离沉浸视角。
  * **VRC-TransKey** 是纯粹的 **OpenVR 原生三维空间悬浮叠加层（In-VR 3D Overlay）**，直接在虚拟视线黄金区域内提供实体化悬浮键盘，打字的同时毫秒级广播 OSC 聊天气泡，保持 100% 沉浸感。

### 2. 极致轻量化架构（~30MB 内存常驻）
* **拒绝 Chromium/CEF 膨胀**：传统内嵌浏览器方案动辄占用 600MB+ 内存，极易导致 VR 掉帧卡顿。
* **自研 Direct 渲染管道**：核心常驻内存仅约 **30MB**，冷启动响应低于 50ms。
* **模块化按需加载**：Emoji 表情包（~0.05MB）与网络流行热梗词库（~0.15MB）独立按需载入，绝不浪费显存与内存。

### 3. 全球智能网络路由与双 AI 引擎
* **网络分区优化**：
  * 🌍 **海外用户（Global Mode）**：全功能秒级原生直连！Google 免费翻译接口与 Google Gemini 官方 API 无需任何代理，超低延迟即开即用。
  * 🇨🇳 **中国大陆用户（Mainland China Mode）**：完美支持 DeepSeek API 极速国内直连，或配置本地代理（如 `http://127.0.0.1:7890`）直达 Google 生态服务，亦可使用内置免翻极速备用通道。
* **双 AI 翻译引擎支持**：
  * **Google Gemini AI 引擎**：支持 `gemini-1.5-flash`、`gemini-2.0-flash` 等官方模型，支持一键动态拉取模型列表自由切换，具备强大的多语言语境感知能力。
  * **DeepSeek 引擎**：语义高度拟人化，精准契合日常口语与游戏社交。
  * **专有游戏黑话提示词（System Prompt）**：告别机翻生硬感，支持自定义提示词，精准把控友好社交或硬核对线情绪。

### 4. 舒适人眼工效学与空间手柄交互
* **视线正下方黄金阅读区**：唤出时自动定位在当前头显**正前方 0.58 米、下俯 24° 夹角**，平视不遮挡镜子与好友，微低头即可舒适打字。
* **手柄自由拖拽定格（Grab & Drag）**：激光指向顶栏把手，按住扳机键即可在三维空间中拉近、推远或悬浮于身侧，松开即刻锁定空间坐标。
* **快捷按键定制**：默认支持双击右手柄摇杆秒级唤出/收起，可任意绑定至 B 键或侧键。

---

## ⚙️ 配置文件说明 (`config.json`)

```json
{
  "hotkey": {
    "controller": "right",          // "right" (右手) 或 "left" (左手)
    "button": "thumbstick",         // 唤出按键: "thumbstick"(摇杆), "b_button", "grip"
    "double_click": true,           // 是否双击触发
    "double_click_interval_ms": 420 // 双击间隔判定
  },
  "overlay": {
    "distance_m": 0.58,             // 距离眼睛米数
    "pitch_deg": -24.0,             // 下俯角度
    "width_m": 0.42,                // VR中键盘物理宽度
    "alpha": 0.95                   // 半透明度
  },
  "vrchat": {
    "osc_ip": "127.0.0.1",
    "osc_port": 9000,
    "send_typing_indicator": true   // 同步头顶打字省略号 ...
  },
  "translation": {
    "network_mode": "global",       // "global"(海外直连) 或 "mainland"(大陆模式)
    "engine": "google_gemini",      // "google_gemini", "deepseek", 或 "free_direct"
    "target_lang": "en",            // 目标语言 (en/ja/ko/ru/fr/de)
    "send_mode": "translated_only", // "translated_only"(纯外语), "bilingual"(双语), "original_only"(纯中文)
    "google": {
      "api_key": "your_gemini_api_key_here",
      "model": "gemini-1.5-flash",  // 可通过接口一键拉取模型列表动态选择
      "prompt": "You are a professional spoken translator for VRChat VR social environments..."
    },
    "deepseek": {
      "api_key": "your_deepseek_api_key_here",
      "model": "deepseek-chat"
    },
    "proxy": ""                     // 大陆模式下访问 Google 服务填入的本地代理 (如 http://127.0.0.1:7890)
  }
}
```

---

<a id="english-summary"></a>
## 🌐 English Summary

### Overview
**VRC-TransKey** is a specialized, ultra-lightweight in-VR 3D spatial virtual keyboard and real-time bidirectional AI translation system crafted for **VRChat** and **SteamVR**. 

### Key Differentiators
1. **Designed for Complex Asian Input**: Unlike traditional Western VR keyboards (e.g., Papi Keyboard) that struggle with multi-byte Asian characters, VRC-TransKey embeds a **570,000+ entry Chinese lexical database** supporting full Pinyin and initial consonant abbreviations (e.g., `wsm` ➔ `为什么`).
2. **Native 3D Spatial Overlay**: Unlike desktop-tethered translation tools (e.g., VRCT) that require window grabbing or context switching, VRC-TransKey runs as a native OpenVR overlay inside the 3D VR environment with 6-DoF spatial drag-and-drop.
3. **Dual AI Engine Architecture**:
   - **Google Gemini API**: Full integration with Gemini models (`gemini-1.5-flash`, `gemini-2.0-flash`) featuring dynamic model listing and low-latency context-aware slang translation.
   - **DeepSeek API**: High-fidelity colloquial translation for natural conversational flow.
4. **Global Network Routing**:
   - **Global Mode**: Direct, lightning-fast connectivity to Google Translation & Gemini APIs without proxies.
   - **Mainland China Mode**: Seamless integration with DeepSeek or configurable local proxy routing for Google services.
5. **Ultra-Low Memory Footprint**: Bypasses heavy Chromium/CEF runtimes, operating within **~30MB of RAM** with 60FPS+ render performance.

---

## 📄 License
This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
