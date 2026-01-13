# 问题管理中心模块 Issue 模板

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
- 设计文档: `claude 设计方案/问题管理中心模块设计.xlsx`
- 评估报告: `问题管理中心模块完成情况评估报告.md`
- 任务清单: `问题管理中心模块_Sprint和Issue任务清单.md`
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
  "sprint": "Sprint 1: 问题模板管理API",
  "issues": [
    {
      "title": "问题模板列表API",
      "priority": "P0",
      "estimate": 3,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "api"],
      "description": "实现获取问题模板列表的API端点，支持分页、搜索和筛选。",
      "acceptance_criteria": [
        "实现 GET /api/v1/issue-templates 接口",
        "支持分页参数（page, page_size）",
        "支持关键词搜索（模板编码、模板名称）",
        "支持分类筛选（category）",
        "支持状态筛选（is_active）",
        "返回 IssueTemplateListResponse 格式数据",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/issues.py"],
      "dependencies": []
    },
    {
      "title": "问题模板详情API",
      "priority": "P0",
      "estimate": 2,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "api"],
      "description": "实现获取单个问题模板详情的API端点。",
      "acceptance_criteria": [
        "实现 GET /api/v1/issue-templates/{id} 接口",
        "验证模板ID存在性",
        "返回 IssueTemplateResponse 格式数据",
        "模板不存在时返回404错误",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/issues.py"],
      "dependencies": []
    },
    {
      "title": "创建问题模板API",
      "priority": "P0",
      "estimate": 4,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "api"],
      "description": "实现创建问题模板的API端点，支持模板编码唯一性验证。",
      "acceptance_criteria": [
        "实现 POST /api/v1/issue-templates 接口",
        "验证模板编码唯一性（template_code）",
        "验证必填字段",
        "支持默认值设置",
        "支持模板变量（title_template, description_template支持变量占位符）",
        "创建成功后返回 IssueTemplateResponse",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/issues.py"],
      "dependencies": []
    },
    {
      "title": "更新问题模板API",
      "priority": "P0",
      "estimate": 3,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "api"],
      "description": "实现更新问题模板的API端点，支持部分更新。",
      "acceptance_criteria": [
        "实现 PUT /api/v1/issue-templates/{id} 接口",
        "验证模板ID存在性",
        "支持部分字段更新",
        "更新模板编码时验证唯一性",
        "更新成功后返回 IssueTemplateResponse",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/issues.py"],
      "dependencies": ["Issue 1.2"]
    },
    {
      "title": "删除问题模板API",
      "priority": "P0",
      "estimate": 2,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "api"],
      "description": "实现删除问题模板的API端点，支持软删除（设置is_active=False）。",
      "acceptance_criteria": [
        "实现 DELETE /api/v1/issue-templates/{id} 接口",
        "验证模板ID存在性",
        "使用软删除（设置 is_active=False）",
        "删除成功后返回成功消息",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/issues.py"],
      "dependencies": ["Issue 1.2"]
    },
    {
      "title": "从模板创建问题API",
      "priority": "P0",
      "estimate": 5,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "api"],
      "description": "实现从模板创建问题的API端点，支持模板变量替换和默认值填充。",
      "acceptance_criteria": [
        "实现 POST /api/v1/issue-templates/{id}/create-issue 接口",
        "验证模板ID存在性和启用状态",
        "从模板读取默认值",
        "支持模板变量替换",
        "支持覆盖模板默认值",
        "自动生成问题编号",
        "更新模板使用统计",
        "返回创建的 IssueResponse",
        "添加单元测试"
      ],
      "files": ["app/api/v1/endpoints/issues.py"],
      "dependencies": ["Issue 1.2", "Issue 1.3"]
    }
  ]
}
```

### Sprint 2 Issues

```json
{
  "sprint": "Sprint 2: 后台定时任务系统",
  "issues": [
    {
      "title": "问题逾期预警定时任务",
      "priority": "P0",
      "estimate": 6,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint2", "scheduler"],
      "description": "实现定时检查逾期问题并发送提醒通知的定时任务。",
      "acceptance_criteria": [
        "创建定时任务 check_overdue_issues()",
        "每小时执行一次",
        "查询所有逾期问题",
        "为每个逾期问题发送通知给处理人",
        "避免重复通知（同一问题每天最多通知一次）",
        "支持配置通知频率",
        "添加单元测试"
      ],
      "files": ["app/services/issue_scheduler.py"],
      "dependencies": []
    },
    {
      "title": "阻塞问题预警定时任务",
      "priority": "P0",
      "estimate": 5,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint2", "scheduler"],
      "description": "实现定时检查阻塞问题并触发项目健康度更新的定时任务。",
      "acceptance_criteria": [
        "创建定时任务 check_blocking_issues()",
        "每小时执行一次",
        "查询所有阻塞问题",
        "为每个阻塞问题关联的项目更新健康度",
        "发送通知给项目负责人",
        "避免重复更新",
        "添加单元测试"
      ],
      "files": ["app/services/issue_scheduler.py"],
      "dependencies": ["Issue 2.1"]
    },
    {
      "title": "问题超时升级定时任务",
      "priority": "P0",
      "estimate": 5,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint2", "scheduler"],
      "description": "实现定时检查长时间未处理的问题并自动升级优先级的定时任务。",
      "acceptance_criteria": [
        "创建定时任务 upgrade_timeout_issues()",
        "每天执行一次（凌晨执行）",
        "查询超时问题",
        "根据超时天数自动升级优先级",
        "记录优先级变更跟进记录",
        "发送通知给处理人和提出人",
        "支持配置超时阈值",
        "添加单元测试"
      ],
      "files": ["app/services/issue_scheduler.py"],
      "dependencies": ["Issue 2.1"]
    },
    {
      "title": "问题统计快照定时任务",
      "priority": "P0",
      "estimate": 8,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint2", "scheduler"],
      "description": "实现每天生成问题统计快照并保存到数据库的定时任务。",
      "acceptance_criteria": [
        "创建定时任务 generate_issue_statistics_snapshot()",
        "每天执行一次（凌晨执行）",
        "统计总体数据、状态分布、严重程度分布等",
        "计算处理时间统计",
        "统计今日数据",
        "保存到 IssueStatisticsSnapshot 表",
        "如果当天快照已存在，则更新而非创建",
        "添加单元测试"
      ],
      "files": ["app/services/issue_scheduler.py"],
      "dependencies": ["Issue 2.1"]
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
with open("问题管理中心模块_Issue数据.json", "r", encoding="utf-8") as f:
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
- 设计文档: `claude 设计方案/问题管理中心模块设计.xlsx`
- 评估报告: `问题管理中心模块完成情况评估报告.md`
- 任务清单: `问题管理中心模块_Sprint和Issue任务清单.md`
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
问题模板列表API,Story,P0,3,Backend Team,"实现获取问题模板列表的API端点","实现 GET /api/v1/issue-templates 接口|支持分页参数|支持关键词搜索|支持分类筛选","backend,sprint1,api"
问题模板详情API,Story,P0,2,Backend Team,"实现获取单个问题模板详情的API端点","实现 GET /api/v1/issue-templates/{id} 接口|验证模板ID存在性|返回 IssueTemplateResponse 格式数据","backend,sprint1,api"
创建问题模板API,Story,P0,4,Backend Team,"实现创建问题模板的API端点","实现 POST /api/v1/issue-templates 接口|验证模板编码唯一性|支持默认值设置|支持模板变量","backend,sprint1,api"
更新问题模板API,Story,P0,3,Backend Team,"实现更新问题模板的API端点","实现 PUT /api/v1/issue-templates/{id} 接口|支持部分字段更新|更新模板编码时验证唯一性","backend,sprint1,api"
删除问题模板API,Story,P0,2,Backend Team,"实现删除问题模板的API端点","实现 DELETE /api/v1/issue-templates/{id} 接口|使用软删除|删除成功后返回成功消息","backend,sprint1,api"
从模板创建问题API,Story,P0,5,Backend Team,"实现从模板创建问题的API端点","实现 POST /api/v1/issue-templates/{id}/create-issue 接口|支持模板变量替换|自动生成问题编号|更新模板使用统计","backend,sprint1,api"
问题逾期预警定时任务,Story,P0,6,Backend Team,"实现定时检查逾期问题并发送提醒通知","创建定时任务 check_overdue_issues()|每小时执行一次|查询所有逾期问题|发送通知给处理人","backend,sprint2,scheduler"
阻塞问题预警定时任务,Story,P0,5,Backend Team,"实现定时检查阻塞问题并触发项目健康度更新","创建定时任务 check_blocking_issues()|每小时执行一次|更新项目健康度|发送通知给项目负责人","backend,sprint2,scheduler"
问题超时升级定时任务,Story,P0,5,Backend Team,"实现定时检查长时间未处理的问题并自动升级优先级","创建定时任务 upgrade_timeout_issues()|每天执行一次|根据超时天数自动升级优先级|记录优先级变更跟进记录","backend,sprint2,scheduler"
问题统计快照定时任务,Story,P0,8,Backend Team,"实现每天生成问题统计快照并保存到数据库","创建定时任务 generate_issue_statistics_snapshot()|每天执行一次|统计总体数据、状态分布等|保存到 IssueStatisticsSnapshot 表","backend,sprint2,scheduler"
```

---

## 使用说明

1. **GitHub Issues**: 使用 JSON 格式数据，运行 Python 脚本批量创建
2. **Jira**: 使用 CSV 格式导入，或手动创建
3. **其他工具**: 根据工具要求调整模板格式

---

**文档版本**: v1.0  
**最后更新**: 2026-01-15
