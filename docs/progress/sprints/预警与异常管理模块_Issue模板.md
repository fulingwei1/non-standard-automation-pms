# 预警与异常管理模块 Issue 模板

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
- 设计文档: `claude 设计方案/预警与异常管理模块_详细设计文档.md`
- 任务清单: `预警与异常管理模块_Sprint和Issue任务清单.md`
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
  "sprint": "Sprint 1: 通知机制与规则配置",
  "issues": [
    {
      "title": "站内消息通知服务",
      "priority": "P0",
      "estimate": 8,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "notification"],
      "description": "实现站内消息通知服务，支持预警通知的发送、存储和阅读状态管理。",
      "acceptance_criteria": [
        "创建 app/services/notification_service.py 服务类",
        "实现 send_alert_notification() 方法",
        "实现 mark_notification_read() 方法",
        "实现 get_user_notifications() 方法",
        "在预警生成时自动调用通知服务",
        "添加单元测试覆盖通知发送和阅读场景"
      ],
      "files": ["app/services/notification_service.py"],
      "dependencies": []
    },
    {
      "title": "预警通知发送集成",
      "priority": "P0",
      "estimate": 6,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "notification"],
      "description": "将通知服务集成到预警生成流程中，确保预警生成时自动发送通知。",
      "acceptance_criteria": [
        "在所有预警服务中集成通知发送",
        "通知发送失败不影响预警记录创建",
        "添加错误日志记录"
      ],
      "files": ["app/utils/scheduled_tasks.py"],
      "dependencies": ["Issue 1.1"]
    },
    {
      "title": "通知重试机制",
      "priority": "P0",
      "estimate": 5,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "notification"],
      "description": "实现通知发送失败时的重试机制，确保重要通知能够成功送达。",
      "acceptance_criteria": [
        "实现 retry_failed_notifications() 定时任务",
        "重试间隔：第1次5分钟，第2次30分钟，第3次2小时",
        "超过最大重试次数后标记为 ABANDONED",
        "注册到定时任务调度器，每小时执行一次"
      ],
      "files": ["app/utils/scheduled_tasks.py"],
      "dependencies": ["Issue 1.1", "1.2"]
    },
    {
      "title": "预警规则配置页面",
      "priority": "P0",
      "estimate": 10,
      "assignee": "Frontend Team",
      "labels": ["frontend", "sprint1", "rule-config"],
      "description": "实现预警规则配置的前端页面，支持规则的创建、编辑、启用/禁用等操作。",
      "acceptance_criteria": [
        "创建 AlertRuleManagement.jsx 页面",
        "规则列表展示（编码、名称、类型、状态）",
        "规则创建/编辑表单（基本信息、监控对象、触发条件、通知配置）",
        "规则模板选择功能",
        "表单验证（编码唯一性、必填项、阈值格式）",
        "系统预置规则标识和保护"
      ],
      "files": ["frontend/src/pages/AlertRuleManagement.jsx"],
      "dependencies": ["Issue 1.5"]
    },
    {
      "title": "预警规则管理API完善",
      "priority": "P0",
      "estimate": 5,
      "assignee": "Backend Team",
      "labels": ["backend", "sprint1", "api"],
      "description": "完善预警规则管理API，确保前端页面所需的所有接口都已实现。",
      "acceptance_criteria": [
        "检查所有规则管理API接口",
        "添加规则配置验证逻辑",
        "完善错误响应，返回详细的验证错误信息",
        "添加 API 文档注释"
      ],
      "files": ["app/api/v1/endpoints/alerts.py"],
      "dependencies": []
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
with open("预警与异常管理模块_Issue数据.json", "r", encoding="utf-8") as f:
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
- 设计文档: `claude 设计方案/预警与异常管理模块_详细设计文档.md`
- 任务清单: `预警与异常管理模块_Sprint和Issue任务清单.md`
- 完成情况评估: `预警与异常管理模块完成情况评估.md`
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
站内消息通知服务,Story,P0,8,Backend Team,"实现站内消息通知服务","创建 notification_service.py|实现 send_alert_notification()|实现 mark_notification_read()|实现 get_user_notifications()","backend,sprint1,notification"
预警通知发送集成,Story,P0,6,Backend Team,"将通知服务集成到预警生成流程","在所有预警服务中集成通知发送|通知发送失败不影响预警记录创建|添加错误日志记录","backend,sprint1,notification"
通知重试机制,Story,P0,5,Backend Team,"实现通知发送失败时的重试机制","实现 retry_failed_notifications() 定时任务|重试间隔：第1次5分钟，第2次30分钟，第3次2小时|超过最大重试次数后标记为 ABANDONED","backend,sprint1,notification"
预警规则配置页面,Story,P0,10,Frontend Team,"实现预警规则配置的前端页面","创建 AlertRuleManagement.jsx|规则列表展示|规则创建/编辑表单|表单验证","frontend,sprint1,rule-config"
预警规则管理API完善,Story,P0,5,Backend Team,"完善预警规则管理API","检查所有规则管理API接口|添加规则配置验证逻辑|完善错误响应","backend,sprint1,api"
```

---

## 使用说明

1. **GitHub Issues**: 使用 JSON 格式数据，运行 Python 脚本批量创建
2. **Jira**: 使用 CSV 格式导入，或手动创建
3. **其他工具**: 根据工具要求调整模板格式

---

## Issue 创建检查清单

在创建 Issue 前，请确认：

- [ ] 已明确 Issue 的优先级（P0/P1/P2）
- [ ] 已估算 Story Points
- [ ] 已明确负责人（Backend/Frontend/Full Stack）
- [ ] 已列出所有验收标准
- [ ] 已明确技术实现方案
- [ ] 已识别依赖关系
- [ ] 已添加相关标签
- [ ] 已关联设计文档或相关 Issue

---

**文档版本**: v1.0  
**最后更新**: 2026-01-15
