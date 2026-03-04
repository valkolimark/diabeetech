"""
Koala Noise Suppression Integration
Enhances voice recognition by removing background noise

Migrated from itiflux voice_assistant/koala_noise_suppressor.py
- Removed PyQt5 dependencies
- Added PICOVOICE_AVAILABLE graceful import
- Added DEV_MODE support
- All noise suppression logic preserved
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() in ("1", "true", "yes")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pvkoala
    PICOVOICE_AVAILABLE = True
except ImportError:
    logger.warning("[Koala] pvkoala not installed. Install with: pip install pvkoala")
    pvkoala = None
    PICOVOICE_AVAILABLE = False


class KoalaNoiseSuppressor:
    """Wrapper for Picovoice Koala noise suppression"""

    def __init__(self, access_key: str):
        """Initialize Koala with access key"""
        self.koala = None
        self.access_key = access_key
        self.is_initialized = False
        self.buffer = []  # Buffer for handling frame size mismatches

        if DEV_MODE:
            logger.info("[Koala] DEV_MODE active - noise suppression disabled")
            return

        if not PICOVOICE_AVAILABLE:
            logger.warning("[Koala] pvkoala module not available")
            return

        try:
            self.koala = pvkoala.create(access_key=access_key)
            self.is_initialized = True
            logger.info(f"[Koala] Initialized successfully")
            logger.info(f"[Koala] Frame length: {self.koala.frame_length}")
            logger.info(f"[Koala] Sample rate: {self.koala.sample_rate}")
        except Exception as e:
            logger.error(f"[Koala] Failed to initialize: {e}")
            self.koala = None
            self.is_initialized = False

    def process_audio(self, pcm_frame: list) -> Optional[list]:
        """
        Process audio frame to suppress noise
        Handles frame size mismatches by buffering

        Args:
            pcm_frame: List of PCM samples (16-bit integers)

        Returns:
            Noise-suppressed PCM frame or original if Koala not available
        """
        if not self.is_initialized or not self.koala:
            return pcm_frame

        try:
            # Add incoming samples to buffer
            self.buffer.extend(pcm_frame)

            # Process complete frames
            output = []
            koala_frame_length = self.koala.frame_length

            while len(self.buffer) >= koala_frame_length:
                # Extract a frame of the correct size for Koala
                frame_to_process = self.buffer[:koala_frame_length]
                self.buffer = self.buffer[koala_frame_length:]

                # Convert to numpy array
                pcm_array = np.array(frame_to_process, dtype=np.int16)

                # Process with Koala
                enhanced_pcm = self.koala.process(pcm_array)

                # Add to output (handle both list and numpy array)
                if isinstance(enhanced_pcm, list):
                    output.extend(enhanced_pcm)
                else:
                    output.extend(enhanced_pcm.tolist())

            # If we don't have enough output samples to match input length,
            # pad with zeros (this maintains timing)
            while len(output) < len(pcm_frame):
                output.append(0)

            # If we have too many samples, trim to match input length
            if len(output) > len(pcm_frame):
                output = output[:len(pcm_frame)]

            return output

        except Exception as e:
            logger.error(f"[Koala] Error processing audio: {e}")
            return pcm_frame

    def get_delay_samples(self) -> int:
        """Get the delay introduced by Koala in samples"""
        if self.is_initialized and self.koala:
            return self.koala.delay_sample
        return 0

    def reset(self):
        """Reset Koala's internal state and clear buffer"""
        if self.is_initialized and self.koala:
            try:
                self.koala.reset()
                self.buffer = []  # Clear the buffer
                logger.info("[Koala] Reset internal state")
            except Exception as e:
                logger.error(f"[Koala] Error resetting: {e}")

    def delete(self):
        """Clean up Koala resources"""
        if self.koala:
            try:
                self.koala.delete()
                logger.info("[Koala] Cleaned up resources")
            except Exception as e:
                logger.error(f"[Koala] Error during cleanup: {e}")
            finally:
                self.koala = None
                self.is_initialized = False

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.delete()


# Global instance
_koala_instance = None


def get_koala_instance(access_key: str = None) -> Optional[KoalaNoiseSuppressor]:
    """Get or create the global Koala instance"""
    global _koala_instance

    if _koala_instance is None and access_key:
        _koala_instance = KoalaNoiseSuppressor(access_key)

    return _koala_instance


def cleanup_koala():
    """Clean up the global Koala instance"""
    global _koala_instance

    if _koala_instance:
        _koala_instance.delete()
        _koala_instance = None
