"""Pembacaan data UMKM yang dikelola di database terpisah."""


def list_umkm(conn, *, q="", kecamatan="", jenis="", page=1, per_page=20):
    where, params = ["1=1"], []
    if q:
        where.append("(nama_usaha LIKE ? OR pemilik LIKE ? OR source_id LIKE ?)")
        params.extend([f"%{q}%"] * 3)
    if kecamatan:
        where.append("kecamatan = ?")
        params.append(kecamatan)
    if jenis:
        where.append("jenis_usaha = ?")
        params.append(jenis)

    clause = " AND ".join(where)
    total = conn.execute(f"SELECT COUNT(*) FROM umkm WHERE {clause}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM umkm WHERE {clause} ORDER BY source_id LIMIT ? OFFSET ?",
        (*params, per_page, (page - 1) * per_page),
    ).fetchall()
    return [dict(row) for row in rows], total


def facets(conn):
    def distinct(column):
        return [row[0] for row in conn.execute(
            f"SELECT DISTINCT {column} FROM umkm "
            f"WHERE {column} IS NOT NULL ORDER BY {column}"
        )]

    return {"kecamatan": distinct("kecamatan"), "jenis": distinct("jenis_usaha")}
