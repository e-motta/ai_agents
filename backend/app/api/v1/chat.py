from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Callable, Tuple, Union, Awaitable

from app.dependencies import get_router_llm, get_math_llm, initialize_knowledge
from app.agents.router_agent import route_query
from app.agents.math_agent import solve_math
from app.agents.knowledge_agent import query_knowledge
from app.enums import ResponseEnum
from app.models import ChatRequest, ChatResponse, WorkflowStep


router = APIRouter()


async def _process_math(message: str, math_llm) -> Tuple[str, WorkflowStep]:
    """Handle MathAgent flow and return response and workflow step."""
    try:
        final_response = await solve_math(message, math_llm)
        return final_response, WorkflowStep(
            agent="MathAgent", action="solve_math", result=final_response
        )
    except Exception as e:
        # Bad request for invalid math expression or LLM math error
        raise HTTPException(status_code=400, detail=str(e))


def _process_knowledge(message: str) -> Tuple[str, WorkflowStep]:
    """Handle KnowledgeAgent flow and return response and workflow step."""
    try:
        final_response = query_knowledge(message)
        return final_response, WorkflowStep(
            agent="KnowledgeAgent", action="query_knowledge", result=final_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _process_unsupported_language(_: str) -> Tuple[str, WorkflowStep]:
    """Handle unsupported language decision."""
    final_response = "Unsupported language. Please ask in English or Portuguese."
    return final_response, WorkflowStep(
        agent="System",
        action="reject",
        result=str(ResponseEnum.UnsupportedLanguage),
    )


def _process_error(_: str) -> Tuple[str, WorkflowStep]:
    """Handle generic error decision."""
    final_response = "Sorry, I could not process your request."
    return final_response, WorkflowStep(
        agent="System", action="error", result=str(ResponseEnum.Error)
    )


HANDLER_BY_DECISION: Dict[
    ResponseEnum,
    Callable[..., Union[Tuple[str, WorkflowStep], Awaitable[Tuple[str, WorkflowStep]]]],
] = {
    ResponseEnum.MathAgent: _process_math,
    ResponseEnum.KnowledgeAgent: _process_knowledge,
    ResponseEnum.UnsupportedLanguage: _process_unsupported_language,
    ResponseEnum.Error: _process_error,
}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    router_llm=Depends(get_router_llm),
    math_llm=Depends(get_math_llm),
    _: bool = Depends(initialize_knowledge),
) -> ChatResponse:
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=422, detail="'message' cannot be empty")

    try:
        decision = await route_query(payload.message, llm=router_llm)
    except Exception:
        decision = ResponseEnum.Error

    agent_workflow: List[WorkflowStep] = [
        WorkflowStep(agent="RouterAgent", action="route_query", result=str(decision))
    ]

    handler = HANDLER_BY_DECISION.get(decision, _process_error)  # type: ignore
    if handler is _process_math:
        final_response, step = await handler(payload.message, math_llm)
    else:
        final_response, step = handler(payload.message)
    agent_workflow.append(step)

    return ChatResponse(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        router_decision=str(decision),
        response=final_response,
        agent_workflow=agent_workflow,
    )
