from pydantic import BaseModel
from typing import Optional, List

class ConversationResponse(BaseModel):
    agent_response: Optional[str]

class FullConversationResponse(BaseModel):
    user_prompt: Optional[str]
    system_prompt: Optional[str]
    agent_response: Optional[str] 
    testcase_name: Optional[str]  
    conversation_id: Optional[int] 
    target: Optional[str]  
    score: Optional[float]
    reason: Optional[str]
