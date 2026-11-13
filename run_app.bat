@echo off
title Dasbor Benchmark Komputasi Paralel Konvolusi Citra
cd /d "%~dp0"
echo Menjalankan aplikasi Streamlit di direktori: %CD%
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app_komputasi_paralel.py
) else (
    python -m streamlit run app_komputasi_paralel.py
)
pause
