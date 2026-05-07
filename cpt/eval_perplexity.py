"""
Measure held-out perplexity for the base Qwen3.5-0.8B-Base model and our
CPT model, then print a comparison table.

Usage (run from cpt/ directory):
    python eval_perplexity.py --finetuned ./checkpoints/final
    python eval_perplexity.py --finetuned ./checkpoints/final --subset 500
"""

import argparse
import json
import math

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer


def compute_perplexity(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    texts: list[str],
    max_seq_length: int,
    device: str,
) -> float:
    model.eval()
    total_nll = 0.0
    total_tokens = 0

    for text in tqdm(texts, desc="  computing perplexity", leave=False):
        enc = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_seq_length,
        )
        input_ids = enc["input_ids"].to(device)
        n = input_ids.shape[-1] - 1
        if n <= 0:
            continue
        with torch.no_grad():
            loss = model(input_ids, labels=input_ids).loss
        total_nll += loss.item() * n
        total_tokens += n

    return math.exp(total_nll / total_tokens)


def load_texts(path: str, subset: int) -> list[str]:
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    if subset:
        lines = lines[:subset]
    return [json.loads(l)["text"] for l in lines]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="Qwen/Qwen3.5-0.8B-Base")
    parser.add_argument("--finetuned", required=True, help="path to CPT model directory")
    parser.add_argument("--held-out", default="./data/held_out.jsonl")
    parser.add_argument("--max-seq-length", type=int, default=1024)
    parser.add_argument(
        "--subset",
        type=int,
        default=200,
        help="number of held-out docs to evaluate (200 is fast, use 0 for all 780)",
    )
    parser.add_argument("--output", default="./perplexity_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    subset = args.subset or None

    print(f"Device : {device}  |  dtype : {dtype}")
    print(f"Held-out: {args.held_out}  |  subset: {subset or 'all'}")

    texts = load_texts(args.held_out, subset)
    print(f"Loaded {len(texts)} documents\n")

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    results = {}

    for label, model_id in [("base", args.base), ("ours", args.finetuned)]:
        print(f"[{label}] Loading {model_id}")
        model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=dtype).to(device)
        ppl = compute_perplexity(model, tokenizer, texts, args.max_seq_length, device)
        results[label] = round(ppl, 3)
        print(f"[{label}] Perplexity = {ppl:.3f}\n")
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    delta = results["base"] - results["ours"]
    delta_pct = delta / results["base"] * 100

    print("=" * 50)
    print(f"{'Metric':<30} {'Base':>8} {'Ours':>8} {'Delta':>8}")
    print("-" * 50)
    print(f"{'Perplexity held-out':<30} {results['base']:>8.3f} {results['ours']:>8.3f} {delta:>+8.3f}")
    print(f"{'Relative improvement':<30} {'':>8} {'':>8} {delta_pct:>+7.1f}%")
    print("=" * 50)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(
            {
                "base_perplexity": results["base"],
                "ours_perplexity": results["ours"],
                "delta": round(delta, 3),
                "delta_pct": round(delta_pct, 2),
                "subset": len(texts),
            },
            f,
            indent=2,
        )
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
