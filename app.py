from flask import Flask, render_template, request, jsonify
import mysql.connector
from datetime import datetime
import traceback

app = Flask(__name__)
app.secret_key = "rahasia_kasir_koperasi"

# ===============================
# ===== Koneksi ke Database =====
# ===============================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="kasir_koperasi"
    )

# ===============================
# === Helper: sinkron harga_jual
# ===============================
def sinkron_harga_jual(conn, id_barang):
    """
    Sinkronkan semua baris detail_barang untuk id_barang agar harga_jual
    masing-masing diset ke nilai tertinggi (MAX) yang ada untuk id_barang itu.
    """
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT MAX(harga_jual) AS max_harga FROM detail_barang WHERE id_barang = %s", (id_barang,))
        row = cur.fetchone()
        if row and row["max_harga"] is not None:
            max_harga = row["max_harga"]
            # Update semua baris detail_barang untuk id_barang agar harga_jual = max_harga
            cur.execute("UPDATE detail_barang SET harga_jual = %s WHERE id_barang = %s", (max_harga, id_barang))
            conn.commit()
    finally:
        cur.close()

# ===============================
# ===== Halaman Utama ===========
# ===============================
@app.route("/")
def index():
    return render_template("index.html", datetime=datetime)

# ===============================
# ===== Ambil Barang by KODE ====
# ===============================
@app.route("/get_barang/<kode>")
def get_barang(kode):
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT b.id_barang, b.nama_barang, b.kode_barang, d.id_detail, 
                   d.harga_beli, d.margin, d.harga_jual, d.stok
            FROM barang b
            JOIN detail_barang d ON b.id_barang = d.id_barang
            WHERE b.kode_barang = %s
            ORDER BY d.harga_jual DESC
            LIMIT 1
        """, (kode,))
        barang = cur.fetchone()
        cur.close()
        conn.close()

        if not barang:
            return jsonify({"error": True, "message": "Kode barang tidak ditemukan"}), 404

        return jsonify({
            "error": False,
            "id_detail": barang["id_detail"],
            "kode_barang": barang["kode_barang"],
            "nama_barang": barang["nama_barang"],
            "harga_beli": int(round(float(barang["harga_beli"]))),
            "margin": round(float(barang["margin"] or 0), 2),
            "harga_jual": int(round(float(barang["harga_jual"]))),
            "stok": int(barang["stok"] or 0)
        })

    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== Pembelian Barang ========
# ===============================
@app.route("/pembelian", methods=["GET", "POST"])
def pembelian():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            items = data.get("items", [])

            if not items:
                return jsonify({"error": True, "message": "Tidak ada barang dibeli"}), 400

            conn = get_db()
            cur = conn.cursor(dictionary=True)

            # Insert transaksi pembelian utama
            cur.execute("INSERT INTO pembelian (tanggal) VALUES (%s)", (datetime.now(),))
            id_pembelian = cur.lastrowid

            for idx, item in enumerate(items, start=1):
                id_detail_awal = int(item["id_detail"])
                harga_beli = float(item.get("harga_beli", 0))
                harga_jual_input = float(item.get("harga_jual", 0))
                margin_input = str(item.get("margin", "")).strip()
                stok_tambah = int(item.get("jumlah", 0))

                # Hitung harga_jual & margin
                harga_jual = harga_jual_input
                margin_persen = 0.0

                if margin_input:
                    cleaned = margin_input.replace("%", "").strip()
                    try:
                        mval = float(cleaned)
                    except:
                        mval = 0.0
                    margin_persen = mval
                    harga_jual = harga_beli + (harga_beli * margin_persen / 100.0)
                elif harga_jual_input > 0:
                    harga_jual = harga_jual_input
                    margin_persen = ((harga_jual - harga_beli) / harga_beli * 100.0) if harga_beli > 0 else 0.0
                else:
                    harga_jual = harga_beli
                    margin_persen = 0.0

                # Bulatkan
                harga_beli = int(round(harga_beli))
                harga_jual = int(round(harga_jual))
                margin_persen = round(margin_persen, 2)

                # Ambil id_barang dari id_detail_awal
                cur.execute("SELECT id_barang FROM detail_barang WHERE id_detail = %s", (id_detail_awal,))
                barang_row = cur.fetchone()
                if not barang_row:
                    raise ValueError(f"Item #{idx}: id_detail {id_detail_awal} tidak ditemukan")
                id_barang = barang_row["id_barang"]

                # Cek ada detail dengan harga_beli sama
                cur.execute("""
                    SELECT id_detail, stok FROM detail_barang
                    WHERE id_barang = %s AND harga_beli = %s
                    LIMIT 1
                """, (id_barang, harga_beli))
                same_price = cur.fetchone()

                if same_price:
                    cur.execute("""
                        UPDATE detail_barang
                        SET stok = stok + %s, margin = %s, harga_jual = %s
                        WHERE id_detail = %s
                    """, (stok_tambah, margin_persen, harga_jual, same_price["id_detail"]))
                    id_detail_final = same_price["id_detail"]
                else:
                    cur.execute("""
                        INSERT INTO detail_barang (id_barang, harga_beli, margin, harga_jual, stok, dibuat_pada)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id_barang, harga_beli, margin_persen, harga_jual, stok_tambah, datetime.now()))
                    id_detail_final = cur.lastrowid

                # Insert detail_pembelian
                cur.execute("""
                    INSERT INTO detail_pembelian (id_pembelian, id_detail, jumlah, harga_beli)
                    VALUES (%s, %s, %s, %s)
                """, (id_pembelian, id_detail_final, stok_tambah, harga_beli))

                # Sinkron harga_jual (set semua detail_barang harga_jual = max)
                sinkron_harga_jual(conn, id_barang)

            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"error": False, "message": "Transaksi pembelian berhasil disimpan dan harga sinkron!"})

        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            return jsonify({"error": True, "message": str(e), "trace": tb}), 500

    return render_template("pembelian.html", datetime=datetime)

# ===============================
# ===== Penjualan Barang ========
# ===============================
@app.route("/penjualan", methods=["GET", "POST"])
def penjualan():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            items = data.get("items", [])

            if not items:
                return jsonify({"error": True, "message": "Tidak ada barang dijual"}), 400

            conn = get_db()
            cur = conn.cursor(dictionary=True)

            # Buat transaksi penjualan utama
            cur.execute("INSERT INTO penjualan (tanggal) VALUES (%s)", (datetime.now(),))
            id_penjualan = cur.lastrowid
            total_harga = 0

            for item in items:
                id_detail = int(item.get("id_detail"))
                jumlah = int(item.get("jumlah", 0))
                harga_jual = int(item.get("harga_jual", 0))

                # Ambil data stok
                cur.execute("SELECT id_barang, stok FROM detail_barang WHERE id_detail = %s FOR UPDATE", (id_detail,))
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Detail barang ID {id_detail} tidak ditemukan")

                id_barang = row["id_barang"]
                stok_sekarang = int(row["stok"] or 0)

                if stok_sekarang < jumlah:
                    raise ValueError(f"Stok barang tidak cukup (tersisa {stok_sekarang})")

                # Kurangi stok
                cur.execute("UPDATE detail_barang SET stok = stok - %s WHERE id_detail = %s", (jumlah, id_detail))

                subtotal = jumlah * harga_jual
                total_harga += subtotal

                # Simpan detail_penjualan (pakai kolom subtotal)
                cur.execute("""
                    INSERT INTO detail_penjualan (id_penjualan, id_detail, jumlah, subtotal)
                    VALUES (%s, %s, %s, %s)
                """, (id_penjualan, id_detail, jumlah, subtotal))

                sinkron_harga_jual(conn, id_barang)

            # Update total di penjualan
            cur.execute("UPDATE penjualan SET total_harga = %s WHERE id_penjualan = %s", (total_harga, id_penjualan))
            conn.commit()
            cur.close()
            conn.close()

            return jsonify({"error": False, "message": "Transaksi penjualan berhasil disimpan!"})

        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            return jsonify({"error": True, "message": str(e), "trace": tb}), 500

    return render_template("penjualan.html", datetime=datetime)

# ===============================
# ===== Edit Stok Barang ========
# ===============================
@app.route("/update_stok", methods=["POST"])
def update_stok():
    try:
        data = request.get_json(force=True)
        id_detail = int(data["id_detail"])
        harga_beli = float(data["harga_beli"])
        margin = float(data["margin"])
        harga_jual = float(data["harga_jual"])
        stok = int(data["stok"])

        # Normalisasi
        harga_beli = int(round(harga_beli))
        harga_jual = int(round(harga_jual))
        margin = round(margin, 2)

        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            UPDATE detail_barang
            SET harga_beli = %s, margin = %s, harga_jual = %s, stok = %s
            WHERE id_detail = %s
        """, (harga_beli, margin, harga_jual, stok, id_detail))

        # Ambil id_barang lalu sinkron
        cur.execute("SELECT id_barang FROM detail_barang WHERE id_detail = %s", (id_detail,))
        row = cur.fetchone()
        if row:
            sinkron_harga_jual(conn, row["id_barang"])

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"error": False, "message": "Data stok berhasil diperbarui dan harga jual disinkronkan!"})
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== Hapus Stok Barang =======
# ===============================
@app.route("/hapus_stok/<int:id_detail>", methods=["DELETE"])
def hapus_stok(id_detail):
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        # Ambil id_barang sebelum hapus
        cur.execute("SELECT id_barang FROM detail_barang WHERE id_detail = %s", (id_detail,))
        row = cur.fetchone()
        id_barang = row["id_barang"] if row else None

        cur.execute("DELETE FROM detail_barang WHERE id_detail = %s", (id_detail,))
        conn.commit()

        if id_barang:
            sinkron_harga_jual(conn, id_barang)

        cur.close()
        conn.close()
        return jsonify({"error": False, "message": "Data stok berhasil dihapus dan harga jual disinkronkan!"})
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== Lihat Stok Barang =======
# ===============================
@app.route("/stok")
def stok():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT 
                b.kode_barang, 
                b.nama_barang, 
                d.id_detail,
                d.harga_beli, 
                d.margin, 
                d.harga_jual, 
                d.stok
            FROM barang b
            JOIN detail_barang d ON b.id_barang = d.id_barang
            ORDER BY b.nama_barang ASC, d.harga_beli ASC
        """)
        data_stok = cur.fetchall()
        cur.close()
        conn.close()

        # normalisasi tipe
        for row in data_stok:
            row["harga_beli"] = int(round(float(row["harga_beli"] or 0)))
            row["harga_jual"] = int(round(float(row["harga_jual"] or 0)))
            row["margin"] = round(float(row["margin"] or 0), 2)
            row["stok"] = int(row["stok"] or 0)

        return render_template("stok.html", data_stok=data_stok, datetime=datetime)
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== Jalankan Aplikasi =======
# ===============================
if __name__ == "__main__":
    app.run(debug=True)
