# api/auth/session.py
from starlette.middleware.sessions import SessionMiddleware


def add_session_middleware(app, secret_key: str) -> None:
    """
    Minimal session middleware wrapper.

    The Windows app uses JWT in Authorization headers, not cookies,
    but keeping this function avoids breaking imports elsewhere.
    """
    if not secret_key:
        secret_key = "dev-session-key"
    app.add_middleware(SessionMiddleware, secret_key=secret_key)
