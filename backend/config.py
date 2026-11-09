"""Pengaturan aplikasi. Semua bisa diganti lewat environment variable."""
import os
from pathlib import Path

# Folder data (database SQLite). Relatif terhadap folder tempat perintah dijalankan.
DATA_DIR = Path(os.environ.get("SPK_DATA_DIR", "data"))
DB_PATH = Path(os.environ.get("SPK_DB", DATA_DIR / "spk.db"))

# Kunci penanda cookie sesi. WAJIB diganti bila dipakai di luar komputer sendiri.
SECRET_KEY = os.environ.get("SPK_SECRET_KEY", "dev-only-ganti-bila-dipakai-di-luar-lokal")

# Akun awal (dibuat otomatis bila belum ada). Hanya untuk development lokal.
DEFAULT_USERS = [
    {"username": "admin", "display_name": "Administrator Dinas", "password": "admin123", "role": "admin"},
    {"username": "penilai", "display_name": "Tim Penilai", "password": "penilai123", "role": "penilai"},
]

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
