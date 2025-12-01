from starlette.middleware.sessions import SessionMiddleware


def add_session_middleware(app, secret_key: str) -> None:
    """
    Attach signed cookie-based session support to the FastAPI app.

    This is required for Discord OAuth and /auth/session to work.
    """
    app.add_middleware(SessionMiddleware, secret_key=secret_key)