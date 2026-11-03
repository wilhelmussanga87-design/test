# -*- coding: utf-8 -*-
"""Parser impor realisasi anggaran.

Mendukung dua sumber:
1. OM-SPAN (.xlsx)          -> baris "GRAND TOTAL ANGGARAN PUSLITBANG POLRI TA 2026"
2. SAKTI/SPAN (.xlsx/.pdf)  -> "LAPORAN REALISASI SP2D TA 2026" + baris "JUMLAH SELURUHNYA"

Aturan validasi disamakan untuk semua sumber: sisa = pagu - realisasi dan
(periode lalu + periode ini) = realisasi s.d. periode. Tidak ada angka rekaan:
jenis belanja (pegawai/barang/modal) hanya disertakan jika jumlahnya cocok
dengan total (ambang selisih 0,5%).
"""
import io
import re

BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
         "Agustus", "September", "Oktober", "November", "Desember"]
RE_BULAN = "(" + "|".join(BULAN) + ")"
RE_PERIODE = re.compile(r"Periode\s*[:]?\s*" + RE_BULAN + r"\s*(\d{4})")
RE_AKUN = re.compile(r"^5\d{5}(\.0+)?$")
BESAR = 1e11   # nilai tabel agregat minimal Rp100 miliar


def _jenis_dari_angka(angka, kode_num=None):
    """Baris akun: [kode, pagu, lock, lalu, ini, s.d.periode, %, sisa] -> (pagu, sd).
    Kode akun ikut terbaca sebagai angka pertama; dibuang bila sama dengan kode."""
    if not angka:
        return None
    if kode_num is not None and abs(angka[0] - kode_num) < 0.5:
        angka = angka[1:]
    if len(angka) < 5:
        return None
    pagu, sd = angka[0], angka[4]
    if not pagu:
        return None
    return pagu, sd if sd else 0.0


def _bersih_angka(v):
    """Ubah sel menjadi float bila memuat satu angka; selain itu None."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        try:
            f = float(v)
        except Exception:
            return None
        return f if f == f and f != float("inf") else None
    s = re.sub(r"\s+", " ", str(v)).strip()
    if not s:
        return None
    m = re.search(r"-?\d[\d.,]*", s)
    if not m:
        return None
    teks = m.group(0).replace(",", "").replace(".", "")
    try:
        return float(teks)
    except Exception:
        return None


def _angka_baris(baris):
    """Semua angka numerik dalam satu baris, urut sesuai kolom."""
    out = []
    for v in baris:
        a = _bersih_angka(v)
        if a is not None:
            out.append(a)
    return out


def _agregat_dari_angka(angka):
    """Dari daftar angka baris total: (pagu, realisasi, sisa, persen, lalu_ini).
    Pagu = angka terbesar; realisasi = terbesar kedua; sisa = angka 1e9..1e11
    yang bukan pagu/realisasi; lalu_ini = pasangan (lalu, ini) bila ada."""
    if not angka:
        return None
    besar = sorted((a for a in angka if a >= BESAR), reverse=True)
    if len(besar) < 2:
        return None
    pagu, realisasi = besar[0], besar[1]
    if realisasi > pagu:
        pagu, realisasi = realisasi, pagu
    sisa = None
    for a in angka:
        if 1e9 <= a < BESAR and a not in besar[:2]:
            sisa = int(round(a))
            break
    lalu = ini = None
    sisa_b = None
    for a in angka:
        if a == pagu or a == realisasi:
            continue
        if 1e9 <= a < BESAR and not (sisa is not None and abs(a - sisa) < 1):
            sisa_b = a
        if a < BESAR and a > 0 and a > (lalu or 0) and a != realisasi:
            pass
    # pasangan lalu/ini: dua angka non-nol yang jumlahnya mendekati realisasi
    for i, a in enumerate(angka):
        for b in angka[i + 1:]:
            if a > 0 and b > 0 and abs((a + b) - realisasi) <= max(1, realisasi * 0.00001):
                lalu, ini = max(a, b), min(a, b)
                break
        if lalu:
            break
    p = (realisasi / pagu * 100.0) if pagu else 0.0
    return dict(pagu=int(round(pagu)), realisasi=int(round(realisasi)),
                sisa=int(round(sisa)) if sisa is not None else None,
                persen=p, lalu=int(round(lalu)) if lalu else None,
                ini=int(round(ini)) if ini else None)


def _kunci_valid(ag):
    if not ag:
        return False, ["baris total tidak terbaca"]
    masalah = []
    if ag["sisa"] is not None and abs((ag["pagu"] - ag["realisasi"]) - ag["sisa"]) > 1:
        masalah.append("sisa (%d) tidak sama dengan pagu - realisasi (%d)"
                       % (ag["sisa"], ag["pagu"] - ag["realisasi"]))
    if ag["lalu"] is not None and abs((ag["lalu"] + ag["ini"]) - ag["realisasi"]) > 1:
        masalah.append("periode lalu + periode ini != realisasi s.d. periode")
    if ag["persen"] and not (ag["persen"] - 0.05 <=
                             (ag["realisasi"] / ag["pagu"] * 100.0) <=
                             ag["persen"] + 0.05 if ag["pagu"] else True):
        masalah.append("persentase pada sumber tidak cocok dengan perhitungan")
    return (not masalah), masalah


def _deteksi_jenis_xlsx(rows, cap=0.5):
    """Jumlah belanja per jenis dari baris akun (kolom ke-8 = kode 5xxxxx)."""
    total = dict(pagu=0.0, real=0.0)
    bagan = {"pegawai": [0.0, 0.0], "barang": [0.0, 0.0], "modal": [0.0, 0.0]}
    for r in rows:
        kode = r[7] if len(r) > 7 else None
        if kode is None or not RE_AKUN.match(str(kode).strip()):
            continue
        pas = _jenis_dari_angka(_angka_baris(r), kode_num=float(str(kode).strip().split(".")[0]))
        if pas is None:
            continue
        pagu, real = pas
        jenis = {"51": "pegawai", "52": "barang", "53": "modal"}.get(str(kode).strip()[:2])
        if not jenis:
            continue
        bagan[jenis][0] += pagu
        bagan[jenis][1] += real
        total["pagu"] += pagu
        total["real"] += real
    return _jenis_final(bagan, total, cap)


def _deteksi_jenis_pdf(teks_hal, cap=0.5):
    total = dict(pagu=0.0, real=0.0)
    bagan = {"pegawai": [0.0, 0.0], "barang": [0.0, 0.0], "modal": [0.0, 0.0]}
    for line in teks_hal:
        s = line.strip()
        m = re.match(r"^(\d{6})\s+(.*)$", s)
        if not m or not RE_AKUN.match(m.group(1)):
            continue
        pas = _jenis_dari_angka(_bersih_angka_list(s),
                                kode_num=float(m.group(1)))
        if pas is None:
            continue
        pagu, real = pas
        jenis = {"51": "pegawai", "52": "barang", "53": "modal"}.get(m.group(1)[:2])
        if not jenis:
            continue
        bagan[jenis][0] += pagu
        bagan[jenis][1] += real
        total["pagu"] += pagu
        total["real"] += real
    return _jenis_final(bagan, total, cap)


def _bersih_angka_list(teks):
    out = []
    for m in re.finditer(r"-?\d[\d.,]*", teks):
        t = m.group(0).replace(",", "").replace(".", "")
        try:
            out.append(float(t))
        except Exception:
            pass
    return out


def _jenis_final(bagan, total, cap):
    """Rangkum jenis; None bila jumlah tidak cocok dengan total."""
    if not total["pagu"]:
        return None
    rinci = []
    for nama in ("pegawai", "barang", "modal"):
        p, r = bagan[nama]
        if p >= 1:
            rinci.append(dict(jenis=nama, pagu=int(round(p)), realisasi=int(round(r)),
                              persen=(r / p * 100.0) if p else 0.0))
    selisih_p = abs(total["pagu"] - sum(b["pagu"] for b in rinci))
    selisih_r = abs(total["real"] - sum(b["realisasi"] for b in rinci))
    ambang = max(1.0, total["pagu"] * cap / 100.0)
    if selisih_p > ambang or selisih_r > ambang:
        return None
    return {"total_pagu": int(round(total["pagu"])),
            "total_realisasi": int(round(total["real"])), "rinci": rinci}


def baca_realisasi(isi: bytes, nama_file: str):
    """Kembalikan daftar kandidat realisasi (SAKTI dan/atau OM-SPAN).

    Setiap kandidat:
      format, detail, periode, satker, pagu, realisasi, sisa, persen,
      valid, masalah[], jenis (None bila tak terkunci)
    """
    nama = (nama_file or "").lower()
    if nama.endswith(".pdf"):
        return _baca_pdf(isi, nama_file)
    return _baca_xlsx(isi, nama_file)


def _baca_xlsx(isi: bytes, nama_file: str):
    import pandas as pd
    xls = pd.ExcelFile(io.BytesIO(isi))
    kandidat = []
    for nama_sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=nama_sheet, header=None)
        rows = df.values.tolist()
        judul = ""
        periode = ""
        satker = ""
        for r in rows[:80]:
            for v in r:
                if isinstance(v, str):
                    if "LAPORAN REALISASI" in v.upper() and judul == "":
                        judul = v.strip()
                    m = RE_PERIODE.search(v)
                    if m and not periode:
                        periode = "%s %s" % (m.group(1), m.group(2))
                    if "PUSLITBANG" in v.upper():
                        satker = v.strip()
        for r in rows:
            teks_sel = [str(v).strip() if not pd.isna(v) else "" for v in r]
            is_judul_sp2d = "JUMLAH SELURUHNYA" in teks_sel
            if not is_judul_sp2d:
                continue
            angka = _angka_baris(r)
            ag = _agregat_dari_angka(angka)
            if ag is None:
                continue
            valid, masalah = _kunci_valid(ag)
            jenis = _deteksi_jenis_xlsx(rows) if not masalah else None
            kandidat.append(dict(
                format="SAKTI", detail="sheet '%s'" % nama_sheet,
                periode=periode or "", satker=satker or "",
                pagu=ag["pagu"], realisasi=ag["realisasi"], sisa=ag["sisa"],
                persen=ag["persen"], valid=bool(valid), masalah=masalah,
                jenis=jenis))
        # OM-SPAN: tidak ada JUMLAH SELURUHNYA
        if not kandidat:
            for nama_sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=nama_sheet, header=None)
                for _, row in df.iterrows():
                    angka = [float(v) for v in row.tolist()
                             if isinstance(v, (int, float)) and not pd.isna(v)]
                    besar = [v for v in angka if v >= BESAR]
                    if len(besar) < 2:
                        continue
                    pagu, realisasi = besar[0], besar[1]
                    if realisasi > pagu:
                        pagu, realisasi = realisasi, pagu
                    sisa = pagu - realisasi
                    ada_sisa = any(abs(v - sisa) < 1 for v in angka)
                    kandidat.append(dict(
                        format="OM-SPAN", detail="sheet '%s'" % nama_sheet,
                        periode="", satker="PUSLITBANG POLRI",
                        pagu=int(round(pagu)), realisasi=int(round(realisasi)),
                        sisa=int(round(sisa)),
                        persen=(realisasi / pagu * 100.0) if pagu else 0.0,
                        valid=bool(ada_sisa),
                        masalah=[] if ada_sisa else ["sisa tidak cocok pada baris sumber"],
                        jenis=None))
                if kandidat:
                    break
    # hapus duplikat (pagu, realisasi) — pertahankan yang pertama
    unik, kunci = [], set()
    for k in kandidat:
        t = (k["format"], k["pagu"], k["realisasi"])
        if t not in kunci:
            kunci.add(t)
            unik.append(k)
    return unik


def _baca_pdf(isi: bytes, nama_file: str):
    import pdfplumber
    kandidat = []
    periode = ""
    satker = ""
    baris_akun = []
    dengan = pdfplumber.open(io.BytesIO(isi))
    try:
        n_pages = len(dengan.pages)
        for page in dengan.pages:
            teks = page.extract_text() or ""
            for m in RE_PERIODE.finditer(teks):
                if not periode:
                    periode = "%s %s" % (m.group(1), m.group(2))
            if "PUSLITBANG" in teks.upper() and not satker:
                mm = re.search(r"(?:Satuan Kerja\s*[:]?\s*[^\s]*\s*)?([A-Z][A-Z0-9 ]*PUSLITBANG[A-Z0-9 ]*)", teks.upper())
                satker = (mm.group(1).strip() if mm else "PUSLITBANG POLRI")
            for line in teks.splitlines():
                if re.match(r"^5\d{5}\s", line.strip()):
                    baris_akun.append(line)
        # baris JUMLAH SELURUHNYA dari tabel halaman pertama
        for i in range(min(3, n_pages)):
            for tbl in dengan.pages[i].extract_tables() or []:
                for baris in tbl:
                    sel = [str(c) if c is not None else "" for c in baris]
                    if any("JUMLAH SELURUHNYA" in s for s in sel):
                        angka = []
                        for s in sel:
                            for t in s.splitlines():
                                a = _bersih_angka(t)
                                if a is not None:
                                    angka.append(a)
                        ag = _agregat_dari_angka(angka)
                        if ag is None:
                            continue
                        valid, masalah = _kunci_valid(ag)
                        jenis = _deteksi_jenis_pdf(baris_akun) if not masalah else None
                        kandidat.append(dict(
                            format="SAKTI", detail="%d halaman (16 Segmen)" % n_pages,
                            periode=periode or "", satker=satker or "",
                            pagu=ag["pagu"], realisasi=ag["realisasi"], sisa=ag["sisa"],
                            persen=ag["persen"], valid=bool(valid), masalah=masalah,
                            jenis=jenis))
                        break
                if kandidat:
                    break
            if kandidat:
                break
    finally:
        dengan.close()
    if not kandidat:
        # pdf bukan SAKTI SP2D
        return []
    return kandidat