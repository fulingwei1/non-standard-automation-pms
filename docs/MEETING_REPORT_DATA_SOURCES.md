# 会议报告数据源清单及配置系统设计

## 一、系统可抽取的关键数据清单

### 1.1 项目管理模块数据

#### 📊 项目基础指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 项目总数 | `Project` | 统计项目数量 | ✅ | ✅ |
| 新增项目数 | `Project.created_at` | 本月/年新增项目 | ✅ | ✅ |
| 完成项目数 | `Project.actual_end_date` | 本月/年完成项目 | ✅ | ✅ |
| 进行中项目数 | `Project.stage` | 非S9阶段项目 | ✅ | ✅ |
| 项目合同总额 | `Project.contract_amount` | 所有项目合同金额汇总 | ✅ | ✅ |
| 新增合同额 | `Project.contract_date` | 本月/年新签合同额 | ✅ | ✅ |
| 项目预算总额 | `Project.budget_amount` | 所有项目预算汇总 | ✅ | ✅ |
| 项目实际成本 | `Project.actual_cost` | 所有项目实际成本汇总 | ✅ | ✅ |
| 项目成本偏差 | `budget_amount - actual_cost` | 预算与实际成本差异 | ✅ | ✅ |
| 项目成本偏差率 | `(actual_cost - budget_amount) / budget_amount` | 成本偏差百分比 | ✅ | ✅ |

#### 📈 项目进度指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 平均项目进度 | `Project.progress_pct` | 所有项目进度平均值 | ✅ | ✅ |
| 进度达标项目数 | `Project.progress_pct >= 目标值` | 进度达到目标的项目数 | ✅ | ✅ |
| 进度滞后项目数 | `Project.progress_pct < 计划值` | 进度滞后的项目数 | ✅ | ✅ |
| 项目阶段分布 | `Project.stage` | 各阶段项目数量（S1-S9） | ✅ | ✅ |
| 项目健康度分布 | `Project.health` | H1/H2/H3/H4分布 | ✅ | ✅ |
| 健康度异常项目数 | `Project.health IN ('H2', 'H3')` | 有风险或阻塞的项目数 | ✅ | ✅ |

#### ⏱️ 项目时间指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 平均项目工期 | `actual_end_date - actual_start_date` | 已完成项目的平均工期 | ✅ | ✅ |
| 工期偏差项目数 | `actual_end_date > planned_end_date` | 延期项目数 | ✅ | ✅ |
| 平均延期天数 | `actual_end_date - planned_end_date` | 延期项目的平均延期天数 | ✅ | ✅ |
| 按时完成率 | `按时完成项目数 / 完成项目总数` | 按时完成的项目占比 | ✅ | ✅ |

#### 💰 项目财务指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 项目成本总额 | `ProjectCost.amount` | 所有项目成本汇总 | ✅ | ✅ |
| 物料成本 | `ProjectCost WHERE cost_type='MATERIAL'` | 物料成本汇总 | ✅ | ✅ |
| 人工成本 | `ProjectCost WHERE cost_type='LABOR'` | 人工成本汇总 | ✅ | ✅ |
| 外协成本 | `ProjectCost WHERE cost_type='OUTSOURCING'` | 外协成本汇总 | ✅ | ✅ |
| 财务成本 | `FinancialProjectCost.amount` | 财务部维护的成本 | ✅ | ✅ |
| 成本按类型分布 | `ProjectCost.cost_type` | 各类型成本占比 | ✅ | ✅ |
| 成本按月份分布 | `ProjectCost.cost_date` | 各月份成本分布 | ✅ | ✅ |

---

### 1.2 销售管理模块数据

#### 💼 销售指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 线索总数 | `Lead` | 线索数量 | ✅ | ✅ |
| 新增线索数 | `Lead.created_at` | 本月/年新增线索 | ✅ | ✅ |
| 线索转化率 | `转化为商机的线索数 / 线索总数` | 线索转化率 | ✅ | ✅ |
| 商机总数 | `Opportunity` | 商机数量 | ✅ | ✅ |
| 新增商机数 | `Opportunity.created_at` | 本月/年新增商机 | ✅ | ✅ |
| 商机金额 | `Opportunity.estimated_value` | 商机预估金额汇总 | ✅ | ✅ |
| 报价总数 | `Quote` | 报价单数量 | ✅ | ✅ |
| 报价金额 | `Quote.total_amount` | 报价总金额 | ✅ | ✅ |
| 报价成功率 | `转化为合同的报价数 / 报价总数` | 报价成功率 | ✅ | ✅ |
| 合同总数 | `Contract` | 合同数量 | ✅ | ✅ |
| 新签合同数 | `Contract.contract_date` | 本月/年新签合同 | ✅ | ✅ |
| 合同金额 | `Contract.contract_amount` | 合同总金额 | ✅ | ✅ |
| 新签合同额 | `Contract WHERE contract_date IN 本月/年` | 本月/年新签合同额 | ✅ | ✅ |
| 回款总额 | `ContractPayment.actual_amount` | 实际回款金额 | ✅ | ✅ |
| 本月回款额 | `ContractPayment.payment_date` | 本月回款金额 | ✅ | ✅ |
| 回款率 | `已回款金额 / 合同金额` | 回款完成率 | ✅ | ✅ |
| 发票总数 | `Invoice` | 发票数量 | ✅ | ✅ |
| 开票金额 | `Invoice.amount` | 发票总金额 | ✅ | ✅ |
| 本月开票额 | `Invoice.issue_date` | 本月开票金额 | ✅ | ✅ |

---

### 1.3 采购与物料管理模块数据

#### 🛒 采购指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 采购订单总数 | `PurchaseOrder` | 采购订单数量 | ✅ | ✅ |
| 新增采购订单数 | `PurchaseOrder.order_date` | 本月/年新增订单 | ✅ | ✅ |
| 采购订单金额 | `PurchaseOrder.total_amount` | 采购订单总金额 | ✅ | ✅ |
| 本月采购额 | `PurchaseOrder WHERE order_date IN 本月` | 本月采购金额 | ✅ | ✅ |
| 已收货订单数 | `PurchaseOrder WHERE status='RECEIVED'` | 已收货订单数 | ✅ | ✅ |
| 收货完成率 | `已收货订单数 / 订单总数` | 收货完成率 | ✅ | ✅ |
| 逾期订单数 | `PurchaseOrder WHERE required_date < 今天 AND status!='RECEIVED'` | 逾期未收货订单 | ✅ | ✅ |
| 物料到货率 | `GoodsReceipt.received_qty / PurchaseOrderItem.quantity` | 物料到货完成率 | ✅ | ✅ |

#### 📦 物料指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 物料总数 | `Material` | 物料种类数 | ✅ | ✅ |
| 新增物料数 | `Material.created_at` | 本月/年新增物料 | ✅ | ✅ |
| BOM总数 | `BomHeader` | BOM清单数量 | ✅ | ✅ |
| 缺料上报数 | `ShortageReport` | 缺料上报次数 | ✅ | ✅ |
| 缺料解决数 | `ShortageReport WHERE status='RESOLVED'` | 已解决缺料数 | ✅ | ✅ |
| 缺料解决率 | `已解决缺料数 / 缺料总数` | 缺料解决率 | ✅ | ✅ |
| 缺料平均解决时间 | `resolved_at - report_time` | 缺料平均解决天数 | ✅ | ✅ |

---

### 1.4 工程变更管理(ECN)数据

#### 🔄 变更指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| ECN总数 | `Ecn` | 工程变更通知数量 | ✅ | ✅ |
| 新增ECN数 | `Ecn.created_at` | 本月/年新增ECN | ✅ | ✅ |
| 已批准ECN数 | `Ecn WHERE status='APPROVED'` | 已批准变更数 | ✅ | ✅ |
| ECN批准率 | `已批准ECN数 / ECN总数` | ECN批准率 | ✅ | ✅ |
| ECN成本影响 | `Ecn.cost_impact` | 变更成本影响汇总 | ✅ | ✅ |
| ECN工期影响 | `Ecn.schedule_impact_days` | 变更工期影响汇总 | ✅ | ✅ |
| 平均ECN处理时间 | `approved_at - created_at` | ECN平均处理天数 | ✅ | ✅ |
| ECN按类型分布 | `Ecn.ecn_type` | 各类型ECN数量 | ✅ | ✅ |

---

### 1.5 验收管理模块数据

#### ✅ 验收指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 验收单总数 | `AcceptanceOrder` | 验收单数量 | ✅ | ✅ |
| 新增验收单数 | `AcceptanceOrder.created_at` | 本月/年新增验收单 | ✅ | ✅ |
| 已完成验收数 | `AcceptanceOrder WHERE status='COMPLETED'` | 已完成验收数 | ✅ | ✅ |
| 验收通过率 | `通过验收数 / 验收总数` | 验收通过率 | ✅ | ✅ |
| 验收问题数 | `AcceptanceIssue` | 验收发现问题数 | ✅ | ✅ |
| 已解决验收问题数 | `AcceptanceIssue WHERE status='RESOLVED'` | 已解决问题数 | ✅ | ✅ |
| 验收问题解决率 | `已解决问题数 / 问题总数` | 问题解决率 | ✅ | ✅ |
| FAT验收数 | `AcceptanceOrder WHERE acceptance_type='FAT'` | 出厂验收数量 | ✅ | ✅ |
| SAT验收数 | `AcceptanceOrder WHERE acceptance_type='SAT'` | 现场验收数量 | ✅ | ✅ |

---

### 1.6 问题管理模块数据

#### ⚠️ 问题指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 问题总数 | `Issue` | 问题数量 | ✅ | ✅ |
| 新增问题数 | `Issue.report_date` | 本月/年新增问题 | ✅ | ✅ |
| 已解决问题数 | `Issue WHERE status='RESOLVED'` | 已解决问题数 | ✅ | ✅ |
| 问题解决率 | `已解决问题数 / 问题总数` | 问题解决率 | ✅ | ✅ |
| 平均问题解决时间 | `resolved_at - report_date` | 平均解决天数 | ✅ | ✅ |
| 严重问题数 | `Issue WHERE severity='CRITICAL'` | 严重问题数 | ✅ | ✅ |
| 问题按类型分布 | `Issue.issue_type` | 各类型问题数量 | ✅ | ✅ |
| 问题按分类分布 | `Issue.category` | 各分类问题数量 | ✅ | ✅ |
| 逾期未解决问题数 | `Issue WHERE due_date < 今天 AND status!='RESOLVED'` | 逾期问题数 | ✅ | ✅ |

---

### 1.7 预警与异常管理数据

#### 🚨 预警指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 预警总数 | `AlertRecord` | 预警记录数量 | ✅ | ✅ |
| 新增预警数 | `AlertRecord.alert_time` | 本月/年新增预警 | ✅ | ✅ |
| 已处理预警数 | `AlertRecord WHERE status='HANDLED'` | 已处理预警数 | ✅ | ✅ |
| 预警处理率 | `已处理预警数 / 预警总数` | 预警处理率 | ✅ | ✅ |
| 紧急预警数 | `AlertRecord WHERE alert_level='URGENT'` | 紧急预警数 | ✅ | ✅ |
| 预警按级别分布 | `AlertRecord.alert_level` | 各级别预警数量 | ✅ | ✅ |
| 异常事件数 | `ExceptionEvent` | 异常事件数量 | ✅ | ✅ |
| 已处理异常数 | `ExceptionEvent WHERE status='RESOLVED'` | 已处理异常数 | ✅ | ✅ |

---

### 1.8 工时管理模块数据

#### ⏰ 工时指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 总工时 | `Timesheet.hours` | 所有工时汇总 | ✅ | ✅ |
| 本月工时 | `Timesheet WHERE work_date IN 本月` | 本月工时汇总 | ✅ | ✅ |
| 平均每日工时 | `总工时 / 工作天数` | 平均每日工时 | ✅ | ✅ |
| 加班工时 | `Timesheet WHERE overtime_type!='NORMAL'` | 加班工时汇总 | ✅ | ✅ |
| 加班工时占比 | `加班工时 / 总工时` | 加班工时占比 | ✅ | ✅ |
| 项目工时分布 | `Timesheet.project_id` | 各项目工时分布 | ✅ | ✅ |
| 人员工时排名 | `Timesheet.user_id` | 人员工时排名 | ✅ | ✅ |
| 部门工时分布 | `Timesheet.department_id` | 各部门工时分布 | ✅ | ✅ |

---

### 1.9 绩效管理模块数据

#### 🎯 绩效指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 绩效考核人数 | `PerformanceResult` | 参与考核人数 | ✅ | ✅ |
| 优秀人数 | `PerformanceResult WHERE level='EXCELLENT'` | 优秀等级人数 | ✅ | ✅ |
| 优秀率 | `优秀人数 / 考核人数` | 优秀率 | ✅ | ✅ |
| 平均绩效分数 | `PerformanceResult.total_score` | 平均绩效分数 | ✅ | ✅ |
| 绩效按等级分布 | `PerformanceResult.level` | 各等级人数分布 | ✅ | ✅ |

---

### 1.10 外协管理模块数据

#### 🤝 外协指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 外协订单总数 | `OutsourcingOrder` | 外协订单数量 | ✅ | ✅ |
| 新增外协订单数 | `OutsourcingOrder.order_date` | 本月/年新增订单 | ✅ | ✅ |
| 外协订单金额 | `OutsourcingOrder.total_amount` | 外协订单总金额 | ✅ | ✅ |
| 已交付外协订单数 | `OutsourcingOrder WHERE status='DELIVERED'` | 已交付订单数 | ✅ | ✅ |
| 外协交付率 | `已交付订单数 / 订单总数` | 外协交付率 | ✅ | ✅ |
| 外协供应商数 | `OutsourcingVendor` | 外协供应商数量 | ✅ | ✅ |

---

### 1.11 任务中心模块数据

#### 📋 任务指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 任务总数 | `TaskUnified` | 任务数量 | ✅ | ✅ |
| 新增任务数 | `TaskUnified.created_at` | 本月/年新增任务 | ✅ | ✅ |
| 已完成任务数 | `TaskUnified WHERE status='COMPLETED'` | 已完成任务数 | ✅ | ✅ |
| 任务完成率 | `已完成任务数 / 任务总数` | 任务完成率 | ✅ | ✅ |
| 逾期任务数 | `TaskUnified WHERE due_date < 今天 AND status!='COMPLETED'` | 逾期任务数 | ✅ | ✅ |
| 平均任务完成时间 | `completed_at - created_at` | 平均完成天数 | ✅ | ✅ |

---

### 1.12 管理节律模块数据（已有）

#### 📅 会议指标
| 数据项 | 字段来源 | 说明 | 支持环比 | 支持同比 |
|--------|---------|------|:--------:|:--------:|
| 会议总数 | `StrategicMeeting` | 会议数量 | ✅ | ✅ |
| 已完成会议数 | `StrategicMeeting WHERE status='COMPLETED'` | 已完成会议数 | ✅ | ✅ |
| 会议完成率 | `已完成会议数 / 会议总数` | 会议完成率 | ✅ | ✅ |
| 行动项总数 | `MeetingActionItem` | 行动项数量 | ✅ | ✅ |
| 已完成行动项数 | `MeetingActionItem WHERE status='COMPLETED'` | 已完成行动项数 | ✅ | ✅ |
| 行动项完成率 | `已完成行动项数 / 行动项总数` | 行动项完成率 | ✅ | ✅ |
| 逾期行动项数 | `MeetingActionItem WHERE status='OVERDUE'` | 逾期行动项数 | ✅ | ✅ |

---

## 二、数据分类汇总

### 2.1 按业务维度分类

#### 💼 经营维度
- 销售指标（线索、商机、合同、回款）
- 项目指标（项目数、合同额、成本）
- 财务指标（收入、成本、利润）

#### 📊 运营维度
- 项目进度指标
- 项目质量指标
- 项目成本指标
- 问题解决指标

#### ⚙️ 执行维度
- 任务完成指标
- 工时指标
- 行动项指标
- 会议指标

#### 🎯 质量维度
- 验收指标
- 问题指标
- ECN指标
- 预警指标

---

### 2.2 按数据类型分类

#### 数量型指标
- 项目数、订单数、问题数、会议数等

#### 金额型指标
- 合同额、成本、回款、采购额等

#### 比率型指标
- 完成率、转化率、解决率等

#### 时间型指标
- 平均工期、平均解决时间等

---

## 三、环比和同比数据支持

### 3.1 环比数据（Month-over-Month, MoM）

**定义**：与上月对比

**计算方式**：
- 当前月数据 vs 上月数据
- 变化量 = 当前月 - 上月
- 变化率 = (当前月 - 上月) / 上月 × 100%

**适用指标**：所有月度指标都支持环比

**示例**：
- 本月项目数：10，上月项目数：8，环比：+2 (+25%)
- 本月合同额：1000万，上月合同额：800万，环比：+200万 (+25%)

---

### 3.2 同比数据（Year-over-Year, YoY）

**定义**：与去年同期对比

**计算方式**：
- 当前月数据 vs 去年同月数据
- 变化量 = 当前月 - 去年同月
- 变化率 = (当前月 - 去年同月) / 去年同月 × 100%

**适用指标**：所有月度指标都支持同比

**示例**：
- 本月项目数：10，去年同月：6，同比：+4 (+66.7%)
- 本月合同额：1000万，去年同月：600万，同比：+400万 (+66.7%)

---

### 3.3 年度报告对比

**年度报告支持**：
- 与去年全年对比（同比）
- 按季度对比（Q1/Q2/Q3/Q4）
- 按月度趋势（12个月趋势）

---

## 四、报告配置系统设计

### 4.1 配置模型设计

```python
class MeetingReportConfig(Base, TimestampMixin):
    """会议报告配置表"""
    __tablename__ = 'meeting_report_config'
    
    id = Column(Integer, primary_key=True)
    config_name = Column(String(200), nullable=False, comment='配置名称')
    report_type = Column(String(20), nullable=False, comment='报告类型:ANNUAL/MONTHLY')
    
    # 指标配置(JSON)
    enabled_metrics = Column(JSON, comment='启用的指标列表')
    # 示例结构:
    # [
    #   {
    #     "category": "项目管理",
    #     "metric_code": "project_total",
    #     "metric_name": "项目总数",
    #     "data_source": "Project",
    #     "calculation": "COUNT",
    #     "enabled": true,
    #     "show_in_summary": true,
    #     "show_in_detail": true,
    #     "show_comparison": true,
    #     "comparison_type": ["环比", "同比"],
    #     "display_order": 1
    #   }
    # ]
    
    # 对比配置(JSON)
    comparison_config = Column(JSON, comment='对比配置')
    # 示例结构:
    # {
    #   "enable_mom": true,  # 启用环比
    #   "enable_yoy": true,  # 启用同比
    #   "comparison_periods": ["previous_month", "same_month_last_year"],
    #   "highlight_threshold": {
    #     "increase_threshold": 10,  # 增长超过10%高亮
    #     "decrease_threshold": -10   # 下降超过10%高亮
    #   }
    # }
    
    # 显示配置(JSON)
    display_config = Column(JSON, comment='显示配置')
    # 示例结构:
    # {
    #   "sections": [
    #     {"name": "执行摘要", "enabled": true, "order": 1},
    #     {"name": "项目管理", "enabled": true, "order": 2},
    #     {"name": "销售管理", "enabled": true, "order": 3},
    #     ...
    #   ],
    #   "chart_types": {
    #     "trend_chart": true,
    #     "comparison_chart": true,
    #     "distribution_chart": true
    #   }
    # }
    
    is_default = Column(Boolean, default=False, comment='是否默认配置')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(Integer, ForeignKey('user.id'))
```

---

### 4.2 指标定义配置

```python
class ReportMetricDefinition(Base, TimestampMixin):
    """报告指标定义表"""
    __tablename__ = 'report_metric_definition'
    
    id = Column(Integer, primary_key=True)
    metric_code = Column(String(50), unique=True, nullable=False, comment='指标编码')
    metric_name = Column(String(200), nullable=False, comment='指标名称')
    category = Column(String(50), nullable=False, comment='指标分类')
    
    # 数据源配置
    data_source = Column(String(50), nullable=False, comment='数据源表名')
    data_field = Column(String(100), comment='数据字段')
    filter_conditions = Column(JSON, comment='筛选条件')
    
    # 计算方式
    calculation_type = Column(String(20), nullable=False, comment='计算类型:COUNT/SUM/AVG/MAX/MIN/RATIO')
    calculation_formula = Column(Text, comment='计算公式')
    
    # 对比支持
    support_mom = Column(Boolean, default=True, comment='支持环比')
    support_yoy = Column(Boolean, default=True, comment='支持同比')
    
    # 显示配置
    unit = Column(String(20), comment='单位')
    format_type = Column(String(20), comment='格式类型:NUMBER/PERCENTAGE/CURRENCY')
    decimal_places = Column(Integer, default=2, comment='小数位数')
    
    # 描述
    description = Column(Text, comment='指标说明')
    is_active = Column(Boolean, default=True, comment='是否启用')
```

---

### 4.3 配置管理功能

#### 功能1：指标库管理
- 查看所有可用指标
- 启用/禁用指标
- 自定义指标
- 指标分类管理

#### 功能2：报告模板配置
- 创建报告模板
- 选择包含的指标
- 设置指标显示顺序
- 配置对比方式（环比/同比）

#### 功能3：默认配置设置
- 设置默认月度报告配置
- 设置默认年度报告配置
- 按层级设置不同配置

---

## 五、实施建议

### Phase 1: 数据源梳理（已完成）
- ✅ 列出所有可抽取的数据
- ✅ 分类整理指标
- ✅ 确定环比/同比支持

### Phase 2: 配置系统开发（待实施）
1. 创建配置数据模型
2. 开发配置管理界面
3. 实现指标定义管理
4. 实现报告模板配置

### Phase 3: 报告生成增强（待实施）
1. 根据配置动态生成报告
2. 支持自定义指标计算
3. 支持环比和同比对比
4. 支持图表展示

### Phase 4: 数据集成（待实施）
1. 集成各模块数据查询
2. 实现数据聚合计算
3. 实现对比数据计算
4. 优化查询性能

---

## 六、关键指标推荐（Top 20）

### 6.1 经营类指标（必选）
1. **新签合同额** - 销售核心指标
2. **项目合同总额** - 项目规模指标
3. **回款总额** - 现金流指标
4. **项目实际成本** - 成本控制指标
5. **项目成本偏差率** - 成本管理指标

### 6.2 运营类指标（必选）
6. **项目总数** - 项目规模
7. **进行中项目数** - 项目活跃度
8. **完成项目数** - 项目交付能力
9. **平均项目进度** - 项目执行效率
10. **健康度异常项目数** - 项目风险

### 6.3 质量类指标（推荐）
11. **验收通过率** - 质量指标
12. **问题解决率** - 问题处理能力
13. **ECN批准率** - 变更管理效率
14. **缺料解决率** - 物料管理效率

### 6.4 执行类指标（推荐）
15. **任务完成率** - 执行效率
16. **行动项完成率** - 会议执行效率
17. **会议完成率** - 管理节律执行
18. **总工时** - 工作量指标

### 6.5 趋势类指标（推荐）
19. **新增项目数环比** - 业务增长趋势
20. **合同额同比** - 年度增长趋势

---

## 七、配置界面设计建议

### 7.1 指标选择界面
- 按分类展示指标（项目管理、销售管理、采购管理等）
- 每个指标显示：名称、数据源、计算方式、支持对比
- 支持搜索和筛选
- 支持批量启用/禁用

### 7.2 报告模板配置界面
- 拖拽排序指标
- 设置指标显示位置（摘要/详细）
- 配置对比方式（环比/同比/两者）
- 预览报告效果

### 7.3 对比配置界面
- 启用/禁用环比
- 启用/禁用同比
- 设置高亮阈值
- 设置对比周期

---

## 八、总结

### 8.1 数据源丰富度
- ✅ **30+个业务模块**提供数据
- ✅ **100+个关键指标**可抽取
- ✅ **全面支持环比和同比**

### 8.2 配置灵活性
- ✅ **管理部可自定义**报告内容
- ✅ **按需选择指标**
- ✅ **灵活配置对比方式**

### 8.3 实施优先级
1. **P0**: 核心经营指标（合同、回款、成本）
2. **P1**: 项目运营指标（进度、质量、问题）
3. **P2**: 执行效率指标（任务、工时、行动项）

---

## 九、下一步行动

1. **创建配置数据模型**
2. **开发配置管理界面**
3. **实现动态报告生成**
4. **集成各模块数据查询**
5. **优化报告展示效果**
