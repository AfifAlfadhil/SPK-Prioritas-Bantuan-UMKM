import numpy as np
import pytest

from backend.mcdm import ahp

N_CRITERIA = 7

# Matriks contoh 7 kriteria (segitiga atas), dipakai untuk uji; bukan bobot resmi Dinas.
SAMPLE_UPPER = {
    (0, 1): 1, (0, 2): 2, (0, 3): 4, (0, 4): 3, (0, 5): 2, (0, 6): 2,
    (1, 2): 2, (1, 3): 4, (1, 4): 3, (1, 5): 2, (1, 6): 2,
    (2, 3): 2, (2, 4): 2, (2, 5): 1, (2, 6): 1,
    (3, 4): 1, (3, 5): 1 / 2, (3, 6): 1 / 2,
    (4, 5): 1 / 2, (4, 6): 1 / 2,
    (5, 6): 1,
}


def test_reciprocal_filled_automatically():
    A = ahp.matrix_from_upper(3, {(0, 1): 3, (0, 2): 5, (1, 2): 2})
    assert A[1, 0] == pytest.approx(1 / 3)
    assert A[2, 0] == pytest.approx(1 / 5)
    assert np.allclose(A * A.T, 1)


def test_perfectly_consistent_matrix_recovers_weights():
    w = np.array([0.5, 0.3, 0.2])
    A = np.outer(w, 1 / w)
    # nilai di luar skala Saaty tidak masalah selama masih dalam 1/9..9
    res = ahp.compute(A)
    assert np.allclose(res["weights"], w, atol=1e-9)
    assert res["lambda_max"] == pytest.approx(3.0, abs=1e-9)
    assert res["cr"] == pytest.approx(0.0, abs=1e-9)
    assert res["consistent"]


def test_weights_sum_to_one():
    res = ahp.compute(ahp.matrix_from_upper(N_CRITERIA, SAMPLE_UPPER))
    assert res["weights"].sum() == pytest.approx(1.0)


def test_default_matrix_is_consistent():
    res = ahp.compute(ahp.matrix_from_upper(N_CRITERIA, SAMPLE_UPPER))
    assert res["consistent"] and res["cr"] <= 0.1


def test_inconsistent_matrix_flagged():
    # A>B (9), B>C (9), tetapi C>A (9): sangat tidak konsisten
    A = ahp.matrix_from_upper(3, {(0, 1): 9, (1, 2): 9, (0, 2): 1 / 9})
    res = ahp.compute(A)
    assert res["cr"] > 0.1
    assert not res["consistent"]


def test_known_textbook_case_lambda_max():
    # Contoh 3x3 yang dihitung manual: kolom dijumlah -> normalisasi -> rata-rata baris
    A = np.array([[1, 2, 4], [1 / 2, 1, 2], [1 / 4, 1 / 2, 1]])  # konsisten sempurna
    res = ahp.compute(A)
    assert res["weights"] == pytest.approx([4 / 7, 2 / 7, 1 / 7])


@pytest.mark.parametrize("bad", [
    np.array([[1, 2], [2, 1]]),          # tidak resiprokal
    np.array([[1, 10], [0.1, 1]]),       # di luar skala 1..9
    np.array([[2, 1], [1, 2]]),          # diagonal bukan 1
    np.ones((2, 3)),                     # tidak persegi
])
def test_invalid_matrices_rejected(bad):
    with pytest.raises(ahp.AhpError):
        ahp.compute(bad)


def test_upper_value_outside_saaty_rejected():
    with pytest.raises(ahp.AhpError):
        ahp.matrix_from_upper(3, {(0, 1): 12})
