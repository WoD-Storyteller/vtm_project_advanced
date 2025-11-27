# api/main.py

import logging
from fastapi import FastAPI
from dotenv import load_dotenv

from api.config import settings
from api.auth.session import add_session_middleware
from api.auth.routes import router as auth_router

from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/map")
async def map_view(request: Request):
    return templates.TemplateResponse("map_view.html", {"request": request})
    
# Load environment
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(
    title="VTM Backend API",
    version="1.0.0"
)

# Sessions
add_session_middleware(app, secret_key=settings.SECRET_KEY)

# Routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])


# Health check
@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "service": "VTM API"}


@app.get("/health", tags=["health"])
async def health():
    return {"ok": True}
