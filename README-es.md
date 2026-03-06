[Português](README.md) | [English](README-en.md) | Español | [中文](README-zh.md)

# 🎤 Estudio de Transcripción Cyberpunk

Una aplicación de escritorio para transcripción de audio en tiempo real, traducción, consulta a DeepSeek y síntesis de voz, enfocada en la privacidad (todo se ejecuta localmente), interfaz cyberpunk y atajos de teclado eficientes.

## ✨ Características

- **Transcripción de audio** con Whisper (modelos `tiny` a `large-v3`) ejecutándose en GPU mediante ROCm.
- **Traducción** con el modelo `tencent/Hunyuan-MT-7B` (campeón WMT25), 100% local.
- **Consulta a DeepSeek** con opciones de "Deep Think" y búsqueda en internet (vía DuckDuckGo).
- **Síntesis de voz** con Piper (voces en portugués y otros idiomas).
- **Interfaz gráfica** cyberpunk con Tkinter y ttkbootstrap.
- **Atajos de teclado globales** mediante D-Bus (funcionan incluso con la app minimizada).
- **Bandeja del sistema** y notificaciones nativas.
- **Persistencia de configuración** en `~/.transcritor_config.json`.
- **Corrección gramatical** opcional antes de enviar a DeepSeek.
- **Modo background** para consultas rápidas sin abrir la ventana.

## 📦 Requisitos

- **Sistema operativo**: Linux (probado en Manjaro/KDE).
- **GPU**: NVIDIA o AMD con ROCm (opcional pero recomendado).
- **Python**: 3.10 o superior.
- **Dependencias principales**:
  - torch (con soporte ROCm o CUDA)
  - transformers
  - sounddevice, pyaudio
  - piper-tts
  - dbus-python
  - pystray, pillow
  - ttkbootstrap
  - requests, beautifulsoup4
  - language-tool-python

## 🔧 Instalación

### 1. Clona el repositorio
```bash
git clone https://github.com/tu-usuario/transcritor-cyberpunk.git
cd transcritor-cyberpunk
```

### 2. Crea un entorno virtual
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instala las dependencias
```bash
pip install -r requirements.txt
```

> **Nota para AMD/ROCm**: Instala PyTorch con soporte ROCm siguiendo las [instrucciones oficiales](https://pytorch.org/get-started/locally/).

### 4. Configura la clave de la API DeepSeek (opcional, si quieres usar el chat)
Crea el archivo `~/.deepseek_config.json` con el contenido:
```json
{"api_key": "tu-clave-aqui"}
```

### 5. Ejecuta el programa
```bash
./run.fish   # si usas fish
# o
python main.py
```

## 🎮 Uso

### Atajos de teclado globales (configurables en KDE)

| Atajo        | Acción                                 |
|--------------|----------------------------------------|
| `Super+1`    | Iniciar/detener grabación              |
| `Super+2`    | Traducir la transcripción actual       |
| `Super+3`    | Guardar transcripción en archivo       |
| `Super+4`    | Corregir gramática de la transcripción |
| `Super+5`    | Abrir/restaurar ventana DeepSeek       |
| `Super+0`    | Modo background (consulta rápida)      |
| `Super+.`    | Detener reproducción de audio (TTS)    |

### Interfaz principal
- Selecciona el modelo Whisper, idioma origen/destino y dispositivo (GPU/CPU).
- Haz clic en **Grabar** para capturar audio; al detener, la transcripción aparece en el área superior.
- Usa los botones **Traducir**, **MultiTraducción**, **Guardar**, **Corregir** y **DeepSeek**.
- Las traducciones aparecen en el área inferior con colores por idioma.

### Ventana DeepSeek
- Escribe tu pregunta o usa el botón **Grabar Audio** para hablar.
- Activa **Deep Think** para razonamiento profundo o **Búsqueda en Internet** para resultados actualizados.
- Las respuestas se pueden escuchar con TTS (botón **Escuchar respuesta**) o automáticamente si no contienen código.
- El atajo `Super+.` detiene la reproducción de audio en cualquier lugar.

### Bandeja del sistema
- Al minimizar la ventana principal, se oculta en la bandeja.
- Haz clic derecho en el icono para mostrar, ocultar o salir.
- Las notificaciones informan el estado de la grabación y transcripción.

## 📁 Estructura del Proyecto

```
transcritor/
├── backend/            # Módulos de funcionalidades (transcripción, traducción, TTS, etc.)
├── frontend/           # Interfaz gráfica (ventanas, widgets, estilos)
├── utils/              # Utilidades (configuración, constantes, helpers)
├── main.py             # Punto de entrada
├── config.py           # Configuraciones globales
├── run.fish            # Script de ejecución
└── requirements.txt    # Dependencias Python
```

## 🧠 Tecnologías Utilizadas

- **Whisper** (via Hugging Face Transformers) – transcripción
- **Hunyuan-MT-7B** – traducción
- **DeepSeek API** – consultas por IA
- **Piper TTS** – síntesis de voz
- **D-Bus** – atajos globales
- **Tkinter + ttkbootstrap** – interfaz gráfica
- **PyTorch (ROCm)** – aceleración GPU

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Siéntete libre de abrir issues o pull requests.

## 📄 Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).
