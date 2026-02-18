import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from app.auth.router import router as auth_router
from app.college.router import router as college_router
from app.core.logging import configure_logging
from app.game.router import router as game_router
from app.leaderboard.router import router as leaderboard_router
from app.mana.router import router as mana_router

configure_logging()
logger = logging.getLogger("steprealm.main")

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(college_router, prefix="/college", tags=["college"])
app.include_router(mana_router, prefix="/mana", tags=["mana"])
app.include_router(game_router, prefix="/game", tags=["game"])
app.include_router(leaderboard_router, prefix="/leaderboard", tags=["leaderboard"])


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error",
        extra={"path": request.url.path, "method": request.method},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.error(
        "http_error",
        extra={"path": request.url.path, "method": request.method, "status_code": exc.status_code},
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
