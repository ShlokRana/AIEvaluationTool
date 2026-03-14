from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from whatsapp import (
    login_whatsapp,
    logout_whatsapp,
    send_prompt_whatsapp,
    close_whatsapp,
    get_ui_response_whatsapp,
)
from webapp import (
    login_webapp,
    logout_webapp,
    send_prompt,
    close_webapp,
    get_ui_response_webapp,
)

from lib.utils.logger import get_logger
from utils import load_config
from context import APIRuntimeContext
from api_handler import handle_api_chat
from pydantic import BaseModel
import json
import os

router = APIRouter()
logger = get_logger("main")
config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")

# new one
# class PromptCreate(BaseModel):
#     chat_id: int
#     prompt_list: List[str]
#     api_context: Optional[Dict[str, Any]] = None

# For audio input, we can extend the PromptCreate model like this:
class PromptCreate(BaseModel):
    chat_id: int
    prompt_list: Optional[List[str]] = None
    is_voice: bool = False
    is_file: bool = False
    audio_path: Optional[str] = None
    return_voice: bool = False
    api_context: Optional[Dict[str, Any]] = None

# -------------------------------
# Helpers
# -------------------------------
def get_app_info():
    config = load_config()
    return config.get("application_type"), config.get("application_name")


# -------------------------------
# Login
# -------------------------------
@router.get("/login")
def login():
    app_type, app_name = get_app_info()

    if app_type == "WHATSAPP_WEB":
        logger.info("Login request: WhatsApp Web")
        result = login_whatsapp()
        return JSONResponse(content={"result": bool(result)})

    if str.upper(app_type) == "WEBAPP":
        logger.info(f"Login request: WebApp {app_name}")
        result = login_webapp(app_name)
        return JSONResponse(content={"result": bool(result)})

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Logout
# -------------------------------
@router.get("/logout")
def logout():
    app_type, app_name = get_app_info()

    if app_type == "WHATSAPP_WEB":
        logger.info("Logout request: WhatsApp Web")
        result = logout_whatsapp()
        return JSONResponse(content={"result": bool(result)})

    if str.upper(app_type) == "WEBAPP":
        logger.info(f"Logout request: WebApp {app_name}")
        result = logout_webapp(app_name)
        return JSONResponse(content={"result": bool(result)})

    return JSONResponse(content={"error": "Unsupported application type"})

@router.post("/chat")
async def chat(prompt: PromptCreate):

    app_type, app_name = get_app_info()
    app_type = app_type.upper()

    # ---------------------------------------------
    # WhatsApp Web
    # ---------------------------------------------
    if app_type == "WHATSAPP_WEB":

        logger.info("Chat request: WhatsApp Web")

        if prompt.is_voice:
            result = send_prompt_whatsapp(
                chat_id=prompt.chat_id,
                audio_path=prompt.audio_path,
                return_voice=True,
            )
        else:
            result = send_prompt_whatsapp(
                chat_id=prompt.chat_id,
                prompt_list=prompt.prompt_list or [],
            )

        return {"response": result}

    # ---------------------------------------------
    # WebApp
    # ---------------------------------------------
    elif app_type == "WEBAPP":

        logger.info(f"Chat request: WebApp {app_name}")

        if prompt.is_voice:
            result = send_prompt(
                app_name=app_name,
                chat_id=prompt.chat_id,
                audio_path=prompt.audio_path,
                return_voice=True,
            )
        else:
            result = send_prompt(
                app_name=app_name,
                chat_id=prompt.chat_id,
                prompt_list=prompt.prompt_list or [],
            )

        return {"response": result}

    # ---------------------------------------------
    # API
    # ---------------------------------------------
    elif app_type == "API":

        logger.info("Chat request: API")

        if not prompt.api_context:
            raise HTTPException(
                status_code=400,
                detail="api_context is required for API application type",
            )

        ctx = APIRuntimeContext.from_dict(prompt.api_context)

        result = handle_api_chat(
            ctx=ctx,
            payload={
                "chat_id": prompt.chat_id,
                "prompt_list": prompt.prompt_list or [],
                "audio_path": prompt.audio_path,
                "is_voice": prompt.is_voice
            },
        )

        return result

    # ---------------------------------------------
    # Unsupported
    # ---------------------------------------------
    else:

        raise HTTPException(
            status_code=400,
            detail="Unsupported application type"
        )


# -------------------------------
# Close
# -------------------------------
@router.get("/close")
def close():
    app_type, app_name = get_app_info()

    if app_type == "WHATSAPP_WEB":
        logger.info("Close request: WhatsApp Web")
        close_whatsapp()
        return JSONResponse(content={"message": "WhatsApp Web closed successfully"})

    if str.upper(app_type) == "WEBAPP":
        logger.info(f"Close request: WebApp {app_name}")
        close_webapp(app_name)
        return JSONResponse(content={"message": f"Closed WebApp {app_name}"})

    return JSONResponse(content={"error": "Unsupported application type"})


# -------------------------------
# Info
# -------------------------------
@router.post("/info")
def chat_interface():
    app_type, _ = get_app_info()

    if app_type == "WHATSAPP_WEB":
        return get_ui_response_whatsapp()
    if str.upper(app_type) == "WEBAPP":
        return get_ui_response_webapp()

    return {"error": "Unsupported application type"}


# -------------------------------
# Config
# -------------------------------
@router.get("/config")
def get_config():
    with open(config_path, "r") as file:
        return json.load(file)


@router.post("/config")
async def update_config(request: Request):
    try:
        new_config = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        with open(config_path, "w") as file:
            json.dump(new_config, file, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")

    return {"message": "Config updated successfully"}
