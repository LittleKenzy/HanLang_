print("HanLang interpreter berhasil dijalankan!")
import ast
import operator
import re
import sys
from pathlib import Path


class KenzyError(Exception):
    pass


# Operator yang boleh digunakan dalam ekspresi.
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
}


def evaluate_expression(expression, variables):
    """Menghitung ekspresi dengan operator yang dibatasi."""
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise KenzyError(
            f"Ekspresi tidak valid: {expression}"
        ) from exc

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(
                node.value, (int, float, str, bool)
            ) or node.value is None:
                return node.value
            raise KenzyError("Jenis nilai belum didukung.")

        if isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            if node.id in ("Benar", "True"):
                return True
            if node.id in ("Salah", "False"):
                return False
            raise KenzyError(
                f"Variabel '{node.id}' belum dibuat."
            )

        if isinstance(node, ast.BinOp):
            if type(node.op) not in OPERATORS:
                raise KenzyError("Operator belum didukung.")

            left = visit(node.left)
            right = visit(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise KenzyError("Nilai pangkat terlalu besar.")

            return OPERATORS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp):
            value = visit(node.operand)

            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.Not):
                return not value

        if isinstance(node, ast.Compare):
            left = visit(node.left)

            for operation, comparator in zip(
                node.ops, node.comparators
            ):
                if type(operation) not in OPERATORS:
                    raise KenzyError(
                        "Operator perbandingan belum didukung."
                    )

                right = visit(comparator)

                if not OPERATORS[type(operation)](left, right):
                    return False

                left = right

            return True

        if isinstance(node, ast.BoolOp):
            values = [visit(value) for value in node.values]

            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)

        raise KenzyError("Ekspresi ini belum didukung.")

    try:
        return visit(tree)
    except (ZeroDivisionError, TypeError, ValueError,
            OverflowError) as exc:
        raise KenzyError(
            f"Ekspresi gagal dihitung: {exc}"
        ) from exc


def split_statements(source):
    """Memisahkan perintah berdasarkan baris dan blok."""
    statements = []
    buffer = []
    depth = 0

    for line_number, original_line in enumerate(
        source.splitlines(), start=1
    ):
        # Hapus komentar, tetapi jangan hapus # di dalam teks.
        cleaned = []
        in_string = False
        quote = None
        escaped = False

        for char in original_line:
            if in_string:
                cleaned.append(char)

                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    in_string = False
            else:
                if char in ("'", '"'):
                    in_string = True
                    quote = char
                    cleaned.append(char)
                elif char == "#":
                    break
                else:
                    cleaned.append(char)

        line = "".join(cleaned).strip()

        if not line:
            continue

        buffer.append(line)

        # Hitung kurung di luar teks.
        in_string = False
        quote = None
        escaped = False

        for char in line:
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    in_string = False
            else:
                if char in ("'", '"'):
                    in_string = True
                    quote = char
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1

                    if depth < 0:
                        raise KenzyError(
                            f"Baris {line_number}: "
                            "kurung penutup berlebih."
                        )

        if depth == 0:
            statements.append(
                ("\n".join(buffer), line_number)
            )
            buffer = []

    if depth != 0:
        raise KenzyError(
            "Ada blok yang belum ditutup dengan '}'."
        )

    if buffer:
        statements.append(
            ("\n".join(buffer), len(source.splitlines()))
        )

    return statements


def extract_block(statement):
    """Mengambil kode di dalam kurung kurawal."""
    start = statement.find("{")
    end = statement.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise KenzyError("Blok harus memakai { dan }.")

    return statement[start + 1:end]


def run_source(source, variables=None):
    if variables is None:
        variables = {}

    for statement, line_number in split_statements(source):
        statement = statement.strip()

        try:
            # Perintah kondisi.
            if statement.startswith("jika "):
                match = re.match(
                    r"^jika\s+(.+?)\s*\{",
                    statement,
                    re.DOTALL,
                )

                if not match:
                    raise KenzyError(
                        "Format: jika kondisi { ... }"
                    )

                condition = evaluate_expression(
                    match.group(1), variables
                )

                if condition:
                    run_source(
                        extract_block(statement), variables
                    )

                continue

            # Perintah untuk menampilkan nilai.
            if (
                statement.startswith("tampil(")
                and statement.endswith(")")
            ):
                expression = statement[
                    len("tampil("):-1
                ]
                print(evaluate_expression(
                    expression, variables
                ))
                continue

            # Membuat atau memperbarui variabel.
            match = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$",
                statement,
                re.DOTALL,
            )

            if match:
                name, expression = match.groups()

                if name in ("jika", "tampil"):
                    raise KenzyError(
                        f"'{name}' adalah kata khusus."
                    )

                variables[name] = evaluate_expression(
                    expression, variables
                )
                continue

            raise KenzyError(
                f"Perintah tidak dikenal: "
                f"{statement.splitlines()[0]}"
            )

        except KenzyError as exc:
            raise KenzyError(
                f"Baris sekitar {line_number}: {exc}"
            ) from exc


def main():
    if len(sys.argv) != 2:
        print(
            "Penggunaan: "
            "python interpreter.py program.kenzy"
        )
        raise SystemExit(1)

    file_path = Path(sys.argv[1])

    if not file_path.is_file():
        print(f"File tidak ditemukan: {file_path}")
        raise SystemExit(1)

    try:
        source = file_path.read_text(encoding="utf-8")
        run_source(source)
    except (KenzyError, OSError) as exc:
        print(f"KenzyLang Error: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()