"""
Lance tous les scrapers en parallèle.
Chaque scraper écrit ses logs dans data/collect/<name>.log.

Usage
-----
    python scrape_all.py
"""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

HERE = Path(__file__).parent

SCRAPERS = [
    ("RAND",          "rand_scraper.py"),
    ("arXiv",         "arxiv_scraper.py"),
    ("Wilson Center", "wilson_scraper.py"),
    ("Brookings",     "brookings_scraper.py"),
    ("Wikipedia",     "wikipedia_scraper.py"),
]


def run(name: str, script: str) -> tuple[str, int]:
    log_path = HERE / f"{script[:-3]}.log"
    with open(log_path, "w", encoding="utf-8") as log:
        proc = subprocess.run(
            [sys.executable, "-u", script],
            cwd=HERE,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    return name, proc.returncode


def main() -> None:
    print(f"Launching {len(SCRAPERS)} scrapers in parallel...")
    print("Progress logs: data/collect/<scraper>.log\n")

    with ThreadPoolExecutor(max_workers=len(SCRAPERS)) as pool:
        futures = {pool.submit(run, name, script): name for name, script in SCRAPERS}

        with tqdm(total=len(SCRAPERS), desc="Scrapers", unit="scraper") as pbar:
            for future in as_completed(futures):
                name, code = future.result()
                icon = "✓" if code == 0 else "✗"
                tqdm.write(f"  {icon} {name} finished (exit {code})")
                pbar.update(1)

    print("\nAll scrapers finished.")
    print("Check .log files for per-scraper details.")


if __name__ == "__main__":
    main()
