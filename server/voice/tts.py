"""
Text-to-Speech using Edge TTS
Plays synthesized audio through system audio

Migrated from itiflux voice_assistant/tts.py
- Removed ALL PyQt5 imports (QObject, QSoundEffect, QUrl, QEventLoop, pyqtSignal)
- Replaced PyQt5 AudioPlayer with subprocess-based playback
- Replaced signals with async callbacks
- All TTS voice settings and text cleaning preserved
"""

import os
import sys
import tempfile
import asyncio
import platform
import shutil
import subprocess
import threading
import json
import re
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

try:
    from edge_tts import Communicate
    EDGE_TTS_AVAILABLE = True
except ImportError:
    logger.warning("[TTS] edge-tts not installed. Install with: pip install edge-tts")
    EDGE_TTS_AVAILABLE = False

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() in ("1", "true", "yes")

# ---- Ensure Homebrew ffmpeg is on PATH for macOS ----
if sys.platform == "darwin":
    brew_dirs = ["/usr/local/bin", "/opt/homebrew/bin"]
    current_path = os.environ.get("PATH", "")
    for d in brew_dirs:
        if os.path.isdir(d) and d not in current_path:
            current_path += os.pathsep + d
    os.environ["PATH"] = current_path


# ----------------------------------------------------------------
# TTS text cleaning helpers (from tts_helper.py)
# ----------------------------------------------------------------

def clean_text_for_tts(text: str) -> str:
    """
    Clean text to make it more natural for TTS reading
    Removes markdown, special characters, and formatting
    """
    if not text:
        return ""

    # Remove markdown headers (###, ##, #)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove markdown bold/italic (***, **, *, _)
    text = re.sub(r'\*{1,3}([^\*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)

    # Remove markdown code blocks
    text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Remove markdown links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove bullet points and list markers
    text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)

    # Remove URLs
    text = re.sub(r'https?://[^\s]+', '', text)

    # Remove special characters that sound weird in TTS
    text = re.sub(r'[<>{}[\]|\\^~]', '', text)

    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)

    # Replace multiple newlines with single period for pause
    text = re.sub(r'\n+', '. ', text)

    # Clean up punctuation
    text = re.sub(r'\.{2,}', '.', text)  # Multiple periods to single
    text = re.sub(r'\s+([,.!?])', r'\1', text)  # Remove space before punctuation

    # Trim whitespace
    text = text.strip()

    # Ensure it ends with punctuation for natural speech
    if text and text[-1] not in '.!?':
        text += '.'

    return text


def clean_response_for_tts(response: str) -> str:
    """
    Specifically clean AI responses for more natural TTS
    """
    # First do general cleaning
    text = clean_text_for_tts(response)

    # Remove common AI response patterns that sound unnatural
    patterns_to_remove = [
        r"Here's a quick recipe.*?:",  # Recipe introductions
        r"Ingredients:",
        r"Instructions:",
        r"Recipe:",
        r"Note:",
        r"Tip:",
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Simplify certain phrases
    replacements = {
        "I've logged": "I logged",
        "I've recorded": "I recorded",
        "I've noted": "I noted",
        "I've saved": "I saved",
        "you've": "you have",
        "we've": "we have",
        "it's": "it is",
        "that's": "that is",
        "what's": "what is",
    }

    for old, new in replacements.items():
        text = re.sub(r'\b' + old + r'\b', new, text, flags=re.IGNORECASE)

    # Remove excessive punctuation
    text = re.sub(r'([.!?])\s*\1+', r'\1', text)

    return text


# ----------------------------------------------------------------
# TTS Controller
# ----------------------------------------------------------------

class TTSController:
    """Controls TTS voice generation and playback via callbacks"""

    def __init__(self,
                 on_tts_start: Optional[Callable] = None,
                 on_tts_end: Optional[Callable] = None,
                 voice: str = "en-GB-SoniaNeural"):
        self.on_tts_start = on_tts_start
        self.on_tts_end = on_tts_end
        self._voice = voice

    def get_voice(self) -> str:
        """Get the TTS voice."""
        return self._voice

    def set_voice(self, voice: str):
        """Set the TTS voice."""
        self._voice = voice
        logger.info(f"[TTS] Voice set to: {voice}")

    def load_voice_from_settings(self, settings_path: str = None):
        """Load the TTS voice from a settings file."""
        try:
            if settings_path and os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    voice = settings.get("tts_voice", "en-GB-SoniaNeural")
                    self._voice = voice
                    logger.info(f"[TTS] Loaded voice from settings: {voice}")
                    return voice
        except Exception as e:
            logger.error(f"[TTS] Error loading voice from settings: {e}")

        return self._voice


async def generate_tts(text: str, filename: str, voice: str = "en-GB-SoniaNeural"):
    """Generate TTS audio file using Edge TTS"""
    if not EDGE_TTS_AVAILABLE:
        logger.warning("[TTS] edge-tts not available, skipping generation")
        return

    tts = Communicate(text, voice=voice)
    await tts.save(filename)


def _play_audio_file(wav_path: str):
    """Play a WAV file using platform-appropriate method (no PyQt5)."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["afplay", wav_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=True)
        elif system == "Linux":
            # Try aplay first (common on Raspberry Pi)
            aplay = shutil.which("aplay")
            if aplay:
                subprocess.run([aplay, wav_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               check=True)
            else:
                # Fallback to paplay
                paplay = shutil.which("paplay")
                if paplay:
                    subprocess.run([paplay, wav_path],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   check=True)
                else:
                    logger.warning("[TTS] No audio player found (tried aplay, paplay)")
        elif system == "Windows":
            # Use PowerShell to play audio
            subprocess.run(
                ["powershell", "-c",
                 f"(New-Object Media.SoundPlayer '{wav_path}').PlaySync()"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=True
            )
        else:
            logger.warning(f"[TTS] Unsupported platform for audio playback: {system}")
    except Exception as e:
        logger.error(f"[TTS] Error playing audio: {e}")


def speak(text: str,
          controller: Optional[TTSController] = None,
          on_tts_start: Optional[Callable] = None,
          on_tts_end: Optional[Callable] = None):
    """
    Synthesize text, play it, and fire on_tts_start/end hooks.
    Uses callbacks instead of PyQt5 signals.
    """
    if DEV_MODE:
        logger.info(f"[TTS] DEV_MODE - would speak: {text[:80]}...")
        return

    if not EDGE_TTS_AVAILABLE:
        logger.warning("[TTS] edge-tts not available, cannot speak")
        return

    # Clean text for more natural TTS
    cleaned_text = clean_response_for_tts(text)

    # Determine voice and callbacks
    voice = "en-GB-SoniaNeural"
    start_hook = on_tts_start
    end_hook = on_tts_end

    if controller:
        voice = controller.get_voice()
        start_hook = start_hook or controller.on_tts_start
        end_hook = end_hook or controller.on_tts_end

    # Create temp files
    tmp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_mp3.close()
    mp3_path = tmp_mp3.name
    wav_path = mp3_path.replace(".mp3", ".wav")

    async def _run_tts():
        try:
            # Hook start
            if start_hook:
                start_hook()

            # Generate MP3 with cleaned text
            await generate_tts(cleaned_text, mp3_path, voice=voice)

            # Convert to WAV
            ff = shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg" or "/opt/homebrew/bin/ffmpeg"
            if not ff or not os.path.exists(ff):
                raise FileNotFoundError(f"ffmpeg not found at {ff}")
            subprocess.run([ff, "-y", "-i", mp3_path, wav_path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            # Play audio (no PyQt5 - uses subprocess)
            _play_audio_file(wav_path)

        except Exception as e:
            logger.error(f"[TTS] Error in TTS: {e}")
        finally:
            # Hook end
            if end_hook:
                end_hook()

            # Cleanup
            for p in (mp3_path, wav_path):
                try:
                    os.remove(p)
                except Exception:
                    pass

    # Fire in background thread
    threading.Thread(target=lambda: asyncio.run(_run_tts()), daemon=True).start()


def speak_greeting(controller: Optional[TTSController] = None):
    """Speak a greeting message."""
    speak("Hello, how can I help you today?", controller=controller)
