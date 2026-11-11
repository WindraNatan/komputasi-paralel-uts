# Komputasi Paralel — Analisis Performa Filter Konvolusi & Upscaling Citra

**Perbandingan kinerja CPU multi-thread vs GPU CUDA** untuk filter konvolusi 3×3 (Sobel, Gaussian blur, sharpening) dan peningkatan resolusi citra (Nearest Neighbor, Bilinear, Bicubic) pada resolusi 1080p, 4K, dan 8K.

Tugas UTS mata kuliah **Komputasi Paralel** — Program Studi Rekayasa Sistem Komputer, FMIPA Universitas Tanjungpura.

## Tim

| Nama | NIM |
|---|---|
| Alfonso Andrano | H1051241031 |
| Windra Maxwall Dari Natalius | H1051241073 |
| Rizal Saputra | H1051241095 |
| Muhammad Rifqi Maulana | H1051241101 |

## Ringkasan Proyek

- **Objek uji**: konvolusi (Sobel, Gaussian, Sharpen) & upscaling (Nearest, Bilinear, Bicubic)
- **Resolusi**: 1080p, 4K, 8K (citra DIV2K valid HR, 100 citra)
- **Platform**: CPU Intel Core 5 210H (4 P-core ber-SMT, dikunci topeng 0xFF) vs GPU NVIDIA RTX 3050 Laptop
- **Metode**: benchmark terkontrol, median 100 citra, speedup dihitung per citra lalu diambil median
- **Hasil utama**:
  - Gaussian 8K: CPU 8 thread ~3,44× lebih cepat dari 1 thread; GPU total 7,03×
  - Sobel 8K: kernel GPU 4,44× lebih cepat dari CPU 1 thread, tapi total hanya 1,25× (didominasi transfer)
  - Upscaling 8K: GPU bilinear mencapai 10,89× dari CPU 1 thread (1080p→8K)
  - Max diff CPU vs GPU = 0 (konvolusi) / ≤4,7×10⁻¹⁰ (upscaling)

## Struktur

```
├── benchmark_v2.py              # Benchmark utama (CPU 1/2/4/8 thread + GPU)
├── benchmark_8k.py              # Benchmark citra 8K
├── kernels_paralel.py           # Kernel konvolusi & interpolasi
├── app_komputasi_paralel.py     # Dashboard Streamlit
├── prepare_dataset_uji.py       # Siapkan citra uji dari DIV2K (Lanczos)
├── generate_laporan_docx.py     # Generator laporan .docx
├── run_app.bat / bench.bat      # Jalankan dashboard / benchmark
├── hasil_*.csv                  # Data pengukuran mentah
├── REKAP_BENCHMARK.md           # Angka kanonik rekap benchmark
├── Laporan_UTS_Komputasi_Paralel.docx
└── Proposal_Tugas_Akhir_ReSiskom_Untan.docx
```

## Menjalankan

### Prasyarat

- Python 3.14, Numba, PIL, python-docx, Streamlit
- NVIDIA CUDA Toolkit (folder `cuda_toolkit/` dibaca via `CUDA_HOME`; tidak dibundel)
- Dataset DIV2K valid HR (tidak disertakan; unduh dari [sumber resmi](https://data.vision.ee.ethz.ch/cvl/DIV2K/) → `DIV2K_valid_HR/`)

### Siapkan citra uji

```bash
python prepare_dataset_uji.py
```

### Benchmark

```bash
python benchmark_v2.py
# atau via batch dengan afinitas 4 P-core + prioritas tinggi:
bench.bat
```

### Dashboard Streamlit

```bash
run_app.bat
# atau: streamlit run app_komputasi_paralel.py
```

## Peringatan

- Dataset DIV2K (449 MB) dan citra uji turunan tidak disertakan karena ukuran; silakan unduh/siapkan ulang.
- CUDA Toolkit tidak dibundel karena lisensi dan ukuran.
