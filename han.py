#!/usr/bin/env python3
"""
HanLang CLI Launcher
====================
Root-level launcher so users can run: python han.py run program.han
This also serves as the bridge for the han.bat / han.ps1 launchers.
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

# Add src to path so the hanlang package is importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from hanlang.cli import main

if __name__ == "__main__":
    sys.exit(main())
