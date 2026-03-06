# utils/hardware_detector.py
"""
Hardware detection module.
Provides functions to detect available GPU (NVIDIA CUDA, AMD ROCm) and CPU,
and recommends appropriate models based on available memory.
"""

import torch
import subprocess
from utils.logger import logger

def detect_device():
    """
    Detect the best available device for inference.
    Returns:
        'cuda' if any GPU (NVIDIA or AMD with ROCm) is available,
        'cpu' otherwise.
    """
    if torch.cuda.is_available():
        logger.info("GPU detected (CUDA/ROCm)")
        return 'cuda'
    else:
        logger.info("No GPU detected, using CPU")
        return 'cpu'

def get_gpu_memory():
    """
    Get total GPU memory in GB for the first GPU.
    Returns:
        float: memory in GB, or 0 if not available.
    """
    if not torch.cuda.is_available():
        return 0

    # Try rocm-smi first (AMD)
    try:
        result = subprocess.run(['rocm-smi', '--showmeminfo', 'vram'],
                                capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'VRAM Total' in line:
                    parts = line.split(':')
                    if len(parts) > 1:
                        mem_str = parts[1].strip().split()[0]  # e.g., "16368"
                        mem_gb = float(mem_str) / 1024.0
                        logger.debug(f"AMD GPU memory detected: {mem_gb:.1f} GB")
                        return mem_gb
    except Exception as e:
        logger.debug(f"rocm-smi failed: {e}")

    # Fallback to nvidia-smi (NVIDIA)
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total',
                                 '--format=csv,noheader,nounits'],
                                capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            mem_mb = float(result.stdout.strip())
            mem_gb = mem_mb / 1024.0
            logger.debug(f"NVIDIA GPU memory detected: {mem_gb:.1f} GB")
            return mem_gb
    except Exception as e:
        logger.debug(f"nvidia-smi failed: {e}")

    # Final fallback: use PyTorch's device properties
    try:
        total_memory = torch.cuda.get_device_properties(0).total_memory
        mem_gb = total_memory / (1024 ** 3)
        logger.debug(f"GPU memory from torch: {mem_gb:.1f} GB")
        return mem_gb
    except Exception as e:
        logger.debug(f"torch.cuda.get_device_properties failed: {e}")

    logger.warning("Could not determine GPU memory, assuming 0 GB")
    return 0

def get_ram_gb():
    """Return total system RAM in GB."""
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    mem_kb = int(line.split()[1])
                    return mem_kb / (1024.0 * 1024.0)
    except Exception as e:
        logger.debug(f"Could not read /proc/meminfo: {e}")
    return 16.0  # fallback

def recommend_whisper_model(device, gpu_mem=None):
    """
    Recommend a Whisper model based on device and available memory.
    """
    if device == 'cuda':
        if gpu_mem is None:
            gpu_mem = get_gpu_memory()
        # Ensure gpu_mem is at least 0
        gpu_mem = max(0, gpu_mem)
        if gpu_mem >= 10.0:
            return "large"
        elif gpu_mem >= 6.0:
            return "medium"
        elif gpu_mem >= 3.0:
            return "small"
        elif gpu_mem >= 1.5:
            return "base"
        else:
            return "tiny"
    else:
        # CPU: use tiny or base depending on RAM
        ram = get_ram_gb()
        if ram >= 16.0:
            return "base"
        else:
            return "tiny"

def recommend_translation_model(device, gpu_mem=None):
    """
    Recommend a NLLB translation model based on device and memory.
    """
    if device == 'cuda':
        if gpu_mem is None:
            gpu_mem = get_gpu_memory()
        gpu_mem = max(0, gpu_mem)
        if gpu_mem >= 10.0:
            return "nllb-3.3B"
        elif gpu_mem >= 6.0:
            return "nllb-1.3B"
        elif gpu_mem >= 3.0:
            return "nllb-600M"
        else:
            return "nllb-200M"
    else:
        # CPU: always use smallest (200M)
        return "nllb-200M"

def recommend_tts_voice(device, gpu_mem=None):
    """
    Recommend a TTS voice based on device. For now, always return a medium voice.
    In the future, could choose lower quality for low-resource systems.
    """
    return "pt_BR-faber-medium"

def get_recommended_settings():
    """
    Return a dictionary with recommended settings:
        device, whisper_model, translation_model, tts_voice
    """
    device = detect_device()
    gpu_mem = get_gpu_memory() if device == 'cuda' else 0
    whisper_model = recommend_whisper_model(device, gpu_mem)
    translation_model = recommend_translation_model(device, gpu_mem)
    tts_voice = recommend_tts_voice(device, gpu_mem)
    return {
        "device": device,
        "model_size": whisper_model,
        "translation_model": translation_model,
        "tts_voice": tts_voice
    }