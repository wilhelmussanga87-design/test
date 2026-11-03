@echo off
rem ============================================================
rem  SATRIA Dashboard - Pengendalian & Pengambilan Keputusan
rem  Klik dua kali file ini, lalu buka http://localhost:8501
rem  Pengguna lain di LAN & HP (Wi-Fi/LAN kantor): buka http://<IP-komputer-ini>:8501
rem  Pertama kali: izinkan port 8501 di firewall Windows (PowerShell admin):
rem    New-NetFirewallRule -DisplayName "SATRIA 8501" -Direction Inbound -Protocol TCP -LocalPort 8501 -Action Allow
rem ============================================================
set PYTHON=C:\Users\sanga\AppData\Local\Programs\Python\Python312\python.exe
cd /d "%~dp0"

if not exist "%PYTHON%" (
  echo Python tidak ditemukan di %PYTHON%
  echo Instal Python 3.12 lalu ulangi.
  pause
  exit /b 1
)

echo Memulai SATRIA Dashboard di http://localhost:8501 (akses LAN 0.0.0.0:8501)
echo Tekan Ctrl+C untuk menghentikan server.
"%PYTHON%" -m streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false
pause