#!/usr/bin/env python3
"""
Add missing mock methods to test files.
Fixes: Cannot read properties of undefined (reading 'mockResolvedValue')
"""

import re
import sys
from pathlib import Path

def extract_api_calls(content):
    """Extract API method calls from beforeEach like: xxxApi.method.mockResolvedValue"""
    pattern = r'(\w+Api)\.(\w+)\.mock'
    matches = re.findall(pattern, content)
    
    # Group by API
    api_methods = {}
    for api_name, method in matches:
        if api_name not in api_methods:
            api_methods[api_name] = set()
        api_methods[api_name].add(method)
    
    return api_methods

def extract_mocked_methods(content):
    """Extract methods defined in vi.mock for each API"""
    api_methods = {}
    
    # Find vi.mock block
    mock_match = re.search(r"vi\.mock\([^)]+,\s*\(\)\s*=>\s*\({(.*?)\}\)\)", content, re.DOTALL)
    if not mock_match:
        return api_methods
    
    mock_content = mock_match.group(1)
    
    # Find each API definition
    api_blocks = re.finditer(r'(\w+Api):\s*\{([^}]+(?:\{[^}]+\}[^}]*)*)\}', mock_content, re.DOTALL)
    for api_block in api_blocks:
        api_name = api_block.group(1)
        api_content = api_block.group(2)
        
        # Extract method names
        methods = set(re.findall(r'(\w+):\s*vi\.fn', api_content))
        api_methods[api_name] = methods
    
    return api_methods

def add_missing_methods(file_path):
    """Add missing mock methods to a test file"""
    content = file_path.read_text()
    
    # Extract what's called and what's defined
    called = extract_api_calls(content)
    defined = extract_mocked_methods(content)
    
    # Find missing methods
    missing = {}
    for api_name, methods in called.items():
        if api_name not in defined:
            missing[api_name] = methods
        else:
            missing_methods = methods - defined[api_name]
            if missing_methods:
                missing[api_name] = missing_methods
    
    if not missing:
        return False, "No missing methods"
    
    # Add missing methods to mock
    for api_name, methods in missing.items():
        # Find the API block in vi.mock
        pattern = f'({api_name}:\\s*{{)'
        match = re.search(pattern, content)
        
        if not match:
            print(f"  Warning: Could not find {api_name} in mock definition")
            continue
        
        # Generate method lines
        method_lines = []
        for method in sorted(methods):
            method_lines.append(f"      {method}: vi.fn().mockResolvedValue({{ data: {{}} }}),")
        
        # Insert after the opening brace
        pos = match.end()
        # Find the first existing method or closing brace
        content[pos:pos+200]
        
        # Insert at the beginning of the API block
        new_methods = '\n' + '\n'.join(method_lines)
        content = content[:pos] + new_methods + content[pos:]
    
    file_path.write_text(content)
    return True, f"Added {sum(len(m) for m in missing.values())} methods"

def main():
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:]]
    else:
        # Process all modified test files
        test_dir = Path('src/pages/__tests__')
        files = list(test_dir.glob('*.test.jsx'))
    
    print("=== Adding Missing Mock Methods ===\n")
    
    for file_path in files:
        if not file_path.exists():
            continue
        
        print(f"Checking {file_path.name}...")
        modified, message = add_missing_methods(file_path)
        
        if modified:
            print(f"  ✅ {message}")
        else:
            print(f"  ⏭️  {message}")
    
    print("\n✅ Done!")

if __name__ == '__main__':
    main()
