#!/usr/bin/env python3
import re
from pathlib import Path

content = (Path("frontend/src/pages/ContractApproval.jsx").read_text(encoding='utf-8'))

# 替换Mock数据定义为状态
pattern = r"// Mock data - 已移除，使用真实API\nconst mockPendingApprovals = \[\]\nconst mockApprovalHistory = \[\]"
replacement = "const [pendingApprovals, setPendingApprovals] = useState([])\nconst [approvalHistory, setApprovalHistory] = useState([])"

content = re.sub(pattern, replacement, content)

# 替换useMemo中的引用
content = re.sub(r"const approvals = activeTab === 'pending' \? mockPendingApprovals : mockApprovalHistory",
                r"const approvals = activeTab === 'pending' ? pendingApprovals : approvalHistory", content)

Path("frontend/src/pages/ContractApproval.jsx").write_text(content, encoding='utf-8')
print("✅ 已修复: ContractApproval.jsx")
