import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from src.api.middleware.security_headers import SecurityHeadersMiddleware
from src.api.routes import dashboard, transactions
from src.core.schemas import HealthResponse

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
STATIC_DIR = WEB_DIR / "static"

logger = logging.getLogger("realtimetfraud")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)
    if settings.app_env == "development":
        logger.info("Dashboard: http://127.0.0.1:%s/", settings.api_port)
        logger.info("API key for /score endpoint: %s", settings.effective_api_key)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Secure real-time fraud detection for banking, UPI, e-commerce, and payments.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def serve_dashboard() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        secure=True,
        version="1.0.0",
    )
