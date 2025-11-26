# api/auth/routes.py

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


# ========== MODELS ==========

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ========== ROUTES ==========

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    # TODO: Replace with DB lookup or JWT auth
    if payload.username != "admin" or payload.password != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    fake_token = "example.jwt.token"
    return LoginResponse(access_token=fake_token)
