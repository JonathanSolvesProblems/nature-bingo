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


def fetch(ids: list[int]) -> dict[int, dict]:
    have = {int(k): v for k, v in json.loads(OUT.read_text("utf-8")).items()} if OUT.exists() else {}
    todo = [i for i in ids if i not in have]
    for n in range(0, len(todo), 30):
        chunk = todo[n:n + 30]
        r = requests.get(f"https://api.inaturalist.org/v1/taxa/{','.join(map(str, chunk))}",
                         headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        for t in r.json()["results"]:
            p = t.get("default_photo") or {}
            have[t["id"]] = {
                "name": t["name"],
                "common": t.get("preferred_common_name"),
                "iconic": t.get("iconic_taxon_name"),
                "photo": p.get("medium_url") if p.get("license_code") else None,
                "photo_credit": p.get("attribution") if p.get("license_code") else None,
                "photo_license": p.get("license_code"),
                "wikipedia": t.get("wikipedia_url"),
            }
        for i in chunk:
            have.setdefault(i, {"missing": True})
        OUT.write_text(json.dumps(have, indent=1), "utf-8")
        time.sleep(1.1)
    return have


if __name__ == "__main__":
    ids = [int(x) for x in sys.argv[1:]]
    print(len(fetch(ids)), "taxa cached")
