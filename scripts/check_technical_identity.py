"""Cheap AST guard for engine behavior, not a general Python linter.

No data files or live constituent list are read. Three-letter uppercase literals
are conservatively treated as stock symbols, except explicit units/standards.
Identity fields and dynamic lookups remain legal. This is a regression guard,
not a proof against arbitrary indirection or dynamically constructed rules.
"""
import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ENGINE_FILES = tuple(sorted((ROOT / "src/materiality").glob("*.py"))) + (
    ROOT / "src/analytics/market.py",
)


def identity_violations(source):
    tree = ast.parse(source)
    docstrings = {id(node.value) for owner in ast.walk(tree)
                  if isinstance(owner, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                  for node in owner.body[:1]
                  if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)}
    provenance_values = {id(value) for node in ast.walk(tree) if isinstance(node, ast.Dict)
                         for key, value in zip(node.keys, node.values)
                         if isinstance(key, ast.Constant) and key.value in {'source', 'currency', 'unit'}}
    violations = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in docstrings | provenance_values):
            value = node.value
            if value.upper() in {"VN30", "VN100"} or (
                re.fullmatch(r"[A-Z]{3}", value) and value not in {"USD", "UTC", "PIT", "EOD"}
            ):
                violations.append((node.lineno, "identity literal: " + value))
        if isinstance(node, (ast.Name, ast.Attribute)):
            name = (node.id if isinstance(node, ast.Name) else node.attr).lower()
            if "membership" in name or "vn30" in name or "vn100" in name or "cohort" in name:
                violations.append((node.lineno, "population feature: " + name))
    return violations


def scan_engine():
    return [(str(path.relative_to(ROOT)), line, reason) for path in ENGINE_FILES
            for line, reason in identity_violations(path.read_text(encoding="utf-8"))]


if __name__ == "__main__":
    findings = scan_engine()
    for finding in findings:
        print(*finding, sep=": ")
    print(f"Technical engine identity scan: {'FAIL' if findings else 'PASS'} ({len(ENGINE_FILES)} files)")
    raise SystemExit(bool(findings))
