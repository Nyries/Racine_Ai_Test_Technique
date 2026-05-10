---
language:
- en
license: apache-2.0
base_model: Qwen/Qwen3.5-0.8B-Base
tags:
- continuous-pre-training
- geopolitics
- middle-east
- causal-lm
datasets:
- Nyries/racine-ai-middle-east
model-index:
- name: qwen3-0.8b-middle-east-cpt
  results:
  - task:
      type: text-generation
    metrics:
    - type: perplexity
      name: Perplexity (held-out domain corpus)
      value: 14.115
---

# qwen3-0.8b-middle-east-cpt

Continuous pre-training of [Qwen/Qwen3.5-0.8B-Base](https://huggingface.co/Qwen/Qwen3.5-0.8B-Base) on a Middle East geopolitics corpus (~65 MB, ~13M tokens).

## Intended Use

Domain-adapted base language model for Middle East geopolitics. Intended for researchers and developers building RAG pipelines, domain-specific text generation, or further fine-tuning on this domain.

**Not intended for**: direct user-facing applications without additional instruction fine-tuning, high-stakes decision making, or tasks requiring up-to-date information (training data collected up to early 2025).

## Training Data

Corpus: [Nyries/racine-ai-middle-east](https://huggingface.co/datasets/Nyries/racine-ai-middle-east)

- **7 016 training documents** / 780 held-out (split seed=42, no overlap verified)
- **Sources**: RAND Corporation (311), Brookings Institution (5 009), Wilson Center (1 138), arXiv (55), Wikipedia thematic (1 339 articles, 43 geopolitical categories)
- **Size**: ~58 MB train / ~6.5 MB held-out — ~11.7M tokens total
- **Language**: English (99%+)
- **License**: all sources scraped under permissive or fair-use terms (RAND, Brookings, Wilson Center publish open-access policy reports; arXiv CC-BY; Wikipedia CC-BY-SA)

**Cleaning pipeline**: exact deduplication → MinHash LSH (Jaccard ≥ 0.85, removed 20 docs) → language filter (removed 29 non-English) → repetition filter (removed 7) → boilerplate removal → basic PII suppression (email, phone regex).

## Training Configuration

| Parameter | Value |
|-----------|-------|
| Framework | transformers 4.51+ + accelerate |
| Base model | Qwen/Qwen3.5-0.8B-Base |
| Precision | bf16 |
| Epochs | 1 |
| Effective batch size | 32 sequences (per_device=2 × grad_accum=16) |
| Max sequence length | 1 024 tokens |
| Learning rate | 1e-4 (cosine scheduler) |
| Warmup steps | 30 |
| Weight decay | 0.01 |
| Gradient checkpointing | yes |
| Tokens seen | ~7.2M (7 016 docs × ~1 024 tokens) |
| Compute | OVH AI Training — A100 32 GB |
| Training time | ~2h30 (220 optimizer steps) |
| Seed | 42 |

## Evaluation

Comparison against base `Qwen/Qwen3.5-0.8B-Base` on held-out sets:

| Metric | Base Qwen3.5-0.8B | This model | Delta |
|--------|------------------|------------|-------|
| Perplexity held-out (200 docs) | 16.083 | **14.115** | -1.97 (-12.2%) |
| Domain QA accuracy (50 q, MMLU-style) | 64.0% | 60.0% | -4.0% |
| Hellaswag-200 accuracy | 44.5% | 42.0% | -2.5% |

**Reproduce**:
```bash
git clone https://github.com/Nyries/racine-ai-middle-east-cpt
cd cpt
python eval_perplexity.py --finetuned ./checkpoints/checkpoint-220
python eval_qa.py --finetuned ./checkpoints/checkpoint-220
python eval_hellaswag.py --finetuned ./checkpoints/checkpoint-220
```

## Limitations

- **1 epoch only**: the model has seen each training token once. Additional epochs or a larger corpus would likely yield stronger domain adaptation.
- **Catastrophic forgetting**: minor regressions on Domain QA (-4%) and Hellaswag (-2.5%) are consistent with CPT without generalist replay. The model is not instruction-tuned — use a chat/instruct variant for conversational tasks.
- **Sequence length**: documents are truncated at 1 024 tokens. Long policy reports lose their tail content.
- **No instruction tuning**: this is a base model. It will not follow instructions or answer questions in a structured way without further SFT.
- **Knowledge cutoff**: corpus collected up to early 2025. Events after that date are not represented.

## Identified Biases

- **Source bias**: corpus skews toward Western think tanks (Brookings, RAND, Wilson Center). Perspectives from regional actors (Arab governments, Iranian sources, Turkish media) are underrepresented.
- **English-only**: despite the multilingual nature of the region, the corpus is almost exclusively in English, which may bias the model toward Western framings of regional events.
- **Topic imbalance**: Brookings contributes 64% of documents, which may overweight US foreign policy analysis relative to regional dynamics.

## Citation

```bibtex
@misc{nyries2025qwen3middleeast,
  title={Qwen3.5-0.8B continuous pre-training on Middle East geopolitics},
  author={Nyries},
  year={2025},
  url={https://huggingface.co/Nyries/qwen3-0.8b-middle-east-cpt}
}
```
