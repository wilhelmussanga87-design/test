# -*- coding: utf-8 -*-
"""Verifikasi keadaan DB bersih pasca uji."""
import db

print("sisa uji -> "
      "keputusan_uji:", len(db.rows("SELECT * FROM keputusan WHERE dasar LIKE '%Uji coba%'")),
      "| anggaran_uji:", len(db.rows("SELECT * FROM anggaran WHERE periode LIKE 'Uji Bulan%'")),
      "| audit_uji:", len(db.rows("SELECT * FROM audit WHERE aksi LIKE '%Uji coba%'")))
print("keputusan total:", len(db.rows("SELECT * FROM keputusan")))
print("ambang ikpa_merah:", db.float_setelan("ikpa_merah", 0))
print("sandi kpa bawaan sah:", db.verifikasi_login("kpa", "satria2026") is not None)
print("paket2 realisasi:", db.one("SELECT realisasi, catatan FROM paket WHERE no=2"))
print("R-02:", db.one("SELECT k, d, status, diperbarui FROM risiko WHERE id='R-02'"))
print("angka Juli agregat:", db.one("SELECT pagu, realisasi FROM anggaran "
                                    "WHERE kategori='AGREGAT' AND periode LIKE 'Juli%'"))