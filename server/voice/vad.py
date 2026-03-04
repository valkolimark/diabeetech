"""
Cobra Voice Activity Detection Integration
Detects when someone is speaking to enable dynamic speech capture

Migrated from itiflux voice_assistant/cobra_vad.py
- Removed PyQt5 dependencies
- Added PICOVOICE_AVAILABLE graceful import
- Added DEV_MODE support
- All VAD thresholds preserved
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEV_MODE = os.environ.get("DEV_MODE", "false").lower() in ("1", "true", "yes")

try:
    import pvcobra
    PICOVOICE_AVAILABLE = True
except ImportError:
    logger.warning("[Cobra] pvcobra not installed. Install with: pip install pvcobra")
    pvcobra = None
    PICOVOICE_AVAILABLE = False


class CobraVAD:
    """Wrapper for Picovoice Cobra Voice Activity Detection"""

    def __init__(self, access_key: str):
        """Initialize Cobra with access key"""
        self.cobra = None
        self.access_key = access_key
        self.is_initialized = False

        if DEV_MODE:
            logger.info("[Cobra] DEV_MODE active - VAD disabled")
            return

        if not PICOVOICE_AVAILABLE:
            logger.warning("[Cobra] pvcobra module not available")
            return

        try:
            self.cobra = pvcobra.create(access_key=access_key)
            self.is_initialized = True
            logger.info(f"[Cobra] Initialized successfully")
            logger.info(f"[Cobra] Frame length: {self.cobra.frame_length}")
            logger.info(f"[Cobra] Sample rate: {self.cobra.sample_rate}")
        except Exception as e:
            logger.error(f"[Cobra] Failed to initialize: {e}")
            self.cobra = None
            self.is_initialized = False

    def process(self, pcm_frame: list) -> float:
        """
        Process audio frame to detect voice activity

        Args:
            pcm_frame: List of PCM samples (16-bit integers)

        Returns:
            Voice activity probability (0.0 to 1.0)
            Returns 0.0 if Cobra not available
        """
        if not self.is_initialized or not self.cobra:
            return 0.0

        try:
            # Cobra expects the exact frame length
            if len(pcm_frame) != self.cobra.frame_length:
                logger.warning(f"[Cobra] Warning: frame length {len(pcm_frame)} != expected {self.cobra.frame_length}")
                return 0.0

            # Process returns probability of voice activity
            probability = self.cobra.process(pcm_frame)
            return probability

        except Exception as e:
            logger.error(f"[Cobra] Error processing audio: {e}")
            return 0.0

    def delete(self):
        """Clean up Cobra resources"""
        if self.cobra:
            try:
                self.cobra.delete()
                logger.info("[Cobra] Cleaned up resources")
            except Exception as e:
                logger.error(f"[Cobra] Error during cleanup: {e}")
            finally:
                self.cobra = None
                self.is_initialized = False

    def __del__(self):
        """Destructor to ensure cleanup"""
        self.delete()


# Global instance
_cobra_instance = None


def get_cobra_instance(access_key: str = None) -> Optional[CobraVAD]:
    """Get or create the global Cobra instance"""
    global _cobra_instance

    if _cobra_instance is None and access_key:
        _cobra_instance = CobraVAD(access_key)

    return _cobra_instance


def cleanup_cobra():
    """Clean up the global Cobra instance"""
    global _cobra_instance

    if _cobra_instance:
        _cobra_instance.delete()
        _cobra_instance = None
