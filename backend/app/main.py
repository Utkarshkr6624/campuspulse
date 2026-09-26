from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app import models  # noqa: F401
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, BadRequestError
from app.db.schema import prepare_database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    prepare_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(_request: Request, call_next):
    response = await call_next(_request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(_request: Request, exc: UnauthorizedError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(ForbiddenError)
async def forbidden_handler(_request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.detail})


@app.exception_handler(BadRequestError)
async def bad_request_handler(_request: Request, exc: BadRequestError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.detail})


@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.detail})


@app.exception_handler(ConflictError)
async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.exception_handler(IntegrityError)
async def integrity_handler(_request: Request, _exc: IntegrityError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": "The request conflicts with existing data."})


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    # Omit Pydantic's `input` field so invalid passwords and other request values aren't echoed.
    errors = [
        {key: value for key, value in error.items() if key in {"loc", "msg", "type"}}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


app.include_router(api_router, prefix="/api")
