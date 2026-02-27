import torch
import soundfile as sf
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import warnings

warnings.filterwarnings("ignore")

class IndicParlerTTS:

    def __init__(self,
                 model_name="ai4bharat/indic-parler-tts"):

        print("[Parler] Loading model...")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = ParlerTTSForConditionalGeneration.from_pretrained(
            model_name
        ).to(self.device)

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        self.desc_tokenizer = AutoTokenizer.from_pretrained(
            self.model.config.text_encoder._name_or_path
        )

        self.sr = self.model.config.sampling_rate

        print("[Parler] Ready on", self.device)


    def audio(self,
              text,
              output_file="output.wav",
              voice_desc=None):

        print("[Parler] Generating speech...")

        if voice_desc is None:
            voice_desc = (
                "A clear neutral voice, normal pace, studio quality"
            )

        desc_inputs = self.desc_tokenizer(
            voice_desc,
            return_tensors="pt"
        ).to(self.device)

        text_inputs = self.tokenizer(
            text,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():

            gen = self.model.generate(
                input_ids=desc_inputs.input_ids,
                attention_mask=desc_inputs.attention_mask,
                prompt_input_ids=text_inputs.input_ids,
                prompt_attention_mask=text_inputs.attention_mask
            )

        audio = gen.cpu().numpy().squeeze()

        sf.write(output_file, audio, self.sr)

        print(f"[Parler] Saved: {output_file}")