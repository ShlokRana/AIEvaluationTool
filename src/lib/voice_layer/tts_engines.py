import torch
import soundfile as sf
# from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import warnings
from sarvamai import SarvamAI
from sarvamai.play import save
from langdetect import detect
from snac import SNAC
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import soundfile as sf
from typing import List
import numpy as np

warnings.filterwarnings("ignore")

# class IndicParlerTTS:

#     def __init__(self,
#                  model_name="ai4bharat/indic-parler-tts"):

#         print("[Parler] Loading model...")

#         self.device = "cuda" if torch.cuda.is_available() else "cpu"

#         self.model = ParlerTTSForConditionalGeneration.from_pretrained(
#             model_name
#         ).to(self.device)

#         self.tokenizer = AutoTokenizer.from_pretrained(model_name)

#         self.desc_tokenizer = AutoTokenizer.from_pretrained(
#             self.model.config.text_encoder._name_or_path
#         )

#         self.sr = self.model.config.sampling_rate

#         print("[Parler] Ready on", self.device)


#     def audio(self,
#               text,
#               output_file="output.wav",
#               voice_desc=None):

#         print("[Parler] Generating speech...")

#         if voice_desc is None:
#             voice_desc = (
#                 "A clear neutral voice, normal pace, studio quality"
#             )

#         desc_inputs = self.desc_tokenizer(
#             voice_desc,
#             return_tensors="pt"
#         ).to(self.device)

#         text_inputs = self.tokenizer(
#             text,
#             return_tensors="pt"
#         ).to(self.device)

#         with torch.no_grad():

#             gen = self.model.generate(
#                 input_ids=desc_inputs.input_ids,
#                 attention_mask=desc_inputs.attention_mask,
#                 prompt_input_ids=text_inputs.input_ids,
#                 prompt_attention_mask=text_inputs.attention_mask
#             )

#         audio = gen.cpu().numpy().squeeze()

#         sf.write(output_file, audio, self.sr)

#         print(f"[Parler] Saved: {output_file}")

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


    def get_audio(self, text, output_file="output.wav"):

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

class Svara_TTS:

    def __init__(self):
        self.model_name = "kenpath/svara-tts-v1"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

        self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz")
        self.snac_model = self.snac_model.to(self.device)

        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.model = self.model.to(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    
    def generate_batch_audio(self, batch_text, languages, gender):
        voices = [f"{l} ({gender})" for l in languages]
        formatted_texts = [f"<|audio|> {v}: {t}<|eot_id|>" for v, t in zip(voices, batch_text)]
        prompts = ["<custom_token_3>" + f + "<custom_token_4><custom_token_5>" for f in formatted_texts]

        batch_ip_ids = self.tokenizer(prompts, return_tensors="pt", padding=True)["input_ids"]
        start_token = torch.tensor([[128259]], dtype=torch.int64).repeat(len(batch_text), 1)
        end_tokens = torch.tensor([[128009, 128260, 128261, 128257]], dtype=torch.int64).repeat(len(batch_text), 1)
        # Add special tokens
        mod_batch_ip_ids = torch.cat([start_token, batch_ip_ids, end_tokens], dim=1)
        # print(mod_batch_ip_ids.shape)
        ip_ids = mod_batch_ip_ids.to(self.device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                input_ids=ip_ids,
                max_new_tokens=4000,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.2,
                num_return_sequences=1,
                eos_token_id=128258,
            )
        
        # print(generated_ids)
        return generated_ids

    def create_audio_arr(self, generated_ids):#, single : bool = False):

        # Parse output tokens to extract SNAC codes
        START_OF_SPEECH_TOKEN = 128257
        END_OF_SPEECH_TOKEN = 128258
        AUDIO_CODE_BASE_OFFSET = 128266
        AUDIO_CODE_MAX = AUDIO_CODE_BASE_OFFSET + (7 * 4096) - 1
        row = generated_ids #if not single else generated_ids[0]
        token_indices = (row == START_OF_SPEECH_TOKEN).nonzero(as_tuple=True)[0]

        if len(token_indices) > 0:
            start_idx = token_indices[-1].item() + 1
            audio_tokens = row[start_idx:]
            audio_tokens = audio_tokens[audio_tokens != END_OF_SPEECH_TOKEN]
            audio_tokens = audio_tokens[audio_tokens != 128263]  # PAD token

            # Only keep valid SNAC tokens
            valid_mask = (audio_tokens >= AUDIO_CODE_BASE_OFFSET) & (audio_tokens <= AUDIO_CODE_MAX)
            audio_tokens = audio_tokens[valid_mask]

            snac_tokens = audio_tokens.tolist()
            snac_tokens = [t - AUDIO_CODE_BASE_OFFSET for t in snac_tokens]

            # Trim to multiple of 7
            new_length = (len(snac_tokens) // 7) * 7
            snac_tokens = snac_tokens[:new_length]
        else:
            raise ValueError("No speech tokens found in generated output")

        # Redistribute codes into hierarchical levels for SNAC decoder
        def redistribute_codes(code_list):
            """De-interleave SNAC tokens into 3 hierarchical levels"""
            codes_lvl = [[] for _ in range(3)]
            llm_codebook_offsets = [i * 4096 for i in range(7)]

            for i in range(0, len(code_list), 7):
                # Level 0: Coarse
                codes_lvl[0].append(code_list[i] - llm_codebook_offsets[0])
                # Level 1: Medium
                codes_lvl[1].append(code_list[i+1] - llm_codebook_offsets[1])
                codes_lvl[1].append(code_list[i+4] - llm_codebook_offsets[4])
                # Level 2: Fine
                codes_lvl[2].append(code_list[i+2] - llm_codebook_offsets[2])
                codes_lvl[2].append(code_list[i+3] - llm_codebook_offsets[3])
                codes_lvl[2].append(code_list[i+5] - llm_codebook_offsets[5])
                codes_lvl[2].append(code_list[i+6] - llm_codebook_offsets[6])

            # Convert to tensors for SNAC decoder
            hierarchical_codes = []
            for lvl_codes in codes_lvl:
                tensor = torch.tensor(lvl_codes, dtype=torch.long, device=self.device).unsqueeze(0)
                hierarchical_codes.append(tensor)

            # Decode with SNAC
            with torch.no_grad():
                audio_hat = self.snac_model.decode(hierarchical_codes)

            return audio_hat

        # Generate audio waveform
        audio_waveform = redistribute_codes(snac_tokens)

        # Convert to numpy array
        audio_array = audio_waveform.detach().squeeze().to("cpu").numpy()

        return audio_array

    def generate_audio_from_text(self, text : str | List[str], language : str | List[str], gender : str):
        """
        Generate audio from text using the Svara-TTS model.

        Args:
            text (str): The text to synthesize into speech
            language (str): The language name (e.g., 'Hindi', 'Bengali', 'English')
            gender (str): The gender of the voice ('Male' or 'Female')

        Returns:
            numpy.ndarray: Audio waveform array at 24kHz sample rate
        """

        if isinstance(text, list):
            gen_ids = self.generate_batch_audio(text, language, gender)
            audio_arr = []
            for r in gen_ids:
               audio_arr.append(self.create_audio_arr(r))
        else:
            raise ValueError("No text to convert to audio.")
        # else:
        #     gen_ids = self.generate_single_audio(text, language, gender)
        #     audio_arr = self.create_audio_arr(gen_ids, single=True)

        return audio_arr 

    def get_audio(self, text_input : str | List[str], save_path : str , lang : str | List[str] , gender : str= "Female"):
        try:
            audio_array = self.generate_audio_from_text(
                text=text_input,
                language = lang,
                gender=gender
            )
            if isinstance(audio_array, list):
                combined_audio = np.concat(audio_array)
                sf.write(save_path, combined_audio, 24000)
            else:
                sf.write(save_path, audio_array, 24000)
        except Exception as e:
            print(f"Error : {e}")
