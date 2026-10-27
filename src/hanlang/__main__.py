"""HanLang entry point."""
import sys

try:
    from hanlang.cli import main
except ImportError:
    from .cli import main

if __name__ == "__main__":
    sys.exit(main())

