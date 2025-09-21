import time
from typing import Callable, Awaitable, Any
from functools import wraps
from fastapi import HTTPException
from structlog.stdlib import BoundLogger

from app.core.logging import log_agent_processing
from app.models import ChatRequest, WorkflowStep


def log_and_handle_agent_errors(
    logger: BoundLogger, agent_name: str, error_status_code: int = 500
):
    """Decorator to handle timing, logging, and exceptions for agent processing."""

    def decorator(func: Callable[..., Awaitable[str]]):
        @wraps(func)
        async def wrapper(context: dict[str, Any]) -> tuple[str, WorkflowStep]:
            payload: ChatRequest = context["payload"]
            start_time = time.time()
            query_preview = payload.message[:100]
            try:
                final_response = await func(context)
                execution_time = time.time() - start_time
                log_agent_processing(
                    logger=logger,
                    conversation_id=payload.conversation_id,
                    user_id=payload.user_id,
                    processed_content=final_response,
                    execution_time=execution_time,
                    query_preview=query_preview,
                )
                return final_response, WorkflowStep(
                    agent=agent_name, action=func.__name__, result=final_response
                )
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{agent_name} processing failed",
                    conversation_id=payload.conversation_id,
                    user_id=payload.user_id,
                    error=str(e),
                    execution_time=execution_time,
                    query_preview=query_preview,
                )
                raise HTTPException(status_code=error_status_code, detail=str(e))

        return wrapper

    return decorator
