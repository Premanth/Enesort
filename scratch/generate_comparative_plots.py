import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

FIG_DIR = 'results/figures'
os.makedirs(FIG_DIR, exist_ok=True)

# Style configuration
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8

ALGO_COLORS = {
    'enesort':       '#d73027', # Bright red/crimson
    'std_sort':      '#4575b4', # Blue
    'pdqsort':       '#fc8d59', # Orange
    'ips4o':         '#91bfdb', # Light blue
    'timsort':       '#9970ab', # Purple
    'mergesort':     '#7fbf7b', # Soft green
    'heapsort':      '#fee090', # Sand/yellow
    'mo3_quicksort': '#e7d4e8', # Violet
    'yaroslavskiy':  '#8073ac', # Deep purple
}

ALGO_LABELS = {
    'enesort':       'Enesort (Ours)',
    'std_sort':      'std::sort',
    'pdqsort':       'pdqsort',
    'ips4o':         'IPS4o',
    'timsort':       'TimSort',
    'mergesort':     'MergeSort',
    'heapsort':      'HeapSort',
    'mo3_quicksort': 'MO3-QSort',
    'yaroslavskiy':  'Yaroslavskiy DPQS',
}

summary_path = 'results/analysis/summary.csv'
df = pd.read_csv(summary_path)

# -------------------------------------------------------------
# 1. Multi-Baseline Comparison Grouped Bar Chart (N=100,000, int32)
# -------------------------------------------------------------
algos = ['enesort', 'std_sort', 'pdqsort', 'ips4o', 'timsort', 'mergesort', 'heapsort', 'mo3_quicksort', 'yaroslavskiy']
wloads = ['uniform_random', 'ascending', 'descending', 'all_equal', 'few_distinct_10', 'organ_pipe', 'median_of_3_killer', 'sorted_append_100']
wload_labels = ['Uniform\nRandom', 'Ascending', 'Descending', 'All\nEqual', 'Few Dist.\n(10 keys)', 'Organ\nPipe', 'MO3\nKiller', 'Sorted +\nAppend 100']

sub = df[(df['n']==100000) & (df['type']=='int32') & (df['algorithm'].isin(algos)) & (df['workload'].isin(wloads))]
pivot = sub.pivot(index='workload', columns='algorithm', values='median_ns') / 1e6 # ms
pivot = pivot.reindex(wloads)[algos]

fig, ax = plt.subplots(figsize=(15, 6), dpi=300)
x = np.arange(len(wloads))
total_width = 0.85
bar_width = total_width / len(algos)

for i, algo in enumerate(algos):
    offset = (i - len(algos)/2 + 0.5) * bar_width
    vals = pivot[algo].values
    edgecolor = 'black' if algo == 'enesort' else 'none'
    linewidth = 1.2 if algo == 'enesort' else 0
    rects = ax.bar(x + offset, vals, bar_width, label=ALGO_LABELS[algo], 
                   color=ALGO_COLORS[algo], edgecolor=edgecolor, linewidth=linewidth, alpha=0.92)

ax.set_ylabel('Execution Time (ms) [Log Scale]', fontsize=12, fontweight='bold')
ax.set_yscale('log')
ax.set_title('Comparative Benchmark: Enesort vs. 8 Baselines (N = 100,000, 32-bit Integers)', fontsize=14, fontweight='bold', pad=12)
ax.set_xticks(x)
ax.set_xticklabels(wload_labels, fontsize=10)
ax.grid(axis='y', which='both', linestyle='--', alpha=0.4)
ax.legend(loc='upper right', bbox_to_anchor=(1.0, 1.0), ncol=3, frameon=True, fontsize=9)
plt.tight_layout()

for ext in ['png', 'pdf']:
    out = os.path.join(FIG_DIR, f'baseline_comparison_barchart_n100000.{ext}')
    fig.savefig(out, bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated baseline_comparison_barchart_n100000")

# -------------------------------------------------------------
# 2. Comprehensive Speedup Overview Across ALL 20 Workloads (N=100,000)
# -------------------------------------------------------------
sub20 = df[(df['n']==100000) & (df['type']=='int32') & (df['algorithm'].isin(['enesort', 'std_sort']))]
p20 = sub20.pivot(index='workload', columns='algorithm', values='median_ns')
p20['speedup'] = p20['std_sort'] / p20['enesort']
p20 = p20.sort_values('speedup', ascending=True)

fig, ax = plt.subplots(figsize=(11, 8), dpi=300)
y_pos = np.arange(len(p20))
colors = ['#2ca02c' if s >= 1.0 else '#d62728' for s in p20['speedup']]

bars = ax.barh(y_pos, p20['speedup'], color=colors, alpha=0.85, edgecolor='black', height=0.65)
ax.axvline(1.0, color='black', linestyle='--', linewidth=1.2, label='std::sort Parity (1.0x)')

for idx, (s, w) in enumerate(zip(p20['speedup'], p20.index)):
    txt = f"{s:.2f}x"
    if s >= 1.0:
        ax.text(s + 0.15, idx, txt, va='center', ha='left', fontsize=8.5, fontweight='bold', color='#1b7837')
    else:
        ax.text(s + 0.05, idx, txt, va='center', ha='left', fontsize=8.5, fontweight='bold', color='#b2182b')

ax.set_yticks(y_pos)
ax.set_yticklabels(p20.index, fontsize=10)
ax.set_xlabel('Speedup Ratio: Time(std::sort) / Time(Enesort) [>1.0x indicates Enesort is faster]', fontsize=11, fontweight='bold')
ax.set_title('Empirical Speedup of Enesort relative to std::sort Across All 20 Workloads (N = 100,000)', fontsize=13, fontweight='bold', pad=10)
ax.set_xlim(0, max(p20['speedup']) * 1.1)
ax.grid(axis='x', linestyle=':', alpha=0.5)
ax.legend(loc='lower right', frameon=True)
plt.tight_layout()

for ext in ['png', 'pdf']:
    out = os.path.join(FIG_DIR, f'speedup_overview_all_workloads_n100000.{ext}')
    fig.savefig(out, bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated speedup_overview_all_workloads_n100000")

# -------------------------------------------------------------
# 3. Runtime vs. Auxiliary Dynamic Heap Memory Pareto Chart (N=100,000)
# -------------------------------------------------------------
mem_kb = {
    'enesort': 0.0,
    'std_sort': 0.0,
    'pdqsort': 0.0,
    'heapsort': 0.0,
    'mo3_quicksort': 0.0,
    'yaroslavskiy': 0.0,
    'timsort': 400.0,
    'mergesort': 400.0,
    'ips4o': 400.0,
}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

for ax, wload, title in [(ax1, 'uniform_random', 'Uniform Random (N=100,000)'), 
                         (ax2, 'organ_pipe', 'Organ Pipe (N=100,000)')]:
    wsub = df[(df['n']==100000) & (df['type']=='int32') & (df['workload']==wload) & (df['algorithm'].isin(algos))]
    for _, row in wsub.iterrows():
        algo = row['algorithm']
        time_ms = row['median_ns'] / 1e6
        mem = mem_kb.get(algo, 0.0)
        c = ALGO_COLORS.get(algo, '#333333')
        marker = '*' if algo == 'enesort' else ('o' if mem == 0 else 's')
        size = 240 if algo == 'enesort' else 110
        ax.scatter(mem, time_ms, color=c, s=size, marker=marker, edgecolors='black', linewidth=1.2, zorder=5)
        y_off = 0.20 if algo in ['mo3_quicksort', 'timsort'] else (-0.30 if algo in ['std_sort', 'mergesort'] else 0.0)
        x_off = 10 if mem > 0 else (12 if algo != 'enesort' else 15)
        ax.annotate(f"{ALGO_LABELS[algo]} ({time_ms:.2f} ms)", (mem, time_ms),
                    xytext=(mem + x_off, time_ms + y_off),
                    fontsize=8.5, fontweight='bold' if algo == 'enesort' else 'normal',
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.7, edgecolor='#aaaaaa', linewidth=0.5))

    ax.set_xlabel('Auxiliary Dynamic Heap Memory (KB)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Execution Time (ms)', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_xlim(-30, 500)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.axvspan(-25, 25, color='#e0f3f8', alpha=0.4, label='In-Place (0 KB Heap)')

ax1.legend(loc='upper right', frameon=True, fontsize=9)
ax2.legend(loc='upper right', frameon=True, fontsize=9)
plt.suptitle('Pareto Efficiency: Execution Time vs. Auxiliary Dynamic Heap Footprint', fontsize=14, fontweight='bold', y=0.98)
plt.tight_layout()

for ext in ['png', 'pdf']:
    out = os.path.join(FIG_DIR, f'runtime_vs_memory_pareto_n100000.{ext}')
    fig.savefig(out, bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated runtime_vs_memory_pareto_n100000")

# -------------------------------------------------------------
# 4. Speedup vs. pdqsort across all workloads (N=100,000)
# -------------------------------------------------------------
sub_pdq = df[(df['n']==100000) & (df['type']=='int32') & (df['algorithm'].isin(['enesort', 'pdqsort']))]
ppdq = sub_pdq.pivot(index='workload', columns='algorithm', values='median_ns')
ppdq['speedup'] = ppdq['pdqsort'] / ppdq['enesort']
ppdq = ppdq.sort_values('speedup', ascending=True)

fig, ax = plt.subplots(figsize=(11, 7), dpi=300)
y_pos = np.arange(len(ppdq))
colors = ['#2ca02c' if s >= 1.0 else '#d62728' for s in ppdq['speedup']]

bars = ax.barh(y_pos, ppdq['speedup'], color=colors, alpha=0.85, edgecolor='black', height=0.65)
ax.axvline(1.0, color='black', linestyle='--', linewidth=1.2, label='pdqsort Parity (1.0x)')

for idx, (s, w) in enumerate(zip(ppdq['speedup'], ppdq.index)):
    txt = f"{s:.2f}x"
    ax.text(s + (0.1 if s>=1.0 else 0.05), idx, txt, va='center', ha='left', fontsize=8.5, fontweight='bold',
            color='#1b7837' if s>=1.0 else '#b2182b')

ax.set_yticks(y_pos)
ax.set_yticklabels(ppdq.index, fontsize=10)
ax.set_xlabel('Speedup Ratio: Time(pdqsort) / Time(Enesort) [>1.0x indicates Enesort is faster]', fontsize=11, fontweight='bold')
ax.set_title('Speedup of Enesort relative to pdqsort (State-of-the-Art Quicksort) at N = 100,000', fontsize=13, fontweight='bold', pad=10)
ax.set_xlim(0, max(ppdq['speedup']) * 1.1)
ax.grid(axis='x', linestyle=':', alpha=0.5)
ax.legend(loc='lower right', frameon=True)
plt.tight_layout()

for ext in ['png', 'pdf']:
    out = os.path.join(FIG_DIR, f'speedup_vs_pdqsort_n100000.{ext}')
    fig.savefig(out, bbox_inches='tight', dpi=300)
plt.close(fig)
print("Generated speedup_vs_pdqsort_n100000")

