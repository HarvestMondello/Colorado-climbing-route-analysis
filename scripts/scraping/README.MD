# Scraping Scripts

This folder contains all **web scraping scripts** for pulling data from the public database.

Scripts:
- `1-region-scrape.py` — Collects all routes in a given region(s) and basic metadata: name, grade, FA info, stars/votes, etc.
- `2-combine-all-csv.py` — Combine all scraped regions into one CSV.
- `3-filter-routes.py` — Filter and rank routes based on classic criteria.
- `4-route-scrape.py` — — Scrapes detailed tick logs.
- `5-tick-aggregations-by-route.py` — aggregate tick logs per route by username.
- `6-join-routes-ticks.py` — Cleans and merges scraping outputs into a combined dataset.
- `scrape-all.py` — Runs the scrape scripts.

**Inputs:**  
- Region URLs from public database

**Outputs:**  
- Route metadata CSVs in `outputs/regions/`.  
- Tick detail CSVs in `outputs/ticks/`.  
- Combined route-level dataset in `outputs/`.  

> These scripts are usually run in sequence to build the raw dataset. The scrape-all.py will run them all consecutively. 



