// =============================================================================
// generators.hpp  –  Deterministic workload generators for EcoSort benchmarks
// =============================================================================
// All generators accept a seed for reproducibility.
// Each returns a std::vector<T> of the requested size.
// =============================================================================

#pragma once

#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

// ---------------------------------------------------------------------------
// 16-byte struct type for heterogeneous benchmarks
// ---------------------------------------------------------------------------
struct KVPair {
    int64_t key;
    int64_t payload;
    bool operator<(const KVPair& o) const {
        if (key != o.key) return key < o.key;
        return payload < o.payload;
    }
    bool operator==(const KVPair& o) const { return key == o.key && payload == o.payload; }
};

struct KVLess {
    bool operator()(const KVPair& a, const KVPair& b) const { return a.key < b.key; }
};

// ---------------------------------------------------------------------------
// Workload identifiers
// ---------------------------------------------------------------------------
enum class WorkloadID : int {
    UNIFORM_RANDOM = 0,
    ASCENDING,
    DESCENDING,
    NEARLY_SORTED_10,     // 10 random swaps
    NEARLY_SORTED_1PCT,   // 1% of n swaps
    NEARLY_SORTED_5PCT,   // 5% of n swaps
    SORTED_APPEND_100,    // sorted + 100 random records appended
    ORGAN_PIPE,
    SAWTOOTH_M4,          // i mod 4
    SAWTOOTH_M16,         // i mod 16
    SAWTOOTH_M64,         // i mod 64
    FEW_DISTINCT_2,
    FEW_DISTINCT_10,
    FEW_DISTINCT_100,
    ALL_EQUAL,
    ALL_EQUAL_BUT_ONE,
    ZIPF,
    REVERSE_NOISE,
    BLOCKS_ASCENDING,     // blocks of ascending runs
    MEDIAN_OF_3_KILLER,   // adversarial for median-of-3 quicksort
    _COUNT
};

static const char* workload_name(WorkloadID wid) {
    static const char* names[] = {
        "uniform_random",
        "ascending",
        "descending",
        "nearly_sorted_10",
        "nearly_sorted_1pct",
        "nearly_sorted_5pct",
        "sorted_append_100",
        "organ_pipe",
        "sawtooth_m4",
        "sawtooth_m16",
        "sawtooth_m64",
        "few_distinct_2",
        "few_distinct_10",
        "few_distinct_100",
        "all_equal",
        "all_equal_but_one",
        "zipf",
        "reverse_noise",
        "blocks_ascending",
        "median_of_3_killer"
    };
    return names[static_cast<int>(wid)];
}

// ---------------------------------------------------------------------------
// Base generator: uniform [0, INT32_MAX] integers
// ---------------------------------------------------------------------------
namespace gen {

using RNG = std::mt19937_64;

template<typename T>
struct value_gen {
    static T gen_uniform(RNG& rng, int64_t lo = 0, int64_t hi = std::numeric_limits<int32_t>::max());
};

template<>
struct value_gen<int32_t> {
    static int32_t gen_uniform(RNG& rng, int64_t lo, int64_t hi) {
        return static_cast<int32_t>(std::uniform_int_distribution<int64_t>(lo, hi)(rng));
    }
};
template<>
struct value_gen<int64_t> {
    static int64_t gen_uniform(RNG& rng, int64_t lo, int64_t hi) {
        return std::uniform_int_distribution<int64_t>(lo, hi)(rng);
    }
};
template<>
struct value_gen<double> {
    static double gen_uniform(RNG& rng, int64_t lo, int64_t hi) {
        return std::uniform_real_distribution<double>(
            static_cast<double>(lo), static_cast<double>(hi))(rng);
    }
};
template<>
struct value_gen<KVPair> {
    static KVPair gen_uniform(RNG& rng, int64_t lo, int64_t hi) {
        int64_t k = std::uniform_int_distribution<int64_t>(lo, hi)(rng);
        int64_t p = rng();
        return {k, p};
    }
};

// ---------------------------------------------------------------------------
// Zipf distribution helper
// ---------------------------------------------------------------------------
class ZipfDistribution {
    double alpha_;
    size_t n_;
    std::vector<double> cdf_;
public:
    ZipfDistribution(size_t n, double alpha) : alpha_(alpha), n_(n), cdf_(n+1, 0.0) {
        double sum = 0.0;
        for (size_t i = 1; i <= n; ++i)
            sum += 1.0 / std::pow(static_cast<double>(i), alpha);
        cdf_[0] = 0.0;
        for (size_t i = 1; i <= n; ++i)
            cdf_[i] = cdf_[i-1] + 1.0 / (std::pow(static_cast<double>(i), alpha) * sum);
    }
    int64_t sample(RNG& rng) {
        double u = std::uniform_real_distribution<double>(0.0, 1.0)(rng);
        auto it = std::lower_bound(cdf_.begin(), cdf_.end(), u);
        return static_cast<int64_t>(it - cdf_.begin());
    }
};

// ---------------------------------------------------------------------------
// Median-of-3 killer sequence (after M.D.McIlroy, "A Killer Adversary
// for Quicksort", SPE 1999) – builds a sequence adversarial for
// single-pivot median-of-3 QS on size n.
// ---------------------------------------------------------------------------
static std::vector<int32_t> median_of_3_killer(size_t n) {
    std::vector<int32_t> a(n);
    // candidate[i] = i initially
    std::vector<int32_t> candidate(n);
    for (size_t i = 0; i < n; ++i) candidate[i] = static_cast<int32_t>(i);
    std::vector<int32_t> val(n);
    // freeze pivot positions
    size_t k = n / 2;
    size_t pos = 0;
    for (size_t i = 0; i < n; ++i) {
        if (i % 2 == 0) { val[i] = pos++; }
        else            { val[i] = k;      }
    }
    // reverse  
    for (size_t i = 0; i < n; ++i) a[i] = val[n-1-i];
    return a;
}

// ---------------------------------------------------------------------------
// Main generate function
// ---------------------------------------------------------------------------
template<typename T>
std::vector<T> generate(WorkloadID wid, size_t n, uint64_t seed) {
    RNG rng(seed);
    std::vector<T> v(n);

    auto fill_uniform = [&]() {
        for (size_t i = 0; i < n; ++i)
            v[i] = value_gen<T>::gen_uniform(rng, 0, static_cast<int64_t>(n)*4);
    };
    auto fill_ascending = [&]() {
        for (size_t i = 0; i < n; ++i)
            v[i] = value_gen<T>::gen_uniform(rng, 0, 0); // placeholder
        // Use iota-like approach
        if constexpr (std::is_arithmetic_v<T>) {
            for (size_t i = 0; i < n; ++i) v[i] = static_cast<T>(i);
        } else {
            for (size_t i = 0; i < n; ++i) v[i] = {static_cast<int64_t>(i), static_cast<int64_t>(i)};
        }
    };

    switch (wid) {
    case WorkloadID::UNIFORM_RANDOM:
        fill_uniform();
        break;

    case WorkloadID::ASCENDING:
        if constexpr (std::is_arithmetic_v<T>) {
            for (size_t i = 0; i < n; ++i) v[i] = static_cast<T>(i);
        } else {
            for (size_t i = 0; i < n; ++i) v[i] = {static_cast<int64_t>(i), static_cast<int64_t>(i)};
        }
        break;

    case WorkloadID::DESCENDING:
        if constexpr (std::is_arithmetic_v<T>) {
            for (size_t i = 0; i < n; ++i) v[i] = static_cast<T>(n-1-i);
        } else {
            for (size_t i = 0; i < n; ++i) v[i] = {static_cast<int64_t>(n-1-i), 0LL};
        }
        break;

    case WorkloadID::NEARLY_SORTED_10:
    case WorkloadID::NEARLY_SORTED_1PCT:
    case WorkloadID::NEARLY_SORTED_5PCT: {
        // Start with ascending
        if constexpr (std::is_arithmetic_v<T>) {
            for (size_t i = 0; i < n; ++i) v[i] = static_cast<T>(i);
        } else {
            for (size_t i = 0; i < n; ++i) v[i] = {static_cast<int64_t>(i), static_cast<int64_t>(i)};
        }
        if (n < 2) break;  // nothing to swap
        size_t k = 10;
        if (wid == WorkloadID::NEARLY_SORTED_1PCT) k = std::max<size_t>(1, n/100);
        if (wid == WorkloadID::NEARLY_SORTED_5PCT) k = std::max<size_t>(1, n/20);
        k = std::min(k, n);  // clamp to array size
        std::uniform_int_distribution<size_t> idist(0, n-1);
        for (size_t s = 0; s < k; ++s) {
            size_t a = idist(rng), b = idist(rng);
            using std::swap; swap(v[a], v[b]);
        }
        break;
    }

    case WorkloadID::SORTED_APPEND_100: {
        size_t base = (n > 100) ? n - 100 : 0;
        size_t app  = n - base;
        if constexpr (std::is_arithmetic_v<T>) {
            for (size_t i = 0; i < base; ++i) v[i] = static_cast<T>(i);
        } else {
            for (size_t i = 0; i < base; ++i) v[i] = {static_cast<int64_t>(i), 0LL};
        }
        for (size_t i = base; i < n; ++i)
            v[i] = value_gen<T>::gen_uniform(rng, 0, static_cast<int64_t>(n)*4);
        (void)app;
        break;
    }

    case WorkloadID::ORGAN_PIPE:
        // v[i] = i for i < n/2, then n-1-i
        if constexpr (std::is_arithmetic_v<T>) {
            for (size_t i = 0; i < n; ++i)
                v[i] = static_cast<T>(i < n/2 ? i : n-1-i);
        } else {
            for (size_t i = 0; i < n; ++i) {
                int64_t k = (i < n/2) ? (int64_t)i : (int64_t)(n-1-i);
                v[i] = {k, 0LL};
            }
        }
        break;

    case WorkloadID::SAWTOOTH_M4:
    case WorkloadID::SAWTOOTH_M16:
    case WorkloadID::SAWTOOTH_M64: {
        size_t m = (wid == WorkloadID::SAWTOOTH_M4) ? 4 : (wid == WorkloadID::SAWTOOTH_M16) ? 16 : 64;
        if constexpr (std::is_arithmetic_v<T>) {
            for (size_t i = 0; i < n; ++i) v[i] = static_cast<T>(i % m);
        } else {
            for (size_t i = 0; i < n; ++i) v[i] = {static_cast<int64_t>(i % m), static_cast<int64_t>(i)};
        }
        break;
    }

    case WorkloadID::FEW_DISTINCT_2:
    case WorkloadID::FEW_DISTINCT_10:
    case WorkloadID::FEW_DISTINCT_100: {
        int64_t k = (wid == WorkloadID::FEW_DISTINCT_2) ? 2 : (wid == WorkloadID::FEW_DISTINCT_10) ? 10 : 100;
        for (size_t i = 0; i < n; ++i)
            v[i] = value_gen<T>::gen_uniform(rng, 0, k-1);
        break;
    }

    case WorkloadID::ALL_EQUAL:
        for (size_t i = 0; i < n; ++i)
            v[i] = value_gen<T>::gen_uniform(rng, 42, 42);
        break;

    case WorkloadID::ALL_EQUAL_BUT_ONE: {
        if (n == 0) break;
        for (size_t i = 0; i < n; ++i)
            v[i] = value_gen<T>::gen_uniform(rng, 42, 42);
        size_t pos = std::uniform_int_distribution<size_t>(0, n-1)(rng);
        v[pos] = value_gen<T>::gen_uniform(rng, 0, 41);
        break;
    }

    case WorkloadID::ZIPF: {
        if (n == 0) break;
        ZipfDistribution zipf(std::max<size_t>(n, 1), 1.1);
        for (size_t i = 0; i < n; ++i)
            v[i] = value_gen<T>::gen_uniform(rng, zipf.sample(rng), zipf.sample(rng)+1);
        break;
    }

    case WorkloadID::REVERSE_NOISE: {
        if (n == 0) break;
        // descending + 5% random noise
        if constexpr (std::is_arithmetic_v<T>) {
            for (size_t i = 0; i < n; ++i) v[i] = static_cast<T>(n-1-i);
        } else {
            for (size_t i = 0; i < n; ++i) v[i] = {static_cast<int64_t>(n-1-i), 0LL};
        }
        size_t noisy = n / 20;
        if (noisy > 0) {
            std::uniform_int_distribution<size_t> idist(0, n-1);
            for (size_t s = 0; s < noisy; ++s) {
                v[idist(rng)] = value_gen<T>::gen_uniform(rng, 0, static_cast<int64_t>(n));
            }
        }
        break;
    }

    case WorkloadID::BLOCKS_ASCENDING: {
        // blocks of ~sqrt(n) ascending values
        size_t block = std::max<size_t>(1, static_cast<size_t>(std::sqrt(static_cast<double>(n))));
        size_t i = 0;
        while (i < n) {
            size_t end = std::min(i + block, n);
            for (size_t j = i; j < end; ++j) {
                int64_t val = (int64_t)(j - i);
                if constexpr (std::is_arithmetic_v<T>) v[j] = static_cast<T>(val);
                else v[j] = {val, static_cast<int64_t>(j)};
            }
            i = end;
        }
        break;
    }

    case WorkloadID::MEDIAN_OF_3_KILLER: {
        if constexpr (std::is_same_v<T, int32_t>) {
            auto killer = median_of_3_killer(n);
            v.assign(killer.begin(), killer.end());
        } else {
            // For other types, generate from int32 killer sequence
            auto killer = median_of_3_killer(n);
            for (size_t i = 0; i < n; ++i) {
                if constexpr (std::is_arithmetic_v<T>)
                    v[i] = static_cast<T>(killer[i]);
                else
                    v[i] = {static_cast<int64_t>(killer[i]), static_cast<int64_t>(i)};
            }
        }
        break;
    }

    default:
        fill_uniform();
        break;
    }

    return v;
}

// ---------------------------------------------------------------------------
// Load real dataset: public timestamp data (Unix epoch seconds)
// Source: generated from public domain log patterns (synthetic but realistic)
// License: public domain (synthetic data)
// ---------------------------------------------------------------------------
inline std::vector<int64_t> load_real_timestamps(size_t n, uint64_t seed) {
    // Synthetic realistic timestamp data: mix of sorted blocks + random gaps
    // Mimics access log timestamps typical of web server logs.
    std::mt19937_64 rng(seed);
    std::vector<int64_t> v;
    v.reserve(n);
    int64_t t = 1700000000LL; // Nov 2023 base
    size_t block_size = 1000;
    while (v.size() < n) {
        // ascending block
        for (size_t i = 0; i < block_size && v.size() < n; ++i) {
            t += std::uniform_int_distribution<int64_t>(0, 60)(rng);
            v.push_back(t);
        }
        // random jump (simulates log rotation / different source)
        if (v.size() < n) {
            t = std::uniform_int_distribution<int64_t>(1600000000LL, 1800000000LL)(rng);
        }
    }
    return v;
}

} // namespace gen

