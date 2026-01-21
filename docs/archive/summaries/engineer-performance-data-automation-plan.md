# 工程师绩效数据源自动化优化详细规划

## 一、优化目标

将绩效评估数据自动化程度从当前的 **70-80%** 提升到 **90-95%**，大幅减少人工填写工作量。

---

## 二、当前数据源分析

### 2.1 完全自动化（无需人工）✅
- 任务完成情况（Task表）
- 项目参与数据（ProjectMember表）
- ECN责任数据（Ecn表）
- BOM数据（BomHeader/BomItem表）
- 方案工程师数据（PresaleSolution/Contract表）

### 2.2 需要优化的数据源 ⚠️

| 数据源 | 当前状态 | 优化目标 | 优先级 |
|--------|---------|---------|--------|
| **工作日志** | 需要工程师每天填写 | 从工时系统自动生成摘要 | 🔴 高 |
| **设计评审** | 需要评审时记录 | 从技术评审系统自动同步 | 🔴 高 |
| **调试问题** | 需要记录问题 | 从问题管理系统自动同步 | 🔴 高 |
| **知识贡献** | 需要工程师提交 | 从代码仓库/文档系统自动识别 | 🟡 中 |

---

## 三、详细优化方案

### 3.1 工作日志自动生成（从工时系统集成）

#### 3.1.1 实现方案
- **数据源**：`Timesheet` 表（工时记录）
- **自动生成逻辑**：
  1. 每日定时任务扫描已审批的工时记录
  2. 按用户、日期聚合工时记录
  3. 自动生成工作日志摘要（包含工作内容、项目、任务等）
  4. 如果工作日志已存在，则更新；否则创建新日志

#### 3.1.2 生成规则
```python
工作日志内容 = f"""
今日工作内容：
- 项目：{project_name}（{hours}小时）
- 任务：{task_name}
- 工作内容：{work_content}
- 工作成果：{work_result}
- 进度：{progress_before}% → {progress_after}%
"""
```

#### 3.1.3 实现文件
- `app/services/work_log_auto_generator.py` - 工作日志自动生成服务
- `app/utils/scheduled_tasks/work_log_auto_tasks.py` - 定时任务

#### 3.1.4 自动化程度
- **优化前**：需要工程师每天填写 ⚠️
- **优化后**：系统自动生成，工程师只需确认或补充 ✅

---

### 3.2 设计评审自动同步（从技术评审系统集成）

#### 3.2.1 实现方案
- **数据源**：`TechnicalReview` 表（技术评审）
- **自动同步逻辑**：
  1. 监听技术评审状态变更（评审完成时）
  2. 自动提取评审结果（一次通过/有条件通过/不通过）
  3. 自动创建或更新 `DesignReview` 记录
  4. 自动关联到项目成员

#### 3.2.2 同步规则
```python
设计评审记录 = {
    'review_date': review.actual_date or review.scheduled_date,
    'is_first_pass': review.conclusion == 'PASS',
    'review_result': review.conclusion,
    'review_type': review.review_type,  # PDR/DDR/PRR/FRR/ARR
    'project_id': review.project_id,
    'reviewer_id': review.host_id,
    'designer_id': review.presenter_id
}
```

#### 3.2.3 实现文件
- `app/services/design_review_sync_service.py` - 设计评审同步服务
- 在技术评审API中添加同步触发器

#### 3.2.4 自动化程度
- **优化前**：需要在评审时手动记录 ⚠️
- **优化后**：评审完成时自动同步 ✅

---

### 3.3 调试问题自动同步（从问题管理系统集成）

#### 3.3.1 实现方案
- **数据源**：`Issue` 表（问题管理）
- **自动同步逻辑**：
  1. 监听问题创建和状态变更
  2. 根据问题分类（PROJECT/TASK）和类型（DEFECT/BUG）自动识别调试问题
  3. 自动创建 `MechanicalDebugIssue` 或 `TestBugRecord` 记录
  4. 自动提取问题信息（发现日期、解决日期、修复时长等）

#### 3.3.2 同步规则
```python
# 机械调试问题
if issue.category == 'PROJECT' and issue.issue_type == 'DEFECT':
    创建 MechanicalDebugIssue {
        'issue_description': issue.description,
        'found_date': issue.report_date,
        'resolved_date': issue.resolved_at,
        'fix_duration_hours': 计算修复时长,
        'severity': issue.severity,
        'responsible_id': issue.assignee_id
    }

# 测试Bug记录
if issue.category == 'PROJECT' and issue.issue_type == 'BUG':
    创建 TestBugRecord {
        'title': issue.title,
        'description': issue.description,
        'found_time': issue.report_date,
        'resolved_time': issue.resolved_at,
        'fix_duration_hours': 计算修复时长,
        'severity': issue.severity,
        'reporter_id': issue.reporter_id,
        'assignee_id': issue.assignee_id
    }
```

#### 3.3.3 实现文件
- `app/services/debug_issue_sync_service.py` - 调试问题同步服务
- 在问题管理API中添加同步触发器

#### 3.3.4 自动化程度
- **优化前**：需要手动记录调试问题 ⚠️
- **优化后**：问题创建/解决时自动同步 ✅

---

### 3.4 知识贡献自动识别（从代码仓库/文档系统集成）

#### 3.4.1 实现方案
- **数据源**：
  - 代码仓库（Git提交记录）
  - 文档系统（KnowledgeBase表）
  - 服务工单（ServiceTicket表，自动提取知识）
- **自动识别逻辑**：
  1. 扫描代码提交记录，识别可复用的代码模块
  2. 从服务工单自动提取知识（已有 `knowledge_extraction_service.py`）
  3. 自动创建 `KnowledgeContribution` 或 `CodeModule` 记录
  4. 自动标记贡献类型和标签

#### 3.4.2 识别规则
```python
# 代码模块识别
if git_commit.message 包含关键词 ['模块', '库', '工具', 'utils', 'common']:
    创建 CodeModule {
        'module_name': 从提交信息提取,
        'author_id': commit.author_id,
        'file_path': commit.file_path,
        'description': commit.message
    }

# 知识贡献识别（从服务工单）
if service_ticket 已解决 and 包含技术方案:
    创建 KnowledgeContribution {
        'contribution_type': 'troubleshooting',
        'title': ticket.title,
        'description': ticket.solution,
        'contributor_id': ticket.resolver_id
    }
```

#### 3.4.3 实现文件
- `app/services/knowledge_auto_identification_service.py` - 知识贡献自动识别服务
- `app/utils/scheduled_tasks/knowledge_auto_tasks.py` - 定时任务

#### 3.4.4 自动化程度
- **优化前**：需要工程师主动提交 ⚠️
- **优化后**：系统自动识别和创建 ✅

---

## 四、技术实现架构

### 4.1 服务层架构

```
┌─────────────────────────────────────────┐
│   PerformanceDataCollector (现有)      │
│   - 数据采集服务                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   自动数据同步服务层（新增）            │
├─────────────────────────────────────────┤
│ 1. WorkLogAutoGenerator                 │
│    - 从工时系统自动生成工作日志          │
├─────────────────────────────────────────┤
│ 2. DesignReviewSyncService               │
│    - 从技术评审系统自动同步              │
├─────────────────────────────────────────┤
│ 3. DebugIssueSyncService                │
│    - 从问题管理系统自动同步              │
├─────────────────────────────────────────┤
│ 4. KnowledgeAutoIdentificationService   │
│    - 从代码仓库/文档系统自动识别          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│   业务系统（数据源）                    │
├─────────────────────────────────────────┤
│ - Timesheet (工时系统)                  │
│ - TechnicalReview (技术评审系统)        │
│ - Issue (问题管理系统)                  │
│ - Git Repository (代码仓库)              │
│ - KnowledgeBase (知识库)                │
└─────────────────────────────────────────┘
```

### 4.2 同步机制

#### 4.2.1 实时同步（事件驱动）
- 技术评审完成时 → 自动同步设计评审
- 问题创建/解决时 → 自动同步调试问题

#### 4.2.2 定时同步（定时任务）
- 每日凌晨：自动生成工作日志（从昨日工时记录）
- 每周一次：扫描代码仓库，识别知识贡献
- 每日一次：同步服务工单知识提取

---

## 五、实施计划

### 阶段一：工作日志自动生成（优先级：🔴 高）
1. ✅ 创建 `WorkLogAutoGenerator` 服务
2. ✅ 实现从工时记录生成工作日志逻辑
3. ✅ 创建定时任务（每日凌晨执行）
4. ✅ 更新数据采集服务使用自动生成的工作日志

### 阶段二：设计评审自动同步（优先级：🔴 高）
1. ✅ 创建 `DesignReviewSyncService` 服务
2. ✅ 在技术评审API中添加同步触发器
3. ✅ 实现评审结果自动同步逻辑
4. ✅ 更新数据采集服务使用同步的设计评审

### 阶段三：调试问题自动同步（优先级：🔴 高）
1. ✅ 创建 `DebugIssueSyncService` 服务
2. ✅ 在问题管理API中添加同步触发器
3. ✅ 实现问题信息自动同步逻辑
4. ✅ 更新数据采集服务使用同步的调试问题

### 阶段四：知识贡献自动识别（优先级：🟡 中）
1. ✅ 创建 `KnowledgeAutoIdentificationService` 服务
2. ✅ 实现代码仓库扫描逻辑（可选，需要Git集成）
3. ✅ 增强服务工单知识提取（已有基础）
4. ✅ 创建定时任务（每周执行）

---

## 六、预期效果

### 6.1 自动化程度提升

| 数据源 | 优化前 | 优化后 | 提升 |
|--------|--------|--------|------|
| 工作日志 | 需要填写 | 自动生成+确认 | +80% |
| 设计评审 | 需要记录 | 自动同步 | +100% |
| 调试问题 | 需要记录 | 自动同步 | +100% |
| 知识贡献 | 需要提交 | 自动识别 | +60% |

### 6.2 总体自动化程度
- **优化前**：70-80%
- **优化后**：90-95%
- **提升**：+15-20%

### 6.3 人工工作量减少
- 工作日志填写：从每天填写 → 每周确认一次
- 设计评审记录：从每次记录 → 无需操作
- 调试问题记录：从每次记录 → 无需操作
- 知识贡献提交：从主动提交 → 系统自动识别

---

## 七、风险与应对

### 7.1 数据质量问题
- **风险**：自动生成的数据可能不够准确
- **应对**：提供人工确认和编辑功能，保留原始数据

### 7.2 系统集成问题
- **风险**：不同系统的数据格式不一致
- **应对**：使用适配器模式，统一数据转换

### 7.3 性能问题
- **风险**：大量数据同步可能影响系统性能
- **应对**：使用异步任务、批量处理、定时执行

---

## 八、后续优化方向

1. **AI增强**：使用AI自动生成工作日志摘要，提高质量
2. **智能识别**：使用NLP识别代码模块和知识贡献
3. **实时监控**：添加数据同步监控和异常告警
4. **数据质量报告**：定期生成数据质量报告，识别问题
