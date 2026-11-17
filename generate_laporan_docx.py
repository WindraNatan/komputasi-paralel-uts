"""Generator laporan UTS Komputasi Paralel (Bab I-V + Daftar Pustaka).

Data angka diambil dari REKAP_BENCHMARK.md (final 2026-10-23) dan hasil
verifikasi topologi CPU 2026-11-08.
"""

import os

import docx
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "Laporan_UTS_Komputasi_Paralel.docx")


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=60, bottom=60, left=120, right=120):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)


def build_document():
    doc = docx.Document()

    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(3.0)
        section.bottom_margin = Cm(3.0)
        section.left_margin = Cm(4.0)
        section.right_margin = Cm(3.0)

    normal = doc.styles['Normal']
    normal.font.name = 'Times New Roman'
    normal.font.size = Pt(12)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(4)

    def emit(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_indent=Cm(1.0),
             space_after=4, bold=False, italic_all=False):
        """Tulis paragraf. Bagian dibatasi _..._ diformat miring."""
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.5
        if first_indent is not None:
            p.paragraph_format.first_line_indent = first_indent
        if text:
            for i, seg in enumerate(text.split('_')):
                if not seg:
                    continue
                r = p.add_run(seg)
                r.font.name = 'Times New Roman'
                r.font.size = Pt(12)
                r.font.italic = italic_all or i % 2 == 1
                r.font.bold = bold
        return p

    def h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(14)
        r.font.bold = True
        return p

    def h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.bold = True
        return p

    def h3(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.italic = True
        return p

    def eq(text, number=None):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.5
        body = text if number is None else f"{text}    ({number})"
        r = p.add_run(body)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.italic = True
        return p

    def table(header, rows, widths=None, caption=None, font_size=10):
        if caption:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(caption)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(11)
            r.font.bold = True
        t = doc.add_table(rows=1 + len(rows), cols=len(header))
        t.style = 'Table Grid'
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        data = [header] + rows
        for i, row in enumerate(data):
            for j, val in enumerate(row):
                cell = t.cell(i, j)
                cell.text = ''
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(0)
                r = p.add_run(str(val))
                r.font.name = 'Times New Roman'
                r.font.size = Pt(font_size)
                if i == 0:
                    r.font.bold = True
                set_cell_margins(cell)
            if i == 0:
                for j in range(len(header)):
                    set_cell_background(t.cell(i, j), 'D9E2F3')
        if widths:
            for j, w in enumerate(widths):
                for i in range(len(data)):
                    t.cell(i, j).width = Cm(w)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)
        return t

    def bullet(text, level=0):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(1.0 + 0.75 * level)
        p.paragraph_format.first_line_indent = Cm(-0.75)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(('• ' if level == 0 else '– ') + text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        return p

    def numlist(num, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(1.25)
        p.paragraph_format.first_line_indent = Cm(-0.75)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.5
        r = p.add_run(f"{num}. {text}")
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        return p

    def page_break():
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # HALAMAN COVER
    emit("LAPORAN TUGAS UJIAN TENGAH SEMESTER", align=WD_ALIGN_PARAGRAPH.CENTER,
         first_indent=None, space_after=2, bold=True)
    emit("MATA KULIAH KOMPUTASI PARALEL", align=WD_ALIGN_PARAGRAPH.CENTER,
         first_indent=None, space_after=24, bold=True)

    emit("IMPLEMENTASI DAN ANALISIS PERFORMA FILTER KONVOLUSI CITRA "
         "RESOLUSI TINGGI MENGGUNAKAN NVIDIA CUDA DIBANDINGKAN PEMROSESAN "
         "CPU _MULTI-THREAD_", align=WD_ALIGN_PARAGRAPH.CENTER,
         first_indent=None, space_after=24, bold=True)

    emit("DISUSUN OLEH:", align=WD_ALIGN_PARAGRAPH.CENTER,
         first_indent=None, space_after=4)
    for nama, nim in [("ALFONSO ANDRANO", "H1051241031"),
                      ("WINDRA MAXWALL DARI NATALIUS", "H1051241073"),
                      ("RIZAL SAPUTRA", "H1051241095"),
                      ("MUHAMMAD RIFQI MAULANA", "H1051241101")]:
        emit(f"{nama}", align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=None,
             space_after=0)
        emit(f"NIM. {nim}", align=WD_ALIGN_PARAGRAPH.CENTER,
             first_indent=None, space_after=4)

    emit("", first_indent=None, space_after=18)
    emit("PROGRAM STUDI REKAYASA SISTEM KOMPUTER",
         align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=None, space_after=2, bold=True)
    emit("FAKULTAS MATEMATIKA DAN ILMU PENGETAHUAN ALAM",
         align=WD_ALIGN_PARAGRAPH.CENTER, first_indent=None, space_after=2, bold=True)
    emit("UNIVERSITAS TANJUNPURA", align=WD_ALIGN_PARAGRAPH.CENTER,
         first_indent=None, space_after=2, bold=True)
    emit("PONTIANAK, 2026", align=WD_ALIGN_PARAGRAPH.CENTER,
         first_indent=None, space_after=2, bold=True)

    page_break()

    # KATA PENGANTAR
    h1("KATA PENGANTAR")
    emit("Puji syukur penulis panjatkan ke hadirat Tuhan Yang Maha Esa atas "
         "selesainya laporan tugas ujian tengah semester mata kuliah Komputasi "
         "Paralel ini. Laporan disusun sebagai laporan pelaksanaan pengujian "
         "performa pemrosesan citra resolusi tinggi pada arsitektur komputasi "
         "paralel heterogen, yakni prosesor CPU multi-_thread_ dan kartu grafis "
         "GPU NVIDIA CUDA.")
    emit("Pengujian dilakukan secara terukur pada perangkat komputasi nyata "
         "dengan dataset standar pemrosesan citra. Angka-angka dalam laporan "
         "ini bersumber dari hasil pengukuran yang telah melalui pemeriksaan "
         "kualitas data, sehingga setiap klaim yang dinyatakan dapat ditelusuri "
         "kembali ke berkas data pengukuran. Penulis menyadari bahwa metode "
         "pengukuran yang dipakai memiliki keterbatasan tersendiri, dan "
         "keterbatasan tersebut dituliskan secara terbuka pada bab pembahasan "
         "agar hasil pembacaan tidak melebihi apa yang sesungguhnya terdukung "
         "oleh data.")
    emit("Penulis berterima kasih kepada dosen pengampu mata kuliah Komputasi "
         "Paralel serta para rekan mahasiswa yang memberi masukan selama "
         "pelaksanaan pengujian. Saran perbaikan dari pembaca akan membantu "
         "menyempurnakan penyusunan laporan pada tahap berikutnya.")
    emit("Pontianak, November 2026", align=WD_ALIGN_PARAGRAPH.RIGHT,
         first_indent=None, space_after=2)
    emit("Penulis", align=WD_ALIGN_PARAGRAPH.RIGHT, first_indent=None)
    page_break()

    # DAFTAR ISI
    h1("DAFTAR ISI")
    for item in [
        "KATA PENGANTAR", "DAFTAR ISI", "DAFTAR TABEL", "DAFTAR PERSAMAAN",
        "BAB I PENDAHULUAN",
        "    1.1 Latar Belakang", "    1.2 Rumusan Masalah",
        "    1.3 Tujuan Penelitian", "    1.4 Batasan Masalah",
        "    1.5 Manfaat Penelitian",
        "BAB II LANDASAN TEORI",
        "    2.1 Pemrosesan Citra Digital Resolusi Tinggi",
        "    2.2 Filter Konvolusi Spasial 3x3",
        "    2.3 Peningkatan Resolusi Citra",
        "    2.4 Komputasi Paralel pada CPU",
        "    2.5 Arsitektur Prosesor Hybrid dan _Simultaneous Multithreading_",
        "    2.6 Arsitektur GPU CUDA",
        "    2.7 Metrik Kinerja Komputasi Paralel",
        "    2.8 Penelitian Terdahulu",
        "BAB III METODOLOGI PENELITIAN",
        "    3.1 Desain Penelitian", "    3.2 Perangkat Keras Pengujian",
        "    3.3 Perangkat Lunak Pengujian", "    3.4 Dataset Citra",
        "    3.5 Prosedur Pengukuran pada CPU",
        "    3.6 Prosedur Pengukuran pada GPU",
        "    3.7 Strategi Statistik Pengukuran",
        "    3.8 Validasi Ekivalensi dan Kualitas Keluaran",
        "    3.9 Aplikasi _Dashboard_ Streamlit",
        "BAB IV HASIL DAN PEMBAHASAN",
        "    4.1 Verifikasi Topologi Prosesor Pengujian",
        "    4.2 Hasil Pengukuran Filter Konvolusi",
        "    4.3 Hasil Pengukuran Peningkatan Resolusi",
        "    4.4 Pembahasan",
        "    4.5 Keterbatasan Pengukuran",
        "BAB V PENUTUP",
        "    5.1 Kesimpulan", "    5.2 Saran",
        "DAFTAR PUSTAKA",
    ]:
        p_isi = emit(item.strip(), align=WD_ALIGN_PARAGRAPH.LEFT,
                     first_indent=None, space_after=1)
        if item.startswith("    "):
            p_isi.paragraph_format.left_indent = Cm(0.75)
    page_break()

    # DAFTAR TABEL
    h1("DAFTAR TABEL")
    for item in [
        "Tabel 2.1 Ringkasan Penelitian Terdahulu",
        "Tabel 3.1 Spesifikasi Perangkat Keras Pengujian",
        "Tabel 3.2 Topologi Prosesor Intel Core 5 210H Hasil Verifikasi",
        "Tabel 3.3 Parameter Pengukuran GPU",
        "Tabel 4.1 Ringkasan Hasil Probe Afinitas pada Beban Kerja "
        "Rantai Aritmetika",
        "Tabel 4.2 Hasil Pengukuran Filter Konvolusi 3x3 "
        "(Median 100 Citra, Milidetik)",
        "Tabel 4.3 Hasil Pengukuran _Upscaling_ (Median 100 Citra, "
        "Milidetik)",
    ]:
        emit(item, align=WD_ALIGN_PARAGRAPH.LEFT, first_indent=None,
             space_after=1)
    page_break()

    # DAFTAR PERSAMAAN
    h1("DAFTAR PERSAMAAN")
    for item in [
        "Persamaan 2.1 Konvolusi Diskret Dua Dimensi",
        "Persamaan 2.2 Magnitudo Gradien Operator Sobel",
        "Persamaan 2.3 Pemetaan Koordinat _Center-Aligned_",
        "Persamaan 2.4 Percepatan (_Speedup_)",
        "Persamaan 2.5 Efisiensi Paralel",
        "Persamaan 2.6 Hukum Amdahl",
        "Persamaan 2.7 Metrik Karp-Flatt",
        "Persamaan 2.8 _Mean Squared Error_ dan _Peak Signal-to-Noise Ratio_",
        "Persamaan 3.1 Waktu Total Pemrosesan GPU",
    ]:
        emit(item, align=WD_ALIGN_PARAGRAPH.LEFT, first_indent=None,
             space_after=1)
    page_break()

    # BAB I PENDAHULUAN
    h1("BAB I")
    h1("PENDAHULUAN")

    h2("1.1 Latar Belakang")
    emit("Pemrosesan citra digital pada resolusi tinggi merupakan kebutuhan "
         "pokok pada bidang penginderaan jauh, diagnosis medis, hiburan visual, "
         "dan sistem visi komputer. Beban komputasi pada operasi pemrosesan "
         "citra tidak hanya bergantung pada jumlah piksel, melainkan juga pada "
         "kompleksitas operator spasial yang diterapkan pada setiap pikselnya. "
         "Operasi konvolusi matriks dua dimensi pada citra 8K UHD "
         "(33,17 megapiksel) dengan kernel 3x3 menuntut sekitar 300 juta "
         "operasi aritmetika per kanal warna, sedangkan operasi peningkatan "
         "resolusi (_upscaling_) dari 4K ke 8K harus menghasilkan sekitar 25 "
         "juta piksel baru yang nilainya diinterpolasi dari piksel sumber. "
         "Pemrosesan sekuensial pada inti prosesor tunggal menghasilkan "
         "latensi yang tinggi karena keterbatasan jumlah instruksi yang "
         "dieksekusi per siklus, sehingga pendekatan paralel menjadi keharusan "
         "agar pemrosesan tetap berada dalam batas waktu yang praktis.")
    emit("Komputasi paralel pada kartu grafis telah terbukti mempercepat "
         "operasi pengolahan citra. Akasapu, Sailaja, dan Prasad (2021) "
         "membuktikan bahwa pemetaan piksel ke ribuan _thread_ pada GPU CUDA "
         "memangkas waktu eksekusi filter deteksi tepi Sobel jauh di bawah "
         "CPU sekuensial. Akan tetapi, akselerasi tersebut menimbulkan penalti "
         "baru berupa latensi transfer data melalui bus PCIe, sebagaimana "
         "ditemukan oleh Asaduzzaman, Jojigiri, Sabu, dan Tailam (2021) yang "
         "menunjukkan waktu pemindahan memori antara _host_ dan _device_ "
         "menjadi beban latensi utama pada pengolahan citra berbasis GPU. "
         "Pada ranah pemilihan operator, Diana dkk. (2026) "
         "mengonfirmasi efisiensi komputasi deteksi tepi Sobel, sedangkan "
         "Ruijters dan Thévenaz (2012) serta Thévenaz, Blu, dan Unser (2000) "
         "menjadi rujukan klasik untuk interpolasi orde tinggi pada GPU.")
    emit("Meskipun landasan teoretis dan empiris telah tersedia, pengujian "
         "performa pada penelitian terdahulu sebagian besar membandingkan CPU "
         "sekuen langsung dengan GPU untuk satu jenis operasi. Belum terdapat "
         "pengujian bertingkat yang menganalisis skalabilitas CPU pada alokasi "
         "1, 2, 4, dan 8 _thread_ sekaligus untuk dua beban kerja yang berbeda "
         "sifatnya, yakni konvolusi dan _upscaling_, pada tiga tingkat "
         "resolusi citra. Titik impas antara penghematan waktu komputasi "
         "kernel GPU murni terhadap latensi transfer data PCIe pada setiap "
         "resolusi juga belum dipetakan secara kuantitatif, demikian pula "
         "kedekatan numerik hasil interpolasi _Nearest Neighbor_, _Bilinear_, "
         "dan _Bicubic_ terhadap referensi _Lanczos_ dalam lingkungan "
         "komputasi paralel. Pengujian bertingkat pada topik ini layak "
         "dilanjutkan.")
    emit("Penelitian ini melaksanakan pengujian tolok ukur (_benchmark_) yang "
         "terkontrol pada 100 citra dataset DIV2K untuk sembilan konfigurasi "
         "filter konvolusi dan delapan belas konfigurasi _upscaling_. Sisi CPU "
         "memakai kompilasi _Just-In-Time_ Numba dengan empat tingkat alokasi "
         "_thread_, sedangkan sisi GPU memakai _kernel_ CUDA dua dimensi pada "
         "NVIDIA GeForce RTX 3050. Pengujian memetakan percepatan waktu "
         "eksekusi, efisiensi paralel, ambang batas resolusi tempat GPU mulai "
         "mengungguli CPU, serta kedekatan numerik keluaran interpolasi "
         "menggunakan _Mean Squared Error_ (MSE) dan _Peak Signal-to-Noise "
         "Ratio_ (PSNR). Hasil pengujian memberikan acuan empiris dalam "
         "memilih arsitektur komputasi dan metode interpolasi yang tepat "
         "sesuai ukuran resolusi citra yang diproses.")

    h2("1.2 Rumusan Masalah")
    emit("Berdasarkan latar belakang yang telah dipaparkan, rumusan masalah "
         "penelitian dirumuskan sebagai berikut.")
    numlist(1, "Bagaimana skalabilitas waktu eksekusi dan percepatan "
               "pemrosesan filter konvolusi serta _upscaling_ citra pada "
               "alokasi 1, 2, 4, dan 8 _thread_ CPU dibandingkan GPU CUDA?")
    numlist(2, "Pada ambang batas resolusi citra mana komputasi GPU CUDA "
               "mulai mengungguli total waktu pemrosesan CPU multi-_thread_, "
               "setelah memperhitungkan latensi transfer data _host-to-device_ "
               "dan _device-to-host_?")
    numlist(3, "Berapa nilai efisiensi paralel dan fraksi serial eksperimental "
               "metrik Karp-Flatt pada setiap alokasi _thread_ CPU dan GPU?")
    numlist(4, "Berapa nilai MSE dan PSNR hasil _upscaling_ dengan metode "
               "_Nearest Neighbor_, _Bilinear_, dan _Bicubic_ terhadap "
               "referensi interpolasi _Lanczos_ pada setiap konfigurasi "
               "pemroses?")

    h2("1.3 Tujuan Penelitian")
    emit("Tujuan yang ingin dicapai melalui pelaksanaan penelitian ini "
         "adalah sebagai berikut.")
    numlist(1, "Menganalisis skalabilitas waktu eksekusi dan percepatan "
               "operasi filter konvolusi serta _upscaling_ citra pada alokasi "
               "1, 2, 4, dan 8 _thread_ CPU dibandingkan GPU CUDA.")
    numlist(2, "Menentukan ambang batas resolusi citra saat komputasi GPU "
               "CUDA mulai mengungguli total waktu pemrosesan CPU "
               "multi-_thread_ yang mencakup komponen transfer data PCIe.")
    numlist(3, "Mengukur efisiensi paralel dan fraksi serial eksperimental "
               "pada setiap alokasi _thread_ CPU serta GPU untuk resolusi "
               "1080p, 4K, dan 8K.")
    numlist(4, "Mengukur nilai MSE dan PSNR hasil _upscaling_ ketiga metode "
               "interpolasi terhadap referensi _Lanczos_ pada setiap "
               "konfigurasi pemroses.")
    numlist(5, "Membangun aplikasi _dashboard_ berbasis Streamlit untuk "
               "pelaporan performa dan visualisasi hasil pemrosesan citra.")

    h2("1.4 Batasan Masalah")
    emit("Agar penelitian terarah dan fokus pada substansi yang diuji, batasan "
         "masalah ditetapkan sebagai berikut.")
    numlist(1, "Perangkat keras pengujian menggunakan prosesor Intel Core 5 "
               "210H (8 inti fisik: 4 _Performance-core_ dan 4 _Efficient-core_, "
               "12 prosesor logis) dengan memori RAM 16 GB, serta GPU NVIDIA "
               "GeForce RTX 3050 Laptop (6 GB GDDR6, arsitektur Ampere).")
    numlist(2, "Alokasi pengujian CPU dibatasi pada 1, 2, 4, dan 8 _thread_ "
               "Numba pada proses yang afinitasnya dikunci ke 4 "
               "_Performance-core_, sehingga skala pengujian menyatakan "
               "jumlah _thread_, bukan jumlah inti fisik.")
    numlist(3, "Resolusi citra dibatasi pada 720p (1280x720), 1080p "
               "(1920x1080), 4K UHD (3840x2160), dan 8K UHD (7680x4320) dalam "
               "format _grayscale_ satu kanal presisi tunggal (_float32_).")
    numlist(4, "Operasi _upscaling_ mencakup pemetaan 720p ke 1080p, 720p ke "
               "4K, 720p ke 8K, 1080p ke 4K, 1080p ke 8K, dan 4K ke 8K dengan "
               "tiga metode interpolasi, serta evaluasi MSE dan PSNR terhadap "
               "referensi _Lanczos_.")
    numlist(5, "Filter konvolusi dibatasi pada kernel 3x3, yakni Sobel "
               "(gradien horizontal dan vertikal), _Gaussian blur_, dan "
               "_sharpening_ dengan matriks [0, -1, 0; -1, 5, -1; 0, -1, 0].")
    numlist(6, "Lingkungan pengujian menggunakan Python 3.14 dengan Numba JIT "
               "CPU (_parallel=True_ dan _prange_) serta Numba CUDA yang "
               "terhubung ke CUDA Toolkit 13.")
    numlist(7, "Setiap konfigurasi diukur satu kali pada setiap citra dan "
               "dirangkum sebagai median dari 100 citra, dengan alasan desain "
               "yang diuraikan pada Bab III.")
    numlist(8, "Aplikasi _dashboard_ Streamlit berfungsi sebagai alat "
               "demonstrasi hasil, sedangkan data utama pengukuran diambil "
               "dari skrip pengujian yang memakai _kernel_ dan tipe data yang "
               "sama.")

    h2("1.5 Manfaat Penelitian")
    emit("Hasil penelitian ini diharapkan memberikan manfaat sebagai berikut.")
    bullet("Bagi pengembang sistem pengolahan citra, hasil pengujian menjadi "
           "acuan empiris dalam memilih arsitektur komputasi paralel dan "
           "metode interpolasi yang efisien sesuai ukuran resolusi citra "
           "yang diproses.")
    bullet("Bagi program studi Rekayasa Sistem Komputer, penelitian "
           "menyediakan data tolok ukur performa komputasi heterogen serta "
           "materi pendukung pada mata kuliah Komputasi Paralel.")
    bullet("Bagi peneliti lanjutan, metode pengukuran dan klasifikasi kualitas "
           "data pada penelitian ini dapat dijadikan contoh penelusuran "
           "keterbatasan pengukuran pada lingkungan pengujian laptop.")

    page_break()

    # BAB II LANDASAN TEORI
    h1("BAB II")
    h1("LANDASAN TEORI")

    h2("2.1 Pemrosesan Citra Digital Resolusi Tinggi")
    emit("Citra digital tersusun atas matriks piksel yang merepresentasikan "
         "intensitas cahaya pada bidang dua dimensi. Resolusi citra dinyatakan "
         "dalam jumlah piksel pada arah horizontal dan vertikal, sehingga "
         "beban komputasi tumbuh seiring kuadrat panjang sisinya. Citra "
         "1080p (1920x1080) memiliki 2,07 megapiksel, citra 4K (3840x2160) "
         "memiliki 8,29 megapiksel, dan citra 8K (7680x4320) memiliki 33,17 "
         "megapiksel. Penelitian ini memproses citra pada mode _grayscale_ "
         "8-bit yang dikonversi ke matriks presisi tunggal (_float32_) satu "
         "kanal, sehingga citra 8K menempati memori sekitar 133 MB per "
         "salinan masukan maupun keluaran.")
    emit("Pertumbuhan ukuran matriks ini berdampak langsung pada dua operasi "
         "yang diuji. Operasi konvolusi 3x3 melakukan sembilan kali operasi "
         "baca dan kali untuk setiap piksel keluaran, sedangkan operasi "
         "_upscaling_ menambah jumlah piksel keluaran hingga empat kali lipat "
         "dari masukan pada pemetaan 1080p ke 4K, dan enam belas kali lipat "
         "pada pemetaan 1080p ke 8K. Skala pertumbuhan inilah yang membuat "
         "pendekatan paralel menjadi pilihan utama untuk mempertahankan "
         "waktu pemrosesan pada batas yang praktis.")

    h2("2.2 Filter Konvolusi Spasial 3x3")
    emit("Konvolusi diskret dua dimensi menerapkan kernel berukuran "
         "(2a+1) x (2b+1) pada setiap piksel citra masukan _I_, dengan "
         "persamaan:")
    eq("I'(x, y) = Σ Σ I(x + i - a, y + j - b) · K(i, j)", "2.1")
    emit("Nilai _a_ dan _b_ menyatakan setengah ukuran kernel, sehingga "
         "kernel 3x3 memiliki _a_ = _b_ = 1. Bagian tepi citra yang "
         "kekurangan tetangga dilakukan dengan pemberian nilai piksel tepi "
         "ke baris atau kolom yang berada di luar matriks (_edge "
         "replication_), agar dimensi keluaran tetap sama dengan dimensi "
         "masukan. Tiga kernel yang diuji pada penelitian ini memiliki "
         "karakter beban yang berbeda, meskipun ketiganya berukuran 3x3.")
    emit("Filter deteksi tepi Sobel menerapkan dua kernel ortogonal untuk "
         "menghitung komponen gradien horizontal _Gx_ dan vertikal _Gy_, "
         "lalu magnitudo gradien totalnya dihitung dengan:")
    eq("G = √(Gx² + Gy²)", "2.2")
    emit("Filter _Gaussian blur_ menggunakan kernel normalisasi "
         "[1, 2, 1; 2, 4, 2; 1, 2, 1] per enam belas, yang meredam derau "
         "dengan pembobotan menurun terhadap jarak dari piksel pusat. Filter "
         "_sharpening_ menggunakan kernel [0, -1, 0; -1, 5, -1; 0, -1, 0] "
         "yang meningkatkan kontras lokal tepi. Ketiga kernel melakukan "
         "jumlah operasi yang hampir sama, sehingga perbedaan waktu "
         "eksekusi antar filter pada konfigurasi pemroses yang sama "
         "mencerminkan karakteristik akses memori dan pola kalkulasi, bukan "
         "perbedaan banyaknya operasi.")

    h2("2.3 Peningkatan Resolusi Citra")
    emit("Operasi peningkatan resolusi (_upscaling_) memetakan citra "
         "masukan berukuran _H_in × _W_in_ ke citra keluaran berukuran "
         "_H_out × _W_out_. Setiap piksel keluaran dihitung dengan mengambil "
         "sampel koordinat sumber memakai konvensi pusat piksel "
         "(_center-aligned_):")
    eq("src_x = (x + 0,5) · W_in / W_out - 0,5 ; src_y = (y + 0,5) · "
       "H_in / H_out - 0,5", "2.3")
    emit("Konvensi ini dipakai pustaka pemrosesan citra seperti PIL "
         "dan OpenCV, sehingga hasil implementasi dapat divalidasi silang. "
         "Karena pembobotan pada tepi citra tidak selalu berjumlah tepat "
         "satu akibat penjepitan koordinat, keluaran dinormalisasi terhadap "
         "jumlah seluruh bobot yang dipakai.")
    emit("Metode _Nearest Neighbor_ mengambil nilai piksel sumber terdekat "
         "tanpa pembobotan, sehingga harganya paling murah secara komputasi. "
         "Metode _Bilinear_ melakukan pembobotan linear atas empat piksel "
         "tetangga, sedangkan metode _Bicubic_ melakukan pembobotan atas "
         "enam belas piksel tetangga dengan fungsi basis Catmull-Rom. "
         "Kualitas keluaran diukur terhadap hasil interpolasi _Lanczos_ "
         "sebagai referensi memakai MSE dan PSNR, yang pada bagian ini "
         "mengukur tingkat kemiripan numerik terhadap keluaran referensi, "
         "bukan kualitas visual mutlak.")

    h2("2.4 Komputasi Paralel pada CPU")
    emit("Komputasi paralel pada CPU membagi beban kerja ke beberapa "
         "_thread_ yang dijalankan secara serempak oleh sistem operasi pada "
         "inti-inti prosesor yang tersedia. Implementasi pada penelitian "
         "ini memakai Numba, kompilator _Just-In-Time_ yang "
         "menerjemahkan fungsi Python bertipe numerik ke kode mesin LLVM "
         "secara langsung (Lam, Pitrou, dan Seibert, 2015). Penanda "
         "_parallel=True_ bersama dengan konstruksi _prange_ mempartisi "
         "iterasi ke _thread pool_ yang bebas dari kunci _Global "
         "Interpreter Lock_ Python, sehingga peningkatan jumlah _thread_ "
         "benar-benar menambah jalur eksekusi paralel.")
    emit("Skalabilitas pendekatan ini dibatasi oleh tiga faktor. Bagian "
         "program yang murni sekuensial membatasi percepatan total menurut "
         "Hukum Amdahl. Biaya sinkronisasi antar-_thread_ tumbuh seiring "
         "jumlah _thread_, terutama pada beban kerja yang eksekusinya "
         "sangat singkat. Faktor ketiga bersifat perangkat keras: _thread_ "
         "yang berbagi inti fisik melalui _Simultaneous Multithreading_ "
         "menghasilkan percepatan yang lebih kecil daripada _thread_ pada "
         "inti terpisah. Ketiga faktor ini saling bertumpuk dan tidak dapat "
         "dipisahkan dengan pengukuran waktu saja, sehingga penelitian ini "
         "melengkapi pengukuran dengan verifikasi topologi prosesor pada "
         "Bab IV.")

    h2("2.5 Arsitektur Prosesor Hybrid dan Simultaneous Multithreading")
    emit("Prosesor Intel generasi Alder Lake ke atas memadukan dua kelas "
         "inti dalam satu keping. _Performance-core_ (P-core) menjalankan "
         "dua _thread_ per inti melalui _Simultaneous Multithreading_ "
         "(SMT), sedangkan _Efficient-core_ (E-core) menjalankan satu "
         "_thread_ per inti dengan daya yang lebih hemat. Sistem operasi "
         "memberi nomor pada setiap _thread_ perangkat keras sebagai "
         "prosesor logis (_logical processor_), dan penomoran ini tidak "
         "pernah sama dengan penomoran inti fisik. Sebagai konsekuensinya, "
         "suatu topeng afinitas (_affinity mask_) yang menetapkan delapan "
         "prosesor logis dapat bermakna delapan inti fisik, atau empat inti "
         "fisik dengan SMT, atau campuran kedua kelas inti, tergantung "
         "pemetaan yang diberikan sistem operasi. Klaim tentang perilaku "
         "inti apa pun dari suatu topeng afinitas karena itu wajib "
         "diverifikasi terhadap pemetaan asli, bukan didasarkan pada "
         "asumsi urutan penomoran.")
    emit("_Simultaneous Multithreading_ meningkatkan pemanfaatan inti "
         "dengan menjalankan dua _thread_ pada unit eksekusi yang sama "
         "secara bergantian. Manfaatnya bergantung pada jenis beban: "
         "_thread_ yang menunggu memori dapat diselingi _thread_ yang "
         "sedang menghitung, sehingga sebagian waktu tungga dipakai untuk "
         "pekerjaan. Pada beban kerja yang selalu menghitung tanpa "
         "menunggu data, kedua _thread_ justru berebut unit eksekusi dan "
         "percepatan totalnya turun jauh di bawah faktor dua. Karakter "
         "inilah yang membedakan penambahan _thread_ dari penambahan inti "
         "fisik.")

    h2("2.6 Arsitektur GPU CUDA")
    emit("Kartu grafis NVIDIA GeForce RTX 3050 Laptop memiliki 20 "
         "_streaming multiprocessor_ (SM) yang masing-masing menampung 128 "
         "_CUDA core_, sehingga total terdapat 2.560 _CUDA core_ dengan "
         "arsitektur Ampere dan kemampuan komputasi 8.6. Eksekusi "
         "mengikuti model _Single Instruction, Multiple Threads_ (SIMT): "
         "satu instruksi diterapkan pada banyak _thread_ yang dikelompokkan "
         "dalam blok berukuran 16x16 _thread_ pada penelitian ini. "
         "Sekelompok blok membentuk _grid_ yang menutupi seluruh dimensi "
         "citra keluaran, dan setiap _thread_ menghitung satu piksel "
         "keluaran.")
    emit("Pemindahan data antara memori sistem dan memori global GPU "
         "menempuh bus PCIe. Memori _pageable_ biasa dipindai dengan "
         "salinan perantara pada memori yang disematkan (_pinned memory_), "
         "sedangkan memori _pinned_ dapat diakses oleh perangkat langsung "
         "lewat _direct memory access_. Pemakaian memori _pinned_ "
         "meningkatkan laju transfer efektif pada beban besar, namun "
         "tidak menghapus latensi bus itu sendiri. Akibatnya, waktu total "
         "pemrosesan GPU selalu mencakup tiga komponen, yakni transfer "
         "_host-to-device_, eksekusi _kernel_, dan transfer "
         "_device-to-host_, yang masing-masing diukur terpisah pada "
         "penelitian ini.")

    h2("2.7 Metrik Kinerja Komputasi Paralel")
    emit("Percepatan (_speedup_) menyatakan rasio waktu eksekusi "
         "sekuensial terhadap waktu eksekusi paralel:")
    eq("S(p) = T₁ / T_p", "2.4")
    emit("Efisiensi paralel membandingkan percepatan terhadap jumlah unit "
         "pemroses yang dipakai, _E(p) = S(p)/p_, dengan nilai 1,0 "
         "sebagai pencapaian ideal. Hukum Amdahl memodelkan batas atas "
         "percepatan akibat bagian program yang tetap sekuensial:")
    eq("S(p) = 1 / ((1 - P) + P/p)", "2.6")
    emit("dengan _P_ sebagai proporsi bagian paralel dan _p_ sebagai "
         "jumlah unit pemroses. Nilai _P_ dapat diestimasi dengan "
         "penyesuaian kurva (_curve fitting_) terhadap hasil pengukuran. "
         "Model ini disempurnakan oleh metrik Karp-Flatt yang "
         "menghitung fraksi serial eksperimental:")
    eq("e = (1/S - 1/p) / (1 - 1/p)", "2.7")
    emit("Nilai _e_ yang konstan terhadap _p_ menandakan fraksi serial "
         "yang stabil, sedangkan nilai _e_ yang membesar menandakan "
         "_overhead_ yang tumbuh seiring jumlah unit pemroses. Pada "
         "penelitian ini kedua metrik dipakai untuk membedakan penurunan "
         "efisiensi yang berasal dari struktur algoritma dengan yang "
         "berasal dari _overhead_ _thread_.")
    emit("Kedekatan numerik keluaran interpolasi diukur dengan _Mean "
         "Squared Error_ (MSE) dan _Peak Signal-to-Noise Ratio_ (PSNR):")
    eq("MSE = (1/N) Σ (x_i - r_i)²  ;  PSNR = 20 · log₁₀(255 / √MSE)",
       "2.8")
    emit("dengan _x_i_ sebagai piksel keluaran metode yang diuji, _r_i_ "
         "sebagai piksel referensi _Lanczos_, dan _N_ sebagai banyaknya "
         "piksel. Referensi dipilih karena _Lanczos_ merupakan filter "
         "interpolasi orde tinggi yang dianggap mendekati hasil ideal, "
         "sehingga nilai PSNR yang dilaporkan menyatakan jarak numerik "
         "metode yang diuji terhadap hasil referensi tersebut.")

    h2("2.8 Penelitian Terdahulu")
    emit("Penelitian yang menjadi landasan penelitian ini dirangkum pada "
         "Tabel 2.1.")
    table(
        header=["Peneliti (Tahun)", "Fokus", "Temuan Utama"],
        rows=[
            ["Akasapu dkk. (2021)", "Filter Sobel pada CUDA",
             "Pemetaan piksel ke ribuan thread memangkas waktu eksekusi "
             "jauh di bawah CPU sekuensial"],
            ["Asaduzzaman dkk. (2021)", "Waktu transfer memori GPU",
             "Pemindahan memori host-device menjadi beban latensi utama "
             "pada pengolahan citra berbasis GPU"],
            ["Diana dkk. (2026)", "Komparasi deteksi tepi",
             "Deteksi tepi Sobel memiliki efisiensi komputasi spasial "
             "yang terbaik dibanding Prewitt dan Canny"],
            ["Ruijters dan Thévenaz (2012)", "Interpolasi B-spline GPU",
             "Prafilter interpolasi cubic B-spline pada GPU memangkas "
             "waktu komputasi orde tinggi"],
        ],
        widths=[4.2, 4.0, 6.2],
        caption="Tabel 2.1 Ringkasan Penelitian Terdahulu")
    emit("Penelitian-penelitian tersebut mengonfirmasi dua sifat "
         "komputasi heterogen yang menjadi fokus pengujian pada penelitian "
         "ini: GPU unggul pada beban komputasi yang dapat didistribusikan "
         "ke banyak _thread_, dan kinerja tersebut dibatasi oleh jalur "
         "transfer data. Celah yang belum dijawab adalah pemetaan "
         "skalabilitas CPU pada alokasi _thread_ bertingkat untuk kedua "
         "jenis beban kerja, serta titik resolusi tempat keunggulan GPU "
         "mulai terbayar oleh biaya transfer yang menyertainya.")

    page_break()



    # BAB III METODOLOGI PENELITIAN
    h1("BAB III")
    h1("METODOLOGI PENELITIAN")

    h2("3.1 Desain Penelitian")
    emit("Penelitian ini menggunakan metode eksperimental kuantitatif berbasis "
         "pengujian tolok ukur (_benchmarking_) yang terkontrol. Setiap "
         "konfigurasi pemroses diuji pada kumpulan citra yang sama dengan "
         "urutan pengukuran yang disusun secara bergantian, sehingga "
         "perubahan kondisi sistem sepanjang pengujian memengaruhi seluruh "
         "konfigurasi secara setara. Tahapan penelitian disusun sebagai "
         "berikut.")
    numlist(1, "Tahap studi literatur mengkaji arsitektur komputasi paralel "
               "heterogen, kernel CUDA, dan operator spasial pengolahan "
               "citra digital.")
    numlist(2, "Tahap perancangan lingkungan dan kernel komputasi membangun "
               "fungsi konvolusi dan interpolasi pada Numba JIT CPU serta "
               "_kernel_ CUDA 2D berbasis _grid_ dan blok.")
    numlist(3, "Tahap persiapan dataset menyiapkan 100 citra DIV2K pada "
               "empat tingkat resolusi uji.")
    numlist(4, "Tahap pengujian empiris menjalankan pengukuran pada perangkat "
               "keras uji dengan prosedur pada bagian 3.5 dan 3.6.")
    numlist(5, "Tahap analisis menghitung percepatan, efisiensi paralel, "
               "fraksi serial eksperimental, serta titik impas resolusi GPU.")
    numlist(6, "Tahap pengembangan _dashboard_ mengintegrasikan hasil "
               "pengukuran ke dalam aplikasi Streamlit untuk pelaporan dan "
               "visualisasi.")

    h2("3.2 Perangkat Keras Pengujian")
    emit("Pengujian dilakukan pada laptop dengan perangkat keras pada "
         "Tabel 3.1.")
    table(
        header=["Komponen", "Spesifikasi"],
        rows=[
            ["Prosesor", "Intel Core 5 210H (Alder Lake), 8 inti fisik, "
             "12 prosesor logis, RAM 16 GB"],
            ["GPU", "NVIDIA GeForce RTX 3050 Laptop, 6 GB GDDR6, 20 SM, "
             "2.560 CUDA core, arsitektur Ampere (compute capability 8.6)"],
            ["Sistem operasi", "Windows 11"],
        ],
        widths=[4.0, 10.0],
        caption="Tabel 3.1 Spesifikasi Perangkat Keras Pengujian")
    emit("Prosesor pengujian memiliki arsitektur hybrid yang memadukan dua "
         "kelas inti. Jumlah inti fisik dan prosesor logis yang dilaporkan "
         "oleh sistem operasi tidak menjelaskan pemetaan nomor prosesor "
         "logis ke inti fisik, padahal pemetaan inilah yang menentukan "
         "makna topeng afinitas pada pengukuran. Pemetaan tersebut karena "
         "itu diverifikasi sebelum pengukuran dengan dua cara, yakni "
         "pembacaan struktur topologi dari sistem operasi dan _probe_ "
         "afinitas pada beban kerja nyata.")
    emit("Pembacaan topologi dilakukan dengan fungsi "
         "_GetLogicalProcessorInformationEx_ pada _RelationProcessorCore_, "
         "yang memberikan daftar inti fisik beserta prosesor logis yang "
         "dimilikinya serta kelas kinerja inti. _Probe_ "
         "afinitas menjalankan beban kerja aritmetika dengan sejumlah "
         "_thread_ pada topeng afinitas yang bervariasi, memakai "
         "pemanggilan _SetProcessAffinityMask_ yang hasilnya dibaca kembali "
         "untuk memastikan topeng benar-benar diterapkan. Hasil verifikasi "
         "disajikan pada Tabel 3.2.")
    table(
        header=["Inti Fisik", "Kelas Kinerja", "Prosesor Logis", "SMT"],
        rows=[
            ["P-core 1", "_Performance_", "0 dan 1", "Ya"],
            ["P-core 2", "_Performance_", "2 dan 3", "Ya"],
            ["P-core 3", "_Performance_", "4 dan 5", "Ya"],
            ["P-core 4", "_Performance_", "6 dan 7", "Ya"],
            ["E-core 1", "_Efficient_", "8", "Tidak"],
            ["E-core 2", "_Efficient_", "9", "Tidak"],
            ["E-core 3", "_Efficient_", "10", "Tidak"],
            ["E-core 4", "_Efficient_", "11", "Tidak"],
        ],
        widths=[3.4, 3.6, 5.0, 2.0],
        caption="Tabel 3.2 Topologi Prosesor Intel Core 5 210H Hasil "
                "Verifikasi")
    emit("Hasil verifikasi menunjukkan bahwa empat P-core menempati "
         "prosesor logis 0 hingga 7 dengan dua prosesor logis per inti, "
         "sedangkan empat E-core menempati prosesor logis 8 hingga 11 "
         "dengan satu prosesor logis per inti. _Probe_ afinitas memberikan "
         "hasil yang konsisten: _thread_ tunggal pada prosesor logis 0 "
         "hingga 7 menyelesaikan beban uji kira-kira 1,76 kali lebih cepat "
         "daripada pada prosesor logis 8 hingga 11, dan dua _thread_ pada "
         "sepasang SMT hanya memberi percepatan kira-kira 1,6 kali "
         "dibandingkan _thread_ tunggal.")
    emit("Makna temuan ini bagi pengukuran adalah bahwa topeng afinitas "
         "0xFF menyatakan pemilihan delapan prosesor logis 0 hingga 7, "
         "yang sesungguhnya adalah empat P-core dengan SMT. Seluruh "
         "konfigurasi pengujian CPU pada penelitian ini berjalan di atas "
         "keempat P-core tersebut, sedangkan E-core tidak diikutsertakan "
         "dan justru dialokasikan untuk aplikasi latar. Skala alokasi "
         "pengujian oleh karena itu menyatakan jumlah _thread_ Numba, "
         "bukan jumlah inti fisik. Akibatnya 4 _thread_ berarti satu "
         "_thread_ pada tiap P-core, sedangkan 8 _thread_ berarti dua "
         "_thread_ yang berbagi setiap P-core.")

    h2("3.3 Perangkat Lunak Pengujian")
    emit("Pengujian memakai Python 3.14 dengan pustaka Numba untuk "
         "kompilasi _Just-In-Time_ pada sisi CPU dan Numba CUDA untuk "
         "sisi GPU, yang terhubung ke CUDA Toolkit 13. Fungsi CPU "
         "ditandai _parallel=True_ dengan konstruksi _prange_ yang "
         "mempartisi iterasi baris citra ke _thread pool_. _Kernel_ GPU "
         "dipanggil dengan konfigurasi blok 16x16 _thread_ dan _grid_ "
         "yang menutupi dimensi citra keluaran. Aplikasi _dashboard_ "
         "dibangun dengan Streamlit. Pengukuran dibungkus oleh skrip "
         "_batch_ yang menetapkan topeng afinitas 0xFF, prioritas proses "
         "_high_, dan nilai _NUMBA_NUM_THREADS_ = 8 sejak proses dimulai, "
         "sehingga jumlah _thread_ pada _thread pool_ sesuai dengan "
         "jumlah prosesor logis yang tersedia.")

    h2("3.4 Dataset Citra")
    emit("Dataset pengujian adalah DIV2K _validation_ high-resolution "
         "yang memuat 100 citra foto dengan resolusi yang bervariasi "
         "(Agustsson dan Timofte, 2017). Karena pengujian memerlukan "
         "citra pada resolusi yang tepat, setiap citra disusun ulang ke "
         "resolusi uji memakai fungsi _resize_ Lanczos pada pustaka PIL. "
         "Operasi penyusunan ulang ini bukan objek pengujian, melainkan "
         "hanya cara menyiapkan masukan yang seragam. Setiap citra "
         "dikonversi ke mode _grayscale_ 8-bit, lalu diproses sebagai "
         "matriks _float32_ satu kanal.")
    emit("Pada pengujian filter konvolusi, citra disusun pada resolusi "
         "1080p, 4K, dan 8K. Pada pengujian _upscaling_, citra disusun "
         "pada resolusi sumber 720p, 1080p, dan 4K, lalu dipetakan ke "
         "resolusi target yang lebih besar, menghasilkan enam "
         "kombinasi pemetaan yang diuji dengan tiga metode interpolasi, "
         "seluruhnya delapan belas konfigurasi. "
         "Referensi kualitas untuk tiap kombinasi adalah hasil _resize_ "
         "Lanczos dari citra sumber ke resolusi target yang sama, "
         "sehingga perbandingan antar metode terhadap referensi terjadi pada "
         "masukan yang identik.")

    h2("3.5 Prosedur Pengukuran pada CPU")
    emit("Pengukuran CPU dilakukan dengan empat tingkat jumlah _thread_, "
         "yakni 1, 2, 4, dan 8 _thread_, pada proses yang afinitasnya "
         "tetap di topeng 0xFF. Sebelum pengukuran tiap citra, "
         "dilakukan satu kali eksekusi penyulaan (_warm-up_) pada "
         "seluruh konfigurasi agar waktu kompilasi JIT tidak terhitung "
         "dalam pengukuran dan array keluaran telah dialokasikan. "
         "Pengukuran lalu diulang sebanyak nilai _reps_ ditambah satu "
         "kali, dan pengulangan pertama dibuang.")
    emit("Urutan pengukuran disusun secara bergantian (_round-robin_): "
         "pada setiap pengulangan, keempat konfigurasi dijalankan "
         "berurutan sebelum pengulangan berikutnya. Tujuan susunan ini "
         "adalah membuat perubahan kondisi sistem yang menetap sepanjang "
         "satu pengulangan, seperti pergeseran frekuensi akibat suhu, "
         "menimpa seluruh konfigurasi secara setara. Waktu eksekusi "
         "diukur dengan _time.perf_counter_ pada level milidetik, dan "
         "setiap citra menghasilkan satu baris data per konfigurasi. "
         "Dengan _reps_ = 1, setiap baris memuat waktu satu citra dan "
         "percepatan citra tersebut, sedangkan agregasi lintas citra "
         "dilakukan pada tahap analisis.")

    h2("3.6 Prosedur Pengukuran pada GPU")
    emit("Pengukuran GPU memakai _device array_ pada memori global "
         "kartu grafis dan _pinned array_ pada memori sistem untuk "
         "membandingkan dua jenis memori _host_. Setiap citra diukur "
         "dalam tiga tahap yang dicatat terpisah, yakni transfer "
         "_host-to-device_ pada memori _pageable_ maupun _pinned_, "
         "eksekusi _kernel_, serta transfer _device-to-host_ pada kedua "
         "jenis memori. Setiap tahap diakhiri dengan _cuda.synchronize_ "
         "agar durasi yang terukur benar-benar menunggu penyelesaian "
         "perangkat. Parameter pengukuran dirangkum pada Tabel 3.3.")
    table(
        header=["Parameter", "Nilai"],
        rows=[
            ["Ukuran blok (_thread per block_)", "16 x 16 = 256 _thread_"],
            ["Ukuran _grid_", " ⌈tinggi/16⌉ x ⌈lebar/16⌉ blok"],
            ["Jumlah _thread_ per piksel keluaran", "1"],
            ["Memori _host_", "_pageable_ dan _pinned_"],
            ["Pengulangan per citra", "_reps_ = 1, pengulangan pertama dibuang"],
        ],
        widths=[6.0, 8.0],
        caption="Tabel 3.3 Parameter Pengukuran GPU")
    emit("Total waktu pemrosesan GPU dirumuskan sebagai:")
    eq("T_total = T_H2D + T_kernel + T_D2H", "3.1")
    emit("dengan _T_H2D_ sebagai waktu transfer memori _host-to-device_, "
         "_T_kernel_ sebagai durasi eksekusi _kernel_ pada "
         "_streaming multiprocessor_, dan _T_D2H_ sebagai waktu transfer "
         "hasil kembali ke memori _host_. Nilai yang dipakai untuk "
         "perbandingan dengan CPU adalah total pada memori _pinned_, "
         "karena nilai inilah yang sesungguhnya diperoleh pengguna pada "
         "implementasi yang sudah dioptimalkan.")

    h2("3.7 Strategi Statistik Pengukuran")
    emit("Setiap konfigurasi diukur satu kali pada setiap citra "
         "(_reps_ = 1), dengan 100 citra sebagai sampel. Pilihan ini "
         "membawa tiga konsekuensi yang dinyatakan secara terbuka. "
         "Deviasi standar yang dihitung dari 100 waktu antar "
         "citra menyatakan variasi beban antar citra, bukan "
         "ketidakpastian pengukuran pada satu citra, sehingga nilai "
         "nol pada _reps_ = 1 tidak ditemui karena perhitungan tetap "
         "memakai 100 data antar citra. Median dipilih sebagai "
         "statistik peringkasan karena distribusi waktu antar citra "
         "mencakup citra dengan detail yang sangat berbeda, sehingga "
         "rerata tergeser oleh citra yang ekstrem. Percepatan "
         "dihitung pada setiap citra, lalu diambil mediannya pada tahap "
         "agregasi, sehingga setiap nilai percepatan di laporan "
         "merupakan median dari 100 nilai, bukan rasio antar dua median "
         "waktu.")
    emit("Strategi ini menetralkan perubahan kondisi sistem yang menetap "
         "sepanjang pengukuran satu citra, sebab seluruh konfigurasi "
         "diukur dalam jendela waktu yang berurutan pada citra yang "
         "sama. Strategi ini tidak menghilangkan gangguan transien "
         "yang mengenai satu jendela pengukuran saja, karena pengukuran "
         "setiap konfigurasi tidak dilakukan bersamaan. Oleh sebab itu, "
         "kualitas data setiap _run_ diklasifikasi dengan rasio "
         "_median/min_ dan arah penyimpangannya. _Spike_ ke atas "
         "menandakan proses lain merebut perhatian prosesor, fase cepat "
         "yang membesar dari sisi minimum menandakan pergeseran keadaan "
         "daya, dan keseluruhan _run_ yang makin melambat menandakan "
         "drift termal. Skenario yang tergolong tercemar diulang setelah "
         "perangkat diistirahatkan, dan hanya data bersih yang "
         "dilaporkan pada laporan ini.")

    h2("3.8 Validasi Ekivalensi dan Kualitas Keluaran")
    emit("Ekivalensi keluaran CPU dan GPU diverifikasi dengan "
         "membandingkan hasil _kernel_ GPU terhadap keluaran CPU 1 "
         "_thread_ pada citra yang sama. Selisih mutlak terbesar "
         "(_max_diff_) dihitung untuk setiap citra konvolusi, dan nilai "
         "nol pada seluruh baris berarti kedua jalur eksekusi "
         "menghasilkan keluaran yang numerik sama. Pada _upscaling_, "
         "kualitas diukur dengan MSE dan PSNR terhadap referensi "
         "Lanczos. MSE dan PSNR pada laporan ini mengukur kedekatan "
         "numerik terhadap referensi tersebut, bukan kualitas visual "
         "mutlak.")

    h2("3.9 Aplikasi Dashboard Streamlit")
    emit("Hasil pengukuran yang tersimpan dalam format CSV dimuat ke "
         "aplikasi Streamlit yang menampilkan tabel agregat, grafik "
         "waktu eksekusi dan percepatan, serta metrik Karp-Flatt per "
         "konfigurasi. Aplikasi berperan sebagai alat pelaporan yang "
         "menyatukan data dari seluruh skenario pengujian, sedangkan "
         "angka pada laporan ini bersumber langsung dari berkas CSV "
         "pengukuran dengan _kernel_ dan tipe data yang sama, sehingga "
         "tidak terdapat perbedaan implementasi antara data yang "
         "ditampilkan dasbor dengan data yang dilaporkan.")

    page_break()

    # BAB IV HASIL DAN PEMBAHASAN
    h1("BAB IV")
    h1("HASIL DAN PEMBAHASAN")

    h2("4.1 Hasil Verifikasi Topologi Prosesor")
    emit("Pengukuran tolok ukur pada Bab III menetapkan bahwa seluruh "
         "konfigurasi CPU dijalankan pada empat P-core dengan SMT. Sifat "
         "ini memengaruhi pembacaan seluruh hasil CPU pada bab ini, "
         "sebab konfigurasi 8 _thread_ adalah konfigurasi yang "
         "mendudukkan dua _thread_ pada tiap P-core. Untuk mengetahui "
         "seberapa besar tambahan _thread_ benar-benar memberi "
         "percepatan, dijalankan _probe_ afinitas dengan beban kerja "
         "rantai operasi aritmetika pada presisi ganda. Setiap "
         "pengukuran _probe_ dilakukan tiga kali dengan jeda tiga "
         "detik, dan topeng afinitas dibaca kembali untuk memastikan "
         "pemetaan benar-benar diterapkan. Ringkasan hasil disajikan "
         "pada Tabel 4.1.")
    table(
        header=["Topeng Afinitas", "Kelas Inti", "Waktu (ms)"],
        rows=[
            ["1 _thread_ (LP 0)", "P-core", "1.220"],
            ["1 _thread_ (LP 8)", "E-core", "2.150"],
            ["2 _thread_ (LP 0 dan 1, 1 inti)", "P-core SMT", "766"],
            ["2 _thread_ (LP 0 dan 2, 2 inti)", "P-core terpisah", "653"],
            ["2 _thread_ (LP 4 dan 5, 1 inti)", "P-core SMT", "727"],
            ["2 _thread_ (LP 4 dan 6, 2 inti)", "P-core terpisah", "617"],
            ["4 _thread_ (LP 0 hingga 3, 2 inti)", "P-core", "383"],
            ["4 _thread_ (LP 4 hingga 7, 2 inti)", "P-core", "370"],
            ["4 _thread_ (LP 0, 2, 4, 6)", "P-core terpisah", "329"],
            ["4 _thread_ (LP 8 hingga 11)", "E-core", "485"],
        ],
        widths=[6.6, 4.4, 3.0],
        caption="Tabel 4.1 Ringkasan Hasil Probe Afinitas pada Beban "
                "Kerja Rantai Aritmetika")
    emit("Hasil _probe_ memberikan tiga temuan. Satu _thread_ "
         "pada E-core membutuhkan waktu kira-kira 1,76 kali _thread_ "
         "pada P-core, sehingga kelas inti tidak setara. Dua "
         "_thread_ yang berbagi satu P-core hanya menyelesaikan beban "
         "kira-kira 1,6 kali lebih cepat daripada satu _thread_, jauh "
         "di bawah faktor dua yang diberikan oleh dua inti terpisah. "
         "Empat _thread_ pada empat P-core terpisah (329 ms) "
         "lebih cepat daripada empat _thread_ pada dua P-core (383 ms "
         "dan 370 ms) maupun pada empat E-core (485 ms). Temuan ini "
         "menjelaskan mengapa penambahan _thread_ dari 4 ke 8 pada "
         "topeng afinitas 0xFF tidak menghasilkan percepatan, karena "
         "_thread_ ke-5 hingga ke-8 harus berbagi unit eksekusi yang "
         "sama dengan empat _thread_ pertama.")

    h2("4.2 Hasil Pengukuran Filter Konvolusi 3x3")
    emit("Pengukuran filter konvolusi dilakukan pada tiga filter dan "
         "tiga resolusi, dengan setiap angka waktu adalah median dari "
         "100 citra dan setiap angka percepatan adalah median dari 100 "
         "nilai per citra. Hasil disajikan pada Tabel 4.2.")
    table(
        header=["Filter", "Resolusi", "1 thread", "2 thread",
                "4 thread", "8 thread", "GPU kernel", "GPU total",
                "Speedup GPU total"],
        rows=[
            ["Sharpen", "1080p", "13,7", "7,6", "5,0", "5,4", "4,2",
             "15,6", "0,89x"],
            ["Sharpen", "4K", "59,8", "32,2", "23,6", "24,2", "7,0",
             "17,9", "3,14x"],
            ["Sharpen", "8K", "270,1", "132,1", "89,6", "91,4", "14,8",
             "57,2", "4,78x"],
            ["Gaussian", "1080p", "22,3", "17,1", "12,6", "9,6", "5,8",
             "19,6", "1,11x"],
            ["Gaussian", "4K", "87,8", "49,6", "32,7", "31,4", "8,4",
             "38,0", "2,37x"],
            ["Gaussian", "8K", "408,9", "198,7", "151,4", "118,6",
             "15,7", "58,3", "7,03x"],
            ["Sobel", "1080p", "4,9", "3,3", "3,1", "4,2", "4,1",
             "15,7", "0,31x"],
            ["Sobel", "4K", "18,4", "11,7", "12,1", "14,3", "8,4",
             "19,3", "0,96x"],
            ["Sobel", "8K", "73,8", "35,5", "40,1", "41,5", "16,6",
             "59,0", "1,25x"],
        ],
        widths=[2.0, 1.5, 1.4, 1.4, 1.4, 1.4, 1.5, 1.4, 1.8],
        caption="Tabel 4.2 Hasil Pengukuran Filter Konvolusi 3x3 "
                "(Median 100 Citra, Milidetik)")
    emit("Skalabilitas CPU berbeda antar filter. Pada filter "
         "_Gaussian_, percepatan 8 _thread_ terhadap 1 _thread_ "
         "tumbuh paling konsisten: 2,34x pada resolusi "
         "1080p, 2,75x pada 4K, dan 3,44x pada 8K.")
    emit("Untuk resolusi yang "
         "sama, filter Sharpen mencapai 2,54x, 2,45x, dan 2,95x, "
         "sedangkan filter Sobel hanya mencapai 1,17x, 1,33x, "
         "dan 1,76x.")
    emit("Pada filter Sharpen, waktu 8 _thread_ berhenti "
         "menurun dan sedikit membesar terhadap 4 _thread_ pada ketiga "
         "resolusi. "
         "Hal ini menunjukkan bahwa penambahan _thread_ tidak selalu "
         "mempercepat, dan titik optimumnya bergeser menurut beban "
         "kerja tiap filter.")
    emit("Pada sisi GPU, waktu _kernel_ berada pada kisaran 4,1 hingga "
         "16,6 milidetik untuk seluruh filter dan resolusi, dan tidak "
         "terlihat tumbuh sebanding dengan jumlah piksel. Waktu total "
         "pemrosesan GPU, yang mencakup transfer data masukan dan "
         "keluaran, berada pada kisaran 15,6 hingga 59,0 milidetik. "
         "Perbandingan kedua nilai ini menunjukkan bahwa transfer data "
         "mendominasi waktu total pada resolusi kecil, dan baru "
         "tertumpuk oleh waktu _kernel_ pada resolusi besar.")
    emit("Percepatan GPU total terhadap CPU 1 _thread_ bertumbuh "
         "menurut resolusi. Pada resolusi 1080p, percepatan total "
         "berada di bawah 1,0 untuk filter Sharpen dan Sobel, "
         "berarti GPU justru lebih lambat daripada CPU 1 _thread_. "
         "Angka ini naik pada 4K ke kisaran 0,96x hingga 3,14x, lalu "
         "melampaui 1,0 untuk ketiga filter pada 8K dengan puncak "
         "7,03x pada filter Gaussian. Ekivalensi numerik antara kedua "
         "jalur eksekusi terverifikasi dengan _max_diff_ = 0 pada "
         "seluruh baris konvolusi.")

    h2("4.3 Hasil Pengukuran Peningkatan Resolusi Citra")
    emit("Pengukuran _upscaling_ dilakukan pada tiga metode "
         "interpolasi pada enam kombinasi pemetaan resolusi. "
         "Tabel 4.3 menyajikan waktu CPU 1 _thread_, CPU 8 _thread_, "
         "waktu _kernel_ GPU, waktu total GPU, percepatan total GPU, "
         "serta PSNR keluaran GPU terhadap referensi Lanczos.")
    table(
        header=["Metode", "Pemetaan", "1 thread", "8 thread",
                "GPU kernel", "GPU total", "Speedup GPU total",
                "PSNR (dB)"],
        rows=[
            ["Bicubic", "720p ke 1080p", "35,6", "12,2", "24,0", "32,7",
             "1,09x", "44,85"],
            ["Bicubic", "720p ke 4K", "148,8", "39,4", "35,5", "41,8",
             "3,40x", "45,04"],
            ["Bicubic", "720p ke 8K", "605,5", "144,3", "99,9", "121,3",
             "4,97x", "44,91"],
            ["Bicubic", "1080p ke 4K", "147,4", "38,2", "37,3", "44,9",
             "3,11x", "46,37"],
            ["Bicubic", "1080p ke 8K", "666,8", "145,5", "100,3",
             "122,4", "5,18x", "46,66"],
            ["Bicubic", "4K ke 8K", "699,9", "140,1", "100,0", "126,4",
             "5,53x", "53,47"],
            ["Bilinear", "720p ke 1080p", "9,8", "3,9", "5,4", "13,3",
             "0,74x", "37,92"],
            ["Bilinear", "720p ke 4K", "62,6", "24,7", "16,7", "39,9",
             "1,60x", "38,36"],
            ["Bilinear", "720p ke 8K", "476,3", "148,1", "38,3", "60,2",
             "7,77x", "38,05"],
            ["Bilinear", "1080p ke 4K", "180,0", "53,6", "25,3", "78,0",
             "2,45x", "39,26"],
            ["Bilinear", "1080p ke 8K", "771,5", "227,1", "38,8", "61,7",
             "10,89x", "39,62"],
            ["Bilinear", "4K ke 8K", "273,7", "80,0", "34,7", "60,9",
             "4,43x", "46,61"],
            ["Nearest", "720p ke 1080p", "7,3", "4,5", "3,0", "19,0",
             "0,41x", "30,70"],
            ["Nearest", "720p ke 4K", "28,7", "19,3", "5,0", "28,5",
             "0,98x", "32,17"],
            ["Nearest", "720p ke 8K", "73,7", "36,9", "9,5", "30,7",
             "2,41x", "31,75"],
            ["Nearest", "1080p ke 4K", "25,3", "12,9", "4,1", "30,8",
             "0,83x", "34,13"],
            ["Nearest", "1080p ke 8K", "84,7", "41,0", "9,5", "31,6",
             "2,53x", "33,10"],
            ["Nearest", "4K ke 8K", "129,9", "56,3", "9,8", "36,0",
             "3,61x", "38,93"],
        ],
        widths=[1.6, 2.0, 1.3, 1.3, 1.4, 1.3, 1.7, 1.2],
        caption="Tabel 4.3 Hasil Pengukuran Upscaling (Median 100 "
                "Citra, Milidetik)")
    emit("Pola percepatan GPU pada _upscaling_ mengikuti ukuran citra "
         "keluaran, bukan ukuran citra masukan. Pada target 1080p, "
         "ketiga metode mencapai percepatan total di bawah 1,1x.")
    emit("Dua di antaranya berada di bawah 1,0, sehingga GPU belum "
         "mampu mengungguli CPU 1 _thread_.")
    emit("Naik ke target 4K "
         "membawa percepatan ke kisaran 0,83x hingga 3,40x, dengan "
         "metode _nearest neighbor_ yang kalah pada pemetaan dari "
         "1080p. Seluruh metode baru menghasilkan percepatan di atas "
         "2,4x pada target 8K, dengan nilai tertinggi 10,89x pada "
         "_bilinear_ dari 1080p. Persebaran ini menunjukkan bahwa "
         "titik impas keunggulan GPU ditentukan oleh jumlah piksel "
         "yang harus dihitung, bukan oleh jumlah piksel masukan.")
    emit("Kualitas keluaran mengikuti urutan yang sama pada seluruh "
         "kombinasi, yakni _bicubic_ diikuti _bilinear_ kemudian "
         "_nearest neighbor_. Kisaran PSNR adalah 44,85 hingga 53,47 "
         "dB untuk _bicubic_, 37,92 hingga 46,61 dB untuk _bilinear_, "
         "dan 30,70 hingga 38,93 dB untuk _nearest neighbor_. Nilai "
         "PSNR _bilinear_ pada pemetaan 4K ke 8K (46,61 dB) berada di "
         "atas _bicubic_ pada pemetaan dari 720p (44,85 hingga 45,04 "
         "dB), yang menunjukkan bahwa perbedaan kualitas antar metode "
         "menyempit ketika "
         "faktor pembesaran mengecil. _Max_diff_ maksimum antara "
         "keluaran GPU dan CPU pada seluruh kombinasi adalah 4,7 x "
         "10^-10, sehingga kedua jalur eksekusi menghasilkan citra "
         "yang praktis identik.")

    h2("4.4 Pembahasan")
    h3("4.4.1 Skalabilitas CPU dan Batas Simultaneous Multithreading")
    emit("Hasil pada Tabel 4.2 menunjukkan bahwa percepatan CPU tumbuh "
         "dari 1 ke 4 _thread_ pada hampir seluruh filter dan "
         "resolusi, namun tidak menambah pada 8 _thread_. Penjelasannya "
         "berasal dari struktur topeng afinitas 0xFF yang dipakai "
         "pengujian. Wilayah pengujian berisi empat P-core dengan "
         "SMT, sehingga 8 _thread_ berarti dua _thread_ pada setiap "
         "P-core. _Probe_ pada Tabel 4.1 menunjukkan tambahan _thread_ "
         "kedua pada satu P-core hanya memberi percepatan kira-kira "
         "1,6 kali, dan pada beberapa pengukuran bahkan membesarkan "
         "waktu akibat persaingan unit eksekusi dan biaya "
         "sinkronisasi. Pembesaran waktu pada 8 _thread_ yang terjadi "
         "pada filter Sobel dan Sharpen karena itu bukan keanehan "
         "penjadwalan, melainkan konsekuensi langsung dari "
         "pemetaan _thread_ pada inti fisik.")
    emit("Perbedaan antar filter menambahkan dimensi lain. Kernel "
         "Sobel menghasilkan dua komponen gradien yang dipadukan "
         "menjadi satu keluaran, sehingga jumlah operasi per piksel "
         "lebih besar daripada filter _Gaussian_ yang membagi bobot "
         "dengan nilai-nilai kecil. Semakin singkat eksekusi "
         "keseluruhan, semakin besar porsi biaya _thread pool_ "
         "terhadap waktu total, dan semakin cepat titik di mana "
         "tambahan _thread_ tidak memberi keuntungan. Hal inilah yang "
         "membuat filter Sobel pada 1080p paling cepat pada 4 "
         "_thread_ (3,1 milidetik) dan memburuk kembali pada 8 "
         "_thread_, sedangkan filter _Gaussian_ pada 8K masih "
         "memperoleh keuntungan hingga 8 _thread_.")
    h3("4.4.2 Percepatan Kernel dan Waktu Total GPU")
    emit("Waktu _kernel_ pada Tabel 4.2 memberi gambaran "
         "kekuatan komputasi GPU yang sesungguhnya. Pada filter Sobel "
         "resolusi 8K, _kernel_ GPU menyelesaikan pekerjaan dalam "
         "16,6 milidetik, sedangkan CPU 8 _thread_ membutuhkan 41,5 "
         "milidetik, sehingga rasio waktu _kernel_ terhadap CPU 8 "
         "_thread_ mencapai 2,50x. Terhadap CPU 1 _thread_ yang "
         "membutuhkan 73,8 milidetik, rasio _kernel_ mencapai 4,44x.")
    emit("Namun waktu total pemrosesan GPU, yang menambahkan transfer "
         "masukan 8K sebesar 33 megapiksel dan transfer keluaran "
         "dengan ukuran yang sama, tercatat 59,0 milidetik, yang "
         "hanya memberi percepatan total 1,25x terhadap CPU 1 "
         "_thread_. Jarak antara kedua angka ini menyatakan bahwa "
         "porsi terbesar dari waktu pemrosesan GPU pada resolusi "
         "tersebut dihabiskan di luar perhitungan. Klaim keunggulan "
         "GPU yang hanya melaporkan waktu _kernel_ karena itu akan "
         "menyesatkan, dan penelitian ini melaporkan kedua nilai "
         "secara terpisah agar pembaca dapat membedakan keduanya.")
    h3("4.4.3 Titik Impas Keunggulan GPU Menurut Resolusi")
    emit("Penyatuan hasil konvolusi dan _upscaling_ menunjukkan pola "
         "titik impas yang serupa. Pada citra keluaran 1080p, waktu "
         "transfer bolak-balik mendominasi waktu total GPU, sehingga "
         "keunggulan komputasi GPU tidak terbayar; percepatan total "
         "berada di bawah 1,2x pada seluruh skenario. Keunggulan baru "
         "tampak pada sebagian besar skenario 4K, dan menjadi "
         "konsisten pada 8K, di mana beban transfer tetap besar namun "
         "jumlah piksel yang dihitung tumbuh lebih cepat daripada "
         "waktu transfer, sehingga seluruh "
         "skenario mencapai percepatan total di atas 1,2x. Pola ini "
         "sesuai dengan temuan Asaduzzaman dkk. (2021) bahwa "
         "pemindahan memori _host-device_ menjadi sumber latensi "
         "utama pada pengolahan citra berbasis GPU. Implikasi "
         "praktisnya adalah keputusan pemindahan beban ke GPU pada "
         "operasi tunggal hanya menguntungkan ketika citra yang "
         "diproses berukuran besar, sedangkan pemrosesan citra kecil "
         "lebih efektif ditinggalkan pada CPU.")
    h3("4.4.4 Keseimbangan Kecepatan dan Kualitas Interpolasi")
    emit("Tabel 4.3 memberikan dasar untuk menilai keseimbangan antara "
         "kecepatan dan kualitas. Metode _nearest neighbor_ paling "
         "cepat pada sisi CPU dengan waktu 1 _thread_ 7,3 hingga 129,9 "
         "milidetik, namun PSNR yang dihasilkan paling jauh dari "
         "referensi Lanczos, yakni pada kisaran 30,70 hingga 38,93 dB. "
         "Metode _bilinear_ memperbaiki kualitas pada kisaran 37,92 "
         "hingga 46,61 dB dengan waktu 1 _thread_ 9,8 hingga 771,5 "
         "milidetik, sedangkan _bicubic_ mencapai kisaran 44,85 hingga "
         "53,47 dB dengan waktu 1 _thread_ 35,6 hingga 699,9 "
         "milidetik. Pada "
         "pemetaan ke 8K, waktu total GPU _bicubic_ (121,3 hingga "
         "126,4 milidetik) baru sekitar dua kali lebih besar daripada "
         "waktu total GPU _bilinear_ (60,2 hingga 61,7 milidetik), "
         "sedangkan selisih PSNR antar kedua metode cukup besar. "
         "Dengan kata lain, _bicubic_ pada batch besar adalah metode "
         "yang paling seimbang antara kualitas dan waktu ketika GPU "
         "sudah digunakan, karena beban transfer yang besar membuat "
         "selisih waktu _kernel_ antar metode menjadi kurang "
         "menentukan.")
    h3("4.4.5 Ekivalensi Numerik Antar Jalur Eksekusi")
    emit("Pengukuran tambahan membuktikan bahwa kedua jalur eksekusi "
         "menghasilkan keluaran yang praktis identik. Pada filter "
         "konvolusi, _max_diff_ antara keluaran GPU dan CPU bernilai "
         "nol pada seluruh baris. Pada _upscaling_, nilai maksimum "
         "yang tercatat adalah 4,7 x 10^-10, yang setara dengan "
         "selisih representasi bilangan pecahan setelah pembulatan "
         "operasi biner. Artinya, perbandingan "
         "waktu pada bab ini membandingkan dua implementasi yang "
         "menghasilkan keluaran yang sama, bukan dua algoritma yang "
         "berbeda.")

    h2("4.5 Keterbatasan Pengukuran")
    emit("Beberapa keterbatasan menyertai hasil pada bab ini. "
         "Setiap konfigurasi diukur satu kali per citra, "
         "sehingga laporan ini tidak menyajikan deviasi standar "
         "pengukuran pada satu citra; angka deviasi yang dilaporkan "
         "menyatakan variasi antar 100 citra. Gangguan transien "
         "yang mengenai satu jendela pengukuran tidak dapat "
         "dinetralkan dengan strategi ini, dan ketergantungannya "
         "dipantau memakai rasio median dan minimum seperti yang "
         "dijelaskan pada Bab III. Pengujian juga dilakukan pada "
         "perangkat laptop, sehingga keadaan daya dan suhu memengaruhi "
         "hasil. _Probe_ afinitas memakai beban kerja rantai "
         "aritmetika yang berbeda dari _kernel_ pengujian, sehingga "
         "angka pada Tabel 4.1 tidak dapat dipakai sebagai patokan "
         "waktu untuk _kernel_ pengujian, melainkan sebagai "
         "pembanding relatif antar topeng afinitas. Poin terakhir, "
         "verifikasi keunggulan GPU pada beban nyata memerlukan "
         "pengukuran dengan antrean pemrosesan banyak citra, yang "
         "berada di luar lingkup penelitian ini.")

    page_break()

    # BAB V PENUTUP
    h1("BAB V")
    h1("PENUTUP")

    h2("5.1 Kesimpulan")
    emit("Berdasarkan pengukuran yang telah dilakukan, kesimpulan "
         "penelitian ini disusun menjawab empat rumusan masalah pada "
         "Bab I sebagai berikut.")
    numlist(1, "Skalabilitas waktu eksekusi CPU tumbuh dari 1 ke 4 "
               "_thread_ pada seluruh filter, namun tidak menambah pada "
               "8 _thread_. Percepatan tertinggi pada filter konvolusi "
               "dicapai oleh filter _Gaussian_ pada resolusi 8K sebesar "
               "3,44x, sedangkan filter Sobel hanya mencapai 1,76x. "
               "Penjelasannya terverifikasi pada topologi prosesor: "
               "topeng afinitas pengujian memuat empat P-core dengan "
               "SMT, sehingga 8 _thread_ berarti dua _thread_ berbagi "
               "setiap P-core, dan _probe_ menunjukkan konfigurasi "
               "tersebut hanya memberi percepatan kira-kira 1,6 kali. "
               "Waktu _kernel_ GPU berada pada kisaran 4,1 hingga 16,6 "
               "milidetik, sedangkan waktu totalnya berada pada kisaran "
               "15,6 hingga 59,0 milidetik karena dibatasi transfer "
               "data.")
    numlist(2, "Ambang batas keunggulan GPU ditentukan oleh ukuran "
               "citra keluaran. Pada target 1080p, percepatan total GPU "
               "berada di bawah 1,2x sehingga GPU belum mengungguli CPU "
               "1 _thread_. Pada target 4K, keunggulan baru terlihat "
               "pada sebagian skenario dengan kisaran 0,83x hingga "
               "3,40x, sedangkan pada target 8K seluruh skenario "
               "mencapai percepatan total di atas 1,2x, dengan nilai "
               "tertinggi 10,89x pada _bilinear_ dari 1080p ke 8K.")
    numlist(3, "Efisiensi paralel pada 8 _thread_ mencapai 43% pada "
               "filter _Gaussian_ 8K, 37% pada filter Sharpen 8K, dan "
               "22% pada filter Sobel 8K. Fraksi serial eksperimental "
               "Karp-Flatt pada resolusi 8K bernilai kira-kira 0,19 "
               "untuk _Gaussian_, 0,24 untuk Sharpen, dan 0,50 untuk "
               "Sobel. Nilai yang membesar dari 4 ke 8 _thread_ "
               "menandakan biaya sinkronisasi yang tumbuh seiring "
               "jumlah _thread_, bukan sekadar fraksi serial murni. "
               "Pada sisi GPU, metrik ini tidak terdefinisi karena "
               "GPU memiliki unit pemroses yang jumlahnya tidak dapat "
               "diperbandingkan satu lawan satu dengan _thread_ CPU, "
               "sehingga evaluasinya dilakukan memakai percepatan "
               "total.")
    numlist(4, "Urutan kedekatan keluaran terhadap referensi Lanczos "
               "konsisten pada seluruh 18 kombinasi pemetaan, yakni "
               "_bicubic_ diikuti _bilinear_ kemudian _nearest "
               "neighbor_. Kisaran PSNR berturut-turut adalah 44,85 "
               "hingga 53,47 dB, 37,92 hingga 46,61 dB, dan 30,70 "
               "hingga 38,93 dB. Metode _bicubic_ memberikan "
               "keseimbangan terbaik antara kualitas dan waktu ketika "
               "pemrosesan dijalankan pada GPU, karena beban transfer "
               "yang besar mengecilkan selisih waktu antar metode. "
               "Ekivalensi numerik antara CPU dan GPU terverifikasi "
               "dengan _max_diff_ bernilai nol pada konvolusi dan "
               "4,7 x 10^-10 pada _upscaling_.")
    emit("Selain keempat rumusan tersebut, _dashboard_ berbasis "
         "Streamlit berhasil dibangun dan menampilkan seluruh hasil "
         "pengukuran dalam bentuk tabel agregat, grafik waktu eksekusi, "
         "grafik percepatan, dan metrik Karp-Flatt per konfigurasi.")

    h2("5.2 Saran")
    emit("Beberapa arah pengembangan dapat dilakukan untuk "
         "menyempurnakan temuan penelitian ini.")
    bullet("Pengukulan berulang dengan nilai _reps_ yang lebih besar "
           "pada kontrol daya dan suhu yang tercatat, sehingga "
           "deviasi pengukuran pada satu citra dapat dilaporkan.")
    bullet("Penggunaan pencacah perangkat keras (_hardware counter_) "
           "untuk melengkapi _probe_ afinitas, sehingga persaingan "
           "unit eksekusi dan efisiensi hierarki memori dapat "
           "diukur secara langsung.")
    bullet("Pengujian pada GPU kelas yang lebih tinggi serta pada "
           "prosesor dengan jumlah P-core yang lebih banyak, untuk "
           "melihat apakah ambang batas resolusi keunggulan GPU "
           "bergeser.")
    bullet("Pengukuran dengan antrean pemrosesan banyak citra pada "
           "GPU, sehingga transfer data dapat saling tumpang tindih "
           "dengan eksekusi _kernel_ dan gambaran keunggulan GPU pada "
           "beban nyata dapat diperoleh.")

    page_break()

    # DAFTAR PUSTAKA
    h1("DAFTAR PUSTAKA")
    for ref in [
        "Agustsson, E., & Timofte, R. (2017). NTIRE 2017 challenge on "
        "single image super-resolution: Dataset and study. _2017 IEEE "
        "Conference on Computer Vision and Pattern Recognition "
        "Workshops (CVPRW)_, 1122-1131. "
        "https://doi.org/10.1109/CVPRW.2017.150",

        "Akasapu, A., Sailaja, V., & Prasad, G. (2021). Implementation "
        "of Sobel filter using CUDA. _IOP Conference Series: Materials "
        "Science and Engineering_, 1045(1), 012016. "
        "https://doi.org/10.1088/1757-899X/1045/1/012016",

        "Amdahl, G. M. (1967). Validity of the single processor "
        "approach to achieving large scale computing capabilities. "
        "_AFIPS Conference Proceedings_, 30, 483-485. "
        "https://doi.org/10.1145/1465482.1465560",

        "Asaduzzaman, A., Jojigiri, S., Sabu, T., & Tailam, S. (2021). "
        "Studying execution time and memory transfer time of image "
        "processing using GPU cards. _2021 IEEE 11th Annual Computing "
        "and Communication Workshop and Conference (CCWC)_, 0689-0695. "
        "https://doi.org/10.1109/CCWC51732.2021.9376170",

        "Karp, A. H., & Flatt, H. P. (1990). Measuring parallel "
        "processor performance. _Communications of the ACM_, 33(5), "
        "539-543. https://doi.org/10.1145/78607.78614",

        "Lam, S. K., Pitrou, A., & Seibert, S. (2015). Numba: A "
        "LLVM-based Python JIT compiler. _Proceedings of the Second "
        "Workshop on the LLVM Compiler Infrastructure in HPC "
        "(LLVM-HPC 2015)_, 1-6. https://doi.org/10.1145/2833157.2833162",

        "Ruijters, D., & Thévenaz, P. (2012). GPU prefilter for "
        "accurate cubic B-spline interpolation. _The Computer "
        "Journal_, 55(1), 15-20. https://doi.org/10.1093/comjnl/bxq086",

        "Diana, D., Putri, A. R., & Santoso, B. (2026). Comparison of "
        "Sobel, Prewitt, and Canny edge detection methods in digital "
        "images. _Journal of Applied Informatics and Computing_, 10(3), "
        "2424-2430. https://doi.org/10.30871/jaic.v10i3.12860",

        "Thévenaz, P., Blu, T., & Unser, M. (2000). Interpolation "
        "revisited. _IEEE Transactions on Medical Imaging_, 19(7), "
        "739-758. https://doi.org/10.1109/42.875199",
    ]:
        p_ref = emit(ref, first_indent=None, space_after=6)
        p_ref.paragraph_format.left_indent = Cm(1.27)
        p_ref.paragraph_format.first_line_indent = Cm(-1.27)

    doc.save(OUTPUT)
    return OUTPUT

if __name__ == "__main__":
    build_document()
    print(f"Laporan berhasil dibuat di: {OUTPUT}")
