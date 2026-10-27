# Changelog

Semua perubahan penting dalam proyek HanLang didokumentasikan di sini.

## [0.1.0] — 2026-10-25

### Ditambahkan

#### Inti Bahasa
- Lexer lengkap dengan dukungan string interpolation, escape sequence, dan komentar
- Parser recursive-descent dengan operator precedence penuh
- AST (Abstract Syntax Tree) untuk semua konstruksi bahasa
- Runtime interpreter dengan tree-walking execution
- Semantic analyzer untuk validasi statis

#### Tipe Data
- Bilangan (integer dan desimal/float)
- Teks (string) dengan interpolation `{expr}`
- Boolean (`Benar` / `Salah`)
- Null (`kosong`)
- Daftar (list) dengan indexing dan methods
- Peta (map/dictionary) dengan dot access

#### Kontrol Alur
- `jika` / `jika_tidak_jika` / `jika_tidak` (if/elif/else)
- `ulangi untuk ... dalam` (for loop)
- `ulangi selama` (while loop)
- `untuk ... dalam` (for-in loop)
- `berhenti` (break) dan `lanjut` (continue)
- `cocokkan` / `pola` / `lainnya` (pattern matching)

#### Fungsi
- Deklarasi fungsi dengan `fungsi`
- Parameter dan return values (`kembali`)
- Rekursi dengan batas kedalaman
- Closure dan lexical scoping
- Lambda expressions (`x => x + 1`)

#### Fitur Khas
- Pipeline operator (`|>`) dengan `saring` dan `ubah`
- Data explorer (`jelajahi`) untuk inspeksi nilai
- Built-in test runner (`uji` / `pastikan`)
- String interpolation dalam double-quoted strings

#### Error Handling
- `coba` / `tangkap` / `akhirnya` (try/catch/finally)
- Error diagnostik bergaya Rust dengan kode error
- Source location tracking (file, baris, kolom)
- Saran perbaikan dalam pesan error

#### Standard Library
- `math` — fungsi matematika
- `text` — pemrosesan string
- `list` — utilitas koleksi
- `file` — baca/tulis file
- `json` — parse dan stringify JSON
- `time` — waktu dan tanggal
- `random` — nilai acak
- `system` — informasi runtime
- `test` — assertions

#### CLI
- `han run` — jalankan program
- `han check` — periksa syntax
- `han test` — jalankan test
- `han repl` — shell interaktif
- `han format` — format kode
- `han --version` dan `han --help`

#### Testing
- 157 unit tests (lexer, parser, runtime)
- Semua tests lulus

#### Dokumentasi
- README lengkap
- Spesifikasi bahasa
- Panduan memulai
- Dokumentasi standard library
- 6 contoh program
