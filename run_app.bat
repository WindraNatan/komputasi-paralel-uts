@echo off
title Dasbor Benchmark Komputasi Paralel Konvolusi Citra
cd /d "%~dp0"
echo Menjalankan aplikasi Streamlit di direktori: %CD%
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m streamlit run app_komputasi_paralel.py
pause
