from fastapi import HTTPException
from configuration.database import db
from configuration.paths import wb
from schemas import FullConversationResponse


def get_full_conversation_service(conversation_id: int):
    conversation = db.get_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    testcase_name = conversation.testcase
    testcase = db.get_testcase_by_name(testcase_name)
    if not testcase:
        user_prompt = None
        system_prompt = None
    else:
        user_prompt = getattr(testcase.prompt, "user_prompt", None)
        system_prompt = getattr(testcase.prompt, "system_prompt", None)

    return FullConversationResponse(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        agent_response=conversation.agent_response,
        testcase_name=testcase_name,
        conversation_id=conversation_id,
        target=conversation.target,
        score=conversation.evaluation_score,
        reason=conversation.evaluation_reason
    )


def get_conversation_timeline_service(conversation_id: int):
    timeline = db.get_conversation_timeline(conversation_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return timeline