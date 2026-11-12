"""Compte de résultat simulé d'un magasin pilote LDLC en Espagne (Barcelone par défaut).

On ne connaît pas le chiffre d'affaires qu'un magasin LDLC ferait en Espagne. Plutôt que
d'inventer un CA, on calcule le CA minimum pour couvrir les charges (point mort), puis on le
compare à la taille du marché local de la téléphonie.

Toutes les hypothèses sont dans config/hypotheses_pnl.csv, avec leur statut :
donnée sourcée, proxy, hypothèse équipe. Le dashboard permet de les faire varier.

Second calcul : la marge que LDLC garderait s'il alignait ses prix sur le concurrent espagnol,
en supposant que son coût d'achat = prix HT France x (1 - marge brute du groupe).
C'est une hypothèse forte (la marge téléphonie réelle n'est pas publiée), signalée comme telle.

Sorties : data/processed/pnl_pilote.csv, data/processed/marge_si_alignement.csv,
          table fact_magasin_sim dans la base DuckDB.
"""
from __future__ import annotations

import duckdb
import pandas as pd

from src.common import CONFIG, DB_PATH, PROCESSED, get_logger

log = get_logger("pnl")


def hypotheses() -> dict[str, float]:
    h = pd.read_csv(CONFIG / "hypotheses_pnl.csv")
    return dict(zip(h.parametre, h.valeur.astype(float)))


def point_mort(h: dict[str, float]) -> dict[str, float]:
    loyer = h["surface_m2"] * h["loyer_eur_m2_mois"] * 12
    personnel = h["etp"] * h["salaire_brut_annuel_eur"] * (1 + h["taux_charges_patronales"])
    fixes = loyer + personnel
    marge_contrib = h["taux_marge_brute"] - h["autres_charges_pct_ca"]
    ca_pm = fixes / marge_contrib if marge_contrib > 0 else float("nan")
    return {"loyer_annuel": loyer, "personnel_annuel": personnel, "charges_fixes": fixes,
            "taux_contribution": marge_contrib, "ca_point_mort_ht": ca_pm}


def main() -> None:
    h = hypotheses()
    r = point_mort(h)
    con = duckdb.connect(str(DB_PATH))

    m = con.execute("SELECT indicateur, pays, annee, valeur FROM fact_marche").df()
    marche_es = m[(m.indicateur == "marche_telephonie") & (m.pays == "ES")].valeur.iloc[0] * 1e6
    pop_es = m[(m.indicateur == "population_1er_janvier") & (m.pays == "ES")].sort_values("annee")
    pop_es = float(pop_es.valeur.iloc[-1]) if len(pop_es) else None
    z = con.execute("SELECT ville, population FROM dim_zone").df().set_index("ville").population

    rows = [
        ("Loyer annuel", r["loyer_annuel"], "surface x loyer x 12"),
        ("Personnel (salaires + charges)", r["personnel_annuel"], "ETP x salaire x (1 + charges)"),
        ("Charges fixes totales", r["charges_fixes"], ""),
        ("Taux de contribution", r["taux_contribution"], "marge brute - autres charges variables"),
        ("CA HT au point mort", r["ca_point_mort_ht"], "charges fixes / taux de contribution"),
        ("Marché téléphonie Espagne", marche_es, "config/marche.csv (calcul équipe)"),
    ]
    ville = "Barcelona"
    if pop_es and pd.notna(z.get(ville)):
        marche_ville = marche_es * float(z[ville]) / pop_es
        rows += [(f"Marché téléphonie {ville} (au prorata de la population)", marche_ville,
                  "hypothèse : dépense par habitant égale à la moyenne nationale"),
                 (f"Part du marché de {ville} nécessaire au point mort", r["ca_point_mort_ht"] / marche_ville, "")]
    else:
        log.warning("Population manquante (Eurostat ou OSM pas encore collectés) : part de marché non calculée")
    pnl = pd.DataFrame(rows, columns=["poste", "valeur", "calcul"])
    pnl.to_csv(PROCESSED / "pnl_pilote.csv", index=False)

    ip = con.execute("SELECT * FROM v_indice_prix").df()
    ip["cout_achat_estime_ht"] = ip.prix_ht_ldlc_fr * (1 - h["taux_marge_brute"])
    ip["marge_si_alignement"] = 1 - ip.cout_achat_estime_ht / ip.prix_ht_es
    ip["canon_digital_eur"] = h["canon_digital_eur_par_mobile"]
    ip[["modele", "famille", "prix_ht_ldlc_fr", "prix_ht_es", "cout_achat_estime_ht", "marge_si_alignement"]] \
        .round(3).to_csv(PROCESSED / "marge_si_alignement.csv", index=False)

    con.register("pnl_df", pnl.assign(ville=ville))
    con.execute("CREATE OR REPLACE TABLE fact_magasin_sim AS SELECT * FROM pnl_df")
    con.close()

    for row in rows:
        log.info("%-60s %15.3f", row[0], row[1])
    log.info("Marge moyenne si alignement : %s", ip.groupby("famille").marge_si_alignement.mean().round(3).to_dict())


if __name__ == "__main__":
    main()
