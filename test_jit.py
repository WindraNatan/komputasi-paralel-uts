import os
import sys
import numpy as np

# ponytail: jalankan pemanasan JIT di luar Streamlit, traceback penuh terlihat
# tanpa harus melihatnya lewat sidebar yang terpotong.
base_dir = os.path.dirname(os.path.abspath(__file__))
cuda_path = os.path.join(base_dir, "cuda_toolkit")
if os.path.exists(cuda_path):
    os.environ["CUDA_HOME"] = cuda_path
    for sub in ("bin", os.path.join("nvvm", "bin")):
        p = os.path.join(cuda_path, sub)
        if os.path.isdir(p):
            os.environ["PATH"] = p + ";" + os.environ.get("PATH", "")

from numba import njit, prange, set_num_threads, cuda
import math

METODE_NEAREST, METODE_BILINEAR, METODE_BICUBIC = 0, 1, 2


@njit(parallel=True, fastmath=True)
def conv_cpu_parallel(img, k):
    h, w = img.shape
    kh, kw = k.shape
    pad_h = kh // 2
    pad_w = kw // 2
    out = np.zeros((h, w), dtype=np.float32)
    for r in prange(pad_h, h - pad_h):
        for c in range(pad_w, w - pad_w):
            val = 0.0
            for i in range(kh):
                for j in range(kw):
                    val += img[r - pad_h + i, c - pad_w + j] * k[i, j]
            out[r, c] = val
    return out


@njit(parallel=True, fastmath=True)
def sobel_cpu_parallel(img):
    h, w = img.shape
    out = np.zeros((h, w), dtype=np.float32)
    for r in prange(1, h - 1):
        for c in range(1, w - 1):
            gx = (img[r-1, c+1] + 2.0*img[r, c+1] + img[r+1, c+1]) - \
                 (img[r-1, c-1] + 2.0*img[r, c-1] + img[r+1, c-1])
            gy = (img[r+1, c-1] + 2.0*img[r+1, c] + img[r+1, c+1]) - \
                 (img[r-1, c-1] + 2.0*img[r-1, c] + img[r-1, c+1])
            out[r, c] = math.sqrt(gx * gx + gy * gy)
    return out


@cuda.jit
def sobel_gpu_kernel(d_img, d_out, h, w):
    r, c = cuda.grid(2)
    if 1 <= r < h - 1 and 1 <= c < w - 1:
        gx = (d_img[r-1, c+1] + 2.0*d_img[r, c+1] + d_img[r+1, c+1]) - \
             (d_img[r-1, c-1] + 2.0*d_img[r, c-1] + d_img[r+1, c-1])
        gy = (d_img[r+1, c-1] + 2.0*d_img[r+1, c] + d_img[r+1, c+1]) - \
             (d_img[r-1, c-1] + 2.0*d_img[r-1, c] + d_img[r-1, c+1])
        d_out[r, c] = math.sqrt(gx * gx + gy * gy)


@njit(parallel=True, fastmath=True)
def resize_cpu_parallel(src, out_h, out_w, method):
    in_h, in_w = src.shape
    out = np.zeros((out_h, out_w), dtype=np.float32)
    sy = in_h / out_h
    sx = in_w / out_w
    for oy in prange(out_h):
        for ox in range(out_w):
            fy = (oy + 0.5) * sy - 0.5
            fx = (ox + 0.5) * sx - 0.5
            if method == METODE_NEAREST:
                iy = min(max(int(math.floor(fy + 0.5)), 0), in_h - 1)
                ix = min(max(int(math.floor(fx + 0.5)), 0), in_w - 1)
                out[oy, ox] = src[iy, ix]
            elif method == METODE_BILINEAR:
                iy = int(math.floor(fy))
                ix = int(math.floor(fx))
                ty = fy - iy
                tx = fx - ix
                val = 0.0
                wsum = 0.0
                for dj in range(2):
                    wy = (1.0 - ty) if dj == 0 else ty
                    sj = min(max(iy + dj, 0), in_h - 1)
                    for di in range(2):
                        wx = (1.0 - tx) if di == 0 else tx
                        si = min(max(ix + di, 0), in_w - 1)
                        val += src[sj, si] * wx * wy
                        wsum += wx * wy
                out[oy, ox] = val / wsum
            else:
                iy = int(math.floor(fy))
                ix = int(math.floor(fx))
                ty = fy - iy
                tx = fx - ix
                val = 0.0
                wsum = 0.0
                for j in range(-1, 3):
                    tt = abs(ty - j)
                    if tt < 1.0:
                        wy = 1.5 * tt * tt * tt - 2.5 * tt * tt + 1.0
                    elif tt < 2.0:
                        wy = -0.5 * tt * tt * tt + 2.5 * tt * tt - 4.0 * tt + 2.0
                    else:
                        wy = 0.0
                    sj = min(max(iy + j, 0), in_h - 1)
                    for i in range(-1, 3):
                        uu = abs(tx - i)
                        if uu < 1.0:
                            wx = 1.5 * uu * uu * uu - 2.5 * uu * uu + 1.0
                        elif uu < 2.0:
                            wx = -0.5 * uu * uu * uu + 2.5 * uu * uu - 4.0 * uu + 2.0
                        else:
                            wx = 0.0
                        si = min(max(ix + i, 0), in_w - 1)
                        val += src[sj, si] * wx * wy
                        wsum += wx * wy
                out[oy, ox] = val / wsum
    return out


@cuda.jit
def resize_gpu_kernel(d_src, d_out, out_h, out_w, method, sy, sx):
    oy, ox = cuda.grid(2)
    if oy >= out_h or ox >= out_w:
        return
    in_h, in_w = d_src.shape
    fy = (oy + 0.5) * sy - 0.5
    fx = (ox + 0.5) * sx - 0.5
    if method == 0:
        iy = int(math.floor(fy + 0.5))
        ix = int(math.floor(fx + 0.5))
        if iy < 0: iy = 0
        elif iy > in_h - 1: iy = in_h - 1
        if ix < 0: ix = 0
        elif ix > in_w - 1: ix = in_w - 1
        d_out[oy, ox] = d_src[iy, ix]
    elif method == 1:
        iy = int(math.floor(fy))
        ix = int(math.floor(fx))
        ty = fy - iy
        tx = fx - ix
        val = 0.0
        wsum = 0.0
        for dj in range(2):
            wy = (1.0 - ty) if dj == 0 else ty
            sj = iy + dj
            if sj < 0: sj = 0
            elif sj > in_h - 1: sj = in_h - 1
            for di in range(2):
                wx = (1.0 - tx) if di == 0 else tx
                si = ix + di
                if si < 0: si = 0
                elif si > in_w - 1: si = in_w - 1
                val += d_src[sj, si] * wx * wy
                wsum += wx * wy
        d_out[oy, ox] = val / wsum
    else:
        iy = int(math.floor(fy))
        ix = int(math.floor(fx))
        ty = fy - iy
        tx = fx - ix
        val = 0.0
        wsum = 0.0
        for j in range(-1, 3):
            tt = abs(ty - j)
            if tt < 1.0:
                wy = 1.5 * tt * tt * tt - 2.5 * tt * tt + 1.0
            elif tt < 2.0:
                wy = -0.5 * tt * tt * tt + 2.5 * tt * tt - 4.0 * tt + 2.0
            else:
                wy = 0.0
            sj = iy + j
            if sj < 0: sj = 0
            elif sj > in_h - 1: sj = in_h - 1
            for i in range(-1, 3):
                uu = abs(tx - i)
                if uu < 1.0:
                    wx = 1.5 * uu * uu * uu - 2.5 * uu * uu + 1.0
                elif uu < 2.0:
                    wx = -0.5 * uu * uu * uu + 2.5 * uu * uu - 4.0 * uu + 2.0
                else:
                    wx = 0.0
                si = ix + i
                if si < 0: si = 0
                elif si > in_w - 1: si = in_w - 1
                val += d_src[sj, si] * wx * wy
                wsum += wx * wy
        d_out[oy, ox] = val / wsum


@cuda.jit
def conv_gpu_kernel(d_img, d_k, d_out, h, w, kh, kw):
    r, c = cuda.grid(2)
    pad_h = kh // 2
    pad_w = kw // 2
    if pad_h <= r < h - pad_h and pad_w <= c < w - pad_w:
        val = 0.0
        for i in range(kh):
            for j in range(kw):
                val += d_img[r - pad_h + i, c - pad_w + j] * d_k[i, j]
        d_out[r, c] = val


print("=== DIAGNOSTIK JIT / CUDA ===")
print(f"numba: {__import__('numba').__version__}  Python: {sys.version.split()[0]}")
try:
    print(f"CUDA tersedia: {cuda.is_available()}")
    if cuda.is_available():
        print(f"GPU: {cuda.get_current_device().name.decode()}")
except Exception as e:
    print(f"cek CUDA gagal: {type(e).__name__}: {e}")

print("\n[1/4] konvolusi CPU...")
set_num_threads(1)
dummy = np.zeros((32, 32), dtype=np.float32)
k_dummy = np.zeros((3, 3), dtype=np.float32)
conv_cpu_parallel(dummy, k_dummy)
print("      OK")

print("[2/4] sobel CPU...")
sobel_cpu_parallel(dummy)
print("      OK")

print("[3/4] resize CPU (bicubic)...")
resize_cpu_parallel(dummy, 64, 64, METODE_BICUBIC)
print("      OK")

print("[4/4] kernel CUDA...")
d_in = cuda.to_device(dummy)
d_out = cuda.device_array((32, 32), dtype=np.float32)
sobel_gpu_kernel[(2, 2), (16, 16)](d_in, d_out, 32, 32)
print("      sobel_gpu_kernel OK")

# ponytail: bandingkan GPU vs CPU pada ketiga metode resize. Cara lama
# (min/max) tidak bisa dikompilasi; jika logika pengganti if/elif benar,
# selisih maksimum kedua kernel harus 0 untuk NEAREST dan BILINEAR.
rng = np.random.default_rng(0)
uji = np.ascontiguousarray(rng.random((17, 19), dtype=np.float32) * 255.0)
d_uji = cuda.to_device(uji)
for nama, m in (("NEAREST", METODE_NEAREST), ("BILINEAR", METODE_BILINEAR), ("BICUBIC", METODE_BICUBIC)):
    cpu_res = resize_cpu_parallel(uji, 34, 38, m)
    gpu_res = cuda.device_array((34, 38), dtype=np.float32)
    resize_gpu_kernel[(4, 4), (16, 16)](d_uji, gpu_res, 34, 38, m, 17.0 / 34.0, 19.0 / 38.0)
    cuda.synchronize()
    sel = float(np.max(np.abs(cpu_res - gpu_res.copy_to_host())))
    status = "OK" if sel < 1e-4 else "SELISIH BESAR"
    print(f"      resize_gpu_kernel {nama:9s} max|CPU-GPU| = {sel:.3e}  [{status}]")

d_out2 = cuda.device_array((64, 64), dtype=np.float32)
resize_gpu_kernel[(2, 2), (16, 16)](d_in, d_out2, 64, 64, METODE_BICUBIC, 0.5, 0.5)
print("      resize_gpu_kernel OK")
d_k = cuda.to_device(k_dummy)
conv_gpu_kernel[(2, 2), (16, 16)](d_in, d_k, d_out, 32, 32, 3, 3)
print("      conv_gpu_kernel OK")
cuda.synchronize()

print("\nSEMUA KERNEL BERHASIL DIKOMPILASI.")
