"use strict";

const vscode = require("vscode");
const path = require("path");
const cp = require("child_process");
const fs = require("fs");

// ═══════════════════════════════════════════════════════════════════
//  HanLang VS Code Extension
//  Provides syntax highlighting, autocomplete, snippets, and
//  integrated execution for the HanLang programming language.
// ═══════════════════════════════════════════════════════════════════

/** @type {vscode.OutputChannel} */
let outputChannel;

/**
 * Extension activation entry point.
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    outputChannel = vscode.window.createOutputChannel("HanLang");

    // ── Register commands ────────────────────────────────────────
    context.subscriptions.push(
        vscode.commands.registerCommand("hanlang.runFile", () => runHanLangFile("run")),
        vscode.commands.registerCommand("hanlang.checkFile", () => runHanLangFile("check")),
        vscode.commands.registerCommand("hanlang.showOutput", () => outputChannel.show(true)),
        vscode.commands.registerCommand("hanlang.openDocs", openDocumentation),
    );

    // ── Register completion provider ─────────────────────────────
    const completionProvider = vscode.languages.registerCompletionItemProvider(
        { language: "hanlang", scheme: "file" },
        new HanLangCompletionProvider(),
        ".", // trigger after dot for module members
    );
    context.subscriptions.push(completionProvider);

    // ── Register signature help provider ─────────────────────────
    const signatureProvider = vscode.languages.registerSignatureHelpProvider(
        { language: "hanlang", scheme: "file" },
        new HanLangSignatureHelpProvider(),
        "(", ","
    );
    context.subscriptions.push(signatureProvider);

    // ── Register hover provider ──────────────────────────────────
    const hoverProvider = vscode.languages.registerHoverProvider(
        { language: "hanlang", scheme: "file" },
        new HanLangHoverProvider()
    );
    context.subscriptions.push(hoverProvider);

    // ── Status bar ───────────────────────────────────────────────
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Left, 100
    );
    statusBarItem.text = "$(play) HanLang";
    statusBarItem.tooltip = "Jalankan file HanLang saat ini";
    statusBarItem.command = "hanlang.runFile";
    context.subscriptions.push(statusBarItem);

    // Show status bar only for .han files
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor && editor.document.languageId === "hanlang") {
                statusBarItem.show();
            } else {
                statusBarItem.hide();
            }
        })
    );

    // Check on activation
    const editor = vscode.window.activeTextEditor;
    if (editor && editor.document.languageId === "hanlang") {
        statusBarItem.show();
    }

    outputChannel.appendLine("HanLang extension activated.");
}

/**
 * Deactivate the extension.
 */
function deactivate() {
    if (outputChannel) {
        outputChannel.dispose();
    }
}

// ═══════════════════════════════════════════════════════════════════
//  Command: Run / Check HanLang File
// ═══════════════════════════════════════════════════════════════════

/**
 * Run or check the current HanLang file.
 * @param {"run" | "check"} mode
 */
function runHanLangFile(mode) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showWarningMessage("Tidak ada file yang terbuka.");
        return;
    }

    const document = editor.document;
    if (document.languageId !== "hanlang") {
        vscode.window.showWarningMessage("File ini bukan file HanLang (.han).");
        return;
    }

    // Save the file first
    document.save().then(() => {
        const filePath = document.fileName;
        const config = vscode.workspace.getConfiguration("hanlang");

        // Resolve the interpreter
        const resolved = resolveInterpreter(config, filePath);
        if (!resolved) return;

        const extraArgs = (config.get("extraArgs", "") || "").trim();
        const useTerminal = config.get("runInTerminal", true);

        if (useTerminal) {
            // Run in integrated terminal
            const termName = "HanLang";
            let terminal = vscode.window.terminals.find(t => t.name === termName);
            if (!terminal) {
                terminal = vscode.window.createTerminal({ name: termName });
            }
            terminal.show(true);

            // Construct terminal command safely
            let cmd;
            if (resolved.type === "command") {
                cmd = `${resolved.bin} ${mode} "${filePath}"`;
            } else if (resolved.type === "python") {
                cmd = `python "${resolved.script}" ${mode} "${filePath}"`;
            } else if (resolved.type === "binary") {
                // In PowerShell, quoted binary paths need the '&' call operator
                cmd = `& "${resolved.bin}" ${mode} "${filePath}"`;
            }

            if (extraArgs) {
                cmd += ` ${extraArgs}`;
            }

            terminal.sendText(cmd);
        } else {
            // Run in output channel
            outputChannel.clear();
            outputChannel.show(true);
            outputChannel.appendLine(`[HanLang] ${mode === "run" ? "Menjalankan" : "Memeriksa"}: ${filePath}`);
            outputChannel.appendLine("─".repeat(60));

            let spawnCmd;
            let spawnArgs = [];

            if (resolved.type === "command") {
                spawnCmd = resolved.bin;
                spawnArgs = [mode, filePath];
            } else if (resolved.type === "python") {
                spawnCmd = "python";
                spawnArgs = [resolved.script, mode, filePath];
            } else if (resolved.type === "binary") {
                spawnCmd = resolved.bin;
                spawnArgs = [mode, filePath];
            }

            if (extraArgs) {
                spawnArgs.push(...extraArgs.split(/\s+/));
            }

            const child = cp.spawn(spawnCmd, spawnArgs, {
                cwd: path.dirname(filePath),
                shell: true,
            });

            child.stdout.on("data", (data) => {
                outputChannel.append(data.toString());
            });

            child.stderr.on("data", (data) => {
                outputChannel.append(data.toString());
            });

            child.on("close", (code) => {
                outputChannel.appendLine("");
                outputChannel.appendLine("─".repeat(60));
                if (code === 0) {
                    outputChannel.appendLine(`[HanLang] ✓ Selesai (exit code: ${code})`);
                } else {
                    outputChannel.appendLine(`[HanLang] ✗ Gagal (exit code: ${code})`);
                }
            });

            child.on("error", (err) => {
                outputChannel.appendLine(`[HanLang] Error: ${err.message}`);
                vscode.window.showErrorMessage(
                    `Gagal menjalankan HanLang: ${err.message}. Instal: pip install -e . (dari folder HanLang)`
                );
            });
        }
    });
}

/**
 * Resolve the HanLang interpreter.
 * Returns an object describing how to invoke HanLang.
 * @param {vscode.WorkspaceConfiguration} config
 * @param {string} filePath
 * @returns {{ type: "command" | "binary" | "python", bin?: string, script?: string } | null}
 */
function resolveInterpreter(config, filePath) {
    const customCmd = (config.get("interpreterCommand", "") || "").trim();

    if (customCmd) {
        return { type: "command", bin: customCmd };
    }

    // Priority 1: Standalone `han` command on PATH (from pip install or global install)
    try {
        cp.execSync("han --version", { stdio: "pipe", timeout: 3000 });
        return { type: "command", bin: "han" };
    } catch (_) {
        // han not found on PATH
    }

    // Priority 2: Standalone binary dist/han.exe or han.exe in workspace
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders) {
        for (const folder of workspaceFolders) {
            const distExe = path.join(folder.uri.fsPath, "dist", "han.exe");
            if (fs.existsSync(distExe)) {
                return { type: "binary", bin: distExe };
            }
            const rootExe = path.join(folder.uri.fsPath, "han.exe");
            if (fs.existsSync(rootExe)) {
                return { type: "binary", bin: rootExe };
            }
            const hanPy = path.join(folder.uri.fsPath, "han.py");
            if (fs.existsSync(hanPy)) {
                return { type: "python", script: hanPy };
            }
        }
    }

    // Priority 3: Walk up directory tree from the file being run
    let dir = path.dirname(filePath);
    for (let i = 0; i < 5; i++) {
        const distExe = path.join(dir, "dist", "han.exe");
        if (fs.existsSync(distExe)) {
            return { type: "binary", bin: distExe };
        }
        const hanPy = path.join(dir, "han.py");
        if (fs.existsSync(hanPy)) {
            return { type: "python", script: hanPy };
        }
        const parent = path.dirname(dir);
        if (parent === dir) break;
        dir = parent;
    }

    vscode.window.showErrorMessage(
        "Tidak dapat menemukan interpreter HanLang. " +
        "Instal dengan: pip install -e . (dari folder HanLang), " +
        "atau atur path di Settings: hanlang.interpreterCommand"
    );
    return null;
}

/**
 * Open HanLang documentation.
 */
function openDocumentation() {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders) {
        const root = workspaceFolders[0].uri.fsPath;
        const docsPath = path.join(root, "docs", "GETTING_STARTED.md");
        const readmePath = path.join(root, "README.md");

        if (fs.existsSync(docsPath)) {
            vscode.commands.executeCommand("markdown.showPreview", vscode.Uri.file(docsPath));
            return;
        }

        if (fs.existsSync(readmePath)) {
            vscode.commands.executeCommand("markdown.showPreview", vscode.Uri.file(readmePath));
            return;
        }
    }

    vscode.window.showInformationMessage("Dokumentasi HanLang tidak ditemukan di workspace.");
}

// ═══════════════════════════════════════════════════════════════════
//  Autocomplete Provider
// ═══════════════════════════════════════════════════════════════════

/** @type {Array<{label: string, kind: number, detail: string, documentation: string, insertText?: string}>} */
const KEYWORDS = [
    { label: "tetapkan", kind: 14, detail: "Keyword", documentation: "Deklarasi variabel — tetapkan nama = nilai" },
    { label: "konstan", kind: 14, detail: "Keyword", documentation: "Deklarasi konstanta — konstan NAMA = nilai" },
    { label: "jika", kind: 14, detail: "Keyword", documentation: "Kondisi — jika kondisi { ... }" },
    { label: "jika_tidak_jika", kind: 14, detail: "Keyword", documentation: "Else-if — jika_tidak_jika kondisi { ... }" },
    { label: "jika_tidak", kind: 14, detail: "Keyword", documentation: "Else — jika_tidak { ... }" },
    { label: "fungsi", kind: 14, detail: "Keyword", documentation: "Deklarasi fungsi — fungsi nama(params) { ... }" },
    { label: "kembali", kind: 14, detail: "Keyword", documentation: "Return dari fungsi — kembali nilai" },
    { label: "ulangi", kind: 14, detail: "Keyword", documentation: "Loop — ulangi untuk/selama ..." },
    { label: "untuk", kind: 14, detail: "Keyword", documentation: "For loop — untuk var dalam iterable { ... }" },
    { label: "selama", kind: 14, detail: "Keyword", documentation: "While loop — selama kondisi { ... }" },
    { label: "dalam", kind: 14, detail: "Keyword", documentation: "Operator in — untuk x dalam data" },
    { label: "berhenti", kind: 14, detail: "Keyword", documentation: "Break dari loop" },
    { label: "lanjut", kind: 14, detail: "Keyword", documentation: "Continue ke iterasi berikutnya" },
    { label: "dan", kind: 14, detail: "Operator Logika", documentation: "Logical AND" },
    { label: "atau", kind: 14, detail: "Operator Logika", documentation: "Logical OR" },
    { label: "bukan", kind: 14, detail: "Operator Logika", documentation: "Logical NOT" },
    { label: "coba", kind: 14, detail: "Keyword", documentation: "Try — coba { ... } tangkap e { ... }" },
    { label: "tangkap", kind: 14, detail: "Keyword", documentation: "Catch — tangkap error { ... }" },
    { label: "akhirnya", kind: 14, detail: "Keyword", documentation: "Finally — akhirnya { ... }" },
    { label: "impor", kind: 14, detail: "Keyword", documentation: "Import modul — impor math" },
    { label: "uji", kind: 14, detail: "Keyword", documentation: "Test block — uji \"nama\" { pastikan ... }" },
    { label: "pastikan", kind: 14, detail: "Keyword", documentation: "Assert — pastikan ekspresi" },
    { label: "jelajahi", kind: 14, detail: "Keyword", documentation: "Data explorer — jelajahi data" },
    { label: "cocokkan", kind: 14, detail: "Keyword", documentation: "Pattern matching — cocokkan x { pola ... }" },
    { label: "pola", kind: 14, detail: "Keyword", documentation: "Match case — pola nilai { ... }" },
    { label: "lainnya", kind: 14, detail: "Keyword", documentation: "Default case — lainnya { ... }" },
    { label: "Benar", kind: 21, detail: "Boolean", documentation: "Nilai boolean true" },
    { label: "Salah", kind: 21, detail: "Boolean", documentation: "Nilai boolean false" },
    { label: "kosong", kind: 21, detail: "Null", documentation: "Nilai null/kosong" },
];

/** @type {Array<{label: string, detail: string, documentation: string, signature: string}>} */
const BUILTINS = [
    { label: "tampil", detail: "Fungsi Bawaan", documentation: "Cetak nilai ke stdout", signature: "tampil(nilai...)" },
    { label: "masukan", detail: "Fungsi Bawaan", documentation: "Baca input dari user", signature: "masukan([prompt])" },
    { label: "bilangan", detail: "Konversi Tipe", documentation: "Konversi ke integer", signature: "bilangan(nilai)" },
    { label: "teks", detail: "Konversi Tipe", documentation: "Konversi ke string", signature: "teks(nilai)" },
    { label: "desimal", detail: "Konversi Tipe", documentation: "Konversi ke float", signature: "desimal(nilai)" },
    { label: "boolean", detail: "Konversi Tipe", documentation: "Konversi ke boolean", signature: "boolean(nilai)" },
    { label: "tipe", detail: "Fungsi Bawaan", documentation: "Dapatkan nama tipe", signature: "tipe(nilai)" },
    { label: "adalah", detail: "Fungsi Bawaan", documentation: "Cek tipe nilai", signature: "adalah(nilai, tipe)" },
    { label: "panjang", detail: "Koleksi", documentation: "Panjang string/list/map", signature: "panjang(koleksi)" },
    { label: "rentang", detail: "Koleksi", documentation: "Buat daftar angka berurutan", signature: "rentang([mulai,] akhir [, langkah])" },
    { label: "tambah", detail: "Koleksi", documentation: "Tambah elemen ke list", signature: "tambah(daftar, nilai)" },
    { label: "hapus", detail: "Koleksi", documentation: "Hapus elemen dari list/map", signature: "hapus(koleksi, kunci)" },
    { label: "gabung", detail: "Koleksi", documentation: "Gabung list jadi string", signature: "gabung(daftar [, pemisah])" },
    { label: "pisah", detail: "Koleksi", documentation: "Pisah string jadi list", signature: "pisah(teks [, pemisah])" },
    { label: "urutkan", detail: "Koleksi", documentation: "Urutkan list", signature: "urutkan(daftar)" },
    { label: "balik", detail: "Koleksi", documentation: "Balik urutan list", signature: "balik(daftar)" },
    { label: "berisi", detail: "Koleksi", documentation: "Cek apakah koleksi berisi nilai", signature: "berisi(koleksi, nilai)" },
    { label: "kunci", detail: "Koleksi", documentation: "Dapatkan semua kunci map", signature: "kunci(peta)" },
    { label: "nilai", detail: "Koleksi", documentation: "Dapatkan semua nilai map", signature: "nilai(peta)" },
    { label: "abs", detail: "Matematika", documentation: "Nilai absolut", signature: "abs(angka)" },
    { label: "bulat", detail: "Matematika", documentation: "Pembulatan", signature: "bulat(angka [, digit])" },
    { label: "min", detail: "Matematika", documentation: "Nilai minimum", signature: "min(a, b, ...)" },
    { label: "max", detail: "Matematika", documentation: "Nilai maksimum", signature: "max(a, b, ...)" },
    { label: "saring", detail: "Pipeline", documentation: "Filter list berdasarkan kondisi", signature: "saring(daftar, fungsi)" },
    { label: "ubah", detail: "Pipeline", documentation: "Map/transform setiap elemen", signature: "ubah(daftar, fungsi)" },
];

const MODULE_MEMBERS = {
    math: [
        { label: "pi", detail: "desimal", documentation: "Nilai π (3.14159...)" },
        { label: "e", detail: "desimal", documentation: "Nilai e (2.71828...)" },
        { label: "inf", detail: "desimal", documentation: "Infinity" },
        { label: "akar", detail: "fungsi", documentation: "Akar kuadrat — math.akar(x)", signature: "akar(angka)" },
        { label: "pangkat", detail: "fungsi", documentation: "Pangkat — math.pangkat(x, y)", signature: "pangkat(basis, eksponen)" },
        { label: "lantai", detail: "fungsi", documentation: "Floor — math.lantai(x)", signature: "lantai(angka)" },
        { label: "langit", detail: "fungsi", documentation: "Ceiling — math.langit(x)", signature: "langit(angka)" },
        { label: "log", detail: "fungsi", documentation: "Logaritma", signature: "log(angka [, basis])" },
        { label: "sin", detail: "fungsi", documentation: "Sinus", signature: "sin(radian)" },
        { label: "cos", detail: "fungsi", documentation: "Cosinus", signature: "cos(radian)" },
        { label: "tan", detail: "fungsi", documentation: "Tangen", signature: "tan(radian)" },
    ],
    text: [
        { label: "huruf_besar", detail: "fungsi", documentation: "Ubah ke huruf besar", signature: "huruf_besar(teks)" },
        { label: "huruf_kecil", detail: "fungsi", documentation: "Ubah ke huruf kecil", signature: "huruf_kecil(teks)" },
        { label: "potong", detail: "fungsi", documentation: "Hapus spasi awal/akhir", signature: "potong(teks)" },
        { label: "awalan", detail: "fungsi", documentation: "Cek awalan string", signature: "awalan(teks, prefix)" },
        { label: "akhiran", detail: "fungsi", documentation: "Cek akhiran string", signature: "akhiran(teks, suffix)" },
        { label: "ganti", detail: "fungsi", documentation: "Ganti substring", signature: "ganti(teks, lama, baru)" },
        { label: "cari", detail: "fungsi", documentation: "Cari posisi substring", signature: "cari(teks, sub)" },
    ],
    list: [
        { label: "buat", detail: "fungsi", documentation: "Buat list dari argumen", signature: "buat(args...)" },
        { label: "kosong", detail: "fungsi", documentation: "Cek apakah list kosong", signature: "kosong(daftar)" },
        { label: "datar", detail: "fungsi", documentation: "Flatten nested list", signature: "datar(daftar)" },
        { label: "unik", detail: "fungsi", documentation: "Hapus duplikat", signature: "unik(daftar)" },
        { label: "iris", detail: "fungsi", documentation: "Slice list", signature: "iris(daftar, mulai, akhir)" },
    ],
    file: [
        { label: "baca", detail: "fungsi", documentation: "Baca isi file", signature: "baca(path)" },
        { label: "tulis", detail: "fungsi", documentation: "Tulis ke file", signature: "tulis(path, isi)" },
        { label: "ada", detail: "fungsi", documentation: "Cek apakah file ada", signature: "ada(path)" },
    ],
    json: [
        { label: "parse", detail: "fungsi", documentation: "Parse JSON string", signature: "parse(teks_json)" },
        { label: "stringify", detail: "fungsi", documentation: "Konversi ke JSON string", signature: "stringify(nilai [, indent])" },
    ],
    time: [
        { label: "sekarang", detail: "fungsi", documentation: "Timestamp saat ini", signature: "sekarang()" },
        { label: "tunggu", detail: "fungsi", documentation: "Pause eksekusi", signature: "tunggu(detik)" },
        { label: "format", detail: "fungsi", documentation: "Format waktu", signature: "format([fmt])" },
    ],
    random: [
        { label: "acak", detail: "fungsi", documentation: "Float acak 0-1", signature: "acak()" },
        { label: "acak_bilangan", detail: "fungsi", documentation: "Integer acak dalam rentang", signature: "acak_bilangan(min, max)" },
        { label: "pilih", detail: "fungsi", documentation: "Pilih elemen acak", signature: "pilih(daftar)" },
        { label: "kocok", detail: "fungsi", documentation: "Kocok urutan list", signature: "kocok(daftar)" },
    ],
    system: [
        { label: "os", detail: "teks", documentation: "Nama sistem operasi" },
        { label: "versi_python", detail: "teks", documentation: "Versi Python runtime" },
        { label: "versi_hanlang", detail: "teks", documentation: "Versi HanLang" },
        { label: "args", detail: "fungsi", documentation: "Argumen command line", signature: "args()" },
        { label: "keluar", detail: "fungsi", documentation: "Keluar program", signature: "keluar([kode])" },
    ],
    test: [
        { label: "sama", detail: "fungsi", documentation: "Assert a == b", signature: "sama(a, b)" },
        { label: "bukan_sama", detail: "fungsi", documentation: "Assert a != b", signature: "bukan_sama(a, b)" },
        { label: "benar", detail: "fungsi", documentation: "Assert truthy", signature: "benar(nilai)" },
    ],
};

class HanLangCompletionProvider {
    /**
     * @param {vscode.TextDocument} document
     * @param {vscode.Position} position
     * @param {vscode.CancellationToken} _token
     * @param {vscode.CompletionContext} context
     */
    provideCompletionItems(document, position, _token, context) {
        const items = [];
        const lineText = document.lineAt(position).text;
        const textBefore = lineText.substring(0, position.character);

        // Check for module member access (e.g., math.)
        const dotMatch = textBefore.match(/\b(\w+)\.\s*$/);
        if (dotMatch) {
            const moduleName = dotMatch[1];
            if (MODULE_MEMBERS[moduleName]) {
                for (const member of MODULE_MEMBERS[moduleName]) {
                    const item = new vscode.CompletionItem(member.label,
                        member.detail === "fungsi"
                            ? vscode.CompletionItemKind.Method
                            : vscode.CompletionItemKind.Property
                    );
                    item.detail = `${moduleName}.${member.label} — ${member.detail}`;
                    item.documentation = new vscode.MarkdownString(member.documentation);
                    if (member.signature) {
                        item.insertText = new vscode.SnippetString(
                            member.label + "(${1})"
                        );
                    }
                    items.push(item);
                }
                return items;
            }
        }

        // Keywords
        for (const kw of KEYWORDS) {
            const item = new vscode.CompletionItem(kw.label,
                kw.kind === 21
                    ? vscode.CompletionItemKind.Constant
                    : vscode.CompletionItemKind.Keyword
            );
            item.detail = kw.detail;
            item.documentation = new vscode.MarkdownString(kw.documentation);
            items.push(item);
        }

        // Built-in functions
        for (const fn of BUILTINS) {
            const item = new vscode.CompletionItem(
                fn.label, vscode.CompletionItemKind.Function
            );
            item.detail = `${fn.detail} — ${fn.signature}`;
            item.documentation = new vscode.MarkdownString(fn.documentation);
            item.insertText = new vscode.SnippetString(fn.label + "(${1})");
            items.push(item);
        }

        // Module names (after impor)
        if (textBefore.match(/\bimpor\s+$/)) {
            const modules = Object.keys(MODULE_MEMBERS);
            for (const mod of modules) {
                const item = new vscode.CompletionItem(
                    mod, vscode.CompletionItemKind.Module
                );
                item.detail = `Modul ${mod}`;
                item.documentation = new vscode.MarkdownString(`Standard library: ${mod}`);
                items.push(item);
            }
            return items;
        }

        // User-defined symbols from current document
        const text = document.getText();
        const funcPattern = /\bfungsi\s+([a-zA-Z_]\w*)/g;
        const varPattern = /\b(?:tetapkan|konstan)\s+([a-zA-Z_]\w*)/g;
        const seen = new Set();

        let match;
        while ((match = funcPattern.exec(text)) !== null) {
            if (!seen.has(match[1])) {
                seen.add(match[1]);
                const item = new vscode.CompletionItem(
                    match[1], vscode.CompletionItemKind.Function
                );
                item.detail = "Fungsi (user-defined)";
                item.insertText = new vscode.SnippetString(match[1] + "(${1})");
                items.push(item);
            }
        }

        while ((match = varPattern.exec(text)) !== null) {
            if (!seen.has(match[1])) {
                seen.add(match[1]);
                const item = new vscode.CompletionItem(
                    match[1], vscode.CompletionItemKind.Variable
                );
                item.detail = "Variabel";
                items.push(item);
            }
        }

        return items;
    }
}

// ═══════════════════════════════════════════════════════════════════
//  Signature Help Provider
// ═══════════════════════════════════════════════════════════════════

class HanLangSignatureHelpProvider {
    provideSignatureHelp(document, position) {
        const lineText = document.lineAt(position).text;
        const textBefore = lineText.substring(0, position.character);

        // Find the function name before the opening paren
        const funcMatch = textBefore.match(/\b(\w+)\s*\([^)]*$/);
        if (!funcMatch) return null;

        const funcName = funcMatch[1];
        const builtin = BUILTINS.find(b => b.label === funcName);

        if (builtin) {
            const sigHelp = new vscode.SignatureHelp();
            const sig = new vscode.SignatureInformation(
                builtin.signature,
                new vscode.MarkdownString(builtin.documentation)
            );
            sigHelp.signatures = [sig];
            sigHelp.activeSignature = 0;

            // Count commas to determine active parameter
            const afterParen = textBefore.substring(textBefore.lastIndexOf("(") + 1);
            sigHelp.activeParameter = (afterParen.match(/,/g) || []).length;

            return sigHelp;
        }

        // Check module function
        const modMatch = textBefore.match(/\b(\w+)\.(\w+)\s*\([^)]*$/);
        if (modMatch && MODULE_MEMBERS[modMatch[1]]) {
            const member = MODULE_MEMBERS[modMatch[1]].find(m => m.label === modMatch[2]);
            if (member && member.signature) {
                const sigHelp = new vscode.SignatureHelp();
                const sig = new vscode.SignatureInformation(
                    `${modMatch[1]}.${member.signature}`,
                    new vscode.MarkdownString(member.documentation)
                );
                sigHelp.signatures = [sig];
                sigHelp.activeSignature = 0;
                const afterParen = textBefore.substring(textBefore.lastIndexOf("(") + 1);
                sigHelp.activeParameter = (afterParen.match(/,/g) || []).length;
                return sigHelp;
            }
        }

        return null;
    }
}

// ═══════════════════════════════════════════════════════════════════
//  Hover Provider
// ═══════════════════════════════════════════════════════════════════

class HanLangHoverProvider {
    provideHover(document, position) {
        const wordRange = document.getWordRangeAtPosition(position, /[a-zA-Z_]\w*/);
        if (!wordRange) return null;

        const word = document.getText(wordRange);

        // Check keywords
        const kw = KEYWORDS.find(k => k.label === word);
        if (kw) {
            return new vscode.Hover(
                new vscode.MarkdownString(`**${kw.detail}** \`${kw.label}\`\n\n${kw.documentation}`)
            );
        }

        // Check builtins
        const builtin = BUILTINS.find(b => b.label === word);
        if (builtin) {
            return new vscode.Hover(
                new vscode.MarkdownString(
                    `**${builtin.detail}** \`${builtin.signature}\`\n\n${builtin.documentation}`
                )
            );
        }

        return null;
    }
}

module.exports = { activate, deactivate };
