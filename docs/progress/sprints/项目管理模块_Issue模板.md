# 项目管理模块 Issue 模板

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
- 设计文档: `项目管理模块_详细设计文档.md`
- 评估报告: `项目管理模块完成情况评估报告.md`
- 任务清单: `项目管理模块_Sprint和Issue任务清单.md`
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
  "sprint": "Sprint 1: 状态联动与阶段门校验细化",
  "issues": [
    {
      "title": "状态联动规则引擎",
      "priority": "P0",
      "estimate": 10,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "实现状态联动规则引擎，支持设计文档中定义的状态自动流转规则。",
      "acceptance_criteria": [
        "创建状态联动服务 status_transition_service.py",
        "实现状态联动规则配置",
        "实现合同签订→S3/ST08自动流转",
        "实现BOM发布→S5/ST12自动流转",
        "实现关键物料缺货→ST14/H3自动流转",
        "支持事件驱动的状态联动",
        "添加单元测试覆盖所有联动规则"
      ],
      "files": ["app/services/status_transition_service.py"],
      "dependencies": []
    },
    {
      "title": "阶段自动流转实现",
      "priority": "P0",
      "estimate": 8,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "基于状态联动规则引擎，实现阶段自动流转功能。",
      "acceptance_criteria": [
        "实现阶段自动流转检查函数",
        "支持S3→S4自动流转（合同签订后）",
        "支持S4→S5自动流转（BOM发布后）",
        "支持S5→S6自动流转（物料齐套后）",
        "支持S7→S8自动流转（FAT通过后）",
        "支持S8→S9自动流转（终验收通过后）",
        "添加单元测试"
      ],
      "files": ["app/services/status_transition_service.py"],
      "dependencies": ["Issue 1.1"]
    },
    {
      "title": "G1-G8 阶段门校验条件细化",
      "priority": "P0",
      "estimate": 12,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "细化8个阶段门的校验条件，确保所有设计文档中定义的准入条件都得到完整实现。",
      "acceptance_criteria": [
        "G1校验：需求采集表完整性、客户信息齐全",
        "G2校验：需求规格书确认、验收标准明确",
        "G3校验：立项评审通过、合同签订",
        "G4校验：方案评审通过、BOM发布",
        "G5校验：物料齐套率≥80%、关键物料到货",
        "G6校验：装配完成、联调通过",
        "G7校验：FAT验收通过、整改项完成",
        "G8校验：终验收通过、回款达标",
        "所有校验函数返回详细的缺失项列表",
        "添加单元测试覆盖所有校验场景"
      ],
      "files": ["app/api/v1/endpoints/projects.py"],
      "dependencies": ["Issue 1.1"]
    },
    {
      "title": "阶段门校验结果详细反馈",
      "priority": "P0",
      "estimate": 5,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1"],
      "description": "优化阶段门校验结果的反馈，提供更详细、更友好的错误信息和建议。",
      "acceptance_criteria": [
        "校验结果包含缺失项列表",
        "校验结果包含建议操作",
        "校验结果包含相关资源链接",
        "前端展示优化（列表形式、进度显示）",
        "API响应格式优化",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/projects.py", "app/schemas/project.py"],
      "dependencies": ["Issue 1.3"]
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
with open("项目管理模块_Issue数据.json", "r", encoding="utf-8") as f:
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
- 设计文档: `项目管理模块_详细设计文档.md`
- 评估报告: `项目管理模块完成情况评估报告.md`
- 任务清单: `项目管理模块_Sprint和Issue任务清单.md`
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
状态联动规则引擎,Story,P0,10,Backend Team,"实现状态联动规则引擎，支持设计文档中定义的状态自动流转规则","创建状态联动服务|实现状态联动规则配置|实现合同签订→S3/ST08自动流转|实现BOM发布→S5/ST12自动流转","backend,sprint1"
阶段自动流转实现,Story,P0,8,Backend Team,"基于状态联动规则引擎，实现阶段自动流转功能","实现阶段自动流转检查函数|支持S3→S4自动流转|支持S4→S5自动流转|支持S5→S6自动流转","backend,sprint1"
G1-G8 阶段门校验条件细化,Story,P0,12,Backend Team,"细化8个阶段门的校验条件","G1校验：需求采集表完整性|G2校验：需求规格书确认|G3校验：立项评审通过|G4校验：方案评审通过","backend,sprint1"
阶段门校验结果详细反馈,Story,P0,5,Backend Team,"优化阶段门校验结果的反馈","校验结果包含缺失项列表|校验结果包含建议操作|前端展示优化|API响应格式优化","backend,sprint1"
合同签订自动创建项目,Story,P1,8,Backend Team,"实现合同签订后自动创建项目功能","合同签订时自动创建项目|使用合同信息填充项目基本信息|项目状态初始化为 S3/ST08|关联合同ID和客户信息","backend,sprint2"
验收管理状态联动（FAT/SAT）,Story,P1,8,Backend Team,"实现验收管理模块与项目管理模块的状态联动","FAT验收通过时自动更新项目状态|FAT验收不通过时更新状态和健康度|SAT验收通过时允许推进至S9|记录状态变更历史","backend,sprint2"
ECN变更影响交期联动,Story,P1,6,Backend Team,"实现ECN变更管理模块与项目管理模块的联动","检查ECN是否影响项目交期|自动更新项目协商交期|更新项目风险信息|更新项目健康度","backend,sprint2"
项目与销售模块数据同步,Story,P1,5,Backend Team,"实现项目与销售模块的数据双向同步","合同金额变更时自动更新项目|收款计划变更时自动更新项目|项目进度更新时自动更新合同状态|提供数据同步状态查询API","backend,sprint2"
```

---

## 使用说明

1. **GitHub Issues**: 使用 JSON 格式数据，运行 Python 脚本批量创建
2. **Jira**: 使用 CSV 格式导入，或手动创建
3. **其他工具**: 根据工具要求调整模板格式

---

**文档版本**: v1.0  
**最后更新**: 2025-01-XX
