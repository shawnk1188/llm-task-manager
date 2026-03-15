"""Chat endpoint — passes user messages through the ADK agent."""

from fastapi import APIRouter

from app.agent.task_agent import run_agent_safe
from app.models.task import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    reply = await run_agent_safe(body.message, body.session_id)
    return ChatResponse(reply=reply, session_id=body.session_id)

