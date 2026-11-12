"""Brique IA : synthèse Go/No-Go rédigée par Claude à partir des KPIs calculés.

Lit les fichiers de data/processed/, les envoie à l'API Claude avec une consigne stricte
(n'utiliser que les chiffres fournis, signaler les hypothèses), et écrit
data/processed/synthese_ia.md.

Nécessite la variable ANTHROPIC_API_KEY (secret GitHub Actions ou fichier .env local).
Sans clé, le script s'arrête proprement sans rien écrire.
"""
from __future__ import annotations

import json

import pandas as pd
import requests

from src.common import PROCESSED, TODAY, env, get_logger

log = get_logger("synthese_ia")
MODEL = env("CLAUDE_MODEL", "claude-sonnet-5-5")

CONSIGNE = """Tu es analyste pour le comité exécutif du Groupe LDLC. Question : l'ouverture de magasins
de téléphonie en Espagne est-elle réalisable et rentable ? Rédige en français une synthèse de 200 mots
maximum : 3 constats chiffrés, 1 recommandation (Go, Go conditionnel ou No-Go) et les 2 données qui
manquent le plus. Utilise uniquement les chiffres ci-dessous. Quand un chiffre repose sur une hypothèse
(colonne statut ou calcul), dis-le. N'invente aucun chiffre."""


def contexte() -> str:
    parts = []
    for f in ("indice_synthese", "pnl_pilote", "marge_si_alignement", "densite_concurrentielle", "marche"):
        p = PROCESSED / f"{f}.csv"
        if p.exists():
            parts.append(f"## {f}\n{pd.read_csv(p).to_csv(index=False)}")
    return "\n".join(parts)


def main() -> None:
    key = env("ANTHROPIC_API_KEY")
    if not key:
        log.warning("ANTHROPIC_API_KEY absente : synthèse IA non générée")
        return
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        data=json.dumps({"model": MODEL, "max_tokens": 800,
                         "messages": [{"role": "user", "content": f"{CONSIGNE}\n\n{contexte()}"}]}),
        timeout=120,
    )
    r.raise_for_status()
    texte = "".join(b.get("text", "") for b in r.json()["content"])
    (PROCESSED / "synthese_ia.md").write_text(f"# Synthèse IA du {TODAY} ({MODEL})\n\n{texte}\n", encoding="utf-8")
    log.info("Synthèse écrite (%d caractères)", len(texte))


if __name__ == "__main__":
    main()
