# 指标计算引擎实现总结

## 一、实现内容

### 1.1 核心服务

#### ✅ MetricCalculationService（指标计算服务）
**文件**：`app/services/metric_calculation_service.py`

**功能**：
- 根据 `ReportMetricDefinition` 配置动态计算指标值
- 支持多种计算类型：COUNT、SUM、AVG、MAX、MIN、RATIO、CUSTOM
- 支持时间范围筛选（自动识别时间字段）
- 支持条件筛选（filter_conditions）
- 支持22个数据源（Project、Contract、PurchaseOrder等）

**主要方法**：
- `calculate_metric()` - 计算单个指标
- `calculate_metrics_batch()` - 批量计算多个指标
- `format_metric_value()` - 格式化指标值

---

#### ✅ ComparisonCalculationService（对比计算服务）
**文件**：`app/services/comparison_calculation_service.py`

**功能**：
- 计算环比（Month-over-Month，与上月对比）
- 计算同比（Year-over-Year，与去年同期对比）
- 计算年度同比（与去年全年对比）
- 批量计算对比数据

**主要方法**：
- `calculate_mom_comparison()` - 计算环比
- `calculate_yoy_comparison()` - 计算同比
- `calculate_annual_yoy_comparison()` - 计算年度同比
- `calculate_comparisons_batch()` - 批量计算对比

---

### 1.2 报告生成服务增强

#### ✅ MeetingReportService（已修改）
**文件**：`app/services/meeting_report_service.py`

**增强功能**：
- 支持传入 `config_id` 参数
- 根据配置动态计算业务指标
- 自动使用默认配置（如果未指定config_id）
- 集成指标计算引擎和对比计算服务

**修改的方法**：
- `generate_annual_report()` - 增加config_id参数和业务指标计算
- `generate_monthly_report()` - 增加config_id参数和业务指标计算

---

### 1.3 API端点增强

#### ✅ 报告生成API（已修改）
**文件**：`app/api/v1/endpoints/management_rhythm.py`

**增强功能**：
- `MeetingReportGenerateRequest` 增加 `config_id` 字段
- 自动查找并使用默认配置
- 支持传入配置ID生成自定义报告

---

## 二、数据源支持

### 2.1 支持的数据源（22个）

| 数据源 | 模型类 | 说明 |
|--------|--------|------|
| Project | `Project` | 项目管理 |
| Lead | `Lead` | 线索管理 |
| Opportunity | `Opportunity` | 商机管理 |
| Contract | `Contract` | 合同管理 |
| ContractPayment | `ContractPayment` | 回款管理 |
| Invoice | `Invoice` | 发票管理 |
| PurchaseOrder | `PurchaseOrder` | 采购订单 |
| PurchaseOrderItem | `PurchaseOrderItem` | 采购订单明细 |
| GoodsReceipt | `GoodsReceipt` | 收货单 |
| Material | `Material` | 物料 |
| ShortageReport | `ShortageReport` | 缺料上报 |
| Ecn | `Ecn` | 工程变更 |
| AcceptanceOrder | `AcceptanceOrder` | 验收单 |
| AcceptanceIssue | `AcceptanceIssue` | 验收问题 |
| Issue | `Issue` | 问题管理 |
| AlertRecord | `AlertRecord` | 预警记录 |
| Timesheet | `Timesheet` | 工时记录 |
| PerformanceResult | `PerformanceResult` | 绩效结果 |
| OutsourcingOrder | `OutsourcingOrder` | 外协订单 |
| TaskUnified | `TaskUnified` | 任务 |
| StrategicMeeting | `StrategicMeeting` | 战略会议 |
| MeetingActionItem | `MeetingActionItem` | 会议行动项 |

---

## 三、计算类型支持

### 3.1 基础计算类型

| 计算类型 | 说明 | 示例 |
|---------|------|------|
| COUNT | 计数 | 项目总数 |
| SUM | 求和 | 合同总额 |
| AVG | 平均值 | 平均项目进度 |
| MAX | 最大值 | 最大合同额 |
| MIN | 最小值 | 最小成本 |

### 3.2 高级计算类型

| 计算类型 | 说明 | 示例 |
|---------|------|------|
| RATIO | 比率 | 完成率 = 已完成数 / 总数 |
| CUSTOM | 自定义公式 | 成本偏差率 = (实际成本 - 预算) / 预算 |

---

## 四、时间筛选逻辑

### 4.1 自动识别时间字段

系统会根据指标类型自动识别时间字段：

- **新增类指标**：使用 `created_at` 字段
- **完成类指标**：使用 `actual_end_date` 或 `completed_at` 字段
- **合同类指标**：使用 `contract_date` 字段
- **回款类指标**：使用 `payment_date` 字段
- **开票类指标**：使用 `issue_date` 字段
- **工时类指标**：使用 `work_date` 字段
- **会议类指标**：使用 `meeting_date` 字段

### 4.2 时间范围筛选

- 支持日期字段（Date）和日期时间字段（DateTime）
- 自动处理跨月、跨年情况
- 支持周期开始和结束日期

---

## 五、使用示例

### 5.1 生成带业务指标的月度报告

```python
# 1. 创建或获取配置
config = {
    "config_name": "月度经营分析报告",
    "report_type": "MONTHLY",
    "enabled_metrics": [
        {"metric_code": "project_total", "enabled": True},
        {"metric_code": "contract_new_amount", "enabled": True},
        {"metric_code": "payment_monthly", "enabled": True},
        # ... 更多指标
    ],
    "comparison_config": {
        "enable_mom": True,  # 启用环比
        "enable_yoy": True,  # 启用同比
    }
}

# 2. 生成报告（传入config_id）
report_request = {
    "report_type": "MONTHLY",
    "period_year": 2025,
    "period_month": 1,
    "config_id": config_id  # 使用配置
}

# 3. 报告将包含：
# - 会议数据（原有）
# - 业务指标（根据配置计算）
# - 对比数据（环比和同比）
```

---

### 5.2 直接计算指标

```python
from app.services.metric_calculation_service import MetricCalculationService

metric_service = MetricCalculationService(db)

# 计算单个指标
result = metric_service.calculate_metric(
    metric_code="project_total",
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 31)
)

# 批量计算
results = metric_service.calculate_metrics_batch(
    metric_codes=["project_total", "contract_new_amount"],
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 31)
)
```

---

### 5.3 计算对比数据

```python
from app.services.comparison_calculation_service import ComparisonCalculationService

comparison_service = ComparisonCalculationService(db)

# 计算环比
mom_result = comparison_service.calculate_mom_comparison(
    metric_code="project_total",
    year=2025,
    month=1
)

# 计算同比
yoy_result = comparison_service.calculate_yoy_comparison(
    metric_code="project_total",
    year=2025,
    month=1
)
```

---

## 六、报告数据结构

### 6.1 报告数据（report_data）

```json
{
  "summary": {
    "total_meetings": 10,
    "completed_meetings": 8,
    "completion_rate": "80%",
    "total_action_items": 50,
    "completed_action_items": 45,
    "overdue_action_items": 2,
    "action_completion_rate": "90%"
  },
  "meetings": [...],
  "action_items_summary": {...},
  "key_decisions": [...],
  "by_level": {...},
  "business_metrics": {
    "project_total": {
      "metric_code": "project_total",
      "metric_name": "项目总数",
      "value": 25,
      "unit": "个",
      "format_type": "NUMBER",
      "decimal_places": 0
    },
    "contract_new_amount": {
      "metric_code": "contract_new_amount",
      "metric_name": "新签合同额",
      "value": 1000000.00,
      "unit": "元",
      "format_type": "CURRENCY",
      "decimal_places": 2
    }
  }
}
```

### 6.2 对比数据（comparison_data）

```json
{
  "previous_period": "2024-12",
  "current_period": "2025-01",
  "meetings_comparison": {...},
  "business_metrics_comparison": {
    "project_total": {
      "mom": {
        "current_value": 25,
        "previous_value": 20,
        "change": 5,
        "change_rate": 25.0,
        "change_rate_formatted": "+25.00%",
        "is_increase": true
      },
      "yoy": {
        "current_value": 25,
        "previous_value": 15,
        "change": 10,
        "change_rate": 66.67,
        "change_rate_formatted": "+66.67%",
        "is_increase": true
      }
    }
  }
}
```

---

## 七、下一步工作

### 7.1 待优化

1. **时间字段识别优化**
   - 当前逻辑较简单，可能需要根据指标定义更精确地识别时间字段
   - 支持自定义时间字段配置

2. **比率计算增强**
   - 当前只支持简单的完成率计算
   - 需要支持更复杂的比率公式解析

3. **自定义公式计算**
   - 当前CUSTOM类型返回0
   - 需要实现公式解析引擎

4. **错误处理**
   - 增强错误处理和日志记录
   - 提供更详细的错误信息

### 7.2 待实现

1. **前端配置管理界面**（P1）
   - 指标选择界面
   - 配置编辑界面

2. **性能优化**（P2）
   - 指标计算结果缓存
   - 批量查询优化

3. **数据验证**（P2）
   - 指标定义验证
   - 数据源存在性检查

---

## 八、总结

### ✅ 已完成

1. **指标计算引擎** - 支持从88个指标的数据源抽取数据
2. **对比计算服务** - 支持环比和同比计算
3. **报告生成增强** - 集成指标计算引擎
4. **API端点增强** - 支持配置参数

### ⏳ 进行中

1. **测试和验证** - 需要测试各种指标的计算准确性

### 📋 待实现

1. **前端配置管理界面** - 管理部可以配置报告
2. **性能优化** - 提升计算速度
3. **功能增强** - 支持更复杂的计算

---

## 九、技术要点

### 9.1 设计模式

- **服务层模式**：将业务逻辑封装在服务类中
- **策略模式**：不同计算类型使用不同策略
- **工厂模式**：根据数据源类型创建查询

### 9.2 关键实现

1. **动态数据源映射**：使用字典映射数据源名称到模型类
2. **时间字段自动识别**：根据指标类型和数据源自动识别时间字段
3. **条件筛选解析**：解析JSON格式的筛选条件并应用
4. **批量计算优化**：支持批量计算多个指标，提升性能

---

## 十、使用建议

1. **先运行指标初始化脚本**：`python scripts/init_report_metrics.py`
2. **创建报告配置**：通过API或后续的前端界面创建配置
3. **生成报告**：传入config_id生成包含业务指标的报告
4. **查看报告**：报告数据中包含business_metrics和对比数据
