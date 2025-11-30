import logging
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from api.auth.routes import router as auth_router
from api.auth.session import add_session_middleware

from api.map_routes import router as map_router
from core.travel.zones_loader import ZoneRegistry
from utils import load_data_from_file, save_data

# -----------------------------------------------------
# App / config
# -----------------------------------------------------

load_dotenv()

logger = logging.getLogger("vtm_api")
logging.basicConfig(level=logging.INFO)

DATA_PATH = os.getenv("DATA_PATH", "vtm_data.json")
DEFAULT_GUILD_ID = os.getenv("DEFAULT_GUILD_ID")

app = FastAPI(title="Garden of Ashes API")

# Session middleware (needed for Discord OAuth + dashboard)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
add_session_middleware(app, secret_key=SECRET_KEY)

# Static dashboard files (player / ST front-end)
app.mount(
    "/dashboard",
    StaticFiles(directory="dashboard", html=True),
    name="dashboard",
)

templates = Jinja2Templates(directory="templates")


# -----------------------------------------------------
# Startup / shutdown
# -----------------------------------------------------

@app.on_event("startup")
async def startup_event():
    global DEFAULT_GUILD_ID

    # Load main data store
    data_store = load_data_from_file(DATA_PATH)
    app.state.data_store = data_store

    # Try to infer default guild if not configured
    if not DEFAULT_GUILD_ID:
        guilds = data_store.get("guilds", {})
        if guilds:
            DEFAULT_GUILD_ID = str(next(iter(guilds.keys())))
            logger.info(
                "Inferred DEFAULT_GUILD_ID=%s from data store.", DEFAULT_GUILD_ID
            )
        else:
            DEFAULT_GUILD_ID = "0"
            logger.warning(
                "DEFAULT_GUILD_ID not set and no guilds found; using '0'."
            )

    app.state.default_guild_id = DEFAULT_GUILD_ID

    # Zone registry for travel/map systems
    zone_registry = ZoneRegistry()
    try:
        zone_registry.load()
        logger.info("ZoneRegistry loaded from data/zones.json")
    except FileNotFoundError:
        logger.warning("No data/zones.json found. Run your zones sync command first.")
    app.state.zone_registry = zone_registry

    logger.info("Startup initialisation complete.")


@app.on_event("shutdown")
async def shutdown_event():
    """Persist any changes back to disk when the API shuts down."""
    data_store = getattr(app.state, "data_store", None)
    if data_store is not None:
        save_data(DATA_PATH, data_store)
        logger.info("Saved data store to %s", DATA_PATH)


# -----------------------------------------------------
# Routers
# -----------------------------------------------------

# Discord / auth endpoints + /auth/session
app.include_router(auth_router)

# Map API routes (zones, players, director state)
app.include_router(map_router)


# -----------------------------------------------------
# Basic views
# -----------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Garden of Ashes API is running"}


@app.get("/map")
async def map_view(request: Request):
    """World map viewer – uses templates/map_view.html + static/map/map.js"""
    return templates.TemplateResponse("map_view.html", {"request": request})