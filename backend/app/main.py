from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.chat import router as chat_router
from app.dependencies import (
    get_knowledge_engine,
    get_math_llm,
    get_router_llm,
)
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up expensive resources once on startup."""
    get_math_llm()
    get_router_llm()
    get_knowledge_engine()
    yield


app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development frontend
        "http://frontend:80",      # Frontend container
        "http://agents-frontend",  # Frontend container name
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler to catch all unhandled errors and return a generic 500 response.

    Args:
        request: The FastAPI request object
        exc: The exception that was raised

    Returns:
        JSONResponse: A generic 500 error response
    """
    logger.error(
        "Unhandled exception caught by global handler",
        path=str(request.url),
        method=request.method,
        exc_info=True,
    )

    return JSONResponse(
        status_code=500, content={"detail": "An internal error occurred."}
    )


app.include_router(chat_router, prefix="/api/v1")
