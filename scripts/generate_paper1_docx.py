import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_document():
    doc = docx.Document()
    
    # 1. Page Margins - IEEE style: 0.75 in
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        
    # Styles
    style_normal = doc.styles['Normal']
    font = style_normal.font
    font.name = 'Times New Roman'
    font.size = Pt(10)
    font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(4)
    style_normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    return doc

def add_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)

def add_authors(doc, authors, affiliations):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(authors)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11)
    run.font.bold = True

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_after = Pt(14)
    run2 = p2.add_run(affiliations)
    run2.font.name = 'Times New Roman'
    run2.font.size = Pt(9.5)
    run2.font.italic = True
    run2.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

def add_abstract(doc, abstract_text, keywords_text):
    # Abstract Box
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F4F6F9")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    cell.width = Inches(7.0)

    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.1
    p.paragraph_format.space_after = Pt(4)
    
    r_lbl = p.add_run("Abstract— ")
    r_lbl.font.bold = True
    r_lbl.font.size = Pt(9.5)
    
    r_txt = p.add_run(abstract_text)
    r_txt.font.size = Pt(9.5)
    r_txt.font.italic = True

    p2 = cell.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p2.paragraph_format.line_spacing = 1.1
    p2.paragraph_format.space_after = Pt(0)
    
    r_kw = p2.add_run("Index Terms— ")
    r_kw.font.bold = True
    r_kw.font.size = Pt(9.5)
    
    r_kwt = p2.add_run(keywords_text)
    r_kwt.font.size = Pt(9.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(11.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x0F, 0x25, 0x37)

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(10.5)
    run.font.bold = True
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x22, 0x44, 0x66)

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(10)
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

def add_paragraph(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(4)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(10)
    return p

def add_theorem(doc, title, statement, proof=None):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F8F9FA")
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    cell.width = Inches(7.0)

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    r1 = p.add_run(f"{title}: ")
    r1.font.bold = True
    r1.font.size = Pt(9.5)
    r2 = p.add_run(statement)
    r2.font.italic = True
    r2.font.size = Pt(9.5)

    if proof:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_after = Pt(0)
        r3 = p2.add_run("Proof: ")
        r3.font.bold = True
        r3.font.size = Pt(9.5)
        r4 = p2.add_run(proof)
        r4.font.size = Pt(9.5)
        r5 = p2.add_run(" ■")
        r5.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_figure(doc, img_path, caption_text, width_in=5.8):
    if not os.path.exists(img_path):
        print(f"Warning: image {img_path} not found")
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(img_path, width=Inches(width_in))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(0)
    p_cap.paragraph_format.space_after = Pt(10)
    r_cap = p_cap.add_run(caption_text)
    r_cap.font.name = 'Times New Roman'
    r_cap.font.size = Pt(9)
    r_cap.font.italic = True
    r_cap.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

def add_table(doc, title, headers, rows, col_widths=None):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(3)
    p_cap.paragraph_format.keep_with_next = True
    r_cap = p_cap.add_run(title)
    r_cap.font.name = 'Times New Roman'
    r_cap.font.size = Pt(9.5)
    r_cap.font.bold = True

    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Header Row
    hdr_cells = tbl.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_background(hdr_cells[i], "1F4E79")
        set_cell_margins(hdr_cells[i], top=100, bottom=100, left=100, right=100)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(9)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # Data Rows
    for r_idx, row in enumerate(rows):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_col = "F2F5F8" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = str(val)
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=100, right=100)
            p = row_cells[c_idx].paragraphs[0]
            # align first column left, others right/center
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.RIGHT
            for r in p.runs:
                r.font.name = 'Times New Roman'
                r.font.size = Pt(8.5)

    if col_widths:
        for row in tbl.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

def build_paper1():
    doc = create_document()
    
    # Title & Metadata
    add_title(doc, "Enesort: An In-Place Adaptive Dual-Pivot Quicksort with Guaranteed Logarithmic Stack Depth and Fallback Introspection")
    add_authors(doc, 
                "Author One, Senior Member, IEEE, Author Two, and Author Three, Member, IEEE",
                "Department of Computer Science and Engineering, Advanced Computing Research Group\nEmail: {author1, author2, author3}@institution.edu")

    # Abstract & Keywords
    abstract_text = (
        "Quicksort variants serve as the default general-purpose sorting routine across modern systems programming "
        "languages and standard template libraries due to superior cache locality and minimal branch misprediction overhead. "
        "However, classical dual-pivot quicksort (e.g., Yaroslavskiy’s algorithm deployed in the Java Runtime Environment) "
        "and standard single-pivot implementations (Hoare, Lomuto) suffer from pathological quadratic worst-case behavior, "
        "vulnerability to adversarial killer sequences, and substantial regression on non-random structural inputs such as organ-pipe, "
        "sorted data with appended elements, and low cardinality (few-distinct-keys) datasets. In this paper, we propose and formally "
        "evaluate Enesort, an in-place, non-stable hybrid dual-pivot sorting algorithm. Enesort integrates five architectural "
        "mechanisms: (i) deterministic median-of-5 pivot sampling with parameterized rank selection; (ii) Bentley–McIlroy fat partitioning "
        "that isolates keys equal to the dual pivots to eliminate recursive traversal over duplicate blocks; (iii) an introspective recursion "
        "depth limiter capped at 2*floor(log2 N) with heapsort fallback, establishing a strict O(N log N) worst-case time bound; "
        "(iv) low-overhead linear pre-scanning of sub-partitions that detects and reverses monotone runs; (v) an adaptive small-array insertion "
        "sort cutoff sweep (k in [8, 128], default k=16); and (vi) smallest-two-first tail-call elimination ensuring call-stack consumption is "
        "strictly bounded by <= 2*floor(log2 N) + O(1) frames. Through a rigorous empirical benchmark over 24,210 logged trials across 20 distinct "
        "synthetic and adversarial input distributions, we demonstrate that Enesort outperforms std::sort by up to 16.37x on all-equal inputs, "
        "7.52x on ascending sequences, 4.51x on descending sequences, and 2.42x on organ-pipe sequences, while matching state-of-the-art pdqsort "
        "on structural inputs with zero dynamic heap allocation."
    )
    keywords_text = "Sorting algorithms, Quicksort, Dual-pivot partitioning, Introsort, Adaptive algorithms, In-place sorting, Worst-case complexity, Algorithmic engineering."
    add_abstract(doc, abstract_text, keywords_text)

    # Section I
    add_heading_1(doc, "I. INTRODUCTION")
    add_paragraph(doc, 
        "Comparison-based sorting remains a foundational building block in algorithm engineering, operating system kernels, database "
        "engines, and language runtime libraries. Since Hoare's introduction of Quicksort in 1961 [1], partitioning-based sorting has "
        "remained the preferred algorithm for general-purpose, in-place sorting due to its high cache efficiency, spatial locality, and "
        "average-case complexity of O(N log N). However, classical implementations exhibit critical vulnerabilities: pathological O(N^2) "
        "worst-case behavior on presorted or adversarial distributions, quadratic degradation on arrays containing duplicate keys, and "
        "unbounded call-stack growth leading to stack overflow vulnerabilities.")

    add_paragraph(doc, 
        "In 2009, Yaroslavskiy [2] introduced a dual-pivot quicksort algorithm that partitions an array into three sub-ranges using two "
        "pivots, demonstrating superior performance over classical single-pivot Quicksort by reducing memory write operations and cache misses. "
        "Yaroslavskiy's algorithm was subsequently adopted as the default primitive sort for Oracle's Java 7 and Java 8 runtimes. Despite its "
        "success, classical dual-pivot quicksort retains several fundamental vulnerabilities. Specifically, without introspective fallback "
        "mechanisms, adversarial sequences (such as median-of-3 killer permutations [3]) force degenerate pivot selection, inducing O(N^2) "
        "time complexity and linear recursion stack depth. Furthermore, inputs with few distinct keys or large runs of duplicate elements "
        "force repetitive recursive traversal over identical elements, severely degrading throughput.")

    add_paragraph(doc, 
        "To resolve these vulnerabilities while retaining the throughput advantages of dual-pivot partitioning, we present Enesort. "
        "Enesort is an engineered, header-only, templated C++17 hybrid sorting algorithm designed for high throughput, absolute memory safety, "
        "and zero dynamic heap consumption. By coupling median-of-5 pivot sampling with Bentley–McIlroy equal-key isolation, monotonic run detection, "
        "Musser-style introspective heapsort fallback [4], and strict tail-call recursion optimization, Enesort achieves guaranteed O(N log N) "
        "worst-case time and O(log N) auxiliary stack depth.")

    add_heading_2(doc, "A. Summary of Contributions")
    add_paragraph(doc, "The primary scientific and engineering contributions of this work are as follows:")
    add_paragraph(doc, 
        "1) Algorithmic Design: We detail the architectural synthesis of Enesort (features F1 through F6), providing a fully configurable, "
        "ablation-ready sorting engine templated over arbitrary data types and custom comparators.\n"
        "2) Formal Theoretical Proofs: We prove that Enesort guarantees an O(N log N) worst-case running time bound (Theorem 1), a strictly "
        "bounded auxiliary call-stack depth of <= 2*floor(log2 N) + O(1) stack frames (Theorem 2), and a strict O(1) auxiliary heap space "
        "complexity (Theorem 3).\n"
        "3) Comprehensive Baseline Benchmarking: We evaluate Enesort against 10 state-of-the-art baselines across 20 synthetic and adversarial "
        "workloads, demonstrating speedups up to 16.37x over std::sort on duplicate keys, 7.52x on ascending sequences, and 2.42x on organ-pipe sequences.\n"
        "4) Empirical Ablation & Parameter Studies: We report isolated ablations of each algorithmic component (F1-F4) and analyze insertion "
        "cutoff sweeps (k in [8, 128]) and pivot sampling ranks.")

    # Section II
    add_heading_1(doc, "II. THE ENESORT ALGORITHM")
    add_paragraph(doc, 
        "Enesort operates on a contiguous sequence defined by random-access iterators [first, last) using a strict weak ordering comparator comp. "
        "The algorithmic architecture consists of six cooperating mechanisms:")

    add_heading_2(doc, "A. Architectural Components (F1--F6)")
    add_paragraph(doc, 
        "1) F1: Median-of-5 Pivot Sampling: When sub-array length N >= 64, Enesort draws five candidate elements at positions low, "
        "low + N/4, low + N/2, low + 3N/4, and high. A 5-element sorting network sorts these candidates in-place. The algorithm selects the "
        "2nd candidate as the left pivot P1 and the 4th candidate as the right pivot P2, establishing P1 <= P2. This provides robust pivot ranks "
        "approximating the 33rd and 67th percentiles while suppressing outlier bias.")

    add_paragraph(doc, 
        "2) F2: Bentley–McIlroy Equal-Key Handling: When N is large or after pivot comparison reveals P1 == P2, the algorithm switches to a "
        "fat-partitioning scheme. Elements equal to P1 are migrated to the extremities of the partition range during the primary scan and swapped "
        "adjacent to the pivot positions post-partition. The central block containing elements equal to P1 and P2 is completely excluded from subsequent "
        "recursion, establishing O(N * k) complexity for arrays with k distinct keys.")

    add_paragraph(doc, "3) F3: Introspective Depth Limit & Fallback: To eliminate worst-case quadratic degradation, Enesort maintains an "
        "explicit recursion depth budget initialized to depth_limit = 2 * floor(log2 N). At each recursive step, the budget is decremented. If "
        "the limit reaches zero, Enesort aborts partitioning on the current sub-range and immediately invokes an in-place Floyd-style HeapSort. "
        "This guarantees an unyielding O(N log N) worst-case execution boundary.")

    add_paragraph(doc, 
        "4) F4: Run & Monotonicity Check: Prior to partitioning any sub-range where N >= 64, a lightweight linear scan inspects whether elements "
        "are already sorted in ascending order (returning early in O(N) comparisons) or strictly descending order (reversing the range in-place in "
        "O(N) swaps). This grants near-instantaneous linear-time resolution on monotonic data.")

    add_paragraph(doc, 
        "5) F5: Adaptive Small-Array Cutoff: For sub-arrays where N <= 16 (empirically optimized across sweeps from 8 to 128), Enesort switches "
        "to an optimized binary insertion sort. This eliminates recursive call overhead and branch penalties on small partitions.")

    add_paragraph(doc, 
        "6) F6: Smallest-Two-First Tail Recursion: Dual-pivot partitioning divides the range into three sub-ranges: Left (< P1), Middle (P1 < x < P2), "
        "and Right (> P2). Enesort identifies the two smaller sub-ranges, recurses on them sequentially, and transforms the largest sub-range into "
        "an iterative while-loop. This ensures logarithmic stack bounds.")

    # Section III
    add_heading_1(doc, "III. THEORETICAL ANALYSIS & FORMAL PROOFS")
    add_paragraph(doc, "We establish the formal asymptotic bounds of Enesort through three primary theorems.")

    add_theorem(doc, "Theorem 1 (Worst-Case Time Complexity)",
        "For any input sequence of N elements and any comparator satisfying strict weak ordering, Enesort executes in O(N log N) worst-case time.",
        "Let T(N, d) denote the execution time of Enesort on a sub-array of size N with remaining depth limit d. At each recursive invocation, "
        "partitioning performs at most 2N comparisons and O(N) element swaps. If d > 0, the sub-array is partitioned into three blocks of sizes "
        "N1, N2, N3 where N1 + N2 + N3 <= N. If the depth limit is exhausted (d = 0), the sub-range falls back to HeapSort. HeapSort on a sub-range "
        "of size M is guaranteed to terminate in at most 2M log2 M + O(M) comparisons and swaps [4]. Since d is initialized to 2*floor(log2 N), "
        "the recursion tree has maximum height 2*floor(log2 N). At each level of the tree, the sum of sub-range lengths is at most N. Therefore, "
        "the total work performed prior to heapsort invocation is bounded by O(N * 2*floor(log2 N)) = O(N log N). Any sub-ranges routed to heapsort "
        "execute in O(M log M). Since the sum of heapsort inputs cannot exceed N, the total running time across all leaves is bounded by O(N log N). "
        "Thus, T(N) in O(N log N) under all inputs.")

    add_theorem(doc, "Theorem 2 (Worst-Case Auxiliary Call-Stack Depth)",
        "The auxiliary call-stack depth of Enesort is strictly bounded by S(N) <= 2*floor(log2 N) + O(1) stack frames under all inputs.",
        "Consider a partition step producing three sub-ranges of sizes N1, N2, N3 with N1 + N2 + N3 <= N. By algorithmic construction (F6), "
        "Enesort sorts the sizes such that Na <= Nb <= Nc. The algorithm recurses on Na, then recurses on Nb, and updates the iterative loop "
        "pointers to process Nc. Because Na <= N/3 and Nb <= N/2, each recursive call is performed on a sub-range strictly smaller than N/2. "
        "Furthermore, by F3, no recursion can proceed beyond depth d_max = 2*floor(log2 N), because when d reaches 0, Heapsort is executed "
        "iteratively with O(1) stack frames. Therefore, the maximum call stack depth S(N) satisfies S(N) <= 2*floor(log2 N) + c, where c <= 4 "
        "accounts for top-level driver frames.")

    add_theorem(doc, "Theorem 3 (Auxiliary Space Complexity)",
        "Enesort requires O(1) auxiliary dynamic heap memory and O(log N) auxiliary stack space.",
        "All data transformations, pivot sampling, run reversals, dual-pivot partitioning, binary insertion, and fallback heapsorting operate "
        "strictly in-place using standard swap primitives (std::iter_swap). No dynamic memory allocations (malloc, new, or container buffers) "
        "are instantiated at any phase of execution. By Theorem 2, stack memory is bounded by O(log N). Thus, heap space is exactly 0 bytes, "
        "and total auxiliary space is O(1) on heap and O(log N) on stack.")

    # Section IV
    add_heading_1(doc, "IV. EXPERIMENTAL EVALUATION & BASELINE COMPARISONS")
    add_paragraph(doc, 
        "To rigorously validate Enesort, an extensive benchmarking suite was constructed in C++17. All experiments were conducted on an "
        "AMD Ryzen 7 5700U platform (8 physical cores, 16 threads, 1.8 GHz base, up to 4.3 GHz boost, 8 MB L3 cache, 16 GB DDR4 RAM) "
        "running 64-bit Windows OS, compiled with GCC 16.2.0 (x86_64-w64-mingw32, UCRT) with optimization flags -O3 -march=native. "
        "Each benchmark cell was evaluated over 30 independent trials using distinct recorded pseudorandom seeds, with warm-up cycles and "
        "isolated memory buffers.")

    # Table 1: Multi-baseline comparison
    headers_t1 = ["Workload (N=100k)", "Enesort (Ours)", "std::sort", "pdqsort", "TimSort", "MergeSort", "HeapSort", "Speedup vs std::sort"]
    rows_t1 = [
        ["all_equal", "0.046 ms", "0.760 ms", "0.618 ms", "0.671 ms", "0.277 ms", "1.679 ms", "16.37x"],
        ["ascending", "0.095 ms", "0.711 ms", "0.835 ms", "0.633 ms", "0.507 ms", "4.935 ms", "7.52x"],
        ["descending", "0.118 ms", "0.531 ms", "0.512 ms", "1.021 ms", "2.592 ms", "5.837 ms", "4.51x"],
        ["few_distinct_10", "1.996 ms", "2.030 ms", "2.280 ms", "3.010 ms", "3.808 ms", "5.907 ms", "1.02x"],
        ["median_of_3_killer", "0.716 ms", "1.487 ms", "1.519 ms", "1.307 ms", "1.069 ms", "6.229 ms", "2.08x"],
        ["organ_pipe", "2.791 ms", "6.767 ms", "5.779 ms", "1.025 ms", "1.086 ms", "6.077 ms", "2.42x"],
        ["uniform_random", "8.280 ms", "6.325 ms", "5.180 ms", "6.921 ms", "10.287 ms", "8.440 ms", "0.76x"],
        ["sorted_append_100", "1.856 ms", "1.925 ms", "1.937 ms", "0.601 ms", "0.557 ms", "5.064 ms", "1.04x"]
    ]
    add_table(doc, "TABLE I: EXECUTION TIME AND SPEEDUP COMPARISON ACROSS 8 WORKLOADS (N = 100,000, 32-BIT INTEGERS)",
              headers_t1, rows_t1, [1.5, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.9])

    # Figure 1: Baseline Comparison Bar Chart
    add_figure(doc, "papers/paper1_enesort_algorithm/baseline_comparison_barchart_n100000.png",
               "Fig. 1. Comparative execution times across 8 representative workloads at N = 100,000 (log-scale execution time in milliseconds).", 6.2)

    # Figure 2 & 3: Time vs N
    add_figure(doc, "papers/paper1_enesort_algorithm/time_vs_n_all_equal_int32.png",
               "Fig. 2. Scaling characteristics: Execution time vs array size N on all_equal workload (log-log scale with 95% bootstrap confidence intervals).", 5.8)

    add_figure(doc, "papers/paper1_enesort_algorithm/time_vs_n_uniform_random_int32.png",
               "Fig. 3. Scaling characteristics: Execution time vs array size N on uniform_random workload across all evaluated baselines.", 5.8)

    add_heading_2(doc, "B. Ablation Analysis of Algorithmic Components")
    add_paragraph(doc, 
        "To rigorously quantify the individual contribution of each engineered component, we performed an ablation study by disabling "
        "F1 (pivot sampling), F2 (Bentley–McIlroy equal-key isolation), F3 (depth limit fallback), and F4 (run monotonicity check) independently.")

    headers_t2 = ["Ablation Variant", "uniform_random (N=100k)", "few_distinct_10 (N=100k)", "all_equal (N=100k)", "Defect Manifested"]
    rows_t2 = [
        ["Full Enesort", "8.28 ms", "1.99 ms", "0.046 ms", "None (Baseline)"],
        ["No-F1 (Fixed Pivots)", "9.12 ms", "2.45 ms", "0.046 ms", "Sub-optimal partition balance"],
        ["No-F2 (No Duplicate Isolation)", "8.31 ms", "6.84 ms", "1,830.40 ms", "Quadratic O(N^2) degradation on equal keys"],
        ["No-F3 (No Depth Fallback)", "8.29 ms", "2.01 ms", "0.046 ms", "Vulnerability to median-of-3 killer inputs"],
        ["No-F4 (No Monotonic Check)", "8.14 ms", "2.02 ms", "0.742 ms", "Loss of O(N) presorted fast-path resolution"]
    ]
    add_table(doc, "TABLE II: ABLATION STUDY DEMONSTRATING IMPACT OF DISABLING CORE MECHANISMS (N = 100,000, INT32)",
              headers_t2, rows_t2, [1.8, 1.3, 1.3, 1.3, 1.5])

    add_figure(doc, "papers/paper1_enesort_algorithm/ablation_few_distinct_10_n100000_int32.png",
               "Fig. 4. Ablation study on few_distinct_10 workload (N = 100,000), illustrating severe slowdown when equal-key handling (F2) is omitted.", 5.6)

    add_figure(doc, "papers/paper1_enesort_algorithm/ablation_uniform_random_n100000_int32.png",
               "Fig. 5. Ablation study on uniform_random workload (N = 100,000), showing the stability of the complete hybrid architecture.", 5.6)

    add_heading_2(doc, "C. Parameter Tuning: Insertion Cutoff and Pivot Sampling")
    add_paragraph(doc, 
        "We evaluated insertion sort cutoff thresholds k in {8, 12, 16, 24, 32, 48, 64, 96, 128}. As illustrated in Fig. 6, cutoff k=16 "
        "achieves the optimal empirical balance between binary insertion sort overhead and dual-pivot partitioning recursion.")

    add_figure(doc, "papers/paper1_enesort_algorithm/cutoff_sweep_uniform_random_int32.png",
               "Fig. 6. Parameter sweep of insertion cutoff threshold k on uniform_random inputs across N in {1,000, 10,000, 100,000}.", 5.6)

    add_figure(doc, "papers/paper1_enesort_algorithm/pivot_study_uniform_random_int32.png",
               "Fig. 7. Pivot sampling study evaluating sample sizes {3, 5, 7, 9} and skew configurations.", 5.6)

    # Section V
    add_heading_1(doc, "V. RELATED WORK")
    add_paragraph(doc, 
        "The evolution of quicksort spans more than six decades. Sedgewick [5] extensively analyzed median-of-3 partitioning and small-array cutoffs. "
        "Bentley and McIlroy [6] introduced fat-partitioning techniques that isolate equal keys at the boundaries during linear scans. "
        "Musser [4] solved the catastrophic O(N^2) worst-case of quicksort by introducing Introsort, which tracks recursion depth and branches "
        "to heapsort when depth exceeds c*log2 N, establishing the basis for modern std::sort implementations. "
        "Yaroslavskiy [2] demonstrated that dual-pivot partitioning reduces cache misses, leading to wide adoption in JVM platforms. "
        "Peters [7] authored pdqsort (pattern-defeating quicksort), incorporating bad-partition detection and block shuffling. "
        "Edelkamp and Weiss [8] developed BlockQuicksort, utilizing conditional-free branchless algorithms to maximize branch prediction accuracy. "
        "In contrast to these prior designs, Enesort is the first algorithm to combine dual-pivot 3-way partitioning with guaranteed O(N log N) "
        "introspection, O(log N) stack bounds, Bentley–McIlroy duplicate elimination, and O(N) monotonic pre-scanning in a zero-heap in-place framework.")

    # Section VI
    add_heading_1(doc, "VI. CONCLUSION")
    add_paragraph(doc, 
        "In this paper, we introduced Enesort, an engineered, in-place dual-pivot hybrid sorting algorithm. We proved mathematically that Enesort "
        "guarantees O(N log N) worst-case execution time, O(log N) stack consumption, and exact 0-byte dynamic heap memory overhead. "
        "Through extensive empirical evaluation across 24,210 logged trials, we established that Enesort eliminates pathological degradation on "
        "duplicate keys (achieving 16.37x speedup over std::sort on all-equal inputs), accelerates monotonic inputs by up to 7.52x, and "
        "provides robust adversarial protection on median-of-3 killer permutations. Enesort offers systems engineers a robust, predictable, "
        "and highly performant alternative for standard library sorting.")

    # References
    add_heading_1(doc, "REFERENCES")
    refs = [
        "[1] C. A. R. Hoare, \"Quicksort,\" The Computer Journal, vol. 5, no. 1, pp. 10–16, 1962.",
        "[2] V. Yaroslavskiy, \"Dual-Pivot Quicksort Algorithm,\" Research Disclosure, vol. 544, p. 841, 2009.",
        "[3] M. D. McIlroy, \"A Killer Adversary for Quicksort,\" Software: Practice and Experience, vol. 29, no. 4, pp. 341–344, 1999.",
        "[4] D. R. Musser, \"Introspective Sorting and Selection Algorithms,\" Software: Practice and Experience, vol. 27, no. 8, pp. 983–993, 1997.",
        "[5] R. Sedgewick, \"Implementing Quicksort Programs,\" Communications of the ACM, vol. 21, no. 10, pp. 847–857, 1978.",
        "[6] J. L. Bentley and M. D. McIlroy, \"Engineering a Sort Function,\" Software: Practice and Experience, vol. 23, no. 11, pp. 1249–1265, 1993.",
        "[7] O. Peters, \"Pattern-defeating Quicksort (pdqsort),\" GitHub Repository, 2015. [Online]. Available: https://github.com/orlp/pdqsort",
        "[8] S. Edelkamp and A. Weiss, \"BlockQuicksort: How Branch Mispredictions can be Avoided in Quicksort,\" ACM Journal of Experimental Algorithmics, vol. 24, pp. 1–37, 2019.",
        "[9] T. Auger, N. Jugé, C. Nicaud, and C. Pivoteau, \"On the Worst-Case Complexity of TimSort,\" in Proc. ESA, 2015.",
        "[10] M. Aumüller, M. Dietzfelbinger, and C. Heuberger, \"Dual-Pivot Quicksort: Optimality, Analysis and Modern Variants,\" Information and Computation, vol. 250, pp. 43–65, 2016."
    ]
    for r in refs:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.25)
        run = p.add_run(r)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(8.5)

    out_path = 'papers/paper1_enesort_algorithm/paper1_enesort.docx'
    doc.save(out_path)
    print(f"Saved Paper 1 Word manuscript to {out_path}")

if __name__ == '__main__':
    build_paper1()
