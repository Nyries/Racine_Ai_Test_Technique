"""
Sanity check: evaluate base vs CPT model on Hellaswag-200.
Detects catastrophic forgetting of general language capabilities.

Scoring: for each example, compute mean log-probability of each ending
given the context; pick the highest-scoring ending.

Usage (run from cpt/ directory):
    python eval_hellaswag.py --finetuned ./checkpoints/checkpoint-220
    python eval_hellaswag.py --base-only
"""

import argparse
import json

import torch
import torch.nn.functional as F
from datasets import load_dataset
from tqdm import tqdm
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


def score_example(model, tokenizer, example, device):
    ctx = example["ctx"]
    endings = example["endings"]
    label = int(example["label"])

    scores = []
    for ending in endings:
        full_ids = tokenizer.encode(ctx + ending, add_special_tokens=True, return_tensors="pt").to(device)
        ending_len = len(tokenizer.encode(ending, add_special_tokens=False))
        if ending_len == 0:
            scores.append(float("-inf"))
            continue

        with torch.no_grad():
            logits = model(full_ids).logits[0]  # [seq_len, vocab]

        start = full_ids.shape[1] - ending_len
        log_probs = F.log_softmax(logits[start - 1 : -1], dim=-1)
        token_log_probs = log_probs[range(ending_len), full_ids[0, start:].tolist()]
        scores.append(token_log_probs.mean().item())

    return scores.index(max(scores)) == label


def evaluate(model_id, dtype, device, tokenizer=None, config=None, n=200):
    print(f"\nLoading {model_id}")
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, config=config, dtype=dtype).to(device)
    model.eval()

    dataset = load_dataset("Rowan/hellaswag", split=f"validation[:{n}]")

    correct = sum(
        score_example(model, tokenizer, ex, device)
        for ex in tqdm(dataset, desc=f"  {model_id.split('/')[-1][:20]}")
    )
    accuracy = correct / n
    print(f"  Hellaswag-{n}: {correct}/{n} = {accuracy:.3f}")

    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {"accuracy": round(accuracy, 4), "correct": correct, "total": n}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="Qwen/Qwen3.5-0.8B-Base")
    parser.add_argument("--finetuned", default=None)
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--output", default="./hellaswag_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    print(f"Device: {device}  |  dtype: {dtype}  |  examples: {args.n}")

    base_tokenizer = AutoTokenizer.from_pretrained(args.base)
    base_config = AutoConfig.from_pretrained(args.base)

    results = {}
    results["base"] = evaluate(args.base, dtype, device, tokenizer=base_tokenizer, n=args.n)

    if not args.base_only and args.finetuned:
        results["ours"] = evaluate(
            args.finetuned, dtype, device,
            tokenizer=base_tokenizer, config=base_config, n=args.n,
        )

        delta = results["ours"]["accuracy"] - results["base"]["accuracy"]
        print("\n" + "=" * 55)
        print(f"{'Metric':<35} {'Base':>8} {'Ours':>8} {'Delta':>8}")
        print("-" * 55)
        print(f"{'Hellaswag-200 accuracy':<35} {results['base']['accuracy']:>8.3f} {results['ours']['accuracy']:>8.3f} {delta:>+8.3f}")
        print("=" * 55)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
