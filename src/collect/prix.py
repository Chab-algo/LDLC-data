"""Relevé automatique des prix smartphones (LDLC France, PcComponentes, MediaMarkt Espagne).

Lit config/produits.csv : une ligne par modèle, une colonne d'URL par enseigne et pays.
Pour chaque URL renseignée, le script télécharge la fiche produit et lit le prix dans les
données structurées de la page (JSON-LD schema.org Product/Offer, sinon balises meta).

Chaque passage ajoute des lignes à data/raw/prix_scrapes.csv (historique, jamais écrasé),
avec le statut du relevé. Les sites protégés par un anti-bot peuvent refuser la requête :
le statut l'indique et la ligne n'a pas de prix. On ne remplace jamais un prix manquant.

Le relevé manuel du 12/11/2026 (data/raw/prix_releves_manuel.csv) reste la base de départ.
"""
from __future__ import annotations

import json
import re

import pandas as pd
from bs4 import BeautifulSoup

from src.common import CONFIG, RAW, TODAY, get_logger, polite_get, session

log = get_logger("prix")
SOURCES = {
    "url_ldlc_fr": ("LDLC", "FR"),
    "url_ldlc_es": ("LDLC", "ES"),
    "url_pccomponentes_es": ("PcComponentes", "ES"),
    "url_mediamarkt_es": ("MediaMarkt", "ES"),
}
TVA = {"FR": 0.20, "ES": 0.21}


def _offers(node):
    if isinstance(node, list):
        for n in node:
            yield from _offers(n)
    elif isinstance(node, dict):
        if node.get("@type") in ("Offer", "AggregateOffer") or "price" in node or "lowPrice" in node:
            yield node
        for k in ("offers", "@graph", "mainEntity"):
            if k in node:
                yield from _offers(node[k])


def extract_price(html: str) -> tuple[float | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for off in _offers(data):
            p = off.get("price") or off.get("lowPrice")
            if p not in (None, ""):
                return float(str(p).replace(",", ".")), "json-ld"
    for sel in ({"itemprop": "price"}, {"property": "product:price:amount"}, {"property": "og:price:amount"}):
        m = soup.find("meta", attrs=sel)
        if m and m.get("content"):
            return float(m["content"].replace(",", ".")), f"meta {list(sel.values())[0]}"
    return None, "prix introuvable dans la page"


def main() -> None:
    prod = pd.read_csv(CONFIG / "produits.csv", dtype=str).fillna("")
    s = session()
    rows = []
    for p in prod.itertuples():
        for col, (enseigne, pays) in SOURCES.items():
            url = getattr(p, col)
            if not url:
                continue
            prix, statut = None, ""
            try:
                r = polite_get(s, url, timeout=30, retries=2)
                if r.status_code != 200:
                    statut = f"HTTP {r.status_code}"
                else:
                    prix, statut = extract_price(r.text)
            except Exception as e:  # noqa: BLE001
                statut = f"erreur {type(e).__name__}"
            rows.append({
                "date_releve": TODAY, "modele": p.modele, "marque": p.marque, "segment": p.segment,
                "enseigne": enseigne, "pays": pays, "prix_ttc_eur": prix, "taux_tva": TVA[pays],
                "prix_ht_eur": None if prix is None else round(prix / (1 + TVA[pays]), 2),
                "url_source": url, "methode": f"scraping automatique ({statut})" if prix else "",
                "statut": "ok" if prix else statut,
            })
            log.info("%s | %s %s : %s (%s)", p.modele, enseigne, pays, prix, statut)
    out = RAW / "prix_scrapes.csv"
    new = pd.DataFrame(rows)
    if out.exists() and not new.empty:
        new = pd.concat([pd.read_csv(out), new], ignore_index=True)
    if not new.empty:
        new.to_csv(out, index=False)
    ok = sum(1 for r in rows if r["statut"] == "ok")
    log.info("%d URL interrogées, %d prix relevés", len(rows), ok)


if __name__ == "__main__":
    main()
