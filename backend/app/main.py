"""
app/main.py
-----------
FastAPI application entry point.

Responsibilities:
  - Create the FastAPI app instance with metadata.
  - Register CORS middleware (reads allowed origins from config).
  - Initialize Firebase Admin SDK via lifespan context.
  - Mount routers under their respective prefixes.
  - Define root-level utility endpoints (/, /health).

Start the server with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
# Importing core.firebase triggers _initialize_firebase() at module load time.
# This ensures Firebase is ready before the first request arrives.
import app.core.firebase as _firebase_init  # noqa: F401
from app.routers import auth as auth_router_module
from app.routers import commands as commands_router_module
from app.schemas.command import HealthResponse, MessageResponse

# ── Load settings once ────────────────────────────────────────────────────────
settings = get_settings()


# ── Lifespan context manager ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup and once on shutdown.

    Startup:
      - Validate required environment variables (OPENAI_API_KEY, credentials file).
        If validation fails, the server refuses to start with a clear error.
      - Firebase is already initialized by the module-level import above.

    Shutdown:
      - Currently a no-op; add cleanup logic here if needed (e.g. close DB pools).
    """
    # ── Startup ───────────────────────────────────────────────────────────
    try:
        settings.validate()
        print(f"✅  {settings.APP_NAME} v{settings.APP_VERSION} — startup complete.")
        print(f"🔥  Firebase Admin SDK initialized.")
        print(f"🤖  Groq model: {settings.GROQ_MODEL}")
        print(f"🌐  CORS allowed origins: {settings.ALLOWED_ORIGINS}")
    except EnvironmentError as exc:
        # Print clearly and re-raise — Uvicorn will exit with a non-zero code.
        print(f"\n❌  STARTUP FAILED:\n{exc}\n")
        raise

    yield  # Application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────
    print(f"👋  {settings.APP_NAME} — shutting down.")


# ── FastAPI app instance ──────────────────────────────────────────────────────
app = FastAPI(
    title="Linux Command Generator API",
    description=(
        "API sinh lệnh Linux từ mô tả tiếng Việt sử dụng Groq (Llama 3). "
        "Yêu cầu xác thực Firebase cho các endpoint bảo mật."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc",     # ReDoc UI
)


# ── CORS Middleware ───────────────────────────────────────────────────────────
# Must be added BEFORE routers so it applies to all routes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,   # From .env ALLOWED_ORIGINS
    allow_credentials=True,                    # Allow cookies & auth headers
    allow_methods=["*"],                       # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],                       # Authorization, Content-Type, etc.
)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(
    auth_router_module.router,
    prefix="/auth",
    tags=["Auth"],
)

app.include_router(
    commands_router_module.router,
    prefix="/commands",
    tags=["Commands"],
)


# ── Root-level utility endpoints ──────────────────────────────────────────────

@app.get(
    "/",
    response_model=MessageResponse,
    tags=["System"],
    summary="Root endpoint",
    description="Trả về thông báo chào mừng của hệ thống.",
)
def root() -> MessageResponse:
    return MessageResponse(
        message=f"Chào mừng đến với {settings.APP_NAME} API v{settings.APP_VERSION}. "
                f"Truy cập /docs để xem tài liệu API."
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description="Kiểm tra trạng thái hoạt động của server.",
)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
    )
