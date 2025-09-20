from fastapi import FastAPI
from app.api.v1.chat import router as chat_router
from app.core.llm import get_math_llm, get_router_llm
from app.agents.knowledge_agent import get_knowledge_agent

app = FastAPI()

app.include_router(chat_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}


@app.on_event("startup")
def startup_event() -> None:
    """Warm up expensive resources once on startup."""
    # Initialize cached LLMs
    get_math_llm()
    get_router_llm()
    # Initialize knowledge agent
    get_knowledge_agent()
