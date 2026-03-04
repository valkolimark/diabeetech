"""
Centralized Audio Stream Manager
Handles single audio stream shared across all voice components
Optimized for USB microphones on Raspberry Pi hardware

Migrated from itiflux voice_assistant/audio_stream_manager.py
- Removed PyQt5 dependencies
- Added DEV_MODE flag to disable audio when not on Pi
- Added graceful import for pyaudio
- Uses threading.Thread instead of QThread
"""

import os
import threading
import queue
import time
import logging
from typing import Optional, List, Callable, Dict
from enum import Enum, auto

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

logger = logging.getLogger(__name__)

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() in ("1", "true", "yes")


class AudioState(Enum):
    """Audio system states - only one active at a time"""
    IDLE = auto()
    WAKE_WORD_LISTENING = auto()
    SPEECH_CAPTURE = auto()
    PROCESSING = auto()
    ERROR = auto()


class AudioStreamManager:
    """
    Manages single audio stream for all voice components on Raspberry Pi
    Prevents concurrent access issues with USB microphones
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        # Audio parameters optimized for Raspberry Pi
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_length = 512  # Standardized frame size

        # Raspberry Pi specific buffer settings
        self.buffer_multiplier = 4  # Larger buffers for Pi stability
        self.frames_per_buffer = self.frame_length * self.buffer_multiplier

        # State management
        self.state = AudioState.IDLE
        self.state_lock = threading.Lock()

        # Audio stream
        self._pyaudio = None
        self.stream = None
        self.stream_lock = threading.Lock()

        # Callbacks for different processors
        self.processors: Dict[AudioState, List[Callable]] = {
            AudioState.WAKE_WORD_LISTENING: [],
            AudioState.SPEECH_CAPTURE: [],
        }

        # Audio data queues
        self.audio_queue = queue.Queue(maxsize=100)
        self.overflow_count = 0
        self.last_overflow_time = 0

        # Raspberry Pi specific settings
        self.use_alsa = True  # Force ALSA on Pi
        self.card_index = 0   # USB mic typically card 0

        # Error recovery
        self.max_retries = 3
        self.retry_delay = 0.5
        self.error_count = 0
        self.last_error_time = 0

    def initialize(self) -> bool:
        """Initialize PyAudio with Raspberry Pi optimizations"""
        if DEV_MODE:
            logger.info("[AudioStreamManager] DEV_MODE active - audio hardware disabled")
            return True

        if not PYAUDIO_AVAILABLE:
            logger.warning("[AudioStreamManager] pyaudio not installed - audio disabled")
            return False

        if not NUMPY_AVAILABLE:
            logger.warning("[AudioStreamManager] numpy not installed - audio disabled")
            return False

        try:
            # Suppress ALSA errors on Pi
            if self.use_alsa:
                os.environ['AUDIODRIVER'] = 'alsa'
                # Suppress ALSA lib errors
                try:
                    from ctypes import c_char_p, c_int, cdll
                    ERROR_HANDLER_FUNC = lambda: None
                    asound = cdll.LoadLibrary('libasound.so.2')
                    asound.snd_lib_error_set_handler(ERROR_HANDLER_FUNC)
                except Exception:
                    pass

            self._pyaudio = pyaudio.PyAudio()

            # Find USB microphone on Raspberry Pi
            device_index = None
            for i in range(self._pyaudio.get_device_count()):
                info = self._pyaudio.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    # Look for USB audio device
                    if 'USB' in info.get('name', '') or i == self.card_index:
                        device_index = i
                        logger.info(f"Found USB microphone: {info['name']} at index {i}")
                        break

            if device_index is None:
                logger.warning("No USB microphone found, using default input")
                device_index = None

            # Open stream with Pi-optimized settings
            self.stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.frames_per_buffer,
                stream_callback=self._audio_callback,
                start=False  # Don't start immediately
            )

            logger.info("Audio stream initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self.cleanup()
            return False

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        PyAudio callback - runs in separate thread
        Optimized for Raspberry Pi performance
        """
        if status:
            # Handle overflow gracefully on Pi
            current_time = time.time()
            if current_time - self.last_overflow_time > 1.0:
                self.overflow_count = 0

            self.overflow_count += 1
            self.last_overflow_time = current_time

            # Only log if excessive overflows
            if self.overflow_count > 10:
                logger.warning(f"Audio overflow x{self.overflow_count}")

        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)

        # Process based on current state
        with self.state_lock:
            current_state = self.state

        if current_state in [AudioState.WAKE_WORD_LISTENING, AudioState.SPEECH_CAPTURE]:
            # Queue data for processing
            try:
                self.audio_queue.put_nowait(audio_data)
            except queue.Full:
                # Drop oldest frame on Pi to prevent blocking
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put_nowait(audio_data)
                except Exception:
                    pass

        return (in_data, pyaudio.paContinue)

    def change_state(self, new_state: AudioState) -> bool:
        """Change audio state with proper transitions"""
        if DEV_MODE:
            with self.state_lock:
                self.state = new_state
            return True

        with self.state_lock:
            old_state = self.state

            # Validate state transition
            valid_transitions = {
                AudioState.IDLE: [AudioState.WAKE_WORD_LISTENING],
                AudioState.WAKE_WORD_LISTENING: [AudioState.SPEECH_CAPTURE, AudioState.IDLE],
                AudioState.SPEECH_CAPTURE: [AudioState.PROCESSING, AudioState.IDLE],
                AudioState.PROCESSING: [AudioState.IDLE, AudioState.WAKE_WORD_LISTENING],
                AudioState.ERROR: [AudioState.IDLE]
            }

            if new_state not in valid_transitions.get(old_state, []):
                logger.warning(f"Invalid state transition: {old_state} -> {new_state}")
                return False

            # Clear audio queue on state change
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except Exception:
                    break

            self.state = new_state
            logger.info(f"Audio state changed: {old_state} -> {new_state}")

            # Handle stream start/stop for Pi stability
            if self.stream:
                if new_state in [AudioState.WAKE_WORD_LISTENING, AudioState.SPEECH_CAPTURE]:
                    if not self.stream.is_active():
                        self.stream.start_stream()
                elif new_state == AudioState.IDLE:
                    if self.stream.is_active():
                        self.stream.stop_stream()

            return True

    def register_processor(self, state: AudioState, callback: Callable):
        """Register audio processor for specific state"""
        if state in self.processors:
            self.processors[state].append(callback)
            logger.info(f"Registered processor for {state}")

    def get_audio_frames(self, num_frames: int, timeout: float = 0.1):
        """
        Get audio frames from queue
        Returns None if timeout or insufficient frames
        """
        if DEV_MODE:
            return None

        frames = []
        deadline = time.time() + timeout

        while len(frames) < num_frames and time.time() < deadline:
            try:
                remaining_time = deadline - time.time()
                if remaining_time <= 0:
                    break

                frame = self.audio_queue.get(timeout=min(remaining_time, 0.01))
                frames.append(frame)
            except queue.Empty:
                continue

        if len(frames) < num_frames:
            return None

        # Concatenate frames
        audio_data = np.concatenate(frames[:num_frames])

        # Return excess frames to queue
        for frame in frames[num_frames:]:
            try:
                self.audio_queue.put_nowait(frame)
            except Exception:
                break

        return audio_data

    def process_audio_chunk(self, audio_chunk) -> Dict:
        """Process audio chunk with current state's processors"""
        results = {}

        with self.state_lock:
            current_state = self.state
            processors = self.processors.get(current_state, [])

        for processor in processors:
            try:
                result = processor(audio_chunk)
                if result:
                    results[processor.__name__] = result
            except Exception as e:
                logger.error(f"Processor {processor.__name__} failed: {e}")

        return results

    def handle_error(self, error: Exception):
        """Handle errors with Pi-specific recovery"""
        current_time = time.time()

        # Reset error count if enough time has passed
        if current_time - self.last_error_time > 60:
            self.error_count = 0

        self.error_count += 1
        self.last_error_time = current_time

        logger.error(f"Audio error #{self.error_count}: {error}")

        # Change to error state
        with self.state_lock:
            self.state = AudioState.ERROR

        # Attempt recovery
        if self.error_count < self.max_retries:
            logger.info(f"Attempting audio recovery {self.error_count}/{self.max_retries}")
            time.sleep(self.retry_delay * self.error_count)  # Exponential backoff

            # Cleanup and reinitialize
            self.cleanup()
            if self.initialize():
                self.change_state(AudioState.IDLE)
                logger.info("Audio recovery successful")
            else:
                logger.error("Audio recovery failed")
        else:
            logger.error("Max retries exceeded, audio system disabled")

    def cleanup(self):
        """Clean up audio resources"""
        with self.stream_lock:
            if self.stream:
                try:
                    if self.stream.is_active():
                        self.stream.stop_stream()
                    self.stream.close()
                except Exception as e:
                    logger.error(f"Error closing stream: {e}")
                self.stream = None

            if self._pyaudio:
                try:
                    self._pyaudio.terminate()
                except Exception as e:
                    logger.error(f"Error terminating PyAudio: {e}")
                self._pyaudio = None

        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Exception:
                break

    def get_status(self) -> Dict:
        """Get current audio system status"""
        with self.state_lock:
            current_state = self.state

        return {
            'state': current_state.name,
            'stream_active': self.stream.is_active() if self.stream else False,
            'queue_size': self.audio_queue.qsize(),
            'overflow_count': self.overflow_count,
            'error_count': self.error_count,
            'dev_mode': DEV_MODE,
            'processors_registered': {
                state.name: len(callbacks)
                for state, callbacks in self.processors.items()
            }
        }


# Singleton instance
_audio_manager: Optional[AudioStreamManager] = None


def get_audio_manager() -> AudioStreamManager:
    """Get or create singleton audio manager instance"""
    global _audio_manager
    if _audio_manager is None:
        if DEV_MODE:
            logger.info("[AudioStreamManager] DEV_MODE - creating stub audio manager")
            _audio_manager = AudioStreamManager()
            _audio_manager.initialize()
        else:
            # Check if running on Raspberry Pi
            try:
                with open('/proc/device-tree/model', 'r') as f:
                    if 'raspberry pi' in f.read().lower():
                        logger.info("Detected Raspberry Pi - using optimized audio manager")
            except Exception:
                pass

            _audio_manager = AudioStreamManager()
            if not _audio_manager.initialize():
                logger.warning("Failed to initialize audio manager - voice disabled")

    return _audio_manager
