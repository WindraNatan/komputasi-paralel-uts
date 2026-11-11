"""
Benchmark komputasi paralel konvolusi + upscaling citra (v2).

Memakai kernel bersama kernels_paralel.py (sama persis dengan dashboard app),
sehingga angka benchmark dan dashboard selalu sebanding.

Operasi yang diuji:
  - conv   : filter konvolusi 3x3 (sobel | gaussian | sharpen) pada 1080p/4K/8K
  - upscale: resize 1080p -> 4K / 1080p -> 8K (nearest | bilinear | bicubic),
             kualitas dibandingkan ke referensi PIL Lanczos via MSE/PSNR

Skenario batch (dataset DIV2K valid HR, 100 citra) maupun citra tunggal.
Metrik: median/rerata/std/min, speedup, efisiensi, Karp-Flatt, fraksi paralel
Amdahl (fit p=2,4,8), H2D/kernel/D2H terpisah (pageable dan pinned), dan
verifikasi kesetaraan hasil CPU vs GPU.

Pakai:
  python benchmark_v2.py --op conv   --res 1080p 4k 8k --filter sharpen --dataset DIV2K_valid_HR
  python benchmark_v2.py --op upscale --res 4k 8k       --method bicubic --dataset DIV2K_valid_HR
  python benchmark_v2.py --op conv --dataset peppers --res 8k --reps 10   # mode lama, citra tunggal

Catatan pengukuran: colokkan charger, atur mode performa, tutup aplikasi lain.
"""
import argparse
import math
import os
import platform
import time

import numpy as np
from PIL import Image

# ---- Konfigurasi Path DLL CUDA Toolkit lokal (sama dengan dashboard) ----
BASE = os.path.dirname(os.path.abspath(__file__))
_cuda_path = os.path.join(BASE, "cuda_toolkit")
if os.path.exists(_cuda_path):
    os.environ["CUDA_HOME"] = _cuda_path
    # ponytail: Windows cari DLL lewat PATH; root saja tidak cukup, subfolder bin
    # dan nvvm/bin wajib, kalau GPU tidak terdeteksi di laptop
    for _sub in ("bin", os.path.join("nvvm", "bin")):
        _p = os.path.join(_cuda_path, _sub)
        if os.path.isdir(_p):
            os.environ["PATH"] = _p + ";" + os.environ.get("PATH", "")

from numba import config, cuda, get_num_threads, set_num_threads

from kernels_paralel import (
    KERNEL_3X3,
    METODE_BICUBIC,
    METODE_BILINEAR,
    METODE_NEAREST,
    conv_cpu_parallel,
    conv_gpu_kernel,
    metode_from_name,
    resize_cpu_parallel,
    resize_gpu_kernel,
    sobel_cpu_parallel,
    sobel_gpu_kernel,
)

CORES = [1, 2, 4, 8]
RESOLUSI = {"720p": (1280, 720), "1080p": (1920, 1080), "4k": (3840, 2160), "8k": (7680, 4320)}
# Upscaling: sumber selalu 1080p sesuai proposal, tujuan berikutnya
UPSCALE_DARI = "1080p"

FILES_PEPPERS = {"720p": "peppers_1080p.png", "1080p": "peppers_1080p.png", "4k": "peppers_4k.png", "8k": "peppers_8k.png"}


def list_dataset(folder):
    """Daftar citra PNG terurut dalam folder dataset (DIV2K_valid_HR)."""
    if not os.path.isdir(folder):
        return []
    return sorted(f for f in os.listdir(folder) if f.lower().endswith(".png"))


def load_gray(path):
    """Citra -> grayscale float32 1 kanal, contiguous."""
    return np.ascontiguousarray(np.array(Image.open(path).convert("L"), dtype=np.float32))


def to_target(img, res):
    """Susun citra uji pada resolusi target via PIL Lanczos (bukan objek uji)."""
    w, h = RESOLUSI[res]
    if (img.shape[1], img.shape[0]) == (w, h):
        return img
    return np.ascontiguousarray(
        np.array(Image.fromarray(img.astype(np.uint8)).resize((w, h), Image.LANCZOS),
                 dtype=np.float32))


def run_cpu_op(op, img, k, out_h, out_w, method):
    if op == "conv":
        if k is None:
            return sobel_cpu_parallel(img)
        return conv_cpu_parallel(img, k)
    return resize_cpu_parallel(img, out_h, out_w, method)


def run_gpu_launch(op, d_in, d_out, k, h, w, out_h, out_w, method, tpb, grid):
    if op == "conv":
        if k is None:
            sobel_gpu_kernel[grid, tpb](d_in, d_out, h, w)
        else:
            conv_gpu_kernel[grid, tpb](d_in, k, d_out, h, w, 3, 3)
    else:
        sy = h / out_h
        sx = w / out_w
        resize_gpu_kernel[grid, tpb](d_in, d_out, out_h, out_w, method, sy, sx)
    cuda.synchronize()


def stats(xs):
    a = np.asarray(xs, dtype=np.float64)
    return dict(median=float(np.median(a)), mean=float(a.mean()),
                std=float(a.std(ddof=1)) if len(a) > 1 else 0.0, min=float(a.min()))


def amdahl_fit(speedups):
    """Cari P yang meminimalkan galat kuadrat S(p)=1/((1-P)+P/p) untuk p>=2."""
    ps = np.array([p for p in speedups if p >= 2], dtype=float)
    ss = np.array([speedups[int(p)] for p in ps])
    grid = np.linspace(0.0, 1.0, 100001)
    pred = 1.0 / ((1.0 - grid[:, None]) + grid[:, None] / ps[None, :])
    return float(grid[np.argmin(((pred - ss[None, :]) ** 2).sum(axis=1))])


def karp_flatt(s, p):
    return (1.0 / s - 1.0 / p) / (1.0 - 1.0 / p)


def mse_psnr(a, b):
    """MSE dan PSNR (dB) terhadap referensi; mengukur kemiripan numerik."""
    d = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    mse = float(np.mean(d * d))
    if mse <= 0:
        return 0.0, float("inf")
    return mse, float(20.0 * math.log10(255.0 / math.sqrt(mse)))


HAS_CUDA = False
try:
    HAS_CUDA = cuda.is_available()
except Exception:
    HAS_CUDA = False


def bench_image(img, op, res, k, method, reps, nama_filter):
    """Uji satu citra pada satu resolusi: semua konfigurasi CPU + GPU.
    Mengembalikan dict baris hasil (atau None bila dilewati)."""
    h, w = img.shape
    if op == "upscale":
        out_w, out_h = RESOLUSI[res]  # RESOLUSI menyimpan (width, height)
    else:
        out_h, out_w = h, w

    # Warm-up kompilasi + thread pool; sekaligus simpan hasil CPU1..CPU8
    # sebagai referensi kesetaraan GPU (max_diff membandingkan keluaran ini)
    outs = {}
    for c in CORES:
        set_num_threads(c)
        outs[c] = run_cpu_op(op, img, k, out_h, out_w, method)

    cpu_t = {c: [] for c in CORES}
    gpu = {"h2d_pg": [], "h2d_pin": [], "kernel": [], "d2h_pg": [], "d2h_pin": []}
    ref_gpu = None

    if HAS_CUDA:
        d_in = cuda.device_array_like(img)
        d_out = cuda.device_array((out_h, out_w), dtype=np.float32)
        d_k = cuda.to_device(k) if k is not None else None
        pin_in = cuda.pinned_array(img.shape, dtype=np.float32)
        pin_in[:] = img
        pin_out = cuda.pinned_array((out_h, out_w), dtype=np.float32)
        host_out = np.zeros((out_h, out_w), dtype=np.float32)
        tpb = (16, 16)
        gh = out_h if op == "upscale" else h
        gw = out_w if op == "upscale" else w
        grid = (math.ceil(gh / tpb[0]), math.ceil(gw / tpb[1]))

        def launch():
            run_gpu_launch(op, d_in, d_out, k, h, w, out_h, out_w, method, tpb, grid)

        d_in.copy_to_device(img)
        launch()  # warm-up kernel

    for rep in range(reps + 1):          # rep 0 = dibuang
        for c in CORES:                  # round-robin: drift termal tidak bias
            set_num_threads(c)
            t0 = time.perf_counter()
            out_c = run_cpu_op(op, img, k, out_h, out_w, method)
            t = time.perf_counter() - t0
            if rep > 0:
                cpu_t[c].append(t)
            if c == 1:
                outs[1] = out_c
        if HAS_CUDA:
            t0 = time.perf_counter(); d_in.copy_to_device(img); cuda.synchronize()
            a = time.perf_counter() - t0
            t0 = time.perf_counter(); d_in.copy_to_device(pin_in); cuda.synchronize()
            b = time.perf_counter() - t0
            t0 = time.perf_counter(); launch()
            kt = time.perf_counter() - t0
            t0 = time.perf_counter(); d_out.copy_to_host(host_out); cuda.synchronize()
            d = time.perf_counter() - t0
            t0 = time.perf_counter(); d_out.copy_to_host(pin_out); cuda.synchronize()
            e = time.perf_counter() - t0
            if rep > 0:
                for key, v in zip(gpu, (a, b, kt, d, e)):
                    gpu[key].append(v)

    base = stats(cpu_t[1])
    spd = {}
    rows = []
    for c in CORES:
        s = stats(cpu_t[c])
        spd[c] = base["median"] / s["median"]
        rows.append(dict(res=res, op=op, unit="cpu%d" % c, filter=nama_filter,
                         **{kk + "_s": vv for kk, vv in s.items()},
                         speedup=spd[c], efficiency=spd[c] / c * 100.0, reps=reps,
                         mse=None, psnr=None, max_diff=None))

    if HAS_CUDA:
        # Jalankan sekali untuk verifikasi kesetaraan + kualitas
        d_in.copy_to_device(img)
        run_gpu_launch(op, d_in, d_out, k, h, w, out_h, out_w, method, tpb, grid)
        d_out.copy_to_host(host_out)
        cuda.synchronize()
        max_diff = float(np.max(np.abs(host_out - outs[1])))
        m = {kk: stats(v)["median"] for kk, v in gpu.items()}
        tot_pg, tot_pin = m["h2d_pg"] + m["kernel"] + m["d2h_pg"], m["h2d_pin"] + m["kernel"] + m["d2h_pin"]
        for label, val in (("gpu_kernel", m["kernel"]), ("gpu_total_pageable", tot_pg),
                           ("gpu_total_pinned", tot_pin)):
            rows.append(dict(res=res, op=op, unit=label, filter=nama_filter,
                             median_s=val, mean=val, std=0.0, min=val,
                             speedup=base["median"] / val, efficiency=None, reps=reps,
                             mse=None, psnr=None, max_diff=max_diff))
    return rows, base, spd, host_out if HAS_CUDA else None


def reference_upscale(img, res):
    """Referensi Lanczos (PIL) untuk evaluasi kualitas upscaling."""
    w, h = RESOLUSI[res]
    return np.ascontiguousarray(
        np.array(Image.fromarray(img.astype(np.uint8)).resize((w, h), Image.LANCZOS),
                 dtype=np.float32))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--op", default="conv", choices=["conv", "upscale"])
    ap.add_argument("--res", nargs="+", default=["1080p", "4k", "8k"], choices=list(RESOLUSI))
    ap.add_argument("--src-res", default=None, choices=list(RESOLUSI),
                    help="Resolusi sumber khusus upscale (default: otomatis deteksi dataset atau 1080p)")
    ap.add_argument("--filter", default="sharpen", choices=["sobel", "gaussian", "sharpen"])
    ap.add_argument("--method", default="bicubic", choices=["nearest", "bilinear", "bicubic"])
    ap.add_argument("--dataset", default=None,
                    help="Folder citra dataset, mis. DIV2K_valid_HR; bila kosong pakai peppers")
    ap.add_argument("--limit", type=int, default=0, help="Batasi jumlah citra dataset (0 = semua)")
    ap.add_argument("--reps", type=int, default=1,
                    help="Pengulangan per citra; untuk batch 100 citra nilai 1 sudah memberi N=100")
    ap.add_argument("--out", default=None,
                    help="Nama file CSV keluaran; default benchmark_v2_hasil.csv")
    ap.add_argument("--append", action="store_true",
                    help="Tambahkan baris ke file CSV yang sudah ada alih-alih menimpa")
    a = ap.parse_args()

    print("=" * 72)
    print("Platform :", platform.platform())
    print("Prosesor :", platform.processor())
    print("NUMBA_NUM_THREADS:", config.NUMBA_NUM_THREADS, "| os.cpu_count:", os.cpu_count())
    if HAS_CUDA:
        dev = cuda.get_current_device()
        print("GPU      :", dev.name.decode() if isinstance(dev.name, bytes) else dev.name,
              "| SM:", dev.MULTIPROCESSOR_COUNT, "| CC:", dev.compute_capability)
        print("  (jumlah CUDA core = SM x core/SM; jangan ditulis di proposal sebelum")
        print("   dicocokkan dengan nilai ini)")
    else:
        print("GPU      : CUDA tidak tersedia, bagian GPU dilewati.")
    print("Catatan  : colokkan charger, mode performa, tutup aplikasi lain; thread tidak di-pin.")
    print("=" * 72)

    k = None if a.filter == "sobel" else KERNEL_3X3[a.filter]
    method = metode_from_name(a.method)
    if a.dataset:
        files = list_dataset(a.dataset)
        if a.limit > 0:
            files = files[:a.limit]
        if not files:
            print("Tidak ada citra PNG di", a.dataset)
            return
        sources = [(os.path.join(a.dataset, f), f) for f in files]
        first_img = load_gray(sources[0][0])
        first_dim = (first_img.shape[1], first_img.shape[0])
        detected_res = next((k for k, v in RESOLUSI.items() if v == first_dim), None)
        src_res = a.src_res or detected_res or "1080p"
    else:
        src_res = a.src_res or "1080p"
        if a.op == "upscale":
            sources = [(os.path.join(BASE, FILES_PEPPERS.get(src_res, "peppers_1080p.png")), "peppers")]
        else:
            sources = [(os.path.join(BASE, FILES_PEPPERS[r]), "peppers") for r in a.res]

    all_rows = []
    for res in a.res:
        if a.op == "upscale" and RESOLUSI[res][0] <= RESOLUSI[src_res][0]:
            print(f"[{res}] Dilewati: resolusi target {res} ({RESOLUSI[res][0]}x{RESOLUSI[res][1]}) "
                  f"tidak lebih besar dari sumber {src_res} ({RESOLUSI[src_res][0]}x{RESOLUSI[src_res][1]}).")
            continue
        for idx, (path, nama) in enumerate(sources, 1):
            img0 = load_gray(path)
            if a.op == "upscale":
                img = to_target(img0, src_res)
            else:
                img = to_target(img0, res)
            h, w = img.shape

            rows, base, spd, gpu_out = bench_image(img, a.op, res, k, method, a.reps,
                                                   a.filter if a.op == "conv" else a.method)

            # Kualitas hanya untuk upscale: bandingkan keluaran CPU1 dan GPU ke Lanczos
            if a.op == "upscale" and gpu_out is not None:
                ref = reference_upscale(img, res); set_num_threads(1)
                out_w, out_h = RESOLUSI[res]
                cpu1 = run_cpu_op(a.op, img, k, out_h, out_w, method)
                mse_c, psnr_c = mse_psnr(cpu1, ref); mse_g, psnr_g = mse_psnr(gpu_out, ref)
            else:
                mse_c = psnr_c = mse_g = psnr_g = None

            # mse/psnr diisikan hanya ke baris cpu1 dan gpu_kernel
            for r in rows:
                if r["unit"] == "cpu1":
                    r["mse"], r["psnr"] = mse_c, psnr_c
                elif r["unit"] == "gpu_kernel":
                    r["mse"], r["psnr"] = mse_g, psnr_g

            all_rows.extend(rows)
            cpu8 = rows[3]["median_s"] * 1e3
            gpu_k = rows[4]["median_s"] * 1e3 if (HAS_CUDA and len(rows) > 4) else 0.0
            ket = f" | MSE {mse_g:.2f} PSNR {psnr_g:.2f} dB" if mse_g else ""
            print(f"[{res}] {idx}/{len(sources)} {nama} ({w}x{h}) "
                  f"CPU1={base['median']*1e3:.1f} ms CPU8={cpu8:.1f} ms "
                  f"| GPU kernel={gpu_k:.1f} ms{ket}")

        if a.dataset:  # ringkasan agregat per resolusi
            print(f"\n=== Ringkasan {res} (N={len(sources)} citra, op={a.op}) ===")
            agg = {}
            for r in all_rows:
                if r["res"] != res:
                    continue
                agg.setdefault(r["unit"], []).append(r)
            print(f"{'Unit':<22}{'med(ms)':>9}{'rerata(ms)':>11}{'std(ms)':>9}{'speedup':>9}{'eff%':>8}{'Karp-Flatt':>12}")
            for unit, rs in agg.items():
                sp = np.array([x["speedup"] for x in rs])
                md = np.array([x["median_s"] * 1e3 for x in rs])
                cores = int("".join(c for c in unit if c.isdigit()) or 1) if unit.startswith("cpu") else 0
                eff = sp / cores * 100 if cores > 0 else None
                med_sp = float(np.median(sp))
                if cores > 1:
                    kf = ((1.0 / med_sp) - (1.0 / cores)) / (1.0 - (1.0 / cores))
                    kf_str = f"{kf:.4f}"
                else:
                    kf_str = "-"
                print(f"{unit:<22}{np.median(md):>9.1f}{md.mean():>11.1f}{md.std(ddof=1) if len(md) > 1 else 0:>9.1f}"
                      f"{med_sp:>8.2f}x{('%6.1f' % eff.mean()) if eff is not None else '':>8}{kf_str:>12}")

            # Penjaga kualitas data. Yang menentukan OBAT-nya adalah ARAH penyimpangan:
            #  - lambat (spike ke atas)  = CPU direbut proses lain  -> tutup aplikasi latar
            #  - cepat  (median/min naik dari sisi min) = power state / boost -> bukan kontaminasi
            #  - drift  (perlahan sepanjang run)          = thermal -> istirahatkan, ulangi
            q = agg.get("cpu1")
            if q and len(q) >= 10:
                v = np.array([x["median_s"] for x in q]) * 1e3  # urut per citra
                med = float(np.median(v))
                p10, p90 = np.percentile(v, [10, 90])
                ratio = med / float(v.min())
                n3 = len(v) // 3
                drift = float(np.median(v[-n3:]) / np.median(v[:n3]))
                if drift > 1.25:
                    print(f"  !! DRIFT: CPU1 awal {np.median(v[:n3]):.1f} ms -> akhir "
                          f"{np.median(v[-n3:]):.1f} ms ({drift:.1f}x sepanjang run). "
                          f"Thermal/power, bukan Chrome. Speedup per-citra tetap sah; "
                          f"waktu absolut CPU jadi batas atas. Tindakan: istirahatkan laptop "
                          f"lalu ulangi run ini saja.")
                elif ratio > 1.3 and p90 / med > 1.25:
                    print(f"  !! GANGGUAN: CPU1 melambat sporadis (p90/median = {p90/med:.2f}x, "
                          f"max {v.max():.0f} ms vs median {med:.0f} ms). Proses lain "
                          f"(Chrome, antivirus) merebut CPU — tutup aplikasi latar, ulangi run ini.")
                elif ratio > 1.3:
                    print(f"  ~~ CATATAN: median/min CPU1 = {ratio:.1f}x tapi penyimpangan "
                          f"ke ARAH CEPAT (p10/median = {p10/med:.2f}x), bukan spike. "
                          f"Power state/boost, bukan kontaminasi. Data dipakai; jangan ulangi.")
                # Speedup per-citra = obat yang tahan gangguan: tiap unit diukur pada citra
                # yang sama, jadi kontaminasi CPU1 membesarkan semua unit sekaligus.
                s_gpu = np.array([x["speedup"] for x in agg.get("gpu_total_pinned", [])])
                if len(s_gpu) >= 6:
                    n = len(s_gpu) // 3
                    s3 = [float(np.median(s_gpu[:n])), float(np.median(s_gpu[n:2*n])),
                          float(np.median(s_gpu[2*n:]))]
                    if max(s3) / min(s3) > 1.5:
                        print(f"  ~~ CATATAN: speedup GPU end-to-end tidak stabil antar "
                              f"sepertiga ({s3[0]:.1f}x | {s3[1]:.1f}x | {s3[2]:.1f}x). "
                              f"Pakai tingkat 8K untuk klaim keunggulan GPU; angka di resolusi "
                              f"kecil didominasi overhead transfer.")

    import pandas as pd
    nama = a.out if a.out else "benchmark_v2_hasil.csv"
    out = nama if os.path.isabs(nama) else os.path.join(BASE, nama)
    df_new = pd.DataFrame(all_rows)
    if a.append and os.path.exists(out):
        try:
            df_old = pd.read_csv(out)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        except Exception:
            df_final = df_new
    else:
        df_final = df_new
    try:
        df_final.to_csv(out, index=False)
    except PermissionError:
        # CSV sedang dibuka Excel -> jangan buang 300 pengukuran, tulis ke nama lain
        alt = out.replace(".csv", "") + "_" + time.strftime("%H%M%S") + ".csv"
        df_final.to_csv(alt, index=False)
        print(f"\n!! {os.path.basename(out)} terkunci (dibuka Excel?). "
              f"Data diselamatkan ke: {alt}")
        print(f"Tersimpan: {alt} ({len(df_final)} baris)")
        return
    print(f"\nTersimpan: {out} ({len(df_final)} baris)")


if __name__ == "__main__":
    main()
