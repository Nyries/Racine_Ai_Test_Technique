# SLO — RAG Backend

## SLO 1 : Disponibilité (Availability)

**Définition** : 99% des requêtes `GET /health` retournent HTTP 200 sur une fenêtre glissante de 30 jours.

**Mesure** :
```promql
sum(rate(http_requests_total{job="rag-backend", handler="/health", status="200"}[30d]))
/
sum(rate(http_requests_total{job="rag-backend", handler="/health"}[30d]))
```

**Error budget mensuel** : 1% × 30 jours × 24h × 60min = **432 minutes** (~7h12) d'indisponibilité tolérée par mois.

---

## SLO 2 : Latence (Latency)

**Définition** : 95% des requêtes `POST /chat` ont une durée inférieure à 90 secondes sur une fenêtre glissante de 30 jours.

> 90s est justifié par le reranker BGE sur CPU (~20-30s) + LLM streaming (~10-30s). Sur GPU, ce seuil descend à ~10s.

**Mesure** :
```promql
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{job="rag-backend", handler="/chat"}[30d]))
  by (le)
) < 90
```

**Error budget mensuel** : 5% × 30 jours × 24h × 3600s = **129 600 secondes** de requêtes lentes tolérées par mois.

---

## Alertes associées

| Alerte | Seuil | Fichier |
|---|---|---|
| BackendHighErrorRate | taux erreur > 5% pendant 2min | `infra/alerts/error-rate.yaml` |
| BackendHighLatencyP95 | p95 > 90s pendant 5min | `infra/alerts/latency-p95.yaml` |
| VectorStoreDown | /health retourne 500 pendant 1min | `infra/alerts/vector-store-down.yaml` |
