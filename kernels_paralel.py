"""Kernel bersama konvolusi, Sobel, dan resize (upscaling) untuk CPU Numba dan GPU CUDA.

Dipakai bersama oleh benchmark_v2.py dan app_komputasi_paralel.py agar kernel
yang diukur di benchmark identik dengan yang dijalankan di dashboard.

Konvensi koordinat: center-aligned (oy+0.5)*sy-0.5, sama seperti PIL/OpenCV.
"""
import math

import numpy as np
from numba import cuda, njit, prange

# Metode interpolasi
METODE_NEAREST, METODE_BILINEAR, METODE_BICUBIC = 0, 1, 2
METODE_LABELS = {
    METODE_NEAREST: "Nearest Neighbor",
    METODE_BILINEAR: "Bilinear",
    METODE_BICUBIC: "Bicubic (Catmull-Rom)",
}

KERNEL_3X3 = {
    "gaussian": (1.0 / 16.0) * np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=np.float32),
    "sharpen": np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32),
}


def metode_from_name(name):
    return {"nearest": METODE_NEAREST, "bilinear": METODE_BILINEAR,
            "bicubic": METODE_BICUBIC}[name]


# ----------------------------- kernel CPU ---------------------------------
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

    # Kernel Sobel Gx dan Gy 3x3
    for r in prange(1, h - 1):
        for c in range(1, w - 1):
            gx = (img[r-1, c+1] + 2.0*img[r, c+1] + img[r+1, c+1]) - \
                 (img[r-1, c-1] + 2.0*img[r, c-1] + img[r+1, c-1])
            gy = (img[r+1, c-1] + 2.0*img[r+1, c] + img[r+1, c+1]) - \
                 (img[r-1, c-1] + 2.0*img[r-1, c] + img[r-1, c+1])
            out[r, c] = math.sqrt(gx * gx + gy * gy)
    return out


@njit(parallel=True, fastmath=True)
def resize_cpu_parallel(src, out_h, out_w, method):
    in_h, in_w = src.shape
    out = np.zeros((out_h, out_w), dtype=np.float32)
    # ponytail: skala per-sumbu, bukan area ratio; tepat untuk resize seragam
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


# ----------------------------- kernel GPU ---------------------------------
# ponytail: jangan pakai min(a,b)/max(a,b) multi-argumen di sini — bug numba
# 0.67 + Python 3.14 saat diturunkan jadi device function CUDA (lihat
# test_bisect.py). Pakai if/elif clamp manual.
@cuda.jit
def sobel_gpu_kernel(d_img, d_out, h, w):
    r, c = cuda.grid(2)
    if 1 <= r < h - 1 and 1 <= c < w - 1:
        gx = (d_img[r-1, c+1] + 2.0*d_img[r, c+1] + d_img[r+1, c+1]) - \
             (d_img[r-1, c-1] + 2.0*d_img[r, c-1] + d_img[r+1, c-1])
        gy = (d_img[r+1, c-1] + 2.0*d_img[r+1, c] + d_img[r+1, c+1]) - \
             (d_img[r-1, c-1] + 2.0*d_img[r-1, c] + d_img[r-1, c+1])
        d_out[r, c] = math.sqrt(gx * gx + gy * gy)


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
