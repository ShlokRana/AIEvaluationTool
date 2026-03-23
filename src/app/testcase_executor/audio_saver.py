import sys
import os

sys.path.append(os.path.dirname(__file__) + "/../../")
from lib.utils import get_logger

logger = get_logger(__name__)

class EncAudio:

    @staticmethod
    def encode_audio(file_path : str):
        if not os.path.exists(file_path):
            logger.error(f"Specified path {file_path} does not exist. Make sure the file is present.")
            return None
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
        return audio_bytes