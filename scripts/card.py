"""Build this October's cards: TabPFN trained on every target year up to 2025, scoring 2026.

Usage: python scripts/card.py [town ...]   (no towns = all 48)
Writes data/cards.json, one 16-square card per town, plus the 2025 backtest result for that town
so the card can say how much of last year's card somebody actually photographed.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest import CARD, SEED, sample_train, shortlist, BATCH  # noqa: E402
from features import FEATURES, encode  # noqa: E402
from taxa import fetch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CARD_YEAR = 2026


def main(towns: list[str]) -> None:
    from tabpfn import TabPFNClassifier

    df = shortlist(encode(pd.read_parquet(ROOT / "data" / "features.parquet")))
    train = sample_train(df[df.year < CARD_YEAR])
    target = df[df.year == CARD_YEAR]
    if towns:
        target = target[target.town.isin(towns)]
    target = target.copy()

    model = TabPFNClassifier(device="cuda", random_state=SEED, ignore_pretraining_limits=True)
    model.fit(train[FEATURES].values, train.label.values)
    target["score"] = np.concatenate([
        model.predict_proba(target[FEATURES].values[i:i + BATCH])[:, 1] for i in range(0, len(target), BATCH)
    ])

    back = json.loads((ROOT / "results" / "backtest.json").read_text("utf-8"))["methods"]["tabpfn"]["per_town"]
    picks = target.sort_values(["town", "score"], ascending=[True, False]).groupby("town").head(CARD)
    info = fetch([int(t) for t in picks.taxon_id.unique()])

    out_path = ROOT / "data" / "cards.json"
    cards = json.loads(out_path.read_text("utf-8")) if out_path.exists() else {}
    for town, g in picks.groupby("town"):
        cards[town] = {
            "year": CARD_YEAR,
            "backtest_2025_logged": back.get(town),
            "squares": [
                {
                    "taxon_id": int(r.taxon_id),
                    "score": round(float(r.score), 4),
                    "seen_here_past_octobers": int(r.loc_oct_sum),
                    "seen_region_past_octobers": int(r.reg_oct_sum),
                    **{k: v for k, v in info.get(int(r.taxon_id), {}).items() if k != "missing"},
                }
                for r in g.itertuples()
            ],
        }
    out_path.write_text(json.dumps(cards, indent=1, ensure_ascii=False), "utf-8")
    for town in sorted(picks.town.unique()):
        print(f"\n{town}")
        for s in cards[town]["squares"]:
            print(f"  {s['score']:.3f}  {s.get('common') or s['name']:32s} {s.get('iconic')}  here:{s['seen_here_past_octobers']} region:{s['seen_region_past_octobers']}")


if __name__ == "__main__":
    main(sys.argv[1:])
