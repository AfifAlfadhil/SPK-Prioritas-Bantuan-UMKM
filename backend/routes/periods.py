"""Periode seleksi: daftar, buat, ringkasan, dan pemilihan UMKM yang ikut dihitung."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from ..dependencies import get_db, login_required, period_or_404, read_form, require_role
from ..services import calculation, periods
from ..templating import flash, render, url_for

router = APIRouter(prefix="/periode", include_in_schema=False)


@router.get("/", name="periods.index")
def index(request: Request, conn=Depends(get_db), user=Depends(login_required)):
    total_umkm = conn.execute("SELECT COUNT(*) FROM umkm").fetchone()[0]
    return render(request, "periods/list.html", periods=periods.list_periods(conn), total_umkm=total_umkm)


@router.post("/", name="periods.create")
def create(request: Request, form=Depends(read_form), conn=Depends(get_db), user=Depends(require_role("admin"))):
    name = str(form.get("nama", "")).strip()
    back = RedirectResponse(url_for(request, "periods.index"), 303)
    if not 3 <= len(name) <= 80:
        flash(request, "Nama periode harus 3 sampai 80 karakter.", "error")
        return back
    if conn.execute("SELECT COUNT(*) FROM umkm").fetchone()[0] == 0:
        flash(request, "Belum ada data UMKM di database. Hubungi pengelola database terlebih dahulu.", "error")
        return back
    period_id = periods.create_period(conn, name)
    flash(request, f"Periode {name} dibuat. Data UMKM saat ini sudah disalin ke periode ini.", "ok")
    return RedirectResponse(url_for(request, "periods.overview", period_id=period_id), 303)


@router.get("/{period_id}", name="periods.overview")
def overview(request: Request, period=Depends(period_or_404), conn=Depends(get_db), user=Depends(login_required)):
    pid = period["id"]
    summary = periods.eligibility_summary(conn, pid)
    ahp_res = calculation.get_ahp_result(conn, pid)
    ranked = conn.execute("SELECT COUNT(*) FROM topsis_result WHERE period_id=?", (pid,)).fetchone()[0]
    selected = conn.execute(
        "SELECT COUNT(*) FROM umkm_score WHERE period_id=? AND status='lolos' AND selected=1", (pid,)).fetchone()[0]
    reasons = [dict(r) for r in conn.execute(
        "SELECT reason, COUNT(*) AS n FROM umkm_score WHERE period_id=? AND status='gugur' "
        "GROUP BY reason ORDER BY n DESC", (pid,))]
    return render(request, "periods/overview.html", summary=summary, ahp=ahp_res, ranked=ranked,
                  selected=selected, reasons=reasons)


@router.api_route("/{period_id}/alternatif", methods=["GET", "POST"], name="periods.alternatives")
def alternatives(request: Request, form=Depends(read_form), period=Depends(period_or_404),
                 conn=Depends(get_db), user=Depends(login_required)):
    pid = period["id"]
    if request.method == "POST":
        ids = [i for i in form.getlist("pilih") if str(i).isdigit()]
        count = periods.set_selection(conn, pid, ids)
        flash(request, f"{count} UMKM akan dihitung. Hasil peringkat sebelumnya dihapus, jadi hitung ulang "
                       "di halaman Peringkat.", "ok" if count else "warn")
        return RedirectResponse(url_for(request, "periods.alternatives", period_id=pid), 303)
    candidates = periods.list_candidates(conn, pid)
    candidates.sort(key=lambda c: (c["status"] != "lolos", c["source_id"]))
    return render(request, "periods/alternatives.html", candidates=candidates)
