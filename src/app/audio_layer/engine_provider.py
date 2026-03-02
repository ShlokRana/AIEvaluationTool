from .asr.whisper_asr.whisper_engine import WhisperEngine
from .asr.indic_conformer_asr.indic_engine import IndicEngine

from .tts.sarvam_tts.sarvam_engine import SarvamEngine
from .tts.indic_parler_tts.parler_engine import ParlerEngine
from .tts.svara_tts.svara_engine import SvaraEngine


class EngineProvider:

    @staticmethod
    def get_asr_engine(engine_name: str):
        if engine_name == "whisper":
            return WhisperEngine()
        elif engine_name == "indic":
            return IndicEngine()
        else:
            raise ValueError(f"Unsupported ASR engine: {engine_name}")

    @staticmethod
    def get_tts_engine(engine_name: str):
        if engine_name == "sarvam":
            return SarvamEngine()
        elif engine_name == "parler":
            return ParlerEngine()
        elif engine_name == "svara":
            return SvaraEngine()
        else:
            raise ValueError(f"Unsupported TTS engine: {engine_name}")