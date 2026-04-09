import sys
import os
import base64

sys.path.append(os.path.dirname(__file__) + "/../../")
from lib.utils import get_logger

logger = get_logger(__name__)

class EncAudio:

    @staticmethod
    def encode_audio(file_path : str):
        if not os.path.exists(file_path):
            logger.error(f"Specified path {file_path} does not exist. Make sure the file is present.")
            return None
        with open(file_path, "rb") as audio_file:
                encoded_bytes = base64.b64encode(audio_file.read())
        logger.info("audio bytes ready..")
        return encoded_bytes