"""Matriks perbandingan berpasangan CONTOH (hanya untuk demo/pengujian).

Di sistem sebenarnya, nilai ini diisi tim penilai Dinas. Urutan: C1..C7.
Hasil: bobot kira-kira C1 0,24; C2 0,24; C3 0,13; C4 0,06; C5 0,07; C6 0,13;
C7 0,13 dengan CR ~ 0,002 (konsisten).
"""
from fractions import Fraction

# segitiga atas, indeks 0-based (i, j) dengan i < j
DEFAULT_PAIRWISE_UPPER = {
    (0, 1): 1, (0, 2): 2, (0, 3): 4, (0, 4): 3, (0, 5): 2, (0, 6): 2,
    (1, 2): 2, (1, 3): 4, (1, 4): 3, (1, 5): 2, (1, 6): 2,
    (2, 3): 2, (2, 4): 2, (2, 5): 1, (2, 6): 1,
    (3, 4): 1, (3, 5): Fraction(1, 2), (3, 6): Fraction(1, 2),
    (4, 5): Fraction(1, 2), (4, 6): Fraction(1, 2),
    (5, 6): 1,
}


def default_upper_floats() -> dict:
    return {k: float(v) for k, v in DEFAULT_PAIRWISE_UPPER.items()}
