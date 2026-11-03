// =============================================================================
// enesort.hpp  –  Enesort: Hybrid Microarchitecture-Aware In-Place Sorting
// =============================================================================
// Header-only, templated on RandomIt and Compare.
// Architectural features:
//   F1  Median-of-5 pivot sampling (configurable sample size & ranks)
//   F2  Equal-key "fat-partition" handling (skip equal bucket when P1 == P2)
//   F3  Depth-limit heapsort fallback (introsort-style O(n log n) guarantee)
//   F4  Monotonic run/sortedness check on sub-ranges
//   F5  Configurable insertion cutoff (default 16) + linear/binary mode
//   F6  Smaller-two-first recursion; loop on largest partition
//
// Instrumented build: define ENESORT_COUNT_OPS at compile time to count
// comparisons and swaps separately (do NOT use for timing — overhead is real).
//
// NOT a stable sort.
// =============================================================================

#pragma once

#include <algorithm>     // std::sort, std::reverse, std::make_heap, std::pop_heap
#include <cassert>
#include <cmath>         // std::log2
#include <cstddef>
#include <cstdint>
#include <functional>    // std::less
#include <iterator>
#include <type_traits>
#include <utility>       // std::swap

// ---------------------------------------------------------------------------
// Optional instrumentation
// ---------------------------------------------------------------------------
#if defined(ENESORT_COUNT_OPS) || defined(ECOSORT_COUNT_OPS)
#  include <atomic>
namespace enesort {
    inline std::atomic<uint64_t> g_comparisons{0};
    inline std::atomic<uint64_t> g_swaps{0};
    inline void reset_counters() { g_comparisons = 0; g_swaps = 0; }
    inline uint64_t get_comparisons() { return g_comparisons.load(); }
    inline uint64_t get_swaps()       { return g_swaps.load(); }
}
#  define ENESORT_CMP_INC()  (++::enesort::g_comparisons)
#  define ENESORT_SWP_INC()  (++::enesort::g_swaps)
#else
#  define ENESORT_CMP_INC()  ((void)0)
#  define ENESORT_SWP_INC()  ((void)0)
#endif

// ---------------------------------------------------------------------------
// Feature flags – each can be overridden at compile time
// F1..F4 default ON; F5 linear insertion default OFF (binary ON)
// ---------------------------------------------------------------------------
#ifndef ENESORT_F1_PIVOT_SAMPLE
#  ifdef ECOSORT_F1_PIVOT_SAMPLE
#    define ENESORT_F1_PIVOT_SAMPLE ECOSORT_F1_PIVOT_SAMPLE
#  else
#    define ENESORT_F1_PIVOT_SAMPLE 1
#  endif
#endif

#ifndef ENESORT_F2_EQUAL_KEYS
#  ifdef ECOSORT_F2_EQUAL_KEYS
#    define ENESORT_F2_EQUAL_KEYS ECOSORT_F2_EQUAL_KEYS
#  else
#    define ENESORT_F2_EQUAL_KEYS 1
#  endif
#endif

#ifndef ENESORT_F3_DEPTH_LIMIT
#  ifdef ECOSORT_F3_DEPTH_LIMIT
#    define ENESORT_F3_DEPTH_LIMIT ECOSORT_F3_DEPTH_LIMIT
#  else
#    define ENESORT_F3_DEPTH_LIMIT 1
#  endif
#endif

#ifndef ENESORT_F4_RUN_CHECK
#  ifdef ECOSORT_F4_RUN_CHECK
#    define ENESORT_F4_RUN_CHECK ECOSORT_F4_RUN_CHECK
#  else
#    define ENESORT_F4_RUN_CHECK 1
#  endif
#endif

#ifndef ENESORT_F5_INSERTION_CUTOFF
#  ifdef ECOSORT_F5_INSERTION_CUTOFF
#    define ENESORT_F5_INSERTION_CUTOFF ECOSORT_F5_INSERTION_CUTOFF
#  else
#    define ENESORT_F5_INSERTION_CUTOFF 16
#  endif
#endif
#ifndef ECOSORT_F5_INSERTION_CUTOFF
#  define ECOSORT_F5_INSERTION_CUTOFF ENESORT_F5_INSERTION_CUTOFF
#endif

#ifndef ENESORT_F5_LINEAR_INSERTION
#  ifdef ECOSORT_F5_LINEAR_INSERTION
#    define ENESORT_F5_LINEAR_INSERTION ECOSORT_F5_LINEAR_INSERTION
#  else
#    define ENESORT_F5_LINEAR_INSERTION 0
#  endif
#endif

#ifndef ENESORT_PIVOT_SAMPLE_SIZE
#  ifdef ECOSORT_PIVOT_SAMPLE_SIZE
#    define ENESORT_PIVOT_SAMPLE_SIZE ECOSORT_PIVOT_SAMPLE_SIZE
#  else
#    define ENESORT_PIVOT_SAMPLE_SIZE 5
#  endif
#endif

#ifndef ENESORT_PIVOT_RANK_LO
#  ifdef ECOSORT_PIVOT_RANK_LO
#    define ENESORT_PIVOT_RANK_LO ECOSORT_PIVOT_RANK_LO
#  else
#    define ENESORT_PIVOT_RANK_LO 1
#  endif
#endif

#ifndef ENESORT_PIVOT_RANK_HI
#  ifdef ECOSORT_PIVOT_RANK_HI
#    define ENESORT_PIVOT_RANK_HI ECOSORT_PIVOT_RANK_HI
#  else
#    define ENESORT_PIVOT_RANK_HI 3
#  endif
#endif

#ifndef ENESORT_F4_RUNCHECK_THRESHOLD
#  ifdef ECOSORT_F4_RUNCHECK_THRESHOLD
#    define ENESORT_F4_RUNCHECK_THRESHOLD ECOSORT_F4_RUNCHECK_THRESHOLD
#  else
#    define ENESORT_F4_RUNCHECK_THRESHOLD 32
#  endif
#endif

namespace enesort {

// ---------------------------------------------------------------------------
// Policy configuration struct for Enesort variants & ablations
// ---------------------------------------------------------------------------
template<
    bool F1_PivotSample = (ENESORT_F1_PIVOT_SAMPLE != 0),
    bool F2_EqualKeys   = (ENESORT_F2_EQUAL_KEYS != 0),
    bool F3_DepthLimit  = (ENESORT_F3_DEPTH_LIMIT != 0),
    bool F4_RunCheck    = (ENESORT_F4_RUN_CHECK != 0),
    int  F5_Cutoff      = ENESORT_F5_INSERTION_CUTOFF,
    bool F5_Linear      = (ENESORT_F5_LINEAR_INSERTION != 0),
    int  SampleSize     = ENESORT_PIVOT_SAMPLE_SIZE,
    int  RankLo         = ENESORT_PIVOT_RANK_LO,
    int  RankHi         = ENESORT_PIVOT_RANK_HI,
    int  RunCheckThresh = ENESORT_F4_RUNCHECK_THRESHOLD
>
struct AlgoPolicy {
    static constexpr bool f1 = F1_PivotSample;
    static constexpr bool f2 = F2_EqualKeys;
    static constexpr bool f3 = F3_DepthLimit;
    static constexpr bool f4 = F4_RunCheck;
    static constexpr int  cutoff = F5_Cutoff;
    static constexpr bool linear = F5_Linear;
    static constexpr int  sample_size = SampleSize;
    static constexpr int  rank_lo = RankLo;
    static constexpr int  rank_hi = RankHi;
    static constexpr int  run_thresh = RunCheckThresh;
};

using DefaultPolicy = AlgoPolicy<>;
using NoF1Policy    = AlgoPolicy<false, true, true, true, 16, false, 5, 1, 3, 32>;
using NoF2Policy    = AlgoPolicy<true, false, true, true, 16, false, 5, 1, 3, 32>;
using NoF3Policy    = AlgoPolicy<true, true, false, true, 16, false, 5, 1, 3, 32>;
using NoF4Policy    = AlgoPolicy<true, true, true, false, 16, false, 5, 1, 3, 32>;

template<int K>
using CutoffPolicy  = AlgoPolicy<true, true, true, true, K, false, 5, 1, 3, 32>;

template<int S, int Lo, int Hi>
using SamplePolicy  = AlgoPolicy<true, true, true, true, 16, false, S, Lo, Hi, 32>;

namespace detail {

// ---------------------------------------------------------------------------
// Insertion sort implementations
// ---------------------------------------------------------------------------

template<typename T, typename Cmp>
void binary_insertion_sort(T* arr, std::ptrdiff_t n, Cmp& comp) {
    for (std::ptrdiff_t i = 1; i < n; ++i) {
        T key = std::move(arr[i]);
        std::ptrdiff_t lo = 0;
        std::ptrdiff_t hi = i;
        while (lo < hi) {
            std::ptrdiff_t mid = lo + (hi - lo) / 2;
            ENESORT_CMP_INC();
            if (comp(key, arr[mid]))
                hi = mid;
            else
                lo = mid + 1;
        }
        for (std::ptrdiff_t j = i; j > lo; --j) {
            arr[j] = std::move(arr[j-1]);
            ENESORT_SWP_INC();
        }
        arr[lo] = std::move(key);
    }
}

template<typename T, typename Cmp>
void linear_insertion_sort(T* arr, std::ptrdiff_t n, Cmp& comp) {
    for (std::ptrdiff_t i = 1; i < n; ++i) {
        T key = std::move(arr[i]);
        std::ptrdiff_t j = i - 1;
        while (j >= 0 && (ENESORT_CMP_INC(), comp(key, arr[j]))) {
            arr[j+1] = std::move(arr[j]);
            ENESORT_SWP_INC();
            --j;
        }
        arr[j+1] = std::move(key);
    }
}

template<typename T, typename Cmp, typename Policy>
inline void insertion_sort(T* arr, std::ptrdiff_t n, Cmp& comp) {
    if constexpr (Policy::linear) {
        linear_insertion_sort(arr, n, comp);
    } else {
        binary_insertion_sort(arr, n, comp);
    }
}

// ---------------------------------------------------------------------------
// Heapsort fallback (standard max-heap via make_heap / sort_heap)
// ---------------------------------------------------------------------------
template<typename T, typename Cmp>
void heapsort(T* arr, std::ptrdiff_t n, Cmp& comp) {
    auto wrapped = [&](const T& a, const T& b) -> bool {
        ENESORT_CMP_INC();
        return comp(a, b);
    };
    std::make_heap(arr, arr + n, wrapped);
    for (std::ptrdiff_t i = n; i > 1; --i) {
        ENESORT_SWP_INC();
        using std::swap; swap(arr[0], arr[i-1]);
        std::ptrdiff_t root = 0, end = i - 1;
        while (2 * root + 1 < end) {
            std::ptrdiff_t child = 2 * root + 1;
            if (child + 1 < end && (ENESORT_CMP_INC(), comp(arr[child], arr[child+1])))
                ++child;
            if (ENESORT_CMP_INC(), comp(arr[root], arr[child])) {
                ENESORT_SWP_INC();
                using std::swap; swap(arr[root], arr[child]);
                root = child;
            } else {
                break;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// F1 Pivot Sampling
// ---------------------------------------------------------------------------
template<typename T, typename Cmp, typename Policy>
inline void select_pivots(T* arr, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    if constexpr (!Policy::f1) {
        // v1 behavior: arr[lo] and arr[hi]
        ENESORT_CMP_INC();
        if (comp(arr[hi], arr[lo])) {
            ENESORT_SWP_INC();
            using std::swap; swap(arr[lo], arr[hi]);
        }
        return;
    }

    constexpr int S = Policy::sample_size;
    constexpr int R_lo = Policy::rank_lo;
    constexpr int R_hi = Policy::rank_hi;

    std::ptrdiff_t n = hi - lo + 1;
    if (n < S) {
        ENESORT_CMP_INC();
        if (comp(arr[hi], arr[lo])) {
            ENESORT_SWP_INC();
            using std::swap; swap(arr[lo], arr[hi]);
        }
        return;
    }

    std::ptrdiff_t step = n / (S + 1);
    std::ptrdiff_t sample_idx[16];
    for (int i = 0; i < S; ++i)
        sample_idx[i] = lo + step * (i + 1);

    // Sort sample elements via insertion sort
    for (int i = 1; i < S; ++i) {
        for (int j = i; j > 0; --j) {
            ENESORT_CMP_INC();
            if (comp(arr[sample_idx[j]], arr[sample_idx[j-1]])) {
                ENESORT_SWP_INC();
                using std::swap; swap(arr[sample_idx[j]], arr[sample_idx[j-1]]);
            } else {
                break;
            }
        }
    }

    // Move chosen ranks to arr[lo] and arr[hi]
    ENESORT_SWP_INC();
    using std::swap;
    swap(arr[lo], arr[sample_idx[R_lo]]);
    ENESORT_SWP_INC();
    swap(arr[hi], arr[sample_idx[R_hi]]);
}

// ---------------------------------------------------------------------------
// F4 Sub-range sortedness / reverse run check
// ---------------------------------------------------------------------------
template<typename T, typename Cmp, typename Policy>
inline bool check_and_handle_run(T* arr, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    if constexpr (!Policy::f4) return false;
    std::ptrdiff_t n = hi - lo + 1;
    if (n < Policy::run_thresh) return false;

    bool asc = true, desc = true;
    for (std::ptrdiff_t i = lo; i < hi && (asc || desc); ++i) {
        ENESORT_CMP_INC();
        bool lt = comp(arr[i+1], arr[i]);
        if (lt)  asc  = false;
        if (!lt) desc = false;
    }

    if (asc) return true;
    if (desc) {
        std::reverse(arr + lo, arr + hi + 1);
        return true;
    }
    return false;
}

// ---------------------------------------------------------------------------
// Partition result struct
// ---------------------------------------------------------------------------
struct PartitionResult {
    std::ptrdiff_t lt;
    std::ptrdiff_t gt;
    bool equal_pivots;
};

// ---------------------------------------------------------------------------
// Dual-pivot 3-way partition (Bentley-McIlroy / Yaroslavskiy style)
// ---------------------------------------------------------------------------
template<typename T, typename Cmp, typename Policy>
PartitionResult partition_3way(T* arr, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    select_pivots<T, Cmp, Policy>(arr, lo, hi, comp);

    ENESORT_CMP_INC();
    bool eq_pivots = false;
    if constexpr (Policy::f2) {
        if (!comp(arr[lo], arr[hi]) && !comp(arr[hi], arr[lo]))
            eq_pivots = true;
    }

    std::ptrdiff_t lt = lo + 1;
    std::ptrdiff_t gt = hi - 1;
    std::ptrdiff_t i  = lo + 1;

    while (i <= gt) {
        ENESORT_CMP_INC();
        if (comp(arr[i], arr[lo])) {
            ENESORT_SWP_INC();
            using std::swap; swap(arr[lt++], arr[i++]);
        } else {
            ENESORT_CMP_INC();
            if (comp(arr[hi], arr[i])) {
                while (i < gt) {
                    ENESORT_CMP_INC();
                    if (comp(arr[hi], arr[gt])) --gt;
                    else break;
                }
                ENESORT_SWP_INC();
                using std::swap; swap(arr[i], arr[gt--]);
            } else {
                ++i;
            }
        }
    }

    --lt;
    ++gt;
    ENESORT_SWP_INC();
    using std::swap;
    swap(arr[lo], arr[lt]);
    ENESORT_SWP_INC();
    swap(arr[hi], arr[gt]);

    return { lt, gt, eq_pivots };
}

// ---------------------------------------------------------------------------
// Main Enesort recursive implementation (fixes F1..F6)
// ---------------------------------------------------------------------------
template<typename T, typename Cmp, typename Policy>
void sort_impl(T* arr, std::ptrdiff_t lo, std::ptrdiff_t hi,
               int depth_limit, Cmp& comp) {
    while (hi - lo + 1 > Policy::cutoff) {
        std::ptrdiff_t n = hi - lo + 1;

        // F3: Depth limit check
        if constexpr (Policy::f3) {
            if (depth_limit <= 0) {
                heapsort(arr + lo, n, comp);
                return;
            }
            --depth_limit;
        }

        // F4: Sub-range run check
        if (check_and_handle_run<T, Cmp, Policy>(arr, lo, hi, comp))
            return;

        // Dual-pivot partition
        PartitionResult pr = partition_3way<T, Cmp, Policy>(arr, lo, hi, comp);
        std::ptrdiff_t lt = pr.lt;
        std::ptrdiff_t gt = pr.gt;

        // Range sizes
        std::ptrdiff_t s1 = lt - lo;
        std::ptrdiff_t s2 = (Policy::f2 && pr.equal_pivots) ? 0 : (gt - lt - 1);
        std::ptrdiff_t s3 = hi - gt;

        // F6: Recurse on smaller two, loop on largest
        if (s1 <= s2 && s1 <= s3) {
            if (s1 > 0) sort_impl<T, Cmp, Policy>(arr, lo, lt - 1, depth_limit, comp);
            if (s2 <= s3) {
                if (s2 > 0) sort_impl<T, Cmp, Policy>(arr, lt + 1, gt - 1, depth_limit, comp);
                lo = gt + 1;
            } else {
                if (s3 > 0) sort_impl<T, Cmp, Policy>(arr, gt + 1, hi, depth_limit, comp);
                lo = lt + 1; hi = gt - 1;
            }
        } else if (s2 <= s1 && s2 <= s3) {
            if (s2 > 0) sort_impl<T, Cmp, Policy>(arr, lt + 1, gt - 1, depth_limit, comp);
            if (s1 <= s3) {
                if (s1 > 0) sort_impl<T, Cmp, Policy>(arr, lo, lt - 1, depth_limit, comp);
                lo = gt + 1;
            } else {
                if (s3 > 0) sort_impl<T, Cmp, Policy>(arr, gt + 1, hi, depth_limit, comp);
                hi = lt - 1;
            }
        } else {
            if (s3 > 0) sort_impl<T, Cmp, Policy>(arr, gt + 1, hi, depth_limit, comp);
            if (s1 <= s2) {
                if (s1 > 0) sort_impl<T, Cmp, Policy>(arr, lo, lt - 1, depth_limit, comp);
                lo = lt + 1; hi = gt - 1;
            } else {
                if (s2 > 0) sort_impl<T, Cmp, Policy>(arr, lt + 1, gt - 1, depth_limit, comp);
                hi = lt - 1;
            }
        }
    }

    // Small sub-range insertion sort
    if (hi > lo) {
        insertion_sort<T, Cmp, Policy>(arr + lo, hi - lo + 1, comp);
    }
}

} // namespace detail

// ---------------------------------------------------------------------------
// Policy-parameterized sort
// ---------------------------------------------------------------------------
template<typename Policy = DefaultPolicy, typename RandomIt, typename Cmp = std::less<>>
void sort_policy(RandomIt first, RandomIt last, Cmp comp = {}) {
    using T = typename std::iterator_traits<RandomIt>::value_type;
    std::ptrdiff_t n = last - first;
    if (n < 2) return;

    // Top-level monotonic pre-scan
    bool asc = true, desc = true;
    for (std::ptrdiff_t i = 0; i < n - 1 && (asc || desc); ++i) {
        ENESORT_CMP_INC();
        bool lt = comp(first[i+1], first[i]);
        if (lt)  asc  = false;
        if (!lt) desc = false;
    }
    if (asc) return;
    if (desc) {
        std::reverse(first, last);
        return;
    }

    if (n <= Policy::cutoff) {
        detail::insertion_sort<T, Cmp, Policy>(&(*first), n, comp);
        return;
    }

    int depth_limit = 2 * static_cast<int>(std::floor(std::log2(static_cast<double>(n))));
    T* arr = &(*first);
    detail::sort_impl<T, Cmp, Policy>(arr, 0, n - 1, depth_limit, comp);
}

// ---------------------------------------------------------------------------
// Standard Enesort entry points
// ---------------------------------------------------------------------------
template<typename RandomIt, typename Cmp = std::less<>>
void sort(RandomIt first, RandomIt last, Cmp comp = {}) {
    sort_policy<DefaultPolicy>(first, last, comp);
}

} // namespace enesort

// Backwards-compatibility alias: ecosort -> enesort
namespace ecosort {
    using namespace enesort;
}
