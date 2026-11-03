#!/usr/bin/env python3
"""
tables.py  –  Generate LaTeX and Markdown tables from EcoSort v2 analysis CSVs
All numbers come directly from CSVs — never hand-edited.
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

def load(results_dir):
    base = os.path.join(results_dir, 'analysis')
    summary  = pd.read_csv(os.path.join(base, 'summary.csv'))
    speedup  = pd.read_csv(os.path.join(base, 'speedup_table.csv'))
    losses   = pd.read_csv(os.path.join(base, 'losses.csv'))
    return summary, speedup, losses

def fmt_ns(v):
    if v < 1000:    return f'{v:.0f} ns'
    if v < 1e6:     return f'{v/1000:.1f} µs'
    if v < 1e9:     return f'{v/1e6:.1f} ms'
    return f'{v/1e9:.2f} s'

def speedup_table_latex(speedup_df, type_='int32', n=100000, out_file=None):
    sub = speedup_df[(speedup_df['type'] == type_) & (speedup_df['n'] == n)].copy()
    if sub.empty:
        print(f"No data for type={type_} n={n}", file=sys.stderr)
        return
    pivot = sub.pivot_table(index='workload', columns='baseline',
                             values='speedup_median', aggfunc='first')
    pivot = pivot.round(3)

    lines = []
    lines.append(r'\begin{table}[h]\centering')
    lines.append(r'\caption{Enesort speedup (baseline time / Enesort time), '
                 + f'n={n}, type={type_}. Values $>1$ mean Enesort is faster.}}')
    cols = pivot.columns.tolist()
    lines.append(r'\begin{tabular}{l' + 'r' * len(cols) + '}')
    lines.append(r'\toprule')
    lines.append('Workload & ' + ' & '.join(cols) + r' \\')
    lines.append(r'\midrule')
    for wload, row in pivot.iterrows():
        vals = []
        for col in cols:
            v = row[col]
            if np.isnan(v): vals.append('--')
            elif v < 0.95:  vals.append(r'\textcolor{red}{' + f'{v:.3f}' + '}')
            elif v > 1.05:  vals.append(r'\textbf{' + f'{v:.3f}' + '}')
            else:           vals.append(f'{v:.3f}')
        lines.append(wload.replace('_', r'\_') + ' & ' + ' & '.join(vals) + r' \\')
    lines.append(r'\bottomrule')
    lines.append(r'\end{tabular}\end{table}')

    text = '\n'.join(lines)
    if out_file:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"  LaTeX table -> {out_file}")
    else:
        print(text)

def df_to_markdown(df):
    cols = df.columns.tolist()
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join([header, sep] + rows)

def losses_markdown(losses_df, out_file=None):
    if losses_df.empty:
        md = "## Enesort Losses\n\nNone — Enesort is within 5% of all baselines.\n"
    else:
        cols = ['baseline','workload','n','type','speedup_median','speedup_ci_lo','speedup_ci_hi']
        available = [c for c in cols if c in losses_df.columns]
        md = "## Enesort Losses (slower than baseline by >5%)\n\n"
        md += df_to_markdown(losses_df[available].sort_values('speedup_median'))
        md += "\n\n*speedup_median = baseline_time / enesort_time; values <1.0 mean Enesort is slower.*\n"
    if out_file:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"  Losses table -> {out_file}")
    else:
        print(md)

def summary_markdown(summary_df, type_='int32', n=100000, out_file=None):
    sub = summary_df[(summary_df['type'] == type_) & (summary_df['n'] == n)].copy()
    sub = sub.sort_values(['workload','algorithm'])
    sub['median_str'] = sub['median_ns'].apply(fmt_ns)
    sub['iqr_str']    = sub['iqr_ns'].apply(fmt_ns)
    sub['ci_str']     = sub.apply(
        lambda r: f"[{fmt_ns(r['ci_lo_ns'])}, {fmt_ns(r['ci_hi_ns'])}]", axis=1)
    tbl = sub[['workload','algorithm','median_str','iqr_str','ci_str','n_trials']]
    tbl.columns = ['Workload','Algorithm','Median','IQR','95% CI','Trials']
    md = f"## Sort Performance Summary (type={type_}, n={n})\n\n"
    md += df_to_markdown(tbl)
    md += "\n"
    if out_file:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"  Summary table -> {out_file}")
    else:
        print(md)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--results-dir', default='results')
    parser.add_argument('--output-dir',  default='results/tables')
    parser.add_argument('--type',        default='int32')
    parser.add_argument('--n',  type=int, default=100000)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    summary, speedup, losses = load(args.results_dir)

    speedup_table_latex(speedup, type_=args.type, n=args.n,
                        out_file=os.path.join(args.output_dir, 'speedup_table.tex'))
    losses_markdown(losses,
                    out_file=os.path.join(args.output_dir, 'losses.md'))
    summary_markdown(summary, type_=args.type, n=args.n,
                     out_file=os.path.join(args.output_dir, 'summary.md'))

if __name__ == '__main__':
    main()

