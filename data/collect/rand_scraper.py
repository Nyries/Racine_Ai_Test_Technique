"""
Scraper RAND Corporation — commentaires sur le Moyen-Orient.
Pagination via ?rows=24&start=N&content_type_ss=Commentary
Produit des fichiers JSON dans data/raw/.
"""

import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

RAW_DIR = Path(__file__).parent.parent / "raw"
BASE_URL = "https://www.rand.org"
LISTING_URL = "https://www.rand.org/topics/middle-east.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

ROWS_PER_PAGE = 24
MAX_ARTICLES = 300
DELAY_SECONDS = 0.25


def get_article_urls() -> list[str]:
    """Récupère toutes les URLs d'articles en paginant via start=N."""
    urls = []
    start = 0

    while start < MAX_ARTICLES:
        params = {
            "rows": ROWS_PER_PAGE,
            "start": start,
            "content_type_ss": "Commentary",
        }
        response = requests.get(LISTING_URL, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        found = 0

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/pubs/commentary/" in href and href.endswith(".html"):
                full_url = BASE_URL + href if not href.startswith("http") else href
                if full_url not in urls:
                    urls.append(full_url)
                    found += 1

        print(f"  start={start} → {found} new articles (total: {len(urls)})")

        if found == 0:
            print("  No more results.")
            break

        start += ROWS_PER_PAGE
        time.sleep(DELAY_SECONDS)

    return urls


def scrape_article(url: str) -> dict | None:
    """Extrait le contenu d'un article RAND."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Titre
    title_tag = soup.find("h1")
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)

    # Auteur
    author = "unknown"
    authors_tag = soup.find("p", class_="authors")
    if authors_tag:
        author_link = authors_tag.find("a")
        if author_link:
            author = author_link.get_text(strip=True)

    # Date extraite depuis l'URL : /pubs/commentary/YYYY/MM/slug.html
    date = "unknown"
    parts = url.split("/")
    for i, part in enumerate(parts):
        if part.isdigit() and len(part) == 4:
            year = part
            month = parts[i + 1] if i + 1 < len(parts) and parts[i + 1].isdigit() else "01"
            date = f"{year}-{month.zfill(2)}-01"
            break

    # Corps : <div class="body-text"> avec <p> et <h2>
    body = soup.find("div", class_="body-text")
    if not body:
        return None

    parts_text = []
    for tag in body.find_all(["h2", "p"]):
        content = tag.get_text(strip=True)
        if content:
            parts_text.append(content)

    text = "\n\n".join(parts_text)

    if len(text) < 300:
        return None

    doc_id = "rand_" + url.rstrip("/").split("/")[-1].replace(".html", "")

    return {
        "id": doc_id,
        "title": title,
        "url": url,
        "source": "RAND Corporation",
        "author": author,
        "date": date,
        "license": "© RAND Corporation (fair use — non-commercial research)",
        "text": f"{title}\n\n{text}",
    }


def save_document(doc: dict) -> None:
    path = RAW_DIR / f"{doc['id']}.json"
    if path.exists():
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)


def main() -> None:
    RAW_DIR.mkdir(exist_ok=True)

    print("Fetching article URLs...")
    urls = get_article_urls()
    print(f"\n{len(urls)} articles found.\n")

    total = 0
    for url in urls:
        try:
            doc = scrape_article(url)
            if doc:
                save_document(doc)
                total += 1
                print(f"✓ {doc['title'][:70]}")
            time.sleep(DELAY_SECONDS)

        except requests.RequestException as e:
            print(f"✗ Error on {url}: {e}")
            time.sleep(DELAY_SECONDS)

    print(f"\nDone — {total} articles saved to {RAW_DIR}")


if __name__ == "__main__":
    main()
