# 销售管理模块 Issue 模板

> 用于在 Jira、GitHub Issues 等项目管理工具中创建 Issue 的模板

---

## Issue 模板 1: 功能开发

```markdown
## 基本信息
- **Sprint**: [Sprint X]
- **优先级**: [P0/P1/P2]
- **估算**: [X] SP
- **负责人**: [姓名]
- **标签**: `backend` / `frontend` / `fullstack`

## 描述
[简要描述要开发的功能]

## 验收标准
- [ ] 验收标准 1
- [ ] 验收标准 2
- [ ] 验收标准 3

## 技术实现
- **文件**: `app/xxx/xxx.py`
- **API**: `GET/POST /api/v1/xxx`
- **依赖**: [依赖的 Issue 编号]

## 参考
- 设计文档: `claude 设计方案/销售管理模块_线索到回款_设计文档.md`
- 相关 Issue: #[issue编号]
```

---

## Issue 模板 2: Bug 修复

```markdown
## 基本信息
- **Sprint**: [Sprint X]
- **优先级**: [P0/P1/P2]
- **估算**: [X] SP
- **负责人**: [姓名]
- **标签**: `bug`

## 问题描述
[描述遇到的问题]

## 复现步骤
1. 步骤 1
2. 步骤 2
3. 步骤 3

## 预期行为
[描述预期的正确行为]

## 实际行为
[描述实际发生的错误行为]

## 环境信息
- 后端版本: [版本号]
- 前端版本: [版本号]
- 数据库: [SQLite/MySQL]
- 浏览器: [Chrome/Firefox/Safari]

## 修复方案
[描述修复方案]

## 测试
- [ ] 单元测试已更新
- [ ] 集成测试已通过
- [ ] 手动测试已验证
```

---

## Issue 模板 3: 技术债务

```markdown
## 基本信息
- **Sprint**: [Sprint X]
- **优先级**: [P0/P1/P2]
- **估算**: [X] SP
- **负责人**: [姓名]
- **标签**: `tech-debt`

## 问题描述
[描述技术债务问题]

## 影响范围
- 模块: [模块名称]
- 影响功能: [功能列表]

## 改进方案
[描述改进方案]

## 收益
[描述改进后的收益]

## 风险评估
[描述改进可能带来的风险]
```

---

## 快速创建 Issue 的 JSON 格式

### Sprint 1 Issues

```json
{
  "sprint": "Sprint 1: 阶段门自动检查与收款计划绑定",
  "issues": [
    {
      "title": "G1 阶段门自动检查（线索→商机）",
      "priority": "P0",
      "estimate": 8,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "实现线索转商机时的自动验证逻辑，检查必填项和数据完整性。",
      "acceptance_criteria": [
        "实现 validate_g1_lead_to_opportunity() 函数",
        "检查客户名称、联系人、联系电话",
        "检查行业、产品对象、节拍、接口、现场约束、验收依据",
        "验证失败时返回详细的错误列表",
        "添加单元测试覆盖所有验证场景"
      ],
      "files": ["app/api/v1/endpoints/sales.py"],
      "dependencies": []
    },
    {
      "title": "G2 阶段门自动检查（商机→报价）",
      "priority": "P0",
      "estimate": 8,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "实现商机转报价时的自动验证逻辑，检查预算、决策链、交付窗口、验收标准等。",
      "acceptance_criteria": [
        "实现 validate_g2_opportunity_to_quote() 函数",
        "检查预算范围、决策链、交付窗口、验收标准",
        "检查技术可行性初评通过",
        "验证失败时阻止报价创建",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/sales.py"],
      "dependencies": ["Issue 1.1"]
    },
    {
      "title": "G3 阶段门自动检查（报价→合同）",
      "priority": "P0",
      "estimate": 10,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "实现报价转合同时的自动验证，包括成本拆解、毛利率检查、交期校验、风险条款检查。",
      "acceptance_criteria": [
        "实现 validate_g3_quote_to_contract() 函数",
        "检查成本拆解齐备",
        "毛利率低于阈值时自动预警",
        "交期校验（关键物料交期 + 设计/装配/调试周期）",
        "检查风险条款与边界条款",
        "添加配置项：毛利率阈值（默认 15%）",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/sales.py"],
      "dependencies": ["Issue 1.2"]
    },
    {
      "title": "G4 阶段门自动检查（合同→项目）",
      "priority": "P0",
      "estimate": 8,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "实现合同生成项目时的自动验证，检查付款节点与交付物绑定、数据完整性。",
      "acceptance_criteria": [
        "实现 validate_g4_contract_to_project() 函数",
        "检查付款节点与可交付物已绑定",
        "检查 SOW/验收标准/BOM初版/里程碑基线已冻结",
        "检查合同交付物清单完整",
        "验证失败时阻止项目生成",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/sales.py"],
      "dependencies": ["Issue 1.3"]
    },
    {
      "title": "收款计划与里程碑自动绑定",
      "priority": "P0",
      "estimate": 6,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "实现合同签订后自动生成收款计划，并与项目里程碑绑定。",
      "acceptance_criteria": [
        "合同签订时自动生成收款计划（ProjectPaymentPlan）",
        "收款计划与合同交付物关联",
        "收款计划与项目里程碑自动绑定（通过 milestone_id）",
        "支持自定义收款比例和节点",
        "添加 API: GET /sales/contracts/{id}/payment-plans",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/sales.py"],
      "dependencies": ["Issue 1.4"]
    }
  ]
}
```

---

## GitHub Issues 批量创建脚本

```python
#!/usr/bin/env python3
"""
批量创建 GitHub Issues 的脚本
需要安装: pip install PyGithub
"""

from github import Github
import json

# 配置
GITHUB_TOKEN = "your_github_token"
REPO_NAME = "your_org/your_repo"

# 读取 Issue 数据
with open("销售管理模块_Issue数据.json", "r", encoding="utf-8") as f:
    issues_data = json.load(f)

# 连接 GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

# 创建 Issues
for sprint_data in issues_data["sprints"]:
    sprint_name = sprint_data["sprint"]
    print(f"\n创建 {sprint_name} 的 Issues...")
    
    for issue in sprint_data["issues"]:
        # 构建 Issue Body
        body = f"""## 描述
{issue['description']}

## 验收标准
{chr(10).join(['- [ ] ' + criteria for criteria in issue['acceptance_criteria']])}

## 技术实现
- **文件**: {', '.join(issue['files'])}
- **依赖**: {', '.join(issue.get('dependencies', []))}

## 参考
- 设计文档: `claude 设计方案/销售管理模块_线索到回款_设计文档.md`
- 任务清单: `销售管理模块_Sprint和Issue任务清单.md`
"""
        
        # 创建 Issue
        created_issue = repo.create_issue(
            title=f"[{sprint_name}] {issue['title']}",
            body=body,
            labels=issue['labels']
        )
        
        print(f"  ✅ 创建 Issue #{created_issue.number}: {issue['title']}")
```

---

## Jira 批量导入 CSV 格式

```csv
Summary,Issue Type,Priority,Story Points,Assignee,Description,Acceptance Criteria,Labels
G1 阶段门自动检查（线索→商机）,Story,P0,8,Backend Team,"实现线索转商机时的自动验证逻辑","实现 validate_g1_lead_to_opportunity() 函数|检查客户名称、联系人、联系电话|检查行业、产品对象、节拍、接口、现场约束、验收依据","backend,sprint1"
G2 阶段门自动检查（商机→报价）,Story,P0,8,Backend Team,"实现商机转报价时的自动验证逻辑","实现 validate_g2_opportunity_to_quote() 函数|检查预算范围、决策链、交付窗口、验收标准|检查技术可行性初评通过","backend,sprint1"
G3 阶段门自动检查（报价→合同）,Story,P0,10,Backend Team,"实现报价转合同时的自动验证","实现 validate_g3_quote_to_contract() 函数|检查成本拆解齐备|毛利率低于阈值时自动预警|交期校验","backend,sprint1"
G4 阶段门自动检查（合同→项目）,Story,P0,8,Backend Team,"实现合同生成项目时的自动验证","实现 validate_g4_contract_to_project() 函数|检查付款节点与可交付物已绑定|检查 SOW/验收标准/BOM初版/里程碑基线已冻结","backend,sprint1"
收款计划与里程碑自动绑定,Story,P0,6,Backend Team,"实现合同签订后自动生成收款计划","合同签订时自动生成收款计划|收款计划与合同交付物关联|收款计划与项目里程碑自动绑定","backend,sprint1"
```

---

## 使用说明

1. **GitHub Issues**: 使用 JSON 格式数据，运行 Python 脚本批量创建
2. **Jira**: 使用 CSV 格式导入，或手动创建
3. **其他工具**: 根据工具要求调整模板格式

---

**文档版本**: v1.0  
**最后更新**: 2026-01-15
