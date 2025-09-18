# 3-filter-routes-by-classic.py
# filters routes for 50 or more Votes, 3.0 or better stars and 100 or more ticks. 
# rank and sort by classic score
# selects top 100 classic routes in order
# top modify to select only top 10 change:  df_top100 = df_filtered.head(100).copy() to .head(10)

import pandas as pd
import numpy as np

# --- CONFIG ---
input_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\all-combined-routes.csv"
output_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\routes-filtered.csv"

# --- LOAD DATA ---
df = pd.read_csv(input_csv)

# --- Constants ---
k = 50  # ⚖️ Bayesian prior dampening constant

# --- Function: Compute Climbing Metrics ---
def compute_climbing_metrics(df):
    df = df.copy()

    # 🔢 Force columns to numeric
    df["Stars"] = pd.to_numeric(df["Stars"], errors="coerce")
    df["Votes"] = pd.to_numeric(df["Votes"], errors="coerce")
    df["Ticks"] = pd.to_numeric(df["Ticks"], errors="coerce")
    df["Pitches"] = pd.to_numeric(df["Pitches"], errors="coerce")
    df["unique_climbers"] = pd.to_numeric(df.get("unique_climbers", np.nan), errors="coerce")

    # 🌍 Global average star rating (Bayesian prior)
    mu = df["Stars"].mean(skipna=True)

    # 🧩 Bayesian Quality Score
    df['quality'] = (df['Votes'] * df['Stars'] + k * mu) / (df['Votes'] + k)

    # 📏 Consensus: log-scaled confidence in the rating
    df['consensus'] = np.log10(1 + df['Votes'])

    # 📈 Popularity: log of total ticks
    df['popularity'] = np.log10(1 + df['Ticks'])

    # -------------------------------
    # 🔁 Hybrid Cult Following Metric
    # -------------------------------
    # 1. Tick-to-vote ratio
    df['cult_ratio'] = df['Ticks'] / (df['Votes'] + 1)

    # 4. Weighted Composite Cult Following Score
    df['cult_following'] = (
        0.25 * df['cult_ratio']
        # + 0.50 * df['top10_tick_pct']
        # + 0.25 * df['loyalist_ratio']
    )

    # ⚖️ Rating-to-Tick Ratio
    df['rating_to_tick_ratio'] = df['Votes'] / (df['Ticks'] + 1)

    # 🧮 Normalize inputs for composite scoring
    for col in ['quality', 'popularity', 'cult_following', 'consensus']:
        min_val = df[col].min()
        max_val = df[col].max()
        df[f'norm_{col}'] = (df[col] - min_val) / (max_val - min_val + 1e-8)

    # 🧠 Composite Classic Score
    df['classic_score'] = (
        0.55 * df['norm_quality'] + #55%
        0.20 * df['norm_popularity'] + #20%
        0.10 * df['norm_cult_following'] + #10%
        0.15 * df['norm_consensus'] #15%
    )

    # ❌ Remove classic score if too few votes
    df.loc[df['Votes'] < 10, 'classic_score'] = np.nan

    return df

print(f"📂 Loading: {input_csv}")
df = pd.read_csv(input_csv)

df = compute_climbing_metrics(df)

# 🔽 Sort by classic_score, highest first
df = df.sort_values(by="classic_score", ascending=False)

df.to_csv(output_csv, index=False)
print(f"✅ Saved (sorted by classic_score): {output_csv}")


print(f"📂 Loading: {input_csv}")
df = pd.read_csv(input_csv)

# ✅ Apply filters (≥50 votes, ≥3.0 stars, ≥100 ticks)
df_filtered = df[
    (df['Votes'] >= 5) &
    (df['Stars'] >= 2.0) &
    (df['Ticks'] >= 10)
].copy()

# 🧮 Compute climbing metrics on the filtered set
df_filtered = compute_climbing_metrics(df_filtered)

# 💾 Save all filtered routes
filtered_all_csv = r"C:\Users\harve\Documents\Projects\MP-routes-Python\outputs\routes_filtered_all.csv"
df_filtered.to_csv(filtered_all_csv, index=False)
print(f"✅ Saved all filtered routes: {filtered_all_csv}")

# 🔽 Sort by classic_score, highest first
df_filtered = df_filtered.sort_values(by="classic_score", ascending=False)

# 🏆 Keep only the top 100 and add rank
df_top100 = df_filtered.head(100).copy()
df_top100.insert(0, "Rank", range(1, len(df_top100) + 1))

# 💾 Save Top 100
df_top100.to_csv(output_csv, index=False)
print(f"✅ Saved Top 100 filtered routes (with rank): {output_csv}")

# 💾 Save Top 10
#df_top100.to_csv(output_csv, index=False)
#print(f"✅ Saved Top 10 filtered routes (with rank): {output_csv}")
