#!/usr/bin/env python3
"""
generate_results_summary.py  –  Auto-generate RESULTS_SUMMARY.md from CSVs.
All numbers come from the CSV files; never hand-edited.
"""

import os
import sys
import datetime
import numpy as np
import pandas as pd
from pathlib import Path

def df_to_markdown(df):
    cols = df.columns.tolist()
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([header, sep] + rows)

def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else 'results'
    analysis_dir = os.path.join(results_dir, 'analysis')

    if not os.path.exists(os.path.join(analysis_dir, 'summary.csv')):
        print("Run analyze.py first to generate summary.csv", file=sys.stderr)
        sys.exit(1)

    summary = pd.read_csv(os.path.join(analysis_dir, 'summary.csv'))
    speedup = pd.read_csv(os.path.join(analysis_dir, 'speedup_table.csv'))
    losses  = pd.read_csv(os.path.join(analysis_dir, 'losses.csv'))

    target_algo = 'enesort' if 'enesort' in summary['algorithm'].values else 'ecosort_v2'
    target_name = 'Enesort' if target_algo == 'enesort' else 'EcoSort v2'

    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    lines = [
        f"# {target_name} Results Summary",
        f"",
        f"*Auto-generated {ts} from raw CSVs in `results/raw/`. Do not edit.*",
        f"",
        f"## Overview",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total trial rows | {len(summary)} cells |",
        f"| Algorithms benchmarked | {summary['algorithm'].nunique()} |",
        f"| Workloads | {summary['workload'].nunique()} |",
        f"| Array sizes tested | {sorted(summary['n'].unique())} |",
        f"| Types tested | {sorted(summary['type'].unique())} |",
        f"",
    ]

    # Best speedups
    if len(speedup) > 0:
        top5 = speedup.nlargest(5, 'speedup_median')[
            ['baseline','workload','n','type','speedup_median']]
        lines.append(f"## Top 5 Speedups ({target_name} vs Baseline)")
        lines.append("")
        lines.append(df_to_markdown(top5.round(3)))
        lines.append("")
        lines.append(f"*speedup = baseline_time / {target_algo}_time. Values >1 mean {target_name} is faster.*")
        lines.append("")

    # Losses
    lines.append(f"## Losses ({target_name} slower than baseline by >5%)")
    lines.append("")
    if len(losses) == 0:
        lines.append(f"**None.** {target_name} is within 5% of all baselines on all tested cells.")
    else:
        cols = ['baseline','workload','n','type','speedup_median']
        available = [c for c in cols if c in losses.columns]
        lines.append(df_to_markdown(losses[available].sort_values('speedup_median').round(3)))
        lines.append("")
        lines.append("*These workloads/sizes deserve further investigation.*")
    lines.append("")

    # Per-type summary at n=100000
    for type_ in sorted(summary['type'].unique()):
        sub = summary[(summary['type'] == type_) & (summary['n'] == 100000)]
        if sub.empty: continue
        lines.append(f"## Performance at n=100,000  (type={type_})")
        lines.append("")
        eco = sub[sub['algorithm'] == target_algo]
        std = sub[sub['algorithm'] == 'std_sort']
        lines.append(f"| Workload | {target_name} (median) | std::sort (median) | Ratio |")
        lines.append("|----------|--------------------|--------------------|-------|")
        for wload in sorted(sub['workload'].unique()):
            e = sub[(sub['algorithm'] == target_algo) & (sub['workload'] == wload)]
            s = sub[(sub['algorithm'] == 'std_sort') & (sub['workload'] == wload)]
            if e.empty or s.empty: continue
            em, sm = e['median_ns'].values[0], s['median_ns'].values[0]
            ratio = sm / em if em > 0 else float('nan')
            def fmt(v):
                if v < 1e6: return f"{v/1e3:.1f} µs"
                return f"{v/1e6:.2f} ms"
            lines.append(f"| {wload} | {fmt(em)} | {fmt(sm)} | {ratio:.2f}x |")
        lines.append("")

    md = '\n'.join(lines)
    out_file = os.path.join(results_dir, 'RESULTS_SUMMARY.md')
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"Results summary written to {out_file}")

if __name__ == '__main__':
    main()
