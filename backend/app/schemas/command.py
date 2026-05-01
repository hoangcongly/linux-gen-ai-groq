"""
schemas/command.py
------------------
Pydantic v2 models (schemas) for the /commands endpoints.

Separation of concerns:
  - Request schemas  : data coming IN  from the client
  - Response schemas : data going  OUT to the client
  - Internal schemas : data stored in / read from Firestore

None of these schemas contain business logic — they are pure data contracts.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS  (client → backend)
# ═══════════════════════════════════════════════════════════════════════════════

class CommandRequest(BaseModel):
    """
    Body of POST /commands.
    The client sends a natural-language description in Vietnamese and the
    backend returns the corresponding Linux command.
    """

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Mô tả yêu cầu bằng tiếng Việt (tối thiểu 3 ký tự).",
        examples=["Hiển thị dung lượng ổ đĩa còn trống"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS  (backend → client)
# ═══════════════════════════════════════════════════════════════════════════════

class CommandResponse(BaseModel):
    """
    Returned by POST /commands after a command is generated and persisted.
    """

    id: str = Field(..., description="Firestore document ID.")
    prompt: str = Field(..., description="Yêu cầu gốc bằng tiếng Việt.")
    command: str = Field(..., description="Lệnh Linux được sinh ra bởi OpenAI (ChatGPT).")
    uid: str = Field(..., description="Firebase UID của người dùng.")
    created_at: datetime = Field(..., description="Thời điểm tạo (UTC).")

    model_config = {"from_attributes": True}


class CommandListItem(BaseModel):
    """
    Lightweight representation used in GET /commands (history list).
    Omits heavy fields to keep list responses compact.
    """

    id: str = Field(..., description="Firestore document ID.")
    prompt: str = Field(..., description="Yêu cầu gốc bằng tiếng Việt.")
    command: str = Field(..., description="Lệnh Linux được sinh ra.")
    created_at: datetime = Field(..., description="Thời điểm tạo (UTC).")

    model_config = {"from_attributes": True}


class CommandDetail(BaseModel):
    """
    Full detail returned by GET /commands/{command_id}.
    Identical to CommandResponse — kept as a separate schema so it can
    diverge independently in the future (e.g. adding explanation field).
    """

    id: str
    prompt: str
    command: str
    uid: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# GENERIC RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    """Returned by GET /health."""

    status: str = "ok"
    version: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic single-message response (e.g. root endpoint)."""

    message: str


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class TokenRequest(BaseModel):
    """Body of POST /auth/login."""

    id_token: str = Field(
        ...,
        min_length=1,
        description="Firebase ID Token obtained from the client SDK.",
    )


class UserResponse(BaseModel):
    """Returned by POST /auth/login and GET /auth/me."""

    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
