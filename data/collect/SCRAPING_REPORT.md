# Rapport de collecte des données

Domaine : Géopolitique du Moyen-Orient
Acteurs couverts : Israël, Arabie Saoudite, Iran, Turquie, Irak, Syrie, Égypte + puissances externes (USA, Chine, Russie, Inde, UE)

---

## Sources traitées

### ✓ arXiv
- **Statut** : Succès
- **Documents récoltés** : 55
- **Méthode** : API officielle Python (`arxiv` library)
- **Licence** : arXiv non-exclusive license
- **Remarques** :
  - Contenu académique, orienté sciences computationnelles appliquées aux conflits
  - Le champ `author` était absent des fichiers — corrigé dans le script
  - Erreur 429 (rate limit) si relancé trop tôt — attendre quelques heures entre deux runs
  - Run précédent avait obtenu 187 docs ; run actuel limité à 55 (résultats API variables)

---

### ✗ Middle East Institute (mei.edu)
- **Statut** : Échec
- **Documents récoltés** : 0
- **Raison** : Protection Cloudflare — le serveur renvoie un 403 Forbidden avant même de servir le HTML
- **Solution envisagée** : Nécessiterait Selenium ou Playwright (navigateur headless) — écarté car complexité disproportionnée

---

### ✗ Carnegie Endowment — Middle East Center (carnegieendowment.org)
- **Statut** : Échec
- **Documents récoltés** : 0
- **Raison** : Rendu JavaScript — le contenu (liste d'articles, pagination) est chargé dynamiquement. `requests` reçoit une page HTML vide. Le sitemap.xml ne contient pas les URLs d'articles.
- **Solution envisagée** : Même problème que MEI — navigateur headless requis

---

### ✓ RAND Corporation (rand.org)
- **Statut** : Succès
- **Documents récoltés** : 311
- **Méthode** : Scraping HTML statique, pagination via `?rows=24&start=N&content_type_ss=Commentary`
- **Licence** : © RAND Corporation (fair use — recherche non commerciale)

---

### ✓ Wilson Center (wilsoncenter.org)
- **Statut** : Succès
- **Documents récoltés** : 1 138
- **Méthode** : Découverte des URLs via sitemap.xml (63 pages), filtrage par mots-clés Moyen-Orient dans le slug, scraping HTML statique
- **Licence** : © Wilson Center (fair use — recherche non commerciale)
- **Remarques** :
  - Auteur extrait depuis `<div class="article-meta">` ou fallback "By ..." dans le corps
  - Certains articles anciens n'ont pas de `article-meta` → auteur `unknown`

---

### ✓ Brookings Institution (brookings.edu)
- **Statut** : Succès
- **Documents récoltés** : 5 009
- **Méthode** : Découverte des URLs via article-sitemap.xml (54 fichiers), filtrage par mots-clés Moyen-Orient dans le slug, scraping HTML statique
- **Licence** : © Brookings Institution (fair use — recherche non commerciale)
- **Remarques** :
  - Auteur extrait depuis le `<h5>` unique de la page
  - Date extraite depuis le `<div>` suivant le `<h5>`
  - Estimation initiale de ~7 758 URLs ; 5 009 articles retenus après filtrage (articles sans contenu `article-content` écartés)

---

### ✓ Wikipedia (en.wikipedia.org)
- **Statut** : Succès
- **Documents récoltés** : 1 339
- **Méthode** : API MediaWiki, découverte par 43 catégories Moyen-Orient, texte brut via `prop=extracts&explaintext=1`, retry automatique sur 429
- **Licence** : CC BY-SA 4.0
- **Remarques** :
  - Articles longs (moyenne ~30 KB), principale source de volume
  - Rate limit 429 fréquent — résolu avec retry + `Retry-After` header
  - L'API TextExtracts ne supporte pas le batch → 1 article par requête

---

## Bilan

| Source | Statut | Documents | Raison d'échec |
|--------|--------|-----------|----------------|
| arXiv | ✓ Succès | 55 | — |
| Middle East Institute | ✗ Échec | 0 | Cloudflare (403) |
| Carnegie Middle East | ✗ Échec | 0 | JavaScript rendering |
| RAND Corporation | ✓ Succès | 311 | — |
| Wilson Center | ✓ Succès | 1 138 | — |
| Brookings Institution | ✓ Succès | 5 009 | — |
| Wikipedia | ✓ Succès | 1 339 | — |
| **Total** | | **7 852** | |

**Volume texte brut : ~66.76 MB / ~16.7M tokens**
**Objectif CPT (50 MB) : ✓ ATTEINT**

---

## Exécution

### Lancement parallèle (recommandé)

Les 5 scrapers peuvent être lancés simultanément via `scrape_all.py`. Chaque scraper tourne dans un thread séparé et écrit ses logs dans `data/collect/<scraper>.log`.

```bash
make scrape
# ou directement :
python data/collect/scrape_all.py
```

Suivi en temps réel d'un scraper pendant l'exécution :
```bash
# Linux/Mac
tail -f data/collect/brookings_scraper.log
# Windows PowerShell
Get-Content data/collect/brookings_scraper.log -Wait
```

### Lancement séquentiel (debug)

```bash
make scrape-sequential
```

### Affichage

Chaque scraper dispose d'une barre de progression `tqdm` avec vitesse et ETA. En mode parallèle, les sorties sont redirigées vers les fichiers `.log` pour éviter l'interleaving.

---

## Leçons apprises

- Vérifier la présence de Cloudflare avant de coder un scraper (signe : 403 immédiat même avec headers navigateur)
- Vérifier si le contenu est dans le code source HTML avant de coder (clic droit → Afficher le code source)
- Les sites qui paginent avec `href=#` chargent leur contenu en JavaScript → non scrapable avec `requests`
- Le sitemap.xml est une alternative fiable à la pagination quand il est renseigné
- L'API MediaWiki TextExtracts ne supporte pas le batch malgré `exlimit=max` → toujours fetcher 1 article à la fois
- Respecter le header `Retry-After` sur les 429 Wikipedia plutôt que d'utiliser un délai fixe
