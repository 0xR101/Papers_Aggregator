# Quantum Papers — arXiv Aggregator

An automated, serverless paper aggregator for quantum computing and condensed matter physics research.  
Papers are fetched from the [arXiv API](https://arxiv.org/help/api/) every morning and served as a static site via GitHub Pages.

---

## Repository structure

```
arxiv-aggregator/
├── fetch_papers.py              # arXiv data fetcher (pure stdlib Python)
├── papers.json                  # Generated dataset (auto-committed by CI)
├── index.html                   # Static frontend with KaTeX + live search
└── .github/
    └── workflows/
        └── fetch_papers.yml     # GitHub Actions: schedule + commit + push
```

---

## Quick start (local)

```bash
# 1. Clone and enter the repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# 2. Run the fetcher  (Python 3.9+ required, no dependencies)
python fetch_papers.py

# 3. Serve the frontend locally
python -m http.server 8080
# then open http://localhost:8080
```

---

## GitHub Pages deployment

1. Push this repository to GitHub.
2. Go to **Settings → Pages**.
3. Under **Source**, select **Deploy from a branch** → `main` / `(root)`.
4. Click **Save**.  
   GitHub Pages will now rebuild every time the Action pushes a new `papers.json`.

---

## GitHub Actions automation

The workflow in `.github/workflows/fetch_papers.yml` runs automatically every day at **08:00 UTC**.

**Required permission (already set in the workflow file):**

```yaml
permissions:
  contents: write
```

You can also trigger it manually from the **Actions** tab → **Fetch arXiv Papers** → **Run workflow**.

---

## Customisation

### Change the research field

Open `fetch_papers.py` and edit:

| Variable | Purpose |
|---|---|
| `CATEGORIES` | arXiv subject areas (e.g. `quant-ph`, `cs.LG`) |
| `KEYWORDS`   | Title / abstract keywords for Boolean filtering |
| `MAX_RESULTS`| Papers fetched per run (max 2000 per arXiv API) |

### Change the schedule

Edit the `cron` line in `.github/workflows/fetch_papers.yml`:

```yaml
- cron: "0 8 * * *"   # daily at 08:00 UTC
```

Use [crontab.guru](https://crontab.guru) to build a schedule.

### Add more category filter buttons

In `index.html`, duplicate the filter button pattern:

```html
<button class="filter-btn" data-cat="cs.LG">cs.LG</button>
```

The JavaScript checks whether any paper category *starts with* the `data-cat` value.

---

## Tech stack

| Layer | Technology |
|---|---|
| Data fetching | Python 3 stdlib (`urllib`, `xml.etree`) |
| Automation | GitHub Actions (cron + `contents: write`) |
| Frontend | Vanilla HTML / CSS / JS |
| Math rendering | [KaTeX](https://katex.org) auto-render |
| Hosting | GitHub Pages |

Zero external dependencies. Completely free.
