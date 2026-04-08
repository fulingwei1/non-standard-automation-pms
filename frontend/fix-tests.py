#!/usr/bin/env python3
import os
import re
import glob

def scan_test_files(directory):
    """扫描测试文件"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.test.js'):
                files.append(os.path.join(root, filename))
    return files

def needs_fix(content):
    """检查是否需要修复"""
    # 检查是否有导入的 API
    import_pattern = r'import\s+\{[^}]*\b(adminApi|settlementApi|projectApi|purchaseApi|productionApi|warehouseApi|timesheetApi|supplierApi|bomApi|qualityApi|serviceApi|scheduleApi|contractApi|customerApi|salesApi|engineerApi|hrApi|departmentApi|workerApi|customerServiceApi|acceptanceApi|shortageApi|materialApi|technicalApi|productionPlanApi|productionExceptionApi|assemblyKitApi)[^}]*\}\s+from'
    has_api_import = re.search(import_pattern, content) is not None
    # 检查是否有默认的 mock
    has_default_mock = 'default: {' in content and 'get: vi.fn()' in content
    # 检查是否有 .list.mockResolvedValue
    has_list_mock = '.list.mockResolvedValue' in content
    
    return has_api_import and has_default_mock and has_list_mock

def get_api_names(content):
    """获取导入的 API 名称"""
    api_names = []
    
    # 匹配各种 API 名称
    api_patterns = [
        r'\b(adminApi)\b',
        r'\b(settlementApi)\b',
        r'\b(projectApi)\b',
        r'\b(purchaseApi)\b',
        r'\b(productionApi)\b',
        r'\b(warehouseApi)\b',
        r'\b(timesheetApi)\b',
        r'\b(supplierApi)\b',
        r'\b(bomApi)\b',
        r'\b(qualityApi)\b',
        r'\b(serviceApi)\b',
        r'\b(scheduleApi)\b',
        r'\b(contractApi)\b',
        r'\b(customerApi)\b',
        r'\b(salesApi)\b',
        r'\b(engineerApi)\b',
        r'\b(hrApi)\b',
        r'\b(departmentApi)\b',
        r'\b(workerApi)\b',
        r'\b(customerServiceApi)\b',
        r'\b(acceptanceApi)\b',
        r'\b(shortageApi)\b',
        r'\b(materialApi)\b',
        r'\b(technicalApi)\b',
        r'\b(productionPlanApi)\b',
        r'\b(productionExceptionApi)\b',
        r'\b(assemblyKitApi)\b',
        r'\b(analysisApi)\b',
        r'\b(financeApi)\b',
        r'\b(permissionApi)\b',
        r'\b(quoteApi)\b',
        r'\b(costApi)\b',
        r'\b(solutionApi)\b',
        r'\b(knowledgeBaseApi)\b',
        r'\b(roleApi)\b',
        r'\b(positionApi)\b',
        r'\b(alertApi)\b',
        r'\b(solutionListApi)\b',
        r'\b(workOrderApi)\b',
        r'\b(schedulerApi)\b',
    ]
    
    # 找到 import 语句
    import_match = re.search(r'import\s+\{([^}]+)\}\s+from\s+[\'"]\.\.\/\.\.\/\.\.\/services\/api[\'"]', content)
    if not import_match:
        import_match = re.search(r'import\s+\{([^}]+)\}\s+from\s+[\'"]\.\.\/\.\.\/services\/api[\'"]', content)
    
    if import_match:
        import_content = import_match.group(1)
        for pattern in api_patterns:
            matches = re.findall(pattern, import_content)
            api_names.extend(matches)
    
    return api_names

def fix_test_file(filepath):
    """修复测试文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    api_names = get_api_names(content)
    if not api_names:
        return False
    
    # 检查是否已经有该 API 的 mock 定义
    modified = False
    for api_name in api_names:
        # 检查是否已有 API mock（通过检查是否有 apiName: { 的模式）
        has_api_mock = re.search(rf'{api_name}:\s*\{{', content) is not None
        
        if not has_api_mock:
            # 添加 API mock
            api_mock = f'''    {api_name}: {{
      list: vi.fn(),
      get: vi.fn(),
      query: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      aiMatch: vi.fn(),
    }},'''
            
            # 在 default 定义的 } 后添加
            # 匹配 default: { ... }, } 模式
            pattern = r'(\s+default:\s*\{[^}]+\},?\s*)\}'
            replacement = rf'\1\n{api_mock}\n  }}'
            
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                content = new_content
                modified = True
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

# 主程序
test_dir = 'src/pages'
files = scan_test_files(test_dir)

fixed_count = 0
for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if needs_fix(content):
        print(f'Processing: {filepath}')
        if fix_test_file(filepath):
            fixed_count += 1

print(f'\nTotal files scanned: {len(files)}')
print(f'Files fixed: {fixed_count}')