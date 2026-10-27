"""
HanLang CLI
===========

Command-line interface for running, checking, testing, formatting,
and interacting with HanLang programs.

Usage:
    han run <file.han>          Execute a HanLang program
    han check <file.han>        Check syntax without executing
    han test [<file.han>]       Run test blocks
    han repl                    Interactive REPL
    han format <file.han>       Format source code
    han --version               Show version
    han --help                  Show help
"""

import sys
import os
from pathlib import Path

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from . import __version__
from .lexer import Lexer, tokenize
from .parser import Parser, parse
from .semantic import SemanticAnalyzer
from .runtime import Interpreter, Environment
from .formatter import format_source
from .errors import HanError, SourceLocation


BANNER = r"""
  ╦ ╦╔═╗╔╗╔╦  ╔═╗╔╗╔╔═╗
  ╠═╣╠═╣║║║║  ╠═╣║║║║ ╦
  ╩ ╩╩ ╩╝╚╝╩═╝╩ ╩╝╚╝╚═╝
"""

HELP_TEXT = f"""\033[1;36m{BANNER}\033[0m
  \033[1mHanLang v{__version__}\033[0m — Bahasa pemrograman yang ekspresif & mudah dibaca

  \033[1;33mPenggunaan:\033[0m
    han <perintah> [opsi]

  \033[1;33mPerintah:\033[0m
    \033[1mrun\033[0m <file.han>           Jalankan program HanLang
    \033[1mcheck\033[0m <file.han>         Periksa syntax tanpa menjalankan
    \033[1mtest\033[0m [file.han]          Jalankan test dalam file
    \033[1mrepl\033[0m                     Buka shell interaktif
    \033[1mformat\033[0m <file.han>        Format kode sumber
    \033[1mexplain\033[0m <file.han>       Jalankan dengan mode penjelasan

  \033[1;33mOpsi:\033[0m
    \033[1m--version\033[0m, \033[1m-v\033[0m            Tampilkan versi
    \033[1m--help\033[0m, \033[1m-h\033[0m               Tampilkan bantuan ini

  \033[1;33mContoh:\033[0m
    han run hello.han
    han check program.han
    han test
    han repl
"""


def _read_source(filepath):
    """Read a source file and return (source, path)."""
    path = Path(filepath)
    if not path.is_file():
        print(f"\033[1;31mError:\033[0m File tidak ditemukan: {filepath}")
        sys.exit(1)
    if not path.suffix == ".han":
        print(f"\033[1;33mPeringatan:\033[0m File bukan .han: {filepath}")
    try:
        return path.read_text(encoding="utf-8"), str(path)
    except Exception as e:
        print(f"\033[1;31mError:\033[0m Gagal membaca file: {e}")
        sys.exit(1)


def _run_source(source, filename, explain=False):
    """Tokenize, parse, and execute source code. Returns exit code."""
    source_lines = source.splitlines()

    try:
        # Phase 1: Tokenize
        tokens = tokenize(source, filename)

        # Phase 2: Parse
        ast = parse(tokens, filename, source)

        # Phase 3: Semantic check
        analyzer = SemanticAnalyzer(filename)
        errors, warnings = analyzer.analyze(ast)

        for warning in warnings:
            print(f"\033[1;33mPeringatan:\033[0m {warning}")

        if errors:
            for error in errors:
                print(f"\033[1;31mError:\033[0m {error}")
            return 1

        # Phase 4: Execute
        interpreter = Interpreter(filename, source_lines)
        interpreter.execute(ast)
        return 0

    except HanError as e:
        print(e.format_error(source_lines))
        return 1
    except KeyboardInterrupt:
        print("\n\033[33mDibatalkan oleh pengguna.\033[0m")
        return 130
    except Exception as e:
        print(f"\033[1;31mInternal Error:\033[0m {e}")
        if os.environ.get("HANLANG_DEBUG"):
            import traceback
            traceback.print_exc()
        return 1


def cmd_run(args):
    """Execute a HanLang program."""
    if not args:
        print("\033[1;31mError:\033[0m Berikan nama file.")
        print("Contoh: han run program.han")
        return 1

    source, filename = _read_source(args[0])
    return _run_source(source, filename)


def cmd_check(args):
    """Check syntax without executing."""
    if not args:
        print("\033[1;31mError:\033[0m Berikan nama file.")
        return 1

    source, filename = _read_source(args[0])
    source_lines = source.splitlines()

    try:
        tokens = tokenize(source, filename)
        ast = parse(tokens, filename, source)

        analyzer = SemanticAnalyzer(filename)
        errors, warnings = analyzer.analyze(ast)

        for warning in warnings:
            print(f"\033[1;33mPeringatan:\033[0m {warning}")

        if errors:
            for error in errors:
                print(f"\033[1;31mError:\033[0m {error}")
            return 1

        print(f"\033[1;32m✓\033[0m {filename} — tidak ada masalah ditemukan.")
        return 0

    except HanError as e:
        print(e.format_error(source_lines))
        return 1


def cmd_test(args):
    """Run test blocks in a file or all .han files."""
    files = []
    if args:
        files = [args[0]]
    else:
        # Find all .han files in current directory and test/ subdirectory
        for pattern in ["*.han", "tests/*.han", "test/*.han"]:
            for p in Path(".").glob(pattern):
                files.append(str(p))

    if not files:
        print("\033[33mTidak ada file test ditemukan.\033[0m")
        return 1

    total_pass = 0
    total_fail = 0
    total_tests = 0

    print(f"\n\033[1;36m{'='*50}\033[0m")
    print(f"\033[1m  HanLang Test Runner v{__version__}\033[0m")
    print(f"\033[1;36m{'='*50}\033[0m\n")

    for filepath in files:
        source, filename = _read_source(filepath)
        source_lines = source.splitlines()

        try:
            tokens = tokenize(source, filename)
            ast = parse(tokens, filename, source)
            interpreter = Interpreter(filename, source_lines)
            interpreter.execute(ast)

            if interpreter.test_results:
                print(f"\033[1m  {filename}\033[0m")
                for desc, passed, error in interpreter.test_results:
                    total_tests += 1
                    if passed:
                        total_pass += 1
                        print(f"    \033[32m✓\033[0m {desc}")
                    else:
                        total_fail += 1
                        print(f"    \033[31m✗\033[0m {desc}")
                        if error:
                            print(f"      \033[31m{error}\033[0m")
                print()

        except HanError as e:
            print(f"\033[31m  ✗ Error in {filename}:\033[0m")
            print(e.format_error(source_lines))
            total_fail += 1

    print(f"\033[1;36m{'─'*50}\033[0m")
    print(f"  Total: {total_tests} test  "
          f"\033[32m{total_pass} lulus\033[0m  "
          f"\033[31m{total_fail} gagal\033[0m")
    print(f"\033[1;36m{'='*50}\033[0m\n")

    return 0 if total_fail == 0 else 1


def cmd_repl(args):
    """Interactive REPL."""
    print(f"\033[1;36m{BANNER}\033[0m")
    print(f"  \033[1mHanLang v{__version__}\033[0m — Interactive REPL")
    print(f"  Ketik 'keluar' atau Ctrl+C untuk keluar.\n")

    interpreter = Interpreter("<repl>")
    env = interpreter.global_env
    buffer = []
    depth = 0

    while True:
        try:
            prompt = "\033[1;36m>>> \033[0m" if depth == 0 else "\033[1;36m... \033[0m"
            line = input(prompt)

            if line.strip() in ("keluar", "exit", "quit"):
                print("\033[33mSampai jumpa! 👋\033[0m")
                break

            buffer.append(line)

            # Track braces
            for ch in line:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1

            if depth > 0:
                continue
            if depth < 0:
                depth = 0
                buffer = []
                print("\033[31mError: Kurung penutup berlebih.\033[0m")
                continue

            source = "\n".join(buffer)
            buffer = []
            depth = 0

            if not source.strip():
                continue

            source_lines = source.splitlines()

            try:
                tokens = tokenize(source, "<repl>")
                ast = parse(tokens, "<repl>", source)
                result = interpreter.execute(ast, env)

                # Show result of expression statements
                from .values import HanNull
                if result is not None and not isinstance(result, HanNull):
                    from .values import value_repr
                    print(f"\033[90m=> {value_repr(result)}\033[0m")

            except HanError as e:
                print(e.format_error(source_lines))

        except KeyboardInterrupt:
            print("\n\033[33mSampai jumpa! 👋\033[0m")
            break
        except EOFError:
            print("\n\033[33mSampai jumpa! 👋\033[0m")
            break

    return 0


def cmd_format(args):
    """Format HanLang source code."""
    if not args:
        print("\033[1;31mError:\033[0m Berikan nama file.")
        return 1

    source, filename = _read_source(args[0])
    formatted = format_source(source)

    # Write back
    path = Path(args[0])
    path.write_text(formatted, encoding="utf-8")
    print(f"\033[1;32m✓\033[0m {filename} telah diformat.")
    return 0


def cmd_explain(args):
    """Run with explain mode (show execution steps)."""
    if not args:
        print("\033[1;31mError:\033[0m Berikan nama file.")
        return 1

    source, filename = _read_source(args[0])
    return _run_source(source, filename, explain=True)


def main():
    """Main CLI entry point."""
    args = sys.argv[1:]

    if not args:
        print(HELP_TEXT)
        return 0

    command = args[0]
    rest = args[1:]

    if command in ("--help", "-h", "help", "bantuan"):
        print(HELP_TEXT)
        return 0

    if command in ("--version", "-v", "version", "versi"):
        print(f"HanLang v{__version__}")
        return 0

    commands = {
        "run": cmd_run,
        "jalankan": cmd_run,
        "check": cmd_check,
        "periksa": cmd_check,
        "test": cmd_test,
        "uji": cmd_test,
        "repl": cmd_repl,
        "format": cmd_format,
        "explain": cmd_explain,
        "jelaskan": cmd_explain,
    }

    if command in commands:
        return commands[command](rest)

    # If a .han file is given directly, run it
    if command.endswith(".han"):
        return cmd_run([command])

    print(f"\033[1;31mError:\033[0m Perintah tidak dikenal: '{command}'")
    print("Ketik 'han --help' untuk melihat daftar perintah.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
