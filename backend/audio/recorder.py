# backend/audio/recorder.py
import sounddevice as sd
import numpy as np
import threading

class AudioRecorder:
    def __init__(self, samplerate=16000, channels=1, blocksize=1600, callback=None):
        self.samplerate = samplerate
        self.channels = channels
        self.blocksize = blocksize
        self.callback = callback
        self.is_recording = False
        self.audio_buffer = []
        self.thread = None

    def start(self):
        self.audio_buffer = []
        self.is_recording = True
        self.thread = threading.Thread(target=self._record, daemon=True)
        self.thread.start()
        print("🔴 Gravação iniciada")

    def stop(self):
        self.is_recording = False
        if self.thread:
            self.thread.join(timeout=2)
        if not self.audio_buffer:
            return np.array([])
        audio = np.concatenate(self.audio_buffer)
        return audio

    def _record(self):
        with sd.InputStream(samplerate=self.samplerate, channels=self.channels,
                            blocksize=self.blocksize, dtype='float32') as stream:
            while self.is_recording:
                audio_chunk, overflowed = stream.read(self.blocksize)
                if overflowed:
                    print("⚠️ Overflow detectado!")
                if audio_chunk.shape[1] > 1:
                    audio_chunk = np.mean(audio_chunk, axis=1)
                else:
                    audio_chunk = audio_chunk.flatten()
                self.audio_buffer.append(audio_chunk.copy())
                if self.callback:
                    self.callback(audio_chunk)