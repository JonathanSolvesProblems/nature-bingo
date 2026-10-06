"""Blind backtest: build each town's October 2025 card from data up to 2024, then
score it against what iNaturalist users actually logged within 10 km that October.

Methods compared on identical rows:
  last_october  rank by the town's own past October counts, ties broken by the region's
  region        rank by the 50 km region's past October counts
  hgb           gradient boosting (scikit-learn) on the same features and training rows
  tabpfn        TabPFN, open weights, run locally
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import FEATURES, encode  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TEST_YEAR = 2025
CARD = 16  # a 4x4 card
SHORTLIST = 300  # per town and year, by regional October count, identical for every method
TRAIN_ROWS = 4_000  # TabPFN context; larger spills past 8 GB of VRAM
BATCH = 1_000
SEED = 0


def shortlist(df: pd.DataFrame) -> pd.DataFrame:
    rank = df.groupby(["town", "year"]).reg_oct_sum.rank(method="first", ascending=False)
    return df[rank <= SHORTLIST]


def sample_train(train: pd.DataFrame) -> pd.DataFrame:
    pos = train[train.label == 1]
    neg = train[train.label == 0]
    pos = pos.sample(min(len(pos), TRAIN_ROWS // 2), random_state=SEED)
    neg = neg.sample(min(len(neg), TRAIN_ROWS - len(pos)), random_state=SEED)
    return pd.concat([pos, neg]).sample(frac=1, random_state=SEED)


def tabpfn_scores(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    from tabpfn import TabPFNClassifier

    model = TabPFNClassifier(device="cuda", random_state=SEED, ignore_pretraining_limits=True)
    model.fit(train[FEATURES].values, train.label.values)
    parts = []
    for i in range(0, len(test), BATCH):
        parts.append(model.predict_proba(test[FEATURES].values[i:i + BATCH])[:, 1])
        print(f"  tabpfn {min(i + BATCH, len(test))}/{len(test)}", flush=True)
    return np.concatenate(parts)


def score_cards(test: pd.DataFrame, col: str, towns: list[str]) -> dict:
    hits = []
    for town in towns:
        t = test[test.town == town].sort_values([col, "reg_oct_sum"], ascending=False).head(CARD)
        hits.append(int(t.label.sum()))
    return {"mean_hits": float(np.mean(hits)), "per_town": dict(zip(towns, hits))}


def main() -> None:
    full = encode(pd.read_parquet(ROOT / "data" / "features.parquet"))
    df = shortlist(full)
    train_all = df[df.year < TEST_YEAR]
    test = df[df.year == TEST_YEAR].copy()
    full_test = full[full.year == TEST_YEAR]
    shortlist_recall = test.label.sum() / max(full_test.label.sum(), 1)

    # A card can only be graded where somebody logged something that October.
    logged = test.groupby("town").label.sum()
    towns = sorted(logged[logged > 0].index)

    train = sample_train(train_all)
    test["last_october"] = test.loc_oct_sum + test.reg_oct_sum / 1e6
    test["region"] = test.reg_oct_sum.astype(float)

    t0 = time.time()
    hgb = HistGradientBoostingClassifier(random_state=SEED).fit(train[FEATURES], train.label)
    test["hgb"] = hgb.predict_proba(test[FEATURES])[:, 1]
    t_hgb = time.time() - t0

    t0 = time.time()
    test["tabpfn"] = tabpfn_scores(train, test)
    t_tab = time.time() - t0

    results = {
        "test_year": TEST_YEAR,
        "card_size": CARD,
        "shortlist": SHORTLIST,
        "shortlist_keeps_logged": round(float(shortlist_recall), 3),
        "towns_graded": len(towns),
        "towns_total": int(test.town.nunique()),
        "train_rows": len(train),
        "train_rows_available": len(train_all),
        "test_rows": len(test),
        "seconds": {"hgb": round(t_hgb, 1), "tabpfn": round(t_tab, 1)},
        "methods": {m: score_cards(test, m, towns) for m in ("last_october", "region", "hgb", "tabpfn")},
    }
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "backtest.json").write_text(json.dumps(results, indent=1), "utf-8")
    test[["town", "taxon_id", "name", "common", "iconic", "label", "loc_oct_sum", "reg_oct_sum",
          "last_october", "region", "hgb", "tabpfn"]].to_parquet(out / "backtest_scores.parquet", index=False)

    print(f"{len(towns)} of {test.town.nunique()} towns had an October {TEST_YEAR} record to grade against")
    for m, r in results["methods"].items():
        print(f"  {m:13s} {r['mean_hits']:.2f} of {CARD} squares logged on average")


if __name__ == "__main__":
    main()
