"""
Script: combine_routes.py

Purpose:
    Combine all region-level CSV files in a folder into a single dataset,
    tagging each row with its source region (derived from the filename),
    and applying basic cleaning (remove 'Sign Up or Log In' routes and Route ID == 0).

Workflow:
    1) Discover input CSV files in data/raw/ (pattern: *.csv)
    2) Load each CSV into a pandas DataFrame
    3) Insert a leading 'source_region' column using the file stem (e.g., aspen_routes)
    4) Clean rows:
         - Drop rows where Route Name == 'Sign Up or Log In'
         - Drop rows where Route ID == 0 (after numeric coercion)
    5) Concatenate all DataFrames (preserving original column order; no sort)
    6) Ensure the output folder exists (data/processed/)
    7) Save the combined result to data/processed/all_combined_routes.csv
    8) Print a short summary (file count, removed counts, head preview, per-region counts with %)

Input:
    - CSV files in:
      C:\\Users\\harve\\Documents\\Projects\\MP-routes-Python\\data\\raw

Output:
    - Combined CSV at:
      C:\\Users\\harve\\Documents\\Projects\\MP-routes-Python\\data\\processed\\all_combined_routes.csv

Dependencies:
    - pandas
    - glob
    - os
    - pathlib
"""

# 📦 Combine all *_routes.csv files in folder, tagging each row with its source region
import pandas as pd
import glob
import os
from pathlib import Path

# 📁 Directory containing your region CSVs
region_folder = r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\raw"

# 📄 Find all matching CSV files
csv_files = glob.glob(os.path.join(region_folder, "*.csv"))
print(f"🔍 Found {len(csv_files)} files to combine.")

def clean_df(df: pd.DataFrame, file_label: str) -> pd.DataFrame:
    """
    Apply basic cleaning:
      - Remove rows where 'Route Name' == 'Sign Up or Log In'
      - Remove rows where 'Route ID' == 0 (after numeric coercion)
    Handles missing columns gracefully.
    """
    before = len(df)

    # Normalize and coerce 'Route ID' to numeric if present
    if "Route ID" in df.columns:
        df["Route ID"] = pd.to_numeric(df["Route ID"], errors="coerce").fillna(0).astype("int64")
    else:
        print(f"   ⚠️  [{file_label}] Missing 'Route ID' column — skipping ID filter.")

    # Filter out placeholder name
    if "Route Name" in df.columns:
        df = df[~df["Route Name"].eq("Sign Up or Log In")]
    else:
        print(f"   ⚠️  [{file_label}] Missing 'Route Name' column — skipping name filter.")

    # Filter out Route ID == 0
    if "Route ID" in df.columns:
        df = df[df["Route ID"] != 0]

    after = len(df)
    removed = before - after
    print(f"   🧹  [{file_label}] Removed {removed} invalid rows (kept {after}/{before}).")
    return df.reset_index(drop=True)

dfs = []
region_counts = {}   # store per-region counts (after cleaning)
total_removed = 0
total_rows_before = 0
total_rows_after = 0

for f in csv_files:
    try:
        df = pd.read_csv(f)
        file_label = Path(f).name
        total_rows_before += len(df)

        # e.g., C:\...\aspen_routes.csv  -> "aspen_routes"
        region_name = Path(f).stem
        df.insert(0, "source_region", region_name)  # put it as the first column

        # Clean per-file
        before = len(df)
        df = clean_df(df, file_label)
        after = len(df)
        total_removed += (before - after)
        total_rows_after += after

        # record per-region route count
        region_counts[region_name] = after

        dfs.append(df)
    except Exception as e:
        print(f"⚠️ Skipping {f} due to read error: {e}")

if not dfs:
    print("⚠️ No matching CSV files found or all failed to read.")
else:
    combined = pd.concat(dfs, ignore_index=True, sort=False)

    master_folder = r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed"
    os.makedirs(master_folder, exist_ok=True)

    output_path = os.path.join(master_folder, "all_combined_routes.csv")
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

    # Per-region route counts (sorted descending) with percentage of total
    print("Per-region route counts (desc):")
    for region, count in sorted(region_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_count * 100.0) if total_count else 0.0
        print(f"   {region}: {count} routes ({pct:.1f}%)")

    # Optional: quick peek
    with pd.option_context("display.max_columns", None):
        print(combined.head(3).to_string(index=False))
