# Spesifikasi Bahasa HanLang v0.1.0

## 1. Ikhtisar

HanLang adalah bahasa pemrograman interpretatif dengan kata kunci berbahasa Indonesia,
tipe data dinamis, lexical scoping, dan fitur-fitur khas seperti pipeline operator,
data explorer, dan built-in testing.

## 2. Sistem Tipe

HanLang menggunakan **dynamic typing** — tipe diperiksa saat runtime.

### Tipe Primitif

| Tipe | Nama Internal | Contoh | Truthy | Falsy |
|------|---------------|--------|--------|-------|
| Integer | `bilangan` | `42`, `-5`, `0` | `!= 0` | `0` |
| Float | `desimal` | `3.14`, `-0.5` | `!= 0` | `0.0` |
| String | `teks` | `"hello"`, `'world'` | non-empty | `""` |
| Boolean | `boolean` | `Benar`, `Salah` | `Benar` | `Salah` |
| Null | `kosong` | `kosong` | — | selalu falsy |

### Tipe Koleksi

| Tipe | Nama Internal | Contoh | Truthy | Falsy |
|------|---------------|--------|--------|-------|
| List | `daftar` | `[1, 2, 3]` | non-empty | `[]` |
| Map | `peta` | `{"a": 1}` | non-empty | `{}` |

### Tipe Callable

| Tipe | Nama Internal |
|------|---------------|
| Function | `fungsi` |
| Lambda | `lambda` |
| Builtin | `fungsi_bawaan` |
| Module | `modul` |

## 3. Leksik

### Kata Kunci

```
tetapkan    konstan     jika        jika_tidak_jika
jika_tidak  fungsi      kembali     ulangi
untuk       selama      dalam       berhenti
lanjut      dan         atau        bukan
coba        tangkap     akhirnya    impor
dari        kelas       diri        uji
pastikan    jelajahi    cocokkan    pola
lainnya
```

### Literal Boolean & Null

```
Benar       Salah       kosong
```

### Operator (urut dari prioritas terendah ke tertinggi)

| Prioritas | Operator | Asosiasi | Deskripsi |
|-----------|----------|----------|-----------|
| 1 | `\|>` | Kiri | Pipeline |
| 2 | `atau` | Kiri | Logical OR |
| 3 | `dan` | Kiri | Logical AND |
| 4 | `bukan` | Unary | Logical NOT |
| 5 | `==` `!=` `<` `>` `<=` `>=` | Kiri | Perbandingan |
| 6 | `+` `-` | Kiri | Penjumlahan, pengurangan |
| 7 | `*` `/` `//` `%` | Kiri | Perkalian, pembagian |
| 8 | `**` | Kanan | Pangkat |
| 9 | `-x` `+x` | Unary | Unary plus/minus |
| 10 | `()` `[]` `.` | Kiri | Call, index, access |

### String

- Double-quoted: `"hello {nama}"` — mendukung interpolation
- Single-quoted: `'hello'` — tanpa interpolation
- Escape: `\n` `\t` `\r` `\\` `\"` `\'` `\{` `\}` `\0`

### Komentar

```han
# Ini adalah komentar satu baris
```

## 4. Deklarasi Variabel

```han
tetapkan nama = ekspresi    # variabel, bisa diubah
konstan NAMA = ekspresi     # konstanta, tidak bisa diubah
nama = ekspresi             # assignment (variabel harus sudah ada)
```

Compound assignment: `+=` `-=` `*=` `/=`

## 5. Kontrol Alur

### Kondisi

```han
jika kondisi {
    ...
} jika_tidak_jika kondisi {
    ...
} jika_tidak {
    ...
}
```

### Loop

```han
ulangi untuk var dalam iterable { ... }
ulangi selama kondisi { ... }
untuk var dalam iterable { ... }
```

Loop control: `berhenti` (break), `lanjut` (continue)

Batas iterasi: 1.000.000 (safeguard terhadap infinite loop)

### Pattern Matching

```han
cocokkan ekspresi {
    pola nilai1 { ... }
    pola nilai2 { ... }
    lainnya { ... }
}
```

## 6. Fungsi

```han
fungsi nama(param1, param2) {
    kembali ekspresi
}
```

- Lexical scoping dengan closure
- Batas rekursi: 500 panggilan
- Lambda: `x => ekspresi` atau `(a, b) => ekspresi`

## 7. Error Handling

```han
coba {
    ...
} tangkap variabel_error {
    # variabel_error.pesan — pesan error
    # variabel_error.kode — kode error
} akhirnya {
    # selalu dijalankan
}
```

## 8. Import

```han
impor nama_modul
nama_modul.fungsi(args)
nama_modul.atribut
```

## 9. Pipeline Operator

```han
data |> fungsi(args)        # data diinjeksi sebagai argumen pertama
data |> saring(predicate)   # filter
data |> ubah(transform)     # map
data |> f |> g |> h         # chaining
```

## 10. Kode Error

| Kode | Kategori | Deskripsi |
|------|----------|-----------|
| H100 | Lexer | Error umum tokenisasi |
| H101 | Lexer | String tidak ditutup |
| H102 | Lexer | Karakter tidak valid |
| H103 | Lexer | Format angka tidak valid |
| H200 | Parser | Error umum parsing |
| H201 | Parser | Token tidak diharapkan |
| H202 | Parser | Token yang diharapkan tidak ditemukan |
| H300 | Runtime | Error umum runtime |
| H301 | Runtime | Variabel tidak ditemukan |
| H302 | Runtime | Tipe tidak cocok |
| H303 | Runtime | Pembagian dengan nol |
| H304 | Runtime | Jumlah argumen salah |
| H305 | Runtime | Batas rekursi terlampaui |
| H306 | Runtime | Indeks diluar jangkauan |
| H307 | Runtime | Kunci tidak ditemukan |
| H308 | Runtime | Variabel read-only |
| H309 | Runtime | Modul tidak ditemukan |
| H310 | Runtime | Batas loop terlampaui |
