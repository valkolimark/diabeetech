"""
Unified Cheetah STT using shared audio stream
Prevents conflicts with wake word on Raspberry Pi

Migrated from itiflux voice_assistant/cheetah_stt_unified.py
- Removed PyQt5 dependencies
- Added PICOVOICE_AVAILABLE graceful import
- Added DEV_MODE support
- Uses threading.Thread instead of QThread
- All Cheetah/Cobra configs preserved
"""

import os
import logging
import threading
import time
from typing import Optional, Callable, Tuple

logger = logging.getLogger(__name__)

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() in ("1", "true", "yes")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pvcheetah
    CHEETAH_AVAILABLE = True
except ImportError:
    logger.warning("[STT] pvcheetah not installed. Install with: pip install pvcheetah")
    pvcheetah = None
    CHEETAH_AVAILABLE = False

try:
    import pvcobra
    COBRA_AVAILABLE = True
except ImportError:
    logger.warning("[STT] pvcobra not installed. Install with: pip install pvcobra")
    pvcobra = None
    COBRA_AVAILABLE = False

from voice.audio import get_audio_manager, AudioState


class CheetahSTT:
    """
    Speech-to-text using shared audio stream
    Designed for Raspberry Pi USB microphone at card 0
    """

    def __init__(self,
                 access_key: str,
                 endpoint_duration_sec: float = 0.8,
                 enable_automatic_punctuation: bool = True,
                 vad_sensitivity: float = 0.5):
        """
        Initialize unified STT

        Args:
            access_key: Picovoice access key
            endpoint_duration_sec: Silence duration to end speech
            enable_automatic_punctuation: Add punctuation to transcript
            vad_sensitivity: Voice activity detection sensitivity (0-1)
        """
        self.access_key = access_key
        self.endpoint_duration_sec = endpoint_duration_sec
        self.enable_automatic_punctuation = enable_automatic_punctuation
        self.vad_sensitivity = vad_sensitivity

        # Picovoice instances
        self.cheetah = None
        self.cobra = None

        # Audio manager
        self.audio_manager = get_audio_manager()

        # Processing state
        self.is_listening = False
        self.speech_detected = False
        self.silence_start_time = None
        self.transcript_parts = []

        # Frame accumulation for different frame sizes
        self.cheetah_accumulator = []
        self.cobra_accumulator = []

        # Callbacks
        self.on_partial_transcript: Optional[Callable] = None
        self.on_final_transcript: Optional[Callable] = None

        # Raspberry Pi optimizations
        self.max_recording_duration = 30.0  # Maximum recording time
        self.recording_start_time = None

        # Performance tracking
        self.frames_processed = 0
        self.vad_decisions = []
        self.max_vad_history = 10

    def initialize(self) -> bool:
        """Initialize Cheetah and Cobra with proper settings"""
        if DEV_MODE:
            logger.info("[STT] DEV_MODE active - STT disabled")
            return True

        if not CHEETAH_AVAILABLE:
            logger.warning("[STT] pvcheetah not available - STT disabled")
            return False

        try:
            # Initialize Cheetah STT
            self.cheetah = pvcheetah.create(
                access_key=self.access_key,
                endpoint_duration_sec=self.endpoint_duration_sec,
                enable_automatic_punctuation=self.enable_automatic_punctuation
            )

            # Initialize Cobra VAD
            if COBRA_AVAILABLE:
                self.cobra = pvcobra.create(
                    access_key=self.access_key
                )

            logger.info(f"STT initialized - Cheetah frame: {self.cheetah.frame_length}" +
                        (f", Cobra frame: {self.cobra.frame_length}" if self.cobra else ""))

            # Register processor with audio manager
            self.audio_manager.register_processor(
                AudioState.SPEECH_CAPTURE,
                self._process_audio_frame
            )

            return True

        except Exception as e:
            logger.error(f"Failed to initialize STT: {e}")
            self.cleanup()
            return False

    def start_listening(self) -> bool:
        """Start speech capture"""
        if DEV_MODE:
            logger.info("[STT] DEV_MODE - skipping STT start")
            return True

        if not self.cheetah:
            if not self.initialize():
                return False

        # Reset state
        self.is_listening = True
        self.speech_detected = False
        self.silence_start_time = None
        self.transcript_parts = []
        self.frames_processed = 0
        self.recording_start_time = time.time()
        self.vad_decisions.clear()

        # Clear accumulators
        self.cheetah_accumulator.clear()
        self.cobra_accumulator.clear()

        # Change audio state to speech capture
        if not self.audio_manager.change_state(AudioState.SPEECH_CAPTURE):
            logger.error("Failed to change audio state to SPEECH_CAPTURE")
            return False

        logger.info("STT listening started")
        return True

    def stop_listening(self) -> Optional[str]:
        """Stop speech capture and return final transcript"""
        self.is_listening = False

        # Process any remaining audio
        final_transcript = self._finalize_transcript()

        # Change audio state back to idle
        if not DEV_MODE:
            self.audio_manager.change_state(AudioState.IDLE)

        logger.info(f"STT stopped. Final transcript: '{final_transcript}'")
        return final_transcript

    def _process_audio_frame(self, audio_frame) -> Optional[dict]:
        """
        Process audio frame from shared stream
        Called by audio manager in SPEECH_CAPTURE state
        """
        if not self.is_listening:
            return None

        try:
            # Check maximum recording duration
            if time.time() - self.recording_start_time > self.max_recording_duration:
                logger.warning("Maximum recording duration reached")
                if self.on_final_transcript:
                    transcript = self.stop_listening()
                    if transcript:
                        self.on_final_transcript(transcript)
                return None

            # Accumulate frames for Cobra VAD
            if self.cobra:
                self.cobra_accumulator.extend(audio_frame)

                # Process VAD when we have enough frames
                if len(self.cobra_accumulator) >= self.cobra.frame_length:
                    cobra_frame = np.array(self.cobra_accumulator[:self.cobra.frame_length])
                    self.cobra_accumulator = list(self.cobra_accumulator[self.cobra.frame_length:])

                    # Get voice activity probability
                    voice_probability = self.cobra.process(cobra_frame)

                    # Track VAD decisions for smoothing
                    self.vad_decisions.append(voice_probability > self.vad_sensitivity)
                    if len(self.vad_decisions) > self.max_vad_history:
                        self.vad_decisions.pop(0)

                    # Use majority vote for stability
                    is_speech = sum(self.vad_decisions) > len(self.vad_decisions) / 2

                    if is_speech:
                        if not self.speech_detected:
                            self.speech_detected = True
                            logger.info("Speech detected, starting transcription")
                        self.silence_start_time = None
                    else:
                        if self.speech_detected and self.silence_start_time is None:
                            self.silence_start_time = time.time()

            # Accumulate frames for Cheetah STT
            self.cheetah_accumulator.extend(audio_frame)

            # Process STT when we have enough frames
            while len(self.cheetah_accumulator) >= self.cheetah.frame_length:
                cheetah_frame = np.array(self.cheetah_accumulator[:self.cheetah.frame_length])
                self.cheetah_accumulator = list(self.cheetah_accumulator[self.cheetah.frame_length:])

                # Process with Cheetah
                partial_transcript, is_endpoint = self.cheetah.process(cheetah_frame)
                self.frames_processed += 1

                if partial_transcript:
                    self.transcript_parts.append(partial_transcript)

                    # Notify partial transcript
                    if self.on_partial_transcript:
                        current_transcript = ''.join(self.transcript_parts)
                        self.on_partial_transcript(current_transcript)

                # Check for endpoint
                if is_endpoint:
                    logger.info("Speech endpoint detected")
                    if self.on_final_transcript:
                        transcript = self.stop_listening()
                        if transcript:
                            self.on_final_transcript(transcript)
                    return {'endpoint': True}

            # Check for silence timeout
            if self.silence_start_time:
                silence_duration = time.time() - self.silence_start_time
                if silence_duration >= self.endpoint_duration_sec:
                    logger.info(f"Silence timeout after {silence_duration:.1f}s")
                    if self.on_final_transcript:
                        transcript = self.stop_listening()
                        if transcript:
                            self.on_final_transcript(transcript)
                    return {'silence_timeout': True}

            return {
                'speech_detected': self.speech_detected,
                'frames_processed': self.frames_processed
            }

        except Exception as e:
            logger.error(f"Error processing audio frame: {e}")
            return None

    def _finalize_transcript(self) -> str:
        """Finalize and return complete transcript"""
        try:
            # Flush any remaining audio through Cheetah
            if self.cheetah:
                final_part = self.cheetah.flush()
                if final_part:
                    self.transcript_parts.append(final_part)

            # Join all parts
            final_transcript = ''.join(self.transcript_parts).strip()

            # Log statistics
            if final_transcript and self.recording_start_time:
                duration = time.time() - self.recording_start_time
                logger.info(f"Transcription complete: {len(final_transcript)} chars in {duration:.1f}s")

            return final_transcript

        except Exception as e:
            logger.error(f"Error finalizing transcript: {e}")
            return ''.join(self.transcript_parts).strip()

    def cleanup(self):
        """Clean up resources"""
        # Stop listening if active
        if self.is_listening:
            self.stop_listening()

        # Clean up Picovoice instances
        if self.cheetah:
            try:
                self.cheetah.delete()
            except Exception as e:
                logger.error(f"Error deleting Cheetah: {e}")
            self.cheetah = None

        if self.cobra:
            try:
                self.cobra.delete()
            except Exception as e:
                logger.error(f"Error deleting Cobra: {e}")
            self.cobra = None

        # Clear accumulators
        self.cheetah_accumulator.clear()
        self.cobra_accumulator.clear()
        self.transcript_parts.clear()

    def get_status(self) -> dict:
        """Get current status"""
        status = {
            'initialized': bool(self.cheetah) or DEV_MODE,
            'listening': self.is_listening,
            'speech_detected': self.speech_detected,
            'audio_state': self.audio_manager.state.name,
            'frames_processed': self.frames_processed,
            'transcript_length': len(''.join(self.transcript_parts)),
            'dev_mode': DEV_MODE
        }

        if self.is_listening and self.recording_start_time:
            status['recording_duration'] = time.time() - self.recording_start_time

        return status


class STTManager:
    """
    Manages STT lifecycle and coordinates with wake word
    """

    def __init__(self, stt: CheetahSTT):
        self.stt = stt
        self.audio_manager = get_audio_manager()

    def capture_speech(self, timeout: float = 10.0) -> Optional[str]:
        """
        Capture speech with timeout
        Ensures proper state transitions
        """
        if DEV_MODE:
            logger.info("[STTManager] DEV_MODE - no speech capture")
            return None

        # Ensure we're not in wake word state
        current_state = self.audio_manager.state
        if current_state == AudioState.WAKE_WORD_LISTENING:
            logger.info("Pausing wake word for speech capture")

        # Start listening
        if not self.stt.start_listening():
            logger.error("Failed to start STT")
            return None

        # Wait for completion or timeout
        start_time = time.time()

        while self.stt.is_listening and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        # Stop and get transcript
        if self.stt.is_listening:
            return self.stt.stop_listening()

        return None
