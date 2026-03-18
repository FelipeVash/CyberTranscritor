# config.py
# Configurações principais do projeto

MODEL_SIZE = "large"
DEVICE = "cuda"
COMPUTE_TYPE = "float16"
BEAM_SIZE = 5

LANGUAGES = {
    "pt": "Português",
    "en": "Inglês",
    "es": "Espanhol",
    "fr": "Francês",
    "de": "Alemão",
    "it": "Italiano",
    "ja": "Japonês",
    "zh": "Chinês"
}

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_DURATION = 5

AUDIO_DIR = "test_audio"
TRANSCRIPTIONS_DIR = "transcricoes"
LOG_DIR = "logs"
LANGUAGE = "pt-br"
TTS_VOICE = "pt_BR-faber-medium" 