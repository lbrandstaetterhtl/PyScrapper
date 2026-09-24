"""Build the three HTML documentation files in HTML_Doku/ from the current source tree.

    python HTML_Doku/_generator/build_docs.py            # all three
    python HTML_Doku/_generator/build_docs.py LocalServer

Everything that can be derived from the code (module pages, signatures, source, call graph,
endpoint list, database schema, the client's server calls, statistics) is extracted on every run.
The explanatory prose lives in content/<package>/ and is merged in:

    meta.json     title, navigation, the fixed search entries
    pages/*.html  one file per doc page; {{stat:...}} and {{gen:...}} placeholders are filled here
    flows.json    the interactive program flows
    notes.json    notes shown at the top of individual module pages
"""
from __future__ import annotations

import html
import json
import re
import sqlite3
import sys
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC_DIR = HERE.parent
REPO = DOC_DIR.parent
sys.path.insert(0, str(HERE))

import extract_cs  # noqa: E402
import extract_py  # noqa: E402

PACKAGES = {
    "PythonModule": {"lang": "py", "exclude": ()},
    "LocalServer": {"lang": "py", "exclude": ()},
    "PyScrapperDesktopApp": {"lang": "cs", "exclude": ("Notes/", "installer/")},
}


def esc(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def mod_href(path: str, anchor: str | None = None) -> str:
    h = "#/m/" + urllib.parse.quote(path, safe="")
    return h + ("#" + anchor if anchor else "")


def src_href(path: str, line: int) -> str:
    return "#/src/" + urllib.parse.quote(path, safe="") + f"#L{line}"


# --------------------------------------------------------------------------- common
def all_functions(mod: dict):
    for f in mod["functions"]:
        yield f
    for c in mod["classes"]:
        for f in c["methods"]:
            yield f


def build_xref(mods: list[dict]) -> dict:
    defined = set()
    for m in mods:
        for c in m["classes"]:
            defined.add(c["name"])
        for f in all_functions(m):
            defined.add(f["name"])
    xref: dict[str, list] = {}
    for m in mods:
        for f in all_functions(m):
            for call in f["calls"]:
                key = call.split(".")[-1]
                if key not in defined or key == f["name"] or key.startswith("__"):
                    continue
                entry = [m["path"], f["qualname"]]
                bucket = xref.setdefault(key, [])
                if entry not in bucket:
                    bucket.append(entry)
    return xref


def stats_block(items: list[tuple[str, str]]) -> str:
    return '<div class="stats">' + "".join(
        f'<div class="stat"><b>{esc(v)}</b><span>{esc(k)}</span></div>' for k, v in items) + "</div>"


def pills(groups: dict, total: int) -> str:
    h = '<div class="epfilter">\n  <span class="pill on" data-f="*">all ' + str(total) + "</span>\n  "
    h += "".join(f'<span class="pill" data-f="{esc(g)}">{esc(g)} {len(v)}</span>' for g, v in groups.items() if v)
    methods = sorted({e["method"] for v in groups.values() for e in v})
    h += "\n  " + "".join(f'<span class="pill" data-f="{m}">{m}</span>' for m in methods) + "\n</div>\n"
    return h


def path_html(path: str) -> str:
    return re.sub(r"(\{[^}]*\})", r'<span class="prm">\1</span>', esc(path))


EP_SEARCH_INPUT = (
    '<input id="epq" placeholder="{ph}" spellcheck="false"\n'
    '       style="width:100%;height:32px;padding:0 10px;border:1px solid var(--line2);border-radius:6px;'
    'background:var(--surface2);color:var(--ink);font-family:var(--mono);font-size:12.5px;margin-bottom:6px">\n'
)


def ep_card(e: dict, table_head: list[str]) -> str:
    s = f'{e["method"]} {e["path"]} {e["fn"]}() {e["group"]}'.lower()
    h = (f'<div class="ep" data-m="{e["method"]}" data-g="{esc(e["group"])}" data-s="{esc(s)}">'
         f'<div class="ephead"><span class="m m-{e["method"]}">{e["method"]}</span>'
         f'<span class="eppath">{path_html(e["path"])}</span><span class="epfn">{esc(e["fn"])}()</span></div>'
         '<div class="epbody hidden"><div class="chips" style="margin:11px 0">')
    h += "".join(f'<span class="tag{" warn" if w else ""}">{esc(t)}</span>' for t, w in e["tags"])
    h += "</div>"
    if e["rows"]:
        h += ('<div class="tbl-wrap"><table><thead><tr>' + "".join(f"<th>{c}</th>" for c in table_head) +
              "</tr></thead><tbody>")
        for row in e["rows"]:
            cells = ""
            for i, c in enumerate(row):
                mono = ' class="mono"' if i != 1 or len(row) == 2 else ""
                cells += f"<td{mono}>{esc(c)}</td>"
            h += "<tr>" + cells + "</tr>"
        h += "</tbody></table></div>"
    h += (f'<div style="margin-top:11px"><a class="tag" href="{e["href"]}">Details &amp; source</a>'
          f'<a class="tag" href="{e["src"]}">line {e["line"]}</a></div></div></div>')
    return h


# --------------------------------------------------------------------------- LocalServer
SERVER_GROUPS = ["Download & streaming", "Search", "Auth", "CRUD", "System"]
SERVER_GROUP_IDS = {"Download & streaming": "gdown", "Search": "gsearch", "Auth": "gauth",
                    "CRUD": "gcrud", "System": "gsys"}


def server_group(path: str) -> str:
    if path.startswith(("/download", "/stream")):
        return "Download & streaming"
    if path.startswith("/search"):
        return "Search"
    if path.startswith(("/login", "/register", "/logout")):
        return "Auth"
    if path in ("/", "/command", "/health"):
        return "System"
    return "CRUD"


def server_endpoints(mods: list[dict]) -> list[dict]:
    server = next(m for m in mods if m["path"] == "server.py")
    pyd = {c["name"] for m in mods for c in m["classes"] if c["flavor"] == "pydantic"}
    out = []
    for f in server["functions"]:
        r = f["route"]
        if not r:
            continue
        deco = r["decorator"]
        tags = []
        user = any("Security(require_user)" in (p["default"] or "") for p in f["params"]) or \
            "Security(require_user)" in deco
        if "Security(require_admin)" in deco:
            tags.append(("X-Admin-Key", False))
        if user:
            tags.append(("X-User-Key + Auth", False))
        if any("Security(require_auth)" in (p["default"] or "") for p in f["params"]):
            tags.append(("Auth", False))
        if not tags:
            tags.append(("reachable without a key", True))
        m = re.search(r"response_model=([\w\[\].]+)", deco)
        if m:
            tags.append(("→ " + m.group(1), False))
        tags += [(x, False) for x in f["raises"][:4]]
        path_params = set(re.findall(r"\{(\w+)\}", r["path"]))
        rows = []
        for p in f["params"]:
            d = p["default"] or ""
            if d.startswith(("Security(", "Depends(")) or (p["annotation"] or "") == "Request":
                continue
            ann = p["annotation"] or ""
            if p["name"] in path_params:
                where = "Path"
            elif ann.split(".")[-1] in pyd or ann.startswith("requests."):
                where = "Body"
            elif d.startswith("Header("):
                where = "Header"
            else:
                where = "Query"
            rows.append((p["name"], where, ann or "—"))
        out.append({"method": r["method"], "path": r["path"], "fn": f["name"], "group": server_group(r["path"]),
                    "tags": tags, "rows": rows, "href": mod_href("server.py", f["name"]),
                    "src": src_href("server.py", f["lineno"]), "line": f["lineno"]})
    return out


def gen_server_endpoints(eps: list[dict]) -> str:
    groups = {g: [e for e in eps if e["group"] == g] for g in SERVER_GROUPS}
    h = pills(groups, len(eps)) + EP_SEARCH_INPUT.format(ph="search path or handler")
    for g, items in groups.items():
        if not items:
            continue
        h += f'\n<h2 id="{SERVER_GROUP_IDS[g]}">{esc(g)}</h2>\n'
        h += "\n".join(ep_card(e, ["Name", "In", "Type"]) for e in items) + "\n"
    return h


def server_tables(mods: list[dict]) -> list[dict]:
    """Run the CREATE TABLE statements of create_app_tables against an in-memory database."""
    server = next(m for m in mods if m["path"] == "server.py")
    fn = next(f for f in server["functions"] if f["name"] == "create_app_tables")
    stmts = re.findall(r'"""\s*(CREATE TABLE.*?)"""', fn["source"], re.S | re.I)
    db = sqlite3.connect(":memory:")
    tables = []
    for sql in stmts:
        db.execute(sql)
        name = re.search(r"CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(\w+)", sql, re.I).group(1)
        body = sql[sql.index("(") + 1:sql.rindex(")")]
        cols, extra = [], []
        for part in extract_cs.split_top(body):
            part = " ".join(part.split())
            if not part:
                continue
            if re.match(r"(PRIMARY KEY|FOREIGN KEY|UNIQUE|CHECK|CONSTRAINT)\b", part, re.I):
                extra.append(part)
                continue
            bits = part.split(None, 2)
            rest = bits[2].upper() if len(bits) > 2 else ""
            flags = []
            if "PRIMARY KEY" in rest:
                flags.append(("PK", "b-enum"))
            if "UNIQUE" in rest:
                flags.append(("UNIQUE", "b-pyd"))
            if "NOT NULL" in rest or "PRIMARY KEY" in rest:
                flags.append(("NOT NULL", "b-priv"))
            m = re.search(r"DEFAULT\s+(\S+)", rest)
            if m:
                flags.append(("DEFAULT " + m.group(1), "b-data"))
            cols.append((bits[0], bits[1] if len(bits) > 1 else "", flags))
        tables.append({"name": name, "cols": cols, "extra": extra})
    return tables


def gen_db_tables(tables: list[dict]) -> str:
    h = ""
    for t in tables:
        h += f'<h3 id="t{esc(t["name"])}">{esc(t["name"])}</h3>\n'
        h += ('<div class="tbl-wrap"><table><thead><tr><th>Column</th><th>Type</th><th>Constraints</th>'
              '</tr></thead><tbody>')
        for name, typ, flags in t["cols"]:
            h += (f'<tr><td class="mono">{esc(name)}</td><td class="mono">{esc(typ)}</td><td><div class="chips">' +
                  "".join(f'<span class="b {c}">{esc(label)}</span>' for label, c in flags) + "</div></td></tr>")
        h += "</tbody></table></div>\n"
        if t["extra"]:
            h += ('<div class="chips" style="margin:9px 0 2px">' +
                  "".join(f'<span class="tag">{esc(x)}</span>' for x in t["extra"]) + "</div>\n")
    return h


# --------------------------------------------------------------------------- Desktop app
CLIENT_GROUPS = ["Auth", "Download & search", "Data", "System"]
CLIENT_GROUP_IDS = {"Auth": "gauth", "Download & search": "gdown", "Data": "gdata", "System": "gsys"}


def client_calls(mods: list[dict]) -> list[dict]:
    out = []
    for m in mods:
        for c in m["classes"]:
            for f in c["methods"]:
                r = f["route"]
                if not r:
                    continue
                path = r["path"]
                if path == "/{…}":
                    dyn = re.search(r"ServerPort\}(\{[^}]+\})", r["decorator"])
                    path = dyn.group(1) if dyn else path
                name = f["name"]
                if path.startswith(("/login", "/logout", "/register")):
                    group = "Auth"
                elif path.startswith(("/download", "/search")) or name in ("GetDownloadProgress", "GetFileFromStream"):
                    group = "Download & search"
                elif path.startswith("/health"):
                    group = "System"
                else:
                    group = "Data"
                tags = [("→ " + f["returns"], False)] if f["returns"] else []
                src = f["source"]
                for hdr in ("X-Admin-Key", "X-User-Key", "Auth"):
                    if re.search(r'"' + re.escape(hdr) + r'"', src, re.I):
                        tags.append((hdr, False))
                rows = [(p["name"], p["annotation"] or "—") for p in f["params"]]
                out.append({"method": r["method"], "path": path, "fn": f["qualname"], "group": group,
                            "tags": tags, "rows": rows, "href": mod_href(m["path"], f["qualname"]),
                            "src": src_href(m["path"], f["lineno"]), "line": f["lineno"]})
    return out


def gen_client_calls(calls: list[dict]) -> str:
    groups = {g: [e for e in calls if e["group"] == g] for g in CLIENT_GROUPS}
    h = pills(groups, len(calls)) + EP_SEARCH_INPUT.format(ph="search path or method")
    for g, items in groups.items():
        if not items:
            continue
        h += f'\n<h2 id="{CLIENT_GROUP_IDS[g]}">{esc(g)}</h2>\n'
        h += "\n".join(ep_card(e, ["Parameter", "Type"]) for e in items) + "\n"
    return h


# --------------------------------------------------------------------------- PythonModule
def provider_matrix(mods: list[dict]) -> str:
    settings = next(m for m in mods if m["path"] == "models/settings.py")
    consts = {c["name"]: c["value"] for c in settings["constants"]}

    def mapping(name):
        return dict(re.findall(r"ProviderTypes\.(\w+):\s*p\.([\w.]+)", consts.get(name, "")))

    get_map, search_map = mapping("PROVIDER_GETRESULTS_MAPPING"), mapping("PROVIDER_SEARCH_MAPPING")
    enum = next(c for c in settings["classes"] if c["name"] == "ProviderTypes")
    by_path = {m["path"]: m for m in mods}
    rows = ""
    for member in enum["fields"]:
        name = member["name"]
        if name == "ERROR":
            continue
        target = get_map.get(name) or search_map.get(name)
        if not target:
            rows += (f'<tr><td class="mono">{esc(name)}</td><td><span class="b b-priv">no</span></td>'
                     f'<td><span class="b b-priv">no</span></td><td>&mdash;</td>'
                     f'<td class="mono" style="font-size:11.5px">declared in ProviderTypes only</td></tr>')
            continue
        module = target.split(".")[0]
        files = [p for p in by_path if p == f"providers/{module}.py" or
                 (p.startswith(f"providers/{module}/") and p != f"providers/{module}/{module}.py")]
        link = f"providers/{module}/__init__.py" if f"providers/{module}/__init__.py" in by_path else f"providers/{module}.py"
        loc = sum(by_path[p]["loc"] for p in files)
        helpers = sorted({f["name"] for p in files for f in by_path[p]["functions"] if f["private"]})

        def yn(ok):
            return '<span class="b b-data">yes</span>' if ok else '<span class="b b-priv">no</span>'

        rows += (f'<tr><td class="mono"><a class="x" href="{mod_href(link)}">{esc(name)}</a></td>'
                 f'<td>{yn(name in search_map)}</td><td>{yn(name in get_map)}</td><td>{loc}</td>'
                 f'<td class="mono" style="font-size:11.5px">{esc(", ".join(helpers)) if helpers else "&mdash;"}</td></tr>')
    return ('<div class="tbl-wrap"><table><thead><tr><th>Provider</th><th>Search</th><th>Resolve</th>'
            '<th>Lines</th><th>Internal helpers</th></tr></thead><tbody>' + rows + '</tbody></table></div>')


# --------------------------------------------------------------------------- build
def build(pkg: str) -> Path:
    cfg = PACKAGES[pkg]
    root = REPO / pkg
    content = HERE / "content" / pkg
    meta = json.loads((content / "meta.json").read_text(encoding="utf-8"))
    if cfg["lang"] == "py":
        mods = extract_py.extract_tree(root, cfg["exclude"])
    else:
        mods = extract_cs.extract_tree(root, cfg["exclude"])

    total_loc = sum(m["loc"] for m in mods)
    stats = {
        "modules": len(mods),
        "files": len(mods),
        "loc": total_loc,
        "classes": sum(len(m["classes"]) for m in mods),
        "functions": sum(len(list(all_functions(m))) for m in mods),
    }
    gen: dict[str, str] = {}
    pages_index = list(meta["pages_index"])

    if pkg == "LocalServer":
        eps = server_endpoints(mods)
        tables = server_tables(mods)
        server = next(m for m in mods if m["path"] == "server.py")
        stats.update({"endpoints": len(eps), "server_loc": server["loc"], "tables": len(tables),
                      "tests": len([m for m in mods if m["path"].startswith("tests/")])})
        for g in SERVER_GROUPS:
            stats["ep:" + g] = len([e for e in eps if e["group"] == g])
        gen["endpoints"] = gen_server_endpoints(eps)
        gen["db_tables"] = gen_db_tables(tables)
        pages_index += [{"title": f'{e["method"]} {e["path"]}', "hash": e["href"], "sub": e["fn"]} for e in eps]
    elif pkg == "PyScrapperDesktopApp":
        calls = client_calls(mods)
        stats.update({"types": stats["classes"], "calls": len(calls),
                      "windows": len([m for m in mods if m["path"].startswith("Views/") and m["path"].endswith(".axaml")])})
        for g in CLIENT_GROUPS:
            stats["call:" + g] = len([e for e in calls if e["group"] == g])
        gen["api_calls"] = gen_client_calls(calls)
        pages_index += [{"title": f'{e["method"]} {e["path"]}', "hash": e["href"], "sub": e["fn"]} for e in calls]
    else:
        gen["provider_matrix"] = provider_matrix(mods)

    by_path = {m["path"]: m for m in mods}

    def fill(text: str) -> str:
        def stat(m):
            key = m.group(1)
            if key.startswith("loc:"):
                return str(by_path[key[4:]]["loc"])
            if key not in stats:
                raise KeyError(f"{pkg}: unknown stat placeholder {key!r}")
            return str(stats[key])

        def gen_(m):
            if m.group(1) not in gen:
                raise KeyError(f"{pkg}: unknown gen placeholder {m.group(1)!r}")
            return gen[m.group(1)]

        text = re.sub(r"\{\{stat:([^}]+)\}\}", stat, text)
        return re.sub(r"\{\{gen:([^}]+)\}\}", gen_, text)

    def const_anchors(text: str) -> str:
        """Constants have no element of their own; point links to them at the constants table."""
        def sub(m):
            mod = by_path.get(urllib.parse.unquote(m.group(1)))
            if mod and any(c["name"] == m.group(2) for c in mod["constants"]):
                return f"#/m/{m.group(1)}#__consts"
            return m.group(0)
        return re.sub(r"#/m/([^\"#\s]+)#([A-Za-z_]\w*)", sub, text)

    pages = {p.stem: const_anchors(fill(p.read_text(encoding="utf-8")))
             for p in sorted((content / "pages").glob("*.html"))}
    flows = json.loads(const_anchors(fill((content / "flows.json").read_text(encoding="utf-8"))))
    notes = json.loads(const_anchors((content / "notes.json").read_text(encoding="utf-8")))

    # links into modules that no longer exist are a sign the prose went stale
    for where, text in list(pages.items()) + [("flows", json.dumps(flows)), ("notes", json.dumps(notes))]:
        for target in re.findall(r'#/m/([^"#]+)(?:#([^"]+))?', text):
            path = urllib.parse.unquote(target[0])
            if path not in by_path:
                print(f"  warning: {pkg}/{where} links to missing module {path}")
            elif target[1]:
                mod = by_path[path]
                anchors = {c["name"] for c in mod["classes"]} | {f["name"] for f in mod["functions"]} | {
                    c["name"] + "." + f["name"] for c in mod["classes"] for f in c["methods"]} | {"__consts"}
                if target[1] not in anchors:
                    print(f"  warning: {pkg}/{where} links to missing symbol {path}#{target[1]}")
    for path in notes:
        if path not in by_path:
            print(f"  warning: {pkg}/notes.json has a note for missing module {path}")

    payload = {
        "package": pkg, "modules": mods, "xref": build_xref(mods), "total_loc": total_loc,
        "lang": cfg["lang"], "pages": pages, "pages_index": pages_index, "flows": flows, "notes": notes,
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    nav = "".join(f'<a class="navlink" href="{n["href"]}">{n["label"]}</a>' for n in meta["nav"])
    out = (HERE / "template.html").read_text(encoding="utf-8")
    for key, value in (("TITLE", meta["title"]), ("BRAND", meta["brand"]), ("PACKAGE", meta["package"]),
                       ("PROMPT", meta["prompt"]), ("NAV", nav)):
        out = out.replace("{{" + key + "}}", value)
    out = out.replace("{{PAYLOAD}}", data)
    target = DOC_DIR / f"{pkg}.html"
    target.write_text(out, encoding="utf-8")
    print(f"{target.relative_to(REPO)}: {len(mods)} files, {total_loc} lines, {len(out) // 1024} KiB")
    return target


def main(argv: list[str]) -> None:
    for pkg in argv or list(PACKAGES):
        if pkg not in PACKAGES:
            raise SystemExit(f"unknown package {pkg!r}, expected one of {', '.join(PACKAGES)}")
        build(pkg)


if __name__ == "__main__":
    main(sys.argv[1:])
