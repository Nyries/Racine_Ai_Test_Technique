"""
Evaluate base vs CPT model on the 50-question domain QA benchmark.

Method: for each question, score the log-probability of each answer choice
letter ("A", "B", "C", "D") as the next token after "Answer:".
The model picks the highest-scoring letter.

Usage (run from cpt/ directory):
    python eval_qa.py --finetuned ./checkpoints/final
    python eval_qa.py --base-only          # score base model only
"""

import argparse
import json

import torch
from tqdm import tqdm
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

from qa_questions import QUESTIONS


def get_choice_token_ids(tokenizer: AutoTokenizer) -> dict[str, int]:
    ids = {}
    for letter in ("A", "B", "C", "D"):
        for prefix in (" " + letter, letter):
            enc = tokenizer.encode(prefix, add_special_tokens=False)
            if len(enc) == 1:
                ids[letter] = enc[0]
                break
        if letter not in ids:
            raise ValueError(f"Cannot find single-token encoding for choice '{letter}'")
    return ids


def score_question(
    model: AutoModelForCausalLM,
    tokenizer: AutoTokenizer,
    question: dict,
    choice_token_ids: dict[str, int],
    device: str,
) -> str:
    choices_str = "\n".join(f"{k}. {v}" for k, v in question["choices"].items())
    prompt = f"Question: {question['question']}\n{choices_str}\nAnswer:"

    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = model(**inputs).logits[0, -1, :]

    scores = {letter: logits[tid].item() for letter, tid in choice_token_ids.items()}
    return max(scores, key=scores.__getitem__)


def evaluate(
    model_id: str,
    dtype: torch.dtype,
    device: str,
    tokenizer: AutoTokenizer | None = None,
    config=None,
) -> dict:
    print(f"\nLoading {model_id}")
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, config=config, dtype=dtype).to(device)
    model.eval()

    choice_token_ids = get_choice_token_ids(tokenizer)

    correct = 0
    errors = []
    for q in tqdm(QUESTIONS, desc=f"  {model_id.split('/')[-1][:20]}"):
        predicted = score_question(model, tokenizer, q, choice_token_ids, device)
        if predicted == q["answer"]:
            correct += 1
        else:
            errors.append({"id": q["id"], "predicted": predicted, "expected": q["answer"]})

    accuracy = correct / len(QUESTIONS)
    print(f"  Accuracy: {correct}/{len(QUESTIONS)} = {accuracy:.3f}")

    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {"accuracy": round(accuracy, 4), "correct": correct, "total": len(QUESTIONS), "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="Qwen/Qwen3.5-0.8B-Base")
    parser.add_argument("--finetuned", default=None, help="path to CPT model; omit for base-only")
    parser.add_argument("--base-only", action="store_true")
    parser.add_argument("--output", default="./qa_results.json")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    print(f"Device: {device}  |  dtype: {dtype}  |  questions: {len(QUESTIONS)}")

    base_tokenizer = AutoTokenizer.from_pretrained(args.base)
    base_config = AutoConfig.from_pretrained(args.base)

    results = {}
    results["base"] = evaluate(args.base, dtype, device, tokenizer=base_tokenizer)

    if not args.base_only and args.finetuned:
        results["ours"] = evaluate(
            args.finetuned, dtype, device, tokenizer=base_tokenizer, config=base_config
        )

        delta = results["ours"]["accuracy"] - results["base"]["accuracy"]
        print("\n" + "=" * 55)
        print(f"{'Metric':<35} {'Base':>8} {'Ours':>8} {'Delta':>8}")
        print("-" * 55)
        print(f"{'Domain QA accuracy (50 q)':<35} {results['base']['accuracy']:>8.3f} {results['ours']['accuracy']:>8.3f} {delta:>+8.3f}")
        print("=" * 55)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
