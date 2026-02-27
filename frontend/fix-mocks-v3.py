#!/usr/bin/env python3
"""
Fix API mock configuration - use importOriginal to preserve named exports.
"""

import os
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

NEW_MOCK = """vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    default: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      defaults: { baseURL: '/api' },
    },
  };
});"""

# Pattern: vi.mock('../../services/api', () => ({ ... }));
# This captures the static factory pattern (not importOriginal)
STATIC_MOCK_PATTERN = re.compile(
    r"vi\.mock\('../../services/api',\s*\(\)\s*=>\s*\(\{[\s\S]*?\}\)\);",
)


def fix_file(path, rel_depth='../../'):
    """Fix a single test file."""
    with open(path) as f:
        content = f.read()
    original = content
    
    mock_str = f"vi.mock('{rel_depth}services/api'"
    
    if mock_str not in content:
        return False
    
    # Find the specific mock block for services/api
    # Check if it already uses importOriginal FOR THIS SPECIFIC MOCK
    # Find the line with the mock
    idx = content.find(mock_str)
    if idx < 0:
        return False
    
    # Get the line
    line_end = content.find('\n', idx)
    mock_line = content[idx:line_end]
    
    # If this specific mock already uses importOriginal, skip
    if 'importOriginal' in mock_line:
        return False
    
    # If this is a static factory pattern () => ({, replace it
    if '() => ({' in mock_line or '() => {' in mock_line:
        # Use regex to match the full mock block
        pattern = re.compile(
            rf"vi\.mock\('{re.escape(rel_depth)}services/api',\s*\(\)\s*=>\s*[\({{][\s\S]*?(?:\}}\)\);|\}}\);)",
        )
        
        new_mock = NEW_MOCK.replace('../../', rel_depth)
        
        content = pattern.sub(new_mock, content, count=1)
    
    if content != original:
        with open(path, 'w') as f:
            f.write(content)
        return True
    return False


def main():
    fixed = 0
    
    # Walk all test directories
    src_dir = os.path.join(PROJECT_ROOT, 'src')
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if not (f.endswith('.test.jsx') or f.endswith('.test.js') or f.endswith('.test.tsx')):
                continue
            path = os.path.join(root, f)
            
            with open(path) as fh:
                content = fh.read()
            
            if "services/api'" not in content and 'services/api"' not in content:
                continue
            
            # Determine relative depth
            rel = os.path.relpath(os.path.join(src_dir, 'services'), root)
            rel = rel.replace('\\', '/') + '/'
            
            # Try multiple depth patterns
            for depth in ['../../', '../../../', '../../../../', '../']:
                mock_str = f"vi.mock('{depth}services/api'"
                if mock_str in content:
                    new_mock = NEW_MOCK.replace("'../../services/api'", f"'{depth}services/api'")
                    
                    # Find the specific mock
                    idx = content.find(mock_str)
                    line_end = content.find('\n', idx)
                    mock_line = content[idx:line_end]
                    
                    if 'importOriginal' in mock_line:
                        continue
                    
                    if '() => ({' in mock_line or '() => {' in mock_line:
                        pattern = re.compile(
                            rf"vi\.mock\('{re.escape(depth)}services/api',\s*\(\)\s*=>\s*[\({{][\s\S]*?(?:\}}\)\);|\}}\);)",
                        )
                        
                        new_content = pattern.sub(new_mock, content, count=1)
                        
                        if new_content != content:
                            with open(path, 'w') as fh:
                                fh.write(new_content)
                            content = new_content
                            fixed += 1
                            rel_path = os.path.relpath(path, PROJECT_ROOT)
                            print(f'✅ Fixed: {rel_path}')
    
    print(f'\n📊 Fixed {fixed} files')


if __name__ == '__main__':
    main()
