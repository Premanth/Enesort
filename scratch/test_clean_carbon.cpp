#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <algorithm>
#include "../src/enesort.hpp"
#include "../src/baselines/baselines.hpp"
#include "../bench/generators.hpp"

int main(int argc, char* argv[]) {
    if (argc < 4) {
        std::cerr << "Usage: bench_carbon <algo> <workload> <N> [repeats]\n";
        return 1;
    }
    std::string algo = argv[1];
    std::string workload_str = argv[2];
    size_t n = std::stoull(argv[3]);
    int repeats = (argc >= 5) ? std::stoi(argv[4]) : 50;

    WorkloadID wid = WorkloadID::UNIFORM_RANDOM;
    for (int w = 0; w < (int)WorkloadID::_COUNT; ++w) {
        if (workload_str == workload_name(static_cast<WorkloadID>(w))) {
            wid = static_cast<WorkloadID>(w);
            break;
        }
    }

    // Pre-generate arrays
    std::vector<std::vector<int32_t>> buffers(repeats);
    for (int r = 0; r < repeats; ++r) {
        buffers[r] = gen::generate<int32_t>(wid, n, 42 + r * 10007);
    }

    // Run sort function pointer
    auto run_sort = [&](int r) {
        if (algo == "enesort") bl_enesort::sort(buffers[r].data(), buffers[r].data() + n);
        else if (algo == "std_sort") bl_std_sort::sort(buffers[r].data(), buffers[r].data() + n);
        else if (algo == "pdqsort") bl_pdqsort::sort(buffers[r].data(), buffers[r].data() + n);
        else if (algo == "timsort") bl_timsort::sort(buffers[r].data(), buffers[r].data() + n);
        else if (algo == "mergesort") bl_mergesort::sort(buffers[r].data(), buffers[r].data() + n);
        else if (algo == "heapsort") bl_heapsort::sort(buffers[r].data(), buffers[r].data() + n);
        else if (algo == "mo3_quicksort") bl_mo3_quicksort::sort(buffers[r].data(), buffers[r].data() + n);
        else if (algo == "yaroslavskiy") bl_yaroslavskiy::sort(buffers[r].data(), buffers[r].data() + n);
        else {
            std::cerr << "Unknown algo: " << algo << "\n";
            std::exit(1);
        }
    };

    // Actual pure sorting loop
    auto t0 = std::chrono::high_resolution_clock::now();
    for (int r = 0; r < repeats; ++r) {
        run_sort(r);
    }
    auto t1 = std::chrono::high_resolution_clock::now();

    double total_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    double avg_ms = total_ms / repeats;

    // Post-hoc verification (not timed)
    bool ok = true;
    for (int r = 0; r < repeats; ++r) {
        for (size_t i = 1; i < n; ++i) {
            if (buffers[r][i] < buffers[r][i - 1]) { ok = false; break; }
        }
    }

    std::cout << "RESULT," << algo << "," << workload_str << "," << n << ","
              << repeats << "," << total_ms << "," << avg_ms << "," << (ok ? 1 : 0) << "\n";
    return 0;
}
