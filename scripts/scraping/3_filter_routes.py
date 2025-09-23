# scripts/filters/3_filter_routes_by_classic.py
from __future__ import annotations

import argparse
from pathlib import Path
import re
import numpy as np
import pandas as pd

"""
Current filters: trad=true, min starts (3), votes (50) and ticks (100)
trad*=true:     # Trad-only filter (Type contains 'trad')
    mask_trad = is_trad_series(df["type"])
# note that:     # Apply base guards
#    guards = (df["votes"] >= 50) & (df["stars"] >= 3.0) & (df["ticks"] >= 100)

Classic Ranking:
    # Composite score
    df["classic_score"] = (
        0.55 * df["norm_quality"] #55%
        + 0.20 * df["norm_popularity"] #20%
        + 0.10 * df["norm_cult_following"] #10%
        + 0.15 * df["norm_consensus"] #15%
    )

Top 100 by classic rank
"""

"""
Script: 3_filter_routes.py

Purpose:
    Filter routes to high-quality classics and rank them using a composite
    "classic_score". Enforces "Trad" type filter.

Workflow:
    1) Load combined routes CSV
    2) Apply quality/volume guards (votes >= 50, stars >= 3.0, ticks >= 100)
    3) Filter to Trad routes only (type contains 'trad', case-insensitive)
    4) Compute normalized quality/popularity/consensus/cult_following
    5) Compute composite classic_score and sort
    6) Select top N and save to CSV (snake_case output)

Input:
    - CSV with columns including (case-insensitive support):
        Stars, Votes, Ticks, Pitches, Type
      (If your file already uses snake_case like 'stars', 'votes', etc.,
       this script maps them automatically.)

Output:
    - Ranked CSV of top classics with a leading Rank column.

Dependencies:
    - pandas
    - numpy
    - python 3.10+

Example:
    python scripts/filters/3_filter_routes_by_classic.py \
        --input "data/processed/all_combined_routes.csv" \
        --output "data/processed/routes_filtered.csv" \
        --top-n 100
"""



# =========================
# Defaults & Constants
# =========================
DEFAULT_INPUT = Path(
    r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed\all_combined_routes.csv"
)
DEFAULT_OUTPUT = Path(
    r"C:\Users\harve\Documents\Projects\MP-routes-Python\data\processed\routes_filtered.csv"
)
DEFAULT_TOP_N = 100
BAYES_K = 50  # Bayesian prior dampening constant


# =========================
# Utilities
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to snake_case for internal use.

    Args:
        df (pd.DataFrame): Raw dataframe with arbitrary column casing.

    Returns:
        pd.DataFrame: Dataframe with snake_case columns.
    """
    def to_snake(s: str) -> str:
        s = re.sub(r"[\s\-]+", "_", s.strip())
        s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
        return s.lower()

    df = df.copy()
    df.columns = [to_snake(c) for c in df.columns]
    return df


def ensure_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Coerce selected columns to numeric.

    Args:
        df (pd.DataFrame): Input dataframe.
        cols (list[str]): Column names to coerce.

    Returns:
        pd.DataFrame: Dataframe with numeric columns (NaN on errors).
    """
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def is_trad_series(series: pd.Series) -> pd.Series:
    """
    Identify rows where 'type' contains 'trad' (case-insensitive, word-boundary).

    Args:
        series (pd.Series): The 'type' column.

    Returns:
        pd.Series: Boolean mask for rows considered Trad.
    """
    # Handle None/NaN robustly; accept strings like "Trad", "Trad, Sport", etc.
    pattern = re.compile(r"\btrad\b", flags=re.IGNORECASE)
    return series.astype(str).str.contains(pattern, na=False)


# =========================
# Core Metric Computations
# =========================
def compute_climbing_metrics(df: pd.DataFrame, k: int = BAYES_K) -> pd.DataFrame:
    """
    Compute normalized quality/popularity/consensus/cult_following and composite classic_score.

    Args:
        df (pd.DataFrame): Filtered dataframe with columns stars, votes, ticks (snake_case).
        k (int): Bayesian prior constant for quality smoothing.

    Returns:
        pd.DataFrame: Dataframe with added metric columns and classic_score.
    """
    df = df.copy()

    # Numeric coercion
    df = ensure_numeric(df, ["stars", "votes", "ticks", "pitches", "unique_climbers"])

    # Bayesian prior quality (stars adjusted by votes)
    mu = df["stars"].mean(skipna=True)
    denom = (df["votes"] + k).replace(0, np.nan)
    df["quality"] = (df["votes"] * df["stars"] + k * mu) / denom

    # Consensus/popularity/cult_following
    df["consensus"] = np.log10(1 + df["votes"])
    df["popularity"] = np.log10(1 + df["ticks"])
    df["cult_ratio"] = df["ticks"] / (df["votes"] + 1)
    df["cult_following"] = 0.25 * df["cult_ratio"]
    df["rating_to_tick_ratio"] = df["votes"] / (df["ticks"] + 1)

    # Min-max normalize selected columns
    for col in ["quality", "popularity", "cult_following", "consensus"]:
        mn, mx = df[col].min(), df[col].max()
        df[f"norm_{col}"] = (df[col] - mn) / (mx - mn + 1e-8)

    # Composite score
    df["classic_score"] = (
        0.55 * df["norm_quality"] #55%
        + 0.20 * df["norm_popularity"] #20%
        + 0.10 * df["norm_cult_following"] #10%
        + 0.15 * df["norm_consensus"] #15%
    )

    # Guardrail: if very low votes, deprioritize/remove score
    df.loc[df["votes"] < 10, "classic_score"] = np.nan

    return df


# =========================
# Main
# =========================
def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed arguments with input, output, and top_n.
    """
    p = argparse.ArgumentParser(description="Filter & rank Trad classic routes.")
    p.add_argument(
        "--input", type=Path, default=DEFAULT_INPUT, help="Path to combined routes CSV."
    )
    p.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT, help="Path to save filtered output CSV."
    )
    p.add_argument(
        "--top-n", type=int, default=DEFAULT_TOP_N, help="How many top classics to keep (default 100)."
    )
    return p.parse_args()


def main() -> None:
    """
    Run the filter/rank pipeline and save results.
    """
    args = parse_args()

    # Load & normalize columns to snake_case for internal consistency
    df = pd.read_csv(args.input)
    df = normalize_columns(df)

    # Column aliasing to support both TitleCase and snake_case inputs
    # (normalize_columns already lowercased; this is for clarity)
    required = ["stars", "votes", "ticks", "type"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found after normalization.")

    # Apply base guards
    guards = (df["votes"] >= 50) & (df["stars"] >= 3.0) & (df["ticks"] >= 100)

    # Trad-only filter (Type contains 'trad')
    mask_trad = is_trad_series(df["type"])

    df_filtered = df.loc[guards & mask_trad].copy()

    # Compute & sort by classic_score
    df_scored = compute_climbing_metrics(df_filtered)
    df_scored = df_scored.sort_values(by="classic_score", ascending=False, na_position="last")

    # Top N and rank
    df_top = df_scored.head(int(args.top_n)).copy()
    df_top.insert(0, "rank", range(1, len(df_top) + 1))

    # Save (snake_case path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df_top.to_csv(args.output, index=False)
    print(f"✅ Saved ranked Trad classics (top {len(df_top)}): {args.output}")


if __name__ == "__main__":
    main()
