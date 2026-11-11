import os
import sys
import numpy as np
import math

base_dir = os.path.dirname(os.path.abspath(__file__))
cuda_path = os.path.join(base_dir, "cuda_toolkit")
if os.path.exists(cuda_path):
    os.environ["CUDA_HOME"] = cuda_path
    for sub in ("bin", os.path.join("nvvm", "bin")):
        p = os.path.join(cuda_path, sub)
        if os.path.isdir(p):
            os.environ["PATH"] = p + ";" + os.environ.get("PATH", "")

from numba import cuda

# ponytail: pembagian dua. Kernel paling kecil dulu, tambah operasi satu per
# satu sampai error muncul, supaya operasi penyebab teridentifikasi pasti.
dummy = np.zeros((4, 4), dtype=np.float32)
d_in = cuda.to_device(dummy)
d_out = cuda.device_array((8, 8), dtype=np.float32)
GRID, TPB = (1, 1), (8, 8)


def coba(nama, kernel, args):
    try:
        kernel[GRID, TPB](*args)
        cuda.synchronize()
        print(f"[OK]   {nama}")
        return True
    except Exception as e:
        baris = str(e).strip().splitlines()[-1][:90]
        print(f"[GAGAL] {nama} -> {type(e).__name__}: {baris}")
        return False


@cuda.jit
def k_floor(out, sy):
    i, j = cuda.grid(2)
    fy = (i + 0.5) * sy - 0.5
    out[i, j] = math.floor(fy)


@cuda.jit
def k_int(out, sy):
    i, j = cuda.grid(2)
    fy = (i + 0.5) * sy - 0.5
    out[i, j] = int(fy)


@cuda.jit
def k_int_floor(out, sy):
    i, j = cuda.grid(2)
    fy = (i + 0.5) * sy - 0.5
    out[i, j] = int(math.floor(fy))


@cuda.jit
def k_abs(out, sy):
    i, j = cuda.grid(2)
    fy = (i + 0.5) * sy - 0.5
    out[i, j] = abs(fy - j)


@cuda.jit
def k_minmax(out, h, w):
    i, j = cuda.grid(2)
    out[i, j] = min(max(i, 0), h - 1)


@cuda.jit
def k_minmax_float(out, h, w):
    i, j = cuda.grid(2)
    out[i, j] = min(max(i + 0.5, 0.0), float(h - 1))


@cuda.jit
def k_gabung(out, h, w, sy):
    i, j = cuda.grid(2)
    fy = (i + 0.5) * sy - 0.5
    iy = int(math.floor(fy + 0.5))
    out[i, j] = min(max(iy, 0), h - 1)


@cuda.jit
def k_clamp_if(out, h, w):
    i, j = cuda.grid(2)
    v = i
    if v < 0:
        v = 0
    elif v > h - 1:
        v = h - 1
    out[i, j] = v


@cuda.jit
def k_gabung_if(out, h, w, sy):
    i, j = cuda.grid(2)
    fy = (i + 0.5) * sy - 0.5
    iy = int(math.floor(fy + 0.5))
    if iy < 0:
        iy = 0
    elif iy > h - 1:
        iy = h - 1
    out[i, j] = iy


print(f"numba {__import__('numba').__version__} | Python {sys.version.split()[0]}")
print("=== PEMBAGIAN DUA KERNEL GPU ===")
coba("math.floor saja", k_floor, (d_out, 0.5))
coba("int() saja", k_int, (d_out, 0.5))
coba("int(math.floor())", k_int_floor, (d_out, 0.5))
coba("abs() saja", k_abs, (d_out, 0.5))
coba("min/max int", k_minmax, (d_out, 8, 8))
coba("min/max float", k_minmax_float, (d_out, 8, 8))
coba("gabungan (nearest)", k_gabung, (d_out, 8, 8, 0.5))
coba("clamp if/elif", k_clamp_if, (d_out, 8, 8))
coba("gabungan if/elif (fix)", k_gabung_if, (d_out, 8, 8, 0.5))
print("=== SELESAI ===")
