# Rekap Hasil Benchmark UTS Komputasi Paralel

Dataset: DIV2K valid HR, 100 citra per resolusi. Setiap citra diukur pada CPU 1/2/4/8
*thread* dan GPU secara berurutan, lalu diambil median.

CPU: Intel Core 5 210H (Alder Lake), 8 inti fisik (4 P-core + 4 E-core), 12 prosesor
logis. Topologi diverifikasi 2026-11-08 melalui `GetLogicalProcessorInformationEx` dan
probe afinitas: **P-core menguasai prosesor logis 0-7 (tiap P-core 2 LP via SMT), E-core
menguasai prosesor logis 8-11** (1 LP per inti, kira-kira 1,76x lebih lambat per thread
pada kernel probe rantai aritmetika). Proses dikunci ke 8 prosesor logis 0-7 (`affinity 0xFF`,
`NUMBA_NUM_THREADS=8`), artinya seluruh konfigurasi CPU 1/2/4/8 berjalan **di atas 4
P-core saja**; E-core tidak pernah diikutsertakan dan justru dialokasikan ke aplikasi lain.
Konfigurasi "CPU 1/2/4/8" adalah jumlah *thread* Numba (`set_num_threads`), bukan jumlah
inti fisik: 4 thread = 4 P-core masing-masing 1 thread, 8 thread = 4 P-core dengan
kontensi SMT (probe: 2 thread pada 1 P-core hanya memberi kira-kira 1,6x).
GPU: NVIDIA RTX 3050 6GB Laptop, 20 SM, compute capability 8.6.

Waktu dalam milidetik, median 100 citra. **Speedup dihitung per citra lalu diambil median**,
bukan rasio antar median. Normalisasi per citra menetralkan perubahan kondisi sistem yang
menetap sepanjang pengukuran satu citra (power state, drift antar citra), **tetapi tidak
menghilangkan gangguan transien yang mengenai satu jendela pengukuran saja**, karena unit
diukur berurutan, tidak bersamaan. Dengan `reps=1`, `std_s=0` hanyalah penanda tanpa
repetisi, bukan bukti keberulangan; statistik yang dilaporkan mencerminkan variansi antar
citra, bukan ketidakpastian pengukuran.

Tiga kolom GPU dibedakan karena artinya berbeda:

- `GPU kernel` = waktu kernel saja, tanpa transfer data.
- `GPU total` = H2D + kernel + D2H dengan memori pinned, yaitu yang benar-benar dirasakan pengguna.
- `Speedup total` = CPU1 dibagi GPU total. **Ini angka yang dipakai untuk klaim performa.**

## Konvolusi 3x3

| Filter | Resolusi | 1 thread | 2 thread | 4 thread | 8 thread | GPU kernel | GPU total | Speedup 8 thread | Speedup GPU total |
|---|---|---|---|---|---|---|---|---|---|
| Sharpen | 1080p | 13,7 | 7,6 | 5,0 | 5,4 | 4,2 | 15,6 | 2,54x | 0,89x |
| Sharpen | 4K | 59,8 | 32,2 | 23,6 | 24,2 | 7,0 | 17,9 | 2,45x | 3,14x |
| Sharpen | 8K | 270,1 | 132,1 | 89,6 | 91,4 | 14,8 | 57,2 | 2,95x | 4,78x |
| Gaussian | 1080p | 22,3 | 17,1 | 12,6 | 9,6 | 5,8 | 19,6 | 2,34x | 1,11x |
| Gaussian | 4K | 87,8 | 49,6 | 32,7 | 31,4 | 8,4 | 38,0 | 2,75x | 2,37x |
| Gaussian | 8K | 408,9 | 198,7 | 151,4 | 118,6 | 15,7 | 58,3 | 3,44x | 7,03x |
| Sobel | 1080p | 4,9 | 3,3 | 3,1 | 4,2 | 4,1 | 15,7 | 1,17x | 0,31x |
| Sobel | 4K | 18,4 | 11,7 | 12,1 | 14,3 | 8,4 | 19,3 | 1,33x | 0,96x |
| Sobel | 8K | 73,8 | 35,5 | 40,1 | 41,5 | 16,6 | 59,0 | 1,76x | 1,25x |

Kesetaraan CPU vs GPU: `max_diff` = 0 pada seluruh baris konvolusi.

## Upscaling (sudah terukur)

| Sumber | Metode | Target | 1 thread | 8 thread | GPU kernel | GPU total | Speedup GPU total | PSNR vs Lanczos |
|---|---|---|---|---|---|---|---|---|
| 1080p | Bicubic | 4K | 147,4 | 38,2 | 37,3 | 44,9 | 3,11x | 46,37 dB |
| 1080p | Bicubic | 8K | 666,8 | 145,5 | 100,3 | 122,4 | 5,18x | 46,66 dB |
| 1080p | Bilinear | 4K | 180,0 | 53,6 | 25,3 | 78,0 | 2,45x | 39,26 dB |
| 1080p | Bilinear | 8K | 771,5 | 227,1 | 38,8 | 61,7 | 10,89x | 39,62 dB |
| 1080p | Nearest | 4K | 25,3 | 12,9 | 4,1 | 30,8 | 0,83x | 34,13 dB |
| 1080p | Nearest | 8K | 84,7 | 41,0 | 9,5 | 31,6 | 2,53x | 33,10 dB |
| 4K | Bicubic | 8K | 699,9 | 140,1 | 100,0 | 126,4 | 5,53x | 53,47 dB |
| 4K | Bilinear | 8K | 273,7 | 80,0 | 34,7 | 60,9 | 4,43x | 46,61 dB |
| 4K | Nearest | 8K | 129,9 | 56,3 | 9,8 | 36,0 | 3,61x | 38,93 dB |
| 720p | Bicubic | 1080p | 35,6 | 12,2 | 24,0 | 32,7 | 1,09x | 44,85 dB |
| 720p | Bilinear | 1080p | 9,8 | 3,9 | 5,4 | 13,3 | 0,74x | 37,92 dB |
| 720p | Nearest | 1080p | 7,3 | 4,5 | 3,0 | 19,0 | 0,41x | 30,70 dB |
| 720p | Bicubic | 4K | 148,8 | 39,4 | 35,5 | 41,8 | 3,40x | 45,04 dB |
| 720p | Bilinear | 4K | 62,6 | 24,7 | 16,7 | 39,9 | 1,60x | 38,36 dB |
| 720p | Nearest | 4K | 28,7 | 19,3 | 5,0 | 28,5 | 0,98x | 32,17 dB |
| 720p | Bicubic | 8K | 605,5 | 144,3 | 99,9 | 121,3 | 4,97x | 44,91 dB |
| 720p | Bilinear | 8K | 476,3 | 148,1 | 38,3 | 60,2 | 7,77x | 38,05 dB |
| 720p | Nearest | 8K | 73,7 | 36,9 | 9,5 | 30,7 | 2,41x | 31,75 dB |

PSNR: bicubic 44,8–53,5 dB, bilinear 38,0–46,6 dB, nearest 30,7–38,9 dB.
Urutan kualitas konsisten di seluruh 18 kombinasi: bicubic > bilinear > nearest.

`max_diff` maksimum di seluruh baris upscaling: 4,7e-10, praktis nol.
GPU menghasilkan citra yang identik dengan CPU untuk ketiga metode.

## Belum terukur

Tidak ada. 18 dari 18 kombinasi sumber ke target sudah punya data, dan sejak
21:30 2026-10-23 semuanya berasal dari run yang guard-nya bersih. Rerun malam ini
memperbaiki dua yang tersisa: Sobel 8K (kini drift 1,11x) dan Bicubic 1080p→8K
(p10/median 0,88, fase cepat). Satu catatan: bagian 4K dari rerun Sobel drift
1,49x, tetapi Sobel 4K yang bersih sudah ada di run lama sehingga tidak perlu
pengulangan tambahan.

## Temuan yang layak masuk analisis

**Keunggulan GPU bergantung pada ukuran data, bukan otomatis lebih cepat.** Pada 1080p,
GPU total 15,7 ms melawan CPU1 4,9 ms (Sobel) sehingga GPU justru 3,2x lebih lambat.
Penyebabnya biaya tetap transfer + peluncuran kernel sekitar 10–14 ms, sementara data
1080p grayscale hanya sekitar 2 MB. Titik impas ada di 4K, dan pada 8K GPU menang
4,8x (Sharpen) sampai 7,8x (Bilinear 720p→8K).

Pada upscaling, GPU total hanya kalah pada target terkecil (nearest 720p→1080p
0,41x, bilinear 720p→1080p 0,74x, nearest 1080p→4K 0,83x) karena kernelnya
sangat singkat sementara biaya tetap transfer dan peluncuran kernel tetap ada.
Sejak 4K ke atas, GPU total sudah menang untuk metode berbobot (bilinear
1,60–2,45x, bicubic 3,11–3,40x), dan di 8K semua metode menang (nearest 2,41x
sampai bilinear 7,77x). Kernel nearest 4K sendiri 6,2x lebih cepat dari CPU1 —
bedanya seluruhnya ditelan transfer.

**Speedup kernel saja menyesatkan.** Sobel 8K: kernel 16,6 ms terlihat 4,44x lebih cepat,
tetapi setelah transfer menjadi 59,0 ms alias hanya 1,25x. Selalu kutip pasangan
kernel dan total.

**Jumlah thread tidak monotonik.** 8 thread kadang lebih lambat dari 4 thread (Sharpen
4K: 23,6 vs 24,2 ms; Sobel 4K: 12,1 vs 14,3 ms). Karena afinitas tetap di 4 P-core,
penurunan ini bukan penjadwalan ke E-core seperti yang sempat diasumsikan, melainkan
kontensi SMT: 8 thread berarti 2 thread per P-core, yang probe ukur hanya memberi
kira-kira 1,6x per inti. Ditambah biaya sinkronisasi, untuk kernel singkat seperti Sobel
manfaat 8 thread habis sebelum terbayar.

**Kualitas vs kecepatan bukan trade-off sederhana.** Nearest sekitar 10x lebih cepat dari
Bicubic pada 8K (9,5 ms vs 100,3 ms kernel) tetapi PSNR-nya 13,6 dB lebih rendah. Bicubic
2,6x lebih lambat dari Bilinear (100,3 vs 38,8 ms kernel) dengan PSNR 7 dB lebih
baik, sehingga Bicubic adalah pilihan paling seimbang.

## Status Kualitas Data (diperbarui 2026-10-23)

Klasifikasi memakai **arah** penyimpangan, bukan hanya rasio median terhadap nilai tercepat.
`median/min` membesar untuk dua sebab berlawanan: spike ke atas (kontaminasi proses lain)
dan adanya fase cepat (power state/boost). Obatnya berbeda, jadi keduanya dipisah.

| Skenario | Resolusi | Status | Tindakan |
|---|---|---|---|
| Sharpen | 1080p / 4K / 8K | bersih | dipakai |
| Gaussian | 1080p / 4K / 8K | bersih, 4K & 8K fase cepat | dipakai, jangan ulang |
| Sobel | 1080p / 4K | bersih | dipakai; catatan: rerun 21:14 drift di 4K (1,49x) — 4K final tetap dari run ini |
| Sobel | 8K | DRIFT 1,56x (run lama) | **diulang 21:14, bersih (drift 1,11x)** |
| Bicubic 1080p→4K | 4K | bersih (run lama) | **diulang 21:30, bersih (p10/median 0,67 = fase cepat)** |
| Bicubic 1080p→8K | 8K | DRIFT 3,28x (run lama) | **diulang 21:30, bersih (p10/median 0,88 = fase cepat)** |
| Bilinear 1080p→4K | 4K | spike ringan (p90 1,29x) | dipakai, spike kecil |
| Bilinear 1080p→8K | 8K | spike ringan (p90 1,25x) | dipakai, spike kecil |
| Nearest 1080p→4K | 4K | DRIFT 5,05x | **diulang 2026-10-23, bersih (drift 1,00x)** |
| Nearest 1080p→8K | 8K | spike (p90 2,08x) | **diulang 2026-10-23, bersih (drift 1,23x)** |
| Bicubic 720p→1080p | 1080p | bersih (kini) | dipakai |
| Bilinear 720p→1080p | 1080p | DRIFT 1,28x | **diulang 2026-10-23, bersih (drift 1,00x)** |
| Nearest 720p→1080p | 1080p | bersih (kini) | dipakai |
| Bicubic 4K→8K | 8K | bersih | dipakai |
| Bilinear 4K→8K | 8K | fase cepat | dipakai |
| Nearest 4K→8K | 8K | fase cepat | dipakai |
| Bicubic 720p→4K | 4K | bersih | dipakai |
| Bilinear 720p→4K | 4K | fase cepat | dipakai |
| Nearest 720p→4K | 4K | fase cepat | dipakai |
| Bicubic 720p→8K | 8K | fase cepat | dipakai |
| Bilinear 720p→8K | 8K | fase cepat | dipakai |
| Nearest 720p→8K | 8K | fase cepat | **diulang 2026-10-23, bersih (drift 1,02x)** |

Yang berstatus "ulangi" memakai `min_s` sebagai pembanding: waktu tercepat yang pernah
teramati pada run itu. Kalau angka absolutnya dipakai di laporan, ukur ulang dengan
`.\bench` setelah laptop diistirahatkan. Kalau yang dipakai hanya speedup per-citra,
datanya tetap selaras untuk gangguan yang menetap sepanjang satu citra, tetapi
gangguan yang mengenai satu jendela pengukuran saja tetap bias — itulah sebabnya
tetap ada klasifikasi DRIFT/GANGGUAN per run.

Bukti gangguan adalah interferensi, bukan thermal murni: pada citra yang lambat,
rasio CPU4/CPU1 naik dari sekitar 0,27 ke 0,45–0,51 dan GPU ikut melambat lalu pulih.
Throttling termal tidak menaikkan rasio antar-unit seperti itu.

Bukti tambahan untuk Bicubic 1080p→8K yang lama: bukan hanya CPU yang lambat — kernel
GPU terukur 384,5 ms di run lama versus 100,3 ms di rerun yang bersih (3,8x), dan CPU1
11.305 ms versus 667 ms (17x). Perlambatan yang menimpa GPU dan CPU sekaligus
menandakan tekanan daya atau memori sistem, bukan thermal CPU murni.

## Berkas data

| Berkas | Isi | Status |
|---|---|---|
| `hasil_conv_sharpen.csv` | Sharpen, 3 resolusi | final |
| `hasil_conv_gaussian_222407.csv` | Gaussian, 3 resolusi | final |
| `hasil_conv_sobel.csv` | Sobel, 3 resolusi (1080p & 4K run lama + 8K rerun 21:14, sudah digabung) | final |
| `hasil_conv_sobel_211420.csv` | Sobel rerun 21:14 | arsip; bagian 8K-nya sudah digabung ke `hasil_conv_sobel.csv` |
| `hasil_upscale_nearest_103023.csv` | 1080p → 4K & 8K, nearest | final (rerun 2026-10-23) |
| `hasil_upscale_bilinear.csv` | 1080p → 4K & 8K, bilinear | final |
| `hasil_upscale_bicubic.csv` | 1080p → 4K & 8K, bicubic (rerun 21:30, sudah ditimpa) | final |
| `hasil_upscale_bicubic_213012.csv` | duplikat rerun 21:30 | arsip |
| `hasil_up_4kto8k_{bicubic,bilinear,nearest}.csv` | 4K → 8K | final |
| `hasil_up_720to1080_{bicubic,bilinear,nearest}.csv` | 720p → 1080p | final (bilinear rerun 2026-10-23) |
| `hasil_up_720to4k_{bicubic,bilinear,nearest}.csv` | 720p → 4K | final |
| `hasil_up_720to8k_{bicubic,bilinear,nearest}.csv` | 720p → 8K | final (nearest rerun 2026-10-23) |
| `hasil_conv_gaussian.csv`, `hasil_conv_gaussian_220221.csv`, `hasil_upscale_nearest_125944.csv` | run tercemar, jangan dipakai | arsip |
| `uji_kunci.csv` | Bicubic 720p→1080p, rerun 21:24 | sanity check, dipakai untuk verifikasi |

Catatan: `hasil_upscale_nearest.csv` adalah run lama 1080p→4K/8K yang tercemar
(DRIFT 5,05x dan spike p90 2,08x). Sudah digantikan `hasil_upscale_nearest_103023.csv`.
`hasil_up_720to1080_bilinear.csv` juga sudah ditimpa oleh rerun 2026-10-23 yang bersih.

Kedua rerun malam ini (sobel 21:14, bicubic 21:30) awalnya hanya tersimpan ke berkas
cadangan `_HHMMSS.csv` karena `hasil_conv_sobel.csv` dan `hasil_upscale_bicubic.csv`
beratribut hanya-baca. Atributnya sudah dibersihkan dan data final kini di berkas
kanonik: `hasil_conv_sobel.csv` berisi gabungan 1080p+4K run lama dan 8K rerun,
sedangkan `hasil_upscale_bicubic.csv` sudah ditimpa langsung. Bila ada run tambahan,
jangan biarkan CSV terbuka di Excel saat penulisan.

Temuan `uji_kunci.csv`: CPU8 bicubic 720p→1080p terukur 22,8 ms di rerun versus
12,2 ms di run lama padahal CPU1, kernel, dan GPU total-nya identik. Pada beban
sekecil ~34 ms, waktu 8 thread tidak stabil antar run, jadi CPU8 di resolusi 720p
jangan ditafsirkan terlalu jauh.

