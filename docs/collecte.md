# Collecte et automatisation (Benjamin Chabani)

Partie data engineering du projet LDLC en Espagne : récupérer les données brutes et les
mettre à jour automatiquement chaque semaine.

| Fichier | Rôle |
|---|---|
| `src/collect/eurostat.py` | Eurostat (API JSON-stat) : ventes des magasins high-tech G474, population, prix à la consommation |
| `src/collect/osm_overpass.py` | OpenStreetMap (Overpass) : magasins de téléphonie, électronique, informatique par ville, population des communes |
| `src/collect/routes.py` | distances et temps de trajet depuis les hubs LDLC (OSRM, ou OpenRouteService si `ORS_API_KEY`) |
| `src/collect/prix.py` | prix des fiches produits (JSON-LD), historisés dans `data/raw/prix_scrapes.csv` |
| `src/common.py` | chemins, session HTTP, nouvelles tentatives |
| `src/pipeline.py` | enchaîne la collecte puis les étapes en aval quand elles existent |
| `.github/workflows/collecte.yml` | lance tout chaque lundi et à chaque modification du code, puis commite les données |
| `config/*.csv` | villes, hubs, modèles suivis, reconnaissance des enseignes |

Lancer en local :

```bash
pip install -r requirements.txt
python -m src.pipeline
```

À faire ensuite : compléter les URL PcComponentes et MediaMarkt dans `config/produits.csv`,
et scraper tout le catalogue téléphonie de LDLC pour le KPI 11.

## Bilan de la première collecte (12/11/2026)

| Source | Résultat |
|---|---|
| Eurostat | 412 observations (sts_trtu_a, demo_gind, prc_hicp_aind) |
| OpenStreetMap | 1 008 points de vente dans 10 villes, population des communes |
| OSRM | 20 trajets hub vers ville (après correction de `config/hubs.csv`) |
| Prix LDLC | 5 fiches scrapées automatiquement (JSON-LD) |

Incidents : le premier passage des distances a échoué (CSV mal formé), un passage OpenStreetMap a expiré.
La chaîne a gardé les données précédentes et l'a écrit dans `data/processed/journal_collecte.csv`.
