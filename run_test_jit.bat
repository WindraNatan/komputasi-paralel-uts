@echo off
title Diagnostik JIT / CUDA Numba
cd /d "%~dp0"
echo Menjalankan diagnostik kompilasi kernel JIT...
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" test_jit.py
echo.
echo ============================================================
echo Salin SELURUH teks di atas (klik kanan - tandai - tekan Enter)
echo ============================================================
pause
