// =============================================================================
// enesort.hpp  –  Enesort: Microarchitecture-Aware Hybrid In-Place Sorting
// =============================================================================
// Header-only, templated on RandomIt and Compare.
// Architectural features:
//   F1  Median-of-5 pivot sampling with 5-element sorting network
//   F2  Equal-key fat-partition handling (Bentley-McIlroy duplicate elimination)
//   F3  Depth-limit heapsort fallback (introsort-style O(N log N) guarantee)
//   F4  Monotonic run / sortedness check with linear-time reversal
//   F5  Microarchitecture-tuned insertion cutoff (default 32)
//   F6  Smaller-two-first recursion with loop on largest partition (O(log N) stack)
//
// Guaranteed invariants:
//   - Time complexity: Worst-case O(N log N), Best-case O(N)
//   - Auxiliary heap memory: O(1) strictly in-place (zero dynamic allocations)
//   - Auxiliary stack depth: <= 2 * floor(log2 N) + O(1) frames (< 65 for any N)
// =============================================================================

#pragma once

#include <algorithm>     // std::swap, std::reverse, std::make_heap, std::sort_heap
#include <cassert>
#include <cmath>         // std::log2, std::floor
#include <cstddef>
#include <cstdint>
#include <functional>    // std::less
#include <iterator>
#include <type_traits>
#include <utility>

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
// Feature flags – compile-time defaults
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
#    define ENESORT_F5_INSERTION_CUTOFF 32
#  endif
#endif
#ifndef ECOSORT_F5_INSERTION_CUTOFF
#  define ECOSORT_F5_INSERTION_CUTOFF ENESORT_F5_INSERTION_CUTOFF
#endif

#ifndef ENESORT_F5_LINEAR_INSERTION
#  ifdef ECOSORT_F5_LINEAR_INSERTION
#    define ENESORT_F5_LINEAR_INSERTION ECOSORT_F5_LINEAR_INSERTION
#  else
#    define ENESORT_F5_LINEAR_INSERTION 1
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
using NoF1Policy    = AlgoPolicy<false, true, true, true, 32, true, 5, 1, 3, 32>;
using NoF2Policy    = AlgoPolicy<true, false, true, true, 32, true, 5, 1, 3, 32>;
using NoF3Policy    = AlgoPolicy<true, true, false, true, 32, true, 5, 1, 3, 32>;
using NoF4Policy    = AlgoPolicy<true, true, true, false, 32, true, 5, 1, 3, 32>;

template<int K>
using CutoffPolicy  = AlgoPolicy<true, true, true, true, K, true, 5, 1, 3, 32>;

template<int S, int Lo, int Hi>
using SamplePolicy  = AlgoPolicy<true, true, true, true, 32, true, S, Lo, Hi, 32>;

namespace detail {

// ---------------------------------------------------------------------------
// High-efficiency insertion sort
// ---------------------------------------------------------------------------
template<typename T, typename Cmp>
inline void linear_insertion_sort(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    for (std::ptrdiff_t i = lo + 1; i <= hi; ++i) {
        T key = std::move(a[i]);
        std::ptrdiff_t j = i - 1;
        while (j >= lo && (ENESORT_CMP_INC(), comp(key, a[j]))) {
            ENESORT_SWP_INC();
            a[j + 1] = std::move(a[j]);
            --j;
        }
        a[j + 1] = std::move(key);
    }
}

template<typename T, typename Cmp>
inline void binary_insertion_sort(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    for (std::ptrdiff_t i = lo + 1; i <= hi; ++i) {
        T key = std::move(a[i]);
        std::ptrdiff_t left = lo;
        std::ptrdiff_t right = i;
        while (left < right) {
            std::ptrdiff_t mid = left + (right - left) / 2;
            ENESORT_CMP_INC();
            if (comp(key, a[mid]))
                right = mid;
            else
                left = mid + 1;
        }
        for (std::ptrdiff_t j = i; j > left; --j) {
            ENESORT_SWP_INC();
            a[j] = std::move(a[j - 1]);
        }
        a[left] = std::move(key);
    }
}

template<typename T, typename Cmp, typename Policy>
inline void insertion_sort(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    if constexpr (Policy::linear) {
        linear_insertion_sort(a, lo, hi, comp);
    } else {
        binary_insertion_sort(a, lo, hi, comp);
    }
}

// ---------------------------------------------------------------------------
// In-place heapsort fallback (F3 guarantee)
// ---------------------------------------------------------------------------
template<typename T, typename Cmp>
inline void heapsort(T* arr, std::ptrdiff_t n, Cmp& comp) {
    auto wrapped = [&](const T& x, const T& y) -> bool {
        ENESORT_CMP_INC();
        return comp(x, y);
    };
    std::make_heap(arr, arr + n, wrapped);
    for (std::ptrdiff_t i = n; i > 1; --i) {
        ENESORT_SWP_INC();
        using std::swap;
        swap(arr[0], arr[i - 1]);
        std::ptrdiff_t root = 0, end = i - 1;
        while (2 * root + 1 < end) {
            std::ptrdiff_t child = 2 * root + 1;
            if (child + 1 < end && (ENESORT_CMP_INC(), comp(arr[child], arr[child + 1])))
                ++child;
            if (ENESORT_CMP_INC(), comp(arr[root], arr[child])) {
                ENESORT_SWP_INC();
                using std::swap;
                swap(arr[root], arr[child]);
                root = child;
            } else {
                break;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// 5-element sorting network for optimal pivot selection
// ---------------------------------------------------------------------------
template<typename T, typename Cmp>
inline void sort5(T& a, T& b, T& c, T& d, T& e, Cmp& comp) {
    auto cmp_swap = [&](T& x, T& y) {
        ENESORT_CMP_INC();
        if (comp(y, x)) {
            ENESORT_SWP_INC();
            using std::swap; swap(x, y);
        }
    };
    cmp_swap(a, b);
    cmp_swap(c, d);
    ENESORT_CMP_INC();
    if (comp(c, a)) {
        ENESORT_SWP_INC();
        using std::swap; swap(a, c); swap(b, d);
    }
    cmp_swap(c, e);
    ENESORT_CMP_INC();
    if (comp(c, b)) {
        ENESORT_SWP_INC();
        using std::swap; swap(b, c);
        cmp_swap(a, b);
    }
    cmp_swap(d, e);
    ENESORT_CMP_INC();
    if (comp(d, c)) {
        ENESORT_SWP_INC();
        using std::swap; swap(c, d);
        cmp_swap(b, c);
    }
    cmp_swap(d, e);
}

// ---------------------------------------------------------------------------
// Pivot selection (F1)
// ---------------------------------------------------------------------------
template<typename T, typename Cmp, typename Policy>
inline void select_pivots(T* arr, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    if constexpr (!Policy::f1) {
        ENESORT_CMP_INC();
        if (comp(arr[hi], arr[lo])) {
            ENESORT_SWP_INC();
            using std::swap; swap(arr[lo], arr[hi]);
        }
        return;
    }

    std::ptrdiff_t len = hi - lo + 1;
    if (len < 5) {
        ENESORT_CMP_INC();
        if (comp(arr[hi], arr[lo])) {
            ENESORT_SWP_INC();
            using std::swap; swap(arr[lo], arr[hi]);
        }
        return;
    }

    std::ptrdiff_t step = len / 6;
    std::ptrdiff_t m1 = lo + step;
    std::ptrdiff_t m2 = lo + 2 * step;
    std::ptrdiff_t m3 = lo + 3 * step;
    std::ptrdiff_t m4 = lo + 4 * step;
    std::ptrdiff_t m5 = lo + 5 * step;

    sort5(arr[m1], arr[m2], arr[m3], arr[m4], arr[m5], comp);

    ENESORT_SWP_INC();
    using std::swap;
    swap(arr[m2], arr[lo]);
    ENESORT_SWP_INC();
    swap(arr[m4], arr[hi]);
}

// ---------------------------------------------------------------------------
// Sub-range sortedness / reverse run check (F4)
// ---------------------------------------------------------------------------
template<typename T, typename Cmp, typename Policy>
inline bool check_and_handle_run(T* arr, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    if constexpr (!Policy::f4) return false;
    std::ptrdiff_t n = hi - lo + 1;
    if (n < Policy::run_thresh) return false;

    bool asc = true, desc = true;
    for (std::ptrdiff_t i = lo; i < hi && (asc || desc); ++i) {
        ENESORT_CMP_INC();
        bool lt = comp(arr[i + 1], arr[i]);
        if (lt) asc = false;
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
// Main recursive Enesort implementation (F1--F6)
// ---------------------------------------------------------------------------
template<typename T, typename Cmp, typename Policy>
void sort_impl(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, int depth_limit, Cmp& comp) {
    while (hi - lo >= Policy::cutoff) {
        // F3: Depth limit fallback to heapsort
        if constexpr (Policy::f3) {
            if (depth_limit <= 0) {
                heapsort(a + lo, hi - lo + 1, comp);
                return;
            }
            --depth_limit;
        }

        // F1: Pivot selection
        select_pivots<T, Cmp, Policy>(a, lo, hi, comp);

        const T p1 = a[lo];
        const T p2 = a[hi];

        // F2: Bentley-McIlroy equal pivot check
        bool eq_pivots = false;
        if constexpr (Policy::f2) {
            ENESORT_CMP_INC();
            if (!comp(p1, p2) && (ENESORT_CMP_INC(), !comp(p2, p1))) {
                eq_pivots = true;
            }
        }

        std::ptrdiff_t less = lo + 1;
        std::ptrdiff_t great = hi - 1;
        std::ptrdiff_t k = less;

        if (eq_pivots) {
            // Fat equal partition (< p1, == p1, > p1)
            while (k <= great) {
                ENESORT_CMP_INC();
                if (comp(a[k], p1)) {
                    if (k != less) {
                        ENESORT_SWP_INC();
                        using std::swap; swap(a[k], a[less]);
                    }
                    ++less;
                    ++k;
                } else {
                    ENESORT_CMP_INC();
                    if (comp(p1, a[k])) {
                        while (k < great && (ENESORT_CMP_INC(), comp(p1, a[great]))) --great;
                        if (k != great) {
                            ENESORT_SWP_INC();
                            using std::swap; swap(a[k], a[great]);
                        }
                        --great;
                    } else {
                        ++k;
                    }
                }
            }
        } else {
            // High-throughput dual-pivot partition
            while (k <= great) {
                const T ak = a[k];
                ENESORT_CMP_INC();
                if (comp(ak, p1)) {
                    if (k != less) {
                        ENESORT_SWP_INC();
                        a[k] = std::move(a[less]);
                        a[less] = std::move(ak);
                    }
                    ++less;
                } else {
                    ENESORT_CMP_INC();
                    if (comp(p2, ak)) {
                        while (k < great && (ENESORT_CMP_INC(), comp(p2, a[great]))) --great;
                        if (k != great) {
                            ENESORT_SWP_INC();
                            a[k] = std::move(a[great]);
                            a[great] = std::move(ak);
                        }
                        --great;
                        ENESORT_CMP_INC();
                        if (comp(a[k], p1)) {
                            if (k != less) {
                                ENESORT_SWP_INC();
                                T tmp = std::move(a[k]);
                                a[k] = std::move(a[less]);
                                a[less] = std::move(tmp);
                            }
                            ++less;
                        }
                    }
                }
                ++k;
            }
        }

        ENESORT_SWP_INC();
        using std::swap;
        swap(a[lo], a[less - 1]);
        ENESORT_SWP_INC();
        swap(a[hi], a[great + 1]);

        std::ptrdiff_t s1 = (less - 1) - lo;
        std::ptrdiff_t s2 = eq_pivots ? 0 : (great - less + 1);
        std::ptrdiff_t s3 = hi - (great + 1);

        // F6: Recurse on smaller two, loop on largest
        if (s1 <= s2 && s1 <= s3) {
            if (s1 > 1) sort_impl<T, Cmp, Policy>(a, lo, less - 2, depth_limit, comp);
            if (s2 <= s3) {
                if (s2 > 1) sort_impl<T, Cmp, Policy>(a, less, great, depth_limit, comp);
                lo = great + 2;
            } else {
                if (s3 > 1) sort_impl<T, Cmp, Policy>(a, great + 2, hi, depth_limit, comp);
                lo = less; hi = great;
            }
        } else if (s2 <= s1 && s2 <= s3) {
            if (s2 > 1) sort_impl<T, Cmp, Policy>(a, less, great, depth_limit, comp);
            if (s1 <= s3) {
                if (s1 > 1) sort_impl<T, Cmp, Policy>(a, lo, less - 2, depth_limit, comp);
                lo = great + 2;
            } else {
                if (s3 > 1) sort_impl<T, Cmp, Policy>(a, great + 2, hi, depth_limit, comp);
                hi = less - 2;
            }
        } else {
            if (s3 > 1) sort_impl<T, Cmp, Policy>(a, great + 2, hi, depth_limit, comp);
            if (s1 <= s2) {
                if (s1 > 1) sort_impl<T, Cmp, Policy>(a, lo, less - 2, depth_limit, comp);
                lo = less; hi = great;
            } else {
                if (s2 > 1) sort_impl<T, Cmp, Policy>(a, less, great, depth_limit, comp);
                hi = less - 2;
            }
        }
    }

    if (hi > lo) {
        insertion_sort<T, Cmp, Policy>(a, lo, hi, comp);
    }
}

} // namespace detail

// ---------------------------------------------------------------------------
// Policy-parameterized sort entry point
// ---------------------------------------------------------------------------
template<typename Policy = DefaultPolicy, typename RandomIt, typename Cmp = std::less<>>
void sort_policy(RandomIt first, RandomIt last, Cmp comp = {}) {
    using T = typename std::iterator_traits<RandomIt>::value_type;
    std::ptrdiff_t n = last - first;
    if (n < 2) return;

    // F4: Top-level linear-time monotonic run check
    if constexpr (Policy::f4) {
        bool asc = true, desc = true;
        for (std::ptrdiff_t i = 0; i < n - 1 && (asc || desc); ++i) {
            ENESORT_CMP_INC();
            bool lt = comp(first[i + 1], first[i]);
            if (lt) asc = false;
            if (!lt) desc = false;
        }
        if (asc) return;
        if (desc) {
            std::reverse(first, last);
            return;
        }
    }

    if (n <= Policy::cutoff) {
        detail::insertion_sort<T, Cmp, Policy>(&(*first), 0, n - 1, comp);
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
