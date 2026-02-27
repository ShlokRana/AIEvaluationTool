from pydantic import BaseModel
from typing import Optional, List

class TestCaseResponse(BaseModel):
    user_prompt: str
    system_prompt: Optional[str]
