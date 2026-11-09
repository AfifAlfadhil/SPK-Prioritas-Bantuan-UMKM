"""AHP: bobot kriteria dari matriks perbandingan berpasangan (skala Saaty 1-9).

Pendekatan sesuai dokumen: normalisasi kolom, bobot = rata-rata baris,
lalu lambda_max, CI, CR. Bobot sah bila CR <= 0,1.
"""
import numpy as np

# Random Index (Saaty) untuk n = 1..10
RI = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
CR_THRESHOLD = 0.1
SAATY_MIN, SAATY_MAX = 1 / 9, 9.0


class AhpError(ValueError):
    pass


def matrix_from_upper(n: int, upper: dict) -> np.ndarray:
    """Bangun matriks dari segitiga atas {(i, j): nilai}, i < j (0-indexed).

    Nilai kebalikan di segitiga bawah terisi otomatis.
    """
    A = np.ones((n, n))
    for (i, j), v in upper.items():
        if not (0 <= i < j < n):
            raise AhpError(f"indeks tidak valid: ({i}, {j})")
        if not (SAATY_MIN - 1e-9 <= v <= SAATY_MAX + 1e-9):
            raise AhpError(f"nilai di luar skala Saaty 1/9..9: {v}")
        A[i, j] = v
        A[j, i] = 1.0 / v
    return A


def validate_matrix(A) -> np.ndarray:
    A = np.asarray(A, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise AhpError("matriks harus persegi")
    if A.shape[0] not in RI:
        raise AhpError(f"ukuran matriks {A.shape[0]} tidak didukung (RI tersedia untuk 1-10)")
    if np.any(A <= 0) or not np.allclose(np.diag(A), 1.0):
        raise AhpError("elemen harus positif dan diagonal bernilai 1")
    if np.any(A < SAATY_MIN - 1e-9) or np.any(A > SAATY_MAX + 1e-9):
        raise AhpError("ada nilai di luar skala Saaty 1/9..9")
    if not np.allclose(A * A.T, 1.0, atol=1e-6):
        raise AhpError("matriks harus resiprokal (a_ij * a_ji = 1)")
    return A


def compute(A) -> dict:
    """Hitung bobot, lambda_max, CI, CR dan status konsistensi."""
    A = validate_matrix(A)
    n = A.shape[0]
    normalized = A / A.sum(axis=0)
    w = normalized.mean(axis=1)
    lam = float(np.mean((A @ w) / w))
    ci = max((lam - n) / (n - 1), 0.0) if n > 1 else 0.0
    ri = RI[n]
    cr = ci / ri if ri > 0 else 0.0
    return {
        "weights": w,
        "lambda_max": lam,
        "ci": float(ci),
        "ri": ri,
        "cr": float(cr),
        "consistent": bool(cr <= CR_THRESHOLD + 1e-12),
    }


def inconsistent_pairs(A, weights, top: int = 3) -> list[dict]:
    """Pasangan kriteria yang paling menyimpang dari bobot turunannya.

    Membantu memperbaiki matriks dengan CR > 0,1: bandingkan nilai yang diisi
    (a_ij) dengan nilai yang tersirat dari bobot (w_i / w_j).
    """
    A = np.asarray(A, dtype=float)
    w = np.asarray(weights, dtype=float)
    n = len(w)
    rows = []
    for i in range(n):
        for j in range(i + 1, n):
            implied = float(w[i] / w[j])
            rows.append({"i": i, "j": j, "given": float(A[i, j]), "implied": implied,
                         "deviation": float(abs(np.log(A[i, j] / implied)))})
    rows.sort(key=lambda r: r["deviation"], reverse=True)
    return rows[:top]
