"""Quick syntax check for all Python files in the backend."""
import ast
import pathlib
import sys

backend_root = pathlib.Path(__file__).parent.parent / "backend"
errors = []

for py_file in sorted(backend_root.rglob("*.py")):
    try:
        source = py_file.read_text(encoding="utf-8")
        ast.parse(source)
        print(f"  OK  {py_file.relative_to(backend_root)}")
    except SyntaxError as e:
        errors.append((py_file, e))
        print(f"  FAIL {py_file.relative_to(backend_root)}: {e}")

if errors:
    print(f"\n{len(errors)} syntax error(s) found.")
    sys.exit(1)
else:
    print(f"\nAll {sum(1 for _ in backend_root.rglob('*.py'))} Python files passed syntax check.")
