# api/auth/session.py

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

def add_session_middleware(app: FastAPI, secret_key: str):
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        same_site="lax",
        https_only=False  # Set to True if HTTPS is enforced
    )
