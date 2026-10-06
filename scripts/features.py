"""Turn per-town, per-year species counts into one row per (town, target year, species).

Every feature for target year Y is computed from years strictly before Y, so the
label (was the species logged within 10 km of the town in October of Y) is never seen.
Candidates are the species logged within 50 km in some earlier October.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
FIRST_TARGET = 2019  # needs at least three earlier years of history


def build(counts: pd.DataFrame, target_years: list[int]) -> pd.DataFrame:
    wide = counts.pivot_table(
        index=["town", "taxon_id", "year"], columns="kind", values="count", aggfunc="sum", fill_value=0
    ).reset_index()
    for k in ("local_oct", "local_all", "region_oct"):
        if k not in wide:
            wide[k] = 0
    taxa = counts.drop_duplicates("taxon_id").set_index("taxon_id")[["name", "common", "iconic", "global_obs"]]
    totals = counts.groupby(["town", "year", "kind"])["count"].sum().unstack(fill_value=0)

    out = []
    for y in target_years:
        past = wide[wide.year < y]
        last = wide[wide.year == y - 1].set_index(["town", "taxon_id"])
        g = past.groupby(["town", "taxon_id"])
        f = pd.DataFrame({
            "loc_oct_sum": g["local_oct"].sum(),
            "loc_oct_years": g["local_oct"].apply(lambda s: (s > 0).sum()),
            "loc_all_sum": g["local_all"].sum(),
            "loc_all_years": g["local_all"].apply(lambda s: (s > 0).sum()),
            "reg_oct_sum": g["region_oct"].sum(),
            "reg_oct_years": g["region_oct"].apply(lambda s: (s > 0).sum()),
        })
        f = f[f.reg_oct_sum > 0]
        f["loc_oct_last"] = last["local_oct"].reindex(f.index).fillna(0).values
        f["loc_all_last"] = last["local_all"].reindex(f.index).fillna(0).values
        f["reg_oct_last"] = last["region_oct"].reindex(f.index).fillna(0).values

        tp = totals[totals.index.get_level_values("year") < y].groupby("town").sum()
        towns = f.index.get_level_values("town")
        for k, col in (("local_oct", "eff_loc_oct"), ("local_all", "eff_loc_all"), ("region_oct", "eff_reg_oct")):
            f[col] = tp[k].reindex(towns).fillna(0).values if k in tp else 0
        f["reg_oct_share"] = f.reg_oct_sum / f.eff_reg_oct.clip(lower=1)
        f["loc_oct_share"] = f.loc_oct_sum / f.eff_loc_oct.clip(lower=1)
        f["loc_oct_season"] = f.loc_oct_sum / f.loc_all_sum.clip(lower=1)

        cur = wide[wide.year == y].set_index(["town", "taxon_id"])["local_oct"]
        f["label"] = (cur.reindex(f.index).fillna(0).values > 0).astype(int)
        f["year"] = y
        out.append(f.reset_index())

    df = pd.concat(out, ignore_index=True)
    df = df.join(taxa, on="taxon_id")
    df["log_global_obs"] = np.log1p(df.global_obs.fillna(0))
    df["iconic"] = df.iconic.fillna("Unknown")
    return df


FEATURES = [
    "loc_oct_sum", "loc_oct_years", "loc_oct_last", "loc_all_sum", "loc_all_years", "loc_all_last",
    "reg_oct_sum", "reg_oct_years", "reg_oct_last", "eff_loc_oct", "eff_loc_all", "eff_reg_oct",
    "reg_oct_share", "loc_oct_share", "loc_oct_season", "log_global_obs", "iconic_code",
]
ICONIC = ["Aves", "Plantae", "Fungi", "Insecta", "Mammalia", "Arachnida", "Mollusca",
          "Reptilia", "Amphibia", "Actinopterygii", "Chromista", "Protozoa", "Animalia", "Unknown"]


def encode(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["iconic_code"] = df.iconic.map({k: i for i, k in enumerate(ICONIC)}).fillna(len(ICONIC) - 1)
    return df


def main() -> None:
    counts = pd.read_parquet(ROOT / "data" / "counts.parquet")
    years = sorted(counts.year.unique())
    df = build(counts, [y for y in years if y >= FIRST_TARGET] + [max(years) + 1])
    df.to_parquet(ROOT / "data" / "features.parquet", index=False)
    print(df.groupby("year").agg(rows=("label", "size"), positives=("label", "sum")))


if __name__ == "__main__":
    main()
