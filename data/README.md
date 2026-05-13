---
language:
  - en
license: cc-by-4.0
task_categories:
  - text-retrieval
  - question-answering
task_ids:
  - document-retrieval
tags:
  - geopolitics
  - middle-east
  - rag
  - retrieval-augmented-generation
  - think-tank
pretty_name: Middle East Geopolitics Corpus
size_categories:
  - 1K<n<10K
---

# Middle East Geopolitics Corpus

A cleaned and deduplicated corpus of ~7,800 documents specializing in Middle East geopolitics, designed to power a RAG (Retrieval-Augmented Generation) pipeline.

## Description

This dataset contains articles and reports from think tanks, academic institutions, and encyclopedias covering Middle East geopolitics: conflicts, diplomacy, regional actors (Israel, Iran, Saudi Arabia, Turkey, Palestine), and external powers (United States, Russia, China).

## Sources

| Source | Documents | Description |
|---|---|---|
| RAND Corporation | 311 | Foreign policy and security reports |
| Brookings Institution | 5,009 | Geopolitical analyses and policy papers |
| Wilson Center | 1,138 | Middle East research articles |
| arXiv | 55 | Academic papers |
| Wikipedia | 1,339 | Encyclopedia articles (43 geopolitical categories) |
| **Total** | **7,852** | **after cleaning: 7,796** |

## Data Cleaning Pipeline

Steps applied in order:

1. **Exact deduplication** — duplicate removal via SHA-256 hash
2. **Fuzzy deduplication** — MinHash LSH (Jaccard ≥ 0.85, 128 permutations)
3. **Language filtering** — English-only documents retained (langdetect)
4. **Repetition filtering** — documents with repetition ratio > 0.3 removed
5. **Boilerplate removal** — recurring headers, footers, and navigation menus stripped
6. **PII removal** — emails and phone numbers anonymized

**Result**: 7,796 documents / 65.21 MB (from 7,852 raw documents)

## Format

`.jsonl` files (JSON Lines), one document per line:

```json
{
  "title": "Iran's Regional Strategy",
  "content": "...",
  "url": "https://...",
  "source": "Brookings Institution",
  "date": "2023-04-15"
}
```

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("Nyries/middle-east-geopolitics-corpus")
```

For the full RAG pipeline, see the [GitHub repository](https://github.com/Nyries/Racine_Ai_Test_Technique).

## Chars/Tokens Ratio

| Metric | This corpus | FineWeb-Edu (reference) |
|---|---|---|
| Avg chars/token | ~4.1 | ~4.3 |
| Estimated tokens | ~15.9M | — |
| Avg document length | 8,370 chars | — |

The slightly lower ratio compared to FineWeb-Edu is explained by the prevalence of geopolitical proper nouns and acronyms (IRGC, GCC, P5+1) that tokenize into multiple subword units.

## Model Trained on This Corpus

[Nyries/qwen3-0.8b-middle-east-cpt](https://huggingface.co/Nyries/qwen3-0.8b-middle-east-cpt) — Continuous pre-training of Qwen3.5-0.8B-Base on this corpus.

## License

Original documents are subject to their respective source licenses. This compiled dataset is distributed under CC BY 4.0.
