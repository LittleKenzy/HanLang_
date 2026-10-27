#!/usr/bin/env python3
"""
HanLang Interpreter — Legacy Entry Point
=========================================

This file now delegates to the new HanLang engine in src/hanlang/.
Preserves backward compatibility: `python interpreter.py program.han`
still works exactly as before.
"""
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from hanlang.lexer import tokenize
from hanlang.parser import parse
from hanlang.runtime import Interpreter
from hanlang.errors import HanError


def main():
    if len(sys.argv) < 2:
        print("Penggunaan: python interpreter.py <file.han>")
        print("Atau gunakan: python han.py --help")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.isfile(filepath):
        print(f"File tidak ditemukan: {filepath}")
        sys.exit(1)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        source_lines = source.splitlines()
        tokens = tokenize(source, filepath)
        ast = parse(tokens, filepath, source)
        interpreter = Interpreter(filepath, source_lines)
        interpreter.execute(ast)

    except HanError as e:
        print(e.format_error(source.splitlines() if 'source' in dir() else []))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDibatalkan.")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        if os.environ.get("HANLANG_DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()