#!/usr/bin/env python3
"""
plots.py  â€“  Publication-quality plots for EcoSort v2 benchmark results
Generates vector PDFs in results/figures/
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
FIGSIZE_WIDE = (12, 6)
FIGSIZE_SQUARE = (8, 8)
ALGO_COLORS = {
    'enesort':       '#e41a1c',
    'ecosort_v2':    '#e41a1c',
    'ecosort_v1':    '#ff7f00',
    'std_sort':      '#377eb8',
    'stable_sort':   '#4daf4a',
    'std_precheck':  '#984ea3',
    'heapsort':      '#a65628',
    'mo3_quicksort': '#f781bf',
    'yaroslavskiy':  '#999999',
    'mergesort':     '#66c2a5',
    'pdqsort':       '#fc8d62',
    'ips4o':         '#8da0cb',
    'timsort':       '#e78ac3',
}

def algo_color(name):
    for k, v in ALGO_COLORS.items():
        if k in name: return v
    return '#333333'

def algo_label(name):
    labels = {
        'enesort': 'Enesort',
        'ecosort_v2': 'Enesort',
        'ecosort_v1': 'EcoSort v1',
        'std_sort': 'std::sort',
        'stable_sort': 'std::stable_sort',
        'std_precheck': 'std::sort+precheck',
        'heapsort': 'HeapSort',
        'mo3_quicksort': 'MO3-QSort',
        'yaroslavskiy': 'Yaroslavskiy DPQS',
        'mergesort': 'MergeSort',
        'pdqsort': 'pdqsort',
        'ips4o': 'IPSâ´o',
        'timsort': 'Timsort',
    }
    return labels.get(name, name)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def save_fig_both(fig, fname):
    fig.savefig(fname, bbox_inches='tight')
    png_name = fname.replace('.pdf', '.png')
    fig.savefig(png_name, bbox_inches='tight', dpi=300)
def load_summary(results_dir):
    p = os.path.join(results_dir, 'analysis', 'summary.csv')
    if not os.path.exists(p):
        print(f"summary.csv not found at {p} â€“ run analyze.py first", file=sys.stderr)
        sys.exit(1)
    return pd.read_csv(p)

def load_speedup(results_dir):
    p = os.path.join(results_dir, 'analysis', 'speedup_table.csv')
    if not os.path.exists(p):
        return None
    return pd.read_csv(p)

# ---------------------------------------------------------------------------
# Plot 1: log-log time vs N per workload (with CI bands)
# ---------------------------------------------------------------------------
def plot_time_vs_n(df, fig_dir, type_='int32', workloads=None):
    algos = df['algorithm'].unique()
    if workloads is None:
        workloads = df['workload'].unique()

    for wload in workloads:
        sub = df[(df['workload'] == wload) & (df['type'] == type_)]
        if sub.empty:
            continue
        fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
        for algo in sorted(algos):
            adf = sub[sub['algorithm'] == algo].sort_values('n')
            if adf.empty: continue
            ns = adf['n'].values
            med = adf['median_ns'].values
            lo  = adf['ci_lo_ns'].values
            hi  = adf['ci_hi_ns'].values
            lw = 2.5 if algo in ('enesort', 'ecosort_v2') else 1.2
            ls = '-'  if algo in ('enesort', 'ecosort_v2') else '--'
            ax.plot(ns, med, label=algo_label(algo), color=algo_color(algo),
                    linewidth=lw, linestyle=ls, marker='o', markersize=4)
            ax.fill_between(ns, lo, hi, alpha=0.15, color=algo_color(algo))
        ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_xlabel('Array size (n)', fontsize=12)
        ax.set_ylabel('Time (ns)', fontsize=12)
        ax.set_title(f'Sort time vs n  â€“  workload: {wload}  â€“  type: {type_}', fontsize=13)
        ax.legend(fontsize=8, ncol=3, loc='upper left')
        ax.grid(True, which='both', alpha=0.3)
        fname = os.path.join(fig_dir, f'time_vs_n_{wload}_{type_}.pdf')
        save_fig_both(fig, fname)
        plt.close(fig)
    print(f"  time_vs_n plots â†’ {fig_dir}")

# ---------------------------------------------------------------------------
# Plot 2: ns/element vs N
# ---------------------------------------------------------------------------
def plot_ns_per_elem(df, fig_dir, type_='int32', workloads=None):
    algos = df['algorithm'].unique()
    if workloads is None:
        workloads = df['workload'].unique()

    for wload in workloads:
        sub = df[(df['workload'] == wload) & (df['type'] == type_)]
        if sub.empty: continue
        fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
        for algo in sorted(algos):
            adf = sub[sub['algorithm'] == algo].sort_values('n')
            if adf.empty: continue
            ns  = adf['n'].values
            npe = adf['median_ns_per_elem'].values
            lw = 2.5 if algo in ('enesort', 'ecosort_v2') else 1.2
            ls = '-'  if algo in ('enesort', 'ecosort_v2') else '--'
            ax.plot(ns, npe, label=algo_label(algo), color=algo_color(algo),
                    linewidth=lw, linestyle=ls, marker='o', markersize=4)
        ax.set_xscale('log')
        ax.set_xlabel('Array size (n)', fontsize=12)
        ax.set_ylabel('ns / element', fontsize=12)
        ax.set_title(f'ns/element vs n  â€“  workload: {wload}  â€“  type: {type_}', fontsize=13)
        ax.legend(fontsize=8, ncol=3, loc='upper left')
        ax.grid(True, alpha=0.3)
        fname = os.path.join(fig_dir, f'ns_per_elem_{wload}_{type_}.pdf')
        save_fig_both(fig, fname)
        plt.close(fig)

# ---------------------------------------------------------------------------
# Plot 3: Heatmap â€“ speedup ratio vs best baseline, workload x size
# ---------------------------------------------------------------------------
def plot_speedup_heatmap(speedup_df, fig_dir, type_='int32'):
    if speedup_df is None or speedup_df.empty:
        return
    sub = speedup_df[speedup_df['type'] == type_]
    if sub.empty: return

    # For each (workload, n), take the minimum speedup across baselines
    # (most conservative: if Enesort beats ALL baselines in this cell)
    pivot_min = sub.groupby(['workload','n'])['speedup_median'].min().reset_index()
    workloads = sorted(pivot_min['workload'].unique())
    sizes     = sorted(pivot_min['n'].unique())

    mat = np.full((len(workloads), len(sizes)), np.nan)
    for _, row in pivot_min.iterrows():
        wi = workloads.index(row['workload'])
        si = sizes.index(row['n'])
        mat[wi, si] = row['speedup_median']

    fig, ax = plt.subplots(figsize=(max(8, len(sizes)*1.2), max(6, len(workloads)*0.4)))
    im = ax.imshow(mat, aspect='auto', cmap='RdYlGn',
                   vmin=0.5, vmax=2.0)
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([str(s) for s in sizes], rotation=45, ha='right')
    ax.set_yticks(range(len(workloads)))
    ax.set_yticklabels(workloads, fontsize=8)
    ax.set_xlabel('Array size', fontsize=11)
    ax.set_title(f'Enesort speedup vs best baseline  â€“  type: {type_}\n'
                 f'(green > 1 = Enesort wins; red < 1 = Enesort loses)', fontsize=11)
    # Annotate cells
    for i in range(len(workloads)):
        for j in range(len(sizes)):
            v = mat[i, j]
            if not np.isnan(v):
                ax.text(j, i, f'{v:.2f}', ha='center', va='center',
                        fontsize=7, color='black')
    cbar = fig.colorbar(im, ax=ax, fraction=0.02)
    cbar.set_label('Speedup (baseline/Enesort)', fontsize=9)
    fname = os.path.join(fig_dir, f'speedup_heatmap_{type_}.pdf')
    save_fig_both(fig, fname)
    plt.close(fig)
    print(f"  speedup heatmap â†’ {fname}")

# ---------------------------------------------------------------------------
# Plot 4: Ablation bar charts
# ---------------------------------------------------------------------------
def plot_ablation(df, fig_dir, workload='uniform_random', n=100000, type_='int32'):
    ablation_algos = [a for a in df['algorithm'].unique()
                      if 'ablation' in a or (a.startswith('enesort') or a.startswith('ecosort'))]
    sub = df[(df['workload'] == workload) & (df['n'] == n) & (df['type'] == type_)
             & (df['algorithm'].isin(ablation_algos))]
    if sub.empty: return
    fig, ax = plt.subplots(figsize=(10, 5))
    names  = sub['algorithm'].values
    medians = sub['median_ns'].values / 1e6  # ms
    ci_lo  = sub['ci_lo_ns'].values / 1e6
    ci_hi  = sub['ci_hi_ns'].values / 1e6
    yerr_lo = medians - ci_lo
    yerr_hi = ci_hi - medians
    colors = [algo_color(n) for n in names]
    ax.bar(range(len(names)), medians, color=colors, alpha=0.8,
           yerr=[yerr_lo, yerr_hi], capsize=4)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=30, ha='right', fontsize=9)
    ax.set_ylabel('Median time (ms)', fontsize=11)
    ax.set_title(f'Ablation study â€“ workload: {workload}, n={n}, type: {type_}', fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    fname = os.path.join(fig_dir, f'ablation_{workload}_n{n}_{type_}.pdf')
    save_fig_both(fig, fname)
    plt.close(fig)
    print(f"  ablation bar chart â†’ {fname}")

def plot_cutoff_sweep(df, fig_dir, type_='int32'):
    cutoff_algos = [a for a in df['algorithm'].unique() if 'cutoff' in a]
    if not cutoff_algos: return
    def get_k(name):
        try: return int(name.split('_')[-1])
        except: return 0
    workloads = ['uniform_random', 'sorted_append_100', 'few_distinct_10']
    for w in workloads:
        sub = df[(df['workload'] == w) & (df['type'] == type_) & (df['algorithm'].isin(cutoff_algos))]
        if sub.empty: continue
        fig, ax = plt.subplots(figsize=(8, 5))
        for n in sorted(sub['n'].unique()):
            nsub = sub[sub['n'] == n].copy()
            nsub['cutoff'] = nsub['algorithm'].apply(get_k)
            nsub = nsub.sort_values('cutoff')
            ax.plot(nsub['cutoff'], nsub['median_ns'] / 1e6, marker='o', label=f'N={n:,}')
        ax.set_xlabel('Insertion Cutoff Threshold', fontsize=11)
        ax.set_ylabel('Median Time (ms)', fontsize=11)
        ax.set_title(f'Insertion Cutoff Sweep - Workload: {w}', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        fname = os.path.join(fig_dir, f'cutoff_sweep_{w}_{type_}.pdf')
        save_fig_both(fig, fname)
        plt.close(fig)
        print(f"  cutoff sweep plot -> {fname}")

def plot_pivot_study(df, fig_dir, type_='int32'):
    sample_algos = [a for a in df['algorithm'].unique() if 'sample' in a]
    if not sample_algos: return
    sub = df[(df['algorithm'].isin(sample_algos)) & (df['type'] == type_)]
    for w in sub['workload'].unique():
        wsub = sub[sub['workload'] == w]
        if wsub.empty: continue
        fig, ax = plt.subplots(figsize=(8, 5))
        for n in sorted(wsub['n'].unique()):
            nsub = wsub[wsub['n'] == n].sort_values('algorithm')
            ax.plot(nsub['algorithm'], nsub['median_ns'] / 1e6, marker='s', label=f'N={n:,}')
        ax.set_xlabel('Sampling Scheme', fontsize=11)
        ax.set_ylabel('Median Time (ms)', fontsize=11)
        ax.set_title(f'Pivot-Sampling & Skew Study - Workload: {w}', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=20, ha='right')
        fname = os.path.join(fig_dir, f'pivot_study_{w}_{type_}.pdf')
        save_fig_both(fig, fname)
        plt.close(fig)
        print(f"  pivot study plot -> {fname}")

def plot_counters(counters_csv, fig_dir):
    if not os.path.exists(counters_csv): return
    cdf = pd.read_csv(counters_csv)
    if cdf.empty: return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    summary = cdf.groupby(['algorithm', 'workload'])[['cmps_per_elem', 'swaps_per_elem']].median().reset_index()
    workloads = summary['workload'].unique()
    x = np.arange(len(workloads))
    width = 0.35
    v2_sub = summary[summary['algorithm'].isin(['enesort', 'ecosort_v2'])]
    if not v2_sub.empty:
        ax1.bar(x, v2_sub['cmps_per_elem'], width, label='Enesort', color='#e41a1c')
        ax1.set_xticks(x)
        ax1.set_xticklabels(workloads, rotation=30, ha='right')
        ax1.set_ylabel('Comparisons / Element', fontsize=11)
        ax1.set_title('Exact Comparisons per Element', fontsize=12)
        ax1.grid(axis='y', alpha=0.3)

        ax2.bar(x, v2_sub['swaps_per_elem'], width, label='Enesort', color='#377eb8')
        ax2.set_xticks(x)
        ax2.set_xticklabels(workloads, rotation=30, ha='right')
        ax2.set_ylabel('Swaps / Element', fontsize=11)
        ax2.set_title('Exact Swaps per Element', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        fname = os.path.join(fig_dir, 'counter_study_per_element.pdf')
        save_fig_both(fig, fname)
        plt.close(fig)
        print(f"  counter study plot -> {fname}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='EcoSort v2 plots')
    parser.add_argument('--results-dir', default='results')
    parser.add_argument('--fig-dir', default='results/figures')
    parser.add_argument('--type', default='int32')
    args = parser.parse_args()

    os.makedirs(args.fig_dir, exist_ok=True)
    df = load_summary(args.results_dir)
    speedup_df = load_speedup(args.results_dir)

    # Key workloads to plot (subset for clarity)
    key_workloads = ['uniform_random', 'ascending', 'descending', 'few_distinct_10',
                     'organ_pipe', 'all_equal', 'nearly_sorted_10', 'sorted_append_100']
    available_workloads = [w for w in key_workloads if w in df['workload'].unique()]

    print("Generating time vs N plots...")
    plot_time_vs_n(df, args.fig_dir, type_=args.type, workloads=available_workloads)

    print("Generating ns/element plots...")
    plot_ns_per_elem(df, args.fig_dir, type_=args.type, workloads=available_workloads)

    print("Generating speedup heatmap...")
    plot_speedup_heatmap(speedup_df, args.fig_dir, type_=args.type)

    print("Generating ablation charts...")
    for wload in ['uniform_random', 'few_distinct_10']:
        for n in [100000]:
            plot_ablation(df, args.fig_dir, workload=wload, n=n, type_=args.type)

    print("Generating cutoff sweep plots...")
    plot_cutoff_sweep(df, args.fig_dir, type_=args.type)

    print("Generating pivot study plots...")
    plot_pivot_study(df, args.fig_dir, type_=args.type)

    print("Generating counter study plots...")
    counters_path = os.path.join(args.results_dir, 'raw', 'study6_counters.csv')
    plot_counters(counters_path, args.fig_dir)

    print(f"All figures written to {args.fig_dir}")

if __name__ == '__main__':
    main()


