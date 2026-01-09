# Colorado Climbing Route Data Analysis

Colorado climbing data collected via a Python pipeline, analyzed in PostgreSQL, and visualized in Python.

<img src="https://github.com/HarvestMondello/Colorado-climbing-route-analysis/blob/main/assets/eldorado-canyon.png" alt="Eldorado Canyon State Park" width="1200"/>


## Synopsis

**Problem**: Route quality, usage, and seasonality in Colorado are discussed anecdotally; there’s no unified dataset to compare cultural impact, historical significance, and modern traffic across regions.  

**Solution**: Build an end-to-end pipeline to scrape a public climbing database, normalize and store data in PostgreSQL, and analyze it with SQL + Python. Surface insights on cultural impact, seasonality, engagement, historical milestones, and demand forecasts for Colorado traditional climbing areas including Eldorado Canyon, Black Canyon of the Gunnison and The Diamond on Long's Peak. This analysis focuses exclusively on traditional (Trad) climbing routes and excludes Sport, Bouldering and Ice disciplines to sharpen insights on Colorado’s historical and cultural traditional legacy.

**Insights**  
- A small cluster of routes consistently anchor Colorado’s climbing identity with high **classic** scores.  
- Seasonality clusters reveal true all-season lines vs. narrow weather windows and seasonal closures.  
- “Hidden gems” emerge: high star ratings with relatively low visibility but strong **engagement** growth.  
- FA/FFA timelines map boldness across decades and correlate with later traffic waves.  
- Forecasts (2025–2029) flag sub-regions likely to see increased pressure.  

**Recommendation**  
- **Climbers**: Plan around seasonal windows and consider under-the-radar classics.  
- **Land managers**: Monitor growth clusters and allocate resources ahead of demand.  
- **Researchers**: Reuse the framework for other regions or national-scale analyses.  

## Introduction

This project turns fragmented Colorado climbing data into actionable insight. I built a Python scraper and cleaning pipeline, modeled and queried data in PostgreSQL, and visualized results in Python answering questions about cultural impact, usage patterns, historical context, and where demand is trending next.

See SQL and scripts here:  
- **SQL**: [`/sql`](sql/)  
- **Scripts (ETL, scraping, EDA)**: [`/scripts`](scripts/)  

## Table of Contents

- [Synopsis](#synopsis)  
- [Introduction](#introduction)  
- [Background](#background)  
- [Tools I Used](#tools-i-used)  
- [How I Built It](#how-i-built-it)  
- [The Analysis](#the-analysis)  
- [Automation](#automation)  
- [Repository Structure](#repository-structure)  
- [Conclusion](#conclusion)  
- [License](#license)
- [Code Style](#code-style)

## Background

Colorado hosts some of North America’s most storied stone, from Eldorado Canyon’s sandstone to the Black Canyon’s granite and RMNP’s alpine big walls. I set out to quantify:

1. Which routes carry the greatest cultural impact and legacy?  
2. How do usage patterns shift by season and decade?  
3. Which climbs are “hidden gems” high quality but under-visited?  
4. What do FA/FFA timelines reveal about boldness and progression?  
5. Where is demand likely to grow through 2029?  

**Data source**: a publicly available climbing database scraped for route metadata and tick histories. From the scraped database, only routes labeled as Trad were included. Sport, Bouldering and Ice routes were excluded to maintain focus on Colorado’s most historically significant climbing styles (Eldorado Canyon, Black Canyon and The Diamond).

## Tools I Used

- **Python**: scraping (Selenium/Requests/BS4), cleaning, EDA, modeling, viz (Pandas, NumPy, Matplotlib).  
- **PostgreSQL**: schema design, joins/aggregation, final query layer.  
- **VS Code + Git/GitHub**: development, versioning, and docs.  
- **Markdown**: documentation + project pages.  
- **ChatGPT**: formatting and routine automation.  

## How I Built It

1. **Collection**: Python scraper pulls route metadata (name, grade, type, pitches, stars, votes, area hierarchy), tick logs (dates, notes, climbers), and FA/FFA info. During scraping, route metadata was filtered by type=Trad. Sport, Bouldering and Ice entries were dropped at this stage, ensuring the PostgreSQL schema and subsequent analysis centered solely on traditional climbing.
2. **Processing**: Normalize grades, parse decades, standardize areas, and join route ↔ tick datasets.  
3. **Storage**: Persist as CSV and load into PostgreSQL for querying and reproducible analysis.  
4. **Analysis & Modeling**:  
   - SQL for aggregations and filters  
   - Python for EDA, seasonality clustering, and demand forecasting (2025–2029)  
5. **Outputs**: Leaderboards and route metrics published to `/docs` and refreshed on a schedule.  

## The Analysis

### 1) Cultural Impact & Classic Ranking
- Bayesian quality scoring with vote-count dampening.  
- “Classic rank” contextualizes raw scores across regions.  
- Cultural signals combined with historical context to surface era-defining lines.  

### 2) Engagement & Visibility
- Flags: `hidden_gem`, `overrated?`, popularity vs. quality, region-normalized usage.  
- Trend metric: share of ticks in the last 5 years; “is_trending_now” vs. “inactive_last_5yr”.  

### 3) Seasonality Profiles
- Monthly percentages + meteorological seasons (Winter/Spring/Summer/Fall).  
- K-Means clustering to label routes (four seasinal profiles were found: “All-Season”, “Summer-Peak”, “Shoulder-Season (Spring/Fall)” and " Nesting Closure Seasonal").  
- Seasonal Concentration Score + dominant season.  

### 4) Historical Context (FA/FFA)
- FA/FFA decades by route and region; boldness timelines.  
- Links between milestone ascents and later popularity waves.  

### 5) Demand Forecasts (2025-2029)
- Linear + exponential models; pick by best fit (R² tracked).  
- Reliability filter (R² ≥ 0.85); summary by sub-region (Area Hierarchy L1–L5).  
- Growth rankings to flag where pressure likely increases.  

### Live Leaderboards (Docs)

- **Top Routes & climbers (refreshed quarterly)**: [`/docs/leaderboards.md`](docs/leaderboards.md) - updated January, 2026
- **Top 100 Climbrs / 100 routes (refreshed annually)**: [`/docs/leaderboards-100.md`](docs/leaderboards-100.md) - updated January, 2026

## Automation

- ***Quarterly refresh**: Top leaderboards rebuild the at the end of each quarter.
- **Annual refresh**: Top 100 leaderboards rebuild January of each year.  
- **Resilience**: Failed routes are logged and retried automatically in the next cycle.  
- **Artifacts**: Refreshed CSVs in `/data` and `/outputs`, with updated docs in `/docs`.  

## Repository Structure

```
Colorado-climbing-route-analysis/
├─ assets/        # Images and figures for README/docs
├─ data/          # Raw & processed CSVs
├─ docs/          # Published leaderboards
├─ scripts/       # Scraping, ETL, analysis, automation
├─ sql/           # PostgreSQL schema & queries
├─ outputs/       # Final datasets & visualizations
├─ README.md      # Project summary
├─ LICENSE.md     # Licensing
├─ .gitattributes
├─ DOCS_CONVENTIONS.md
└─ NAMING_CONVENTIONS.md
```

## Conclusion

**The problem**: Climbing decisions and planning by climbers and land managers benefit from objective measures of quality, seasonality, engagement and trend.  

**How it was solved**: A reproducible pipeline + SQL/Python analysis to rank cultural impact, profile seasonality, surface hidden gems and forecast demand.  

**Key takeaways**:  
1. A consistent “cultural core” of routes appears across regions.  
2. Seasonality clusters separate all-season objectives from narrow windows.  
3. Hidden gems and overrated flags help prioritize exploration.  
4. FA/FFA timelines illuminate eras of boldness and later engagement waves.  
5. Forecasts highlight where demand is likely to rise, useful for both trip planning and stewardship.  

## License

Created by Harvest Mondello. You’re welcome to use this project for **personal** or **educational** purposes!  
Feel free to explore, adapt, and learn from the code and visuals. **Commercial use isn’t permitted** without permission.  
See [LICENSE.md](https://github.com/HarvestMondello/Colorado-climbing-route-analysis/blob/main/LICENSE.MD) for full details and contact info.

## Code Style

All Python code in this repository follows **Google-style Python docstrings**.  
See [DOCS_CONVENTIONS.md](https://github.com/HarvestMondello/Colorado-climbing-route-analysis/blob/main/DOCS_CONVENTIONS.md) for details and examples.
