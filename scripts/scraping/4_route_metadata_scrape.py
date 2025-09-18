# 4-tick-scraper-updated.py
# -*- coding: utf-8 -*-
# ORIGINAL WORKFLOW, CHROME-ONLY PATCH
# - The ONLY change from your prior working script is init_driver():
#   it uses Selenium Manager by default (avoids driver/version crashes),
#   and falls back to your pinned chromedriver path if needed.
# - Additionally (NEW): show route name during scraping and include it in the CSV.

import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from tqdm import tqdm

# --- CONFIG (same as your original; adjust paths if needed) ---
# from 3-filter-routes.py we get: routes_filtered.csv to analyze all remaining routes in the dataset
# this will be top 10 or top 100 routes by classic rating
area_csv   = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\routes-filtered.csv"
output_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\tick-details.csv"
failed_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\failed-routes.csv"
chrome_path = r"C:\Tools\chromedriver\chromedriver.exe"  # fallback path only

# --- Chrome/WebDriver SETUP ---
def init_driver():
    """
    Try Selenium Manager first (auto-matches Chrome),
    fall back to your pinned chromedriver if needed.
    """
    opts = webdriver.ChromeOptions()
    # Keep headed for reliability (same behavior as before)
    # opts.add_argument("--headless=new")
    opts.add_argument("--start-maximized")
    # Cut down noisy Chrome logs on Windows
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        # Selenium Manager pathless init (Selenium 4.6+)
        driver = webdriver.Chrome(options=opts)
    except Exception:
        # Fallback to your local chromedriver if Manager fails
        service = Service(chrome_path)
        driver = webdriver.Chrome(service=service, options=opts)

    driver.set_page_load_timeout(35)
    return driver

driver = init_driver()

# --- Load route metadata (unchanged, plus route_name available) ---
df = pd.read_csv(area_csv)
df['route_id'] = df['URL'].str.extract(r'/route/(\d+)/')
df = df.dropna(subset=['route_id'])
df['route_id'] = df['route_id'].astype(str)

# Keep the original metadata indexed by route_id. Expect columns like 'Route Name', 'Ticks', 'URL', etc.
route_meta = df.set_index('route_id')
route_ids = route_meta.index.unique()

tick_data = []
retry_log = {}

# --- Parse tick block (unchanged) ---
def parse_text_block(lines, route_id):
    results = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # EXACT regex from your working version
        date_match = re.match(r"\w{3} \d{1,2}, \d{4}", line)
        if date_match:
            date = date_match.group(0)
            climber = lines[i - 1] if i > 0 else "Unknown"
            tick_info = line
            i += 1
            while i < len(lines) and not re.match(r"\w{3} \d{1,2}, \d{4}", lines[i]):
                tick_info += " " + lines[i]
                i += 1
            results.append({
                "route_id": route_id,
                "climber": climber.strip(),
                "tick_info": tick_info.strip()
            })
        else:
            i += 1
    return results

# --- Scrape one route (same logic; show route name) ---
def scrape_route(route_id, retry_num=0):
    # NEW: pull route name from metadata for nicer logs
    route_name = "Unknown"
    if 'Route Name' in route_meta.columns and route_id in route_meta.index:
        try:
            # .loc returns a Series for unique index; handle both Series/scalar
            rn = route_meta.loc[route_id, 'Route Name']
            route_name = rn if isinstance(rn, str) else str(rn)
        except Exception:
            pass

    print(f"\n➡️ Scraping route: {route_name} (ID {route_id}, Attempt {retry_num + 1})")
    url = f"https://www.mountainproject.com/route/stats/{route_id}"
    expected = route_meta.loc[route_id, 'Ticks'] if route_id in route_meta.index else None

    try:
        driver.get(url)
        time.sleep(3)  # exact fixed delay as before

        # 🔁 Click "Show More" as many times as needed (exact logic)
        for _ in range(100):
            buttons = driver.find_elements(By.TAG_NAME, "button")
            show_more = next((b for b in buttons if "Show More" in b.text), None)
            if not show_more:
                break
            prev_count = len(driver.find_elements(By.CSS_SELECTOR, "div.MuiBox-root"))
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(2.0)  # exact delay as before

            # stability polling (exact)
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

        # 🌀 Scroll inside container (exact)
        scroll_js = "return document.querySelector('div.onx-stats-table').scrollHeight"
        last_height = driver.execute_script(scroll_js)
        while True:
            driver.execute_script("""
                let el = document.querySelector('div.onx-stats-table');
                el.scrollTop = el.scrollHeight;
            """)
            time.sleep(2)  # exact
            new_height = driver.execute_script(scroll_js)
            if new_height == last_height:
                break
            last_height = new_height

        # 📋 Copy visible tick block (exact)
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

        if expected and abs(actual - expected) > 500:
            print(f"⚠️ Route {route_name} (ID {route_id}): {actual} ticks < {expected} expected")
            return False, actual, expected
        else:
            print(f"✅ {route_name} (ID {route_id}): {actual} ticks")
            return True, actual, expected

    except Exception as e:
        print(f"❌ Error scraping {route_name} (ID {route_id}): {e}")
        return False, 0, None

# --- Main scraping loop (unchanged) ---
pbar = tqdm(route_ids, desc="Scraping routes", unit="route")
for route_id in pbar:
    # (Optional) live label tweak: show current route name on the bar
    try:
        rn = route_meta.loc[route_id, 'Route Name'] if 'Route Name' in route_meta.columns else "Unknown"
        pbar.set_description(f"Scraping: {str(rn)[:48]}")
    except Exception:
        pass

    success, got, expected = scrape_route(route_id)
    if not success:
        retry_log[route_id] = 1

# --- Retry up to 3 attempts (unchanged) ---
for attempt in range(2, 4):
    to_retry = [r for r, tries in retry_log.items() if tries == attempt - 1]
    if not to_retry:
        break
    print(f"\n🔁 Retry Attempt {attempt}: {len(to_retry)} routes")
    for route_id in to_retry:
        success, got, expected = scrape_route(route_id, retry_num=attempt - 1)
        if not success:
            retry_log[route_id] = attempt

# --- Save final failures (unchanged) ---
final_failed = [r for r, tries in retry_log.items() if tries >= 3]
if final_failed:
    pd.DataFrame(final_failed, columns=["route_id"]).to_csv(failed_csv, index=False)
    print(f"\n❌ Failed routes saved: {failed_csv}")
else:
    print("\n✅ All routes completed successfully within 3 attempts.")

# --- Final tick dataframe (unchanged base, plus route_name merge) ---
driver.quit()
df_out = pd.DataFrame(tick_data)

if df_out.empty or 'tick_info' not in df_out.columns:
    print("❌ No valid tick_info data to parse. Exiting.")
    raise SystemExit

# NEW: Add route name (and keep this flexible to add URL/Area later if desired)
cols_to_pull = ['Route Name']  # add 'URL', 'Area Hierarchy', 'Grade', etc. if you want
available_cols = [c for c in cols_to_pull if c in route_meta.columns]
if available_cols:
    df_out = df_out.merge(
        route_meta[available_cols],
        left_on='route_id',
        right_index=True,
        how='left'
    )
    df_out = df_out.rename(columns={'Route Name': 'route_name'})
else:
    df_out['route_name'] = None  # fallback if column missing

# (optional) move name up front for readability
front_cols = ['route_id', 'route_name', 'climber', 'tick_info']
other_cols = [c for c in df_out.columns if c not in front_cols]
df_out = df_out[front_cols + other_cols]

# --- Parse tick_info block (unchanged) ---
def parse_tick_info(tick):
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

df_out[['date', 'style', 'lead_style', 'notes']] = df_out['tick_info'].apply(parse_tick_info)
dt = pd.to_datetime(df_out['date'], format="%b %d, %Y", errors='coerce')
df_out['year'] = dt.dt.year
df_out['month'] = dt.dt.month
df_out['month_name'] = dt.dt.month_name()
df_out.drop(columns=['tick_info'], inplace=True)

# (optional) final tidy column order
final_order = ['route_id','route_name','date','year','month','month_name','style','lead_style','climber','notes']
final_order += [c for c in df_out.columns if c not in final_order]
df_out = df_out[final_order]

# 💾 Save final CSV
df_out.to_csv(output_csv, index=False)
print(f"\n✅ Final tick output: {output_csv}")
print(f"📊 Total ticks collected: {len(df_out)}")
print(f"❗ Failed routes: {len(final_failed)}")
