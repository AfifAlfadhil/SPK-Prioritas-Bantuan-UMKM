"""Perhitungan di atas database: AHP -> TOPSIS.

Matematikanya ada di paket `mcdm`; berkas ini hanya mengambil data periode dari SQLite,
memanggil `mcdm`, lalu menyimpan hasilnya.
"""
import numpy as np
from ..mcdm import ahp
from ..mcdm.topsis import topsis

from ..criteria import N_CRITERIA, TYPES
from . import periods


class CalculationError(RuntimeError):
    """Akar semua kesalahan perhitungan; pesannya siap ditampilkan ke pengguna."""


class NoWeightsError(CalculationError):
    pass


class InconsistentWeightsError(CalculationError):
    pass


class NoAlternativesError(CalculationError):
    pass


def run_ahp(conn, period_id: int, matrix) -> dict:
    result = ahp.compute(matrix)
    A = np.asarray(matrix, dtype=float)
    conn.execute("DELETE FROM pairwise_comparison WHERE period_id=?", (period_id,))
    conn.executemany(
        "INSERT INTO pairwise_comparison (period_id, i, j, value) VALUES (?,?,?,?)",
        [(period_id, i, j, float(A[i, j])) for i in range(N_CRITERIA) for j in range(i + 1, N_CRITERIA)],
    )
    w = result["weights"]
    conn.execute("DELETE FROM ahp_result WHERE period_id=?", (period_id,))
    conn.execute(
        "INSERT INTO ahp_result (period_id, w1, w2, w3, w4, w5, w6, w7, lambda_max, ci, cr, consistent) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (period_id, *[float(x) for x in w], result["lambda_max"], result["ci"], result["cr"],
         int(result["consistent"])),
    )
    conn.commit()
    result["ranking_cleared"] = periods.clear_ranking(conn, period_id)  # bobot baru -> peringkat lama kedaluwarsa
    return result


def get_weights(conn, period_id: int) -> np.ndarray:
    row = conn.execute("SELECT * FROM ahp_result WHERE period_id=?", (period_id,)).fetchone()
    if row is None:
        raise NoWeightsError("bobot AHP belum dihitung untuk periode ini")
    if not row["consistent"]:
        raise InconsistentWeightsError(
            f"CR = {row['cr']:.4f} > 0,1: perbaiki perbandingan berpasangan sebelum bobot dipakai"
        )
    return np.array([row[f"w{k}"] for k in range(1, N_CRITERIA + 1)])


def load_alternatives(conn, period_id: int):
    rows = conn.execute(
        "SELECT s.umkm_id, u.nama_usaha, s.c1, s.c2, s.c3, s.c4, s.c5, s.c6, s.c7 "
        "FROM umkm_score s JOIN umkm u ON u.id = s.umkm_id "
        "WHERE s.period_id=? AND s.status='lolos' AND s.selected=1 ORDER BY s.umkm_id",
        (period_id,),
    ).fetchall()
    if not rows:
        raise NoAlternativesError("tidak ada alternatif yang dipilih untuk dihitung")
    ids = [r["umkm_id"] for r in rows]
    X = np.array([[r[f"c{k}"] for k in range(1, N_CRITERIA + 1)] for r in rows], dtype=float)
    return ids, X


def run_topsis(conn, period_id: int) -> list[dict]:
    w = get_weights(conn, period_id)
    ids, X = load_alternatives(conn, period_id)
    res = topsis(X, w, TYPES, ids)
    conn.execute("DELETE FROM topsis_result WHERE period_id=?", (period_id,))
    conn.executemany(
        "INSERT INTO topsis_result (period_id, umkm_id, d_plus, d_minus, v, rank) VALUES (?,?,?,?,?,?)",
        [(period_id, int(ids[k]), float(res["d_plus"][k]), float(res["d_minus"][k]),
          float(res["preference"][k]), int(res["rank"][k])) for k in range(len(ids))],
    )
    conn.execute("UPDATE selection_period SET status='dihitung' WHERE id=?", (period_id,))
    conn.commit()
    return get_ranking(conn, period_id)


def get_ranking(conn, period_id: int, limit: int | None = None) -> list[dict]:
    sql = (
        "SELECT t.rank, t.umkm_id, u.source_id, u.nama_usaha, u.jenis_usaha, u.kecamatan, "
        "t.v, t.d_plus, t.d_minus FROM topsis_result t JOIN umkm u ON u.id = t.umkm_id "
        "WHERE t.period_id=? ORDER BY t.rank"
    )
    params = [period_id]
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_ahp_result(conn, period_id: int):
    row = conn.execute("SELECT * FROM ahp_result WHERE period_id=?", (period_id,)).fetchone()
    if row is None:
        return None
    return {
        "weights": [row[f"w{k}"] for k in range(1, N_CRITERIA + 1)],
        "lambda_max": row["lambda_max"], "ci": row["ci"], "cr": row["cr"],
        "ri": ahp.RI[N_CRITERIA], "consistent": bool(row["consistent"]),
    }


def get_pairwise_upper(conn, period_id: int) -> dict:
    rows = conn.execute(
        "SELECT i, j, value FROM pairwise_comparison WHERE period_id=? AND i<j", (period_id,)
    ).fetchall()
    return {(r["i"], r["j"]): r["value"] for r in rows}


