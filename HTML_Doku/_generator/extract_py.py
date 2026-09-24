"""Extract the documentation model of a Python source tree with the ast module."""
from __future__ import annotations

import ast
from pathlib import Path

BIG_CONSTANT = 160
ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _unparse(node) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def _segment(lines: list[str], node) -> str:
    start = node.lineno
    if getattr(node, "decorator_list", None):
        start = min(d.lineno for d in node.decorator_list)
    return "\n".join(lines[start - 1:node.end_lineno])


def _params(args: ast.arguments) -> list[dict]:
    out = []
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    for a, d in zip(positional, defaults):
        out.append({"name": a.arg, "annotation": _unparse(a.annotation), "default": _unparse(d), "kind": "pos"})
    if args.vararg:
        out.append({"name": args.vararg.arg, "annotation": _unparse(args.vararg.annotation),
                    "default": None, "kind": "vararg"})
    for a, d in zip(args.kwonlyargs, args.kw_defaults):
        out.append({"name": a.arg, "annotation": _unparse(a.annotation), "default": _unparse(d), "kind": "kwonly"})
    if args.kwarg:
        out.append({"name": args.kwarg.arg, "annotation": _unparse(args.kwarg.annotation),
                    "default": None, "kind": "kwarg"})
    return out


def _signature(params: list[dict]) -> str:
    parts = []
    for p in params:
        s = {"vararg": "*", "kwarg": "**"}.get(p["kind"], "") + p["name"]
        if p["annotation"]:
            s += ": " + p["annotation"]
        if p["default"] is not None:
            s += " = " + p["default"]
        parts.append(s)
    return "(" + ", ".join(parts) + ")"


def _route(decorators: list[ast.expr]) -> dict | None:
    for d in decorators:
        if (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                and d.func.attr in ROUTE_METHODS and d.args
                and isinstance(d.args[0], ast.Constant) and isinstance(d.args[0].value, str)):
            return {"method": d.func.attr.upper(), "path": d.args[0].value, "decorator": _unparse(d)}
    return None


def _is_name_chain(node) -> bool:
    while isinstance(node, (ast.Attribute, ast.Call, ast.Subscript)):
        node = node.func if isinstance(node, ast.Call) else node.value
    return isinstance(node, (ast.Name, ast.Constant))


class _BodyVisitor(ast.NodeVisitor):
    """Collects calls and raises of one function body, including nested helper functions."""

    def __init__(self):
        self.calls: set[str] = set()
        self.raises: set[str] = set()

    def visit_Call(self, node):
        if _is_name_chain(node.func):
            name = _unparse(node.func)
            if name and len(name) < 80:
                self.calls.add(name)
        self.generic_visit(node)

    def visit_Raise(self, node):
        exc = node.exc
        if exc is not None:
            target = exc.func if isinstance(exc, ast.Call) else exc
            name = _unparse(target)
            if name and len(name) < 80:
                self.raises.add(name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        pass


def _function(node, lines, owner: str | None) -> dict:
    params = _params(node.args)
    v = _BodyVisitor()
    for d in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
        v.visit(d)
    for stmt in node.body:
        v.visit(stmt)
    name = node.name
    dunder = name.startswith("__") and name.endswith("__")
    return {
        "kind": "function",
        "name": name,
        "qualname": f"{owner}.{name}" if owner else name,
        "async": isinstance(node, ast.AsyncFunctionDef),
        "signature": _signature(params),
        "params": params,
        "returns": _unparse(node.returns),
        "doc": ast.get_docstring(node),
        "decorators": [_unparse(d) for d in node.decorator_list],
        "route": _route(node.decorator_list),
        "lineno": node.lineno,
        "end_lineno": node.end_lineno,
        "calls": sorted(v.calls),
        "raises": sorted(v.raises),
        "source": _segment(lines, node),
        "is_method": owner is not None,
        "private": name.startswith("_") and not dunder,
        "dunder": dunder,
    }


def _flavor(node: ast.ClassDef) -> str:
    bases = [(_unparse(b) or "").split(".")[-1] for b in node.bases]
    decos = [(_unparse(d) or "").split("(")[0].split(".")[-1] for d in node.decorator_list]
    if any(b in {"Enum", "IntEnum", "StrEnum", "Flag", "IntFlag"} for b in bases):
        return "enum"
    if "dataclass" in decos:
        return "dataclass"
    if any(b in {"BaseModel", "BaseSettings", "RootModel"} for b in bases):
        return "pydantic"
    return "class"


def _class(node: ast.ClassDef, lines, out: list[dict], prefix: str = "") -> None:
    fields, methods, nested = [], [], []
    qual = prefix + node.name
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            fields.append({"name": stmt.target.id, "annotation": _unparse(stmt.annotation),
                           "default": _unparse(stmt.value)})
        elif isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name):
                    fields.append({"name": t.id, "annotation": None, "default": _unparse(stmt.value)})
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_function(stmt, lines, qual))
        elif isinstance(stmt, ast.ClassDef):
            nested.append(prefix + node.name + "." + stmt.name)
    out.append({
        "kind": "class",
        "name": qual,
        "bases": [_unparse(b) for b in node.bases],
        "decorators": [_unparse(d) for d in node.decorator_list],
        "doc": ast.get_docstring(node),
        "fields": fields,
        "methods": methods,
        "nested": nested,
        "lineno": node.lineno,
        "end_lineno": node.end_lineno,
        "source": _segment(lines, node),
        "flavor": _flavor(node),
    })
    for stmt in node.body:
        if isinstance(stmt, ast.ClassDef):
            _class(stmt, lines, out, qual + ".")


def _toplevel(body):
    """Top-level statements, looking into module-level if/try blocks (import fallbacks)."""
    for stmt in body:
        if isinstance(stmt, ast.If):
            if "__name__" in (_unparse(stmt.test) or ""):
                continue
            yield from _toplevel(stmt.body)
            yield from _toplevel(stmt.orelse)
        elif isinstance(stmt, ast.Try):
            yield from _toplevel(stmt.body)
            for h in stmt.handlers:
                yield from _toplevel(h.body)
        else:
            yield stmt


def module_name(rel: str) -> str:
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__" and len(parts) > 1:
        parts = parts[:-1]
    return ".".join(parts)


def extract_file(root: Path, path: Path) -> dict:
    rel = path.relative_to(root).as_posix()
    source = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    lines = source.split("\n")
    mod = {"path": rel, "name": module_name(rel), "doc": None, "imports": [], "constants": [],
           "classes": [], "functions": [], "source": source, "loc": source.count("\n") + 1,
           "error": None, "lang": "py"}
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        mod["error"] = f"SyntaxError: {e}"
        return mod
    mod["doc"] = ast.get_docstring(tree)
    for stmt in _toplevel(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            mod["imports"].append(_unparse(stmt))
        elif isinstance(stmt, (ast.Assign, ast.AnnAssign)):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            value = _unparse(stmt.value) if stmt.value is not None else _unparse(stmt.annotation)
            for t in targets:
                if isinstance(t, ast.Name) and value is not None:
                    mod["constants"].append({"name": t.id, "value": value, "lineno": stmt.lineno,
                                             "big": len(value) > BIG_CONSTANT})
        elif isinstance(stmt, ast.ClassDef):
            _class(stmt, lines, mod["classes"])
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            mod["functions"].append(_function(stmt, lines, None))
    return mod


def extract_tree(root: Path, exclude: tuple[str, ...] = ()) -> list[dict]:
    mods = []
    for p in sorted(root.rglob("*.py"), key=lambda p: p.relative_to(root).as_posix()):
        rel = p.relative_to(root).as_posix()
        if "__pycache__" in rel or any(rel.startswith(e) for e in exclude):
            continue
        mods.append(extract_file(root, p))
    return mods
