#include <iostream>
#include <vector>
#include <chrono>
#include <random>
#include <algorithm>
#include "../src/enesort.hpp"
#include "../src/baselines/baselines.hpp"

namespace enesort_opt2 {

template<typename T, typename Cmp>
inline void insertion_sort(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, Cmp& comp) {
    for (std::ptrdiff_t i = lo + 1; i <= hi; ++i) {
        T key = a[i];
        std::ptrdiff_t j = i - 1;
        while (j >= lo && comp(key, a[j])) {
            a[j + 1] = a[j];
            --j;
        }
        a[j + 1] = key;
    }
}

template<typename T, typename Cmp>
inline void heapsort(T* arr, std::ptrdiff_t n, Cmp& comp) {
    std::make_heap(arr, arr + n, comp);
    std::sort_heap(arr, arr + n, comp);
}

// Unrolled sorting network for 5 elements
template<typename T, typename Cmp>
inline void sort5(T& a, T& b, T& c, T& d, T& e, Cmp& comp) {
    if (comp(b, a)) std::swap(a, b);
    if (comp(d, c)) std::swap(c, d);
    if (comp(c, a)) { std::swap(a, c); std::swap(b, d); }
    if (comp(e, c)) std::swap(c, e);
    if (comp(c, b)) { std::swap(b, c); if (comp(b, a)) std::swap(a, b); }
    if (comp(e, d)) std::swap(d, e);
    if (comp(d, c)) { std::swap(c, d); if (comp(c, b)) std::swap(b, c); }
    if (comp(e, d)) std::swap(d, e);
}

template<typename T, typename Cmp>
void sort_impl(T* a, std::ptrdiff_t lo, std::ptrdiff_t hi, int depth_limit, Cmp& comp) {
    while (hi - lo >= 32) {
        if (depth_limit <= 0) {
            heapsort(a + lo, hi - lo + 1, comp);
            return;
        }
        --depth_limit;

        std::ptrdiff_t len = hi - lo + 1;
        std::ptrdiff_t step = len / 6;
        std::ptrdiff_t m1 = lo + step;
        std::ptrdiff_t m2 = lo + 2 * step;
        std::ptrdiff_t m3 = lo + 3 * step;
        std::ptrdiff_t m4 = lo + 4 * step;
        std::ptrdiff_t m5 = lo + 5 * step;

        sort5(a[m1], a[m2], a[m3], a[m4], a[m5], comp);

        std::swap(a[m2], a[lo]);
        std::swap(a[m4], a[hi]);

        const T p1 = a[lo];
        const T p2 = a[hi];
        bool eq_pivots = (!comp(p1, p2) && !comp(p2, p1));

        std::ptrdiff_t less = lo + 1;
        std::ptrdiff_t great = hi - 1;
        std::ptrdiff_t k = less;

        if (eq_pivots) {
            while (k <= great) {
                if (comp(a[k], p1)) {
                    if (k != less) std::swap(a[k], a[less]);
                    ++less;
                    ++k;
                } else if (comp(p1, a[k])) {
                    while (k < great && comp(p1, a[great])) --great;
                    if (k != great) std::swap(a[k], a[great]);
                    --great;
                } else {
                    ++k;
                }
            }
        } else {
            // High-throughput dual-pivot partitioning
            while (k <= great) {
                const T ak = a[k];
                if (comp(ak, p1)) {
                    if (k != less) {
                        a[k] = a[less];
                        a[less] = ak;
                    }
                    ++less;
                } else if (comp(p2, ak)) {
                    while (k < great && comp(p2, a[great])) --great;
                    if (k != great) {
                        const T ag = a[great];
                        a[great] = ak;
                        a[k] = ag;
                    }
                    --great;
                    if (comp(a[k], p1)) {
                        if (k != less) {
                            const T tmp = a[k];
                            a[k] = a[less];
                            a[less] = tmp;
                        }
                        ++less;
                    }
                }
                ++k;
            }
        }

        a[lo] = a[less - 1];
        a[less - 1] = p1;
        a[hi] = a[great + 1];
        a[great + 1] = p2;

        std::ptrdiff_t s1 = (less - 1) - lo;
        std::ptrdiff_t s2 = eq_pivots ? 0 : (great - less + 1);
        std::ptrdiff_t s3 = hi - (great + 1);

        // Recurse smaller, loop largest
        if (s1 <= s2 && s1 <= s3) {
            if (s1 > 1) sort_impl(a, lo, less - 2, depth_limit, comp);
            if (s2 <= s3) {
                if (s2 > 1) sort_impl(a, less, great, depth_limit, comp);
                lo = great + 2;
            } else {
                if (s3 > 1) sort_impl(a, great + 2, hi, depth_limit, comp);
                lo = less; hi = great;
            }
        } else if (s2 <= s1 && s2 <= s3) {
            if (s2 > 1) sort_impl(a, less, great, depth_limit, comp);
            if (s1 <= s3) {
                if (s1 > 1) sort_impl(a, lo, less - 2, depth_limit, comp);
                lo = great + 2;
            } else {
                if (s3 > 1) sort_impl(a, great + 2, hi, depth_limit, comp);
                hi = less - 2;
            }
        } else {
            if (s3 > 1) sort_impl(a, great + 2, hi, depth_limit, comp);
            if (s1 <= s2) {
                if (s1 > 1) sort_impl(a, lo, less - 2, depth_limit, comp);
                lo = less; hi = great;
            } else {
                if (s2 > 1) sort_impl(a, less, great, depth_limit, comp);
                hi = less - 2;
            }
        }
    }
    if (hi > lo) {
        insertion_sort(a, lo, hi, comp);
    }
}

template<typename T, typename Cmp = std::less<T>>
void sort(T* first, T* last, Cmp comp = {}) {
    std::ptrdiff_t n = last - first;
    if (n < 2) return;

    // Top-level monotonic run check
    bool asc = true, desc = true;
    for (std::ptrdiff_t i = 0; i < n - 1 && (asc || desc); ++i) {
        bool lt = comp(first[i + 1], first[i]);
        if (lt) asc = false;
        if (!lt) desc = false;
    }
    if (asc) return;
    if (desc) {
        std::reverse(first, last);
        return;
    }

    if (n <= 32) {
        insertion_sort(first, 0, n - 1, comp);
        return;
    }

    int depth_limit = 2 * static_cast<int>(std::floor(std::log2(static_cast<double>(n))));
    sort_impl(first, 0, n - 1, depth_limit, comp);
}

} // namespace enesort_opt2

template<typename Func>
double time_sort(Func f, const std::vector<int32_t>& input, int trials = 20) {
    auto copy = input;
    f(copy.data(), copy.data() + copy.size(), std::less<int32_t>{});
    
    double total_ms = 0;
    for (int t = 0; t < trials; ++t) {
        copy = input;
        auto t0 = std::chrono::high_resolution_clock::now();
        f(copy.data(), copy.data() + copy.size(), std::less<int32_t>{});
        auto t1 = std::chrono::high_resolution_clock::now();
        total_ms += std::chrono::duration<double, std::milli>(t1 - t0).count();
    }
    return total_ms / trials;
}

int main() {
    const int N = 100000;
    std::mt19937 rng(42);
    std::vector<int32_t> data(N);
    for (int i = 0; i < N; ++i) data[i] = rng();

    std::cout << "Testing N = " << N << " uniform random...\n";
    double t_ene = time_sort(bl_enesort::sort<int32_t>, data);
    double t_opt2 = time_sort(enesort_opt2::sort<int32_t>, data);
    double t_std = time_sort(bl_std_sort::sort<int32_t>, data);
    double t_pdq = time_sort(bl_pdqsort::sort<int32_t>, data);
    double t_yaro = time_sort(bl_yaroslavskiy::sort<int32_t>, data);

    std::cout << "Enesort (current): " << t_ene << " ms\n";
    std::cout << "Enesort (opt2):    " << t_opt2 << " ms\n";
    std::cout << "std::sort:         " << t_std << " ms\n";
    std::cout << "pdqsort:           " << t_pdq << " ms\n";
    std::cout << "Yaroslavskiy:      " << t_yaro << " ms\n";

    return 0;
}
