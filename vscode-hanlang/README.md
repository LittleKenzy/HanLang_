# HanLang — VS Code Extension

**Dukungan lengkap untuk bahasa pemrograman HanLang di Visual Studio Code.**

## Fitur

### 🎨 Syntax Highlighting
- Semua kata kunci HanLang disorot dengan benar
- Fungsi bawaan dibedakan dari fungsi user-defined
- String interpolation `"{expr}"` disorot
- Angka, boolean, dan null disorot
- Operator pipeline `|>` dan arrow `=>` disorot
- Komentar `#` disorot

### 💡 Autocomplete & IntelliSense
- **Keyword completion** — semua kata kunci HanLang
- **Built-in functions** — tampil, panjang, rentang, dll.
- **Module members** — ketik `math.` untuk lihat semua fungsi math
- **Signature help** — bantuan parameter saat mengetik `(`
- **Hover info** — arahkan mouse ke keyword/function untuk info
- **User symbols** — variabel dan fungsi yang didefinisikan di file

### ✂️ Code Snippets
- `hl-hello` — Hello World
- `tetapkan` — Deklarasi variabel
- `jika` — Kondisi if
- `hl-ifelse` — Kondisi if/else
- `fungsi` — Deklarasi fungsi
- `hl-for` — Loop for
- `coba` — Error handling
- `impor` — Import modul
- `cocokkan` — Pattern matching
- `uji` — Test block
- Dan 10+ snippet lainnya!

### ▶️ Jalankan Langsung
- **Ctrl+Shift+R** — Jalankan file `.han` saat ini
- **Ctrl+Shift+C** — Periksa syntax
- Klik kanan → HanLang: Jalankan/Periksa
- Tombol ▶ di title bar editor

### 📁 File Icon
- Ikon khusus `.han` di Explorer dan tab editor
- Aktifkan tema ikon: File → Preferences → File Icon Theme → HanLang File Icons

### ⚙️ Editing Experience
- Auto-close brackets `{ }`, `[ ]`, `( )`
- Auto-close quotes `" "`, `' '`
- Komentar toggle dengan Ctrl+/
- Indentasi otomatis setelah `{`
- Code folding

## Instalasi

### Dari File VSIX (Offline)
1. Download file `hanlang-0.1.0.vsix`
2. Buka VS Code
3. Ctrl+Shift+P → "Extensions: Install from VSIX..."
4. Pilih file VSIX
5. Restart VS Code

### Dari Source
```bash
cd vscode-hanlang
npm install
npx @vscode/vsce package --allow-missing-repository
# File hanlang-0.1.0.vsix akan dibuat
code --install-extension hanlang-0.1.0.vsix
```

## Konfigurasi

| Setting | Default | Deskripsi |
|---------|---------|-----------|
| `hanlang.interpreterCommand` | `""` (auto-detect) | Path ke interpreter HanLang |
| `hanlang.extraArgs` | `""` | Argumen tambahan |
| `hanlang.runInTerminal` | `true` | Jalankan di terminal (true) atau output (false) |

### Contoh Konfigurasi
```json
{
    "hanlang.interpreterCommand": "python C:/Bilal_Projects/Hanlang/han.py",
    "hanlang.runInTerminal": true
}
```

## Keyboard Shortcuts

| Shortcut | Perintah |
|----------|----------|
| `Ctrl+Shift+R` | Jalankan file HanLang |
| `Ctrl+Shift+C` | Periksa syntax |
| `Ctrl+/` | Toggle komentar |

## Screenshot

Buka file `.han` untuk melihat:
- Syntax highlighting berwarna
- Autocomplete saat mengetik
- Snippet dengan tab stops
- Tombol Run di title bar

## Persyaratan

- VS Code 1.75.0 atau lebih baru
- Python 3.9+ (untuk menjalankan interpreter)
- Proyek HanLang harus ada di workspace atau path dikonfigurasi

## Changelog

### 0.1.0
- Rilis awal
- Syntax highlighting untuk semua konstruksi HanLang
- 25+ code snippets
- Autocomplete untuk keywords, builtins, dan modules
- Signature help dan hover info
- Perintah Run dan Check
- File icon dan icon theme
- Keybinding dan context menu

## Lisensi

MIT
