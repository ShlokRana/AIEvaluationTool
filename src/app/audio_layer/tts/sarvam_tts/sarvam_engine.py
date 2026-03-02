from sarvamai import SarvamAI
from sarvamai.play import save
from langdetect import detect


class SarvamTTS:

    def __init__(self, api_key, model="bulbul:v3"):

        print("[Sarvam] Initializing client...")

        self.client = SarvamAI(
            api_subscription_key=api_key
        )

        self.model = model

        # Language mapping
        self.lang_map = {
            "en": "en-IN",
            "ta": "ta-IN"
        }

        print("[Sarvam] Ready")


    def _detect_lang(self, text):

        try:
            return detect(text)
        except:
            return "en"


    def audio(self, text, output_file="output.wav"):

        print("[Sarvam] Generating speech...")

        lang = self._detect_lang(text)

        code = self.lang_map.get(lang, "en-IN")

        print(f"[Sarvam] Language: {lang} → {code}")

        response = self.client.text_to_speech.convert(
            text=text,
            target_language_code=code,
            model=self.model
        )

        save(response, output_file)

        print(f"[Sarvam] Saved: {output_file}")