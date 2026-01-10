#!/usr/bin/env python3
import re
from pathlib import Path

file_path = Path("frontend/src/pages/ManufacturingDirectorDashboard.jsx")
content = file_path.read_text(encoding='utf-8')

# 1. 添加useState导入（如果缺失）
if "useState" not in content:
    content = re.sub(
        r"import \{ useState, useEffect",
        "import { useState, useEffect",
        content
    )

# 2. 在状态定义中添加pendingApprovals状态
# 找到shippingStats状态定义，在其后添加
pattern = r"(const \[shippingStats, setShippingStats\] = useState\()"
replacement = r"\1\n  const [pendingApprovals, setPendingApprovals] = useState([])"

content = re.sub(pattern, replacement, content)

# 3. 替换mockPendingApprovals.map为pendingApprovals.map
content = re.sub(r"mockPendingApprovals\.map", r"pendingApprovals.map", content)

file_path.write_text(content, encoding='utf-8')
print("✅ 已修复: ManufacturingDirectorDashboard.jsx")
print("  - 添加了pendingApprovals状态")
print("  - 替换了mockPendingApprovals引用")
