.PHONY: install install-backend install-frontend \
        scrape clean-data \
        db-start ingest ingest-sample \
        test benchmark benchmark-full \
        dev-backend dev-frontend \
        setup \
        cpt-prepare cpt-train cpt-eval-perplexity cpt-eval-qa cpt-eval

# ── Dependencies ──────────────────────────────────────────────────────────────

install: install-backend install-frontend

install-backend:
	pip install -r backend/requirements.txt
	pip install -r data/requirements.txt

install-frontend:
	cd frontend && npm install

# ── Data pipeline (one-time) ──────────────────────────────────────────────────

scrape:
	cd data/collect && python scrape_all.py

scrape-sequential:
	cd data/collect && python rand_scraper.py
	cd data/collect && python arxiv_scraper.py
	cd data/collect && python wilson_scraper.py
	cd data/collect && python brookings_scraper.py
	cd data/collect && python wikipedia_scraper.py

clean-data:
	cd data/clean && python clean.py
	cd data/clean && python eval_tokens.py

# ── Database ──────────────────────────────────────────────────────────────────

db-start:
	docker run -d --name pgvector \
	  -e POSTGRES_USER=racine \
	  -e POSTGRES_PASSWORD=racine \
	  -e POSTGRES_DB=racine \
	  -p 5432:5432 \
	  pgvector/pgvector:pg16

# ── Ingestion ─────────────────────────────────────────────────────────────────

ingest:
	cd backend && python -m app.ingest

ingest-sample:
	cd backend && python -m app.ingest --limit 100

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	cd backend && pytest

# ── Benchmark ─────────────────────────────────────────────────────────────────

benchmark:
	cd backend && python -m benchmark.run_benchmark --no-llm

benchmark-full:
	cd backend && python -m benchmark.run_benchmark

# ── Dev servers ───────────────────────────────────────────────────────────────

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── CPT — Continuous Pre-Training ────────────────────────────────────────────

cpt-prepare:
	cd cpt && python prepare_corpus.py

cpt-train:
	cd cpt && python train.py --config config.yaml

cpt-eval-perplexity:
	cd cpt && python eval_perplexity.py --finetuned ./checkpoints/final

cpt-eval-qa:
	cd cpt && python eval_qa.py --finetuned ./checkpoints/final

cpt-eval: cpt-eval-perplexity cpt-eval-qa

# ── Full setup from scratch ───────────────────────────────────────────────────

setup: install db-start ingest-sample test
	@echo "Setup complete. Run 'make dev-backend' and 'make dev-frontend' in separate terminals."
