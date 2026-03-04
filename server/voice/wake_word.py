"""
Unified wake word detection using shared audio stream
Prevents concurrent access issues on Raspberry Pi

Migrated from itiflux voice_assistant/wake_word_unified.py
- Removed PyQt5 dependencies
- Added PICOVOICE_AVAILABLE graceful import
- Added DEV_MODE support
- Uses threading.Thread instead of QThread
- All Porcupine configs/sensitivities preserved
"""

import os
import logging
import threading
import time
from typing import Optional, Callable

logger = logging.getLogger(__name__)

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() in ("1", "true", "yes")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pvporcupine
    PICOVOICE_AVAILABLE = True
except ImportError:
    logger.warning("[WakeWord] pvporcupine not installed. Install with: pip install pvporcupine")
    pvporcupine = None
    PICOVOICE_AVAILABLE = False

from voice.audio import get_audio_manager, AudioState


class WakeWordDetector:
    """
    Wake word detection that uses shared audio stream
    Designed for Raspberry Pi USB microphone constraints
    """

    def __init__(self,
                 access_key: str,
                 keyword_paths: list,
                 sensitivities: Optional[list] = None,
                 on_wake_word: Optional[Callable] = None):
        """
        Initialize wake word detector

        Args:
            access_key: Picovoice access key
            keyword_paths: List of .ppn keyword model paths
            sensitivities: Detection sensitivities (0-1)
            on_wake_word: Callback when wake word detected
        """
        self.access_key = access_key
        self.keyword_paths = keyword_paths
        self.sensitivities = sensitivities or [0.5] * len(keyword_paths)
        self.on_wake_word = on_wake_word

        # Porcupine instance
        self.porcupine = None

        # Audio manager
        self.audio_manager = get_audio_manager()

        # Processing thread
        self.processing_thread = None
        self.stop_event = threading.Event()

        # Performance tracking
        self.last_detection_time = 0
        self.min_detection_interval = 1.0  # Prevent rapid fire detections

        # Raspberry Pi optimizations
        self.frame_accumulator = []
        self.frames_needed = 0

    def initialize(self) -> bool:
        """Initialize Porcupine with proper frame size"""
        if DEV_MODE:
            logger.info("[WakeWord] DEV_MODE active - wake word detection disabled")
            return True

        if not PICOVOICE_AVAILABLE:
            logger.warning("[WakeWord] pvporcupine not available - wake word disabled")
            return False

        try:
            # Create Porcupine instance
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keyword_paths=self.keyword_paths,
                sensitivities=self.sensitivities
            )

            # Calculate frames needed based on Porcupine requirements
            # Porcupine expects specific frame length
            audio_frame_length = self.audio_manager.frame_length
            porcupine_frame_length = self.porcupine.frame_length

            if audio_frame_length != porcupine_frame_length:
                # Need to accumulate frames
                self.frames_needed = porcupine_frame_length // audio_frame_length
                if porcupine_frame_length % audio_frame_length != 0:
                    self.frames_needed += 1
                logger.info(f"Wake word needs {self.frames_needed} audio frames per process")
            else:
                self.frames_needed = 1

            # Register processor with audio manager
            self.audio_manager.register_processor(
                AudioState.WAKE_WORD_LISTENING,
                self._process_audio_frame
            )

            logger.info("Wake word detector initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize wake word: {e}")
            self.cleanup()
            return False

    def start(self) -> bool:
        """Start wake word detection"""
        if DEV_MODE:
            logger.info("[WakeWord] DEV_MODE - skipping wake word start")
            return True

        if not self.porcupine:
            if not self.initialize():
                return False

        # Change audio state to wake word listening
        if not self.audio_manager.change_state(AudioState.WAKE_WORD_LISTENING):
            logger.error("Failed to change audio state to WAKE_WORD_LISTENING")
            return False

        # Start processing thread
        self.stop_event.clear()
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            name="WakeWordProcessor",
            daemon=True
        )
        self.processing_thread.start()

        logger.info("Wake word detection started")
        return True

    def stop(self):
        """Stop wake word detection"""
        # Signal thread to stop
        self.stop_event.set()

        # Wait for thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)

        # Change audio state to idle
        if not DEV_MODE:
            self.audio_manager.change_state(AudioState.IDLE)

        logger.info("Wake word detection stopped")

    def _processing_loop(self):
        """Main processing loop for wake word detection"""
        logger.info("Wake word processing loop started")

        while not self.stop_event.is_set():
            try:
                # Get audio frames from manager
                # Adjust timeout for Raspberry Pi performance
                audio_frames = self.audio_manager.get_audio_frames(
                    num_frames=self.frames_needed,
                    timeout=0.1  # Short timeout for responsiveness
                )

                if audio_frames is None:
                    # No audio available, continue
                    continue

                # Process with Porcupine
                if self.frames_needed > 1:
                    # Need to reshape audio to match Porcupine frame length
                    target_length = self.porcupine.frame_length
                    if len(audio_frames) >= target_length:
                        # Take exactly what we need
                        process_frames = audio_frames[:target_length]
                    else:
                        # Pad with zeros if needed (shouldn't happen)
                        process_frames = np.pad(
                            audio_frames,
                            (0, target_length - len(audio_frames)),
                            mode='constant'
                        )
                else:
                    process_frames = audio_frames

                # Detect wake word
                keyword_index = self.porcupine.process(process_frames)

                if keyword_index >= 0:
                    current_time = time.time()

                    # Check minimum interval to prevent false triggers
                    if current_time - self.last_detection_time >= self.min_detection_interval:
                        self.last_detection_time = current_time

                        logger.info(f"Wake word detected: index {keyword_index}")

                        # Notify callback
                        if self.on_wake_word:
                            try:
                                # Stop wake word detection during callback
                                self.audio_manager.change_state(AudioState.IDLE)

                                # Execute callback
                                self.on_wake_word(keyword_index)

                                # Resume wake word detection if not in speech capture
                                if self.audio_manager.state == AudioState.IDLE:
                                    self.audio_manager.change_state(AudioState.WAKE_WORD_LISTENING)

                            except Exception as e:
                                logger.error(f"Wake word callback error: {e}")
                                # Ensure we return to listening state
                                self.audio_manager.change_state(AudioState.WAKE_WORD_LISTENING)

            except Exception as e:
                logger.error(f"Wake word processing error: {e}")
                # Brief pause on error to prevent tight loop
                time.sleep(0.1)

        logger.info("Wake word processing loop ended")

    def _process_audio_frame(self, audio_frame) -> Optional[int]:
        """
        Process single audio frame (callback from audio manager)
        This is an alternative to the thread-based approach
        """
        if not self.porcupine:
            return None

        try:
            # Accumulate frames if needed
            self.frame_accumulator.append(audio_frame)

            # Check if we have enough frames
            total_samples = sum(len(f) for f in self.frame_accumulator)

            if total_samples >= self.porcupine.frame_length:
                # Concatenate frames
                combined = np.concatenate(self.frame_accumulator)

                # Process exact frame length
                process_frames = combined[:self.porcupine.frame_length]

                # Save any excess for next time
                excess = combined[self.porcupine.frame_length:]
                if len(excess) > 0:
                    self.frame_accumulator = [excess]
                else:
                    self.frame_accumulator = []

                # Detect wake word
                keyword_index = self.porcupine.process(process_frames)

                if keyword_index >= 0:
                    current_time = time.time()
                    if current_time - self.last_detection_time >= self.min_detection_interval:
                        self.last_detection_time = current_time
                        return keyword_index

        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            self.frame_accumulator = []  # Reset on error

        return None

    def cleanup(self):
        """Clean up resources"""
        # Stop detection
        self.stop()

        # Clean up Porcupine
        if self.porcupine:
            try:
                self.porcupine.delete()
            except Exception as e:
                logger.error(f"Error deleting Porcupine: {e}")
            self.porcupine = None

        # Clear accumulator
        self.frame_accumulator = []

    def get_status(self) -> dict:
        """Get current status"""
        return {
            'initialized': self.porcupine is not None or DEV_MODE,
            'running': (self.processing_thread and self.processing_thread.is_alive()) if self.processing_thread else False,
            'audio_state': self.audio_manager.state.name,
            'last_detection': self.last_detection_time,
            'frame_accumulator_size': len(self.frame_accumulator),
            'dev_mode': DEV_MODE
        }
