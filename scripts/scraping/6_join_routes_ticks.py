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
        - Read both CSVs (routes + ticks).
        - Ensure consistent `route_id` field.
        - Perform full outer join on route_id.

    2. NORMALIZE HEADERS:
        - Strip whitespace, rename common variants, deduplicate columns.

    3. REMOVE DUPLICATES:
        - Drop duplicate route entries by ID (keep first).

    4. DROP UNNEEDED COLUMNS:
        - Remove columns like Length(ft), Ticks, route_id (optional),
          and duplicate variants like unique_climbers_x.

    5. YEAR CLEANUP:
        - Drop tick-year columns outside 1950..current_year.

    6. FILTER ROUTES:
        - Remove rows with missing/blank Grade.
        - Apply “classic” filters:
            • Votes ≥ 50
            • Stars ≥ 3.0
            • total_ticks ≥ 100

    7. CLEAN UNIQUE CLIMBERS:
        - Normalize `unique_climbers_y` → `unique_climbers`.

    8. REORDER COLUMNS:
        - Place Votes → total_ticks → unique_climbers together.

    9. SAVE:
        - Output final cleaned CSV.
        - Print summary (dropped years, final route count, columns).
"""

import argparse
from datetime import datetime
from pathlib import Path
import pandas as pd


# ================================================================
# DEFAULT PATHS
# ================================================================
BASE_DIR = Path(r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed")

DEFAULT_ROUTES = BASE_DIR / "routes_filtered.csv"
DEFAULT_TICKS = BASE_DIR / "tick_summary_by_route.csv"
DEFAULT_OUT = BASE_DIR / "joined_route_tick_cleaned.csv"


# ================================================================
# HELPER FUNCTIONS
# ================================================================
def deduplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicated columns by name, keeping the first occurrence."""
    return df.loc[:, ~df.columns.duplicated()]


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and rename common variants to canonical names."""
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    df = deduplicate_columns(df)

    rename_map = {
        "Route ID": "route_id",
        "RouteID": "route_id",
        "ID": "route_id",
        "Route Name": "route_name",
        "Total Ticks": "total_ticks",
        "Total_Ticks": "total_ticks",
        "Ticks Total": "total_ticks",
        "Stars ": "Stars",
        "Votes ": "Votes",
        "Length (feet)": "Length (ft)",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    df = deduplicate_columns(df)
    return df


# ================================================================
# MAIN PIPELINE
# ================================================================
def full_pipeline(routes_csv: str, ticks_csv: str) -> pd.DataFrame:
    """Perform join + cleaning pipeline on route and tick CSVs."""
    # 1) Load
    df_routes = pd.read_csv(routes_csv)
    df_ticks = pd.read_csv(ticks_csv)

    # Ensure/derive route_id
    if "route_id" not in df_routes.columns:
        if "URL" in df_routes.columns:
            df_routes["route_id"] = df_routes["URL"].str.extract(r"/route/(\d+)")
        else:
            raise ValueError("No 'route_id' and no 'URL' column in routes CSV.")
    df_routes["route_id"] = df_routes["route_id"].astype(str)
    if "route_id" not in df_ticks.columns:
        raise ValueError("No 'route_id' column in ticks CSV.")
    df_ticks["route_id"] = df_ticks["route_id"].astype(str)

    # Full outer join
    df_joined = pd.merge(df_routes, df_ticks, on="route_id", how="outer")

    # 2) Normalize headers
    df = normalize_headers(df_joined)

    # 3) Remove duplicate route entries
    id_candidates = [c for c in ["route_id", "Route ID", "RouteID", "ID"] if c in df.columns]
    route_id_col = id_candidates[0] if id_candidates else None
    if route_id_col:
        df_cleaned = df.drop_duplicates(subset=route_id_col, keep="first").copy()
    else:
        print("⚠️ No route ID column found; skipping de-duplication.")
        df_cleaned = df.copy()

    # 4) Drop unneeded columns
    cols_to_drop = [c for c in ["Length (ft)", "Ticks", "route_id", "unique_climbers_x"] if c in df_cleaned.columns]
    if cols_to_drop:
        df_cleaned = df_cleaned.drop(columns=cols_to_drop)

    # 5) Drop invalid year columns
    current_year = datetime.now().year
    year_cols = [col for col in df_cleaned.columns if str(col).isdigit() and len(str(col)) == 4]
    invalid_year_cols = [col for col in year_cols if int(col) > current_year or int(col) < 1950]
    if invalid_year_cols:
        df_cleaned = df_cleaned.drop(columns=invalid_year_cols)

    # 6) Filter routes with valid Grade
    if "Grade" in df_cleaned.columns:
        df_cleaned = df_cleaned[df_cleaned["Grade"].notna() & (df_cleaned["Grade"].astype(str).str.strip() != "")]
    else:
        print("⚠️ No 'Grade' column found; skipping grade-based filtering.")

    # 7) Apply classic filters
    for col in ["Votes", "Stars", "total_ticks"]:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")

    filters = []
    if "Votes" in df_cleaned.columns:
        filters.append(df_cleaned["Votes"] >= 50)
    else:
        filters.append(pd.Series([True] * len(df_cleaned), index=df_cleaned.index))

    if "Stars" in df_cleaned.columns:
        filters.append(df_cleaned["Stars"] >= 3.0)
    else:
        filters.append(pd.Series([True] * len(df_cleaned), index=df_cleaned.index))

    if "total_ticks" in df_cleaned.columns:
        filters.append(df_cleaned["total_ticks"] >= 100)
    else:
        filters.append(pd.Series([True] * len(df_cleaned), index=df_cleaned.index))

    mask = filters[0]
    for f in filters[1:]:
        mask &= f
    df_filtered = df_cleaned.loc[mask].copy()

    # 8) Clean unique_climbers column
    if "unique_climbers_y" in df_filtered.columns:
        df_filtered = df_filtered.rename(columns={"unique_climbers_y": "unique_climbers"})

    # 9) Reorder key columns
    if "Votes" in df_filtered.columns:
        cols = [c for c in df_filtered.columns if c not in ("total_ticks", "unique_climbers")]
        if "Votes" in cols:
            v_idx = cols.index("Votes")
            insert_after = v_idx + 1
            if "total_ticks" in df_filtered.columns:
                cols.insert(insert_after, "total_ticks")
                insert_after += 1
            if "unique_climbers" in df_filtered.columns:
                cols.insert(insert_after, "unique_climbers")
            df_filtered = df_filtered[cols]

    # Summary prints
    print("🧱 Columns after cleaning:", list(df_filtered.columns))
    print(f"🗓️ Dropped year columns outside 1950–{current_year}: {invalid_year_cols}")
    print(f"📉 Routes remaining after filters: {len(df_filtered)}")

    return df_filtered


# ================================================================
# ENTRY POINT
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="Join + clean route/tick CSVs (one-pass).")
    parser.add_argument("--routes", default=str(DEFAULT_ROUTES), help="Path to routes_filtered.csv")
    parser.add_argument("--ticks",  default=str(DEFAULT_TICKS), help="Path to tick_summary_by_route.csv")
    parser.add_argument("--out",    default=str(DEFAULT_OUT),   help="Full output path for final cleaned CSV")
    args = parser.parse_args()

    df_final = full_pipeline(args.routes, args.ticks)
    df_final.to_csv(args.out, index=False)
    print(f"✅ Filtered + cleaned data saved to: {args.out}")


if __name__ == "__main__":
    main()
