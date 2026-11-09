"""Satu pintu masuk proyek.

    python run.py                 jalankan aplikasi web (http://127.0.0.1:8000)
    python run.py initdb          buat database, akun awal, dan data simulasi UMKM
    python run.py compute 1       AHP (matriks contoh) + TOPSIS untuk periode 1
    python run.py --help

Struktur proyek dipisah menjadi:
  backend/        aplikasi FastAPI dan logika AHP-TOPSIS
  frontend/       template HTML dan aset tampilan
"""
import argparse
from pathlib import Path
import sys

from backend import config, security
from backend import database as db
from backend.criteria import CODES, N_CRITERIA
from backend.mcdm import ahp
from backend.services import calculation, periods, sample_matrix
from backend.services.sample_umkm import seed_sample_umkm


def open_db(path=None):
    conn = db.connect(path)
    db.init_db(conn)
    security.seed_users(conn, config.DEFAULT_USERS)
    seed_sample_umkm(conn)
    return conn


def print_ranking(rows, limit):
    print(f"{'No':>3}  {'ID':<10} {'Nama usaha':<28} {'Kecamatan':<13} {'V':>7}")
    for r in rows[:limit]:
        print(f"{r['rank']:>3}  {r['source_id']:<10} {r['nama_usaha'][:27]:<28} {r['kecamatan'] or '-':<13} {r['v']:>7.4f}")


def compute(conn, period_id, top=10):
    matrix = ahp.matrix_from_upper(N_CRITERIA, sample_matrix.default_upper_floats())
    res = calculation.run_ahp(conn, period_id, matrix)
    print("Bobot AHP: " + ", ".join(f"{c}={w:.3f}" for c, w in zip(CODES, res["weights"])))
    print(f"lambda_max={res['lambda_max']:.4f}  CI={res['ci']:.4f}  CR={res['cr']:.4f}  konsisten={res['consistent']}")
    rows = calculation.run_topsis(conn, period_id)
    print(f"\n{len(rows)} UMKM diperingkat. {top} teratas:")
    print_ranking(rows, top)


def cmd_serve(args):
    import uvicorn
    from backend.main import create_app
    print(f"Aplikasi web: http://127.0.0.1:{args.port}   akun: admin/admin123 atau penilai/penilai123")
    app = create_app(db_path=args.db)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


def main(argv=None):
    p = argparse.ArgumentParser(prog="run.py", description="SPK prioritas bantuan UMKM (AHP + TOPSIS)")
    p.add_argument("--db", default=None, help="berkas SQLite (default data/spk.db)")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("serve", help="jalankan web (perintah bawaan)")
    s.add_argument("--port", type=int, default=8000)
    s.set_defaults(fn=cmd_serve)

    sub.add_parser("initdb", help="buat database, akun awal, dan data simulasi UMKM").set_defaults(
        fn=lambda a: print("Database siap:", open_db(a.db) and (a.db or config.DB_PATH)))

    c = sub.add_parser("compute", help="AHP (matriks contoh) + TOPSIS untuk satu periode")
    c.add_argument("period", type=int)
    c.set_defaults(fn=lambda a: compute(open_db(a.db), a.period))

    args = p.parse_args(argv)
    if args.cmd is None:
        args = p.parse_args([*(argv or sys.argv[1:]), "serve"])
    args.fn(args)


if __name__ == "__main__":
    main()
