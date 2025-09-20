# scripts/leaderboards/build_route_pages.py
"""
Minimal, idempotent updater for per-route Markdown pages.

Writes (in this exact order, once each):
- ### Metrics
- ### Seasonality  (always includes '#### Meteorological Seasons' and '### Seasonality Usage by Month')
- ### Leaderboards (Top Climbers table; omitted if no data)

Design decisions:
- Entire section header + content is placed INSIDE the AUTO markers.
- Hard reset only removes AUTO blocks (no aggressive header stripping).
- H1 '# Route Profile: <name>' is respected; if present and mismatched to
  dataset row, the file is skipped (prevents wrong-page updates).

Matching:
- Prefers H1 '# Route Profile: <name>'
- Falls back to filename (snake/kebab), indexing both 'the_naked_edge.md'
  and 'the-naked-edge.md' style names.

Usage:
  python scripts/leaderboards/update_route_profiles_min.py \
    --dataset <joined_route_tick_cleaned.csv> \
    --routes-dir <docs/routes> \
    [--leaderboards docs/leaderboards.md] [--dry-run] [--no-backup]
"""

from __future__ import annotations
import argparse, re, sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# ----------------------
# Defaults
# ----------------------
DEFAULT_DATASET = Path(
    r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed\joined_route_tick_cleaned.csv"
)
DEFAULT_ROUTES_DIR = Path(
    r"C:\Users\harve\Documents\Projects\MP-routes-Python\docs\routes"
)
DEFAULT_LEADERBOARDS = Path(
    r"C:\Users\harve\Documents\Projects\MP-routes-Python\docs\leaderboards.md"
)

# ----------------------
# Constants
# ----------------------
MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]
SEASONS = {
    "Winter": ["December","January","February"],
    "Spring": ["March","April","May"],
    "Summer": ["June","July","August"],
    "Fall":   ["September","October","November"],
}

# NOTE: We title the climber section "Leaderboards" per your preference.
AUTO = {
    "METRICS":      ("<!-- AUTO:METRICS:START -->",      "<!-- AUTO:METRICS:END -->",      "### Metrics"),
    "SEASONALITY":  ("<!-- AUTO:SEASONALITY:START -->",  "<!-- AUTO:SEASONALITY:END -->",  "### Seasonality"),
    "TOP_CLIMBERS": ("<!-- AUTO:TOP_CLIMBERS:START -->", "<!-- AUTO:TOP_CLIMBERS:END -->", "### Leaderboards"),
    "SUMMARY":      ("<!-- AUTO:SUMMARY:START -->",      "<!-- AUTO:SUMMARY:END -->",      "## Auto-Updated Summary"),
}

H1_RE = re.compile(r"^\s*#\s*Route Profile:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)

# ----------------------
# Small helpers
# ----------------------
def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def kebab(s: str) -> str:
    s = re.sub(r"[^\w\s-]+","", s, flags=re.UNICODE)
    return re.sub(r"[\s_]+","-", s.strip().lower()).strip("-")

def snake(s: str) -> str:
    s = re.sub(r"[^\w\s-]+","", s, flags=re.UNICODE)
    return re.sub(r"[\s-]+","_", s.strip().lower()).strip("_")

def map_month_cols(df: pd.DataFrame) -> List[str]:
    """Return month columns in canonical order, case-insensitive."""
    lm = {c.lower(): c for c in df.columns}
    cols = [lm[m.lower()] for m in MONTHS if m.lower() in lm]
    return cols

def find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Find a column by trying multiple candidate names (case-insensitive)."""
    for c in candidates:
        if c in df.columns:
            return c
    lm = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lm:
            return lm[c.lower()]
    return None

def extract_h1_name(md: str) -> Optional[str]:
    m = H1_RE.search(md)
    return m.group(1).strip() if m else None

def index_markdown(routes_dir: Path) -> Dict[str, Path]:
    """Create an index mapping both kebab and snake slugs to file paths."""
    idx: Dict[str, Path] = {}
    for p in routes_dir.rglob("*.md"):
        if p.name.endswith(".bak.md") or p.suffix.endswith(".bak"):
            # ignore backups
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        name = extract_h1_name(txt)
        if name:
            idx[kebab(name)] = p
            idx[snake(name)] = p
        # also index by filename
        idx[kebab(p.stem)] = p
        idx[snake(p.stem)] = p
    return idx

def read_ranks(leaderboards_md: Optional[Path]) -> Dict[str,int]:
    """Parse ranks from leaderboards table lines like:
       |  1 | [The Naked Edge](#the-naked-edge-rank-1)
    """
    if not leaderboards_md or not leaderboards_md.exists():
        return {}
    text = leaderboards_md.read_text(encoding="utf-8", errors="ignore")
    ranks: Dict[str,int] = {}
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*\[(.+?)\]\(#.+?\)\s*$", text, re.MULTILINE):
        rank = int(m.group(1))
        name = m.group(2)
        ranks[kebab(name)] = rank
    return ranks

def clean_area(area: Optional[str]) -> str:
    if not area:
        return ""
    s = re.sub(r"\s+"," ", str(area)).strip()
    s = re.sub(r"(?i)^all locations\s*>\s*","", s)
    s = re.sub(r"(?i)\s*sort routes\s*$","", s)
    return s

def fmt_cell(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    if isinstance(x, float):
        return f"{x:.2f}" if x % 1 else f"{int(x)}"
    return str(x)

def strip_none_lines(text: str) -> str:
    return "\n".join([ln for ln in text.splitlines() if ln.strip() != "None"])

def ensure_backup(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    if not bak.exists():
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

# ---------- NEW helpers for Metrics ----------
def _fmt_num(x, nd=1) -> str:
    """Format a number with fixed decimals; empty if NaN/None."""
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return f"{float(x):.{nd}f}"
    except Exception:
        return ""

def _fmt_rank(x) -> str:
    """Format rank as integer string; empty if NaN."""
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return f"{int(round(float(x)))}"
    except Exception:
        return ""

def _extract_location(area_hierarchy: str) -> str:
    """
    Derive a concise 'Location' from Area Hierarchy.
    Rules per examples:
      All Locations > Colorado > Boulder > Eldorado Canyon SP > ...
        -> Eldorado Canyon SP
      All Locations > Colorado > Boulder > Flatirons > North > Third Flatiron
        -> Flatirons
    Implementation: split on '>' and take index 3 if starts with 'All'/'All Locations' and len>=4,
    else fallback to last non-empty part.
    """
    if not area_hierarchy or not isinstance(area_hierarchy, str):
        return ""
    parts = [p.strip() for p in area_hierarchy.split(">") if p.strip()]
    if not parts:
        return ""
    first = parts[0].lower()
    if first in ("all", "all locations") and len(parts) >= 4:
        return parts[3]
    return parts[-1]

# ----------------------
# Content builders
# ----------------------
def build_metrics(row: pd.Series, cols: Dict[str,str], rank_map: Dict[str,int]) -> str:
    """
    Build the 'Metrics' table with:
    Classic Rank, Grade, Location, Stars (avg), Votes, Unique Climbers,
    Lifetime Ticks, Avg Ticks / Climber.
    """
    name = str(row[cols["name"]]).strip()
    slug = kebab(name)

    # Prefer explicit classic_rank column; fallback to parsed ranks from leaderboards.md
    classic_rank_val = row.get(cols["classic_rank"]) if cols["classic_rank"] else rank_map.get(slug)

    grade_val        = row.get(cols["grade"])
    stars_val        = row.get(cols["stars"])
    votes_val        = row.get(cols["votes"])
    total_ticks_val  = row.get(cols["total_ticks"])
    uniq_climbers_val= row.get(cols["unique_climbers"])
    area_val         = clean_area(row.get(cols["area"])) if cols["area"] else ""

    # Derive Location from Area Hierarchy
    location_val     = _extract_location(area_val)

    # Avg ticks / climber (2 decimals), guard division by zero
    avg_ticks_per_climber = ""
    try:
        if pd.notna(total_ticks_val) and pd.notna(uniq_climbers_val) and float(uniq_climbers_val) > 0:
            avg_ticks_per_climber = f"{float(total_ticks_val) / float(uniq_climbers_val):.2f}"
    except Exception:
        avg_ticks_per_climber = ""

    rows = [
        ("Classic Rank",        _fmt_rank(classic_rank_val)),
        ("Grade",               f"{grade_val}" if pd.notna(grade_val) else ""),
        ("Location",            location_val),
        ("Stars (avg)",         _fmt_num(stars_val, nd=1)),
        ("Votes",               _fmt_num(votes_val, nd=1)),
        ("Unique Climbers",     _fmt_num(uniq_climbers_val, nd=1)),
        ("Lifetime Ticks",      _fmt_num(total_ticks_val, nd=1)),
        ("Avg Ticks / Climber", avg_ticks_per_climber),
    ]

    lines = ["| Metric              | Value     |", "|:--------------------|:----------|"]
    lines += [f"| {k:<20} | {v:<9} |" for k, v in rows]
    out = "\n".join(lines)
    return re.sub(r"\|\s*None\s*\|", "|  |", out)

def _build_month_usage_block(month_series: pd.Series) -> str:
    """
    Build a monospaced text chart of monthly usage like:

    Jan | █                            2.9%
    Feb | █                            2.8%
    ...
    Oct | ████                        14.3%

    Scaling: ~3.5% per block to match leaderboard visuals.
    """
    # Map month -> short label
    labels = {
        "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
        "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
        "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec",
    }

    total = float(month_series.sum())
    if total <= 0:
        # still render empty bars at 0.0% for consistency
        pct = {m: 0.0 for m in MONTHS}
    else:
        pct = {m: float(month_series.get(m, 0.0)) / total * 100.0 for m in MONTHS}

    scale = 3.5  # percent per block
    lines = []
    for m in MONTHS:
        p = pct[m]
        blocks = max(1, int(round(p / scale))) if p > 0 else 0
        bar = "█" * blocks
        # Pad bars to a fixed width for pleasing alignment (optional)
        # Choose width generous enough for 4–5 blocks; keep right margin for percent text
        bar_padded = f"{bar:<28}"
        lines.append(f"{labels[m]:<3} | {bar_padded}{p:6.1f}%")
    return "```\n" + "\n".join(lines) + "\n```"

def build_seasonality(row: pd.Series, month_cols: List[str]) -> str:
    # Build safe monthly series
    m = pd.Series({c: float(row.get(c, 0) or 0) for c in month_cols}, dtype=float)
    total = float(m.sum())

    # Always compute season percentages (even if zero) so the block is stable
    if total <= 0:
        bullets = [
            "- ❄️ **Winter (Dec–Feb)**: 0.0% **off season**",
            "- 🌸 **Spring (Mar–May)**: 0.0%",
            "- ☀️ **Summer (Jun–Aug)**: 0.0%",
            "- 🍂 **Fall (Sep–Nov)**: 0.0%",
        ]
        month_usage = _build_month_usage_block(pd.Series({c: 0.0 for c in MONTHS}, dtype=float))
        return "\n".join(["#### Meteorological Seasons", *bullets, "", "### Seasonality Usage by Month", month_usage])

    # Season percentages
    pct = {s: float(m[[c for c in months if c in m.index]].sum()) / total * 100.0
           for s, months in SEASONS.items()}

    lowest = min(pct, key=pct.get)
    highest = max(pct, key=pct.get)

    # Rules:
    # - "off season" for any season < 3.0%
    # - "low season" for the lowest season if it's >= 3.0%
    # - "high season" for the highest season
    def line(season, emoji, span):
        v = pct[season]
        label = ""
        if v < 3.0:
            label = " **off season**"
        elif season == lowest:
            label = " **low season**"
        elif season == highest:
            label = " **high season**"
        return f"- {emoji} **{season} ({span})**: {v:.1f}%{label}"

    bullets = [
        line("Winter","❄️","Dec–Feb"),
        line("Spring","🌸","Mar–May"),
        line("Summer","☀️","Jun–Aug"),
        line("Fall",  "🍂","Sep–Nov"),
    ]

    # Month usage block (monospace)
    # Reindex 'm' to full MONTHS order to avoid missing months
    m_full = pd.Series({c: float(m.get(c, 0.0)) for c in MONTHS}, dtype=float)
    month_usage = _build_month_usage_block(m_full)

    return "\n".join(["#### Meteorological Seasons", *bullets, "", "### Seasonality Usage by Month", month_usage])

def build_top_climbers(row: pd.Series) -> Optional[str]:
    rows = []
    for i in range(1, 11):
        name = str(row.get(f"Top Climber {i}", "") or "").strip()
        if not name:
            continue
        ticks = row.get(f"Top Climber {i}_ticks")
        # Allow embedded "Name:123" format if ticks column is missing
        if ":" in name and (ticks is None or pd.isna(ticks)):
            left, right = name.split(":", 1)
            name = left.strip()
            try:
                ticks = int(float(right.strip().split()[0]))
            except:
                ticks = 0
        try:
            ticks = int(float(ticks)) if pd.notna(ticks) else 0
        except:
            ticks = 0
        rows.append((i, name, ticks))

    if not rows:
        return None

    head = "| Rank | Climber | Ticks |\n|-----:|:--------|------:|"
    body = "\n".join([f"| {r} | {n} | {t} |" for r,n,t in rows])
    return re.sub(r"\|\s*None\s*\|", "|  |", f"{head}\n{body}")

# ----------------------
# Hard reset of auto content
# ----------------------
def hard_reset_auto_sections(md: str) -> str:
    # 1) Remove ANY auto blocks (robust; case-insensitive)
    for key in ("METRICS","SEASONALITY","TOP_CLIMBERS","SUMMARY"):
        start, end, _ = AUTO[key]
        md = re.sub(
            rf"[ \t]*{re.escape(start)}[\s\S]*?{re.escape(end)}[ \t]*\n?",
            "",
            md,
            flags=re.IGNORECASE,
        )

    # 2) Remove stray horizontal rules
    md = re.sub(r"(?m)^[ \t]*---[ \t]*\n?", "", md)

    # 3) Collapse >2 blank lines to just 2
    md = re.sub(r"\n{3,}", "\n\n", md)

    return md

def upsert(md: str, title: str, start: str, end: str, body: str) -> str:
    # Entire section (header + body) lives INSIDE the AUTO block
    section = f"{start}\n{title}\n\n{body}\n{end}\n"
    if not md.endswith("\n"):
        md += "\n"
    return md + "\n" + section

# ----------------------
# Main page update
# ----------------------
def update_page(
    md_path: Path,
    row: pd.Series,
    cols: Dict[str,str],
    months: List[str],
    ranks: Dict[str,int],
    dry: bool,
    backup: bool
) -> bool:
    text = md_path.read_text(encoding="utf-8")
    h1 = extract_h1_name(text)
    name = str(row[cols["name"]]).strip()

    # Respect H1 if present and mismatched
    if h1 and h1.strip().lower() != name.lower():
        print(f"↪︎ Skip (H1 mismatch): {md_path.name}  (H1='{h1}' vs CSV='{name}')")
        return False

    # Hard reset any prior auto content
    text = hard_reset_auto_sections(text)

    metrics = build_metrics(row, cols, ranks)
    season  = build_seasonality(row, months)
    top     = build_top_climbers(row)

    # ORDER: Metrics -> Seasonality -> Leaderboards (Top Climbers)
    updated = text
    updated = upsert(updated, AUTO["METRICS"][2],     *AUTO["METRICS"][:2],     metrics)
    updated = upsert(updated, AUTO["SEASONALITY"][2], *AUTO["SEASONALITY"][:2], season)
    if top:
        updated = upsert(updated, AUTO["TOP_CLIMBERS"][2], *AUTO["TOP_CLIMBERS"][:2], top)

    updated = strip_none_lines(updated)

    if updated != text:
        if dry:
            print(f"[DRY] Would update: {md_path.name}")
        else:
            if backup:
                ensure_backup(md_path)
            md_path.write_text(updated, encoding="utf-8")
            print(f"✅ Updated: {md_path.name}")
        return True

    print(f"— No changes: {md_path.name}")
    return False

# ----------------------
# Wire-up
# ----------------------
def main():
    ap = argparse.ArgumentParser(description="Minimal route page updater.")
    ap.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    ap.add_argument("--routes-dir", type=Path, default=DEFAULT_ROUTES_DIR)
    ap.add_argument("--leaderboards", type=Path, default=DEFAULT_LEADERBOARDS)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    if not args.dataset.exists() or not args.routes_dir.exists():
        print("Dataset or routes dir not found.")
        sys.exit(1)

    df = read_csv(args.dataset)
    months = map_month_cols(df)

    cols = {
        "name":            find_col(df, ["Route Name","route_name","name"]),
        "grade":           find_col(df, ["Grade","grade"]),
        "stars":           find_col(df, ["Stars","stars"]),
        "votes":           find_col(df, ["Votes","votes"]),
        "total_ticks":     find_col(df, ["total_ticks","Total Ticks","ticks"]),
        "unique_climbers": find_col(df, ["unique_climbers","Unique Climbers"]),
        "area":            find_col(df, ["Area Hierarchy","area_hierarchy"]),
        "classic_rank":    find_col(df, ["Classic Rank","_classic_rank","classic_rank"]),
    }
    if not cols["name"]:
        print("Dataset missing route name column.")
        sys.exit(1)

    ranks = read_ranks(args.leaderboards) if args.leaderboards else {}

    md_idx = index_markdown(args.routes_dir)

    updated = 0
    missing: List[str] = []
    for _, row in df.iterrows():
        name = str(row[cols["name"]]).strip()
        md_path = md_idx.get(kebab(name)) or md_idx.get(snake(name))
        if not md_path:
            missing.append(name)
            continue
        if update_page(md_path, row, cols, months, ranks, args.dry_run, not args.no_backup):
            updated += 1

    print("\nSummary:")
    print(f"  Updated pages: {updated}")
    if missing:
        print("  Missing .md files for:")
        for n in missing[:25]:
            print(f"   - {n} -> {snake(n)}.md / {kebab(n)}.md (not found)")
        if len(missing) > 25:
            print(f"   ...and {len(missing)-25} more")

if __name__ == "__main__":
    main()
