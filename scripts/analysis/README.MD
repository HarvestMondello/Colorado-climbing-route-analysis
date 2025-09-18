# Analysis Scripts

This folder contains all **analysis and modeling scripts** for the climbing dataset.

Scripts:
- `1_EDA_dataset.py` — Exploratory data analysis at the dataset level.
- `2_EDA_routes.py` — Route-level analysis (seasonality, FA/FFA trends, climber stats).
- `3_forecast_demand_growth.py` — Forecasts route demand with linear/exponential models.
- `4_model_seasonality_clusters.py` — K-means clustering of monthly tick patterns.
- `5_model_daily_use.py` — Daily tick usage analysis by route.

**Inputs:**  
- Cleaned route and tick CSVs from `outputs/`.  

**Outputs:**  
- Summary CSVs in `outputs/`.  
- Visualizations in `assets/`.  
- Stats included in published docs under `docs/`.  

> These scripts focus on EDA, modeling, and generating insights for reporting.
