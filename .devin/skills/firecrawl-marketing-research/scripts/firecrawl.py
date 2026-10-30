#!/usr/bin/env python3
"""Firecrawl helper for marketing research. Python 3.8+, standard library only.

Commands:
  set-key     Save FIRECRAWL_API_KEY into .env (asks interactively if --key is omitted)
  check-key   Verify the key and print remaining credits
  scrape      Scrape one URL (markdown / summary / links / JSON extraction)
  extract     Extract structured data from many URLs into CSV + JSON
  search      Web/news search, optionally scraping each result
  map         List all URLs of a site + section breakdown
  crawl       Crawl a site and save every page as markdown

Exit codes: 0 ok, 1 API/runtime error, 2 missing or invalid API key.
"""
import argparse
import csv
import datetime as dt
import getpass
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

API_BASE = os.environ.get("FIRECRAWL_API_URL", "https://api.firecrawl.dev").rstrip("/") + "/v2"
KEY_NAME = "FIRECRAWL_API_KEY"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent


def project_root():
    for p in SCRIPT_DIR.parents:
        if p.name == ".devin":
            return p.parent
    return Path.cwd()


def env_files():
    out = []
    for p in (Path.cwd() / ".env", project_root() / ".env", SKILL_DIR / ".env"):
        if p not in out:
            out.append(p)
    return out


def read_env_key(path):
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(?:export\s+)?%s\s*=\s*['\"]?([^'\"\s#]+)" % KEY_NAME, line)
        if m:
            return m.group(1)
    return None


def load_key():
    if os.environ.get(KEY_NAME):
        return os.environ[KEY_NAME].strip()
    for p in env_files():
        key = read_env_key(p)
        if key:
            return key
    return None


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def require_key():
    key = load_key()
    if not key:
        die(
            "NO_API_KEY: Chua co Firecrawl API key. Hay hoi nguoi dung API key (lay tai "
            "https://www.firecrawl.dev/app/api-keys), roi chay: firecrawl.py set-key",
            2,
        )
    return key


def api(method, path, body=None, key=None, retries=3, timeout=180):
    key = key or require_key()
    data = json.dumps(body).encode("utf-8") if body is not None else None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            API_BASE + path,
            data=data,
            method=method,
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                err = json.loads(raw)
            except ValueError:
                err = {"error": raw[:500]}
            if e.code in (429, 502, 503, 504) and attempt < retries:
                time.sleep(2 ** attempt * 3)
                continue
            if e.code == 401:
                die("INVALID_API_KEY: API key khong hop le hoac da bi thu hoi. Hoi nguoi dung key moi.", 2)
            if e.code == 402:
                die("PAYMENT_REQUIRED: Tai khoan Firecrawl het credit. " + str(err.get("error", "")))
            raise RuntimeError("HTTP %s: %s %s" % (e.code, err.get("code", ""), err.get("error", raw[:300])))
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(2 ** attempt * 3)
                continue
            raise RuntimeError("Network error: %s" % e)


# ---------- output helpers ----------

def slugify(text, maxlen=60):
    text = re.sub(r"^https?://(www\.)?", "", text.strip().lower()).replace("đ", "d")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return (text[:maxlen].rstrip("-")) or "item"


def out_dir(arg, cmd, label):
    if arg:
        d = Path(arg)
    else:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        d = Path.cwd() / "research" / ("%s-%s-%s" % (stamp, cmd, slugify(label, 40)))
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path, rows):
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, "%s.%s" % (prefix, k) if prefix else str(k)))
    elif isinstance(obj, list):
        if all(not isinstance(x, (dict, list)) for x in obj):
            out[prefix or "value"] = "; ".join("" if x is None else str(x) for x in obj)
        else:
            out[prefix or "value"] = json.dumps(obj, ensure_ascii=False)
    else:
        out[prefix or "value"] = obj
    return out


def save_markdown(d, url, doc, idx=None):
    md = doc.get("markdown") or ""
    if not md:
        return None
    name = ("%02d-" % idx if idx is not None else "") + slugify(url) + ".md"
    meta = doc.get("metadata") or {}
    header = "<!-- source: %s | title: %s -->\n\n" % (url, meta.get("title", ""))
    (d / name).write_text(header + md, encoding="utf-8")
    return d / name


def load_schema(arg):
    if not arg:
        return None
    p = Path(arg)
    if not p.is_file() and (SKILL_DIR / "assets" / "schemas" / arg).is_file():
        p = SKILL_DIR / "assets" / "schemas" / arg
    if not p.is_file() and (SKILL_DIR / "assets" / "schemas" / (arg + ".json")).is_file():
        p = SKILL_DIR / "assets" / "schemas" / (arg + ".json")
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(arg)


def build_formats(names, prompt=None, schema=None):
    fmts = [n.strip() for n in (names or "").split(",") if n.strip()]
    out = [f for f in fmts if f != "json"]
    if prompt or schema or "json" in fmts:
        j = {"type": "json"}
        if prompt:
            j["prompt"] = prompt
        if schema:
            j["schema"] = schema
        out.append(j)
    return out or ["markdown"]


def scrape_body(url, a, formats):
    body = {"url": url, "formats": formats, "onlyMainContent": not a.full_page}
    if a.country:
        body["location"] = {"country": a.country.upper()}
        if a.lang:
            body["location"]["languages"] = [a.lang]
    if a.wait:
        body["waitFor"] = a.wait
    if getattr(a, "max_age", None) is not None:
        body["maxAge"] = a.max_age
    return body


def preview(obj, limit=1500):
    s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=2)
    return s if len(s) <= limit else s[:limit] + "\n... (cat bot, xem file day du)"


# ---------- commands ----------

def cmd_set_key(a):
    key = (a.key or "").strip() or getpass.getpass("Nhap Firecrawl API key (fc-...): ").strip()
    if not key.startswith("fc-"):
        die("INVALID_API_KEY: Key Firecrawl phai bat dau bang 'fc-'.", 2)
    path = Path(a.env_file) if a.env_file else project_root() / ".env"
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    lines = [l for l in lines if not re.match(r"^\s*(?:export\s+)?%s\s*=" % KEY_NAME, l)]
    lines.append("%s=%s" % (KEY_NAME, key))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)
    gi = path.parent / ".gitignore"
    gi_lines = gi.read_text(encoding="utf-8").splitlines() if gi.is_file() else []
    if ".env" not in gi_lines:
        gi.write_text("\n".join(gi_lines + [".env"]) + "\n", encoding="utf-8")
    print("Da luu %s vao %s (quyen 600, da them vao .gitignore)." % (KEY_NAME, path))
    if not a.no_check:
        check(key)


def check(key):
    try:
        res = api("GET", "/team/credit-usage", key=key, retries=1)
        d = res.get("data") or {}
        print("KEY_OK: remainingCredits=%s planCredits=%s" % (d.get("remainingCredits"), d.get("planCredits")))
    except RuntimeError as e:
        if "HTTP 404" in str(e):
            print("KEY_OK: key hop le (khong lay duoc thong tin credit).")
        else:
            die("CHECK_FAILED: %s" % e)


def cmd_check_key(a):
    check(require_key())


def cmd_scrape(a):
    schema = load_schema(a.schema)
    formats = build_formats(a.formats, a.prompt, schema)
    res = api("POST", "/scrape", scrape_body(a.url, a, formats))
    doc = res.get("data") or {}
    d = out_dir(a.out_dir, "scrape", a.url)
    write_json(d / (slugify(a.url) + ".json"), doc)
    md = save_markdown(d, a.url, doc)
    meta = doc.get("metadata") or {}
    print("URL: %s\nTitle: %s\nStatus: %s" % (a.url, meta.get("title"), meta.get("statusCode")))
    print("Saved: %s" % d)
    if md:
        print("Markdown: %s (%d ky tu)" % (md, len(doc.get("markdown", ""))))
    if doc.get("summary"):
        print("\nSummary:\n" + preview(doc["summary"], 2000))
    if doc.get("json") is not None:
        print("\nJSON:\n" + preview(doc["json"], 3000))
    if doc.get("links"):
        print("\nLinks: %d (xem file .json)" % len(doc["links"]))


def read_urls(a):
    urls = list(a.urls or [])
    if a.urls_file:
        for line in Path(a.urls_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line.split(",")[0].strip())
    if not urls:
        die("Can it nhat 1 URL (tham so hoac --urls-file).")
    return urls


def explode_rows(url, data, rows_key):
    base = {"source_url": url}
    if not isinstance(data, dict):
        return [{**base, **flatten(data)}]
    key = rows_key
    if not key:
        lists = [k for k, v in data.items() if isinstance(v, list) and v and all(isinstance(x, dict) for x in v)]
        key = lists[0] if len(lists) == 1 else None
    if key and isinstance(data.get(key), list) and data[key]:
        shared = flatten({k: v for k, v in data.items() if k != key})
        return [{**base, **shared, **flatten(item)} for item in data[key]]
    return [{**base, **flatten(data)}]


def cmd_extract(a):
    urls = read_urls(a)
    schema = load_schema(a.schema)
    if not (a.prompt or schema):
        die("Can --prompt hoac --schema de trich xuat du lieu.")
    formats = build_formats("markdown" if a.keep_markdown else "", a.prompt, schema)
    d = out_dir(a.out_dir, "extract", urls[0] if len(urls) == 1 else "%d-urls" % len(urls))

    def one(u):
        try:
            return u, (api("POST", "/scrape", scrape_body(u, a, formats)).get("data") or {}), None
        except RuntimeError as e:
            return u, None, str(e)

    rows, raw, errors = [], [], []
    with ThreadPoolExecutor(max_workers=max(1, a.workers)) as ex:
        for u, doc, err in ex.map(one, urls):
            if err:
                errors.append({"url": u, "error": err})
                print("FAIL %s -> %s" % (u, err))
                continue
            raw.append({"url": u, "json": doc.get("json"), "metadata": doc.get("metadata")})
            if a.keep_markdown:
                save_markdown(d, u, doc)
            new = explode_rows(u, doc.get("json"), a.rows_key)
            rows.extend(new)
            print("OK   %s -> %d dong" % (u, len(new)))
    write_json(d / "extract.json", {"prompt": a.prompt, "schema": schema, "results": raw, "errors": errors})
    if rows:
        write_csv(d / "extract.csv", rows)
    print("\nSaved: %s\nCSV: %s (%d dong)\nLoi: %d URL" % (d, d / "extract.csv", len(rows), len(errors)))
    if rows:
        print("\nPreview:\n" + preview(rows[:5], 2500))


def cmd_search(a):
    body = {"query": a.query, "limit": a.limit, "sources": [{"type": s.strip()} for s in a.sources.split(",")]}
    if a.country:
        body["country"] = a.country.upper()
    if a.location:
        body["location"] = a.location
    if a.tbs:
        body["tbs"] = a.tbs
    if a.include_domains:
        body["includeDomains"] = a.include_domains.split(",")
    if a.exclude_domains:
        body["excludeDomains"] = a.exclude_domains.split(",")
    if a.scrape:
        body["scrapeOptions"] = {"formats": ["markdown"], "onlyMainContent": True}
    res = api("POST", "/search", body, timeout=300)
    data = res.get("data") or {}
    if isinstance(data, list):
        data = {"web": data}
    d = out_dir(a.out_dir, "search", a.query)
    rows = []
    for source, items in data.items():
        if not isinstance(items, list):
            continue
        for i, it in enumerate(items, 1):
            url = it.get("url") or it.get("imageUrl") or ""
            md = save_markdown(d, url, it, len(rows) + 1) if a.scrape else None
            rows.append({
                "rank": i,
                "source": source,
                "title": it.get("title") or (it.get("metadata") or {}).get("title", ""),
                "url": url,
                "description": it.get("description") or it.get("snippet") or "",
                "date": it.get("date", ""),
                "markdown_file": md.name if md else "",
            })
    write_json(d / "search.json", res)
    if rows:
        write_csv(d / "search.csv", rows)
    print("Query: %s | %d ket qua | Saved: %s\n" % (a.query, len(rows), d))
    for r in rows:
        print("[%s #%s] %s\n    %s\n    %s" % (r["source"], r["rank"], r["title"], r["url"], (r["description"] or "")[:200]))


def cmd_map(a):
    body = {"url": a.url, "limit": a.limit}
    if a.search:
        body["search"] = a.search
    res = api("POST", "/map", body)
    links = [l if isinstance(l, dict) else {"url": l} for l in res.get("links", [])]
    d = out_dir(a.out_dir, "map", a.url)
    write_json(d / "map.json", links)
    if links:
        write_csv(d / "map.csv", links)
    sections = Counter()
    for l in links:
        parts = [p for p in urlparse(l["url"]).path.split("/") if p]
        sections["/" + parts[0] if parts else "/"] += 1
    print("Site: %s | %d URL | Saved: %s\n" % (a.url, len(links), d))
    print("Phan bo theo section (top 25):")
    for sec, n in sections.most_common(25):
        print("  %-40s %d" % (sec, n))
    print("\nVi du URL:")
    for l in links[: a.show]:
        print("  %s  %s" % (l["url"], ("- " + l["title"]) if l.get("title") else ""))


def cmd_crawl(a):
    body = {
        "url": a.url,
        "limit": a.limit,
        "scrapeOptions": {"formats": ["markdown"], "onlyMainContent": True},
    }
    if a.include:
        body["includePaths"] = a.include
    if a.exclude:
        body["excludePaths"] = a.exclude
    if a.max_depth is not None:
        body["maxDiscoveryDepth"] = a.max_depth
    if a.entire_domain:
        body["crawlEntireDomain"] = True
    job = api("POST", "/crawl", body)
    job_id = job.get("id")
    if not job_id:
        die("Khong tao duoc crawl job: %s" % job)
    print("Crawl job %s dang chay..." % job_id, flush=True)
    deadline = time.time() + a.wait_max
    while True:
        st = api("GET", "/crawl/%s" % job_id)
        status = st.get("status")
        print("  status=%s %s/%s" % (status, st.get("completed"), st.get("total")), flush=True)
        if status in ("completed", "failed", "cancelled"):
            break
        if time.time() > deadline:
            die("Het thoi gian cho. Job id: %s (co the kiem tra lai sau)." % job_id)
        time.sleep(5)
    docs = list(st.get("data") or [])
    nxt = st.get("next")
    while nxt:
        page = api("GET", nxt.split("/v2", 1)[1] if "/v2" in nxt else nxt)
        docs.extend(page.get("data") or [])
        nxt = page.get("next")
    d = out_dir(a.out_dir, "crawl", a.url)
    rows = []
    for i, doc in enumerate(docs, 1):
        meta = doc.get("metadata") or {}
        url = meta.get("sourceURL") or meta.get("url") or ""
        md = save_markdown(d, url, doc, i)
        rows.append({"n": i, "url": url, "title": meta.get("title", ""),
                     "chars": len(doc.get("markdown") or ""), "file": md.name if md else ""})
    if rows:
        write_csv(d / "index.csv", rows)
    print("\nStatus: %s | %d trang | Saved: %s" % (status, len(rows), d))
    for r in rows[:50]:
        print("  %3d. %s (%s ky tu) %s" % (r["n"], r["url"], r["chars"], r["title"]))


def add_scrape_opts(p):
    p.add_argument("--country", help="Ma quoc gia ISO, vd VN, US")
    p.add_argument("--lang", help="Ngon ngu uu tien, vd vi-VN (dung kem --country)")
    p.add_argument("--full-page", action="store_true", help="Lay ca header/footer/nav (mac dinh chi noi dung chinh)")
    p.add_argument("--wait", type=int, help="Cho them N ms truoc khi lay noi dung (trang JS nang)")
    p.add_argument("--max-age", type=int, help="Chap nhan cache tre toi da N ms (0 = luon lay moi)")
    p.add_argument("--out-dir")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("set-key")
    p.add_argument("--key")
    p.add_argument("--env-file")
    p.add_argument("--no-check", action="store_true")
    p.set_defaults(fn=cmd_set_key)

    sub.add_parser("check-key").set_defaults(fn=cmd_check_key)

    p = sub.add_parser("scrape")
    p.add_argument("url")
    p.add_argument("--formats", default="markdown", help="markdown,summary,links,html,json")
    p.add_argument("--prompt", help="Prompt trich xuat JSON")
    p.add_argument("--schema", help="File JSON schema, ten schema trong assets/schemas, hoac chuoi JSON")
    add_scrape_opts(p)
    p.set_defaults(fn=cmd_scrape)

    p = sub.add_parser("extract")
    p.add_argument("urls", nargs="*")
    p.add_argument("--urls-file")
    p.add_argument("--prompt")
    p.add_argument("--schema")
    p.add_argument("--rows-key", help="Truong mang can tach thanh nhieu dong CSV (vd plans)")
    p.add_argument("--keep-markdown", action="store_true")
    p.add_argument("--workers", type=int, default=3)
    add_scrape_opts(p)
    p.set_defaults(fn=cmd_extract)

    p = sub.add_parser("search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--sources", default="web", help="web,news,images")
    p.add_argument("--country")
    p.add_argument("--location", help="vd 'Vietnam' hoac 'Ho Chi Minh City,Vietnam'")
    p.add_argument("--tbs", help="qdr:d|qdr:w|qdr:m|qdr:y hoac cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY")
    p.add_argument("--include-domains")
    p.add_argument("--exclude-domains")
    p.add_argument("--scrape", action="store_true", help="Scrape noi dung markdown cua tung ket qua")
    p.add_argument("--out-dir")
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("map")
    p.add_argument("url")
    p.add_argument("--search", help="Loc/sap xep URL theo tu khoa, vd pricing, blog")
    p.add_argument("--limit", type=int, default=5000)
    p.add_argument("--show", type=int, default=30)
    p.add_argument("--out-dir")
    p.set_defaults(fn=cmd_map)

    p = sub.add_parser("crawl")
    p.add_argument("url")
    p.add_argument("--limit", type=int, default=20, help="So trang toi da (mac dinh 20 de tiet kiem credit)")
    p.add_argument("--include", nargs="*", help="Regex path can lay, vd 'blog/.*'")
    p.add_argument("--exclude", nargs="*")
    p.add_argument("--max-depth", type=int)
    p.add_argument("--entire-domain", action="store_true")
    p.add_argument("--wait-max", type=int, default=900)
    p.add_argument("--out-dir")
    p.set_defaults(fn=cmd_crawl)

    a = ap.parse_args()
    try:
        a.fn(a)
    except RuntimeError as e:
        die("ERROR: %s" % e)


if __name__ == "__main__":
    main()
