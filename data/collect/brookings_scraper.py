"""
Scraper Brookings Institution — articles sur le Moyen-Orient.
Découverte des URLs via article-sitemap.xml (54 fichiers).
Filtre par mots-clés dans le slug pour ne garder que le Moyen-Orient.
Produit des fichiers JSON dans data/raw/.
"""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

RAW_DIR = Path(__file__).parent.parent / "raw"
BASE_URL = "https://www.brookings.edu"
SITEMAP_URLS = (
    ["https://www.brookings.edu/article-sitemap.xml"]
    + [f"https://www.brookings.edu/article-sitemap{i}.xml" for i in range(2, 55)]
)
DELAY_SECONDS = 0.5

MIDDLE_EAST_KEYWORDS = [
    "iran", "israel", "saudi", "arab", "syria", "syrian", "iraq", "iraqi",
    "turkey", "turkish", "egypt", "egyptian", "middle-east", "gulf",
    "persian", "hezbollah", "hamas", "palestine", "palestinian", "jordan",
    "lebanon", "lebanese", "yemen", "yemeni", "oman", "bahrain", "qatar",
    "kuwait", "maghreb", "mosul", "fallujah", "baghdad", "tehran", "riyadh",
    "islamic-state", "isis", "isil", "jihadist", "sunni", "shia",
    "nuclear-deal", "sanctions-iran", "arab-spring",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def is_middle_east_url(url: str) -> bool:
    slug = url.rstrip("/").split("/")[-1].lower()
    return any(kw in slug for kw in MIDDLE_EAST_KEYWORDS)


def get_article_urls() -> list[str]:
    """Parcourt les 54 sitemaps d'articles et filtre les URLs Moyen-Orient."""
    urls = []
    total_sitemaps = len(SITEMAP_URLS)

    for i, sitemap_url in enumerate(SITEMAP_URLS, start=1):
        try:
            response = requests.get(sitemap_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "xml")
            page_urls = [loc.get_text(strip=True) for loc in soup.find_all("loc")]

            filtered = [u for u in page_urls if is_middle_east_url(u)]
            urls.extend(filtered)

            print(f"  Sitemap {i:02d}/{total_sitemaps} → {len(page_urls)} URLs, {len(filtered)} Middle East (total: {len(urls)})")
            time.sleep(DELAY_SECONDS)

        except requests.RequestException as e:
            print(f"  ✗ Error on sitemap {i}: {e}")
            time.sleep(DELAY_SECONDS)

    return urls


def scrape_article(url: str) -> dict | None:
    """Extrait le contenu d'un article Brookings."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Titre
    title_tag = soup.find("h1")
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)

    # Auteur : <a> dans le <div> à l'intérieur du seul <h5>
    author = "unknown"
    h5 = soup.find("h5")
    if h5:
        author_links = [a.get_text(strip=True) for a in h5.find_all("a")]
        if author_links:
            author = ", ".join(author_links)

    # Date : <p> dans le <div> suivant le <h5>
    date = "unknown"
    if h5:
        next_div = h5.find_next_sibling("div")
        if next_div:
            date_p = next_div.find("p")
            if date_p:
                date_text = date_p.get_text(strip=True)
                # Normaliser "May 6, 2026" → "2026-05-06"
                try:
                    from datetime import datetime
                    date = datetime.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")
                except ValueError:
                    date = date_text

    # Corps : <div class="article-content"> → <div class="byo-block"> → <p>
    body = soup.find("div", class_="article-content")
    if not body:
        return None

    parts_text = []
    for block in body.find_all("div", class_="byo-block"):
        for tag in block.find_all(["h2", "h3", "p"]):
            content = tag.get_text(strip=True)
            if content and len(content) > 40:
                parts_text.append(content)

    text = "\n\n".join(parts_text)

    if len(text) < 300:
        return None

    slug = url.rstrip("/").split("/")[-1]
    doc_id = f"brookings_{slug}"

    return {
        "id": doc_id,
        "title": title,
        "url": url,
        "source": "Brookings Institution",
        "author": author,
        "date": date,
        "license": "© Brookings Institution (fair use — non-commercial research)",
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

    print("Fetching article URLs via sitemaps...")
    urls = get_article_urls()
    print(f"\n{len(urls)} Middle East articles found.\n")

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
