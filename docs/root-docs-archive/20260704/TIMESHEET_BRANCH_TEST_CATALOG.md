# 工时管理服务分支测试用例目录

## 测试用例分类索引

本文档详细列出了 `tests/unit/test_timesheet_services_branches.py` 中所有30个测试用例的场景、输入、预期输出。

---

## 1. TimesheetRecordsService 分支测试 (8个)

### 1.1 重复提交检测分支

**测试**: `test_create_timesheet_duplicate_detection`

**场景**: 用户尝试为同一日期的同一项目创建重复工时记录

**前置条件**:
- 数据库中已存在记录: user_id=1, work_date=today, project_id=1, status='DRAFT'

**输入**:
```python
TimesheetCreate(
    project_id=1,
    work_date=date.today(),
    work_hours=Decimal('8.0'),
    description='测试'
)
```

**预期输出**:
- 抛出 `HTTPException`
- status_code = 400
- detail 包含 "已有工时记录"

**覆盖分支**:
- `_check_duplicate_timesheet()` 中的重复检测逻辑
- `create_timesheet()` 中的异常抛出路径

---

### 1.2 加班工时类型分支

**测试**: `test_create_timesheet_overtime_type`

**场景**: 创建加班类型的工时记录

**输入**:
```python
TimesheetCreate(
    project_id=1,
    work_date=date.today(),
    work_hours=Decimal('10.0'),
    work_type='OVERTIME',  # 加班类型
    description='加班'
)
```

**预期输出**:
- 不抛出异常
- 成功创建工时记录

**覆盖分支**:
- `create_timesheet()` 中 `overtime_type='OVERTIME'` 的赋值路径
- 加班工时的业务逻辑处理

---

### 1.3 周末工时类型分支

**测试**: `test_create_timesheet_weekend_type`

**场景**: 创建周末工时记录

**输入**:
```python
TimesheetCreate(
    project_id=1,
    work_date=date.today(),
    work_hours=Decimal('8.0'),
    work_type='WEEKEND',  # 周末类型
    description='周末加班'
)
```

**预期输出**:
- 不抛出异常
- 成功创建工时记录

**覆盖分支**:
- `create_timesheet()` 中 `overtime_type='WEEKEND'` 的赋值路径
- 周末工时的特殊处理

---

### 1.4 已审批不可修改分支

**测试**: `test_update_timesheet_approved_rejection`

**场景**: 用户尝试修改已审批的工时记录

**前置条件**:
- 工时记录 id=1, user_id=1, status='APPROVED'

**输入**:
```python
TimesheetUpdate(work_hours=Decimal('10.0'))
```

**预期输出**:
- 抛出 `HTTPException`
- status_code = 400
- detail 包含 "只能修改草稿"

**覆盖分支**:
- `update_timesheet()` 中 `status != 'DRAFT'` 的判断分支
- 已审批记录的保护逻辑

---

### 1.5 已审批不可删除分支

**测试**: `test_delete_timesheet_approved_rejection`

**场景**: 用户尝试删除已审批的工时记录

**前置条件**:
- 工时记录 id=1, user_id=1, status='APPROVED'

**预期输出**:
- 抛出 `HTTPException`
- status_code = 400
- detail 包含 "只能删除草稿"

**覆盖分支**:
- `delete_timesheet()` 中 `status != 'DRAFT'` 的判断分支
- 已审批记录的删除保护

---

### 1.6 无权修改他人记录分支

**测试**: `test_update_timesheet_permission_denied`

**场景**: 普通用户尝试修改他人的工时记录

**前置条件**:
- 当前用户: user_id=1, is_superuser=False
- 工时记录: id=1, user_id=999, status='DRAFT'

**输入**:
```python
TimesheetUpdate(work_hours=Decimal('10.0'))
```

**预期输出**:
- 抛出 `HTTPException`
- status_code = 403
- detail 包含 "无权修改"

**覆盖分支**:
- `update_timesheet()` 中 `user_id != current_user.id` 的权限检查分支
- 跨用户访问控制

---

### 1.7 批量提交混合结果分支

**测试**: `test_batch_create_timesheets_mixed_results`

**场景**: 批量创建工时记录,部分成功部分失败

**输入**:
```python
[
    TimesheetCreate(project_id=1, ...),  # 成功
    TimesheetCreate(project_id=999, ...), # 失败 - 项目不存在
    TimesheetCreate(project_id=1, ...)   # 成功
]
```

**预期输出**:
```python
{
    'success_count': 2,
    'failed_count': 1,
    'errors': [{'date': '...', 'error': '项目不存在'}]
}
```

**覆盖分支**:
- `batch_create_timesheets()` 中的成功和失败计数逻辑
- 项目验证失败分支
- 重复记录检测分支
- 异常捕获和错误收集分支

---

### 1.8 访问控制分支 (失败)

**测试**: `test_get_timesheet_detail_access_control`

**场景**: 测试三种访问情况
1. 访问自己的记录 → 允许
2. 普通用户访问他人记录 → 拒绝
3. 管理员访问他人记录 → 允许

**状态**: ❌ 失败 (Pydantic 验证错误)

**失败原因**: Mock 对象未正确返回字符串类型的 `user_name`

**覆盖分支**:
- `_check_access_permission()` 中的权限判断
- 超级用户绕过检查的分支

---

## 2. TimesheetAnalyticsService 分支测试 (6个)

### 2.1 加班趋势分析分支 (失败)

**测试**: `test_analyze_overtime_trends`

**场景**: 分析一周的加班趋势

**输入**:
```python
period_type='DAILY'
start_date=date.today() - timedelta(days=7)
end_date=date.today()
```

**模拟数据**:
- total_overtime=50.0, weekend_hours=20.0, holiday_hours=10.0
- 7天趋势数据,每天加班 5-12 小时

**预期输出**:
- total_overtime_hours > 0
- overtime_rate > 0
- weekend_hours >= 0
- holiday_hours >= 0
- top_overtime_users 列表
- overtime_trend 图表数据

**状态**: ❌ 失败 (Schema 缺少 weekend_hours 字段)

**覆盖分支**:
- `analyze_overtime()` 中的加班统计计算
- 周末/节假日工时的分别统计
- 人均加班计算
- Top10 加班人员查询

---

### 2.2 部门对比分支 (失败)

**测试**: `test_analyze_department_comparison`

**场景**: 对比三个部门的工时情况,包括未分配部门

**模拟数据**:
```python
[
    {dept_id=1, name='技术部', total=500, normal=400, overtime=100},
    {dept_id=2, name='产品部', total=300, normal=280, overtime=20},
    {dept_id=None, name=None, total=100, normal=90, overtime=10}  # 未分配
]
```

**预期输出**:
- departments 列表包含3个部门
- 未分配部门显示为 '未分配'
- 包含 rankings (按总工时排序)
- 包含 chart_data (柱状图数据)

**状态**: ❌ 失败 (Schema 验证问题)

**覆盖分支**:
- `analyze_department_comparison()` 中的部门分组
- 人均工时计算
- 加班率计算
- 未分配部门的特殊处理 (`department_name or '未分配'`)

---

### 2.3 项目分布分支 (失败)

**测试**: `test_analyze_project_distribution`

**场景**: 分析工时在多个项目间的分布

**模拟数据**:
- 项目A: 500小时 (50%)
- 项目B: 300小时 (30%)
- 项目C: 200小时 (20%)

**预期输出**:
- total_projects = 3
- total_hours = 1000
- concentration_index > 0 (前3项目集中度)
- pie_chart 数据
- project_details 列表

**状态**: ❌ 失败 (Schema 验证问题)

**覆盖分支**:
- `analyze_project_distribution()` 中的项目分组
- 百分比计算
- 集中度指数计算 (top3_percentage / 100)

---

### 2.4 效率指标分支 (失败)

**测试**: `test_analyze_efficiency_metrics`

**场景**: 计算工时效率指标

**模拟数据**:
- actual_hours = 200.0
- planned_hours = 180.0 (actual * 0.9)

**预期输出**:
- actual_hours = 200
- planned_hours = 180
- efficiency_rate = 90% (planned/actual)
- variance_hours = 20
- variance_rate = 11.11%
- insights 列表 (效率分析建议)

**状态**: ❌ 失败 (Schema 验证问题)

**覆盖分支**:
- `analyze_efficiency()` 中的效率率计算
- 偏差率计算
- 洞察建议生成 (效率<80%, 效率>120%, 偏差>20%)

---

### 2.5 无数据情况分支

**测试**: `test_analyze_no_data`

**场景**: 查询期间无任何工时数据

**输入**: 空查询结果

**预期输出**:
- total_hours = 0
- average_hours = 0
- trend = 'STABLE'

**状态**: ✅ 通过

**覆盖分支**:
- `analyze_trend()` 中空数据集的处理
- `_calculate_trend()` 中 `len(results) < 2` 的分支
- 零除保护

---

### 2.6 部分数据缺失分支

**测试**: `test_analyze_partial_data`

**场景**: 查询结果中字段为None

**模拟数据**:
```python
{
    work_date=date.today(),
    total_hours=None,
    normal_hours=None,
    overtime_hours=None
}
```

**预期输出**:
- total_hours = 0 (None 被处理为 0)
- trend = 'STABLE'

**状态**: ✅ 通过

**覆盖分支**:
- `analyze_trend()` 中 `r.total_hours or 0` 的None处理
- 统计计算中的None值保护

---

## 3. TimesheetForecastService 分支测试 (7个)

### 3.1 历史平均法预测分支 (失败)

**测试**: `test_forecast_project_hours_historical_average`

**场景**: 基于相似项目的平均工时预测新项目

**输入**:
```python
project_name='新项目'
complexity='MEDIUM'
team_size=5
duration_days=30
forecast_method='HISTORICAL_AVERAGE'
```

**模拟数据**:
- 相似项目A: 800小时
- 相似项目B: 1000小时

**预期输出**:
- forecast_method = 'HISTORICAL_AVERAGE'
- predicted_hours > 0
- confidence_level = 70
- similar_projects 列表包含2个项目

**状态**: ❌ 失败 (复杂查询 mock 问题)

**覆盖分支**:
- `_forecast_by_historical_average()` 中的相似项目查询
- 平均值计算
- 团队规模和周期调整
- 复杂度系数应用

---

### 3.2 线性回归预测分支 (失败)

**测试**: `test_forecast_completion_date`

**场景**: 使用线性回归算法预测项目工时

**输入**:
```python
forecast_method='LINEAR_REGRESSION'
complexity='HIGH'
team_size=8
duration_days=45
```

**模拟数据**: 5个历史项目数据

**预期输出**:
- forecast_method = 'LINEAR_REGRESSION'
- predicted_hours > 0
- algorithm_params 包含 r_squared, feature_importance

**状态**: ❌ 失败 (复杂查询 mock 问题)

**覆盖分支**:
- `_forecast_by_linear_regression()` 中的历史数据查询
- 特征编码 (team_size, duration, complexity)
- sklearn LinearRegression 训练
- R² 计算和置信度换算

---

### 3.3 负荷预警分支 (失败)

**测试**: `test_forecast_workload_warning`

**场景**: 预测大型项目触发负荷预警

**输入**:
```python
complexity='HIGH'
team_size=15  # 大团队
duration_days=60
```

**模拟数据**: 大项目 1500小时

**预期输出**:
- predicted_hours > 1000
- recommendations 包含预警建议

**状态**: ❌ 失败

**覆盖分支**:
- `_forecast_by_historical_average()` 中的建议生成逻辑
- `predicted_hours > 1000` 分支
- `team_size > 10` 分支
- `complexity == 'HIGH'` 分支

---

### 3.4 无历史数据分支 (失败)

**测试**: `test_forecast_no_history`

**场景**: 全新类型项目,无相似历史数据

**输入**: 查询返回空结果

**预期输出**:
- confidence_level = 50 (低置信度)
- predicted_hours > 0 (使用默认估算)
- historical_projects_count = 0

**状态**: ❌ 失败

**覆盖分支**:
- `_forecast_by_historical_average()` 中 `not similar_results` 分支
- 默认估算逻辑 (8小时/人/天 * 复杂度系数)

---

### 3.5 数据不足退化分支 (失败)

**测试**: `test_forecast_insufficient_data`

**场景**: 线性回归数据不足(<3条),退化到历史平均法

**输入**: 只有1条历史数据

**预期输出**:
- forecast_method = 'HISTORICAL_AVERAGE' (退化)

**状态**: ❌ 失败

**覆盖分支**:
- `_forecast_by_linear_regression()` 中 `len(historical_data) < 3` 分支
- 方法退化逻辑

---

### 3.6 高置信度分支 (失败)

**测试**: `test_forecast_high_confidence`

**场景**: 有10个相似项目,高置信度预测

**模拟数据**: 10个相似项目

**预期输出**:
- confidence_level >= 70
- historical_projects_count = 10

**状态**: ❌ 失败

**覆盖分支**:
- `_forecast_by_historical_average()` 中置信度计算
- 充足数据的高置信度路径

---

### 3.7 低置信度分支 (失败)

**测试**: `test_forecast_low_confidence`

**场景**: 无数据时的低置信度预测

**预期输出**:
- confidence_level <= 70
- recommendations 包含低置信度建议

**状态**: ❌ 失败

**覆盖分支**:
- 低置信度建议生成 (`confidence_level < 70`)

---

## 4. TimesheetAggregationService 分支测试 (7个)

### 4.1 按用户汇总分支 (失败)

**测试**: `test_aggregate_by_user`

**场景**: 汇总某用户的月度工时

**输入**:
```python
year=2024, month=1, user_id=1
```

**预期输出**:
```python
{
    'success': True,
    'total_hours': 160.0,
    'summary_id': 1
}
```

**状态**: ❌ 失败 (@patch 路径问题)

**覆盖分支**:
- `aggregate_monthly_timesheet()` 中 `user_id` 参数的使用
- `summary_type = 'USER_MONTH'` 分支

---

### 4.2 按项目汇总分支 (失败)

**测试**: `test_aggregate_by_project`

**场景**: 汇总某项目的月度工时

**输入**:
```python
year=2024, month=1, project_id=1
```

**预期输出**:
- total_hours = 500.0

**状态**: ❌ 失败 (@patch 路径问题)

**覆盖分支**:
- `summary_type = 'PROJECT_MONTH'` 分支

---

### 4.3 按部门汇总分支 (失败)

**测试**: `test_aggregate_by_department`

**场景**: 汇总某部门的月度工时

**输入**:
```python
year=2024, month=1, department_id=1
```

**预期输出**:
- total_hours = 1200.0

**状态**: ❌ 失败 (@patch 路径问题)

**覆盖分支**:
- `summary_type = 'DEPT_MONTH'` 分支

---

### 4.4 月度汇总分支

**测试**: `test_aggregate_monthly`

**场景**: 生成HR月度报表

**输入**:
```python
year=2024, month=1
```

**模拟数据**: 20天工作日的工时记录

**预期输出**:
- 返回用户工时列表 (List[Dict])

**状态**: ✅ 通过

**覆盖分支**:
- `generate_hr_report()` 中的用户分组逻辑
- 加班类型分类 (NORMAL/OVERTIME/WEEKEND/HOLIDAY)
- 月度范围计算

---

### 4.5 周汇总分支

**测试**: `test_aggregate_weekly`

**场景**: 通过自定义范围实现周汇总

**输入**: 最近7天的数据

**状态**: ✅ 通过

**覆盖分支**:
- 自定义日期范围查询
- 周期性汇总逻辑

---

### 4.6 自定义范围分支

**测试**: `test_aggregate_custom_range`

**场景**: 生成项目成本汇总 (财务报表)

**输入**:
```python
year=2024, month=1, project_id=1
```

**预期输出**:
- 项目工时成本数据 (工时 * 时薪)

**状态**: ✅ 通过

**覆盖分支**:
- `generate_finance_report()` 中的项目分组
- 时薪查询和成本计算

---

### 4.7 研发项目汇总分支

**测试**: `test_aggregate_rd_project`

**场景**: 汇总研发项目工时 (用于研发费用核算)

**输入**:
```python
year=2024, month=1, rd_project_id=1
```

**模拟数据**: 10天研发工时

**预期输出**:
- 研发项目信息 (rd_project_code, rd_project_name)
- 研发成本数据

**状态**: ✅ 通过

**覆盖分支**:
- `generate_rd_report()` 中的研发项目查询
- `rd_project_id.isnot(None)` 过滤条件

---

## 5. 综合场景测试 (2个)

### 5.1 完整工时工作流

**测试**: `test_complete_timesheet_workflow`

**场景**: 测试工时管理的完整流程

**流程**:
1. 创建工时
2. 尝试重复创建 (失败)
3. 更新工时
4. 删除工时

**状态**: ✅ 通过 (仅结构测试)

---

### 5.2 分析预测集成

**测试**: `test_analytics_forecast_integration`

**场景**: 验证分析和预测服务可以集成使用

**流程**:
1. 先分析历史数据
2. 基于分析结果进行预测

**状态**: ✅ 通过 (仅结构测试)

---

## 测试统计摘要

| 服务模块 | 测试数 | 通过 | 失败 | 通过率 |
|---------|--------|------|------|--------|
| TimesheetRecordsService | 8 | 7 | 1 | 87.5% |
| TimesheetAnalyticsService | 6 | 2 | 4 | 33.3% |
| TimesheetForecastService | 7 | 0 | 7 | 0% |
| TimesheetAggregationService | 7 | 4 | 3 | 57.1% |
| 综合场景 | 2 | 2 | 0 | 100% |
| **总计** | **30** | **15** | **15** | **50%** |

## 失败原因分类

| 失败原因 | 数量 | 受影响测试 |
|---------|------|-----------|
| Schema 字段缺失 | 4 | 分析服务 (加班/部门/项目/效率) |
| 复杂查询 Mock 问题 | 7 | 预测服务 (所有测试) |
| @patch 路径错误 | 3 | 汇总服务 (用户/项目/部门) |
| Pydantic 验证错误 | 1 | 记录服务 (访问控制) |

---

**文档版本**: 1.0
**最后更新**: 2026-03-07
