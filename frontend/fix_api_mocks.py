#!/usr/bin/env python3
"""
修复 API Mock 响应格式问题
问题：{ data: {} } 对于 res.data?.items 会返回 undefined，导致显示错误
解决：{ data: { items: [] } } 确保 .items 返回空数组
"""
import os
import re
import glob

test_dir = "/Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/frontend/src"

def find_test_files():
    files = []
    for root, dirs, filenames in os.walk(test_dir):
        if 'node_modules' in root:
            continue
        for f in filenames:
            if f.endswith('.test.js') or f.endswith('.test.jsx') or f.endswith('.test.ts') or f.endswith('.test.tsx'):
                files.append(os.path.join(root, f))
    return files

def fix_mock_data(file_path):
    with open(file_path, 'r', encoding='utf8') as f:
        content = f.read()
    
    original = content
    modified = False
    
    # 修复1: { data: {} } -> { data: { items: [] } }
    # 匹配各种 api 的 mockResolvedValue({ data: {} })
    # 需要更精确的匹配，只修复直接返回空对象的
    
    # Pattern 1: xxxApi: { ... method: vi.fn().mockResolvedValue({ data: {} }), ... }
    # 需要在每个方法后面添加 items: []
    
    # 策略：替换 { data: {} } 为 { data: { items: [] } } 但只针对 list, query, getAll 等返回列表的 API
    
    # 找到所有的 mockResolvedValue({ data: {} }) 并替换
    # 排除已经正确格式的
    
    # 简单替换: { data: {} } => { data: { items: [] } }
    # 但需要排除已经包含 items 的
    
    # 使用更精确的正则表达式
    pattern = r"(\w+Api:\s*\{[^}]*?)(\w+:\s*vi\.fn\(\)\.mockResolvedValue\(\{)\s*data:\s*\{\}\s*(\}\))"
    
    def replace_list_method(match):
        nonlocal modified
        modified = True
        api_section = match.group(1)
        method_start = match.group(2)
        method_end = match.group(3)
        
        # 检查方法名是否是列表类型
        method_match = re.search(r'(\w+):\s*vi\.fn\(\)', api_section + method_start)
        
        # 列表类型方法
        list_methods = ['list', 'query', 'getAll', 'getProjects', 'getEmployees', 
                       'getIssues', 'getSolutions', 'getTasks', 'getMeetings',
                       'getBonuses', 'getMaterials', 'getWeightConfig',
                       'getCost', 'getBudget', 'getActual', 'getRevenue',
                       'getCostSummary', 'getProfit', 'getSummary', 'getTrend',
                       'getDistribution', 'getPending', 'getActive', 'getOptions',
                       'getStatistics', 'getItems', 'getTotal', 'getWorkspace',
                       'getBom', 'getInventory', 'getServiceHistory']
        
        # 简单的启发式判断：如果前面有 list, query 等关键字
        full_match = match.group(0)
        for lst_method in list_methods:
            if lst_method in full_match:
                return f"{api_section}{method_start}data: {{ items: [] }}{method_end}"
        
        return match.group(0)
    
    # 不要用这个策略，太复杂了。直接简单处理：
    # 把所有 { data: {} } 改成 { data: { items: [] } }
    
    # 排除已正确的格式
    # 1. { data: { items: [...] } } - 不改
    # 2. { data: [] } - 不改
    # 3. { data: {} } - 需要改
    
    # 匹配 "data: {}" 后面是 ) 或 , 或 }
    # 但要排除已经包含 items 的
    
    # 简单方法：把所有 mockResolvedValue 里的 { data: {} } 改成 { data: { items: [] } }
    # 但有个问题：有些 API 返回的不是列表，是单个对象，这时不应该加 items
    
    # 更好的策略：全部改成 { data: { items: [] } }，因为即使对于单个对象，items: [] 也不会出错
    # 组件代码通常使用 res.data?.items || res.data，所以空的 items 数组是安全的
    
    # 匹配 mockResolvedValue({ data: {} })
    # 更精确：匹配 vi.fn().mockResolvedValue({ data: {} })
    
    content = re.sub(
        r"(vi\.fn\(\)\.mockResolvedValue\(\{)\s*data:\s*\{\}\s*(\}\))",
        r"\1data: { items: [] }\2",
        content
    )
    
    # 同样处理 mockResolvedValueOnce
    content = re.sub(
        r"(vi\.fn\(\)\.mockResolvedValueOnce\(\{)\s*data:\s*\{\}\s*(\}\))",
        r"\1data: { items: [] }\2",
        content
    )
    
    if content != original:
        with open(file_path, 'w', encoding='utf8') as f:
            f.write(content)
        return True
    
    return False

def main():
    print('查找测试文件...')
    test_files = find_test_files()
    print(f'找到 {len(test_files)} 个测试文件')
    
    fixed = 0
    errors = []
    
    for f in test_files:
        try:
            if fix_mock_data(f):
                print(f'修复: {f}')
                fixed += 1
        except Exception as e:
            errors.append((f, str(e)))
    
    print(f'\n修复了 {fixed} 个测试文件')
    
    if errors:
        print(f'\n错误:')
        for f, e in errors:
            print(f'  {f}: {e}')

if __name__ == '__main__':
    main()