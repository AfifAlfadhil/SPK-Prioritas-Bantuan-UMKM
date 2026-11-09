"""Peringkat TOPSIS: hitung, tampilkan tabel dan grafik."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from ..dependencies import get_db, login_required, period_or_404
from ..services import calculation
from ..templating import flash, render, url_for

router = APIRouter(prefix="/periode", include_in_schema=False)


@router.get("/{period_id}/peringkat", name="ranking.show")
def show(request: Request, period=Depends(period_or_404), conn=Depends(get_db), user=Depends(login_required)):
    pid = period["id"]
    args = request.query_params
    all_rows = calculation.get_ranking(conn, pid)

    q = args.get("q", "").strip().lower()
    kecamatan, jenis = args.get("kecamatan", ""), args.get("jenis", "")
    rows = [r for r in all_rows
            if (not q or q in r["nama_usaha"].lower() or q in r["source_id"].lower())
            and (not kecamatan or r["kecamatan"] == kecamatan)
            and (not jenis or r["jenis_usaha"] == jenis)]
    show_all = args.get("tampil") == "semua"
    return render(
        request, "ranking/show.html", ahp=calculation.get_ahp_result(conn, pid),
        rows=rows if show_all else rows[:25], matched=len(rows), total=len(all_rows), show_all=show_all,
        q=args.get("q", ""), kecamatan=kecamatan, jenis=jenis,
        kecamatan_options=sorted({r["kecamatan"] for r in all_rows if r["kecamatan"]}),
        jenis_options=sorted({r["jenis_usaha"] for r in all_rows if r["jenis_usaha"]}))


@router.post("/{period_id}/peringkat/hitung", name="ranking.compute")
def compute(request: Request, period=Depends(period_or_404), conn=Depends(get_db),
            user=Depends(login_required)):
    pid = period["id"]
    try:
        rows = calculation.run_topsis(conn, pid)
        flash(request, f"Peringkat selesai dihitung untuk {len(rows)} UMKM.", "ok")
    except calculation.NoWeightsError:
        flash(request, "Bobot AHP belum dihitung. Isi perbandingan kriteria di halaman Bobot AHP dulu.", "error")
    except calculation.InconsistentWeightsError as exc:
        flash(request, str(exc) + ".", "error")
    except calculation.NoAlternativesError as exc:
        flash(request, f"Peringkat tidak bisa dihitung: {exc}.", "error")
    return RedirectResponse(url_for(request, "ranking.show", period_id=pid), 303)
