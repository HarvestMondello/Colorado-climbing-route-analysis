# scrape-all.py
# runs the entire series of webscraper scripts
# must be placed in the same directory as the scripts 1-6 below
import subprocess
import sys
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

# ================================================================
# CONFIGURATION
# ================================================================
BASE_DIR = Path(__file__).parent.resolve()

scripts = [
    BASE_DIR / "1-region-scrape.py", #Collects all routes in a given region(s) and basic metadata: name, grade, FA info, stars/votes, etc.
    BASE_DIR / "2-combine-all-csv.py", #Combine all scraped regions into one CSV.
    BASE_DIR / "3-filter-routes.py", #Filter and rank routes based on classic criteria.
    BASE_DIR / "4-route-scrape.py", #Scrapes detailed tick logs.
    BASE_DIR / "5-tick-aggregations-by-route.py", #Aggregate tick logs per route by username.
    BASE_DIR / "6-join-routes-ticks.py", #Cleans and merges scraping outputs into a combined dataset.
]

MAX_RETRIES = 1   # Number of times to retry a failed script
RETRY_DELAY = 3   # Seconds to wait before retrying

# Create a timestamped log file name (date + time for uniqueness)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = BASE_DIR / f"runner_log_{timestamp}.txt"

# ================================================================
# HELPERS
# ================================================================
def log(message: str) -> None:
    """Print message to console and append to log file."""
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def fmt_secs(seconds: float) -> str:
    """Format seconds as H:MM:SS.mmm."""
    td = timedelta(seconds=seconds)
    # Keep milliseconds precision
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    secs = total_seconds % 60
    return f"{hours}:{minutes:02d}:{secs:06.3f}"

# ================================================================
# INITIALIZE LOG FILE
# ================================================================
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write(f"===== Run started at {datetime.now()} =====\n")
    f.write(f"Runner cwd: {os.getcwd()}\n")
    f.write(f"BASE_DIR : {BASE_DIR}\n")
    f.write(f"Python   : {sys.executable}\n\n")

# ================================================================
# SCRIPT RUNNER
# ================================================================
per_script_durations = {}  # {script_name: seconds}
overall_t0 = time.perf_counter()

for script in scripts:
    log(f"\n▶ Running {script}...")
    success = False  # Track if the script eventually succeeded

    # Attempt loop: first attempt + retries
    for attempt in range(1, MAX_RETRIES + 2):
        t0 = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "-u", str(script)],
            cwd=str(BASE_DIR),                    # Ensure relative paths work
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONUTF8": "1"} # Stable encoding on Windows
        )
        dt = time.perf_counter() - t0

        # Show captured output
        log(f"--- Meta (attempt {attempt}) ---\n"
            f"cmd: {[sys.executable, '-u', str(script)]}\n"
            f"cwd: {BASE_DIR}\n"
            f"rc : {result.returncode}\n"
            f"dur: {fmt_secs(dt)}")

        if result.stdout:
            log(f"--- STDOUT ---\n{result.stdout}")
        if result.stderr:
            log(f"⚠️ --- STDERR ---\n{result.stderr}")

        if result.returncode == 0:
            log(f"✅ {script.name} completed successfully on attempt {attempt}. ({fmt_secs(dt)})")
            per_script_durations[script.name] = per_script_durations.get(script.name, 0.0) + dt
            success = True
            break
        else:
            log(f"❌ {script.name} failed on attempt {attempt} (exit code {result.returncode}).")
            if attempt <= MAX_RETRIES:
                log(f"🔄 Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)

    if not success:
        log(f"⛔ {script.name} failed after {MAX_RETRIES + 1} attempts. Stopping execution.")
        total_dt = time.perf_counter() - overall_t0
        log(f"⏱️ Total runtime before failure: {fmt_secs(total_dt)}")
        sys.exit(result.returncode)

    log("-" * 50)

# ================================================================
# FINISH
# ================================================================
total_runtime = time.perf_counter() - overall_t0
log("\n🎉 All scripts ran successfully in sequence!")
log(f"⏱️ Total runtime: {fmt_secs(total_runtime)}")

# Per-script summary (sorted by longest first)
log("\n📊 Per-script durations (desc):")
for name, secs in sorted(per_script_durations.items(), key=lambda kv: kv[1], reverse=True):
    log(f"  • {name}: {fmt_secs(secs)}")

log(f"\n===== Run finished at {datetime.now()} =====\n")
