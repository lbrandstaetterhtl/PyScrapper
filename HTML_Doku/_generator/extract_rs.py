"""Extract the documentation model of a small Rust crate.

Like extract_cs this is a structural scanner: comments and literals are masked, then items are
found by brace matching. It covers what the captcha OCR crate uses: free functions, structs with
named fields, enums, impl blocks, `use`/`mod` lines, consts and statics, attributes and `///` docs.
"""
from __future__ import annotations

import re
from pathlib import Path

from extract_cs import match_brace, split_top

RS_KEYWORDS = set((
    "as async await break const continue crate dyn else enum extern false fn for if impl in let loop "
    "match mod move mut pub ref return self Self static struct super trait true type unsafe use where while"
).split())
ITEM_RE = re.compile(r"\b(fn|struct|enum|impl|mod|trait|const|static|use|type)\b")


def mask(src: str) -> str:
    """Blank comments, string literals and char literals. Lifetimes ('a, '_) are left alone."""
    out = list(src)
    i, n = 0, len(src)

    def blank(a, b):
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            blank(i, j)
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            blank(i, j)
            i = j
        elif src[i] == "r" and re.match(r'r#*"', src[i:i + 8]) and (i == 0 or not src[i - 1].isalnum()):
            hashes = re.match(r"r(#*)\"", src[i:]).group(1)
            start = i + 2 + len(hashes)
            j = src.find('"' + hashes, start)
            j = n if j == -1 else j
            blank(start, j)
            i = j + 1 + len(hashes)
        elif src[i] == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            blank(i + 1, j)
            i = j + 1
        elif src[i] == "'":
            m = re.match(r"'(\\.|\\u\{[0-9a-fA-F]+\}|[^\\'])'", src[i:i + 12])
            if m:
                blank(i + 1, i + len(m.group(0)) - 1)
                i += len(m.group(0))
            else:
                i += 1
        else:
            i += 1
    return "".join(out)


def line_of(src: str, pos: int) -> int:
    return src.count("\n", 0, pos) + 1


def doc_and_attrs_before(lines: list[str], lineno: int) -> tuple[str | None, list[str]]:
    """Walk upwards over attributes and /// lines directly above an item."""
    k = lineno - 2
    attrs, docs = [], []
    while k >= 0:
        s = lines[k].strip()
        if s.startswith("#[") or s.startswith("#!["):
            attrs.insert(0, s)
        elif s.startswith("///"):
            docs.insert(0, s[3:].strip())
        else:
            break
        k -= 1
    doc = " ".join(docs).strip() or None
    return doc, attrs


def parse_params(s: str) -> list[dict]:
    out = []
    for raw in split_top(s):
        p = re.sub(r"#\[[^\]]*\]", "", raw).strip()
        if not p:
            continue
        if re.fullmatch(r"&?\s*(?:'\w+\s+)?(?:mut\s+)?self", p):
            out.append({"name": "self", "annotation": p.replace("self", "Self").strip() if p != "self" else None,
                        "default": None, "kind": "pos"})
            continue
        name, _, ann = p.partition(":")
        name = name.replace("mut ", "").strip()
        out.append({"name": name, "annotation": " ".join(ann.split()) or None, "default": None, "kind": "pos"})
    return out


def find_calls(body: str, own: str) -> list[str]:
    calls = set()
    for m in re.finditer(r"(?<![\w.:])([A-Za-z_]\w*(?:::[A-Za-z_]\w*)*)\s*(?:::<[^()]*?>)?\s*\(", body):
        name = m.group(1)
        if name.split("::")[0] in RS_KEYWORDS - {"Self", "self"}:
            continue
        calls.add(name.replace("::", "."))
    for m in re.finditer(r"\.\s*([A-Za-z_]\w*)\s*(?:::<[^()]*?>)?\s*\(", body):
        calls.add(m.group(1))
    calls.discard(own)
    return sorted(calls)


class Scanner:
    def __init__(self, src: str, rel: str):
        self.src = src
        self.m = mask(src)
        self.lines = src.split("\n")
        self.rel = rel
        self.classes: list[dict] = []
        self.functions: list[dict] = []
        self.imports: list[str] = []
        self.constants: list[dict] = []
        self.by_name: dict[str, dict] = {}

    def lines_between(self, a: int, b: int) -> tuple[int, int, str]:
        la, lb = line_of(self.src, a), line_of(self.src, b)
        return la, lb, "\n".join(self.lines[la - 1:lb])

    def end_of_item(self, i: int) -> tuple[int, int]:
        """From position i, return (position of the item's '{' or -1, end position)."""
        m = self.m
        depth = 0
        while i < len(m):
            ch = m[i]
            if ch in "([<":
                depth += 1
            elif ch in ")]>":
                depth -= 1
            elif ch == "-" and m.startswith("->", i):
                i += 2
                continue
            elif ch == "=" and m.startswith("=>", i):
                i += 2
                continue
            elif ch == "{" and depth <= 0:
                return i, match_brace(m, i)
            elif ch == ";" and depth <= 0:
                return -1, i
            i += 1
        return -1, len(m) - 1

    def scan(self, start: int, end: int, owner: dict | None = None):
        m = self.m
        i = start
        while i < end:
            # skip whitespace, attributes and visibility to the next item keyword
            if m[i].isspace():
                i += 1
                continue
            if m.startswith("#", i) and m[i + 1:i + 3].lstrip("!").startswith("["):
                j = m.index("[", i)
                depth = 0
                for k in range(j, end):
                    if m[k] == "[":
                        depth += 1
                    elif m[k] == "]":
                        depth -= 1
                        if depth == 0:
                            i = k + 1
                            break
                else:
                    i = end
                continue
            head_m = re.match(r"(?:pub(?:\([^)]*\))?\s+)?(?:const\s+(?=fn\b|unsafe\b|async\b)|async\s+|unsafe\s+|extern\s+\"\w*\"\s+)*", m[i:end])
            j = i + head_m.end()
            km = ITEM_RE.match(m, j)
            if not km:
                # not an item we know (e.g. `extern crate x;`, a macro call): skip the statement
                brace, stop = self.end_of_item(i)
                i = stop + 1
                continue
            kind = km.group(1)
            if kind == "use":
                brace, stop = -1, m.index(";", km.end())
            else:
                brace, stop = self.end_of_item(km.end())
            header = " ".join(m[i:brace if brace >= 0 else stop].split())
            raw_header = " ".join(self.src[i:brace if brace >= 0 else stop].split())
            if kind == "use" or (kind == "mod" and brace < 0):
                self.imports.append(" ".join(self.src[i:stop + 1].split()))
            elif kind in ("const", "static") and owner is None:
                cm = re.match(r".*?\b(?:const|static)\s+(?:mut\s+)?(\w+)\s*:\s*([^=]+)=(.*)", raw_header)
                if cm:
                    value = cm.group(3).strip()
                    self.constants.append({"name": cm.group(1), "value": value,
                                           "lineno": line_of(self.src, i), "big": len(value) > 160})
            elif kind == "fn":
                self.function(i, brace, stop, header, owner)
            elif kind in ("struct", "enum", "trait"):
                self.type_item(i, brace, stop, kind, header)
            elif kind == "impl":
                self.impl_item(i, brace, stop, header)
            elif kind == "mod" and brace >= 0:
                self.scan(brace + 1, stop, owner)
            i = stop + 1

    def function(self, pos, brace, stop, header, owner):
        fm = re.search(r"\bfn\s+(\w+)\s*(<[^(]*>)?\s*\(", header)
        if not fm:
            return
        name = fm.group(1)
        # parameter list from the masked source, balanced parentheses
        open_at = self.m.index("(", pos + self.m[pos:].index("fn"))
        depth, k = 0, open_at
        while k < len(self.m):
            if self.m[k] == "(":
                depth += 1
            elif self.m[k] == ")":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        params = parse_params(self.src[open_at + 1:k])
        after = " ".join(self.m[k + 1:brace if brace >= 0 else stop].split())
        rm = re.match(r"->\s*(.*?)(?:\bwhere\b.*)?$", after)
        returns = rm.group(1).strip() if rm and rm.group(1).strip() else None
        la = line_of(self.src, pos)
        doc, attrs = doc_and_attrs_before(self.lines, la)
        _, lb, source = self.lines_between(pos, stop)
        body = self.m[brace:stop + 1] if brace >= 0 else ""
        is_pub = header.startswith("pub")
        fn = {
            "kind": "function", "name": name,
            "qualname": (owner["name"] + "." if owner else "") + name,
            "async": " async " in f" {header} ",
            "signature": "(" + ", ".join(
                p["name"] + (": " + p["annotation"] if p["annotation"] else "") for p in params) + ")",
            "params": params, "returns": returns, "doc": doc, "decorators": attrs, "route": None,
            "lineno": la, "end_lineno": lb, "calls": find_calls(body, name),
            "raises": sorted(set(re.findall(r"\b(\w+Error)::new_err", body))),
            "source": source, "is_method": owner is not None, "private": not is_pub, "dunder": False,
        }
        (owner["methods"] if owner else self.functions).append(fn)

    def type_item(self, pos, brace, stop, kind, header):
        tm = re.search(r"\b(?:struct|enum|trait)\s+(\w+)", header)
        if not tm:
            return
        name = tm.group(1)
        la = line_of(self.src, pos)
        doc, attrs = doc_and_attrs_before(self.lines, la)
        _, lb, source = self.lines_between(pos, stop)
        fields = []
        if brace >= 0 and kind in ("struct", "enum"):
            for part in split_top(self.src[brace + 1:stop]):
                p = re.sub(r"#\[[^\]]*\]|///[^\n]*", "", part).strip()
                if not p:
                    continue
                if kind == "struct":
                    fname, _, ftype = p.partition(":")
                    fields.append({"name": fname.replace("pub ", "").strip(),
                                   "annotation": " ".join(ftype.split()) or None, "default": None})
                else:
                    fields.append({"name": re.split(r"[\s({=]", p, 1)[0], "annotation": None, "default": None})
        derives = re.findall(r"derive\(([^)]*)\)", " ".join(attrs))
        cls = {"kind": "class", "name": name,
               "bases": [d.strip() for d in ",".join(derives).split(",") if d.strip()],
               "decorators": attrs, "doc": doc, "fields": fields, "methods": [], "nested": [],
               "lineno": la, "end_lineno": lb, "source": source,
               "flavor": "enum" if kind == "enum" else ("interface" if kind == "trait" else "struct")}
        self.classes.append(cls)
        self.by_name[name] = cls

    def impl_item(self, pos, brace, stop, header):
        im = re.match(r".*?\bimpl\b\s*(?:<[^>]*>)?\s*(.*)$", header)
        target = im.group(1).strip() if im else "?"
        trait = None
        if " for " in f" {target} ":
            trait, target = [x.strip() for x in target.split(" for ", 1)]
        target = re.sub(r"<.*", "", target).strip()
        cls = self.by_name.get(target)
        if cls is None:
            la = line_of(self.src, pos)
            _, lb, source = self.lines_between(pos, stop)
            cls = {"kind": "class", "name": target, "bases": [], "decorators": [], "doc": None, "fields": [],
                   "methods": [], "nested": [], "lineno": la, "end_lineno": lb, "source": source,
                   "flavor": "class"}
            self.classes.append(cls)
            self.by_name[target] = cls
        if trait:
            cls["bases"].append(trait)
        if brace >= 0:
            self.scan(brace + 1, stop, cls)


def module_name(rel: str, crate: str) -> str:
    parts = rel[:-3].split("/")
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts in (["lib"], ["main"]):
        return crate
    if parts and parts[-1] == "mod":
        parts = parts[:-1]
    return "::".join([crate] + parts)


def extract_file(root: Path, path: Path, crate: str) -> dict:
    rel = path.relative_to(root).as_posix()
    src = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    sc = Scanner(src, rel)
    error = None
    try:
        sc.scan(0, len(src))
    except Exception as e:  # keep the file in the doc even if the scanner trips
        error = f"{type(e).__name__}: {e}"
    return {"path": rel, "name": module_name(rel, crate), "doc": None, "imports": sc.imports,
            "constants": sc.constants, "classes": sc.classes, "functions": sc.functions, "source": src,
            "loc": src.count("\n") + 1, "error": error, "lang": "rs"}


def plain_file(path: Path, rel: str, lang: str = "text", doc: str | None = None) -> dict:
    src = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    return {"path": rel, "name": rel.split("/")[-1], "doc": doc, "imports": [], "constants": [],
            "classes": [], "functions": [], "source": src, "loc": src.count("\n") + 1, "error": None,
            "lang": lang}
