from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from neptou_api.routers import chat, health, map_search, optimize, recommendations, search

load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI(title="Neptou AI Backend (Anthropic)", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(recommendations.router)
    app.include_router(search.router)
    app.include_router(optimize.router)
    app.include_router(map_search.router)

    return app


app = create_app()
