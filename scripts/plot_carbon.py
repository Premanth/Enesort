#!/usr/bin/env python3
"""
plot_carbon.py – Generates publication-ready figures for Carbon Emissions and Energy
measured using CodeCarbon.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(PROJ_DIR, "results", "analysis", "carbon_summary.csv")
FIG_DIR = os.path.join(PROJ_DIR, "results", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Publication styling
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'figure.dpi': 300,
    'lines.linewidth': 1.5,
    'lines.markersize': 6
})

ALGO_COLORS = {
    "enesort": "#1b9e77",      # Green (EcoSort/Enesort)
    "std_sort": "#d95f02",     # Orange
    "pdqsort": "#7570b3",      # Purple
    "timsort": "#e7298a",      # Pink
    "mergesort": "#66a61e",    # Olive
    "heapsort": "#e6ab02",     # Yellow
    "mo3_quicksort": "#a6761d",# Brown
    "yaroslavskiy": "#666666"  # Gray
}

ALGO_LABELS = {
    "enesort": "Enesort (Ours)",
    "std_sort": "std::sort",
    "pdqsort": "pdqsort",
    "timsort": "TimSort",
    "mergesort": "MergeSort",
    "heapsort": "HeapSort",
    "mo3_quicksort": "MO3-QSort",
    "yaroslavskiy": "Yaroslavskiy"
}

def plot_pareto(df_100k):
    """Plot Pareto frontier of Carbon Emissions vs Runtime across algorithms."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    # Aggregate across workloads
    agg = df_100k.groupby("algorithm").agg({
        "avg_ms": "mean",
        "g_co2_per_million": "mean",
        "uj_per_elem": "mean"
    }).reset_index()
    
    for _, row in agg.iterrows():
        algo = row["algorithm"]
        color = ALGO_COLORS.get(algo, "#333333")
        label = ALGO_LABELS.get(algo, algo)
        x = row["avg_ms"]
        y = row["g_co2_per_million"]
        
        ax.scatter(x, y, color=color, s=120, zorder=5, label=label, edgecolor="black", linewidth=0.8)
        # Annotation offset
        offset_x = 0.05
        offset_y = 0.00002
        if algo == "enesort":
            ax.annotate(f"{label}\n(Pareto Optimal)", (x, y), xytext=(x - 0.7, y + 0.00008),
                        fontweight="bold", color=color,
                        arrowprops=dict(arrowstyle="->", color=color, lw=1.2))
        else:
            ax.annotate(label, (x, y), xytext=(x + offset_x, y + offset_y), fontsize=8.5)
            
    ax.set_xlabel("Mean Execution Time (ms) [Lower is Better]")
    ax.set_ylabel("Mean Carbon Emissions (g CO₂ / 10⁶ elements) [Lower is Better]")
    ax.set_title("Pareto Frontier: Execution Time vs. Carbon Emissions (N = 100,000, CodeCarbon)")
    ax.grid(True, linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    png_path = os.path.join(FIG_DIR, "carbon_vs_runtime_pareto.png")
    pdf_path = os.path.join(FIG_DIR, "carbon_vs_runtime_pareto.pdf")
    fig.savefig(png_path)
    fig.savefig(pdf_path)
    plt.close(fig)
    print(f"Saved {png_path} and {pdf_path}")

def plot_energy_barchart(df_100k):
    """Barchart comparing energy consumption across workloads."""
    workloads = ["all_equal", "ascending", "descending", "few_distinct_10",
                 "organ_pipe", "median_of_3_killer", "sorted_append_100", "uniform_random"]
    algos_to_plot = ["enesort", "std_sort", "pdqsort", "timsort", "mergesort"]
    
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(workloads))
    width = 0.15
    
    for i, algo in enumerate(algos_to_plot):
        vals = []
        for w in workloads:
            sub = df_100k[(df_100k["workload"] == w) & (df_100k["algorithm"] == algo)]
            if not sub.empty:
                vals.append(sub["uj_per_elem"].values[0])
            else:
                vals.append(0)
        ax.bar(x + (i - 2) * width, vals, width, label=ALGO_LABELS.get(algo, algo),
               color=ALGO_COLORS.get(algo, "#333333"), edgecolor="black", linewidth=0.6)
               
    ax.set_xticks(x)
    ax.set_xticklabels([w.replace("_", "\n") for w in workloads])
    ax.set_ylabel("Energy Consumed (µJ / element)")
    ax.set_title("Energy Consumption per Sorted Element Across Workloads (N = 100,000, CodeCarbon)")
    ax.legend(loc="upper left")
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    png_path = os.path.join(FIG_DIR, "energy_per_element_barchart.png")
    pdf_path = os.path.join(FIG_DIR, "energy_per_element_barchart.pdf")
    fig.savefig(png_path)
    fig.savefig(pdf_path)
    plt.close(fig)
    print(f"Saved {png_path} and {pdf_path}")

def plot_carbon_reduction(df_100k):
    """Bar chart of Carbon Reduction % of Enesort vs std::sort and pdqsort."""
    workloads = ["all_equal", "ascending", "descending", "organ_pipe",
                 "median_of_3_killer", "few_distinct_10", "sorted_append_100", "uniform_random"]
    
    red_vs_std = []
    red_vs_pdq = []
    
    for w in workloads:
        sub = df_100k[df_100k["workload"] == w]
        ene = sub[sub["algorithm"] == "enesort"]["g_co2_per_million"].values[0]
        std = sub[sub["algorithm"] == "std_sort"]["g_co2_per_million"].values[0]
        pdq_sub = sub[sub["algorithm"] == "pdqsort"]
        pdq = pdq_sub["g_co2_per_million"].values[0] if not pdq_sub.empty else std
        
        red_vs_std.append((std - ene) / std * 100.0)
        red_vs_pdq.append((pdq - ene) / pdq * 100.0)
        
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(workloads))
    width = 0.35
    
    b1 = ax.bar(x - width/2, red_vs_std, width, label="Reduction vs std::sort", color="#1b9e77", edgecolor="black", linewidth=0.6)
    b2 = ax.bar(x + width/2, red_vs_pdq, width, label="Reduction vs pdqsort", color="#7570b3", edgecolor="black", linewidth=0.6)
    
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([w.replace("_", "\n") for w in workloads])
    ax.set_ylabel("Carbon Reduction (%) [Higher is Greener]")
    ax.set_title("Carbon Emission Reduction by Enesort vs Standard Baseline Algorithms (CodeCarbon)")
    ax.legend()
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)
    
    plt.tight_layout()
    png_path = os.path.join(FIG_DIR, "carbon_reduction_barchart.png")
    pdf_path = os.path.join(FIG_DIR, "carbon_reduction_barchart.pdf")
    fig.savefig(png_path)
    fig.savefig(pdf_path)
    plt.close(fig)
    print(f"Saved {png_path} and {pdf_path}")

def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.", file=sys.stderr)
        sys.exit(1)
        
    df = pd.read_csv(CSV_PATH)
    df_100k = df[df["n"] == 100000]
    
    plot_pareto(df_100k)
    plot_energy_barchart(df_100k)
    plot_carbon_reduction(df_100k)
    print("All carbon figures plotted successfully!")

if __name__ == "__main__":
    main()
