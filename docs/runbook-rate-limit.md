# Runbook — LLM upstream en rate limit

## Symptôme

Les utilisateurs voient le message `"LLM rate limit reached — please retry in a moment"`. L'endpoint `/chat` retourne HTTP 200 avec un événement SSE `{"type": "error", "message": "LLM rate limit reached..."}`.

## Cause

OpenRouter free tier impose des limites de débit par clé API. Le modèle `nvidia/nemotron-3-super-120b-a12b:free` est soumis à ces limites.

## Diagnostic

### 1. Confirmer via les logs
```bash
docker logs $(docker ps -qf name=backend) --tail 50 | grep "rate limit"
```

### 2. Vérifier le compteur d'erreurs Prometheus
```promql
sum(increase(rag_errors_total{stage="llm"}[1h]))
```

### 3. Vérifier le statut OpenRouter
Consulter [status.openrouter.ai](https://status.openrouter.ai) pour un incident global.

## Résolution

### Immédiat : attendre
Le rate limit OpenRouter free tier se réinitialise automatiquement après quelques minutes. Aucune action requise.

### Si persistant : vérifier la clé API
```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```
Vérifier les champs `limit`, `usage`, `limit_remaining`.

### Si la clé est épuisée : rotation de clé
1. Créer une nouvelle clé sur [openrouter.ai/keys](https://openrouter.ai/keys)
2. Mettre à jour le secret dans `infra/terraform.tfvars`
3. Redémarrer le backend :
```bash
docker compose up -d backend
```

### Long terme : passer au tier payant
Ajouter des crédits OpenRouter pour lever les limites de débit.
