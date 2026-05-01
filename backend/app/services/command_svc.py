"""
services/command_svc.py
-----------------------
Command service layer — Firestore CRUD + AI orchestration.

Responsibility:
  - Coordinate between openai_svc (AI generation) and Firestore (persistence).
  - Enforce data-ownership rules (a user can only access their own commands).
  - Translate Firestore documents into clean Python dicts ready for Pydantic.

This module does NOT know about HTTP requests, headers, or routing.
All HTTP concerns (status codes, HTTPException) are raised here only for
business-logic violations (403 Forbidden, 404 Not Found).
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.config import get_settings
from app.core.firebase import firestore_db
from app.services.groq_svc import generate_linux_command

# Collection name from config (default: "commands")
_COLLECTION = get_settings().FIRESTORE_COMMANDS_COLLECTION


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

async def generate_and_save_command(uid: str, prompt: str) -> dict:
    """
    Orchestrate the full generate-then-persist flow.

    Steps:
      1. Call Groq to produce a Linux command from the Vietnamese prompt.
      2. Build a Firestore document with uid, prompt, command, and UTC timestamp.
      3. Save the document to the ``commands`` collection.
      4. Return the saved document as a dict (including the auto-generated ID).

    Args:
        uid    : Firebase UID of the authenticated user.
        prompt : Vietnamese natural-language description from the client.

    Returns:
        Dict with keys: id, uid, prompt, command, created_at.

    Raises:
        HTTPException 422/503/500 : Propagated from groq_svc if AI call fails.
        HTTPException 500         : Firestore write failure.
    """

    # ── Step 1: Generate command via Groq (Llama 3) ────────────────────────
    command: str = await generate_linux_command(prompt)

    # ── Step 2: Build document payload ───────────────────────────────────
    now_utc = datetime.now(tz=timezone.utc)

    payload: dict[str, Any] = {
        "uid": uid,
        "prompt": prompt,
        "command": command,
        "created_at": now_utc,   # Firestore stores this as a Timestamp
    }

    # ── Step 3: Persist to Firestore ─────────────────────────────────────
    try:
        # add() auto-generates a document ID and returns a DocumentReference.
        doc_ref = firestore_db.collection(_COLLECTION).add(payload)

        # firestore.add() returns a tuple: (update_time, DocumentReference)
        # Unpack safely regardless of SDK version.
        if isinstance(doc_ref, tuple):
            _, doc_ref = doc_ref

        document_id: str = doc_ref.id

    except Exception as exc:
        print(f"[command_svc] Firestore write error: {exc}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lưu lệnh vào cơ sở dữ liệu. Vui lòng thử lại.",
        )

    print(f"[command_svc] Đã lưu command thành công vào DB. ID: {document_id}")
    # ── Step 4: Return the persisted document ────────────────────────────
    return {
        "id": document_id,
        **payload,
    }


def get_user_commands(uid: str) -> list[dict]:
    """
    Retrieve the command history for a specific user, newest first.

    Firestore query:
        WHERE uid == <uid>
        ORDER BY created_at DESCENDING

    Args:
        uid: Firebase UID of the authenticated user.

    Returns:
        List of dicts (may be empty), each with keys:
        id, uid, prompt, command, created_at.

    Raises:
        HTTPException 500: Firestore query failure.
    """

    try:
        from google.cloud.firestore_v1 import Query

        docs = (
            firestore_db
            .collection(_COLLECTION)
            .where(filter=FieldFilter("uid", "==", uid))
            .order_by("created_at", direction=Query.DESCENDING)
            .stream()
        )

        results: list[dict] = []
        for doc in docs:
            data = doc.to_dict()
            results.append(_normalize_document(doc.id, data))

        return results

    except Exception as exc:
        print(f"[command_svc] Firestore query error (get_user_commands): {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy lịch sử lệnh. Vui lòng thử lại.",
        )


def get_command_by_id(uid: str, command_id: str) -> dict:
    """
    Retrieve a single command document and enforce ownership.

    Ownership rule:
        The ``uid`` stored in the Firestore document MUST match the
        ``uid`` of the currently authenticated user. If they differ,
        raise 403 Forbidden — do NOT reveal that the document exists.

    Args:
        uid        : Firebase UID of the authenticated user.
        command_id : Firestore document ID.

    Returns:
        Dict with keys: id, uid, prompt, command, created_at.

    Raises:
        HTTPException 404: Document does not exist.
        HTTPException 403: Document exists but belongs to a different user.
        HTTPException 500: Firestore read failure.
    """

    try:
        doc_ref = firestore_db.collection(_COLLECTION).document(command_id)
        doc = doc_ref.get()

    except Exception as exc:
        print(f"[command_svc] Firestore read error (get_command_by_id): {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể đọc dữ liệu từ cơ sở dữ liệu. Vui lòng thử lại.",
        )

    # ── 404: Document does not exist ─────────────────────────────────────
    if not doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy lệnh với ID: {command_id}",
        )

    data = doc.to_dict()

    # ── 403: Ownership check ──────────────────────────────────────────────
    # Intentionally use 403 (not 404) so the client knows the ID is valid
    # but they lack permission — consistent with RESTful security practices.
    if data.get("uid") != uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền truy cập lệnh này.",
        )

    return _normalize_document(doc.id, data)


# ═══════════════════════════════════════════════════════════════════════════════
# PRIVATE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_document(doc_id: str, data: dict) -> dict:
    """
    Convert a raw Firestore document dict into a normalized Python dict.

    Handles:
      - Adding the document ``id`` field (not stored inside the document).
      - Converting Firestore Timestamp → Python datetime (UTC-aware).
      - Providing safe defaults for missing fields.

    Args:
        doc_id : Firestore document ID string.
        data   : Raw dict from doc.to_dict().

    Returns:
        Normalized dict compatible with CommandResponse / CommandDetail schemas.
    """
    created_at = data.get("created_at")

    # Firestore Timestamps have a .replace() or are already datetime objects.
    # Ensure we always return a timezone-aware datetime.
    if isinstance(created_at, datetime):
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
    else:
        # Firestore Timestamp object → convert to datetime
        try:
            created_at = created_at.astimezone(timezone.utc)
        except (AttributeError, TypeError):
            created_at = datetime.now(tz=timezone.utc)

    return {
        "id": doc_id,
        "uid": data.get("uid", ""),
        "prompt": data.get("prompt", ""),
        "command": data.get("command", ""),
        "created_at": created_at,
    }
