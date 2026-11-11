import os
import sys
import time
import math
import numpy as np
from PIL import Image

# Ensure CUDA paths are properly set
if os.path.isdir('cuda_toolkit'):
    os.environ['CUDA_HOME'] = os.path.abspath('cuda_toolkit')

from numba import jit, prange, cuda, set_num_threads

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 70)
    print("UJI BENCHMARK KOMPUTASI PARALEL SKALA 8K UHD (7680x4320 RGB)")
    print("Perangkat: Intel Core 5 210H (8 Cores) vs NVIDIA RTX 3050 (6GB VRAM)")
    print("=" * 70)

    img_path = os.path.join(BASE_DIR, 'gambar_asli_1080p.png')
    img_raw = Image.open(img_path).convert('RGB')
    print(f"Resolusi asli berkas terunggah: {img_raw.size[0]}x{img_raw.size[1]} piksel")

    print("Meng-upscale citra ke 8K UHD (7680x4320) menggunakan interpolasi Lanczos presisi tinggi...")
    t_resize_start = time.perf_counter()
    img_8k = img_raw.resize((7680, 4320), Image.Resampling.LANCZOS)
    img_8k_arr = np.ascontiguousarray(np.array(img_8k, dtype=np.float32))
    h, w, c = img_8k_arr.shape
    print(f"Selesai dalam {time.perf_counter() - t_resize_start:.2f} detik.")
    print(f"Total elemen data matriks: {w * h * c / 1e6:.2f} Juta Elemen Float32 (~{img_8k_arr.nbytes / 1e6:.1f} MB)")

    out_cpu = np.empty_like(img_8k_arr)

    # 1. Definisi Kernel Konvolusi Penajaman Warna (Sharpening / Laplacian Enhancer)
    @jit(nopython=True, parallel=True)
    def filter_cpu(src, dst):
        cur_h, cur_w = src.shape[0], src.shape[1]
        for ch in range(3):
            for y in prange(1, cur_h - 1):
                for x in range(1, cur_w - 1):
                    val = (
                        -0.25 * src[y - 1, x, ch]
                        -0.25 * src[y, x - 1, ch] + 2.0 * src[y, x, ch] - 0.25 * src[y, x + 1, ch]
                        -0.25 * src[y + 1, x, ch]
                    )
                    if val < 0.0: val = 0.0
                    elif val > 255.0: val = 255.0
                    dst[y, x, ch] = val

    @cuda.jit
    def filter_gpu(src, dst):
        x, y = cuda.grid(2)
        cur_h, cur_w = src.shape[0], src.shape[1]
        if 1 <= x < cur_w - 1 and 1 <= y < cur_h - 1:
            for ch in range(3):
                val = (
                    -0.25 * src[y - 1, x, ch]
                    -0.25 * src[y, x - 1, ch] + 2.0 * src[y, x, ch] - 0.25 * src[y, x + 1, ch]
                    -0.25 * src[y + 1, x, ch]
                )
                if val < 0.0: val = 0.0
                elif val > 255.0: val = 255.0
                dst[y, x, ch] = val

    # Pemanasan JIT CPU & GPU
    print("\nMelakukan pemanasan kompilasi JIT (Warm-up)...")
    set_num_threads(8)
    dummy = np.ascontiguousarray(img_8k_arr[:32, :32])
    dummy_out = np.empty_like(dummy)
    filter_cpu(dummy, dummy_out)

    threads = (16, 16)
    grid = (math.ceil(w / threads[0]), math.ceil(h / threads[1]))
    d_dummy_in = cuda.to_device(dummy)
    d_dummy_out = cuda.device_array_like(d_dummy_in)
    filter_gpu[(2, 2), threads](d_dummy_in, d_dummy_out)
    cuda.synchronize()
    print("Pemanasan selesai.")

    # 2. Pengujian CPU (1 Core, 2 Core, 4 Core, 8 Core)
    print("\n--- PENGUJIAN SKALABILITAS CPU (Resolusi 8K: 33,17 Juta Piksel) ---")
    core_list = [1, 2, 4, 8]
    t_cpu1 = 0.0
    hasil_cpu = {}

    for cores in core_list:
        set_num_threads(cores)
        print(f"Menjalankan CPU {cores} Core...", end="", flush=True)
        times = []
        for it in range(3):
            t0 = time.perf_counter()
            filter_cpu(img_8k_arr, out_cpu)
            t1 = time.perf_counter()
            times.append(t1 - t0)
        avg_t = float(np.mean(times))
        hasil_cpu[cores] = avg_t

        if cores == 1:
            t_cpu1 = avg_t
            speedup = 1.0
            eff = 100.0
            label = "1 Core (Sekuensial)"
        else:
            speedup = t_cpu1 / avg_t
            eff = (speedup / cores) * 100.0
            label = f"{cores} Core (Paralel)"

        print(f" Selesai! Waktu: {avg_t:.3f} detik | Speedup: {speedup:4.2f}x | Efisiensi: {eff:5.1f}%")

    # 3. Pengujian GPU NVIDIA RTX 3050 CUDA
    print("\n--- PENGUJIAN GPU NVIDIA CUDA (2.560 Cores) ---")
    print("Menjalankan eksekusi GPU CUDA 8K...", end="", flush=True)
    gpu_kernel_times = []
    gpu_total_times = []
    d_in = None
    d_out = None
    res = None

    for it in range(3):
        t0 = time.perf_counter()
        d_in = cuda.to_device(img_8k_arr)
        d_out = cuda.device_array_like(d_in)
        cuda.synchronize()
        t1 = time.perf_counter()

        filter_gpu[grid, threads](d_in, d_out)
        cuda.synchronize()
        t2 = time.perf_counter()

        res = d_out.copy_to_host()
        cuda.synchronize()
        t3 = time.perf_counter()

        gpu_kernel_times.append(t2 - t1)
        gpu_total_times.append(t3 - t0)

    avg_kernel = float(np.mean(gpu_kernel_times))
    avg_total_gpu = float(np.mean(gpu_total_times))
    speedup_kernel = t_cpu1 / avg_kernel
    speedup_total = t_cpu1 / avg_total_gpu
    print(" Selesai!")
    print(f"GPU Kernel Murni (CUDA)  : {avg_kernel:.3f} detik | Speedup: {speedup_kernel:4.2f}x")
    print(f"GPU Total (+ PCIe H2D)   : {avg_total_gpu:.3f} detik | Speedup: {speedup_total:4.2f}x")

    # 4. Simpan Citra PNG 8K Lossless (100% Warna Asli & Presisi)
    path_hasil_8k = os.path.join(BASE_DIR, 'hasil_filter_8k_warna_asli.png')
    path_input_8k = os.path.join(BASE_DIR, 'foto_asli_8k.png')
    print(f"\nMenyimpan citra 8K format PNG lossless di:\n- Input : {path_input_8k}\n- Output: {path_hasil_8k}")
    img_8k.save(path_input_8k)
    Image.fromarray(res.astype(np.uint8)).save(path_hasil_8k)
    print("Semua proses 8K selesai dengan sukses!")

if __name__ == '__main__':
    main()
