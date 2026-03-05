# 🎤 Studio de Transcrição Cyberpunk

Um aplicativo desktop para transcrição de áudio em tempo real, tradução, consulta ao DeepSeek e síntese de voz, com foco em privacidade (tudo rodando localmente), interface cyberpunk e atalhos de teclado eficientes.

![Interface Cyberpunk](screenshot.png) *(opcional: adicione uma imagem da interface)*

## ✨ Funcionalidades

- **Transcrição de áudio** com Whisper (modelos `tiny` a `large-v3`) rodando na GPU via ROCm.
- **Tradução** com o modelo `tencent/Hunyuan-MT-7B` (campeão WMT25), 100% local.
- **Consulta ao DeepSeek** com opções de "Deep Think" e pesquisa na internet (via DuckDuckGo).
- **Síntese de voz** com Piper (vozes em português e outros idiomas).
- **Interface gráfica** cyberpunk com Tkinter e ttkbootstrap.
- **Atalhos de teclado globais** via D-Bus (funcionam mesmo com o app minimizado).
- **Bandeja do sistema** e notificações nativas.
- **Persistência de configurações** em `~/.transcritor_config.json`.
- **Correção gramatical** opcional antes do envio ao DeepSeek.
- **Modo background** para consultas rápidas sem abrir a janela.

## 📦 Requisitos

- **Sistema operacional**: Linux (testado no Manjaro/KDE).
- **GPU**: NVIDIA ou AMD com ROCm (opcional, mas recomendado).
- **Python**: 3.10 ou superior.
- **Dependências principais**:
  - torch (com suporte a ROCm ou CUDA)
  - transformers
  - sounddevice, pyaudio
  - piper-tts
  - dbus-python
  - pystray, pillow
  - ttkbootstrap
  - requests, beautifulsoup4
  - language-tool-python

## 🔧 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/transcritor-cyberpunk.git
cd transcritor-cyberpunk

### 2. Crie um ambiente virtual
bash
python -m venv venv
source venv/bin/activate
