# Parallel Publication Package (Scopus Q2 / Q1 Venues)

This folder contains two completely independent, non-overlapping research manuscripts authored in the official IEEE manuscript template (`IEEEtran.cls`), accompanied by complete BibTeX references (`references.bib`) and high-resolution vector PDF figures from the experimental benchmarks.

These two papers address distinct theoretical and empirical research questions, allowing them to be submitted **in parallel to different Scopus Q2 / Q1 journals without duplicate submission or self-plagiarism concerns**.

---

## Paper 1: Algorithm Architecture & Theory Focus
- **Directory**: [`paper1_enesort_algorithm/`](paper1_enesort_algorithm/)
- **Main Manuscript**: [`paper1_enesort.tex`](paper1_enesort_algorithm/paper1_enesort.tex)
- **Title**: *Enesort: A Microarchitecture-Aware Hybrid In-Place Sorting Algorithm with Bounded Recursion Depth and Adaptive Equal-Key Partitioning*
- **Primary Focus**:
  - Algorithmic specification of the Enesort hybrid design (F1--F6).
  - Formal complexity proofs:
    - **Theorem 1**: Worst-case time complexity $O(N \log N)$ under any comparator.
    - **Theorem 2**: Strict upper bound on call-stack depth $\le 2 \lfloor \log_2 N \rfloor + O(1)$ stack frames ($< 65$ frames for any array up to $2^{64}$).
    - **Theorem 3**: In-place $O(1)$ auxiliary dynamic heap memory.
  - Multi-type evaluation (`int32`, `int64`, `double`, `KVPair` struct).
  - Component ablations (F1--F4) and parametric sweeps (cutoff $K=8..128$, pivot sample size $S=3..9$).
- **Recommended Journal Targets**:
  - *IEEE Access* (IEEE, Scopus Q1/Q2, Open Access, 4--6 week fast review)
  - *The Journal of Supercomputing* (Springer, Scopus Q2)
  - *Concurrency and Computation: Practice and Experience* (Wiley, Scopus Q2)
  - *Software: Practice and Experience* (Wiley, Scopus Q1/Q2)

---

## Paper 2: Empirical Benchmarking, Adversarial Robustness & Microarchitectural Trade-Offs
- **Directory**: [`paper2_adversarial_benchmarking/`](paper2_adversarial_benchmarking/)
- **Main Manuscript**: [`paper2_adversarial.tex`](paper2_adversarial_benchmarking/paper2_adversarial.tex)
- **Title**: *Empirical Evaluation of Adversarial Robustness and Cache Efficiency in Modern In-Place and Adaptive Sorting Algorithms*
- **Primary Focus**:
  - Systematic stress-testing of 10 modern sorting paradigms against 20 deterministic workloads across scaling orders up to $10^6$.
  - In-depth investigation of adversarial sequences: McIlroy median-of-3 killer permutations, organ-pipe sequences, periodic sawtooth frequencies, duplicate clusters, and Zipf distributions.
  - Operational step counter profiling: measuring exact comparison counts and swap operations per element.
  - Architectural trade-off analysis: quantitative comparison between in-place dual-pivot partitioning (zero heap overhead) vs adaptive run-merging (TimSort, MergeSort on contiguous monotonic runs).
  - Non-parametric statistical tests (paired Wilcoxon signed-rank with Holm family-wise correction, bootstrap 95% confidence intervals).
  - Concrete engineering decision guidelines for database systems and embedded software architects.
- **Recommended Journal Targets**:
  - *Journal of Systems Architecture* (Elsevier, Scopus Q2)
  - *Computing* (Springer, Scopus Q2)
  - *IEEE Transactions on Reliability* (IEEE, Scopus Q1/Q2)
  - *Simulation Modelling Practice and Theory* (Elsevier, Scopus Q2)

---

## How to Compile & Submit

### Option A: Overleaf (Zero Setup)
1. Zip the folder of either paper (e.g., zip the contents of `paper1_enesort_algorithm/`).
2. Go to [Overleaf.com](https://www.overleaf.com) $\rightarrow$ *New Project* $\rightarrow$ *Upload Project*.
3. Upload the `.zip` file. Overleaf will automatically detect `IEEEtran.cls` and compile the PDF with vector figures and bibliography.

### Option B: Local TeX Live / MiKTeX
Navigate to either folder and run:
```bash
pdflatex paper1_enesort.tex
bibtex paper1_enesort
pdflatex paper1_enesort.tex
pdflatex paper1_enesort.tex
```

