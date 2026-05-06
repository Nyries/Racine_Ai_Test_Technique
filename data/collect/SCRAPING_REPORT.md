# Rapport de collecte des données

Domaine : Géopolitique du Moyen-Orient
Acteurs couverts : Israël, Arabie Saoudite, Iran, Turquie, Irak, Syrie, Égypte + puissances externes (USA, Chine, Russie, Inde, UE)

---

## Sources traitées

### ⏳ arXiv
- **Statut** : Succès partiel — à compléter
- **Documents récoltés** : 55 (présents dans data/raw/, sur 187 initialement récupérés)
- **Méthode** : API officielle Python (`arxiv` library)
- **Licence** : arXiv non-exclusive license
- **Remarques** :
  - Contenu académique, orienté sciences computationnelles appliquées aux conflits
  - Le champ `author` était absent des fichiers — corrigé dans le script
  - Erreur 429 (rate limit) si relancé trop tôt — attendre quelques heures entre deux runs
  - Relancer le scraper pour atteindre les ~187 documents initiaux

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
- **Documents récoltés** : 26
- **Méthode** : Découverte des URLs via sitemap.xml (63 pages), filtrage par mots-clés Moyen-Orient dans le slug, scraping HTML statique
- **Licence** : © Wilson Center (fair use — recherche non commerciale)
- **Remarques** :
  - Auteur extrait depuis `<div class="article-meta">` ou fallback "By ..." dans le corps
  - Certains articles anciens n'ont pas de `article-meta` → auteur `unknown`

---

## Bilan

| Source | Statut | Documents | Raison d'échec |
|--------|--------|-----------|----------------|
| arXiv | ⏳ Partiel | 55 | Rate limit 429 — à compléter |
| Middle East Institute | ✗ Échec | 0 | Cloudflare (403) |
| Carnegie Middle East | ✗ Échec | 0 | JavaScript rendering |
| RAND Corporation | ✓ Succès | 311 | — |
| Wilson Center | ✓ Succès | 26 | — |
| **Total** | | **392** | |

**Volume texte brut actuel : ~2 MB / ~530K tokens**
**Objectif CPT : 50 MB / ~10-15M tokens → sources supplémentaires requises (Wikipedia)**

---

## Leçons apprises

- Vérifier la présence de Cloudflare avant de coder un scraper (signe : 403 immédiat même avec headers navigateur)
- Vérifier si le contenu est dans le code source HTML avant de coder (clic droit → Afficher le code source)
- Les sites qui paginent avec `href=#` chargent leur contenu en JavaScript → non scrapable avec `requests`
- Le sitemap.xml est une alternative fiable à la pagination quand il est renseigné
