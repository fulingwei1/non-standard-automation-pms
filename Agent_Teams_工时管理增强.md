# Agent Teams - 工时管理功能增强

**启动时间**: 2026-02-14 18:44  
**任务发起**: 符哥  
**协调人**: Claude AI Agent  
**并行Teams**: 2个

---

## 🎯 总体目标

**补充工时管理的缺失功能（15%）**

**完成后效果**:
- 工时管理完整度：85% → **100%**
- 工时填报及时率 ↑ 50%
- 工时异常发现时间 ↓ 80%
- 项目工时预测准确率 ↑ 40%

---

## 📋 Agent Teams任务分配

### 🔴 Team 1: 工时提醒自动化（高优先级）

**会话标签**: `timesheet-reminder-automation`  
**会话ID**: `agent:main:subagent:7348fe66-42ef-4f5b-9c8a-8bdd61317274`  
**预计时间**: 2-3天

**任务内容**:
1. ✅ TimesheetReminder数据模型
2. ✅ 自动检测和提醒
   - 未填报工时检测
   - 超时未审批检测
   - 异常工时检测（5条规则）
   - 周末/节假日工时提醒
3. ✅ 定时任务（每天早上9点）
4. ✅ 提醒管理API（4个端点）
5. ✅ 通知机制（邮件/企业微信）
6. ✅ 15+单元测试
7. ✅ 完整文档

**验收标准**:
- [ ] 支持3种提醒类型（未填报/超时审批/异常工时）
- [ ] 定时任务每日自动检测
- [ ] 5条异常工时检测规则
- [ ] 通知机制可用
- [ ] 15+测试用例通过
- [ ] 配置指南完整

**业务价值**:
- 工时填报及时率 ↑ 50%
- 工时异常发现时间 ↓ 80%
- 审批效率 ↑ 30%
- 无需手动催促

**核心功能**:

#### 1. 未填报工时检测
```python
@cron("0 9 * * *")  # 每天早上9点
def check_unfilled_timesheet():
    yesterday = today - 1
    users = get_all_active_users()
    
    for user in users:
        timesheet = get_timesheet(user.id, yesterday)
        if not timesheet:
            send_notification(user, "请及时填报昨日工时")
```

#### 2. 异常工时检测规则
```python
# 规则1: 单日工时 > 12小时
if timesheet.hours > 12:
    alert("工时超过12小时，请确认")

# 规则2: 单日工时 < 0 或 > 24
if timesheet.hours < 0 or timesheet.hours > 24:
    error("工时数据异常")

# 规则3: 周工时 > 60小时
weekly_hours = calculate_weekly_hours(user_id, week)
if weekly_hours > 60:
    alert("本周工时已超60小时")

# 规则4: 连续7天无休息
if check_continuous_work_days(user_id) >= 7:
    alert("连续工作7天，请注意休息")

# 规则5: 工时与任务进度不匹配
if task.hours_spent > task.estimated_hours * 1.5:
    warning("工时超预算50%，请确认")
```

#### 3. 超时审批检测
```python
# 提交3天未审批
submitted_timesheets = get_submitted_timesheets()
for ts in submitted_timesheets:
    days_pending = (today - ts.submit_time).days
    if days_pending > 3:
        notify_approver("工时审批超时：" + ts.user_name)
```

---

### 🟡 Team 2: 工时分析和预测（中高优先级）

**会话标签**: `timesheet-analysis-forecast`  
**会话ID**: `agent:main:subagent:1c3cec43-9b0d-476c-bf5d-b7dcfe3d8d2d`  
**预计时间**: 3-5天

**任务内容**:
1. ✅ 工时分析数据模型（3个）
2. ✅ 工时分析功能（6种分析维度）
   - 工时趋势分析
   - 人员负荷分析
   - 工时效率对比
   - 加班统计分析
   - 部门工时对比
   - 项目工时分布
3. ✅ 工时预测功能（4种）
   - 项目工时预测
   - 完工时间预测
   - 人员负荷预警
   - 工时缺口分析
4. ✅ 工时分析API（6个端点）
5. ✅ 工时预测API（4个端点）
6. ✅ 预测算法（3种方法）
7. ✅ 可视化数据生成
8. ✅ 15+单元测试
9. ✅ 完整文档（含算法说明）

**验收标准**:
- [ ] 支持6种分析维度
- [ ] 支持4种预测功能
- [ ] 3种预测算法完整
- [ ] 可视化数据完整
- [ ] 15+测试用例通过
- [ ] 文档包含算法说明

**业务价值**:
- 项目工时预测准确率 ↑ 40%
- 人员负荷可视化
- 工时效率提升
- 数据驱动决策

**核心功能**:

#### 1. 工时趋势分析
```python
GET /api/v1/timesheet/analytics/trend
{
    "dimension": "monthly",  # daily/weekly/monthly/quarterly
    "user_id": 123,
    "start_date": "2026-01-01",
    "end_date": "2026-02-14",
    "trend_data": [
        {"period": "2026-01", "hours": 176},
        {"period": "2026-02", "hours": 120}
    ],
    "avg_hours": 148,
    "trend": "DECREASING"  # INCREASING/STABLE/DECREASING
}
```

#### 2. 人员负荷分析
```python
GET /api/v1/timesheet/analytics/workload
{
    "users": [
        {
            "user_id": 123,
            "user_name": "张三",
            "weekly_hours": 52,
            "workload_rate": 130%,  # 负荷率（52/40=130%）
            "saturation": "HIGH",  # LOW/MEDIUM/HIGH/CRITICAL
            "projects": ["项目A", "项目B"]
        }
    ],
    "heatmap": [
        {"user": "张三", "week1": 45, "week2": 52, "week3": 48}
    ]
}
```

#### 3. 项目工时预测
```python
POST /api/v1/timesheet/forecast/project
{
    "project_id": 456,
    "prediction": {
        "method": "HISTORICAL_AVERAGE",  # 使用的预测方法
        "predicted_total_hours": 1200,
        "current_hours": 350,
        "remaining_hours": 850,
        "confidence": 0.85,  # 85%置信度
        "similar_projects": [  # 参考的相似项目
            {"project_id": 111, "hours": 1150},
            {"project_id": 222, "hours": 1280}
        ]
    }
}
```

#### 4. 完工时间预测
```python
GET /api/v1/timesheet/forecast/completion?project_id=456
{
    "project_id": 456,
    "current_progress": 30%,
    "hours_spent": 350,
    "predicted_total_hours": 1200,
    "remaining_hours": 850,
    "avg_daily_hours": 25,  # 平均每日工时
    "predicted_days": 34,  # 预计还需34天
    "predicted_completion_date": "2026-03-20",
    "variance_from_plan": 10天,  # 预测延期10天
    "methods": {
        "linear": "2026-03-20",
        "trend_based": "2026-03-18",
        "historical": "2026-03-22"
    }
}
```

#### 5. 预测算法
```python
# 方法1: 历史平均法
def predict_by_historical_avg(project):
    similar_projects = find_similar_projects(project)
    avg_hours = mean([p.total_hours for p in similar_projects])
    return avg_hours

# 方法2: 线性回归
def predict_by_regression(project):
    from sklearn.linear_model import LinearRegression
    X = [[p.complexity, p.team_size] for p in historical_projects]
    y = [p.total_hours for p in historical_projects]
    model = LinearRegression().fit(X, y)
    return model.predict([[project.complexity, project.team_size]])

# 方法3: 趋势预测
def predict_by_trend(project):
    current_hours = project.hours_spent
    current_progress = project.progress
    if current_progress > 0:
        predicted_total = current_hours / (current_progress / 100)
    return predicted_total
```

---

## 📊 进度追踪

| Team | 任务 | 状态 | 进度 | 预计完成 |
|------|------|------|------|---------|
| Team 1 | 工时提醒自动化 | 🟡 进行中 | 0% | 2-3天 |
| Team 2 | 工时分析和预测 | 🟡 进行中 | 0% | 3-5天 |

**总体进度**: 0% (2个任务并行中)

**预计总耗时**: 3-5天（并行开发）  
**串行耗时估算**: 5-8天（节省40%时间）

---

## 🎯 验收标准汇总

### 代码交付
- [ ] 4个新数据模型
- [ ] 14+个API端点
- [ ] 30+个单元测试
- [ ] 定时任务配置

### 文档交付
- [ ] 工时提醒配置指南
- [ ] 工时分析用户手册
- [ ] 预测算法说明
- [ ] API文档

### 功能完整度
- [ ] 工时管理：85% → 100%

---

## 📈 业务价值预期

### 实施提醒自动化后:
- ✅ 工时填报及时率 ↑ 50%
- ✅ 工时异常发现时间 ↓ 80%
- ✅ 审批效率 ↑ 30%
- ✅ 无需手动催促

### 实施分析和预测后:
- ✅ 项目工时预测准确率 ↑ 40%
- ✅ 人员负荷可视化
- ✅ 工时效率提升
- ✅ 数据驱动决策

---

## 🔄 任务依赖关系

```
独立并行（无依赖）:
Team 1: 工时提醒自动化
Team 2: 工时分析和预测

可选依赖（不阻塞）:
Team 2 可选使用 Team 1 的异常检测数据
```

**优势**: 2个Teams完全独立，可并行开发，互不阻塞

---

## 🔔 通知策略

### 何时通知符哥
- ✅ 任意Team完成时（阶段性成果）
- ✅ 所有Teams完成时（最终成果）
- ⚠️ 任务遇到阻塞时
- 📊 重要发现或建议时

### 进度检查点
- **6小时**: 检查所有Teams初步进展
- **12小时**: 检查Team 1（高优先级）状态
- **24小时**: 检查所有Teams中期进度
- **48小时**: 评估完成时间，调整计划

---

## 💡 技术亮点

### 1. 工时提醒自动化
- 定时任务（每日自动检测）
- 5条异常工时规则
- 多渠道通知（邮件/企业微信）
- 提醒历史记录

### 2. 工时分析
- 6种分析维度
- 可视化数据（趋势图/热力图/饼图/柱状图）
- 多维度对比
- 实时更新

### 3. 工时预测
- 3种预测算法
- 置信度评估
- 相似项目参考
- 多方法对比

---

## ✅ 成功指标

### 功能指标
- [ ] 2个新模块全部可用
- [ ] 30+测试用例通过
- [ ] API响应时间 < 500ms

### 质量指标
- [ ] 测试覆盖率 > 85%
- [ ] 代码审查通过
- [ ] 文档完整度 100%

### 业务指标
- [ ] 工时管理完整度 +15%
- [ ] 工时填报及时率 +50%
- [ ] 预测准确率 +40%

---

## 📁 交付清单

### 代码文件
```
app/models/
  - timesheet_reminder.py
  - timesheet_analytics.py
  - timesheet_forecast.py

app/api/v1/endpoints/timesheet/
  - reminders.py
  - analytics.py
  - forecast.py

app/tasks/
  - timesheet_reminder_tasks.py

tests/
  - test_timesheet_reminder.py
  - test_timesheet_analytics.py
  - test_timesheet_forecast.py
```

### 文档文件
```
docs/
  - timesheet_reminder_guide.md
  - timesheet_analytics_guide.md
  - timesheet_forecast_guide.md
  - prediction_algorithms.md
```

---

**任务创建**: 2026-02-14 18:44  
**预计完成**: 2026-02-17 ~ 2026-02-19（3-5天）  

**实时状态查询**:
```bash
openclaw sessions list --kinds isolated
```

**2个Agent Teams已启动，正在并行工作中...** 🚀
