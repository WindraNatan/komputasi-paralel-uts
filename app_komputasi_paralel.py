import os
import sys
import time
import math
import numpy as np
from PIL import Image
import streamlit as st
import pandas as pd

# Konfigurasi Path DLL CUDA Toolkit Lokal untuk Numba
base_dir = os.path.dirname(os.path.abspath(__file__))
cuda_path = os.path.join(base_dir, "cuda_toolkit")
if os.path.exists(cuda_path):
    os.environ["CUDA_HOME"] = cuda_path
    # ponytail: Windows cari DLL lewat PATH; root saja tidak cukup, subfolder bin dan nvvm/bin wajib
    for sub in ("bin", os.path.join("nvvm", "bin")):
        p = os.path.join(cuda_path, sub)
        if os.path.isdir(p):
            os.environ["PATH"] = p + ";" + os.environ.get("PATH", "")

from numba import set_num_threads, cuda, config as _numba_config

# Kernel bersama: definisi tunggal di kernels_paralel.py, dipakai juga benchmark_v2.py,
# sehingga kernel yang dijalankan dashboard selalu identik dengan yang diukur benchmark.
from kernels_paralel import (
    KERNEL_3X3,
    METODE_BICUBIC,
    METODE_BILINEAR,
    METODE_NEAREST,
    conv_cpu_parallel,
    conv_gpu_kernel,
    resize_cpu_parallel,
    resize_gpu_kernel,
    sobel_cpu_parallel,
    sobel_gpu_kernel,
)

# Alias label metode interpolasi untuk GUI (kunci int, konvensi sama dengan modul)
metode_labels = {
    METODE_NEAREST: "Nearest Neighbor",
    METODE_BILINEAR: "Bilinear",
    METODE_BICUBIC: "Bicubic (Catmull-Rom)"
}

# Uji hanya konfigurasi yang benar-benar tersedia dalam pool Numba host.
CPU_THREADS = tuple(n for n in (1, 2, 4, 8) if n <= _numba_config.NUMBA_NUM_THREADS)

# Pesan error CUDA dari warm_up_jit, ditampilkan di sidebar bila GPU gagal
cuda_error_msg = None

# Konfigurasi Tampilan Halaman Streamlit
st.set_page_config(
    page_title="Benchmark Komputasi Paralel",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema visual: gradient-border (ui-layouts) — slate/indigo, radius 16px
st.markdown('''
<style>
  .stApp { background: linear-gradient(45deg, #080b11, #1e293b 50%, #172033); }
  [data-testid="stSidebar"] { background: #080b11; border-right: 1px solid rgba(99,102,241,.25); }
  .stButton>button { border-radius: 12px; border: 1px solid transparent;
    background: linear-gradient(#080b11, #080b11) padding-box, conic-gradient(from 0deg, rgba(100,116,139,.48) 80%, #6366f1 86%, #a5b4fc 90%, #6366f1 94%, rgba(100,116,139,.48)) border-box; }
  div[data-testid="stMetric"] { border-radius: 16px; background: #0f172a; padding: 1rem; }
</style>
''', unsafe_allow_html=True)

# Pre-compile JIT Warm-up
@st.cache_resource
def warm_up_jit():
    dummy = np.zeros((32, 32), dtype=np.float32)
    k_dummy = np.zeros((3, 3), dtype=np.float32)
    set_num_threads(1)
    _ = conv_cpu_parallel(dummy, k_dummy)
    _ = sobel_cpu_parallel(dummy)
    _ = resize_cpu_parallel(dummy, 64, 64, METODE_BICUBIC)

    cuda_available = False
    global cuda_error_msg
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            d_in = cuda.to_device(dummy)
            d_out = cuda.device_array((32, 32), dtype=np.float32)
            sobel_gpu_kernel[(2, 2), (16, 16)](d_in, d_out, 32, 32)
            d_out2 = cuda.device_array((64, 64), dtype=np.float32)
            resize_gpu_kernel[(2, 2), (16, 16)](d_in, d_out2, 64, 64, METODE_BICUBIC, 0.5, 0.5)
            cuda.synchronize()
        cuda_available = True
        cuda_error_msg = None
    except Exception as e:
        cuda_available = False
        import traceback
        cuda_error_msg = "".join(traceback.format_exception(e))
    return cuda_available

cuda_status = warm_up_jit()

st.title("Benchmark CPU vs GPU")
st.caption("Diukur pada host yang menjalankan aplikasi; hasil laptop ada di REKAP_BENCHMARK.md.")

def run_cpu(img, op, filt, meth, out_h, out_w):
    if op == "Upscaling Citra":
        return resize_cpu_parallel(img, out_h, out_w, meth)
    if filt == "Sobel Edge Detection":
        return sobel_cpu_parallel(img)
    return conv_cpu_parallel(img, kernel_dict[filt])

def gpu_blocks(h, w):
    tpb = (16, 16)
    return (math.ceil(h / tpb[1]), math.ceil(w / tpb[0])), tpb

def run_gpu(d_in, d_out, h, w, op, filt, meth, out_h, out_w, sy, sx):
    if op == "Upscaling Citra":
        grid, tpb = gpu_blocks(out_h, out_w)
        resize_gpu_kernel[grid, tpb](d_in, d_out, out_h, out_w, meth, sy, sx)
    else:
        grid, tpb = gpu_blocks(h, w)
        if filt == "Sobel Edge Detection":
            sobel_gpu_kernel[grid, tpb](d_in, d_out, h, w)
        else:
            d_k = cuda.to_device(kernel_dict[filt])
            conv_gpu_kernel[grid, tpb](d_in, d_k, d_out, h, w, 3, 3)
    cuda.synchronize()

st.sidebar.header("Pengujian")

source_option = st.sidebar.radio(
    "Sumber Citra:",
    ["Citra Acuan (Peppers)", "Batch Dataset (DIV2K)", "Unggah Citra"]
)

img_loaded = None
img_name = ""
files = []
dataset_dir = os.path.join(base_dir, "DIV2K_valid_HR")

preset_files = {
    "Peppers 1080p (1920x1080)": os.path.join(base_dir, "peppers_1080p.png"),
    "Peppers 4K (3840x2160)": os.path.join(base_dir, "peppers_4k.png"),
    "Peppers 8K (7680x4320)": os.path.join(base_dir, "peppers_8k.png")
}

if source_option == "Citra Acuan (Peppers)":
    selected_preset = st.sidebar.selectbox("Pilih Resolusi:", list(preset_files.keys()))
    path_preset = preset_files[selected_preset]
    if os.path.exists(path_preset):
        img_loaded = Image.open(path_preset).convert('L')
        img_name = selected_preset
    else:
        st.sidebar.warning(f"Berkas {selected_preset} tidak ada di folder proyek.")
elif source_option == "Batch Dataset (DIV2K)":
    tier_options = {
        "Rendah 720p (30 Citra)": os.path.join(base_dir, "dataset_uji", "rendah_720p"),
        "Sedang 1080p (30 Citra)": os.path.join(base_dir, "dataset_uji", "sedang_1080p"),
        "Tinggi 4K (30 Citra)": os.path.join(base_dir, "dataset_uji", "tinggi_4k"),
        "Semua DIV2K (100 Citra)": os.path.join(base_dir, "DIV2K_valid_HR"),
    }
    selected_tier = st.sidebar.selectbox("Kategori Dataset:", list(tier_options.keys()))
    dataset_dir = tier_options[selected_tier]

    if os.path.isdir(dataset_dir):
        files = sorted(f for f in os.listdir(dataset_dir) if f.lower().endswith(".png"))
        if not files:
            st.sidebar.warning(f"Tidak ada file PNG di {os.path.basename(dataset_dir)}.")
        else:
            default_n = min(30, len(files))
            n = st.sidebar.slider("Jumlah Citra:", 1, len(files), default_n)
            files = files[:n]
            st.sidebar.success(f"{len(files)} citra tersedia.")
    else:
        st.sidebar.warning(f"Folder {os.path.basename(dataset_dir)} tidak ada di host ini.")
        st.info("Mode batch butuh dataset lokal. Streamlit Cloud tidak menyertakan dataset_uji; jalankan app secara lokal.")

    _res_ops = {"720p (1280x720)": (1280, 720),
                "1080p (1920x1080)": (1920, 1080),
                "4K (3840x2160)": (3840, 2160),
                "8K (7680x4320)": (7680, 4320)}
    _default_idx = 0 if "720p" in selected_tier else (1 if "1080p" in selected_tier else 2)
    _res_label = st.sidebar.selectbox("Resolusi Target (Konvolusi):", list(_res_ops.keys()), index=_default_idx)
    batch_res = _res_ops[_res_label]
else:
    uploaded_file = st.sidebar.file_uploader("Unggah Citra:", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        img_loaded = Image.open(uploaded_file).convert('L')
        img_name = uploaded_file.name

operation = st.sidebar.selectbox(
    "Operasi Komputasi:",
    ["Filter Konvolusi Spasial", "Upscaling Citra"]
)

filter_type = None
method_code = METODE_BICUBIC
target_size = None

if operation == "Filter Konvolusi Spasial":
    filter_type = st.sidebar.selectbox(
        "Jenis Filter:",
        ["Sobel Edge Detection", "Gaussian Blur 3x3", "Sharpening 3x3"]
    )
else:
    method_code = st.sidebar.selectbox(
        "Metode Interpolasi:",
        list(metode_labels.keys()),
        format_func=lambda m: metode_labels[m]
    )
    target_size = st.sidebar.selectbox(
        "Resolusi Target:",
        ["4K (3840x2160)", "8K (7680x4320)"]
    )

kernel_dict = {
    "Gaussian Blur 3x3": KERNEL_3X3["gaussian"],
    "Sharpening 3x3": KERNEL_3X3["sharpen"]
}

exec_mode = st.sidebar.selectbox(
    "Mode Eksekusi:",
    ["Semua Konfigurasi Tersedia", "Uji Satuan (Thread Tertentu / GPU)"]
)

single_target = "CPU 1 thread"
if exec_mode == "Uji Satuan (Thread Tertentu / GPU)":
    options = [f"CPU {n} thread" for n in CPU_THREADS]
    if cuda_status:
        options.append("GPU NVIDIA CUDA")
    single_target = st.sidebar.selectbox("Pilih Unit:", options)

st.sidebar.markdown("---")
st.sidebar.markdown("**Perangkat**")
st.sidebar.write(f"CPU host: batas pool Numba {_numba_config.NUMBA_NUM_THREADS} thread.")
st.sidebar.caption("Thread yang diuji: " + ", ".join(map(str, CPU_THREADS)) + "; thread di atas batas host tidak dijalankan.")
if cuda_status:
    dev = cuda.get_current_device()
    nama_gpu = dev.name.decode(errors="ignore").strip() if isinstance(dev.name, bytes) else str(dev.name)
    jumlah_sm = int(dev.MULTIPROCESSOR_COUNT)
    st.sidebar.success(f"• **GPU:** {nama_gpu} ({jumlah_sm} SM)")
else:
    st.sidebar.info("CUDA tidak tersedia; pengujian menggunakan CPU host.")
    if cuda_error_msg:
        with st.sidebar.expander("Detail deteksi CUDA"):
            st.code(cuda_error_msg, language="text")

if files:
    if operation == "Upscaling Citra":
        with Image.open(os.path.join(dataset_dir, files[0])) as _first_im:
            src_w, src_h = _first_im.size

        if target_size.startswith("4K"):
            out_w, out_h = 3840, 2160
        else:
            out_w, out_h = 7680, 4320

        if out_w <= src_w or out_h <= src_h:
            st.warning(f"Resolusi target ({out_w}x{out_h}) harus lebih besar dari resolusi sumber dataset ({src_w}x{src_h}).")
            st.stop()

        sy = src_h / out_h
        sx = src_w / out_w
        st.info(f"Batch: **{len(files)} citra** | Input **{src_w}x{src_h}** → Target **{out_w}x{out_h}** | Metode: **{metode_labels[method_code]}**")
    else:
        src_w, src_h = batch_res
        out_w, out_h = batch_res
        sy = sx = 1.0
        st.info(f"Batch: **{len(files)} citra** | Resolusi: **{out_w}x{out_h}** | Filter: **{filter_type}**")

    col_btn, _ = st.columns([1, 4])
    start_btn = col_btn.button(f"Jalankan batch ({len(files)} citra)", type="primary")

    if start_btn:
        with st.spinner(f"Memproses {len(files)} citra..."):
            prog = st.progress(0.0, text="Memulai")
            rows = []
            for i, fname in enumerate(files, 1):
                img0 = np.array(Image.open(os.path.join(dataset_dir, fname)).convert("L"),
                                dtype=np.float32)
                if (img0.shape[1], img0.shape[0]) != (src_w, src_h):
                    img0 = np.array(Image.fromarray(img0.astype(np.uint8)).resize(
                        (src_w, src_h), Image.Resampling.LANCZOS), dtype=np.float32)
                img_arr = np.ascontiguousarray(img0)
                h, w = img_arr.shape

                rec = {"No": i, "Citra": fname, "Lebar": w, "Tinggi": h}
                t1 = None
                cpu1_out = None
                for c in CPU_THREADS:
                    set_num_threads(c)
                    t0 = time.perf_counter()
                    out_c = run_cpu(img_arr, operation, filter_type, method_code, out_h, out_w)
                    dur = time.perf_counter() - t0
                    if c == 1:
                        t1 = dur
                        cpu1_out = out_c
                    rec[f"CPU {c} thread (ms)"] = dur * 1000.0
                    rec[f"Speedup CPU {c}"] = t1 / dur

                gpu_out = None
                if cuda_status:
                    d_in = cuda.to_device(img_arr)
                    d_out = cuda.device_array((out_h, out_w), dtype=np.float32)
                    t0 = time.perf_counter()
                    run_gpu(d_in, d_out, h, w, operation, filter_type, method_code,
                            out_h, out_w, sy, sx)
                    t_kernel = time.perf_counter() - t0
                    gpu_out = d_out.copy_to_host()
                    rec["GPU Kernel (ms)"] = t_kernel * 1000.0
                    rec["Speedup GPU"] = t1 / t_kernel

                if operation == "Upscaling Citra":
                    ref = np.array(Image.fromarray(img_arr.astype(np.uint8)).resize(
                        (out_w, out_h), Image.Resampling.LANCZOS), dtype=np.float32)
                    eval_target = gpu_out if gpu_out is not None else cpu1_out
                    eval_clamped = np.clip(eval_target, 0, 255)
                    mse_val = float(np.mean((eval_clamped - ref) ** 2))
                    psnr_val = float(20.0 * math.log10(255.0 / math.sqrt(mse_val))) if mse_val > 0 else float("inf")
                    rec["MSE"] = round(mse_val, 4)
                    rec["PSNR (dB)"] = round(psnr_val, 2)

                rows.append(rec)
                prog.progress(i / len(files), text=f"{i}/{len(files)}")

            df_batch = pd.DataFrame(rows)

        st.subheader("Hasil batch")

        if operation == "Upscaling Citra" and "PSNR (dB)" in df_batch.columns:
            st.markdown("**Kualitas batch (acuan PIL Lanczos)**")
            q_col1, q_col2 = st.columns(2)
            q_col1.metric("Median MSE", f"{df_batch['MSE'].median():.4f}")
            q_col2.metric("Median PSNR", f"{df_batch['PSNR (dB)'].median():.2f} dB")

        agg = {"Unit Pemroses": [], "Median Waktu (ms)": [], "Rerata Waktu (ms)": [],
               "Median Speedup": [], "Rerata Speedup": [], "Karp-Flatt": []}

        def _tambah(kolom_waktu, kolom_spd, label, cores=1):
            agg["Unit Pemroses"].append(label)
            agg["Median Waktu (ms)"].append(df_batch[kolom_waktu].median())
            agg["Rerata Waktu (ms)"].append(df_batch[kolom_waktu].mean())
            med_spd = df_batch[kolom_spd].median()
            agg["Median Speedup"].append(med_spd)
            agg["Rerata Speedup"].append(df_batch[kolom_spd].mean())
            if cores > 1:
                kf = ((1.0 / med_spd) - (1.0 / cores)) / (1.0 - (1.0 / cores))
                agg["Karp-Flatt"].append(f"{kf:.4f}")
            else:
                agg["Karp-Flatt"].append("-")

        for c in CPU_THREADS:
            _tambah(f"CPU {c} thread (ms)", f"Speedup CPU {c}",
                    f"CPU {c} thread", cores=c)
        if cuda_status:
            _tambah("GPU Kernel (ms)", "Speedup GPU", "GPU CUDA (Kernel)", cores=0)
        df_agg = pd.DataFrame(agg)

        st.dataframe(
            df_agg.style.format({
                "Median Waktu (ms)": "{:.1f}",
                "Rerata Waktu (ms)": "{:.1f}",
                "Median Speedup": "{:.2f}x",
                "Rerata Speedup": "{:.2f}x"
            }),
            use_container_width=True
        )
        st.caption("Karp-Flatt memakai jumlah thread yang dijalankan, bukan inti fisik; tidak berlaku untuk 1 thread atau GPU.")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("**Waktu median (ms)**")
            st.bar_chart(df_agg.set_index("Unit Pemroses")[["Median Waktu (ms)"]])
        with col_g2:
            st.markdown("**Speedup relatif (CPU 1 thread)**")
            st.bar_chart(df_agg.set_index("Unit Pemroses")[["Median Speedup"]])

        with st.expander("Rincian per citra", expanded=False):
            st.dataframe(df_batch, use_container_width=True)

        csv_batch = df_batch.to_csv(index=False).encode("utf-8")
        nama_op = (filter_type or metode_labels[method_code]).lower().replace(" ", "_")
        st.download_button(
            label="Unduh CSV batch",
            data=csv_batch,
            file_name=f"batch_div2k_{operation.split()[0].lower()}_{nama_op}"
                      f"_{len(files)}citra_{out_w}x{out_h}.csv",
            mime="text/csv"
        )

elif img_loaded is not None:
    img_arr = np.array(img_loaded, dtype=np.float32)
    h, w = img_arr.shape
    total_pixels = h * w
    
    st.info(f"Citra: **{img_name}** ({w}x{h} piksel)")

    if operation == "Upscaling Citra":
        if target_size.startswith("4K"):
            out_w, out_h = 3840, 2160
        else:
            out_w, out_h = 7680, 4320
        if out_w == w and out_h == h:
            st.warning(f"Resolusi citra sudah {w}x{h}. Pilih resolusi target yang lebih tinggi.")
            st.stop()
        if out_w < w or out_h < h:
            st.warning(f"Target {out_w}x{out_h} lebih kecil dari citra input ({w}x{h}). Pilih resolusi target yang lebih tinggi.")
            st.stop()
        sy = h / out_h
        sx = w / out_w
        st.info(f"Target: **{out_w}x{out_h}** piksel | Metode: **{metode_labels[method_code]}**")
    else:
        out_w, out_h = w, h
        sy = sx = 1.0

    col_btn, _ = st.columns([1, 4])
    start_btn = col_btn.button("Mulai pengujian", type="primary")
    
    if start_btn:
        st.subheader("Hasil")
        
        if exec_mode == "Uji Satuan (Thread Tertentu / GPU)":
            with st.spinner(f"Memproses pada {single_target}..."):
                res_img = None
                t_exec = 0.0
                
                if "CPU" in single_target:
                    cores = int(single_target.split()[1])
                    set_num_threads(cores)
                    t0 = time.perf_counter()
                    res_img = run_cpu(img_arr, operation, filter_type, method_code, out_h, out_w)
                    t_exec = time.perf_counter() - t0
                else: # GPU CUDA
                    t0 = time.perf_counter()
                    d_in = cuda.to_device(img_arr)
                    d_out = cuda.device_array((out_h, out_w), dtype=np.float32)
                    run_gpu(d_in, d_out, h, w, operation, filter_type, method_code,
                            out_h, out_w, sy, sx)
                    res_img = d_out.copy_to_host()
                    t_exec = time.perf_counter() - t0

                # Normalisasi hasil gambar
                res_norm = np.clip(res_img, 0, 255).astype(np.uint8)
                
                # Tampilkan Kartu Metrik
                out_pixels = out_h * out_w
                c1, c2, c3 = st.columns(3)
                c1.metric("Unit Pemroses", single_target)
                c2.metric("Waktu Eksekusi", f"{1000*t_exec:.1f} ms", f"{t_exec:.4f} s")
                c3.metric("Throughput", f"{(out_pixels / (t_exec * 1e6)):.2f} MPiksel/s")

                im_col1, im_col2 = st.columns(2)
                im_col1.image(img_loaded, caption=f"Input ({w}x{h})", use_container_width=True)
                im_col2.image(res_norm, caption=f"Output ({single_target})", use_container_width=True)

        else:
            with st.spinner("Menjalankan pengujian terpilih..."):
                bench_results = []
                last_result_img = None
                
                t1_baseline = None
                res_cpu1 = None
                for c in CPU_THREADS:
                    set_num_threads(c)
                    t0 = time.perf_counter()
                    res = run_cpu(img_arr, operation, filter_type, method_code, out_h, out_w)
                    dur = time.perf_counter() - t0
                    last_result_img = res

                    if c == 1:
                        t1_baseline = dur
                        res_cpu1 = res
                    
                    speedup = t1_baseline / dur
                    eff = (speedup / c) * 100.0
                    if c > 1:
                        kf = ((1.0 / speedup) - (1.0 / c)) / (1.0 - (1.0 / c))
                        kf_str = f"{kf:.4f}"
                    else:
                        kf_str = "-"
                    bench_results.append({
                        "Unit Pemroses": f"CPU {c} thread",
                        "Waktu (detik)": dur,
                        "Waktu (ms)": dur * 1000.0,
                        "Speedup": speedup,
                        "Efisiensi (%)": eff,
                        "Karp-Flatt": kf_str,
                        "Kategori": "CPU Multi-Thread"
                    })
                
                if cuda_status:
                    t_start_total = time.perf_counter()
                    d_in = cuda.to_device(img_arr)
                    d_out = cuda.device_array((out_h, out_w), dtype=np.float32)

                    t_start_kernel = time.perf_counter()
                    run_gpu(d_in, d_out, h, w, operation, filter_type, method_code,
                            out_h, out_w, sy, sx)
                    t_dur_kernel = time.perf_counter() - t_start_kernel

                    res_gpu = d_out.copy_to_host()
                    t_dur_total = time.perf_counter() - t_start_total
                    last_result_img = res_gpu

                    bench_results.append({
                        "Unit Pemroses": "GPU CUDA (Kernel Murni)",
                        "Waktu (detik)": t_dur_kernel,
                        "Waktu (ms)": t_dur_kernel * 1000.0,
                        "Speedup": t1_baseline / t_dur_kernel,
                        "Efisiensi (%)": 0.0,
                        "Karp-Flatt": "-",
                        "Kategori": "GPU CUDA"
                    })
                    bench_results.append({
                        "Unit Pemroses": "GPU CUDA (Total I/O PCIe)",
                        "Waktu (detik)": t_dur_total,
                        "Waktu (ms)": t_dur_total * 1000.0,
                        "Speedup": t1_baseline / t_dur_total,
                        "Efisiensi (%)": 0.0,
                        "Karp-Flatt": "-",
                        "Kategori": "GPU CUDA"
                    })
                
                df_res = pd.DataFrame(bench_results)
                
                st.dataframe(
                    df_res.style.format({
                        "Waktu (detik)": "{:.4f}",
                        "Waktu (ms)": "{:.1f}",
                        "Speedup": "{:.2f}x",
                        "Efisiensi (%)": "{:.1f}%"
                    }),
                    use_container_width=True
                )
                st.caption("Karp-Flatt memakai jumlah thread yang dijalankan, bukan inti fisik; tidak berlaku untuk 1 thread atau GPU.")
                
                col_g1, col_g2 = st.columns(2)
                
                with col_g1:
                    st.markdown("**Waktu (ms)**")
                    chart_time = df_res.set_index("Unit Pemroses")[["Waktu (ms)"]]
                    st.bar_chart(chart_time)
                    
                with col_g2:
                    st.markdown("**Speedup (vs CPU 1 thread)**")
                    chart_spd = df_res.set_index("Unit Pemroses")[["Speedup"]]
                    st.bar_chart(chart_spd)
                
                im_c1, im_c2 = st.columns(2)
                im_c1.image(img_loaded, caption=f"Input ({w}x{h})", use_container_width=True)
                im_c2.image(res_norm,
                            caption=f"Output ({filter_type or metode_labels[method_code]})",
                            use_container_width=True)

                if cuda_status and res_cpu1 is not None and last_result_img is not None:
                    max_diff = float(np.max(np.abs(last_result_img - res_cpu1)))
                    st.caption(f"Deviasi maksimum CPU vs GPU = {max_diff:.6f}")

                if operation == "Upscaling Citra" and last_result_img is not None:
                    hasil = np.clip(last_result_img, 0, 255)
                    ref = np.array(img_loaded.resize((out_w, out_h), Image.Resampling.LANCZOS),
                                   dtype=np.float32)
                    mse = float(np.mean((hasil - ref) ** 2))
                    if mse > 0:
                        psnr = float(20.0 * math.log10(255.0 / math.sqrt(mse)))
                    else:
                        psnr = float('inf')
                    st.markdown("**Kualitas upscaling (acuan PIL Lanczos)**")
                    st.write(f"MSE: **{mse:.4f}** | PSNR: **{psnr:.2f} dB** ({metode_labels[method_code]})")

                csv_data = df_res.to_csv(index=False).encode('utf-8')
                nama_op = (filter_type or metode_labels[method_code]).lower().replace(' ', '_')
                st.download_button(
                    label="Unduh CSV hasil",
                    data=csv_data,
                    file_name=f"benchmark_{operation.split()[0].lower()}_{nama_op}_{w}x{h}_ke_{out_w}x{out_h}.csv",
                    mime="text/csv"
                )

else:
    st.info("Pilih citra atau unggah berkas untuk mulai.")
