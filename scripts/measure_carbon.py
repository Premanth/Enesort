#!/usr/bin/env python3
"""
measure_carbon.py – Measures energy consumption and carbon emissions of sorting algorithms
using CodeCarbon exclusively, following IEEE/ACM green software standards.

Tracks:
  - Total duration (seconds)
  - Energy consumed (kWh and Joules)
  - Carbon emissions (kg CO2eq and g CO2eq)
  - Energy per sort (Joules/sort) and energy per element (microjoules/elem)
  - Carbon intensity per million elements sorted (g CO2 / 10^6 elem)
  - Efficiency (elements sorted per Joule)
"""

import os
import sys
import subprocess
import datetime
import pandas as pd
import numpy as np
from codecarbon import EmissionsTracker

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(PROJ_DIR, "build_manual")
BENCH_CARBON_EXE = os.path.join(BIN_DIR, "bench_carbon.exe")
RAW_DIR = os.path.join(PROJ_DIR, "results", "raw")
ANALYSIS_DIR = os.path.join(PROJ_DIR, "results", "analysis")
TABLES_DIR = os.path.join(PROJ_DIR, "results", "tables")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(ANALYSIS_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

ALGORITHMS = [
    "enesort",
    "std_sort",
    "pdqsort",
    "timsort",
    "mergesort",
    "heapsort",
    "mo3_quicksort",
    "yaroslavskiy"
]

WORKLOADS = [
    "uniform_random",
    "ascending",
    "descending",
    "all_equal",
    "organ_pipe",
    "few_distinct_10",
    "median_of_3_killer",
    "sorted_append_100"
]

SIZES = [10000, 100000]

def get_repeats(size, workload):
    if size <= 10000:
        return 150
    elif size <= 100000:
        if workload in ["ascending", "descending", "all_equal"]:
            return 200
        else:
            return 50
    else:
        return 10

def main():
    print("=" * 80)
    print("CodeCarbon Environmental Sustainability Profiler for Sorting Algorithms")
    print("Tracking Joules, micro-Joules/elem, g CO2eq, and carbon efficiency")
    print("=" * 80)
    
    raw_csv = os.path.join(RAW_DIR, "carbon_emissions.csv")
    records = []
    
    total_cells = len(ALGORITHMS) * len(WORKLOADS) * len(SIZES)
    cell_idx = 0
    
    tracker = EmissionsTracker(
        project_name="ecosort_carbon_study",
        measure_power_secs=1,
        save_to_file=False,
        log_level="error"
    )
    tracker.start()
    
    try:
        for size in SIZES:
            for workload in WORKLOADS:
                print(f"\n--- Workload: {workload} (N = {size}) ---")
                repeats = get_repeats(size, workload)
                for algo in ALGORITHMS:
                    cell_idx += 1
                    task_name = f"{algo}_{workload}_{size}"
                    print(f"[{cell_idx}/{total_cells}] Measuring {algo.ljust(15)} (repeats={repeats})...", end="", flush=True)
                    
                    cmd = [BENCH_CARBON_EXE, algo, workload, str(size), str(repeats)]
                    
                    tracker.start_task(task_name)
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    task_data = tracker.stop_task()
                    
                    if res.returncode != 0:
                        print(f" Error: {res.stderr}", flush=True)
                        continue
                        
                    line = res.stdout.strip().splitlines()[-1]
                    tokens = line.split(",")
                    if len(tokens) < 8 or tokens[0] != "RESULT":
                        print(f" Malformed output: {line}", flush=True)
                        continue
                        
                    total_ms = float(tokens[5])
                    avg_ms = float(tokens[6])
                    sorted_ok = int(tokens[7])
                    
                    duration_s = task_data.duration if task_data.duration > 0 else (total_ms / 1000.0)
                    energy_kwh = task_data.energy_consumed
                    energy_joules = energy_kwh * 3.6e6
                    emissions_kg = task_data.emissions
                    cpu_power_w = task_data.cpu_power
                    
                    emissions_g = emissions_kg * 1000.0
                    joules_per_sort = energy_joules / repeats if repeats > 0 else 0
                    uj_per_elem = (joules_per_sort / size) * 1e6 if size > 0 else 0
                    g_co2_per_million = (emissions_g / (repeats * size)) * 1e6 if (repeats * size) > 0 else 0
                    elem_per_joule = size / joules_per_sort if joules_per_sort > 0 else 0
                    
                    rec = {
                        "timestamp": datetime.datetime.now().isoformat(),
                        "algorithm": algo,
                        "workload": workload,
                        "n": size,
                        "repeats": repeats,
                        "total_ms": total_ms,
                        "avg_ms": avg_ms,
                        "sorted_ok": sorted_ok,
                        "duration_s": duration_s,
                        "cpu_power_w": cpu_power_w,
                        "energy_kwh": energy_kwh,
                        "energy_joules": energy_joules,
                        "emissions_kg": emissions_kg,
                        "emissions_g": emissions_g,
                        "joules_per_sort": joules_per_sort,
                        "uj_per_elem": uj_per_elem,
                        "g_co2_per_million": g_co2_per_million,
                        "elem_per_joule": elem_per_joule
                    }
                    records.append(rec)
                    print(f" OK: {avg_ms:.3f} ms/sort | {uj_per_elem:.2f} µJ/elem | {g_co2_per_million:.5f} g CO2/10^6 elem", flush=True)
    finally:
        tracker.stop()
                    
    df = pd.DataFrame(records)
    df.to_csv(raw_csv, index=False)
    print(f"\nSaved raw carbon measurements ({len(df)} records) to {raw_csv}")
    
    # Generate summary CSV
    summary_csv = os.path.join(ANALYSIS_DIR, "carbon_summary.csv")
    df.to_csv(summary_csv, index=False)
    print(f"Saved carbon summary to {summary_csv}")
    
    # Generate comparison Table (Markdown & LaTeX)
    df_100k = df[df["n"] == 100000]
    
    table_md = os.path.join(TABLES_DIR, "carbon_table.md")
    table_tex = os.path.join(TABLES_DIR, "carbon_table.tex")
    
    with open(table_md, "w", encoding="utf-8") as f:
        f.write("# Carbon Emissions and Energy Consumption Across 8 Workloads (N = 100,000, 32-bit Integers)\n\n")
        f.write("Measured with CodeCarbon. Energy in microjoules/element (µJ/elem), Carbon in g CO2 / 10^6 elements.\n\n")
        f.write("| Workload | Enesort (µJ/elem) | std::sort (µJ/elem) | pdqsort (µJ/elem) | Enesort (g CO2/10^6) | std::sort (g CO2/10^6) | Carbon Reduction vs std::sort | Energy Speedup |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        
        for w in WORKLOADS:
            sub = df_100k[df_100k["workload"] == w]
            ene_row = sub[sub["algorithm"] == "enesort"]
            std_row = sub[sub["algorithm"] == "std_sort"]
            pdq_row = sub[sub["algorithm"] == "pdqsort"]
            
            if not ene_row.empty and not std_row.empty:
                ene_uj = ene_row["uj_per_elem"].values[0]
                std_uj = std_row["uj_per_elem"].values[0]
                pdq_uj = pdq_row["uj_per_elem"].values[0] if not pdq_row.empty else np.nan
                
                ene_co2 = ene_row["g_co2_per_million"].values[0]
                std_co2 = std_row["g_co2_per_million"].values[0]
                
                carbon_red = ((std_co2 - ene_co2) / std_co2 * 100.0) if std_co2 > 0 else 0
                energy_speedup = (std_uj / ene_uj) if ene_uj > 0 else 1.0
                
                f.write(f"| **{w}** | **{ene_uj:.3f}** | {std_uj:.3f} | {pdq_uj:.3f} | **{ene_co2:.5f}** | {std_co2:.5f} | **{carbon_red:+.1f}%** | **{energy_speedup:.2f}x** |\n")
                
    with open(table_tex, "w", encoding="utf-8") as f:
        f.write("% Carbon emissions and energy table generated by CodeCarbon\n")
        f.write("\\begin{table*}[t]\n\\centering\n")
        f.write("\\caption{Energy Consumption and Carbon Emissions Comparison on $N=100,000$ elements (32-bit integers) measured via CodeCarbon. Energy reported in $\\mu$J/element, Carbon emissions in grams of $\\text{CO}_2$ equivalent per million elements ($g\\,\\text{CO}_2 / 10^6\\,\\text{elem}$).}\n")
        f.write("\\label{tab:carbon_results}\n")
        f.write("\\begin{tabular}{lrrrrrrr}\n\\toprule\n")
        f.write("Workload & Enesort ($\\mu$J/elem) & \\texttt{std::sort} ($\\mu$J/elem) & \\texttt{pdqsort} ($\\mu$J/elem) & Enesort ($g\\,\\text{CO}_2$) & \\texttt{std::sort} ($g\\,\\text{CO}_2$) & Carbon Reduction (\\%) & Energy Speedup \\\\\n\\midrule\n")
        for w in WORKLOADS:
            sub = df_100k[df_100k["workload"] == w]
            ene_row = sub[sub["algorithm"] == "enesort"]
            std_row = sub[sub["algorithm"] == "std_sort"]
            pdq_row = sub[sub["algorithm"] == "pdqsort"]
            if not ene_row.empty and not std_row.empty:
                ene_uj = ene_row["uj_per_elem"].values[0]
                std_uj = std_row["uj_per_elem"].values[0]
                pdq_uj = pdq_row["uj_per_elem"].values[0] if not pdq_row.empty else np.nan
                ene_co2 = ene_row["g_co2_per_million"].values[0]
                std_co2 = std_row["g_co2_per_million"].values[0]
                carbon_red = ((std_co2 - ene_co2) / std_co2 * 100.0) if std_co2 > 0 else 0
                energy_speedup = (std_uj / ene_uj) if ene_uj > 0 else 1.0
                f.write(f"\\texttt{{{w}}} & \\textbf{{{ene_uj:.3f}}} & {std_uj:.3f} & {pdq_uj:.3f} & \\textbf{{{ene_co2:.5f}}} & {std_co2:.5f} & \\textbf{{{carbon_red:+.1f}\\%}} & \\textbf{{{energy_speedup:.2f}$\\times$}} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table*}\n")

    print(f"Generated {table_md} and {table_tex}")

if __name__ == "__main__":
    main()
