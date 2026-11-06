from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException

from .config import Settings
from .documents import MAX_BYTES, prepare_document
from .errors import AppError
from .llm import Analyzer, OpenAIAnalyzer
from .models import Analysis, AnalysisResponse, Document
from .report import build_report
from .service import verify_analysis

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
EXAMPLES = [
    {"id": "postgres", "title": "PostgreSQL connection", "description": "A refused database connection"},
    {"id": "missing-env", "title": "Missing configuration", "description": "A required environment variable"},
    {"id": "port-in-use", "title": "Port already in use", "description": "An application that cannot bind"},
    {"id": "healthy", "title": "Healthy startup", "description": "A successful start, without errors"},
]


class BodyLimit:
    """Bound multipart overhead and file bytes before the form parser spools data."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if scope["method"] == "POST" and scope["path"] in ("/api/preview", "/api/analyze"):
            chunks, total = [], 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                total += len(chunk)
                if total > MAX_BYTES + 8192:
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "request_too_large",
                                "message": "Upload one file up to 64 KiB (65,536 bytes).",
                            }
                        },
                    )
                    response.headers["Cache-Control"] = "no-store"
                    return await response(scope, receive, send)
                chunks.append(chunk)
                if not message.get("more_body", False):
                    break
            body = b"".join(chunks)
            delivered = False

            async def buffered_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()

            return await self.app(scope, buffered_receive, send)
        return await self.app(scope, receive, send)


async def read_document(request: Request) -> Document:
    if not request.headers.get("content-type", "").startswith("multipart/form-data"):
        raise AppError("invalid_upload", "Upload one file using multipart/form-data.")
    try:
        async with request.form(max_files=2, max_fields=0, max_part_size=MAX_BYTES) as form:
            items = list(form.multi_items())
            if len(items) != 1 or items[0][0] != "file" or not isinstance(items[0][1], UploadFile):
                raise AppError("invalid_upload", "Upload exactly one file in the 'file' field.")
            upload = items[0][1]
            return prepare_document(upload.filename or "", await upload.read(MAX_BYTES + 1))
    except HTTPException:
        raise AppError("invalid_upload", "Upload exactly one .log or .txt file, up to 64 KiB.") from None


def create_app(settings: Settings | None = None, analyzer: Analyzer | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings()
    engine = analyzer if analyzer is not None else OpenAIAnalyzer(settings)
    app = FastAPI(title="ServerMedic", version="0.1.0")
    app.add_middleware(BodyLimit)

    @app.middleware("http")
    async def no_store(request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            # Handle unexpected failures before Uvicorn can log a data-bearing traceback.
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "internal_error",
                        "message": "Analysis failed unexpectedly. Please try again.",
                    }
                },
            )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "invalid_request", "message": "The request could not be validated."}},
        )

    @app.get("/api/health")
    async def health():
        return {
            "status": "ok",
            "analysis_configured": analyzer is not None or settings.configured,
            "provider": engine.provider,
            "model": engine.model,
        }

    @app.get("/api/examples")
    async def examples():
        return EXAMPLES

    @app.get("/api/examples/{example_id}")
    async def example(example_id: str):
        if example_id not in {item["id"] for item in EXAMPLES}:
            raise AppError("not_found", "Example not found.", 404)
        return Response((EXAMPLES_DIR / f"{example_id}.log").read_bytes(), media_type="text/plain")

    @app.post("/api/preview", response_model=Document)
    async def preview(request: Request):
        return await read_document(request)

    @app.post("/api/analyze", response_model=AnalysisResponse)
    async def analyze(request: Request):
        document = await read_document(request)
        raw = await engine.analyze(document)
        try:
            # Revalidate even injected providers; they must obey the same contract.
            analysis = Analysis.model_validate(raw.model_dump() if isinstance(raw, Analysis) else raw)
        except (ValueError, TypeError):
            raise AppError(
                "invalid_result", "The model returned an invalid result. Please try again.", 502
            ) from None
        verified = verify_analysis(analysis, document)
        return AnalysisResponse(
            document=document,
            analysis=verified,
            markdown=build_report(document, verified, engine.provider, engine.model),
            provider=engine.provider,
            model=engine.model,
        )

    return app


app = create_app()
