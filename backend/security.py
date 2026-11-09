"""Kata sandi, akun awal, dan token CSRF. (Penjaga akses per halaman ada di dependencies.py.)"""
import base64
import hashlib
import hmac
import os
import secrets
from urllib.parse import urlparse

from . import database as db

ROLE_LABELS = {"admin": "Administrator", "penilai": "Tim penilai"}
_N, _R, _P = 2 ** 14, 8, 1          # parameter scrypt


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(key).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, key_b64 = stored.split("$")
        salt, expected = base64.b64decode(salt_b64), base64.b64decode(key_b64)
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    key = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P)
    return hmac.compare_digest(key, expected)


def seed_users(conn, users) -> None:
    """Buat akun awal bila belum ada."""
    for u in users:
        if conn.execute("SELECT 1 FROM app_user WHERE username=?", (u["username"],)).fetchone():
            continue
        conn.execute(
            "INSERT INTO app_user (username, display_name, password_hash, role, created_at) VALUES (?,?,?,?,?)",
            (u["username"], u["display_name"], hash_password(u["password"]), u["role"], db.now()))
    conn.commit()


def authenticate(conn, username: str, password: str):
    row = conn.execute("SELECT * FROM app_user WHERE username=?", (username.strip(),)).fetchone()
    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def csrf_token(session) -> str:
    """Token CSRF per sesi; dibuat saat pertama diminta."""
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(24)
    return session["_csrf"]


def is_safe_next(target) -> bool:
    """Hanya alamat dalam situs ini yang boleh jadi tujuan setelah login (cegah open redirect)."""
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and not parsed.scheme and target.startswith("/") and not target.startswith("//")
