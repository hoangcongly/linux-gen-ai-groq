"""
core/firebase.py
----------------
Firebase Admin SDK initialization (singleton pattern).

Provides two pre-initialized clients:
  - firebase_auth  : firebase_admin.auth  (verify ID tokens)
  - firestore_db   : google.cloud.firestore.Client  (read/write documents)

Both are initialized once at module import time. If initialization fails
(e.g. missing credentials file), the error is caught and re-raised with a
human-readable message so the application fails fast on startup rather than
producing cryptic 500 errors at request time.

Cross-platform note
-------------------
The credentials file path is resolved via ``Settings.resolve_credentials_path()``
which uses ``pathlib.Path`` anchored to the project root. This means the same
.env value works correctly on Windows and Linux without any modification.
"""

import firebase_admin
from firebase_admin import auth as firebase_auth_module
from firebase_admin import credentials, firestore

from app.core.config import get_settings

# ── Module-level singletons ──────────────────────────────────────────────────
# These are set during _initialize_firebase() and exposed as public names.
firebase_auth = None          # firebase_admin.auth module
firestore_db = None           # google.cloud.firestore.Client instance
_firebase_app = None          # firebase_admin.App instance (kept for reference)


def _initialize_firebase() -> None:
    """
    Initialize the Firebase Admin SDK.

    Called once at module import. Subsequent imports reuse the already-
    initialized app thanks to the `_firebase_app is not None` guard.

    Raises:
        FileNotFoundError : credentials JSON file not found at configured path.
        ValueError        : credentials file exists but is malformed / invalid.
        RuntimeError      : any other unexpected Firebase initialization error.
    """
    global firebase_auth, firestore_db, _firebase_app

    # Already initialized — nothing to do.
    if firebase_admin._apps:
        _firebase_app = firebase_admin.get_app()
        firebase_auth = firebase_auth_module
        firestore_db = firestore.client()
        return

    settings = get_settings()
    # resolve_credentials_path() returns an absolute pathlib.Path,
    # cross-platform (works on Windows backslash and Linux slash).
    cred_path = settings.resolve_credentials_path()

    # ── Validate credentials file existence before attempting init ────────
    if not cred_path.is_file():
        print(
            f"WARNING: Firebase credentials file not found at: '{cred_path}'. "
            "Auth and Firestore features will NOT work."
        )
        return

    try:
        # Pass the string representation for SDK compatibility
        cred = credentials.Certificate(str(cred_path))
        _firebase_app = firebase_admin.initialize_app(cred)

        # Expose the auth module and Firestore client as module-level names.
        firebase_auth = firebase_auth_module
        firestore_db = firestore.client()

    except ValueError as exc:
        raise ValueError(
            f"Firebase credentials file is invalid or malformed: {exc}\n"
            "Please ensure the file is a valid service account JSON."
        ) from exc

    except Exception as exc:
        raise RuntimeError(
            f"Unexpected error while initializing Firebase Admin SDK: {exc}"
        ) from exc


# ── Run initialization at import time ────────────────────────────────────────
_initialize_firebase()
