"""FastAPI application entry point.

Creates the app and mounts the HTTP routers.
"""
from fastapi import FastAPI

from routers import users

app = FastAPI()

app.include_router(users.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
