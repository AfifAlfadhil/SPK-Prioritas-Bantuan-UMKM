"""Bobot kriteria: matriks perbandingan berpasangan AHP."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from ..mcdm import ahp

from .. import formatting as fmt
from ..criteria import CODES, CRITERIA, N_CRITERIA
from ..dependencies import get_db, login_required, period_or_404, read_form
from ..services import calculation, sample_matrix
from ..templating import flash, render, url_for

router = APIRouter(prefix="/periode", include_in_schema=False)


def _parse_form(form):
    """Baca 21 pilihan segitiga atas. Return (nilai, label_isian, daftar_kesalahan)."""
    upper, labels, errors = {}, {}, []
    for i in range(N_CRITERIA):
        for j in range(i + 1, N_CRITERIA):
            raw = str(form.get(f"a_{i}_{j}", ""))
            labels[(i, j)] = raw
            try:
                upper[(i, j)] = fmt.parse_saaty(raw)
            except ValueError:
                errors.append(f"Nilai {CODES[i]} dibanding {CODES[j]} harus dipilih dari skala 9 sampai 1/9.")
    return upper, labels, errors


@router.api_route("/{period_id}/bobot", methods=["GET", "POST"], name="weighting.edit")
def edit(request: Request, form=Depends(read_form), period=Depends(period_or_404),
         conn=Depends(get_db), user=Depends(login_required)):
    pid = period["id"]
    errors, labels = [], None

    if request.method == "POST":
        if form.get("aksi") == "contoh":
            upper, sample = sample_matrix.default_upper_floats(), True
        else:
            upper, labels, errors = _parse_form(form)
            sample = False
        if not errors:
            result = calculation.run_ahp(conn, pid, ahp.matrix_from_upper(N_CRITERIA, upper))
            note = " Peringkat lama dihapus karena bobot berubah." if result["ranking_cleared"] else ""
            prefix = "Matriks contoh dipakai. " if sample else ""
            if result["consistent"]:
                flash(request, f"{prefix}Bobot dihitung dan konsisten (CR {fmt.angka(result['cr'], 4)}).{note}", "ok")
            else:
                flash(request, f"{prefix}Bobot dihitung, tetapi tidak konsisten (CR {fmt.angka(result['cr'], 4)} "
                               f"lebih dari 0,1). Perbaiki perbandingan di bawah sebelum menghitung peringkat.{note}",
                      "warn")
            return RedirectResponse(url_for(request, "weighting.edit", period_id=pid), 303)

    result = calculation.get_ahp_result(conn, pid)
    saved = calculation.get_pairwise_upper(conn, pid)
    if labels is None:
        labels = {(i, j): (fmt.saaty_label(saved[(i, j)]) if saved else "1")
                  for i in range(N_CRITERIA) for j in range(i + 1, N_CRITERIA)}

    suspects = []                                  # petunjuk: pasangan yang paling menyimpang
    if result and not result["consistent"] and saved:
        matrix = ahp.matrix_from_upper(N_CRITERIA, saved)
        for s in ahp.inconsistent_pairs(matrix, result["weights"]):
            suspects.append({"pair": f"{CODES[s['i']]} dibanding {CODES[s['j']]}",
                             "given": fmt.saaty_label(s["given"]), "implied": fmt.saaty_label(s["implied"])})

    weight_rows = []
    if result:
        weight_rows = [{"code": c["code"], "name": c["name"], "type": c["type"], "weight": w}
                       for c, w in zip(CRITERIA, result["weights"])]
    return render(request, "weighting/form.html", errors=errors, labels=labels, result=result, suspects=suspects,
                  weight_rows=weight_rows, saaty_labels=fmt.SAATY_LABELS, n=N_CRITERIA,
                  reciprocal=fmt.reciprocal_label)
