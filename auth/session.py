
from starlette.middleware.sessions import SessionMiddleware

def add_session_middleware(app, secret_key: str):
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        max_age=60*60*24*7,
    )
