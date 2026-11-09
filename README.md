# SPK Prioritas Bantuan UMKM (AHP + TOPSIS)

Sistem pendukung keputusan untuk menentukan UMKM prioritas penerima bantuan di Kota Surakarta. Bobot kriteria dihitung dengan **AHP**, peringkat dengan **TOPSIS**. Peringkat hanya bahan pertimbangan; penetapan penerima tetap oleh tim penilai.

> Data yang digunakan pada projek ini adalah data dummy, bukan data UMKM sebenarnya.

## Menjalankan

```bash
pip install -r requirements.txt
python run.py
```

Buka <http://127.0.0.1:8000>.
Akun development: `admin / admin123` dan `penilai / penilai123`.

Alur di web: **Data UMKM**, lalu **Periode seleksi → buat periode → 1. Alternatif → 2. Bobot AHP → 3. Peringkat**.
Untuk mencoba cepat, di halaman Bobot AHP pilih *Pakai matriks contoh*.

| Perintah | Fungsi |
|---|---|
| `python run.py` | web dengan database yang sudah tersedia |
| `python run.py compute 1` / `initdb` | langkah satuan dari terminal |
| `python -m pytest` | seluruh unit test |

Pengaturan lewat environment: `SPK_DATA_DIR` (folder data, default `data/`), `SPK_DB`,
`SPK_SECRET_KEY` (**ganti** bila dipakai di luar komputer sendiri).

## Isi Folder

```
run.py              satu pintu masuk (CLI dan server web SPK)
requirements.txt    daftar pustaka Python yang dibutuhkan
pytest.ini          konfigurasi unit test
backend/            kode server FastAPI dan logika AHP-TOPSIS
  mcdm/             rumus murni MCDM: AHP dan TOPSIS (NumPy)
  criteria.py       definisi kriteria C1-C7, validasi rentang, syarat kelayakan
  database.py       koneksi dan inisialisasi SQLite
  schema.sql        skema tabel database
  security.py       hashing password (scrypt), otentikasi, token CSRF
  dependencies.py   dependency injection FastAPI (DB, session, role, form)
  formatting.py     formatter angka, rupiah, tanggal, skala Saaty
  templating.py     integrasi Jinja2 template engine dan flash messages
  main.py           instansiasi FastAPI app, middleware, routing, error handler
  routes/           controller/router per fitur web
  services/         business logic data UMKM, periode seleksi, dan kalkulasi
frontend/           tampilan aplikasi (Server-Side Rendering)
  templates/        templat HTML Jinja2 (antarmuka pengguna)
  static/           berkas statis (CSS styling dan JavaScript pendukung)
tests/              pengujian matematika AHP & TOPSIS dan verifikasi manual
```

`backend/` membaca data UMKM secara read-only dari SQLite. Endpoint JSON read-only tersedia di `/api/umkm`,
`/api/periode`, dan `/api/periode/{id}/hasil` untuk kebutuhan integrasi.

## Catatan untuk Pengembang

- **Rumus terpisah dari web.** Perubahan rumus hanya di `backend/mcdm/`.
- **Periode adalah arsip.** Saat dibuat, nilai kriteria disalin ke `umkm_score`; data UMKM dikelola di luar aplikasi SPK.
- **Bobot hanya dipakai bila CR ≤ 0,1.** Bobot atau pilihan UMKM yang berubah menghapus peringkat lama agar tidak ada hasil kedaluwarsa.
- **Dua lapis penyaringan data.** Data rusak (kosong, tipe salah, di luar rentang) ditolak dan dicatat alasannya. Aturan bisnis (tanpa NIB, usaha < 6 bulan)
  tidak membuang data; UMKM diberi status `gugur` per periode.
- **Halaman bekerja tanpa JavaScript** (formulir biasa, redirect, pesan flash). `static/app.js` hanya kenyamanan kecil.
- **Keamanan dasar:** sesi bertanda tangan, token CSRF di semua POST, kata sandi di-hash (scrypt), tujuan redirect login divalidasi.
- Matriks contoh (`backend/services/sample_matrix.py`) **bukan bobot resmi Dinas**.

## Pengujian

Tes memeriksa kebenaran formula matematika AHP dan TOPSIS (`python -m pytest`).
Pembanding hitung manual berbasis Python murni ada di `tests/test_manual_calculation.py`.
