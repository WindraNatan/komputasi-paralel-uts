@echo off
title Perbaiki PATH Python (sekali jalan)
cd /d "%~dp0"
echo Menempatkan Python 3.14 (pythoncore) di depan PATH pengguna...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$py = 'C:\Users\User\AppData\Local\Python\pythoncore-3.14-64';" ^
  "$cur = [Environment]::GetEnvironmentVariable('Path', 'User');" ^
  "$parts = @($cur -split ';' | Where-Object { $_ -ne '' -and $_ -ne $py });" ^
  "[Environment]::SetEnvironmentVariable('Path', ($py + ';' + ($parts -join ';')), 'User');" ^
  "Write-Host ('PATH pengguna sekarang diawali: ' + $py) -ForegroundColor Green"
echo.
echo ============================================================
echo SELESAI.
echo 1. Tutup SEMUA jendela terminal (PowerShell/cmd), termasuk yang ini.
echo 2. Buka terminal BARU di folder proyek.
echo 3. Cek:  python -c "import numpy, numba, pandas; print('OK')"
echo Harus tercetak OK.
echo ============================================================
pause
