"""Lance toute la chaîne : collecte, base en étoile, compte de résultat simulé, synthèse IA.

Usage : python -m src.pipeline            (tout)
        python -m src.pipeline --offline  (sans collecte, reconstruit la base depuis data/raw)

Une étape de collecte qui échoue n'arrête pas la chaîne : on garde les données de la
collecte précédente et l'erreur est écrite dans data/processed/journal_collecte.csv.
"""
from __future__ import annotations

import sys
import traceback

import pandas as pd

from src.common import PROCESSED, TODAY, get_logger

log = get_logger("pipeline")


def main() -> None:
    from src.analysis import pnl_pilote
    from src.ai import synthese
    from src.collect import eurostat, osm_overpass, prix, routes
    from src.transform import build_star

    journal = []
    if "--offline" not in sys.argv:
        for name, mod in (("eurostat", eurostat), ("osm_overpass", osm_overpass),
                          ("routes", routes), ("prix", prix)):
            try:
                mod.main()
                journal.append((TODAY, name, "ok", ""))
            except Exception as e:  # noqa: BLE001
                log.error("Collecte %s en échec : %s", name, e)
                traceback.print_exc()
                journal.append((TODAY, name, "échec", str(e)[:300]))
    build_star.build().close()
    pnl_pilote.main()
    try:
        synthese.main()
    except Exception as e:  # noqa: BLE001
        log.error("Synthèse IA en échec : %s", e)
        journal.append((TODAY, "synthese_ia", "échec", str(e)[:300]))
    if journal:
        out = PROCESSED / "journal_collecte.csv"
        new = pd.DataFrame(journal, columns=["date", "etape", "statut", "detail"])
        if out.exists():
            new = pd.concat([pd.read_csv(out), new], ignore_index=True)
        new.to_csv(out, index=False)


if __name__ == "__main__":
    main()
