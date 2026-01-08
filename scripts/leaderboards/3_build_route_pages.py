# scripts/leaderboards/build_route_pages.py
"""
Minimal, idempotent updater for per-route Markdown pages.

Writes (in this exact order, once each):
- ### Metrics
- ### Seasonality  (always includes '#### Meteorological Seasons' and '### Seasonality Usage by Month')
- ### Leaderboards (Top Climbers table; omitted if no data)

Key behavior:
- Searches ALL subfolders for .md via rglob("*.md").
- Robust matching between CSV route name and .md files:
  - Uses H1 '# Route Profile: <name>' if present (warns on mismatch, still updates).
  - Falls back to filename stem.
  - Ignores leading articles ('the', 'a', 'an').
  - Treats spaces, hyphens, and underscores as equivalent.
  - Handles duplicate route names by keeping all candidates and
    selecting the best via Area Hierarchy tokens, then filename stem, then path length.
- Idempotent by default; add --force to rewrite even without diffs.

Also reports BOTH sides:
- CSV routes matched/updated/unchanged/missing
- Folder .md files discovered/processed (matched)/not matched (orphans)

Usage:
  python scripts/leaderboards/build_route_pages.py \
    --dataset <joined_route_tick_cleaned.csv> \
    --routes-dir <docs/routes> \
    [--leaderboards docs/leaderboards.md] [--dry-run] [--no-backup] [--force]
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd

# ----------------------
# Defaults (PORTABLE)
# ----------------------
# file: scripts/leaderboards/build_route_pages.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATASET = (PROJECT_ROOT / "data" / "processed" / "joined_route_tick_cleaned.csv").resolve()
DEFAULT_ROUTES_DIR = (PROJECT_ROOT / "docs" / "routes").resolve()
DEFAULT_LEADERBOARDS = (PROJECT_ROOT / "docs" / "leaderboards.md").resolve()

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
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

def _base_clean(s: str) -> str:
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
    s = _base_clean(s).replace("_", " ")
    return re.sub(r"[\s_]+", "-", s).strip("-")

def snake(s: str) -> str:
    s = _base_clean(s).replace("-", " ")
    return re.sub(r"[\s-]+", "_", s).strip("_")

def norm_loose(s: str) -> str:
    s = _base_clean(s)
    s = _drop_leading_article(s)
    s = s.replace("-", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def generate_keys(name: str) -> List[str]:
    base = _base_clean(name)
    no_article = _drop_leading_article(base)
    keys: Set[str] = set()
    keys.add(kebab(base));        keys.add(snake(base))
    keys.add(kebab(no_article));  keys.add(snake(no_article))
    loose = norm_loose(name)
    keys.add(loose)
    keys.add(loose.replace(" ", "-"))
    keys.add(loose.replace(" ", "_"))
    keys.add(base); keys.add(no_article)
    return [k.lower() for k in keys if k]

# ----------------------
# Small helpers
# ----------------------
def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

def map_month_cols(df: pd.DataFrame) -> List[str]:
    lm = {c.lower(): c for c in df.columns}
    return [lm[m.lower()] for m in MONTHS if m.lower() in lm]

def find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
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

# ---------- Area tokens ----------
def area_tokens(area_hierarchy: Optional[str]) -> Set[str]:
    """
    Convert Area Hierarchy to a bag of tokens for path disambiguation.
    """
    if not isinstance(area_hierarchy, str) or not area_hierarchy.strip():
        return set()
    s = _base_clean(area_hierarchy)
    s = re.sub(r"(?i)^all locations\s*>\s*", "", s)
    parts = [p.strip() for p in s.split(">") if p.strip()]
    tokens: Set[str] = set()
    for p in parts:
        for t in re.split(r"[\s\-_/]+", p):
            if t:
                tokens.add(t)
    return tokens

# ----------------------
# Index markdown: key -> list[Path]
# ----------------------
def index_markdown(routes_dir: Path) -> Dict[str, List[Path]]:
    idx: Dict[str, List[Path]] = {}

    def add(key: str, p: Path):
        key = key.lower()
        idx.setdefault(key, []).append(p)

    for p in routes_dir.rglob("*.md"):
        # don't skip ".bak.md" here because we now write backups as ".md.bak"
        # (but still skip if you have other backup conventions)
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
                add(k, p)

        # From filename stem
        stem = p.stem
        for k in generate_keys(stem):
            add(k, p)

    return idx

# ---------- Disambiguation among multiple file candidates ----------
def pick_best_path(candidates: List[Path], area_hint: Optional[str], route_name: str) -> Optional[Path]:
    """
    Disambiguate multiple .md paths:
      1) Prefer paths whose folder path contains any token from Area Hierarchy.
      2) Prefer exact filename stem matches to snake/kebab variants of route_name (with/without article).
      3) Prefer shortest path (least nested) as a stable fallback.
    """
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    path_strs = [c.as_posix().lower() for c in candidates]
    tokens = area_tokens(area_hint)

    if tokens:
        scored = []
        for p, s in zip(candidates, path_strs):
            hits = sum(1 for t in tokens if t and t in s)
            scored.append((hits, p))
        scored.sort(key=lambda x: (-x[0], len(x[1].as_posix())))
        if scored[0][0] > 0:
            return scored[0][1]

    stems = {
        snake(route_name),
        kebab(route_name),
        snake(_drop_leading_article(_base_clean(route_name))),
        kebab(_drop_leading_article(_base_clean(route_name))),
    }
    stem_map = {c.stem.lower(): c for c in candidates}
    for st in stems:
        if st.lower() in stem_map:
            return stem_map[st.lower()]

    return sorted(candidates, key=lambda p: len(p.as_posix()))[0]

def read_ranks(leaderboards_md: Optional[Path]) -> Dict[str, int]:
    if not leaderboards_md or not leaderboards_md.exists():
        return {}
    text = leaderboards_md.read_text(encoding="utf-8", errors="ignore")
    ranks: Dict[str, int] = {}
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*\[(.+?)\]\(#.*?\)\s*$", text, re.MULTILINE):
        rank = int(m.group(1))
        name = m.group(2)
        for k in generate_keys(name):
            ranks[k] = rank
    return ranks

def clean_area(area: Optional[str]) -> str:
    if not area:
        return ""
    s = re.sub(r"\s+", " ", str(area)).strip()
    s = re.sub(r"(?i)^all locations\s*>\s*", "", s)
    s = re.sub(r"(?i)\s*sort routes\s*$", "", s)
    return s

def strip_none_lines(text: str) -> str:
    return "\n".join([ln for ln in text.splitlines() if ln.strip() != "None"])

def ensure_backup(path: Path) -> None:
    """
    Create a one-time backup file at '<file>.bak' (portable, no duplicate '.md').
    """
    try:
        bak = path.with_suffix(path.suffix + ".bak")  # e.g., page.md -> page.md.bak
        if not bak.exists():
            bak.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
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
def build_metrics(row: pd.Series, cols: Dict[str, str], rank_map: Dict[str, int]) -> str:
    name = str(row[cols["name"]]).strip()
    key_variants = generate_keys(name)

    classic_rank_val = row.get(cols["classic_rank"]) if cols["classic_rank"] else None
    if (classic_rank_val is None) or (isinstance(classic_rank_val, float) and pd.isna(classic_rank_val)):
        for k in key_variants:
            if k in rank_map:
                classic_rank_val = rank_map[k]
                break

    grade_val         = row.get(cols["grade"])
    stars_val         = row.get(cols["stars"])
    votes_val         = row.get(cols["votes"])
    total_ticks_val   = row.get(cols["total_ticks"])
    uniq_climbers_val = row.get(cols["unique_climbers"])
    area_val          = clean_area(row.get(cols["area"])) if cols["area"] else ""
    location_val      = _extract_location(area_val)

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
    """
    FIX: month_cols are the dataset's actual column names.
         For season/month math we must remap to canonical month names.
    """
    if not month_cols:
        bullets = [
            "- ❄️ **Winter (Dec–Feb)**: 0.0% **off season**",
            "- 🌸 **Spring (Mar–May)**: 0.0%",
            "- ☀️ **Summer (Jun–Aug)**: 0.0%",
            "- 🍂 **Fall (Sep–Nov)**: 0.0%",
        ]
        month_usage = _build_month_usage_block(pd.Series({c: 0.0 for c in MONTHS}, dtype=float))
        return "\n".join(["#### Meteorological Seasons", *bullets, "", "### Seasonality Usage by Month", month_usage])

    # Build canonical month-name series regardless of dataset casing
    lm = {c.lower(): c for c in month_cols}
    m = pd.Series({mn: float(row.get(lm[mn.lower()], 0) or 0) for mn in MONTHS if mn.lower() in lm}, dtype=float)
    # ensure all months exist
    for mn in MONTHS:
        if mn not in m.index:
            m[mn] = 0.0
    m = m[MONTHS]

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

    pct = {s: float(m[months].sum()) / total * 100.0 for s, months in SEASONS.items()}
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
        line("Winter", "❄️", "Dec–Feb"),
        line("Spring", "🌸", "Mar–May"),
        line("Summer", "☀️", "Jun–Aug"),
        line("Fall",   "🍂", "Sep–Nov"),
    ]

    month_usage = _build_month_usage_block(m)
    return "\n".join(["#### Meteorological Seasons", *bullets, "", "### Seasonality Usage by Month", month_usage])

def build_top_climbers(row: pd.Series) -> Optional[str]:
    """
    FIX: accept both legacy columns ("Top Climber 1") and snake_case ("top_climber_1"),
         plus optional *_ticks columns in either style.
    """
    # Build case-insensitive mapping
    col_map = {str(c).lower(): c for c in row.index}

    def getv(*names):
        for nm in names:
            key = nm.lower()
            if key in col_map:
                return row.get(col_map[key])
        return None

    out_rows = []
    for i in range(1, 11):
        name = getv(f"Top Climber {i}", f"top_climber_{i}")
        name = "" if name is None or (isinstance(name, float) and pd.isna(name)) else str(name).strip()
        if not name:
            continue

        ticks = getv(f"Top Climber {i}_ticks", f"top_climber_{i}_ticks")

        if ":" in name and (ticks is None or pd.isna(ticks)):
            left, right = name.split(":", 1)
            name = left.strip()
            try:
                ticks = int(float(right.strip().split()[0].replace(",", "")))
            except Exception:
                ticks = 0

        try:
            ticks = int(float(ticks)) if ticks is not None and pd.notna(ticks) else 0
        except Exception:
            ticks = 0

        out_rows.append((i, name, ticks))

    if not out_rows:
        return None

    head = "| Rank | Climber | Ticks |\n|-----:|:--------|------:|"
    body = "\n".join([f"| {r} | {n} | {t} |" for r, n, t in out_rows])
    return re.sub(r"\|\s*None\s*\|", "|  |", f"{head}\n{body}")

# ----------------------
# Hard reset of auto content
# ----------------------
def hard_reset_auto_sections(md: str) -> str:
    for key in ("METRICS", "SEASONALITY", "TOP_CLIMBERS", "SUMMARY"):
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
    cols: Dict[str, str],
    months: List[str],
    ranks: Dict[str, int],
    dry: bool,
    backup: bool,
    force: bool = False,
) -> str:
    """
    Returns:
        "updated" or "unchanged"
    """
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    h1 = extract_h1_name(text)
    name = str(row[cols["name"]]).strip()

    csv_keys = set(generate_keys(name))
    if h1:
        h1_keys = set(generate_keys(h1))
        if csv_keys.isdisjoint(h1_keys):
            print(f"⚠ H1 differs (continuing): {md_path.name} | H1='{h1}' vs CSV='{name}'")

    base_text = hard_reset_auto_sections(text)

    metrics = build_metrics(row, cols, ranks)
    season = build_seasonality(row, months)
    top = build_top_climbers(row)

    updated_text = base_text
    updated_text = upsert(updated_text, AUTO["METRICS"][2], *AUTO["METRICS"][:2], metrics)
    updated_text = upsert(updated_text, AUTO["SEASONALITY"][2], *AUTO["SEASONALITY"][:2], season)
    if top:
        updated_text = upsert(updated_text, AUTO["TOP_CLIMBERS"][2], *AUTO["TOP_CLIMBERS"][:2], top)

    updated_text = strip_none_lines(updated_text)

    if force:
        if dry:
            print(f"[DRY][FORCE] Would update: {md_path.name}")
        else:
            if backup:
                ensure_backup(md_path)
            md_path.write_text(updated_text, encoding="utf-8")
            print(f"✅ Updated (forced): {md_path.name}")
        return "updated"

    if updated_text != text:
        if dry:
            print(f"[DRY] Would update: {md_path.name}")
        else:
            if backup:
                ensure_backup(md_path)
            md_path.write_text(updated_text, encoding="utf-8")
            print(f"✅ Updated: {md_path.name}")
        return "updated"

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
    ap.add_argument("--force", action="store_true", help="Rewrite sections even if no content changes")
    args = ap.parse_args()

    if not args.dataset.exists() or not args.routes_dir.exists():
        print("Dataset or routes dir not found.")
        sys.exit(1)

    df = read_csv(args.dataset)
    months = map_month_cols(df)

    cols = {
        "name":            find_col(df, ["Route Name", "route_name", "name"]),
        "grade":           find_col(df, ["Grade", "grade"]),
        "stars":           find_col(df, ["Stars", "stars"]),
        "votes":           find_col(df, ["Votes", "votes"]),
        "total_ticks":     find_col(df, ["total_ticks", "Total Ticks", "ticks"]),
        "unique_climbers": find_col(df, ["unique_climbers", "Unique Climbers"]),
        "area":            find_col(df, ["Area Hierarchy", "area_hierarchy"]),
        "classic_rank":    find_col(df, ["Classic Rank", "_classic_rank", "classic_rank"]),
    }
    if not cols["name"]:
        print("Dataset missing route name column.")
        sys.exit(1)

    ranks = read_ranks(args.leaderboards) if args.leaderboards else {}

    md_idx = index_markdown(args.routes_dir)

    all_md_files: Set[Path] = {p for plist in md_idx.values() for p in plist}
    discovered_pages = len(all_md_files)

    updated = 0
    unchanged = 0
    updated_files: List[str] = []
    processed_files: Set[Path] = set()
    missing: List[str] = []

    for _, row in df.iterrows():
        name = str(row[cols["name"]]).strip()
        area_hint = row.get(cols["area"]) if cols["area"] else ""
        key_candidates = generate_keys(name)

        candidates: List[Path] = []
        seen: Set[Path] = set()
        for k in key_candidates:
            for p in md_idx.get(k.lower(), []):
                if p not in seen:
                    seen.add(p)
                    candidates.append(p)

        if not candidates:
            missing.append(name)
            continue

        md_path = pick_best_path(candidates, area_hint, name)
        if not md_path:
            missing.append(name)
            continue

        status = update_page(
            md_path, row, cols, months, ranks,
            args.dry_run, not args.no_backup,
            force=args.force,
        )
        processed_files.add(md_path)
        if status == "updated":
            updated += 1
            updated_files.append(md_path.as_posix().replace("\\", "/"))
        else:
            unchanged += 1

    processed = updated + unchanged
    folder_processed_unique = len(processed_files)
    orphan_files = sorted({p.as_posix().replace("\\", "/") for p in all_md_files - processed_files})
    orphan_count = len(orphan_files)

    print("\nSummary:")
    print(f"  CSV routes matched to files: {processed}  (Updated: {updated}, Unchanged: {unchanged})")
    if missing:
        print(f"  CSV routes with NO matching .md file: {len(missing)}")
        for n in missing[:40]:
            print(f"    • {n} -> candidates: '{snake(n)}.md', '{kebab(n)}.md', '{norm_loose(n).replace(' ', '_')}.md'")
        if len(missing) > 40:
            print(f"    ...and {len(missing)-40} more")

    print(f"\n  Folder .md files discovered (incl. subfolders): {discovered_pages}")
    print(f"  Folder .md files processed (had matching CSV row): {folder_processed_unique}")
    print(f"  Folder .md files NOT matched to any CSV row (orphans): {orphan_count}")
    if orphan_files:
        for fp in orphan_files[:40]:
            print(f"    • {fp}")
        if orphan_count > 40:
            print(f"    ...and {orphan_count-40} more")

    print(
        f"\n✅ Done: {processed} CSV matches "
        f"({updated} updated, {unchanged} unchanged, {len(missing)} missing). "
        f"Folder coverage: {folder_processed_unique}/{discovered_pages} files processed; {orphan_count} orphan(s)."
    )

    if updated_files:
        print("\nUpdated file list:")
        for fn in updated_files:
            print(f"  • {fn}")

if __name__ == "__main__":
    main()
