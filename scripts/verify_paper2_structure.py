
import docx, re

tex_file = 'papers/paper2_adversarial_benchmarking/paper2_adversarial.tex'
docx_file = 'papers/paper2_adversarial_benchmarking/paper2_adversarial.docx'

with open(tex_file, 'r', encoding='utf-8') as f:
    tex_content = f.read()

doc = docx.Document(docx_file)

checklist = [
    ('Abstract', r'\\begin\{abstract\}', 'Abstract—'),
    ('Keywords', r'\\begin\{IEEEkeywords\}', 'Index Terms—'),
    ('Introduction', r'\\section\{Introduction\}', 'I. INTRODUCTION'),
    ('Literature review', r'\\section\{Literature Review\}', 'II. LITERATURE REVIEW'),
    ('Research Gaps', r'Identified Research Gaps', 'A. Identified Research Gaps'),
    ('Research questions', r'Research Questions', 'B. Research Questions'),
    ('Methodology', r'\\section\{Methodology\}', 'IV. METHODOLOGY'),
    ('- Algorithm', r'Algorithm Taxonomy', 'Algorithm Taxonomy'),
    ('- Enesort Lifecycle', r'Enesort: Architecture', 'Enesort: Architecture'),
    ('- Workloads / etc', r'Workload Taxonomy', 'Workload Taxonomy'),
    ('- Measurement & Steps', r'Operational Step Counter Instrumentation', 'Operational Step Counter Instrumentation'),
    ('Results', r'\\section\{Results', 'V. RESULTS'),
    ('- RQ1 Evaluation', r'RQ1', 'A. RQ1 Evaluation'),
    ('- RQ2 Adversarial', r'RQ2', 'B. RQ2 Evaluation'),
    ('- RQ3 Operational Steps', r'RQ3', 'C. RQ3 Evaluation'),
    ('- RQ4 Pareto / Microarch', r'RQ4', 'D. RQ4 Evaluation'),
    ('Conclusion', r'\\section\{Conclusion\}', 'VII. CONCLUSION'),
    ('Reference', r'bibliographystyle|thebibliography', 'REFERENCES')
]

col1 = 'Section / Item'
col2 = 'LaTeX'
col3 = 'DOCX'
print(f'{col1:<25} | {col2:<12} | {col3:<12}')
print('-' * 55)

docx_all_text = []
for p in doc.paragraphs:
    docx_all_text.append(p.text)
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                docx_all_text.append(p.text)
docx_full = chr(10).join(docx_all_text)

for name, tex_pat, docx_pat in checklist:
    tex_ok = bool(re.search(tex_pat, tex_content, re.IGNORECASE))
    docx_ok = docx_pat.lower() in docx_full.lower()
    t_status = 'PRESENT' if tex_ok else 'MISSING'
    d_status = 'PRESENT' if docx_ok else 'MISSING'
    print(f'{name:<25} | {t_status:<12} | {d_status:<12}')
