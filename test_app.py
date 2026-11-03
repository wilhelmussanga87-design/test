# -*- coding: utf-8 -*-
"""Smoke test: login tiap peran lalu buka setiap menu; laporkan exception."""
import os
import sys

from streamlit.testing.v1 import AppTest

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import db  # noqa: E402

SEMUA = ["Ringkasan KPA", "Anggaran & Paket", "Manajemen Risiko", "Kontrak",
         "Milestone & Lampiran", "Keputusan KPA", "Impor Data (SAKTI/OM-SPAN)",
         "Pengaturan & Audit"]

# Rekam posisi audit agar jejak masuk/keluar saat uji tidak tertinggal.
_awal_audit = db.one("SELECT COALESCE(MAX(id), 0) AS m FROM audit")["m"]

gagal = 0

for akun in ("kpa", "urkeu", "pokja", "ppk1", "ppk2", "ppk4"):
    at = AppTest.from_file("app.py", default_timeout=60)
    at.run()
    if at.exception:
        print("X %s: halaman masuk error %s" % (akun, at.exception))
        gagal += 1
        continue
    at.text_input[0].set_value(akun)
    at.text_input[1].set_value("satria2026")
    at.button[0].click().run()
    if at.exception:
        print("X %s: sesudah login error %s" % (akun, at.exception))
        gagal += 1
        continue
    menu_ada = [o for o in at.radio[0].options]
    for hal in menu_ada:
        at.radio[0].set_value(hal).run()
        if at.exception:
            print("X %s / %s: %s" % (akun, hal, at.exception))
            gagal += 1
        else:
            judul = at.title[0].value if at.title else "(tanpa judul)"
            print("ok %s / %s -> %s" % (akun, hal, judul[:60]))
    # logout
    if at.button:
        at.button[-1].click().run()
        if at.exception:
            print("X %s: logout error %s" % (akun, at.exception))
            gagal += 1

# login salah
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.text_input[0].set_value("kpa")
at.text_input[1].set_value("salah")
at.button[0].click().run()
if at.error:
    print("ok penolakan login salah ->", at.error[0].value[:60])
else:
    print("X login salah TIDAK ditolak")
    gagal += 1

# bersihkan jejak audit proses masuk/keluar selama uji
db.run("DELETE FROM audit WHERE id > ?", (_awal_audit,))
try:
    db.run("VACUUM")
except Exception:  # noqa: BLE001
    pass
print("\nTOTAL GAGAL:", gagal)
raise SystemExit(1 if gagal else 0)
