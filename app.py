from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import mysql.connector
from datetime import datetime, timedelta
import traceback
import os
from functools import wraps
import random
import string

app = Flask(__name__)
app.secret_key = "rahasia_kasir_koperasi"

# ===============================
# ===== Decorator untuk Login ===
# ===============================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            print("🔒 Belum login — redirect ke /login")
            return redirect(url_for('login'))
        print(f"✅ Sudah login sebagai {session.get('nama_petugas')}")
        return f(*args, **kwargs)
    return decorated_function


# ===============================
# ===== Koneksi ke Database =====
# ===============================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="kasir_koperasi",
        charset="utf8mb4",
        use_unicode=True
    )

# ===============================
# ===== Koneksi ke DB Faktur ====
# ===============================
def get_db_faktur():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="faktur",
        charset="utf8mb4",
        use_unicode=True
    )

# ===============================
# === Helper: Generate Kode Barang Unik
# ===============================
def generate_kode_barang():
    """Generate kode barang unik dengan format BRG-XXXXXX"""
    conn = get_db()
    cur = conn.cursor()
    
    while True:
        # Generate random 6 digit alphanumeric
        random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        kode = f"BRG-{random_code}"
        
        # Check if code already exists
        cur.execute("SELECT COUNT(*) FROM barang WHERE kode_barang = %s", (kode,))
        if cur.fetchone()[0] == 0:
            cur.close()
            conn.close()
            return kode
    
# ===============================
# === Helper: sinkron harga_jual
# ===============================
def sinkron_harga_jual(conn, id_barang):
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT MAX(harga_jual) AS max_harga FROM detail_barang WHERE id_barang = %s", (id_barang,))
        row = cur.fetchone()
        if row and row["max_harga"] is not None:
            max_harga = row["max_harga"]
            cur.execute("UPDATE detail_barang SET harga_jual = %s WHERE id_barang = %s", (max_harga, id_barang))
            conn.commit()
    finally:
        cur.close()

# ===============================
# === Helper: nomor faktur sederhana
# ===============================
def buat_nomor_faktur(tipe):
    now = datetime.now()
    tahun2 = now.strftime("%y")  # 2 digit tahun
    sisa = now.strftime("%m%d%H%M%S")  # bulan, hari, jam, menit, detik
    if tipe == "pembelian":
        return f"b{tahun2}{sisa}"
    else:
        return f"j{tahun2}{sisa}"

# ===============================
# === Helper: simpan faktur ke DB faktur
# ===============================
def simpan_faktur(tipe, ref_id, nomor_faktur, tanggal, pelanggan, total, html_content):
    conn = get_db_faktur()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO faktur_master (tipe, ref_id, nomor_faktur, tanggal, pelanggan, total, html)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (tipe, ref_id, nomor_faktur, tanggal, pelanggan, total, html_content))
        conn.commit()
        id_faktur = cur.lastrowid
        return id_faktur
    finally:
        cur.close()
        conn.close()

# ===============================
# === Helper: konversi angka ke terbilang
# ===============================
def angka_ke_terbilang(angka):
    """Konversi angka ke terbilang dalam Bahasa Indonesia"""
    angka = int(angka)
    
    if angka == 0:
        return "nol"
    
    satuan = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"]
    belasan = ["sepuluh", "sebelas", "dua belas", "tiga belas", "empat belas", "lima belas", 
               "enam belas", "tujuh belas", "delapan belas", "sembilan belas"]
    
    def konversi_ratusan(n):
        if n == 0:
            return ""
        elif n < 10:
            return satuan[n]
        elif n < 20:
            return belasan[n - 10]
        elif n < 100:
            return satuan[n // 10] + " puluh" + (" " + satuan[n % 10] if n % 10 != 0 else "")
        else:
            ratus = " seratus" if n // 100 == 1 else " " + satuan[n // 100] + " ratus"
            return ratus.strip() + (" " + konversi_ratusan(n % 100) if n % 100 != 0 else "")
    
    if angka < 1000:
        return konversi_ratusan(angka)
    elif angka < 1000000:
        ribu = "seribu" if angka // 1000 == 1 else konversi_ratusan(angka // 1000) + " ribu"
        return ribu + (" " + konversi_ratusan(angka % 1000) if angka % 1000 != 0 else "")
    elif angka < 1000000000:
        juta = konversi_ratusan(angka // 1000000) + " juta"
        return juta + (" " + angka_ke_terbilang(angka % 1000000) if angka % 1000000 != 0 else "")
    else:
        miliar = konversi_ratusan(angka // 1000000000) + " miliar"
        return miliar + (" " + angka_ke_terbilang(angka % 1000000000) if angka % 1000000000 != 0 else "")

# ===============================
# ===== Login & Logout ==========
# ===============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        try:
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT id_petugas, nama_petugas, username, password 
                FROM petugas 
                WHERE username = %s AND password = %s
            """, (username, password))
            
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user:
                session['user_id'] = user['id_petugas']
                session['username'] = user['username']
                session['nama_petugas'] = user['nama_petugas']
                return redirect(url_for('index'))
            else:
                return render_template("login.html", error="Username atau password salah!")
                
        except Exception as e:
            print(f"Error login: {e}")
            return render_template("login.html", error="Terjadi kesalahan sistem!")
    
    # Jika sudah login, redirect ke index
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

# ===============================
# ===== Halaman Utama ===========
# ===============================
@app.route("/")
@login_required
def index():
    return render_template("index.html", datetime=datetime, nama_petugas=session.get('nama_petugas'))

# ===============================
# ===== API TAMBAH BARANG BARU ==
# ===============================
@app.route("/tambah_barang", methods=["GET", "POST"])
@login_required
def tambah_barang():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            
            # ✅ DEFENSIVE HANDLING untuk field yang bisa None
            nama_barang = (data.get("nama_barang") or "").strip()
            kode_barang_manual = (data.get("kode_barang") or "").strip()
            barcode = (data.get("barcode") or "").strip()
            keterangan = (data.get("keterangan") or "").strip()
            
            # ✅ ID bisa None atau integer
            id_supplier = data.get("id_supplier")
            id_kategori = data.get("id_kategori")
            
            # Convert empty string ke None
            if id_supplier == "":
                id_supplier = None
            if id_kategori == "":
                id_kategori = None
            
            if not nama_barang:
                return jsonify({"error": True, "message": "Nama barang wajib diisi!"}), 400
            
            # ✅ VALIDASI BARCODE FLEKSIBEL
            if barcode:
                import re
                if not re.match(r'^[a-zA-Z0-9\-_]+$', barcode):
                    return jsonify({
                        "error": True, 
                        "message": "Barcode hanya boleh berisi huruf, angka, tanda hubung (-), dan underscore (_)"
                    }, 400)
            
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            
            # Generate kode barang jika tidak diisi
            if kode_barang_manual:
                # Cek apakah kode sudah digunakan
                cur.execute("SELECT COUNT(*) as total FROM barang WHERE kode_barang = %s", (kode_barang_manual,))
                if cur.fetchone()['total'] > 0:
                    cur.close()
                    conn.close()
                    return jsonify({
                        "error": True, 
                        "message": f"Kode barang '{kode_barang_manual}' sudah digunakan!"
                    }), 400
                kode_barang = kode_barang_manual
            else:
                kode_barang = generate_kode_barang()
            
            # ✅ CEK APAKAH BARCODE SUDAH DIGUNAKAN
            if barcode:
                cur.execute("""
                    SELECT kode_barang, nama_barang 
                    FROM barang 
                    WHERE barcode = %s
                """, (barcode,))
                existing = cur.fetchone()
                
                if existing:
                    cur.close()
                    conn.close()
                    return jsonify({
                        "error": True, 
                        "message": f"Barcode '{barcode}' sudah digunakan oleh: {existing['nama_barang']} ({existing['kode_barang']})"
                    }), 400
            
            # ✅ INSERT BARANG dengan handling None
            cur.execute("""
                INSERT INTO barang (kode_barang, nama_barang, barcode, id_supplier, id_kategori, keterangan, dibuat_pada)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                kode_barang, 
                nama_barang, 
                barcode if barcode else None,
                id_supplier,
                id_kategori,
                keterangan if keterangan else None,
                datetime.now()
            ))
            
            id_barang = cur.lastrowid
            
            # Insert detail_barang dengan harga 0
            cur.execute("""
                INSERT INTO detail_barang (id_barang, harga_beli, margin, harga_jual, stok, dibuat_pada)
                VALUES (%s, 0, 0, 0, 0, %s)
            """, (id_barang, datetime.now()))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return jsonify({
                "error": False,
                "message": "✅ Barang berhasil ditambahkan!",
                "kode_barang": kode_barang,
                "nama_barang": nama_barang,
                "barcode": barcode if barcode else None,
                "id_barang": id_barang
            })
            
        except Exception as e:
            tb = traceback.format_exc()
            print("❌ ERROR TAMBAH BARANG:")
            print(tb)
            return jsonify({
                "error": True, 
                "message": f"Terjadi kesalahan: {str(e)}",
                "trace": tb
            }), 500
    
    return render_template("tambah_barang.html", nama_petugas=session.get('nama_petugas'))

# ===============================
# ===== HALAMAN BARCODE SCANNER =
# ===============================
@app.route("/barcode-scanner")
@login_required
def barcode_scanner():
    return render_template("barcode_scanner.html", nama_petugas=session.get('nama_petugas'))

# ===============================
# ===== API UPDATE BARCODE ======
# ===============================
@app.route("/api/update_barcode", methods=["POST"])
@login_required
def update_barcode():
    """Update barcode untuk barang yang sudah ada"""
    try:
        data = request.get_json(force=True)
        kode_barang = data.get("kode_barang", "").strip()
        barcode = data.get("barcode", "").strip()
        
        if not kode_barang or not barcode:
            return jsonify({"error": True, "message": "Kode barang dan barcode wajib diisi!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah kode barang ada
        cur.execute("SELECT id_barang, nama_barang FROM barang WHERE kode_barang = %s", (kode_barang,))
        barang = cur.fetchone()
        
        if not barang:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Kode barang tidak ditemukan!"}), 404
        
        # Cek apakah barcode sudah digunakan barang lain
        cur.execute("SELECT kode_barang, nama_barang FROM barang WHERE barcode = %s AND kode_barang != %s", (barcode, kode_barang))
        existing = cur.fetchone()
        
        if existing:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Barcode sudah digunakan oleh barang: {existing['nama_barang']} ({existing['kode_barang']})"
            }), 400
        
        # Update barcode
        cur.execute("UPDATE barang SET barcode = %s WHERE kode_barang = %s", (barcode, kode_barang))
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "Barcode berhasil disimpan!",
            "kode_barang": kode_barang,
            "nama_barang": barang['nama_barang'],
            "barcode": barcode
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API GET BARANG BY BARCODE
# ===============================
@app.route("/api/get_barang_by_barcode/<barcode>")
@login_required
def get_barang_by_barcode(barcode):
    """Ambil data barang berdasarkan barcode"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cari barang berdasarkan barcode
        cur.execute("""
            SELECT b.id_barang, b.nama_barang, b.kode_barang, b.barcode, d.id_detail,
                   d.harga_beli, d.margin, d.harga_jual, d.stok
            FROM barang b
            JOIN detail_barang d ON b.id_barang = d.id_barang
            WHERE b.barcode = %s
            ORDER BY d.harga_jual DESC, d.dibuat_pada DESC
            LIMIT 1
        """, (barcode,))
        
        barang = cur.fetchone()
        cur.close()
        conn.close()

        if not barang:
            return jsonify({"error": True, "message": "Barcode tidak ditemukan"}), 404

        return jsonify({
            "error": False,
            "id_detail": barang["id_detail"],
            "kode_barang": barang["kode_barang"],
            "nama_barang": barang["nama_barang"],
            "barcode": barang["barcode"],
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
# ===== API RESET DATABASE ======
# ===============================
@app.route("/api/reset_database", methods=["POST"])
@login_required
def reset_database():
    """Reset semua data transaksi (penjualan, pembelian, faktur) dan stok barang ke 0"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # Hapus semua detail penjualan
        cur.execute("DELETE FROM detail_penjualan")
        
        # Hapus semua penjualan
        cur.execute("DELETE FROM penjualan")
        
        # Hapus semua detail pembelian
        cur.execute("DELETE FROM detail_pembelian")
        
        # Hapus semua pembelian
        cur.execute("DELETE FROM pembelian")
        
        # Reset stok semua barang ke 0
        cur.execute("UPDATE detail_barang SET stok = 0")
        
        # Reset AUTO_INCREMENT
        cur.execute("ALTER TABLE penjualan AUTO_INCREMENT = 1")
        cur.execute("ALTER TABLE detail_penjualan AUTO_INCREMENT = 1")
        cur.execute("ALTER TABLE pembelian AUTO_INCREMENT = 1")
        cur.execute("ALTER TABLE detail_pembelian AUTO_INCREMENT = 1")
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Hapus semua faktur dari database faktur
        conn_faktur = get_db_faktur()
        cur_faktur = conn_faktur.cursor()
        
        cur_faktur.execute("DELETE FROM faktur_master")
        cur_faktur.execute("ALTER TABLE faktur_master AUTO_INCREMENT = 1")
        
        conn_faktur.commit()
        cur_faktur.close()
        conn_faktur.close()
        
        print(f"✅ Database berhasil direset oleh {session.get('nama_petugas')}")
        
        return jsonify({
            "error": False,
            "message": "Database berhasil direset! Semua transaksi dan stok telah dihapus."
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({
            "error": True,
            "message": f"Gagal reset database: {str(e)}",
            "trace": tb
        }), 500

# ===============================
# ===== API Dashboard Stats =====
# ===============================
@app.route("/api/dashboard_stats")
@login_required
def dashboard_stats():
    """API endpoint untuk mendapatkan statistik dashboard secara dinamis"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # ===== 1. STATISTIK PENJUALAN =====
        now = datetime.now()
        today = now.date()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Penjualan Hari Ini
        cur.execute("""
            SELECT COALESCE(SUM(total_harga), 0) as total
            FROM penjualan
            WHERE DATE(tanggal) = %s
        """, (today,))
        penjualan_hari = cur.fetchone()['total']
        
        # Penjualan Bulan Ini
        cur.execute("""
            SELECT COALESCE(SUM(total_harga), 0) as total
            FROM penjualan
            WHERE tanggal >= %s
        """, (current_month_start,))
        penjualan_bulan = cur.fetchone()['total']
        
        # Penjualan Tahun Ini
        cur.execute("""
            SELECT COALESCE(SUM(total_harga), 0) as total
            FROM penjualan
            WHERE tanggal >= %s
        """, (current_year_start,))
        penjualan_tahun = cur.fetchone()['total']
        
        # Total Semua Penjualan
        cur.execute("SELECT COALESCE(SUM(total_harga), 0) as total FROM penjualan")
        penjualan_total = cur.fetchone()['total']
        
        # ===== 2. STATISTIK LABA =====
        # Laba Hari Ini
        cur.execute("""
            SELECT COALESCE(SUM(
                dp.subtotal - (db.harga_beli * dp.jumlah)
            ), 0) as laba
            FROM detail_penjualan dp
            JOIN penjualan p ON dp.id_penjualan = p.id_penjualan
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            WHERE DATE(p.tanggal) = %s
        """, (today,))
        laba_hari = cur.fetchone()['laba']
        
        # Laba Bulan Ini
        cur.execute("""
            SELECT COALESCE(SUM(
                dp.subtotal - (db.harga_beli * dp.jumlah)
            ), 0) as laba
            FROM detail_penjualan dp
            JOIN penjualan p ON dp.id_penjualan = p.id_penjualan
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            WHERE p.tanggal >= %s
        """, (current_month_start,))
        laba_bulan = cur.fetchone()['laba']
        
        # Laba Tahun Ini
        cur.execute("""
            SELECT COALESCE(SUM(
                dp.subtotal - (db.harga_beli * dp.jumlah)
            ), 0) as laba
            FROM detail_penjualan dp
            JOIN penjualan p ON dp.id_penjualan = p.id_penjualan
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            WHERE p.tanggal >= %s
        """, (current_year_start,))
        laba_tahun = cur.fetchone()['laba']
        
        # Total Laba
        cur.execute("""
            SELECT COALESCE(SUM(
                dp.subtotal - (db.harga_beli * dp.jumlah)
            ), 0) as laba
            FROM detail_penjualan dp
            JOIN detail_barang db ON dp.id_detail = db.id_detail
        """)
        laba_total = cur.fetchone()['laba']
        
        # ===== 3. INFO CARDS =====
        # Jumlah Produk (unique barang)
        cur.execute("SELECT COUNT(*) as jumlah FROM barang")
        jumlah_produk = cur.fetchone()['jumlah']
        
        # Jumlah Invoice (dari database faktur)
        conn_faktur = get_db_faktur()
        cur_faktur = conn_faktur.cursor(dictionary=True)
        cur_faktur.execute("SELECT COUNT(*) as jumlah FROM faktur_master")
        jumlah_invoice = cur_faktur.fetchone()['jumlah']
        cur_faktur.close()
        conn_faktur.close()
        
        # Produk Terjual (total item terjual bulan ini)
        cur.execute("""
            SELECT COALESCE(SUM(dp.jumlah), 0) as total
            FROM detail_penjualan dp
            JOIN penjualan p ON dp.id_penjualan = p.id_penjualan
            WHERE p.tanggal >= %s
        """, (current_month_start,))
        produk_terjual = cur.fetchone()['total']
        
        # Rata-rata Transaksi (bulan ini)
        cur.execute("""
            SELECT COUNT(*) as total_transaksi
            FROM penjualan
            WHERE tanggal >= %s
        """, (current_month_start,))
        total_transaksi = cur.fetchone()['total_transaksi']
        rata_transaksi = int(penjualan_bulan / total_transaksi) if total_transaksi > 0 else 0
        
        # ===== 4. ANALISIS LABA RUGI (BULAN INI) =====
        # Pendapatan Penjualan
        pendapatan = penjualan_bulan
        
        # Harga Pokok Penjualan (HPP)
        cur.execute("""
            SELECT COALESCE(SUM(db.harga_beli * dp.jumlah), 0) as hpp
            FROM detail_penjualan dp
            JOIN penjualan p ON dp.id_penjualan = p.id_penjualan
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            WHERE p.tanggal >= %s
        """, (current_month_start,))
        hpp = cur.fetchone()['hpp']
        
        # Laba Kotor = Pendapatan - HPP
        laba_kotor = pendapatan - hpp
        
        # Biaya Operasional (sementara 0, bisa ditambahkan dari tabel biaya)
        biaya_operasional = 0
        
        # Laba Bersih = Laba Kotor - Biaya Operasional
        laba_bersih = laba_kotor - biaya_operasional
        
        # ===== 5. GRAFIK PENJUALAN HARIAN (30 hari terakhir) =====
        cur.execute("""
            SELECT 
                DATE(tanggal) as tanggal,
                COALESCE(SUM(total_harga), 0) as total
            FROM penjualan
            WHERE tanggal >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(tanggal)
            ORDER BY tanggal ASC
        """)
        data_harian = cur.fetchall()
        
        # Generate 30 hari terakhir dengan data 0 jika tidak ada transaksi
        grafik_harian_labels = []
        grafik_harian_data = []
        data_harian_dict = {str(row['tanggal']): float(row['total']) for row in data_harian}
        
        for i in range(29, -1, -1):
            date = today - timedelta(days=i)
            date_str = str(date)
            grafik_harian_labels.append(date.strftime('%d/%m'))
            grafik_harian_data.append(data_harian_dict.get(date_str, 0))
        
        # ===== 6. GRAFIK PENJUALAN BULANAN (12 bulan terakhir) =====
        cur.execute("""
            SELECT 
                DATE_FORMAT(tanggal, '%%Y-%%m') as bulan,
                COALESCE(SUM(total_harga), 0) as total
            FROM penjualan
            WHERE tanggal >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(tanggal, '%%Y-%%m')
            ORDER BY bulan ASC
        """)
        data_bulanan = cur.fetchall()
        
        # Generate 12 bulan terakhir dengan data 0 jika tidak ada transaksi
        grafik_bulanan_labels = []
        grafik_bulanan_data = []
        data_bulanan_dict = {row['bulan']: float(row['total']) for row in data_bulanan}
        
        nama_bulan = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
        
        for i in range(11, -1, -1):
            target_date = now - timedelta(days=30*i)
            month_key = target_date.strftime('%Y-%m')
            month_label = f"{nama_bulan[target_date.month-1]} {target_date.strftime('%y')}"
            
            grafik_bulanan_labels.append(month_label)
            grafik_bulanan_data.append(data_bulanan_dict.get(month_key, 0))
        
        cur.close()
        conn.close()
        
        # ===== 7. RESPONSE JSON =====
        return jsonify({
            "error": False,
            "penjualan": {
                "hari_ini": int(penjualan_hari),
                "bulan_ini": int(penjualan_bulan),
                "tahun_ini": int(penjualan_tahun),
                "total": int(penjualan_total)
            },
            "laba": {
                "hari_ini": int(laba_hari),
                "bulan_ini": int(laba_bulan),
                "tahun_ini": int(laba_tahun),
                "total": int(laba_total)
            },
            "info": {
                "jumlah_produk": jumlah_produk,
                "jumlah_invoice": jumlah_invoice,
                "produk_terjual": int(produk_terjual),
                "rata_transaksi": rata_transaksi
            },
            "profit_loss": {
                "pendapatan": int(pendapatan),
                "hpp": int(hpp),
                "laba_kotor": int(laba_kotor),
                "biaya_operasional": int(biaya_operasional),
                "laba_bersih": int(laba_bersih)
            },
            "grafik_harian": {
                "labels": grafik_harian_labels,
                "data": grafik_harian_data
            },
            "grafik_bulanan": {
                "labels": grafik_bulanan_labels,
                "data": grafik_bulanan_data
            }
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({
            "error": True, 
            "message": str(e), 
            "trace": tb
        }), 500

# ===============================
# ===== Ambil Barang by KODE atau BARCODE ====
# ===============================
@app.route("/get_barang/<kode>")
@login_required
def get_barang(kode):
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # 1. Cari detail_barang dengan stok > 0, urutkan harga_jual DESC, stok DESC, dibuat_pada DESC
        cur.execute("""
            SELECT b.id_barang, b.nama_barang, b.kode_barang, b.barcode, d.id_detail,
                   d.harga_beli, d.margin, d.harga_jual, d.stok
            FROM barang b
            JOIN detail_barang d ON b.id_barang = d.id_barang
            WHERE (b.kode_barang = %s OR b.barcode = %s) AND d.stok > 0
            ORDER BY d.harga_jual DESC, d.stok DESC, d.dibuat_pada DESC
            LIMIT 1
        """, (kode, kode))
        barang = cur.fetchone()

        # 2. Jika tidak ada stok > 0, ambil baris harga_jual tertinggi (stok 0)
        if not barang:
            cur.execute("""
                SELECT b.id_barang, b.nama_barang, b.kode_barang, b.barcode, d.id_detail,
                       d.harga_beli, d.margin, d.harga_jual, d.stok
                FROM barang b
                JOIN detail_barang d ON b.id_barang = d.id_barang
                WHERE b.kode_barang = %s OR b.barcode = %s
                ORDER BY d.harga_jual DESC, d.dibuat_pada DESC
                LIMIT 1
            """, (kode, kode))
            barang = cur.fetchone()

        cur.close()
        conn.close()

        if not barang:
            return jsonify({"error": True, "message": "Kode barang/barcode tidak ditemukan"}), 404

        return jsonify({
            "error": False,
            "id_detail": barang["id_detail"],
            "kode_barang": barang["kode_barang"],
            "nama_barang": barang["nama_barang"],
            "barcode": barang.get("barcode", ""),
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
@login_required
def pembelian():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            items = data.get("items", [])
            tambahan_meta = data.get("meta", {})

            if not items:
                return jsonify({"error": True, "message": "Tidak ada barang dibeli"}), 400

            conn = get_db()
            cur = conn.cursor(dictionary=True)

            # Simpan dengan id_petugas
            cur.execute("INSERT INTO pembelian (tanggal, id_petugas) VALUES (%s, %s)", 
                       (datetime.now(), session.get('user_id')))
            id_pembelian = cur.lastrowid

            total_transaksi = 0
            faktur_items = []
            
            for idx, item in enumerate(items, start=1):
                id_detail_awal = int(item["id_detail"])
                harga_beli = item.get("harga_beli", 0)
                harga_jual_input = item.get("harga_jual", 0)
                margin_input = str(item.get("margin", "")).strip()
                stok_tambah = int(item.get("jumlah", 0))

                # Pastikan harga_beli dan harga_jual integer akurat
                harga_beli = int(float(harga_beli))
                harga_jual_input = int(float(harga_jual_input))

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

                # Pastikan harga_beli dan harga_jual integer (tanpa round)
                harga_beli = int(harga_beli)
                harga_jual = int(harga_jual)
                margin_persen = round(margin_persen, 2)

                cur.execute("SELECT id_barang FROM detail_barang WHERE id_detail = %s", (id_detail_awal,))
                barang_row = cur.fetchone()
                if not barang_row:
                    raise ValueError(f"Item #{idx}: id_detail {id_detail_awal} tidak ditemukan")
                id_barang = barang_row["id_barang"]

                cur.execute("SELECT kode_barang, nama_barang FROM barang WHERE id_barang = %s", (id_barang,))
                info_barang = cur.fetchone()

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

                cur.execute("""
                    INSERT INTO detail_pembelian (id_pembelian, id_detail, jumlah, harga_beli)
                    VALUES (%s, %s, %s, %s)
                """, (id_pembelian, id_detail_final, stok_tambah, harga_beli))

                subtotal = stok_tambah * harga_beli
                total_transaksi += subtotal

                faktur_items.append({
                    "kode": info_barang["kode_barang"] if info_barang else "",
                    "nama": info_barang["nama_barang"] if info_barang else item.get("nama_barang", ""),
                    "jumlah": stok_tambah,
                    "unit": item.get("unit", "pcs"),
                    "harga": harga_beli,
                    "disc": item.get("disc", "0%"),
                    "subtotal": subtotal,
                    "pajak": item.get("pajak", "0%")
                })

                sinkron_harga_jual(conn, id_barang)

            conn.commit()
            cur.close()
            conn.close()

            nomor_faktur = buat_nomor_faktur("pembelian")
            tanggal_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            terbilang = angka_ke_terbilang(total_transaksi).capitalize() + " Rupiah"

            html_faktur = render_template("faktur.html",
                                         tipe="pembelian",
                                         nomor_faktur=nomor_faktur,
                                         tanggal=tanggal_str,
                                         kepada=tambahan_meta.get("kepada", "Supplier"),
                                         up=tambahan_meta.get("up", "-"),
                                         alamat=tambahan_meta.get("alamat", "-"),
                                         pengiriman=tambahan_meta.get("pengiriman", "-"),
                                         nomor_po=tambahan_meta.get("nomor_po", "-"),
                                         mata_uang="IDR",
                                         term=tambahan_meta.get("term", "Cash"),
                                         dikirim_ke=tambahan_meta.get("dikirim_ke", "-"),
                                         items=faktur_items,
                                         terbilang=terbilang,
                                         penerima=tambahan_meta.get("penerima", "-"),
                                         nama_petugas=session.get('nama_petugas'),
                                         total=total_transaksi,
                                         total_pajak=0,
                                         biaya_kirim=0,
                                         dibayar=total_transaksi,
                                         saldo=0)

            id_faktur = simpan_faktur("pembelian", id_pembelian, nomor_faktur, datetime.now(), 
                                     tambahan_meta.get("kepada", "Supplier"), total_transaksi, html_faktur)

            return jsonify({
                "error": False, 
                "message": "Transaksi berhasil disimpan!", 
                "id_pembelian": id_pembelian, 
                "id_faktur": id_faktur, 
                "nomor_faktur": nomor_faktur,
                "redirect_url": url_for('lihat_faktur', id_faktur=id_faktur)
            })

        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            return jsonify({"error": True, "message": str(e), "trace": tb}), 500

    return render_template("pembelian.html", datetime=datetime, nama_petugas=session.get('nama_petugas'))

# ===============================
# ===== Penjualan Barang ========
# ===============================
@app.route("/penjualan", methods=["GET", "POST"])
@login_required
def penjualan():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            items = data.get("items", [])
            
            # Informasi tambahan dari form pembeli
            nama_pembeli = data.get("nama_pembeli", "").strip()
            nomor_telepon = data.get("nomor_telepon", "").strip()
            metode_pembayaran = data.get("metode_pembayaran", "Tunai")
            keterangan = data.get("keterangan", "").strip()
            subtotal = int(data.get("subtotal", 0))
            total_diskon = int(data.get("total_diskon", 0))
            total_bayar = int(data.get("total_bayar", 0))

            if not items:
                return jsonify({"error": True, "message": "Tidak ada barang dijual"}), 400

            conn = get_db()
            cur = conn.cursor(dictionary=True)

            # ===== VALIDASI STOK PERTAMA (SEBELUM INSERT) =====
            error_messages = []
            for idx, item in enumerate(items, start=1):
                id_detail = int(item.get("id_detail"))
                jumlah = int(item.get("jumlah", 0))

                # Cek stok yang tersedia
                cur.execute("""
                    SELECT db.stok, b.nama_barang, b.kode_barang
                    FROM detail_barang db
                    JOIN barang b ON db.id_barang = b.id_barang
                    WHERE db.id_detail = %s
                """, (id_detail,))
                
                row = cur.fetchone()
                
                if not row:
                    error_messages.append(f"Item #{idx}: Detail barang tidak ditemukan (ID: {id_detail})")
                    continue
                
                stok_tersedia = int(row["stok"] or 0)
                nama_barang = row["nama_barang"]
                kode_barang = row["kode_barang"]

                # Validasi stok
                if jumlah > stok_tersedia:
                    error_messages.append(
                        f"Item #{idx} ({kode_barang} - {nama_barang}): "
                        f"Stok tidak mencukupi! Tersedia: {stok_tersedia}, Diminta: {jumlah}"
                    )
                elif jumlah <= 0:
                    error_messages.append(
                        f"Item #{idx} ({kode_barang} - {nama_barang}): "
                        f"Jumlah harus lebih dari 0!"
                    )

            # Jika ada error validasi, return error
            if error_messages:
                cur.close()
                conn.close()
                return jsonify({
                    "error": True, 
                    "message": "Validasi stok gagal:\n" + "\n".join(error_messages)
                }), 400

            # ===== PROSES TRANSAKSI =====
            # Simpan header penjualan dengan id_petugas dan informasi pembeli
            cur.execute("""
                INSERT INTO penjualan 
                (tanggal, id_petugas, nama_pembeli, nomor_telepon, metode_pembayaran, keterangan, total_harga)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (datetime.now(), session.get('user_id'), nama_pembeli or None, 
                  nomor_telepon or None, metode_pembayaran, keterangan or None, total_bayar))
            
            id_penjualan = cur.lastrowid
            faktur_items = []

            # Proses setiap item dengan FOR UPDATE untuk locking
            for item in items:
                id_detail = int(item.get("id_detail"))
                jumlah = int(item.get("jumlah", 0))
                harga_jual = int(item.get("harga_jual", 0))
                promo_persen = float(item.get("promo_persen", 0))
                diskon = int(item.get("diskon", 0))
                total = int(item.get("total", 0))

                # Lock row untuk update (mencegah race condition)
                cur.execute("""
                    SELECT db.id_barang, db.stok, db.harga_beli, b.kode_barang, b.nama_barang 
                    FROM detail_barang db
                    JOIN barang b ON db.id_barang = b.id_barang
                    WHERE db.id_detail = %s 
                    FOR UPDATE
                """, (id_detail,))
                
                row = cur.fetchone()
                
                if not row:
                    raise ValueError(f"Detail barang ID {id_detail} tidak ditemukan")

                id_barang = row["id_barang"]
                stok_sekarang = int(row["stok"] or 0)
                harga_beli = int(row["harga_beli"] or 0)

                # VALIDASI ULANG dengan lock (double check)
                if stok_sekarang < jumlah:
                    raise ValueError(
                        f"Stok barang '{row['nama_barang']}' tidak cukup! "
                        f"Tersedia: {stok_sekarang}, Diminta: {jumlah}"
                    )

                # Update stok (kurangi)
                cur.execute("""
                    UPDATE detail_barang 
                    SET stok = stok - %s 
                    WHERE id_detail = %s
                """, (jumlah, id_detail))

                # Hitung subtotal (tanpa diskon)
                subtotal_item = jumlah * harga_jual

                # Insert detail penjualan
                cur.execute("""
                    INSERT INTO detail_penjualan 
                    (id_penjualan, id_detail, jumlah, subtotal, diskon, total)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id_penjualan, id_detail, jumlah, subtotal_item, diskon, total))

                # Prepare data untuk faktur
                faktur_items.append({
                    "kode": row["kode_barang"],
                    "nama": row["nama_barang"],
                    "jumlah": jumlah,
                    "unit": "pcs",
                    "harga": harga_jual,
                    "disc": f"{promo_persen}%" if promo_persen > 0 else "0%",
                    "subtotal": total,
                    "pajak": "0%"
                })

                # Sinkron harga jual tertinggi
                sinkron_harga_jual(conn, id_barang)

            # Commit transaksi
            conn.commit()
            cur.close()
            conn.close()

            # ===== GENERATE FAKTUR =====
            nomor_faktur = buat_nomor_faktur("penjualan")
            tanggal_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            terbilang = angka_ke_terbilang(total_bayar).capitalize() + " Rupiah"

            # Data pelanggan untuk faktur
            kepada = nama_pembeli if nama_pembeli else "Customer"
            up = nomor_telepon if nomor_telepon else "-"

            html_faktur = render_template("faktur.html",
                                         tipe="penjualan",
                                         nomor_faktur=nomor_faktur,
                                         tanggal=tanggal_str,
                                         kepada=kepada,
                                         up=up,
                                         alamat="-",
                                         pengiriman=metode_pembayaran,
                                         nomor_po="-",
                                         mata_uang="IDR",
                                         term="Cash",
                                         dikirim_ke="-",
                                         items=faktur_items,
                                         terbilang=terbilang,
                                         penerima="-",
                                         nama_petugas=session.get('nama_petugas'),
                                         total=total_bayar,
                                         total_pajak=0,
                                         biaya_kirim=0,
                                         dibayar=total_bayar,
                                         saldo=0)

            id_faktur = simpan_faktur("penjualan", id_penjualan, nomor_faktur, 
                                     datetime.now(), kepada, total_bayar, html_faktur)

            return jsonify({
                "error": False, 
                "message": "✅ Transaksi penjualan berhasil disimpan!", 
                "id_penjualan": id_penjualan, 
                "id_faktur": id_faktur, 
                "nomor_faktur": nomor_faktur,
                "redirect_url": url_for('lihat_faktur', id_faktur=id_faktur)
            })

        except ValueError as ve:
            # Error validasi bisnis
            return jsonify({"error": True, "message": str(ve)}), 400
            
        except Exception as e:
            tb = traceback.format_exc()
            print("ERROR PENJUALAN:")
            print(tb)
            return jsonify({
                "error": True, 
                "message": f"Terjadi kesalahan: {str(e)}", 
                "trace": tb
            }), 500

    return render_template("penjualan.html", datetime=datetime, nama_petugas=session.get('nama_petugas'))

# ===============================
# ===== Lihat riwayat faktur ====
# ===============================
@app.route("/faktur/history")
@login_required
def faktur_history():
    tipe = request.args.get("tipe")
    conn = get_db_faktur()
    cur = conn.cursor(dictionary=True)
    try:
        if tipe in ("pembelian", "penjualan"):
            cur.execute("""
                SELECT id_faktur, tipe, ref_id, nomor_faktur, tanggal, pelanggan, total, created_at 
                FROM faktur_master 
                WHERE tipe = %s 
                ORDER BY tanggal DESC
            """, (tipe,))
        else:
            cur.execute("""
                SELECT id_faktur, tipe, ref_id, nomor_faktur, tanggal, pelanggan, total, created_at 
                FROM faktur_master 
                ORDER BY tanggal DESC
            """)
        
        rows = cur.fetchall()
        
        for r in rows:
            if isinstance(r.get("tanggal"), datetime):
                r["tanggal"] = r["tanggal"].strftime("%d/%m/%Y %H:%M:%S")
            if isinstance(r.get("created_at"), datetime):
                r["created_at"] = r["created_at"].strftime("%d/%m/%Y %H:%M:%S")
            r["total"] = int(r.get("total", 0))
        
        return render_template("faktur_history.html", fakturs=rows, tipe_filter=tipe, nama_petugas=session.get('nama_petugas'))
    finally:
        cur.close()
        conn.close()

# ===============================
# ===== Lihat faktur spesifik ===
# ===============================
@app.route("/faktur/view/<int:id_faktur>")
@login_required
def lihat_faktur(id_faktur):
    conn = get_db_faktur()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM faktur_master WHERE id_faktur = %s", (id_faktur,))
        row = cur.fetchone()
        if not row:
            return "Faktur tidak ditemukan", 404
        
        if row.get("html"):
            return row["html"]
        
        return render_template("faktur.html", 
                             tipe=row["tipe"], 
                             nomor_faktur=row["nomor_faktur"], 
                             tanggal=row["tanggal"], 
                             items=[], 
                             total=row["total"],
                             nama_petugas=session.get('nama_petugas'))
    finally:
        cur.close()
        conn.close()

# ===============================
# ===== Edit Stok Barang ========
# ===============================
@app.route("/update_stok", methods=["POST"])
@login_required
def update_stok():
    try:
        data = request.get_json(force=True)
        id_detail = int(data["id_detail"])
        harga_beli = float(data["harga_beli"])
        margin = float(data["margin"])
        harga_jual = float(data["harga_jual"])
        stok = int(data["stok"])

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
# ===== Hapus Stok Barang ========  
@app.route("/hapus_stok/<int:id_detail>", methods=["DELETE"])
@login_required
def hapus_stok(id_detail):
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)

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
@login_required
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

        for row in data_stok:
            row["harga_beli"] = int(round(float(row["harga_beli"] or 0)))
            row["harga_jual"] = int(round(float(row["harga_jual"] or 0)))
            row["margin"] = round(float(row["margin"] or 0), 2)
            row["stok"] = int(row["stok"] or 0)

        return render_template("stok.html", data_stok=data_stok, datetime=datetime, nama_petugas=session.get('nama_petugas'))
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== Hapus Faktur ============
# ===============================
@app.route("/faktur/delete/<int:id_faktur>", methods=["DELETE"])
@login_required
def hapus_faktur(id_faktur):
    try:
        conn = get_db_faktur()
        cur = conn.cursor(dictionary=True)

        # Pastikan faktur ada
        cur.execute("SELECT * FROM faktur_master WHERE id_faktur = %s", (id_faktur,))
        faktur = cur.fetchone()

        if not faktur:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Faktur tidak ditemukan"}), 404

        # Hapus faktur
        cur.execute("DELETE FROM faktur_master WHERE id_faktur = %s", (id_faktur,))
        conn.commit()

        cur.close()
        conn.close()
        return jsonify({"error": False, "message": f"Faktur {faktur['nomor_faktur']} berhasil dihapus!"})

    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500
    
# ===============================
# ===== API List Barang =========
# ===============================
@app.route("/api/list_barang")
@login_required
def list_barang():
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # ✅ QUERY YANG BENAR - INCLUDE BARCODE
        cur.execute("""
            SELECT 
                b.id_barang,
                b.kode_barang,
                b.nama_barang,
                b.barcode,
                COALESCE(MAX(d.harga_jual), 0) as harga_jual_tertinggi,
                COALESCE(SUM(d.stok), 0) as total_stok
            FROM barang b
            LEFT JOIN detail_barang d ON b.id_barang = d.id_barang
            GROUP BY b.id_barang, b.kode_barang, b.nama_barang, b.barcode
            ORDER BY b.nama_barang ASC
        """)
        barang = cur.fetchall()
        cur.close()
        conn.close()
        
        # ✅ CONVERT DATA DAN PRINT DEBUG
        print("\n===== DEBUG LIST BARANG =====")
        for item in barang:
            print(f"Kode: {item['kode_barang']}, Nama: {item['nama_barang']}, Barcode: {item['barcode']}")
            
            item['harga_jual_tertinggi'] = int(item['harga_jual_tertinggi'] or 0)
            item['total_stok'] = int(item['total_stok'] or 0)
            
            # ✅ PENTING: Convert barcode ke string atau None
            if item['barcode']:
                item['barcode'] = str(item['barcode'])
            else:
                item['barcode'] = None
        
        print(f"Total barang: {len(barang)}")
        print("=============================\n")
        
        return jsonify({"error": False, "barang": barang})
        
    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR di list_barang:")
        print(tb)
        return jsonify({"error": True, "message": str(e)}), 500


# ===============================
# ===== Halaman Master Data =====
# ===============================
@app.route("/master-data")
@login_required
def master_data():
    return render_template("master_data.html", nama_petugas=session.get('nama_petugas'))

# ===== ROUTE MASTER DATA DETAIL =====
@app.route("/master/supplier")
@login_required
def master_supplier():
    return render_template("master_supplier.html", nama_petugas=session.get('nama_petugas'))

@app.route("/master/customer")
@login_required
def master_customer():
    return render_template("master_customer.html", nama_petugas=session.get('nama_petugas'))

@app.route("/master/kategori")
@login_required
def master_kategori():
    return render_template("master_kategori.html", nama_petugas=session.get('nama_petugas'))

@app.route("/master/petugas")
@login_required
def master_petugas():
    return render_template("master_petugas.html", nama_petugas=session.get('nama_petugas'))

@app.route("/master/barang")
@login_required
def master_barang():
    return render_template("data_barang.html", nama_petugas=session.get('nama_petugas'))

# ===============================
# ===== Laporan Laba Rugi =======
# ===============================
@app.route("/laporan")
@login_required
def laporan():
    return render_template("laporan_laba_rugi.html", nama_petugas=session.get('nama_petugas'))

# ===============================
# ===== API Laba Rugi Detail ====
# ===== (FIFO Method - Akurat) ==
# ===============================
@app.route("/api/laba_rugi")
@login_required
def api_laba_rugi():
    try:
        periode = request.args.get('periode', 'bulan')  # hari, bulan, tahun, semua
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        now = datetime.now()

        # Tentukan filter tanggal berdasarkan periode
        if periode == 'hari':
            tanggal_filter = now.date()
            where_clause = "WHERE DATE(p.tanggal) = %s"
            params = (tanggal_filter,)
            periode_text = now.strftime('%d %B %Y')
        elif periode == 'bulan':
            tanggal_filter = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            where_clause = "WHERE p.tanggal >= %s"
            params = (tanggal_filter,)
            periode_text = now.strftime('%B %Y')
        elif periode == 'tahun':
            tanggal_filter = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            where_clause = "WHERE p.tanggal >= %s"
            params = (tanggal_filter,)
            periode_text = now.strftime('Tahun %Y')
        else:
            where_clause = ""
            params = ()
            periode_text = "Semua Periode"

        # Ambil data penjualan per kode_barang
        query = f"""
            SELECT 
                b.kode_barang,
                b.nama_barang,
                SUM(dp.jumlah) as jumlah_terjual,
                MAX(db.harga_jual) as harga_jual_tertinggi,
                SUM(db.harga_beli * dp.jumlah) as hpp,
                SUM(dp.diskon) as total_promo
            FROM detail_penjualan dp
            JOIN penjualan p ON dp.id_penjualan = p.id_penjualan
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            JOIN barang b ON db.id_barang = b.id_barang
            {where_clause}
            GROUP BY b.kode_barang, b.nama_barang
            ORDER BY b.nama_barang ASC
        """
        cur.execute(query, params)
        rows = cur.fetchall()

        # Hitung pendapatan_max, max_profit, laba_bersih per kode_barang
        detail = []
        total_hpp = 0
        total_pendapatan_max = 0
        total_max_profit = 0
        total_promo = 0
        total_laba_bersih = 0

        for r in rows:
            kode_barang = r['kode_barang']
            nama_barang = r['nama_barang']
            jumlah_terjual = int(r['jumlah_terjual'] or 0)
            harga_jual_tertinggi = int(r['harga_jual_tertinggi'] or 0)
            hpp = int(r['hpp'] or 0)
            total_diskon = int(r['total_promo'] or 0)

            pendapatan_max = jumlah_terjual * harga_jual_tertinggi
            max_profit = pendapatan_max - hpp
            laba_bersih = max_profit - total_diskon

            detail.append({
                "kode_barang": kode_barang,
                "nama_barang": nama_barang,
                "jumlah_terjual": jumlah_terjual,
                "harga_jual_tertinggi": harga_jual_tertinggi,
                "hpp": hpp,
                "pendapatan_max": pendapatan_max,
                "max_profit": max_profit,
                "promo": total_diskon,
                "laba_bersih": laba_bersih
            })

            total_hpp += hpp
            total_pendapatan_max += pendapatan_max
            total_max_profit += max_profit
            total_promo += total_diskon
            total_laba_bersih += laba_bersih

        cur.close()
        conn.close()

        return jsonify({
            "error": False,
            "periode": periode,
            "periode_text": periode_text,
            "summary": {
                "total_hpp": total_hpp,
                "total_pendapatan_max": total_pendapatan_max,
                "total_max_profit": total_max_profit,
                "total_promo": total_promo,
                "total_laba_bersih": total_laba_bersih
            },
            "detail": detail
        })

    except Exception as e:
        tb = traceback.format_exc()
        print("❌ ERROR API LABA RUGI:")
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500


# ===============================
# ===== Helper: Generate Kode Supplier
# ===============================
def generate_kode_supplier():
    """Generate kode supplier unik dengan format SUP-XXXXXX"""
    conn = get_db()
    cur = conn.cursor()
    
    while True:
        # Generate random 6 digit alphanumeric
        random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        kode = f"SUP-{random_code}"
        
        # Check if code already exists
        cur.execute("SELECT COUNT(*) FROM supplier WHERE kode_supplier = %s", (kode,))
        if cur.fetchone()[0] == 0:
            cur.close()
            conn.close()
            return kode

# ===============================
# ===== API LIST SUPPLIER =======
# ===============================
@app.route("/api/supplier", methods=["GET"])
@login_required
def api_list_supplier():
    """Get list semua supplier dengan statistik"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Get all suppliers
        cur.execute("""
            SELECT 
                id_supplier,
                kode_supplier,
                nama_supplier,
                nama_kontak,
                telepon,
                email,
                alamat,
                keterangan,
                status,
                dibuat_pada,
                diperbarui_pada
            FROM supplier
            ORDER BY nama_supplier ASC
        """)
        suppliers = cur.fetchall()
        
        # Convert datetime to string
        for s in suppliers:
            if s.get('dibuat_pada'):
                s['dibuat_pada'] = s['dibuat_pada'].strftime('%Y-%m-%d %H:%M:%S')
            if s.get('diperbarui_pada'):
                s['diperbarui_pada'] = s['diperbarui_pada'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Get statistics
        # Total supplier
        total_supplier = len(suppliers)
        
        # Supplier aktif
        supplier_aktif = len([s for s in suppliers if s['status'] == 'aktif'])
        
        # Transaksi bulan ini
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cur.execute("""
            SELECT COUNT(*) as total
            FROM pembelian
            WHERE tanggal >= %s AND id_supplier IS NOT NULL
        """, (current_month_start,))
        transaksi_bulan_ini = cur.fetchone()['total']
        
        # Supplier baru (bulan ini)
        cur.execute("""
            SELECT COUNT(*) as total
            FROM supplier
            WHERE dibuat_pada >= %s
        """, (current_month_start,))
        supplier_baru = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "suppliers": suppliers,
            "stats": {
                "total": total_supplier,
                "aktif": supplier_aktif,
                "transaksi_bulan_ini": transaksi_bulan_ini,
                "supplier_baru": supplier_baru
            }
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API GET SUPPLIER BY ID ==
# ===============================
@app.route("/api/supplier/<int:id_supplier>", methods=["GET"])
@login_required
def api_get_supplier(id_supplier):
    """Get detail supplier by ID"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT 
                id_supplier,
                kode_supplier,
                nama_supplier,
                nama_kontak,
                telepon,
                email,
                alamat,
                keterangan,
                status,
                dibuat_pada,
                diperbarui_pada
            FROM supplier
            WHERE id_supplier = %s
        """, (id_supplier,))
        
        supplier = cur.fetchone()
        cur.close()
        conn.close()
        
        if not supplier:
            return jsonify({"error": True, "message": "Supplier tidak ditemukan"}), 404
        
        # Convert datetime to string
        if supplier.get('dibuat_pada'):
            supplier['dibuat_pada'] = supplier['dibuat_pada'].strftime('%Y-%m-%d %H:%M:%S')
        if supplier.get('diperbarui_pada'):
            supplier['diperbarui_pada'] = supplier['diperbarui_pada'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "error": False,
            **supplier
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API TAMBAH SUPPLIER =====
# ===============================
@app.route("/api/supplier", methods=["POST"])
@login_required
def api_tambah_supplier():
    """Tambah supplier baru"""
    try:
        data = request.get_json(force=True)
        
        # Validasi input
        kode_supplier = data.get("kode_supplier", "").strip()
        nama_supplier = data.get("nama_supplier", "").strip()
        nama_kontak = data.get("nama_kontak", "").strip()
        telepon = data.get("telepon", "").strip()
        email = data.get("email", "").strip()
        alamat = data.get("alamat", "").strip()
        keterangan = data.get("keterangan", "").strip()
        status = data.get("status", "aktif")
        
        # Validasi wajib
        if not nama_supplier:
            return jsonify({"error": True, "message": "Nama supplier wajib diisi!"}), 400
        
        if not telepon:
            return jsonify({"error": True, "message": "Telepon wajib diisi!"}), 400
        
        if len(telepon) < 10 or len(telepon) > 15:
            return jsonify({"error": True, "message": "Nomor telepon tidak valid (10-15 digit)!"}), 400
        
        if not alamat:
            return jsonify({"error": True, "message": "Alamat wajib diisi!"}), 400
        
        # Validasi email jika diisi
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({"error": True, "message": "Format email tidak valid!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Generate kode jika tidak diisi
        if not kode_supplier:
            kode_supplier = generate_kode_supplier()
        else:
            # Cek apakah kode sudah digunakan
            cur.execute("SELECT COUNT(*) as total FROM supplier WHERE kode_supplier = %s", (kode_supplier,))
            if cur.fetchone()['total'] > 0:
                cur.close()
                conn.close()
                return jsonify({"error": True, "message": f"Kode supplier '{kode_supplier}' sudah digunakan!"}), 400
        
        # Insert supplier
        cur.execute("""
            INSERT INTO supplier 
            (kode_supplier, nama_supplier, nama_kontak, telepon, email, alamat, keterangan, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (kode_supplier, nama_supplier, nama_kontak or None, telepon, 
              email or None, alamat, keterangan or None, status))
        
        id_supplier = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Supplier berhasil ditambahkan!",
            "id_supplier": id_supplier,
            "kode_supplier": kode_supplier
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API UPDATE SUPPLIER =====
# ===============================
@app.route("/api/supplier/<int:id_supplier>", methods=["PUT"])
@login_required
def api_update_supplier(id_supplier):
    """Update data supplier"""
    try:
        data = request.get_json(force=True)
        
        # Validasi input
        kode_supplier = data.get("kode_supplier", "").strip()
        nama_supplier = data.get("nama_supplier", "").strip()
        nama_kontak = data.get("nama_kontak", "").strip()
        telepon = data.get("telepon", "").strip()
        email = data.get("email", "").strip()
        alamat = data.get("alamat", "").strip()
        keterangan = data.get("keterangan", "").strip()
        status = data.get("status", "aktif")
        
        # Validasi wajib
        if not kode_supplier:
            return jsonify({"error": True, "message": "Kode supplier wajib diisi!"}), 400
        
        if not nama_supplier:
            return jsonify({"error": True, "message": "Nama supplier wajib diisi!"}), 400
        
        if not telepon:
            return jsonify({"error": True, "message": "Telepon wajib diisi!"}), 400
        
        if len(telepon) < 10 or len(telepon) > 15:
            return jsonify({"error": True, "message": "Nomor telepon tidak valid (10-15 digit)!"}), 400
        
        if not alamat:
            return jsonify({"error": True, "message": "Alamat wajib diisi!"}), 400
        
        # Validasi email jika diisi
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({"error": True, "message": "Format email tidak valid!"}), 400
        
        # Validasi status
        if status not in ['aktif', 'nonaktif']:
            return jsonify({
                "error": True, 
                "message": "Status tidak valid! Pilih: aktif atau nonaktif"
            }), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah supplier exists
        cur.execute("SELECT id_supplier FROM supplier WHERE id_supplier = %s", (id_supplier,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Supplier tidak ditemukan!"}), 404
        
        # Cek apakah kode sudah digunakan supplier lain
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM supplier 
            WHERE kode_supplier = %s AND id_supplier != %s
        """, (kode_supplier, id_supplier))
        
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": f"Kode supplier '{kode_supplier}' sudah digunakan supplier lain!"}), 400
        
        # Cek apakah nama sudah digunakan supplier lain
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM supplier 
            WHERE nama_supplier = %s AND id_supplier != %s
        """, (nama_supplier, id_supplier))
        
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": f"Nama supplier '{nama_supplier}' sudah digunakan supplier lain!"}), 400
        
        # Update supplier
        cur.execute("""
            UPDATE supplier SET
                kode_supplier = %s,
                nama_supplier = %s,
                nama_kontak = %s,
                telepon = %s,
                email = %s,
                alamat = %s,
                keterangan = %s,
                status = %s
            WHERE id_supplier = %s
        """, (kode_supplier, nama_supplier, nama_kontak or None, telepon, 
              email or None, alamat, keterangan or None, status, id_supplier))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Supplier berhasil diupdate!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API HAPUS SUPPLIER ======
# ===============================
@app.route("/api/supplier/<int:id_supplier>", methods=["DELETE"])
@login_required
def api_hapus_supplier(id_supplier):
    """Hapus supplier"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah supplier exists
        cur.execute("""
            SELECT kode_supplier, nama_supplier 
            FROM supplier 
            WHERE id_supplier = %s
        """, (id_supplier,))
        
        supplier = cur.fetchone()
        if not supplier:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Supplier tidak ditemukan!"}), 404
        
        # Cek apakah supplier punya transaksi pembelian
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM pembelian 
            WHERE id_supplier = %s
        """, (id_supplier,))
        
        total_transaksi = cur.fetchone()['total']
        
        if total_transaksi > 0:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Supplier '{supplier['nama_supplier']}' tidak bisa dihapus karena memiliki {total_transaksi} transaksi pembelian!"
            }), 400
        
        # Hapus supplier
        cur.execute("DELETE FROM supplier WHERE id_supplier = %s", (id_supplier,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": f"✅ Supplier '{supplier['nama_supplier']}' berhasil dihapus!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500
# Tambahkan setelah API Supplier

# ===============================
# ===== Helper: Generate Kode Customer
# ===============================
def generate_kode_customer():
    """Generate kode customer unik dengan format CUST-XXXXXX"""
    conn = get_db()
    cur = conn.cursor()
    
    while True:
        # Generate random 6 digit alphanumeric
        random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        kode = f"CUST-{random_code}"
        
        # Check if code already exists
        cur.execute("SELECT COUNT(*) FROM customer WHERE kode_customer = %s", (kode,))
        if cur.fetchone()[0] == 0:
            cur.close()
            conn.close()
            return kode

# ===============================
# ===== API LIST CUSTOMER =======
# ===============================
@app.route("/api/customer", methods=["GET"])
@login_required
def api_list_customer():
    """Get list semua customer dengan statistik"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Get all customers
        cur.execute("""
            SELECT 
                id_customer,
                kode_customer,
                nama_customer,
                telepon,
                email,
                alamat,
                tipe,
                catatan,
                status,
                dibuat_pada,
                diperbarui_pada
            FROM customer
            ORDER BY nama_customer ASC
        """)
        customers = cur.fetchall()
        
        # Convert datetime to string
        for c in customers:
            if c.get('dibuat_pada'):
                c['dibuat_pada'] = c['dibuat_pada'].strftime('%Y-%m-%d %H:%M:%S')
            if c.get('diperbarui_pada'):
                c['diperbarui_pada'] = c['diperbarui_pada'].strftime('%Y-%m-%d %H:%M:%S')
        
        # Get statistics
        # Total customer
        total_customer = len(customers)
        
        # Customer aktif
        customer_aktif = len([c for c in customers if c['status'] == 'aktif'])
        
        # Customer VIP
        customer_vip = len([c for c in customers if c['tipe'] == 'vip'])
        
        # Customer baru (bulan ini)
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cur.execute("""
            SELECT COUNT(*) as total
            FROM customer
            WHERE dibuat_pada >= %s
        """, (current_month_start,))
        customer_baru = cur.fetchone()['total']
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "customers": customers,
            "stats": {
                "total": total_customer,
                "aktif": customer_aktif,
                "vip": customer_vip,
                "baru": customer_baru
            }
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API GET CUSTOMER BY ID ==
# ===============================
@app.route("/api/customer/<int:id_customer>", methods=["GET"])
@login_required
def api_get_customer(id_customer):
    """Get detail customer by ID"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT 
                id_customer,
                kode_customer,
                nama_customer,
                telepon,
                email,
                alamat,
                tipe,
                catatan,
                status,
                dibuat_pada,
                diperbarui_pada
            FROM customer
            WHERE id_customer = %s
        """, (id_customer,))
        
        customer = cur.fetchone()
        cur.close()
        conn.close()
        
        if not customer:
            return jsonify({"error": True, "message": "Customer tidak ditemukan"}), 404
        
        # Convert datetime to string
        if customer.get('dibuat_pada'):
            customer['dibuat_pada'] = customer['dibuat_pada'].strftime('%Y-%m-%d %H:%M:%S')
        if customer.get('diperbarui_pada'):
            customer['diperbarui_pada'] = customer['diperbarui_pada'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "error": False,
            **customer
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API TAMBAH CUSTOMER =====
# ===============================
@app.route("/api/customer", methods=["POST"])
@login_required
def api_tambah_customer():
    """Tambah customer baru"""
    try:
        data = request.get_json(force=True)
        
        # Validasi input
        kode_customer = data.get("kode_customer", "").strip()
        nama_customer = data.get("nama_customer", "").strip()
        telepon = data.get("telepon", "").strip()
        email = data.get("email", "").strip()
        alamat = data.get("alamat", "").strip()
        tipe = data.get("tipe", "reguler")
        catatan = data.get("catatan", "").strip()
        status = data.get("status", "aktif")
        
        # Validasi wajib
        if not nama_customer:
            return jsonify({"error": True, "message": "Nama customer wajib diisi!"}), 400
        
        if not telepon:
            return jsonify({"error": True, "message": "Telepon wajib diisi!"}), 400
        
        if len(telepon) < 10 or len(telepon) > 15:
            return jsonify({"error": True, "message": "Nomor telepon tidak valid (10-15 digit)!"}), 400
        
        # Validasi email jika diisi
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({"error": True, "message": "Format email tidak valid!"}), 400
        
        # Validasi tipe
        if tipe not in ['reguler', 'member', 'vip']:
            return jsonify({"error": True, "message": "Tipe customer tidak valid!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Generate kode jika tidak diisi
        if not kode_customer:
            kode_customer = generate_kode_customer()
        else:
            # Cek apakah kode sudah digunakan
            cur.execute("SELECT COUNT(*) as total FROM customer WHERE kode_customer = %s", (kode_customer,))
            if cur.fetchone()['total'] > 0:
                cur.close()
                conn.close()
                return jsonify({"error": True, "message": f"Kode customer '{kode_customer}' sudah digunakan!"}), 400
        
        # Insert customer
        cur.execute("""
            INSERT INTO customer 
            (kode_customer, nama_customer, telepon, email, alamat, tipe, catatan, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (kode_customer, nama_customer, telepon, email or None, 
              alamat or None, tipe, catatan or None, status))
        
        id_customer = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Customer berhasil ditambahkan!",
            "id_customer": id_customer,
            "kode_customer": kode_customer
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API UPDATE CUSTOMER =====
# ===============================
@app.route("/api/customer/<int:id_customer>", methods=["PUT"])
@login_required
def api_update_customer(id_customer):
    """Update data customer"""
    try:
        data = request.get_json(force=True)
        
        # Validasi input
        kode_customer = data.get("kode_customer", "").strip()
        nama_customer = data.get("nama_customer", "").strip()
        telepon = data.get("telepon", "").strip()
        email = data.get("email", "").strip()
        alamat = data.get("alamat", "").strip()
        tipe = data.get("tipe", "reguler")
        catatan = data.get("catatan", "").strip()
        status = data.get("status", "aktif")
        
        # Validasi wajib
        if not kode_customer:
            return jsonify({"error": True, "message": "Kode customer wajib diisi!"}), 400
        
        if not nama_customer:
            return jsonify({"error": True, "message": "Nama customer wajib diisi!"}), 400
        
        if not telepon:
            return jsonify({"error": True, "message": "Telepon wajib diisi!"}), 400
        
        if len(telepon) < 10 or len(telepon) > 15:
            return jsonify({"error": True, "message": "Nomor telepon tidak valid (10-15 digit)!"}), 400
        
        # Validasi email jika diisi
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({"error": True, "message": "Format email tidak valid!"}), 400
        
        # Validasi tipe
        if tipe not in ['reguler', 'member', 'vip']:
            return jsonify({"error": True, "message": "Tipe customer tidak valid!"}), 400
        
        # Validasi status
        if status not in ['aktif', 'nonaktif']:
            return jsonify({"error": True, "message": "Status tidak valid!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah customer exists
        cur.execute("SELECT id_customer FROM customer WHERE id_customer = %s", (id_customer,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Customer tidak ditemukan!"}), 404
        
        # Cek apakah kode sudah digunakan customer lain
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM customer 
            WHERE kode_customer = %s AND id_customer != %s
        """, (kode_customer, id_customer))
        
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": f"Kode customer '{kode_customer}' sudah digunakan customer lain!"}), 400
        
        # Cek apakah nama sudah digunakan customer lain
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM customer 
            WHERE nama_customer = %s AND id_customer != %s
        """, (nama_customer, id_customer))
        
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": f"Nama customer '{nama_customer}' sudah digunakan customer lain!"}), 400
        
        # Update customer
        cur.execute("""
            UPDATE customer SET
                kode_customer = %s,
                nama_customer = %s,
                telepon = %s,
                email = %s,
                alamat = %s,
                tipe = %s,
                catatan = %s,
                status = %s
            WHERE id_customer = %s
        """, (kode_customer, nama_customer, telepon, email or None, 
              alamat or None, tipe, catatan or None, status, id_customer))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Customer berhasil diupdate!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API HAPUS CUSTOMER ======
# ===============================
@app.route("/api/customer/<int:id_customer>", methods=["DELETE"])
@login_required
def api_hapus_customer(id_customer):
    """Hapus customer"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah customer exists
        cur.execute("""
            SELECT kode_customer, nama_customer 
            FROM customer 
            WHERE id_customer = %s
        """, (id_customer,))
        
        customer = cur.fetchone()
        if not customer:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Customer tidak ditemukan!"}), 404
        
        # Cek apakah customer punya transaksi penjualan
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM penjualan 
            WHERE id_customer = %s
        """, (id_customer,))
        
        total_transaksi = cur.fetchone()['total']
        
        if total_transaksi > 0:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Customer '{customer['nama_customer']}' tidak bisa dihapus karena memiliki {total_transaksi} transaksi penjualan!"
            }), 400
        
        # Hapus customer
        cur.execute("DELETE FROM customer WHERE id_customer = %s", (id_customer,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": f"✅ Customer '{customer['nama_customer']}' berhasil dihapus!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500
    
# Tambahkan setelah API Customer

# ===============================
# ===== Helper: Generate Kode Kategori
# ===============================
def generate_kode_kategori():
    """Generate kode kategori unik dengan format KAT-XXX"""
    conn = get_db()
    cur = conn.cursor()
    
    # Cari nomor urut terakhir
    cur.execute("SELECT kode_kategori FROM kategori WHERE kode_kategori LIKE 'KAT-%' ORDER BY kode_kategori DESC LIMIT 1")
    last = cur.fetchone()
    
    if last:
        # Extract nomor dari kode terakhir
        try:
            last_num = int(last[0].split('-')[1])
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1
    
    kode = f"KAT-{new_num:03d}"
    
    cur.close()
    conn.close()
    return kode

# ===============================
# ===== API LIST KATEGORI =======
# ===============================
@app.route("/api/kategori", methods=["GET"])
@login_required
def api_list_kategori():
    """Get list semua kategori dengan jumlah produk"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Get all categories with product count
        cur.execute("""
            SELECT 
                k.id_kategori,
                k.kode_kategori,
                k.nama_kategori,
                k.icon_kategori,
                k.deskripsi,
                k.dibuat_pada,
                k.diperbarui_pada,
                COUNT(b.id_barang) as jumlah_produk
            FROM kategori k
            LEFT JOIN barang b ON k.id_kategori = b.id_kategori
            GROUP BY k.id_kategori, k.kode_kategori, k.nama_kategori, k.icon_kategori, 
                     k.deskripsi, k.dibuat_pada, k.diperbarui_pada
            ORDER BY k.nama_kategori ASC
        """)
        kategoris = cur.fetchall()
        
        # Convert datetime to string
        for kat in kategoris:
            if kat.get('dibuat_pada'):
                kat['dibuat_pada'] = kat['dibuat_pada'].strftime('%Y-%m-%d %H:%M:%S')
            if kat.get('diperbarui_pada'):
                kat['diperbarui_pada'] = kat['diperbarui_pada'].strftime('%Y-%m-%d %H:%M:%S')
            kat['jumlah_produk'] = int(kat['jumlah_produk'] or 0)
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "kategoris": kategoris,
            "total": len(kategoris)
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API GET KATEGORI BY ID ==
# ===============================
@app.route("/api/kategori/<int:id_kategori>", methods=["GET"])
@login_required
def api_get_kategori(id_kategori):
    """Get detail kategori by ID"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT 
                k.id_kategori,
                k.kode_kategori,
                k.nama_kategori,
                k.icon_kategori,
                k.deskripsi,
                k.dibuat_pada,
                k.diperbarui_pada,
                COUNT(b.id_barang) as jumlah_produk
            FROM kategori k
            LEFT JOIN barang b ON k.id_kategori = b.id_kategori
            WHERE k.id_kategori = %s
            GROUP BY k.id_kategori, k.kode_kategori, k.nama_kategori, k.icon_kategori, 
                     k.deskripsi, k.dibuat_pada, k.diperbarui_pada
        """, (id_kategori,))
        
        kategori = cur.fetchone()
        cur.close()
        conn.close()
        
        if not kategori:
            return jsonify({"error": True, "message": "Kategori tidak ditemukan"}), 404
        
        # Convert datetime to string
        if kategori.get('dibuat_pada'):
            kategori['dibuat_pada'] = kategori['dibuat_pada'].strftime('%Y-%m-%d %H:%M:%S')
        if kategori.get('diperbarui_pada'):
            kategori['diperbarui_pada'] = kategori['diperbarui_pada'].strftime('%Y-%m-%d %H:%M:%S')
        kategori['jumlah_produk'] = int(kategori['jumlah_produk'] or 0)
        
        return jsonify({
            "error": False,
            **kategori
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API TAMBAH KATEGORI =====
# ===============================
@app.route("/api/kategori", methods=["POST"])
@login_required
def api_tambah_kategori():
    """Tambah kategori baru"""
    try:
        data = request.get_json(force=True)
        
        # Validasi input
        kode_kategori = data.get("kode_kategori", "").strip()
        nama_kategori = data.get("nama_kategori", "").strip()
        icon_kategori = data.get("icon_kategori", "").strip()
        deskripsi = data.get("deskripsi", "").strip()
        
        # Validasi wajib
        if not nama_kategori:
            return jsonify({"error": True, "message": "Nama kategori wajib diisi!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Generate kode jika tidak diisi
        if not kode_kategori:
            kode_kategori = generate_kode_kategori()
        else:
            # Cek apakah kode sudah digunakan
            cur.execute("SELECT COUNT(*) as total FROM kategori WHERE kode_kategori = %s", (kode_kategori,))
            if cur.fetchone()['total'] > 0:
                cur.close()
                conn.close()
                return jsonify({"error": True, "message": f"Kode kategori '{kode_kategori}' sudah digunakan!"}), 400
        
        # Cek apakah nama sudah digunakan
        cur.execute("SELECT COUNT(*) as total FROM kategori WHERE nama_kategori = %s", (nama_kategori,))
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": f"Nama kategori '{nama_kategori}' sudah digunakan!"}), 400
        
        # Insert kategori
        cur.execute("""
            INSERT INTO kategori 
            (kode_kategori, nama_kategori, icon_kategori, deskripsi)
            VALUES (%s, %s, %s, %s)
        """, (kode_kategori, nama_kategori, icon_kategori or None, deskripsi or None))
        
        id_kategori = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Kategori berhasil ditambahkan!",
            "id_kategori": id_kategori,
            "kode_kategori": kode_kategori
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API UPDATE KATEGORI =====
# ===============================
@app.route("/api/kategori/<int:id_kategori>", methods=["PUT"])
@login_required
def api_update_kategori(id_kategori):
    """Update data kategori"""
    try:
        data = request.get_json(force=True)
        
        # Validasi input
        kode_kategori = data.get("kode_kategori", "").strip()
        nama_kategori = data.get("nama_kategori", "").strip()
        icon_kategori = data.get("icon_kategori", "").strip()
        deskripsi = data.get("deskripsi", "").strip()
        
        # Validasi wajib
        if not kode_kategori:
            return jsonify({"error": True, "message": "Kode kategori wajib diisi!"}), 400
        
        if not nama_kategori:
            return jsonify({"error": True, "message": "Nama kategori wajib diisi!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah kategori exists
        cur.execute("SELECT id_kategori FROM kategori WHERE id_kategori = %s", (id_kategori,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Kategori tidak ditemukan!"}), 404
        
        # Cek apakah kode sudah digunakan kategori lain
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM kategori 
            WHERE kode_kategori = %s AND id_kategori != %s
        """, (kode_kategori, id_kategori))
        
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": f"Kode kategori '{kode_kategori}' sudah digunakan kategori lain!"}), 400
        
        # Cek apakah nama sudah digunakan kategori lain
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM kategori 
            WHERE nama_kategori = %s AND id_kategori != %s
        """, (nama_kategori, id_kategori))
        
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": f"Nama kategori '{nama_kategori}' sudah digunakan kategori lain!"}), 400
        
        # Update kategori
        cur.execute("""
            UPDATE kategori SET
                kode_kategori = %s,
                nama_kategori = %s,
                icon_kategori = %s,
                deskripsi = %s
            WHERE id_kategori = %s
        """, (kode_kategori, nama_kategori, icon_kategori or None, 
              deskripsi or None, id_kategori))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Kategori berhasil diupdate!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API HAPUS KATEGORI ======
# ===============================
@app.route("/api/kategori/<int:id_kategori>", methods=["DELETE"])
@login_required
def api_hapus_kategori(id_kategori):
    """Hapus kategori"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah kategori exists
        cur.execute("""
            SELECT kode_kategori, nama_kategori 
            FROM kategori 
            WHERE id_kategori = %s
        """, (id_kategori,))
        
        kategori = cur.fetchone()
        if not kategori:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Kategori tidak ditemukan!"}), 404
        
        # Cek apakah kategori punya produk
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM barang 
            WHERE id_kategori = %s
        """, (id_kategori,))
        
        total_produk = cur.fetchone()['total']
        
        if total_produk > 0:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Kategori '{kategori['nama_kategori']}' tidak bisa dihapus karena memiliki {total_produk} produk!\n\nHapus atau pindahkan produk terlebih dahulu."
            }), 400
        
        # Hapus kategori
        cur.execute("DELETE FROM kategori WHERE id_kategori = %s", (id_kategori,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": f"✅ Kategori '{kategori['nama_kategori']}' berhasil dihapus!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API GET KATEGORI FOR SELECT
# ===============================
@app.route("/api/kategori/select", methods=["GET"])
@login_required
def api_kategori_select():
    """Get list kategori untuk dropdown/select"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT 
                id_kategori,
                kode_kategori,
                nama_kategori,
                icon_kategori
            FROM kategori
            ORDER BY nama_kategori ASC
        """)
        kategoris = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "kategoris": kategoris
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# Tambahkan di app.py setelah route /api/list_barang

# ===============================
# ===== API UPDATE BARANG =======
# ===============================
@app.route("/api/update_barang", methods=["POST"])
@login_required
def api_update_barang():
    """Update data barang (kode, nama, barcode)"""
    try:
        data = request.get_json(force=True)
        
        kode_barang_lama = data.get("kode_barang_lama", "").strip()
        kode_barang_baru = data.get("kode_barang_baru", "").strip()
        nama_barang = data.get("nama_barang", "").strip()
        barcode = data.get("barcode")
        
        if not kode_barang_lama or not kode_barang_baru or not nama_barang:
            return jsonify({"error": True, "message": "Data tidak lengkap!"}), 400
        
        # Validasi barcode jika diisi
        if barcode:
            barcode = barcode.strip()
            if not barcode.isdigit():
                return jsonify({"error": True, "message": "Barcode harus berupa angka!"}), 400
            
            if len(barcode) != 13:
                return jsonify({"error": True, "message": "Barcode harus 13 digit!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah barang exists
        cur.execute("SELECT id_barang FROM barang WHERE kode_barang = %s", (kode_barang_lama,))
        barang = cur.fetchone()
        
        if not barang:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Barang tidak ditemukan!"}), 404
        
        id_barang = barang['id_barang']
        
        # Jika kode barang berubah, cek apakah kode baru sudah digunakan
        if kode_barang_lama != kode_barang_baru:
            cur.execute("SELECT COUNT(*) as total FROM barang WHERE kode_barang = %s", (kode_barang_baru,))
            if cur.fetchone()['total'] > 0:
                cur.close()
                conn.close()
                return jsonify({"error": True, "message": f"Kode barang '{kode_barang_baru}' sudah digunakan!"}), 400
        
        # Jika barcode diisi, cek apakah sudah digunakan barang lain
        if barcode:
            cur.execute("""
                SELECT kode_barang, nama_barang 
                FROM barang 
                WHERE barcode = %s AND id_barang != %s
            """, (barcode, id_barang))
            existing = cur.fetchone()
            
            if existing:
                cur.close()
                conn.close()
                return jsonify({
                    "error": True, 
                    "message": f"Barcode sudah digunakan oleh: {existing['nama_barang']} ({existing['kode_barang']})"
                }), 400
        
        # Update barang
        cur.execute("""
            UPDATE barang 
            SET kode_barang = %s, nama_barang = %s, barcode = %s
            WHERE id_barang = %s
        """, (kode_barang_baru, nama_barang, barcode if barcode else None, id_barang))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Data barang berhasil diupdate!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API HAPUS BARANG ========
# ===============================
@app.route("/api/hapus_barang/<kode_barang>", methods=["DELETE"])
@login_required
def api_hapus_barang(kode_barang):
    """Hapus barang beserta semua detail_barang nya"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah barang exists
        cur.execute("""
            SELECT id_barang, kode_barang, nama_barang 
            FROM barang 
            WHERE kode_barang = %s
        """, (kode_barang,))
        
        barang = cur.fetchone()
        if not barang:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Barang tidak ditemukan!"}), 404
        
        id_barang = barang['id_barang']
        
        # Cek apakah barang punya transaksi penjualan
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM detail_penjualan dp
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            WHERE db.id_barang = %s
        """, (id_barang,))
        
        total_penjualan = cur.fetchone()['total']
        
        # Cek apakah barang punya transaksi pembelian
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM detail_pembelian dp
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            WHERE db.id_barang = %s
        """, (id_barang,))
        
        total_pembelian = cur.fetchone()['total']
        
        if total_penjualan > 0 or total_pembelian > 0:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Barang '{barang['nama_barang']}' tidak bisa dihapus karena memiliki riwayat transaksi!\n\nPenjualan: {total_penjualan} transaksi\nPembelian: {total_pembelian} transaksi"
            }), 400
        
        # Hapus semua detail_barang
        cur.execute("DELETE FROM detail_barang WHERE id_barang = %s", (id_barang,))
        
        # Hapus barang
        cur.execute("DELETE FROM barang WHERE id_barang = %s", (id_barang,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": f"✅ Barang '{barang['nama_barang']}' berhasil dihapus!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API GET PRODUK BY KATEGORI
# ===============================
@app.route("/api/kategori/<int:id_kategori>/produk", methods=["GET"])
@login_required
def api_get_produk_kategori(id_kategori):
    """Get list produk dalam kategori tertentu"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT 
                b.id_barang,
                b.kode_barang,
                b.nama_barang,
                b.barcode,
                COALESCE(MAX(d.harga_jual), 0) as harga_jual,
                COALESCE(SUM(d.stok), 0) as stok
            FROM barang b
            LEFT JOIN detail_barang d ON b.id_barang = d.id_barang
            WHERE b.id_kategori = %s
            GROUP BY b.id_barang, b.kode_barang, b.nama_barang, b.barcode
            ORDER BY b.nama_barang ASC
        """, (id_kategori,))
        
        produk = cur.fetchall()
        
        # Convert data
        for p in produk:
            p['harga_jual'] = int(p['harga_jual'] or 0)
            p['stok'] = int(p['stok'] or 0)
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "produk": produk
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API GET PRODUK TANPA KATEGORI
# ===============================
@app.route("/api/produk/tanpa-kategori", methods=["GET"])
@login_required
def api_produk_tanpa_kategori():
    """Get list produk yang belum punya kategori"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT 
                id_barang,
                kode_barang,
                nama_barang,
                barcode
            FROM barang
            WHERE id_kategori IS NULL
            ORDER BY nama_barang ASC
        """)
        
        produk = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "produk": produk
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API TAMBAH PRODUK KE KATEGORI
# ===============================
@app.route("/api/kategori/<int:id_kategori>/tambah-produk", methods=["POST"])
@login_required
def api_tambah_produk_ke_kategori(id_kategori):
    """Tambahkan produk ke kategori"""
    try:
        data = request.get_json(force=True)
        id_barang = data.get("id_barang")
        
        if not id_barang:
            return jsonify({"error": True, "message": "ID barang tidak valid!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Update kategori barang
        cur.execute("""
            UPDATE barang 
            SET id_kategori = %s 
            WHERE id_barang = %s
        """, (id_kategori, id_barang))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Produk berhasil ditambahkan ke kategori!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API HAPUS PRODUK DARI KATEGORI
# ===============================
@app.route("/api/kategori/hapus-produk/<int:id_barang>", methods=["DELETE"])
@login_required
def api_hapus_produk_dari_kategori(id_barang):
    """Hapus produk dari kategori (set ke NULL)"""
    try:
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE barang 
            SET id_kategori = NULL 
            WHERE id_barang = %s
        """, (id_barang,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Produk berhasil dihapus dari kategori!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API LIST PETUGAS ========
# ===============================
@app.route("/api/petugas", methods=["GET"])
@login_required
def api_list_petugas():
    """Get list semua petugas"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT 
                id_petugas,
                nama_petugas,
                username,
                telepon,
                email,
                alamat,
                jabatan,
                status,
                dibuat_pada,
                diperbarui_pada
            FROM petugas
            ORDER BY nama_petugas ASC
        """)
        petugas_list = cur.fetchall()
        
        # Convert datetime to string
        for p in petugas_list:
            if p.get('dibuat_pada'):
                p['dibuat_pada'] = p['dibuat_pada'].strftime('%Y-%m-%d %H:%M:%S')
            if p.get('diperbarui_pada'):
                p['diperbarui_pada'] = p['diperbarui_pada'].strftime('%Y-%m-%d %H:%M:%S')
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "petugas": petugas_list,
            "total": len(petugas_list)
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API GET PETUGAS BY ID ===
# ===============================
@app.route("/api/petugas/<int:id_petugas>", methods=["GET"])
@login_required
def api_get_petugas(id_petugas):
    """Get detail petugas by ID"""
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        cur.execute("""
            SELECT 
                id_petugas,
                nama_petugas,
                username,
                telepon,
                email,
                alamat,
                jabatan,
                status,
                dibuat_pada,
                diperbarui_pada
            FROM petugas
            WHERE id_petugas = %s
        """, (id_petugas,))
        
        petugas = cur.fetchone()
        cur.close()
        conn.close()
        
        if not petugas:
            return jsonify({"error": True, "message": "Petugas tidak ditemukan"}), 404
        
        # Convert datetime to string
        if petugas.get('dibuat_pada'):
            petugas['dibuat_pada'] = petugas['dibuat_pada'].strftime('%Y-%m-%d %H:%M:%S')
        if petugas.get('diperbarui_pada'):
            petugas['diperbarui_pada'] = petugas['diperbarui_pada'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            "error": False,
            **petugas
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API TAMBAH PETUGAS ======
# ===============================
@app.route("/api/petugas", methods=["POST"])
@login_required
def api_tambah_petugas():
    """Tambah petugas baru"""
    try:
        data = request.get_json(force=True)
        
        # Validasi input
        nama_petugas = data.get("nama_petugas", "").strip()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        telepon_raw = data.get("telepon", "").strip()
        email = data.get("email", "").strip()
        alamat = data.get("alamat", "").strip()
        jabatan = data.get("jabatan", "kasir").strip()
        status = data.get("status", "aktif").strip()
        
        # Validasi wajib
        if not nama_petugas:
            return jsonify({"error": True, "message": "Nama petugas wajib diisi!"}), 400
        
        if not username:
            return jsonify({"error": True, "message": "Username wajib diisi!"}), 400
        
        if not password:
            return jsonify({"error": True, "message": "Password wajib diisi!"}), 400
        
        if len(password) < 6:
            return jsonify({"error": True, "message": "Password minimal 6 karakter!"}), 400
        
        # ✅ VALIDASI TELEPON - Bersihkan dari strip, spasi, dll
        if not telepon_raw:
            return jsonify({"error": True, "message": "Nomor telepon wajib diisi!"}), 400
        
        # Hapus semua karakter selain angka
        telepon_clean = ''.join(filter(str.isdigit, telepon_raw))
        
        # Validasi panjang
        if len(telepon_clean) < 10 or len(telepon_clean) > 15:
            return jsonify({
                "error": True,
                "message": f"Nomor telepon tidak valid! Harus 10-15 digit (Anda input: {len(telepon_clean)} digit)"
            }), 400

        cur.execute("SELECT COUNT(*) as total FROM petugas WHERE username = %s", (username,))
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": f"Username '{username}' sudah digunakan!"}), 400
        
        # Cek apakah telepon sudah digunakan
        # Inisialisasi koneksi dan cursor sebelum digunakan
        conn = get_db()
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT COUNT(*) as total FROM petugas WHERE telepon = %s", (telepon_clean,))
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Nomor telepon '{telepon_raw}' sudah terdaftar!"
            }), 400
        
        # Insert petugas dengan telepon yang sudah dibersihkan
        cur.execute("""
            INSERT INTO petugas 
            (nama_petugas, username, password, telepon, email, alamat, jabatan, status, dibuat_pada)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (nama_petugas, username, password, telepon_clean, email or None, 
              alamat or None, jabatan, status))
        
        id_petugas = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Petugas berhasil ditambahkan!",
            "id_petugas": id_petugas,
            "telepon": telepon_clean
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API UPDATE PETUGAS ======
# ===============================
@app.route("/api/petugas/<int:id_petugas>", methods=["PUT"])
@login_required
def api_update_petugas(id_petugas):
    """Update data petugas"""
    try:
        data = request.get_json(force=True)
        
        # Validasi input
        nama_petugas = data.get("nama_petugas", "").strip()
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        telepon_raw = data.get("telepon", "").strip()
        email = data.get("email", "").strip()
        alamat = data.get("alamat", "").strip()
        jabatan = data.get("jabatan", "kasir").strip()
        status = data.get("status", "aktif").strip()
        
        # Validasi wajib
        if not nama_petugas:
            return jsonify({"error": True, "message": "Nama petugas wajib diisi!"}), 400
        
        if not username:
            return jsonify({"error": True, "message": "Username wajib diisi!"}), 400
        
        # ✅ VALIDASI TELEPON - Bersihkan dari strip, spasi, dll
        if not telepon_raw:
            return jsonify({"error": True, "message": "Nomor telepon wajib diisi!"}), 400
        
        # Hapus semua karakter selain angka
        telepon_clean = ''.join(filter(str.isdigit, telepon_raw))
        
        # Validasi panjang
        if len(telepon_clean) < 10 or len(telepon_clean) > 15:
            return jsonify({
                "error": True,
                "message": f"Nomor telepon tidak valid! Harus 10-15 digit (Anda input: {len(telepon_clean)} digit)"
            }), 400
        
        # Validasi awalan
        if not (telepon_clean.startswith('0') or telepon_clean.startswith('62')):
            return jsonify({
                "error": True, 
                "message": "Nomor telepon harus diawali dengan 0 atau 62"
            }), 400
        
        # Validasi password jika diisi
        if password and len(password) < 6:
            return jsonify({"error": True, "message": "Password minimal 6 karakter!"}), 400
        
        # Validasi email jika diisi
        if email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return jsonify({"error": True, "message": "Format email tidak valid!"}), 400
        
        # Validasi jabatan
        if jabatan not in ['admin', 'kasir', 'supervisor']:
            return jsonify({"error": True, "message": "Jabatan tidak valid!"}), 400
        
        # Validasi status
        if status not in ['aktif', 'nonaktif']:
            return jsonify({"error": True, "message": "Status tidak valid!"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah petugas exists
        cur.execute("SELECT id_petugas FROM petugas WHERE id_petugas = %s", (id_petugas,))
        if not cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Petugas tidak ditemukan!"}), 404
        
        # Cek apakah username sudah digunakan petugas lain
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM petugas 
            WHERE username = %s AND id_petugas != %s
        """, (username, id_petugas))
        
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Username '{username}' sudah digunakan petugas lain!"
            }), 400
        
        # Cek apakah telepon sudah digunakan petugas lain
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM petugas 
            WHERE telepon = %s AND id_petugas != %s
        """, (telepon_clean, id_petugas))
        
        if cur.fetchone()['total'] > 0:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Nomor telepon '{telepon_raw}' sudah terdaftar untuk petugas lain!"
            }), 400
        
        # Update petugas
        if password:
            # Update dengan password baru
            cur.execute("""
                UPDATE petugas SET
                    nama_petugas = %s,
                    username = %s,
                    password = %s,
                    telepon = %s,
                    email = %s,
                    alamat = %s,
                    jabatan = %s,
                    status = %s,
                    diperbarui_pada = NOW()
                WHERE id_petugas = %s
            """, (nama_petugas, username, password, telepon_clean, 
                  email or None, alamat or None, jabatan, status, id_petugas))
        else:
            # Update tanpa mengubah password
            cur.execute("""
                UPDATE petugas SET
                    nama_petugas = %s,
                    username = %s,
                    telepon = %s,
                    email = %s,
                    alamat = %s,
                    jabatan = %s,
                    status = %s,
                    diperbarui_pada = NOW()
                WHERE id_petugas = %s
            """, (nama_petugas, username, telepon_clean, 
                  email or None, alamat or None, jabatan, status, id_petugas))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": "✅ Petugas berhasil diupdate!",
            "telepon": telepon_clean
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

# ===============================
# ===== API HAPUS PETUGAS =======
# ===============================
@app.route("/api/petugas/<int:id_petugas>", methods=["DELETE"])
@login_required
def api_hapus_petugas(id_petugas):
    """Hapus petugas"""
    try:
        # Tidak boleh menghapus diri sendiri
        if id_petugas == session.get('user_id'):
            return jsonify({
                "error": True, 
                "message": "Anda tidak dapat menghapus akun Anda sendiri!"
            }), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Cek apakah petugas exists
        cur.execute("""
            SELECT nama_petugas, username
            FROM petugas 
            WHERE id_petugas = %s
        """, (id_petugas,))
        
        petugas = cur.fetchone()
        if not petugas:
            cur.close()
            conn.close()
            return jsonify({"error": True, "message": "Petugas tidak ditemukan!"}), 404
        
        # Cek apakah petugas punya transaksi penjualan
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM penjualan 
            WHERE id_petugas = %s
        """, (id_petugas,))
        
        total_penjualan = cur.fetchone()['total']
        
        # Cek apakah petugas punya transaksi pembelian
        cur.execute("""
            SELECT COUNT(*) as total 
            FROM pembelian 
            WHERE id_petugas = %s
        """, (id_petugas,))
        
        total_pembelian = cur.fetchone()['total']
        
        if total_penjualan > 0 or total_pembelian > 0:
            cur.close()
            conn.close()
            return jsonify({
                "error": True, 
                "message": f"Petugas '{petugas['nama_petugas']}' tidak bisa dihapus karena memiliki riwayat transaksi!\n\nPenjualan: {total_penjualan} transaksi\nPembelian: {total_pembelian} transaksi"
            }), 400
        
        # Hapus petugas
        cur.execute("DELETE FROM petugas WHERE id_petugas = %s", (id_petugas,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "message": f"✅ Petugas '{petugas['nama_petugas']}' berhasil dihapus!"
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500
 
# Tambahkan route-route berikut ke app.py

# ===============================
# ===== HALAMAN LAPORAN =========
# ===============================
@app.route("/laporan/penjualan")
@login_required
def laporan_penjualan():
    return render_template("laporan_penjualan.html", nama_petugas=session.get('nama_petugas'))

@app.route("/laporan/pembelian")
@login_required
def laporan_pembelian():
    return render_template("laporan_pembelian.html", nama_petugas=session.get('nama_petugas'))

# ===============================
# ===== API LAPORAN PENJUALAN ===
# ===============================
# ===============================
# ===== API LAPORAN PENJUALAN ===
# ===============================
@app.route("/api/laporan/penjualan/umum")
@login_required
def api_laporan_penjualan_umum():
    """Get laporan umum penjualan per customer dengan filter tanggal"""
    try:
        tanggal_mulai = request.args.get('tanggal_mulai')
        tanggal_selesai = request.args.get('tanggal_selesai')
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Base query - PERBAIKAN: Aggregate per customer
        query = """
            SELECT 
                COALESCE(p.nama_pembeli, 'Customer Umum') as customer,
                COALESCE(p.nomor_telepon, '-') as telepon,
                COUNT(DISTINCT p.id_penjualan) as jumlah_transaksi,
                COALESCE(SUM(p.total_harga), 0) as total,
                COALESCE(SUM(dp.diskon), 0) as total_promo
            FROM penjualan p
            LEFT JOIN detail_penjualan dp ON p.id_penjualan = dp.id_penjualan
            WHERE 1=1
        """
        
        params = []
        
        # Filter tanggal
        if tanggal_mulai:
            query += " AND DATE(p.tanggal) >= %s"
            params.append(tanggal_mulai)
        
        if tanggal_selesai:
            query += " AND DATE(p.tanggal) <= %s"
            params.append(tanggal_selesai)
        
        query += """
            GROUP BY p.nama_pembeli, p.nomor_telepon
            HAVING total > 0
            ORDER BY total DESC
        """
        
        cur.execute(query, params)
        data = cur.fetchall()
        
        print(f"✅ Data ditemukan: {len(data)} customer")
        
        # Calculate totals
        total_keseluruhan = 0
        total_promo_keseluruhan = 0
        total_transaksi = 0
        
        # Format data
        for row in data:
            row['total'] = int(row['total'] or 0)
            row['total_promo'] = int(row['total_promo'] or 0)
            row['jumlah_transaksi'] = int(row['jumlah_transaksi'] or 0)
            
            total_keseluruhan += row['total']
            total_promo_keseluruhan += row['total_promo']
            total_transaksi += row['jumlah_transaksi']
            
            print(f"  - {row['customer']}: Rp {row['total']:,} ({row['jumlah_transaksi']} transaksi)")
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "data": data,
            "summary": {
                "total_keseluruhan": int(total_keseluruhan),
                "total_promo": int(total_promo_keseluruhan),
                "total_transaksi": int(total_transaksi),
                "jumlah_customer": len(data)
            }
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print("❌ ERROR LAPORAN PENJUALAN UMUM:")
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

@app.route("/api/laporan/penjualan/detail")
@login_required
def api_laporan_penjualan_detail():
    """Get laporan detail penjualan per customer dengan daftar barang"""
    try:
        nama_pembeli = request.args.get('customer')
        tanggal_mulai = request.args.get('tanggal_mulai')
        tanggal_selesai = request.args.get('tanggal_selesai')

        if not nama_pembeli:
            return jsonify({"error": True, "message": "Customer tidak ditemukan"}), 400

        conn = get_db()
        cur = conn.cursor(dictionary=True)

        query = """
            SELECT 
                p.id_penjualan,
                p.tanggal,
                COALESCE(p.nama_pembeli, 'Customer Umum') as customer,
                COALESCE(p.nomor_telepon, '-') as telepon,
                b.kode_barang as kode_faktur,
                b.nama_barang as nama_barang,
                dp.jumlah as item,
                dp.diskon as promo,
                dp.subtotal as harga,
                dp.total as subtotal
            FROM penjualan p
            JOIN detail_penjualan dp ON p.id_penjualan = dp.id_penjualan
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            JOIN barang b ON db.id_barang = b.id_barang
            WHERE 1=1
        """

        params = []

        # Filter customer (handle Customer Umum)
        if nama_pembeli == 'Customer Umum':
            query += " AND (p.nama_pembeli IS NULL OR p.nama_pembeli = '')"
        else:
            query += " AND p.nama_pembeli = %s"
            params.append(nama_pembeli)

        # Filter tanggal
        if tanggal_mulai:
            query += " AND DATE(p.tanggal) >= %s"
            params.append(tanggal_mulai)
        if tanggal_selesai:
            query += " AND DATE(p.tanggal) <= %s"
            params.append(tanggal_selesai)

        query += " ORDER BY p.tanggal DESC, b.nama_barang ASC"

        cur.execute(query, params)
        data = cur.fetchall()

        total_keseluruhan = 0
        total_promo = 0

        for row in data:
            row['subtotal'] = int(row.get('subtotal', 0) or 0)
            row['promo'] = int(row.get('promo', 0) or 0)
            row['item'] = int(row.get('item', 0) or 0)
            row['tanggal'] = row['tanggal'].strftime('%Y-%m-%d %H:%M:%S') if row['tanggal'] else '-'
            total_keseluruhan += row['subtotal']
            total_promo += row['promo']

        cur.close()
        conn.close()

        return jsonify({
            "error": False,
            "data": data,
            "customer": nama_pembeli,
            "summary": {
                "total_keseluruhan": int(total_keseluruhan),
                "total_promo": int(total_promo),
                "jumlah_item": len(data)
            }
        })

    except Exception as e:
        tb = traceback.format_exc()
        print("❌ ERROR LAPORAN PENJUALAN DETAIL:")
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500



# ===============================
# ===== API LAPORAN PEMBELIAN ===
# ===============================
@app.route("/api/laporan/pembelian/umum")
@login_required
def api_laporan_pembelian_umum():
    """Get laporan umum pembelian per supplier dengan filter tanggal"""
    try:
        tanggal_mulai = request.args.get('tanggal_mulai')
        tanggal_selesai = request.args.get('tanggal_selesai')
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Base query - pembelian tidak punya field supplier, jadi kita ambil dari detail
        query = """
            SELECT 
                s.nama_supplier as anggota,
                s.nama_kontak as kontak,
                COUNT(DISTINCT p.id_pembelian) as jumlah_transaksi,
                SUM(dp.jumlah * dp.harga_beli) as total
            FROM pembelian p
            LEFT JOIN detail_pembelian dp ON p.id_pembelian = dp.id_pembelian
            LEFT JOIN detail_barang db ON dp.id_detail = db.id_detail
            LEFT JOIN barang b ON db.id_barang = b.id_barang
            LEFT JOIN supplier s ON b.id_supplier = s.id_supplier
            WHERE 1=1
        """
        
        params = []
        
        # Filter tanggal
        if tanggal_mulai:
            query += " AND DATE(p.tanggal) >= %s"
            params.append(tanggal_mulai)
        
        if tanggal_selesai:
            query += " AND DATE(p.tanggal) <= %s"
            params.append(tanggal_selesai)
        
        query += """
            GROUP BY s.nama_supplier, s.nama_kontak
            ORDER BY total DESC
        """
        
        cur.execute(query, params)
        data = cur.fetchall()
        
        # Calculate totals
        total_keseluruhan = sum(row['total'] for row in data if row['total']) if data else 0
        total_transaksi = sum(row['jumlah_transaksi'] for row in data) if data else 0
        
        # Format data
        for row in data:
            row['total'] = int(row['total'] or 0)
            row['jumlah_transaksi'] = int(row['jumlah_transaksi'] or 0)
            row['anggota'] = row['anggota'] if row['anggota'] else 'Supplier Umum'
            row['kontak'] = row['kontak'] if row['kontak'] else '-'
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "data": data,
            "summary": {
                "total_keseluruhan": int(total_keseluruhan),
                "total_transaksi": int(total_transaksi),
                "jumlah_supplier": len(data)
            }
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500

@app.route("/api/laporan/pembelian/detail")
@login_required
def api_laporan_pembelian_detail():
    """Get laporan detail pembelian per supplier dengan daftar barang"""
    try:
        nama_supplier = request.args.get('anggota')
        tanggal_mulai = request.args.get('tanggal_mulai')
        tanggal_selesai = request.args.get('tanggal_selesai')
        
        if not nama_supplier:
            return jsonify({"error": True, "message": "Supplier tidak ditemukan"}), 400
        
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        
        # Query untuk mendapatkan detail barang yang dibeli dari supplier
        query = """
            SELECT 
                p.id_pembelian,
                p.tanggal,
                s.nama_supplier as anggota,
                b.kode_barang as faktur,
                b.nama_barang as barang,
                dp.jumlah as item,
                dp.harga_beli * dp.jumlah as subtotal
            FROM pembelian p
            JOIN detail_pembelian dp ON p.id_pembelian = dp.id_pembelian
            JOIN detail_barang db ON dp.id_detail = db.id_detail
            JOIN barang b ON db.id_barang = b.id_barang
            JOIN supplier s ON b.id_supplier = s.id_supplier
            WHERE s.nama_supplier = %s
        """
        
        params = [nama_supplier]
        
        # Filter tanggal
        if tanggal_mulai:
            query += " AND DATE(p.tanggal) >= %s"
            params.append(tanggal_mulai)
        
        if tanggal_selesai:
            query += " AND DATE(p.tanggal) <= %s"
            params.append(tanggal_selesai)
        
        query += " ORDER BY p.tanggal DESC, b.nama_barang ASC"
        
        cur.execute(query, params)
        data = cur.fetchall()
        
        # Calculate totals
        total_keseluruhan = sum(row['subtotal'] for row in data) if data else 0
        
        # Format data
        for row in data:
            row['subtotal'] = int(row['subtotal'] or 0)
            row['item'] = int(row['item'] or 0)
            row['tanggal'] = row['tanggal'].strftime('%Y-%m-%d %H:%M:%S') if row['tanggal'] else '-'
        
        cur.close()
        conn.close()
        
        return jsonify({
            "error": False,
            "data": data,
            "anggota": nama_supplier,
            "summary": {
                "total_keseluruhan": int(total_keseluruhan),
                "jumlah_item": len(data)
            }
        })
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        return jsonify({"error": True, "message": str(e), "trace": tb}), 500
       
# Tambahkan route ini setelah route /faktur/view/<int:id_faktur>

# ===============================
# ===== Lihat struk 58mm ========
# ===============================
@app.route("/struk/view/<int:id_faktur>")
@login_required
def lihat_struk(id_faktur):

    """Tampilkan struk thermal 58mm untuk auto-print"""
    conn = get_db_faktur()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM faktur_master WHERE id_faktur = %s", (id_faktur,))
        row = cur.fetchone()
        if not row:
            return "Faktur tidak ditemukan", 404
        
        # Ambil detail items dari HTML atau query ulang
        if row.get("html"):
            # Parse items dari data transaksi asli
            conn_main = get_db()
            cur_main = conn_main.cursor(dictionary=True)
            
            if row['tipe'] == 'penjualan':
                cur_main.execute("""
                    SELECT 
                        b.kode_barang as kode,
                        b.nama_barang as nama,
                        dp.jumlah as item,
                        dp.subtotal as harga,
                        dp.total as subtotal
                    FROM detail_penjualan dp
                    JOIN detail_barang db ON dp.id_detail = db.id_detail
                    JOIN barang b ON db.id_barang = b.id_barang
                    JOIN penjualan p ON dp.id_penjualan = p.id_penjualan
                    WHERE p.id_penjualan = %s
                    ORDER BY b.nama_barang
                """, (row['ref_id'],))
            else:
                cur_main.execute("""
                    SELECT 
                        b.kode_barang as kode,
                        b.nama_barang as nama,
                        dpb.jumlah,
                        dpb.harga_beli as harga,
                        (dpb.jumlah * dpb.harga_beli) as subtotal
                    FROM detail_pembelian dpb
                    JOIN detail_barang db ON dpb.id_detail = db.id_detail
                    JOIN barang b ON db.id_barang = b.id_barang
                    WHERE dpb.id_pembelian = %s
                    ORDER BY b.nama_barang
                """, (row['ref_id'],))
            
            items = cur_main.fetchall()
            # --- Tambahkan field 'jumlah' agar template tidak error ---
            for item in items:
                if 'jumlah' not in item:
                    if 'item' in item:
                        item['jumlah'] = item['item']
                    else:
                        item['jumlah'] = 0  # fallback jika tidak ada
            cur_main.close()
            conn_main.close()
            
            # Format tanggal
            tanggal_str = row['tanggal'].strftime("%d/%m/%Y %H:%M:%S") if isinstance(row['tanggal'], datetime) else str(row['tanggal'])
            
            # Render struk 58mm
            return render_template("struk_58mm.html",
                                 tipe=row['tipe'],
                                 nomor_faktur=row['nomor_faktur'],
                                 tanggal=tanggal_str,
                                 kepada=row['pelanggan'],
                                 items=items,
                                 total=int(row['total']),
                                 total_pajak=0,
                                 biaya_kirim=0,
                                 dibayar=int(row['total']),
                                 saldo=0,
                                 terbilang=angka_ke_terbilang(row['total']).capitalize() + " Rupiah",
                                 nama_petugas=session.get('nama_petugas'),
                                 auto_print=True)
        
        return "Data tidak lengkap", 404
        
    finally:
        cur.close()
        conn.close()

# ===============================
# ===== Jalankan Aplikasi =======
# ===============================
if __name__ == "__main__":
    app.run(debug=True)