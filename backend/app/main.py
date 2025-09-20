from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.chat import router as chat_router
from app.dependencies import get_math_llm, get_router_llm, initialize_knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up expensive resources once on startup."""
    # Initialize cached LLMs
    get_math_llm()
    get_router_llm()
    # Initialize knowledge agent
    initialize_knowledge()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(chat_router, prefix="/api/v1")
