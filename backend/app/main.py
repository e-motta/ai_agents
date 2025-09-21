from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.chat import router as chat_router
from app.dependencies import (
    get_knowledge_engine,
    get_math_llm,
    get_router_llm,
)
from app.core.logging import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up expensive resources once on startup."""
    get_math_llm()
    get_router_llm()
    get_knowledge_engine()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(chat_router, prefix="/api/v1")
