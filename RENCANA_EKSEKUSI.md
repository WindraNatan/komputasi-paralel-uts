# Rencana Eksekusi UTS Komputasi Paralel

Dosen mensyaratkan: (1) pengujian dengan **puluhan/ratusan data**, (2) **produk akhir** berupa aplikasi/website.
Keduanya sudah tercakup: dataset **DIV2K valid HR (100 citra)** + **dashboard Streamlit** dengan mode batch.

## Langkah 1 — Unduh Dataset DIV2K

Unduh `DIV2K_valid_HR.zip` (100 citra resolusi tinggi, ~1.2 GB, ETH Zürich NTIRE 2017):

```
http://data.vision.ee.ethz.ch/cvl/DIV2K/DIV2K_valid_HR.zip
```

Ekstrak sehingga struktur folder menjadi:

```
D:\Kuliah\Komputasi Pararel\Proposal UTS\
├── app_komputasi_paralel.py
├── benchmark_v2.py
├── kernels_paralel.py
├── DIV2K_valid_HR\
│   ├── 0001.png
│   ├── 0002.png
│   └── ... (total 100 citra PNG)
└── cuda_toolkit\
```

## Langkah 2 — Benchmark CLI (data utama laporan)

Jalankan di laptop (colok charger, mode performa, tutup aplikasi lain):

```
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" benchmark_v2.py --op conv    --res 1080p 4k 8k --filter sharpen   --dataset DIV2K_valid_HR --out hasil_conv_sharpen.csv
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" benchmark_v2.py --op conv    --res 1080p 4k 8k --filter gaussian  --dataset DIV2K_valid_HR --out hasil_conv_gaussian.csv
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" benchmark_v2.py --op conv    --res 1080p 4k 8k --filter sobel     --dataset DIV2K_valid_HR --out hasil_conv_sobel.csv
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" benchmark_v2.py --op upscale --res 4k 8k         --method bicubic  --dataset DIV2K_valid_HR --out hasil_upscale_bicubic.csv
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" benchmark_v2.py --op upscale --res 4k 8k         --method bilinear --dataset DIV2K_valid_HR --out hasil_upscale_bilinear.csv
"C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe" benchmark_v2.py --op upscale --res 4k 8k         --method nearest  --dataset DIV2K_valid_HR --out hasil_upscale_nearest.csv
```

Catatan: `--reps` default 1 sudah memberi N=100 (tiap citra diuji sekali).
Pakai `--out` berbeda per skenario karena CSV default ditimpa setiap run.
Untuk uji citra tunggal (mode lama), ganti `--dataset DIV2K_valid_HR` dengan `--dataset peppers`
atau hilangkan argumen `--dataset`, dan tambah `--reps 10`.

Hasil tersimpan ke CSV per skenario (default: `benchmark_v2_hasil.csv`).

## Langkah 2b — Upscaling Bertingkat (syarat dosen: tiga tingkat)

Dosen meminta upscaling punya tiga tingkatan: rendah, sedang, tinggi, dengan 8K sebagai batas
maksimal penelitian. Sumber upscaling **tidak perlu dataset baru** — `to_target(img0, src_res)`
menurunkan citra DIV2K ke resolusi sumber saat runtime, sehingga ke-100 citra bisa dipakai
di semua tingkat. Folder `dataset_uji/` (30 citra per tingkat) tidak dipakai di sini.

Dua skema dijalankan keduanya, tetapi hasil yang sudah ada dipakai ulang,
jadi tinggal **6 run baru**: 720p→4K dan 720p→8K (3 metode masing-masing).
720p→1080p sudah dijalankan (ada di Langkah 2c untuk dua metode yang perlu diulang),
dan bicubic 4K→8K sudah ada di `hasil_upscale_bicubic.csv` baris res=8k.

Pakai `.\bench`, bukan path interpreter langsung, karena wrapper itu yang mengunci
proses ke 8 CPU dan men-set `NUMBA_NUM_THREADS=8`.

**Batch 1 — 720p ke 4K (paling ringan, jalankan dulu)**

```
.\bench --op upscale --src-res 720p --res 4k --method nearest  --dataset DIV2K_valid_HR --out hasil_up_720to4k_nearest.csv
.\bench --op upscale --src-res 720p --res 4k --method bilinear --dataset DIV2K_valid_HR --out hasil_up_720to4k_bilinear.csv
.\bench --op upscale --src-res 720p --res 4k --method bicubic  --dataset DIV2K_valid_HR --out hasil_up_720to4k_bicubic.csv
```

**Batch 2 — 4K ke 8K (dua metode yang belum ada)**

```
.\bench --op upscale --src-res 4k --res 8k --method nearest  --dataset DIV2K_valid_HR --out hasil_up_4kto8k_nearest.csv
.\bench --op upscale --src-res 4k --res 8k --method bilinear --dataset DIV2K_valid_HR --out hasil_up_4kto8k_bilinear.csv
```

**Batch 3 — 720p ke 8K (terberat, satu per satu, jeda 10 menit)**

```
.\bench --op upscale --src-res 720p --res 8k --method nearest  --dataset DIV2K_valid_HR --out hasil_up_720to8k_nearest.csv
.\bench --op upscale --src-res 720p --res 8k --method bilinear --dataset DIV2K_valid_HR --out hasil_up_720to8k_bilinear.csv
.\bench --op upscale --src-res 720p --res 8k --method bicubic  --dataset DIV2K_valid_HR --out hasil_up_720to8k_bicubic.csv
```

Cakupan 18 kombinasi sumber ke target setelah semua batch:

| Sumber | 1080p | 4K | 8K |
|---|---|---|---|
| 720p | ✓ | batch 1 | batch 3 |
| 1080p | — | ✓ | ✓ |
| 4K | — | — | batch 2 (bilinear, nearest), ✓ (bicubic) |

Catatan eksekusi:

- Jangan pakai `--append`; satu CSV per kombinasi agar asal data jelas.
- Jalankan bertahap dengan jeda 5–10 menit antar run. Drift termal terukur nyata pada
  run panjang (bicubic 8K CPU1 naik 3,2x selama 100 citra), dan `720p -> 8K` adalah run
  terberat karena faktor perbesaran 6x per sumbu.
- Lebar minimum DIV2K adalah 1356 px, jadi sumber "4K" adalah hasil resize Lanczos, bukan
  4K native. Tulis di laporan sebagai "disiapkan pada resolusi 4K", bukan "citra 4K asli".
- Statistik agregat dihitung dari kolom `speedup` per citra (median), bukan rasio median
  antar-unit — lihat `REKAP_BENCHMARK.md`.

## Langkah 2c — Run Ulang yang Datanya Tercemar

Empat run di bawah ini waktunya membengkak karena drift atau spike. Rinciannya di
`REKAP_BENCHMARK.md` bagian *Status Kualitas Data*. Konvolusi (sharpen, gaussian,
sobel) sudah final, tidak perlu diulang.

**Status 2026-10-23 malam: semua sudah selesai.** Nearest 720p→1080p, nearest
1080p→4K/8K, bicubic 1080p→4K/8K, plus Sobel 8K sudah diulang dan bersih. Rerun
menyimpan data ke berkas cadangan `_HHMMSS.csv` karena CSV asli beratribut
hanya-baca; lihat `REKAP_BENCHMARK.md` bagian *Berkas data* untuk pemetaan
final. Tidak ada langkah benchmark yang tersisa — lanjut ke Langkah 3.

```
.\bench --op upscale --src-res 720p --res 1080p --method bicubic  --dataset DIV2K_valid_HR --out hasil_up_720to1080_bicubic.csv
.\bench --op upscale --src-res 720p --res 1080p --method nearest  --dataset DIV2K_valid_HR --out hasil_up_720to1080_nearest.csv
.\bench --op upscale --res 4k 8k --method nearest --dataset DIV2K_valid_HR --out hasil_upscale_nearest.csv
.\bench --op upscale --res 4k 8k --method bicubic --dataset DIV2K_valid_HR --out hasil_upscale_bicubic.csv
```

Bilinear 1080p→4K/8K tidak diulang: spike-nya kecil (p90 1,25–1,29x) dan speedup
per-citranya tetap sah. Bicubic 1080p→8K hanya perlu diulang kalau waktu absolut CPU-nya
mau dipakai sebagai angka utama; kalau yang dipakai speedup, cukup dibaca sebagai batas atas.

Kriteria lulus: di akhir run **tidak** muncul baris `!! DRIFT` maupun `!! GANGGUAN`.
Skrip membedakan empat kondisi berdasarkan **arah** penyimpangan, karena obatnya beda:

| Baris yang muncul | Arti | Tindakan |
|---|---|---|
| `!! DRIFT` | CPU melambat monoton sepanjang run (thermal) | istirahatkan laptop 10 menit, ulangi run itu |
| `!! GANGGUAN` | spike ke atas (p90/median > 1,25) = CPU direbut proses lain | tutup Chrome/antivirus, ulangi |
| `~~ CATATAN: ... arah CEPAT` | median/min tinggi tapi karena ada segmen **cepat** (p10/median < 1) = power state/boost | **jangan ulangi**, data dipakai |
| `~~ CATATAN: speedup GPU ... tidak stabil` | speedup end-to-end naik-turun antar sepertiga run | pakai angka 8K untuk klaim GPU |

Kenapa `CATATAN` bukan peringatan: `median/min` membesar juga kalau ada fase laptop
ngebut. Itu bukan kontaminasi, dan mengulanginya cuma membuang waktu.

Kalau CSV gagal ditulis karena masih terbuka di Excel, data otomatis diselamatkan
ke `<nama>_HHMMSS.csv`, bukan hilang.

Chrome tetap boleh terbuka. Bila masih mengganggu, batasi Chrome secara manual:
Task Manager → Details → klik kanan `chrome.exe` → *Set affinity* → centang hanya
prosesor logis 8-11 (E-core) agar 4 P-core (prosesor logis 0-7) tetap utuh untuk benchmark.

## Langkah 3 — Dashboard (produk akhir)

```
streamlit run app_komputasi_paralel.py
```

Pilih **Sumber Citra → Dataset DIV2K (Batch)**, atur jumlah citra (slider, default 50,
maksimum 100), lalu klik **🚀 Jalankan Batch**. Dashboard menampilkan:

- tabel agregat (median/rerata waktu + speedup per konfigurasi CPU 1/2/4/8 core dan GPU),
- bar chart waktu dan speedup,
- detail per citra (expander),
- tombol unduh hasil batch ke CSV.

## Catatan

- `benchmark_v2.py` dan `app_komputasi_paralel.py` memakai kernel yang sama dari
  `kernels_paralel.py`, sehingga angka benchmark dan dashboard sebanding.
- Jumlah CUDA core GPU ditampilkan dari API perangkat, jangan ditulis sebagai angka pasti
  sebelum dicocokkan dengan output dashboard.
