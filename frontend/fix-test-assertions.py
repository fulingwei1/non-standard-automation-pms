#!/usr/bin/env python3
"""
Fix test assertion references from bare api.get/post/put/delete to named API methods.
This handles the 'PARTIAL' cases where the mock is correct but assertions still reference `api`.
"""

import os
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(PROJECT_ROOT, 'src/pages')
TESTS_DIR = os.path.join(PAGES_DIR, '__tests__')
API_DIR = os.path.join(PROJECT_ROOT, 'src/services/api')


def get_component_api_calls(comp_file):
    """Analyze which API methods the component actually calls."""
    with open(comp_file) as f:
        content = f.read()
    
    # Find calls like: serviceApi.records.list(...)
    calls = re.findall(r'(\w+Api)\.([\w.]+)\(', content)
    # Also: api.get(...)
    api_calls = re.findall(r'\bapi\.(get|post|put|delete|patch)\(', content)
    
    return calls, api_calls


def fix_test_assertions(test_file, comp_file):
    """Fix test assertions to match actual API usage in component."""
    with open(test_file) as f:
        content = f.read()
    original = content
    
    with open(comp_file) as f:
        comp_content = f.read()
    
    # Check which named APIs the component uses
    m = re.search(r'import\s+\{([^}]+)\}\s+from\s+["\'].*services/api["\']', comp_content)
    if not m:
        return False
    
    comp_apis = []
    for item in m.group(1).split(','):
        item = item.strip()
        name = item.split(' as ')[0].strip()
        if name.endswith('Api') or name.endswith('api'):
            comp_apis.append(name)
    
    if not comp_apis:
        return False
    
    # Get the primary API used by the component
    primary_api = comp_apis[0]
    
    # Analyze component API calls to build a mapping
    api_calls, bare_calls = get_component_api_calls(comp_file)
    
    # If component uses bare api.get etc, test assertions on api.get are correct
    if bare_calls and not api_calls:
        return False
    
    # Build method mapping: figure out what the component calls
    # e.g., serviceApi.records.list -> for GET operations
    # serviceApi.records.create -> for POST operations
    
    # Find the most common patterns
    get_methods = []
    post_methods = []
    put_methods = []
    delete_methods = []
    
    for api_name, method_chain in api_calls:
        parts = method_chain.split('.')
        # Check what HTTP method this maps to by looking at the API definition
        full_method = f'{api_name}.{method_chain}'
        
        # Heuristic: list/get -> GET, create -> POST, update -> PUT, delete -> DELETE
        last_method = parts[-1]
        if last_method in ('list', 'get', 'getStatistics', 'statistics', 'search'):
            get_methods.append(full_method)
        elif last_method in ('create', 'upload', 'send', 'submit', 'export'):
            post_methods.append(full_method)
        elif last_method in ('update', 'assign', 'close', 'complete', 'approve', 'reject'):
            put_methods.append(full_method)
        elif last_method == 'delete':
            delete_methods.append(full_method)
        elif last_method.startswith('get') or last_method.startswith('list'):
            get_methods.append(full_method)
        elif last_method.startswith('create') or last_method.startswith('add') or last_method.startswith('batch'):
            post_methods.append(full_method)
        elif last_method.startswith('update') or last_method.startswith('set'):
            put_methods.append(full_method)
        elif last_method.startswith('delete') or last_method.startswith('remove'):
            delete_methods.append(full_method)
        else:
            # Default to POST for unknown
            post_methods.append(full_method)
    
    # Now replace api.get references with the primary list/get method
    primary_get = get_methods[0] if get_methods else f'{primary_api}.list'
    primary_post = post_methods[0] if post_methods else f'{primary_api}.create'
    primary_put = put_methods[0] if put_methods else f'{primary_api}.update'
    primary_delete = delete_methods[0] if delete_methods else f'{primary_api}.delete'
    
    # Replace in beforeEach mock setup
    # api.get.mockResolvedValue -> primaryApi.method.mockResolvedValue
    content = re.sub(
        r'\bapi\.get\.mock(ResolvedValue|RejectedValue|Implementation)',
        f'{primary_get}.mock\\1',
        content
    )
    content = re.sub(
        r'\bapi\.post\.mock(ResolvedValue|RejectedValue|Implementation)',
        f'{primary_post}.mock\\1',
        content
    )
    content = re.sub(
        r'\bapi\.put\.mock(ResolvedValue|RejectedValue|Implementation)',
        f'{primary_put}.mock\\1',
        content
    )
    content = re.sub(
        r'\bapi\.delete\.mock(ResolvedValue|RejectedValue|Implementation)',
        f'{primary_delete}.mock\\1',
        content
    )
    
    # Replace in assertions
    # expect(api.get).toHaveBeenCalled() -> expect(primaryApi.method).toHaveBeenCalled()
    content = re.sub(
        r'expect\(api\.get\)',
        f'expect({primary_get})',
        content
    )
    content = re.sub(
        r'expect\(api\.post\)',
        f'expect({primary_post})',
        content
    )
    content = re.sub(
        r'expect\(api\.put\)',
        f'expect({primary_put})',
        content
    )
    content = re.sub(
        r'expect\(api\.delete\)',
        f'expect({primary_delete})',
        content
    )
    
    if content != original:
        with open(test_file, 'w') as f:
            f.write(content)
        return True
    return False


def main():
    fixed = 0
    
    for test_file_name in sorted(os.listdir(TESTS_DIR)):
        if not test_file_name.endswith('.test.jsx'):
            continue
        
        comp_name = test_file_name.replace('.test.jsx', '')
        comp_file = os.path.join(PAGES_DIR, comp_name + '.jsx')
        test_file = os.path.join(TESTS_DIR, test_file_name)
        
        if not os.path.exists(comp_file):
            continue
        
        with open(test_file) as f:
            test_content = f.read()
        
        # Only fix files that have bare api.get/post/put/delete references
        if not re.search(r'\bapi\.(get|post|put|delete)\b', test_content):
            continue
        
        try:
            result = fix_test_assertions(test_file, comp_file)
            if result:
                fixed += 1
                print(f'✅ Fixed assertions: {test_file_name}')
            else:
                print(f'⏭ Skipped: {test_file_name}')
        except Exception as e:
            print(f'❌ Error: {test_file_name}: {e}')
    
    print(f'\n📊 Fixed {fixed} files')


if __name__ == '__main__':
    main()
