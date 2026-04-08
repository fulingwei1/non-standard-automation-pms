#!/usr/bin/env python3
import os
import re
import glob

test_dir = "/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/frontend/src"

# Common API methods to mock
common_methods = [
    'list', 'get', 'create', 'update', 'delete', 'query',
    'getAll', 'getById', 'getDetail', 'export', 'import',
    'submit', 'approve', 'reject', 'cancel', 'reset',
    'getStatistics', 'getOptions', 'batch', 'upload', 'download',
    'getWeightConfig', 'updateWeightConfig',
    'getWeek', 'aiMatch', 'getWorkspace', 'getBonuses', 'getMeetings',
    'getIssues', 'getSolutions', 'getTasks', 'getEmployees',
    'getProjects', 'getSummary', 'getTrend', 'getDistribution',
    'getItems', 'getTotal', 'getPending', 'getActive',
    'linkMeeting', 'getCost', 'getBudget', 'getActual',
    'getRevenue', 'getCostSummary', 'getProfit',
    'getMaterials', 'getBom', 'getInventory'
]

def find_test_files():
    files = []
    for root, dirs, filenames in os.walk(test_dir):
        if 'node_modules' in root:
            continue
        for f in filenames:
            if f.endswith('.test.js') or f.endswith('.test.jsx'):
                files.append(os.path.join(root, f))
    return files

def extract_api_imports(content):
    """Extract API names from import statements"""
    apis = []
    # Find import statements with API imports
    import_pattern = r"import\s+\{([^}]+)\}\s+from\s+['\"]([^'\"]*services\/api)['\"]"
    for match in re.finditer(import_pattern, content):
        import_content = match.group(1)
        for item in import_content.split(','):
            item = item.strip()
            if ' as ' in item:
                # Handle aliased imports like "adminApi as settingsApi"
                alias = item.split(' as ')[1].strip()
                apis.append(alias)
            else:
                apis.append(item)
    return list(set(apis))

def get_mock_path(content):
    """Get the mock path from vi.mock"""
    match = re.search(r"vi\.mock\(['\"]([^'\"]*services\/api)['\"]", content)
    return match.group(1) if match else None

def format_mock_code(mock_path, apis):
    """Generate the mock code"""
    lines = [
        f"vi.mock('{mock_path}', async (importOriginal) => {{",
        "  const actual = await importOriginal();",
        "  return {",
        "    ...actual,",
        "    default: {",
        "      get: vi.fn(),",
        "      post: vi.fn(),",
        "      put: vi.fn(),",
        "      delete: vi.fn(),",
        "      patch: vi.fn(),",
        "      defaults: { baseURL: '/api' },",
        "    },"
    ]
    
    for api in apis:
        lines.append(f"    {api}: {{")
        for method in common_methods:
            lines.append(f"      {method}: vi.fn(),")
        lines.append("    },")
    
    lines.append("  };")
    lines.append("});")
    
    return '\n'.join(lines)

def process_test_file(file_path):
    with open(file_path, 'r', encoding='utf8') as f:
        content = f.read()
    
    # Check if this file has the problematic mock pattern
    if 'api.list.mockResolvedValue' not in content and \
       'api.get.mockResolvedValue' not in content and \
       'api.query.mockResolvedValue' not in content:
        return False
    
    # Extract API imports
    apis = extract_api_imports(content)
    mock_path = get_mock_path(content)
    
    if not apis or not mock_path:
        print(f"  Skipping {file_path} - no APIs found or no mock path")
        return False
    
    # Generate mock code
    mock_code = format_mock_code(mock_path, apis)
    
    # Replace the existing mock
    mock_pattern = r"vi\.mock\(['\"][^'\"]*services\/api['\"],\s*async\s*\(importOriginal\)\s*=>\s*\{[\s\S]*?^\}\);"
    new_content = re.sub(mock_pattern, mock_code, content, flags=re.MULTILINE)
    
    if new_content != content:
        with open(file_path, 'w', encoding='utf8') as f:
            f.write(new_content)
        print(f"Fixed: {file_path}")
        print(f"  APIs: {', '.join(apis)}")
        return True
    
    return False

def main():
    print('Finding test files...')
    test_files = find_test_files()
    print(f'Found {len(test_files)} test files')
    
    fixed = 0
    for f in test_files:
        if process_test_file(f):
            fixed += 1
    
    print(f'\nFixed {fixed} test files')

if __name__ == '__main__':
    main()