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
    Contains per-tick records with columns like:
    route_id, route_name, date, year, month, month_name, climber, style, etc.

OUTPUT:
  - tick_summary_by_route.csv
    Contains one row per route_id with aggregated stats.

STEPS:
  1. CONFIGURATION:
     - Define input and output file paths.

  2. LOAD DATA:
     - Read CSV into DataFrame.
     - Parse `date` into datetime (`date_parsed`).

  3. MONTHLY TICK COUNTS:
     - Pivot route_id × month_name → tick count.
     - Ensure months ordered Jan → Dec.

  4. YEARLY TICK COUNTS:
     - Pivot route_id × year → tick count.
     - Columns sorted newest → oldest.

  5. DATE RANGE:
     - Compute first and last tick date per route.

  6. BASE AGGREGATIONS:
     - Total ticks
     - Unique climbers
     - Number of distinct years logged
     - Number of distinct months logged

  7. PRIVATE TICKS:
     - Count how many "Private Tick" entries per route.

  8. TOP CLIMBERS:
     - Count ticks per climber per route (excluding "Private Tick" and "Unknown").
     - Select top 25 climbers by tick volume per route.
     - Format as "Name:Count" and rank them.
     - Pivot wide into columns: Top Climber 1 … Top Climber 25.

  9. FINAL MERGE:
     - Join base stats, date ranges, monthly/yearly pivots, private tick counts,
       and top climbers into one summary DataFrame.

 10. ADD ROUTE NAME:
     - Merge in route_name from tick_details.csv.
     - Reorder columns so route_name is first.

 11. SAVE OUTPUT:
     - Write to tick_summary_by_route.csv.
     - Print confirmation with path.

-------------------------------------------------------------------------
"""

import pandas as pd

# ================================================================
# 1. CONFIGURATION
# ================================================================
input_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed\tick_details.csv"
output_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed\tick_summary_by_route.csv"

# ================================================================
# 2. LOAD DATA
# ================================================================
df = pd.read_csv(input_csv)
df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')

# ================================================================
# 3. MONTHLY TICK COUNTS
# ================================================================
month_pivot = df.pivot_table(index='route_id', columns='month_name', values='climber', aggfunc='count')
month_pivot = month_pivot.fillna(0).astype(int)
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
month_pivot = month_pivot.reindex(columns=month_order, fill_value=0)

# ================================================================
# 4. YEARLY TICK COUNTS (newest → oldest)
# ================================================================
year_pivot = df.pivot_table(index='route_id', columns='year', values='climber', aggfunc='count')
year_pivot = year_pivot.fillna(0).astype(int)
year_pivot = year_pivot[sorted(year_pivot.columns, reverse=True)]

# ================================================================
# 5. FIRST AND LAST TICK DATES
# ================================================================
date_range = df.groupby('route_id').agg(
    first_tick_date=('date_parsed', 'min'),
    last_tick_date=('date_parsed', 'max')
)

# ================================================================
# 6. BASE AGGREGATIONS
# ================================================================
base_agg = df.groupby('route_id').agg(
    total_ticks=('climber', 'count'),
    unique_climbers=('climber', 'nunique'),
    years_logged=('year', lambda x: x.dropna().nunique()),
    months_logged=('month', lambda x: x.dropna().nunique())
)

# ================================================================
# 7. PRIVATE TICKS COUNT
# ================================================================
private_tick_counts = (
    df[df['climber'] == "Private Tick"]
    .groupby('route_id')
    .size()
    .rename("Private Ticks")
    .to_frame()
)

# ================================================================
# 8. TOP 25 CLIMBERS PER ROUTE
# ================================================================
# Count climber ticks per route (exclude Private/Unknown)
climber_counts = (
    df[(df['climber'] != "Private Tick") & (df['climber'] != "Unknown")]
    .groupby(['route_id', 'climber'])
    .size()
    .reset_index(name='tick_count')
)

# Sort within each route and keep top 25
top10_per_route = (
    climber_counts
    .sort_values(['route_id', 'tick_count'], ascending=[True, False])
    .groupby('route_id')
    .head(25)  # updated to top 25
)

# Format: Name:Count
top10_per_route['climber_string'] = top10_per_route['climber'] + ":" + top10_per_route['tick_count'].astype(str)
top10_per_route['rank'] = top10_per_route.groupby('route_id').cumcount() + 1

# Pivot wide into Top Climber 1 … Top Climber 25
top_climbers = top10_per_route.pivot(index='route_id', columns='rank', values='climber_string')
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
id_name_map = df[['route_id', 'route_name']].drop_duplicates()
summary_df = summary_df.merge(id_name_map, on='route_id', how='left')

# Reorder columns so route_name comes first
cols = ['route_name'] + [c for c in summary_df.columns if c != 'route_name']
summary_df = summary_df[cols]

# ================================================================
# 11. SAVE OUTPUT
# ================================================================
summary_df.to_csv(output_csv, index=False)
print(f"✅ Summary saved to: {output_csv}")
