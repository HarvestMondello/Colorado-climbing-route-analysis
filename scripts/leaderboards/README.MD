# Leaderboard Scripts

This folder contains scripts that **generate Markdown leaderboards** and per-route profile pages.

Scripts:
- `build_leaderboards.py` — Builds `docs/leaderboards.md` from CSV data.
- `build_route_pages.py` — Creates per-route `.md` files under `docs/routes/`.

**Inputs:**  
- Processed CSVs from `analysis/` outputs.  

**Outputs:**  
- Markdown docs in `docs/leaderboards.md` and `docs/routes/`.  

> These scripts automate the publication of analysis results into GitHub-ready docs.
