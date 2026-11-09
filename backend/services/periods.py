"""Periode seleksi: salinan data UMKM, syarat awal, dan pilihan UMKM yang ikut dihitung.

Saat periode dibuat, nilai kriteria semua UMKM DISALIN ke tabel umkm_score. Jadi
mengubah data UMKM sesudahnya tidak mengubah arsip periode yang sudah ada.
"""
from .. import database as db
from ..criteria import FIELDS, evaluate_eligibility


def create_period(conn, name: str) -> int:
    cur = conn.execute(
        "INSERT INTO selection_period (name, status, created_at) VALUES (?, 'draft', ?)", (name, db.now()))
    period_id = cur.lastrowid
    for row in conn.execute("SELECT * FROM umkm ORDER BY id").fetchall():
        umkm = dict(row)
        ok, reason = evaluate_eligibility(umkm)
        conn.execute(
            "INSERT INTO umkm_score (umkm_id, period_id, c1, c2, c3, c4, c5, c6, c7, status, reason) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (umkm["id"], period_id, *[umkm[f] for f in FIELDS], "lolos" if ok else "gugur", reason or None),
        )
    conn.commit()
    return period_id


def get_period(conn, period_id: int):
    row = conn.execute("SELECT * FROM selection_period WHERE id=?", (period_id,)).fetchone()
    return dict(row) if row else None


def list_periods(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT p.*, "
        "(SELECT COUNT(*) FROM umkm_score s WHERE s.period_id=p.id) AS total, "
        "(SELECT COUNT(*) FROM umkm_score s WHERE s.period_id=p.id AND s.status='lolos') AS lolos, "
        "(SELECT COUNT(*) FROM topsis_result t WHERE t.period_id=p.id) AS ranked "
        "FROM selection_period p ORDER BY p.id DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def eligibility_summary(conn, period_id: int) -> dict:
    rows = conn.execute(
        "SELECT status, COUNT(*) AS n FROM umkm_score WHERE period_id=? GROUP BY status", (period_id,)
    ).fetchall()
    out = {"lolos": 0, "gugur": 0}
    out.update({r["status"]: r["n"] for r in rows})
    return out


def list_candidates(conn, period_id: int) -> list[dict]:
    """Semua UMKM pada periode (lolos dan gugur) beserta nilai kriterianya."""
    rows = conn.execute(
        "SELECT s.umkm_id, s.status, s.reason, s.selected, s.c1, s.c2, s.c3, s.c4, s.c5, s.c6, s.c7, "
        "u.source_id, u.nama_usaha, u.jenis_usaha, u.kecamatan "
        "FROM umkm_score s JOIN umkm u ON u.id = s.umkm_id WHERE s.period_id=? ORDER BY s.umkm_id",
        (period_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def set_selection(conn, period_id: int, selected_ids) -> int:
    """Tandai UMKM lolos yang ikut dihitung. UMKM gugur tidak pernah terpilih.

    Peringkat lama dihapus karena sudah tidak sesuai. Return jumlah UMKM terpilih.
    """
    selected_ids = {int(x) for x in selected_ids}
    conn.execute("UPDATE umkm_score SET selected=0 WHERE period_id=?", (period_id,))
    conn.executemany(
        "UPDATE umkm_score SET selected=1 WHERE period_id=? AND umkm_id=? AND status='lolos'",
        [(period_id, i) for i in selected_ids],
    )
    conn.commit()
    clear_ranking(conn, period_id)
    return conn.execute(
        "SELECT COUNT(*) FROM umkm_score WHERE period_id=? AND selected=1 AND status='lolos'", (period_id,)
    ).fetchone()[0]


def clear_ranking(conn, period_id: int) -> bool:
    """Hapus peringkat periode (bobot atau pilihan UMKM berubah). True bila ada yang dihapus."""
    n = conn.execute("DELETE FROM topsis_result WHERE period_id=?", (period_id,)).rowcount
    conn.execute("UPDATE selection_period SET status='draft' WHERE id=?", (period_id,))
    conn.commit()
    return n > 0
