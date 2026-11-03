# -*- coding: utf-8 -*-
"""Basis data lokal Dashboard Pengendalian SATRIA Puslitbang (SQLite).

Seluruh angka awal (seed) berasal dari dokumen sumber yang sudah diverifikasi:
- Kartu Kendali Bulanan KPA berbasis Risiko, Bulan Juli 2026  -> daftar 6 paket
- Monitoring Data Kontrak OM-SPAN unduh 28-09-2026 (7 kontrak) -> tabel kontrak
- Realisasi Anggaran Puslitbang Polri Juli 2026 06082026.xlsx -> anggaran agregat,
  per bagian, dan per jenis belanja (baris GRAND TOTAL & baris TOTAL per blok)
- Nilai IKPA Februari-Juli 2026 (screenshot SPAN, diverifikasi visual 3 Okt 2026)
- Risk Register Kinerja SATRIA Puslitbang (pembaruan 28 September 2026)
- Matriks Milestone-Output-Eviden + Master Jadwal PKN ANGK XXVI

Aturan aplikasi: setiap perubahan data wajib meninggalkan jejak audit.
"""

import hashlib
import os
import random
import shutil
import sqlite3
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
DB_PATH = os.path.join(DATA_DIR, "satria.db")

CHECKLIST_MD = os.path.join(
    BASE, "assets", "pilar",
    "03. Checklist Isian Data - Kerangka Lampiran L-01 sd L-15.md")
if not os.path.exists(CHECKLIST_MD):
    # cadangan: lokasi asli pada laptop penyusun (bila folder paket belum lengkap)
    CHECKLIST_MD = (
        r"E:\1. Dari_Laptop_Pribadi_22062021\15. PKN II WILHELMUS SANGA SE MM"
        r"\2. PKN II th 2026\6. Proyek Perubahan PKN II 2026\2. LPP PKN II TH 2026"
        r"\Draf LPP dan Lampiran - 22 September 2026"
        r"\03. Checklist Isian Data - Kerangka Lampiran L-01 sd L-15.md"
    )

KATA_SANDI_BAWAAN = "satria2026"


# ---------------------------------------------------------------- koneksi ----
def connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA journal_mode=WAL")
    except sqlite3.Error:
        pass
    return con


def rows(sql, params=()):
    with connect() as con:
        return [dict(r) for r in con.execute(sql, params).fetchall()]


def one(sql, params=()):
    with connect() as con:
        r = con.execute(sql, params).fetchone()
        return dict(r) if r else None


def run(sql, params=()):
    with connect() as con:
        con.execute(sql, params)
        con.commit()


# --------------------------------------------------------------- utilitas ----
def _hash(sandi, garam):
    return hashlib.sha256((garam + sandi).encode("utf-8")).hexdigest()


def audit(pengguna, aksi, detail=""):
    run(
        "INSERT INTO audit(waktu, pengguna, aksi, detail) VALUES (?,?,?,?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pengguna, aksi, detail),
    )


def setelan(kunci, default=None):
    r = one("SELECT nilai FROM pengaturan WHERE kunci=?", (kunci,))
    return r["nilai"] if r else default


def set_setelan(kunci, nilai, keterangan=""):
    run(
        "INSERT INTO pengaturan(kunci, nilai, keterangan) VALUES (?,?,?) "
        "ON CONFLICT(kunci) DO UPDATE SET nilai=excluded.nilai",
        (kunci, str(nilai), keterangan),
    )


def float_setelan(kunci, default):
    try:
        return float(setelan(kunci, default))
    except (TypeError, ValueError):
        return float(default)


# --------------------------------------------------------------- file impor ----
def simpan_file_impor(jenis, format_, nama_file, isi, periode, ringkasan, pengimpor):
    run(
        "INSERT INTO file_impor(jenis, format, nama_file, isi, periode, ringkasan, "
        "pengimpor, waktu) VALUES (?,?,?,?,?,?,?,?)",
        (jenis, format_, nama_file, sqlite3.Binary(isi), periode, ringkasan, pengimpor,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def file_impor_terakhir(jenis):
    return one(
        "SELECT id, jenis, format, nama_file, isi, periode, ringkasan, pengimpor, waktu "
        "FROM file_impor WHERE jenis=? ORDER BY id DESC LIMIT 1", (jenis,))


def daftar_file_impor(jenis):
    return rows(
        "SELECT id, jenis, format, nama_file, periode, ringkasan, pengimpor, waktu, "
        "length(isi) AS ukuran FROM file_impor WHERE jenis=? ORDER BY id DESC", (jenis,))


def _id(x, des=2):
    """Format angka gaya Indonesia (koma desimal)."""
    return ("{:." + str(des) + "f}").format(x).replace(".", ",")


def verifikasi_login(nama_pengguna, sandi):
    r = one("SELECT * FROM pengguna WHERE nama_pengguna=? AND aktif=1", (nama_pengguna.strip(),))
    if not r:
        return None
    if _hash(sandi, r["garam"]) == r["hash"]:
        return r
    return None


def ganti_sandi(nama_pengguna, sandi_baru):
    r = one("SELECT garam FROM pengguna WHERE nama_pengguna=?", (nama_pengguna,))
    if not r:
        return False
    garam = r["garam"]
    run(
        "UPDATE pengguna SET hash=? WHERE nama_pengguna=?",
        (_hash(sandi_baru, garam), nama_pengguna),
    )
    audit(nama_pengguna, "Ganti kata sandi", "kata sandi pengguna diperbarui")
    return True


def backup_database():
    stempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    tujuan = os.path.join(DATA_DIR, "backup", "satria_%s.db" % stempel)
    os.makedirs(os.path.dirname(tujuan), exist_ok=True)
    shutil.copy2(DB_PATH, tujuan)
    audit("sistem", "Backup database", tujuan)
    return tujuan


# ------------------------------------------------------------- peringatan ----
def daftar_peringatan():
    """Gabungan aturan peringatan dini. Mengembalikan list dict(level, pesan, objek)."""
    hasil = []
    ikpa_merah = float_setelan("ikpa_merah", 95)
    ikpa_kuning = float_setelan("ikpa_kuning", 97)
    cap_merah = float_setelan("capaian_merah", 50)
    cap_kuning = float_setelan("capaian_kuning", 80)
    risiko_merah = float_setelan("risiko_merah", 10)

    ikpa = rows("SELECT * FROM ikpa ORDER BY urutan")
    if ikpa:
        terakhir = ikpa[-1]
        nilai = terakhir["nilai"]
        if nilai < ikpa_merah:
            turun = ikpa[0]["nilai"] - nilai
            hasil.append(
                dict(level="Merah", objek="IKPA",
                     pesan="IKPA %s = %s di bawah ambang merah %s (turun %s poin sejak %s) "
                           "- perlu tindak lanjut kebijakan mutu anggaran"
                           % (terakhir["bulan"], _id(nilai), _id(ikpa_merah, 0), _id(turun),
                              ikpa[0]["bulan"]))
            )
        elif nilai < ikpa_kuning:
            hasil.append(dict(level="Kuning", objek="IKPA",
                              pesan="IKPA %s = %s di bawah ambang kuning %s"
                                    % (terakhir["bulan"], _id(nilai), _id(ikpa_kuning, 0))))

    for p in rows("SELECT * FROM paket ORDER BY no"):
        if p["target"]:
            cap = p["realisasi"] / p["target"] * 100
            if cap < cap_merah:
                hasil.append(dict(level="Merah", objek="Paket %d" % p["no"],
                                  pesan="Paket %s (PPK %s): capaian %s%% terhadap target s.d. bulan "
                                        "di bawah ambang merah %s%%"
                                        % (p["nama"], p["ppk"], _id(cap), _id(cap_merah, 0))))
            elif cap < cap_kuning:
                hasil.append(dict(level="Kuning", objek="Paket %d" % p["no"],
                                  pesan="Paket %s (PPK %s): capaian %s%% - di bawah ambang kuning %s%%"
                                        % (p["nama"], p["ppk"], _id(cap), _id(cap_kuning, 0))))

    for k in rows("SELECT * FROM kontrak"):
        if "TERLAMBAT" in (k["status"] or "").upper():
            hasil.append(dict(level="Merah", objek="Kontrak",
                              pesan="%s (%s) status %s - nilai Rp%s"
                                    % (k["nomor"], k["supplier"], k["status"],
                                       format(int(k["nilai"]), ",d").replace(",", "."))))

    today = datetime.now().date()
    for m in rows("SELECT * FROM milestone ORDER BY tanggal"):
        t = datetime.strptime(m["tanggal"], "%Y-%m-%d").date()
        sisa = (t - today).days
        if m["status"] == "Terlaksana":
            continue
        if sisa < 0:
            hasil.append(dict(level="Merah", objek=m["kode"],
                              pesan="%s %s lewat jadwal (%d hari) - status %s"
                                    % (m["kode"], m["nama"], -sisa, m["status"])))
        elif sisa <= 3:
            hasil.append(dict(level="Kuning", objek=m["kode"],
                              pesan="%s %s %s (H-%d) - status %s"
                                    % (m["kode"], m["nama"],
                                       "besok" if sisa == 1 else ("hari ini" if sisa == 0 else "3 hari lagi"),
                                       sisa, m["status"])))

    for r in rows("SELECT * FROM risiko"):
        if (r["k"] or 0) * (r["d"] or 0) >= risiko_merah:
            hasil.append(dict(level="Merah", objek=r["id"],
                              pesan="Risiko %s skor %d (K%d x D%d) - wajib dilaporkan ke KPA 1 x 24 jam"
                                    % (r["id"], (r["k"] or 0) * (r["d"] or 0), r["k"], r["d"])))

    for p in rows("SELECT * FROM paket WHERE catatan LIKE '%[PERIKSA%'"):
        hasil.append(dict(level="Kuning", objek="Data paket %d" % p["no"],
                          pesan="Butir [PERIKSA] pada paket %s - perlu konfirmasi Urkeu/PPK" % p["nama"]))
    return hasil


# ------------------------------------------------------- status lampiran ----
def status_lampiran():
    """Membaca checklist .md dan menyimpulkan status tiap lampiran L-01..L-15."""
    if not os.path.exists(CHECKLIST_MD):
        return []
    with open(CHECKLIST_MD, encoding="utf-8") as fh:
        teks = fh.read()
    bagian = []
    for blok in teks.split("\n### ")[1:]:
        judul = blok.split("\n", 1)[0].strip()
        isi = blok.split("\n### ", 1)[0]
        if not judul[:3].startswith("L-"):
            continue
        kode = judul.split(".")[0].strip()
        isi = blok.split("\n### ", 1)[0]
        rendah = isi.lower()
        if "[TETAPKAN]" in isi or "[VERIFIKASI" in isi:
            status = "Perlu keputusan/verifikasi"
        elif "[PERIKSA" in isi:
            status = "Perlu verifikasi data"
        elif "[ISI" in isi:
            status = "Perlu diisi"
        elif ("perlu diisi" in rendah or "perlu dilengkapi" in rendah
              or "perlu ditetapkan" in rendah or "dapat diisikan" in rendah
              or "perlu diisi" in rendah):
            status = "Perlu diisi (prosa)"
        elif "selesai" in rendah or "sudah terisi" in rendah:
            status = "Terisi"
        else:
            status = "Perlu ditelaah"
        bagian.append(dict(kode=kode, judul=judul, status=status,
                           periksa=isi.count("[PERIKSA"), isi=isi.count("[ISI")))
    return bagian


# ------------------------------------------------------------------ seed ----
def _seed():
    garam_default = "satria"
    pengguna = [
        ("kpa", "Brigjen Pol Didi Hayamansyah, S.H., S.I.K., M.H. (Kapuslitbang Polri - KPA)", "kpa", None),
        ("urkeu", "Wilhelmus Sanga, S.E., M.M. (Kaurkeu - Bendahara/Urkeu)", "urkeu", None),
        ("pokja", "Pokja Data dan Instrumen SATRIA", "pokja", None),
        ("ppk1", "KBP Caterina (PPK Laboratorium)", "ppk", "1"),
        ("ppk2", "IPTU Kristo (PPK Gedung & Peralatan Fungsional)", "ppk", "2,3"),
        ("ppk3", "AKP Handono (PPK Jasa Keamanan & Kebersihan)", "ppk", "4"),
        ("ppk4", "AKBP Septi (PPK SPBE & Website)", "ppk", "5"),
        ("ppk5", "AKP Gustika (PPK Rutin Kendaraan & Peralatan)", "ppk", "6"),
    ]
    for nama, lengkap, peran, paket_id in pengguna:
        garam = garam_default + nama
        run("INSERT INTO pengguna(nama_pengguna, nama, peran, paket_id, garam, hash, aktif) "
            "VALUES (?,?,?,?,?,?,1)",
            (nama, lengkap, peran, paket_id, garam, _hash(KATA_SANDI_BAWAAN, garam)))

    paket = [
        (1, "Peralatan Uji Laboratorium Litbangyasa (3 paket)", 300000000000, 260356756687, 269911522000,
         "KBP Caterina", "SPPB/1/II/2026; SPPB/2/II/2026; SPPB/3/II/2026", "",
         "Kartu Kendali Juli 2026; OM-SPAN 28-09-2026"),
        (2, "Pemeliharaan Gedung Kantor", 1983405172, 1983405172, 1090872844,
         "IPTU Kristo", "SPPBJ/5/IV/2026", "",
         "Kartu Kendali Juli 2026; OM-SPAN 28-09-2026"),
        (3, "Pemeliharaan Peralatan Fungsional", 1964584050, 1964584050, 982292025,
         "IPTU Kristo", "SPPBJ/6/IV/2026", "",
         "Kartu Kendali Juli 2026; OM-SPAN 28-09-2026"),
        (4, "Jasa Keamanan dan Kebersihan", 855221000, 855221000, 427610500,
         "AKP Handono", "SPPB/09/III/2026", "",
         "Kartu Kendali Juli 2026; OM-SPAN 28-09-2026"),
        (5, "Pemeliharaan Software/Hardware SPBE dan Website", 895864000, 895864000, 407649000,
         "AKBP Septi", "SPPB/30/II/2026",
         "[PERIKSA] selisih pagu Rp895.864.000 vs nilai kontrak Rp748.140.000 (Rp147.724.000) "
         "- rekonsiliasi Urkeu/PPK",
         "Kartu Kendali Juli 2026; OM-SPAN 28-09-2026"),
        (6, "Pemeliharaan Kendaraan R4/6/10, R2/3 dan Peralatan Kantor", 732074000, 732074000, 289334820,
         "AKP Gustika (PPK Rutin)", "",
         "[PERIKSA] paket rutin tidak tercantum pada ekspor monitoring kontrak OM-SPAN 28-09-2026 "
         "- nomor dokumen & metode perlu konfirmasi PPK",
         "Kartu Kendali Juli 2026 (RKAKL Rev.2 2026: kendaraan R4/6/10 21 unit, R2/3 2 unit)"),
    ]
    for p in paket:
        run("INSERT INTO paket(no,nama,pagu,target,realisasi,ppk,kontrak,catatan,sumber) "
            "VALUES (?,?,?,?,?,?,?,?,?)", p)

    kontrak = [
        ("SPPB/09/III/2026/PPK-PUSLITBANG", "FAISAL NAMIRA ABADI", "25 Maret 2026", "25 Maret 2026",
         "31 Desember 2026", "PENGADAAN TENAGA JASA KEAMANAN DAN KEBERSIHAN PUSLITBANG POLRI T.A. 2026",
         855221000, 427610500, 427610500, "BELUM SELESAI", 4),
        ("SPPB/1/II/2026/PUSLITBANG", "MARACIPTA UTAMA", "10 Februari 2026", "10 Februari 2026",
         "08 Agustus 2026", "PENGADAAN PERALATAN UJI LABORATORIUM RISET MOBILE SATKER PUSLITBANG POLRI TAHUN ANGGARAN 2026",
         99751680000, 99751680000, 0, "SELESAI TEPAT WAKTU", 1),
        ("SPPB/2/II/2026/PUSLITBANG", "MARACIPTA UTAMA", "10 Februari 2026", "10 Februari 2026",
         "08 Agustus 2026", "PENGADAAN PERALATAN LABORATORIUM UJI TEST BENCH MOBILE SATKER PUSLITBANG POLRI T.A. 2026",
         99716800000, 99716800000, 0, "SELESAI TEPAT WAKTU", 1),
        ("SPPB/3/II/2026/PUSLITBANG", "MARACIPTA UTAMA", "10 Februari 2026", "10 Februari 2026",
         "08 Agustus 2026", "PENGADAAN PERALATAN LABORATORIUM UJI PENETRATION TESTING MOBILE SATKER PUSLITBANG POLRI",
         99749700000, 99749700000, 0, "SELESAI TEPAT WAKTU", 1),
        ("SPPB/30/II/2026/PPK-PUSLITBANG", "PT.SOLU FILANTROPI TEKNOLOGI", "13 Februari 2026",
         "13 Februari 2026", "31 Desember 2026",
         "PENGADAAN PEMELIHARAAN JARINGAN (SOFTWARE SPBE, HARDWARE SPBE DAN PEMELIHARAAN WEBSITE PUSLITBANG POLRI T.A. 2026",
         748140000, 374070000, 374070000, "BELUM SELESAI", 5),
        ("SPPBJ/5/IV/2026/PPK/PUSLITBANG", "GARATJIPTA LAUTAN BERLIAN", "02 April 2026", "02 April 2026",
         "08 Desember 2026", "PEMELIHARAAN GEDUNG KANTOR PUSLITBANG POLRI T.A. 2026",
         1983405172, 1090872844, 892532328, "BELUM SELESAI TERLAMBAT TERMIN", 2),
        ("SPPBJ/6/IV/2026/PPK/PUSLITBANG", "PRO SOLUSI INDONESIA", "10 April 2026", "10 April 2026",
         "06 Desember 2026", "PEMELIHARAAN PERALATAN FUNGSIONAL PUSLITBANG POLRI T.A. 2026",
         1964584050, 982292025, 982292025, "BELUM SELESAI TERLAMBAT TERMIN", 3),
    ]
    sql_kontrak = (
        "INSERT INTO kontrak(nomor,supplier,tanggal_kontrak,mulai,selesai,uraian,nilai,dibayar,"
        "sisa,status,paket_no,sumber) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)")
    for k in kontrak:
        run(sql_kontrak, k + ("OM-SPAN Monitoring Data Kontrak unduh 28-09-2026",))

    anggaran = [
        ("Juli 2026", "AGREGAT", "GRAND TOTAL ANGGARAN PUSLITBANG POLRI TA 2026",
         333636862000, 286218428959, 47418433041, 85.787411871473608,
         "Realisasi Anggaran Puslitbang Polri Juli 2026 06082026.xlsx, sheet 'Realisasi Juli sd 2026', baris GRAND TOTAL"),
        ("Juni 2026", "AGREGAT", "GRAND TOTAL ANGGARAN PUSLITBANG POLRI TA 2026",
         333720245000, 280440470703, 53279774297, 84.034599310269599,
         "Realisasi Anggaran Puslitbang Polri Juli 2026 06082026.xlsx, sheet 'Realisasi Juni sd 2026'"),
        ("Juli 2026", "BAGIAN", "Bagian Urkeu", 15167126000, 9208543386, 5958582614, 60.713831915156504,
         "xlsx sheet 'Realisasi Juli sd 2026', baris 'URKEU Bel Barang dan Pegawai TOTAL'"),
        ("Juni 2026", "BAGIAN", "Bagian Urkeu", 15214980000, 4870390370, 10344589630, 32.01049472296382,
         "xlsx sheet 'Realisasi Juni sd 2026', baris 'URKEU Bel Barang dan Pegawai TOTAL'"),
        ("Juli 2026", "JENIS", "Belanja Pegawai", 13039798000, 8312636161, 4727161839, 63.748197334038458,
         "xlsx sheet 'Realisasi Juli sd 2026', baris 'Gaji dan Tunjangan' (jumlah pagu 3 jenis = pagu GRAND TOTAL)"),
        ("Juli 2026", "JENIS", "Belanja Barang", 20597064000, 7994270798, 12602793202, 38.812311780247867,
         "LPP Bab III & xlsx (selisih pagu GRAND TOTAL - modal - pegawai)"),
        ("Juli 2026", "JENIS", "Belanja Modal", 300000000000, 269911522000, 30088478000, 89.97050733333333,
         "xlsx sheet 'Realisasi Juli sd 2026' & RKAKL (pagu modal Rp300.000.000.000)"),
    ]
    for a in anggaran:
        run("INSERT INTO anggaran(periode,kategori,uraian,pagu,realisasi,sisa,persen,sumber) "
            "VALUES (?,?,?,?,?,?,?,?)", a)

    ikpa = [("Februari 2026", 1, 98.92), ("Maret 2026", 2, 95.63), ("April 2026", 3, 97.67),
            ("Mei 2026", 4, 96.08), ("Juni 2026", 5, 95.58), ("Juli 2026", 6, 94.38)]
    for bulan, urutan, nilai in ikpa:
        run("INSERT INTO ikpa(bulan, urutan, nilai, sumber, verifikasi) VALUES (?,?,?,?,?)",
            (bulan, urutan, nilai, "Screenshot SPAN - file PDF Nilai IKPA %s" % bulan,
             "TERVERIFIKASI 3 Oktober 2026 (verifikasi visual penulis; citra 204x206 px tidak terbaca OCR)"))

    risiko = [
        ("R-01", "Pengadaan barang/jasa",
         "Perlambatan belanja barang: lelang terlambat, dokumen tidak siap",
         "Realisasi Semester I rendah; penumpukan akhir tahun", "SOP Kontraktual 2025",
         3, 4, "Percepatan Pra-DIPA, inventarisasi paket, checklist", "PPK", "Desember 2026",
         "Realisasi sd. Juli 2026 85,79%; monitoring kontrak OM-SPAN (7 kontrak terunggah)"),
        ("R-02", "Kesiapan dokumen pengadaan", "Keterlambatan KAK/spek teknis/HPS",
         "Paket tidak dapat dilelang", "Checklist manual", 2, 3,
         "Jadwal kesiapan dini; monitoring bulanan", "Unit/PPK", "November 2026",
         "Checklist kesiapan paket pengadaan dini TA 2027"),
        ("R-03", "Pelaksana (kultur kerja)", "Delaying habit/keraguan PPK memulai",
         "Penundaan tahapan pengadaan", "SOP kontraktual", 3, 3,
         "Pendampingan, contoh pengisian, Komitmen Kerja Bersama", "Project Leader", "Oktober 2026",
         "Pendampingan berjalan; 2 kontrak pemeliharaan terlambat termin"),
        ("R-04", "Pembayaran/SPJ", "Keterlambatan dokumen SPJ/spesifikasi",
         "Pembayaran tertunda; realisasi menumpuk", "Checklist PJ keuangan", 2, 3,
         "Rekonsiliasi berkala; pengingat tenggat", "Bendahara/BPP", "Bulanan",
         "Rekonsiliasi SP2D dengan KPPN berjalan"),
        ("R-05", "Kepemimpinan (KPA)", "Transisi/mutasi KPA, keputusan tertunda",
         "Business continuity terganggu", "Belum ada prosedur transisi", 2, 4,
         "SOP mitigasi transisi, berkas serah terima", "Sespuslitbang", "Saat transisi/mutasi",
         "SOP mitigasi transisi disusun (draf)"),
        ("R-06", "Perencanaan anggaran", "Perubahan kebijakan/revisi anggaran",
         "Penyesuaian rencana dan pagu", "RKAKL revisi", 2, 3,
         "Pemutakhiran daftar paket dan kartu", "Subbag REN", "Saat revisi diterbitkan",
         "Revisi DIPA ke-5 posting 16-09-2026"),
    ]
    for r in risiko:
        run("INSERT INTO risiko(id,sasaran,risiko,dampak,pengendalian,k,d,mitigasi,pic,tenggat,status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)", r)

    milestone = [
        ("M1", "Pembentukan Tim Efektif", "2026-09-10", "Terlaksana",
         "Sprin Tim Efektif Sprin/1022/VIII/HUM.10.2/2026 (18 September 2026); Sprin terbit 18 September 2026 (sesuai A.8 Log Activity & Checklist PROPER)",
         "Surat Perintah Sprin TIM EFEKTIF.pdf; Sprin TIM POKJA.pdf"),
        ("M2", "Pembuatan output proyek perubahan", "2026-09-22", "Terlaksana",
         "3 output tersedia: SOP, Risk Register, Kartu Kendali (draf untuk ditelaah)",
         "Folder 3 Pilar Output SATRIA (3 dokumen .docx)"),
        ("M3", "Uji coba instrumen", "2026-10-04", "Dijalankan",
         "[ISI hasil uji coba - 4 Oktober 2026]", "[ISI bukti: foto, daftar hadir, form uji coba L-07B]"),
        ("M4", "Analisis evaluasi", "2026-10-16", "Terjadwal",
         "[ISI catatan hasil analisis evaluasi]", "[ISI bukti]"),
        ("M5", "Penetapan SATRIA sebagai inovasi", "2026-10-28", "Terjadwal",
         "[ISI dokumen penetapan (nomor SK, tanggal, pejabat pengesah)]", "[ISI bukti]"),
        ("M6", "Kembali ke Pusdikmin & sidang LPP", "2026-11-09", "Terjadwal",
         "[ISI catatan hasil] - sidang LPP 10 November 2026, penutupan 12 November 2026",
         "[ISI bukti]"),
    ]
    for m in milestone:
        run("INSERT INTO milestone(kode,nama,tanggal,status,hasil,eviden) VALUES (?,?,?,?,?,?)", m)

    setelan_awal = [
        ("ikpa_merah", 95, "IKPA di bawah nilai ini = merah"),
        ("ikpa_kuning", 97, "IKPA di bawah nilai ini = kuning"),
        ("capaian_merah", 50, "Capaian realisasi terhadap target s.d. bulan (%): di bawah ini = merah"),
        ("capaian_kuning", 80, "Capaian (%): di bawah ini = kuning"),
        ("risiko_merah", 10, "Skor risiko (KxD) di atas/sama dengan nilai ini = merah (eskalasi KPA 1x24 jam)"),
        ("risiko_kuning", 5, "Skor risiko: di atas/sama dengan nilai ini = kuning"),
    ]
    for k, v, ket in setelan_awal:
        set_setelan(k, v, ket)

    audit("sistem", "Inisialisasi database", "data awal dari dokumen sumber terverifikasi")


SKEMA = """
CREATE TABLE IF NOT EXISTS pengguna(
  nama_pengguna TEXT PRIMARY KEY, nama TEXT NOT NULL, peran TEXT NOT NULL,
  paket_id TEXT, garam TEXT NOT NULL, hash TEXT NOT NULL, aktif INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS paket(
  no INTEGER PRIMARY KEY, nama TEXT, pagu INTEGER, target INTEGER, realisasi INTEGER,
  ppk TEXT, kontrak TEXT, catatan TEXT, sumber TEXT, diperbarui TEXT);
CREATE TABLE IF NOT EXISTS kontrak(
  id INTEGER PRIMARY KEY AUTOINCREMENT, nomor TEXT UNIQUE, supplier TEXT,
  tanggal_kontrak TEXT, mulai TEXT, selesai TEXT, uraian TEXT,
  nilai INTEGER, dibayar INTEGER, sisa INTEGER, status TEXT,
  paket_no INTEGER, sumber TEXT);
CREATE TABLE IF NOT EXISTS anggaran(
  id INTEGER PRIMARY KEY AUTOINCREMENT, periode TEXT, kategori TEXT, uraian TEXT,
  pagu INTEGER, realisasi INTEGER, sisa INTEGER, persen REAL, sumber TEXT,
  UNIQUE(periode, kategori, uraian));
CREATE TABLE IF NOT EXISTS file_impor(
  id INTEGER PRIMARY KEY AUTOINCREMENT, jenis TEXT NOT NULL, format TEXT,
  nama_file TEXT NOT NULL, isi BLOB NOT NULL, periode TEXT,
  ringkasan TEXT, pengimpor TEXT, waktu TEXT);
CREATE TABLE IF NOT EXISTS ikpa(
  bulan TEXT PRIMARY KEY, urutan INTEGER, nilai REAL, sumber TEXT, verifikasi TEXT);
CREATE TABLE IF NOT EXISTS risiko(
  id TEXT PRIMARY KEY, sasaran TEXT, risiko TEXT, dampak TEXT, pengendalian TEXT,
  k INTEGER, d INTEGER, mitigasi TEXT, pic TEXT, tenggat TEXT, status TEXT,
  diperbarui TEXT);
CREATE TABLE IF NOT EXISTS milestone(
  kode TEXT PRIMARY KEY, nama TEXT, tanggal TEXT, status TEXT, hasil TEXT, eviden TEXT);
CREATE TABLE IF NOT EXISTS keputusan(
  id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT, pengguna TEXT, objek TEXT,
  opsi TEXT, dasar TEXT, tenggat TEXT);
CREATE TABLE IF NOT EXISTS audit(
  id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT, pengguna TEXT, aksi TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS pengaturan(
  kunci TEXT PRIMARY KEY, nilai TEXT, keterangan TEXT);
"""


def init():
    os.makedirs(DATA_DIR, exist_ok=True)
    with connect() as con:
        con.executescript(SKEMA)
        con.commit()
    if one("SELECT COUNT(*) AS n FROM pengguna")["n"] == 0:
        _seed()


if __name__ == "__main__":
    init()
    print("Database siap:", DB_PATH)
    print("Paket:", len(rows("SELECT * FROM paket")),
          "| Kontrak:", len(rows("SELECT * FROM kontrak")),
          "| Risiko:", len(rows("SELECT * FROM risiko")),
          "| Milestone:", len(rows("SELECT * FROM milestone")))
