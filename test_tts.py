#!/usr/bin/env python
# test_tts.py - Teste do Coqui TTS em português

import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path para importar o módulo
sys.path.insert(0, str(Path(__file__).parent))

from backend.tts import TTSEngine

def main():
    print("🎤 Inicializando Coqui TTS...")
    tts = TTSEngine(device="cuda")  # use "cpu" se quiser testar na CPU

    # Teste 1: Síntese básica em português
    print("\n📝 Teste 1: Síntese em português")
    texto = "Olá mundo! Este é um teste de síntese de voz em português."
    audio, sr = tts.synthesize(texto, language="pt")

    if audio is not None:
        print(f"✅ Áudio gerado! {len(audio)} amostras, {sr}Hz")
        print("🔊 Reproduzindo...")
        tts.play_audio(audio, sr)
    else:
        print("❌ Falha na síntese")

    # Aguarda a reprodução terminar
    import time
    time.sleep(3)

    # Teste 2: Listar vozes disponíveis
    print("\n📝 Teste 2: Listando vozes pré-definidas")
    speakers = tts.list_speakers()
    if speakers:
        print(f"✅ {len(speakers)} vozes disponíveis:")
        for i, spk in enumerate(speakers[:5]):  # mostra as primeiras 5
            print(f"   {i+1}. {spk}")
    else:
        print("⚠️ Nenhuma voz pré-definida encontrada")

    # Teste 3: Síntese em inglês (para comparar)
    print("\n📝 Teste 3: Síntese em inglês")
    texto_en = "Hello world! This is a test of English speech synthesis."
    audio_en, sr_en = tts.synthesize(texto_en, language="en")

    if audio_en is not None:
        print("✅ Áudio em inglês gerado!")
        print("🔊 Reproduzindo...")
        tts.play_audio(audio_en, sr_en)
    else:
        print("❌ Falha na síntese em inglês")

    time.sleep(3)

    # Finaliza
    tts.unload_model()
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    main()
