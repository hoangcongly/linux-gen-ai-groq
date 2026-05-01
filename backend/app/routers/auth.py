"""
routers/auth.py
---------------
Authentication router — handles /auth endpoints.

Endpoints:
  POST /auth/login  — Verify a Firebase ID Token, return user info.
  GET  /auth/me     — Return the currently authenticated user's info.

This router contains ZERO business logic. It delegates everything to
auth_svc and uses the shared get_current_user dependency for protection.
"""

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.schemas.command import TokenRequest, UserResponse
from app.services.auth_svc import extract_user_info, verify_token

router = APIRouter()


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Đăng nhập bằng Firebase ID Token",
    description=(
        "Nhận Firebase ID Token từ client (sau khi người dùng đăng nhập "
        "bằng Google hoặc Email/Password trên frontend). "
        "Xác thực token và trả về thông tin người dùng."
    ),
)
def login(body: TokenRequest) -> UserResponse:
    """
    POST /auth/login

    Flow:
      1. Client signs in via Firebase JS SDK → receives idToken.
      2. Client sends idToken in request body to this endpoint.
      3. Backend verifies token with Firebase Admin SDK.
      4. Backend returns uid + profile info.

    The returned uid is used by the frontend to confirm identity,
    but the idToken itself is what must be sent in subsequent
    Authorization headers.
    """
    decoded_token = verify_token(body.id_token)
    user_info = extract_user_info(decoded_token)
    return UserResponse(**user_info)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Lấy thông tin người dùng hiện tại",
    description=(
        "Endpoint được bảo vệ. Yêu cầu header: Authorization: Bearer <idToken>. "
        "Trả về thông tin của người dùng đang đăng nhập."
    ),
)
def get_me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """
    GET /auth/me

    The get_current_user dependency handles all token verification.
    This handler simply returns the already-extracted user dict.
    """
    return UserResponse(**current_user)
