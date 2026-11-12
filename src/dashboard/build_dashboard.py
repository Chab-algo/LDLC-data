"""Génère le dashboard HTML (dashboard/index.html) à partir de data/processed/.

Le gabarit est dashboard/template.html. Ce script y injecte les données en JSON :
on relance `python -m src.dashboard.build_dashboard` après chaque collecte et le
dashboard est à jour. La synthèse IA est générée dans la page, à la demande.
"""
from __future__ import annotations

import json
import math

import pandas as pd

from src.common import CONFIG, PROCESSED, ROOT, TODAY, get_logger

log = get_logger("dashboard")
OUT = ROOT / "dashboard"


def records(name: str) -> list[dict]:
    p = PROCESSED / f"{name}.csv"
    if not p.exists():
        log.warning("%s absent", p.name)
        return []
    df = pd.read_csv(p)
    out = []
    for r in df.to_dict(orient="records"):
        out.append({k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()})
    return out


def main() -> None:
    journal = records("journal_collecte")
    data = {
        "genere_le": TODAY,
        "indice_prix": records("indice_prix"),
        "indice_synthese": records("indice_synthese"),
        "marge_si_alignement": records("marge_si_alignement"),
        "densite": records("densite_concurrentielle"),
        "concurrents": records("concurrents_par_enseigne"),
        "marche": records("marche"),
        "pnl": records("pnl_pilote"),
        "eligibilite": records("eligibilite_catalogue"),
        "hypotheses": pd.read_csv(CONFIG / "hypotheses_pnl.csv").to_dict(orient="records"),
        "journal": journal[-12:],
    }
    tpl = (OUT / "template.html").read_text(encoding="utf-8")
    html = tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    log.info("dashboard/index.html écrit (%d Ko)", len(html) // 1024)


if __name__ == "__main__":
    main()
