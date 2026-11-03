#include <iostream>
#include <future>
#include <thread>
#include <chrono>

int main() {
    std::promise<void> prom;
    auto fut = prom.get_future();
    auto t0 = std::chrono::steady_clock::now();
    std::thread th([&]() {
        volatile long long sum = 0;
        for (long long i = 0; i < 20000000000LL; ++i) sum += i;
        prom.set_value();
    });
    if (fut.wait_for(std::chrono::seconds(1)) == std::future_status::timeout) {
        auto t1 = std::chrono::steady_clock::now();
        std::cout << "Timed out as expected in " 
                  << std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count() 
                  << " ms" << std::endl;
        th.detach();
    } else {
        auto t1 = std::chrono::steady_clock::now();
        std::cout << "Finished in " 
                  << std::chrono::duration_cast<std::chrono::milliseconds>(t1 - t0).count() 
                  << " ms" << std::endl;
        th.join();
    }
    return 0;
}
