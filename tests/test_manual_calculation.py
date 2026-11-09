"""Perhitungan manual (Python murni, tanpa numpy) mengikuti langkah-langkah di proposal.

Gunanya sebagai pembanding yang ditulis terpisah dari pustaka: bila keduanya sama,
rumus di pustaka sudah sesuai dengan langkah 1-11 pada proposal.
"""
import math

import pytest

from backend.mcdm import ahp, topsis

RI7 = 1.32


def manual_ahp(A):
    n = len(A)
    col_sum = [sum(A[i][j] for i in range(n)) for j in range(n)]                 # langkah 3: jumlah kolom
    norm = [[A[i][j] / col_sum[j] for j in range(n)] for i in range(n)]          # normalisasi
    w = [sum(norm[i]) / n for i in range(n)]                                     # rata-rata baris = bobot
    aw = [sum(A[i][j] * w[j] for j in range(n)) for i in range(n)]
    lam = sum(aw[i] / w[i] for i in range(n)) / n                                # lambda max
    ci = (lam - n) / (n - 1)
    return w, lam, ci, ci / RI7                                                  # langkah 4: CR


def manual_topsis(X, w, types):
    m, n = len(X), len(w)
    denom = [math.sqrt(sum(X[i][j] ** 2 for i in range(m))) for j in range(n)]   # langkah 6: normalisasi vektor
    V = [[X[i][j] / denom[j] * w[j] for j in range(n)] for i in range(m)]        # langkah 7: terbobot
    a_pos, a_neg = [], []
    for j in range(n):                                                           # langkah 8: solusi ideal
        col = [V[i][j] for i in range(m)]
        a_pos.append(max(col) if types[j] == "benefit" else min(col))
        a_neg.append(min(col) if types[j] == "benefit" else max(col))
    d_pos = [math.sqrt(sum((V[i][j] - a_pos[j]) ** 2 for j in range(n))) for i in range(m)]   # langkah 9
    d_neg = [math.sqrt(sum((V[i][j] - a_neg[j]) ** 2 for j in range(n))) for i in range(m)]
    pref = [d_neg[i] / (d_pos[i] + d_neg[i]) for i in range(m)]                  # langkah 10: nilai V
    order = sorted(range(m), key=lambda i: (-pref[i], i))                        # langkah 11: urutan
    rank = [0] * m
    for position, i in enumerate(order, start=1):
        rank[i] = position
    return pref, rank


# Contoh tetap: 7 kriteria, 6 UMKM (angka rekaan, hanya untuk uji)
UPPER = {(0, 1): 1, (0, 2): 2, (0, 3): 4, (0, 4): 3, (0, 5): 2, (0, 6): 2, (1, 2): 2, (1, 3): 4, (1, 4): 3,
         (1, 5): 2, (1, 6): 2, (2, 3): 2, (2, 4): 2, (2, 5): 1, (2, 6): 1, (3, 4): 1, (3, 5): 1 / 2,
         (3, 6): 1 / 2, (4, 5): 1 / 2, (4, 6): 1 / 2, (5, 6): 1}
TYPES = ["cost", "cost", "benefit", "benefit", "benefit", "cost", "cost"]
X = [
    [25_000_000, 8_000_000, 3, 24, 2, 0, 0],
    [60_000_000, 20_000_000, 6, 60, 3, 1, 1],
    [10_000_000, 3_000_000, 2, 12, 0, 0, 0],
    [90_000_000, 45_000_000, 9, 120, 4, 2, 2],
    [15_000_000, 5_000_000, 4, 8, 1, 0, 1],
    [40_000_000, 12_000_000, 5, 36, 2, 1, 0],
]


def test_ahp_matches_manual_steps():
    A = ahp.matrix_from_upper(7, UPPER)
    res = ahp.compute(A)
    w, lam, ci, cr = manual_ahp(A.tolist())
    assert list(res["weights"]) == pytest.approx(w, abs=1e-12)
    assert (res["lambda_max"], res["ci"], res["cr"]) == pytest.approx((lam, ci, cr), abs=1e-12)
    assert sum(w) == pytest.approx(1.0)


def test_topsis_matches_manual_steps_and_ranking():
    w, *_ = manual_ahp(ahp.matrix_from_upper(7, UPPER).tolist())
    pref, rank = manual_topsis(X, w, TYPES)
    res = topsis.topsis(X, w, TYPES, ids=list(range(len(X))))
    assert list(res["preference"]) == pytest.approx(pref, abs=1e-12)
    assert [int(r) for r in res["rank"]] == rank
    assert all(0 <= p <= 1 for p in pref)


def test_cost_and_benefit_directions_make_sense():
    """UMKM kecil dan belum pernah dibantu (modal rendah, bantuan 0) harus unggul atas yang besar."""
    w, *_ = manual_ahp(ahp.matrix_from_upper(7, UPPER).tolist())
    _, rank = manual_topsis(X, w, TYPES)
    assert rank[2] < rank[3]      # UMKM #3 (modal 10 jt, bantuan 0) di atas UMKM #4 (modal 90 jt, bantuan 2)


def test_inconsistency_hint_points_at_the_broken_pair_on_7_criteria():
    import numpy as np
    w = np.array([9, 6, 4, 3, 2, 1.5, 1.0])
    M = np.outer(w, 1 / w)
    M[0, 6] = M[6, 0] = 1.0                    # satu penilaian dirusak (seharusnya 9)
    res = ahp.compute(M)
    top = ahp.inconsistent_pairs(M, res["weights"], top=1)[0]
    assert (top["i"], top["j"]) == (0, 6)
    assert top["implied"] > top["given"]
