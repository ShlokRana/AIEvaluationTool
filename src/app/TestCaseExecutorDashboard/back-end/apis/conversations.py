from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from fastapi import APIRouter, HTTPException
from schemas import FullConversationResponse
from services.conversations import get_full_conversation_service, get_conversation_timeline_service

router = APIRouter()

@router.get("/conversations/full/{conversation_id}", response_model=FullConversationResponse)
def get_full_conversation(conversation_id: int):
    try:
        return get_full_conversation_service(conversation_id=conversation_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}/timeline")
def get_conversation_timeline(conversation_id: int):
    try:
        return get_conversation_timeline_service(conversation_id=conversation_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))