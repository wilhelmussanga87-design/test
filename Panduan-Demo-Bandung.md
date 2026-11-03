# Panduan Demo Bandung - Seminar LPP

Dashboard SATRIA Puslitbang berjalan **lokal/offline**. Tidak perlu internet
saat presentasi. Cukup laptop ini, proyektor, dan file aplikasi yang lengkap.

## 1. Sebelum berangkat

- [ ] Salin seluruh folder `6. Dashboard Pengendalian SATRIA` (jangan hanya `app.py`).
- [ ] Pastikan ikut tersalin: `data\satria.db`, `assets\`, `.streamlit\`, `db.py`, `impor.py`.
- [ ] Buat cadangan data: buka **Pengaturan & Audit > Salin basis data ke folder backup**,
      atau salin manual `data\satria.db` ke flashdisk.
- [ ] Uji sekali di rumah/kantor dengan **Wi-Fi dimatikan**:
      klik dua kali `Demo-Bandung.bat`, lalu login.
- [ ] Pastikan akun demo diketahui: `kpa` / `satria2026`
      (atau kata sandi yang sudah Bapak/Ibu ubah).
- [ ] Bawa charger laptop dan kabel proyektor (HDMI/USB-C).

## 2. Saat akan presentasi

1. Nyalakan laptop, **tidak perlu** menyambung internet.
2. Klik dua kali **`Demo-Bandung.bat`**.
3. Tunggu jendela hitam menampilkan "Dashboard siap".
4. Browser terbuka otomatis dalam mode aplikasi (tanpa tab/address bar).
5. Tekan **F11** untuk layar penuh, lalu login sebagai `kpa`.
6. Gunakan menu sidebar untuk berpindah halaman:
   Ringkasan KPA - Anggaran & Paket - Manajemen Risiko - Kontrak -
   Milestone & Lampiran - Keputusan KPA.

> Jika teks terasa kecil di proyektor, tekan **Ctrl + +** beberapa kali
> (zoom 110-125%) atau ubah resolusi proyektor ke 1920x1080.

## 3. Alur demo yang disarankan (10-15 menit)

1. **Ringkasan KPA** - tunjukkan pagu, realisasi, IKPA, peringatan dini,
   tren, milestone, profil risiko, dan galeri.
2. **Anggaran & Paket** - tunjukkan 6 paket sasaran dan status capaian.
3. **Manajemen Risiko** - tunjukkan matriks 5x5 dan mitigasi.
4. **Kontrak** - tunjukkan kontrak yang terlambat termin.
5. **Milestone & Lampiran** - tunjukkan status M1-M6 dan kelengkapan L-01 s.d. L-15.
6. **Keputusan KPA** - tunjukkan log keputusan (jika sudah ada).
7. Kembali ke **Ringkasan KPA** sebagai penutup.

## 4. Bila ingin diakses dari HP peserta

Ini opsional dan **hanya bisa** bila laptop + HP berada di jaringan yang sama
(Wi-Fi venue atau hotspot). Port 8505 perlu dibuka di firewall Windows sekali.
Minta bantuan panitia IT, atau gunakan hotspot pribadi dan minta satu petugas
membuka firewall dengan PowerShell Administrator:

```powershell
New-NetFirewallRule -DisplayName "SATRIA 8505" -Direction Inbound `
  -Protocol TCP -LocalPort 8505 -Action Allow
```

Lalu jalankan server dengan alamat LAN (bukan 127.0.0.1):

```bat
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8505
```

Cari IP laptop dengan `ipconfig`, lalu buka di HP:
`http://IP-LAPTOP:8505` (contoh: `http://10.184.245.197:8505`).

> Jangan menghubungkan aplikasi ini ke internet publik. Data anggaran/risiko
> sebaiknya tetap di jaringan lokal.

## 5. Bila terjadi masalah

| Gejala | Solusi |
|---|---|
| Browser tidak terbuka | Buka manual `http://127.0.0.1:8505` |
| "Python tidak ditemukan" | Gunakan laptop ini, atau instal Python 3.12 + `pip install -r requirements.txt` |
| Port 8505 sudah dipakai | Tutup jendela SATRIA lama, lalu jalankan `Demo-Bandung.bat` lagi |
| Halaman kosong/error | Tekan **R** atau muat ulang browser; cek jendela server |
| Data ingin dikembalikan | Tutup server, salin backup dari `data\backup\` menjadi `data\satria.db` |
| Dokumen 3 Pilar tidak muncul | Pastikan folder `assets\pilar\` ikut tersalin |

## 6. Checklist 5 menit sebelum tampil

- [ ] `Demo-Bandung.bat` berhasil membuka dashboard.
- [ ] Login `kpa` berhasil.
- [ ] Ringkasan KPA menampilkan angka dan grafik.
- [ ] Galeri bawah tampil (5 foto).
- [ ] Menu **Milestone & Lampiran** menampilkan lampiran L-01 s.d. L-15.
- [ ] Proyektor menampilkan layar penuh, teks terbaca dari belakang ruangan.
- [ ] Notifikasi Windows (email/chat) dimatikan agar tidak mengganggu.
