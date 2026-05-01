"""
routers/commands.py
-------------------
Commands router — handles /commands endpoints (feature core).

Endpoints:
  POST /commands              — Generate a Linux command via OpenAI + save to Firestore.
  GET  /commands              — Retrieve the authenticated user's command history.
  GET  /commands/{command_id} — Retrieve a specific command (with ownership check).

All endpoints are protected by the get_current_user dependency.
All business logic is delegated to command_svc.
"""

from typing import List

from fastapi import APIRouter, Depends, Path

from app.dependencies import get_current_user
from app.schemas.command import (
    CommandDetail,
    CommandListItem,
    CommandRequest,
    CommandResponse,
)
from app.services import command_svc

router = APIRouter()


@router.post(
    "/",
    response_model=CommandResponse,
    status_code=201,
    summary="Sinh lệnh Linux từ tiếng Việt",
    description=(
        "Nhận mô tả yêu cầu bằng tiếng Việt, gọi Groq (Llama 3) để sinh "
        "lệnh Linux tương ứng, lưu kết quả vào Firestore và trả về bản ghi đầy đủ."
    ),
)
async def create_command(
    body: CommandRequest,
    current_user: dict = Depends(get_current_user),
) -> CommandResponse:
    """
    POST /commands

    Flow:
      1. Dependency extracts & verifies uid from Bearer token.
      2. body.prompt is passed to command_svc alongside uid.
      3. command_svc calls Groq → gets Linux command string.
      4. command_svc persists {uid, prompt, command, created_at} to Firestore.
      5. Router returns the saved document as CommandResponse.
    """
    uid: str = current_user["uid"]
    result = await command_svc.generate_and_save_command(uid=uid, prompt=body.prompt)
    return CommandResponse(**result)


@router.get(
    "/",
    response_model=List[CommandListItem],
    summary="Lấy lịch sử lệnh của người dùng",
    description=(
        "Truy vấn Firestore để lấy toàn bộ lịch sử lệnh Linux của người dùng "
        "đang đăng nhập, sắp xếp theo thứ tự mới nhất lên đầu."
    ),
)
def list_commands(
    current_user: dict = Depends(get_current_user),
) -> List[CommandListItem]:
    """
    GET /commands

    Flow:
      1. Dependency extracts uid from Bearer token.
      2. command_svc queries Firestore: WHERE uid == uid ORDER BY created_at DESC.
      3. Router maps each document dict → CommandListItem schema.
    """
    uid: str = current_user["uid"]
    results = command_svc.get_user_commands(uid=uid)
    return [CommandListItem(**item) for item in results]


@router.get(
    "/{command_id}",
    response_model=CommandDetail,
    summary="Lấy chi tiết một lệnh cụ thể",
    description=(
        "Lấy toàn bộ thông tin của một lệnh dựa trên Firestore document ID. "
        "Chỉ trả về nếu lệnh thuộc sở hữu của người dùng đang đăng nhập "
        "(403 Forbidden nếu không phải chủ sở hữu)."
    ),
)
def get_command(
    command_id: str = Path(
        ...,
        description="Firestore document ID của lệnh cần xem.",
        min_length=1,
    ),
    current_user: dict = Depends(get_current_user),
) -> CommandDetail:
    """
    GET /commands/{command_id}

    Flow:
      1. Dependency extracts uid from Bearer token.
      2. command_svc fetches the document by command_id.
      3. command_svc compares document.uid vs current user uid:
           - Mismatch → raises HTTPException 403 Forbidden.
           - Missing   → raises HTTPException 404 Not Found.
      4. Router maps result dict → CommandDetail schema.
    """
    uid: str = current_user["uid"]
    result = command_svc.get_command_by_id(uid=uid, command_id=command_id)
    return CommandDetail(**result)
