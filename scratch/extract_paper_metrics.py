import pandas as pd

sum_df = pd.read_csv('results/analysis/summary.csv')
sp_df  = pd.read_csv('results/analysis/speedup_table.csv')
los_df = pd.read_csv('results/analysis/losses.csv')

print('--- Summary Shape ---', sum_df.shape)
print('--- Speedup Shape ---', sp_df.shape)
print('--- Losses Shape ---', los_df.shape)

# Paper 1 metrics: Enesort vs std_sort, pdqsort, ips4o, timsort on uniform_random at 100k
sub = sum_df[(sum_df['n'] == 100000) & (sum_df['type'] == 'int32') & (sum_df['workload'] == 'uniform_random')]
print('\nUniform Random (N=100k, int32):')
for _, r in sub.iterrows():
    if r['algorithm'] in ['enesort', 'std_sort', 'pdqsort', 'ips4o', 'timsort', 'mergesort', 'heapsort']:
        print(f"  {r['algorithm']}: {r['median_ns']/1e6:.3f} ms (IQR: {r['iqr_ns']/1e6:.3f} ms, 95% CI: [{r['ci_lo_ns']/1e6:.3f}, {r['ci_hi_ns']/1e6:.3f}])")

# Duplicate / monotonic cases
print('\nKey Workloads (N=100k, int32):')
for w in ['all_equal', 'ascending', 'descending', 'organ_pipe', 'few_distinct_10', 'nearly_sorted_10', 'median_of_3_killer']:
    sub_w = sum_df[(sum_df['n'] == 100000) & (sum_df['type'] == 'int32') & (sum_df['workload'] == w)]
    e_rows = sub_w[sub_w['algorithm'] == 'enesort']
    s_rows = sub_w[sub_w['algorithm'] == 'std_sort']
    p_rows = sub_w[sub_w['algorithm'] == 'pdqsort']
    if not e_rows.empty and not s_rows.empty:
        e = e_rows['median_ns'].values[0] / 1e6
        s = s_rows['median_ns'].values[0] / 1e6
        p = p_rows['median_ns'].values[0] / 1e6 if not p_rows.empty else 0.0
        print(f"  {w:20s}: Enesort={e:.3f}ms | std::sort={s:.3f}ms (ratio {s/e:.2f}x) | pdqsort={p:.3f}ms (ratio {p/e:.2f}x)")

# Types at 100k uniform random
print('\nTypes at N=100k (uniform_random):')
for t in ['int32', 'int64', 'double', 'kvpair']:
    sub_t = sum_df[(sum_df['n'] == 100000) & (sum_df['type'] == t) & (sum_df['workload'] == 'uniform_random')]
    e = sub_t[sub_t['algorithm'] == 'enesort']['median_ns'].values[0] / 1e6
    s = sub_t[sub_t['algorithm'] == 'std_sort']['median_ns'].values[0] / 1e6
    print(f"  {t:10s}: Enesort={e:.3f}ms | std::sort={s:.3f}ms (ratio {s/e:.2f}x)")

# Ablation at 100k uniform_random and few_distinct_10
print('\nAblations at N=100k:')
for w in ['uniform_random', 'few_distinct_10']:
    print(f" Workload: {w}")
    sub_ab = sum_df[(sum_df['n'] == 100000) & (sum_df['type'] == 'int32') & (sum_df['workload'] == w)]
    for a in ['enesort', 'enesort_no_f1', 'enesort_no_f2', 'enesort_no_f3', 'enesort_no_f4', 'mo3_quicksort', 'std_sort']:
        row = sub_ab[sub_ab['algorithm'] == a]
        if not row.empty:
            print(f"    {a:18s}: {row['median_ns'].values[0]/1e6:.3f}ms")
