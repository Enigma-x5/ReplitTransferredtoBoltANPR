from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from src.config import settings
from src.logging_config import setup_logging, get_logger
from src.services.queue import queue_service

from src.api import auth, users, cameras, uploads, jobs, events, feedback, bolos, licenses, admin, maps

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ANPR City API", mode=settings.MODE)
    await queue_service.connect()
    yield
    await queue_service.disconnect()
    logger.info("ANPR City API shutdown")


app = FastAPI(
    title="ANPR City API",
    version="0.2.0",
    description="API for ANPR ingestion, detection events, corrections, BOLOs, and licensing",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = FastAPI()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(cameras.router)
api_router.include_router(uploads.router)
api_router.include_router(jobs.router)
api_router.include_router(events.router)
api_router.include_router(feedback.router)
api_router.include_router(bolos.router)
api_router.include_router(licenses.router)
api_router.include_router(admin.router)
api_router.include_router(maps.router)

app.mount("/api", api_router)

if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    return {
        "service": "ANPR City API",
        "version": "0.2.0",
        "mode": settings.MODE,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
