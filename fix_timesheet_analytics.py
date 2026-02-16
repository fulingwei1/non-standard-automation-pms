#!/usr/bin/env python3
"""批量修复timesheet_analytics.py的类型注解"""

import re

file_path = "app/schemas/timesheet_analytics.py"

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 替换 List[...] → list[...]
content = re.sub(r'\bList\[', 'list[', content)

# 2. 替换 Dict[...] → dict (因为Dict[str, Any]已经在之前改成dict了)
# content = re.sub(r'\bDict\[str, Any\]', 'dict', content)

# 3. 替换 Optional[List[...]] → Optional[list[...]]  
# (已经被步骤1处理了)

# 4. 为所有没有model_config的BaseModel添加配置
# 找到所有 class XXX(BaseModel): 并在下一行添加 model_config
lines = content.split('\n')
new_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    
    # 检测 class XXX(BaseModel): 模式
    if re.match(r'^class \w+\(BaseModel\):', line):
        # 检查下一行是否已经有 model_config 或 """文档字符串"""
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            # 如果下一行是文档字符串，在文档字符串后插入
            if next_line.strip().startswith('"""'):
                # 找到文档字符串结束
                new_lines.append(next_line)
                i += 1
                # 如果是多行文档字符串
                if not next_line.strip().endswith('"""') or next_line.strip().count('"""') == 1:
                    # 继续找到结束
                    while i < len(lines) - 1:
                        i += 1
                        new_lines.append(lines[i])
                        if '"""' in lines[i]:
                            break
                # 在文档字符串后插入配置
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('model_config'):
                    new_lines.append('    model_config = ConfigDict(arbitrary_types_allowed=True)')
                    new_lines.append('')
            # 如果下一行不是 model_config，插入
            elif not next_line.strip().startswith('model_config'):
                new_lines.append('    model_config = ConfigDict(arbitrary_types_allowed=True)')
                new_lines.append('')
    
    i += 1

content = '\n'.join(new_lines)

# 5. 确保导入了 ConfigDict (可能已经导入了)
if 'from pydantic import' in content and 'ConfigDict' not in content:
    content = content.replace(
        'from pydantic import BaseModel, Field',
        'from pydantic import BaseModel, Field, ConfigDict'
    )

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ 已修复 {file_path}")
print("修复内容:")
print("  1. List[...] → list[...]")
print("  2. 为所有BaseModel添加 model_config = ConfigDict(arbitrary_types_allowed=True)")
