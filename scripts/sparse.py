"""Split the backtest by how much October history each town had before 2025.

Towns are cut into thirds by their past October record count (eff_loc_oct for 2025), and each
method's mean squares-photographed is reported per third. Writes results/backtest_bands.json.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    b = json.loads((ROOT / "results" / "backtest.json").read_text("utf-8"))
    f = pd.read_parquet(ROOT / "data" / "features.parquet")
    history = f[f.year == b["test_year"]].groupby("town").eff_loc_oct.first()
    d = pd.DataFrame({m: pd.Series(r["per_town"]) for m, r in b["methods"].items()})
    d["history"] = history
    d["band"] = pd.qcut(d.history, 3, labels=["sparse", "middle", "dense"])
    out = {}
    for band, g in d.groupby("band", observed=True):
        out[str(band)] = {"towns": len(g), "median_past_october_records": float(g.history.median()),
                          **{m: round(float(g[m].mean()), 2) for m in b["methods"]}}
    (ROOT / "results" / "backtest_bands.json").write_text(json.dumps(out, indent=1), "utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
