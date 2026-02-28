import json

with open('coverage.json', 'r') as f:
    data = json.load(f)

files = data['files']

categories = {
    'models': [],
    'schemas': [],
    'api': [],
    'services': [],
    'core': [],
    'utils': []
}

for filepath, info in files.items():
    if not filepath.startswith('app/'):
        continue
    
    summary = info['summary']
    percent = summary['percent_covered']
    
    category = None
    if filepath.startswith('app/models/'):
        category = 'models'
    elif filepath.startswith('app/schemas/'):
        category = 'schemas'
    elif filepath.startswith('app/api/'):
        category = 'api'
    elif filepath.startswith('app/services/'):
        category = 'services'
    elif filepath.startswith('app/core/'):
        category = 'core'
    elif filepath.startswith('app/utils/'):
        category = 'utils'
    
    if category:
        categories[category].append({
            'file': filepath,
            'percent': percent,
            'statements': summary['num_statements']
        })

for cat, items in categories.items():
    print(f"\n### {cat.upper()}")
    if not items:
        print("No files found.")
        continue
    
    # Sort by coverage descending
    items.sort(key=lambda x: x['percent'], reverse=True)
    
    covered = [i for i in items if i['percent'] > 0]
    uncovered = [i for i in items if i['percent'] == 0]
    
    print(f"Total files: {len(items)}")
    print(f"Covered files: {len(covered)}")
    print(f"Completely uncovered: {len(uncovered)}")
    
    print("\nTop 5 Most Covered:")
    for i in items[:5]:
        print(f"- {i['file']}: {i['percent']:.2f}% ({i['statements']} statements)")
    
    print("\nSome Uncovered (or least covered):")
    for i in items[-5:]:
        print(f"- {i['file']}: {i['percent']:.2f}% ({i['statements']} statements)")

# Identify specific business modules across all layers
business_modules = set()
for filepath in files.keys():
    if filepath.startswith('app/api/v1/endpoints/'):
        parts = filepath.split('/')
        if len(parts) > 4:
            business_modules.add(parts[4].replace('.py', ''))

print("\n### Business Module Coverage Matrix")
print("| Module | API Coverage | Service Coverage | Model Coverage | Schema Coverage |")
print("|--------|--------------|------------------|----------------|-----------------|")

for module in sorted(business_modules):
    if module == '__pycache__' or module == '__init__': continue
    
    api_cov = [f['percent'] for f in categories['api'] if f'/endpoints/{module}' in f['file']]
    svc_cov = [f['percent'] for f in categories['services'] if f'/{module}' in f['file']]
    mdl_cov = [f['percent'] for f in categories['models'] if f'/{module}.py' in f['file']]
    sch_cov = [f['percent'] for f in categories['schemas'] if f'/{module}.py' in f['file']]
    
    def avg(lst):
        return f"{sum(lst)/len(lst):.1f}%" if lst else "N/A"
    
    print(f"| {module} | {avg(api_cov)} | {avg(svc_cov)} | {avg(mdl_cov)} | {avg(sch_cov)} |")

