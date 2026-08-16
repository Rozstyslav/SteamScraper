from fastapi import FastAPI

from app.api.routes.games import router as games_router
from app.api.routes.histories import router as histories_router

app = FastAPI(title="Steam Scraper API")
app.include_router(games_router)
app.include_router(histories_router)
