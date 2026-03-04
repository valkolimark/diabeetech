"""
Voice Engine - Main orchestrator for the voice pipeline
Integrates wake word, STT, TTS, intent classification, and command parsing

Migrated from itiflux voice_assistant/voice_assistant_unified.py
- Removed ALL PyQt5 imports (QObject, QThread, pyqtSignal, pyqtSlot, QTimer)
- Replaced PyQt5 signals with callback functions passed in __init__
- Replaced QThread with threading.Thread
- Replaced QTimer with asyncio
- Uses Picovoice graceful imports (try/except ImportError, check PICOVOICE_AVAILABLE)
- Uses DEV_MODE flag to disable voice when not on Pi
- Emits events via WebSocket broadcast callback:
    wake_word_detected, transcript (partial+final),
    voice_state_changed, voice_response
"""

import os
import asyncio
import logging
import threading
import time
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from voice.audio import get_audio_manager, AudioState, DEV_MODE
from voice.wake_word import WakeWordDetector
from voice.stt import CheetahSTT, STTManager
from voice.tts import TTSController, speak
from voice.intent import IntentClassifier
from voice.corrections import STTPostProcessor
from voice.parsers.glucose import GlucoseCommandParser
from voice.parsers.insulin import InsulinCommandParser

logger = logging.getLogger(__name__)


class VoiceEngine:
    """
    Complete voice assistant engine for diabeetech-web.
    Accepts a broadcast callback for pushing events over WebSocket.
    Runs audio processing in a separate thread.
    Disabled in DEV_MODE (just logs a message).
    """

    def __init__(self,
                 picovoice_key: str,
                 wake_word_paths: list,
                 wake_word_sensitivities: Optional[list] = None,
                 stt_endpoint_duration: float = 0.8,
                 vad_sensitivity: float = 0.5,
                 broadcast: Optional[Callable] = None,
                 on_wake_word: Optional[Callable] = None,
                 on_transcript: Optional[Callable] = None,
                 on_partial_transcript: Optional[Callable] = None,
                 on_state_changed: Optional[Callable] = None,
                 on_voice_response: Optional[Callable] = None):
        """
        Initialize voice engine.

        Args:
            picovoice_key: Picovoice access key
            wake_word_paths: List of .ppn wake word model paths
            wake_word_sensitivities: Wake word detection sensitivities
            stt_endpoint_duration: Silence duration to end speech
            vad_sensitivity: Voice activity detection sensitivity
            broadcast: Async callback for WebSocket event broadcasting
            on_wake_word: Callback when wake word detected
            on_transcript: Callback with final transcript
            on_partial_transcript: Callback with partial transcript
            on_state_changed: Callback when voice state changes
            on_voice_response: Callback with voice response text
        """
        self.picovoice_key = picovoice_key

        # WebSocket broadcast callback
        self.broadcast = broadcast

        # Direct callbacks
        self.on_wake_word = on_wake_word
        self.on_transcript = on_transcript
        self.on_partial_transcript = on_partial_transcript
        self.on_state_changed = on_state_changed
        self.on_voice_response = on_voice_response

        # Get shared audio manager
        self.audio_manager = get_audio_manager()

        # Initialize components
        self.wake_word = WakeWordDetector(
            access_key=picovoice_key,
            keyword_paths=wake_word_paths,
            sensitivities=wake_word_sensitivities,
            on_wake_word=self._on_wake_word_detected
        )

        self.stt = CheetahSTT(
            access_key=picovoice_key,
            endpoint_duration_sec=stt_endpoint_duration,
            vad_sensitivity=vad_sensitivity
        )

        self.stt_manager = STTManager(self.stt)

        # TTS controller (no PyQt5 signals)
        self.tts_controller = TTSController(
            on_tts_start=self._on_tts_start,
            on_tts_end=self._on_tts_end
        )

        # Intent classifier and parsers
        self.intent_classifier = IntentClassifier()
        self.stt_processor = STTPostProcessor()
        self.glucose_parser = GlucoseCommandParser()
        self.insulin_parser = InsulinCommandParser()

        # State
        self.is_running = False
        self.is_processing_command = False

        # Command timeout
        self.command_timeout = 10.0

        # Event loop for async broadcast
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> bool:
        """Initialize all components"""
        if DEV_MODE:
            logger.info("[VoiceEngine] DEV_MODE active - voice hardware disabled, engine ready")
            return True

        try:
            logger.info("Initializing voice engine components...")

            # Initialize wake word
            if not self.wake_word.initialize():
                logger.error("Failed to initialize wake word")
                return False

            # Initialize STT
            if not self.stt.initialize():
                logger.error("Failed to initialize STT")
                return False

            # Set STT callbacks
            self.stt.on_partial_transcript = self._on_partial_transcript
            self.stt.on_final_transcript = self._on_final_transcript

            logger.info("Voice engine initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize voice engine: {e}")
            return False

    def start(self) -> bool:
        """Start voice engine"""
        if DEV_MODE:
            logger.info("[VoiceEngine] DEV_MODE - voice engine start skipped (no hardware)")
            self.is_running = True
            self._emit_event("voice_state_changed", {"state": "dev_mode"})
            return True

        if not self.is_running:
            if not self.wake_word.porcupine or not self.stt.cheetah:
                if not self.initialize():
                    return False

            self.is_running = True

            # Start with wake word detection
            if not self.wake_word.start():
                self.is_running = False
                return False

            self._emit_event("voice_state_changed", {"state": "listening"})
            logger.info("Voice engine started")
            return True

        return True

    def stop(self):
        """Stop voice engine"""
        if self.is_running:
            self.is_running = False

            if not DEV_MODE:
                # Stop wake word
                self.wake_word.stop()

                # Stop STT if active
                if self.stt.is_listening:
                    self.stt.stop_listening()

                # Return to idle state
                self.audio_manager.change_state(AudioState.IDLE)

            self._emit_event("voice_state_changed", {"state": "stopped"})
            logger.info("Voice engine stopped")

    def cleanup(self):
        """Clean up all resources"""
        self.stop()

        if not DEV_MODE:
            self.wake_word.cleanup()
            self.stt.cleanup()

        # Note: Don't cleanup audio_manager here as it's shared

    # ------------------------------------------------------------------
    # Internal event handlers
    # ------------------------------------------------------------------

    def _on_wake_word_detected(self, keyword_index: int):
        """Handle wake word detection"""
        if not self.is_running or self.is_processing_command:
            return

        logger.info(f"Wake word detected (index {keyword_index})")

        # Emit event
        self._emit_event("wake_word_detected", {"keyword_index": keyword_index})

        # Notify direct callback
        if self.on_wake_word:
            try:
                self.on_wake_word(keyword_index)
            except Exception as e:
                logger.error(f"Wake word callback error: {e}")

        # Start command capture in separate thread to not block audio
        threading.Thread(
            target=self._capture_command,
            daemon=True,
            name="CommandCapture"
        ).start()

    def _capture_command(self):
        """Capture voice command after wake word"""
        if self.is_processing_command:
            return

        self.is_processing_command = True
        self._emit_event("voice_state_changed", {"state": "capturing"})

        try:
            logger.info("Listening for command...")

            # Capture speech
            transcript = self.stt_manager.capture_speech(timeout=self.command_timeout)

            if transcript:
                logger.info(f"Command captured: '{transcript}'")

                # Apply STT corrections
                corrected = self.stt_processor.process(transcript)
                if corrected != transcript:
                    logger.info(f"STT corrected: '{transcript}' -> '{corrected}'")

                # Emit final transcript event
                self._emit_event("transcript", {
                    "text": corrected,
                    "raw": transcript,
                    "is_final": True
                })

                # Notify direct callback
                if self.on_transcript:
                    try:
                        self.on_transcript(corrected)
                    except Exception as e:
                        logger.error(f"Transcript callback error: {e}")
            else:
                logger.warning("No command captured")

        except Exception as e:
            logger.error(f"Error capturing command: {e}")

        finally:
            self.is_processing_command = False

            # Return to wake word listening if still running
            if self.is_running and not DEV_MODE:
                # Small delay before resuming wake word
                time.sleep(0.5)

                if self.audio_manager.state == AudioState.IDLE:
                    self.wake_word.start()
                    self._emit_event("voice_state_changed", {"state": "listening"})

    def _on_partial_transcript(self, transcript: str):
        """Handle partial transcript"""
        # Emit partial transcript event
        self._emit_event("transcript", {
            "text": transcript,
            "is_final": False
        })

        # Notify direct callback
        if self.on_partial_transcript:
            try:
                self.on_partial_transcript(transcript)
            except Exception as e:
                logger.error(f"Partial transcript callback error: {e}")

    def _on_final_transcript(self, transcript: str):
        """Handle final transcript from STT"""
        # This is called by STT when endpoint is detected
        # The main processing happens in _capture_command
        pass

    def _on_tts_start(self):
        """Handle TTS playback start"""
        self._emit_event("voice_state_changed", {"state": "speaking"})

    def _on_tts_end(self):
        """Handle TTS playback end"""
        if self.is_running:
            self._emit_event("voice_state_changed", {"state": "listening"})

    # ------------------------------------------------------------------
    # Public API for processing text commands
    # ------------------------------------------------------------------

    def classify_command(self, text: str) -> Dict:
        """Classify a voice command using the intent classifier"""
        return self.intent_classifier.classify_intent(text)

    def parse_glucose_command(self, text: str) -> Dict:
        """Parse a glucose-related command"""
        return self.glucose_parser.parse(text)

    def parse_insulin_command(self, text: str) -> Optional[Dict]:
        """Parse an insulin-related command"""
        return self.insulin_parser.parse_insulin_command(text)

    def speak_response(self, text: str):
        """Speak a response using TTS"""
        self._emit_event("voice_response", {"text": text})

        if self.on_voice_response:
            try:
                self.on_voice_response(text)
            except Exception as e:
                logger.error(f"Voice response callback error: {e}")

        speak(text, controller=self.tts_controller)

    # ------------------------------------------------------------------
    # Event emission
    # ------------------------------------------------------------------

    def _emit_event(self, event_type: str, data: Dict[str, Any] = None):
        """
        Emit a voice event via the broadcast callback.
        Supports both sync and async broadcast callbacks.
        """
        if not self.broadcast:
            return

        payload = {
            "type": event_type,
            "data": data or {},
            "timestamp": time.time()
        }

        try:
            if asyncio.iscoroutinefunction(self.broadcast):
                # Async broadcast - schedule in event loop
                loop = self._get_event_loop()
                if loop and loop.is_running():
                    asyncio.run_coroutine_threadsafe(self.broadcast(payload), loop)
                else:
                    # Fallback: run in new loop
                    threading.Thread(
                        target=lambda: asyncio.run(self.broadcast(payload)),
                        daemon=True
                    ).start()
            else:
                # Sync broadcast
                self.broadcast(payload)
        except Exception as e:
            logger.error(f"Error emitting event {event_type}: {e}")

    def _get_event_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """Get the running event loop"""
        if self._loop is not None:
            return self._loop
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
        return self._loop

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the event loop for async broadcasting"""
        self._loop = loop

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Get current status"""
        status = {
            'running': self.is_running,
            'processing_command': self.is_processing_command,
            'dev_mode': DEV_MODE,
        }

        if not DEV_MODE:
            status['audio_manager'] = self.audio_manager.get_status()
            status['wake_word'] = self.wake_word.get_status()
            status['stt'] = self.stt.get_status()

        return status


# ------------------------------------------------------------------
# Factory
# ------------------------------------------------------------------

def create_voice_engine(settings: dict,
                        broadcast: Optional[Callable] = None) -> VoiceEngine:
    """
    Factory function to create voice engine from settings.

    Args:
        settings: Dictionary with configuration
        broadcast: Async callback for WebSocket event broadcasting

    Returns:
        Configured VoiceEngine instance
    """
    # Extract settings
    picovoice_key = settings.get('picovoice_access_key', '')

    # Wake word configuration
    wake_word_models = settings.get('wake_word_models', ['GlucoCom'])
    wake_word_dir = Path(settings.get('wake_word_model_dir', 'models'))
    wake_word_paths = []

    for model in wake_word_models:
        # Handle model names with or without .ppn extension
        if model.endswith('.ppn'):
            model_path = wake_word_dir / model
        else:
            model_path = wake_word_dir / f"{model}.ppn"
        if model_path.exists():
            wake_word_paths.append(str(model_path))
        else:
            logger.warning(f"Wake word model not found: {model_path}")

    wake_word_sensitivities = settings.get('wake_word_sensitivities', [0.5] * len(wake_word_paths))

    # STT configuration
    stt_endpoint_duration = settings.get('stt_endpoint_duration', 0.8)
    vad_sensitivity = settings.get('vad_sensitivity', 0.5)

    # Create engine
    engine = VoiceEngine(
        picovoice_key=picovoice_key,
        wake_word_paths=wake_word_paths,
        wake_word_sensitivities=wake_word_sensitivities,
        stt_endpoint_duration=stt_endpoint_duration,
        vad_sensitivity=vad_sensitivity,
        broadcast=broadcast
    )

    return engine
