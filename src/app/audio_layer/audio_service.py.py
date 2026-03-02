from .engine_provider import EngineProvider


class AudioLayer:

    def __init__(self, asr_engine_name: str, tts_engine_name: str):
        self.asr = EngineProvider.get_asr_engine(asr_engine_name)
        self.tts = EngineProvider.get_tts_engine(tts_engine_name)

    def text_to_audio(self, text: str, output_path: str):
        self.tts.synthesize(text, output_path)

    def audio_to_text(self, audio_path: str):
        return self.asr.transcribe(audio_path)