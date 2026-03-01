# BEM 战略管理模块设计文档

## 概述

基于华为 BEM（Business Execution Model）战略解码方法论，设计公司级战略管理模块，实现战略从制定到执行的全链路闭环管理。

### 设计背景

BEM 是华为在 BLM（Business Leadership Model）基础上，融合六西格玛质量方法创造的战略解码方法论，通过对战略逐层分解，导出可衡量、可管理的关键任务，保证战略被有效分解到组织与个人。

### 核心价值

- 战略可视化：让全员看到公司战略方向
- 目标可分解：从公司到部门到个人的层层解码
- 执行可跟踪：KPI 数据实时采集与监控
- 结果可衡量：战略健康度评估与同比分析

---

## 一、整体架构

### 1.1 模块定位

BEM 战略管理模块作为系统的**战略中枢**，位于业务模块之上，负责：
- 承载公司战略目标和方向
- 将战略解码为可执行的任务
- 监控战略执行健康度
- 关联现有业务模块数据

### 1.2 核心实体关系

```
Strategy（战略）
    ├── StrategicObjective（战略目标）
    │       ├── CSF（关键成功要素）- 按 BSC 四维度
    │       │       ├── KPI（关键绩效指标）- IPOOC 度量
    │       │       │       └── KPIDataSource（数据源配置）
    │       │       └── AnnualKeyWork（年度重点工作）
    │       │               └── 关联 Project / Task
    │       └── DepartmentObjective（部门目标）
    │               └── TeamObjective（团队目标）
    │                       └── PersonalKPI（个人 KPI）
    └── StrategyReview（战略审视记录）
```

### 1.3 与现有模块的集成点

| 集成模块 | 集成方式 |
|---------|---------|
| 项目管理 | 重点工作 → Project 关联 |
| 绩效管理 | 个人 KPI → 绩效考核 |
| 财务/四算 | 财务维度 CSF ← 成本数据 |
| HR | 学习成长维度 ← 培训/能力数据 |

---

## 二、数据模型设计

### 2.1 核心实体

#### Strategy（战略主表）

```python
class Strategy(Base):
    """战略主表 - 公司级战略规划"""
    id: int
    code: str                    # 战略编码，如 STR-2026
    name: str                    # 战略名称
    vision: str                  # 愿景描述
    slogan: str                  # 战略口号（响亮、易记）
    year: int                    # 战略年度
    start_date: date             # 战略周期开始
    end_date: date               # 战略周期结束
    status: StrategyStatus       # draft/active/archived
    created_by: int              # 创建人
    approved_by: int             # 审批人
    approved_at: datetime        # 审批时间
```

#### CSF（关键成功要素）

```python
class CSF(Base):
    """关键成功要素 - BSC 四维度"""
    id: int
    strategy_id: int             # 关联战略
    dimension: BSCDimension      # financial/customer/internal/learning
    code: str                    # CSF 编码，如 CSF-F-001
    name: str                    # 要素名称
    description: str             # 详细描述
    derivation_method: str       # 导出方法（四维参数法/五大源法/价值链法/无形资产法）
    weight: Decimal              # 权重占比
    owner_dept_id: int           # 责任部门
    owner_user_id: int           # 责任人
    sort_order: int              # 排序
```

#### KPI（关键绩效指标）

```python
class KPI(Base):
    """KPI 指标 - IPOOC 度量"""
    id: int
    csf_id: int                  # 关联 CSF
    code: str                    # KPI 编码
    name: str                    # 指标名称
    ipooc_type: IPOOCType        # input/process/output/outcome
    unit: str                    # 单位（%、万元、天、个）
    target_value: Decimal        # 目标值
    baseline_value: Decimal      # 基线值
    current_value: Decimal       # 当前值
    data_source_type: str        # manual/auto/formula
    data_source_config: JSON     # 数据源配置
    frequency: str               # 更新频率（daily/weekly/monthly/quarterly）
    owner_user_id: int           # 责任人
```

### 2.2 扩展实体

#### AnnualKeyWork（年度重点工作）

```python
class AnnualKeyWork(Base):
    """年度重点工作 - VOC 法导出"""
    id: int
    csf_id: int                  # 关联 CSF
    code: str                    # 工作编码，如 AKW-2026-001
    name: str                    # 工作名称
    description: str             # 工作描述
    voc_source: str              # 声音来源（customer/management/employee/partner）
    pain_point: str              # 识别的痛点/短板
    solution: str                # 解决方案
    target: str                  # 目标描述
    start_date: date
    end_date: date
    owner_dept_id: int           # 责任部门
    owner_user_id: int           # 责任人
    status: WorkStatus           # planning/in_progress/completed/delayed
    progress_percent: int        # 完成进度
    related_project_id: int      # 关联项目（可选）
```

#### DepartmentObjective（部门目标）

```python
class DepartmentObjective(Base):
    """部门目标 - 承接战略"""
    id: int
    strategy_id: int
    department_id: int
    year: int
    objectives: JSON             # 部门级目标列表
    kpis: JSON                   # 部门级 KPI
    status: str
```

#### PersonalKPI（个人 KPI）

```python
class PersonalKPI(Base):
    """个人 KPI - 最终落地"""
    id: int
    employee_id: int
    year: int
    quarter: int                 # 季度
    source_type: str             # csf_kpi / dept_objective / annual_work
    source_id: int               # 来源 ID
    kpi_name: str
    target_value: Decimal
    actual_value: Decimal
    weight: Decimal
    self_rating: int             # 自评分
    manager_rating: int          # 主管评分
```

#### StrategyReview（战略审视）

```python
class StrategyReview(Base):
    """战略审视记录"""
    id: int
    strategy_id: int
    review_type: str             # health_check / execution_review
    review_date: date
    reviewer_id: int
    health_score: int            # 健康度评分 (0-100)
    findings: JSON               # 发现的问题
    recommendations: JSON        # 改进建议
    decisions: JSON              # 关键决策
    next_review_date: date
```

---

## 三、功能模块设计

### 3.1 功能架构

```
BEM 战略管理模块
├── 1. 战略规划
│   ├── 战略制定与发布
│   ├── 战略地图可视化
│   └── 战略共识（沟通/宣贯记录）
│
├── 2. 战略解码
│   ├── CSF 管理（四维度）
│   ├── KPI 指标库（IPOOC）
│   ├── 年度重点工作（VOC）
│   └── 目标分解（部门→团队→个人）
│
├── 3. 战略执行
│   ├── KPI 数据采集与更新
│   ├── 重点工作进度跟踪
│   └── 执行预警与提醒
│
├── 4. 战略审视
│   ├── 战略健康度仪表板
│   ├── 执行进度看板
│   └── 审视会议管理
│
└── 5. 全员视图
    ├── 我的战略关联（个人看板）
    ├── 部门战略看板
    └── 战略穿透查询
```

### 3.2 核心页面清单

| 页面 | 主要用户 | 核心功能 |
|------|---------|---------|
| 战略总览 | 高管 | 查看当前战略、健康度、关键指标 |
| 战略地图 | 全员 | BSC 四维度可视化、CSF/KPI 穿透 |
| CSF 管理 | 战略部 | 新增/编辑 CSF、配置导出方法 |
| KPI 管理 | 战略部 | 指标定义、数据源配置、IPOOC 分类 |
| 重点工作 | 部门负责人 | 工作创建、进度更新、项目关联 |
| 目标分解 | 各级管理者 | 逐层分解目标、分配责任人 |
| 我的战略 | 全员 | 查看个人承担的 KPI 和任务 |
| 战略审视 | 高管/战略部 | 健康度评估、问题记录、决策跟踪 |

---

## 四、API 设计

### 4.1 API 端点规划

```
/api/v1/strategy/
├── strategies/                    # 战略管理
│   ├── GET    /                   # 战略列表
│   ├── POST   /                   # 创建战略
│   ├── GET    /{id}               # 战略详情
│   ├── PUT    /{id}               # 更新战略
│   ├── POST   /{id}/publish       # 发布战略
│   └── GET    /{id}/map           # 获取战略地图数据
│
├── csf/                           # 关键成功要素
│   ├── GET    /                   # CSF 列表（按维度筛选）
│   ├── POST   /                   # 创建 CSF
│   ├── PUT    /{id}               # 更新 CSF
│   └── GET    /by-dimension       # 按 BSC 维度分组
│
├── kpi/                           # KPI 指标
│   ├── GET    /                   # KPI 列表
│   ├── POST   /                   # 创建 KPI
│   ├── PUT    /{id}               # 更新 KPI
│   ├── POST   /{id}/collect       # 采集数据
│   ├── PUT    /{id}/value         # 更新当前值
│   └── GET    /{id}/history       # 历史数据
│
├── annual-works/                  # 年度重点工作
│   ├── GET    /                   # 工作列表
│   ├── POST   /                   # 创建工作
│   ├── PUT    /{id}               # 更新工作
│   ├── PUT    /{id}/progress      # 更新进度
│   └── POST   /{id}/link-project  # 关联项目
│
├── decomposition/                 # 目标分解
│   ├── GET    /department/{id}    # 部门目标
│   ├── POST   /department/        # 创建部门目标
│   ├── GET    /personal/{id}      # 个人 KPI
│   └── POST   /personal/          # 分配个人 KPI
│
├── review/                        # 战略审视
│   ├── GET    /                   # 审视记录列表
│   ├── POST   /                   # 创建审视记录
│   └── GET    /health-score       # 健康度评分
│
├── comparison/                    # 同比分析
│   ├── GET    /{current}/{previous}  # 年度对比
│   └── GET    /yoy-report/{year}     # 同比报告
│
└── dashboard/                     # 仪表板
    ├── GET    /overview           # 战略总览
    ├── GET    /my-strategy        # 我的战略关联
    └── GET    /execution-status   # 执行状态看板
```

### 4.2 数据源集成配置示例

```python
# KPI 数据源配置示例
{
    "kpi_id": 1,
    "data_source_type": "auto",
    "config": {
        "source_module": "project_cost",
        "query_type": "aggregate",
        "metric": "total_profit_margin",
        "filters": {"year": 2026},
        "aggregation": "avg"
    }
}
```

---

## 五、前端页面设计

### 5.1 战略地图页面

```
┌─────────────────────────────────────────────────────────────────┐
│  战略地图 - 2026年度                            [编辑] [导出]    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 愿景：成为华南区领先的非标自动化测试设备供应商            │   │
│  │ 口号：技术领先、交付卓越、客户成功                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─ 财务维度 ──────────────────────────────────────────────┐   │
│  │ [营收增长30%]  [毛利率≥35%]  [现金流健康]                │   │
│  │   ● 85%          ○ 72%         ● 90%                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↑                                     │
│  ┌─ 客户维度 ──────────────────────────────────────────────┐   │
│  │ [客户满意度≥90]  [市占率提升]  [复购率≥60%]             │   │
│  │   ○ 78%           ● 88%         ● 92%                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↑                                     │
│  ┌─ 内部运营维度 ──────────────────────────────────────────┐   │
│  │ [交付周期缩短20%]  [一次通过率≥95%]  [成本降低10%]      │   │
│  │   ○ 65%             ● 96%            ○ 70%              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↑                                     │
│  ┌─ 学习成长维度 ──────────────────────────────────────────┐   │
│  │ [核心人才保留≥90%]  [人均培训≥40h]  [创新项目≥5个]     │   │
│  │   ● 92%              ○ 75%           ● 100%             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  图例：● 达标(≥80%)  ○ 预警(60-80%)  ◌ 落后(<60%)          │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 我的战略页面

```
┌─────────────────────────────────────────────────────────────────┐
│  我的战略关联                                    张三 / 研发部   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  战略穿透路径：                                                  │
│  公司战略 → 研发部目标 → 研发一组目标 → 我的 KPI               │
│                                                                 │
│  ┌─ 我承担的 KPI ─────────────────────────────────────────┐    │
│  │ 指标名称          目标值    当前值    完成率    权重    │    │
│  │ ─────────────────────────────────────────────────────  │    │
│  │ 项目交付准时率     95%      92%      96.8%    30%     │    │
│  │ 设计一次通过率     90%      88%      97.8%    25%     │    │
│  │ 技术文档完整率     100%     95%      95.0%    20%     │    │
│  │ 创新提案数量       3个      2个      66.7%    15%     │    │
│  │ 培训学时          40h      32h      80.0%    10%     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ 我参与的重点工作 ─────────────────────────────────────┐    │
│  │ • [进行中] 新一代 ICT 测试平台研发 - 负责架构设计        │    │
│  │ • [进行中] 交付流程优化项目 - 参与评审                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 战略同比分析页面

```
┌─────────────────────────────────────────────────────────────────┐
│  战略同比分析                    2025 vs 2026    [导出报告]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ 总体健康度对比 ─────────────────────────────────────────┐  │
│  │   2025年: ████████████████░░░░ 78%                       │  │
│  │   2026年: ██████████████████░░ 85%  ↑ +7%                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ BSC 四维度同比 ─────────────────────────────────────────┐  │
│  │   维度        2025    2026    变化     趋势               │  │
│  │   ──────────────────────────────────────────────         │  │
│  │   财务        75%     82%    +7%      ↑ 提升             │  │
│  │   客户        80%     78%    -2%      ↓ 下降             │  │
│  │   内部运营    72%     88%    +16%     ↑↑ 显著提升        │  │
│  │   学习成长    85%     92%    +7%      ↑ 提升             │  │
│  └─────────────────���─────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ 战略目标达成对比 ─────────────────────────────────────┐    │
│  │   指标                2025目标  2025实际  2026目标  预测   │  │
│  │   ─────────────────────────────────────────────────────  │  │
│  │   年营收(万元)         5000     4800     6500     进行中  │  │
│  │   新客户数量           20       18       25       进行中  │  │
│  │   项目交付周期(天)     90       95       75       进行中  │  │
│  │   员工满意度           85%      82%      90%      进行中  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 六、模块集成设计

### 6.1 集成架构图

```
                    ┌─────────────────────┐
                    │   BEM 战略管理模块   │
                    │   (战略中枢)         │
                    └──────────┬──────────┘
                               │
        ┌──────────┬───────────┼───────────┬──────────┐
        ↓          ↓           ↓           ↓          ↓
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │项目管理 │ │绩效管理 │ │财务/四算│ │  HR    │ │客户管理 │
   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
        │          │           │           │          │
   重点工作    个人KPI      财务维度    学习成长    客户维度
   关联项目    绩效考核     CSF数据    CSF数据     CSF数据
```

### 6.2 与项目管理集成

```python
class AnnualKeyWorkProjectLink(Base):
    """年度重点工作与项目关联"""
    annual_work_id: int
    project_id: int
    link_type: str               # main / support
    contribution_weight: Decimal
```

### 6.3 与绩效管理集成

```python
class PerformanceStrategyLink(Base):
    """绩效考核与战略 KPI 关联"""
    performance_id: int
    personal_kpi_id: int
    weight_in_performance: Decimal
```

### 6.4 财务/HR 数据源配置

```python
FINANCIAL_KPI_SOURCES = {
    "revenue": {"module": "project_cost", "field": "contract_amount", "aggregation": "sum"},
    "profit_margin": {"module": "project_cost", "field": "profit_margin", "aggregation": "avg"},
    "cash_flow": {"module": "payment", "field": "received_amount - paid_amount", "aggregation": "sum"}
}

HR_KPI_SOURCES = {
    "talent_retention": {"module": "employee", "calculation": "留存人数 / 年初人数"},
    "training_hours": {"module": "training_record", "field": "hours", "aggregation": "avg_per_person"}
}
```

---

## 七、战略例行管理

### 7.1 年度日历

```
Q4 (10-12月)               Q1 (1-3月)
• 下年度战略规划            • 战略宣贯与共识
• CSF/KPI 目标制定         • 部门目标分解
• 年度重点工作规划          • 个人 KPI 签署
• 预算编制                  • Q1 执行启动

Q3 (7-9月)                 Q2 (4-6月)
• 战略中期审视              • Q1 复盘
• 目标调整（如需要）        • Q2 执行推进
• 下半年重点调整            • 半年度预警检查
```

### 7.2 例行工作事项

| 周期 | 工作事项 | 责任角色 | 产出物 |
|------|---------|---------|--------|
| **年度** | | | |
| 11月 | 下年度战略规划 | 高管/战略部 | 战略规划书 |
| 12月 | CSF/KPI 目标制定 | 战略部 | 指标目标表 |
| 1月 | 战略宣贯共识 | 全员 | 共识签署 |
| 12月 | 年度战略复盘 | 高管 | 复盘报告 |
| **季度** | | | |
| 季末 | 季度经营分析会 | 高管/部门负责人 | 经营分析报告 |
| 季末 | KPI 达成评估 | 战略部 | 季度 KPI 报告 |
| **月度** | | | |
| 月初 | KPI 数据采集 | 各数据责任人 | KPI 数据更新 |
| 月中 | 重点工作进度检查 | 部门负责人 | 进度报告 |
| **周度** | | | |
| 每周 | 重点工作周会 | 项目负责人 | 周报 |

### 7.3 战略日历事件模型

```python
class StrategyCalendarEvent(Base):
    """战略日历事件"""
    id: int
    strategy_id: int
    event_type: StrategyEventType
    frequency: str               # yearly/quarterly/monthly/weekly
    scheduled_date: date
    actual_date: date
    status: str                  # pending/completed/skipped
    participants: JSON
    outputs: JSON
    meeting_minutes_id: int
```

---

## 八、技术实现要点

### 8.1 目录结构

```
app/
├── api/v1/endpoints/
│   └── strategy/
│       ├── __init__.py
│       ├── strategies.py
│       ├── csf.py
│       ├── kpi.py
│       ├── annual_works.py
│       ├── decomposition.py
│       ├── review.py
│       └── dashboard.py
│
├── models/
│   └── strategy.py
│
├── schemas/
│   └── strategy/
│       ├── strategy.py
│       ├── csf.py
│       ├── kpi.py
│       └── annual_work.py
│
├── services/
│   └── strategy/
│       ├── strategy_service.py
│       ├── kpi_collector.py
│       ├── health_calculator.py
│       └── decomposition_service.py
│
frontend/src/
├── pages/
│   └── Strategy/
│       ├── StrategyOverview.jsx
│       ├── StrategyMap.jsx
│       ├── CSFManagement.jsx
│       ├── KPIManagement.jsx
│       ├── AnnualWorks.jsx
│       ├── MyStrategy.jsx
│       └── StrategyReview.jsx
```

### 8.2 关键技术点

| 技术点 | 实现方案 |
|--------|---------|
| 战略地图可视化 | React + D3.js / ECharts 树图 |
| KPI 数据采集 | 定时任务 + 事件驱动混合模式 |
| 公式计算引擎 | 使用 `simpleeval` 安全表达式引擎 |
| 目标分解树 | 递归查询 + 前端树形组件 |
| 健康度算法 | 加权平均 + 阈值判定 |
| 权限控制 | 基于角色 + 数据范围（只看本部门） |

### 8.3 枚举定义

```python
class BSCDimension(str, Enum):
    """平衡计分卡四维度"""
    FINANCIAL = "financial"
    CUSTOMER = "customer"
    INTERNAL = "internal"
    LEARNING = "learning"

class IPOOCType(str, Enum):
    """IPOOC 指标类型"""
    INPUT = "input"
    PROCESS = "process"
    OUTPUT = "output"
    OUTCOME = "outcome"

class VOCSource(str, Enum):
    """VOC 声音来源"""
    CUSTOMER = "customer"
    MANAGEMENT = "management"
    EMPLOYEE = "employee"
    PARTNER = "partner"

class StrategyEventType(str, Enum):
    """战略事件类型"""
    ANNUAL_PLANNING = "annual_planning"
    ANNUAL_REVIEW = "annual_review"
    BUDGET_PLANNING = "budget_planning"
    QUARTERLY_REVIEW = "quarterly_review"
    QUARTERLY_ADJUSTMENT = "quarterly_adjustment"
    MONTHLY_TRACKING = "monthly_tracking"
    KPI_COLLECTION = "kpi_collection"
    WEEKLY_STANDUP = "weekly_standup"
```

---

## 九、设计决策记录

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 架构模式 | 战略驱动型 | 符合 BEM 自上而下解码理念 |
| 应用层级 | 公司战略层 | 聚焦公司级战略管理 |
| 服务角色 | 全员可见 | 实现"上下同欲" |
| 交付方式 | 一次性完整交付 | 功能完整性 |
| 集成范围 | 全面集成 | 打通项目/绩效/财务/HR |
| 数据来源 | 灵活配置 | 手动/自动/公式可选 |

---

## 附录：参考资料

- 华为 BLM/BEM 战略解码方法论
- 平衡计分卡 (BSC) - 卡普兰
- 六西格玛质量管理方法
- IPOOC 流程度量框架
- VOC (Voice of Customer) 方法
