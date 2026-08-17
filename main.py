import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.routes.games import router as games_router
from app.api.routes.histories import router as histories_router
from app.database import initialize_database
from app.scrapers.browser import steam_browser


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await asyncio.to_thread(initialize_database)
    try:
        yield
    finally:
        await asyncio.to_thread(steam_browser.close)


app = FastAPI(title="Steam Scraper API", lifespan=lifespan)
register_error_handlers(app)
app.include_router(games_router)
app.include_router(histories_router)
