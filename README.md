# VRC-TransKey

> 专为 **VRChat** 与 **SteamVR** 定制的轻量虚拟键盘与实时翻译小工具。  
> An ultra-lightweight in-VR keyboard & real-time translation tool for VRChat & SteamVR.

---

## 💡 为什么做这个工具？

在 VRChat 中与外国朋友交流时，经常遇到两个困扰：
1. 大多数海外 VR 键盘对中文拼音输入的支持不够友好，打字选词比较繁琐；
2. 边打字边查翻译需要频繁切换窗口，容易打断当前的沉浸交流。

**VRC-TransKey** 将类似讯飞输入法的“即时翻译”体验带入了 VR 空间：
在头显内打完中文，上方输入框即时呈现翻译预览，确认后通过 OSC 协议毫秒级广播至角色的 ChatBox。

---

## 🌟 主要功能与特点

- **打字即时翻译**：
  - 拼音打字确认后，上方自动显示翻译预览。
  - 支持发送纯译文、双语对照或纯中文原文。
  - 支持 Google 翻译、Google Gemini、DeepSeek 及免翻备用接口。
  - 海外直连与国内网络按需分流，开箱即用。

- **深度中文输入体验**：
  - 内置丰富的高频日常词库，选词命中率高。
  - 支持全拼与常用拼音首字母简写（如 `wsm` ➔ `为什么`、`yyds`、`v50` 等）。
  - 支持中英文初始输入模式自由切换。

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
- **Optimized Chinese IME**: Embedded comprehensive lexical dictionary with support for initial consonant abbreviations (e.g., `wsm` ➔ `为什么`).
- **Flexible Translation Providers**: Supports Google Translate, Google Gemini, and DeepSeek with global and local network routing.
- **Ultra-Lightweight**: Minimal ~30MB memory footprint with no Chromium overhead.
- **Natural Spatial Ergonomics**: Positioned below the direct line of sight; supports 6-DoF controller grab-and-drag.

---

## 📄 开源许可证
本项目采用 [MIT License](LICENSE) 开源协议。
