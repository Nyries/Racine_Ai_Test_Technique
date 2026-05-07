"""
Wikipedia scraper — Middle East geopolitics articles.
Discovers articles via MediaWiki category API, fetches full plain text.
Produces JSON files in data/raw/.
"""

import json
import time
from pathlib import Path

import requests
from tqdm import tqdm

RAW_DIR = Path(__file__).parent.parent / "raw"
API_URL = "https://en.wikipedia.org/w/api.php"
DELAY_SECONDS = 1.1  # Wikipedia asks for max 1 req/s

SEED_CATEGORIES = [
    # Core regional politics
    "Politics_of_the_Middle_East",
    "Gulf_Cooperation_Council",
    "Arab_League",
    "OPEC",

    # Conflicts & wars
    "Arab–Israeli_conflict",
    "History_of_the_Arab–Israeli_conflict",
    "Israeli–Palestinian_conflict",
    "Lebanon–Israel_conflict",
    "Syrian_civil_war",
    "Iraqi_Civil_War_(2014–2017)",
    "Yemeni_civil_war_(2014–present)",
    "Iran–Iraq_War",
    "Gulf_War",
    "Iraq_War",
    "2023_Israel–Hamas_war",

    # Armed groups
    "Islamic_State_of_Iraq_and_the_Levant",
    "Hezbollah",
    "Hamas",
    "Al-Qaeda",
    "Muslim_Brotherhood",

    # Iran
    "Foreign_relations_of_Iran",
    "Iran–United_States_relations",
    "Iran_nuclear_program",
    "Iranian_Revolution",
    "Iran–Saudi_Arabia_proxy_conflict",
    "Iran–Israel_relations",
    "Politics_of_Iran",

    # Israel & Palestine
    "Foreign_relations_of_Israel",
    "Gaza_Strip",
    "West_Bank",
    "Palestinian_Authority",
    "Abraham_Accords",

    # Saudi Arabia
    "Foreign_relations_of_Saudi_Arabia",
    "Saudi_Arabia–Iran_relations",

    # Turkey
    "Foreign_relations_of_Turkey",
    "Turkey–United_States_relations",
    "Kurdish–Turkish_conflict",
    "Turkish_involvement_in_the_Syrian_civil_war",

    # Other key actors
    "Foreign_relations_of_Egypt",
    "Foreign_relations_of_Iraq",
    "Arab_Spring",
]

HEADERS = {
    "User-Agent": "MiddleEastGeopoliticsResearch/1.0 (non-commercial academic use; contact: research@example.com)"
}


def api_get(params: dict, max_retries: int = 5) -> dict:
    """Wrapper around requests.get with automatic retry on 429."""
    for attempt in range(max_retries):
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", DELAY_SECONDS * (2 ** attempt)))
            print(f"  Rate limited (429) — waiting {wait}s before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("Max retries exceeded after repeated 429 errors")


def get_category_members(category: str) -> list[str]:
    """Returns all article titles in a Wikipedia category."""
    titles = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": f"Category:{category}",
        "cmtype": "page",
        "cmlimit": 500,
        "format": "json",
    }

    while True:
        data = api_get(params)
        members = data.get("query", {}).get("categorymembers", [])
        titles.extend(m["title"] for m in members)

        # Handle pagination via "continue"
        if "continue" in data:
            params["cmcontinue"] = data["continue"]["cmcontinue"]
            time.sleep(DELAY_SECONDS)
        else:
            break

    return titles


def fetch_article(title: str) -> dict | None:
    """Fetches plain text content of a single Wikipedia article."""
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts|info",
        "explaintext": 1,
        "inprop": "url",
        "format": "json",
    }

    data = api_get(params)
    pages = data.get("query", {}).get("pages", {})
    page = next(iter(pages.values()))

    if page.get("pageid", -1) == -1:
        return None

    text = page.get("extract", "").strip()
    if len(text) < 500:
        return None

    page_url = page.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")
    slug = title.replace(" ", "_").replace("/", "-")
    doc_id = f"wiki_{slug[:80]}"

    return {
        "id": doc_id,
        "title": title,
        "url": page_url,
        "source": "Wikipedia",
        "author": "Wikipedia contributors",
        "date": "unknown",
        "license": "CC BY-SA 4.0",
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

    # Collect all article titles from seed categories
    print("Fetching article titles from categories...")
    all_titles: set[str] = set()

    with tqdm(SEED_CATEGORIES, desc="Categories", unit="cat") as pbar:
        for category in pbar:
            members = get_category_members(category)
            new = [t for t in members if t not in all_titles]
            all_titles.update(members)
            pbar.set_postfix(total=len(all_titles), new=len(new))
            time.sleep(DELAY_SECONDS)

    title_list = sorted(all_titles)
    print(f"\n{len(title_list)} unique articles to fetch.\n")

    total = 0
    with tqdm(title_list, desc="Wikipedia", unit="doc") as pbar:
        for title in pbar:
            try:
                doc = fetch_article(title)
                if doc:
                    save_document(doc)
                    total += 1
                    pbar.set_postfix(saved=total)
                time.sleep(DELAY_SECONDS)

            except Exception as e:
                tqdm.write(f"✗ '{title}': {e}")
                time.sleep(DELAY_SECONDS)

    print(f"\nDone — {total} articles saved to {RAW_DIR}")


if __name__ == "__main__":
    main()
