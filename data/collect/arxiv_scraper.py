"""
Scraper arXiv — papiers académiques sur la géopolitique du Moyen-Orient.
Produit des fichiers JSON dans data/raw/.
"""

import arxiv
import json
import time
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "raw"

QUERIES = [
    "Middle East geopolitics Iran Saudi Arabia Israel",
    "Turkey foreign policy Middle East",
    "Iran nuclear program sanctions",
    "Israel Palestine conflict",
    "Syria conflict proxy war Russia",
    "Saudi Arabia Iran rivalry",
    "Arab Spring political instability",
    "US China Russia influence Middle East",
]

MAX_RESULTS_PER_QUERY = 30


def fetch_papers(query: str) -> list[dict]:
    client = arxiv.Client(page_size=MAX_RESULTS_PER_QUERY, delay_seconds=3)
    search = arxiv.Search(
        query=query,
        max_results=MAX_RESULTS_PER_QUERY,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    papers = []
    for result in client.results(search):
        text = f"{result.title}\n\n{result.summary}"
        papers.append({
            "id": f"arxiv_{result.entry_id.split('/')[-1]}",
            "title": result.title,
            "url": result.entry_id,
            "source": "arXiv",
            "date": result.published.strftime("%Y-%m-%d"),
            "license": "arXiv non-exclusive license",
            "text": text,
        })

    return papers


def save_paper(paper: dict) -> None:
    path = RAW_DIR / f"{paper['id']}.json"
    if path.exists():
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(paper, f, ensure_ascii=False, indent=2)


def main() -> None:
    RAW_DIR.mkdir(exist_ok=True)
    seen_ids = set()
    total = 0

    for query in QUERIES:
        print(f"\nRecherche : {query}")
        papers = fetch_papers(query)

        for paper in papers:
            if paper["id"] in seen_ids:
                continue
            seen_ids.add(paper["id"])
            save_paper(paper)
            total += 1
            print(f"  ✓ {paper['title'][:70]}")

        time.sleep(2)

    print(f"\nTerminé — {total} papiers sauvegardés dans {RAW_DIR}")


if __name__ == "__main__":
    main()
