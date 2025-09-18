# Scraping Scripts

This folder contains all **web scraping scripts** for pulling data from the public database.

Scripts:
- `1_region_scrape.py` — Collects all routes in a given region(s) and basic metadata: name, grade, FA info, stars/votes, etc.
- `2_combine_all_csv.py` — Combine all scraped regions into one CSV.
- `3_filter_routes.py` — Filter and rank routes based on classic criteria.
- `4_route_scrape.py` — — Scrapes detailed tick logs.
- `5_tick_aggregations_by_route.py` — aggregate tick logs per route by username.
- `6_join_routes_ticks.py` — Cleans and merges scraping outputs into a combined dataset.
- `scrape_all.py` — Runs the scrape scripts.

**Inputs:**  
- Region URLs from public database

**Outputs:**  
- Route metadata CSVs in `outputs/regions/`.  
- Tick detail CSVs in `outputs/ticks/`.  
- Combined route-level dataset in `outputs/`.  

> These scripts are usually run in sequence to build the raw dataset. The scrape-all.py will run them all consecutively. 





