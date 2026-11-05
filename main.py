"""FastAPI application entry point.

Creates the app, adds CORS and mounts the HTTP routers.
"""
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from config import settings
from database import get_session
from routers import auth, ships, users

app = FastAPI()

# Clients authenticate with bearer tokens, not cookies, so no credentials mode.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(users.router)
app.include_router(ships.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    """Root greeting / liveness check.

    Confirms the API process is up and serving requests (does not touch the
    database — see `/health` for a readiness probe).

    Returns:
        A welcome message for the crew.
    """
    return {"message": "Welcome aboard your HomeShip!"}


@app.get("/health")
def health(session: Session = Depends(get_session)):
    """Readiness probe: confirm the app can reach the database.

    Runs a trivial `SELECT 1`; if the database is unreachable the query
    raises and the endpoint returns 500, signalling "not ready" to the
    platform's health check.

    Args:
        session: Request-scoped session, injected via `get_session`.

    Returns:
        `{"status": "ok"}` when the database round-trip succeeds.
    """
    session.execute(text("SELECT 1"))
    return {"status": "ok"}
