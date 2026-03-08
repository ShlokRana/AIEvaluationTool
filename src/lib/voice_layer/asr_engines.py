from transformers import AutoModel
import torch
import torchaudio
import whisper

class IndicConformerASR:

    def __init__(self, model_name="ai4bharat/indic-conformer-600m-multilingual"):
        print("[IndicConformer] Loading model...")

        self.model = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True
        )

        self.model.eval()

        print("[IndicConformer] Model loaded")

        self.target_sr = 16000


    def _preprocess(self, audio_path):
        wav, sr = torchaudio.load(audio_path)

        # Convert to mono
        wav = torch.mean(wav, dim=0, keepdim=True)

        # Resample if needed
        if sr != self.target_sr:
            resampler = torchaudio.transforms.Resample(
                orig_freq=sr,
                new_freq=self.target_sr
            )
            wav = resampler(wav)

        return wav


    def transcribe(self, audio_path, lang="ta", decoder="rnnt"):
        print(f"[IndicConformer] Transcribing: {audio_path}")

        wav = self._preprocess(audio_path)

        with torch.no_grad():
            text = self.model(wav, lang, decoder)

        return text

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