[Português](README.md) | English | [Español](README-es.md) | [中文](README-zh.md)

# 🎤 Cyberpunk Transcription Studio

A desktop application for real-time audio transcription, translation, DeepSeek queries, and speech synthesis, focused on privacy (everything runs locally), cyberpunk interface, and efficient keyboard shortcuts.

## ✨ Features

- **Audio transcription** with Whisper (models `tiny` to `large-v3`) running on GPU via ROCm.
- **Translation** with the `tencent/Hunyuan-MT-7B` model (WMT25 champion), 100% local.
- **DeepSeek queries** with "Deep Think" and internet search options (via DuckDuckGo).
- **Speech synthesis** with Piper (voices in Portuguese and other languages).
- **Cyberpunk GUI** with Tkinter and ttkbootstrap.
- **Global keyboard shortcuts** via D-Bus (work even when the app is minimized).
- **System tray** and native notifications.
- **Persistent settings** in `~/.transcritor_config.json`.
- **Optional grammar correction** before sending to DeepSeek.
- **Background mode** for quick queries without opening the window.

## 📦 Requirements

- **Operating system**: Linux (tested on Manjaro/KDE).
- **GPU**: NVIDIA or AMD with ROCm (optional but recommended).
- **Python**: 3.10 or higher.
- **Main dependencies**:
  - torch (with ROCm or CUDA support)
  - transformers
  - sounddevice, pyaudio
  - piper-tts
  - dbus-python
  - pystray, pillow
  - ttkbootstrap
  - requests, beautifulsoup4
  - language-tool-python

## 🔧 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/transcritor-cyberpunk.git
cd transcritor-cyberpunk
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> **Note for AMD/ROCm**: Install PyTorch with ROCm support following the [official instructions](https://pytorch.org/get-started/locally/).

### 4. Configure DeepSeek API key (optional, if you want to use chat)
Create the file `~/.deepseek_config.json` with the content:
```json
{"api_key": "your-key-here"}
```

### 5. Run the program
```bash
./run.fish   # if using fish
# or
python main.py
```

## 🎮 Usage

### Global keyboard shortcuts (configurable in KDE)

| Shortcut     | Action                               |
|--------------|--------------------------------------|
| `Super+1`    | Start/stop recording                 |
| `Super+2`    | Translate current transcription      |
| `Super+3`    | Save transcription to file           |
| `Super+4`    | Correct grammar of transcription     |
| `Super+5`    | Open/restore DeepSeek window         |
| `Super+0`    | Background mode (quick query)        |
| `Super+.`    | Stop audio playback (TTS)            |

### Main interface
- Select Whisper model, source/target language, and device (GPU/CPU).
- Click **Record** to capture audio; when stopped, transcription appears in the top area.
- Use the **Translate**, **MultiTranslate**, **Save**, **Correct**, and **DeepSeek** buttons.
- Translations appear in the bottom area with colors per language.

### DeepSeek window
- Type your question or use the **Record Audio** button to speak.
- Enable **Deep Think** for in-depth reasoning or **Internet Search** for up-to-date results.
- Answers can be played with TTS (button **Listen to answer**) or automatically if they contain no code.
- The shortcut `Super+.` stops audio playback anywhere.

### System tray
- When minimizing the main window, it is hidden to the tray.
- Right-click the icon to show, hide, or exit.
- Notifications inform recording and transcription status.

## 📁 Project Structure

```
transcritor/
├── backend/            # Feature modules (transcription, translation, TTS, etc.)
├── frontend/           # GUI (windows, widgets, styles)
├── utils/              # Utilities (configuration, constants, helpers)
├── main.py             # Entry point
├── config.py           # Global settings
├── run.fish            # Execution script
└── requirements.txt    # Python dependencies
```

## 🧠 Technologies Used

- **Whisper** (via Hugging Face Transformers) – transcription
- **Hunyuan-MT-7B** – translation
- **DeepSeek API** – AI queries
- **Piper TTS** – speech synthesis
- **D-Bus** – global shortcuts
- **Tkinter + ttkbootstrap** – GUI
- **PyTorch (ROCm)** – GPU acceleration

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## 📄 License

This project is licensed under the [MIT License](LICENSE).
