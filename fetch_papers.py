#!/usr/bin/env python3
"""
arXiv Paper Fetcher
Queries the arXiv API for papers in quantum computing / condensed matter
and serializes results to papers.json for the static frontend.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import datetime
import os
import sys

# ── Configuration ────────────────────────────────────────────────────────────

# arXiv categories to search
CATEGORIES = [
    "quant-ph",
    "cond-mat.mes-hall",
    "cond-mat.supr-con",
    "cond-mat.str-el",
]

# Keywords for title/abstract matching (at least one must appear)
KEYWORDS = [
    "quantum computing",
    "qubit",
    "quantum error correction",
    "topological qubit",
    "quantum gate",
    "quantum circuit",
    "quantum algorithm",
    "quantum entanglement",
    "decoherence",
    "quantum supremacy",
    "variational quantum",
    "quantum annealing",
    "quantum simulation",
    "quantum hardware",
    "superconducting qubit",
    "trapped ion",
    "spin qubit",
    "photonic qubit",
    "quantum advantage",
    "fault tolerant",
]

MAX_RESULTS = 100          # papers per query
OUTPUT_FILE = "papers.json"

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}


# ── Query Builder ─────────────────────────────────────────────────────────────

def build_query() -> str:
    """Construct a boolean arXiv search query."""
    cat_clause = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    kw_clause  = " OR ".join(f'ti:"{k}" OR abs:"{k}"' for k in KEYWORDS)
    return f"({cat_clause}) AND ({kw_clause})"


# ── arXiv Fetcher ─────────────────────────────────────────────────────────────

def fetch_arxiv(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """Fetch papers from arXiv and return a list of structured dicts."""
    params = urllib.parse.urlencode({
        "search_query": query,
        "start":        0,
        "max_results":  max_results,
        "sortBy":       "submittedDate",
        "sortOrder":    "descending",
    })
    url = f"{ARXIV_API}?{params}"
    print(f"[fetch] GET {url[:120]}…")

    with urllib.request.urlopen(url, timeout=30) as resp:
        xml_bytes = resp.read()

    root    = ET.fromstring(xml_bytes)
    entries = root.findall("atom:entry", NS)
    print(f"[fetch] Received {len(entries)} entries")

    papers = []
    for entry in entries:
        paper = parse_entry(entry)
        if paper:
            papers.append(paper)

    return papers


def parse_entry(entry: ET.Element) -> dict | None:
    """Extract metadata from a single <entry> element."""
    try:
        title    = (entry.findtext("atom:title",   "", NS) or "").strip().replace("\n", " ")
        abstract = (entry.findtext("atom:summary", "", NS) or "").strip().replace("\n", " ")
        pub_date = (entry.findtext("atom:published","", NS) or "")[:10]  # YYYY-MM-DD
        updated  = (entry.findtext("atom:updated",  "", NS) or "")[:10]

        # Authors
        authors = [
            a.findtext("atom:name", "", NS).strip()
            for a in entry.findall("atom:author", NS)
        ]

        # Links – prefer the abs page; derive PDF from it
        abs_url = pdf_url = ""
        for link in entry.findall("atom:link", NS):
            rel  = link.get("rel", "")
            href = link.get("href", "")
            typ  = link.get("type", "")
            if rel == "alternate":
                abs_url = href
            elif "pdf" in typ or "pdf" in href:
                pdf_url = href

        if not abs_url:
            return None

        if not pdf_url and abs_url:
            pdf_url = abs_url.replace("/abs/", "/pdf/") + ".pdf"

        # arXiv ID
        arxiv_id = abs_url.split("/abs/")[-1] if "/abs/" in abs_url else ""

        # Categories
        cats = [
            c.get("term", "")
            for c in entry.findall("atom:category", NS)
        ]

        return {
            "id":         arxiv_id,
            "title":      title,
            "authors":    authors,
            "abstract":   abstract,
            "date":       pub_date,
            "updated":    updated,
            "abs_url":    abs_url,
            "pdf_url":    pdf_url,
            "categories": cats,
        }
    except Exception as exc:
        print(f"[warn] Failed to parse entry: {exc}", file=sys.stderr)
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    query  = build_query()
    papers = fetch_arxiv(query)

    # Deduplicate by arXiv ID
    seen, unique = set(), []
    for p in papers:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "total":        len(unique),
        "papers":       unique,
    }

    out_path = os.path.join(os.path.dirname(__file__), OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[done] Wrote {len(unique)} papers → {out_path}")


if __name__ == "__main__":
    main()
