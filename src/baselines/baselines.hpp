// =============================================================================
// baselines.hpp  –  Thin wrappers around all baseline sorting algorithms
// =============================================================================
// Each baseline exposes the same interface:
//   void sort(T* begin, T* end, Cmp comp);
// Compile guards ensure missing third-party headers degrade gracefully.
// =============================================================================

#pragma once

#include <algorithm>
#include <functional>
#include <iterator>
#include <stdexcept>
#include <type_traits>
#include <utility>
#include <vector>

// ---------------------------------------------------------------------------
// 1. std::sort
// ---------------------------------------------------------------------------
namespace bl_std_sort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::sort(first, last, comp);
    }
}

// ---------------------------------------------------------------------------
// 2. std::stable_sort
// ---------------------------------------------------------------------------
namespace bl_stable_sort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::stable_sort(first, last, comp);
    }
}

// ---------------------------------------------------------------------------
// 3. std::sort with is_sorted / reverse pre-check
// ---------------------------------------------------------------------------
namespace bl_std_sort_precheck {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        if (std::is_sorted(first, last, comp)) return;
        // check reverse
        bool rev = true;
        for (T* p = first; p+1 < last && rev; ++p)
            if (comp(*p, *(p+1))) rev = false;
        if (rev) { std::reverse(first, last); return; }
        std::sort(first, last, comp);
    }
}

// ---------------------------------------------------------------------------
// 4. HeapSort
// ---------------------------------------------------------------------------
namespace bl_heapsort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::make_heap(first, last, comp);
        std::sort_heap(first, last, comp);
    }
}

// ---------------------------------------------------------------------------
// 5. Single-pivot Median-of-3 Quicksort (same insertion cutoff as EcoSort)
// ---------------------------------------------------------------------------
namespace bl_mo3_quicksort {
    namespace detail {
        template<typename T, typename Cmp>
        void insertion(T* arr, std::ptrdiff_t n, Cmp& comp) {
            for (std::ptrdiff_t i = 1; i < n; ++i) {
                T key = std::move(arr[i]);
                std::ptrdiff_t j = i - 1;
                while (j >= 0 && comp(key, arr[j])) { arr[j+1] = std::move(arr[j]); --j; }
                arr[j+1] = std::move(key);
            }
        }
        template<typename T, typename Cmp>
        void qsort_impl(T* arr, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
            while (hi - lo >= ENESORT_F5_INSERTION_CUTOFF) {
                std::ptrdiff_t mid = lo + (hi - lo) / 2;
                if (comp(arr[mid], arr[lo])) std::swap(arr[lo], arr[mid]);
                if (comp(arr[hi],  arr[lo])) std::swap(arr[lo], arr[hi]);
                if (comp(arr[hi], arr[mid])) std::swap(arr[mid], arr[hi]);
                // arr[lo] <= arr[mid] <= arr[hi]
                std::swap(arr[mid], arr[hi-1]);
                T& pivot = arr[hi-1];

                std::ptrdiff_t i = lo;
                std::ptrdiff_t j = hi - 1;
                while (true) {
                    while (comp(arr[++i], pivot)) {}
                    while (comp(pivot, arr[--j])) {}
                    if (i >= j) break;
                    std::swap(arr[i], arr[j]);
                }
                std::swap(arr[i], arr[hi-1]); // restore pivot

                // Recurse smaller, loop larger
                if (i - lo < hi - i) {
                    if (i > lo + 1) qsort_impl(arr, lo, i - 1, comp);
                    lo = i + 1;
                } else {
                    if (hi > i + 1) qsort_impl(arr, i + 1, hi, comp);
                    hi = i - 1;
                }
            }
            if (hi > lo) {
                insertion(arr + lo, hi - lo + 1, comp);
            }
        }
    }
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::ptrdiff_t n = last - first;
        if (n < 2) return;
        detail::qsort_impl(first, 0, n-1, comp);
    }
}

// ---------------------------------------------------------------------------
// 6. Yaroslavskiy Dual-Pivot Quicksort (Java-style C++ port)
// ---------------------------------------------------------------------------
namespace bl_yaroslavskiy {
    namespace detail {
        template<typename T, typename Cmp>
        void insertion(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
            for (std::ptrdiff_t i = lo+1; i <= hi; ++i) {
                T key = std::move(a[i]);
                std::ptrdiff_t j = i-1;
                while (j >= lo && comp(key, a[j])) { a[j+1] = std::move(a[j]); --j; }
                a[j+1] = std::move(key);
            }
        }
        template<typename T, typename Cmp>
        void ysort(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
            if (hi - lo < 27) { insertion(a, lo, hi, comp); return; }
            std::ptrdiff_t seventh = (hi - lo + 1) / 7;
            std::ptrdiff_t e3 = lo + (hi - lo) / 2;
            std::ptrdiff_t e2 = e3 - seventh, e4 = e3 + seventh;
            std::ptrdiff_t e1 = lo, e5 = hi;
            // sort e1..e5
            if (comp(a[e2], a[e1])) std::swap(a[e1], a[e2]);
            if (comp(a[e3], a[e2])) std::swap(a[e2], a[e3]);
            if (comp(a[e2], a[e1])) std::swap(a[e1], a[e2]);
            if (comp(a[e4], a[e3])) std::swap(a[e3], a[e4]);
            if (comp(a[e3], a[e2])) std::swap(a[e2], a[e3]);
            if (comp(a[e5], a[e4])) std::swap(a[e4], a[e5]);
            if (comp(a[e4], a[e3])) std::swap(a[e3], a[e4]);
            if (comp(a[e3], a[e2])) std::swap(a[e2], a[e3]);
            // p1 = a[e2], p2 = a[e4]
            std::swap(a[e2], a[lo]); std::swap(a[e4], a[hi]);
            std::ptrdiff_t less = lo+1, great = hi-1;
            std::ptrdiff_t k = less;
            while (k <= great) {
                if (comp(a[k], a[lo])) {
                    std::swap(a[k], a[less++]);
                } else if (comp(a[hi], a[k])) {
                    while (k < great && comp(a[hi], a[great])) --great;
                    std::swap(a[k], a[great--]);
                    if (comp(a[k], a[lo])) std::swap(a[k], a[less++]);
                }
                ++k;
            }
            std::ptrdiff_t dist1 = less - lo - 1;
            std::ptrdiff_t dist2 = hi - great - 1;
            std::swap(a[lo], a[less-1]);
            std::swap(a[hi], a[great+1]);
            ysort(a, lo, less-2, comp);
            ysort(a, great+2, hi, comp);

            // Middle partition: only sort if pivots are distinct
            if (comp(a[less-1], a[great+1])) {
                while (less <= great && !comp(a[less-1], a[less])) ++less;
                while (less <= great && !comp(a[great], a[great+1])) --great;
                if (less < great) {
                    ysort(a, less, great, comp);
                }
            }
        }
    }
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::ptrdiff_t n = last - first;
        if (n < 2) return;
        detail::ysort(first, 0, n-1, comp);
    }
}

// ---------------------------------------------------------------------------
// 7. Optimized MergeSort (one pre-allocated buffer, insertion cutoff)
// ---------------------------------------------------------------------------
namespace bl_mergesort {
    namespace detail {
        template<typename T, typename Cmp>
        void insertion(T* a, std::ptrdiff_t n, Cmp& comp) {
            for (std::ptrdiff_t i = 1; i < n; ++i) {
                T key = std::move(a[i]);
                std::ptrdiff_t j = i-1;
                while (j >= 0 && comp(key, a[j])) { a[j+1] = std::move(a[j]); --j; }
                a[j+1] = std::move(key);
            }
        }
        template<typename T, typename Cmp>
        void merge_impl(T* a, std::ptrdiff_t lo, std::ptrdiff_t mid,
                        std::ptrdiff_t hi, T* buf, Cmp& comp) {
            for (std::ptrdiff_t i = lo; i <= hi; ++i) buf[i] = std::move(a[i]);
            std::ptrdiff_t i = lo, j = mid+1, k = lo;
            while (i <= mid && j <= hi) {
                if (!comp(buf[j], buf[i])) a[k++] = std::move(buf[i++]);
                else                       a[k++] = std::move(buf[j++]);
            }
            while (i <= mid) a[k++] = std::move(buf[i++]);
            while (j <= hi)  a[k++] = std::move(buf[j++]);
        }
        template<typename T, typename Cmp>
        void msort(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, T* buf, Cmp& comp) {
            if (hi - lo < 32) { insertion(a + lo, hi - lo + 1, comp); return; }
            std::ptrdiff_t mid = lo + (hi - lo) / 2;
            msort(a, lo, mid, buf, comp);
            msort(a, mid+1, hi, buf, comp);
            if (!comp(a[mid+1], a[mid])) return; // already sorted
            merge_impl(a, lo, mid, hi, buf, comp);
        }
    }
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::ptrdiff_t n = last - first;
        if (n < 2) return;
        std::vector<T> buf(n);
        detail::msort(first, 0, n-1, buf.data(), comp);
    }
}

// ---------------------------------------------------------------------------
// 8. pdqsort (Orson Peters) – vendored via CMake FetchContent
// ---------------------------------------------------------------------------
#ifdef HAS_PDQSORT
#include "pdqsort.h"
namespace bl_pdqsort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        pdqsort(first, last, comp);
    }
}
#else
namespace bl_pdqsort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        // fallback to std::sort when pdqsort not available
        std::sort(first, last, comp);
    }
}
#endif

// ---------------------------------------------------------------------------
// 9. IPS4o – sequential mode (vendored via CMake FetchContent)
// ---------------------------------------------------------------------------
#ifdef HAS_IPS4O
#include "ips4o.hpp"
namespace bl_ips4o {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        ips4o::sort(first, last, comp);
    }
}
#else
namespace bl_ips4o {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::sort(first, last, comp);
    }
}
#endif

// ---------------------------------------------------------------------------
// 10. gfx::timsort – vendored via CMake FetchContent
// ---------------------------------------------------------------------------
#ifdef HAS_TIMSORT
#include "timsort.hpp"
namespace bl_timsort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        gfx::timsort(first, last, comp);
    }
}
#else
namespace bl_timsort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::stable_sort(first, last, comp);  // proxy
    }
}
#endif

// ---------------------------------------------------------------------------
// 11. BlockQuicksort (Edelkamp & Weiss)
// ---------------------------------------------------------------------------
#ifdef HAS_BLOCKQUICKSORT
#include "BlockQuicksort/BlockQuicksort.h"
namespace bl_blockqs {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        blocked_sort(first, last, comp);
    }
}
#else
namespace bl_blockqs {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::sort(first, last, comp);
    }
}
#endif

// ---------------------------------------------------------------------------
// 12. Highway vqsort (optional)
// ---------------------------------------------------------------------------
#ifdef HAS_HIGHWAY_VQSORT
#include "hwy/contrib/sort/vqsort.h"
namespace bl_vqsort {
    // vqsort only works for specific types; wrap gracefully
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        // Highway vqsort doesn't take custom comparators in simple form
        // Only supports ascending for numeric types
        if constexpr (std::is_same_v<Cmp, std::less<T>> &&
                      (std::is_same_v<T, int32_t> || std::is_same_v<T, int64_t> ||
                       std::is_same_v<T, float>   || std::is_same_v<T, double>)) {
            hwy::HWY_NAMESPACE::VQSort(first, last - first, hwy::SortAscending());
        } else {
            std::sort(first, last, comp);
        }
    }
}
#else
namespace bl_vqsort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        std::sort(first, last, comp);
    }
}
#endif

// ---------------------------------------------------------------------------
// Enesort baseline wrapper (from enesort.hpp)
// ---------------------------------------------------------------------------
#include "../enesort.hpp"

namespace bl_enesort {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        enesort::sort(first, last, comp);
    }
}
namespace bl_ecosort_v2 = bl_enesort;

// ---------------------------------------------------------------------------
// Enesort Ablations & Studies
// ---------------------------------------------------------------------------
namespace bl_enesort_no_f1 {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        enesort::sort_policy<enesort::NoF1Policy>(first, last, comp);
    }
}
namespace bl_ecosort_no_f1 = bl_enesort_no_f1;

namespace bl_enesort_no_f2 {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        enesort::sort_policy<enesort::NoF2Policy>(first, last, comp);
    }
}
namespace bl_ecosort_no_f2 = bl_enesort_no_f2;

namespace bl_enesort_no_f3 {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        enesort::sort_policy<enesort::NoF3Policy>(first, last, comp);
    }
}
namespace bl_ecosort_no_f3 = bl_enesort_no_f3;

namespace bl_enesort_no_f4 {
    template<typename T, typename Cmp = std::less<T>>
    void sort(T* first, T* last, Cmp comp = {}) {
        enesort::sort_policy<enesort::NoF4Policy>(first, last, comp);
    }
}
namespace bl_ecosort_no_f4 = bl_enesort_no_f4;

// Cutoff sweep
template<int K>
struct bl_enesort_cutoff {
    template<typename T, typename Cmp = std::less<T>>
    static void sort(T* first, T* last, Cmp comp = {}) {
        enesort::sort_policy<enesort::CutoffPolicy<K>>(first, last, comp);
    }
};
template<int K>
using bl_ecosort_cutoff = bl_enesort_cutoff<K>;

// Sample study
template<int S, int Lo, int Hi>
struct bl_enesort_sample {
    template<typename T, typename Cmp = std::less<T>>
    static void sort(T* first, T* last, Cmp comp = {}) {
        enesort::sort_policy<enesort::SamplePolicy<S, Lo, Hi>>(first, last, comp);
    }
};
template<int S, int Lo, int Hi>
using bl_ecosort_sample = bl_enesort_sample<S, Lo, Hi>;

