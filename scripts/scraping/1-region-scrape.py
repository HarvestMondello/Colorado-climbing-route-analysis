# 1-route-scraper-multi-minimal.py
import time
import os
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

# --- Configuration ---
URLS = [
    "https://www.mountainproject.com/area/126410925/aspen",
    "https://www.mountainproject.com/area/106247375/fairplay",
    # add more region URLs here...
]

# Optional: set CHROME_BINARY env var if your Chrome isn’t in the default location
# os.environ["CHROME_BINARY"] = r"C:\Path\To\chrome.exe"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")                  # 1. disable GPU
options.add_argument("--disable-webgpu")         # stops WebGPU init (D3D12)
options.add_argument("--disable-3d-apis")        # belts & suspenders
options.add_argument("--use-angle=swiftshader")  # software ANGLE path
options.add_argument("--use-gl=swiftshader")     # software GL path
options.add_argument("--disable-software-rasterizer")  # 1. disable software rasterizer
options.add_argument("--log-level=3")                  # 2. suppress logging
options.add_argument("--silent")                       # 2. extra suppression
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.page_load_strategy = "eager"

# If user provided a non-standard Chrome binary, wire it in:
if "CHROME_BINARY" in os.environ and os.environ["CHROME_BINARY"]:
    options.binary_location = os.environ["CHROME_BINARY"]

# --- Robust driver init: Selenium Manager -> webdriver_manager fallback ---
def build_driver():
    try:
        return webdriver.Chrome(options=options)
    except Exception as e1:
        print(f"[info] Selenium Manager init failed, falling back to webdriver_manager… ({e1})", flush=True)
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception as e2:
            raise RuntimeError(
                f"Could not start Chrome WebDriver. "
                f"Selenium Manager error: {e1}\nwebdriver_manager error: {e2}"
            )

driver = build_driver()

# --- Preflight check ---
try:
    browser_version = driver.capabilities.get("browserVersion") or driver.capabilities.get("version")
    driver_version = driver.capabilities.get("chrome", {}).get("chromedriverVersion", "").split(" ")[0]
    print(f"🟢 Chrome browser version: {browser_version}", flush=True)
    print(f"🟢 ChromeDriver version:   {driver_version}", flush=True)
except Exception as e:
    print(f"⚠️ Could not detect versions: {e}", flush=True)

# --- Helpers (unchanged) ---
def get_soup(page_url, retries=1):
    for _ in range(retries + 1):
        try:
            driver.get(page_url)
            time.sleep(1.5)
            return BeautifulSoup(driver.page_source, "html.parser")
        except TimeoutException:
            print(f"⏳ Timeout: {page_url}", flush=True)
            time.sleep(2)
    return None

def get_route_links_from(page_url):
    driver.get(page_url)
    time.sleep(1)
    return [
        el.get_attribute("href")
        for el in driver.find_elements(By.CSS_SELECTOR, "a[href*='/route/']")
    ]

def collect_all_routes_recursive(area_url, visited=None):
    if visited is None:
        visited = set()

    if area_url in visited:
        return []

    visited.add(area_url)
    print(f"📂 Visiting: {area_url}", flush=True)
    driver.get(area_url)
    time.sleep(1)

    route_links = get_route_links_from(area_url)

    # Note: same selector as your working version
    subarea_elements = driver.find_elements(By.CSS_SELECTOR, ".lef-nav-row a")
    subarea_links = [el.get_attribute("href") for el in subarea_elements]

    for sub_link in subarea_links:
        if sub_link and sub_link not in visited:
            route_links += collect_all_routes_recursive(sub_link, visited)

    return route_links

# --- Output folder (unchanged) ---
output_dir = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\regions"
os.makedirs(output_dir, exist_ok=True)

# ===========================
# MULTI-REGION WRAPPER START
# ===========================
for url in URLS:
    # --- Step 1: Traverse and Collect Routes ---
    print(f"\n➡️ Starting recursive scrape from: {url}", flush=True)
    route_urls = list(set(collect_all_routes_recursive(url)))
    print(f"✅ Total routes found: {len(route_urls)}", flush=True)

    # --- Step 2: Scrape Route Metadata ---
    all_routes = []

    for i, route_url in enumerate(route_urls, 1):
        print(f"➡️ Scraping route {i}/{len(route_urls)}: {route_url}", flush=True)
        soup = get_soup(route_url)
        if not soup:
            print(f"⚠️ Failed to get soup for {route_url}", flush=True)
            continue

        route_id_m = re.search(r"/route/(\d+)", route_url)
        route_id = route_id_m.group(1) if route_id_m else ""

        h1 = soup.find("h1")
        route_name = h1.text.strip() if h1 else ""

        grade_elem = soup.select_one("h2 span.rateYDS")
        grade = grade_elem.text.strip() if grade_elem else ""

        try:
            det_table = soup.find("table", class_="description-details")
            td = det_table.find("td", string="Type:").find_next_sibling("td") if det_table else None
            type_text = td.get_text(" ", strip=True) if td else ""
            print(f"🔎 Type Text: {type_text} — {route_url}", flush=True)

            pitch_match = re.search(r"(\d+)\s*pitches?", type_text, re.IGNORECASE)
            pitch = int(pitch_match.group(1)) if pitch_match else 1

            length_match = re.search(r"(\d+)\s*ft", type_text)
            length_ft = int(length_match.group(1)) if length_match else None

            route_type = type_text.split(",")[0].split("(")[0].strip() if type_text else ""
        except Exception as e:
            print(f"⚠️ Type block error at {route_url}: {e}", flush=True)
            pitch = 1
            length_ft = None
            route_type = ""

        area_hierarchy = " > ".join(a.text for a in soup.select("div.text-warm a"))

        stars, votes = (None, None)
        stars_elem = soup.select_one("span[id^=starsWithAvgText]")
        if stars_elem:
            st = stars_elem.get_text(strip=True)
            m = re.search(r"Avg:\s*([\d.]+)\s*from\s*([\d,]+)", st)
            if m:
                stars = float(m.group(1))
                votes = int(m.group(2).replace(",", ""))

        fa_info = ""
        fa_td = soup.find("td", string="FA:")
        if fa_td:
            nxt = fa_td.find_next_sibling("td")
            fa_info = nxt.get_text(" ", strip=True) if nxt else ""

        ticks = None
        if route_id:
            stats_url = route_url.replace("/route/", "/route/stats/")
            stats_soup = get_soup(stats_url)
            if stats_soup:
                for h3 in stats_soup.find_all("h3"):
                    if h3.get_text(strip=True).startswith("Ticks"):
                        span = h3.select_one("span.small.text-muted")
                        if span:
                            try:
                                ticks = int(span.text.strip().replace(",", ""))
                            except ValueError:
                                ticks = None
                        break

        all_routes.append({
            "Route ID": route_id,
            "Route Name": route_name,
            "Grade": grade,
            "Type": route_type,
            "Pitches": pitch,
            "Length (ft)": length_ft,
            "Stars": stars,
            "Votes": votes,
            "Ticks": ticks,
            "FA Info": fa_info,
            "Area Hierarchy": area_hierarchy,
            "URL": route_url
        })

    # --- Step 3: Save CSV for THIS region ---
    print(f"✅ Total routes scraped: {len(all_routes)}", flush=True)

    area_slug = url.rstrip("/").split("/")[-1]
    file_path = os.path.join(output_dir, f"{area_slug}.csv")

    if all_routes:
        df = pd.DataFrame(all_routes)
        if "Pitches" in df.columns:
            df["Pitches"] = df["Pitches"].fillna(1).astype(int)
        df.to_csv(file_path, index=False)
        print(f"✅ Saved: {file_path}")
    else:
        print("⚠️ No data scraped. Check network or structure.")

# --- Cleanup ---
driver.quit()
