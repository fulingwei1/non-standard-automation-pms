#!/usr/bin/env python3
"""
Fix API mock configuration in page-level tests.

Strategy: Replace the vi.mock factory with one that uses importOriginal
to preserve real named API exports, while providing a mock default api.

The global setupTests.js already mocks '../services/api/client' with
api.get/post/put/delete. The named APIs (serviceApi, bomApi, etc.)
import from client.js and use those mocked methods.

So the fix is: DON'T replace named exports in the barrel mock.
Use importOriginal to keep them, only provide the default api mock.
"""

import os
import re

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(PROJECT_ROOT, 'src/pages')
TESTS_DIR = os.path.join(PAGES_DIR, '__tests__')

# Old mock pattern (static factory)
OLD_MOCK_PATTERN = re.compile(
    r"vi\.mock\('../../services/api',\s*\(\)\s*=>\s*\(\{\s*"
    r"default:\s*\{"
    r"\s*get:\s*vi\.fn\(\),?\s*"
    r"post:\s*vi\.fn\(\),?\s*"
    r"put:\s*vi\.fn\(\),?\s*"
    r"delete:\s*vi\.fn\(\),?\s*"
    r"\}\s*\}\)\);",
    re.DOTALL
)

# More flexible old mock pattern
OLD_MOCK_FLEXIBLE = re.compile(
    r"vi\.mock\('../../services/api',\s*\(\)\s*=>\s*\(\{[\s\S]*?\}\)\);",
)

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


def fix_test_file(test_path):
    with open(test_path) as f:
        content = f.read()
    original = content
    
    # Check if it has the old pattern
    if "vi.mock('../../services/api'" not in content:
        return False
    
    # Check if already uses importOriginal
    if "importOriginal" in content and "../../services/api" in content:
        return False
    
    # Replace the mock
    content = OLD_MOCK_FLEXIBLE.sub(NEW_MOCK, content, count=1)
    
    if content != original:
        with open(test_path, 'w') as f:
            f.write(content)
        return True
    return False


def main():
    fixed = 0
    for tf in sorted(os.listdir(TESTS_DIR)):
        if not tf.endswith('.test.jsx'):
            continue
        path = os.path.join(TESTS_DIR, tf)
        if fix_test_file(path):
            fixed += 1
            print(f'✅ Fixed: {tf}')
    
    # Also fix other test directories
    for root, dirs, files in os.walk(os.path.join(PROJECT_ROOT, 'src')):
        if '__tests__' not in root:
            continue
        for f in files:
            if not f.endswith('.test.jsx') and not f.endswith('.test.js'):
                continue
            path = os.path.join(root, f)
            if fix_test_file(path):
                fixed += 1
                print(f'✅ Fixed: {os.path.relpath(path, PROJECT_ROOT)}')
    
    print(f'\n📊 Fixed {fixed} files')


if __name__ == '__main__':
    main()
