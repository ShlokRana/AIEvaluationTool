import yaml

# ASR Imports
from asr.whisper_asr.whisper_engine import WhisperASR
from asr.indic_conformer_asr.indic_engine import IndicConformerASR

# TTS Imports
from tts.sarvam_tts.sarvam_engine import SarvamTTS
from tts.indic_parler_tts.parler_engine import IndicParlerTTS
from tts.svara_tts.svara_engine import Svara_TTS

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)


def get_asr_engine(cfg):
    engine = cfg["asr"]["engine"]

    if engine == "whisper":
        return WhisperASR(cfg["asr"]["model_size"])

    elif engine == "indic":
        return IndicConformerASR()

    else:
        raise ValueError("Invalid ASR engine")


def get_tts_engine(cfg):
    engine = cfg["tts"]["engine"]

    if engine == "sarvam":
        return SarvamTTS(cfg["tts"]["api_key"])

    elif engine == "parler":
        return IndicParlerTTS()

    elif engine == "svara":
        return Svara_TTS()
    else:
        raise ValueError("Invalid TTS engine")
    

def main():

    print("Loading configuration...")
    cfg = load_config()

    print("Initializing ASR...")
    asr = get_asr_engine(cfg)

    print("Initializing TTS...")
    tts = get_tts_engine(cfg)

    audio_path = "input.wav"

    print("\n--- ASR Stage ---")
    text = asr.transcribe(audio_path)
    print("Transcribed Text:", text)

    print("\n--- TTS Stage ---")
    tts.audio(text, "output.wav")

    print("\nPipeline Complete ✅")

if __name__ == "__main__":
    main()