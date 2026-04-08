#!/usr/bin/env python3
"""修复 hooks 测试文件中的 API mock 问题"""
import os
import re
import glob

PROJECT_ROOT = "/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/frontend"

def get_api_imports(test_content):
    """从测试文件中提取导入的 API 名称"""
    for line in test_content.split('\n'):
        if 'from' in line and 'services/api' in line and line.strip().startswith('import'):
            # 提取花括号中的内容
            match = re.search(r'\{(.+)\}', line)
            if match:
                items = match.group(1).split(',')
                imports = []
                for item in items:
                    item = item.strip()
                    if ' as ' in item:
                        parts = item.split(' as ')
                        imports.append((parts[0].strip(), parts[1].strip()))
                    else:
                        imports.append((item, item))
                return imports
    return []

def needs_fix(test_content):
    """检查测试文件是否需要修复"""
    has_wrong_mock = 'async (importOriginal)' in test_content
    has_mock_call = '.mockResolvedValue' in test_content
    return has_wrong_mock and has_mock_call

def fix_test_file(file_path):
    """修复单个测试文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if not needs_fix(content):
        return False
    
    api_imports = get_api_imports(content)
    if not api_imports:
        return False
    
    # 构建正确的 mock - 找到正确的相对路径
    import_path = None
    for line in content.split('\n'):
        if 'from' in line and 'services/api' in line and line.strip().startswith('import'):
            match = re.search(r"from\s+'([^']+)'", line)
            if match:
                import_path = match.group(1)
                break
    
    if not import_path:
        import_path = '../../../../services/api'
    
    mock_lines = [f"vi.mock('{import_path}', () => ({{"]
    for original_api, alias in api_imports:
        mock_lines.append(f"  {alias}: {{")
        methods = ['list', 'get', 'query', 'create', 'update', 'delete', 'aiMatch', 
                   'getOverdue', 'getAging', 'getSummary', 'batch', 'export', 'submit',
                   'approve', 'reject', 'start', 'complete', 'cancel']
        for m in methods:
            mock_lines.append(f"    {m}: vi.fn(),")
        mock_lines.append("  },")
    
    mock_lines.append("  default: {")
    mock_lines.append("    get: vi.fn(),")
    mock_lines.append("    post: vi.fn(),")
    mock_lines.append("    put: vi.fn(),")
    mock_lines.append("    delete: vi.fn(),")
    mock_lines.append("    patch: vi.fn(),")
    mock_lines.append("    defaults: { baseURL: '/api' },")
    mock_lines.append("  },")
    mock_lines.append("}));")
    mock_template = "\n".join(mock_lines)
    
    # 找到 mock 块的开始和结束
    lines = content.split('\n')
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if 'vi.mock' in line and 'services/api' in line and 'async (importOriginal)' in line:
            start_idx = i
        if start_idx >= 0 and end_idx < 0:
            if line.strip() == '});':
                if i > start_idx:
                    end_idx = i
    
    if start_idx >= 0 and end_idx >= 0:
        new_lines = lines[:start_idx] + [mock_template] + lines[end_idx+1:]
        content = "\n".join(new_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    pattern = os.path.join(PROJECT_ROOT, "src/pages/*/hooks/__tests__/*.test.js")
    files = glob.glob(pattern)
    
    fixed_count = 0
    for f in files:
        try:
            if fix_test_file(f):
                print(f"Fixed: {f}")
                fixed_count += 1
        except Exception as e:
            print(f"Error fixing {f}: {e}")
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()