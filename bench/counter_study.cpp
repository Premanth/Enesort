// =============================================================================
// counter_study.cpp  –  Measure comparisons and swaps per element
// =============================================================================
// Compiles with ENESORT_COUNT_OPS=1. Counts exact comparisons & swaps for Enesort.
// Outputs CSV to stdout:
// algorithm,workload,n,type,trial,comparisons,swaps,cmps_per_elem,swaps_per_elem
// =============================================================================

#ifndef ENESORT_COUNT_OPS
#  define ENESORT_COUNT_OPS 1
#endif
#ifndef ECOSORT_COUNT_OPS
#  define ECOSORT_COUNT_OPS 1
#endif

#include "../src/enesort.hpp"
#include "generators.hpp"

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    std::vector<size_t> sizes = {1000, 10000, 100000};
    int trials = 5;
    std::vector<WorkloadID> workloads = {
        WorkloadID::UNIFORM_RANDOM,
        WorkloadID::FEW_DISTINCT_10,
        WorkloadID::ASCENDING,
        WorkloadID::DESCENDING,
        WorkloadID::ALL_EQUAL,
        WorkloadID::ORGAN_PIPE
    };

    printf("algorithm,workload,n,type,trial,comparisons,swaps,cmps_per_elem,swaps_per_elem\n");

    for (size_t n : sizes) {
        for (WorkloadID wid : workloads) {
            const char* wname = workload_name(wid);

            for (int t = 0; t < trials; ++t) {
                uint64_t seed = 42 + t * 10007 + n * 997 + static_cast<int>(wid) * 101;

                // Test Enesort
                {
                    auto data = gen::generate<int32_t>(wid, n, seed);
                    enesort::reset_counters();
                    enesort::sort(data.begin(), data.end(), std::less<int32_t>{});
                    uint64_t cmps = enesort::get_comparisons();
                    uint64_t swps = enesort::get_swaps();
                    printf("enesort,%s,%zu,int32,%d,%llu,%llu,%.4f,%.4f\n",
                           wname, n, t,
                           (unsigned long long)cmps, (unsigned long long)swps,
                           (double)cmps / n, (double)swps / n);
                }
            }
        }
    }

    return 0;
}

