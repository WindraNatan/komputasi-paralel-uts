import time
import math
import numpy as np
from PIL import Image, ImageDraw
from numba import jit, prange, set_num_threads

def create_sample_image(width=1920, height=1080):
    img = Image.new('L', (width, height), color=128)
    draw = ImageDraw.Draw(img)
    for i in range(40):
        draw.rectangle([i * 45, i * 25, i * 45 + 120, i * 25 + 90], outline=255, fill=i * 6 % 255)
        draw.ellipse([width - i * 45 - 120, i * 25, width - i * 45, i * 25 + 90], outline=0, fill=(255 - i * 6) % 255)
    return img

@jit(nopython=True, parallel=True)
def sobel_cpu(image, output):
    height, width = image.shape
    for y in prange(1, height - 1):
        for x in range(1, width - 1):
            gx = (
                -1.0 * image[y - 1, x - 1] + 1.0 * image[y - 1, x + 1]
                -2.0 * image[y,     x - 1] + 2.0 * image[y,     x + 1]
                -1.0 * image[y + 1, x - 1] + 1.0 * image[y + 1, x + 1]
            )
            gy = (
                -1.0 * image[y - 1, x - 1] - 2.0 * image[y - 1, x] - 1.0 * image[y - 1, x + 1]
                +1.0 * image[y + 1, x - 1] + 2.0 * image[y + 1, x] + 1.0 * image[y + 1, x + 1]
            )
            output[y, x] = np.sqrt(gx * gx + gy * gy)

def main():
    print("=" * 65)
    print("PENGUJIAN FILTER KONVOLUSI SOBEL 3x3")
    print("Perangkat: Intel Core 5 210H (8 Cores, 12 Threads)")
    print("=" * 65)

    width, height = 1920, 1080
    print(f"Membuat citra uji sintesis resolusi {width}x{height} (Full HD)...")
    img = create_sample_image(width, height)
    img_arr = np.array(img, dtype=np.float32)
    out_arr = np.zeros_like(img_arr)

    # Simpan citra input asli
    input_path = "gambar_input.png"
    img.save(input_path)
    print(f"Citra input disimpan di: {input_path}")

    # Pemanasan kompilasi JIT (Warm-up)
    set_num_threads(8)
    sobel_cpu(img_arr, out_arr)

    print("\n--- Memulai Pengujian Skalabilitas CPU (1, 2, 4, 8 Core) ---")
    core_configs = [1, 2, 4, 8]
    t_baseline = 0.0

    print(f"{'Konfigurasi':<15} | {'Waktu Rata-rata':<18} | {'Speedup':<10} | {'Efisiensi':<10}")
    print("-" * 65)

    for cores in core_configs:
        set_num_threads(cores)
        sobel_cpu(img_arr, out_arr)  # Pemanasan thread pool

        durations = []
        for _ in range(10):
            t0 = time.perf_counter()
            sobel_cpu(img_arr, out_arr)
            t1 = time.perf_counter()
            durations.append(t1 - t0)

        avg_time = float(np.mean(durations))

        if cores == 1:
            t_baseline = avg_time
            speedup = 1.0
            efficiency = 100.0
            label = "1 Core (Sekuensial)"
        else:
            speedup = t_baseline / avg_time
            efficiency = (speedup / cores) * 100.0
            label = f"{cores} Core (Paralel)"

        print(f"{label:<15} | {avg_time * 1000:10.2f} ms       | {speedup:8.2f}x | {efficiency:8.1f}%")

    # Simpan citra hasil
    result_path = "hasil_sobel.png"
    result_img = Image.fromarray(np.clip(out_arr, 0, 255).astype(np.uint8))
    result_img.save(result_path)
    print("\n" + "=" * 65)
    print(f"Citra hasil deteksi tepi berhasil disimpan di: {result_path}")
    print("=" * 65)

if __name__ == "__main__":
    main()
