@echo off
REM Wrapper benchmark: Python 3.14 + proses dikunci ke prosesor logis 0-7 (mask FF)
REM sejak detik pertama, prioritas High. Topologi terverifikasi: LP 0-7 = 4 P-core
REM ber-SMT, LP 8-11 = 4 E-core; aplikasi lain (Chrome) dialokasikan ke E-core
REM sehingga tidak mengotori pengukuran.
REM Pakai dari PowerShell:  .\bench --op upscale --src-res 720p --res 1080p ...
setlocal
cd /d "%~dp0"

set "PY=C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%PY%" (
    echo [ERROR] Python 3.14 tidak ditemukan di %PY%
    exit /b 1
)

REM Pool thread numba harus = jumlah CPU pada mask (8), bukan 12 (cpu_count).
REM Harus diset SEBELUM numba dimuat, jadi lewat env var di sini.
set "NUMBA_NUM_THREADS=8"

start "" /affinity FF /high /b /wait "%PY%" benchmark_v2.py %*
set "RC=%ERRORLEVEL%"

endlocal & exit /b %RC%
