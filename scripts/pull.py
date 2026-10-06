"""Pull iNaturalist research-grade species counts per town and year.

Three queries per town and year:
  local_oct  October, 10 km
  local_all  all months, 10 km
  region_oct October, 50 km
Each response page is cached under data/cache, so a rerun only fetches what is missing.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache"
UA = "nature-bingo/0.1 (https://github.com/JonathanSolvesProblems/nature-bingo)"
API = "https://api.inaturalist.org/v1/observations/species_counts"
YEARS = range(2016, 2026)
QUERIES = {"local_oct": (10, 10), "local_all": (10, None), "region_oct": (50, 10)}

_last = 0.0


def get(params: dict) -> dict:
    global _last
    key = hashlib.sha1(json.dumps(params, sort_keys=True).encode()).hexdigest()
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    for attempt in range(6):
        wait = 1.05 - (time.time() - _last)
        if wait > 0:
            time.sleep(wait)
        _last = time.time()
        try:
            r = requests.get(API, params=params, headers={"User-Agent": UA}, timeout=60)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            data = r.json()
            CACHE.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data), "utf-8")
            return data
        except requests.RequestException as e:
            print("  retry", attempt, e, file=sys.stderr)
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"gave up on {params}")


def species_counts(lat: float, lng: float, radius: int, year: int, month: int | None) -> list[dict]:
    rows, page = [], 1
    while True:
        params = {
            "lat": round(lat, 4), "lng": round(lng, 4), "radius": radius, "year": year,
            "quality_grade": "research", "rank": "species", "per_page": 500, "page": page,
        }
        if month:
            params["month"] = month
        data = get(params)
        for r in data["results"]:
            t = r["taxon"]
            rows.append({
                "taxon_id": t["id"], "name": t["name"],
                "common": t.get("preferred_common_name"),
                "iconic": t.get("iconic_taxon_name"),
                "global_obs": t.get("observations_count"),
                "count": r["count"],
            })
        if page * 500 >= data["total_results"]:
            return rows
        page += 1


def main() -> None:
    towns = json.loads((ROOT / "data" / "towns.json").read_text("utf-8"))
    out = []
    for i, town in enumerate(towns):
        for year in YEARS:
            for kind, (radius, month) in QUERIES.items():
                for row in species_counts(town["lat"], town["lng"], radius, year, month):
                    out.append({"town": town["name"], "year": year, "kind": kind, **row})
        print(f"{i + 1}/{len(towns)} {town['name']}: {len(out)} rows so far", flush=True)
    import pandas as pd
    pd.DataFrame(out).to_parquet(ROOT / "data" / "counts.parquet", index=False)
    print("wrote data/counts.parquet", len(out))


if __name__ == "__main__":
    main()
