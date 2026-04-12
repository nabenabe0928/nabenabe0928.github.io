"""Generate JSON-LD structured data in index.html from publications.json.

This exists because the homepage embeds schema.org `ScholarlyArticle` entries for Generative Engine Optimization (GEO),
and these must stay in sync with the publication data maintained in the `my-work-list` repo.

**Run after updating publications:**

```sh
python3 scripts/update_jsonld.py ../my-work-list/src/publications.json
```

The script:
- Reads `publications.json` and filters for Conference and Journal papers (excludes example entries, Japanese-only, notebooks, theses, talks, workshops, and preprints).
- Builds a JSON-LD `@graph` with static `WebSite` + `Person` entries and `ScholarlyArticle` entries for each publication.
- Replaces the `<!-- JSON-LD Structured Data -->` block in `index.html` in place.
- If the Person metadata (job title, employer, research interests, etc.) changes, update the `STATIC_ENTRIES` in the script.

This script reads publications.json from the my-work-list repo,
builds schema.org JSON-LD (WebSite + Person + ScholarlyArticle entries),
and patches the JSON-LD block in index.html in place.

Usage:
    python scripts/update_jsonld.py <path-to-publications.json>

Example:
    python scripts/update_jsonld.py ../my-work-list/src/publications.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = REPO_ROOT / "index.html"

SITE_URL = "https://nabenabe0928.github.io"

# Venue types to include as ScholarlyArticle entries.
INCLUDED_VENUE_TYPES = {"Conference", "Journal"}

# Static entries that are always present in the JSON-LD graph.
STATIC_ENTRIES = [
    {
        "@type": "WebSite",
        "name": "Shuhei Watanabe / Homepage",
        "url": f"{SITE_URL}/",
        "description": "Personal homepage of Shuhei Watanabe, Senior Research Scientist at SB Intuitions Corp.",
    },
    {
        "@type": "Person",
        "name": "Shuhei Watanabe",
        "alternateName": "\u6e21\u908a\u4fee\u5e73",
        "url": f"{SITE_URL}/",
        "image": f"{SITE_URL}/img/self.jpg",
        "jobTitle": "Senior Research Scientist",
        "worksFor": {
            "@type": "Organization",
            "name": "SB Intuitions Corp.",
            "url": "https://www.sbintuitions.co.jp/en/",
        },
        "knowsAbout": [
            "Bayesian Optimization",
            "Hyperparameter Optimization",
            "Multi-Objective Optimization",
            "Constraint Optimization",
            "Meta-Learning",
            "Tree-structured Parzen Estimator (TPE)",
            "Gaussian Processes",
            "Parallel Computing",
            "Machine Learning",
            "Deep Learning",
        ],
        "sameAs": [
            "https://github.com/nabenabe0928",
            "https://scholar.google.com/citations?hl=en&user=jqKQ2xoAAAAJ",
            "https://www.linkedin.com/in/shuhei-watanabe-4a3175194/",
        ],
    },
]


def _build_article_entry(pub: dict) -> dict:
    """Convert a single publication record to a ScholarlyArticle JSON-LD entry."""
    urls = pub.get("urls", {})
    venue = pub.get("venueName", "")
    abbrev = pub.get("venueNameAbbreviation", "")
    publisher_name = f"{venue} ({abbrev})" if abbrev else venue

    entry: dict = {
        "@type": "ScholarlyArticle",
        "name": pub["title"],
        "author": [{"@type": "Person", "name": name} for name in pub["authorNames"]],
    }

    # Use the venue paper URL first, then arXiv, then pdf.
    url = urls.get("paper") or urls.get("arxiv") or urls.get("pdf")
    if url:
        entry["url"] = url

    # If arXiv exists and is different from the primary URL, add as sameAs.
    arxiv = urls.get("arxiv")
    if arxiv and arxiv != entry.get("url"):
        entry["sameAs"] = arxiv

    entry["publisher"] = {"@type": "Organization", "name": publisher_name}
    entry["datePublished"] = f"{pub['publishedYear']}-{pub['publishedMonth']:02d}"

    return entry


def build_jsonld(publications: list[dict]) -> dict:
    """Build the full JSON-LD object from publications data."""
    articles = []
    for pub in publications:
        if pub.get("title") == "example":
            continue
        if pub.get("isJapaneseOnly"):
            continue
        if pub.get("venueType") not in INCLUDED_VENUE_TYPES:
            continue
        articles.append(_build_article_entry(pub))

    return {
        "@context": "https://schema.org",
        "@graph": STATIC_ENTRIES + articles,
    }


def patch_index_html(jsonld: dict) -> None:
    """Replace the JSON-LD script block in index.html."""
    html = INDEX_HTML.read_text(encoding="utf-8")

    jsonld_str = json.dumps(jsonld, indent=2, ensure_ascii=False)
    # Indent each line by 2 spaces to match the surrounding HTML.
    indented = "\n".join("  " + line if line else "" for line in jsonld_str.splitlines())

    pattern = re.compile(
        r"(  <!-- JSON-LD Structured Data -->\n)"
        r"  <script type=\"application/ld\+json\">\n"
        r".*?"
        r"  </script>",
        re.DOTALL,
    )

    replacement = (
        r"\g<1>"
        "  <script type=\"application/ld+json\">\n"
        f"{indented}\n"
        "  </script>"
    )

    new_html, count = pattern.subn(replacement, html)
    if count == 0:
        print("ERROR: Could not find JSON-LD block in index.html.", file=sys.stderr)
        print("Make sure index.html contains a '<!-- JSON-LD Structured Data -->' comment", file=sys.stderr)
        print("followed by a <script type=\"application/ld+json\"> block.", file=sys.stderr)
        sys.exit(1)

    INDEX_HTML.write_text(new_html, encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <path-to-publications.json>", file=sys.stderr)
        sys.exit(1)

    pub_path = Path(sys.argv[1])
    if not pub_path.exists():
        print(f"ERROR: {pub_path} not found.", file=sys.stderr)
        sys.exit(1)

    with pub_path.open(encoding="utf-8") as f:
        publications = json.load(f)

    jsonld = build_jsonld(publications)
    patch_index_html(jsonld)

    article_count = sum(1 for e in jsonld["@graph"] if e["@type"] == "ScholarlyArticle")
    print(f"Updated index.html with {article_count} ScholarlyArticle entries.")


if __name__ == "__main__":
    main()
