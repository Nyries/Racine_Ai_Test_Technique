# Rapport de collecte des données

Domaine : Géopolitique du Moyen-Orient
Acteurs couverts : Israël, Arabie Saoudite, Iran, Turquie, Irak, Syrie, Égypte + puissances externes (USA, Chine, Russie, Inde, UE)

---

## Sources traitées

### ⏳ arXiv
- **Statut** : À rescraper
- **Documents récoltés** : 0 (187 précédemment récoltés puis supprimés)
- **Méthode** : API officielle Python (`arxiv` library)
- **Licence** : arXiv non-exclusive license
- **Remarques** :
  - Contenu académique, orienté sciences computationnelles appliquées aux conflits
  - Le champ `author` était absent des fichiers — corrigé dans le script
  - Erreur 429 (rate limit) si relancé trop tôt — attendre quelques heures entre deux runs

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

## Bilan

| Source | Statut | Documents | Raison d'échec |
|--------|--------|-----------|----------------|
| arXiv | ⏳ À rescraper | 0 | Documents supprimés, rate limit 429 |
| Middle East Institute | ✗ Échec | 0 | Cloudflare (403) |
| Carnegie Middle East | ✗ Échec | 0 | JavaScript rendering |
| RAND Corporation | ✓ Succès | 311 | — |

---

## Leçons apprises

- Vérifier la présence de Cloudflare avant de coder un scraper (signe : 403 immédiat même avec headers navigateur)
- Vérifier si le contenu est dans le code source HTML avant de coder (clic droit → Afficher le code source)
- Les sites qui paginent avec `href=#` chargent leur contenu en JavaScript → non scrapable avec `requests`
- Le sitemap.xml est une alternative fiable à la pagination quand il est renseigné
