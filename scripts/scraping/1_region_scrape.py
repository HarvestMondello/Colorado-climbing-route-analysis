"""
Script: 1_region_scrape.py rename to 1_route_scraper_multi_region.py
Purpose:
    Scrape climbing route metadata from Mountain Project for multiple Colorado regions.

Workflow:
    1. Traverse region URLs recursively to collect all route links.
    2. Scrape metadata for each route (name, grade, type, pitches, length, stars, votes, FA, ticks).
    3. Save one CSV file per region into the output directory.

Input:
    - List of region URLs defined in URLS[].

Output:
    - CSV per region with filename cleaned (underscores, lowercase).

Dependencies:
    - Selenium, BeautifulSoup4, Pandas, webdriver_manager (optional fallback).
"""

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

# ===========================
# CONFIGURATION
# ===========================
URLS = [
    # top 15 classic climbing areas in Colorado
    #'https://www.mountainproject.com/area/105744466/alpine-rock',
    #'https://www.mountainproject.com/area/105744397/black-canyon-of-the-gunnison',
    'https://www.mountainproject.com/area/105744222/boulder-canyon',
    #'https://www.mountainproject.com/area/105744448/colorado-national-monument',
    'https://www.mountainproject.com/area/105744246/eldorado-canyon-state-park',
    #'https://www.mountainproject.com/area/105744255/eldorado-mountain',
    #'https://www.mountainproject.com/area/105788880/escalante-canyon',
    'https://www.mountainproject.com/area/105797700/flatirons',
    #'https://www.mountainproject.com/area/105744301/garden-of-the-gods',
    #'https://www.mountainproject.com/area/105744228/lumpy-ridge',
    #'https://www.mountainproject.com/area/105744249/north-table-mountaingolden-cliffs',
    #'https://www.mountainproject.com/area/105744385/old-stage-road',
    #'https://www.mountainproject.com/area/105797719/south-platte',
    #'https://www.mountainproject.com/area/105744400/unaweep-canyon',
    #'https://www.mountainproject.com/area/105744234/upper-dream-canyon',
]

# ===========================
# SELENIUM OPTIONS
# ===========================
options = Options()
options.add_argument("--headless=new")
options.add_argument("--disable-gpu")
options.add_argument("--disable-webgpu")
options.add_argument("--disable-3d-apis")
options.add_argument("--use-angle=swiftshader")
options.add_argument("--use-gl=swiftshader")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--log-level=3")
options.add_argument("--silent")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.page_load_strategy = "eager"

# ===========================
# DRIVER BUILDER
# ===========================
def build_driver():
    """
    Initialize a Chrome WebDriver with headless options.
    Tries Selenium Manager first, falls back to webdriver_manager.

    Returns:
        webdriver.Chrome: Configured Chrome WebDriver instance.
    """
    try:
        return webdriver.Chrome(options=options)
    except Exception as e1:
        print(f"[info] Selenium Manager init failed, fallback… ({e1})", flush=True)
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

# ===========================
# HELPER FUNCTIONS
# ===========================
def get_soup(page_url, retries=1):
    """
    Load a page into BeautifulSoup with retries on timeout.

    Args:
        page_url (str): Target webpage URL.
        retries (int): Number of retry attempts.

    Returns:
        BeautifulSoup | None: Parsed HTML soup object, or None on failure.
    """
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
    """
    Extract all route links from a given area page.

    Args:
        page_url (str): Area page URL.

    Returns:
        list[str]: List of route URLs found on the page.
    """
    driver.get(page_url)
    time.sleep(1)
    return [
        el.get_attribute("href")
        for el in driver.find_elements(By.CSS_SELECTOR, "a[href*='/route/']")
    ]

def collect_all_routes_recursive(area_url, visited=None):
    """
    Recursively collect all route links by visiting sub-areas.

    Args:
        area_url (str): The starting area URL.
        visited (set[str]): Tracks already visited areas.

    Returns:
        list[str]: All unique route URLs found under this area and subareas.
    """
    if visited is None:
        visited = set()

    if area_url in visited:
        return []

    visited.add(area_url)
    print(f"📂 Visiting: {area_url}", flush=True)
    driver.get(area_url)
    time.sleep(1)

    # Collect routes
    route_links = get_route_links_from(area_url)

    # Collect subareas
    subarea_elements = driver.find_elements(By.CSS_SELECTOR, ".lef-nav-row a")
    subarea_links = [el.get_attribute("href") for el in subarea_elements]

    # Recurse into subareas
    for sub_link in subarea_links:
        if sub_link and sub_link not in visited:
            route_links += collect_all_routes_recursive(sub_link, visited)

    return route_links

# ===========================
# OUTPUT DIRECTORY
# ===========================
output_dir = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\regions"
os.makedirs(output_dir, exist_ok=True)

# ===========================
# MAIN SCRAPER LOOP
# ===========================
for url in URLS:
    # Step 1: Traverse region and collect route URLs
    print(f"\n➡️ Starting recursive scrape from: {url}", flush=True)
    route_urls = list(set(collect_all_routes_recursive(url)))
    print(f"✅ Total routes found: {len(route_urls)}", flush=True)

    # Step 2: Scrape metadata for each route
    all_routes = []

    for i, route_url in enumerate(route_urls, 1):
        print(f"➡️ Scraping route {i}/{len(route_urls)}: {route_url}", flush=True)
        soup = get_soup(route_url)
        if not soup:
            print(f"⚠️ Failed to get soup for {route_url}", flush=True)
            continue

        # Extract metadata
        route_id_m = re.search(r"/route/(\d+)", route_url)
        route_id = route_id_m.group(1) if route_id_m else ""

        h1 = soup.find("h1")
        route_name = h1.text.strip() if h1 else ""

        grade_elem = soup.select_one("h2 span.rateYDS")
        grade = grade_elem.text.strip() if grade_elem else ""

        # Type, pitches, length
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

        # Area hierarchy
        area_hierarchy = " > ".join(a.text for a in soup.select("div.text-warm a"))

        # Stars + votes
        stars, votes = (None, None)
        stars_elem = soup.select_one("span[id^=starsWithAvgText]")
        if stars_elem:
            st = stars_elem.get_text(strip=True)
            m = re.search(r"Avg:\s*([\d.]+)\s*from\s*([\d,]+)", st)
            if m:
                stars = float(m.group(1))
                votes = int(m.group(2).replace(",", ""))

        # First ascent info
        fa_info = ""
        fa_td = soup.find("td", string="FA:")
        if fa_td:
            nxt = fa_td.find_next_sibling("td")
            fa_info = nxt.get_text(" ", strip=True) if nxt else ""

        # Tick count from stats page
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

        # Append data
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

    # Step 3: Save CSV per region
    print(f"✅ Total routes scraped: {len(all_routes)}", flush=True)

    area_slug = url.rstrip("/").split("/")[-1].replace("-", "_").lower()
    file_path = os.path.join(output_dir, f"{area_slug}.csv")

    if all_routes:
        df = pd.DataFrame(all_routes)
        if "Pitches" in df.columns:
            df["Pitches"] = df["Pitches"].fillna(1).astype(int)
        df.to_csv(file_path, index=False)
        print(f"✅ Saved: {file_path}")
    else:
        print("⚠️ No data scraped. Check network or structure.")

# ===========================
# CLEANUP
# ===========================
driver.quit()
