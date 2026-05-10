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

---

## Action si épuisement du budget d'erreur

### SLO 1 — Disponibilité épuisée (< 99%)

**Seuil d'alerte** : budget consommé à 50% → action préventive. Budget consommé à 100% → freeze des déploiements.

**Actions immédiates :**
1. Consulter le runbook [`runbook-500.md`](runbook-500.md) pour identifier la cause.
2. Freeze des déploiements non critiques jusqu'à reconstitution du budget.
3. Si indisponibilité > 1h consécutive : escalader, communiquer aux utilisateurs.

**Communication :**
- Message sur la page de statut : "Le service RAG rencontre des difficultés. Nos équipes travaillent à la résolution."
- Mise à jour toutes les 30 minutes jusqu'à résolution.

### SLO 2 — Latence épuisée (p95 > 90s)

**Seuil d'alerte** : budget consommé à 50% → investigation. Budget consommé à 100% → freeze des déploiements.

**Actions immédiates :**
1. Vérifier les métriques `rag_reranker_seconds` et `rag_llm_first_token_seconds` — identifier le goulot.
2. Si reranker : envisager de réduire le top-k (20 → 10) en configuration.
3. Si LLM : consulter [`runbook-rate-limit.md`](runbook-rate-limit.md).
4. Freeze des déploiements jusqu'à stabilisation.

**Communication :**
- Message aux utilisateurs : "Les réponses peuvent être plus lentes que d'habitude. Merci de votre patience."
