# Runbook — Backend répond HTTP 500

## Symptôme

L'endpoint `/chat` ou `/health` retourne HTTP 500. L'alerte `BackendHighErrorRate` ou `VectorStoreDown` se déclenche.

## Diagnostic

### 1. Vérifier les logs du backend
```bash
docker logs $(docker ps -qf name=backend) --tail 100
```
Chercher les lignes `"level":"ERROR"` pour identifier la cause.

### 2. Vérifier l'état de la base de données
```bash
docker ps | grep db
curl http://localhost:8000/health
```
Si `/health` retourne `{"db": "unreachable"}` → problème PostgreSQL.

### 3. Vérifier la mémoire disponible
```bash
free -h
docker stats --no-stream
```
Un OOM (Out Of Memory) sur le container backend tue le processus sans log explicite.

### 4. Vérifier l'espace disque
```bash
df -h
```
PostgreSQL échoue silencieusement si le disque est plein.

## Résolution

### Cas : PostgreSQL unreachable
```bash
docker compose restart db
# Attendre le healthcheck (30s), puis :
docker compose restart backend
```

### Cas : OOM backend
```bash
# Libérer de la mémoire en arrêtant les containers non essentiels
docker compose restart backend
```
Si récurrent → augmenter la flavor VM dans `infra/variables.tf`.

### Cas : Erreur applicative (bug)
```bash
# Rollback vers la version précédente
docker compose pull
BACKEND_IMAGE=ghcr.io/nyries/racine_ai_test_technique/backend:<sha-précédent> docker compose up -d backend
```

## Escalade

Si non résolu après 15 minutes → vérifier les GitHub Actions pour un déploiement récent qui aurait introduit une régression.

## Communication

**Pendant l'incident :**
- Si indisponibilité > 5 minutes : notifier les utilisateurs actifs — "Le service est momentanément indisponible. Nos équipes travaillent à la résolution."
- Mise à jour de statut toutes les 15 minutes.

**Après résolution :**
- Message de résolution : "Le service est rétabli. Cause : [résumé]. Mesures prises : [actions]."
- Post-mortem si l'incident a duré plus de 30 minutes ou si le SLO d'availability a été impacté.
