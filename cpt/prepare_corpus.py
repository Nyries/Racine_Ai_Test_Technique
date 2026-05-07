import argparse
import json
import random
from pathlib import Path

SEED = 42
TRAIN_RATIO = 0.9
CORPUS_DIR = Path(__file__).parent.parent / "data" / "clean"
OUT_DIR = Path(__file__).parent / "data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--push-to-hub",
        metavar="DATASET_ID",
        default=None,
        help="push splits to HuggingFace Datasets, e.g. 'your-username/racine-ai-middle-east'",
    )
    parser.add_argument("--private", action="store_true", help="make the HF dataset private")
    args = parser.parse_args()

    docs = []
    for i in range(4):
        p = CORPUS_DIR / f"corpus_{i:02d}.jsonl"
        with open(p, encoding="utf-8") as f:
            for line in f:
                docs.append(json.loads(line))
    print(f"Loaded {len(docs)} docs from {CORPUS_DIR}")

    random.seed(SEED)
    random.shuffle(docs)

    split = int(len(docs) * TRAIN_RATIO)
    train_docs = docs[:split]
    held_out_docs = docs[split:]

    OUT_DIR.mkdir(exist_ok=True)

    def write_split(docs: list, path: Path) -> tuple[int, int]:
        total_chars = 0
        with open(path, "w", encoding="utf-8") as f:
            for d in docs:
                text = d["title"] + "\n\n" + d["text"]
                total_chars += len(text)
                f.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
        return len(docs), total_chars

    train_n, train_chars = write_split(train_docs, OUT_DIR / "train.jsonl")
    held_n, held_chars = write_split(held_out_docs, OUT_DIR / "held_out.jsonl")

    total_chars = train_chars + held_chars
    est_tokens = total_chars / 4.998

    print(f"\nSplit (seed={SEED}, ratio={TRAIN_RATIO}):")
    print(f"  train    : {train_n:>5} docs  {train_chars/1e6:.2f} MB")
    print(f"  held-out : {held_n:>5} docs  {held_chars/1e6:.2f} MB")
    print(f"  total    : {train_n+held_n:>5} docs  {total_chars/1e6:.2f} MB  ~{est_tokens/1e6:.1f}M tokens")
    print(f"\nOutput: {OUT_DIR}")
    print("IMPORTANT: run this script ONCE before training. Never retokenize held-out.")

    if args.push_to_hub:
        from datasets import DatasetDict, load_dataset

        print(f"\nPushing to HuggingFace Datasets: {args.push_to_hub}")
        dataset = DatasetDict(
            {
                "train": load_dataset("json", data_files=str(OUT_DIR / "train.jsonl"), split="train"),
                "held_out": load_dataset("json", data_files=str(OUT_DIR / "held_out.jsonl"), split="train"),
            }
        )
        dataset.push_to_hub(args.push_to_hub, private=args.private)
        print(f"Dataset pushed: https://huggingface.co/datasets/{args.push_to_hub}")


if __name__ == "__main__":
    main()
