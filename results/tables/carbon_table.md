# Carbon Emissions and Energy Consumption Across 8 Workloads (N = 100,000, 32-bit Integers)

Measured with CodeCarbon. Energy in microjoules/element (µJ/elem), Carbon in g CO2 / 10^6 elements.

| Workload | Enesort (µJ/elem) | std::sort (µJ/elem) | pdqsort (µJ/elem) | Enesort (g CO2/10^6) | std::sort (g CO2/10^6) | Carbon Reduction vs std::sort | Energy Speedup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **uniform_random** | **3.961** | 3.758 | 3.651 | **0.00078** | 0.00074 | **-5.4%** | **0.95x** |
| **ascending** | **0.709** | 0.852 | 0.865 | **0.00014** | 0.00017 | **+16.8%** | **1.20x** |
| **descending** | **0.714** | 0.972 | 0.831 | **0.00014** | 0.00019 | **+26.5%** | **1.36x** |
| **all_equal** | **0.736** | 0.975 | 0.919 | **0.00015** | 0.00019 | **+24.5%** | **1.33x** |
| **organ_pipe** | **2.972** | 4.336 | 4.517 | **0.00059** | 0.00086 | **+31.5%** | **1.46x** |
| **few_distinct_10** | **2.997** | 3.048 | 3.080 | **0.00059** | 0.00060 | **+1.7%** | **1.02x** |
| **median_of_3_killer** | **2.760** | 3.014 | 3.020 | **0.00055** | 0.00060 | **+8.4%** | **1.09x** |
| **sorted_append_100** | **3.394** | 2.971 | 2.988 | **0.00067** | 0.00059 | **-14.2%** | **0.88x** |
