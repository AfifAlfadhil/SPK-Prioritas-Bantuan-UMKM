"""Format angka, tanggal, dan skala Saaty (dipakai web dan laporan)."""
import math
from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))
BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def rupiah(v) -> str:
    if v is None:
        return "-"
    return "Rp " + f"{int(v):,}".replace(",", ".")


def angka(v, digits: int = 2) -> str:
    """Angka berformat Indonesia: pemisah ribuan titik, desimal koma."""
    if v is None:
        return "-"
    s = f"{float(v):,.{digits}f}"
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def persen(v, digits: int = 1) -> str:
    return "-" if v is None else angka(float(v) * 100, digits) + "%"


def tanggal(iso) -> str:
    if not iso:
        return "-"
    d = datetime.fromisoformat(iso)
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    d = d.astimezone(WIB)
    return f"{d.day} {BULAN[d.month - 1]} {d.year}, {d:%H.%M} WIB"


# ---- skala Saaty ----
SAATY_LABELS = ["9", "8", "7", "6", "5", "4", "3", "2", "1",
                "1/2", "1/3", "1/4", "1/5", "1/6", "1/7", "1/8", "1/9"]


def parse_saaty(text) -> float:
    """'3' -> 3.0, '1/3' -> 0.333. Hanya label skala Saaty yang diterima."""
    s = str(text).strip()
    if s not in SAATY_LABELS:
        raise ValueError(f"nilai bukan skala Saaty: {text!r}")
    if "/" in s:
        a, b = s.split("/")
        return int(a) / int(b)
    return float(s)


def saaty_label(value: float) -> str:
    """Label skala Saaty terdekat untuk nilai yang tersimpan."""
    return min(SAATY_LABELS, key=lambda lbl: abs(math.log(parse_saaty(lbl)) - math.log(value)))


def reciprocal_label(label: str) -> str:
    return label[2:] if label.startswith("1/") else ("1" if label == "1" else f"1/{label}")


def saaty_to_slider(label: str) -> int:
    """Konversi label Saaty ('9', '1', '1/3') ke nilai slider (-8..+8)."""
    try:
        return SAATY_LABELS.index(str(label).strip()) - 8
    except ValueError:
        return 0


def status_label(status: str) -> str:
    return {"draft": "Belum dihitung", "dihitung": "Sudah dihitung"}.get(status, status)
