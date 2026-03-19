import torch
import soundfile as sf
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
import torch
from torch.nn.utils.rnn import pad_sequence
import time
from openai import OpenAI
from vllm import LLM, SamplingParams
import traceback

warnings.filterwarnings("ignore")


class SarvamTTS:

    def __init__(self, api_key : str, model : str ="bulbul:v3"):

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


    def _detect_lang(self, text : str):

        try:
            return detect(text)
        except:
            return "en"


    def get_audio(self, text : str, output_file : str ="output.wav"):

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

    def __init__(self, use_vllm : bool = True):
        self.model_name = "kenpath/svara-tts-v1"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")

        self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz")
        self.snac_model = self.snac_model.to(self.device)
        self.use_vllm = use_vllm

        if not self.use_vllm:
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self.model = self.model.to(self.device)
        else:
            """vllm model"""    
            self.model = LLM(
                model="kenpath/svara-tts-v1", # or local path
                trust_remote_code=True, # only if model needs it
                gpu_memory_utilization=0.1,
                max_model_len=2000
            )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
    
    def generate_batch_audio(self, batch_text : List, languages : List, gender : str):
        voices = [f"{l} ({gender})" for l in languages]
        formatted_texts = [f"<|audio|> {v}: {t}<|eot_id|>" for v, t in zip(voices, batch_text)]
        prompts = ["<custom_token_3>" + f + "<custom_token_4><custom_token_5>" for f in formatted_texts]
        

        self.tokenizer.pad_token_id = 128263
        batch_ip_ids = self.tokenizer(prompts, return_tensors="pt", padding=True, padding_side="right")["input_ids"]
        attention_mask = self.tokenizer(prompts, return_tensors="pt", padding=True, padding_side="right")["attention_mask"]
        # Add special tokens
        start_token = torch.tensor([[128259]], dtype=torch.int64).repeat(len(batch_text), 1)
        end_tokens = torch.tensor([[128009, 128260, 128261, 128257]], dtype=torch.int64).repeat(len(batch_text), 1)
        mod_batch_ip_ids = torch.cat([start_token, batch_ip_ids, end_tokens], dim=1)
        mod_attention_mask = torch.cat([torch.ones_like(start_token), attention_mask, torch.ones_like(end_tokens)], dim=1) 

        """vllm code using library"""
        if self.use_vllm:
            ip_ids = mod_batch_ip_ids.to(self.device).tolist()
            mod_attention_mask = mod_attention_mask.tolist()
            sampling_params = SamplingParams(
                temperature=0.7,
                top_p=0.95,
                max_tokens=4000,
                repetition_penalty=1.2,
                stop_token_ids=[128258],
            )
            prompts = [
                {"prompt_token_ids": ids, "attention_mask" : att_mask}
                for ids, att_mask in zip(ip_ids, mod_attention_mask)
            ]

            results = []

            for p in prompts:
                result = self.model.generate(
                    prompts=[p],
                    sampling_params=sampling_params,
                    
                )
                results.append(result)

            generated_ids = [torch.tensor(ip_ids[i] + res[0].outputs[0].token_ids) for i, res in enumerate(results)]

        else:
            """This is the normal hf working code"""
            ip_ids = mod_batch_ip_ids.to(self.device)
            att_mask = mod_attention_mask.to(self.device)
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
                    attention_mask=att_mask
                )
        return generated_ids

    # Redistribute codes into hierarchical levels for SNAC decoder
    def opt_redistribution(self, code_list):
        """De-interleave SNAC tokens into 3 hierarchical levels"""
        llm_codebook_offsets = torch.tensor([i * 4096 for i in range(7)], dtype=torch.long, device=self.device)
        A = torch.tensor(code_list, dtype=torch.long, device=self.device)
        A = (A.view(len(A) // 7, 7) - llm_codebook_offsets).reshape(-1)

        col_indices = [torch.tensor([0]), torch.tensor([1, 4]), torch.tensor([2,3,5,6])] # Level 0: Coarse, Level 1: Medium, Level 2: Fine
        hierarchical_codes = []
        for i in range(len(col_indices)):
            chunk = A.view(len(A)//7, 7)[:, col_indices[i]]
            chunk = chunk.reshape(-1)
            hierarchical_codes.append(chunk)
        return hierarchical_codes
        
    def decode_to_audio(self, hier_codes_list : List):
        l1_lengths = [x[0].shape[0] for x in hier_codes_list]
        batched_levels = [[x[i] for x in hier_codes_list] for i in range(3)]
        batched_levels = [pad_sequence(batched_levels[i], batch_first=True, padding_value=0) for i in range(3)]

        with torch.no_grad():
            audio_hat = self.snac_model.decode(batched_levels)
        
        samples_per_token = audio_hat.shape[-1] // batched_levels[0].shape[1]
        combined_audio = torch.cat([audio_hat[i, :, : l1_lengths[i] * samples_per_token] for i in range(len(l1_lengths))], dim=-1)
        return combined_audio

    def create_audio_arr(self, row):
        # Parse output tokens to extract SNAC codes
        START_OF_SPEECH_TOKEN = 128257
        END_OF_SPEECH_TOKEN = 128258
        AUDIO_CODE_BASE_OFFSET = 128266
        AUDIO_CODE_MAX = AUDIO_CODE_BASE_OFFSET + (7 * 4096) - 1 
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
            raise ValueError("No speech tokens found in generated output.")

        hier_codes = self.opt_redistribution(snac_tokens)

        return hier_codes

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
            hier_codes = []
            for r in gen_ids:
                hier_codes.append(self.create_audio_arr(r))
            audio_op = self.decode_to_audio(hier_codes)
            audio_arr = audio_op.detach().reshape(-1).to("cpu").numpy()
        else:
            raise ValueError("No text to convert to audio.")

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
