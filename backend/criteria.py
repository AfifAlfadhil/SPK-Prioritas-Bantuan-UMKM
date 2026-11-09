"""Aturan data sesuai proposal: kriteria C1-C7, validasi nilai, dan syarat kelayakan awal."""

CRITERIA = [
    # "min" pada C4 sengaja 0: usaha < 6 bulan tetap valid sebagai data,
    # tetapi digugurkan oleh aturan kelayakan (lihat evaluate_eligibility di bawah).
    {"code": "C1", "name": "Modal usaha", "type": "cost", "min": 0, "max": 1_000_000_000, "field": "modal_usaha"},
    {"code": "C2", "name": "Omzet bulanan", "type": "cost", "min": 0, "max": 166_000_000, "field": "omzet_bulanan"},
    {"code": "C3", "name": "Jumlah tenaga kerja", "type": "benefit", "min": 1, "max": 9, "field": "jumlah_tenaga_kerja"},
    {"code": "C4", "name": "Lama usaha (bulan)", "type": "benefit", "min": 0, "max": 1200, "field": "lama_usaha_bulan"},
    {"code": "C5", "name": "Tingkat digitalisasi", "type": "benefit", "min": 0, "max": 4, "field": "tingkat_digitalisasi"},
    {"code": "C6", "name": "Akses permodalan", "type": "cost", "min": 0, "max": 20, "field": "akses_permodalan"},
    {"code": "C7", "name": "Riwayat bantuan", "type": "cost", "min": 0, "max": 20, "field": "riwayat_bantuan"},
]

CODES = [c["code"] for c in CRITERIA]
FIELDS = [c["field"] for c in CRITERIA]
TYPES = [c["type"] for c in CRITERIA]
N_CRITERIA = len(CRITERIA)

TEXT_FIELDS = ["nama_usaha", "pemilik", "jenis_usaha", "kecamatan", "kelurahan", "nib"]
MIN_BUSINESS_AGE_MONTHS = 6


def validate_record(rec: dict) -> list[str]:
    """Kembalikan daftar alasan penolakan (kosong = valid).

    Hanya memeriksa kualitas data (kosong, tipe, rentang). Kelayakan bisnis
    (NIB, lama usaha >= 6 bulan) diperiksa terpisah oleh evaluate_eligibility().
    """
    errors = []
    for key in ("source_id", "nama_usaha"):
        if not rec.get(key):
            errors.append(f"field kosong: {key}")
    for c in CRITERIA:
        v = rec.get(c["field"])
        if v is None:
            errors.append(f"field kosong: {c['field']}")
        elif not isinstance(v, int) or isinstance(v, bool):
            errors.append(f"tipe tidak valid: {c['field']}")
        elif v < c["min"] or v > c["max"]:
            errors.append(f"di luar rentang {c['code']} ({c['field']}={v}, rentang {c['min']}-{c['max']})")
    return errors


# ---- syarat kelayakan awal: UMKM yang tidak memenuhi tidak ikut dihitung ----

def evaluate_eligibility(umkm: dict) -> tuple[bool, str]:
    """Return (layak, alasan_gugur). Alasan kosong bila layak."""
    reasons = []
    nib = umkm.get("nib")
    if nib is None or str(nib).strip() == "":
        reasons.append("Tidak memiliki NIB")
    lama = umkm.get("lama_usaha_bulan")
    if lama is None or lama < MIN_BUSINESS_AGE_MONTHS:
        reasons.append(f"Lama usaha kurang dari {MIN_BUSINESS_AGE_MONTHS} bulan")
    return (not reasons), "; ".join(reasons)


# ---- pilihan isian formulir (hanya saran; isian bebas tetap diterima) ----
KECAMATAN_OPTIONS = ["Banjarsari", "Jebres", "Laweyan", "Pasar Kliwon", "Serengan"]
JENIS_USAHA_OPTIONS = ["Kuliner", "Batik", "Kerajinan", "Jasa", "Lainnya"]
