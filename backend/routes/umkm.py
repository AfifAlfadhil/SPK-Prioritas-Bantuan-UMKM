"""Data UMKM read-only dari database aplikasi."""
from math import ceil

from fastapi import APIRouter, Depends, Request

from ..dependencies import get_db, int_arg, login_required
from ..services import umkm_repository as repo
from ..templating import render

router = APIRouter(prefix="/umkm", include_in_schema=False)
PER_PAGE = 20


@router.get("/", name="umkm.index")
def index(request: Request, conn=Depends(get_db), user=Depends(login_required)):
    args = request.query_params
    q, kecamatan, jenis = args.get("q", "").strip(), args.get("kecamatan", ""), args.get("jenis", "")
    page = int_arg(args, "hal", 1)
    rows, total = repo.list_umkm(conn, q=q, kecamatan=kecamatan, jenis=jenis, page=page, per_page=PER_PAGE)
    pages = max(1, ceil(total / PER_PAGE))
    return render(request, "umkm/list.html", rows=rows, total=total, page=min(page, pages), pages=pages,
                  q=q, kecamatan=kecamatan, jenis=jenis, facets=repo.facets(conn))
