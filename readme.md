<p align="center">
  <img src="docs/logo.jpg" alt="HanLang Logo" width="220">
</p>

<h1 align="center">HanLang</h1>
<p align="center">
  <strong>Bahasa Pemrograman Modern Berbasis Bahasa Indonesia yang Ekspresif, Aman, dan Berdiri Sendiri.</strong>
</p>

<p align="center">
  <a href="#ikhtisar--filosofi">Ikhtisar</a> •
  <a href="#arsitektur-runtime-sampai-akar-akarnya">Arsitektur Runtime</a> •
  <a href="#spesifikasi-lengkap-bahasa">Spesifikasi Bahasa</a> •
  <a href="#fitur-khas--unggulan">Fitur Unggulan</a> •
  <a href="#standard-library--fungsi-bawaan">Standard Library</a> •
  <a href="#kode-diagnostik--error">Kode Error</a> •
  <a href="#cli--binary-mandiri-standalone">CLI & Binary Mandiri</a> •
  <a href="#vs-code--ide-extension">VS Code Extension</a>
</p>

---

## 📖 Ikhtisar & Filosofi

**HanLang** adalah bahasa pemrograman tingkat tinggi berparadigma imperatif dan fungsional dengan kata kunci alami berbahasa Indonesia. HanLang dirancang untuk memadukan **kemudahan pembacaan (readability)** bagi pengembang dan pembelajar dengan **ketegasan logika bahasa modern** (seperti Pipeline Operator dari Elixir/F#, Data Explorer terstruktur, dan Built-in Testing tanpa framework luar).

### 🎯 Prinsip Desain Inti
1. **Ekspresif & Terbaca**: Sintaks menyerupai logika percakapan terstruktur, meminimalkan simbol ambigu tanpa mengorbankan performa.
2. **Safe Defaults & Predictable**: Variabel harus dideklarasikan secara eksplisit (`tetapkan` / `konstan`). Tidak ada *implicit global leakage*.
3. **Helpful Diagnostics (Rust-Style)**: Pesan kesalahan tidak sekadar mencetak *stack trace*, melainkan menunjukkan lokasi berkas, nomor baris & kolom, cuplikan kode asli dengan penunjuk visual `^`, serta saran perbaikan konkrit.
4. **Mandiri (Standalone First)**: HanLang dapat diinstal sebagai package global (`han`), dijalankan sebagai native executable mandiri (`dist/han.exe`) tanpa ketergantungan pada runtime Python luar, dan dilengkapi extension resmi VS Code.

---

## ⚙️ Arsitektur Runtime: "Sampai Akar-akarnya"

HanLang dibangun dengan arsitektur modular yang memisahkan tahap pemindaian leksikal, parsing AST, analisis semantik statik, hingga eksekusi runtime dengan *lexical scope environment*.

```
   Kode Sumber (.han)
           │
           ▼
┌───────────────────────┐
│     1. Lexer          │ ──▶ Token Stream (TokenType, Lexeme, SourceLocation)
└───────────────────────┘
           │
           ▼
┌───────────────────────┐
│     2. Parser         │ ──▶ Abstract Syntax Tree (AST Nodes)
└───────────────────────┘     (Recursive Descent + Precedence Climbing)
           │
           ▼
┌───────────────────────┐
│  3. Semantic Analyzer │ ──▶ Static Validation (Scope, Const Mutation, Return/Loop Context)
└───────────────────────┘
           │
           ▼
┌───────────────────────┐
│  4. Tree-Walking      │ ──▶ Lexical Environment Chains + Call Frames
│     Interpreter       │ ──▶ Built-in Modules & Dynamic Dispatch
└───────────────────────┘
           │
           ▼
      Output / I/O
```

### 1. Lexical Analysis (Pemindaian Token) — `lexer.py`, `tokens.py`
- **Source Location Tracker**: Setiap token menyertakan objek `SourceLocation(file, line, column, length)` yang dipertahankan sampai runtime untuk diagnosa kesalahan presisi tinggi.
- **Komentar Multi-Gaya**: Mendukung komentar satu baris (`#` dan `//`) serta blok multi-baris (`/* ... */`).
- **Dynamic String Interpolation Scanner**: Tokenizer mendeteksi pola interpolasi `{...}` di dalam string kutip ganda (`"`), secara otomatis memecah literal string dan ekspresi tertanam menjadi token terpisah untuk dievaluasi dinamis saat runtime.
- **Number Parsing**: Mendukung bilangan bulat (*integer*) basis 10, heksadesimal (`0x`), pecahan desimal (*float*), dan notasi ilmiah (`1e-5`).

### 2. Syntactic Analysis (Parsing & AST) — `parser.py`, `nodes.py`
- **Recursive Descent Parser**: Mengurai pernyataan majemuk, blok kurung kurawal `{ ... }`, deklarasi fungsi, kondisi, perulangan, dan blok pengujian.
- **Pratt Precedence Climbing**: Menangani ekspresi matematika, logika, dan operator rantai dengan tabel presedensi hierarkis 10 tingkat untuk memastikan urutan evaluasi matematis yang tepat.
- **AST Node Hierarchy**: Node direpresentasikan sebagai struktur kelas typed (`ProgramNode`, `VarDeclNode`, `BinaryOpNode`, `PipelineNode`, `MatchNode`, `TryCatchNode`, `JelajahiNode`, dll.).

### 3. Analisis Semantik Statik — `semantic.py`
Sebelum kode dieksekusi, AST melewati tahap validasi semantik:
- **Deteksi Mutasi Konstanta**: Mencegah penugasan ulang terhadap identifier yang dideklarasikan dengan `konstan`.
- **Validasi Alur Kontrol**: Memastikan `kembali` hanya berada di dalam fungsi, serta `berhenti` (*break*) dan `lanjut` (*continue*) hanya berada di dalam loop.
- **Peringatan Identifier**: Memberikan peringatan dini jika ada variabel yang dideklarasikan namun tidak pernah digunakan.

### 4. Sistem Runtime & Environment Scoping — `runtime.py`
- **Lexical Environment Chains**: Setiap blok (`{ ... }`) dan fungsi membuat objek `Environment` baru yang merujuk ke `parent` scope-nya. Pencarian variabel berjalan naik (*walk-up*) melalui rantai lingkup hingga scope global.
- **First-Class Functions & Closures**: Objek `HanFunction` menyimpan referensi lingkup saat fungsi didefinisikan (`closure_env`). Variabel luar tetap hidup di dalam fungsi meskipun fungsi induk telah selesai dieksekusi.
- **Signal-Based Control Flow**: Pernyataan `kembali`, `berhenti`, dan `lanjut` diimplementasikan secara internal menggunakan sinyal khusus (`ReturnSignal`, `BreakSignal`, `ContinueSignal`) yang ditangkap tepat pada batas blok yang bersangkutan.
- **Batas Keamanan Terpasang (Guardrails)**:
  - **Recursion Limit**: Maksimal **500 pemanggilan** rekursif. Melebihi ini akan memicu error `H305 (RecursionLimitError)` untuk mencegah stack overflow.
  - **Loop Iteration Limit**: Maksimal **1.000.000 iterasi** per loop. Mencegah freeze tak terbatas (*infinite loop*) akibat bug logika dengan memicu `H310 (LoopLimitError)`.

### 5. Sistem Tipe & Memori — `values.py`
Semua entitas data dibungkus dalam turunan `HanValue` dengan metode standar (`type_name()`, `to_display()`, `to_boolean()`):
- `HanNumber`: Representasi bilangan bulat (`bilangan`) atau desimal (`desimal`).
- `HanString`: Teks UTF-8 dengan metode manipulasi bawaan.
- `HanBoolean`: Nilai kebenaran `Benar` atau `Salah`.
- `HanNull`: Nilai hampa `kosong`.
- `HanList`: Array dinamis (`daftar`) yang mendukung pengindeksan negatif (`list[-1]`), slicing, dan operasi pipeline.
- `HanMap`: Key-value dictionary (`peta`) dengan akses kurung siku `map["kunci"]` maupun dot notation `map.kunci`.
- `HanFunction` & `HanLambda`: Entitas pemanggil (*callables*).
- `HanModule`: Namespace modul terisolasi.

### 6. Sistem Diagnostik Error (Rust-Style) — `errors.py`
Ketika terjadi kesalahan (baik pada tahap leksikal, parsing, semantik, maupun runtime), HanLang memformat output diagnostik dengan ANSI color:
```
HanLang Kesalahan Sintaks [H201]
Token tidak diharapkan: '}'

  --> program.han:12:5
   |
12 |     }
   |     ^
   |
Bantuan: Pastikan tanda kurung kurawal buka '{' dan tutup '}' seimbang.
```

---

## 📚 Spesifikasi Lengkap Bahasa HanLang

### 1. Sistem Tipe Data

| Kategori | Tipe di HanLang | Nama Tipe | Contoh Literal | Nilai Truthy | Nilai Falsy |
|:---|:---|:---|:---|:---|:---|
| **Numerik** | Integer | `bilangan` | `42`, `-10`, `0xFF` | Selain `0` | `0` |
| **Numerik** | Float | `desimal` | `3.14`, `-0.001`, `1e5` | Selain `0.0` | `0.0` |
| **Teks** | String | `teks` | `"Halo"`, `'Dunia'` | String tidak kosong | `""` |
| **Logika** | Boolean | `boolean` | `Benar`, `Salah` | `Benar` | `Salah` |
| **Ketiadaan** | Null | `kosong` | `kosong` | — | Selalu Falsy |
| **Koleksi** | List | `daftar` | `[1, "dua", Benar]` | List tidak kosong | `[]` |
| **Koleksi** | Map | `peta` | `{"nama": "Han", "umur": 20}` | Map tidak kosong | `{}` |
| **Pemanggil**| Function | `fungsi` | `fungsi(x) { kembali x }` | Selalu Truthy | — |

---

### 2. Deklarasi Variabel & Konstanta

```han
# 1. Variabel biasa (dapat diubah nilainya)
tetapkan skor = 100
skor = skor + 25
skor += 10          # Compound assignment: +=, -=, *=, /=

# 2. Konstanta (tidak dapat diubah setelah inisialisasi)
konstan GRAVITASI = 9.80665
konstan APLIKASI = "HanLang Engine"

# 3. String Interpolation (hanya kutip ganda)
tetapkan pengguna = "Kenzy"
tampil("Halo, {pengguna}! Skor akhir kamu: {skor}")

# 4. Escape Sequences
tampil("Baris satu\nBaris dua\tTabulasi\nSimbol: \" \{ \}")
```

---

### 3. Operator & Presedensi Matematis

Tabel urutan evaluasi dari prioritas terendah ke tertinggi:

| Tingkat | Operator | Asosiatif | Kategori | Penjelasan |
|:---:|:---|:---:|:---|:---|
| **1** | `\|>` | Kiri | Pipeline | Mengalirkan data sebagai argumen pertama |
| **2** | `atau` | Kiri | Logika | OR Logis (`a atau b`) |
| **3** | `dan` | Kiri | Logika | AND Logis (`a dan b`) |
| **4** | `bukan` | Unary | Logika | NOT Logis (`bukan Benar` -> `Salah`) |
| **5** | `==`, `!=`, `<`, `>`, `<=`, `>=` | Kiri | Relasional | Perbandingan kesetaraan dan nilai |
| **6** | `+`, `-` | Kiri | Aritmatika | Penjumlahan & Pengurangan |
| **7** | `*`, `/`, `//`, `%` | Kiri | Aritmatika | Perkalian, Pembagian, Floor Div, Modulo |
| **8** | `**` | Kanan | Eksponensial | Pangkat (`2 ** 8` -> `256`) |
| **9** | `-x`, `+x` | Unary | Tanda | Negasi numerik |
| **10**| `()`, `[]`, `.` | Kiri | Akses | Pemanggilan fungsi, indeks array/map, atribut |

---

### 4. Kontrol Alur (Control Flow)

#### Percabangan Kondisional
```han
tetapkan nilai = 85

jika nilai >= 90 {
    tampil("Grade: A (Luar biasa!)")
} jika_tidak_jika nilai >= 75 {
    tampil("Grade: B (Bagus)")
} jika_tidak {
    tampil("Grade: C (Perlu perbaikan)")
}
```

#### Perulangan
```han
# Loop Rentang / List (Untuk)
ulangi untuk item dalam ["apel", "jeruk", "mangga"] {
    tampil("Buah: {item}")
}

# Loop Selama (While)
tetapkan counter = 5
ulangi selama counter > 0 {
    tampil("Hitung mundur: {counter}")
    counter -= 1
}

# Kontrol Loop
ulangi untuk i dalam rentang(1, 20) {
    jika i % 2 == 0 {
        lanjut        # Lanjut ke iterasi berikutnya
    }
    jika i > 10 {
        berhenti      # Berhenti dari loop
    }
    tampil("Angka ganjil: {i}")
}
```

#### Pattern Matching (`cocokkan`)
```han
tetapkan status_code = 404

cocokkan status_code {
    pola 200 { tampil("Sukses: OK") }
    pola 403 { tampil("Error: Dilarang Masuk") }
    pola 404 { tampil("Error: Halaman Tidak Ditemukan") }
    pola 500 { tampil("Error: Masalah Server") }
    lainnya  { tampil("Status tidak dikenal") }
}
```

---

### 5. Fungsi & Closure

```han
# Fungsi dengan nama
fungsi hitung_luas_segitiga(alas, tinggi) {
    kembali (alas * tinggi) / 2
}
tampil("Luas: {hitung_luas_segitiga(10, 6)}")

# Fungsi Anonim / Lambda (Arrow Syntax)
tetapkan kuadrat = x => x * x
tampil("5 kuadrat = {kuadrat(5)}")

tetapkan kali = (a, b) => a * b
tampil("3 x 4 = {kali(3, 4)}")

# Closure (Menyimpan State Lingkup Luar)
fungsi pembuat_penambah(n) {
    kembali x => x + n
}
tetapkan tambah_sepuluh = pembuat_penambah(10)
tampil("25 + 10 = {tambah_sepuluh(25)}") # Output: 35
```

---

## 🌟 Fitur Khas & Unggulan

### 1. Pipeline Operator (`|>`)
Menghilangkan struktur bersarang yang sulit dibaca. Nilai di sisi kiri operator secara otomatis disuntikkan sebagai **argumen pertama** ke fungsi di sisi kanan:

```han
# Kode Bersarang Tradisional:
# tampil(urutkan(saring(rentang(1, 10), x => x % 2 == 0)))

# Dengan HanLang Pipeline:
rentang(1, 10)
    |> saring(x => x % 2 == 0)
    |> ubah(x => x * 10)
    |> urutkan
    |> tampil

# Output: [20, 40, 60, 80, 100]
```

### 2. Data Explorer (`jelajahi`)
Fitur bawaan untuk inspeksi visual hierarki data kompleks (list dan map bertingkat) ke format pohon ASCII yang elegan:

```han
tetapkan proyek = {
    "nama": "HanLang Engine",
    "versi": 1,
    "tim": ["Arsitek", "Runtime", "Tooling"],
    "konfigurasi": {
        "debug": Benar,
        "max_threads": 4
    }
}

jelajahi proyek
```

**Output:**
```
┌─ peta (4 pasangan)
├─ "nama" = teks "HanLang Engine"
├─ "versi" = bilangan 1
├─ "tim":
│   ┌─ daftar (3 elemen)
│   ├─ [0] teks = "Arsitek"
│   ├─ [1] teks = "Runtime"
│   └─ [2] teks = "Tooling"
└─ "konfigurasi":
    ┌─ peta (2 pasangan)
    ├─ "debug" = boolean Benar
    └─ "max_threads" = bilangan 4
```

### 3. Built-in Testing Framework (`uji` & `pastikan`)
Menulis test case langsung tanpa membutuhkan test-runner eksternal:

```han
uji "Kalkulasi Matematika Dasar" {
    pastikan 10 + 5 == 15
    pastikan 2 ** 3 == 8
    pastikan bukan (5 < 2)
}

uji "Manipulasi String" {
    tetapkan nama = "hanlang"
    pastikan panjang(nama) == 7
}
```

Jalankan langsung dengan perintah:
```powershell
han test program.han
```

### 4. Robust Error Handling (`coba`-`tangkap`-`akhirnya`)
```han
coba {
    tetapkan angka = bilangan("bukan_angka")
    tetapkan hasil = 10 / 0
} tangkap e {
    tampil("Tertangkap Error!")
    tampil("Kode Error : {e.kode}")
    tampil("Pesan Error: {e.pesan}")
} akhirnya {
    tampil("Operasi pembersihan selesai.")
}
```

---

## 📦 Standard Library & Fungsi Bawaan

### 1. Fungsi Global (Built-in Tanpa Perlu `impor`)

| Fungsi | Tanda Tangan | Penjelasan Singkat |
|:---|:---|:---|
| `tampil` | `tampil(nilai...)` | Mencetak satu atau beberapa nilai ke konsol standar |
| `masukan`| `masukan([prompt])`| Membaca satu baris teks dari input pengguna |
| `bilangan` | `bilangan(val)` | Mengubah nilai menjadi bilangan bulat (*integer*) |
| `desimal` | `desimal(val)` | Mengubah nilai menjadi pecahan desimal (*float*) |
| `teks` | `teks(val)` | Mengubah nilai apapun menjadi representasi string |
| `boolean` | `boolean(val)` | Mengevaluasi truthiness nilai ke `Benar` atau `Salah` |
| `tipe` | `tipe(val)` | Menghasilkan nama tipe string (`"bilangan"`, `"daftar"`, dll.) |
| `adalah` | `adalah(val, tipe)` | Memeriksa apakah nilai bertipe tertentu (`adalah(5, "bilangan")`) |
| `panjang`| `panjang(koleksi)` | Mendapatkan jumlah elemen pada list/map atau karakter string |
| `rentang`| `rentang([awal,] akhir [, langkah])` | Menghasilkan list angka urut |
| `tambah` | `tambah(daftar, item)` | Menambahkan elemen baru ke akhir list |
| `hapus` | `hapus(koleksi, kunci)` | Menghapus elemen dari list berdasarkan indeks atau map berdasarkan kunci |
| `gabung` | `gabung(daftar [, pemisah])` | Menggabungkan list string menjadi satu teks |
| `pisah` | `pisah(teks [, pemisah])` | Memecah teks menjadi list string berdasarkan delimiter |
| `urutkan`| `urutkan(daftar)` | Mengurutkan list secara ascending |
| `balik` | `balik(daftar)` | Membalik urutan elemen dalam list |
| `berisi` | `berisi(koleksi, item)` | Mengecek apakah elemen ada dalam list atau kunci ada dalam map |
| `kunci` | `kunci(peta)` | Mengambil seluruh kunci dalam map sebagai list |
| `nilai` | `nilai(peta)` | Mengambil seluruh value dalam map sebagai list |
| `abs` | `abs(angka)` | Menghasilkan nilai mutlak absolut |
| `bulat` | `bulat(angka [, digit])` | Membulatkan pecahan desimal |
| `min` | `min(args...)` | Mendapatkan nilai terkecil |
| `max` | `max(args...)` | Mendapatkan nilai terbesar |
| `saring` | `saring(daftar, fungsi)` | Menyaring list berdasarkan predikat fungsi |
| `ubah` | `ubah(daftar, fungsi)` | Mentransformasikan setiap elemen list dengan fungsi pemeta |

---

### 2. Modul Standar (`impor <nama_modul>`)

#### `impor math`
- `math.pi`, `math.e`, `math.inf`
- `math.akar(x)`: Menghitung akar kuadrat.
- `math.pangkat(x, y)`: Menghitung $x^y$.
- `math.lantai(x)`: Pembulatan ke bawah (*floor*).
- `math.langit(x)`: Pembulatan ke atas (*ceiling*).
- `math.log(x [, basis])`: Logaritma natural atau basis tertentu.
- `math.sin(rad)`, `math.cos(rad)`, `math.tan(rad)`: Fungsi trigonometri.

#### `impor text`
- `text.huruf_besar(s)`: Mengubah string ke UPPERCASE.
- `text.huruf_kecil(s)`: Mengubah string ke lowercase.
- `text.potong(s)`: Menghapus spasi di awal dan akhir (*trim*).
- `text.awalan(s, pref)`: Memeriksa apakah teks diawali substring tertentu.
- `text.akhiran(s, suff)`: Memeriksa apakah teks diakhiri substring tertentu.
- `text.ganti(s, lama, baru)`: Mengganti semua kemunculan substring.
- `text.cari(s, target)`: Menemukan indeks pertama substring (-1 jika tidak ditemukan).

#### `impor list`
- `list.buat(args...)`: Membuat list baru dari argumen yang diberikan.
- `list.kosong(l)`: Memeriksa apakah list berukuran 0.
- `list.datar(l)`: Meratakan list bersarang (*flatten*).
- `list.unik(l)`: Menghapus duplikat elemen dalam list.
- `list.iris(l, mulai, akhir)`: Memotong sub-list (*slice*).

#### `impor file`
- `file.baca(path)`: Membaca seluruh isi berkas sebagai teks UTF-8.
- `file.tulis(path, isi)`: Menuliskan teks ke dalam berkas.
- `file.ada(path)`: Memeriksa keberadaan berkas di filesystem.

#### `impor json`
- `json.parse(str)`: Melakukan parsing string JSON menjadi struktur data HanLang (`peta` / `daftar`).
- `json.stringify(val [, indent])`: Mengubah struktur data HanLang menjadi string format JSON rapi.

#### `impor time`
- `time.sekarang()`: Menghasilkan Unix timestamp presisi desimal.
- `time.tunggu(detik)`: Menghentikan eksekusi sementara (*sleep*).
- `time.format([format])`: Menghasilkan string waktu terbaca manusia.

#### `impor random`
- `random.acak()`: Bilangan desimal acak $0.0 \le x < 1.0$.
- `random.acak_bilangan(min, max)`: Bilangan bulat acak dalam rentang.
- `random.pilih(daftar)`: Memilih satu elemen acak dari list.
- `random.kocok(daftar)`: Mengacak urutan elemen list (*shuffle*).

#### `impor system`
- `system.os`: Nama sistem operasi runtime (`"Windows"`, `"Linux"`, `"Darwin"`).
- `system.versi_hanlang`: Versi runtime HanLang aktif.
- `system.versi_python`: Versi interpreter Python penyokong.
- `system.args()`: Mengambil list argumen baris perintah CLI.
- `system.keluar([kode])`: Menghentikan eksekusi program segera.

#### `impor test`
- `test.sama(a, b)`: Memastikan nilai $a == b$.
- `test.bukan_sama(a, b)`: Memastikan nilai $a \ne b$.
- `test.benar(val)`: Memastikan nilai berstatus truthy.

---

## 🚨 Kode Diagnostik & Error Lengkap

HanLang mengelompokkan kode kesalahan untuk memudahkan identifikasi dan debugging:

| Kode | Kategori | Nama Error | Deskripsi Masalah |
|:---:|:---:|:---|:---|
| `H100` | **Lexer** | `LexerError` | Kesalahan umum pemindaian token |
| `H101` | **Lexer** | `UnterminatedStringError` | String kutip tidak ditutup hingga akhir baris |
| `H102` | **Lexer** | `InvalidCharacterError` | Karakter ilegal/tidak dikenal dalam alfabet bahasa |
| `H103` | **Lexer** | `InvalidNumberError` | Format penulisan angka tidak valid |
| `H200` | **Parser**| `ParseError` | Kesalahan umum penyusunan tata bahasa |
| `H201` | **Parser**| `UnexpectedTokenError` | Menemukan token yang tidak sesuai aturan gramatika |
| `H202` | **Parser**| `ExpectedTokenError` | Token yang wajib (seperti `}`) tidak ditemukan |
| `H300` | **Runtime**| `RuntimeError_` | Kesalahan umum saat eksekusi program |
| `H301` | **Runtime**| `UndefinedVariableError` | Mengakses variabel yang belum dideklarasikan |
| `H302` | **Runtime**| `TypeMismatchError` | Operasi pada dua tipe data yang tidak kompatibel |
| `H303` | **Runtime**| `DivisionByZeroError` | Pembagian numerik atau modulo dengan nol (`/ 0`) |
| `H304` | **Runtime**| `ArgumentError` | Jumlah argumen pemanggilan fungsi tidak cocok |
| `H305` | **Runtime**| `RecursionLimitError` | Batas kedalaman pemanggilan fungsi (500) terlampaui |
| `H306` | **Runtime**| `IndexOutOfRangeError` | Mengakses indeks list di luar panjang elemen |
| `H307` | **Runtime**| `KeyNotFoundError` | Kunci tidak ditemukan di dalam objek map |
| `H308` | **Runtime**| `ReadOnlyError` | Mencoba mengubah nilai konstanta (`konstan`) |
| `H309` | **Runtime**| `ImportError_` | Modul yang diimpor tidak ditemukan atau gagal dimuat |
| `H310` | **Runtime**| `LoopLimitError` | Loop melebihi batas pengaman 1.000.000 iterasi |

---

## 💻 CLI & Binary Mandiri (Standalone)

HanLang dapat digunakan tanpa perlu menyertakan perintah `python` di depan CLI:

### 1. Perintah CLI Utama
```powershell
han run program.han        # Eksekusi berkas HanLang
han program.han            # Jalan pintas eksekusi langsung
han repl                   # Membuka REPL shell interaktif
han check program.han      # Validasi sintaks statik tanpa menjalankan kode
han test program.han       # Menjalankan blok pengujian (uji { ... })
han format program.han     # Memformat ulang kode sumber menjadi rapi
han explain program.han    # Menjalankan kode dengan log eksekusi bertahap
han --version              # Informasi versi HanLang
han --help                 # Menampilkan panduan bantuan lengkap
```

### 2. Binary Native Mandiri (`dist/han.exe`)
Untuk lingkungan produksi tanpa instalasi Python, tersedia executable native mandiri:
```powershell
# Langsung jalankan file biner native:
.\dist\han.exe run program.han
```
Untuk meng-compile ulang executable mandiri ini di Windows:
```powershell
pyinstaller --noconfirm --onefile --name han --clean han.py
```

### 3. Distribusi Python Wheel (PyPI Ready)
Paket resmi dapat di-build menjadi `.whl` dan `.tar.gz` yang siap dipublikasikan ke PyPI:
```powershell
python -m build
pip install dist/hanlang-0.1.0-py3-none-any.whl
```

---

## 🧩 VS Code & Antigravity IDE Extension

Ekstensi resmi **HanLang** tersedia di folder [`vscode-hanlang/`](vscode-hanlang/) dan telah dikemas ke dalam berkas [`hanlang-0.1.0.vsix`](vscode-hanlang/hanlang-0.1.0.vsix).

### Fitur Ekstensi:
- 🎨 **Full Syntax Highlighting**: Pewarnaan presisi untuk kata kunci bahasa Indonesia, operator, string interpolation, komentar blok, dan tipe data.
- 💡 **IntelliSense & Autocomplete**: Rekomendasi otomatis cerdas untuk seluruh kata kunci dan 40+ fungsi bawaan serta dokumentasi modul.
- 📖 **Signature Help & Hover Docs**: Menampilkan panduan parameter aktif dan dokumentasi markdown saat kursor diarahkan ke fungsi atau keyword.
- ✂️ **22 Code Snippets**: Template cepat untuk `fungsi`, `jika`, `jika_tidak`, `ulangi`, `coba`, `uji`, `cocokkan`, dan koleksi data.
- ▶️ **One-Click Run**:
  - Tombol **$(play) HanLang** di status bar bawah.
  - Shortcut keyboard cepat: `Ctrl + Shift + R` (Run File) dan `Ctrl + Shift + C` (Check Syntax).
- 📁 **Custom File Icon**: Ikon berkas `.han` resmi bertema dark-tech geometric cyan/blue.

### Cara Memasang Ekstensi (.vsix):
1. Buka Command Palette di VS Code / Antigravity IDE (`Ctrl + Shift + P`).
2. Ketik dan pilih: **`Extensions: Install from VSIX...`**
3. Arahkan dan pilih berkas: `vscode-hanlang/hanlang-0.1.0.vsix`.
4. Muat ulang (*reload*) window IDE.

---

## 🚀 Contoh Program Nyata

### Algoritma Bilangan Prima & Pipeline
```han
# Fungsi pengecekan bilangan prima
fungsi adalah_prima(n) {
    jika n <= 1 { kembali Salah }
    jika n <= 3 { kembali Benar }
    jika n % 2 == 0 atau n % 3 == 0 { kembali Salah }

    tetapkan i = 5
    ulangi selama i * i <= n {
        jika n % i == 0 atau n % (i + 2) == 0 {
            kembali Salah
        }
        i += 6
    }
    kembali Benar
}

tampil("=== 10 Bilangan Prima Pertama ===")
rentang(1, 30)
    |> saring(adalah_prima)
    |> tampil
```

### Pemrosesan Data & JSON Terstruktur
```han
impor json
impor text

tetapkan raw_json = '{"nama": "kenzy", "nilai": [80, 95, 90]}'
tetapkan data = json.parse(raw_json)

# Transformasi nama ke huruf besar
data["nama"] = text.huruf_besar(data["nama"])

# Hitung rata-rata
tetapkan total = 0
ulangi untuk skor dalam data["nilai"] {
    total += skor
}
data["rata_rata"] = total / panjang(data["nilai"])

# Tampilkan hasil
jelajahi data
tampil("JSON Hasil:")
tampil(json.stringify(data, 2))
```

---

## 🗺️ Roadmap Pengembangan

### v0.1.0 (Versi Saat Ini — Alpha)
- [x] Core Syntax: Variabel, konstanta, fungsi, closure, arrow lambdas.
- [x] Control Flow: `jika`/`kalau`, `ulangi untuk`, `ulangi selama`, `cocokkan`.
- [x] Struktur Data: `daftar` (list) dinamis & `peta` (hash map) fleksibel.
- [x] Operator Pipeline `|>` & Data Explorer `jelajahi`.
- [x] Error Handling kuat: `coba` - `tangkap` - `akhirnya`.
- [x] Standard Library lengkap: `math`, `text`, `list`, `file`, `json`, `time`, `random`, `system`, `test`.
- [x] CLI mandiri: `run`, `check`, `test`, `repl`, `format`, `explain`.
- [x] Native standalone binary (`dist/han.exe`) & launcher scripts.
- [x] Ekstensi VS Code / Antigravity IDE resmi (`.vsix`).

### v0.2.0 (Direncanakan)
- [ ] Object-Oriented Programming (`kelas`, `konstruktor`, metode, warisan).
- [ ] Modul kustom buatan pengguna (`dari modul impor fungsi`).
- [ ] Multiline String literal (triple quotes `"""..."""`).
- [ ] Sintaks rentang ekspresif (`1..100`).
- [ ] Destructuring assignment untuk list dan map.

### v0.3.0 & v1.0.0 (Masa Depan)
- [ ] Bytecode compilation & HanLang Virtual Machine (VM) khusus.
- [ ] Package manager terdistribusi (`han install <package>`).
- [ ] Language Server Protocol (LSP) mandiri terintegrasi.
- [ ] Compiler self-hosting & kompilasi langsung ke native binary machine code.

---

## 📄 Lisensi

HanLang didistribusikan di bawah lisensi terbuka [MIT License](LICENSE). Bebas digunakan, dipelajari, dimodifikasi, dan didistribusikan untuk keperluan pendidikan maupun komersial.

<p align="center">
  Dibuat dengan ❤️ untuk kemajuan ekosistem bahasa pemrograman Indonesia.
</p>
