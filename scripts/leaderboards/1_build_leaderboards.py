# -*- coding: utf-8 -*-
"""
scripts/leaderboards/build_leaderboards.py

WORKFLOW NOTES
-------------------------------------------------------------------------
PURPOSE
    Build `docs/leaderboards.md` from a route-level CSV (snake_case) that already
    includes seasonality and leaderboard columns. Produces a printable Markdown with:
      - Routes index by classic_score
      - Per-route “Summary”, “Seasonality” (plus ASCII monthly bars), and “Top N Climbers”
      - A compact Top 100 Users leaderboard aggregated from per-route top_climber_* columns

INPUTS (defaults, UTF-8)
    - data/processed/joined_route_tick_cleaned.csv   (snake_case headers)
    - data/processed/featured_routes.csv  (optional)

OUTPUT
    - docs/leaderboards.md (UTF-8)

CHANGE (2026-01-08)
    - Score Top 100 Users using top 25 climbers per route
    - Display only top 10 climbers in each route section
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

# =============================================================================
# CONFIG DEFAULTS (PORTABLE)
# =============================================================================
# file lives at: scripts/leaderboards/build_leaderboards.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DOCS_DIR = (PROJECT_ROOT / "docs").resolve()
DEFAULT_FEATURED_CSV = (PROJECT_ROOT / "data" / "processed" / "featured_routes.csv").resolve()
DEFAULT_OUT_MD = (DEFAULT_DOCS_DIR / "leaderboards.md").resolve()
DEFAULT_SOURCE_CSV = (PROJECT_ROOT / "data" / "processed" / "joined_route_tick_cleaned.csv").resolve()

# ✅ Display per-route top 10, but score using top 25
TOP_N_CLIMBERS_DISPLAY = 10
TOP_N_CLIMBERS_SCORE = 25

# Optional “manual featured” for stable ordering; md only used for per-route “Open route profile” links
# top 20 routes
FEATURED_ROUTES = [
    {"name": "The Naked Edge",       "area_hint": "Eldorado Canyon", "md": "routes/eldo/naked-edge.md"},
    {"name": "Outer Space",          "area_hint": "Eldorado Canyon", "md": "routes/eldo/outer-space.md"},
    {"name": "Rewritten",            "area_hint": "Eldorado Canyon", "md": "routes/eldo/rewritten.md"},
    {"name": "East Face (Standard)", "area_hint": "Third Flatiron",  "md": "routes/east-face-standard.md"},
    {"name": "The Yellow Spur",      "area_hint": "Eldorado Canyon", "md": "routes/eldo/yellow-spur.md"},
    {"name": "Center Route",         "area_hint": "Cathedral Spire", "md": "routes/center-route.md"},
    {"name": "Direct Route",         "area_hint": "First Flatiron",  "md": "routes/direct-route.md"},
    {"name": "Casual Route",         "area_hint": "Long's Peak",     "md": "routes/casual-route.md"},
    {"name": "Country Club Crack",   "area_hint": "Boulder Canyon",  "md": "routes/country-club-crack.md"},
    {"name":  "Wunsch's Dihedral",   "area_hint": "Cathedral Spire", "md": "routes/wunschs-dihedral.md"},
    {"name": "Rosy Crucifixion",     "area_hint": "Eldorado Canyon",    "md": "routes/rosy-crucifixion.md"},
    {"name": "The Bastille Crack",   "area_hint": "Eldorado Canyon",    "md": "routes/bastille-crack.md"},
    {"name": "Freeway",              "area_hint": "Second Flatiron",    "md": "routes/freeway.md"},
    {"name": "South Face",           "area_hint": "RMNP",               "md": "routes/south-face.md"},
    {"name": "The Scenic Cruise",    "area_hint": "Black Canyon",       "md": "routes/scenic-cruise.md"},
    {"name": "Vertigo",   "area_hint": "Eldorado Canyon",    "md": "routes/vertigo.md"},
    {"name": "Blind Faith",   "area_hint": "Eldorado Canyon",    "md": "routes/blind-faith.md"},
    # Rebuffat's Arete...this is really a variation on Rewritten
    {"name": "Ruper",   "area_hint": "Eldorado Canyon",    "md": "routes/ruper.md"},
    {"name": "Over the Hill",   "area_hint": "Eldorado Canyon",    "md": "routes/over-the-hill.md"},
    {"name": "Handcracker Direct",   "area_hint": "Eldorado Canyon",    "md": "routes/handcracker-direct.md"},
]

# =============================================================================
# Column constants (snake_case)
# =============================================================================
COL_ROUTE_ID = "route_id"
COL_ROUTE_NAME = "route_name"
COL_AREA = "area_hierarchy"
COL_STARS = "stars"
COL_VOTES = "votes"
COL_TICKS = "total_ticks"
COL_CLASSIC = "classic_score"
COL_GRADE = "grade"

# Regex helpers
CLIMBER_NAME_RE_SNAKE = re.compile(r"^top_climber_(\d+)$", re.IGNORECASE)
CLIMBER_TICKS_RE_SNAKE = re.compile(r"^top_climber_(\d+)_ticks$", re.IGNORECASE)
CLIMBER_NAME_RE_LEGACY = re.compile(r"^\s*top\s+climber\s+(\d+)\s*$", re.IGNORECASE)
CLIMBER_TICKS_RE_LEGACY = re.compile(r"^\s*top\s+climber\s+(\d+)_ticks\s*$", re.IGNORECASE)

SPLIT_SUFFIX_RE = re.compile(r"^(.*?)(?::\s*([0-9][\d,]*))\s*$")
GRADE_NUM_RE = re.compile(r"5\.(\d{1,2})")

MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# =============================================================================
# Header normalization
# =============================================================================
def snake_case(name: str) -> str:
    s = str(name).strip().lower()
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"__+", "_", s).strip("_")
    return s

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [snake_case(c) for c in df.columns]
    rename_map = {
        "routeid": "route_id",
        "id": "route_id",
        "name": "route_name",
        "ticks_total": "total_ticks",
        "length_feet": "length_ft",
        "length": "length_ft",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    df = df.loc[:, ~df.columns.duplicated()]
    return df

def read_csv_snake(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    return normalize_headers(df)

def read_source_df(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Source CSV not found: {csv_path}")
    return read_csv_snake(csv_path)

# =============================================================================
# Small helpers
# =============================================================================
def clean_area_text(s: object) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)): return ""
    txt = str(s)
    txt = re.sub(r"[\r\n\t]+", " ", txt)
    txt = re.sub(r"(\s*>\s*)?Sort\s*Routes\b", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s+", " ", txt).strip()
    txt = re.sub(r"\s*>\s*", " > ", txt)
    return re.sub(r"\s*>\s*$", "", txt)

def canon(s: object) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)): return ""
    return re.sub(r"\s+", " ", str(s).strip())

def canon_area(s: object) -> str:
    return canon(clean_area_text(s))

def to_int_str(x) -> str:
    try:
        return str(int(float(x)))
    except Exception:
        return "" if pd.isna(x) else str(x)

def pct_or_zero(x) -> float:
    if pd.isna(x): return 0.0
    if isinstance(x, (int, float)): return float(x)
    s = str(x).strip()
    if s.endswith("%"): s = s[:-1]
    try: return float(s)
    except Exception: return 0.0

def slugify_anchor(text: str) -> str:
    s = re.sub(r"[^a-z0-9 -]", "", text.lower())
    s = re.sub(r"\s+", "-", s.strip()).replace(" ", "-")
    return re.sub(r"-+", "-", s)

def route_anchor(name: str) -> str:
    return f"#{slugify_anchor(name)}"

def split_name_ticks(label):
    if label is None or (isinstance(label, float) and pd.isna(label)): return None, None
    s = str(label).strip()
    if not s: return "", None
    m = SPLIT_SUFFIX_RE.match(s)
    if not m: return s, None
    name = m.group(1).strip()
    t = m.group(2)
    try: ticks = int(str(t).replace(",", ""))
    except Exception: ticks = None
    return name, ticks

def extract_top_climbers(row: pd.Series, top_n: int) -> pd.DataFrame:
    names, ticks = {}, {}
    for col in row.index:
        if not isinstance(col, str):
            continue
        c = snake_case(col)
        m1s = CLIMBER_NAME_RE_SNAKE.match(c)
        m2s = CLIMBER_TICKS_RE_SNAKE.match(c)
        m1l = CLIMBER_NAME_RE_LEGACY.match(col)
        m2l = CLIMBER_TICKS_RE_LEGACY.match(col)

        if m1s:
            names[int(m1s.group(1))] = row[col]
        elif m2s:
            ticks[int(m2s.group(1))] = row[col]
        elif m1l:
            names[int(m1l.group(1))] = row[col]
        elif m2l:
            ticks[int(m2l.group(1))] = row[col]

    recs = []
    for i in range(1, top_n + 1):
        raw = names.get(i)
        cname, name_ticks = split_name_ticks(raw)
        cticks = ticks.get(i, name_ticks)
        if (cname or cticks):
            recs.append({"Rank": i, "Climber": cname, "Ticks": cticks})
    return pd.DataFrame(recs, columns=["Rank", "Climber", "Ticks"])

def grade_weight(grade_text: object) -> float:
    if grade_text is None or (isinstance(grade_text, float) and pd.isna(grade_text)): return 1.0
    s = str(grade_text).lower()
    m = GRADE_NUM_RE.search(s)
    if not m: return 1.0
    try: num = int(m.group(1))
    except Exception: return 1.0
    if num >= 11: return 10.0
    if num in (9, 10): return 5.0
    if num in (5, 6, 7, 8): return 2.5
    if 0 <= num <= 4: return 1.25
    return 1.0

def md_table(df: pd.DataFrame) -> str:
    if df.empty: return "_No data available_"
    try: return df.to_markdown(index=False)
    except Exception:
        cols = list(df.columns)
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join(["---"]*len(cols)) + " |"
        rows = ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |" for r in df.values]
        return "\n".join([header, sep, *rows])

# =============================================================================
# Featured route resolution
# =============================================================================
def load_featured_exact(csv_path: Path | None, source: pd.DataFrame) -> pd.DataFrame:
    if not csv_path or not csv_path.exists():
        return pd.DataFrame()
    df = read_csv_snake(csv_path)

    need = {"route_id", "route_name", "area_hierarchy"}
    if not need.issubset(df.columns):
        return pd.DataFrame()

    left = source.copy()
    right = df.copy()

    for d in (left, right):
        d["_rid"] = d[COL_ROUTE_ID].map(canon)
        d["_rname"] = d[COL_ROUTE_NAME].map(canon)
        d["_area"] = d[COL_AREA].map(canon_area)

    if "md" not in right.columns:
        right["md"] = ""

    right = right.drop_duplicates(subset=["_rid", "_rname", "_area"], keep="first")
    merged = pd.merge(left, right[["_rid", "_rname", "_area", "md"]], on=["_rid", "_rname", "_area"], how="inner")
    return merged.rename(columns={"md": "_md"})

def resolve_manual_featured(manual_list: list[dict], source: pd.DataFrame) -> pd.DataFrame:
    if not manual_list:
        return pd.DataFrame()
    df = source.copy()
    df["_rname"] = df[COL_ROUTE_NAME].map(canon)
    df["_area"] = df[COL_AREA].map(canon_area)

    rows = []
    for idx, it in enumerate(manual_list):
        name = canon(it.get("name", ""))
        area = canon(it.get("area_hint", it.get("area", "")))
        md = (it.get("md") or "").strip()
        if not name:
            continue
        cand = df[df["_rname"] == name]
        if area:
            cand = cand[cand["_area"].str.contains(re.escape(area), case=False, na=False)]
        if cand.empty:
            continue
        if COL_CLASSIC in cand.columns:
            cand = cand.sort_values(by=COL_CLASSIC, ascending=False, kind="mergesort")
        take = cand.iloc[0].copy()
        take["_md"] = md
        take["_feature_order"] = idx
        rows.append(take)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).drop_duplicates(subset=["_rname", "_area"], keep="first")

# =============================================================================
# Seasonality text + ASCII chart
# =============================================================================
def get_month_percentages(row: pd.Series) -> dict[str, float]:
    have_pct = all((f"%_{m}" in row.index) for m in MONTHS)
    if have_pct:
        vals = [pct_or_zero(row.get(f"%_{m}", 0.0)) for m in MONTHS]
        if (max(vals) if vals else 0.0) <= 1.01:
            vals = [v * 100 for v in vals]
        return dict(zip(MONTHS, vals))

    counts = [float(0 if pd.isna(row.get(m.lower(), 0)) else row.get(m.lower(), 0)) for m in MONTHS]
    tot = sum(counts)
    return dict(zip(MONTHS, ([c / tot * 100 if tot > 0 else 0 for c in counts])))

def ascii_bar(pct: float, width: int = 26) -> str:
    pct = max(0.0, float(pct))
    fill = int(round((pct / 100.0) * width))
    return f"{'█' * fill}{' ' * (width - fill)} {pct:>5.1f}%"

def build_monthly_chart_block(row: pd.Series) -> str:
    months = get_month_percentages(row)
    if not months or sum(months.values()) <= 0.01:
        return ""
    lines = ["### Seasonality Usage by Month", "```"]
    for m, a in zip(MONTHS, MONTH_ABBR):
        lines.append(f"{a} | {ascii_bar(months[m])}")
    lines.append("```")
    return "\n".join(lines)

def seasonality_block(row: pd.Series) -> str:
    months = get_month_percentages(row)
    top4 = ", ".join([f"**{m} {v:.1f}%**" for m, v in sorted(months.items(), key=lambda kv: kv[1], reverse=True)[:4]])

    def _season_pct(lbls):
        return sum(months.get(m, 0.0) for m in lbls)

    if all(k in row.index for k in ("winter_pct", "spring_pct", "summer_pct", "fall_pct")):
        def safe(v):
            v = pct_or_zero(v)
            return v * 100 if v <= 1.01 else v
        seasons = {
            "❄️ **Winter (Dec–Feb)**": safe(row["winter_pct"]),
            "🌸 **Spring (Mar–May)**": safe(row["spring_pct"]),
            "☀️ **Summer (Jun–Aug)**": safe(row["summer_pct"]),
            "🍂 **Fall (Sep–Nov)**": safe(row["fall_pct"]),
        }
    else:
        seasons = {
            "❄️ **Winter (Dec–Feb)**": _season_pct(["December","January","February"]),
            "🌸 **Spring (Mar–May)**": _season_pct(["March","April","May"]),
            "☀️ **Summer (Jun–Aug)**": _season_pct(["June","July","August"]),
            "🍂 **Fall (Sep–Nov)**": _season_pct(["September","October","November"]),
        }

    vals = {k: float(pct_or_zero(v)) for k, v in seasons.items()}
    max_v = max(vals.values()) if vals else 0.0
    min_v = min(vals.values()) if vals else 0.0
    off_labels = {k for k, v in vals.items() if v < 3.0}
    low_labels = {k for k, v in vals.items() if abs(v - min_v) < 1e-9}
    peak_labels = {k for k, v in vals.items() if abs(v - max_v) < 1e-9}

    def fmt(v): return f"{v:.1f}%"
    lines = []
    for label, pct in vals.items():
        suffix = ""
        if label in peak_labels:
            suffix += " **peak season**"
        if label in off_labels:
            suffix = " **off season**" + (" **peak season**" if label in peak_labels else "")
        elif label in low_labels:
            suffix += " **low season**"
        lines.append(f"- {label}: {fmt(pct)}{suffix}")

    return "### Seasonality\n\n" + "- Seasonality Profile: (placeholder)\n" + f"- Highest-use months in order: {top4}\n\n" + "\n".join(lines) + "\n"

# =============================================================================
# User leaderboard (compact)
# =============================================================================
def build_user_leaderboard(rows: list[pd.Series], top_n: int) -> pd.DataFrame:
    rank_counts = defaultdict(lambda: defaultdict(int))
    tick_totals = defaultdict(int)
    grade_points = defaultdict(float)

    for r in rows:
        tdf = extract_top_climbers(r, top_n)
        if tdf.empty:
            continue
        gw = grade_weight(r.get(COL_GRADE, ""))
        for _, x in tdf.iterrows():
            user = str(x["Climber"]).strip() if not pd.isna(x["Climber"]) else ""
            if not user:
                continue
            rk = int(x["Rank"]) if not pd.isna(x["Rank"]) else None
            tk = x["Ticks"]
            try:
                tk = 0 if pd.isna(tk) else int(float(tk))
            except Exception:
                tk = 0
            if rk and 1 <= rk <= top_n:
                rank_counts[user][rk] += 1
            if tk > 0:
                tick_totals[user] += tk
                grade_points[user] += tk * gw

    out_rows = []
    users = set(rank_counts) | set(tick_totals) | set(grade_points)
    for u in users:
        rk_counts = rank_counts.get(u, {})
        rank_score = sum((11 - r) * rk_counts.get(r, 0) for r in range(1, top_n + 1))
        row = {
            "Username": u,
            "RankScore": rank_score,
            "GradePts": float(grade_points.get(u, 0.0)),
            "Total Ticks": int(tick_totals.get(u, 0)),
            "Score": 0.0,
        }
        row["Score"] = row["RankScore"] + row["GradePts"]
        for r in range(1, top_n + 1):
            row[f"#{r}"] = rk_counts.get(r, 0)
        row["Total Ranks"] = sum(rk_counts.values())
        out_rows.append(row)

    if not out_rows:
        cols = ["Username","Score","RankScore","GradePts"] + [f"#{r}" for r in range(1, top_n + 1)] + ["Total Ranks","Total Ticks"]
        return pd.DataFrame(columns=cols)

    df_out = pd.DataFrame(out_rows)
    return (
        df_out
        .sort_values(["Score","GradePts","RankScore","#1","Username"], ascending=[False,False,False,False,True], kind="mergesort")
        .reset_index(drop=True)
    )

# =============================================================================
# Args
# =============================================================================
def parse_args():
    ap = argparse.ArgumentParser(description="Build leaderboards markdown (snake_case, UTF-8).")
    ap.add_argument("--out", type=str, help="Absolute output .md path.")
    ap.add_argument("--csv", type=str, help="Path to source CSV (joined_route_tick_cleaned.csv).")
    ap.add_argument("--featured-csv", type=str, help="CSV with featured routes (expects route_id, route_name, area_hierarchy[, md])")
    return ap.parse_args()

# =============================================================================
# MAIN
# =============================================================================
def main():
    args = parse_args()

    out_md = Path(args.out).expanduser().resolve() if args.out else DEFAULT_OUT_MD
    docsdir = out_md.parent
    csvpath = Path(args.csv).expanduser().resolve() if args.csv else DEFAULT_SOURCE_CSV
    featcsv = Path(args.featured_csv).expanduser().resolve() if getattr(args, "featured_csv", None) else DEFAULT_FEATURED_CSV

    docsdir.mkdir(parents=True, exist_ok=True)

    df = read_source_df(csvpath)
    if COL_AREA in df.columns:
        df[COL_AREA] = df[COL_AREA].map(clean_area_text)

    need = [COL_ROUTE_NAME, COL_AREA, COL_STARS, COL_VOTES, COL_TICKS, COL_CLASSIC]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise KeyError(f"Missing required CSV columns (snake_case): {miss}")

    df_csv = load_featured_exact(featcsv if featcsv.exists() else None, df)
    df_manual = resolve_manual_featured(FEATURED_ROUTES, df)
    for col in ("_md", "_feature_order"):
        if col not in df_csv.columns:
            df_csv[col] = "" if col == "_md" else 10_000
        if col not in df_manual.columns:
            df_manual[col] = "" if col == "_md" else 0

    to_render = pd.concat([df_manual, df_csv], ignore_index=True)
    keys = ["_rname", "_area"] if all(k in to_render.columns for k in ["_rname", "_area"]) else [COL_ROUTE_ID, COL_ROUTE_NAME, COL_AREA]
    to_render = to_render.drop_duplicates(subset=keys, keep="first")
    sort_cols = ["_feature_order"] + ([COL_CLASSIC] if COL_CLASSIC in to_render.columns else [])
    to_render = to_render.sort_values(by=sort_cols, ascending=[True, False], kind="mergesort").reset_index(drop=True)

    if len(to_render) > 0:
        scores = pd.to_numeric(to_render[COL_CLASSIC], errors="coerce")
        to_render["_classic_rank"] = scores.rank(ascending=False, method="min").astype("Int64")
        matched_sorted = to_render.sort_values(by=["_classic_rank", COL_CLASSIC, COL_ROUTE_NAME], ascending=[True, False, True])
    else:
        matched_sorted = to_render
        to_render["_classic_rank"] = pd.NA

    now_str = datetime.now(tz=ZoneInfo("America/Denver")).strftime("%Y-%m-%d %H:%M:%S %Z")

    route_rows = []
    for _, rr in matched_sorted.iterrows():
        rnk, rnm = rr.get("_classic_rank"), rr.get(COL_ROUTE_NAME, "")
        if pd.isna(rnk) or not str(rnm).strip():
            continue
        route_rows.append({"Classic Rank": int(rnk), "Route": f"[{rnm}]({route_anchor(rnm)})"})
    routes_block = "**Routes (by Classic Rank):**\n" + (md_table(pd.DataFrame(route_rows)) if route_rows else "_No routes selected_")

    parts = [
        "# Colorado Climbing Route Leaderboards - Top Routes",
        f"_Generated {now_str}_\n",
        "**[Top 100 Users by Score](#top-100-users-by-score)**\n",
        f"**Selected routes:** {len(to_render)}\n",
        f"**Scoring uses top {TOP_N_CLIMBERS_SCORE} climbers per route; route pages display top {TOP_N_CLIMBERS_DISPLAY}.**\n",
        routes_block,
        "",
    ]

    def grade_bucket(g):
        if g is None or (isinstance(g, float) and pd.isna(g)): return None
        s = str(g).lower()
        m = GRADE_NUM_RE.search(s)
        if not m:
            return "5.0*" if s.startswith("5.0") else ("4th*" if "4th" in s or "fourth" in s else None)
        n = int(m.group(1))
        return f"5.{n}*" if n <= 12 else "5.12*"

    if len(to_render) and COL_GRADE in to_render.columns:
        buckets = to_render[COL_GRADE].map(grade_bucket).value_counts()
        order = ["5.12*","5.11*","5.10*","5.9*","5.8*","5.7*","5.6*","5.5*","5.4*","5.3*","5.2*","5.1*","5.0*","4th*"]
        parts.append("**Grades Summary:**")
        parts.append(md_table(pd.DataFrame([{"Bucket": b, "Routes": int(buckets.get(b, 0))} for b in order])))
        parts.append("")

    if len(to_render) and COL_AREA in to_render.columns:
        ser = to_render[COL_AREA].astype(str).str.strip()
        ser = ser[ser.ne("") & ser.str.lower().ne("nan")]
        if not ser.empty:
            counts = ser.value_counts()
            top_areas = [f"{int(n)} routes {area}" for area, n in counts.head(5).items()]
            if top_areas:
                parts.append(f"**Top Areas:** {', '.join(top_areas)}\n")

    parts.append("> Source: joined_route_tick_cleaned.csv with embedded leaderboard columns.\n")

    rows_for_lb = []
    for _, r in matched_sorted.iterrows():
        rname = r.get(COL_ROUTE_NAME, "(unnamed route)") or "(unnamed route)"
        area = r.get(COL_AREA, "")
        mdrel = (r.get("_md") or "").strip()

        parts.append(f"## {rname}")
        if area:
            parts.append(f"**Area:** {area}")
        if mdrel:
            if not mdrel.startswith(("./", "../")):
                mdrel = f"./{mdrel}"
            parts.append(f"[Open route profile]({mdrel})\n")

        ticks_val = pd.to_numeric(r.get(COL_TICKS, 0), errors="coerce")
        climbers_val = pd.to_numeric(r.get("unique_climbers", 0), errors="coerce")
        avg_per_user = f"{ticks_val / climbers_val:.2f}" if pd.notna(ticks_val) and pd.notna(climbers_val) and climbers_val > 0 else ""

        summary = pd.DataFrame([
            {"Metric": "Classic Rank",        "Value": to_int_str(r.get("_classic_rank"))},
            {"Metric": "Grade",               "Value": r.get(COL_GRADE, "")},
            {"Metric": "Stars (avg)",         "Value": r.get(COL_STARS, "")},
            {"Metric": "Votes",               "Value": r.get(COL_VOTES, "")},
            {"Metric": "Unique Climbers",     "Value": r.get("unique_climbers", "")},
            {"Metric": "Lifetime Ticks",      "Value": r.get(COL_TICKS, "")},
            {"Metric": "Avg Ticks / Climber", "Value": avg_per_user},
        ])
        parts.append("### Summary")
        parts.append(md_table(summary))
        parts.append("")

        parts.append(seasonality_block(r))
        chart = build_monthly_chart_block(r)
        if chart:
            parts.append(chart)
            parts.append("")

        # ✅ Per-route display still Top 10
        top_df = extract_top_climbers(r, TOP_N_CLIMBERS_DISPLAY)
        parts.append(f"### Top {TOP_N_CLIMBERS_DISPLAY} Climbers")
        parts.append(md_table(top_df))
        parts.append("\n---\n")

        rows_for_lb.append(r)

    # ✅ Scoring uses Top 25
    lb_df = build_user_leaderboard(rows_for_lb, TOP_N_CLIMBERS_SCORE)

    parts.append("## Top 100 Users by Score")
    if lb_df.empty:
        parts.append("_No data available_\n")
    else:
        top100 = lb_df.head(100).copy().reset_index(drop=True)
        top100.insert(0, "Rank", range(1, len(top100) + 1))
        for c in ("Score", "GradePts"):
            if c in top100.columns:
                top100[c] = top100[c].map(lambda x: f"{float(x):.1f}")
        if "RankScore" in top100.columns:
            top100["RankScore"] = top100["RankScore"].map(lambda x: f"{int(x)}")
        if "Total Ticks" in top100.columns:
            top100["Total Ticks"] = top100["Total Ticks"].map(lambda x: f"{int(x)}")

        compact = [c for c in ["Rank","Username","Score","RankScore","GradePts","Total Ticks"] if c in top100.columns]
        parts.append(md_table(top100[compact]))
        parts.append("")

        # Keep optional detail block (still works with top 25 scoring)
        if "#1" in top100.columns and "Total Ranks" in top100.columns:
            parts.append("<details><summary>Show #1 finishes and Total Ranks (Top 100)</summary>\n")
            parts.append(md_table(top100[["Rank","Username","#1","Total Ranks"]]))
            parts.append("\n</details>\n")

    parts += [
        "\n---\n",
        "### License\n",
        ("Created by Harvest Mondello. You're welcome to use this project for **personal** or **educational** purposes! "
         "Feel free to explore, adapt, and learn from the code and visuals. Just note that **commercial use isn’t permitted** "
         "without permission. See LICENSE for full details and contact info.\n"),
    ]

    content = "\n".join(parts)
    tmp = out_md.with_suffix(".md.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, out_md)
    print(f"Wrote {out_md}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
