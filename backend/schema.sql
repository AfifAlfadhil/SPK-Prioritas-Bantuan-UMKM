CREATE TABLE IF NOT EXISTS criterion (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('benefit','cost')),
    min_val REAL,
    max_val REAL
);

CREATE TABLE IF NOT EXISTS umkm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL UNIQUE,
    nama_usaha TEXT NOT NULL,
    pemilik TEXT,
    jenis_usaha TEXT,
    kecamatan TEXT,
    kelurahan TEXT,
    nib TEXT,
    modal_usaha INTEGER NOT NULL,
    omzet_bulanan INTEGER NOT NULL,
    jumlah_tenaga_kerja INTEGER NOT NULL,
    lama_usaha_bulan INTEGER NOT NULL,
    tingkat_digitalisasi INTEGER NOT NULL,
    akses_permodalan INTEGER NOT NULL,
    riwayat_bantuan INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS selection_period (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS umkm_score (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    umkm_id INTEGER NOT NULL REFERENCES umkm(id),
    period_id INTEGER NOT NULL REFERENCES selection_period(id),
    c1 REAL, c2 REAL, c3 REAL, c4 REAL, c5 REAL, c6 REAL, c7 REAL,
    status TEXT NOT NULL CHECK (status IN ('lolos','gugur')),
    reason TEXT,
    -- Pilihan petugas: UMKM lolos syarat awal yang dipilih untuk masuk perhitungan TOPSIS
    selected INTEGER NOT NULL DEFAULT 1,
    UNIQUE (umkm_id, period_id)
);

CREATE TABLE IF NOT EXISTS pairwise_comparison (
    period_id INTEGER NOT NULL REFERENCES selection_period(id),
    i INTEGER NOT NULL,
    j INTEGER NOT NULL,
    value REAL NOT NULL,
    PRIMARY KEY (period_id, i, j)
);

CREATE TABLE IF NOT EXISTS ahp_result (
    period_id PRIMARY KEY REFERENCES selection_period(id),
    w1 REAL, w2 REAL, w3 REAL, w4 REAL, w5 REAL, w6 REAL, w7 REAL,
    lambda_max REAL,
    ci REAL,
    cr REAL,
    consistent INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS topsis_result (
    period_id INTEGER NOT NULL REFERENCES selection_period(id),
    umkm_id INTEGER NOT NULL REFERENCES umkm(id),
    d_plus REAL,
    d_minus REAL,
    v REAL,
    rank INTEGER,
    PRIMARY KEY (period_id, umkm_id)
);

CREATE TABLE IF NOT EXISTS app_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin','penilai')),
    created_at TEXT NOT NULL
);
