cmake_minimum_required(VERSION 3.18)
project(EcoSortV2 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ---------------------------------------------------------------------------
# Build options
# ---------------------------------------------------------------------------
option(ECOSORT_ENABLE_SANITIZERS "Build tests with ASan+UBSan" OFF)
option(ECOSORT_ENABLE_ASAN       "Address Sanitizer only"       OFF)
option(ECOSORT_FETCH_DEPS        "Fetch third-party deps"       ON)

# Default: optimised build
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# Compiler flags
set(COMMON_FLAGS "-Wall -Wextra -march=native")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG ${COMMON_FLAGS}")
set(CMAKE_CXX_FLAGS_DEBUG   "-Og -g ${COMMON_FLAGS}")

# ---------------------------------------------------------------------------
# Third-party dependencies via FetchContent
# ---------------------------------------------------------------------------
include(FetchContent)

if(ECOSORT_FETCH_DEPS)
    # pdqsort
    FetchContent_Declare(
        pdqsort
        GIT_REPOSITORY https://github.com/orlp/pdqsort.git
        GIT_TAG        b1ef26a55cdb60d236a5cb199c4234c704f46726  # 2021-04-06
    )
    FetchContent_MakeAvailable(pdqsort)

    # gfx::timsort
    FetchContent_Declare(
        timsort
        GIT_REPOSITORY https://github.com/timsort/cpp-TimSort.git
        GIT_TAG        v3.0.0
    )
    FetchContent_MakeAvailable(timsort)

    # ips4o (sequential)
    FetchContent_Declare(
        ips4o
        GIT_REPOSITORY https://github.com/ips4o/ips4o.git
        GIT_TAG        v1.1.0
    )
    FetchContent_MakeAvailable(ips4o)
endif()

# ---------------------------------------------------------------------------
# Interface library: EcoSort headers
# ---------------------------------------------------------------------------
add_library(ecosort_iface INTERFACE)
target_include_directories(ecosort_iface INTERFACE
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_SOURCE_DIR}/bench
)

# Conditionally add pdqsort
if(ECOSORT_FETCH_DEPS AND TARGET pdqsort)
    target_compile_definitions(ecosort_iface INTERFACE HAS_PDQSORT=1)
    target_include_directories(ecosort_iface INTERFACE ${pdqsort_SOURCE_DIR})
endif()

# Conditionally add timsort
if(ECOSORT_FETCH_DEPS AND TARGET timsort)
    target_compile_definitions(ecosort_iface INTERFACE HAS_TIMSORT=1)
    target_include_directories(ecosort_iface INTERFACE
        ${timsort_SOURCE_DIR}/include)
endif()

# Conditionally add ips4o
if(ECOSORT_FETCH_DEPS AND TARGET ips4o)
    target_compile_definitions(ecosort_iface INTERFACE HAS_IPS4O=1)
    target_include_directories(ecosort_iface INTERFACE ${ips4o_SOURCE_DIR}/include)
endif()

# ---------------------------------------------------------------------------
# Benchmark harness
# ---------------------------------------------------------------------------
add_executable(bench bench/harness.cpp)
target_link_libraries(bench PRIVATE ecosort_iface)
if(UNIX AND NOT APPLE)
    target_link_libraries(bench PRIVATE pthread)
endif()

# ---------------------------------------------------------------------------
# Correctness tests
# ---------------------------------------------------------------------------
add_executable(test_correctness tests/test_correctness.cpp)
target_link_libraries(test_correctness PRIVATE ecosort_iface)

if(ECOSORT_ENABLE_SANITIZERS OR ECOSORT_ENABLE_ASAN)
    target_compile_options(test_correctness PRIVATE
        -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(test_correctness PRIVATE
        -fsanitize=address,undefined)
endif()

# ---------------------------------------------------------------------------
# Instrumented build (for counter study)
# ---------------------------------------------------------------------------
add_executable(bench_instrumented bench/harness.cpp)
target_link_libraries(bench_instrumented PRIVATE ecosort_iface)
target_compile_definitions(bench_instrumented PRIVATE ECOSORT_COUNT_OPS=1)
target_compile_options(bench_instrumented PRIVATE -O2)  # lighter opt for counting

# ---------------------------------------------------------------------------
# Ablation targets (F1..F4 disabled individually)
# ---------------------------------------------------------------------------
foreach(FX RANGE 1 4)
    set(ANAME "bench_no_f${FX}")
    add_executable(${ANAME} bench/harness.cpp)
    target_link_libraries(${ANAME} PRIVATE ecosort_iface)
    target_compile_definitions(${ANAME} PRIVATE
        ECOSORT_F${FX}_PIVOT_SAMPLE=0
        ECOSORT_F${FX}_EQUAL_KEYS=0
        ECOSORT_F${FX}_DEPTH_LIMIT=0
        ECOSORT_F${FX}_RUN_CHECK=0)
endforeach()

# Actually, we need to set only one at a time:
foreach(FX IN ITEMS 1 2 3 4)
    set(ANAME "bench_ablation_no_f${FX}")
    add_executable(${ANAME} bench/harness.cpp)
    target_link_libraries(${ANAME} PRIVATE ecosort_iface)
    if(FX EQUAL 1)
        target_compile_definitions(${ANAME} PRIVATE ECOSORT_F1_PIVOT_SAMPLE=0)
    elseif(FX EQUAL 2)
        target_compile_definitions(${ANAME} PRIVATE ECOSORT_F2_EQUAL_KEYS=0)
    elseif(FX EQUAL 3)
        target_compile_definitions(${ANAME} PRIVATE ECOSORT_F3_DEPTH_LIMIT=0)
    elseif(FX EQUAL 4)
        target_compile_definitions(${ANAME} PRIVATE ECOSORT_F4_RUN_CHECK=0)
    endif()
endforeach()

# ---------------------------------------------------------------------------
# CTest integration
# ---------------------------------------------------------------------------
enable_testing()
add_test(NAME correctness COMMAND test_correctness)
add_test(NAME smoke_bench  COMMAND bench --smoke --sizes 1000,10000,100000 --trials 3)

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
install(TARGETS bench test_correctness RUNTIME DESTINATION bin)
install(DIRECTORY src/ DESTINATION include/ecosort FILES_MATCHING PATTERN "*.hpp")

