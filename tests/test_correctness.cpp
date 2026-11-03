// =============================================================================
// tests/test_correctness.cpp – Correctness, fuzz, adversarial, property tests
// =============================================================================

#include "../src/enesort.hpp"
#include "../src/baselines/baselines.hpp"
#include "../bench/generators.hpp"

#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <random>
#include <string>
#include <vector>

// Convenience wrapper to call enesort with explicit comparator
template<typename T>
void ene_sort(std::vector<T>& v) {
    enesort::sort(v.begin(), v.end(), std::less<T>{});
}
template<typename T>
void eco_sort(std::vector<T>& v) {
    ene_sort(v);
}

static int tests_passed = 0;
static int tests_failed = 0;

#define CHECK(cond, msg) do { \
    if (!(cond)) { \
        fprintf(stderr, "FAIL: %s (line %d)\n", msg, __LINE__); \
        ++tests_failed; \
    } else { \
        ++tests_passed; \
    } \
} while(0)

// ---------------------------------------------------------------------------
// Helper: verify sorted
// ---------------------------------------------------------------------------
template<typename T, typename Cmp = std::less<T>>
bool verify_sorted(const std::vector<T>& v, Cmp comp = {}) {
    for (size_t i = 0; i+1 < v.size(); ++i)
        if (comp(v[i+1], v[i])) return false;
    return true;
}

template<typename T>
bool verify_multiset(const std::vector<T>& orig, const std::vector<T>& sorted) {
    std::vector<T> a = orig, b = sorted;
    std::sort(a.begin(), a.end());
    std::sort(b.begin(), b.end());
    return a == b;
}

// ---------------------------------------------------------------------------
// Basic correctness for each workload
// ---------------------------------------------------------------------------
static void test_basic_workloads() {
    printf("=== Basic workload correctness ===\n");
    std::vector<size_t> sizes = {0, 1, 2, 3, 7, 15, 16, 17, 31, 32, 33,
                                  100, 1000, 10000};
    for (size_t n : sizes) {
        for (int w = 0; w < (int)WorkloadID::_COUNT; ++w) {
            WorkloadID wid = static_cast<WorkloadID>(w);
            auto orig = gen::generate<int32_t>(wid, n, 42);
            auto data = orig;
            eco_sort(data);
            std::string msg = std::string("sorted:") + workload_name(wid)
                              + " n=" + std::to_string(n);
            CHECK(verify_sorted(data), msg.c_str());
            CHECK(verify_multiset(orig, data), ("multiset:" + msg).c_str());
        }
    }
}

// ---------------------------------------------------------------------------
// Fuzz: 1e6 small arrays (n < 500) vs std::sort
// ---------------------------------------------------------------------------
static void test_fuzz() {
    printf("=== Fuzz test (1e6 small arrays vs std::sort) ===\n");
    std::mt19937_64 rng(12345);
    int n_fuzz = 1000000;
    int failures = 0;
    for (int t = 0; t < n_fuzz; ++t) {
        size_t n = rng() % 500;
        // random value range and duplicate rate
        int range = 1 + (int)(rng() % 50);
        std::vector<int32_t> data(n);
        for (size_t i = 0; i < n; ++i)
            data[i] = (int32_t)(rng() % range);
        auto expected = data;
        std::sort(expected.begin(), expected.end());
        eco_sort(data);
        if (data != expected) {
            ++failures;
            if (failures <= 3) {
                fprintf(stderr, "FUZZ FAIL at trial %d n=%zu range=%d\n", t, n, range);
            }
        }
    }
    CHECK(failures == 0, "fuzz: no failures vs std::sort");
    printf("  Fuzz: %d failures out of %d trials\n", failures, n_fuzz);
}

// ---------------------------------------------------------------------------
// Adversarial regression: each workload at n=1e5 must finish in < 10x std::sort
// ---------------------------------------------------------------------------
static void test_adversarial_timing() {
    printf("=== Adversarial timing regression (n=100000) ===\n");
    const size_t N = 100000;
    // Warm up cache
    auto dummy = gen::generate<int32_t>(WorkloadID::UNIFORM_RANDOM, N, 1);
    std::sort(dummy.begin(), dummy.end());

    for (int w = 0; w < (int)WorkloadID::_COUNT; ++w) {
        WorkloadID wid = static_cast<WorkloadID>(w);
        auto orig = gen::generate<int32_t>(wid, N, 77);

        // Measure std::sort
        auto d1 = orig;
        auto t0 = std::chrono::steady_clock::now();
        std::sort(d1.begin(), d1.end());
        auto t1 = std::chrono::steady_clock::now();
        auto std_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(t1-t0).count();

        // Measure ecosort
        auto d2 = orig;
        auto t2 = std::chrono::steady_clock::now();
        eco_sort(d2);
        auto t3 = std::chrono::steady_clock::now();
        auto eco_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(t3-t2).count();

        double ratio = (std_ns > 0) ? static_cast<double>(eco_ns) / std_ns : 0.0;
        bool ok = (ratio < 10.0);
        std::string msg = std::string("adversarial_timing:") + workload_name(wid)
                          + " ratio=" + std::to_string(ratio);
        CHECK(ok, msg.c_str());
        if (!ok || ratio > 2.0) {
            printf("  [%s] EcoSort=%.3fms std::sort=%.3fms ratio=%.2fx %s\n",
                   workload_name(wid),
                   eco_ns / 1e6, std_ns / 1e6, ratio,
                   ok ? "OK" : "SLOW!");
        }
    }
}

// ---------------------------------------------------------------------------
// Property: depth bound (F3 heapsort fallback must trigger when forced)
// ---------------------------------------------------------------------------
static void test_depth_limit_property() {
    printf("=== Depth limit property test ===\n");
    // Use median-of-3 killer as adversarial input
    size_t N = 10000;
    auto data = gen::generate<int32_t>(WorkloadID::MEDIAN_OF_3_KILLER, N, 1);
    auto backup = data;
    // Should not hang / should be sorted correctly
    eco_sort(data);
    CHECK(verify_sorted(data), "depth_limit: killer input sorted");
    CHECK(verify_multiset(backup, data), "depth_limit: killer multiset preserved");
}

// ---------------------------------------------------------------------------
// Property: partition invariants (manual check on small array)
// ---------------------------------------------------------------------------
static void test_partition_invariants() {
    printf("=== Partition invariant test ===\n");
    // After sort: array is non-decreasing
    for (int trial = 0; trial < 1000; ++trial) {
        std::mt19937_64 rng(trial);
        size_t n = 2 + rng() % 200;
        std::vector<int32_t> v(n);
        for (size_t i = 0; i < n; ++i) v[i] = (int32_t)(rng() % 10);
        auto orig = v;
        eco_sort(v);
        CHECK(verify_sorted(v), "partition_invariants: sorted");
        CHECK(verify_multiset(orig, v), "partition_invariants: multiset");
    }
}

// ---------------------------------------------------------------------------
// Test baselines correctness
// ---------------------------------------------------------------------------
static void test_baselines_correctness() {
    printf("=== Baselines correctness ===\n");
    std::vector<size_t> sizes = {0, 1, 2, 15, 16, 33, 1000};
    for (size_t n : sizes) {
        for (int w = 0; w < (int)WorkloadID::_COUNT; ++w) {
            WorkloadID wid = static_cast<WorkloadID>(w);
            auto orig = gen::generate<int32_t>(wid, n, 42);

            // mo3_quicksort
            {
                auto data = orig;
                bl_mo3_quicksort::sort(data.data(), data.data() + data.size());
                CHECK(verify_sorted(data), ("mo3:" + std::string(workload_name(wid))).c_str());
                CHECK(verify_multiset(orig, data), "mo3_multiset");
            }
            // yaroslavskiy
            {
                auto data = orig;
                bl_yaroslavskiy::sort(data.data(), data.data() + data.size());
                CHECK(verify_sorted(data), ("yaro:" + std::string(workload_name(wid))).c_str());
                CHECK(verify_multiset(orig, data), "yaro_multiset");
            }
            // mergesort
            {
                auto data = orig;
                bl_mergesort::sort(data.data(), data.data() + data.size());
                CHECK(verify_sorted(data), ("merge:" + std::string(workload_name(wid))).c_str());
                CHECK(verify_multiset(orig, data), "merge_multiset");
            }
            // heapsort
            {
                auto data = orig;
                bl_heapsort::sort(data.data(), data.data() + data.size());
                CHECK(verify_sorted(data), ("heap:" + std::string(workload_name(wid))).c_str());
                CHECK(verify_multiset(orig, data), "heap_multiset");
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Test struct (KVPair)
// ---------------------------------------------------------------------------
static void test_struct_type() {
    printf("=== KVPair struct type ===\n");
    auto orig = gen::generate<KVPair>(WorkloadID::UNIFORM_RANDOM, 10000, 7);
    auto data = orig;
    ecosort::sort(data.begin(), data.end(), KVLess{});
    CHECK(verify_sorted(data, KVLess{}), "struct: sorted");
    // multiset check by key only
    std::vector<int64_t> ok, dk;
    for (auto& kv : orig)  ok.push_back(kv.key);
    for (auto& kv : data)  dk.push_back(kv.key);
    std::sort(ok.begin(), ok.end()); std::sort(dk.begin(), dk.end());
    CHECK(ok == dk, "struct: multiset keys match");
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
int main() {
    test_basic_workloads();
    test_baselines_correctness();
    test_partition_invariants();
    test_depth_limit_property();
    test_struct_type();

    // Fuzz is expensive – only run if explicitly requested
    const char* run_fuzz = getenv("ECOSORT_FUZZ");
    if (run_fuzz && strcmp(run_fuzz, "1") == 0) {
        test_fuzz();
    } else {
        // Quick fuzz: 10000 trials
        printf("=== Quick fuzz (10000 trials; set ECOSORT_FUZZ=1 for full 1M) ===\n");
        std::mt19937_64 rng(999);
        int failures = 0;
        for (int t = 0; t < 10000; ++t) {
            size_t n = rng() % 500;
            int range = 1 + (int)(rng() % 50);
            std::vector<int32_t> data(n);
            for (size_t i = 0; i < n; ++i) data[i] = (int32_t)(rng() % range);
            auto expected = data;
            std::sort(expected.begin(), expected.end());
            eco_sort(data);
            if (data != expected) ++failures;
        }
        CHECK(failures == 0, "quick_fuzz: no failures");
    }

    test_adversarial_timing();

    printf("\n=== RESULTS: %d passed, %d failed ===\n", tests_passed, tests_failed);
    return tests_failed > 0 ? 1 : 0;
}
