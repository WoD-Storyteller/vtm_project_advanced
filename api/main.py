import logging
import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from auth_routes import router as auth_router
from auth.session import add_session_middleware

from api.map_routes import router as map_router
from core.travel.zones_loader import ZoneRegistry
from utils import load_data_from_file, save_data

# -----------------------------------------------------
# LOGGING / ENV
# -----------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Path to your persistent guild/world data
DATA_PATH = os.getenv("DATA_PATH", "data/guild_data.json")

# Default guild ID used by the dashboard / map API
DEFAULT_GUILD_ID = os.getenv("DEFAULT_GUILD_ID")


# -----------------------------------------------------
# FASTAPI APP
# -----------------------------------------------------

app = FastAPI(title="Garden of Ashes API")

# Session middleware for auth (your existing system)
add_session_middleware(app, secret_key=os.getenv("SECRET_KEY", "change-me"))

# Templates and static files (for dashboard + map)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# -----------------------------------------------------
# APP STATE INITIALISATION
# -----------------------------------------------------

@app.on_event("startup")
async def startup_event():
    """
    Load persistent data and zone registry into app.state for use by routes.
    """
    # Load data store
    try:
        data_store = load_data_from_file(DATA_PATH)
        logger.info(f"Loaded data store from {DATA_PATH}")
    except FileNotFoundError:
        logger.warning(f"No data file at {DATA_PATH}, starting with empty store.")
        data_store = {"guilds": {}}

    app.state.data_store = data_store

    # Determine default guild id
    global DEFAULT_GUILD_ID
    if DEFAULT_GUILD_ID is None or DEFAULT_GUILD_ID == "":
        # Try to infer from data_store
        guilds = data_store.get("guilds", {})
        if guilds:
            DEFAULT_GUILD_ID = str(next(iter(guilds.keys())))
            logger.info(f"Inferred DEFAULT_GUILD_ID={DEFAULT_GUILD_ID} from data store.")
        else:
            DEFAULT_GUILD_ID = "0"
            logger.warning("DEFAULT_GUILD_ID not set and no guilds found; using '0'.")

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
    """
    Persist any changes back to disk when the API shuts down.
    """
    data_store = getattr(app.state, "data_store", None)
    if data_store is not None:
        save_data(DATA_PATH, data_store)
        logger.info(f"Saved data store to {DATA_PATH}")


# -----------------------------------------------------
# ROUTES
# -----------------------------------------------------

# Auth routes (existing)
app.include_router(auth_router)

# Map API routes (zones, players, director state)
app.include_router(map_router)


@app.get("/")
async def root():
    return {"message": "Garden of Ashes API is running"}


@app.get("/map")
async def map_view(request: Request):
    """
    World map viewer – uses templates/map_view.html + static/map/map.js
    """
    return templates.TemplateResponse("map_view.html", {"request": request})