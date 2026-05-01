"""
services/auth_svc.py
--------------------
Authentication service layer.

Responsibility:
  - Verify Firebase ID Token sent by the client.
  - Extract and return user claims (uid, email, name, picture).
  - Translate all Firebase auth exceptions into FastAPI HTTPExceptions
    so the router layer stays clean.

This module does NOT handle routing, request parsing, or response formatting.
Those concerns belong in routers/auth.py.
"""

from firebase_admin import auth
from fastapi import HTTPException, status

from app.core.firebase import firebase_auth


# ── Type alias for decoded token dict ────────────────────────────────────────
DecodedToken = dict


def verify_token(id_token: str) -> DecodedToken:
    """
    Verify a Firebase ID Token and return the decoded claims.

    Args:
        id_token: Raw JWT string from the Authorization header
                  (typically: `Bearer <token>` stripped by the router).

    Returns:
        A dict containing at minimum:
            - ``uid``     (str)  : Firebase User ID
            - ``email``   (str | None)
            - ``name``    (str | None)
            - ``picture`` (str | None)

    Raises:
        HTTPException 401 : Token is expired, invalid, revoked, or malformed.
        HTTPException 500 : Unexpected server-side Firebase error.
    """

    try:
        decoded: DecodedToken = firebase_auth.verify_id_token(
            id_token,
            check_revoked=True,   # Also reject tokens whose session was revoked
        )
        return decoded

    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn. Vui lòng đăng nhập lại.",
        )

    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã bị thu hồi. Vui lòng đăng nhập lại.",
        )

    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ. Xác thực thất bại.",
        )

    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại trong hệ thống Firebase.",
        )

    except auth.CertificateFetchError:
        # Firebase's public key endpoint is temporarily unavailable.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể xác thực token lúc này. Vui lòng thử lại sau.",
        )

    except Exception as exc:
        # Catch-all: log the real error server-side, return generic 500.
        # In production, replace print() with a proper logger.
        print(f"[auth_svc] Unexpected error during token verification: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi máy chủ nội bộ trong quá trình xác thực.",
        )


def extract_user_info(decoded_token: DecodedToken) -> dict:
    """
    Normalize the raw decoded token dict into a clean user-info dict.

    Firebase tokens may or may not contain optional fields (name, picture)
    depending on the sign-in provider. This helper centralizes the extraction
    so callers never need to deal with KeyError.

    Args:
        decoded_token: Dict returned by verify_token().

    Returns:
        Dict with keys: uid, email, name, picture.
    """
    return {
        "uid": decoded_token.get("uid") or decoded_token.get("user_id", ""),
        "email": decoded_token.get("email"),
        "name": decoded_token.get("name"),
        "picture": decoded_token.get("picture"),
    }
