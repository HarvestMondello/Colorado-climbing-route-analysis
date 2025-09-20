# scripts/leaderboards/build_route_pages.py
"""
Minimal, idempotent updater for per-route Markdown pages.

Writes (in this exact order, once each):
- ### Metrics
- ### Seasonality  (always includes '#### Meteorological Seasons' and '### Seasonality Usage by Month')
- ### Leaderboards (Top Climbers table; omitted if no data)

Key behavior:
- Searches ALL subfolders for .md via rglob("*.md").
- Robust matching between CSV route name and .md files by:
  - Using H1 '# Route Profile: <name>' if present (warning on mismatch, still update).
  - Falling back to filename.
  - Ignoring leading articles ('the', 'a', 'an').
  - Treating spaces, hyphens, and underscores as equivalent.
  - Normalizing punctuation/case.

Usage:
  python scripts/leaderboards/build_route_pages.py \
    --dataset <joined_route_tick_cleaned.csv> \
    --routes-dir <docs/routes> \
    [--leaderboards docs/leaderboards.md] [--dry-run] [--no-backup]
"""

from __future__ import annotations
import argparse, re, sys, unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Iterable, Set
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

AUTO = {
    "METRICS":      ("<!-- AUTO:METRICS:START -->",      "<!-- AUTO:METRICS:END -->",      "### Metrics"),
    "SEASONALITY":  ("<!-- AUTO:SEASONALITY:START -->",  "<!-- AUTO:SEASONALITY:END -->",  "### Seasonality"),
    "TOP_CLIMBERS": ("<!-- AUTO:TOP_CLIMBERS:START -->", "<!-- AUTO:TOP_CLIMBERS:END -->", "### Leaderboards"),
    "SUMMARY":      ("<!-- AUTO:SUMMARY:START -->",      "<!-- AUTO:SUMMARY:END -->",      "## Auto-Updated Summary"),
}

H1_RE = re.compile(r"^\s*#\s*Route Profile:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
ARTICLES = ("the ", "a ", "an ")

# ----------------------
# String normalization & key generation
# ----------------------
def _strip_accents(s: str) -> str:
    # NFKD normalize and strip combining marks
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

def _base_clean(s: str) -> str:
    """Lowercase, strip spaces, remove most punctuation (keep - _ and spaces), collapse whitespace."""
    if not isinstance(s, str):
        return ""
    s = _strip_accents(s)
    s = s.lower().strip()
    s = re.sub(r"[^\w\s\-_]+", "", s)   # keep letters/digits/space/_/-
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _drop_leading_article(s: str) -> str:
    for a in ARTICLES:
        if s.startswith(a):
            return s[len(a):]
    return s

def kebab(s: str) -> str:
    s = _base_clean(s)
    s = s.replace("_", " ")
    return re.sub(r"[\s_]+","-", s).strip("-")

def snake(s: str) -> str:
    s = _base_clean(s)
    s = s.replace("-", " ")
    return re.sub(r"[\s-]+","_", s).strip("_")

def norm_loose(s: str) -> str:
    """Very loose key: remove -, _, collapse spaces; drop leading article."""
    s = _base_clean(s)
    s = _drop_leading_article(s)
    s = s.replace("-", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def generate_keys(name: str) -> List[str]:
    """
    Generate a set of alias keys for matching:
    - kebab / snake of original
    - kebab / snake of article-dropped
    - loose norm with:
        * spaces
        * spaces->'-'
        * spaces->'_'
    """
    base = _base_clean(name)
    no_article = _drop_leading_article(base)

    keys: Set[str] = set()

    # original
    keys.add(kebab(base))
    keys.add(snake(base))

    # article-dropped
    keys.add(kebab(no_article))
    keys.add(snake(no_article))

    # very loose variants
    loose = norm_loose(name)            # 'naked edge'
    keys.add(loose)                     # 'naked edge'
    keys.add(loose.replace(" ", "-"))   # 'naked-edge'
    keys.add(loose.replace(" ", "_"))   # 'naked_edge'

    # also add raw stems just in case
    keys.add(base)
    keys.add(no_article)

    # ensure lowercase
    return [k.lower() for k in keys if k]

# ----------------------
# Small helpers
# ----------------------
def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

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
    """
    Index .md pages by multiple keys derived from:
    - H1 ('# Route Profile: <name>') if present
    - Filename stem
    Includes snake/kebab/article-dropped/loose variants.
    Searches subfolders with rglob.
    """
    idx: Dict[str, Path] = {}
    for p in routes_dir.rglob("*.md"):
        if p.name.endswith(".bak.md") or p.suffix.endswith(".bak"):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # From H1
        name = extract_h1_name(txt)
        if name:
            for k in generate_keys(name):
                idx[k] = p

        # From filename stem
        stem = p.stem
        for k in generate_keys(stem):
            idx[k] = p
    return idx

def read_ranks(leaderboards_md: Optional[Path]) -> Dict[str,int]:
    """Parse ranks from leaderboards table lines like:
       |  1 | [The Naked Edge](#the-naked-edge)
    """
    if not leaderboards_md or not leaderboards_md.exists():
        return {}
    text = leaderboards_md.read_text(encoding="utf-8", errors="ignore")
    ranks: Dict[str,int] = {}
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*\[(.+?)\]\(#.*?\)\s*$", text, re.MULTILINE):
        rank = int(m.group(1))
        name = m.group(2)
        for k in generate_keys(name):
            ranks[k] = rank
    return ranks

def clean_area(area: Optional[str]) -> str:
    if not area:
        return ""
    s = re.sub(r"\s+"," ", str(area)).strip()
    s = re.sub(r"(?i)^all locations\s*>\s*","", s)
    s = re.sub(r"(?i)\s*sort routes\s*$","", s)
    return s

def strip_none_lines(text: str) -> str:
    return "\n".join([ln for ln in text.splitlines() if ln.strip() != "None"])

def ensure_backup(path: Path) -> None:
    try:
        bak = path.with_suffix(path.suffix + ".bak")
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass

# ---------- Formatting helpers ----------
def _fmt_num(x, nd=1) -> str:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return f"{float(x):.{nd}f}"
    except Exception:
        return ""

def _fmt_rank(x) -> str:
    try:
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return ""
        return f"{int(round(float(x)))}"
    except Exception:
        return ""

def _extract_location(area_hierarchy: str) -> str:
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
    name = str(row[cols["name"]]).strip()
    key_variants = generate_keys(name)

    # Prefer explicit classic_rank; fallback to parsed ranks
    classic_rank_val = row.get(cols["classic_rank"]) if cols["classic_rank"] else None
    if (classic_rank_val is None) or (isinstance(classic_rank_val, float) and pd.isna(classic_rank_val)):
        for k in key_variants:
            if k in rank_map:
                classic_rank_val = rank_map[k]
                break

    grade_val        = row.get(cols["grade"])
    stars_val        = row.get(cols["stars"])
    votes_val        = row.get(cols["votes"])
    total_ticks_val  = row.get(cols["total_ticks"])
    uniq_climbers_val= row.get(cols["unique_climbers"])
    area_val         = clean_area(row.get(cols["area"])) if cols["area"] else ""

    location_val     = _extract_location(area_val)

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
    labels = {
        "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
        "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
        "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec",
    }
    total = float(month_series.sum())
    pct = {m: (float(month_series.get(m, 0.0)) / total * 100.0) if total > 0 else 0.0 for m in MONTHS}
    scale = 3.5
    lines = []
    for m in MONTHS:
        p = pct[m]
        blocks = max(1, int(round(p / scale))) if p > 0 else 0
        bar = "█" * blocks
        bar_padded = f"{bar:<28}"
        lines.append(f"{labels[m]:<3} | {bar_padded}{p:6.1f}%")
    return "```\n" + "\n".join(lines) + "\n```"

def build_seasonality(row: pd.Series, month_cols: List[str]) -> str:
    m = pd.Series({c: float(row.get(c, 0) or 0) for c in month_cols}, dtype=float)
    total = float(m.sum())

    if total <= 0:
        bullets = [
            "- ❄️ **Winter (Dec–Feb)**: 0.0% **off season**",
            "- 🌸 **Spring (Mar–May)**: 0.0%",
            "- ☀️ **Summer (Jun–Aug)**: 0.0%",
            "- 🍂 **Fall (Sep–Nov)**: 0.0%",
        ]
        month_usage = _build_month_usage_block(pd.Series({c: 0.0 for c in MONTHS}, dtype=float))
        return "\n".join(["#### Meteorological Seasons", *bullets, "", "### Seasonality Usage by Month", month_usage])

    pct = {s: float(m[[c for c in months if c in m.index]].sum()) / total * 100.0
           for s, months in SEASONS.items()}

    lowest = min(pct, key=pct.get)
    highest = max(pct, key=pct.get)

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

    m_full = pd.Series({c: float(m.get(c, 0.0)) for c in MONTHS}, dtype=float)
    month_usage = _build_month_usage_block(m_full)

    return "\n".join(["#### Meteorological Seasons", *bullets, "", "### Seasonality Usage by Month", month_usage])

def build_top_climbers(row: pd.Series) -> Optional[str]:
    rows = []
    for i in range(1, 10+1):
        name = str(row.get(f"Top Climber {i}", "") or "").strip()
        if not name:
            continue
        ticks = row.get(f"Top Climber {i}_ticks")
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
    for key in ("METRICS","SEASONALITY","TOP_CLIMBERS","SUMMARY"):
        start, end, _ = AUTO[key]
        md = re.sub(
            rf"[ \t]*{re.escape(start)}[\s\S]*?{re.escape(end)}[ \t]*\n?",
            "",
            md,
            flags=re.IGNORECASE,
        )
    md = re.sub(r"(?m)^[ \t]*---[ \t]*\n?", "", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md

def upsert(md: str, title: str, start: str, end: str, body: str) -> str:
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
) -> str:
    text = md_path.read_text(encoding="utf-8")
    h1 = extract_h1_name(text)
    name = str(row[cols["name"]]).strip()

    # Warn on different H1 but do NOT skip
    csv_keys = set(generate_keys(name))
    if h1:
        h1_keys = set(generate_keys(h1))
        if csv_keys.isdisjoint(h1_keys):
            print(f"⚠ H1 differs (continuing): {md_path.name} | H1='{h1}' vs CSV='{name}'")

    base_text = hard_reset_auto_sections(text)

    metrics = build_metrics(row, cols, ranks)
    season  = build_seasonality(row, months)
    top     = build_top_climbers(row)

    updated = base_text
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
        return "updated"

    print(f"— No changes: {md_path.name}")
    return "unchanged"

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

    # Index all markdown (includes subfolders)
    md_idx = index_markdown(args.routes_dir)
    discovered_pages = len(set(md_idx.values()))

    updated = 0
    unchanged = 0
    updated_files: List[str] = []
    missing: List[str] = []

    for _, row in df.iterrows():
        name = str(row[cols["name"]]).strip()
        key_candidates = generate_keys(name)

        md_path = None
        for k in key_candidates:
            md_path = md_idx.get(k.lower())
            if md_path:
                break
        if not md_path:
            missing.append(name)
            continue

        status = update_page(md_path, row, cols, months, ranks, args.dry_run, not args.no_backup)
        if status == "updated":
            updated += 1
            updated_files.append(md_path.as_posix().replace('\\','/'))
        else:
            unchanged += 1

    processed = updated + unchanged

    print("\nSummary:")
    print(f"  Markdown pages discovered (incl. subfolders): {discovered_pages}")
    print(f"  CSV routes matched to files: {processed}")
    print(f"  Updated pages: {updated}")
    print(f"  Unchanged pages: {unchanged}")
    if missing:
        print("  Missing .md files for:")
        for n in missing[:50]:
            # show likely filenames
            print(f"   - {n} -> candidates: '{snake(n)}.md', '{kebab(n)}.md', '{norm_loose(n).replace(' ', '_')}.md'")
        if len(missing) > 50:
            print(f"   ...and {len(missing)-50} more")

    if updated_files:
        print("\nUpdated file list:")
        for fn in updated_files:
            print(f"  • {fn}")

    print(f"\n✅ Done: updated {updated} route page(s), {unchanged} unchanged, {len(missing)} missing.")

if __name__ == "__main__":
    main()
