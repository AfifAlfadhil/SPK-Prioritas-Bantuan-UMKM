"""Jinja2: filter format, pesan kilat (flash), url_for bergaya Flask, dan fungsi render().

Template memanggil url_for('bagian.nama', ...) memakai nama rute yang diberikan pada
tiap dekorator rute (mis. name="ranking.show"). Parameter yang bukan bagian jalur
otomatis menjadi query string.
"""
from pathlib import Path
from urllib.parse import urlencode

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from . import formatting as fmt
from .criteria import CRITERIA
from .security import ROLE_LABELS, csrf_token

HERE = Path(__file__).resolve().parent
FRONTEND = HERE.parent / "frontend"
templates = Jinja2Templates(directory=FRONTEND / "templates")


# ---------------------------------------------------------------- url_for
def url_for(request: Request, endpoint: str, **values) -> str:
    if endpoint == "static":
        return "/static/" + str(values["filename"])
    path_keys = request.app.state.route_params[endpoint]
    path = request.app.url_path_for(endpoint, **{k: values.pop(k) for k in path_keys})
    query = {k: v for k, v in values.items() if v is not None and v != ""}
    return path + ("?" + urlencode(query) if query else "")


def register_routes(app, routers) -> None:
    """Catat nama rute dan parameter jalurnya, dipakai url_for()."""
    app.state.route_params = {r.name: set(r.param_convertors) for router in routers for r in router.routes}


# ---------------------------------------------------------------- flash
def flash(request: Request, message: str, category: str = "info") -> None:
    """Pesan satu kali tampil pada halaman berikutnya. Kategori: ok, info, warn, error."""
    request.session["flash"] = [*request.session.get("flash", []), {"text": message, "category": category}]


# ---------------------------------------------------------------- render
def _period_context(request: Request, period_id: int) -> dict:
    """Untuk semua halaman /periode/<id>/...: data periode + status langkah (dipakai _header.html)."""
    from .services import calculation, periods
    conn = getattr(request.state, "db", None)
    period = periods.get_period(conn, period_id) if conn else None
    if not period:
        return {}
    ahp_res = calculation.get_ahp_result(conn, period_id)
    ranked = conn.execute("SELECT COUNT(*) FROM topsis_result WHERE period_id=?", (period_id,)).fetchone()[0]
    selected = conn.execute(
        "SELECT COUNT(*) FROM umkm_score WHERE period_id=? AND status='lolos' AND selected=1", (period_id,)
    ).fetchone()[0]
    return {"period": period, "nav": {
        "has_weights": ahp_res is not None, "weights_ok": bool(ahp_res and ahp_res["consistent"]),
        "has_ranking": ranked > 0, "selected": selected}}


def _area(path: str) -> str:
    first = path.strip("/").split("/")[0]
    return {"": "dashboard", "umkm": "umkm", "periode": "periods"}.get(first, first)


def render(request: Request, template: str, status_code: int = 200, with_period: bool = True, **context):
    ctx = {
        "current_user": getattr(request.state, "user", None),
        "criteria": CRITERIA,
        "area": _area(request.url.path),
        "flashes": request.session.pop("flash", []),
        "query": dict(request.query_params),
    }
    period_id = request.path_params.get("period_id")
    if period_id and with_period:      # halaman error: koneksi DB sudah ditutup
        ctx.update(_period_context(request, int(period_id)))
    ctx.update(context)
    return templates.TemplateResponse(request, template, ctx, status_code=status_code)


@pass_context
def _jinja_url_for(ctx, endpoint, **values):
    return url_for(ctx["request"], endpoint, **values)


@pass_context
def _jinja_csrf_token(ctx):
    return csrf_token(ctx["request"].session)


templates.env.globals.update(url_for=_jinja_url_for, csrf_token=_jinja_csrf_token)
templates.env.filters.update(
    rupiah=fmt.rupiah, angka=fmt.angka, persen=fmt.persen, tanggal=fmt.tanggal,
    status_label=fmt.status_label, role_label=lambda r: ROLE_LABELS.get(r, r))
