# Raw Data

This folder contains **raw datasets** as scraped from the public database.  
Files in this directory are not modified or cleaned — they represent the original outputs from the scraping scripts.

- Source: `scripts/scraping/` (region, route, and tick scrapers).  
- Format: CSV files (UTF-8).  
- Naming convention: `<area-slug>_routes.csv`, `<route-id>_ticks.csv`, etc.  

⚠️ **Note:** Raw data may contain duplicates, missing values, or inconsistent formatting.  
It should not be used directly for analysis — see `../processed/` for cleaned datasets.
