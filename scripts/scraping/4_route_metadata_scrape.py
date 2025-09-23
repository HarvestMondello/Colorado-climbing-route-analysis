# -*- coding: utf-8 -*-
# 4_tick_scraper_updated.py

"""
WORKFLOW NOTES

1) CONFIG
   - Input: routes_filtered.csv (from 3_filter_routes_by_classic.py)
   - Output: tick_details.csv (snake_case)
   - Fallback ChromeDriver path supported.

2) DRIVER SETUP
   - Initialize Selenium Chrome driver using Selenium Manager by default.
   - Falls back to pinned local chromedriver.exe if Selenium Manager fails.

3) LOAD ROUTE METADATA
   - Read input CSV.
   - Normalize headers to snake_case (lowercase; spaces/hyphens → underscores).
   - Extract route_id from url, keep metadata (route_name, ticks, etc.).

4) SCRAPING
   - For each route_id:
       • Open Mountain Project /stats page.
       • Click "Show More" to load all ticks.
       • Scroll the tick table to bottom until stable.
       • Copy text block and parse into rows.

5) RETRIES
   - Retry failed routes up to 3 times.
   - Save failures to failed_routes.csv.

6) OUTPUT
   - Merge parsed ticks with route metadata (route_name).
   - Parse tick_info into date, style, lead_style, notes.
   - Derive year, month, month_name.
   - Save to tick_details.csv with snake_case column names.
"""

import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from tqdm import tqdm

# =========================
# CONFIG (paths/filenames)
# =========================
area_csv   = r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed\routes_filtered.csv"
output_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed\tick_details.csv"
failed_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed\failed_routes.csv"
chrome_path = r"C:\Tools\chromedriver\chromedriver.exe"  # fallback path only

# =========================
# Helpers
# =========================
def snake_case_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert DataFrame columns to snake_case:
    - strip, lower
    - replace spaces and hyphens with underscores
    - collapse multiple underscores
    """
    def _snake(s: str) -> str:
        s = s.strip().lower()
        s = s.replace("-", "_").replace(" ", "_")
        s = re.sub(r"__+", "_", s)
        return s
    df = df.copy()
    df.columns = [_snake(c) for c in df.columns]
    return df

def init_driver():
    """
    Try Selenium Manager first (auto-matches Chrome),
    fall back to your pinned chromedriver if needed.
    """
    opts = webdriver.ChromeOptions()
    # Keep headed for reliability (same behavior as before)
    # opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    # Reduce noisy logs on Windows
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        driver = webdriver.Chrome(options=opts)  # Selenium Manager
    except Exception:
        service = Service(chrome_path)
        driver = webdriver.Chrome(service=service, options=opts)

    driver.set_page_load_timeout(35)
    return driver

# =========================
# Start
# =========================
driver = init_driver()

# --- Load route metadata (now normalized to snake_case) ---
df = pd.read_csv(area_csv)
df = snake_case_cols(df)

# Common alias shim (handles older CSV variants)
# If your CSV already has these canonical names, nothing changes.
aliases = {
    "route_name": ["route_name", "name", "route"],
    "url": ["url", "route_url", "link", "page"],
    "ticks": ["ticks", "total_ticks", "tick_count"],
    "area_hierarchy": ["area_hierarchy", "area", "area_path", "hierarchy"],
    "grade": ["grade", "yds_grade", "route_grade"]
}

def pick_col(df: pd.DataFrame, preferred: str, options: list[str]) -> str | None:
    for c in options:
        if c in df.columns:
            return c
    return None

col_url = pick_col(df, "url", aliases["url"])
if not col_url:
    raise KeyError(
        "Could not find a URL column in the input CSV. "
        "Tried: " + ", ".join(aliases["url"])
    )

# Extract route_id from url
df["route_id"] = df[col_url].astype(str).str.extract(r"/route/(\d+)/")
df = df.dropna(subset=["route_id"])
df["route_id"] = df["route_id"].astype(str)

# Build route_meta indexed by route_id (keep useful metadata if available)
maybe_cols = []
for key in ["route_name", "url", "ticks", "area_hierarchy", "grade"]:
    chosen = pick_col(df, key, aliases[key])
    if chosen:
        # standardize to canonical snake_case name
        if chosen != key:
            df = df.rename(columns={chosen: key})
        maybe_cols.append(key)

meta_cols = ["route_id"] + maybe_cols
route_meta = df[meta_cols].drop_duplicates(subset=["route_id"]).set_index("route_id")

route_ids = route_meta.index.unique()
tick_data = []
retry_log = {}

# =========================
# Parse and scrape
# =========================
def parse_text_block(lines, route_id):
    results = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Date lines like "Jan 5, 2023"
        date_match = re.match(r"\w{3} \d{1,2}, \d{4}", line)
        if date_match:
            date = date_match.group(0)
            climber = lines[i - 1] if i > 0 else "Unknown"
            tick_info = line
            i += 1
            # Accumulate until the next date header
            while i < len(lines) and not re.match(r"\w{3} \d{1,2}, \d{4}", lines[i]):
                tick_info += " " + lines[i]
                i += 1
            results.append(
                {
                    "route_id": route_id,
                    "climber": climber.strip(),
                    "tick_info": tick_info.strip(),
                }
            )
        else:
            i += 1
    return results

def get_route_name(route_id: str) -> str:
    if "route_name" in route_meta.columns and route_id in route_meta.index:
        try:
            rn = route_meta.loc[route_id, "route_name"]
            return rn if isinstance(rn, str) else str(rn)
        except Exception:
            return "Unknown"
    return "Unknown"

def get_expected_ticks(route_id: str):
    if "ticks" in route_meta.columns and route_id in route_meta.index:
        try:
            return int(route_meta.loc[route_id, "ticks"])
        except Exception:
            return None
    return None

def scrape_route(route_id, retry_num=0):
    route_name = get_route_name(route_id)
    print(f"\n➡️ Scraping route: {route_name} (ID {route_id}, Attempt {retry_num + 1})")
    url = f"https://www.mountainproject.com/route/stats/{route_id}"
    expected = get_expected_ticks(route_id)

    try:
        driver.get(url)
        time.sleep(3)  # fixed delay

        # Click "Show More" until stable
        for _ in range(100):
            buttons = driver.find_elements(By.TAG_NAME, "button")
            show_more = next((b for b in buttons if "Show More" in b.text), None)
            if not show_more:
                break
            prev_count = len(driver.find_elements(By.CSS_SELECTOR, "div.MuiBox-root"))
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(2.0)

            # stability polling
            stable_count = 0
            for _ in range(40):
                curr_count = len(driver.find_elements(By.CSS_SELECTOR, "div.MuiBox-root"))
                if curr_count == prev_count:
                    stable_count += 1
                else:
                    stable_count = 0
                    prev_count = curr_count
                if stable_count >= 5:
                    break
                time.sleep(0.25)

        # Scroll inside the container until no more growth
        scroll_js = "return document.querySelector('div.onx-stats-table').scrollHeight"
        last_height = driver.execute_script(scroll_js)
        while True:
            driver.execute_script("""
                let el = document.querySelector('div.onx-stats-table');
                if (el) { el.scrollTop = el.scrollHeight; }
            """)
            time.sleep(2)
            new_height = driver.execute_script(scroll_js)
            if new_height == last_height:
                break
            last_height = new_height

        # Copy the visible tick block text
        js = """
        const container = document.querySelector('div.onx-stats-table');
        if (!container) return '';
        const sel = window.getSelection();
        sel.removeAllRanges();
        const range = document.createRange();
        range.selectNode(container);
        sel.addRange(range);
        return sel.toString();
        """
        full_text = driver.execute_script(js)
        if not full_text.strip():
            print(f"⚠️ No text extracted for {route_name} (ID {route_id})")
            return False, 0, expected

        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        parsed = parse_text_block(lines, route_id)
        tick_data.extend(parsed)
        actual = len(parsed)

        # (Optional) sanity check vs expected
        if expected is not None and abs(actual - expected) > 500:
            print(f"⚠️ Route {route_name} (ID {route_id}): {actual} ticks < {expected} expected")
            return False, actual, expected
        else:
            print(f"✅ {route_name} (ID {route_id}): {actual} ticks")
            return True, actual, expected

    except Exception as e:
        print(f"❌ Error scraping {route_name} (ID {route_id}): {e}")
        return False, 0, expected

# --- Main scraping loop ---
pbar = tqdm(route_ids, desc="Scraping routes", unit="route")
for route_id in pbar:
    # live label with current route name
    try:
        rn = get_route_name(route_id)
        pbar.set_description(f"Scraping: {str(rn)[:48]}")
    except Exception:
        pass

    success, got, expected = scrape_route(route_id)
    if not success:
        retry_log[route_id] = 1

# --- Retry up to 3 attempts ---
for attempt in range(2, 4):
    to_retry = [r for r, tries in retry_log.items() if tries == attempt - 1]
    if not to_retry:
        break
    print(f"\n🔁 Retry Attempt {attempt}: {len(to_retry)} routes")
    for route_id in to_retry:
        success, got, expected = scrape_route(route_id, retry_num=attempt - 1)
        if not success:
            retry_log[route_id] = attempt

# --- Save final failures ---
final_failed = [r for r, tries in retry_log.items() if tries >= 3]
if final_failed:
    pd.DataFrame(final_failed, columns=["route_id"]).to_csv(failed_csv, index=False)
    print(f"\n❌ Failed routes saved: {failed_csv}")
else:
    print("\n✅ All routes completed successfully within 3 attempts.")

# =========================
# Build final output
# =========================
driver.quit()
df_out = pd.DataFrame(tick_data)

if df_out.empty or "tick_info" not in df_out.columns:
    print("❌ No valid tick_info data to parse. Exiting.")
    raise SystemExit

# Merge route_name (and optionally url/area/grade) from route_meta
cols_to_pull = [c for c in ["route_name", "url", "area_hierarchy", "grade", "ticks"] if c in route_meta.columns]
if cols_to_pull:
    df_out = df_out.merge(
        route_meta[cols_to_pull],
        left_on="route_id",
        right_index=True,
        how="left"
    )
else:
    df_out["route_name"] = None

# Reorder (readable, snake_case)
front_cols = ["route_id", "route_name", "climber", "tick_info"]
other_cols = [c for c in df_out.columns if c not in front_cols]
df_out = df_out[front_cols + other_cols]

# Parse tick_info → date, style, lead_style, notes
def parse_tick_info(tick: str) -> pd.Series:
    date = style = lead = notes = ""
    try:
        tick = tick.replace("•", "·")
        parts = tick.split("·")
        date = parts[0].strip()
        rest = parts[1].strip() if len(parts) > 1 else ""
        if "." in rest:
            lead_part, notes = rest.split(".", 1)
            notes = notes.strip()
        else:
            lead_part = rest
        if "/" in lead_part:
            style, lead = [x.strip() for x in lead_part.split("/", 1)]
        else:
            style = lead_part.strip()
            lead = ""
    except Exception:
        pass
    return pd.Series([date, style, lead, notes])

df_out[["date", "style", "lead_style", "notes"]] = df_out["tick_info"].apply(parse_tick_info)

# Dates & parts
dt = pd.to_datetime(df_out["date"], format="%b %d, %Y", errors="coerce")
df_out["year"] = dt.dt.year
df_out["month"] = dt.dt.month
df_out["month_name"] = dt.dt.month_name()

# Drop the raw combined string
df_out.drop(columns=["tick_info"], inplace=True)

# Final tidy column order (all snake_case)
final_order = [
    "route_id", "route_name", "date", "year", "month", "month_name",
    "style", "lead_style", "climber", "notes",
]
final_order += [c for c in df_out.columns if c not in final_order]
df_out = df_out[final_order]

# Save
df_out.to_csv(output_csv, index=False)
print(f"\n✅ Final tick output: {output_csv}")
print(f"📊 Total ticks collected: {len(df_out)}")
print(f"❗ Failed routes: {len(final_failed)}")
