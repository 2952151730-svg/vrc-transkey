# VRC-TransKey

> 专为 **VRChat** 与 **SteamVR** 定制的轻量虚拟键盘与实时翻译小工具。  
> An ultra-lightweight in-VR keyboard & real-time translation tool for VRChat & SteamVR.

---

## 💡 背景与解决的问题

在虚拟现实与跨语言社交场景中，文本交互普遍面临两大体验瓶颈：
1. **空间输入体验欠佳**：主流 VR 虚拟键盘对中文拼音支持薄弱，选词繁琐且缺乏本地化词库；
2. **切屏查词打断沉浸感**：在游戏内与外部翻译软件之间频繁切换，严重影响实时对话的流畅度。

**TransKey VR** 致力于打造低延迟、无缝的空间输入与翻译工具：  
用户在头显内输入时即可实时获得高质量双向译文预览，确认后通过本地 OSC 协议毫秒级同步至虚拟角色的 ChatBox，实现零干扰的跨语言沉浸交流。

---

## 🌟 主要功能与特点

- **打字即时翻译**：
  - 拼音打字确认后，上方自动显示翻译预览。
  - 支持发送纯译文、双语对照或纯中文原文。
  - 支持 Google 翻译、Google Gemini、DeepSeek 及免翻备用接口。
  - 海外直连与国内网络按需分流，开箱即用。

- **深度中文输入与颜文字体验**：
  - 深度内置 **37 万+ 离线高频中文词库**（370,262 词条），涵盖日常口语、游戏常用语与网络热梗，选词命中率极高。
  - 支持拼音全拼与常用首字母简写（如 `wsm` ➔ `为什么`、`yyds`、`v50` 等）。
  - 支持中英文初始输入模式自由切换，且支持在设置中一键切换**全软件中英双语界面**。
  - 专属 **`(^_^)` 颜文字分类面板**：内置卖萌、开心、难过、对线、问候、日常等 6 大分类 72+ 款常用颜文字，全量经过 Windows 字库校验零方块乱码，原生完美支持 VRChat ChatBox 头顶文字气泡。

- **轻量低占用**：
  - 不采用笨重的浏览器内核架构，常驻内存仅约 30MB，极速秒开，不抢占游戏显存与帧率。

- **贴合视线的空间工效学**：
  - 呼出时默认位于头显前方略微下俯的位置，平视不挡朋友和镜子，低头即可舒适打字。
  - 键盘顶部设置有抓取把手，按住手柄抓取键可在三维空间中随意拖拽移动、拉近推远或放置在身旁。
  - 默认双击右手柄摇杆呼出/收起，可在设置中改为左手或其他按键。

- **便捷小细节**：
  - **常用语快捷板**：一键直发常用短语（如“在听稍等我在打字”、“AFK马上回”等，可在 `phrases.json` 自由修改）。
  - **打字状态同步**：打字时 VRChat 角色头顶自动显示省略号 `...`，提示好友正在输入。
  - **剪贴板一键粘贴**：电脑复制的文字可直接一键粘贴进输入框进行翻译。

---

## 🚀 启动与使用

### 1. VR 模式（在 SteamVR 中使用）
1. 启动 SteamVR 并戴上头显；
2. 运行 `VRC-TransKey.exe`；
3. 在 VR 中连按两次右手摇杆，键盘即会出现在眼前。

### 2. 桌面预览模式（免头显测试）
- 运行 `启动_桌面预览模式.bat` 即可在桌面上直接用鼠标测试打字、翻译与 OSC 发送。

---

## ⚙️ 配置文件 (`config.json`)

```json
{
  "translation": {
    "network_mode": "global",       // "global"(海外直连) 或 "mainland"(中国大陆模式)
    "engine": "free_direct",        // "free_direct", "google_gemini", "deepseek"
    "target_lang": "en",            // 目标语言 (en, ja, ko, ru, fr, de)
    "send_mode": "translated_only", // "translated_only"(纯英文), "bilingual"(双语), "original_only"(纯中文)
    "google_api_key": "",           // 可选填入 Google Gemini API Key
    "deepseek_api_key": "",         // 可选填入 DeepSeek API Key
    "proxy": ""                     // 大陆模式下访问 Google 时的本地代理
  }
}
```

---

## 🌐 English Summary

**VRC-TransKey** is a lightweight in-VR keyboard and real-time translation utility for **VRChat** and **SteamVR**.

- **Instant Typing Translation**: Types Chinese via Pinyin and instantly displays translated previews before broadcasting via OSC to the VRChat ChatBox.
- **Optimized Chinese IME & Kaomoji**: Embedded comprehensive 370k+ offline lexical dictionary (370,262 entries) with support for initial consonant abbreviations (e.g., `wsm` ➔ `为什么`), full bilingual English/Chinese UI localization, and a dedicated 6-category Kaomoji mood keyboard for VRChat ChatBox.
- **Flexible Translation Providers**: Supports Google Translate, Google Gemini, and DeepSeek with global and local network routing.
- **Ultra-Lightweight**: Minimal ~30MB memory footprint with no Chromium overhead.
- **Natural Spatial Ergonomics**: Positioned below the direct line of sight; supports 6-DoF controller grab-and-drag.

---

## 📄 开源许可证
本项目采用 [MIT License](LICENSE) 开源协议。
