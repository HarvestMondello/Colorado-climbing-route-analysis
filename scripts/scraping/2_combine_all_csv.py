"""
Script: combine_routes.py

Purpose:
    Combine all region-level CSV files in a folder into a single dataset,
    tagging each row with its source region (derived from the filename),
    and applying basic cleaning (remove 'Sign Up or Log In' routes and Route ID == 0).

Workflow:
    1) Discover input CSV files in data/raw/ (pattern: *.csv)
    2) Load each CSV into a pandas DataFrame
    3) Insert a leading 'source_region' column using the file stem
    4) Clean rows
    5) Concatenate all DataFrames
    6) Ensure output folder exists (data/processed/)
    7) Save combined CSV
    8) Print summary stats

Dependencies:
    - pandas
    - glob
    - pathlib
"""

import pandas as pd
import glob
from pathlib import Path

# ===========================
# PATH SETUP (PORTABLE)
# ===========================
# This file lives at: scripts/processing/combine_routes.py (example)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

print("RAW_DIR       =", RAW_DIR)
print("PROCESSED_DIR =", PROCESSED_DIR)

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ===========================
# DISCOVER CSV FILES
# ===========================
csv_files = list(RAW_DIR.glob("*.csv"))
print(f"🔍 Found {len(csv_files)} files to combine.")

# ===========================
# CLEANING FUNCTION
# ===========================
def clean_df(df: pd.DataFrame, file_label: str) -> pd.DataFrame:
    """
    Apply basic cleaning:
      - Remove rows where 'Route Name' == 'Sign Up or Log In'
      - Remove rows where 'Route ID' == 0
    """
    before = len(df)

    if "Route ID" in df.columns:
        df["Route ID"] = (
            pd.to_numeric(df["Route ID"], errors="coerce")
            .fillna(0)
            .astype("int64")
        )
        df = df[df["Route ID"] != 0]
    else:
        print(f"⚠️ [{file_label}] Missing 'Route ID' column")

    if "Route Name" in df.columns:
        df = df[~df["Route Name"].eq("Sign Up or Log In")]
    else:
        print(f"⚠️ [{file_label}] Missing 'Route Name' column")

    after = len(df)
    print(f"🧹 [{file_label}] Removed {before - after} rows (kept {after}/{before})")
    return df.reset_index(drop=True)

# ===========================
# MAIN COMBINE LOOP
# ===========================
dfs = []
region_counts = {}
total_rows_before = 0
total_rows_after = 0
total_removed = 0

for f in csv_files:
    try:
        df = pd.read_csv(f)
        file_label = f.name
        total_rows_before += len(df)

        region_name = f.stem
        df.insert(0, "source_region", region_name)

        before = len(df)
        df = clean_df(df, file_label)
        after = len(df)

        total_removed += (before - after)
        total_rows_after += after
        region_counts[region_name] = after

        dfs.append(df)

    except Exception as e:
        print(f"⚠️ Skipping {f} due to error: {e}")

# ===========================
# OUTPUT
# ===========================
if not dfs:
    print("⚠️ No valid CSV files found.")
else:
    combined = pd.concat(dfs, ignore_index=True, sort=False)

    output_path = PROCESSED_DIR / "all_combined_routes.csv"
    combined.to_csv(output_path, index=False, encoding="utf-8")

    total_count = len(combined)

    print("\n================ SUMMARY ================")
    print(f"📦 Files combined:        {len(dfs)}")
    print(f"🧾 Rows before cleaning:  {total_rows_before}")
    print(f"🧹 Rows removed:          {total_removed}")
    print(f"✅ Rows after cleaning:   {total_rows_after}")
    print(f"🔢 Total route count:     {total_count}")
    print(f"💾 Saved to:              {output_path}")
    print("========================================\n")

    print("Per-region route counts (desc):")
    for region, count in sorted(region_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_count * 100) if total_count else 0
        print(f"   {region}: {count} routes ({pct:.1f}%)")

    with pd.option_context("display.max_columns", None):
        print(combined.head(3).to_string(index=False))
