@echo off
rem ============================================================
rem  DEMO BANDUNG - Dashboard Pengendalian SATRIA Puslitbang
rem  Jalankan file ini sebelum presentasi seminar LPP.
rem  Aplikasi berjalan 100%% offline di laptop ini.
rem ============================================================
setlocal
set "PORT=8505"
set "URL=http://127.0.0.1:%PORT%"
cd /d "%~dp0"
set "PYTHON=py"
where py >nul 2>&1
if errorlevel 1 (
  set "PYTHON=C:\Users\sanga\AppData\Local\Programs\Python\Python312\python.exe"
)
if /i not "%PYTHON%"=="py" if not exist "%PYTHON%" (
  echo.
  echo [X] Python tidak ditemukan.
  echo.
  echo Gunakan laptop ini - sudah terpasang Python + Streamlit,
  echo atau instal Python 3.12 dan jalankan: pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

rem --- bila server sudah menyala, langsung buka browser ---
powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
if not errorlevel 1 goto :buka

echo.
echo Menyalakan Dashboard SATRIA (mode offline)...
start "SATRIA Dashboard - Demo Bandung" cmd /k call "%PYTHON%" -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port %PORT% --browser.gatherUsageStats false --client.toolbarMode minimal

echo Menunggu server siap...
powershell -NoProfile -Command "$u='%URL%/_stcore/health'; for($i=0;$i -lt 40;$i++){ try{ $r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 2; if($r.StatusCode -eq 200){ exit 0 } }catch{}; Start-Sleep -Milliseconds 500 }; exit 1"
if errorlevel 1 (
  echo.
  echo [X] Server belum siap. Periksa jendela "SATRIA Dashboard - Demo Bandung".
  echo.
  pause
  exit /b 1
)

:buka
echo Membuka dashboard di browser (mode aplikasi)...
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
  start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="%URL%" --start-maximized
) else if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
  start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app="%URL%" --start-maximized
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
  start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="%URL%" --start-maximized
) else (
  start "" "%URL%"
)

echo.
echo ============================================================
echo  Dashboard siap: %URL%
echo  Login demo: kpa / satria2026
echo  Tekan F11 pada browser untuk layar penuh (proyektor).
echo ============================================================
echo.
echo Jendela ini boleh ditutup; server tetap berjalan.
echo Untuk mematikan server, tutup jendela "SATRIA Dashboard - Demo Bandung".
echo.
pause >nul
endlocal
