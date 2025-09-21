import time
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from typing import Callable, Awaitable, Any

from langchain_openai.chat_models.base import ChatOpenAI
from llama_index.core.base.base_query_engine import BaseQueryEngine

from app.dependencies import get_router_llm, get_math_llm, get_knowledge_engine
from app.agents.router_agent import route_query
from app.agents.math_agent import solve_math
from app.agents.knowledge_agent import query_knowledge
from app.enums import ResponseEnum
from app.models import ChatRequest, ChatResponse, WorkflowStep
from app.core.logging import get_logger, log_system_event
from app.core.decorators import log_and_handle_agent_errors

router = APIRouter()
logger = get_logger(__name__)


@log_and_handle_agent_errors(logger, agent_name="MathAgent", error_status_code=400)
async def _process_math(context: dict[str, Any]) -> str:
    """Handle MathAgent flow."""
    return await solve_math(context["payload"].message, context["math_llm"])


@log_and_handle_agent_errors(logger, agent_name="KnowledgeAgent", error_status_code=400)
async def _process_knowledge(context: dict[str, Any]) -> str:
    """Handle KnowledgeAgent flow."""
    return await query_knowledge(
        context["payload"].message, context["knowledge_engine"]
    )


def _process_unsupported_language(context: dict[str, Any]) -> tuple[str, WorkflowStep]:
    """Handle unsupported language decision."""
    payload = context["payload"]
    final_response = "Unsupported language. Please ask in English or Portuguese."
    log_system_event(
        logger=logger,
        event="unsupported_language_rejected",
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
    )
    return final_response, WorkflowStep(
        agent="System", action="reject", result=str(ResponseEnum.UnsupportedLanguage)
    )


def _process_error(context: dict[str, Any]) -> tuple[str, WorkflowStep]:
    """Handle generic error decision."""
    payload = context["payload"]
    final_response = "Sorry, I could not process your request."
    log_system_event(
        logger=logger,
        event="error_processing_request",
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
    )
    return final_response, WorkflowStep(
        agent="System", action="error", result=str(ResponseEnum.Error)
    )


HANDLER_BY_DECISION: dict[
    ResponseEnum,
    Callable[
        [dict[str, Any]], Awaitable[tuple[str, WorkflowStep]] | tuple[str, WorkflowStep]
    ],
] = {
    ResponseEnum.MathAgent: _process_math,
    ResponseEnum.KnowledgeAgent: _process_knowledge,
    ResponseEnum.UnsupportedLanguage: _process_unsupported_language,
    ResponseEnum.Error: _process_error,
}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    router_llm: ChatOpenAI = Depends(get_router_llm),
    math_llm: ChatOpenAI = Depends(get_math_llm),
    knowledge_engine: BaseQueryEngine = Depends(get_knowledge_engine),
) -> ChatResponse:
    start_time = time.time()

    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=422, detail="'message' cannot be empty")

    logger.info(
        "Chat request received",
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
        message_preview=payload.message[:100],
    )

    try:
        decision = await route_query(
            payload.message,
            llm=router_llm,
            conversation_id=payload.conversation_id,
            user_id=payload.user_id,
        )
    except Exception as e:
        logger.error(
            "Router agent failed",
            conversation_id=payload.conversation_id,
            user_id=payload.user_id,
            error=str(e),
        )
        decision = ResponseEnum.Error

    agent_workflow: list[WorkflowStep] = [
        WorkflowStep(agent="RouterAgent", action="route_query", result=str(decision))
    ]

    context = {
        "payload": payload,
        "math_llm": math_llm,
        "knowledge_engine": knowledge_engine,
    }
    handler = HANDLER_BY_DECISION.get(decision, _process_error)  # type: ignore

    if asyncio.iscoroutinefunction(handler):
        final_response, step = await handler(context)
    else:
        final_response, step = handler(context)

    agent_workflow.append(step)

    total_execution_time = time.time() - start_time
    logger.info(
        "Chat request completed",
        conversation_id=payload.conversation_id,
        user_id=payload.user_id,
        router_decision=str(decision),
        execution_time=total_execution_time,
        response_preview=final_response[:100],
    )

    return ChatResponse(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        router_decision=str(decision),
        response=final_response,
        agent_workflow=agent_workflow,
    )
