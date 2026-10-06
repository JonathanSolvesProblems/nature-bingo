"""Fetch a photo, its credit and licence for each species that can appear on a card.

Only openly licensed photos are kept (CC0, CC BY, CC BY-SA, CC BY-NC and variants), and the
photographer's attribution travels with the photo onto the printed card.
"""

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "taxa.json"
UA = "nature-bingo/0.1 (https://github.com/JonathanSolvesProblems/nature-bingo)"


def open_photo(t: dict) -> dict:
    """The default photo if it is openly licensed, else the first openly licensed taxon photo."""
    d = t.get("default_photo") or {}
    if d.get("license_code"):
        return d
    for tp in t.get("taxon_photos") or []:
        p = tp.get("photo") or {}
        if p.get("license_code"):
            return p
    return {}


def fetch(ids: list[int]) -> dict[int, dict]:
    have = {int(k): v for k, v in json.loads(OUT.read_text("utf-8")).items()} if OUT.exists() else {}
    have = {k: v for k, v in have.items() if v.get("photo")}  # retry anything still without an open photo
    todo = [i for i in ids if i not in have]
    for n in range(0, len(todo), 30):
        chunk = todo[n:n + 30]
        r = requests.get(f"https://api.inaturalist.org/v1/taxa/{','.join(map(str, chunk))}",
                         headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        for t in r.json()["results"]:
            p = open_photo(t)
            have[t["id"]] = {
                "name": t["name"],
                "common": t.get("preferred_common_name"),
                "iconic": t.get("iconic_taxon_name"),
                "photo": p.get("medium_url"),
                "photo_credit": p.get("attribution"),
                "photo_license": p.get("license_code"),
                "wikipedia": t.get("wikipedia_url"),
            }
        for i in chunk:
            have.setdefault(i, {"missing": True})
        OUT.write_text(json.dumps(have, indent=1), "utf-8")
        time.sleep(1.1)
    return have


def refresh_cards() -> None:
    """Re-apply photo, credit and names to every square in data/cards.json."""
    path = ROOT / "data" / "cards.json"
    cards = json.loads(path.read_text("utf-8"))
    info = fetch(sorted({s["taxon_id"] for c in cards.values() for s in c["squares"]}))
    missing = 0
    for c in cards.values():
        for s in c["squares"]:
            s.update({k: v for k, v in info.get(s["taxon_id"], {}).items() if k != "missing"})
            missing += not s.get("photo")
    path.write_text(json.dumps(cards, indent=1, ensure_ascii=False), "utf-8")
    print(f"refreshed {len(cards)} cards, {missing} squares still without an open photo")


if __name__ == "__main__":
    if sys.argv[1:] == ["--refresh-cards"]:
        refresh_cards()
    else:
        print(len(fetch([int(x) for x in sys.argv[1:]])), "taxa cached")
