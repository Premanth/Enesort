import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def create_document():
    doc = docx.Document()
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        
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

    for r_idx, row in enumerate(rows):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_col = "F2F5F8" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = str(val)
            set_cell_background(row_cells[c_idx], bg_col)
            set_cell_margins(row_cells[c_idx], top=80, bottom=80, left=100, right=100)
            p = row_cells[c_idx].paragraphs[0]
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
    add_title(doc, "Enesort: An In-Place Adaptive Dual-Pivot Quicksort with Guaranteed Logarithmic Stack Depth, Fallback Introspection, and Sustainable Software Design")
    add_authors(doc, 
                "Author One, Senior Member, IEEE, Author Two, and Author Three, Member, IEEE",
                "Department of Computer Science and Engineering, Sustainable Computing & Software Systems Group\nEmail: {author1, author2, author3}@institution.edu")

    # Abstract & Keywords
    abstract_text = (
        "Modern software engineering increasingly treats energy efficiency and computational sustainability as primary architectural "
        "requirements rather than incidental hardware side-effects. Recent advances in model-based software sustainability (Lano et al., 2026; "
        "García-Mireles et al., 2026) establish that identifying and eliminating algorithmic energy flaws—such as unamortized redundant comparisons, "
        "repetitive re-partitioning of duplicate elements, and unbounded recursion—dramatically reduces CPU cycle dissipation without specialized hardware. "
        "While dual-pivot quicksort (Yaroslavskiy, 2009) serves as a high-throughput primitive across runtime libraries, it suffers from catastrophic "
        "quadratic degradation on non-random inputs, such as low-cardinality datasets, presorted streams, and adversarial killer sequences. In this paper, "
        "we present Enesort, an engineered, in-place hybrid dual-pivot sorting algorithm architected for computational sustainability, worst-case "
        "predictability, and zero dynamic heap overhead. Enesort synthesizes six cooperating mechanisms: (i) deterministic median-of-5 pivot sampling (F1); "
        "(ii) Bentley–McIlroy fat partitioning with duplicate-key isolation (F2); (iii) an introspective depth limit capped at 2*floor(log2 N) with in-place "
        "heapsort fallback (F3); (iv) low-overhead linear pre-scanning that resolves monotonic runs in O(N) comparisons (F4); (v) an empirical small-array "
        "insertion cutoff (k=16) (F5); and (vi) smallest-two-first tail-call elimination ensuring call-stack depth is strictly <= 2*floor(log2 N) + O(1) frames (F6). "
        "We formally prove that Enesort guarantees O(N log N) worst-case running time (Theorem 1), O(log N) stack bounds (Theorem 2), and exact 0-byte dynamic heap "
        "allocation (Theorem 3). Benchmarked across 24,210 logged trials, Enesort achieves up to 16.37x speedup over std::sort on duplicate keys and 7.52x on presorted "
        "streams, establishing an energy-efficient foundation for standard library sorting."
    )
    keywords_text = "Sustainable software engineering, Green computing, Quicksort, Dual-pivot partitioning, Introsort, Computational complexity, Energy efficiency, Software modeling."
    add_abstract(doc, abstract_text, keywords_text)

    # Section I
    add_heading_1(doc, "I. INTRODUCTION")
    add_paragraph(doc, 
        "Computational sustainability has emerged as a critical imperative across software engineering and systems design. As demonstrated by recent "
        "systematic reviews and tertiary studies (García-Mireles et al. [18], Devadas & T [21], Roy et al. [23]), environmental sustainability in software "
        "engineering is predominantly governed by energy efficiency, resource utilization, and operational cycle reduction. Importantly, Lano, Rahman, "
        "and Alwakeel [14] establish that algorithmic energy flaws—such as unamortized redundant branch operations, unpruned recursive traversals, and "
        "pathological worst-case computational explosions—can be systematically modeled and eliminated at the software design stage, yielding substantial "
        "energy reductions across execution platforms without requiring hardware alterations. Similarly, Podder et al. [22] observe that software-level "
        "optimizations consistently deliver 30% to 50% computational energy savings by preventing unnecessary compute cycles.")

    add_paragraph(doc, 
        "Within systems software, database engines, and standard runtime libraries, comparison-based sorting is among the most frequently invoked "
        "computational kernels. Since Hoare's formulation in 1962 [1] and Knuth's classical treatment [2], Quicksort variants have remained the default choice "
        "for in-place sorting due to excellent spatial locality and average-case O(N log N) complexity. In 2009, Yaroslavskiy [5] demonstrated that dual-pivot "
        "partitioning outperforms classical single-pivot Quicksort by reducing memory write operations, leading to its adoption in Oracle's Java 7 and 8 runtimes. "
        "Subsequent theoretical analysis by Wild and Nebel [7] confirmed that dual-pivot partitioning decreases cache misses by dividing the input into three "
        "sub-ranges per partitioning stage.")

    add_paragraph(doc, 
        "Despite these average-case advantages, classical dual-pivot Quicksort harbors severe algorithmic energy flaws: (1) it exhibits O(N^2) quadratic worst-case "
        "complexity under adversarial permutations, causing severe CPU thermal throttling and Denial-of-Service vulnerabilities; (2) on inputs with low cardinality "
        "or large clusters of duplicate keys, it repeatedly recurses into identical elements, squandering millions of comparisons; and (3) naive recursion produces "
        "unbounded call-stack depth, threatening thread stack exhaustion. While Musser's Introsort [8] introduced heapsort fallback to solve the quadratic "
        "worst-case in single-pivot quicksort (forming modern std::sort), dual-pivot architectures have lacked a mathematically rigorous, energy-sustainable hybrid "
        "framework that integrates duplicate-key pruning, run monotonicity detection, and strict stack bounding in a zero-heap footprint.")

    add_paragraph(doc, 
        "To resolve these challenges, this paper introduces Enesort (Energy-Efficient Sort), an engineered in-place dual-pivot hybrid algorithm designed "
        "specifically to satisfy modern software sustainability requirements (Roy et al. [23]). Enesort integrates median-of-5 pivot sampling (F1), Bentley–McIlroy "
        "equal-key fat partitioning (F2), introspective fallback to Floyd HeapSort (F3), monotonic run pre-scanning (F4), an adaptive small-array cutoff (F5), "
        "and smallest-two-first tail-recursion optimization (F6).")

    add_heading_2(doc, "A. Primary Contributions")
    add_paragraph(doc, "The contributions of this work are organized as follows:")
    add_paragraph(doc, 
        "1) Sustainable Algorithmic Synthesis: We design Enesort (F1--F6), eliminating algorithmic energy waste across structural and adversarial inputs while "
        "maintaining exact O(1) auxiliary dynamic heap allocation.\n"
        "2) Formal Asymptotic Proofs: We prove that Enesort guarantees an unyielding O(N log N) worst-case time bound (Theorem 1), an auxiliary call-stack depth "
        "strictly bounded by <= 2*floor(log2 N) + O(1) frames (Theorem 2), and zero heap allocation (Theorem 3).\n"
        "3) Comprehensive Empirical Validation: Benchmarked across 24,210 logged trials over 20 workloads, Enesort achieves up to 16.37x speedup over std::sort on "
        "duplicate keys, 7.52x on ascending sequences, and 2.08x on median-of-3 killer permutations.\n"
        "4) Empirical Ablation & Parameter Sweeps: We conduct isolated ablations of F1--F4, cutoff threshold sweeps (k in [8, 128]), and pivot sampling studies, "
        "validating each architectural decision under rigorous experimental controls.")

    # Section II
    add_heading_1(doc, "II. THE ENESORT ALGORITHM")
    add_paragraph(doc, 
        "Enesort operates on contiguous ranges [first, last) using a strict weak ordering comparator comp. The algorithmic engine coordinates six distinct mechanisms:")

    add_heading_2(doc, "A. Architectural Mechanisms (F1--F6)")
    add_paragraph(doc, 
        "1) F1 (Median-of-5 Pivot Sampling): When sub-array size N >= 64, Enesort samples 5 elements at indices {low, low + N/4, low + N/2, low + 3N/4, high}. "
        "An unrolled 5-element sorting network sorts these candidates in-place. Enesort selects the 2nd candidate as P1 and the 4th as P2. This samples the 33rd "
        "and 67th percentiles, ensuring balanced 1/3 : 1/3 : 1/3 partition splits and suppressing outlier-induced energy waste.")

    add_paragraph(doc, 
        "2) F2 (Bentley–McIlroy Equal-Key Handling): If P1 == P2 or after partitioning elements equal to the pivots are clustered, Enesort routes execution into "
        "fat partitioning. Crucially, the middle block containing elements equal to P1 and P2 is completely excluded from subsequent recursion. This converts "
        "O(N^2) quadratic duplicate key recursion into an O(N * k) linear-time resolution for k distinct keys.")

    add_paragraph(doc, 
        "3) F3 (Introspective Depth Limit & Fallback): To provide hard worst-case bounds, Enesort maintains a recursion budget d = 2*floor(log2 N). If degenerate "
        "partitions exhaust d (d = 0), Enesort immediately aborts quicksort on that sub-range and invokes in-place Floyd HeapSort, enforcing an unbreachable "
        "O(N log N) upper bound.")

    add_paragraph(doc, 
        "4) F4 (Monotonic Run Check): Prior to partitioning sub-arrays with N >= 64, a lightweight linear scan verifies whether elements are already in ascending "
        "order (returning in O(N) comparisons, 0 swaps) or strictly descending order (reversed in-place with N/2 swaps).")

    add_paragraph(doc, 
        "5) F5 (Small-Array Insertion Cutoff): When sub-range length N <= 16 (empirically optimized across sweeps from 8 to 128), Enesort switches to binary "
        "insertion sort, eliminating function call overhead and branch mispredictions.")

    add_paragraph(doc, 
        "6) F6 (Smallest-Two-First Tail Recursion): Dual-pivot partitioning creates three sub-ranges. Enesort sorts the lengths of the three sub-ranges, performs "
        "recursive calls on the two smaller partitions, and converts the largest partition into an iterative while-loop, bounding stack consumption to O(log N).")

    # Section III
    add_heading_1(doc, "III. THEORETICAL ANALYSIS & FORMAL COMPLEXITY PROOFS")
    add_paragraph(doc, "We establish the formal asymptotic bounds of Enesort through three primary theorems.")

    add_theorem(doc, "Theorem 1 (Guaranteed Worst-Case Time Complexity)",
        "For any input sequence of N elements and any comparator satisfying strict weak ordering, Enesort executes in O(N log N) worst-case time.",
        "Let T(N, d) denote the execution time on a sub-array of size N with depth limit d. At each recursive invocation, dual-pivot partitioning performs at most "
        "2N comparisons and O(N) swaps. If d > 0, the range is split into three sub-ranges of sizes N1, N2, N3 with N1 + N2 + N3 <= N. If d = 0, Enesort falls "
        "back to HeapSort. HeapSort on a sub-range of size M executes in at most 2M log2 M + O(M) operations (Musser [8]). Because d is initialized to 2*floor(log2 N), "
        "the maximum height of the partitioning tree prior to fallback is 2*floor(log2 N). At each level, the sum of sub-range sizes is at most N. Thus, the total "
        "partitioning work before fallback is bounded by 2N * (2*floor(log2 N)) = O(N log N). Since any sub-ranges reaching heapsort execute in O(M log M) and the "
        "sum of heapsort inputs cannot exceed N, the total running time across all leaves is strictly bounded by O(N log N).")

    add_theorem(doc, "Theorem 2 (Worst-Case Auxiliary Call-Stack Depth)",
        "The auxiliary call-stack depth of Enesort is strictly bounded by S(N) <= 2*floor(log2 N) + O(1) stack frames under all inputs.",
        "Consider a partition step producing three sub-ranges of sizes N1, N2, N3 with N1 + N2 + N3 <= N. By construction (F6), Enesort sorts the sizes such that "
        "Na <= Nb <= Nc. The algorithm recurses on Na, then recurses on Nb, and updates loop bounds to process Nc iteratively. Because Na <= N/3 and Nb <= N/2, "
        "each recursive call operates on a sub-range strictly smaller than N/2. Furthermore, by F3, no recursion can proceed beyond depth d_max = 2*floor(log2 N). "
        "Therefore, the maximum call stack depth S(N) satisfies S(N) <= 2*floor(log2 N) + c, where c <= 4 represents driver frames.")

    add_theorem(doc, "Theorem 3 (Strict Zero-Heap Auxiliary Space Complexity)",
        "Enesort requires exact O(1) auxiliary dynamic heap memory and O(log N) auxiliary stack space.",
        "All element movements, pivot sampling, run reversals, dual-pivot partitioning, binary insertion, and fallback heapsorting operate strictly in-place "
        "using std::iter_swap. Zero dynamic memory allocations (malloc, new, or dynamic buffers) are instantiated. Thus, auxiliary heap consumption is "
        "identically 0 bytes under all inputs.")

    # Section IV
    add_heading_1(doc, "IV. EXPERIMENTAL EVALUATION & BASELINE COMPARISONS")
    add_paragraph(doc, 
        "Experiments were conducted on an AMD Ryzen 7 5700U platform (8 physical cores, 16 threads, 1.8 GHz base, up to 4.3 GHz boost, 8 MB L3 cache, "
        "16 GB DDR4 RAM) running 64-bit Windows OS, compiled with GCC 16.2.0 (x86_64-w64-mingw32, UCRT) with optimization flags -O3 -march=native. "
        "In accordance with software sustainability benchmarking protocols (Bylina et al. [13], Jiménez et al. [6], Pulido et al. [17]), each benchmark "
        "cell was evaluated over 30 independent trials using distinct recorded pseudorandom seeds, with warm-up cycles and isolated memory buffers.")

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

    add_figure(doc, "papers/paper1_enesort_algorithm/baseline_comparison_barchart_n100000.png",
               "Fig. 1. Comparative execution times across 8 representative workloads at N = 100,000 (log-scale execution time in milliseconds).", 6.2)

    add_figure(doc, "papers/paper1_enesort_algorithm/time_vs_n_all_equal_int32.png",
               "Fig. 2. Scaling characteristics: Execution time vs array size N on all_equal workload (log-log scale with 95% bootstrap confidence intervals).", 5.8)

    add_figure(doc, "papers/paper1_enesort_algorithm/time_vs_n_uniform_random_int32.png",
               "Fig. 3. Scaling characteristics: Execution time vs array size N on uniform_random workload across all evaluated baselines.", 5.8)

    add_heading_2(doc, "B. Ablation Study: Validating Individual Mechanisms")
    add_paragraph(doc, 
        "To verify that each architectural mechanism is essential for computational sustainability, we evaluated Enesort with F1, F2, F3, and F4 "
        "disabled individually. As shown in Table II, disabling F2 (equal-key fat partitioning) causes execution time on all_equal to explode from 0.046 ms "
        "to 1,830.40 ms (a 39,791x slowdown), confirming that duplicate-key pruning is an indispensable green software requirement.")

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

    add_heading_2(doc, "C. Parameter Sweep: Cutoff Threshold and Pivot Sampling")
    add_paragraph(doc, 
        "We evaluated insertion sort cutoffs k in {8, 12, 16, 24, 32, 48, 64, 96, 128} and pivot sampling sizes {3, 5, 7, 9}. Cutoff k=16 and sample "
        "size 5 (ranks 2 and 4) provide the empirical optimum, minimizing sorting network overhead while maximizing L1 cache locality.")

    add_figure(doc, "papers/paper1_enesort_algorithm/cutoff_sweep_uniform_random_int32.png",
               "Fig. 6. Parameter sweep of insertion cutoff threshold k on uniform_random inputs across N in {1,000, 10,000, 100,000}.", 5.6)

    add_figure(doc, "papers/paper1_enesort_algorithm/pivot_study_uniform_random_int32.png",
               "Fig. 7. Pivot sampling study evaluating sample sizes {3, 5, 7, 9} and skew configurations.", 5.6)

    # Section V
    add_heading_1(doc, "V. RELATED WORK")
    add_paragraph(doc, 
        "Quicksort optimization has evolved through single-pivot analysis (Sedgewick [3]), introspective bounds (Musser [8]), and dual-pivot designs "
        "(Yaroslavskiy [5], Wild & Nebel [7]). In parallel, the software sustainability domain has matured rapidly. Lano et al. [14] formulated "
        "model-based sustainability refactoring to eliminate energy flaws. García-Mireles et al. [18] mapped 80 systematic reviews on software engineering "
        "sustainability, emphasizing the necessity of standardized experimental measurements across runtime, resource utilization, and energy. "
        "Roy et al. [23] established formal sustainability requirements for software architecture, while Devadas and T [21] developed taxonomies "
        "connecting algorithmic efficiency directly to carbon reduction. Furthermore, Yang [11] and El Outmani et al. [12] directly investigated the "
        "energy consumption of sorting algorithms, demonstrating that reducing branch mispredictions and operational comparison steps directly reduces "
        "joules consumed per sorted sequence. Enesort bridges these domains, providing a mathematically verified dual-pivot sort aligned with modern "
        "sustainable software principles.")

    # Section VI
    add_heading_1(doc, "VI. CONCLUSION")
    add_paragraph(doc, 
        "Enesort demonstrates that in-place dual-pivot sorting can achieve high throughput while satisfying stringent software sustainability and "
        "memory safety requirements. By eliminating quadratic degradation on duplicate keys (16.37x speedup on all_equal), resolving monotonic streams "
        "in linear time (7.52x speedup on ascending), and guaranteeing O(N log N) worst-case time with bounded O(log N) stack depth and exact 0-byte dynamic "
        "heap space, Enesort establishes a predictable, energy-efficient sorting engine for modern systems.")

    # References
    add_heading_1(doc, "REFERENCES")
    refs = [
        "[1] C. A. R. Hoare, \"Quicksort,\" The Computer Journal, vol. 5, no. 1, pp. 10–16, 1962.",
        "[2] D. E. Knuth, The Art of Computer Programming, Volume 3: Sorting and Searching, 2nd ed. Reading, MA: Addison-Wesley, 1998.",
        "[3] R. Sedgewick, \"The analysis of Quicksort programs,\" Acta Informatica, vol. 7, no. 4, pp. 327–355, 1977.",
        "[4] A. Fariña, M. A. Martínez-Prieto, and F. Claude, \"Onto how compression yields energy-efficient text search,\" Computing, vol. 107, pp. 45–68, 2025. DOI: 10.1007/s00607-025-01469-0.",
        "[5] V. Yaroslavskiy, \"Dual-Pivot Quicksort algorithm,\" Research disclosure, 2009. [Online]. Available: http://iaroslavski.narod.ru/quicksort/DualPivotQuicksort.pdf.",
        "[6] E. Jiménez, P. P. Alarcón, and J. C. Dueñas, \"Does the compiler or interpreter version influence the energy consumption of programming languages?,\" Science of Computer Programming, vol. 240, p. 103270, 2025. DOI: 10.1016/j.scico.2025.103270.",
        "[7] S. Wild and M. E. Nebel, \"Average case analysis of Java 7's dual pivot Quicksort,\" in Proc. 20th European Symposium on Algorithms (ESA), Springer, 2012, pp. 825–836.",
        "[8] D. R. Musser, \"Introspective sorting and selection algorithms,\" Software: Practice and Experience, vol. 27, no. 8, pp. 983–993, 1997.",
        "[9] T. Peters, \"TimSort description,\" Python Software Foundation, 2002. [Online]. Available: https://github.com/python/cpython/blob/main/Objects/listsort.txt.",
        "[10] M. Frigo, C. E. Leiserson, H. Prokop, and S. Ramachandran, \"Cache-oblivious algorithms,\" ACM Transactions on Algorithms (TALG), vol. 8, no. 1, pp. 1–22, 2012.",
        "[11] Z. Yang, \"Holistic Performance, Memory, and Energy Analysis of Sorting Algorithms and Binary Search Trees in Python,\" Applied and Computational Engineering, vol. 104, pp. 112–124, 2025. DOI: 10.54254/2755-2721/2025.LD26932.",
        "[12] A. El Outmani, E. M. Jaara, and M. Azizi, \"Exploring the Energy Consumption of Some Typical Applications: The Case of Sorting Algorithms,\" in Proc. Int. Conf. Netw. Comput. Sci. Softw. Eng., Springer, Cham, 2025, pp. 185–196. DOI: 10.1007/978-3-031-66854-8_16.",
        "[13] B. Bylina, M. Piekarz, and J. Bylina, \"Importance of C/C++ compiler choice for performance and energy consumption of multithreaded WZ factorization,\" Bulletin of the Polish Academy of Sciences: Technical Sciences, vol. 73, no. 2, p. e153226, 2025. DOI: 10.24425/bpasts.2025.153226.",
        "[14] K. Lano, Z. Rahman, and L. Alwakeel, \"Model-based software sustainability analysis and improvement,\" Software and Systems Modeling, vol. 25, pp. 201–225, 2026. DOI: 10.1007/s10270-026-01374-w.",
        "[15] O. Poy, G. A. Lewis, and C. A. Gomez, \"Impact on energy consumption of design patterns, code smells and refactoring techniques: A systematic mapping study,\" Journal of Systems and Software, vol. 220, p. 112303, 2025. DOI: 10.1016/j.jss.2024.112303.",
        "[16] A. Noureddine and O. Le Goaer, \"Investigating the Impact of Software Design Patterns on Energy Consumption,\" in Proc. IEEE Int. Conf. Softw. Architecture (ICSA), 2025, pp. 153–163. DOI: 10.1109/ICSA65012.2025.00024.",
        "[17] C. Pulido, J. A. Parejo, and A. Ruiz-Cortés, \"Pypen: Code instrumentation tool for dynamic analysis and energy efficiency evaluation,\" Computer Standards & Interfaces, vol. 91, p. 104000, 2025. DOI: 10.1016/j.csi.2025.104000.",
        "[18] R. E. García-Mireles, M. A. Moraga, and F. García, \"Sustainability in the Field of Software Engineering: A Tertiary Study,\" ACM Computing Surveys, vol. 58, no. 3, pp. 1–38, 2026. DOI: 10.1145/3747178.",
        "[19] A. Al-Dweik et al., \"Low complexity sphere decoding with probabilistic radius prediction and hybrid modulation for low latency wireless MIMO systems,\" Scientific Reports, vol. 16, p. 41109, 2026. DOI: 10.1038/s41598-026-41109-x.",
        "[20] S. Ijaz, S. G. Ahmad, K. Ayyub, et al., \"Energy-efficient time and cost constraint scheduling algorithm using improved multi-objective differential evolution in fog computing,\" The Journal of Supercomputing, vol. 81, p. 116, 2025. DOI: 10.1007/s11227-024-06550-7.",
        "[21] R. M. Devadas and S. T, \"Towards carbon-aware AI: a systematic PRISMA review and taxonomy of green architectures, hardware life-cycle, and energy-efficient algorithms,\" Energy Informatics, vol. 9, p. 38, 2026. DOI: 10.1186/s42162-026-00651-8.",
        "[22] S. Podder, H. Date, and S. Murthy, \"Green prompt engineering for sustainable generative AI,\" Environmental Science and Ecotechnology, vol. 30, p. 100684, 2026. DOI: 10.1016/j.ese.2026.100684.",
        "[23] M. Roy, N. Deb, A. Cortesi, and N. Chaki, \"Towards a Taxonomy of Sustainability Requirements for Software Design,\" in Proc. IEEE/ACM 10th Int. Workshop Green Sustainable Softw. (GREENS), 2026, pp. 22–27. DOI: 10.1145/3786148.3788620.",
        "[24] J. L. Bentley and M. D. McIlroy, \"Engineering a Sort Function,\" Software: Practice and Experience, vol. 23, no. 11, pp. 1249–1265, 1993.",
        "[25] O. Peters, \"Pattern-defeating Quicksort (pdqsort),\" GitHub Repository, 2015. [Online]. Available: https://github.com/orlp/pdqsort"
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
    out_path_alt = 'papers/paper1_enesort_algorithm/paper1_enesort_sustainable.docx'
    try:
        doc.save(out_path)
        print(f"Saved rewritten Paper 1 Word manuscript to {out_path}")
    except PermissionError:
        doc.save(out_path_alt)
        print(f"Original file was open in Word. Saved rewritten Paper 1 Word manuscript to {out_path_alt}")

if __name__ == '__main__':
    build_paper1()
