"""Construit la base en étoile DuckDB à partir des fichiers bruts.

Entrées : data/raw/*.csv et config/*.csv
Sortie  : data/ldlc_espagne.duckdb (tables dim_* et fact_*, vues v_*)
          data/processed/*.csv (une copie lisible de chaque vue d'analyse)

Le script tolère l'absence d'un fichier brut (par exemple si une API n'a pas répondu) :
la table correspondante est créée vide et un avertissement est écrit dans le log.
"""
from __future__ import annotations

import re

import duckdb
import pandas as pd

from src.common import CONFIG, DB_PATH, PROCESSED, RAW, get_logger

log = get_logger("build_star")

ENSEIGNES = pd.read_csv(CONFIG / "enseignes_regex.csv")


def read(path, **kw) -> pd.DataFrame:
    if not path.exists():
        log.warning("Fichier absent : %s (table vide)", path.relative_to(path.parents[2]))
        return pd.DataFrame()
    return pd.read_csv(path, **kw)


def classify(nom: str, marque: str, operateur: str) -> tuple[str, str]:
    txt = " ".join(str(x) for x in (marque, nom, operateur) if isinstance(x, str)).lower()
    for e in ENSEIGNES.itertuples():
        if re.search(e.regex, txt):
            return e.enseigne, e.type
    return "Indépendant ou non identifié", "independant"


def build() -> duckdb.DuckDBPyConnection:
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))

    # ---------- Prix : relevé manuel + scraping automatique ----------
    manuel = read(RAW / "prix_releves_manuel.csv")
    scrap = read(RAW / "prix_scrapes.csv")
    if not scrap.empty:
        scrap = scrap[scrap.statut == "ok"]
    prix = pd.concat([manuel, scrap], ignore_index=True)
    prix = prix[prix.prix_ttc_eur.notna()].copy()
    prix["source_type"] = prix.methode.fillna("").map(lambda m: "scraping" if "automatique" in m else "relevé manuel")

    produits = pd.read_csv(CONFIG / "produits.csv", dtype=str).fillna("")
    produits.insert(0, "produit_id", range(1, len(produits) + 1))
    produits["famille"] = produits.marque.map(lambda m: "Apple" if m == "Apple" else "Android")

    # ---------- Dimensions ----------
    con.register("produits_df", produits)
    con.execute("""
        CREATE TABLE dim_produit AS
        SELECT produit_id, modele, marque, famille, segment,
               TRY_CAST(NULLIF(capacite_go,'') AS INTEGER) AS capacite_go,
               TRY_CAST(NULLIF(ram_go,'') AS INTEGER) AS ram_go,
               url_ldlc_fr, url_pccomponentes_es, url_mediamarkt_es
        FROM produits_df
    """)

    ens = ENSEIGNES[["enseigne", "type"]].copy()
    for extra in (("LDLC", "specialiste"), ("Indépendant ou non identifié", "independant")):
        if extra[0] not in set(ens.enseigne):
            ens.loc[len(ens)] = extra
    ens.insert(0, "enseigne_id", range(1, len(ens) + 1))
    ens["pays_origine"] = ens.enseigne.map({"LDLC": "FR", "Fnac": "FR", "Carrefour": "FR", "Orange": "FR",
                                            "MediaMarkt": "DE", "PcComponentes": "ES", "El Corte Inglés": "ES",
                                            "Phone House": "ES", "Movistar": "ES", "Worten": "PT"}).fillna("")
    con.register("ens_df", ens)
    con.execute("CREATE TABLE dim_enseigne AS SELECT * FROM ens_df")

    hyp = pd.read_csv(CONFIG / "hypotheses_pnl.csv").set_index("parametre").valeur
    con.execute(f"""
        CREATE TABLE dim_pays AS
        SELECT * FROM (VALUES
          ('FR','France',0.20,NULL,'EUR'),
          ('ES','Espagne',0.21,{float(hyp['canon_digital_eur_par_mobile'])},'EUR')
        ) t(pays, nom, taux_tva, canon_digital_mobile_eur, devise)
    """)

    hubs = pd.read_csv(CONFIG / "hubs.csv")
    con.register("hubs_df", hubs)
    con.execute("CREATE TABLE dim_hub AS SELECT hub, ville, pays, lat, lon, note FROM hubs_df")

    villes = pd.read_csv(CONFIG / "villes_es.csv")
    osm_v = read(RAW / "osm_villes.csv")
    if not osm_v.empty:
        villes = villes.merge(osm_v[["ville", "code_ine", "population", "population_date"]], on="ville", how="left")
    else:
        villes[["code_ine", "population", "population_date"]] = None
    dist = read(RAW / "distances_routieres.csv")
    if not dist.empty:
        best = dist.sort_values("distance_km").groupby("ville").first().reset_index()
        villes = villes.merge(best[["ville", "hub", "distance_km", "duree_h", "moteur"]]
                              .rename(columns={"hub": "hub_le_plus_proche", "distance_km": "distance_route_km",
                                               "duree_h": "duree_route_h", "moteur": "moteur_routage"}),
                              on="ville", how="left")
    else:
        villes[["hub_le_plus_proche", "distance_route_km", "duree_route_h", "moteur_routage"]] = None
    villes.insert(0, "zone_id", range(1, len(villes) + 1))
    con.register("villes_df", villes)
    con.execute("CREATE TABLE dim_zone AS SELECT * FROM villes_df")

    dates = sorted(set(prix.date_releve.astype(str)))
    con.register("dates_df", pd.DataFrame({"d": pd.to_datetime(dates)}))
    con.execute("""
        CREATE TABLE dim_date AS
        SELECT CAST(strftime(d, '%Y%m%d') AS INTEGER) AS date_id, CAST(d AS DATE) AS jour,
               month(d) AS mois, quarter(d) AS trimestre, year(d) AS annee,
               CASE WHEN month(d) >= 4 THEN year(d) || '-' || (year(d)+1) ELSE (year(d)-1) || '-' || year(d) END
                 AS exercice_ldlc
        FROM dates_df
    """)

    # ---------- Faits ----------
    con.register("prix_df", prix)
    con.execute("""
        CREATE TABLE fact_prix AS
        SELECT CAST(strftime(CAST(p.date_releve AS DATE), '%Y%m%d') AS INTEGER) AS date_id,
               d.produit_id, e.enseigne_id, p.pays,
               p.prix_ttc_eur, round(p.prix_ttc_eur / (1 + c.taux_tva), 2) AS prix_ht_eur,
               TRY_CAST(p.prix_barre_ou_pvpr_eur AS DOUBLE) AS prix_barre_ou_pvpr_eur,
               p.variante_relevee, p.url_source, p.source_type
        FROM prix_df p
        JOIN dim_produit d USING (modele)
        JOIN dim_enseigne e USING (enseigne)
        JOIN dim_pays c USING (pays)
    """)

    marche = pd.read_csv(CONFIG / "marche.csv")
    eu = read(RAW / "eurostat_sts_trtu_a.csv")
    rows = [marche.assign(dataset="config/marche.csv")]
    if not eu.empty:
        eu2 = eu.rename(columns={"geo": "pays", "time": "annee", "value": "valeur"})
        eu2["indicateur"] = ("eurostat_" + eu2.indic_bt.astype(str) + "_" + eu2.nace_r2.astype(str) + "_"
                             + eu2.unit.astype(str) + "_" + eu2.s_adj.astype(str))
        eu2["unite"] = eu2.unit
        eu2["statut"] = "donnée sourcée"
        eu2["source"] = "Eurostat sts_trtu_a"
        rows.append(eu2[["pays", "annee", "indicateur", "valeur", "unite", "statut", "source", "dataset"]])
    pop = read(RAW / "eurostat_demo_gind.csv")
    if not pop.empty:
        p2 = pop.rename(columns={"geo": "pays", "time": "annee", "value": "valeur"})
        p2 = p2.assign(indicateur="population_1er_janvier", unite="habitants", statut="donnée sourcée",
                       source="Eurostat demo_gind", dataset="demo_gind")
        rows.append(p2[["pays", "annee", "indicateur", "valeur", "unite", "statut", "source", "dataset"]])
    hicp = read(RAW / "eurostat_prc_hicp_aind.csv")
    if not hicp.empty:
        h2 = hicp.rename(columns={"geo": "pays", "time": "annee", "value": "valeur"})
        h2 = h2.assign(indicateur="ipch_" + h2.coicop.astype(str), unite="indice", statut="donnée sourcée",
                       source="Eurostat prc_hicp_aind", dataset="prc_hicp_aind")
        rows.append(h2[["pays", "annee", "indicateur", "valeur", "unite", "statut", "source", "dataset"]])
    fm = pd.concat(rows, ignore_index=True)
    fm["annee"] = fm.annee.astype(str).str[:4].astype(int)
    con.register("fm_df", fm)
    con.execute("CREATE TABLE fact_marche AS SELECT pays, annee, indicateur, valeur, unite, statut, source FROM fm_df")

    mag = read(RAW / "osm_magasins.csv")
    if not mag.empty:
        cls = mag.apply(lambda r: classify(r.get("nom"), r.get("marque"), r.get("operateur")), axis=1)
        mag["enseigne"] = [c[0] for c in cls]
        con.register("mag_df", mag)
        con.execute("""
            CREATE TABLE fact_point_de_vente AS
            SELECT z.zone_id, e.enseigne_id, m.shop, m.nom, m.lat, m.lon, m.osm_type, m.osm_id, m.date_collecte
            FROM mag_df m JOIN dim_zone z USING (ville) JOIN dim_enseigne e USING (enseigne)
        """)
    else:
        con.execute("""CREATE TABLE fact_point_de_vente (zone_id INT, enseigne_id INT, shop VARCHAR, nom VARCHAR,
                       lat DOUBLE, lon DOUBLE, osm_type VARCHAR, osm_id BIGINT, date_collecte VARCHAR)""")
    con.execute("""
        CREATE TABLE fact_concurrence_zone AS
        SELECT zone_id, enseigne_id, shop, count(*) AS nb_points_de_vente
        FROM fact_point_de_vente GROUP BY ALL
    """)

    # ---------- Vues d'analyse (KPIs) ----------
    con.execute("""
        CREATE VIEW v_indice_prix AS
        WITH last AS (
          SELECT f.*, row_number() OVER (PARTITION BY produit_id, enseigne_id, pays
                                        ORDER BY date_id DESC, (source_type = 'scraping') DESC) rn
          FROM fact_prix f
        ), fr AS (SELECT produit_id, prix_ht_eur ht_fr, prix_ttc_eur ttc_fr FROM last
                  JOIN dim_enseigne USING (enseigne_id) WHERE rn=1 AND enseigne='LDLC' AND pays='FR'),
        es AS (SELECT produit_id, enseigne AS concurrent_es, prix_ht_eur ht_es, prix_ttc_eur ttc_es,
                      prix_barre_ou_pvpr_eur pvpr_es FROM last JOIN dim_enseigne USING (enseigne_id)
               WHERE rn=1 AND pays='ES' AND enseigne <> 'LDLC')
        SELECT p.modele, p.marque, p.famille, p.segment, es.concurrent_es,
               fr.ttc_fr AS prix_ttc_ldlc_fr, es.ttc_es AS prix_ttc_es, fr.ht_fr AS prix_ht_ldlc_fr,
               es.ht_es AS prix_ht_es, es.pvpr_es,
               round(100 * es.ht_es / fr.ht_fr, 1) AS indice_es_vs_fr
        FROM fr JOIN es USING (produit_id) JOIN dim_produit p USING (produit_id)
    """)
    con.execute("""
        CREATE VIEW v_indice_synthese AS
        SELECT 'Tous modèles' AS perimetre, count(*) AS nb_modeles, round(avg(indice_es_vs_fr),1) AS indice
        FROM v_indice_prix
        UNION ALL
        SELECT famille, count(*), round(avg(indice_es_vs_fr),1) FROM v_indice_prix GROUP BY famille
    """)
    con.execute("""
        CREATE VIEW v_densite_concurrentielle AS
        SELECT z.ville, z.region, z.population, z.hub_le_plus_proche, z.distance_route_km, z.duree_route_h,
               coalesce(sum(c.nb_points_de_vente),0) AS nb_points_de_vente,
               coalesce(sum(c.nb_points_de_vente) FILTER (WHERE e.type IN ('specialiste','generaliste')),0)
                 AS nb_grandes_enseignes,
               round(1e5 * coalesce(sum(c.nb_points_de_vente),0) / nullif(z.population,0), 1)
                 AS points_de_vente_pour_100k_hab
        FROM dim_zone z
        LEFT JOIN fact_concurrence_zone c USING (zone_id)
        LEFT JOIN dim_enseigne e USING (enseigne_id)
        GROUP BY z.ville, z.region, z.population, z.hub_le_plus_proche, z.distance_route_km, z.duree_route_h
        ORDER BY points_de_vente_pour_100k_hab DESC NULLS LAST
    """)
    con.execute("""
        CREATE VIEW v_concurrents_par_enseigne AS
        SELECT z.ville, e.enseigne, e.type, sum(c.nb_points_de_vente) AS nb
        FROM fact_concurrence_zone c JOIN dim_zone z USING (zone_id) JOIN dim_enseigne e USING (enseigne_id)
        GROUP BY ALL ORDER BY z.ville, nb DESC
    """)
    con.execute("""
        CREATE VIEW v_eligibilite_catalogue AS
        SELECT count(*) AS nb_modeles_ldlc_suivis,
               count(*) FILTER (WHERE produit_id IN (SELECT produit_id FROM fact_prix WHERE pays='ES'))
                 AS nb_vendus_en_espagne,
               round(100.0 * count(*) FILTER (WHERE produit_id IN (SELECT produit_id FROM fact_prix WHERE pays='ES'))
                 / count(*), 1) AS pct_eligible
        FROM dim_produit
    """)

    for v in ("v_indice_prix", "v_indice_synthese", "v_densite_concurrentielle",
              "v_concurrents_par_enseigne", "v_eligibilite_catalogue"):
        con.execute(f"SELECT * FROM {v}").df().to_csv(PROCESSED / f"{v[2:]}.csv", index=False)
    con.execute("SELECT * FROM fact_marche").df().to_csv(PROCESSED / "marche.csv", index=False)
    pv = con.execute("""SELECT z.ville, e.enseigne, e.type, f.shop, f.nom, f.lat, f.lon
                        FROM fact_point_de_vente f JOIN dim_zone z USING (zone_id) JOIN dim_enseigne e USING (enseigne_id)""").df()
    pv.to_csv(PROCESSED / "points_de_vente.csv", index=False)

    for t in ("dim_produit", "dim_enseigne", "dim_pays", "dim_zone", "dim_hub", "dim_date",
              "fact_prix", "fact_marche", "fact_point_de_vente", "fact_concurrence_zone"):
        n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        log.info("%-22s %6d lignes", t, n)
    return con


if __name__ == "__main__":
    build().close()
