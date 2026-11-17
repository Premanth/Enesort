import os
import subprocess
from codecarbon import EmissionsTracker

PROJ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCH_EXE = os.path.join(PROJ_DIR, "build_manual", "bench.exe")

def run_carbon_test(algo, workload, n, trials):
    print(f"Tracking {algo} on {workload} (N={n}, trials={trials})...", flush=True)
    tracker = EmissionsTracker(project_name="ecosort_test", save_to_file=False, log_level="warning")
    tracker.start()
    
    cmd = [
        BENCH_EXE,
        "--study", "main",
        "--algo", algo,
        "--workload", workload,
        "--type", "int32",
        "--sizes", str(n),
        "--trials", str(trials)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    emissions = tracker.stop()
    energy_kwh = tracker.final_emissions_data.energy_consumed
    energy_joules = energy_kwh * 3.6e6
    duration = tracker.final_emissions_data.duration
    cpu_power = tracker.final_emissions_data.cpu_power
    
    g_co2 = emissions * 1000.0
    joules_per_sort = energy_joules / trials
    uj_per_elem = (joules_per_sort / n) * 1e6
    g_co2_per_million = (g_co2 / (trials * n)) * 1e6
    
    print(f"  Duration: {duration:.3f} s")
    print(f"  CPU Power: {cpu_power:.2f} W")
    print(f"  Energy: {energy_joules:.4f} Joules ({joules_per_sort:.6f} J/sort, {uj_per_elem:.3f} uJ/elem)")
    print(f"  Emissions: {g_co2:.6f} g CO2 ({g_co2_per_million:.6f} g CO2 / 10^6 elements)")
    return {
        "algo": algo,
        "duration": duration,
        "energy_joules": energy_joules,
        "joules_per_sort": joules_per_sort,
        "uj_per_elem": uj_per_elem,
        "g_co2": g_co2,
        "g_co2_per_million": g_co2_per_million
    }

if __name__ == "__main__":
    r_ene = run_carbon_test("enesort", "uniform_random", 100000, 50)
    r_std = run_carbon_test("std_sort", "uniform_random", 100000, 50)
    
    speedup = r_std["duration"] / r_ene["duration"]
    carbon_saving = (r_std["g_co2"] - r_ene["g_co2"]) / r_std["g_co2"] * 100.0
    print(f"\nSpeedup: {speedup:.2f}x")
    print(f"Carbon Reduction: {carbon_saving:.2f}%")
