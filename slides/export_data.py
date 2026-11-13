"""Exporte les chiffres du dashboard vers slides/data.json (lu par build_deck.js)."""
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
P = ROOT / "data" / "processed"


def clean(v):
    return None if isinstance(v, float) and math.isnan(v) else v


def rd(name):
    return [{k: clean(v) for k, v in r.items()} for r in pd.read_csv(P / f"{name}.csv").to_dict("records")]


hyp = {r["parametre"]: float(r["valeur"]) for r in pd.read_csv(ROOT / "config" / "hypotheses_pnl.csv").to_dict("records")}
m = rd("marche")


def ser(pays):
    return sorted((r["annee"], r["valeur"]) for r in m if r["indicateur"] == "eurostat_VOL_SLS_G474_I21_CA" and r["pays"] == pays and r["annee"] >= 2021)


def pick(ind, pays="ES"):
    return [r for r in m if r["indicateur"] == ind and r["pays"] == pays][-1]


dens = rd("densite_concurrentielle")
bcn = next(r for r in dens if r["ville"] == "Barcelona")
loyer = hyp["surface_m2"] * hyp["loyer_eur_m2_mois"] * 12
pers = hyp["etp"] * hyp["salaire_brut_annuel_eur"] * (1 + hyp["taux_charges_patronales"])
fixes = loyer + pers
contrib = hyp["taux_marge_brute"] - hyp["autres_charges_pct_ca"]
ca = fixes / contrib
marche_ville = pick("marche_telephonie")["valeur"] * 1e6 * bcn["population"] / pick("population_1er_janvier")["valeur"]

out = dict(es=ser("ES"), fr=ser("FR"), tel=pick("marche_telephonie"), idx=rd("indice_prix"), syn=rd("indice_synthese"),
           marge=rd("marge_si_alignement"), dens=dens,
           sim=dict(loyer=loyer, pers=pers, fixes=fixes, contrib=contrib, ca=ca, marche_ville=marche_ville, part=ca / marche_ville),
           market_rows=[r for r in m if not str(r["source"]).startswith("Eurostat")])
(ROOT / "slides" / "data.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("slides/data.json écrit")
