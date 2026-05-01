"""
app/dependencies.py
--------------------
Shared FastAPI dependency functions — reused across all protected routers.

Having dependencies in a dedicated module prevents circular imports
(routers importing from each other) and makes it trivial to swap the
auth backend in the future without touching router code.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth_svc import extract_user_info, verify_token

# HTTPBearer extracts the token from "Authorization: Bearer <token>" header.
# auto_error=True means FastAPI returns 403 automatically if the header
# is missing, before our code even runs.
_bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency — authenticate and return the current user.

    Extracts the Bearer token from the Authorization header, verifies it
    against Firebase Auth, and returns a normalized user-info dict.

    Usage in any protected endpoint::

        @router.get("/protected")
        def protected_route(user: dict = Depends(get_current_user)):
            uid = user["uid"]

    Returns:
        dict with keys: uid, email, name, picture

    Raises:
        HTTPException 401 : Token missing, invalid, expired, or revoked.
        HTTPException 403 : Authorization header missing (raised by HTTPBearer).
    """
    id_token: str = credentials.credentials

    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token xác thực không được để trống.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    decoded_token = verify_token(id_token)
    return extract_user_info(decoded_token)
