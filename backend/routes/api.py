"""API read-only untuk frontend dan integrasi backend."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from ..dependencies import get_db, login_required
from ..services import calculation, periods
from ..services import umkm_repository as repo

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/umkm")
def list_umkm(request: Request, conn=Depends(get_db), user=Depends(login_required)):
    args = request.query_params
    rows, total = repo.list_umkm(
        conn, q=args.get("q", "").strip(), kecamatan=args.get("kecamatan", ""),
        jenis=args.get("jenis", ""), page=1, per_page=1000,
    )
    return {"data": rows, "total": total, "source": "database"}


@router.get("/periode")
def list_periods(conn=Depends(get_db), user=Depends(login_required)):
    return {"data": periods.list_periods(conn), "source": "database"}


@router.get("/periode/{period_id}/hasil")
def ranking(period_id: int, conn=Depends(get_db), user=Depends(login_required)):
    period = periods.get_period(conn, period_id)
    if period is None:
        return JSONResponse({"detail": "Periode seleksi tidak ditemukan."}, status_code=404)
    return {
        "period": period,
        "ahp": calculation.get_ahp_result(conn, period_id),
        "ranking": calculation.get_ranking(conn, period_id),
        "source": "database",
    }
