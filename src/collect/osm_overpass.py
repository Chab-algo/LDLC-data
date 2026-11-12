"""Collecte OpenStreetMap via l'API Overpass (gratuite, sans clé).

Pour chaque ville de config/villes_es.csv :
- la population de la commune (tag `population` de la limite administrative, souvent repris de l'INE) ;
- tous les points de vente shop=mobile_phone, shop=electronics et shop=computer situés dans la commune,
  avec nom, marque, coordonnées.

Sorties : data/raw/osm_villes.csv et data/raw/osm_magasins.csv.
Limite connue : OSM est contributif. Un magasin absent d'OSM n'est pas compté. On le dit dans le README.
"""
from __future__ import annotations

import time

import pandas as pd

from src.common import CONFIG, RAW, TODAY, get_logger, session

log = get_logger("overpass")
ENDPOINTS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
SHOPS = "mobile_phone|electronics|computer"

QUERY = """
[out:json][timeout:180];
rel["boundary"="administrative"]["admin_level"="8"]["name"="{name}"]["ine:municipio"];
out tags center;
map_to_area->.a;
nwr["shop"~"^({shops})$"](area.a);
out tags center;
"""


def run(query: str) -> dict:
    s = session()
    last = None
    for ep in ENDPOINTS:
        for attempt in range(3):
            try:
                r = s.post(ep, data={"data": query}, timeout=240)
                if r.status_code == 200:
                    return r.json()
                last = f"{ep} HTTP {r.status_code}"
            except Exception as e:  # noqa: BLE001
                last = f"{ep} {e}"
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"Overpass indisponible : {last}")


def main() -> None:
    villes = pd.read_csv(CONFIG / "villes_es.csv")
    v_rows, m_rows = [], []
    for v in villes.itertuples():
        js = run(QUERY.format(name=v.nom_osm, shops=SHOPS))
        els = js.get("elements", [])
        rels = [e for e in els if e["type"] == "relation" and e.get("tags", {}).get("boundary") == "administrative"]
        if len(rels) != 1:
            log.warning("%s : %d limites administratives trouvées (attendu 1)", v.ville, len(rels))
        if rels:
            t = rels[0]["tags"]
            v_rows.append({
                "ville": v.ville, "osm_relation_id": rels[0]["id"], "code_ine": t.get("ine:municipio"),
                "population": pd.to_numeric(t.get("population"), errors="coerce"),
                "population_date": t.get("population:date", ""), "date_collecte": TODAY,
            })
        n = 0
        for e in els:
            t = e.get("tags", {})
            if "shop" not in t or e["type"] == "relation" and t.get("boundary"):
                continue
            c = e.get("center") or {"lat": e.get("lat"), "lon": e.get("lon")}
            m_rows.append({
                "ville": v.ville, "osm_type": e["type"], "osm_id": e["id"], "shop": t.get("shop"),
                "nom": t.get("name", ""), "marque": t.get("brand", ""), "operateur": t.get("operator", ""),
                "lat": c.get("lat"), "lon": c.get("lon"), "date_collecte": TODAY,
            })
            n += 1
        log.info("%s : %d points de vente", v.ville, n)
        time.sleep(5)
    pd.DataFrame(v_rows).to_csv(RAW / "osm_villes.csv", index=False)
    pd.DataFrame(m_rows).to_csv(RAW / "osm_magasins.csv", index=False)


if __name__ == "__main__":
    main()
