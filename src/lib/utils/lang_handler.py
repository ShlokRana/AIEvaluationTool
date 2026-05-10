# Stubbed for English-only evaluation (googletrans incompatible with current httpcore)
from typing import Optional

def lang_translate(text: str, target_language: str = "en") -> str:
    return text

def lang_detect(text: str) -> str:
    return "en"

def iso639_to_language_name(lang_code: str) -> Optional[str]:
    mapping = {"en": "english", "hi": "hindi", "te": "telugu"}
    return mapping.get(lang_code, "english")

def language_name_to_iso639(lang_name: str, need_part3=False) -> Optional[str]:
    mapping = {"english": "en", "hindi": "hi", "telugu": "te"}
    code = mapping.get(lang_name.lower(), "en")
    return code if not need_part3 else ({"en": "eng"}.get(code, code))
