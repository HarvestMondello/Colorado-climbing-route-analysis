# 5-tick-aggregations-by-route.py
import pandas as pd

# --- CONFIGURATION ---
input_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\tick-details.csv"
output_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\tick-summary-by-route.csv"

# --- LOAD DATA ---
df = pd.read_csv(input_csv)
df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')

# --- MONTHLY TICK COUNTS ---
month_pivot = df.pivot_table(index='route_id', columns='month_name', values='climber', aggfunc='count')
month_pivot = month_pivot.fillna(0).astype(int)
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
month_pivot = month_pivot.reindex(columns=month_order, fill_value=0)

# --- YEARLY TICK COUNTS (Newest to Oldest) ---
year_pivot = df.pivot_table(index='route_id', columns='year', values='climber', aggfunc='count')
year_pivot = year_pivot.fillna(0).astype(int)
year_pivot = year_pivot[sorted(year_pivot.columns, reverse=True)]

# --- FIRST AND LAST TICK DATES ---
date_range = df.groupby('route_id').agg(
    first_tick_date=('date_parsed', 'min'),
    last_tick_date=('date_parsed', 'max')
)

# --- BASE AGGREGATIONS ---
base_agg = df.groupby('route_id').agg(
    total_ticks=('climber', 'count'),
    unique_climbers=('climber', 'nunique'),
    years_logged=('year', lambda x: x.dropna().nunique()),
    months_logged=('month', lambda x: x.dropna().nunique())
)

# --- PRIVATE TICKS COUNT ---
private_tick_counts = (
    df[df['climber'] == "Private Tick"]
    .groupby('route_id')
    .size()
    .rename("Private Ticks")
    .to_frame()
)

# --- TOP 25 CLIMBERS PER ROUTE (as Name:Count) ---
climber_counts = (
    df[(df['climber'] != "Private Tick") & (df['climber'] != "Unknown")]
    .groupby(['route_id', 'climber'])
    .size()
    .reset_index(name='tick_count')
)

top10_per_route = (
    climber_counts
    .sort_values(['route_id', 'tick_count'], ascending=[True, False])
    .groupby('route_id')
    .head(25) #updated to top 25
)

# Format: Name:Count
top10_per_route['climber_string'] = top10_per_route['climber'] + ":" + top10_per_route['tick_count'].astype(str)
top10_per_route['rank'] = top10_per_route.groupby('route_id').cumcount() + 1

# Pivot to wide format: Top Climber 1 → Top Climber 10
top_climbers = top10_per_route.pivot(index='route_id', columns='rank', values='climber_string')
top_climbers.columns = [f"Top Climber {i}" for i in top_climbers.columns]
top_climbers = top_climbers.fillna("")

# --- FINAL MERGE ---
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

# --- ADD ROUTE NAME ---
# Get unique mapping of route_id → route_name from input
id_name_map = df[['route_id', 'route_name']].drop_duplicates()
summary_df = summary_df.merge(id_name_map, on='route_id', how='left')

# Reorder columns so route_name comes first
cols = ['route_name'] + [c for c in summary_df.columns if c != 'route_name']
summary_df = summary_df[cols]

# --- SAVE OUTPUT ---
summary_df.to_csv(output_csv, index=False)
print(f"✅ Summary saved to: {output_csv}")
