#!/usr/bin/env python3
"""
analyze.py  –  Statistical analysis of EcoSort v2 benchmark results
Reads all CSVs in results/raw/, computes:
  - Median, IQR, bootstrap 95% CI per cell
  - Pairwise Wilcoxon signed-rank tests vs best baseline (Holm correction)
  - Speedup ratios (baseline_time / ecosort_time)
Outputs: results/analysis/summary.csv, speedup_table.csv, losses.csv
"""

import argparse
import glob
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from itertools import combinations

# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------
def bootstrap_ci(data, stat=np.median, n_boot=10000, ci=0.95):
    """Return (lower, upper) bootstrap CI for `stat` of `data`."""
    if len(data) < 2:
        v = stat(data) if len(data) == 1 else np.nan
        return v, v
    rng = np.random.default_rng(42)
    resamples = rng.choice(data, size=(n_boot, len(data)), replace=True)
    if stat is np.median or stat == np.median:
        boot = np.median(resamples, axis=1)
    elif stat is np.mean or stat == np.mean:
        boot = np.mean(resamples, axis=1)
    else:
        boot = np.apply_along_axis(stat, 1, resamples)
    alpha = (1 - ci) / 2
    return np.percentile(boot, alpha*100), np.percentile(boot, (1-alpha)*100)

# ---------------------------------------------------------------------------
# Load and clean data
# ---------------------------------------------------------------------------
def load_data(results_dir: str) -> pd.DataFrame:
    pattern = os.path.join(results_dir, "raw", "*.csv")
    files = glob.glob(pattern)
    if not files:
        print(f"No CSV files found in {pattern}", file=sys.stderr)
        sys.exit(1)
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, encoding='utf-8')
            dfs.append(df)
        except Exception:
            try:
                df = pd.read_csv(f, encoding='utf-16')
                dfs.append(df)
            except Exception as e:
                print(f"Warning: could not read {f}: {e}", file=sys.stderr)
    df = pd.concat(dfs, ignore_index=True)
    # Filter failed / timed-out rows
    df['time_ns'] = pd.to_numeric(df['time_ns'], errors='coerce')
    df = df[df['time_ns'] > 0]
    df = df[df['sorted_ok'] == 1]
    df = df[df['multiset_ok'] == 1]
    return df

# ---------------------------------------------------------------------------
# Per-cell statistics
# ---------------------------------------------------------------------------
def cell_stats(df: pd.DataFrame) -> pd.DataFrame:
    groups = ['algorithm', 'workload', 'n', 'type']
    rows = []
    for key, grp in df.groupby(groups):
        times = grp['time_ns'].values
        median = np.median(times)
        q1, q3 = np.percentile(times, [25, 75])
        iqr = q3 - q1
        ci_lo, ci_hi = bootstrap_ci(times)
        rows.append({
            'algorithm': key[0], 'workload': key[1], 'n': key[2], 'type': key[3],
            'n_trials': len(times),
            'median_ns': median, 'iqr_ns': iqr,
            'ci_lo_ns': ci_lo, 'ci_hi_ns': ci_hi,
            'median_ns_per_elem': median / max(key[2], 1),
        })
    return pd.DataFrame(rows)

# ---------------------------------------------------------------------------
# Speedup table: baseline_time / enesort_time
# ---------------------------------------------------------------------------
def compute_speedups(df: pd.DataFrame, target_algo='enesort') -> pd.DataFrame:
    if target_algo not in df['algorithm'].values and 'ecosort_v2' in df['algorithm'].values:
        target_algo = 'ecosort_v2'
    groups = ['workload', 'n', 'type']
    baselines = [a for a in df['algorithm'].unique() if a != target_algo and not a.startswith('enesort_') and not a.startswith('ecosort_')]
    rows = []
    for key, grp in df.groupby(groups):
        eco_times = grp[grp['algorithm'] == target_algo]['time_ns'].values
        if len(eco_times) == 0:
            continue
        for bl in baselines:
            bl_times = grp[grp['algorithm'] == bl]['time_ns'].values
            if len(bl_times) == 0:
                continue
            # Pair by trial index (same seed)
            n_pairs = min(len(eco_times), len(bl_times))
            eco_paired = eco_times[:n_pairs]
            bl_paired  = bl_times[:n_pairs]
            ratio_median = np.median(bl_paired) / np.median(eco_paired)
            # Wilcoxon signed-rank test (paired)
            try:
                stat, pval = stats.wilcoxon(bl_paired, eco_paired)
            except ValueError:
                stat, pval = np.nan, np.nan
            # Effect size: median ratio with CI
            ratios = bl_paired / eco_paired
            ratio_ci_lo, ratio_ci_hi = bootstrap_ci(ratios)
            rows.append({
                'baseline': bl, 'workload': key[0], 'n': key[1], 'type': key[2],
                'speedup_median': ratio_median,
                'speedup_ci_lo': ratio_ci_lo, 'speedup_ci_hi': ratio_ci_hi,
                'wilcoxon_stat': stat, 'wilcoxon_p': pval,
                'n_pairs': n_pairs,
            })
    sdf = pd.DataFrame(rows)
    # Holm correction per baseline
    if len(sdf) > 0 and 'wilcoxon_p' in sdf.columns:
        from scipy.stats import false_discovery_control
        for bl, bgrp in sdf.groupby('baseline'):
            idx = bgrp.index
            pvals = bgrp['wilcoxon_p'].fillna(1.0).values
            # Holm correction
            sorted_idx = np.argsort(pvals)
            holm_p = np.ones(len(pvals))
            m = len(pvals)
            for rank, si in enumerate(sorted_idx):
                holm_p[si] = min(1.0, pvals[si] * (m - rank))
            sdf.loc[idx, 'wilcoxon_p_holm'] = holm_p
    return sdf

# ---------------------------------------------------------------------------
# Losses table: cells where EcoSort is slower than ANY baseline by >5%
# ---------------------------------------------------------------------------
def find_losses(speedup_df: pd.DataFrame, threshold=0.95) -> pd.DataFrame:
    """speedup < threshold means EcoSort is slower by > (1/threshold - 1)*100%"""
    losses = speedup_df[speedup_df['speedup_median'] < threshold].copy()
    losses = losses.sort_values('speedup_median')
    return losses

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="EcoSort v2 analysis")
    parser.add_argument('--results-dir', default='results', help='Root results directory')
    parser.add_argument('--output-dir', default='results/analysis')
    parser.add_argument('--target-algo', '--ecosort-algo', dest='target_algo', default='enesort')
    parser.add_argument('--n-boot', type=int, default=10000)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("Loading data...")
    df = load_data(args.results_dir)
    print(f"  Loaded {len(df)} rows, {df['algorithm'].nunique()} algorithms, "
          f"{df['workload'].nunique()} workloads")

    print("Computing cell statistics...")
    stats_df = cell_stats(df)
    stats_df.to_csv(os.path.join(args.output_dir, 'summary.csv'), index=False)
    print(f"  Written {len(stats_df)} rows to summary.csv")

    print("Computing speedups...")
    speedup_df = compute_speedups(df, args.target_algo)
    speedup_df.to_csv(os.path.join(args.output_dir, 'speedup_table.csv'), index=False)
    print(f"  Written {len(speedup_df)} rows to speedup_table.csv")

    print(f"Finding losses ({args.target_algo} > 5% slower than any baseline)...")
    losses_df = find_losses(speedup_df, threshold=0.95)
    losses_df.to_csv(os.path.join(args.output_dir, 'losses.csv'), index=False)
    print(f"  Found {len(losses_df)} loss cells (written to losses.csv)")

    # Quick summary to stdout
    print(f"\n=== TOP SPEEDUPS ({args.target_algo} vs best baseline, median) ===")
    if len(speedup_df) > 0:
        top = speedup_df.nlargest(10, 'speedup_median')[
            ['baseline','workload','n','type','speedup_median','wilcoxon_p']]
        print(top.to_string(index=False))

    print("\n=== NOTABLE LOSSES ===")
    if len(losses_df) > 0:
        print(losses_df[['baseline','workload','n','type','speedup_median']].to_string(index=False))
    else:
        print("  None (EcoSort is within 5% of all baselines everywhere)")

if __name__ == '__main__':
    main()

