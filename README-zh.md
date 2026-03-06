[Português](README.md) | [English](README-en.md) | [Español](README-es.md) | 中文

# 🎤 赛博朋克转录工作室

一款桌面应用程序，用于实时音频转录、翻译、DeepSeek查询和语音合成，专注于隐私保护（所有内容本地运行）、赛博朋克界面和高效的键盘快捷键。

## ✨ 功能特性

- **音频转录**：使用Whisper模型（`tiny` 至 `large-v3`），通过ROCm在GPU上运行。
- **翻译**：使用 `tencent/Hunyuan-MT-7B` 模型（WMT25冠军），100%本地运行。
- **DeepSeek查询**：支持“深度思考”和互联网搜索选项（通过DuckDuckGo）。
- **语音合成**：使用Piper（支持葡萄牙语及其他语言的语音）。
- **赛博朋克图形界面**：基于Tkinter和ttkbootstrap。
- **全局键盘快捷键**：通过D-Bus实现（即使应用最小化也能使用）。
- **系统托盘**和原生通知。
- **配置持久化**：保存在 `~/.transcritor_config.json`。
- **可选语法校正**：发送到DeepSeek前进行语法修正。
- **后台模式**：无需打开窗口即可快速查询。

## 📦 系统要求

- **操作系统**：Linux（已在Manjaro/KDE上测试）。
- **GPU**：NVIDIA或AMD（支持ROCm，可选但推荐）。
- **Python**：3.10或更高版本。
- **主要依赖**：
  - torch（支持ROCm或CUDA）
  - transformers
  - sounddevice, pyaudio
  - piper-tts
  - dbus-python
  - pystray, pillow
  - ttkbootstrap
  - requests, beautifulsoup4
  - language-tool-python

## 🔧 安装

### 1. 克隆仓库
```bash
git clone https://github.com/your-username/transcritor-cyberpunk.git
cd transcritor-cyberpunk
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

> **AMD/ROCm用户注意**：请按照[官方说明](https://pytorch.org/get-started/locally/)安装支持ROCm的PyTorch。

### 4. 配置DeepSeek API密钥（可选，如需使用聊天功能）
创建文件 `~/.deepseek_config.json`，内容如下：
```json
{"api_key": "你的密钥"}
```

### 5. 运行程序
```bash
./run.fish   # 如果使用fish shell
# 或
python main.py
```

## 🎮 使用方法

### 全局键盘快捷键（可在KDE中配置）

| 快捷键       | 动作                     |
|--------------|--------------------------|
| `Super+1`    | 开始/停止录音            |
| `Super+2`    | 翻译当前转录文本         |
| `Super+3`    | 将转录文本保存到文件     |
| `Super+4`    | 校正转录文本的语法       |
| `Super+5`    | 打开/恢复DeepSeek窗口    |
| `Super+0`    | 后台模式（快速查询）     |
| `Super+.`    | 停止音频播放（TTS）      |

### 主界面
- 选择Whisper模型、源语言/目标语言和设备（GPU/CPU）。
- 点击**录音**开始捕获音频；停止后，转录内容显示在上方区域。
- 使用**翻译**、**多语言翻译**、**保存**、**校正**和**DeepSeek**按钮。
- 翻译结果显示在下方区域，不同语言用颜色区分。

### DeepSeek窗口
- 输入问题或使用**录音**按钮说话。
- 启用**深度思考**进行深入推理，或启用**互联网搜索**获取最新结果。
- 回答可通过TTS播放（**听回答**按钮），若不包含代码则自动播放。
- 快捷键 `Super+.` 可随时停止音频播放。

### 系统托盘
- 最小化主窗口后，程序将隐藏到系统托盘。
- 右键点击托盘图标可显示、隐藏或退出程序。
- 通知会提示录音和转录状态。

## 📁 项目结构

```
transcritor/
├── backend/            # 功能模块（转录、翻译、TTS等）
├── frontend/           # 图形界面（窗口、组件、样式）
├── utils/              # 工具类（配置、常量、辅助函数）
├── main.py             # 入口点
├── config.py           # 全局配置
├── run.fish            # 运行脚本
└── requirements.txt    # Python依赖列表
```

## 🧠 所用技术

- **Whisper**（通过Hugging Face Transformers） – 转录
- **Hunyuan-MT-7B** – 翻译
- **DeepSeek API** – AI查询
- **Piper TTS** – 语音合成
- **D-Bus** – 全局快捷键
- **Tkinter + ttkbootstrap** – 图形界面
- **PyTorch (ROCm)** – GPU加速

## 🤝 贡献

欢迎贡献！请随时提交issue或pull request。

## 📄 许可证

本项目采用 [MIT许可证](LICENSE)。
