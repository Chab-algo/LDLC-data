# LDLC en Espagne : Go ou No-Go ?

Projet de groupe Data Analytics, MSc Eugenia School.
Question posée par le Comex : **l'implantation de magasins LDLC en Espagne, sur la téléphonie, est-elle réalisable et rentable ?**

Équipe : **Georges Do Xuan, Thomas Lefevbre, Benjamin Chabani, Rubens Le Scao.**

> État au 12/11/2026 : la chaîne de collecte et la base en étoile tournent. Une partie des chiffres
> repose encore sur des hypothèses, toutes listées dans `config/hypotheses_pnl.csv` avec leur statut.

---

## 1. L'entreprise

Le Groupe LDLC (Lyon) vend du matériel informatique et high-tech, en ligne et en magasins.

| | |
|---|---|
| Magasins | 125, dont 102 sous enseigne LDLC (33 en propre, 54 en franchise, 15 LDLC APR) |
| Chiffre d'affaires 2025-2026 | 554,1 M€, marge brute 24,5 %, EBE 24,2 M€, résultat net 10,2 M€ |
| Situation financière | dette nette 42,2 M€, trésorerie 7,1 M€ |
| Tendance | CA du premier semestre 2026-2027 : 241,3 M€ (-9,6 %) |
| International | la France fait 88,3 % du CA. LDLC a ouvert des magasins en Espagne en 2018 et les a fermés en 2020 (environ 2 M€) |
| Logistique | Saint-Quentin-Fallavier (Isère) et Nantes, 46 000 m² |

Périmètre retenu : **la téléphonie (smartphones)**. Pays cible : **l'Espagne**.

## 2. Cadrage

### KPIs suivis

| # | KPI | Où il est calculé | Statut |
|---|---|---|---|
| 1 | Croissance du secteur | `fact_marche` (Eurostat `sts_trtu_a`, NACE G474) | collecté automatiquement |
| 2 | Part de marché de LDLC en France | fiche entreprise | estimé, tous biens techniques |
| 3 | Part de marché du leader espagnol | `config/marche.csv` (MediaMarkt 21,5 %) | sourcé |
| 4 | Indice de prix Espagne / France | vue `v_indice_prix` | voir `data/processed/indice_synthese.csv` |
| 5 | Marge brute post-taxe | `marge_si_alignement.csv` | simulé |
| 6 | Densité concurrentielle | vue `v_densite_concurrentielle` (OpenStreetMap) | collecté automatiquement |
| 7 | Coût au m² | `config/hypotheses_pnl.csv` | proxy (rue commerçante secondaire) |
| 8 | Distance aux hubs | `dim_zone` (OSRM ou OpenRouteService) | collecté automatiquement |
| 9 | Taxes locales | `dim_pays` (TVA, canon digital) | canon digital à vérifier |
| 10 | Pénétration de la téléphonie | `config/marche.csv` | sourcé |
| 11 | % du catalogue éligible | vue `v_eligibilite_catalogue` (`config/catalogue_ldlc.csv`) | 97,9 % (368 smartphones sur 376 déjà en ligne sur ldlc.com/es-es) |
| + | Rentabilité d'un magasin pilote | `pnl_pilote.csv` | CA au point mort simulé |

### Modèle en étoile (DuckDB, `data/ldlc_espagne.duckdb`)

```
                 dim_date            dim_pays
                     \                 /
   dim_produit --- fact_prix --- dim_enseigne
                                     |
   dim_hub --- dim_zone --- fact_point_de_vente / fact_concurrence_zone
                  |
             fact_magasin_sim        fact_marche --- dim_pays
```

### Dictionnaire de données

| Table | Grain | Colonnes clés |
|---|---|---|
| `dim_produit` | un modèle (marque, modèle, capacité, RAM) | `produit_id`, `famille` (Apple ou Android), `segment`, URL par enseigne |
| `dim_enseigne` | une enseigne | `enseigne_id`, `type` (spécialiste, généraliste, opérateur, marque), `pays_origine` |
| `dim_pays` | un pays | `taux_tva`, `canon_digital_mobile_eur` |
| `dim_zone` | une ville espagnole | `population` (OSM, d'après l'INE), `hub_le_plus_proche`, `distance_route_km`, `duree_route_h` |
| `dim_hub` | un entrepôt LDLC | coordonnées (centre de la commune) |
| `dim_date` | un jour de relevé | `exercice_ldlc` (avril à mars) |
| `fact_prix` | un prix, un jour, un modèle, une enseigne, un pays | `prix_ttc_eur`, `prix_ht_eur`, `source_type` (relevé manuel ou scraping) |
| `fact_marche` | un indicateur, un pays, une année | `valeur`, `unite`, `statut`, `source` |
| `fact_point_de_vente` | un magasin concurrent repéré dans OSM | `shop`, `nom`, `lat`, `lon` |
| `fact_concurrence_zone` | une ville x une enseigne x un type de commerce | `nb_points_de_vente` |
| `fact_magasin_sim` | un poste du compte de résultat simulé | `valeur`, `calcul` |

Définitions des termes métier :

| Terme | Définition |
|---|---|
| Chiffre d'affaires (CA) | ventes facturées, hors taxes |
| Marge brute | CA moins coût d'achat des produits vendus |
| Marge brute post-taxe | marge recalculée après TVA locale et canon digital, au prix du marché espagnol |
| Indice de prix relatif | moyenne de (prix HT Espagne / prix HT LDLC France) x 100 sur les modèles appariés |
| Point mort | CA à partir duquel la marge couvre les charges fixes (loyer, personnel) |
| Taux de contribution | marge brute moins charges variables, en % du CA |
| Densité concurrentielle | points de vente concurrents pour 100 000 habitants. Zone = la commune (zone de chalandise par temps de trajet : à faire) |
| Canon digital | redevance espagnole pour copie privée, incluse dans le prix des appareils numériques |
| ETP | équivalent temps plein |
| Exercice LDLC | d'avril à mars |

Règles de gestion :
- Les prix sont comparés **hors taxes** (TTC / (1 + TVA)) pour neutraliser l'écart de TVA (20 % contre 21 %).
- Deux prix sont appariés s'ils portent sur la même marque, le même modèle, la même capacité et la même RAM.
  Pas d'appariement par EAN : Apple utilise des références différentes selon le pays (MG6K4F/A en France, MG6M4QL/A en Espagne).
- Indice de prix = moyenne de (prix HT Espagne / prix HT LDLC France) x 100. En dessous de 100, l'Espagne est moins chère.
- Toute donnée qui n'est pas mesurée porte un statut : `donnée sourcée`, `proxy`, `calcul équipe` ou `hypothèse équipe`.

## 3. Architecture et sources

```
config/            villes, hubs, produits suivis, hypothèses du compte de résultat, données de marché sourcées
src/collect/       un script par source (écrit dans data/raw/)
src/transform/     build_star.py : construit la base en étoile et les vues KPI
src/analysis/      pnl_pilote.py : point mort d'un magasin pilote, marge si alignement des prix
src/ai/            synthese.py : synthèse Go/No-Go rédigée par l'API Claude
src/dashboard/     build_dashboard.py : injecte data/processed/ dans dashboard/template.html
dashboard/         index.html : le dashboard (ouvrable dans un navigateur)
src/pipeline.py    enchaîne tout
data/raw/          données brutes horodatées
data/processed/    tables prêtes pour le dashboard
.github/workflows/ collecte automatique chaque lundi
```

| Source | Accès | Ce qu'on en tire | Script |
|---|---|---|---|
| Eurostat `sts_trtu_a`, `demo_gind`, `prc_hicp_aind` | API JSON-stat, gratuite, sans clé | croissance du commerce high-tech, population, prix à la consommation | `eurostat.py` |
| OpenStreetMap (Overpass) | API gratuite, sans clé | magasins `mobile_phone`, `electronics`, `computer` par ville, population des communes | `osm_overpass.py` |
| OSRM ou OpenRouteService | gratuit (clé gratuite pour ORS) | distance et temps de trajet routier depuis les hubs | `routes.py` |
| Sites LDLC, PcComponentes, MediaMarkt | pages produits publiques | prix TTC par modèle | `prix.py` |
| Relevé manuel du 12/11/2026 | 22 prix sur 11 modèles | base de l'indice de prix | `data/raw/prix_releves_manuel.csv` |
| BOE (Real Decreto 126/2026, Orden PJC/297/2026) | public | SMI 2026, taux de cotisations patronales | `config/hypotheses_pnl.csv` |
| AECOC/GfK, StatCounter, Ceconomy, rapports LDLC | public | taille du marché, parts de marché, finances LDLC | `config/marche.csv` |

## 4. Organisation et roadmap

Répartition des rôles (proposée, à valider par l'équipe) :

| Membre | Rôle | Fichiers |
|---|---|---|
| Benjamin Chabani | data engineering : collecte, automatisation | `src/collect/`, `.github/workflows/` |
| Thomas Lefevbre | modélisation : base en étoile, dictionnaire | `src/transform/`, section 2 du README |
| Georges Do Xuan | analyse : KPIs, compte de résultat simulé | `src/analysis/`, `config/hypotheses_pnl.csv` |
| Rubens Le Scao | restitution : dashboard, synthèse IA, slides Comex | `src/ai/`, dashboard, slides |

Méthodologie de travail : une branche Git par membre, fusion dans `main` après relecture par un autre membre.
Chaque donnée entre par un script (`src/collect/`) ou par un fichier de `config/` avec sa source et son statut.
La collecte tourne seule chaque lundi (GitHub Actions) ; le dashboard est régénéré à chaque passage.

| Étape | Statut |
|---|---|
| Choix de l'entreprise, du pays, du périmètre | fait |
| Relevé de prix manuel (11 modèles) | fait |
| Scripts de collecte et automatisation hebdomadaire | fait, premier passage à vérifier |
| Base en étoile | fait |
| Compte de résultat simulé (point mort) | fait, hypothèses à affiner |
| URL produits PcComponentes et MediaMarkt dans `config/produits.csv` | à faire |
| KPI 11 : comparaison des catalogues LDLC France et Espagne | fait par marque, à automatiser par référence |
| Dashboard et synthèse IA | en cours |
| Slides Comex | à faire |

### Next steps (recommandations post-étude)

Recommandation provisoire : **pas de magasins en 2027**, renforcer la vente en ligne vers l'Espagne depuis les hubs français.
Conditions pour repasser en Go : prix Android à moins de 5 % des concurrents, marge post-taxe d'au moins 22 %,
loyer en centre commercial confirmé. Données à obtenir avant de revoir la décision en 2028 :
1. coûts d'achat réels de LDLC en téléphonie (donnée interne) ;
2. prix d'une deuxième enseigne espagnole (MediaMarkt) ;
3. disponibilité réelle en stock des références sur ldlc.com/es-es ;
4. loyers en centre commercial et en périphérie de Barcelone ;
5. effectif et CA moyen d'un magasin LDLC.

## 5. Stack technique

| Besoin | Outil | Pourquoi |
|---|---|---|
| Collecte | Python (`requests`, `beautifulsoup4`) | APIs publiques et pages produits |
| Transformation | `pandas` | nettoyage, appariement des prix |
| Base de données | DuckDB | modèle en étoile en SQL dans un seul fichier, sans serveur |
| Automatisation | GitHub Actions (cron hebdomadaire) | gratuit, relance la collecte et versionne les données |
| Synthèse IA | API Claude (Anthropic) | synthèse Go/No-Go à partir des KPIs, sans chiffre inventé |
| Restitution | dashboard interactif (artifact Claude) et slides | lecture par le Comex |

## 6. Lancer le projet

```bash
pip install -r requirements.txt
python -m src.pipeline            # collecte + base + compte de résultat + synthèse IA
python -m src.pipeline --offline  # reconstruit la base sans collecter
```

Secrets GitHub (Settings > Secrets and variables > Actions), tous deux facultatifs :
`ANTHROPIC_API_KEY` pour la synthèse IA, `ORS_API_KEY` pour OpenRouteService (sinon OSRM est utilisé).

## 7. Limites connues

- **Prix** : une seule enseigne espagnole pour l'instant (PcComponentes), 11 modèles, un seul jour de relevé.
- **KPI 11** : comparaison du nombre de smartphones par marque entre ldlc.com et ldlc.com/es-es (relevé manuel du 13/11/2026),
  pas encore référence par référence. Le site espagnol montre que LDLC peut vendre ces modèles en Espagne, pas qu'ils sont en stock
  ni qu'ils sont vendus par des enseignes espagnoles. À automatiser : scraper les deux listes et les apparier par référence.
- **Marge** : la marge téléphonie de LDLC n'est pas publiée. On utilise la marge brute du groupe (24,5 %), probablement trop haute.
- **Loyer** : proxy d'une rue commerçante secondaire (Bilbao). Aucun chiffre trouvé pour un centre commercial à Barcelone.
- **Concurrence** : OpenStreetMap est contributif. Un magasin absent d'OSM n'est pas compté.
- **Canon digital** : montant de 2017 (1,10 € par mobile), à vérifier dans le Real Decreto 209/2023.
- **Hubs** : coordonnées du centre de la commune, pas l'adresse exacte des entrepôts.
