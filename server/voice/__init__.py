"""
Voice Pipeline for Diabeetech Web
Migrated from itiflux PyQt5 app to async callback architecture.

All PyQt5 imports removed. Uses:
- threading.Thread instead of QThread
- asyncio instead of QTimer
- Callback functions instead of pyqtSignal
- Graceful Picovoice imports with PICOVOICE_AVAILABLE flags
- DEV_MODE flag to disable voice hardware on dev machines
"""

from voice.engine import VoiceEngine, create_voice_engine
from voice.audio import AudioState, AudioStreamManager, get_audio_manager
from voice.corrections import STTPostProcessor, correct_stt_output
from voice.intent import IntentClassifier
from voice.tts import TTSController, speak, speak_greeting

__all__ = [
    "VoiceEngine",
    "create_voice_engine",
    "AudioState",
    "AudioStreamManager",
    "get_audio_manager",
    "STTPostProcessor",
    "correct_stt_output",
    "IntentClassifier",
    "TTSController",
    "speak",
    "speak_greeting",
]
