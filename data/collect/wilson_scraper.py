"""
Scraper Wilson Center — articles sur le Moyen-Orient.
Découverte des URLs via sitemap.xml?page=N (63 pages).
Filtre par mots-clés dans le slug pour ne garder que le Moyen-Orient.
Produit des fichiers JSON dans data/raw/.
"""

import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

RAW_DIR = Path(__file__).parent.parent / "raw"
BASE_URL = "https://www.wilsoncenter.org"
SITEMAP_URL = "https://www.wilsoncenter.org/sitemap.xml?page={page}"
SITEMAP_PAGES = 63
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
    """Parcourt les 63 pages du sitemap et filtre les URLs Moyen-Orient."""
    urls = []

    for page in range(1, SITEMAP_PAGES + 1):
        sitemap_url = SITEMAP_URL.format(page=page)
        try:
            response = requests.get(sitemap_url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "xml")
            page_urls = [loc.get_text(strip=True) for loc in soup.find_all("loc")]

            filtered = [
                u for u in page_urls
                if "/article/" in u and is_middle_east_url(u)
            ]
            urls.extend(filtered)

            print(f"  Page {page:02d}/{SITEMAP_PAGES} → {len(page_urls)} URLs, {len(filtered)} Middle East (total: {len(urls)})")
            time.sleep(DELAY_SECONDS)

        except requests.RequestException as e:
            print(f"  ✗ Error on page {page}: {e}")
            time.sleep(DELAY_SECONDS)

    return urls


def scrape_article(url: str) -> dict | None:
    """Extrait le contenu d'un article Wilson Center."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Titre : <h1 class="h2"> (l'autre <h1> est invisible)
    title_tag = soup.find("h1", class_="h2")
    if not title_tag:
        return None
    title = title_tag.get_text(strip=True)

    # Auteur et date dans <div class="article-meta">
    author = "unknown"
    date = "unknown"
    meta = soup.find("div", class_="article-meta")
    if meta:
        # Date : <time datetime="YYYY-MM-DDT...">
        time_tag = meta.find("time", class_="post-time")
        if time_tag and time_tag.get("datetime"):
            date = time_tag["datetime"][:10]  # "YYYY-MM-DD"

        # Auteur : <ul class="authors"> → <li><a>Nom</a></li>
        authors_ul = meta.find("ul", class_="authors")
        if authors_ul:
            author_links = [a.get_text(strip=True) for a in authors_ul.find_all("a")]
            if author_links:
                author = ", ".join(author_links)

    # Corps : <article class="text-block ..."><div class="inner">
    body = soup.find("article", class_=re.compile(r"text-block"))
    if body:
        inner = body.find("div", class_="inner") or body
    else:
        return None

    all_paragraphs = [tag.get_text(strip=True) for tag in inner.find_all(["h2", "h3", "p", "blockquote"])]

    parts_text = [p for p in all_paragraphs if len(p) > 40]
    text = "\n\n".join(parts_text)

    if len(text) < 300:
        return None

    # Fallback auteur : passe séparée sans filtre de longueur
    if author == "unknown":
        for fragment in reversed(all_paragraphs):
            match = re.match(r"^By\s+(.+)$", fragment, re.IGNORECASE)
            if match and len(match.group(1)) < 100:
                author = match.group(1).strip()
                break

    slug = url.rstrip("/").split("/")[-1]
    doc_id = f"wilson_{slug}"

    return {
        "id": doc_id,
        "title": title,
        "url": url,
        "source": "Wilson Center",
        "author": author,
        "date": date,
        "license": "© Wilson Center (fair use — non-commercial research)",
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

    print("Fetching article URLs via sitemap...")
    urls = get_article_urls()
    print(f"\n{len(urls)} Middle East articles found.\n")

    total = 0
    with tqdm(urls, desc="Wilson Center", unit="doc") as pbar:
        for url in pbar:
            try:
                doc = scrape_article(url)
                if doc:
                    save_document(doc)
                    total += 1
                    pbar.set_postfix(saved=total)
                time.sleep(DELAY_SECONDS)

            except requests.RequestException as e:
                tqdm.write(f"✗ {url}: {e}")
                time.sleep(DELAY_SECONDS)

    print(f"\nDone — {total} articles saved to {RAW_DIR}")


if __name__ == "__main__":
    main()
