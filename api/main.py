from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from api.core.config import settings
from api import db, llm, rag, routers, tools
from api.middlewares.logging_middleware import LoggingMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager for the FastAPI application.

    This function handles the application's startup and shutdown events.
    On startup, it creates the database and tables, and ensures the vector store exists.
    The 'yield' statement passes control back to the application.
    Any code after 'yield' would be executed on application shutdown.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    llm.preload_ollama_models()
    db.create_db_and_tables()
    rag.ensure_vectorstore_exists()
    yield
    # Clean up


server = FastAPI(
    title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan
)

server.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"],
    allow_origins=["http://localhost:3000",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging Middleware
server.add_middleware(LoggingMiddleware)

server.include_router(routers.api_router, prefix="/api")


@server.get("/")
def index():
    """
    Root endpoint for the application.

    Returns:
        dict: A dictionary containing the application's version.
    """
    return {"version": settings.VERSION}
