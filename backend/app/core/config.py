"""
core/config.py
--------------
Centralized configuration management.
Reads all settings from the .env file using python-dotenv.
Never hardcode secrets — always use environment variables.

Cross-platform notes
--------------------
- All file paths use ``pathlib.Path`` so they work identically on
  Windows (backslash) and Linux/macOS (forward slash).
- The project root is derived from ``__file__`` and is therefore
  independent of the current working directory when you start uvicorn.
- The .env file is loaded with an explicit encoding='utf-8' so that
  Vietnamese comments in the file never trigger a UnicodeDecodeError on
  Windows systems whose default ANSI codepage is not UTF-8.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# ── Project root resolution (cross-platform) ──────────────────────────────────
# Layout:  <project_root>/backend/app/core/config.py
#                         ^--- 3 levels up from this file
BASE_DIR: Path = Path(__file__).resolve().parents[3]
# e.g. /home/user/Firebase  or  C:\Users\user\Firebase

# Load .env from project root; override=False so real env vars take precedence.
# encoding='utf-8' prevents UnicodeDecodeError on Windows with non-UTF-8 ANSI.
load_dotenv(dotenv_path=BASE_DIR / ".env", encoding="utf-8", override=True)


class Settings:
    """
    Application settings loaded from environment variables.
    All sensitive values must be defined in the .env file.
    """

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = os.getenv("APP_NAME", "Linux Command Generator")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # ── CORS ─────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins, e.g.:
    # "http://localhost:5500,http://127.0.0.1:5500"
    ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]

    # ── Firebase Admin SDK ───────────────────────────────────────────────
    # FIREBASE_CREDENTIALS_PATH in .env can be:
    #   - an absolute path  (works on any OS)
    #   - a filename only   (e.g. "firebase-credentials.json") — resolved
    #     relative to BASE_DIR automatically in resolve_credentials_path().
    FIREBASE_CREDENTIALS_PATH: str = os.getenv(
        "FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json"
    )

    # ── Groq API ───────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    GROQ_BASE_URL: str | None = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # ── Firestore ────────────────────────────────────────────────────────
    FIRESTORE_COMMANDS_COLLECTION: str = os.getenv(
        "FIRESTORE_COMMANDS_COLLECTION", "commands"
    )

    def resolve_credentials_path(self) -> Path:
        """Return an absolute Path to the Firebase credentials JSON.

        If the configured value is already absolute, use it as-is.
        Otherwise resolve it relative to BASE_DIR (project root).
        This makes the setting portable across Windows and Linux.
        """
        raw = self.FIREBASE_CREDENTIALS_PATH.strip()
        p = Path(raw)
        if p.is_absolute():
            return p
        # Relative path — anchor to project root
        return (BASE_DIR / p).resolve()

    def validate(self) -> None:
        """Validate required settings at startup."""
        if not self.GROQ_API_KEY:
            print("WARNING: GROQ_API_KEY is not set. AI generation will fail.")

        cred_path = self.resolve_credentials_path()
        if not cred_path.is_file():
            print(
                f"WARNING: Firebase credentials file not found at '{cred_path}'. "
                "Firestore and Auth services will fail."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.
    Use this function everywhere instead of instantiating Settings directly.
    """
    return Settings()
