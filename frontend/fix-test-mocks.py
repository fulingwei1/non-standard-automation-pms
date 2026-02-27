#!/usr/bin/env python3
"""
Fix test mock configurations for page-level tests.
The core issue: tests mock `api` (default), but components use named API exports
like `serviceApi`, `materialApi`, etc.

Strategy: For each test file that has a mismatch, rewrite the vi.mock and import
to use the correct named API with all methods as vi.fn().
"""

import os
import re
import json

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(PROJECT_ROOT, 'src/pages')
TESTS_DIR = os.path.join(PAGES_DIR, '__tests__')
API_DIR = os.path.join(PROJECT_ROOT, 'src/services/api')

def get_api_structure(api_file):
    """Parse an API file and return the structure of exported APIs."""
    path = os.path.join(API_DIR, api_file)
    if not os.path.exists(path):
        return {}
    
    with open(path) as f:
        content = f.read()
    
    result = {}
    # Find all exported const names
    for m in re.finditer(r'export\s+const\s+(\w+)\s*=\s*\{', content):
        name = m.group(1)
        start = m.end()
        depth = 1
        pos = start
        keys = []
        current_key = ''
        in_string = False
        string_char = None
        
        while pos < len(content) and depth > 0:
            ch = content[pos]
            
            if in_string:
                if ch == string_char and content[pos-1] != '\\':
                    in_string = False
            elif ch in ('"', "'", '`'):
                in_string = True
                string_char = ch
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            elif depth == 1 and ch == ':' and current_key.strip():
                key = current_key.strip()
                # Clean up the key - get last word only
                key = key.split('\n')[-1].strip()
                key = re.sub(r'^//.*', '', key).strip()
                if key and re.match(r'^[a-zA-Z_]\w*$', key):
                    keys.append(key)
                current_key = ''
            elif depth == 1 and ch == ',':
                current_key = ''
            elif depth == 1:
                current_key += ch
            else:
                current_key = ''
            pos += 1
        
        # For each key, determine if it's a nested object or a function
        result[name] = keys
    
    return result


def get_component_apis(comp_file):
    """Get the API imports used by a component."""
    if not os.path.exists(comp_file):
        return [], False
    
    with open(comp_file) as f:
        content = f.read()
    
    named_apis = []
    uses_default = False
    
    # Named imports
    m = re.search(r'import\s+\{([^}]+)\}\s+from\s+["\'].*services/api["\']', content)
    if m:
        for item in m.group(1).split(','):
            item = item.strip()
            # Handle "api as _api" -> skip aliased, or "api" -> keep
            parts = item.split(' as ')
            name = parts[0].strip()
            alias = parts[-1].strip() if len(parts) > 1 else name
            if alias.startswith('_'):
                continue  # skipped alias
            named_apis.append(name)
    
    # Default import
    m2 = re.search(r'import\s+api\s+from\s+["\'].*services/api["\']', content)
    if m2:
        uses_default = True
    
    # Also check for: import api, { namedApi } from '...'
    m3 = re.search(r'import\s+api\s*,\s*\{([^}]+)\}\s+from\s+["\'].*services/api["\']', content)
    if m3:
        uses_default = True
        for item in m3.group(1).split(','):
            item = item.strip()
            parts = item.split(' as ')
            name = parts[0].strip()
            alias = parts[-1].strip() if len(parts) > 1 else name
            if not alias.startswith('_'):
                named_apis.append(name)
    
    return named_apis, uses_default


def find_api_file_for_export(export_name):
    """Find which API file exports a given name."""
    for f in os.listdir(API_DIR):
        if not f.endswith('.js') or f == 'client.js':
            continue
        path = os.path.join(API_DIR, f)
        if os.path.isdir(path):
            continue
        with open(path) as fh:
            content = fh.read()
        if re.search(rf'export\s+const\s+{export_name}\b', content):
            return f
    return None


def generate_mock_for_api(api_name, keys):
    """Generate a mock object for an API with nested structure."""
    if not keys:
        return f'    {api_name}: {{\n      list: vi.fn().mockResolvedValue({{ data: [] }}),\n      get: vi.fn().mockResolvedValue({{ data: {{}} }}),\n      create: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),\n      update: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),\n      delete: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),\n    }}'
    
    lines = [f'    {api_name}: {{']
    for key in keys:
        # Check if this key is likely a nested object or a function
        # Heuristic: if the key name matches common CRUD patterns, it's likely a nested object with sub-methods
        crud_keys = ['list', 'get', 'create', 'update', 'delete', 'search']
        if key in crud_keys or key.startswith('get') or key.startswith('create') or key.startswith('update') or key.startswith('delete') or key.startswith('list') or key.startswith('search') or key.startswith('send') or key.startswith('submit') or key.startswith('batch') or key.startswith('export') or key.startswith('import') or key.startswith('download') or key.startswith('upload') or key.startswith('calculate') or key.startswith('sync') or key.startswith('check') or key.startswith('analyze') or key.startswith('recommend') or key.startswith('apply') or key.startswith('refresh') or key.startswith('execute') or key.startswith('trigger') or key.startswith('preview') or key.startswith('generate'):
            lines.append(f'      {key}: vi.fn().mockResolvedValue({{ data: {{}} }}),')
        else:
            # It's likely a nested object - create sub-methods
            lines.append(f'      {key}: {{')
            lines.append(f'        list: vi.fn().mockResolvedValue({{ data: [] }}),')
            lines.append(f'        get: vi.fn().mockResolvedValue({{ data: {{}} }}),')
            lines.append(f'        create: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),')
            lines.append(f'        update: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),')
            lines.append(f'        delete: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),')
            lines.append(f'      }},')
    lines.append(f'    }}')
    return '\n'.join(lines)


def is_nested_key(api_name, key, api_file):
    """Check if a key in an API is a nested object (not a direct function)."""
    path = os.path.join(API_DIR, api_file)
    with open(path) as f:
        content = f.read()
    
    # Find the export
    pattern = rf'export\s+const\s+{api_name}\s*=\s*\{{'
    m = re.search(pattern, content)
    if not m:
        return False
    
    # Find the key and check if its value starts with {
    # This is a simplified check
    start = m.end()
    # Find "key:" or "key :" at depth 1
    depth = 1
    pos = start
    in_string = False
    string_char = None
    
    while pos < len(content) and depth > 0:
        ch = content[pos]
        if in_string:
            if ch == string_char and content[pos-1] != '\\':
                in_string = False
        elif ch in ('"', "'", '`'):
            in_string = True
            string_char = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif depth == 1:
            # Check if we're at our key
            remainder = content[pos:]
            km = re.match(rf'\s*{key}\s*:\s*', remainder)
            if km:
                after_colon = content[pos + km.end():]
                after_colon = after_colon.lstrip()
                if after_colon.startswith('{'):
                    return True
                else:
                    return False
        pos += 1
    
    return False


def generate_smart_mock(api_name, keys, api_file):
    """Generate a mock that mirrors the actual API structure."""
    if not keys:
        return f'    {api_name}: {{\n      list: vi.fn().mockResolvedValue({{ data: [] }}),\n      get: vi.fn().mockResolvedValue({{ data: {{}} }}),\n    }}'
    
    lines = [f'    {api_name}: {{']
    for key in keys:
        if is_nested_key(api_name, key, api_file):
            lines.append(f'      {key}: {{')
            # Get sub-keys from the actual file
            sub_keys = get_nested_keys(api_name, key, api_file)
            for sk in sub_keys:
                lines.append(f'        {sk}: vi.fn().mockResolvedValue({{ data: {{}} }}),')
            if not sub_keys:
                lines.append(f'        list: vi.fn().mockResolvedValue({{ data: [] }}),')
                lines.append(f'        get: vi.fn().mockResolvedValue({{ data: {{}} }}),')
                lines.append(f'        create: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),')
                lines.append(f'        update: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),')
                lines.append(f'        delete: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),')
            lines.append(f'      }},')
        else:
            lines.append(f'      {key}: vi.fn().mockResolvedValue({{ data: {{}} }}),')
    lines.append(f'    }}')
    return '\n'.join(lines)


def get_nested_keys(api_name, key, api_file):
    """Get the sub-keys of a nested object in an API."""
    path = os.path.join(API_DIR, api_file)
    with open(path) as f:
        content = f.read()
    
    # Find "key: {" inside the api_name export at depth 1
    pattern = rf'export\s+const\s+{api_name}\s*=\s*\{{'
    m = re.search(pattern, content)
    if not m:
        return []
    
    start = m.end()
    depth = 1
    pos = start
    in_string = False
    string_char = None
    
    while pos < len(content) and depth > 0:
        ch = content[pos]
        if in_string:
            if ch == string_char and (pos == 0 or content[pos-1] != '\\'):
                in_string = False
        elif ch in ('"', "'", '`'):
            in_string = True
            string_char = ch
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif depth == 1:
            remainder = content[pos:]
            km = re.match(rf'{key}\s*:\s*\{{', remainder)
            if km:
                # Found the nested object, now extract its keys
                nested_start = pos + km.end()
                nested_depth = 1
                npos = nested_start
                sub_keys = []
                current_key = ''
                
                while npos < len(content) and nested_depth > 0:
                    nch = content[npos]
                    if nch == '{':
                        nested_depth += 1
                    elif nch == '}':
                        nested_depth -= 1
                    elif nested_depth == 1 and nch == ':' and current_key.strip():
                        k = current_key.strip().split('\n')[-1].strip()
                        k = re.sub(r'^//.*', '', k).strip()
                        if k and re.match(r'^[a-zA-Z_]\w*$', k):
                            sub_keys.append(k)
                        current_key = ''
                    elif nested_depth == 1 and nch == ',':
                        current_key = ''
                    elif nested_depth == 1:
                        current_key += nch
                    else:
                        current_key = ''
                    npos += 1
                
                return sub_keys
        pos += 1
    
    return []


def fix_test_file(test_file, comp_apis, uses_default_api):
    """Fix a test file's mock configuration."""
    with open(test_file) as f:
        content = f.read()
    
    original = content
    
    # Build the complete API structure we need
    all_api_structures = {}
    for api_name in comp_apis:
        api_file = find_api_file_for_export(api_name)
        if api_file:
            structures = get_api_structure(api_file)
            if api_name in structures:
                all_api_structures[api_name] = (structures[api_name], api_file)
    
    # Generate the new mock
    mock_parts = []
    
    # Always include default api mock (some tests reference it directly)
    mock_parts.append('  default: {\n    get: vi.fn().mockResolvedValue({ data: {} }),\n    post: vi.fn().mockResolvedValue({ data: { success: true } }),\n    put: vi.fn().mockResolvedValue({ data: { success: true } }),\n    delete: vi.fn().mockResolvedValue({ data: { success: true } }),\n    defaults: { baseURL: \'/api\' },\n  }')
    
    for api_name in comp_apis:
        if api_name == 'api':
            continue  # Already handled as default
        if api_name in all_api_structures:
            keys, api_file = all_api_structures[api_name]
            mock_parts.append(generate_smart_mock(api_name, keys, api_file))
        else:
            # Unknown API - create a generic mock
            mock_parts.append(f'    {api_name}: {{\n      list: vi.fn().mockResolvedValue({{ data: [] }}),\n      get: vi.fn().mockResolvedValue({{ data: {{}} }}),\n      create: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),\n      update: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),\n      delete: vi.fn().mockResolvedValue({{ data: {{ success: true }} }}),\n    }}')
    
    new_mock = 'vi.mock(\'../../services/api\', () => ({\n' + ',\n'.join(mock_parts) + '\n}));'
    
    # Replace the existing mock
    old_mock_pattern = r"vi\.mock\('../../services/api',\s*\(\)\s*=>\s*\(\{[\s\S]*?\}\)\);"
    if re.search(old_mock_pattern, content):
        content = re.sub(old_mock_pattern, new_mock, content, count=1)
    
    # Fix the import statement
    # Replace: import api from '../../services/api';
    # With: import api, { serviceApi } from '../../services/api';
    named_imports = [a for a in comp_apis if a != 'api']
    
    if named_imports:
        import_str = ', '.join(named_imports)
        
        # Pattern 1: import api from '../../services/api';
        old_import = re.search(r"import\s+api\s+from\s+'../../services/api';", content)
        if old_import:
            new_import = f"import api, {{ {import_str} }} from '../../services/api';"
            content = content[:old_import.start()] + new_import + content[old_import.end():]
        
        # Pattern 2: import { someApi } from '../../services/api';  (already named, might need additions)
        old_named = re.search(r"import\s+\{([^}]+)\}\s+from\s+'../../services/api';", content)
        if old_named and not old_import:
            existing = [x.strip() for x in old_named.group(1).split(',')]
            all_imports = list(set(existing + named_imports))
            new_import = f"import {{ {', '.join(all_imports)} }} from '../../services/api';"
            content = content[:old_named.start()] + new_import + content[old_named.end():]
    
    # Fix references in beforeEach that use api.get.mockResolvedValue
    # These need to be updated to use the correct named API
    # But we need to be careful - the tests use api.get, api.post etc.
    # The actual component calls like serviceApi.records.list()
    # Since we now have both default and named mocks, the component will use the named mock
    # but old test assertions like `expect(api.get)` won't match anymore
    
    # We'll leave the test assertions as-is for now, since fixing them requires understanding
    # each test's intent. The main fix is providing the correct mocks.
    
    if content != original:
        with open(test_file, 'w') as f:
            f.write(content)
        return True
    return False


def main():
    fixed = 0
    skipped = 0
    errors = []
    
    for test_file_name in sorted(os.listdir(TESTS_DIR)):
        if not test_file_name.endswith('.test.jsx'):
            continue
        
        comp_name = test_file_name.replace('.test.jsx', '')
        comp_file = os.path.join(PAGES_DIR, comp_name + '.jsx')
        test_file = os.path.join(TESTS_DIR, test_file_name)
        
        if not os.path.exists(comp_file):
            skipped += 1
            continue
        
        # Get what APIs the component uses
        comp_apis, uses_default = get_component_apis(comp_file)
        
        if not comp_apis and not uses_default:
            skipped += 1
            continue
        
        # Check if test already has correct mock
        with open(test_file) as f:
            test_content = f.read()
        
        # Check if test imports default api but component uses named apis
        test_imports_default = 'import api from' in test_content
        has_named_in_test = any(api in test_content for api in comp_apis if api != 'api')
        
        needs_fix = test_imports_default and comp_apis and not all(a == 'api' for a in comp_apis)
        
        if not needs_fix:
            # Also check if test has named imports but mock doesn't include them
            for api in comp_apis:
                if api != 'api' and f"'{api}'" not in test_content and f'"{api}"' not in test_content and api not in test_content:
                    needs_fix = True
                    break
        
        if needs_fix:
            try:
                result = fix_test_file(test_file, comp_apis, uses_default)
                if result:
                    fixed += 1
                    print(f'✅ Fixed: {test_file_name} (APIs: {comp_apis})')
                else:
                    skipped += 1
                    print(f'⏭ No changes: {test_file_name}')
            except Exception as e:
                errors.append((test_file_name, str(e)))
                print(f'❌ Error: {test_file_name}: {e}')
        else:
            skipped += 1
    
    print(f'\n📊 Summary: Fixed {fixed}, Skipped {skipped}, Errors {len(errors)}')
    if errors:
        print('\nErrors:')
        for name, err in errors:
            print(f'  {name}: {err}')


if __name__ == '__main__':
    main()
