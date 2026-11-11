import os
import docx
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_proposal_document(filename):
    doc = docx.Document()

    # Atur ukuran kertas A4
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(3.0)
        section.bottom_margin = Cm(3.0)
        section.left_margin = Cm(4.0)
        section.right_margin = Cm(3.0)

    # Base style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.space_after = Pt(4)

    def add_p(text="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=4, line_spacing=1.5, first_indent=Cm(1.0)):
        p = doc.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = line_spacing
        if first_indent:
            p.paragraph_format.first_line_indent = first_indent
        if text:
            r = p.add_run(text)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(12)
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.bold = True
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.first_line_indent = Cm(0)
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(12)
        r.font.bold = True
        return p

    # ==========================================
    # HALAMAN COVER / JUDUL PIRAMIDA TERBALIK
    # ==========================================
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_header.paragraph_format.space_before = Pt(0)
    p_header.paragraph_format.space_after = Pt(18)
    r_hdr = p_header.add_run("PROPOSAL TUGAS AKHIR")
    r_hdr.font.name = 'Times New Roman'
    r_hdr.font.size = Pt(14)
    r_hdr.font.bold = True

    # Judul Piramida Terbalik
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(24)
    p_title.paragraph_format.line_spacing = 1.15
    
    r_t1 = p_title.add_run("ANALISIS PERFORMANSI KOMPUTASI PARALEL\nPADA FILTER KONVOLUSI CITRA RESOLUSI TINGGI MENGGUNAKAN\nCPU ")
    r_t1.font.name = 'Times New Roman'
    r_t1.font.size = Pt(14)
    r_t1.font.bold = True

    r_t2 = p_title.add_run("MULTI-CORE")
    r_t2.font.name = 'Times New Roman'
    r_t2.font.size = Pt(14)
    r_t2.font.bold = True
    r_t2.font.italic = True

    r_t3 = p_title.add_run(" DAN GPU CUDA")
    r_t3.font.name = 'Times New Roman'
    r_t3.font.size = Pt(14)
    r_t3.font.bold = True

    # Keterangan Pengajuan
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(18)
    p_sub.paragraph_format.space_after = Pt(36)
    p_sub.paragraph_format.line_spacing = 1.15
    r_sub = p_sub.add_run("Diajukan sebagai salah satu syarat untuk melaksanakan Seminar Proposal\npada Program Studi Rekayasa Sistem Komputer\nFakultas Matematika dan Ilmu Pengetahuan Alam\nUniversitas Tanjungpura\nPontianak")
    r_sub.font.name = 'Times New Roman'
    r_sub.font.size = Pt(11)

    # Identitas Pengusul
    p_bio = doc.add_paragraph()
    p_bio.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_bio.paragraph_format.space_before = Pt(24)
    p_bio.paragraph_format.space_after = Pt(36)
    p_bio.paragraph_format.line_spacing = 1.2
    
    r_oleh = p_bio.add_run("Disusun Oleh:\n")
    r_oleh.font.name = 'Times New Roman'
    r_oleh.font.size = Pt(12)
    
    r_nama = p_bio.add_run("TIM MAHASISWA REKAYASA SISTEM KOMPUTER\n")
    r_nama.font.name = 'Times New Roman'
    r_nama.font.size = Pt(12)
    r_nama.font.bold = True
    
    r_nim = p_bio.add_run("NIM. H1051241073\n")
    r_nim.font.name = 'Times New Roman'
    r_nim.font.size = Pt(12)

    # Institusi & Tahun
    p_foot = doc.add_paragraph()
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_foot.paragraph_format.space_before = Pt(36)
    p_foot.paragraph_format.space_after = Pt(0)
    p_foot.paragraph_format.line_spacing = 1.15
    r_foot = p_foot.add_run("PROGRAM STUDI REKAYASA SISTEM KOMPUTER\nFAKULTAS MATEMATIKA DAN ILMU PENGETAHUAN ALAM\nUNIVERSITAS TANJUNGPURA\nPONTIANAK\n2026")
    r_foot.font.name = 'Times New Roman'
    r_foot.font.size = Pt(12)
    r_foot.font.bold = True

    doc.add_page_break()

    # ==========================================
    # BAGIAN 1: IDENTITAS DAN BIDANG PENELITIAN
    # ==========================================
    add_h1("A. JUDUL PENELITIAN")
    p_jdl = add_p(first_indent=Cm(0))
    p_jdl.paragraph_format.line_spacing = 1.15
    r_j1 = p_jdl.add_run("ANALISIS PERFORMANSI KOMPUTASI PARALEL PADA FILTER KONVOLUSI CITRA RESOLUSI TINGGI MENGGUNAKAN CPU ")
    r_j1.font.bold = True
    r_j2 = p_jdl.add_run("MULTI-CORE")
    r_j2.font.bold = True
    r_j2.font.italic = True
    r_j3 = p_jdl.add_run(" DAN GPU CUDA")
    r_j3.font.bold = True

    add_h1("B. BIDANG PENELITIAN DAN MATA KULIAH PILIHAN PENDUKUNG")
    p_bid = add_p(first_indent=Cm(0))
    p_bid.paragraph_format.line_spacing = 1.15
    p_bid.add_run("Bidang Penelitian: Rekayasa Perangkat Keras, Arsitektur Sistem Komputer, dan Komputasi Cerdas.\n")
    p_bid.add_run("Mata Kuliah Pilihan Pendukung:\n")
    p_bid.add_run("1. Pengolahan Citra Digital (Semester Ganjil / 3 SKS)\n")
    p_bid.add_run("2. Sistem Terdistribusi dan Komputasi Paralel (Semester Genap / 3 SKS)\n")
    p_bid.add_run("3. Arsitektur dan Organisasi Sistem Komputer Lanjut (Semester Ganjil / 3 SKS)")

    # ==========================================
    # BAGIAN 2: LATAR BELAKANG (5 UNSUR WAJIB)
    # ==========================================
    add_h1("C. LATAR BELAKANG")
    
    p_lb1 = add_p()
    p_lb1.add_run("Pemrosesan citra digital beresolusi ultra-tinggi seperti ")
    r = p_lb1.add_run("Full HD"); r.font.italic = True
    p_lb1.add_run(" 1080p (1920x1080 piksel), 4K (3840x2160 piksel), hingga 8K (7680x4320 piksel) kini menjadi kebutuhan standar pada berbagai domain komputasi modern, mulai dari pencitraan medis, pemantauan satelit geospasial, hingga sistem inspeksi kualitas industri. Operasi konvolusi matriks dua dimensi merupakan salah satu fondasi utama dalam ekstraksi fitur, penajaman kontras (")
    r = p_lb1.add_run("sharpening"); r.font.italic = True
    p_lb1.add_run("), peredaman derau (")
    r = p_lb1.add_run("Gaussian blur"); r.font.italic = True
    p_lb1.add_run("), dan deteksi tepi (")
    r = p_lb1.add_run("Sobel edge detection"); r.font.italic = True
    p_lb1.add_run("). Namun, ketika diterapkan pada citra 8K yang memuat lebih dari 33,17 juta piksel, operasi konvolusi spasial membutuhkan ratusan juta perkalian dan penjumlahan akumulatif. Pemrosesan secara sekuensial menggunakan CPU ")
    r = p_lb1.add_run("single-core"); r.font.italic = True
    p_lb1.add_run(" tradisional menimbulkan kendala latensi eksekusi yang tinggi dan ")
    r = p_lb1.add_run("bottleneck"); r.font.italic = True
    p_lb1.add_run(" komputasi yang parah, sehingga tidak mampu memenuhi tuntutan pemrosesan waktu-nyata (")
    r = p_lb1.add_run("real-time processing"); r.font.italic = True
    p_lb1.add_run(").")

    p_lb2 = add_p()
    p_lb2.add_run("Sejumlah riset terdahulu telah meneliti strategi akselerasi komputasi untuk mengatasi keterbatasan performa tersebut. Akasapu, Sailaja, dan Prasad (2021) mengimplementasikan filter deteksi tepi Sobel berbasis ")
    r = p_lb2.add_run("Compute Unified Device Architecture"); r.font.italic = True
    p_lb2.add_run(" (CUDA) pada GPU, di mana pemanfaatan ribuan ")
    r = p_lb2.add_run("threads"); r.font.italic = True
    p_lb2.add_run(" secara serentak terbukti memangkas waktu eksekusi secara drastis dibandingkan komputasi CPU sekuensial. Selanjutnya, Asaduzzaman, Jojigiri, Sabu, dan Tailam (2021) menganalisis rasio antara waktu komputasi murni dengan waktu transfer memori pada kartu GPU, yang menunjukkan bahwa transfer data antara memori utama sistem (")
    r = p_lb2.add_run("host"); r.font.italic = True
    p_lb2.add_run(") dan memori grafis (")
    r = p_lb2.add_run("device"); r.font.italic = True
    p_lb2.add_run(") melalui bus PCIe merupakan komponen latensi kritis yang menentukan batas efisiensi riil akselerator. Di bidang evaluasi kualitas operator deteksi tepi, Diana, Agustina, Situmorang, Kholid, dan Pratama (2026) membandingkan operator Sobel, Prewitt, dan Canny pada 20 citra uji dari basis data USC-SIPI menggunakan empat metrik, yaitu ")
    r = p_lb2.add_run("Mean Squared Error"); r.font.italic = True
    p_lb2.add_run(" (MSE), PSNR, F-")
    r = p_lb2.add_run("measure"); r.font.italic = True
    p_lb2.add_run(", dan waktu komputasi. Hasil pengujian menunjukkan bahwa operator Canny memperoleh MSE rata-rata terendah sebesar 7,26 serta PSNR tertinggi 40,06 dB, namun menanggung biaya komputasi tiga hingga empat kali lipat dibandingkan operator Sobel dan Prewitt yang berkisar 2,4 milidetik. Temuan tersebut menegaskan adanya ")
    r = p_lb2.add_run("trade-off"); r.font.italic = True
    p_lb2.add_run(" antara akurasi deteksi dan beban komputasi yang menjadi pertimbangan utama dalam pemilihan operator pada sistem pemrosesan waktu-nyata.")

    p_lb2b = add_p()
    p_lb2b.add_run("Pada ranah peningkatan resolusi citra, kualitas interpolasi dan efisiensi komputasinya menjadi kajian yang sama pentingnya. Thévenaz, Blu, dan Unser (2000) merumuskan kembali landasan teoretik interpolasi citra digital, yang menekankan bahwa pemilihan fungsi basis interpolasi menentukan keseimbangan antara akurasi pemulihan sinyal dan beban komputasi, serta memperkenalkan kerangka evaluasi kesalahan interpolasi berbasis kesalahan kuadrat rata-rata. Ruijters dan Thévenaz (2012) kemudian mengimplementasikan prafilter interpolasi ")
    r = p_lb2b.add_run("cubic B-spline"); r.font.italic = True
    p_lb2b.add_run(" pada GPU CUDA, membuktikan bahwa metode interpolasi orde tinggi yang sebelumnya hanya layak dijalankan pada CPU dapat dipercepat secara signifikan melalui rekursi kausal dan anti-kausal yang dipetakan ke ribuan ")
    r = p_lb2b.add_run("threads"); r.font.italic = True
    p_lb2b.add_run(" GPU. Kedua kajian ini menjadi landasan penting bagi penelitian yang menggabungkan analisis kualitas interpolasi dengan analisis performa komputasi paralel.")

    p_lb3 = add_p()
    p_lb3.add_run("Meskipun riset-riset tersebut membuktikan efektivitas komputasi paralel, terdapat kesenjangan penelitian (")
    r = p_lb3.add_run("research gap"); r.font.italic = True
    p_lb3.add_run(") yang belum dikaji secara tuntas. Beberapa penelitian terdahulu hanya membandingkan performa secara polar antara CPU 1 ")
    r = p_lb3.add_run("core"); r.font.italic = True
    p_lb3.add_run(" berhadapan langsung dengan GPU, tanpa membedah karakteristik skalabilitas bertingkat pada CPU ")
    r = p_lb3.add_run("multi-core"); r.font.italic = True
    p_lb3.add_run(" (alokasi 1, 2, 4, hingga 8 ")
    r = p_lb3.add_run("core"); r.font.italic = True
    p_lb3.add_run(") berdasarkan Hukum Amdahl. Selain itu, kajian interpolasi citra seperti yang dilakukan Thévenaz dkk. (2000) dan Ruijters serta Thévenaz (2012) berfokus pada akurasi pemulihan sinyal, namun belum membandingkan hasil keluaran antarmetode secara kuantitatif terhadap referensi pada konfigurasi pemroses yang bervariasi. Evaluasi komparasi yang menggabungkan kedua aspek tersebut, yaitu kualitas keluaran dan waktu eksekusi pada resolusi ultra-tinggi hingga 8K, belum dipetakan secara presisi, terutama mengenai ambang batas peralihan (")
    r = p_lb3.add_run("trade-off threshold"); r.font.italic = True
    p_lb3.add_run(") antara penalti waktu transfer memori ")
    r = p_lb3.add_run("host-to-device"); r.font.italic = True
    p_lb3.add_run(" dengan akselerasi komputasi ")
    r = p_lb3.add_run("kernel"); r.font.italic = True
    p_lb3.add_run(" GPU secara kuantitatif.")

    p_lb4 = add_p()
    p_lb4.add_run("Sebagai solusi atas permasalahan tersebut, penelitian ini mengusulkan analisis performansi komprehensif dan perancangan kerangka komputasi paralel heterogen untuk filter konvolusi citra resolusi bertingkat (1080p, 4K, dan 8K), sekaligus operasi peningkatan resolusi (")
    r = p_lb4.add_run("upscaling"); r.font.italic = True
    p_lb4.add_run(") dari 1080p ke 4K dan dari 4K ke 8K. Kerangka kerja ini dibangun menggunakan teknik kompilasi ")
    r = p_lb4.add_run("Just-In-Time"); r.font.italic = True
    p_lb4.add_run(" (JIT) Numba pada arsitektur CPU ")
    r = p_lb4.add_run("multi-core"); r.font.italic = True
    p_lb4.add_run(" dengan alokasi terdistribusi (1, 2, 4, dan 8 ")
    r = p_lb4.add_run("core"); r.font.italic = True
    p_lb4.add_run(") serta kernel paralel teroptimasi pada arsitektur GPU NVIDIA CUDA (RTX 3050). Alasan pemilihan solusi ini didasarkan pada kemampuan Numba JIT dalam mengeliminasi ")
    r = p_lb4.add_run("overhead Global Interpreter Lock"); r.font.italic = True
    p_lb4.add_run(" (GIL) Python secara natif dan kemampuan CUDA dalam mengeksekusi operasi konvolusi dua dimensi secara masif melalui ribuan ")
    r = p_lb4.add_run("thread"); r.font.italic = True
    p_lb4.add_run(" yang terpetakan ke dalam ")
    r = p_lb4.add_run("grid of blocks"); r.font.italic = True
    p_lb4.add_run(".")

    p_lb5 = add_p()
    p_lb5.add_run("Melalui penelitian ini, akan dihasilkan tolok ukur (")
    r = p_lb5.add_run("benchmark"); r.font.italic = True
    p_lb5.add_run(") kuantitatif mengenai rasio percepatan (")
    r = p_lb5.add_run("speedup"); r.font.italic = True
    p_lb5.add_run("), efisiensi komputasi paralel, identifikasi titik jenuh pemrosesan, serta pengaruh latensi transfer memori antarmuka PCIe. Pada operasi ")
    r = p_lb5.add_run("upscaling"); r.font.italic = True
    p_lb5.add_run(", dihasilkan pula pengukuran kedekatan keluaran antarmetode interpolasi terhadap hasil interpolasi ")
    r = p_lb5.add_run("Lanczos"); r.font.italic = True
    p_lb5.add_run(" sebagai referensi. Selain itu, seluruh modul komputasi akan diintegrasikan ke dalam sebuah aplikasi dasbor pengujian visual interaktif berbasis web, yang memungkinkan akademisi dan praktisi mereplikasi, memvalidasi, serta menganalisis performa filter konvolusi citra secara langsung.")

    # ==========================================
    # BAGIAN 3: RUMUSAN MASALAH
    # ==========================================
    add_h1("D. RUMUSAN MASALAH")
    p_rm = add_p(first_indent=Cm(0))
    p_rm.add_run("Berdasarkan latar belakang masalah yang telah diuraikan, rumusan masalah dalam penelitian ini dirumuskan sebagai berikut:")
    
    p_rm1 = add_p(first_indent=Cm(0.5))
    p_rm1.add_run("1. Bagaimana karakteristik skalabilitas waktu eksekusi dan rasio ")
    r = p_rm1.add_run("speedup"); r.font.italic = True
    p_rm1.add_run(" pemrosesan filter konvolusi citra serta operasi ")
    r = p_rm1.add_run("upscaling"); r.font.italic = True
    p_rm1.add_run(" citra pada variasi alokasi 1 ")
    r = p_rm1.add_run("core"); r.font.italic = True
    p_rm1.add_run(", 2 ")
    r = p_rm1.add_run("core"); r.font.italic = True
    p_rm1.add_run(", 4 ")
    r = p_rm1.add_run("core"); r.font.italic = True
    p_rm1.add_run(", dan 8 ")
    r = p_rm1.add_run("core"); r.font.italic = True
    p_rm1.add_run(" CPU dibandingkan dengan akselerasi masif GPU NVIDIA CUDA?")

    p_rm2 = add_p(first_indent=Cm(0.5))
    p_rm2.add_run("2. Pada ambang batas resolusi citra berapakah akselerasi komputasi paralel GPU CUDA mulai efektif melampaui penalti latensi ")
    r = p_rm2.add_run("overhead"); r.font.italic = True
    p_rm2.add_run(" transfer memori ")
    r = p_rm2.add_run("host-to-device"); r.font.italic = True
    p_rm2.add_run(" melalui antarmuka PCIe jika dibandingkan dengan komputasi CPU ")
    r = p_rm2.add_run("multi-core"); r.font.italic = True
    p_rm2.add_run("?")

    p_rm3 = add_p(first_indent=Cm(0.5))
    p_rm3.add_run("3. Berapa tingkat efisiensi paralel (")
    r = p_rm3.add_run("parallel efficiency"); r.font.italic = True
    p_rm3.add_run(") dan fraksi paralel (")
    r = p_rm3.add_run("parallel fraction"); r.font.italic = True
    p_rm3.add_run(") berdasarkan Hukum Amdahl pada penambahan jumlah ")
    r = p_rm3.add_run("core"); r.font.italic = True
    p_rm3.add_run(" CPU serta ")
    r = p_rm3.add_run("streaming multiprocessor"); r.font.italic = True
    p_rm3.add_run(" GPU untuk variasi resolusi citra 1080p, 4K, dan 8K?")

    p_rm4 = add_p(first_indent=Cm(0.5))
    p_rm4.add_run("4. Bagaimana tingkat kedekatan keluaran operasi ")
    r = p_rm4.add_run("upscaling"); r.font.italic = True
    p_rm4.add_run(" citra dari 1080p ke 4K dan dari 4K ke 8K yang dihasilkan oleh metode interpolasi ")
    r = p_rm4.add_run("Nearest Neighbor"); r.font.italic = True
    p_rm4.add_run(", Bilinear, dan Bicubic terhadap referensi interpolasi ")
    r = p_rm4.add_run("Lanczos"); r.font.italic = True
    p_rm4.add_run(" yang diukur menggunakan MSE dan PSNR pada setiap konfigurasi pemroses?")

    # ==========================================
    # BAGIAN 4: BATASAN MASALAH
    # ==========================================
    add_h1("E. BATASAN MASALAH")
    p_bm = add_p(first_indent=Cm(0))
    p_bm.add_run("Agar penelitian ini terarah dan fokus pada substansi yang diuji, batasan masalah ditetapkan sebagai berikut:")
    
    p_bm1 = add_p(first_indent=Cm(0.5))
    p_bm1.add_run("1. Perangkat keras komputasi yang digunakan adalah prosesor Intel Core 5 210H (8 ")
    r = p_bm1.add_run("physical cores"); r.font.italic = True
    p_bm1.add_run(": 4 ")
    r = p_bm1.add_run("Performance-cores"); r.font.italic = True
    p_bm1.add_run(" dan 4 ")
    r = p_bm1.add_run("Efficient-cores"); r.font.italic = True
    p_bm1.add_run(", 12 ")
    r = p_bm1.add_run("threads"); r.font.italic = True
    p_bm1.add_run(") dengan memori RAM 16 GB DDR5, serta unit pemroses grafis NVIDIA GeForce RTX 3050 Laptop GPU (6 GB GDDR6 VRAM, arsitektur Ampere ")
    r = p_bm1.add_run("Compute Capability"); r.font.italic = True
    p_bm1.add_run(" 8.6). Jumlah ")
    r = p_bm1.add_run("streaming multiprocessor"); r.font.italic = True
    p_bm1.add_run(" dan ")
    r = p_bm1.add_run("CUDA cores"); r.font.italic = True
    p_bm1.add_run(" dibaca langsung dari perangkat melalui API CUDA saat pengujian, bukan diasumsikan dari deskripsi pabrikan, karena jumlah tersebut berbeda antar varian kartu grafis yang sama.")

    p_bm2 = add_p(first_indent=Cm(0.5))
    p_bm2.add_run("2. Resolusi citra uji dibatasi pada tiga tingkatan standar resolusi tinggi: ")
    r = p_bm2.add_run("Full HD"); r.font.italic = True
    p_bm2.add_run(" 1080p (1920x1080 piksel / 2,07 megapiksel), 4K UHD (3840x2160 piksel / 8,29 megapiksel), dan 8K UHD (7680x4320 piksel / 33,17 megapiksel). Citra diubah ke mode grayscale 8-bit kemudian diproses dalam matriks presisi tunggal (")
    r = p_bm2.add_run("float32"); r.font.italic = True
    p_bm2.add_run(") satu kanal.")

    p_bm3 = add_p(first_indent=Cm(0.5))
    p_bm3.add_run("3. Operasi spasial konvolusi citra difokuskan pada operator matriks kernel 3x3: filter deteksi tepi Sobel (gradien horizontal ")
    r = p_bm3.add_run("Gx"); r.font.italic = True
    p_bm3.add_run(" dan vertikal ")
    r = p_bm3.add_run("Gy"); r.font.italic = True
    p_bm3.add_run("), filter peredam derau ")
    r = p_bm3.add_run("Gaussian Blur"); r.font.italic = True
    p_bm3.add_run(" 3x3, dan filter penajaman citra (")
    r = p_bm3.add_run("Sharpening"); r.font.italic = True
    p_bm3.add_run(") 3x3 dengan matriks [0, -1, 0; -1, 5, -1; 0, -1, 0]. Kernel ini berlaku untuk seluruh pengujian CPU, GPU, dan dasbor, sehingga hasil ketiganya dapat dibandingkan langsung.")

    p_bm3b = add_p(first_indent=Cm(0.5))
    p_bm3b.add_run("4. Operasi peningkatan resolusi (")
    r = p_bm3b.add_run("upscaling"); r.font.italic = True
    p_bm3b.add_run(") dibatasi pada pemetaan 1080p ke 4K UHD dan 4K UHD ke 8K UHD menggunakan tiga metode interpolasi, yaitu ")
    r = p_bm3b.add_run("Nearest Neighbor"); r.font.italic = True
    p_bm3b.add_run(", Bilinear, dan Bicubic (Catmull-Rom), dengan kualitas keluaran dievaluasi terhadap hasil interpolasi ")
    r = p_bm3b.add_run("Lanczos"); r.font.italic = True
    p_bm3b.add_run(" pada referensi yang sama.")

    p_bm4 = add_p(first_indent=Cm(0.5))
    p_bm4.add_run("5. Lingkungan pemrograman menggunakan bahasa Python 3.14 dengan akselerasi kompilasi ")
    r = p_bm4.add_run("Just-In-Time"); r.font.italic = True
    p_bm4.add_run(" Numba CPU (")
    r = p_bm4.add_run("parallel=True"); r.font.italic = True
    p_bm4.add_run(" dan ")
    r = p_bm4.add_run("prange"); r.font.italic = True
    p_bm4.add_run(") serta Numba CUDA terintegrasi dengan CUDA Toolkit 13.")

    p_bm5 = add_p(first_indent=Cm(0.5))
    p_bm5.add_run("6. Konfigurasi CPU yang diuji dibatasi pada alokasi 1 ")
    r = p_bm5.add_run("core"); r.font.italic = True
    p_bm5.add_run(", 2 ")
    r = p_bm5.add_run("core"); r.font.italic = True
    p_bm5.add_run(", 4 ")
    r = p_bm5.add_run("core"); r.font.italic = True
    p_bm5.add_run(", dan 8 ")
    r = p_bm5.add_run("core"); r.font.italic = True
    p_bm5.add_run(" fisik aktif untuk menguji skalabilitas murni komputasi paralel.")

    p_bm6 = add_p(first_indent=Cm(0.5))
    p_bm6.add_run("7. Aplikasi pengujian visual dibangun sebagai dasbor interaktif berbasis web menggunakan pustaka Streamlit yang berjalan secara lokal pada sistem komputer pengujian.")

    # ==========================================
    # BAGIAN 5: TUJUAN PENELITIAN
    # ==========================================
    add_h1("F. TUJUAN PENELITIAN")
    p_tj = add_p(first_indent=Cm(0))
    p_tj.add_run("Tujuan yang ingin dicapai melalui pelaksanaan penelitian Tugas Akhir ini adalah:")
    
    p_tj1 = add_p(first_indent=Cm(0.5))
    p_tj1.add_run("1. Menganalisis karakteristik skalabilitas waktu eksekusi dan menghitung rasio percepatan (")
    r = p_tj1.add_run("speedup"); r.font.italic = True
    p_tj1.add_run(") pemrosesan filter konvolusi citra serta operasi ")
    r = p_tj1.add_run("upscaling"); r.font.italic = True
    p_tj1.add_run(" citra pada variasi konfigurasi 1 ")
    r = p_tj1.add_run("core"); r.font.italic = True
    p_tj1.add_run(", 2 ")
    r = p_tj1.add_run("core"); r.font.italic = True
    p_tj1.add_run(", 4 ")
    r = p_tj1.add_run("core"); r.font.italic = True
    p_tj1.add_run(", 8 ")
    r = p_tj1.add_run("core"); r.font.italic = True
    p_tj1.add_run(" CPU, dan GPU NVIDIA CUDA.")

    p_tj2 = add_p(first_indent=Cm(0.5))
    p_tj2.add_run("2. Menentukan ambang batas resolusi citra di mana akselerasi komputasi paralel GPU CUDA efektif mengungguli penalti latensi transfer memori ")
    r = p_tj2.add_run("host-to-device"); r.font.italic = True
    p_tj2.add_run(" melalui bus PCIe.")

    p_tj3 = add_p(first_indent=Cm(0.5))
    p_tj3.add_run("3. Mengukur efisiensi komputasi paralel (")
    r = p_tj3.add_run("parallel efficiency"); r.font.italic = True
    p_tj3.add_run(") dan mengestimasi fraksi paralel berdasarkan Hukum Amdahl pada setiap tingkatan resolusi citra (1080p, 4K, dan 8K).")

    p_tj3b = add_p(first_indent=Cm(0.5))
    p_tj3b.add_run("4. Mengukur tingkat kedekatan keluaran operasi ")
    r = p_tj3b.add_run("upscaling"); r.font.italic = True
    p_tj3b.add_run(" dari 1080p ke 4K dan dari 4K ke 8K yang dihasilkan oleh metode interpolasi ")
    r = p_tj3b.add_run("Nearest Neighbor"); r.font.italic = True
    p_tj3b.add_run(", Bilinear, dan Bicubic menggunakan MSE dan PSNR terhadap referensi interpolasi ")
    r = p_tj3b.add_run("Lanczos"); r.font.italic = True
    p_tj3b.add_run(" menggunakan MSE dan PSNR pada setiap konfigurasi pemroses (CPU 1, 2, 4, 8 core, dan GPU).")

    p_tj4 = add_p(first_indent=Cm(0.5))
    p_tj4.add_run("5. Mengembangkan aplikasi dasbor pengujian visual interaktif untuk mendemonstrasikan perbandingan performa, analisis grafis, dan visualisasi hasil operasi secara langsung.")

    # ==========================================
    # BAGIAN 6: MANFAAT PENELITIAN
    # ==========================================
    add_h1("G. MANFAAT PENELITIAN")
    p_mf = add_p(first_indent=Cm(0))
    p_mf.add_run("Hasil penelitian ini diharapkan dapat memberikan manfaat teoretis dan praktis sebagai berikut:")
    
    p_mf1 = add_p(first_indent=Cm(0.5))
    p_mf1.add_run("1. Bagi Mahasiswa dan Peneliti: Memperdalam pemahaman empiris mengenai arsitektur sistem komputasi heterogen (CPU-GPU), mekanisme hierarki memori, teknik eliminasi ")
    r = p_mf1.add_run("overhead"); r.font.italic = True
    p_mf1.add_run(" kompilasi, serta formulasi Hukum Amdahl dalam aplikasi nyata.")

    p_mf2 = add_p(first_indent=Cm(0.5))
    p_mf2.add_run("2. Bagi Program Studi Rekayasa Sistem Komputer: Menyediakan repositori data tolok ukur (")
    r = p_mf2.add_run("benchmark"); r.font.italic = True
    p_mf2.add_run(") perangkat keras modern serta menjadi bahan rujukan praktikum pada mata kuliah Sistem Terdistribusi dan Komputasi Paralel serta Pengolahan Citra Digital.")

    p_mf3 = add_p(first_indent=Cm(0.5))
    p_mf3.add_run("3. Bagi Industri dan Praktisi Sistem Cerdas: Memberikan panduan praktis dan rekomendasi pemilihan arsitektur perangkat keras dalam merancang sistem pemrosesan citra resolusi tinggi secara efisien dan tepat guna.")

    # ==========================================
    # BAGIAN 7: DESKRIPSI PENELITIAN
    # ==========================================
    add_h1("H. DESKRIPSI PENELITIAN")
    
    p_dp1 = add_p()
    p_dp1.add_run("Penelitian ini berfokus pada analisis mendalam mengenai pemrosesan konvolusi citra dua dimensi berbasis komputasi paralel heterogen. Operasi konvolusi diskret pada citra digital ")
    r = p_dp1.add_run("I(x, y)"); r.font.italic = True
    p_dp1.add_run(" dengan matriks kernel ")
    r = p_dp1.add_run("K"); r.font.italic = True
    p_dp1.add_run(" berukuran ")
    r = p_dp1.add_run("(2a+1) x (2b+1)"); r.font.italic = True
    p_dp1.add_run(" dimodelkan melalui persamaan matematika berikut:")

    # Persamaan Konvolusi
    p_eq1 = doc.add_paragraph()
    p_eq1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq1.paragraph_format.space_before = Pt(4)
    p_eq1.paragraph_format.space_after = Pt(4)
    r_eq1 = p_eq1.add_run("S(x, y) = (I * K)(x, y) = ∑[i=-a..a] ∑[j=-b..b] I(x - i, y - j) · K(i, j)        (1)")
    r_eq1.font.bold = True

    p_dp2 = add_p()
    p_dp2.add_run("Pada operator deteksi tepi Sobel 3x3, citra dikenakan dua kernel ortogonal untuk menghitung komponen gradien horizontal (")
    r = p_dp2.add_run("Gx"); r.font.italic = True
    p_dp2.add_run(") dan vertikal (")
    r = p_dp2.add_run("Gy"); r.font.italic = True
    p_dp2.add_run("), dengan magnitudo gradien total dirumuskan sebagai:")

    p_eq2 = doc.add_paragraph()
    p_eq2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq2.paragraph_format.space_before = Pt(4)
    p_eq2.paragraph_format.space_after = Pt(4)
    r_eq2 = p_eq2.add_run("G(x, y) = √[ (Gx(x, y))² + (Gy(x, y))² ]        (2)")
    r_eq2.font.bold = True

    p_dp2b = add_p()
    p_dp2b.add_run("Pada operasi peningkatan resolusi (")
    r = p_dp2b.add_run("upscaling"); r.font.italic = True
    p_dp2b.add_run("), citra masukan berukuran ")
    r = p_dp2b.add_run("H_in × W_in"); r.font.italic = True
    p_dp2b.add_run(" dipetakan ke citra keluaran ")
    r = p_dp2b.add_run("H_out × W_out"); r.font.italic = True
    p_dp2b.add_run(". Setiap piksel keluaran dihitung dengan mengambil sampel koordinat sumber menggunakan konvensi pusat piksel (")
    r = p_dp2b.add_run("center-aligned"); r.font.italic = True
    p_dp2b.add_run("):")

    p_eq2b = doc.add_paragraph()
    p_eq2b.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq2b.paragraph_format.space_before = Pt(2)
    p_eq2b.paragraph_format.space_after = Pt(2)
    r_eq2b = p_eq2b.add_run("fy = (yo + 0,5) · sy − 0,5,  sy = H_in / H_out        (2b)\n")
    r_eq2b.font.bold = True
    r_eq2c = p_eq2b.add_run("fx = (xo + 0,5) · sx − 0,5,  sx = W_in / W_out        (2c)")
    r_eq2c.font.bold = True

    p_dp2c = add_p()
    p_dp2c.add_run("Konvensi ini merupakan standar yang digunakan oleh pustaka pemrosesan citra seperti PIL dan OpenCV, sehingga hasil implementasi dapat divalidasi silang secara langsung. Metode ")
    r = p_dp2c.add_run("Nearest Neighbor"); r.font.italic = True
    p_dp2c.add_run(" mengambil nilai piksel sumber terdekat, metode Bilinear melakukan pembobotan linear atas empat piksel tetangga, dan metode Bicubic melakukan pemboboan 16 piksel tetangga menggunakan fungsi basis Catmull-Rom. Karena bobot interpolasi pada tepi citra tidak selalu berjumlah tepat satu akibat penjepitan koordinat, nilai akhir dinormalisasi terhadap jumlah seluruh bobot yang digunakan. Kualitas keluaran diukur terhadap hasil interpolasi ")
    r = p_dp2c.add_run("Lanczos"); r.font.italic = True
    p_dp2c.add_run(" sebagai referensi menggunakan MSE dan PSNR. MSE dan PSNR pada bagian ini mengukur tingkat kemiripan numerik terhadap keluaran referensi ")
    r = p_dp2c.add_run("Lanczos"); r.font.italic = True
    p_dp2c.add_run(", bukan kualitas visual mutlak:")

    p_eq2d = doc.add_paragraph()
    p_eq2d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq2d.paragraph_format.space_before = Pt(2)
    p_eq2d.paragraph_format.space_after = Pt(2)
    r_eq2d = p_eq2d.add_run("MSE = (1/N) · ∑ (Îᵢ − Iᵢᵣₑբ)²        (2d)\n")
    r_eq2d.font.bold = True
    r_eq2e = p_eq2d.add_run("PSNR = 20 · log₁₀ (255 / √MSE)        (2e)")
    r_eq2e.font.bold = True

    p_dp3 = add_p()
    p_dp3.add_run("Evaluasi performansi komputasi paralel dianalisis melalui tiga metrik fundamental, yaitu percepatan (")
    r = p_dp3.add_run("speedup"); r.font.italic = True
    p_dp3.add_run("), efisiensi paralel, dan formulasi Hukum Amdahl:")

    p_eq3 = doc.add_paragraph()
    p_eq3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq3.paragraph_format.space_before = Pt(2)
    p_eq3.paragraph_format.space_after = Pt(2)
    r_eq3 = p_eq3.add_run("Speedup (Sp) = T₁ / Tp        (3)\n")
    r_eq3.font.bold = True
    r_eq4 = p_eq3.add_run("Efisiensi (Ep) = Sp / p = T₁ / (p · Tp) × 100%        (4)\n")
    r_eq4.font.bold = True
    r_eq5 = p_eq3.add_run("Hukum Amdahl: S_teoretis = 1 / [ (1 - P) + (P / s) ]        (5)")
    r_eq5.font.bold = True

    p_dp4 = add_p()
    p_dp4.add_run("Di mana ")
    r = p_dp4.add_run("T₁"); r.font.italic = True
    p_dp4.add_run(" adalah waktu eksekusi sekuensial (1 ")
    r = p_dp4.add_run("core"); r.font.italic = True
    p_dp4.add_run("), ")
    r = p_dp4.add_run("Tp"); r.font.italic = True
    p_dp4.add_run(" adalah waktu eksekusi pada ")
    r = p_dp4.add_run("p core"); r.font.italic = True
    p_dp4.add_run(" paralel, ")
    r = p_dp4.add_run("P"); r.font.italic = True
    p_dp4.add_run(" merepresentasikan proporsi program yang dapat diparalelkan, dan ")
    r = p_dp4.add_run("s"); r.font.italic = True
    p_dp4.add_run(" adalah faktor percepatan perangkat keras. Pada arsitektur GPU CUDA, waktu total mencakup komponen transfer data antarmuka PCIe:")

    p_eq6 = doc.add_paragraph()
    p_eq6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq6.paragraph_format.space_before = Pt(4)
    p_eq6.paragraph_format.space_after = Pt(8)
    r_eq6 = p_eq6.add_run("T_total_GPU = T_H2D + T_kernel + T_D2H        (6)")
    r_eq6.font.bold = True

    p_dp5 = add_p()
    p_dp5.add_run("Di mana ")
    r = p_dp5.add_run("T_H2D"); r.font.italic = True
    p_dp5.add_run(" adalah latensi salin memori ")
    r = p_dp5.add_run("host-to-device"); r.font.italic = True
    p_dp5.add_run(", ")
    r = p_dp5.add_run("T_kernel"); r.font.italic = True
    p_dp5.add_run(" adalah durasi komputasi murni pada ")
    r = p_dp5.add_run("Streaming Multiprocessors"); r.font.italic = True
    p_dp5.add_run(", dan ")
    r = p_dp5.add_run("T_D2H"); r.font.italic = True
    p_dp5.add_run(" adalah waktu salin hasil kembali ke memori ")
    r = p_dp5.add_run("host"); r.font.italic = True
    p_dp5.add_run(". Persamaan ini menjadi landasan analisis penentuan titik impas (")
    r = p_dp5.add_run("break-even point"); r.font.italic = True
    p_dp5.add_run(") efisiensi pemrosesan GPU.")

    p_prelim = add_p()
    p_prelim.add_run("Pengujian pendahuluan telah dilakukan pada perangkat uji nyata (Intel Core 5 210H dan NVIDIA GeForce RTX 3050 Laptop GPU) untuk memproses citra 8K UHD (7680x4320 piksel) menggunakan filter penajaman 3x3. Hasil pengujian dirangkum pada Tabel 1. Data ini diperoleh dari 3 kali pengulangan tanpa deviasi standar, sehingga hanya diperlakukan sebagai indikasi awal. Pengukuran final dengan 10 pengulangan, median, dan deviasi standar akan dilakukan pada tahap pengujian empiris menggunakan skrip ")
    r = p_prelim.add_run("benchmark"); r.font.italic = True
    p_prelim.add_run(" yang sama dengan aplikasi dasbor.")

    # Tabel Prelim Benchmark Hasil Nyata
    add_h2("Tabel 1. Hasil Pengujian Pendahuluan Komputasi Konvolusi Citra 8K")
    
    table = doc.add_table(rows=7, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Konfigurasi Unit Pemroses", "Waktu Eksekusi (Detik)", "Speedup Relatif", "Efisiensi Paralel", "Kategori Latensi"]
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = text
        set_cell_background(cell, "E0E0E0")
        set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.font.bold = True

    data_rows = [
        ["CPU 1 Core (Sekuensial Baseline)", "0.551", "1.00x", "100.0%", "Komputasi Sekuensial Murni"],
        ["CPU 2 Cores (Multi-Core Paralel)", "0.259", "2.13x", "106.5%", "Thread Parallelism P-Cores"],
        ["CPU 4 Cores (Multi-Core Paralel)", "0.164", "3.35x", "83.8%", "Thread Parallelism Full P-Cores"],
        ["CPU 8 Cores (Multi-Core Paralel)", "0.107", "5.17x", "64.6%", "Kombinasi P-Cores & E-Cores"],
        ["GPU CUDA (Kernel Komputasi Murni)", "0.040", "13.68x", "N/A", "Massive SIMT GPU Execution"],
        ["GPU CUDA (Total Waktu Termasuk I/O)", "0.417", "1.32x", "N/A", "Host-to-Device + Kernel + Device-to-Host"]
    ]

    for row_idx, row_data in enumerate(data_rows):
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = val
            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx in [1, 2, 3] else WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10)

    p_tbl_note = doc.add_paragraph()
    p_tbl_note.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_tbl_note.paragraph_format.space_before = Pt(4)
    p_tbl_note.paragraph_format.space_after = Pt(12)
    p_tbl_note.paragraph_format.first_line_indent = Cm(0)
    r_note = p_tbl_note.add_run("*Sumber: Pengujian pendahuluan pada perangkat uji Intel Core 5 210H dan NVIDIA RTX 3050 (2026), 3 pengulangan, kernel penajaman 5 titik pada citra RGB. Angka pada tabel ini bersifat sementara dan akan diganti dengan hasil pengukuran final.")
    r_note.font.size = Pt(9)
    r_note.font.italic = True

    p_find1 = add_p()
    p_find1.add_run("Tiga pengamatan dapat ditarik dari Tabel 1. Pertama, skalabilitas CPU bersifat sublinear pada jumlah ")
    r = p_find1.add_run("core"); r.font.italic = True
    p_find1.add_run(" yang lebih besar. Efisiensi turun dari 83,8% pada 4 ")
    r = p_find1.add_run("core"); r.font.italic = True
    p_find1.add_run(" menjadi 64,6% pada 8 ")
    r = p_find1.add_run("core"); r.font.italic = True
    p_find1.add_run(". Penurunan ini konsisten dengan keterbatasan ")
    r = p_find1.add_run("bandwidth"); r.font.italic = True
    p_find1.add_run(" memori pada operasi konvolusi 3x3 yang intensitas aritmetikanya rendah, serta dengan komposisi 8 ")
    r = p_find1.add_run("core"); r.font.italic = True
    p_find1.add_run(" yang terdiri atas 4 ")
    r = p_find1.add_run("Performance-core"); r.font.italic = True
    p_find1.add_run(" dan 4 ")
    r = p_find1.add_run("Efficient-core"); r.font.italic = True
    p_find1.add_run(" dengan kemampuan berbeda. Penyebab dominan belum dibuktikan pada tahap proposal, dan akan ditelaah dengan metrik Karp-Flatt serta pengujian tambahan pada konfigurasi ")
    r = p_find1.add_run("thread"); r.font.italic = True
    p_find1.add_run(" menengah.")

    p_find2 = add_p()
    p_find2.add_run("Kedua, efisiensi 106,5% pada 2 ")
    r = p_find2.add_run("core"); r.font.italic = True
    p_find2.add_run(" melebihi batas 100% dan diperlakukan sebagai anomali pengukuran, bukan sebagai bukti efek ")
    r = p_find2.add_run("cache"); r.font.italic = True
    p_find2.add_run(". Citra 8K pada pengujian ini berukuran 398 MB (3 kanal ")
    r = p_find2.add_run("float32"); r.font.italic = True
    p_find2.add_run("), jauh melampaui kapasitas ")
    r = p_find2.add_run("cache"); r.font.italic = True
    p_find2.add_run(" pada 1 maupun 2 ")
    r = p_find2.add_run("core"); r.font.italic = True
    p_find2.add_run(", dan konvolusi 3x3 hampir tidak memiliki ")
    r = p_find2.add_run("reuse"); r.font.italic = True
    p_find2.add_run(" data yang dapat dimanfaatkan L1 dan L2. Penjelasan yang lebih mungkin adalah biaya awal pada pengukuran 1 ")
    r = p_find2.add_run("core"); r.font.italic = True
    p_find2.add_run(", terutama ")
    r = p_find2.add_run("page fault"); r.font.italic = True
    p_find2.add_run(" pada array keluaran yang baru dialokasikan dan belum pernah disentuh, ditambah jumlah pengulangan yang kecil. Hipotesis ini diuji pada penelitian dengan mengalokasikan dan menyentuh array keluaran sebelum pengukuran, mengulang pengukuran 10 kali, serta melaporkan deviasi standar. Klaim efek ")
    r = p_find2.add_run("cache"); r.font.italic = True
    p_find2.add_run(" hanya akan dipakai jika didukung pembacaan ")
    r = p_find2.add_run("hardware counter"); r.font.italic = True
    p_find2.add_run(".")

    p_find3 = add_p()
    p_find3.add_run("Ketiga, waktu total GPU (0,417 detik) hanya 1,32x lebih cepat dari 1 ")
    r = p_find3.add_run("core"); r.font.italic = True
    p_find3.add_run(" dan sekitar 3,9 kali lebih lambat dari CPU 8 ")
    r = p_find3.add_run("core"); r.font.italic = True
    p_find3.add_run(" (0,107 detik), sedangkan ")
    r = p_find3.add_run("kernel"); r.font.italic = True
    p_find3.add_run(" murni hanya 0,040 detik. Selisih 0,377 detik berasal dari transfer ")
    r = p_find3.add_run("host-to-device"); r.font.italic = True
    p_find3.add_run(" dan ")
    r = p_find3.add_run("device-to-host"); r.font.italic = True
    p_find3.add_run(" untuk sekitar 800 MB data. Laju efektif sekitar 2 GB/s ini jauh di bawah kapasitas teoretis PCIe, sehingga selisih tersebut tidak hanya menunjukkan latensi bus, tetapi juga mencakup penggunaan memori ")
    r = p_find3.add_run("pageable"); r.font.italic = True
    p_find3.add_run(" dan alokasi ")
    r = p_find3.add_run("buffer"); r.font.italic = True
    p_find3.add_run(" perangkat di dalam bagian pengukuran. Pengaruh masing-masing komponen akan diukur terpisah pada penelitian, termasuk pembandingan memori ")
    r = p_find3.add_run("pageable"); r.font.italic = True
    p_find3.add_run(" dan ")
    r = p_find3.add_run("pinned"); r.font.italic = True
    p_find3.add_run(". ")

    p_find4 = add_p()
    p_find4.add_run("Estimasi fraksi paralel dari satu titik (8 ")
    r = p_find4.add_run("core"); r.font.italic = True
    p_find4.add_run(") tidak digunakan sebagai dasar prediksi GPU. Satu titik menyerap seluruh efek non-serial, termasuk keterbatasan ")
    r = p_find4.add_run("bandwidth"); r.font.italic = True
    p_find4.add_run(" memori dan ketidakseragaman ")
    r = p_find4.add_run("core"); r.font.italic = True
    p_find4.add_run(", sehingga nilai P yang diperoleh bukan fraksi serial murni. Selain itu, memasukkan jumlah ")
    r = p_find4.add_run("CUDA cores"); r.font.italic = True
    p_find4.add_run(" sebagai s pada Hukum Amdahl menganggap ")
    r = p_find4.add_run("CUDA core"); r.font.italic = True
    p_find4.add_run(" setara dengan ")
    r = p_find4.add_run("core"); r.font.italic = True
    p_find4.add_run(" CPU, padahal keduanya memiliki arsitektur dan model eksekusi yang berbeda. Pada penelitian, P diestimasi dengan ")
    r = p_find4.add_run("curve fitting"); r.font.italic = True
    p_find4.add_run(" terhadap ")
    r = p_find4.add_run("speedup"); r.font.italic = True
    p_find4.add_run(" pada 2, 4, dan 8 ")
    r = p_find4.add_run("core"); r.font.italic = True
    p_find4.add_run(", dan dilengkapi metrik Karp-Flatt:")

    p_eq_kf = doc.add_paragraph()
    p_eq_kf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_eq_kf.paragraph_format.space_before = Pt(2)
    p_eq_kf.paragraph_format.space_after = Pt(2)
    r_eq_kf = p_eq_kf.add_run("e_p = (1/Sp − 1/p) / (1 − 1/p)        (7)")
    r_eq_kf.font.bold = True

    p_find5 = add_p()
    p_find5.add_run("Nilai e_p yang konstan menunjukkan fraksi serial yang stabil, sedangkan nilai yang naik terhadap p menunjukkan ")
    r = p_find5.add_run("overhead"); r.font.italic = True
    p_find5.add_run(" yang membesar seiring jumlah ")
    r = p_find5.add_run("core"); r.font.italic = True
    p_find5.add_run(". Kecocokan angka antara prediksi Amdahl dan ")
    r = p_find5.add_run("speedup kernel"); r.font.italic = True
    p_find5.add_run(" GPU pada pengujian pendahuluan dipandang sebagai kebetulan numerik, bukan validasi model. Kinerja ")
    r = p_find5.add_run("kernel"); r.font.italic = True
    p_find5.add_run(" GPU pada filter ini juga lebih ditentukan oleh ")
    r = p_find5.add_run("bandwidth"); r.font.italic = True
    p_find5.add_run(" memori global daripada jumlah ")
    r = p_find5.add_run("CUDA cores"); r.font.italic = True
    p_find5.add_run(".")

    # Blok Diagram Arsitektur
    add_h2("Arsitektur Sistem Komputasi Heterogen")
    p_arch = add_p()
    p_arch.add_run("Arsitektur pemrosesan terbagi menjadi dua jalur eksekusi independen yang berlaku untuk seluruh operasi, yaitu filter konvolusi spasial dan operasi ")
    r = p_arch.add_run("upscaling"); r.font.italic = True
    p_arch.add_run(". Pada jalur CPU, data citra yang dimuat ke dalam memori utama dipartisi ke dalam blok baris matriks melalui ")
    r = p_arch.add_run("thread pool"); r.font.italic = True
    p_arch.add_run(" Numba dengan pustaka OpenMP. Setiap ")
    r = p_arch.add_run("core"); r.font.italic = True
    p_arch.add_run(" memproses segmen baris independen tanpa terjadi tabrakan memori (")
    r = p_arch.add_run("race condition"); r.font.italic = True
    p_arch.add_run("), diakhiri dengan sinkronisasi ")
    r = p_arch.add_run("barrier"); r.font.italic = True
    p_arch.add_run(". Pada jalur GPU, data citra ditransfer melalui jalur bus PCIe menuju memori global kartu grafis. Kernel CUDA memetakan piksel citra ke dalam struktur ")
    r = p_arch.add_run("grid of 2D thread blocks"); r.font.italic = True
    p_arch.add_run(" (berukuran 16x16 ")
    r = p_arch.add_run("threads"); r.font.italic = True
    p_arch.add_run(" per blok). Setiap ")
    r = p_arch.add_run("thread"); r.font.italic = True
    p_arch.add_run(" menghitung satu nilai piksel keluaran secara bersamaan sebelum hasilnya disalin kembali ke memori sistem utama. Pada operasi ")
    r = p_arch.add_run("upscaling"); r.font.italic = True
    p_arch.add_run(", setiap ")
    r = p_arch.add_run("thread"); r.font.italic = True
    p_arch.add_run(" menghitung satu piksel pada resolusi target, sehingga ukuran ")
    r = p_arch.add_run("grid"); r.font.italic = True
    p_arch.add_run(" ditentukan oleh dimensi keluaran.")

    # ==========================================
    # BAGIAN 8: METODE PENELITIAN
    # ==========================================
    add_h1("I. METODE PENELITIAN")
    
    p_mp1 = add_p()
    p_mp1.add_run("Metode penelitian yang digunakan adalah metode eksperimental kuantitatif berbasis pengujian tolok ukur (")
    r = p_mp1.add_run("benchmarking"); r.font.italic = True
    p_mp1.add_run(") terkontrol. Tahapan penelitian disusun secara terstruktur sebagai berikut:")

    stages = [
        ("1. Tahap Identifikasi Masalah dan Studi Literatur", "Mengkaji literatur ilmiah mengenai arsitektur heterogen, komputasi paralel GPU CUDA, dan operator spasial pengolahan citra digital."),
        ("2. Tahap Perancangan Lingkungan dan Kernel Komputasi", "Membangun fungsi komputasi konvolusi matriks teroptimasi menggunakan Numba JIT CPU (1, 2, 4, 8 core) serta merancang kernel CUDA 2D berbasis grid dan block."),
        ("3. Tahap Persiapan Dataset Citra Skala Bertingkat", "Menyiapkan dataset citra standar pada resolusi bertingkat 1080p, 4K, dan 8K. Citra diubah ke mode grayscale 8-bit dan diproses sebagai matriks float32 satu kanal. Citra referensi untuk pengujian upscaling disiapkan pada resolusi 1080p, kemudian dipetakan ke 4K dan 8K menggunakan interpolasi Lanczos sebagai referensi."),
        ("4. Tahap Pengujian Empiris dan Pengumpulan Data Benchmark", "Melakukan pengujian komputasi terkontrol dengan mekanisme warm-up run (mengeliminasi latensi kompilasi awal), alokasi dan penyentuhan awal array keluaran sebelum pengukuran, serta 10 kali pengulangan per variasi dengan pelaporan median, rerata, dan deviasi standar. Pada operasi upscaling, dilakukan pula pencatatan MSE dan PSNR untuk setiap metode interpolasi pada setiap konfigurasi pemroses. Aplikasi dasbor digunakan sebagai alat demonstrasi, sedangkan data utama berasal dari skrip benchmark yang menggunakan kernel dan tipe data yang sama."),
        ("5. Tahap Analisis Skalabilitas dan Pemodelan Amdahl", "Menganalisis rasio speedup, efisiensi paralel, fraksi paralel komputasi, dan pemetaan ambang batas transfer data host-to-device PCIe."),
        ("6. Tahap Pengembangan Aplikasi Dasbor Pengujian Interaktif", "Mengintegrasikan modul pengujian ke dalam antarmuka aplikasi web visual interaktif berbasis Streamlit untuk visualisasi komparatif dan ekspor data."),
        ("7. Tahap Penyusunan Laporan dan Publikasi Ilmiah", "Mendokumentasikan seluruh metodologi, temuan empiris, dan pembahasan analitis ke dalam naskah Tugas Akhir dan naskah publikasi berkala ilmiah.")
    ]

    for title, desc in stages:
        p_st = add_p(first_indent=Cm(0.5))
        r_t = p_st.add_run(title + ": "); r_t.font.bold = True
        p_st.add_run(desc)

    add_h2("Diagram Alir Penelitian")
    p_flow = add_p()
    p_flow.add_run("Alur pelaksanaan penelitian Tugas Akhir ini divisualisasikan dalam bagan alir berikut:")
    
    # Textual Flowchart Box
    p_box = doc.add_paragraph()
    p_box.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_box.paragraph_format.space_before = Pt(6)
    p_box.paragraph_format.space_after = Pt(6)
    p_box.paragraph_format.line_spacing = 1.15
    flow_text = (
        "[ Mulai ]\n"
        "   ↓\n"
        "[ Identifikasi Masalah & Studi Literatur ]\n"
        "   ↓\n"
        "[ Perancangan Algoritma: Numba JIT CPU Multi-Core & CUDA Kernel ]\n"
        "   ↓\n"
        "[ Persiapan Dataset Citra Resolusi Bertingkat (1080p, 4K, 8K) ]\n"
        "   ↓\n"
        "[ Eksekusi Warm-up Run (Eliminasi JIT Compilation Overhead) ]\n"
        "   ↓\n"
        "[ Pengujian Benchmark Terkontrol (10x Repetisi per Konfigurasi) ]\n"
        "   ↓\n"
        "[ Ekstraksi Metrik: Waktu Eksekusi, Speedup, Efisiensi, Latensi PCIe, MSE, PSNR ]\n"
        "   ↓\n"
        "[ Analisis Skalabilitas & Pemodelan Hukum Amdahl ]\n"
        "   ↓\n"
        "[ Integrasi ke Aplikasi Dasbor Interaktif Streamlit ]\n"
        "   ↓\n"
        "[ Penyusunan Laporan Tugas Akhir & Validasi Hasil ]\n"
        "   ↓\n"
        "[ Selesai ]"
    )
    r_box = p_box.add_run(flow_text)
    r_box.font.name = 'Consolas'
    r_box.font.size = Pt(10)
    r_box.font.bold = True

    # ==========================================
    # BAGIAN 9: JADWAL PELAKSANAAN PENELITIAN
    # ==========================================
    add_h1("J. JADWAL PELAKSANAAN PENELITIAN")
    p_jd = add_p(first_indent=Cm(0))
    p_jd.add_run("Rencana tahapan pelaksanaan penelitian Tugas Akhir dirancang selama kurun waktu 5 bulan dengan rincian jadwal sebagai berikut:")

    table_jdw = doc.add_table(rows=7, cols=6)
    table_jdw.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_jdw = ["Tahapan Kegiatan Penelitian", "Bulan 1", "Bulan 2", "Bulan 3", "Bulan 4", "Bulan 5"]
    for col_idx, text in enumerate(hdr_jdw):
        cell = table_jdw.cell(0, col_idx)
        cell.text = text
        set_cell_background(cell, "E0E0E0")
        set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in p.runs:
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.font.bold = True

    jdw_data = [
        ["Studi Literatur dan Perumusan Masalah", "✓", "", "", "", ""],
        ["Perancangan Algoritma & Kernel CUDA/JIT", "✓", "✓", "", "", ""],
        ["Pengujian Empiris dan Pengambilan Data Benchmark", "", "✓", "✓", "", ""],
        ["Analisis Skalabilitas dan Hukum Amdahl", "", "", "✓", "✓", ""],
        ["Pengembangan Aplikasi Dasbor Interaktif Streamlit", "", "", "", "✓", "✓"],
        ["Penyusunan Laporan Akhir dan Publikasi Ilmiah", "", "", "", "", "✓"]
    ]

    for row_idx, row_vals in enumerate(jdw_data):
        for col_idx, val in enumerate(row_vals):
            cell = table_jdw.cell(row_idx + 1, col_idx)
            cell.text = val
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(10)

    # ==========================================
    # BAGIAN 10: DAFTAR PUSTAKA (APA 7th MENDELEY)
    # ==========================================
    add_h1("K. DAFTAR PUSTAKA")
    p_dp_intro = add_p(first_indent=Cm(0))
    p_dp_intro.paragraph_format.space_after = Pt(8)
    p_dp_intro.add_run("Seluruh referensi yang digunakan dalam proposal ini merupakan publikasi ilmiah yang memiliki Digital Object Identifier (DOI) aktif serta dapat diakses dan diunduh naskah lengkapnya:")

    references = [
        ("Akasapu, A., Sailaja, V., & Prasad, G. (2021). Implementation of Sobel filter using CUDA. ",
         "IOP Conference Series: Materials Science and Engineering",
         ", 1045(1), 012016. https://doi.org/10.1088/1757-899X/1045/1/012016"),
        
        ("Asaduzzaman, A., Jojigiri, S., Sabu, T., & Tailam, S. (2021). Studying Execution Time and Memory Transfer Time of Image Processing Using GPU Cards. ",
         "2021 IEEE 11th Annual Computing and Communication Workshop and Conference (CCWC)",
         ", 0689-0695. https://doi.org/10.1109/CCWC51732.2021.9376044"),
        
        ("Diana, D., Agustina, D., Situmorang, D. Y., Kholid, D., & Pratama, A. R. (2026). Comparison of Sobel, Prewitt, and Canny Edge Detection Methods in Digital Images. ",
         "Journal of Applied Informatics and Computing (JAIC)",
         ", 10(3), 2424-2430. https://doi.org/10.30871/jaic.v10i3.25101"),

        ("Ruijters, D., & Thévenaz, P. (2012). GPU prefilter for accurate cubic B-spline interpolation. ",
         "The Computer Journal",
         ", 55(1), 15-20. https://doi.org/10.1093/comjnl/bxq086"),

        ("Thévenaz, P., Blu, T., & Unser, M. (2000). Interpolation revisited. ",
         "IEEE Transactions on Medical Imaging",
         ", 19(7), 739-758. https://doi.org/10.1109/42.875199")
    ]

    for part1, journal, part2 in references:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.space_before = Pt(2)
        p_ref.paragraph_format.space_after = Pt(6)
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.left_indent = Cm(1.27)
        p_ref.paragraph_format.first_line_indent = Cm(-1.27) # Hanging indent
        
        r1 = p_ref.add_run(part1)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11)
        
        r2 = p_ref.add_run(journal)
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(11)
        r2.font.italic = True
        
        r3 = p_ref.add_run(part2)
        r3.font.name = 'Times New Roman'
        r3.font.size = Pt(11)

    # ==========================================
    # BAGIAN 11: LAMPIRAN KELENGKAPAN ADMINISTRASI
    # ==========================================
    doc.add_page_break()
    add_h1("L. LAMPIRAN KELENGKAPAN ADMINISTRASI PROPOSAL")
    
    p_lamp = add_p(first_indent=Cm(0))
    p_lamp.add_run("Berdasarkan Buku Panduan Pelaksanaan Tugas Akhir Program Studi Rekayasa Sistem Komputer FMIPA Universitas Tanjungpura (2022), lampiran proposal memuat Lembar Informasi Hasil Studi (LIHS) dan lembar verifikasi calon dosen pembimbing.")

    add_h2("Lembar Rekomendasi Calon Dosen Pembimbing Tugas Akhir")
    p_rek = add_p(first_indent=Cm(0))
    p_rek.paragraph_format.line_spacing = 1.15
    p_rek.add_run("Calon Dosen Pembimbing Utama:\nNama: ........................................................................\nNIP: ............................................................................\nBidang Keahlian: Komputasi Cerdas / Arsitektur Sistem Komputer\nStatus: Bersedia / Tidak Bersedia Membimbing\nTanda Tangan: ................................................................\n\n")
    p_rek.add_run("Calon Dosen Pembimbing Pendamping:\nNama: ........................................................................\nNIP: ............................................................................\nBidang Keahlian: Pengolahan Citra Digital / Jaringan Komputer\nStatus: Bersedia / Tidak Bersedia Membimbing\nTanda Tangan: ................................................................\n\n")
    p_rek.add_run("Mengetahui,\nKetua Jurusan / Ketua Program Studi Rekayasa Sistem Komputer FMIPA UNTAN\n\n\n\n(........................................................................)\nNIP. ....................................................................")

    # Simpan dokumen
    doc.save(filename)
    print(f"File dokumen proposal berhasil dibuat di: {filename}")

if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Proposal_Tugas_Akhir_ReSiskom_Untan.docx")
    create_proposal_document(out_path)
