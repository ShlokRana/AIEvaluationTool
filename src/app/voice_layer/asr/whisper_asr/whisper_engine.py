import whisper


class WhisperASR:
    def __init__(self, model_size="small"):
        print(f"[Whisper] Loading model: {model_size}")
        self.model = whisper.load_model(model_size)
        print("[Whisper] Model loaded")

    def transcribe(self, audio_path):
        print(f"[Whisper] Transcribing: {audio_path}")

        result = self.model.transcribe(
            audio_path,
            temperature=0.0,
            beam_size=5,
            best_of=5,
            fp16=False
        )

        return result["text"]