# Racine AI — Chatbot RAG Géopolitique du Moyen-Orient

Chatbot conversationnel basé sur un pipeline RAG (Retrieval-Augmented Generation) spécialisé en géopolitique du Moyen-Orient. Le système répond à des questions en s'appuyant sur un corpus de ~7 800 documents issus de RAND Corporation, Brookings Institution, Wilson Center, arXiv et Wikipedia, et cite ses sources.

---

## Architecture

```
┌─────────────────┐     SSE streaming      ┌──────────────────────────┐
│  React frontend │ ◄─────────────────────► │  FastAPI backend         │
│  (Vite :5173)   │     POST /chat          │  (:8000)                 │
└─────────────────┘                         └────────────┬─────────────┘
                                                         │
                              ┌──────────────────────────┼──────────────────┐
                              ▼                          ▼                  ▼
                     ┌────────────────┐      ┌─────────────────┐   ┌──────────────┐
                     │  PostgreSQL    │      │  BGE-M3         │   │  OpenRouter  │
                     │  + pgvector   │      │  embeddings     │   │  (LLM)       │
                     └────────────────┘      └─────────────────┘   └──────────────┘
```

**Pipeline de retrieval** : dense cosine (pgvector) + BM25 (tsvector PostgreSQL) → RRF fusion → BGE-reranker-v2-m3

---

## Lancer en local

### Prérequis

- Python 3.11+
- Node.js 18+
- Docker
- Git Bash ou WSL (pour `make` sur Windows)

### 1. Cloner et configurer

```bash
git clone <repo-url>
cd Racine_Ai_Test_Technique
cp backend/.env.example backend/.env
# Remplir OPENROUTER_API_KEY dans backend/.env
```

### 2. Installation complète en une commande

```bash
make setup
# Équivalent à : make install + make db-start + make ingest-sample + make test
```

### 3. Lancer l'application

Dans deux terminaux séparés :

```bash
# Terminal 1
make dev-backend   # FastAPI sur http://localhost:8000

# Terminal 2
make dev-frontend  # React sur http://localhost:5173
```

Ouvrir [http://localhost:5173](http://localhost:5173).

### Ingestion complète du corpus (optionnel)

`make ingest-sample` ingère 100 documents pour une démo rapide. Pour le corpus complet (~7 800 docs, ~3-6h sur CPU) :

```bash
make ingest
```

### Commandes disponibles

| Commande | Description |
|---|---|
| `make install` | Installe les dépendances Python + npm |
| `make db-start` | Lance PostgreSQL+pgvector via Docker |
| `make ingest` | Ingère tout le corpus |
| `make ingest-sample` | Ingère 100 docs (test rapide) |
| `make test` | Lance la suite de tests |
| `make benchmark` | Benchmark Recall + latence |
| `make dev-backend` | Serveur FastAPI en mode reload |
| `make dev-frontend` | Serveur Vite en mode HMR |

---

## Choix techniques

### Corpus — ~7 800 documents, 65 MB

Sources : RAND Corporation (311), Brookings Institution (5 009), Wilson Center (1 138), arXiv (55), Wikipedia (1 339 articles, 43 catégories géopolitiques).

Nettoyage : déduplication exacte + MinHash LSH (Jaccard ≥ 0.85), filtrage langue (langdetect), filtrage répétition, suppression boilerplate et PII. Résultat : 7 796 docs / 65.21 MB après nettoyage depuis 7 852 docs bruts.

### Vector store — pgvector

Choix de pgvector plutôt que Qdrant ou Chroma : PostgreSQL était déjà requis pour le déploiement cloud (OVH Managed PostgreSQL). Ajouter pgvector évite un service supplémentaire, simplifie l'infra, et le requêtage BM25 est natif via `tsvector`. Index IVFFlat (cosine) + GIN (full-text).

### Embeddings — BGE-M3

BGE-M3 (BAAI, 1024 dims) est un modèle unifié qui gère dense, sparse et ColBERT en un seul passage. Il est open source, multilingue, et les scores sur BEIR sont comparables aux meilleurs modèles propriétaires. `use_fp16=False` pour compatibilité CPU — à passer à `True` sur GPU.

### Retrieval hybride

Dense seul manque les requêtes à mots-clés exacts ; BM25 seul manque la sémantique. La fusion RRF (k=60) combine les deux listes sans nécessiter de calibration des poids. Le reranker BGE-reranker-v2-m3 (cross-encoder) affine le top-20 en top-5 — lent sur CPU (~24s p50), rapide sur GPU (~1-2s).

### LLM — OpenRouter `nvidia/nemotron-3-super-120b-a12b:free`

Modèle spécifié dans l'énoncé. Accès via OpenRouter free tier. Streaming SSE token par token, pas d'attente de réponse complète. Gestion des erreurs : 429 rate limit, timeout, LLM down.

### Frontend — React 19 + Vite

React (Next.js accepté par l'énoncé) avec Vite pour la rapidité de développement. CSS Modules pour le scoping des styles sans dépendance UI. SSE consommé via `fetch` + `ReadableStream` (EventSource ne supporte pas les requêtes POST). `flushSync` pour forcer le re-render token par token.

---

## Évaluation RAG

Benchmark sur 30 questions de géopolitique du Moyen-Orient avec mots-clés attendus dans les sources récupérées. Métriques maison (pas de dépendance RAGAS).

| Métrique | Valeur | Commande |
|---|---|---|
| Recall@5 | 0.533 | `make benchmark` |
| Recall@10 | 0.533 | `make benchmark` |
| Faithfulness (custom) | _TODO_ | `make benchmark-full` |
| Answer Relevancy (custom) | _TODO_ | `make benchmark-full` |
| Latence retrieval p50 | 264 ms | `make benchmark` |
| Latence retrieval p95 | 2 491 ms | `make benchmark` |
| Latence reranker p50 | 17 801 ms | `make benchmark` |
| Latence reranker p95 | 42 058 ms | `make benchmark` |

> **Note latence reranker** : mesuré sur CPU (BGE-reranker-v2-m3, cross-encoder sur 20 paires). Sur GPU (déploiement OVH), latence estimée ~1-2s p50.

> **Note Recall** : mesuré sur 1 000 docs ingérés (13% du corpus total). Recall@5 = Recall@10 indique que les documents manqués sont absents du top-10 — principalement dû à la couverture partielle du corpus. Sur corpus complet, Recall@10 attendu significativement supérieur.

**Faithfulness** : fraction de phrases de la réponse dont un quadrigramme apparaît textuellement dans les sources récupérées.  
**Answer Relevancy** : similarité cosinus (BGE-M3) entre l'embedding de la question et celui de la réponse.

---

## Évaluation CPT — Qwen3.5-0.8B-Base

Continuous pre-training sur le corpus nettoyé (65 MB). Split train/held-out effectué avant tout entraînement.

| Métrique | Base Qwen3.5-0.8B | Notre modèle | Delta |
|---|---|---|---|
| Perplexité held-out | _TODO_ | _TODO_ | _TODO_ |
| Domain QA accuracy (50 q) | _TODO_ | _TODO_ | _TODO_ |
| Hellaswag-200 accuracy | _TODO_ | _TODO_ | _TODO_ |

Modèle disponible sur HuggingFace : _TODO_

---

## Déploiement

Application déployée sur OVH (cloud souverain européen) : _TODO_

Infrastructure as Code : Terraform — `terraform apply` reconstruit l'environnement complet depuis zéro.

```bash
# Redéployer
cd infra
terraform init
terraform apply
```

---

## Limitations connues

- **Latence reranker sur CPU** : ~24s p50. Acceptable en production sur GPU, pas pour un usage local sans GPU dédié.
- **Corpus limité à 1 000 docs** pour les benchmarks (ingestion complète ~6h sur CPU). Les métriques seraient plus représentatives sur le corpus complet.
- **Streaming frontend** : le streaming token par token fonctionne en appel direct au backend. Un proxy intermédiaire (Nginx sans configuration SSE) peut buffériser la réponse.
- **LLM free tier** : `nvidia/nemotron-3-super-120b-a12b:free` est soumis aux limites de débit d'OpenRouter. En cas de surcharge, le chatbot renvoie un message d'erreur explicite.
- **Langue** : le corpus est majoritairement en anglais. Les questions en français peuvent produire des résultats de retrieval dégradés.

---

## Assistant IA utilisé

Ce projet a été développé avec **Claude Code** (Anthropic) comme assistant de développement. Claude Code a été utilisé pour la génération de code, le debugging, et les explications techniques. Chaque fichier a été relu, validé et modifié si nécessaire avant commit. Les choix d'architecture, les hyperparamètres et les décisions techniques restent sous la responsabilité de l'auteur.

---

## Coût estimé

| Service | Coût |
|---|---|
| OVH AI Training (CPT) | _TODO_ |
| OVH infrastructure (déploiement) | _TODO_ |
| OpenRouter (LLM free tier) | 0 € |
