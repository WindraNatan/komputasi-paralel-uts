import os
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE, "DIV2K_valid_HR")
OUT_BASE = os.path.join(BASE, "dataset_uji")

TIERS = [
    ("rendah_720p", (1280, 720), 0, 30),
    ("sedang_1080p", (1920, 1080), 30, 60),
    ("tinggi_4k", (3840, 2160), 60, 90),
]

def main():
    files = sorted(f for f in os.listdir(SRC_DIR) if f.lower().endswith(".png"))
    for folder, (w, h), start, end in TIERS:
        target_dir = os.path.join(OUT_BASE, folder)
        os.makedirs(target_dir, exist_ok=True)
        print(f"Menyiapkan {folder} ({w}x{h})...")
        for fname in files[start:end]:
            src_path = os.path.join(SRC_DIR, fname)
            dst_path = os.path.join(target_dir, fname)
            with Image.open(src_path) as img:
                img.convert("L").resize((w, h), Image.Resampling.LANCZOS).save(dst_path, "PNG")
        print(f"Selesai: {target_dir}")

if __name__ == "__main__":
    main()
