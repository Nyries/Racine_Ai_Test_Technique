"""
Data cleaning pipeline.

Reads  : data/raw/*.json
Writes : data/clean/corpus_{N:02d}.jsonl  (shards of SHARD_SIZE docs)
         data/clean/cleaning_stats.json   (step-by-step counts for the README)

Steps
-----
1. Load all JSON docs
2. Exact deduplication       — on the `id` field
3. Near-deduplication        — MinHash LSH, Jaccard >= 0.85, 5-gram word shingles
4. Quality filter            — length, language (English), alphanumeric ratio,
                               line-repetition ratio (proxy for low-quality /
                               boilerplate-heavy docs, analogous to perplexity filtering)
5. Boilerplate removal       — strip navigation / cookie / subscribe lines
6. PII removal               — replace emails and phone numbers
7. Post-clean length filter  — re-check length after text cleaning
8. Shard export              — JSONL shards
"""

import json
import re
from collections import Counter
from pathlib import Path

from datasketch import MinHash, MinHashLSH
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0  # make langdetect deterministic

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RAW_DIR = Path(__file__).parent.parent / "raw"
CLEAN_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
SHARD_SIZE = 2000

MINHASH_NUM_PERM = 128
MINHASH_THRESHOLD = 0.85
NGRAM_SIZE = 5  # word n-grams for shingling

MIN_TEXT_LENGTH = 300       # characters
MIN_ALPHA_RATIO = 0.60      # fraction of alpha + space characters
MAX_LINE_REPEAT_RATIO = 0.30  # max fraction of duplicate lines within one doc

# ---------------------------------------------------------------------------
# Boilerplate patterns (matched line by line, case-insensitive)
# ---------------------------------------------------------------------------
_BOILERPLATE_PATTERNS = [
    r"^skip to (main )?content",
    r"^subscribe (to|now)",
    r"^sign up for",
    r"^newsletter",
    r"^cookie(s)? (policy|notice|consent|settings)",
    r"^accept (all )?cookies",
    r"^privacy policy",
    r"^terms (of use|and conditions)",
    r"^all rights reserved",
    r"^copyright \d{4}",
    r"^\s*share (this|on|via)\b",
    r"^\s*follow us\b",
    r"^\s*(tweet|facebook|linkedin|instagram|youtube)\s*$",
    r"^loading\.\.\.",
    r"^please enable javascript",
    r"^\s*(menu|search|home|about|contact|donate)\s*$",
    r"^read more\b",
    r"^related articles?\b",
    r"^tags?\s*:",
    r"^print (this )?(article|page)",
]
BOILERPLATE_RE = re.compile("|".join(_BOILERPLATE_PATTERNS), re.IGNORECASE)

# ---------------------------------------------------------------------------
# PII patterns
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(
    r"(\+?1[\s.\-]?)?(\(?\d{3}\)?[\s.\-]?)?\d{3}[\s.\-]\d{4}"
)


# ---------------------------------------------------------------------------
# Step 1 — Load
# ---------------------------------------------------------------------------
def load_docs(raw_dir: Path) -> list[dict]:
    docs = []
    for path in sorted(raw_dir.glob("*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                docs.append(json.load(f))
        except Exception as e:
            print(f"  Warning: skipped {path.name}: {e}")
    return docs


# ---------------------------------------------------------------------------
# Step 2 — Exact deduplication
# ---------------------------------------------------------------------------
def exact_dedup(docs: list[dict]) -> tuple[list[dict], list[dict]]:
    seen: set[str] = set()
    kept, removed = [], []
    for doc in docs:
        if doc["id"] not in seen:
            seen.add(doc["id"])
            kept.append(doc)
        else:
            removed.append(doc)
    return kept, removed


# ---------------------------------------------------------------------------
# Step 3 — Near-deduplication (MinHash LSH)
# ---------------------------------------------------------------------------
def _shingles(text: str) -> set[str]:
    words = text.lower().split()
    if len(words) < NGRAM_SIZE:
        return {text.lower()[:50]}
    return {" ".join(words[i : i + NGRAM_SIZE]) for i in range(len(words) - NGRAM_SIZE + 1)}


def near_dedup(docs: list[dict]) -> tuple[list[dict], list[dict]]:
    lsh = MinHashLSH(threshold=MINHASH_THRESHOLD, num_perm=MINHASH_NUM_PERM)
    kept, removed = [], []

    for i, doc in enumerate(docs):
        mh = MinHash(num_perm=MINHASH_NUM_PERM)
        for s in _shingles(doc["text"]):
            mh.update(s.encode("utf-8"))

        if lsh.query(mh):
            removed.append(doc)
            continue

        lsh.insert(f"d{i}", mh)
        kept.append(doc)

    return kept, removed


# ---------------------------------------------------------------------------
# Step 4 — Quality filter
# ---------------------------------------------------------------------------
def _body(doc: dict) -> str:
    """Return the body text without the prepended title (title is also in doc['title'])."""
    title = doc.get("title", "")
    text = doc["text"]
    if title and text.startswith(title):
        return text[len(title):].lstrip()
    return text


def _alpha_ratio(text: str) -> float:
    if not text:
        return 0.0
    return sum(1 for c in text if c.isalpha() or c.isspace()) / len(text)


def _line_repeat_ratio(text: str) -> float:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return 1.0
    return 1.0 - len(set(lines)) / len(lines)


def _is_english(text: str) -> bool:
    try:
        return detect(text[:2000]) == "en"
    except Exception:
        return False


def quality_filter(docs: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    kept = []
    removed: dict[str, list[dict]] = {
        "too_short": [],
        "not_english": [],
        "low_alpha": [],
        "high_repetition": [],
    }

    for doc in docs:
        body = _body(doc)

        if len(body) < MIN_TEXT_LENGTH:
            removed["too_short"].append(doc)
            continue

        if _alpha_ratio(body) < MIN_ALPHA_RATIO:
            removed["low_alpha"].append(doc)
            continue

        if _line_repeat_ratio(body) > MAX_LINE_REPEAT_RATIO:
            removed["high_repetition"].append(doc)
            continue

        if not _is_english(body):
            removed["not_english"].append(doc)
            continue

        kept.append(doc)

    return kept, removed


# ---------------------------------------------------------------------------
# Steps 5 + 6 — Boilerplate removal + PII removal
# ---------------------------------------------------------------------------
def _remove_boilerplate(text: str) -> str:
    lines = text.splitlines()
    return "\n".join(l for l in lines if not BOILERPLATE_RE.match(l.strip()))


def _remove_pii(text: str) -> str:
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text


def clean_text(doc: dict) -> dict:
    text = _remove_boilerplate(doc["text"])
    text = _remove_pii(text)
    return {**doc, "text": text.strip()}


# ---------------------------------------------------------------------------
# Step 8 — Shard export
# ---------------------------------------------------------------------------
def save_shards(docs: list[dict], clean_dir: Path) -> list[Path]:
    clean_dir.mkdir(exist_ok=True)
    paths = []
    for i in range(0, len(docs), SHARD_SIZE):
        shard = docs[i : i + SHARD_SIZE]
        path = clean_dir / f"corpus_{i // SHARD_SIZE:02d}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for doc in shard:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        print(f"  corpus_{i // SHARD_SIZE:02d}.jsonl — {len(shard)} docs")
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _report(step: str, before: int, after: int) -> None:
    removed = before - after
    pct = removed / before * 100 if before else 0.0
    print(f"  {step:<40} {before:>6} → {after:<6}  (−{removed}, {pct:.1f}% removed)")


def _examples(docs: list[dict], n: int = 3) -> list[dict]:
    return [{"id": d["id"], "title": d.get("title", ""), "source": d["source"]} for d in docs[:n]]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 60)
    print("Data Cleaning")
    print("=" * 60)

    stats: dict = {}

    # 1. Load
    print("\nStep 1 — Loading docs from data/raw/ ...")
    docs = load_docs(RAW_DIR)
    stats["1_loaded"] = len(docs)
    print(f"  Loaded {len(docs)} docs")

    # 2. Exact dedup
    print("\nStep 2 — Exact deduplication (id field) ...")
    docs, exact_removed = exact_dedup(docs)
    stats["2_exact_dedup"] = {
        "kept": len(docs),
        "removed": len(exact_removed),
        "examples_removed": _examples(exact_removed),
    }
    _report("Exact dedup", stats["1_loaded"], len(docs))

    # 3. Near-dedup
    print("\nStep 3 — Near-deduplication (MinHash LSH, threshold=0.85) ...")
    n_before = len(docs)
    docs, near_removed = near_dedup(docs)
    stats["3_near_dedup"] = {
        "kept": len(docs),
        "removed": len(near_removed),
        "examples_removed": _examples(near_removed),
    }
    _report("Near-dedup", n_before, len(docs))

    # 4. Quality filter
    print("\nStep 4 — Quality filtering ...")
    n_before = len(docs)
    docs, quality_removed = quality_filter(docs)
    stats["4_quality_filter"] = {
        "kept": len(docs),
        "removed_by_reason": {k: len(v) for k, v in quality_removed.items()},
        "examples_removed": {k: _examples(v) for k, v in quality_removed.items()},
    }
    _report("Quality filter (total)", n_before, len(docs))
    for reason, removed_docs in quality_removed.items():
        print(f"    {reason:<35} −{len(removed_docs)}")

    # 5+6. Boilerplate + PII
    print("\nStep 5+6 — Boilerplate removal + PII removal ...")
    n_before = len(docs)
    docs = [clean_text(doc) for doc in docs]
    # Re-check length after cleaning
    docs = [d for d in docs if len(_body(d)) >= MIN_TEXT_LENGTH]
    stats["5_6_text_cleaning"] = {
        "kept": len(docs),
        "removed_post_clean": n_before - len(docs),
    }
    _report("Post-clean length filter", n_before, len(docs))

    # 7. Final stats
    total_chars = sum(len(d["text"]) for d in docs)
    by_source = dict(sorted(Counter(d["source"] for d in docs).items()))
    stats["7_final"] = {
        "total_docs": len(docs),
        "total_chars": total_chars,
        "total_mb": round(total_chars / 1e6, 2),
        "by_source": by_source,
    }

    print(f"\n{'=' * 60}")
    print(f"Final corpus: {len(docs)} docs / {total_chars / 1e6:.2f} MB")
    print("By source:")
    for src, count in by_source.items():
        print(f"  {src:<35} {count}")

    # 8. Shards
    print("\nStep 8 — Writing shards ...")
    save_shards(docs, CLEAN_DIR)

    # Save stats JSON
    stats_path = CLEAN_DIR / "cleaning_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"\nStats written to {stats_path.name}")
    print("Done.")


if __name__ == "__main__":
    main()
