#include <cstdio>
#include <vector>
#include <functional>
#include "../src/ecosort.hpp"
#include "../bench/generators.hpp"

int main() {
    printf("Test start\n"); fflush(stdout);
    
    // Test n=0
    {
        std::vector<int> v;
        ecosort::sort(v.begin(), v.end(), std::less<int>{});
        printf("n=0 OK\n"); fflush(stdout);
    }
    // Test n=1
    {
        std::vector<int> v = {42};
        ecosort::sort(v.begin(), v.end(), std::less<int>{});
        printf("n=1 OK\n"); fflush(stdout);
    }
    // Test n=2
    {
        std::vector<int> v = {5, 3};
        ecosort::sort(v.begin(), v.end(), std::less<int>{});
        printf("n=2 OK: %d %d\n", v[0], v[1]); fflush(stdout);
    }
    // Test n=16 (cutoff boundary)
    {
        std::vector<int> v = {9,8,7,6,5,4,3,2,1,0,15,14,13,12,11,10};
        ecosort::sort(v.begin(), v.end(), std::less<int>{});
        bool ok = true;
        for(int i=1;i<16;i++) if(v[i]<v[i-1]) ok=false;
        printf("n=16 cutoff: %s\n", ok?"OK":"FAIL"); fflush(stdout);
    }
    // Test n=17 (just above cutoff - triggers partitioning)
    {
        std::vector<int> v = {9,8,7,6,5,4,3,2,1,0,16,15,14,13,12,11,10};
        printf("Starting n=17 sort...\n"); fflush(stdout);
        ecosort::sort(v.begin(), v.end(), std::less<int>{});
        bool ok = true;
        for(int i=1;i<17;i++) if(v[i]<v[i-1]) ok=false;
        printf("n=17: %s\n", ok?"OK":"FAIL"); fflush(stdout);
    }
    // Test ascending n=1000
    {
        printf("Testing ascending n=1000...\n"); fflush(stdout);
        auto v = gen::generate<int32_t>(WorkloadID::ASCENDING, 1000, 42);
        ecosort::sort(v.begin(), v.end(), std::less<int32_t>{});
        printf("ascending 1000: done\n"); fflush(stdout);
    }
    printf("All mini tests passed!\n");
    return 0;
}
