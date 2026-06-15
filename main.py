"""FastAPI application entry point.

Creates the app and mounts the HTTP routers.
"""
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_session
from routers import auth, ships, users

app = FastAPI()

app.include_router(users.router)
app.include_router(ships.router)
app.include_router(auth.router)


@app.get("/")
async def root():
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
