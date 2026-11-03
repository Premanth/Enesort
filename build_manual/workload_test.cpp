#include <cstdio>
#include <vector>
#include <functional>
#include "../src/ecosort.hpp"
#include "../bench/generators.hpp"

template<typename T>
void eco_sort(std::vector<T>& v) {
    ecosort::sort(v.begin(), v.end(), std::less<T>{});
}

int main() {
    printf("Testing all workloads...\n"); fflush(stdout);
    
    std::vector<size_t> sizes = {0, 1, 2, 3, 7, 15, 16, 17, 31, 32, 33, 100, 1000, 10000};
    
    for (int w = 0; w < (int)WorkloadID::_COUNT; ++w) {
        WorkloadID wid = static_cast<WorkloadID>(w);
        printf("  Workload: %s\n", workload_name(wid)); fflush(stdout);
        
        for (size_t n : sizes) {
            printf("    n=%zu ... ", n); fflush(stdout);
            try {
                auto orig = gen::generate<int32_t>(wid, n, 42);
                auto data = orig;
                eco_sort(data);
                
                // Verify sorted
                bool ok = true;
                for (size_t i = 0; i+1 < data.size(); ++i)
                    if (data[i+1] < data[i]) { ok = false; break; }
                printf("%s\n", ok ? "OK" : "SORT_FAIL"); fflush(stdout);
            } catch (...) {
                printf("EXCEPTION\n"); fflush(stdout);
            }
        }
    }
    printf("Done!\n");
    return 0;
}
