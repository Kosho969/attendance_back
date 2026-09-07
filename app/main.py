from collections import defaultdict

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import Base, engine
from .routers import activities, auth, checkin, users

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Attendance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Reshape Pydantic's default error format into Laravel-style {"errors": {field: [msg, ...]}}."""
    errors: dict[str, list[str]] = defaultdict(list)
    for error in exc.errors():
        field = str(error["loc"][-1])
        message = error["msg"].removeprefix("Value error, ")
        errors[field].append(message)
    return JSONResponse(status_code=422, content={"errors": dict(errors)})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Keep {"message": ...} for plain-string errors, {"errors": {...}} for field errors."""
    if isinstance(exc.detail, dict) and "errors" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(activities.router, prefix="/api")
app.include_router(checkin.router, prefix="/api")


@app.get("/up")
def health():
    return {"status": "ok"}
