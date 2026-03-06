```markdown
Português | [English](README-en.md) | [Español](README-es.md) | [中文](README-zh.md)

# 🎤 Studio de Transcrição Cyberpunk

Um aplicativo desktop para transcrição de áudio em tempo real, tradução, consulta ao DeepSeek e síntese de voz, com foco em privacidade (tudo rodando localmente), interface cyberpunk e atalhos de teclado eficientes.

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
```

### 2. Crie um ambiente virtual
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

> **Nota para AMD/ROCm**: Instale o PyTorch com suporte a ROCm conforme [instruções oficiais](https://pytorch.org/get-started/locally/).

### 4. Configure a chave da API DeepSeek (opcional, se quiser usar o chat)
Crie o arquivo `~/.deepseek_config.json` com o conteúdo:
```json
{"api_key": "sua-chave-aqui"}
```

### 5. Execute o programa
```bash
./run.fish   # se estiver usando fish
# ou
python main.py
```

## 🎮 Uso

### Atalhos de teclado globais (configuráveis no KDE)

| Atalho       | Ação                                    |
|--------------|-----------------------------------------|
| `Super+1`    | Iniciar/parar gravação                  |
| `Super+2`    | Traduzir a transcrição atual            |
| `Super+3`    | Salvar a transcrição em arquivo         |
| `Super+4`    | Corrigir gramática da transcrição       |
| `Super+5`    | Abrir/restaurar a janela DeepSeek       |
| `Super+0`    | Modo background (consulta rápida)       |
| `Super+.`    | Parar reprodução de áudio (TTS)         |

### Interface principal
- Selecione o modelo Whisper, idioma de origem/destino e dispositivo (GPU/CPU).
- Clique em **Gravar** para capturar áudio; ao parar, a transcrição aparece na área superior.
- Use os botões **Traduzir**, **MultiTradução**, **Salvar**, **Corrigir** e **DeepSeek**.
- As traduções aparecem na área inferior com cores por idioma.

### Janela DeepSeek
- Digite sua pergunta ou use o botão **Gravar Áudio** para falar.
- Ative **Deep Think** para raciocínio aprofundado ou **Pesquisa na Internet** para resultados atualizados.
- As respostas podem ser ouvidas com TTS (botão **Ouvir resposta**) ou automaticamente se não contiverem código.
- O atalho `Super+.` interrompe a reprodução de áudio em qualquer lugar.

### Bandeja do sistema
- Ao minimizar a janela principal, ela é ocultada para a bandeja.
- Clique com o botão direito no ícone para mostrar, ocultar ou sair.
- Notificações informam o status da gravação e transcrição.

## 📁 Estrutura do Projeto

```
transcritor/
├── backend/            # Módulos de funcionalidades (transcrição, tradução, TTS, etc.)
├── frontend/           # Interface gráfica (janelas, widgets, estilos)
├── utils/              # Utilitários (configuração, constantes, helpers)
├── main.py             # Ponto de entrada
├── config.py           # Configurações globais
├── run.fish            # Script de execução
└── requirements.txt    # Dependências Python
```

## 🧠 Tecnologias Utilizadas

- **Whisper** (via Hugging Face Transformers) – transcrição
- **Hunyuan-MT-7B** – tradução
- **DeepSeek API** – consulta por IA
- **Piper TTS** – síntese de voz
- **D-Bus** – atalhos globais
- **Tkinter + ttkbootstrap** – interface gráfica
- **PyTorch (ROCm)** – aceleração GPU

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
```
