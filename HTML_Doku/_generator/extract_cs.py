"""Extract the documentation model of a C# / Avalonia project.

This is a structural scanner, not a compiler: comments and string literals are masked out, then
type and member declarations are found by brace matching. That is enough for the conventions used
in PyScrapperDesktopApp (one namespace per file, ordinary classes, records, interfaces and enums).
"""
from __future__ import annotations

import re
from pathlib import Path

CS_KEYWORDS = set((
    "abstract as async await base bool break byte case catch char checked class const continue "
    "decimal default delegate do double else enum event explicit extern false finally fixed float for "
    "foreach get goto if implicit in int interface internal is lock long namespace new null object "
    "operator out override params private protected public readonly record ref return sbyte sealed set "
    "short sizeof stackalloc static string struct switch this throw true try typeof uint ulong unchecked "
    "unsafe ushort using value var virtual void volatile when where while yield partial nameof init "
    "required file global"
).split())
MODIFIERS = {"public", "private", "protected", "internal", "static", "readonly", "const", "virtual",
             "override", "abstract", "sealed", "async", "partial", "new", "extern", "unsafe",
             "volatile", "required", "file", "event"}
VIEW_BASES = {"Window", "UserControl", "Application", "ContentControl", "TemplatedControl"}
VIEWMODEL_BASES = {"ObservableObject", "ViewModelBase", "ObservableRecipient", "ObservableValidator"}
HTTP_CALL = re.compile(r"\b(\w+)\.(Get|Post|Put|Delete|Patch)Async\s*\(")


# --------------------------------------------------------------------------- masking
def mask(src: str) -> str:
    """Replace comments and string/char literal contents with spaces, keeping offsets and newlines."""
    out = list(src)
    i, n = 0, len(src)

    def blank(a, b):
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        c = src[i]
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
        elif src.startswith('"""', i):
            j = src.find('"""', i + 3)
            j = n if j == -1 else j + 3
            blank(i + 1, j - 1)
            i = j
        elif c == '"' or (c in "$@" and i + 1 < n and src[i + 1] in '"$@'):
            k = i
            verbatim = False
            while k < n and src[k] in "$@":
                verbatim |= src[k] == "@"
                k += 1
            if k >= n or src[k] != '"':
                i += 1
                continue
            j = k + 1
            while j < n:
                if verbatim:
                    if src[j] == '"':
                        if j + 1 < n and src[j + 1] == '"':
                            j += 2
                            continue
                        break
                else:
                    if src[j] == "\\":
                        j += 2
                        continue
                    if src[j] == '"' or src[j] == "\n":
                        break
                j += 1
            blank(k + 1, j)
            i = j + 1
        elif c == "'":
            j = i + 1
            while j < n and src[j] != "'" and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            blank(i + 1, j)
            i = j + 1
        else:
            i += 1
    return "".join(out)


def match_brace(m: str, i: int) -> int:
    """Index of the brace closing the one at m[i]."""
    depth = 0
    for k in range(i, len(m)):
        if m[k] == "{":
            depth += 1
        elif m[k] == "}":
            depth -= 1
            if depth == 0:
                return k
    return len(m) - 1


def split_top(s: str, sep: str = ",") -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch in "(<[{":
            depth += 1
        elif ch in ")>]}":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return parts


# --------------------------------------------------------------------------- helpers
def line_of(src: str, pos: int) -> int:
    return src.count("\n", 0, pos) + 1


def doc_before(lines: list[str], lineno: int) -> str | None:
    """Collect the /// block directly above a declaration (attributes may sit in between)."""
    k = lineno - 2
    while k >= 0 and lines[k].strip().startswith("["):
        k -= 1
    block = []
    while k >= 0 and lines[k].strip().startswith("///"):
        block.insert(0, lines[k].strip()[3:].strip())
        k -= 1
    if not block:
        return None
    text = " ".join(block)
    m = re.search(r"<summary>(.*?)</summary>", text, re.S)
    if m:
        text = m.group(1)
    text = re.sub(r"<see\s+cref=\"([^\"]+)\"\s*/>", r"\1", text)
    text = re.sub(r"<paramref\s+name=\"([^\"]+)\"\s*/>", r"\1", text)
    text = re.sub(r"<(param|returns|remarks|exception)[^>]*>.*?</\1>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def strip_attrs(header: str) -> tuple[list[str], str]:
    attrs = []
    h = header.strip()
    while h.startswith("["):
        depth = 0
        for k, ch in enumerate(h):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    attrs.append(re.sub(r"\s+", " ", h[:k + 1]))
                    h = h[k + 1:].strip()
                    break
        else:
            break
    return attrs, h


def words_before(h: str) -> list[str]:
    """Split a declaration head into tokens, keeping generic arguments glued to their type."""
    toks, cur, depth = [], "", 0
    for ch in h:
        if ch in "<([":
            depth += 1
        elif ch in ">)]":
            depth -= 1
        if ch.isspace() and depth == 0:
            if cur:
                toks.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        toks.append(cur)
    # "Dictionary<string, int>" may have been split at the comma space when depth was mis-tracked
    return toks


def parse_params(s: str) -> list[dict]:
    out = []
    for raw in split_top(s):
        _, p = strip_attrs(raw)
        p = p.strip()
        if not p:
            continue
        default = None
        eq = split_top(p, "=")
        if len(eq) > 1:
            p, default = eq[0].strip(), "=".join(eq[1:]).strip()
        toks = words_before(p)
        if len(toks) == 1:
            name, ann = toks[0], None
        else:
            name, ann = toks[-1], " ".join(toks[:-1])
        out.append({"name": name, "annotation": ann, "default": default, "kind": "pos"})
    return out


def find_calls(body_masked: str, own: str) -> list[str]:
    calls = set()
    for m in re.finditer(r"\bnew\s+([A-Za-z_][\w.]*)\s*(?:<[^()]*?>)?\s*[({]", body_masked):
        calls.add(m.group(1))
    for m in re.finditer(r"(?<![\w.])([A-Za-z_][\w.]*?)\s*(?:<[\w<>,\s.?\[\]]*>)?\s*\(", body_masked):
        name = m.group(1)
        head = name.split(".")[0]
        if head in CS_KEYWORDS and head not in ("base", "this", "string"):
            continue
        before = body_masked[max(0, m.start() - 5):m.start()]
        if re.search(r"\bnew\s*$", before):
            continue
        calls.add(name)
    # chained calls: .Foo( after a closing paren
    for m in re.finditer(r"\)\s*\??\.\s*([A-Za-z_]\w*)\s*\(", body_masked):
        calls.add(m.group(1))
    calls.discard(own)
    return sorted(calls)


def find_route(body_src: str, body_masked: str) -> dict | None:
    m = HTTP_CALL.search(body_masked)
    if not m:
        return None
    arg_start = m.end()
    j = arg_start
    depth = 1
    while j < len(body_masked) and depth:
        if body_masked[j] == "(":
            depth += 1
        elif body_masked[j] == ")":
            depth -= 1
        j += 1
    arg = body_src[arg_start:j - 1]
    first = split_top(arg)[0].strip() if arg.strip() else ""
    decorator = (body_src[m.start():arg_start] + first)[:120]
    lit = re.match(r'\$?@?"(.*)"', first, re.S)
    if not lit:
        return {"method": m.group(2).upper(), "path": "/{…}", "decorator": decorator}
    text = lit.group(1)
    text = re.sub(r"^.*?\{AppData\.Config\.ServerPort\}", "", text)
    text = re.sub(r"\{[^{}]*\}", "{…}", text)
    if not text.startswith("/"):
        text = "/" + text
    return {"method": m.group(2).upper(), "path": text, "decorator": decorator}


# --------------------------------------------------------------------------- scanner
TYPE_RE = re.compile(r"\b(class|interface|struct|record|enum)\s+([A-Za-z_]\w*)")


class Scanner:
    def __init__(self, src: str):
        self.src = src
        self.m = mask(src)
        self.lines = src.split("\n")
        self.types: list[dict] = []
        self.namespace: str | None = None
        self.namespace_hint = ""

    def full_lines(self, a: int, b: int) -> tuple[int, int, str]:
        la, lb = line_of(self.src, a), line_of(self.src, b)
        return la, lb, "\n".join(self.lines[la - 1:lb])

    def scan(self, start: int, end: int, owner: dict | None):
        m = self.m
        i = start
        head_start = start
        paren = 0
        while i < end:
            ch = m[i]
            if ch in "([":
                paren += 1
            elif ch in ")]":
                paren -= 1
            if paren <= 0 and (ch in "{;" or m.startswith("=>", i)):
                paren = 0
                header_raw = m[head_start:i]
                header = header_raw.strip()
                if not header:
                    if ch == "{":
                        close = match_brace(m, i)
                        i = close + 1
                        head_start = i
                        continue
                    i += 1 if ch != "=" else 2
                    head_start = i
                    continue
                decl_pos = head_start + (len(header_raw) - len(header_raw.lstrip()))
                i, head_start = self.declaration(header, decl_pos, i, owner)
                continue
            if ch == "}" and paren <= 0:
                i += 1
                head_start = i
                continue
            i += 1

    def _end_of_expression(self, i: int) -> int:
        """From '=>' or '=' find the terminating ';' at depth 0."""
        depth = 0
        m = self.m
        while i < len(m):
            if m[i] in "({[":
                depth += 1
            elif m[i] in ")}]":
                depth -= 1
            elif m[i] == ";" and depth <= 0:
                return i
            i += 1
        return len(m) - 1

    def declaration(self, header: str, pos: int, i: int, owner: dict | None):
        m = self.m
        attrs, h = strip_attrs(header)
        lineno = line_of(self.src, pos)
        attr_lines = [a for a in attrs]
        if h.startswith("using ") or h.startswith("using("):
            if m[i] == "{":
                return match_brace(m, i) + 1, match_brace(m, i) + 1
            return i + 1, i + 1
        if h.startswith("namespace "):
            self.namespace = h.split(None, 1)[1].strip()
            self.namespace_hint = self.namespace
            if m[i] == "{":
                close = match_brace(m, i)
                self.scan(i + 1, close, owner)
                return close + 1, close + 1
            return i + 1, i + 1
        tm = TYPE_RE.search(h)
        if tm and "(" not in h[:tm.start()] and "=" not in h[:tm.start()]:
            return self.type_decl(h, attrs, tm, pos, i, owner)
        if owner is None:
            # stray statement at namespace level
            if m[i] == "{":
                c = match_brace(m, i)
                return c + 1, c + 1
            return i + 1, i + 1
        if owner["flavor"] == "enum":
            return i + 1, i + 1
        return self.member(h, attrs, pos, lineno, i, owner)

    def type_decl(self, h, attrs, tm, pos, i, owner):
        m = self.m
        kind, name = tm.group(1), tm.group(2)
        mods = h[:tm.start()].split()
        rest = h[tm.end():]
        bases = []
        colon = None
        depth = 0
        for k, ch in enumerate(rest):
            if ch in "<(":
                depth += 1
            elif ch in ">)":
                depth -= 1
            elif ch == ":" and depth == 0:
                colon = k
                break
        if colon is not None:
            base_txt = re.split(r"\bwhere\b", rest[colon + 1:])[0]
            bases = [b.strip() for b in split_top(base_txt) if b.strip()]
        if kind == "enum":
            flavor = "enum"
        elif kind == "interface":
            flavor = "interface"
        elif kind == "record":
            flavor = "record"
        elif "static" in mods:
            flavor = "static"
        elif name.endswith("ViewModel") or (
                any(b.split("<")[0].split(".")[-1] in VIEWMODEL_BASES for b in bases) and "ViewModels" in self.namespace_hint):
            flavor = "viewmodel"
        elif any(b.split("<")[0].split(".")[-1] in VIEW_BASES for b in bases):
            flavor = "view"
        else:
            flavor = "class"
        qual = (owner["name"] + "." if owner else "") + name
        t = {"kind": "class", "name": name, "bases": bases, "decorators": attrs,
             "doc": doc_before(self.lines, line_of(self.src, pos)), "fields": [], "methods": [],
             "nested": [], "lineno": line_of(self.src, pos), "end_lineno": 0, "source": "",
             "flavor": flavor, "_qual": qual}
        # positional record parameters
        pm = re.match(r"\s*(?:<[^>]*>)?\s*\((.*)\)", rest[:colon] if colon is not None else rest, re.S)
        if kind == "record" and pm:
            for p in parse_params(pm.group(1)):
                t["fields"].append({"name": p["name"], "annotation": p["annotation"], "default": p["default"]})
        if owner:
            owner["nested"].append(name)
        self.types.append(t)
        if m[i] == "{":
            close = match_brace(m, i)
            if kind == "enum":
                body = m[i + 1:close]
                for part in split_top(body):
                    _, p = strip_attrs(part)
                    p = p.strip()
                    if not p:
                        continue
                    nm, _, val = p.partition("=")
                    t["fields"].append({"name": nm.strip(), "annotation": None,
                                        "default": val.strip() or None})
            else:
                self.scan(i + 1, close, t)
            end = close
        else:
            end = self._end_of_expression(i) if m[i] != ";" else i
        t["lineno"], t["end_lineno"], t["source"] = self.full_lines(pos, end)
        return end + 1, end + 1

    def member(self, h, attrs, pos, lineno, i, owner):
        m, src = self.m, self.src
        # method-like: identifier followed by a parameter list
        paren = None
        depth = 0
        for k, ch in enumerate(h):
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
            elif ch == "(" and depth == 0:
                paren = k
                break
        is_method = paren is not None and "=" not in h[:paren].replace("=>", "")
        if is_method and not re.search(r"\boperator\b", h[:paren]):
            pre = h[:paren].strip()
            close_p = h.rfind(")")
            params_txt = h[paren + 1:close_p]
            toks = words_before(pre)
            name = re.sub(r"<.*>$", "", toks[-1]) if toks else "?"
            mods = [t for t in toks[:-1] if t in MODIFIERS]
            rtoks = [t for t in toks[:-1] if t not in MODIFIERS]
            returns = " ".join(rtoks) or None
            # body
            if m[i] == "{":
                end = match_brace(m, i)
            elif m.startswith("=>", i):
                end = self._end_of_expression(i)
            else:
                end = i
            body_start = i
            sig_pos = pos
            if attrs:
                # the signature starts after the attribute list
                sig_pos = pos + m[pos:i].find(h[:20]) if h[:20] in m[pos:i] else pos
            la, lb, source = self.full_lines(sig_pos, end)
            params = parse_params(params_txt)
            body_m = m[body_start:end + 1]
            body_s = src[body_start:end + 1]
            fn = {
                "kind": "function", "name": name, "qualname": owner["name"] + "." + name,
                "async": "async" in mods,
                "signature": "(" + ", ".join(
                    (p["annotation"] + " " if p["annotation"] else "") + p["name"] +
                    (" = " + p["default"] if p["default"] is not None else "") for p in params) + ")",
                "params": params, "returns": returns,
                "doc": doc_before(self.lines, la), "decorators": attrs,
                "route": find_route(body_s, body_m),
                "lineno": la, "end_lineno": lb,
                "calls": find_calls(body_m, name),
                "raises": sorted(set(re.findall(r"\bthrow\s+new\s+([A-Za-z_][\w.]*)", body_m))),
                "source": source, "is_method": True, "private": "private" in mods,
                "dunder": False,
            }
            owner["methods"].append(fn)
            return end + 1, end + 1
        # property / field / event
        eq_field = top_level_assign(m, pos, i) if m[i] == "{" else None
        if eq_field is not None:
            end = self._end_of_expression(eq_field)
            decl = strip_attrs(m[pos:eq_field])[1]
            default = re.sub(r"\s+", " ", src[eq_field + 1:end].strip())
            return self._add_fields(decl, attrs, default, owner, end)
        if m[i] == "{":
            close = match_brace(m, i)
            end = close
            after = m[close + 1:close + 40].lstrip()
            default = None
            if after.startswith("="):
                eq = m.index("=", close + 1)
                end = self._end_of_expression(eq)
                default = src[eq + 1:end].strip()
        elif m.startswith("=>", i):
            end = self._end_of_expression(i)
            default = "=> " + re.sub(r"\s+", " ", src[i + 2:end].strip())
        else:
            end = i
            default = None
        decl = h
        if m[i] == ";":
            eq = top_level_assign(m, pos, i)
            if eq is not None:
                decl = m[pos:eq]
                _, decl = strip_attrs(decl)
                default = re.sub(r"\s+", " ", src[eq + 1:i].strip())
        return self._add_fields(decl, attrs, default, owner, end)

    def _add_fields(self, decl, attrs, default, owner, end):
        toks = [t for t in words_before(decl.strip()) if t not in MODIFIERS]
        if len(toks) < 2:
            return end + 1, end + 1
        names = [x.strip() for x in " ".join(toks[1:]).split(",")]
        ann = toks[0]
        for nm in names:
            if not re.match(r"^[A-Za-z_]\w*$", nm):
                continue
            label = nm
            if any("ObservableProperty" in a for a in attrs):
                prop = nm.lstrip("_")
                label = f"{nm} → {prop[:1].upper()}{prop[1:]}"
            owner["fields"].append({"name": label, "annotation": ann, "default": default})
        return end + 1, end + 1


def top_level_assign(m: str, a: int, b: int) -> int | None:
    """Position of the first '=' in m[a:b] that is an assignment at bracket depth 0."""
    depth = 0
    for k in range(a, b):
        ch = m[k]
        if ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth -= 1
        elif ch == "=" and depth <= 0:
            nxt = m[k + 1] if k + 1 < b else ""
            prv = m[k - 1] if k > a else ""
            if nxt in "=>" or prv in "=!<>+-*/%&|^?":
                continue
            return k
    return None


# --------------------------------------------------------------------------- files
def extract_cs(root: Path, path: Path) -> dict:
    rel = path.relative_to(root).as_posix()
    src = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    sc = Scanner(src)
    mod = {"path": rel, "name": "", "doc": None, "imports": [], "constants": [], "classes": [],
           "functions": [], "source": src, "loc": src.count("\n") + 1, "error": None, "lang": "cs"}
    mod["imports"] = sorted(set(l.strip() for l in src.split("\n")
                                if re.match(r"^\s*(global\s+)?using\s+(static\s+)?[\w.]+(\s*=\s*[\w.<>, ]+)?\s*;\s*$", l)))
    try:
        sc.scan(0, len(src), None)
    except Exception as e:  # keep the file in the doc even if the scanner trips
        mod["error"] = f"{type(e).__name__}: {e}"
    for t in sc.types:
        t.pop("_qual", None)
    mod["classes"] = sc.types
    stem = path.name[:-3]
    mod["name"] = (sc.namespace + "." if sc.namespace else "") + stem
    return mod


def extract_xaml(root: Path, path: Path) -> dict:
    rel = path.relative_to(root).as_posix()
    src = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    root_el = re.search(r"<\s*([\w:.]+)", re.sub(r"<\?.*?\?>|<!--.*?-->", "", src, flags=re.S))
    xclass = re.search(r'x:Class\s*=\s*"([^"]+)"', src)
    doc = "Root element: " + (root_el.group(1) if root_el else "?")
    if xclass:
        doc += "\nCode-behind: " + xclass.group(1)
    imports = re.findall(r'(xmlns(?::\w+)?\s*=\s*"[^"]*")', src)
    return {"path": rel, "name": path.name, "doc": doc, "imports": [re.sub(r"\s*=\s*", "=", i) for i in imports],
            "constants": [], "classes": [], "functions": [], "source": src,
            "loc": src.count("\n") + 1, "error": None, "lang": "xml"}


def extract_tree(root: Path, exclude: tuple[str, ...] = ()) -> list[dict]:
    mods = []
    files = [p for p in root.rglob("*") if p.is_file() and (p.suffix == ".cs" or p.suffix == ".axaml")]
    for p in sorted(files, key=lambda p: p.relative_to(root).as_posix()):
        rel = p.relative_to(root).as_posix()
        parts = rel.split("/")
        if any(x in ("bin", "obj") for x in parts) or any(rel.startswith(e) for e in exclude):
            continue
        mods.append(extract_cs(root, p) if p.suffix == ".cs" else extract_xaml(root, p))
    return mods
