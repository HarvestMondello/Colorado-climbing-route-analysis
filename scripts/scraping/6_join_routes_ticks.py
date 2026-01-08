# -*- coding: utf-8 -*-
"""
Script: 6_join_routes_ticks.py

WORKFLOW NOTES
-------------------------------------------------------------------------
PURPOSE:
    Combine and clean route metadata + tick summary data into a unified
    per-route dataset, applying filters to highlight “classic” routes.

INPUTS (default paths):
    - data/processed/routes_filtered.csv
    - data/processed/tick_summary_by_route.csv

OUTPUT (default path):
    - data/processed/joined_route_tick_cleaned.csv

STEPS:
    1. LOAD DATA:
        - Read both CSVs (routes + ticks) with UTF-8.
        - Ensure consistent `route_id` (str) and derive from URL if needed.
        - LEFT join routes ⟕ ticks on route_id (routes are canonical).

    2. NORMALIZE HEADERS:
        - Lowercase, strip, snake_case (no spaces/parens), deduplicate.

    3. SMART COALESCE (no _x/_y in final output):
        - Temporarily suffix overlaps as (“”, “_y”).
        - Prefer ticks for: total_ticks, unique_climbers.
        - Prefer routes for everything else (fallback to ticks if routes null).
        - Drop all “_y” after coalescing (clean, single columns).

    4. REMOVE DUPLICATES:
        - Drop duplicate route rows by route_id (keep first).

    5. YEAR CLEANUP:
        - Rename 4-digit year columns like 2025_0/2025_y back to 2025.
        - Drop tick-year columns outside 1950..current_year.

    6. FILTER ROUTES:
        - Drop rows with missing/blank grade.
        - Keep “classic” routes:
            • votes ≥ 50
            • stars ≥ 3.0
            • total_ticks ≥ 100

    7. TIDY & ORDER:
        - Drop length_ft.
        - Ensure key columns grouped: votes → total_ticks → unique_climbers.
        - Keep route_id in final output.

    8. SAVE:
        - Output final cleaned CSV (UTF-8).
        - Print summary (dropped years, final route count, columns).
"""

import argparse
from datetime import datetime
from pathlib import Path
import re
import pandas as pd


# ================================================================
# DEFAULT PATHS (PORTABLE)
# ================================================================
# file lives at: scripts/processing/6_join_routes_ticks.py (example)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = PROJECT_ROOT / "data" / "processed"
BASE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_ROUTES = BASE_DIR / "routes_filtered.csv"
DEFAULT_TICKS = BASE_DIR / "tick_summary_by_route.csv"
DEFAULT_OUT = BASE_DIR / "joined_route_tick_cleaned.csv"


# ================================================================
# HEADER NORMALIZATION
# ================================================================
def snake_case(name: str) -> str:
    """Normalize a header to lowercase snake_case; collapse repeated underscores."""
    s = name.strip().lower()
    replacements = {"stars ": "stars", "votes ": "votes"}
    s = replacements.get(s, s)
    s = re.sub(r"[’'`]", "", s)             # drop apostrophes
    s = re.sub(r"[^a-z0-9]+", "_", s)       # non-alnum -> underscore
    s = re.sub(r"__+", "_", s).strip("_")   # collapse/trims
    return s


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Apply snake_case and map common synonyms to canonical names."""
    df = df.copy()
    df.columns = [snake_case(c) for c in df.columns]

    rename_map = {
        # ids
        "routeid": "route_id",
        "id": "route_id",
        # names
        "name": "route_name",
        # totals
        "ticks_total": "total_ticks",
        "ticks": "total_ticks",
        # votes/stars
        "stars": "stars",
        "votes": "votes",
        # url
        "url": "url",
        # length
        "length_feet": "length_ft",
        "length": "length_ft",
        # unique climbers
        "unique_climbers": "unique_climbers",
        # grade
        "grade": "grade",
        # area hierarchy
        "area_hierarchy": "area_hierarchy",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    df = df.loc[:, ~df.columns.duplicated()]
    return df


def read_csv_normalized(path: Path) -> pd.DataFrame:
    """Read CSV with UTF-8 and normalized headers."""
    df = pd.read_csv(path, encoding="utf-8")
    return normalize_headers(df)


# ================================================================
# MERGE & COALESCE
# ================================================================
def ensure_route_id(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a string route_id exists; derive from url when missing."""
    df = df.copy()
    if "route_id" not in df.columns:
        if "url" in df.columns:
            extracted = df["url"].astype(str).str.extract(r"/route/(\d+)", expand=False)
            if extracted.isna().all():
                raise ValueError("Could not derive route_id from url.")
            df["route_id"] = extracted
        else:
            raise ValueError("No 'route_id' and no 'url' column available.")
    df["route_id"] = df["route_id"].astype(str)
    return df


def smart_merge_routes_ticks(df_routes: pd.DataFrame, df_ticks: pd.DataFrame) -> pd.DataFrame:
    """
    LEFT join (routes ⟕ ticks) on route_id.
    For overlapping columns, coalesce to avoid _x/_y:
      - Prefer ticks for: total_ticks, unique_climbers
      - Prefer routes for everything else (fallback to ticks if routes null)
    """
    df_routes = ensure_route_id(df_routes)
    df_ticks = ensure_route_id(df_ticks)

    overlap = sorted(set(df_routes.columns).intersection(df_ticks.columns) - {"route_id"})

    merged = pd.merge(
        df_routes,
        df_ticks,
        on="route_id",
        how="left",
        suffixes=("", "_y"),
    )

    prefer_right = {"total_ticks", "unique_climbers"}

    for col in overlap:
        right_col = f"{col}_y"
        if right_col not in merged.columns:
            continue
        if col in prefer_right:
            merged[col] = merged[right_col].combine_first(merged[col])
        else:
            merged[col] = merged[col].combine_first(merged[right_col])
        merged = merged.drop(columns=[right_col])

    y_cols = [c for c in merged.columns if c.endswith("_y")]
    if y_cols:
        merged = merged.drop(columns=y_cols)

    return merged


# ================================================================
# YEAR NORMALIZATION & FILTERS
# ================================================================
def normalize_year_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns like 2025_0 or 2025_y back to plain 2025; de-duplicate."""
    rename_map = {}
    for col in df.columns:
        col_str = str(col)
        if re.fullmatch(r"\d{4}(_\d+|_y)", col_str):
            base = col_str.split("_")[0]
            rename_map[col] = base
    if rename_map:
        df = df.rename(columns=rename_map)
        df = df.loc[:, ~df.columns.duplicated()]
    return df


def drop_out_of_range_years(df: pd.DataFrame, start=1950, end=None):
    """Drop columns named exactly as 4-digit years outside [start..end]."""
    if end is None:
        end = datetime.now().year
    year_cols = [c for c in df.columns if re.fullmatch(r"\d{4}", str(c))]
    invalid = [c for c in year_cols if int(c) < start or int(c) > end]
    if invalid:
        df = df.drop(columns=invalid)
    return df, invalid, end


# ================================================================
# CLEANING & FILTERS
# ================================================================
def drop_duplicate_routes(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate rows by route_id (keep first)."""
    if "route_id" not in df.columns:
        return df
    return df.drop_duplicates(subset="route_id", keep="first")


def apply_classic_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Keep rows that pass classic filters (votes ≥50, stars ≥3.0, total_ticks ≥100)."""
    df = df.copy()
    for col in ("votes", "stars", "total_ticks"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "grade" in df.columns:
        df = df[df["grade"].astype(str).str.strip().ne("") & df["grade"].notna()]

    conds = []
    conds.append(df["votes"] >= 50 if "votes" in df.columns else True)
    conds.append(df["stars"] >= 3.0 if "stars" in df.columns else True)
    conds.append(df["total_ticks"] >= 100 if "total_ticks" in df.columns else True)

    if isinstance(conds[0], bool):
        mask = True
        for c in conds[1:]:
            mask = mask & (True if isinstance(c, bool) else c)
    else:
        mask = conds[0]
        for c in conds[1:]:
            mask = mask & (c if not isinstance(c, bool) else True)

    return df.loc[mask].copy()


def reorder_key_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Put votes → total_ticks → unique_climbers together early in the schema."""
    cols = list(df.columns)
    key_order = [c for c in ("votes", "total_ticks", "unique_climbers") if c in cols]

    front = ["route_id"] if "route_id" in cols else []
    front += [c for c in ("route_name", "grade") if c in cols]
    front += key_order

    rest = [c for c in cols if c not in set(front)]
    return df[front + rest]


# ================================================================
# MAIN PIPELINE
# ================================================================
def full_pipeline(routes_csv: str, ticks_csv: str) -> pd.DataFrame:
    """Perform join + cleaning pipeline on route and tick CSVs."""
    df_routes = read_csv_normalized(Path(routes_csv))
    df_ticks = read_csv_normalized(Path(ticks_csv))

    df = smart_merge_routes_ticks(df_routes, df_ticks)
    df = normalize_year_columns(df)
    df = drop_duplicate_routes(df)

    df, invalid_year_cols, current_year = drop_out_of_range_years(df, start=1950)

    if "length_ft" in df.columns:
        df = df.drop(columns=["length_ft"])

    df = apply_classic_filters(df)
    df = reorder_key_columns(df)

    print("🧱 Columns after cleaning:", list(df.columns))
    print(f"🗓️ Dropped year columns outside 1950–{current_year}: {invalid_year_cols}")
    print(f"📉 Routes remaining after filters: {len(df)}")

    return df


# ================================================================
# ENTRY POINT
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="Join + clean route/tick CSVs without _x/_y duplicates.")
    parser.add_argument("--routes", default=str(DEFAULT_ROUTES), help="Path to routes_filtered.csv")
    parser.add_argument("--ticks", default=str(DEFAULT_TICKS), help="Path to tick_summary_by_route.csv")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output path for final cleaned CSV")
    args = parser.parse_args()

    df_final = full_pipeline(args.routes, args.ticks)
    df_final.to_csv(args.out, index=False, encoding="utf-8")
    print(f"✅ Filtered + cleaned data saved to: {args.out}")


if __name__ == "__main__":
    main()
