#!/usr/bin/env python3
"""
arXiv fetcher — Quantum Computing & Spin Qubits
Saves results to papers.json
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json, datetime, os, time

# ── Your field configuration ──────────────────────────────────────────────────

# Best arXiv categories for spin qubits + quantum computing
CATEGORIES = [
    "quant-ph",           # quantum physics (main QC category)
    "cond-mat.mes-hall",  # mesoscale — where spin qubit experiments live
]

# Focused spin-qubit keywords (title search only — keeps URL short)
KEYWORDS = [
    "spin qubit",
    "spin-orbit qubit",
    "hole spin qubit",
    "singlet triplet qubit",
    "exchange interaction qubit",
    "quantum dot qubit",
    "silicon spin qubit",
    "germanium spin qubit",
    "GaAs spin qubit",
    "two-qubit gate spin",
]

MAX_RESULTS = 50
OUTPUT_FILE = "papers.json"
ARXIV_API   = "https://export.arxiv.org/api/query"
NS          = {"atom": "http://www.w3.org/2005/Atom"}
USER_AGENT  = "spin-qubit-aggregator/1.0 (personal research tool)"

# ── Query builder ─────────────────────────────────────────────────────────────

def build_query():
    cats = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    kws  = " OR ".join(f'ti:"{k}"' for k in KEYWORDS)
    return f"({cats}) AND ({kws})"

# ── Fetcher ───────────────────────────────────────────────────────────────────

def fetch(query):
    params = urllib.parse.urlencode({
        "search_query": query,
        "start":        0,
        "max_results":  MAX_RESULTS,
        "sortBy":       "submittedDate",
        "sortOrder":    "descending",
    })
    url = f"{ARXIV_API}?{params}"
    print(f"[fetch] querying arXiv…")
    print(f"[fetch] {url[:100]}…\n")

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 20 * attempt
                print(f"[warn] rate limited — waiting {wait}s (attempt {attempt}/3)…")
                time.sleep(wait)
            else:
                raise
    else:
        raise SystemExit("Still rate-limited after 3 retries. Wait a few minutes and try again.")

    entries = ET.fromstring(raw).findall("atom:entry", NS)
    print(f"[fetch] {len(entries)} papers returned\n")

    papers = []
    for e in entries:
        try:
            abs_url = next(
                (l.get("href","") for l in e.findall("atom:link", NS) if l.get("rel") == "alternate"),
                ""
            )
            if not abs_url:
                continue

            papers.append({
                "id":         abs_url.split("/abs/")[-1],
                "title":      (e.findtext("atom:title",   "", NS) or "").strip().replace("\n", " "),
                "authors":    [a.findtext("atom:name", "", NS).strip() for a in e.findall("atom:author", NS)],
                "abstract":   (e.findtext("atom:summary", "", NS) or "").strip().replace("\n", " "),
                "date":       (e.findtext("atom:published","", NS) or "")[:10],
                "abs_url":    abs_url,
                "pdf_url":    abs_url.replace("/abs/", "/pdf/") + ".pdf",
                "categories": [c.get("term","") for c in e.findall("atom:category", NS)],
            })
        except Exception as ex:
            print(f"[warn] skipped one entry: {ex}")

    return papers

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Polite delay — arXiv recommends ~3s between requests
    print("[info] waiting 3s before request (arXiv rate limit courtesy)…")
    time.sleep(3)

    papers = fetch(build_query())

    # Deduplicate
    seen, unique = set(), []
    for p in papers:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    # Print preview
    print("─" * 60)
    for p in unique[:5]:
        print(f"  {p['date']}  {p['title'][:70]}")
    if len(unique) > 5:
        print(f"  … and {len(unique)-5} more")
    print("─" * 60)

    # Save
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "total":        len(unique),
            "papers":       unique,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[done] saved {len(unique)} papers → {out}")
    print(f"[next] run:  python3 -m http.server 8080  then open http://localhost:8080")

if __name__ == "__main__":
    main()
