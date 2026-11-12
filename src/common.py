"""Chemins, session HTTP et petites fonctions partagées par tous les scripts."""
from __future__ import annotations

import logging
import os
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "ldlc_espagne.duckdb"

for p in (RAW, PROCESSED):
    p.mkdir(parents=True, exist_ok=True)

TODAY = date.today().isoformat()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "LDLC-data student project (Eugenia School) - contact via GitHub Chab-algo/ldlc-data",
        "Accept-Language": "fr-FR,fr;q=0.9,es;q=0.8,en;q=0.7",
    })
    return s


def polite_get(s: requests.Session, url: str, *, params=None, timeout=60, retries=3, pause=2.0, **kw):
    """GET avec quelques tentatives et une pause entre deux appels (APIs publiques gratuites)."""
    last = None
    for i in range(retries):
        try:
            r = s.get(url, params=params, timeout=timeout, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            return r
        except requests.RequestException as e:  # noqa: PERF203
            last = e
            time.sleep(pause * (i + 1))
    raise last  # type: ignore[misc]


def env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name)
    return v if v else default
