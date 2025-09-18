# Scripts

This directory contains all Python scripts used in the **Colorado Climbing Route Analysis** project.  
They are organized by purpose into four subfolders:

## 📂 Subfolders

- **[`scraping/`](./scraping/)**  
  Scripts for web scraping data from Mountain Project (routes, ticks, metadata).  
  Typical flow: scrape regions → scrape routes → scrape ticks → clean & join outputs.  

- **[`analysis/`](./analysis/)**  
  Exploratory data analysis, modeling, and forecasting.  
  Includes scripts for seasonality, clustering, forecasting, and daily usage patterns.  

- **[`leaderboards/`](./leaderboards/)**  
  Builds Markdown leaderboards and per-route profile pages for publication under `docs/`.  
  Automates the conversion of analysis outputs into GitHub-ready documentation.  

- **[`automation/`](./automation/)**  
  Runner scripts that glue the whole pipeline together.  
  Used for local refreshes or scheduled jobs (cron, GitHub Actions).  

## 🔄 Typical Workflow
1. **Scraping** → Collect raw route/tick data.  
2. **Analysis** → Perform EDA, seasonality, forecasting, and route-level insights.  
3. **Leaderboards** → Generate Markdown docs from processed data.  
4. **Automation** → Run everything end-to-end (manual or scheduled).  

---

> Each subfolder has its own `README.md` with details on the scripts inside.
