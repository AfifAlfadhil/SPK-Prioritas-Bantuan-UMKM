"""TOPSIS: pemeringkatan alternatif memakai bobot AHP.

Penanganan edge case:
- kolom bernilai nol semua: pembagi dianggap 1, kolom ternormalisasi = 0
- D+ + D- = 0 (alternatif berimpit dengan solusi ideal): V = 1
- nilai V sama: urut berdasarkan id alternatif (deterministik)
"""
import numpy as np


def rank_from_preference(pref, ids=None) -> np.ndarray:
    pref = np.asarray(pref, dtype=float)
    m = len(pref)
    ids = np.arange(m) if ids is None else np.asarray(ids)
    # dibulatkan agar selisih floating point tidak memengaruhi urutan
    order = np.lexsort((ids, -np.round(pref, 12)))
    ranks = np.empty(m, dtype=int)
    ranks[order] = np.arange(1, m + 1)
    return ranks


def topsis(X, weights, types, ids=None) -> dict:
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or X.shape[0] == 0:
        raise ValueError("matriks keputusan kosong atau bukan 2 dimensi")
    m, n = X.shape
    w = np.asarray(weights, dtype=float)
    if w.shape != (n,):
        raise ValueError(f"jumlah bobot ({w.size}) tidak sama dengan jumlah kriteria ({n})")
    if len(types) != n or any(t not in ("benefit", "cost") for t in types):
        raise ValueError("types harus 'benefit' atau 'cost' untuk tiap kriteria")
    if np.any(w < 0) or abs(w.sum() - 1.0) > 1e-6:
        raise ValueError("bobot harus non-negatif dan berjumlah 1")

    denom = np.sqrt((X ** 2).sum(axis=0))
    R = X / np.where(denom == 0, 1.0, denom)  # normalisasi vektor
    V = R * w                                 # matriks terbobot

    benefit = np.array([t == "benefit" for t in types])
    a_pos = np.where(benefit, V.max(axis=0), V.min(axis=0))
    a_neg = np.where(benefit, V.min(axis=0), V.max(axis=0))

    d_pos = np.sqrt(((V - a_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((V - a_neg) ** 2).sum(axis=1))
    total = d_pos + d_neg
    pref = np.where(total > 0, d_neg / np.where(total > 0, total, 1.0), 1.0)

    return {
        "d_plus": d_pos,
        "d_minus": d_neg,
        "preference": pref,
        "rank": rank_from_preference(pref, ids),
    }
