"""Membuat aplikasi FastAPI SPK UMKM."""
from contextlib import asynccontextmanager
from http import HTTPStatus
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from . import config
from . import database as db
from . import security
from .dependencies import LoginRequired, verify_csrf
from .routes import api, auth, dashboard, periods, ranking, umkm, weighting
from .services.sample_umkm import seed_sample_umkm
from .templating import FRONTEND, register_routes, render

ROUTE_MODULES = (auth, dashboard, umkm, periods, weighting, ranking, api)

DEFAULT_ERROR_TEXT = {
    400: "Permintaan tidak bisa diproses.",
    403: "Akun Anda tidak punya izin untuk membuka halaman ini.",
    404: "Halaman yang Anda cari tidak ada.",
    405: "Cara akses ini tidak diizinkan untuk halaman tersebut.",
    413: "Berkas terlalu besar. Maksimal 5 MB.",
}


def create_app(db_path=None) -> FastAPI:
    """Buat aplikasi SPK yang membaca data dari database SQLite."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = db.connect(app.state.db_path)
        try:
            db.init_db(conn)
            security.seed_users(conn, config.DEFAULT_USERS)
            seed_sample_umkm(conn)
        finally:
            conn.close()
        yield

    # verify_csrf dipasang global: semua POST wajib membawa token CSRF
    app = FastAPI(
        title="SPK Prioritas Bantuan UMKM",
        lifespan=lifespan,
        dependencies=[Depends(verify_csrf)],
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.db_path = Path(db_path or config.DB_PATH)

    app.add_middleware(
        SessionMiddleware,
        secret_key=config.SECRET_KEY,
        same_site="lax",
        max_age=8 * 3600,
        session_cookie="spk_sesi",
    )
    app.mount("/static", StaticFiles(directory=FRONTEND / "static"), name="static")
    for module in ROUTE_MODULES:
        app.include_router(module.router)
    register_routes(app, [m.router for m in ROUTE_MODULES])

    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok"}

    @app.exception_handler(LoginRequired)
    async def need_login(request: Request, exc: LoginRequired):
        target = request.url.path + (f"?{request.url.query}" if request.url.query else "")
        url = "/login" + (f"?next={target}" if request.method == "GET" and target != "/" else "")
        return RedirectResponse(url, 303)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        phrase = HTTPStatus(exc.status_code).phrase
        message = exc.detail if exc.detail != phrase else DEFAULT_ERROR_TEXT.get(exc.status_code, phrase)
        return render(
            request,
            "error.html",
            status_code=exc.status_code,
            with_period=False,
            code=exc.status_code,
            title=phrase,
            message=message,
        )

    @app.exception_handler(RequestValidationError)
    async def bad_input(request: Request, exc: RequestValidationError):
        return render(
            request,
            "error.html",
            status_code=404,
            with_period=False,
            code=404,
            title="Not Found",
            message=DEFAULT_ERROR_TEXT[404],
        )

    return app


app = create_app()
