"""Syntax + import check for every file under backend/app/ and backend/alembic/"""
import ast, pathlib, sys

root = pathlib.Path(__file__).parent.parent / "backend"
targets = list(root.glob("app/**/*.py")) + list(root.glob("alembic/**/*.py"))
errors = []

for f in sorted(targets):
    try:
        ast.parse(f.read_text(encoding="utf-8"))
        print(f"  OK  {f.relative_to(root)}")
    except SyntaxError as e:
        errors.append((f, e))
        print(f"  FAIL {f.relative_to(root)}: {e}")

print(f"\n{'ALL PASSED' if not errors else f'{len(errors)} ERROR(S)'} — {len(targets)} files checked")
sys.exit(1 if errors else 0)
