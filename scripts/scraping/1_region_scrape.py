"""
Script: 1_route_scraper_multi_region.py
Purpose:
    Scrape climbing route metadata from Mountain Project for multiple Colorado regions.

Workflow:
    1. Traverse region URLs recursively to collect all route links.
    2. Scrape metadata for each route (name, grade, type, pitches, length, stars, votes, FA, ticks).
    3. Save one CSV file per region into the output directory + a debug CSV of routes missing Ticks.

Input:
    - List of region URLs defined in URLS[].

Output:
    - CSV per region with filename cleaned (underscores, lowercase).
    - Debug CSV per region listing any routes with missing Ticks.

Dependencies:
    - Selenium, BeautifulSoup4, Pandas, webdriver_manager (optional fallback).
"""
#output line 21

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
    #'https://www.mountainproject.com/area/105744222/boulder-canyon',
    #'https://www.mountainproject.com/area/105744448/colorado-national-monument',
    #'https://www.mountainproject.com/area/105744246/eldorado-canyon-state-park',
    #'https://www.mountainproject.com/area/105744255/eldorado-mountain',
    #'https://www.mountainproject.com/area/105788880/escalante-canyon',
    #'https://www.mountainproject.com/area/105797700/flatirons',
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
        webdriver.Chrome
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
def gentle_scroll(driver, steps=3, pause=0.25):
    """Small incremental scroll to coax lazy content to render on /stats/."""
    try:
        for i in range(steps):
            driver.execute_script(
                f"window.scrollTo(0, (document.body.scrollHeight/{steps})*{i+1});"
            )
            time.sleep(pause)
    except Exception:
        pass

def get_soup(page_url, retries=1):
    """Load a page into BeautifulSoup with retries on timeout."""
    for _ in range(retries + 1):
        try:
            driver.get(page_url)
            time.sleep(1.5)
            return BeautifulSoup(driver.page_source, "html.parser")
        except TimeoutException:
            print(f"⏳ Timeout: {page_url}", flush=True)
            time.sleep(2)
    return None

def get_stats_soup(page_url, retries=1):
    """Load /route/stats/ with a gentle scroll so lazy sections hydrate."""
    for _ in range(retries + 1):
        try:
            driver.get(page_url)
            time.sleep(1.2)
            gentle_scroll(driver)
            time.sleep(0.3)
            return BeautifulSoup(driver.page_source, "html.parser")
        except TimeoutException:
            print(f"⏳ Timeout (stats): {page_url}", flush=True)
            time.sleep(2)
    return None

def parse_ticks_from_stats_soup(stats_soup):
    """Robustly extract total Ticks from a /route/stats/ page."""
    if not stats_soup:
        return None

    # 1) header + span or inline number
    try:
        for hx in stats_soup.find_all(["h2", "h3", "h4"]):
            t = hx.get_text(" ", strip=True)
            if "ticks" in t.lower():
                span = hx.select_one("span.small.text-muted") or hx.find("span", class_="small")
                if span:
                    m_num = re.search(r"(\d[\d,]*)", span.get_text(strip=True))
                    if m_num:
                        return int(m_num.group(1).replace(",", ""))
                m_head = re.search(r"(\d[\d,]*)", t)
                if m_head:
                    return int(m_head.group(1).replace(",", ""))
    except Exception:
        pass

    # Consolidated text for regex passes
    text = stats_soup.get_text(" ", strip=True)

    # 2) All Time (12,345)
    m_all_time = re.search(r"All\s*Time\s*\((\d[\d,]*)\)", text, flags=re.IGNORECASE)
    if m_all_time:
        return int(m_all_time.group(1).replace(",", ""))

    # 3) 'Ticks ... 12,345'
    m_ticks_inline = re.search(r"Ticks[^0-9]{0,40}(\d[\d,]*)", text, flags=re.IGNORECASE)
    if m_ticks_inline:
        return int(m_ticks_inline.group(1).replace(",", ""))

    # 4) 'Ticks ...(12,345)'
    m_ticks_paren = re.search(r"Ticks[^()]{0,40}\((\d[\d,]*)\)", text, flags=re.IGNORECASE)
    if m_ticks_paren:
        return int(m_ticks_paren.group(1).replace(",", ""))

    return None

def get_route_links_from(page_url):
    """Extract all route links from a given area page."""
    driver.get(page_url)
    time.sleep(1)
    return [
        el.get_attribute("href")
        for el in driver.find_elements(By.CSS_SELECTOR, "a[href*='/route/']")
    ]

def collect_all_routes_recursive(area_url, visited=None):
    """Recursively collect all route links by visiting sub-areas."""
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

    # Collect subareas (only lef-nav-row links)
    subarea_elements = driver.find_elements(By.CSS_SELECTOR, ".lef-nav-row a")
    subarea_links = [el.get_attribute("href") for el in subarea_elements]

    # Recurse
    for sub_link in subarea_links:
        if sub_link and sub_link not in visited:
            route_links += collect_all_routes_recursive(sub_link, visited)

    return route_links

# ===========================
# OUTPUT DIRECTORIES
# ===========================
output_dir = r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\raw"
debug_dir = os.path.join(output_dir, "debug")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(debug_dir, exist_ok=True)

# ===========================
# MAIN SCRAPER LOOP
# ===========================
for url in URLS:
    print(f"\n➡️ Starting recursive scrape from: {url}", flush=True)
    route_urls = list(set(collect_all_routes_recursive(url)))
    print(f"✅ Total routes found: {len(route_urls)}", flush=True)

    all_routes = []
    missing_ticks = []  # <-- for debug CSV

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
            pitch, length_ft, route_type = 1, None, ""

        # Area hierarchy (prefer breadcrumb, fallback to warm links)
        breadcrumb = soup.select("nav[aria-label='breadcrumb'] a, .breadcrumbs a")
        if breadcrumb:
            area_hierarchy = " > ".join(a.get_text(strip=True) for a in breadcrumb)
        else:
            area_hierarchy = " > ".join(a.get_text(strip=True) for a in soup.select("div.text-warm a"))

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

        # Tick count
        ticks = None
        stats_url = ""
        if route_id:
            stats_url = route_url.replace("/route/", "/route/stats/")
            stats_soup = get_stats_soup(stats_url)
            if stats_soup:
                # Original pattern first
                found = False
                for h3 in stats_soup.find_all("h3"):
                    if h3.get_text(strip=True).startswith("Ticks"):
                        span = h3.select_one("span.small.text-muted")
                        if span:
                            try:
                                ticks = int(span.text.strip().replace(",", ""))
                                found = True
                            except ValueError:
                                ticks = None
                        break
                # Fallback
                if not found:
                    ticks = parse_ticks_from_stats_soup(stats_soup)

        if ticks is None:
            print(f"⚠️ Ticks not found → {route_name} ({route_id})", flush=True)
            missing_ticks.append({
                "Route ID": route_id,
                "Route Name": route_name,
                "URL": route_url,
                "Stats URL": stats_url or route_url.replace("/route/", "/route/stats/"),
                "Stars": stars,
                "Votes": votes,
                "Grade": grade,
                "Type": route_type,
                "Pitches": pitch,
                "Length (ft)": length_ft,
                "Area Hierarchy": area_hierarchy,
            })

        # Append
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

        # courteous pacing to avoid hammering the site
        time.sleep(0.2)

    print(f"✅ Total routes scraped: {len(all_routes)}", flush=True)
    print(f"🧪 Routes missing Ticks: {len(missing_ticks)}", flush=True)

    area_slug = url.rstrip("/").split("/")[-1].replace("-", "_").lower()
    file_path = os.path.join(output_dir, f"{area_slug}.csv")
    debug_path = os.path.join(debug_dir, f"{area_slug}_missing_ticks.csv")

    if all_routes:
        df = pd.DataFrame(all_routes)
        if "Pitches" in df.columns:
            df["Pitches"] = df["Pitches"].fillna(1).astype(int)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"✅ Saved: {file_path}")

        # Write debug CSV (always write so you can diff over time)
        dbg = pd.DataFrame(missing_ticks, columns=[
            "Route ID", "Route Name", "URL", "Stats URL", "Stars", "Votes",
            "Grade", "Type", "Pitches", "Length (ft)", "Area Hierarchy"
        ])
        dbg.to_csv(debug_path, index=False, encoding="utf-8-sig")
        print(f"🧾 Debug saved: {debug_path}")
    else:
        print("⚠️ No data scraped. Check network or structure.")

# ===========================
# CLEANUP
# ===========================
driver.quit()
