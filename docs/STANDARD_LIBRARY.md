# Standard Library HanLang

Semua modul diimpor dengan `impor nama_modul`.

---

## math

Fungsi dan konstanta matematika.

```han
impor math
```

| Anggota | Tipe | Deskripsi | Contoh |
|---------|------|-----------|--------|
| `math.pi` | desimal | Nilai π | `3.14159...` |
| `math.e` | desimal | Nilai e | `2.71828...` |
| `math.inf` | desimal | Infinity | `inf` |
| `math.akar(x)` | fungsi | Akar kuadrat | `math.akar(144)` → `12` |
| `math.pangkat(x, y)` | fungsi | x pangkat y | `math.pangkat(2, 10)` → `1024` |
| `math.lantai(x)` | fungsi | Floor | `math.lantai(3.7)` → `3` |
| `math.langit(x)` | fungsi | Ceiling | `math.langit(3.2)` → `4` |
| `math.log(x[, base])` | fungsi | Logaritma | `math.log(100, 10)` → `2` |
| `math.sin(x)` | fungsi | Sinus | `math.sin(0)` → `0` |
| `math.cos(x)` | fungsi | Cosinus | `math.cos(0)` → `1` |
| `math.tan(x)` | fungsi | Tangen | `math.tan(0)` → `0` |

---

## text

Pemrosesan string.

```han
impor text
```

| Fungsi | Deskripsi | Contoh |
|--------|-----------|--------|
| `text.huruf_besar(s)` | Ubah ke huruf besar | `"hello"` → `"HELLO"` |
| `text.huruf_kecil(s)` | Ubah ke huruf kecil | `"HELLO"` → `"hello"` |
| `text.potong(s)` | Hapus spasi awal/akhir | `" hi "` → `"hi"` |
| `text.awalan(s, prefix)` | Cek awalan | `text.awalan("hello", "he")` → `Benar` |
| `text.akhiran(s, suffix)` | Cek akhiran | `text.akhiran("hello", "lo")` → `Benar` |
| `text.ganti(s, old, new)` | Ganti substring | `text.ganti("hello", "l", "r")` → `"herro"` |
| `text.cari(s, sub)` | Cari posisi | `text.cari("hello", "ll")` → `2` |

---

## list

Utilitas koleksi.

```han
impor list
```

| Fungsi | Deskripsi | Contoh |
|--------|-----------|--------|
| `list.buat(args...)` | Buat list dari argumen | `list.buat(1, 2, 3)` → `[1, 2, 3]` |
| `list.kosong(l)` | Cek apakah list kosong | `list.kosong([])` → `Benar` |
| `list.datar(l)` | Flatten nested list | `list.datar([[1,2],[3]])` → `[1,2,3]` |
| `list.unik(l)` | Hapus duplikat | `list.unik([1,1,2])` → `[1,2]` |
| `list.iris(l, start, end)` | Slice list | `list.iris([1,2,3,4], 1, 3)` → `[2,3]` |

---

## file

Operasi file (sandboxed).

```han
impor file
```

| Fungsi | Deskripsi | Contoh |
|--------|-----------|--------|
| `file.baca(path)` | Baca file sebagai string | `file.baca("data.txt")` |
| `file.tulis(path, content)` | Tulis string ke file | `file.tulis("out.txt", "hello")` |
| `file.ada(path)` | Cek apakah file ada | `file.ada("config.json")` → `Benar` |

---

## json

JSON parsing dan serialization.

```han
impor json
```

| Fungsi | Deskripsi | Contoh |
|--------|-----------|--------|
| `json.parse(str)` | Parse JSON string | `json.parse('{"a":1}')` → peta |
| `json.stringify(val[, indent])` | Ubah ke JSON string | `json.stringify(data, 2)` |

---

## time

Waktu dan tanggal.

```han
impor time
```

| Fungsi | Deskripsi | Contoh |
|--------|-----------|--------|
| `time.sekarang()` | Timestamp saat ini | `1729853400.123` |
| `time.tunggu(detik)` | Pause eksekusi | `time.tunggu(1)` |
| `time.format([fmt])` | Format waktu | `time.format()` → `"2026-10-25 17:00:00"` |

---

## random

Nilai acak.

```han
impor random
```

| Fungsi | Deskripsi | Contoh |
|--------|-----------|--------|
| `random.acak()` | Float acak 0-1 | `0.7234...` |
| `random.acak_bilangan(min, max)` | Integer acak | `random.acak_bilangan(1, 100)` |
| `random.pilih(list)` | Pilih elemen acak | `random.pilih(["a", "b", "c"])` |
| `random.kocok(list)` | Kocok urutan list | `random.kocok([1, 2, 3])` |

---

## system

Informasi runtime.

```han
impor system
```

| Anggota | Tipe | Deskripsi |
|---------|------|-----------|
| `system.os` | teks | Nama OS (`"Windows"`, `"Linux"`, dll.) |
| `system.versi_python` | teks | Versi Python |
| `system.versi_hanlang` | teks | Versi HanLang |
| `system.args()` | fungsi | Argumen command line |
| `system.keluar([code])` | fungsi | Keluar program |

---

## test

Assertions untuk testing.

```han
impor test
```

| Fungsi | Deskripsi |
|--------|-----------|
| `test.sama(a, b)` | Assert `a == b` |
| `test.bukan_sama(a, b)` | Assert `a != b` |
| `test.benar(val)` | Assert `val` truthy |

---

## Fungsi Bawaan (Tanpa Import)

Fungsi-fungsi ini tersedia langsung tanpa `impor`:

| Fungsi | Deskripsi |
|--------|-----------|
| `tampil(args...)` | Cetak ke stdout |
| `masukan([prompt])` | Baca input dari stdin |
| `bilangan(val)` | Konversi ke number |
| `teks(val)` | Konversi ke string |
| `desimal(val)` | Konversi ke float |
| `boolean(val)` | Konversi ke boolean |
| `tipe(val)` | Dapatkan nama tipe |
| `adalah(val, type)` | Cek tipe |
| `panjang(val)` | Panjang string/list/map |
| `rentang([start,] end [, step])` | Buat list angka |
| `tambah(list, val)` | Append ke list |
| `hapus(coll, key)` | Hapus dari list/map |
| `gabung(list [, sep])` | Join list ke string |
| `pisah(str [, sep])` | Split string ke list |
| `urutkan(list)` | Urutkan list |
| `balik(list)` | Balik urutan list |
| `berisi(coll, val)` | Cek keberadaan |
| `kunci(map)` | Dapatkan semua kunci |
| `nilai(map)` | Dapatkan semua nilai |
| `abs(x)` | Nilai absolut |
| `bulat(x [, digits])` | Pembulatan |
| `min(args...)` | Nilai minimum |
| `max(args...)` | Nilai maksimum |
| `saring(list, func)` | Filter list |
| `ubah(list, func)` | Map function ke list |
