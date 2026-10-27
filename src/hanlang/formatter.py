"""
HanLang Code Formatter
======================

Reads HanLang source code and reformats it with consistent
indentation, spacing, and style.
"""

from .lexer import Lexer
from .tokens import TokenType


def format_source(source, indent_size=4):
    """Format HanLang source code with consistent style."""
    lines = source.splitlines()
    formatted_lines = []
    indent_level = 0
    indent = " " * indent_size

    for line in lines:
        stripped = line.strip()

        if not stripped:
            formatted_lines.append("")
            continue

        # Comments — preserve as-is
        if stripped.startswith("#"):
            formatted_lines.append(indent * indent_level + stripped)
            continue

        # Decrease indent before closing brace
        if stripped.startswith("}"):
            indent_level = max(0, indent_level - 1)

        # Handle jika_tidak_jika and jika_tidak at same level as }
        if stripped.startswith("} jika_tidak") or stripped.startswith("} tangkap") or stripped.startswith("} akhirnya"):
            indent_level = max(0, indent_level)
            formatted_lines.append(indent * (indent_level) + stripped)
        else:
            formatted_lines.append(indent * indent_level + stripped)

        # Count braces outside strings
        in_string = False
        quote_char = None
        escaped = False
        for ch in stripped:
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote_char:
                    in_string = False
            else:
                if ch in ('"', "'"):
                    in_string = True
                    quote_char = ch
                elif ch == "{":
                    indent_level += 1
                elif ch == "}":
                    pass  # already handled above

    # Clean up trailing whitespace and ensure final newline
    result = "\n".join(line.rstrip() for line in formatted_lines)
    if not result.endswith("\n"):
        result += "\n"
    return result
