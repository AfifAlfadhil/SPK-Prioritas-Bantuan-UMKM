"""Masuk dan keluar."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from .. import security
from ..dependencies import current_user, get_db, read_form
from ..templating import flash, render, url_for

router = APIRouter(include_in_schema=False)


@router.api_route("/login", methods=["GET", "POST"], name="auth.login")
def login(request: Request, form=Depends(read_form), conn=Depends(get_db), user=Depends(current_user)):
    nxt = form.get("next") or request.query_params.get("next", "")
    home = nxt if security.is_safe_next(nxt) else url_for(request, "dashboard.index")
    if user:
        return RedirectResponse(home, 303)
    error = None
    if request.method == "POST":
        found = security.authenticate(conn, str(form.get("username", "")), str(form.get("password", "")))
        if found:
            request.session.clear()                       # sesi baru setelah login
            request.session["user_id"] = found["id"]
            security.csrf_token(request.session)
            return RedirectResponse(home, 303)
        error = "Nama pengguna atau kata sandi salah."
    return render(request, "auth/login.html", error=error, next=nxt)


@router.post("/logout", name="auth.logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "Anda sudah keluar.", "info")
    return RedirectResponse(url_for(request, "auth.login"), 303)
