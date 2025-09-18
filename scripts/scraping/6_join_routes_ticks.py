# 7-clean-route-tick-data.py
# Cleans route-tick summary data:
# - Normalizes/renames common column variants
# - Removes duplicate columns (keeps first; e.g., duplicate route_name)
# - Removes duplicate routes by ID
# - Drops irrelevant columns if present
# - Removes tick-year columns outside 1950..current_year
# - Drops rows with missing/blank Grade
# - Filters to "classic" routes (Votes >= 50, Stars >= 3.0, total_ticks >= 100)
# - Reorders key columns: Votes -> total_ticks -> unique_climbers


#full JOIN on route_id
import pandas as pd
from datetime import datetime

# --- Load both CSVs --- 
# load: routes-filtered.csv from 3-filter-routes-by-classic.py
# load: tick_csv from 5-tick-aggregations-by-route.py
route_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\routes-filtered.csv"
tick_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\tick-summary-by-route.csv"
output_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\joined-route-tick-summary.csv"

# Load files
df_routes = pd.read_csv(route_csv)
df_ticks = pd.read_csv(tick_csv)

# Extract route_id from URL in df_routes if needed
if 'route_id' not in df_routes.columns:
    df_routes['route_id'] = df_routes['URL'].str.extract(r'/route/(\d+)')

# Ensure route_id is string in both for consistency
df_routes['route_id'] = df_routes['route_id'].astype(str)
df_ticks['route_id'] = df_ticks['route_id'].astype(str)

# --- Full outer join on route_id ---
df_joined = pd.merge(df_routes, df_ticks, on='route_id', how='outer')

# --- Save result ---
df_joined.to_csv(output_csv, index=False)
print(f"✅ Full join complete. Output saved to: {output_csv}")



# --- CONFIGURATION ---
input_csv  = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\joined-route-tick-summary.csv"
output_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\joined-route-tick-cleaned.csv"





def deduplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop duplicated columns by name, keeping the first occurrence.
    Preserves column order of the first appearance.
    """
    return df.loc[:, ~df.columns.duplicated()]

# --- LOAD DATA ---
df = pd.read_csv(input_csv)

# --- STEP 0: NORMALIZE/RENAME COMMON VARIANTS ---
# 0a) Trim whitespace from headers
df.columns = [c.strip() for c in df.columns]

# 0b) Drop duplicate columns (including duplicate 'route_name'), keep first
df = deduplicate_columns(df)

# 0c) Map common variants to canonical names
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

# 0d) After renaming, deduplicate again in case renames created collisions
df = deduplicate_columns(df)

# --- Identify the best candidate for route ID ---
id_candidates = [c for c in ["route_id", "Route ID", "RouteID", "ID"] if c in df.columns]
route_id_col = id_candidates[0] if id_candidates else None

# --- STEP 1: DROP DUPLICATE ROUTE ENTRIES ---
if route_id_col:
    df_cleaned = df.drop_duplicates(subset=route_id_col, keep="first").copy()
else:
    print("⚠️ No route ID column found; skipping de-duplication.")
    df_cleaned = df.copy()

# --- STEP 2: DROP UNNEEDED COLUMNS (only if they exist) ---
# Also drop unique_climbers_x if present
cols_to_drop = [c for c in ["Length (ft)", "Ticks", "route_id", "unique_climbers_x"] if c in df_cleaned.columns]
if cols_to_drop:
    df_cleaned = df_cleaned.drop(columns=cols_to_drop)

# --- STEP 3: DROP TICK YEAR COLUMNS OUTSIDE VALID RANGE ---
current_year = datetime.now().year
year_cols = [col for col in df_cleaned.columns if str(col).isdigit() and len(str(col)) == 4]
invalid_year_cols = [col for col in year_cols if int(col) > current_year or int(col) < 1950]
if invalid_year_cols:
    df_cleaned = df_cleaned.drop(columns=invalid_year_cols)

# --- STEP 4: DROP ROUTES WITH MISSING/BLANK GRADE ---
if "Grade" in df_cleaned.columns:
    df_cleaned = df_cleaned[df_cleaned["Grade"].notna() & (df_cleaned["Grade"].astype(str).str.strip() != "")]
else:
    print("⚠️ No 'Grade' column found; skipping grade-based filtering.")

# --- Ensure numeric types for filtering ---
for col in ["Votes", "Stars", "total_ticks"]:
    if col in df_cleaned.columns:
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")

# --- STEP 5: APPLY "CLASSIC" FILTERS (only if columns exist) ---
filters = []
if "Votes" in df_cleaned.columns:
    filters.append(df_cleaned["Votes"] >= 50)
else:
    print("⚠️ 'Votes' not found; omitting Votes filter.")
    filters.append(pd.Series([True]*len(df_cleaned), index=df_cleaned.index))

if "Stars" in df_cleaned.columns:
    filters.append(df_cleaned["Stars"] >= 3.0)
else:
    print("⚠️ 'Stars' not found; omitting Stars filter.")
    filters.append(pd.Series([True]*len(df_cleaned), index=df_cleaned.index))

if "total_ticks" in df_cleaned.columns:
    filters.append(df_cleaned["total_ticks"] >= 100)
else:
    print("⚠️ 'total_ticks' not found; omitting total_ticks filter.")
    filters.append(pd.Series([True]*len(df_cleaned), index=df_cleaned.index))

mask = filters[0]
for f in filters[1:]:
    mask &= f

df_filtered = df_cleaned.loc[mask].copy()

# --- STEP 6: HANDLE UNIQUE_CLIMBERS COLUMNS ---
# Rename unique_climbers_y -> unique_climbers if present
if "unique_climbers_y" in df_filtered.columns:
    df_filtered = df_filtered.rename(columns={"unique_climbers_y": "unique_climbers"})

# --- STEP 7: REORDER KEY COLUMNS ---
# Ensure 'Votes' -> 'total_ticks' -> 'unique_climbers' appear consecutively (when present)
if "Votes" in df_filtered.columns:
    # Build a fresh order that removes these three if present, then re-inserts in desired order
    cols = [c for c in df_filtered.columns if c not in ("total_ticks", "unique_climbers")]
    if "Votes" in cols:
        v_idx = cols.index("Votes")
        # Insert after Votes in correct sequence if columns exist
        insert_after = v_idx + 1
        if "total_ticks" in df_filtered.columns:
            cols.insert(insert_after, "total_ticks")
            insert_after += 1
        if "unique_climbers" in df_filtered.columns:
            cols.insert(insert_after, "unique_climbers")
        df_filtered = df_filtered[cols]

# --- DEBUG: show resulting columns ---
print("🧱 Columns after cleaning:", list(df_filtered.columns))

# --- SAVE CLEANED DATA ---
df_filtered.to_csv(output_csv, index=False)

# --- CONFIRMATION MESSAGE ---
print(f"✅ Filtered + cleaned data saved to: {output_csv}")
print(f"🗓️ Dropped year columns outside 1950–{current_year}: {invalid_year_cols}")
print(f"📉 Routes remaining after filters: {len(df_filtered)}")
