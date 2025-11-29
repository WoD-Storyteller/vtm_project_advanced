from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth")

class LoginForm(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(req: Request, form: LoginForm):
    # Replace with real DB lookup later
    if form.username == "admin" and form.password == "admin":
        req.session["user"] = form.username
        return {"ok": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
async def logout(req: Request):
    req.session.clear()
    return {"ok": True}
