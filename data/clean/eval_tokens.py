"""
Tokenizer evaluation — chars/token ratio.

Compares our domain corpus against a FineWeb-Edu sample using the Qwen3.5-0.8B
tokenizer. A lower ratio means more domain-specific terms are split into
sub-word fragments, which motivates vocabulary extension discussion.

Usage
-----
    python data/clean/eval_tokens.py

Outputs a summary table to stdout and writes token_eval.json.
"""

import json
import random
from pathlib import Path

from datasets import load_dataset
from transformers import AutoTokenizer

CLEAN_DIR = Path(__file__).parent
SHARD_PATH = CLEAN_DIR / "corpus_00.jsonl"
OUTPUT_PATH = CLEAN_DIR / "token_eval.json"

MODEL_ID = "Qwen/Qwen3.5-0.8B-Base"
SAMPLE_SIZE = 500
FINEWEB_DATASET = "HuggingFaceFW/fineweb-edu"
FINEWEB_SUBSET = "sample-10BT"

RANDOM_SEED = 42


def _body(doc: dict) -> str:
    """Body text without the prepended title."""
    title = doc.get("title", "")
    text = doc.get("text", "")
    if title and text.startswith(title):
        return text[len(title):].lstrip()
    return text


def load_our_corpus(path: Path, n: int) -> list[str]:
    docs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))
    random.seed(RANDOM_SEED)
    sample = random.sample(docs, min(n, len(docs)))
    return [_body(d) for d in sample]


def load_fineweb(n: int) -> list[str]:
    print(f"  Streaming {n} docs from {FINEWEB_DATASET} ({FINEWEB_SUBSET})...")
    ds = load_dataset(FINEWEB_DATASET, name=FINEWEB_SUBSET, split="train", streaming=True)
    texts = []
    for item in ds:
        text = item.get("text", "").strip()
        if text:
            texts.append(text)
        if len(texts) >= n:
            break
    return texts


def compute_ratio(tokenizer, texts: list[str]) -> dict:
    total_chars = 0
    total_tokens = 0
    ratios = []

    for text in texts:
        if not text:
            continue
        chars = len(text)
        tokens = len(tokenizer.encode(text, add_special_tokens=False))
        if tokens == 0:
            continue
        total_chars += chars
        total_tokens += tokens
        ratios.append(chars / tokens)

    return {
        "docs": len(ratios),
        "total_chars": total_chars,
        "total_tokens": total_tokens,
        "mean_ratio": round(total_chars / total_tokens, 4) if total_tokens else 0,
    }


def main() -> None:
    print(f"Loading tokenizer: {MODEL_ID}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    print(f"\nLoading our corpus sample ({SAMPLE_SIZE} docs) ...")
    our_texts = load_our_corpus(SHARD_PATH, SAMPLE_SIZE)
    print(f"  {len(our_texts)} docs loaded")

    print(f"\nLoading FineWeb-Edu sample ({SAMPLE_SIZE} docs) ...")
    fw_texts = load_fineweb(SAMPLE_SIZE)
    print(f"  {len(fw_texts)} docs loaded")

    print("\nTokenizing ...")
    our_stats = compute_ratio(tokenizer, our_texts)
    fw_stats = compute_ratio(tokenizer, fw_texts)

    delta = round(our_stats["mean_ratio"] - fw_stats["mean_ratio"], 4)

    print("\n" + "=" * 58)
    print(f"{'Corpus':<20} {'Docs':>6}  {'Chars/token':>12}  {'Total tokens':>13}")
    print("-" * 58)
    print(f"{'Our corpus':<20} {our_stats['docs']:>6}  {our_stats['mean_ratio']:>12.4f}  {our_stats['total_tokens']:>13,}")
    print(f"{'FineWeb-Edu':<20} {fw_stats['docs']:>6}  {fw_stats['mean_ratio']:>12.4f}  {fw_stats['total_tokens']:>13,}")
    print("-" * 58)
    print(f"{'Delta':<20} {'':>6}  {delta:>+12.4f}")
    print("=" * 58)

    if delta < -0.15:
        interpretation = (
            "Our ratio is notably lower than FineWeb-Edu. Domain-specific terms "
            "(Arabic/Persian/Turkish proper nouns, geopolitical terminology) are "
            "over-segmented by the base vocabulary. A vocabulary extension would "
            "reduce token count and improve training efficiency."
        )
    elif delta < 0:
        interpretation = (
            "Our ratio is slightly lower than FineWeb-Edu. Mild over-segmentation "
            "of domain terms. A vocabulary extension is possible but not critical "
            "given the small delta."
        )
    else:
        interpretation = (
            "Our ratio matches or exceeds FineWeb-Edu. The base Qwen vocabulary "
            "handles our domain terms efficiently. Vocabulary extension is not "
            "warranted."
        )

    print(f"\nInterpretation: {interpretation}\n")

    result = {
        "model": MODEL_ID,
        "sample_size": SAMPLE_SIZE,
        "our_corpus": our_stats,
        "fineweb_edu": fw_stats,
        "delta_chars_per_token": delta,
        "interpretation": interpretation,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Results written to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
