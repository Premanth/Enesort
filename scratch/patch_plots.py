with open('scripts/plots.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "'ecosort_v2':    '#e41a1c',",
    "'enesort':       '#e41a1c',\n    'ecosort_v2':    '#e41a1c',"
)

content = content.replace(
    "'ecosort_v2': 'EcoSort v2',",
    "'enesort': 'Enesort',\n        'ecosort_v2': 'Enesort',"
)

content = content.replace("algo == 'ecosort_v2'", "algo in ('enesort', 'ecosort_v2')")
content = content.replace('EcoSort v2 speedup vs best baseline', 'Enesort speedup vs best baseline')
content = content.replace('Speedup (baseline/EcoSort)', 'Speedup (baseline/Enesort)')
content = content.replace('if EcoSort beats ALL baselines', 'if Enesort beats ALL baselines')
content = content.replace('green > 1 = EcoSort wins; red < 1 = EcoSort loses', 'green > 1 = Enesort wins; red < 1 = Enesort loses')
content = content.replace("a.startswith('ecosort')", "(a.startswith('enesort') or a.startswith('ecosort'))")
content = content.replace("summary[summary['algorithm'] == 'ecosort_v2']", "summary[summary['algorithm'].isin(['enesort', 'ecosort_v2'])]")
content = content.replace("label='EcoSort v2'", "label='Enesort'")

with open('scripts/plots.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated scripts/plots.py successfully!")

