
# Automation Scripts

This folder contains **runner scripts** that automate the end-to-end workflow.  
They don’t scrape or analyze directly — they call the other scripts in sequence.

Scripts:
- `run-all.py` — Executes the full pipeline (scraping → cleaning → analysis → leaderboards).  
  Stops immediately if any step fails. Logs to `outputs/logs/run_all.log`.  
- `scrape-all.py` — Executes the full scraping scripts. 
- `run-analysis.py` — Executes the full analysis scripts. 
- `monthly-leaderboards.py` — Version of `build-leaderboards-update.py` designed for monthly refresh jobs, can be modified for weekl or daily. Can be triggered by cron or GitHub Actions.  
- `quarterly-leaderboards.py` — Version of `build-leaderboards-update.py` designed for monthly refresh jobs, can be modified for weekl or daily. Can be triggered by cron or GitHub Actions. 

**Purpose:**  
- Ensure the pipeline runs in the correct order.  
- Centralize logging and error handling.  
- Support scheduled jobs for continuous updates.  

> Think of these scripts as the “glue” that ties everything together.
