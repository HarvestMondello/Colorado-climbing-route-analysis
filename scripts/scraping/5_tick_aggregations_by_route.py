"""
5-tick-aggregations-by-route.py
-------------------------------------------------------------------------

WORKFLOW NOTES
-------------------------------------------------------------------------

PURPOSE:
  Aggregate tick-level climbing data (from tick_details.csv) into
  a per-route summary (tick_summary_by_route.csv).

INPUT:
  - tick_details.csv (from 4-tick-scraper-updated.py)

OUTPUT:
  - tick_summary_by_route.csv

-------------------------------------------------------------------------
"""

from pathlib import Path
import pandas as pd

# ================================================================
# 1. CONFIGURATION (PORTABLE)
# ================================================================
# file lives at: scripts/processing/5-tick-aggregations-by-route.py (example)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

input_csv = PROCESSED_DIR / "tick_details.csv"
output_csv = PROCESSED_DIR / "tick_summary_by_route.csv"

print("INPUT_CSV  =", input_csv)
print("OUTPUT_CSV =", output_csv)

# ================================================================
# 2. LOAD DATA
# ================================================================
df = pd.read_csv(input_csv)
df["date_parsed"] = pd.to_datetime(df["date"], errors="coerce")

# ================================================================
# 3. MONTHLY TICK COUNTS
# ================================================================
month_pivot = df.pivot_table(index="route_id", columns="month_name", values="climber", aggfunc="count")
month_pivot = month_pivot.fillna(0).astype(int)
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
month_pivot = month_pivot.reindex(columns=month_order, fill_value=0)

# ================================================================
# 4. YEARLY TICK COUNTS (newest → oldest)
# ================================================================
year_pivot = df.pivot_table(index="route_id", columns="year", values="climber", aggfunc="count")
year_pivot = year_pivot.fillna(0).astype(int)
year_pivot = year_pivot[sorted(year_pivot.columns, reverse=True)]

# ================================================================
# 5. FIRST AND LAST TICK DATES
# ================================================================
date_range = df.groupby("route_id").agg(
    first_tick_date=("date_parsed", "min"),
    last_tick_date=("date_parsed", "max"),
)

# ================================================================
# 6. BASE AGGREGATIONS
# ================================================================
base_agg = df.groupby("route_id").agg(
    total_ticks=("climber", "count"),
    unique_climbers=("climber", "nunique"),
    years_logged=("year", lambda x: x.dropna().nunique()),
    months_logged=("month", lambda x: x.dropna().nunique()),
)

# ================================================================
# 7. PRIVATE TICKS COUNT
# ================================================================
private_tick_counts = (
    df[df["climber"] == "Private Tick"]
    .groupby("route_id")
    .size()
    .rename("Private Ticks")
    .to_frame()
)

# ================================================================
# 8. TOP 25 CLIMBERS PER ROUTE
# ================================================================
climber_counts = (
    df[(df["climber"] != "Private Tick") & (df["climber"] != "Unknown")]
    .groupby(["route_id", "climber"])
    .size()
    .reset_index(name="tick_count")
)

top10_per_route = (
    climber_counts
    .sort_values(["route_id", "tick_count"], ascending=[True, False])
    .groupby("route_id")
    .head(25)
)

top10_per_route["climber_string"] = top10_per_route["climber"] + ":" + top10_per_route["tick_count"].astype(str)
top10_per_route["rank"] = top10_per_route.groupby("route_id").cumcount() + 1

top_climbers = top10_per_route.pivot(index="route_id", columns="rank", values="climber_string")
top_climbers.columns = [f"Top Climber {i}" for i in top_climbers.columns]
top_climbers = top_climbers.fillna("")

# ================================================================
# 9. FINAL MERGE
# ================================================================
summary_df = (
    base_agg
    .join(date_range)
    .join(month_pivot)
    .join(year_pivot)
    .join(private_tick_counts)
    .join(top_climbers)
    .fillna({"Private Ticks": 0})
    .reset_index()
)

# ================================================================
# 10. ADD ROUTE NAME
# ================================================================
id_name_map = df[["route_id", "route_name"]].drop_duplicates()
summary_df = summary_df.merge(id_name_map, on="route_id", how="left")

cols = ["route_name"] + [c for c in summary_df.columns if c != "route_name"]
summary_df = summary_df[cols]

# ================================================================
# 11. SAVE OUTPUT
# ================================================================
summary_df.to_csv(output_csv, index=False)
print(f"✅ Summary saved to: {output_csv}")
