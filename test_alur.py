# -*- coding: utf-8 -*-
"""Uji alur tulis: keputusan KPA, update paket, impor realisasi & kontrak."""
import os
import sys

from streamlit.testing.v1 import AppTest

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = (r"E:\1. Dari_Laptop_Pribadi_22062021\15. PKN II WILHELMUS SANGA SE MM"
        r"\2. PKN II th 2026\6. Proyek Perubahan PKN II 2026"
        r"\2. LPP PKN II TH 2026\data dukung")
DATA_SAKTI = (r"E:\1. Dari_Laptop_Pribadi_22062021\15. PKN II WILHELMUS SANGA SE MM"
              r"\2. PKN II th 2026\6. Proyek Perubahan PKN II 2026"
              r"\3. DATA DUKUNG Proper PKN II TH 2026")

sys.path.insert(0, BASE)
import db  # noqa: E402

gagal = 0

# Rekam keadaan awal agar uji dapat membersihkan diri sepenuhnya setelah selesai.
_awal_audit = db.one("SELECT COALESCE(MAX(id), 0) AS m FROM audit")["m"]
_awal_file = db.one("SELECT COALESCE(MAX(id), 0) AS m FROM file_impor")["m"]
_awal_kontrak = db.rows("SELECT * FROM kontrak")


def login(akun):
    at = AppTest.from_file(os.path.join(BASE, "app.py"), default_timeout=60)
    at.run()
    at.text_input[0].set_value(akun)
    at.text_input[1].set_value("satria2026")
    at.button[0].click().run()
    assert not at.exception, at.exception
    return at


def cari_tombol(at, label):
    for b in at.button:
        if getattr(b, "label", None) == label:
            return b
    return None


def cek(nama, kondisi, info=""):
    global gagal
    if kondisi:
        print("ok %s %s" % (nama, info))
    else:
        print("X %s %s" % (nama, info))
        gagal += 1


# ---- 1. KPA mencatat keputusan ----
awal = len(db.rows("SELECT * FROM keputusan"))
at = login("kpa")
at.radio[0].set_value("Keputusan KPA")
at.run()
at.selectbox[0].set_value("Risiko " + db.rows("SELECT * FROM risiko ORDER BY id")[0]["id"])
at.selectbox[1].set_value("Pendampingan atau teguran PPK")
at.text_area[0].set_value("Uji coba pencatatan keputusan - dasar: kontrak terlambat termin.")
btn = cari_tombol(at, "Catat keputusan")
if btn is None:
    cek("keputusan tombol", False, "(tidak ditemukan)")
else:
    btn.click().run()
    sesudah = len(db.rows("SELECT * FROM keputusan"))
    cek("keputusan tersimpan", sesudah == awal + 1,
        "(sebelum %d -> sesudah %d)" % (awal, sesudah))
    cek("keputusan bebas exception", not at.exception, str(at.exception))
    baris = db.one("SELECT * FROM keputusan ORDER BY id DESC")
    cek("isi keputusan sesuai", baris["opsi"] == "Pendampingan atau teguran PPK"
        and "kontrak terlambat" in baris["dasar"], "(%s)" % baris["opsi"])

# ---- 2. PPK2 memperbarui paket miliknya ----
at = login("ppk2")
at.radio[0].set_value("Anggaran & Paket")
at.run()
p2 = db.one("SELECT * FROM paket WHERE no=2")
at.selectbox[0].set_value("2. %s" % p2["nama"])
at.run()
at.number_input[0].set_value(float(p2["realisasi"]) + 1000000.0)
at.text_area[0].set_value("Uji coba pembaruan oleh PPK2")
btn = cari_tombol(at, "Simpan perubahan")
if btn is None:
    cek("paket update tombol", False, "(tidak ditemukan)")
else:
    btn.click().run()
    p2b = db.one("SELECT * FROM paket WHERE no=2")
    cek("paket2 realisasi naik 1jt", p2b["realisasi"] == p2["realisasi"] + 1000000,
        "(%d -> %d)" % (p2["realisasi"], p2b["realisasi"]))
    cek("audit kecatat", any("Perbarui paket 2" in a["aksi"]
                             for a in db.rows("SELECT * FROM audit ORDER BY id DESC LIMIT 5")))
    db.run("UPDATE paket SET realisasi=?, catatan=? WHERE no=?",
           (p2["realisasi"], p2["catatan"] or "", 2))

# ---- 3. PPK4 tidak bisa mengubah paket 1 ----
at = login("ppk4")
at.radio[0].set_value("Anggaran & Paket")
at.run()
p1 = db.one("SELECT * FROM paket WHERE no=1")
at.selectbox[0].set_value("1. %s" % p1["nama"])
at.run()
cek("ppk4 diblok ubah paket1", len(at.number_input) == 0,
    "(jumlah input di form = %d, exception=%s)" % (len(at.number_input), at.exception))

# ---- 4. Impor realisasi (file asli OM-SPAN Juli) ----
at = login("urkeu")
at.radio[0].set_value("Impor Data (SAKTI/OM-SPAN)")
at.run()
file_real = os.path.join(DATA, "Realisasi Anggaran Puslitbang Polri Juli  2026 06082026.xlsx")
impor = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",)
try:
    at.file_uploader[0].set_value(
        (os.path.basename(file_real), open(file_real, "rb").read(), impor[0]))
    at.run()
    baca_ok = not at.exception
except Exception as exc:  # noqa: BLE001
    baca_ok = False
    print("   (file_uploader realisasi gagal: %s)" % exc)
if not baca_ok:
    cek("impor realisasi UI", False, "(tidak bisa unggah lewat AppTest)")
else:
    at.text_input[-1].set_value("Uji Bulan 2099")
    btn = cari_tombol(at, "Simpan ke basis data")
    if btn is None:
        cek("impor realisasi tombol", False, "(tidak ditemukan)")
    else:
        btn.click().run()
        ada = db.one("SELECT * FROM anggaran WHERE periode='Uji Bulan 2099' "
                     "AND kategori='AGREGAT'")
        cek("impor realisasi tersimpan", ada is not None and ada["pagu"] == 333636862000,
            "(pagu %s)" % (ada["pagu"] if ada else "-"))
        if ada:
            db.run("DELETE FROM anggaran WHERE periode='Uji Bulan 2099'", ())

# ---- 4b. Impor realisasi SAKTI (xlsx & pdf asli, periode Oktober 2026) ----
for nama_sakti, mime_sakti in (
        ("Laporan Fa Detail (16 Segmen) (46).xlsx",
         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("Laporan Fa Detail (16 Segmen) - 2026-10-06T154140.104.pdf", "application/pdf")):
    jalur = os.path.join(DATA_SAKTI, nama_sakti)
    if not os.path.exists(jalur):
        print("   (file SAKTI tidak ada, dilewati: %s)" % nama_sakti)
        continue
    at = login("urkeu")
    at.radio[0].set_value("Impor Data (SAKTI/OM-SPAN)")
    at.run()
    isi = open(jalur, "rb").read()
    try:
        at.file_uploader[0].set_value((nama_sakti, isi, mime_sakti))
        at.run()
        baca_ok = not at.exception
    except Exception as exc:  # noqa: BLE001
        baca_ok = False
        print("   (upload SAKTI %s gagal: %s)" % (nama_sakti, exc))
    if not baca_ok:
        cek("impor SAKTI UI %s" % nama_sakti, False, "(tidak bisa unggah lewat AppTest)")
        continue
    at.text_input[-1].set_value("Uji SAKTI 2099")
    btn = cari_tombol(at, "Simpan ke basis data")
    cek("impor SAKTI tombol %s" % nama_sakti, btn is not None,
        "" if btn is not None else "(tidak ditemukan)")
    if btn is None:
        continue
    btn.click().run()
    ag = db.one("SELECT * FROM anggaran WHERE periode='Uji SAKTI 2099' "
                "AND kategori='AGREGAT'")
    cek("SAKTI agregat %s" % nama_sakti,
        ag is not None and ag["pagu"] == 333720245000
        and ag["realisasi"] == 320475730777 and ag["sisa"] == 13244514223,
        "(pagu %s)" % (ag["pagu"] if ag else "-"))
    jns = db.rows("SELECT * FROM anggaran WHERE periode='Uji SAKTI 2099' "
                  "AND kategori='JENIS' ORDER BY uraian")
    cek("SAKTI jenis %s" % nama_sakti,
        len(jns) == 3 and sum(r["pagu"] for r in jns) == 333720245000
        and sum(r["realisasi"] for r in jns) == 320475730777,
        "(%d baris; jumlah pagu %s; real %s)"
        % (len(jns), sum(r["pagu"] for r in jns), sum(r["realisasi"] for r in jns)))
    f = db.file_impor_terakhir("realisasi")
    cek("berkas impor tersimpan %s" % nama_sakti,
        f is not None and f["nama_file"] == nama_sakti
        and f["periode"] == "Uji SAKTI 2099" and f["format"] == "SAKTI"
        and f["isi"] == isi,
        "(nama %s, format %s)" % (f["nama_file"] if f else "-",
                                  f["format"] if f else "-"))
    db.run("DELETE FROM anggaran WHERE periode='Uji SAKTI 2099'", ())
    db.run("DELETE FROM file_impor WHERE periode='Uji SAKTI 2099'", ())

# ---- 5. Impor kontrak (file asli OM-SPAN) ----
at = login("urkeu")
at.radio[0].set_value("Impor Data (SAKTI/OM-SPAN)")
at.run()
file_kontrak = os.path.join(DATA, "Monitoring Data Kontrak_2026-09-28 22-44.xlsx")
try:
    at.file_uploader[1].set_value(
        (os.path.basename(file_kontrak), open(file_kontrak, "rb").read(), impor[0]))
    at.run()
    baca_ok = not at.exception
except Exception as exc:  # noqa: BLE001
    baca_ok = False
    print("   (file_uploader kontrak gagal: %s)" % exc)
if not baca_ok:
    cek("impor kontrak UI", False, "(tidak bisa unggah lewat AppTest)")
else:
    btn = cari_tombol(at, "Ganti tabel kontrak dengan data ini")
    if btn is None:
        cek("impor kontrak tombol", False, "(tidak ditemukan)")
    else:
        btn.click().run()
        n = len(db.rows("SELECT * FROM kontrak"))
        cek("impor kontrak 7 baris", n == 7, "(jumlah %d)" % n)
        cek("audit impor kontrak", any("Impor kontrak" in a["aksi"]
                                       for a in db.rows("SELECT * FROM audit ORDER BY id DESC LIMIT 5")))

# ---- 6. KPA ubah ambang ----
at = login("kpa")
at.radio[0].set_value("Pengaturan & Audit")
at.run()
if len(at.number_input) >= 6:
    at.number_input[0].set_value(94.0)
    btn = cari_tombol(at, "Simpan ambang")
    btn.click().run()
    cek("ubah ambang ikpa_merah", db.float_setelan("ikpa_merah", 0) == 94.0,
        "(nilai %s)" % db.float_setelan("ikpa_merah", 0))
    db.set_setelan("ikpa_merah", 95, "IKPA merah di bawah")
else:
    cek("form ambang", False, "(input %d)" % len(at.number_input))

# ---- 7. Ganti sandi ----
at = login("kpa")
at.radio[0].set_value("Pengaturan & Audit")
at.run()
idx = [i for i, w in enumerate(at.text_input) if w.label == "Kata sandi saat ini"]
if idx:
    i = idx[0]
    at.text_input[i].set_value("satria2026")
    at.text_input[i + 1].set_value("rahasia12345")
    at.text_input[i + 2].set_value("rahasia12345")
    cari_tombol(at, "Ganti kata sandi").click().run()
    cek("ganti sandi berhasil", db.verifikasi_login("kpa", "rahasia12345") is not None)
    db.ganti_sandi("kpa", "satria2026")
else:
    cek("form ganti sandi", False, "(label tidak ditemukan)")

# ---- 8. PPK risiko di-update pokja ----
awal = db.one("SELECT * FROM risiko WHERE id='R-02'")
at = login("pokja")
at.radio[0].set_value("Manajemen Risiko")
at.run()
at.selectbox[0].set_value("R-02")
at.run()
at.number_input[0].set_value(4.0)
at.number_input[1].set_value(4.0)
btn = cari_tombol(at, "Simpan penilaian")
if btn is None:
    cek("update risiko tombol", False, "(tidak ditemukan)")
else:
    btn.click().run()
    sesudah = db.one("SELECT k, d FROM risiko WHERE id='R-02'")
    cek("risiko R-02 jadi 4x4", sesudah["k"] == 4 and sesudah["d"] == 4,
        "(K%d x D%d)" % (sesudah["k"], sesudah["d"]))
    _kolom = [c for c in awal if c != "id"]
    db.run("UPDATE risiko SET %s WHERE id='R-02'"
           % ",".join("%s=?" % c for c in _kolom),
           tuple(awal[c] for c in _kolom))

# ---- bersihkan data hasil uji (kembalikan ke keadaan awal) ----
db.run("DELETE FROM keputusan WHERE dasar LIKE '%Uji coba pencatatan%'", ())
db.run("DELETE FROM anggaran WHERE periode IN ('Uji Bulan 2099', 'Uji SAKTI 2099')", ())
# impor kontrak uji mengganti seluruh tabel -> tulis ulang persis seperti semula
db.run("DELETE FROM kontrak", ())
for _r in _awal_kontrak:
    _kol = ",".join(_r.keys())
    _ph = ",".join(["?"] * len(_r))
    db.run("INSERT INTO kontrak (%s) VALUES (%s)" % (_kol, _ph), tuple(_r.values()))
# hapus berkas impor & baris audit yang dibuat selama uji
db.run("DELETE FROM file_impor WHERE id > ?", (_awal_file,))
db.run("DELETE FROM audit WHERE id > ?", (_awal_audit,))
# rapatkan kembali berkas basis data (aman; diabaikan bila gagal)
try:
    db.run("VACUUM")
except Exception:  # noqa: BLE001
    pass
print("bersihkan data uji selesai (kontrak, berkas impor, dan audit dipulihkan)")

print("\nTOTAL GAGAL:", gagal)
sys.exit(1 if gagal else 0)
