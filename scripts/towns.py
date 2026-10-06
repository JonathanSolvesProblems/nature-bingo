"""Small towns between Ottawa and Montreal, geocoded once with Nominatim and cached."""

import json
import time
from pathlib import Path

import requests

UA = "nature-bingo/0.1 (https://github.com/JonathanSolvesProblems/nature-bingo)"
OUT = Path(__file__).resolve().parent.parent / "data" / "towns.json"

TOWNS = [
    # Ontario
    "Hawkesbury, Ontario", "L'Orignal, Ontario", "Vankleek Hill, Ontario", "Alfred, Ontario",
    "Plantagenet, Ontario", "Rockland, Ontario", "Bourget, Ontario", "Casselman, Ontario",
    "Embrun, Ontario", "Russell, Ontario", "Limoges, Ontario", "Alexandria, Ontario",
    "Maxville, Ontario", "Lancaster, Ontario", "Cornwall, Ontario", "Long Sault, Ontario",
    "Ingleside, Ontario", "Morrisburg, Ontario", "Iroquois, Ontario", "Winchester, Ontario",
    "Chesterville, Ontario", "Kemptville, Ontario", "Merrickville, Ontario", "Prescott, Ontario",
    "Brockville, Ontario", "Gananoque, Ontario", "Athens, Ontario", "Smiths Falls, Ontario",
    "Perth, Ontario", "Carleton Place, Ontario", "Almonte, Ontario", "Arnprior, Ontario",
    "Renfrew, Ontario", "Westport, Ontario",
    # Quebec
    # Grenville is left out: it sits 1.5 km across the river from Hawkesbury.
    "Lachute, Quebec", "Brownsburg-Chatham, Quebec",
    "Saint-André-d'Argenteuil, Quebec", "Rigaud, Quebec", "Hudson, Quebec", "Montebello, Quebec",
    "Papineauville, Quebec", "Thurso, Quebec", "Saint-Polycarpe, Quebec", "Coteau-du-Lac, Quebec",
    "Huntingdon, Quebec", "Ormstown, Quebec", "Wakefield, Quebec", "Shawville, Quebec",
]


def geocode(name: str) -> dict | None:
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": name + ", Canada", "format": "json", "limit": 1},
        headers={"User-Agent": UA},
        timeout=30,
    )
    r.raise_for_status()
    hits = r.json()
    if not hits:
        return None
    return {"name": name.split(",")[0], "query": name, "lat": float(hits[0]["lat"]), "lng": float(hits[0]["lon"])}


def main() -> None:
    have = {t["query"]: t for t in json.loads(OUT.read_text("utf-8"))} if OUT.exists() else {}
    for name in TOWNS:
        if name in have:
            continue
        hit = geocode(name)
        print(name, "->", hit and (round(hit["lat"], 4), round(hit["lng"], 4)))
        if hit:
            have[name] = hit
        time.sleep(1.1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps([have[n] for n in TOWNS if n in have], indent=1), "utf-8")
    print(len(have), "towns")


if __name__ == "__main__":
    main()
