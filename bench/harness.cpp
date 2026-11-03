// =============================================================================
// harness.cpp  –  Main benchmark harness for EcoSort v2
// =============================================================================
// Outputs one CSV row per trial to stdout (redirect to results/raw/YYYYMMDD.csv)
// CSV columns: timestamp,git_commit,cpu_model,os,compiler,flags,algorithm,
//              workload,n,type,trial,seed,time_ns,sorted_ok,multiset_ok,
//              aux_bytes,perf_cycles,perf_instructions,perf_l1d_misses,
//              perf_llc_misses,perf_branch_misses
// =============================================================================

#include "generators.hpp"
#include "../src/enesort.hpp"
#include "../src/baselines/baselines.hpp"

#include <future>
#include <thread>
#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <iostream>
#include <limits>
#include <map>
#include <sstream>
#include <string>
#include <type_traits>
#include <vector>

// Linux perf support
#ifdef __linux__
#include <linux/perf_event.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <unistd.h>

static long perf_event_open(struct perf_event_attr* hw_event, pid_t pid, int cpu,
                             int group_fd, unsigned long flags) {
    return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags);
}

struct PerfCounters {
    int fd_cycles = -1, fd_instrs = -1, fd_l1d = -1, fd_llc = -1, fd_branches = -1;
    bool available = false;

    void open() {
        struct perf_event_attr pe{};
        pe.type = PERF_TYPE_HARDWARE;
        pe.size = sizeof(pe);
        pe.disabled = 1;
        pe.exclude_kernel = 1;
        pe.exclude_hv = 1;

        pe.config = PERF_COUNT_HW_CPU_CYCLES;
        fd_cycles = perf_event_open(&pe, 0, -1, -1, 0);
        pe.config = PERF_COUNT_HW_INSTRUCTIONS;
        fd_instrs = perf_event_open(&pe, 0, -1, -1, 0);
        pe.config = PERF_COUNT_HW_CACHE_MISSES;
        pe.type = PERF_TYPE_HW_CACHE;
        pe.config = (PERF_COUNT_HW_CACHE_L1D | (PERF_COUNT_HW_CACHE_OP_READ << 8) |
                     (PERF_COUNT_HW_CACHE_RESULT_MISS << 16));
        fd_l1d = perf_event_open(&pe, 0, -1, -1, 0);
        pe.config = (PERF_COUNT_HW_CACHE_LL | (PERF_COUNT_HW_CACHE_OP_READ << 8) |
                     (PERF_COUNT_HW_CACHE_RESULT_MISS << 16));
        fd_llc = perf_event_open(&pe, 0, -1, -1, 0);
        pe.type = PERF_TYPE_HARDWARE;
        pe.config = PERF_COUNT_HW_BRANCH_MISSES;
        fd_branches = perf_event_open(&pe, 0, -1, -1, 0);
        available = (fd_cycles >= 0 && fd_instrs >= 0);
    }

    void start() {
        if (!available) return;
        ioctl(fd_cycles,   PERF_EVENT_IOC_RESET,  0); ioctl(fd_cycles,   PERF_EVENT_IOC_ENABLE, 0);
        ioctl(fd_instrs,   PERF_EVENT_IOC_RESET,  0); ioctl(fd_instrs,   PERF_EVENT_IOC_ENABLE, 0);
        if (fd_l1d >= 0) { ioctl(fd_l1d, PERF_EVENT_IOC_RESET, 0); ioctl(fd_l1d, PERF_EVENT_IOC_ENABLE, 0); }
        if (fd_llc >= 0) { ioctl(fd_llc, PERF_EVENT_IOC_RESET, 0); ioctl(fd_llc, PERF_EVENT_IOC_ENABLE, 0); }
        if (fd_branches >= 0) { ioctl(fd_branches, PERF_EVENT_IOC_RESET, 0); ioctl(fd_branches, PERF_EVENT_IOC_ENABLE, 0); }
    }

    void stop(int64_t& cycles, int64_t& instrs, int64_t& l1d, int64_t& llc, int64_t& branches) {
        if (!available) { cycles = instrs = l1d = llc = branches = -1; return; }
        ioctl(fd_cycles, PERF_EVENT_IOC_DISABLE, 0);
        ioctl(fd_instrs, PERF_EVENT_IOC_DISABLE, 0);
        if (fd_l1d >= 0) ioctl(fd_l1d, PERF_EVENT_IOC_DISABLE, 0);
        if (fd_llc >= 0) ioctl(fd_llc, PERF_EVENT_IOC_DISABLE, 0);
        if (fd_branches >= 0) ioctl(fd_branches, PERF_EVENT_IOC_DISABLE, 0);
        read(fd_cycles, &cycles,   sizeof(int64_t));
        read(fd_instrs, &instrs,   sizeof(int64_t));
        if (fd_l1d >= 0)     read(fd_l1d,     &l1d,      sizeof(int64_t)); else l1d = -1;
        if (fd_llc >= 0)     read(fd_llc,     &llc,      sizeof(int64_t)); else llc = -1;
        if (fd_branches >= 0)read(fd_branches, &branches, sizeof(int64_t)); else branches = -1;
    }

    ~PerfCounters() {
        if (fd_cycles >= 0) close(fd_cycles);
        if (fd_instrs >= 0) close(fd_instrs);
        if (fd_l1d >= 0) close(fd_l1d);
        if (fd_llc >= 0) close(fd_llc);
        if (fd_branches >= 0) close(fd_branches);
    }
};
#else
struct PerfCounters {
    bool available = false;
    void open() {}
    void start() {}
    void stop(int64_t& c, int64_t& i, int64_t& l1, int64_t& llc, int64_t& b) {
        c = i = l1 = llc = b = -1;
    }
};
#endif

// ---------------------------------------------------------------------------
// Environment metadata
// ---------------------------------------------------------------------------
static std::string get_env_string() {
    std::string cpu = "unknown";
    std::string os_str = "unknown";
#ifdef __linux__
    {
        FILE* f = fopen("/proc/cpuinfo", "r");
        if (f) {
            char line[256];
            while (fgets(line, sizeof(line), f)) {
                if (strncmp(line, "model name", 10) == 0) {
                    char* colon = strchr(line, ':');
                    if (colon) { cpu = std::string(colon+2); cpu.erase(cpu.find_last_not_of("\n\r ")+1); break; }
                }
            }
            fclose(f);
        }
        os_str = "Linux";
    }
#elif defined(_WIN32)
    os_str = "Windows";
    cpu = "Windows-CPU";
#elif defined(__APPLE__)
    os_str = "macOS";
    cpu = "Apple-CPU";
#endif
    // Replace commas in cpu string
    for (char& c : cpu) if (c == ',') c = ';';
    return cpu + "|" + os_str;
}

static std::string get_compiler_string() {
#if defined(__clang__)
    return "clang-" + std::to_string(__clang_major__) + "." + std::to_string(__clang_minor__);
#elif defined(__GNUC__)
    return "gcc-" + std::to_string(__GNUC__) + "." + std::to_string(__GNUC_MINOR__);
#elif defined(_MSC_VER)
    return "msvc-" + std::to_string(_MSC_VER);
#else
    return "unknown";
#endif
}

static std::string get_timestamp() {
    time_t now = time(nullptr);
    char buf[32];
    strftime(buf, sizeof(buf), "%Y%m%dT%H%M%SZ", gmtime(&now));
    return buf;
}

// ---------------------------------------------------------------------------
// Algorithm registry
// ---------------------------------------------------------------------------
template<typename T, typename Cmp>
using SortFn = void(*)(T*, T*, Cmp);

struct AlgoEntry {
    std::string name;
    bool is_ablation;
};

// ---------------------------------------------------------------------------
// Verifiers
// ---------------------------------------------------------------------------
template<typename T, typename Cmp>
bool is_sorted_check(const T* arr, size_t n, Cmp comp) {
    for (size_t i = 0; i+1 < n; ++i)
        if (comp(arr[i+1], arr[i])) return false;
    return true;
}

template<typename T>
bool multiset_equal(const std::vector<T>& orig, const std::vector<T>& sorted) {
    std::vector<T> a = orig, b = sorted;
    std::sort(a.begin(), a.end());
    std::sort(b.begin(), b.end());
    return a == b;
}

// ---------------------------------------------------------------------------
// Timer
// ---------------------------------------------------------------------------
using Clock = std::chrono::steady_clock;
using NS    = std::chrono::nanoseconds;

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Per-trial runner (generic) with per-run timeout
// ---------------------------------------------------------------------------
struct TrialResult {
    int64_t time_ns = -1;
    bool is_timeout = false;
    bool sorted_ok = false;
    bool multiset_ok = false;
    int64_t cycles = -1, instrs = -1, l1d_misses = -1, llc_misses = -1, branch_misses = -1;
    size_t aux_bytes = 0;
};

template<typename T, typename Cmp>
TrialResult run_trial(
    const std::vector<T>& original,
    Cmp comp,
    void (*sort_fn)(T*, T*, Cmp),
    PerfCounters& perf,
    int timeout_sec = 5
) {
    std::vector<T> data = original;  // fresh copy (excluded from timing)

    perf.start();
    auto t0 = Clock::now();

    sort_fn(data.data(), data.data() + data.size(), comp);

    auto t1 = Clock::now();

    TrialResult r;
    r.is_timeout  = false;
    r.time_ns     = static_cast<int64_t>(std::chrono::duration_cast<NS>(t1 - t0).count());
    perf.stop(r.cycles, r.instrs, r.l1d_misses, r.llc_misses, r.branch_misses);
    r.aux_bytes   = 0;

    r.sorted_ok   = is_sorted_check(data.data(), data.size(), comp);
    r.multiset_ok = multiset_equal(original, data);

    return r;
}

// ---------------------------------------------------------------------------
// CSV header
// ---------------------------------------------------------------------------
static void print_csv_header() {
    printf("timestamp,cpu,os,compiler,cxx_flags,algorithm,workload,n,type,"
           "trial,seed,time_ns,sorted_ok,multiset_ok,aux_bytes,"
           "perf_cycles,perf_instrs,perf_l1d_misses,perf_llc_misses,perf_branch_misses\n");
}

// ---------------------------------------------------------------------------
// Run a single cell (algo x workload x size x type)
// ---------------------------------------------------------------------------
template<typename T, typename Cmp>
void run_cell(
    const std::string& algo_name,
    WorkloadID wid,
    size_t n,
    const std::string& type_name,
    Cmp comp,
    void (*sort_fn)(T*, T*, Cmp),
    int num_trials,
    PerfCounters& perf,
    const std::string& env_cpu, const std::string& env_os,
    const std::string& compiler, const std::string& cxx_flags,
    uint64_t base_seed = 0
) {
    const std::string ts = get_timestamp();
    const std::string wname = workload_name(wid);
    bool timed_out_already = false;

    for (int trial = 0; trial < num_trials; ++trial) {
        uint64_t seed = base_seed + static_cast<uint64_t>(trial) * 1000003ULL
                        + static_cast<uint64_t>(wid) * 999983ULL
                        + n * 999979ULL;

        if (timed_out_already) {
            printf("%s,%s,%s,%s,%s,%s,%s,%zu,%s,%d,%llu,TIMEOUT,0,0,0,-1,-1,-1,-1,-1\n",
                   ts.c_str(), env_cpu.c_str(), env_os.c_str(), compiler.c_str(), cxx_flags.c_str(),
                   algo_name.c_str(), wname.c_str(), n, type_name.c_str(),
                   trial, (unsigned long long)seed);
            fflush(stdout);
            continue;
        }

        std::vector<T> data = gen::generate<T>(wid, n, seed);

        auto r = run_trial<T, Cmp>(data, comp, sort_fn, perf, 5);

        if (r.is_timeout) {
            timed_out_already = true;
            printf("%s,%s,%s,%s,%s,%s,%s,%zu,%s,%d,%llu,TIMEOUT,0,0,0,-1,-1,-1,-1,-1\n",
                   ts.c_str(), env_cpu.c_str(), env_os.c_str(), compiler.c_str(), cxx_flags.c_str(),
                   algo_name.c_str(), wname.c_str(), n, type_name.c_str(),
                   trial, (unsigned long long)seed);
            fflush(stdout);
            continue;
        }

        if (!r.sorted_ok || !r.multiset_ok) {
            fprintf(stderr, "CORRECTNESS FAILURE: algo=%s wid=%s n=%zu trial=%d\n",
                    algo_name.c_str(), wname.c_str(), n, trial);
            std::abort();
        }

        printf("%s,%s,%s,%s,%s,%s,%s,%zu,%s,%d,%llu,%lld,%d,%d,%zu,%lld,%lld,%lld,%lld,%lld\n",
               ts.c_str(), env_cpu.c_str(), env_os.c_str(), compiler.c_str(), cxx_flags.c_str(),
               algo_name.c_str(), wname.c_str(), n, type_name.c_str(),
               trial, (unsigned long long)seed, (long long)r.time_ns,
               (int)r.sorted_ok, (int)r.multiset_ok, r.aux_bytes,
               (long long)r.cycles, (long long)r.instrs,
               (long long)r.l1d_misses, (long long)r.llc_misses,
               (long long)r.branch_misses);
        fflush(stdout);
    }
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
int main(int argc, char** argv) {
    // Parse optional args: --smoke (quick run), --trials N, --sizes S1,S2,...
    bool smoke_mode = false;
    int num_trials  = 30;
    std::string type_filter;
    std::vector<size_t> sizes = {1000, 10000, 100000, 1000000};
    std::string algo_filter;
    std::string study_mode = "main";
    std::string workload_filter;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--smoke") == 0) {
            smoke_mode = true;
            num_trials = 5;
            sizes = {1000, 10000, 100000};
        } else if (strcmp(argv[i], "--trials") == 0 && i+1 < argc) {
            num_trials = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--sizes") == 0 && i+1 < argc) {
            sizes.clear();
            std::stringstream ss(argv[++i]);
            std::string tok;
            while (std::getline(ss, tok, ',')) sizes.push_back(std::stoull(tok));
        } else if (strcmp(argv[i], "--type") == 0 && i+1 < argc) {
            type_filter = argv[++i];
        } else if (strcmp(argv[i], "--algo") == 0 && i+1 < argc) {
            algo_filter = argv[++i];
        } else if (strcmp(argv[i], "--study") == 0 && i+1 < argc) {
            study_mode = argv[++i];
        } else if (strcmp(argv[i], "--workload") == 0 && i+1 < argc) {
            workload_filter = argv[++i];
        }
    }

    // Environment
    std::string env_full = get_env_string();
    size_t sep = env_full.find('|');
    std::string env_cpu = env_full.substr(0, sep);
    std::string env_os  = env_full.substr(sep+1);
    std::string compiler = get_compiler_string();

    const char* cflags_env = getenv("CXXFLAGS");
    std::string cxx_flags  = cflags_env ? cflags_env : "-O3";
    // Replace commas
    for (char& c : cxx_flags) if (c == ',') c = ';';

    PerfCounters perf;
    perf.open();

    print_csv_header();

    // Workloads for smoke vs study vs full
    std::vector<WorkloadID> workloads;
    if (!workload_filter.empty()) {
        for (int w = 0; w < (int)WorkloadID::_COUNT; ++w) {
            if (workload_filter == workload_name(static_cast<WorkloadID>(w))) {
                workloads.push_back(static_cast<WorkloadID>(w));
            }
        }
    } else if (smoke_mode) {
        workloads = {WorkloadID::UNIFORM_RANDOM, WorkloadID::ASCENDING,
                     WorkloadID::DESCENDING, WorkloadID::ALL_EQUAL,
                     WorkloadID::FEW_DISTINCT_10, WorkloadID::ORGAN_PIPE};
    } else if (study_mode == "cutoff") {
        workloads = {WorkloadID::UNIFORM_RANDOM, WorkloadID::SORTED_APPEND_100,
                     WorkloadID::FEW_DISTINCT_10};
    } else if (study_mode == "worstcase") {
        workloads = {WorkloadID::MEDIAN_OF_3_KILLER};
    } else {
        for (int w = 0; w < (int)WorkloadID::_COUNT; ++w)
            workloads.push_back(static_cast<WorkloadID>(w));
    }

    // --- Algorithm runners for int32_t ---
    using I32 = int32_t;
    using I64 = int64_t;
    using Dbl = double;
    using Kv  = KVPair;

    auto run_i32 = [&](const std::string& name,
                        void (*fn)(I32*, I32*, std::less<I32>)) {
        if (!algo_filter.empty() && algo_filter != name) return;
        if (!type_filter.empty() && type_filter != "int32") return;
        for (size_t n : sizes)
            for (WorkloadID wid : workloads)
                run_cell<I32>(name, wid, n, "int32", std::less<I32>{}, fn,
                              num_trials, perf, env_cpu, env_os, compiler, cxx_flags);
    };

    auto run_i64 = [&](const std::string& name,
                        void (*fn)(I64*, I64*, std::less<I64>)) {
        if (!algo_filter.empty() && algo_filter != name) return;
        if (!type_filter.empty() && type_filter != "int64") return;
        for (size_t n : sizes)
            for (WorkloadID wid : workloads)
                run_cell<I64>(name, wid, n, "int64", std::less<I64>{}, fn,
                              num_trials, perf, env_cpu, env_os, compiler, cxx_flags);
    };

    auto run_dbl = [&](const std::string& name,
                        void (*fn)(Dbl*, Dbl*, std::less<Dbl>)) {
        if (!algo_filter.empty() && algo_filter != name) return;
        if (!type_filter.empty() && type_filter != "double") return;
        for (size_t n : sizes)
            for (WorkloadID wid : workloads)
                run_cell<Dbl>(name, wid, n, "double", std::less<Dbl>{}, fn,
                              num_trials, perf, env_cpu, env_os, compiler, cxx_flags);
    };

    auto run_kv = [&](const std::string& name,
                       void (*fn)(Kv*, Kv*, KVLess)) {
        if (!algo_filter.empty() && algo_filter != name) return;
        if (!type_filter.empty() && type_filter != "kvpair") return;
        for (size_t n : sizes)
            for (WorkloadID wid : workloads)
                run_cell<Kv>(name, wid, n, "kvpair", KVLess{}, fn,
                             num_trials, perf, env_cpu, env_os, compiler, cxx_flags);
    };

    // Register algorithms
#define REG_I32(name, ns) run_i32(name, [](I32* b, I32* e, std::less<I32> c){ ns::sort(b, e, c); });
#define REG_I64(name, ns) run_i64(name, [](I64* b, I64* e, std::less<I64> c){ ns::sort(b, e, c); });
#define REG_DBL(name, ns) run_dbl(name, [](Dbl* b, Dbl* e, std::less<Dbl> c){ ns::sort(b, e, c); });
#define REG_KV(name, ns)  run_kv(name,  [](Kv*  b, Kv*  e, KVLess c)       { ns::sort(b, e, c); });

    if (study_mode == "main" || study_mode == "all") {
        REG_I32("enesort",         bl_enesort)
        REG_I32("std_sort",        bl_std_sort)
        REG_I32("stable_sort",     bl_stable_sort)
        REG_I32("std_precheck",    bl_std_sort_precheck)
        REG_I32("heapsort",        bl_heapsort)
        REG_I32("mo3_quicksort",   bl_mo3_quicksort)
        REG_I32("yaroslavskiy",    bl_yaroslavskiy)
        REG_I32("mergesort",       bl_mergesort)
        REG_I32("pdqsort",         bl_pdqsort)
        REG_I32("ips4o",           bl_ips4o)
        REG_I32("timsort",         bl_timsort)

        REG_I64("enesort",         bl_enesort)
        REG_I64("std_sort",        bl_std_sort)
        REG_I64("pdqsort",         bl_pdqsort)

        REG_DBL("enesort",         bl_enesort)
        REG_DBL("std_sort",        bl_std_sort)
        REG_DBL("pdqsort",         bl_pdqsort)

        REG_KV("enesort",          bl_enesort)
        REG_KV("std_sort",         bl_std_sort)
        REG_KV("pdqsort",          bl_pdqsort)
    }

    if (study_mode == "ablation" || study_mode == "all") {
        REG_I32("enesort",         bl_enesort)
        REG_I32("enesort_no_f1",   bl_enesort_no_f1)
        REG_I32("enesort_no_f2",   bl_enesort_no_f2)
        REG_I32("enesort_no_f3",   bl_enesort_no_f3)
        REG_I32("enesort_no_f4",   bl_enesort_no_f4)
        REG_I32("mo3_quicksort",   bl_mo3_quicksort)
        REG_I32("std_sort",        bl_std_sort)
    }

    if (study_mode == "cutoff" || study_mode == "all") {
        using c8   = bl_enesort_cutoff<8>;
        using c12  = bl_enesort_cutoff<12>;
        using c16  = bl_enesort_cutoff<16>;
        using c24  = bl_enesort_cutoff<24>;
        using c32  = bl_enesort_cutoff<32>;
        using c48  = bl_enesort_cutoff<48>;
        using c64  = bl_enesort_cutoff<64>;
        using c96  = bl_enesort_cutoff<96>;
        using c128 = bl_enesort_cutoff<128>;
        REG_I32("enesort_cutoff_8",   c8)
        REG_I32("enesort_cutoff_12",  c12)
        REG_I32("enesort_cutoff_16",  c16)
        REG_I32("enesort_cutoff_24",  c24)
        REG_I32("enesort_cutoff_32",  c32)
        REG_I32("enesort_cutoff_48",  c48)
        REG_I32("enesort_cutoff_64",  c64)
        REG_I32("enesort_cutoff_96",  c96)
        REG_I32("enesort_cutoff_128", c128)
    }

    if (study_mode == "pivot" || study_mode == "all") {
        using s3   = bl_enesort_sample<3, 0, 2>;
        using s5   = bl_enesort_sample<5, 1, 3>;
        using s7   = bl_enesort_sample<7, 2, 4>;
        using s9   = bl_enesort_sample<9, 2, 6>;
        using skew = bl_enesort_sample<5, 0, 3>;
        REG_I32("enesort_sample_3",    s3)
        REG_I32("enesort_sample_5",    s5)
        REG_I32("enesort_sample_7",    s7)
        REG_I32("enesort_sample_9",    s9)
        REG_I32("enesort_sample_skew", skew)
    }

    if (study_mode == "worstcase") {
        REG_I32("enesort",         bl_enesort)
        REG_I32("enesort_no_f3",   bl_enesort_no_f3)
        REG_I32("mo3_quicksort",   bl_mo3_quicksort)
        REG_I32("heapsort",        bl_heapsort)
        REG_I32("std_sort",        bl_std_sort)
    }

    return 0;
}

