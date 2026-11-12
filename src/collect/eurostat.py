"""Collecte Eurostat (API JSON-stat, gratuite, sans clé).

Séries collectées, Espagne et France :
- sts_trtu_a  : chiffre d'affaires et volume des ventes du commerce de détail, annuel.
                NACE G474 = commerce de détail d'équipements de l'information et de la communication
                en magasin spécialisé (ordinateurs, télécoms). G47 = tout le commerce de détail (référence).
- demo_gind   : population au 1er janvier (pour ramener le marché à l'habitant).
- prc_hicp_aind : indice des prix à la consommation harmonisé, moyenne annuelle,
                  postes téléphonie (les codes COICOP sont testés un par un, Eurostat ayant changé
                  de nomenclature en 2026).

Sortie : data/raw/eurostat_<dataset>.csv au format long (une ligne par observation).
"""
from __future__ import annotations

import itertools

import pandas as pd

from src.common import RAW, TODAY, get_logger, polite_get, session

log = get_logger("eurostat")
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{ds}"

REQUESTS = [
    ("sts_trtu_a", {"geo": ["ES", "FR"], "nace_r2": ["G474", "G47"], "sinceTimePeriod": "2015"}),
    ("demo_gind", {"geo": ["ES", "FR"], "indic_de": "JAN", "sinceTimePeriod": "2020"}),
]
HICP_CODES = ["CP0820", "CP082", "CP083", "CP0830"]


def jsonstat_to_df(js: dict) -> pd.DataFrame:
    """Aplatit une réponse JSON-stat 2.0 en table longue."""
    dims = js["id"]
    sizes = js["size"]
    cats = []
    for d in dims:
        idx = js["dimension"][d]["category"]["index"]
        order = sorted(idx, key=idx.get) if isinstance(idx, dict) else list(idx)
        cats.append(order)
    values = js.get("value", {})
    if isinstance(values, list):
        values = {str(i): v for i, v in enumerate(values) if v is not None}
    status = js.get("status", {}) or {}
    rows = []
    for flat, combo in enumerate(itertools.product(*cats)):
        v = values.get(str(flat))
        if v is None:
            continue
        rows.append({**dict(zip(dims, combo)), "value": v, "flag": status.get(str(flat), "")})
    df = pd.DataFrame(rows)
    labels = {d: js["dimension"][d]["category"].get("label", {}) for d in dims}
    for d in dims:
        if d not in ("geo", "time") and d in df:
            df[f"{d}_label"] = df[d].map(labels[d])
    return df


def fetch(ds: str, params: dict) -> pd.DataFrame:
    s = session()
    q = {"format": "JSON", "lang": "EN", **params}
    r = polite_get(s, BASE.format(ds=ds), params=q)
    if r.status_code != 200:
        log.warning("%s %s -> HTTP %s : %s", ds, params, r.status_code, r.text[:200])
        return pd.DataFrame()
    df = jsonstat_to_df(r.json())
    df["dataset"] = ds
    df["date_collecte"] = TODAY
    return df


def main() -> None:
    for ds, params in REQUESTS:
        df = fetch(ds, params)
        log.info("%s : %d observations", ds, len(df))
        if not df.empty:
            df.to_csv(RAW / f"eurostat_{ds}.csv", index=False)

    frames = []
    for code in HICP_CODES:
        df = fetch("prc_hicp_aind", {"geo": ["ES", "FR"], "coicop": code, "unit": "INX_A_AVG", "sinceTimePeriod": "2015"})
        log.info("prc_hicp_aind coicop=%s : %d observations", code, len(df))
        if not df.empty:
            frames.append(df)
    if frames:
        pd.concat(frames).to_csv(RAW / "eurostat_prc_hicp_aind.csv", index=False)
    else:
        log.warning("Aucun code COICOP téléphonie trouvé dans prc_hicp_aind : à vérifier sur le site Eurostat")


if __name__ == "__main__":
    main()
