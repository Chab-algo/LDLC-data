"""Distances et temps de trajet routiers entre les hubs LDLC et les villes espagnoles.

Si la variable ORS_API_KEY existe (clé gratuite OpenRouteService), on utilise ORS Matrix.
Sinon on utilise le serveur de démonstration public OSRM (gratuit, sans clé, usage léger).

Sortie : data/raw/distances_routieres.csv
"""
from __future__ import annotations

import pandas as pd

from src.common import CONFIG, RAW, TODAY, env, get_logger, polite_get, session

log = get_logger("routes")


def osrm(hubs: pd.DataFrame, villes: pd.DataFrame) -> pd.DataFrame:
    pts = pd.concat([hubs[["lon", "lat"]], villes[["lon", "lat"]]])
    coords = ";".join(f"{r.lon},{r.lat}" for r in pts.itertuples())
    src = ";".join(str(i) for i in range(len(hubs)))
    dst = ";".join(str(i) for i in range(len(hubs), len(pts)))
    url = f"https://router.project-osrm.org/table/v1/driving/{coords}"
    r = polite_get(session(), url, params={"sources": src, "destinations": dst, "annotations": "distance,duration"})
    r.raise_for_status()
    js = r.json()
    rows = []
    for i, h in enumerate(hubs.itertuples()):
        for j, v in enumerate(villes.itertuples()):
            d, t = js["distances"][i][j], js["durations"][i][j]
            rows.append({"hub": h.hub, "ville": v.ville, "distance_km": None if d is None else round(d / 1000, 1),
                         "duree_h": None if t is None else round(t / 3600, 2), "moteur": "OSRM demo"})
    return pd.DataFrame(rows)


def ors(hubs: pd.DataFrame, villes: pd.DataFrame, key: str) -> pd.DataFrame:
    pts = pd.concat([hubs[["lon", "lat"]], villes[["lon", "lat"]]])
    body = {"locations": pts.values.tolist(), "sources": list(range(len(hubs))),
            "destinations": list(range(len(hubs), len(pts))), "metrics": ["distance", "duration"], "units": "km"}
    s = session()
    r = s.post("https://api.openrouteservice.org/v2/matrix/driving-hgv", json=body,
               headers={"Authorization": key}, timeout=60)
    r.raise_for_status()
    js = r.json()
    rows = []
    for i, h in enumerate(hubs.itertuples()):
        for j, v in enumerate(villes.itertuples()):
            rows.append({"hub": h.hub, "ville": v.ville, "distance_km": js["distances"][i][j],
                         "duree_h": round(js["durations"][i][j] / 3600, 2), "moteur": "OpenRouteService poids lourd"})
    return pd.DataFrame(rows)


def main() -> None:
    hubs = pd.read_csv(CONFIG / "hubs.csv")
    villes = pd.read_csv(CONFIG / "villes_es.csv")
    key = env("ORS_API_KEY")
    df = ors(hubs, villes, key) if key else osrm(hubs, villes)
    df["date_collecte"] = TODAY
    df.to_csv(RAW / "distances_routieres.csv", index=False)
    log.info("%d trajets calculés avec %s", len(df), df.moteur.iloc[0])


if __name__ == "__main__":
    main()
