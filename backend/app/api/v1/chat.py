from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Callable, Tuple

from app.core.llm import get_router_llm, get_math_llm
from app.agents.router_agent import route_query
from app.agents.math_agent import solve_math
from app.agents.knowledge_agent import query_knowledge, get_knowledge_agent
from app.enums import ResponseEnum


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_id: str
    conversation_id: str


def _process_math(message: str, math_llm) -> Tuple[str, Dict[str, Any]]:
    """Handle MathAgent flow and return response and workflow step."""
    try:
        final_response = solve_math(message, math_llm)
        return final_response, {
            "agent": "MathAgent",
            "action": "solve_math",
            "result": final_response,
        }
    except Exception as e:
        # Bad request for invalid math expression or LLM math error
        raise HTTPException(status_code=400, detail=str(e))


def _process_knowledge(message: str, _initialized: bool) -> Tuple[str, Dict[str, Any]]:
    """Handle KnowledgeAgent flow and return response and workflow step."""
    try:
        # knowledge agent is guaranteed initialized by dependency
        final_response = query_knowledge(message)
        return final_response, {
            "agent": "KnowledgeAgent",
            "action": "query_knowledge",
            "result": final_response,
        }
    except Exception as e:
        # Internal error for knowledge agent issues
        raise HTTPException(status_code=500, detail=str(e))


def _process_unsupported_language(_: str) -> Tuple[str, Dict[str, Any]]:
    """Handle unsupported language decision."""
    final_response = "Unsupported language. Please ask in English or Portuguese."
    return final_response, {
        "agent": "System",
        "action": "reject",
        "result": str(ResponseEnum.UnsupportedLanguage),
    }


def _process_error(_: str) -> Tuple[str, Dict[str, Any]]:
    """Handle generic error decision."""
    final_response = "Sorry, I could not process your request."
    return final_response, {
        "agent": "System",
        "action": "error",
        "result": str(ResponseEnum.Error),
    }


HANDLER_BY_DECISION: Dict[ResponseEnum, Callable[..., Tuple[str, Dict[str, Any]]]] = {
    ResponseEnum.MathAgent: _process_math,
    ResponseEnum.KnowledgeAgent: _process_knowledge,
    ResponseEnum.UnsupportedLanguage: _process_unsupported_language,
    ResponseEnum.Error: _process_error,
}


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    router_llm = Depends(get_router_llm),
    math_llm = Depends(get_math_llm),
    knowledge_initialized: bool = Depends(get_knowledge_agent),
) -> Dict[str, Any]:
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=422, detail="'message' cannot be empty")

    try:
        # router_llm is injected (and cached); this ensures proper init
        _ = router_llm
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize router LLM: {str(e)}"
        )

    try:
        decision = route_query(payload.message, llm=router_llm)
    except Exception:
        decision = ResponseEnum.Error

    agent_workflow: List[Dict[str, Any]] = [
        {"agent": "RouterAgent", "action": "route_query", "result": str(decision)}
    ]

    handler = HANDLER_BY_DECISION.get(decision, _process_error)
    if handler is _process_math:
        final_response, step = handler(payload.message, math_llm)
    elif handler is _process_knowledge:
        final_response, step = handler(payload.message, knowledge_initialized)
    else:
        final_response, step = handler(payload.message)
    agent_workflow.append(step)

    return {
        "user_id": payload.user_id,
        "conversation_id": payload.conversation_id,
        "router_decision": str(decision),
        "response": final_response,
        "agent_workflow": agent_workflow,
    }
