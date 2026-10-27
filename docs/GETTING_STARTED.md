# Panduan Memulai HanLang

## Prasyarat

- **Python 3.9+** sudah terinstal
- Terminal (PowerShell, CMD, atau Bash)

## Instalasi

### Cara 1: Langsung (Tanpa Install)

```powershell
# Download atau clone proyek
cd C:\path\to\HanLang

# Jalankan program
python han.py run program.han
```

### Cara 2: Install sebagai Package

```powershell
cd C:\path\to\HanLang
pip install -e .

# Sekarang perintah 'han' tersedia
han run program.han
```

### Cara 3: Buat Alias (PowerShell)

```powershell
# Tambahkan ke profil PowerShell
Set-Alias han "python C:\path\to\HanLang\han.py"

# Sekarang bisa langsung
han run program.han
han --version
han repl
```

## Program Pertama

Buat file `hello.han`:

```han
tampil("Selamat datang di HanLang! 🎉")
```

Jalankan:

```powershell
python han.py run hello.han
```

## Tutorial 5 Menit

### 1. Variabel

```han
tetapkan nama = "Kenzy"
tetapkan umur = 25
tetapkan aktif = Benar

tampil("Nama: {nama}, Umur: {umur}")
```

### 2. Kondisi

```han
tetapkan nilai = 85

jika nilai >= 90 {
    tampil("A")
} jika_tidak_jika nilai >= 80 {
    tampil("B")
} jika_tidak {
    tampil("C")
}
```

### 3. Loop

```han
# Hitung 1 sampai 5
ulangi untuk i dalam rentang(1, 6) {
    tampil(i)
}

# Iterasi list
tetapkan buah = ["apel", "jeruk", "mangga"]
untuk b dalam buah {
    tampil(b)
}
```

### 4. Fungsi

```han
fungsi salam(nama) {
    kembali "Halo, {nama}!"
}

tampil(salam("Dunia"))
```

### 5. Koleksi

```han
# List
tetapkan angka = [5, 3, 1, 4, 2]
tampil(urutkan(angka))

# Map
tetapkan user = {"nama": "Kenzy", "level": 5}
tampil(user.nama)
```

### 6. Error Handling

```han
coba {
    tetapkan hasil = bilangan("bukan_angka")
} tangkap error {
    tampil("Terjadi error: {error.pesan}")
}
```

### 7. Pipeline

```han
tetapkan data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

tetapkan genap = data |> saring(x => x % 2 == 0)
tampil(genap)  # [2, 4, 6, 8, 10]
```

## Langkah Selanjutnya

1. Lihat contoh di folder `examples/`
2. Baca [Spesifikasi Bahasa](LANGUAGE_SPEC.md)
3. Coba shell interaktif: `python han.py repl`
4. Jelajahi [Standard Library](STANDARD_LIBRARY.md)
