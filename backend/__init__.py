"""SPK prioritas penerima bantuan UMKM (AHP + TOPSIS).

Peta modul:
  criteria.py     kriteria C1-C7, validasi nilai, syarat kelayakan awal
  database.py     koneksi SQLite; skema ada di schema.sql
  mcdm/           rumus AHP dan TOPSIS (NumPy)
  services/       logika alur kerja di atas database (tanpa urusan web)
  routes/         halaman web (satu berkas per fitur)
  main.py         membuat aplikasi FastAPI
"""
