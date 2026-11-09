"""Beranda."""
from fastapi import APIRouter, Depends, Request

from ..dependencies import get_db, login_required
from ..services import periods
from ..templating import render

router = APIRouter(include_in_schema=False)


@router.get("/", name="dashboard.index")
def index(request: Request, conn=Depends(get_db), user=Depends(login_required)):
    total = conn.execute("SELECT COUNT(*) FROM umkm").fetchone()[0]
    return render(request, "dashboard/index.html", total=total,
                  periods=periods.list_periods(conn)[:5])
