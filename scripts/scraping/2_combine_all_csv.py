# 📦 Combine all *_routes.csv files in folder, tagging each row with its source region
import pandas as pd
import glob
import os
from pathlib import Path

# 📁 Directory containing your region CSVs
region_folder = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\regions"

# 📄 Find all matching CSV files
csv_files = glob.glob(os.path.join(region_folder, "*.csv"))
print(f"🔍 Found {len(csv_files)} files to combine.")

dfs = []
for f in csv_files:
    try:
        df = pd.read_csv(f)
        # e.g., C:\...\regions\aspen.csv  -> "aspen"
        region_name = Path(f).stem
        df.insert(0, "source_region", region_name)  # put it as the first column
        dfs.append(df)
    except Exception as e:
        print(f"⚠️ Skipping {f} due to read error: {e}")

if not dfs:
    print("⚠️ No matching CSV files found or all failed to read.")
else:
    # Keep original column order across files; don’t sort columns
    combined = pd.concat(dfs, ignore_index=True, sort=False)

    # 📁 Top-level outputs folder
    master_folder = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs"
    os.makedirs(master_folder, exist_ok=True)

    # 📄 Save combined CSV
    output_path = os.path.join(master_folder, "all-combined-routes.csv")
    combined.to_csv(output_path, index=False)

    print(f"✅ Combined {len(dfs)} files — saved to: {output_path}")
    # Optional: quick peek
    print(combined.head(3).to_string(index=False))
