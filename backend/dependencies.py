"""Dependensi FastAPI yang dipasang pada rute: koneksi database, login, peran, CSRF, form.

Cara baca: sebuah rute yang menulis `user=Depends(login_required)` hanya jalan bila pengguna
sudah masuk; `Depends(require_role("admin"))` juga memeriksa perannya.
"""
import secrets

from fastapi import Depends, HTTPException, Request

from . import config
from . import database as db


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class LoginRequired(Exception):
    """Belum masuk. Ditangani di main.py: arahkan ke halaman login."""


# ---------------------------------------------------------------- database
def get_db(request: Request):
    """Satu koneksi SQLite per permintaan; ditutup otomatis setelah respons."""
    conn = db.connect(request.app.state.db_path)
    request.state.db = conn
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------- form + CSRF
async def read_form(request: Request):
    """Isi formulir (kosong untuk GET). Berkas yang terlalu besar ditolak sebelum dibaca."""
    if request.method in SAFE_METHODS:
        return {}
    try:
        size = int(request.headers.get("content-length", 0))
    except ValueError:
        size = 0
    if size > config.MAX_UPLOAD_BYTES + 64 * 1024:
        raise HTTPException(413, "Berkas terlalu besar. Maksimal 5 MB.")
    return await request.form()


async def verify_csrf(request: Request):
    """Semua permintaan yang mengubah data harus membawa token CSRF yang cocok dengan sesi."""
    if request.method in SAFE_METHODS:
        return
    form = await read_form(request)
    sent = str(form.get("_csrf") or request.headers.get("x-csrf-token", ""))
    expected = request.session.get("_csrf", "")
    if not expected or not secrets.compare_digest(sent, expected):
        raise HTTPException(400, "Sesi formulir sudah kedaluwarsa. Muat ulang halaman, lalu coba lagi.")


# ---------------------------------------------------------------- login dan peran
def current_user(request: Request, conn=Depends(get_db)):
    """Pengguna yang sedang masuk, atau None. Disimpan juga di request.state untuk templat."""
    uid = request.session.get("user_id")
    row = conn.execute(
        "SELECT id, username, display_name, role FROM app_user WHERE id=?", (uid,)).fetchone() if uid else None
    request.state.user = dict(row) if row else None
    return request.state.user


def login_required(user=Depends(current_user)):
    if user is None:
        raise LoginRequired()
    return user


def require_role(*roles):
    def check(user=Depends(login_required)):
        if user["role"] not in roles:
            raise HTTPException(403, "Akun Anda tidak punya izin untuk tindakan ini. Hubungi administrator.")
        return user
    return check


# ---------------------------------------------------------------- fungsi bantu kecil
def int_arg(args, name: str, default: int = 1, minimum: int = 1, maximum: int = 100_000) -> int:
    """Baca angka dari query string tanpa error: nilai salah memakai default, nilai ekstrem dibatasi."""
    try:
        value = int(args.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, value))


def period_or_404(period_id: int, conn=Depends(get_db)) -> dict:
    from .services import periods
    period = periods.get_period(conn, period_id)
    if period is None:
        raise HTTPException(404, "Periode seleksi tidak ditemukan.")
    return period


