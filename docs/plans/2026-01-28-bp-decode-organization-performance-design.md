# BP解码组织绩效设计 - DSTE流程与BEM完善

## 概述

基于华为BP解码组织绩效方法论，完善现有BEM战略管理模块，将"静态结构"升级为"动态流程"，实现从战略到执行的严密闭环管理。

### 设计背景

华为的BP解码组织绩效是一套高度体系化、刚性落地的流程。它以DSTE为框架，以BEM为核心方法论，借助平衡计分卡等工具，通过三次解码将宏观战略转化为每一个组织和个人清晰可衡量的年度作战目标与责任。

### 现有模块差距分析

| 华为BP解码体系 | 现有BEM模块 | 状态 |
|--------------|------------|------|
| Strategy（战略） | ✓ Strategy | 已有 |
| CSF（关键成功要素）| ✓ CSF（BSC四维度）| 已有 |
| KPI（指标） | ✓ KPI（IPOOC度量）| 已有（需增强三级目标值）|
| 年度重点工作 | ✓ AnnualKeyWork | 已有 |
| 部门目标分解 | ✓ DepartmentObjective | 已有 |
| 个人KPI | ✓ PersonalKPI | 已有（较简单）|
| **DSTE日历化流程** | ✗ | **本次新增** |
| **责任中心划分** | ✗ | **本次新增** |
| **三级目标值** | ✗ | **本次新增** |
| **PBC签署流程** | ✗ | **本次新增** |
| **经营分析会** | ✗ | **本次新增** |

### 核心价值

- **流程刚性化**：将BP解码变成有时间节点、有任务提醒的年度循环
- **目标精细化**：三级目标值（底线/达标/挑战）让考核更科学
- **责任明确化**：责任中心机制让不同部门的KPI导向清晰
- **承诺正式化**：PBC签署让绩效承诺有仪式感和约束力
- **监控闭环化**：经营分析会实现议题→决议→跟踪的完整闭环

---

## 一、整体架构

### 1.1 模块定位

```
BEM 战略管理模块
├── [现有] 战略规划
│   └── Strategy → CSF → KPI → AnnualKeyWork
│
├── [现有] 目标分解
│   └── DepartmentObjective → PersonalKPI
│
├── [现有] 横向协同
│   └── 铁三角协同绩效
│
└── [新增] BP解码体系
    ├── 1. DSTE日历化流程
    │   └── 财年配置 → BP周期 → 阶段任务 → 节点提醒
    │
    ├── 2. 责任中心机制
    │   └── 部门责任中心类型 → 差异化KPI模板
    │
    ├── 3. PBC签署流程
    │   └── KPI分配 → 员工承诺 → 主管确认 → 附件上传
    │
    └── 4. 经营分析会
        └── 议题生成 → 会议记录 → 决议跟踪 → 闭环回顾
```

### 1.2 设计原则

1. **财年可配置** - 支持自然年度、4月制等不同财年周期
2. **流程刚性化** - BP解码有明确的阶段、任务和截止日期
3. **分层管理** - 高管PBC与普通员工PBC流程有差异
4. **闭环跟踪** - 经营分析会的决议必须跟踪到完成

---

## 二、DSTE日历化流程

### 2.1 核心概念

DSTE（Develop Strategy To Execution）是从战略到执行的年度循环：

```
┌─ 财年周期（可配置）──────────────────────────────────────────┐
│                                                              │
│  SP输入期        BP制定期         执行期         复盘期      │
│  (Y-1.9~11)     (Y-1.12~Y.1)    (Y.2~Y.11)    (Y.12)       │
���                                                              │
│  ·SP战略输入     ·战略解码        ·月度经营分析   ·年度复盘   │
│  ·机会点识别     ·KPI制定         ·季度BP审视    ·绩效评价   │
│  ·预算指引       ·PBC签署         ·执行监控      ·奖金结算   │
│                  ·BP述职                                     │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 数据模型

```python
class FiscalYearConfig(Base):
    """财年配置"""
    __tablename__ = "fiscal_year_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, comment="财年编码，如 FY2026")
    name = Column(String(100), nullable=False, comment="财年名称，如 2026财年")

    # 财年周期
    start_date = Column(Date, nullable=False, comment="财年开始日期")
    end_date = Column(Date, nullable=False, comment="财年结束日期")

    # 状态
    is_current = Column(Boolean, default=False, comment="是否当前财年")
    status = Column(String(20), default="PLANNING", comment="状态：PLANNING/ACTIVE/CLOSED")

    # DSTE阶段时间配置
    sp_input_start = Column(Date, comment="SP输入期开始")
    sp_input_end = Column(Date, comment="SP输入期结束")
    bp_planning_start = Column(Date, comment="BP制定期开始")
    bp_planning_end = Column(Date, comment="BP制定期结束")
    pbc_deadline = Column(Date, comment="PBC签署截止日")
    execution_start = Column(Date, comment="执行期开始")
    annual_review_start = Column(Date, comment="年度复盘开始")
    annual_review_end = Column(Date, comment="年度复盘结束")

    # 关系
    phases = relationship("BPPhase", back_populates="fiscal_year", lazy="dynamic")

    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class BPPhase(Base):
    """BP周期阶段"""
    __tablename__ = "bp_phases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_year_configs.id"), nullable=False)

    # 阶段信息
    phase_type = Column(String(30), nullable=False, comment="阶段类型：SP_INPUT/BP_PLANNING/EXECUTION/REVIEW")
    name = Column(String(100), nullable=False, comment="阶段名称")
    description = Column(Text, comment="阶段说明")

    # 时间
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # 状态
    status = Column(String(20), default="UPCOMING", comment="状态：UPCOMING/IN_PROGRESS/COMPLETED")
    completed_at = Column(DateTime, comment="完成时间")

    # 关系
    fiscal_year = relationship("FiscalYearConfig", back_populates="phases")
    tasks = relationship("BPTask", back_populates="phase", lazy="dynamic")


class BPTask(Base):
    """BP阶段任务"""
    __tablename__ = "bp_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_id = Column(Integer, ForeignKey("bp_phases.id"), nullable=False)

    # 任务信息
    task_type = Column(String(50), nullable=False, comment="任务类型")
    name = Column(String(200), nullable=False, comment="任务名称")
    description = Column(Text, comment="任务描述")

    # 责任
    responsible_role = Column(String(50), comment="责任角色：STRATEGY_DEPT/DEPT_HEAD/EMPLOYEE/HR/FINANCE")
    responsible_dept_id = Column(Integer, ForeignKey("departments.id"), comment="责任部门")
    responsible_user_id = Column(Integer, ForeignKey("users.id"), comment="责任人")

    # 时间
    deadline = Column(Date, nullable=False, comment="截止日期")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态：PENDING/IN_PROGRESS/COMPLETED/OVERDUE")
    completed_at = Column(DateTime)
    completed_by = Column(Integer, ForeignKey("users.id"))

    # 产出物
    deliverable = Column(String(200), comment="产出物描述")
    deliverable_link = Column(String(500), comment="产出物链接")

    # 排序
    sort_order = Column(Integer, default=0)

    # 关系
    phase = relationship("BPPhase", back_populates="tasks")
```

### 2.3 BP阶段任务类型

| 阶段 | 任务类型 | 责任角色 | 产出物 |
|------|---------|---------|--------|
| **SP输入期** | | | |
| | SP_REVIEW | 战略部 | SP文档确认 |
| | OPPORTUNITY_IDENTIFY | 业务部门 | 机会点清单 |
| | BUDGET_GUIDELINE | 财务部 | 预算指引 |
| **BP制定期** | | | |
| | STRATEGY_DECODE | 战略部 | CSF/KPI方案 |
| | DEPT_KPI_DRAFT | 部门负责人 | 部门KPI草案 |
| | BP_PRESENTATION | 部门负责人 | BP述职 |
| | PBC_ASSIGN | 各级主管 | PBC分配 |
| | PBC_SIGN | 全员 | PBC签署 |
| **执行期** | | | |
| | MONTHLY_REVIEW | 管理层 | 月度经营分析 |
| | QUARTERLY_REVIEW | 管理层 | 季度BP审视 |
| | KPI_COLLECTION | 数据责任人 | KPI数据更新 |
| **复盘期** | | | |
| | ANNUAL_REVIEW | 战略部 | 年度复盘报告 |
| | PERFORMANCE_EVAL | HR | 绩效评价 |
| | BONUS_CALCULATION | HR/财务 | 奖金核算 |

### 2.4 枚举定义

```python
class BPPhaseType(str, Enum):
    """BP阶段类型"""
    SP_INPUT = "SP_INPUT"           # SP输入期
    BP_PLANNING = "BP_PLANNING"     # BP制定期
    EXECUTION = "EXECUTION"         # 执行期
    REVIEW = "REVIEW"               # 复盘期


class BPTaskType(str, Enum):
    """BP任务类型"""
    # SP输入期
    SP_REVIEW = "SP_REVIEW"
    OPPORTUNITY_IDENTIFY = "OPPORTUNITY_IDENTIFY"
    BUDGET_GUIDELINE = "BUDGET_GUIDELINE"
    # BP制定期
    STRATEGY_DECODE = "STRATEGY_DECODE"
    DEPT_KPI_DRAFT = "DEPT_KPI_DRAFT"
    BP_PRESENTATION = "BP_PRESENTATION"
    PBC_ASSIGN = "PBC_ASSIGN"
    PBC_SIGN = "PBC_SIGN"
    # 执行期
    MONTHLY_REVIEW = "MONTHLY_REVIEW"
    QUARTERLY_REVIEW = "QUARTERLY_REVIEW"
    KPI_COLLECTION = "KPI_COLLECTION"
    # 复盘期
    ANNUAL_REVIEW = "ANNUAL_REVIEW"
    PERFORMANCE_EVAL = "PERFORMANCE_EVAL"
    BONUS_CALCULATION = "BONUS_CALCULATION"


class BPTaskStatus(str, Enum):
    """BP任务状态"""
    PENDING = "PENDING"             # 待开始
    IN_PROGRESS = "IN_PROGRESS"     # 进行中
    COMPLETED = "COMPLETED"         # 已完成
    OVERDUE = "OVERDUE"             # 已逾期
```

---

## 三、责任中心机制

### 3.1 责任中心类型

| 责任中心 | 典型部门 | KPI导向 |
|---------|---------|--------|
| **利润中心(PROFIT)** | 区域销售、产品线、事业部 | 收入、利润、回款 |
| **收入中心(REVENUE)** | 销售部 | 订单、收入（不背成本）|
| **成本中心(COST)** | 生产部、研发部 | 成本控制、效率、质量 |
| **费用中心(EXPENSE)** | 行政、HR、财务、IT | 预算执行、服务质量 |

### 3.2 数据模型

```python
class ResponsibilityCenter(str, Enum):
    """责任中心类型"""
    PROFIT = "profit"         # 利润中心
    REVENUE = "revenue"       # 收入中心
    COST = "cost"             # 成本中心
    EXPENSE = "expense"       # 费用中心


class DepartmentResponsibility(Base):
    """部门责任中心配置"""
    __tablename__ = "department_responsibilities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_year_configs.id"), nullable=False)

    # 责任中心类型
    center_type = Column(String(20), nullable=False, comment="责任中心类型")

    # 考核导向
    kpi_orientation = Column(Text, comment="KPI导向说明")

    # 预算权限
    budget_authority = Column(String(50), comment="预算权限级别")
    budget_amount = Column(Numeric(14, 2), comment="预算额度")

    # 状态
    is_active = Column(Boolean, default=True)

    # 关系
    department = relationship("Department")
    fiscal_year = relationship("FiscalYearConfig")

    __table_args__ = (
        Index("idx_dept_resp_unique", "department_id", "fiscal_year_id", unique=True),
    )


class ResponsibilityCenterKPITemplate(Base):
    """责任中心KPI模板"""
    __tablename__ = "responsibility_center_kpi_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 责任中心类型
    center_type = Column(String(20), nullable=False, comment="责任中心类型")

    # KPI模板信息
    kpi_code = Column(String(50), nullable=False, comment="KPI编码")
    kpi_name = Column(String(200), nullable=False, comment="KPI名称")
    kpi_category = Column(String(50), comment="类别：FINANCIAL/EFFICIENCY/QUALITY/SERVICE")

    # 指标定义
    unit = Column(String(20), comment="单位")
    direction = Column(String(10), default="UP", comment="方向：UP/DOWN")
    description = Column(Text, comment="指标说明")
    calculation_method = Column(Text, comment="计算方法")

    # 模板配置
    is_mandatory = Column(Boolean, default=False, comment="是否必选")
    default_weight = Column(Numeric(5, 2), comment="默认权重")

    # 状态
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
```

### 3.3 不同责任中心的KPI模板示例

| 责任中心 | 必选KPI | 可选KPI |
|---------|--------|--------|
| **利润中心** | 营收达成率、利润达成率、回款率 | 新客户开发、市占率、客户满意度 |
| **收入中心** | 订单额、收入达成率 | 客户满意度、新客户数、复购率 |
| **成本中心** | 成本节约率、生产效率、质量合格率 | 交付准时率、库存周转率、一次通过率 |
| **费用中心** | 预算执行率、服务满意度 | 响应及时率、流程合规率、员工满意度 |

---

## 四、三级目标值与KPI增强

### 4.1 三级目标值概念

| 目标档位 | 含义 | 绩效等级 |
|---------|------|---------|
| **底线值(Baseline)** | 不可接受线，低于此为不合格 | D档 |
| **达标值(Target)** | 合格线，正常绩效水平 | B档 |
| **挑战值(Stretch)** | 卓越线，超预期表现 | A档 |

### 4.2 KPI模型增强

```python
class KPI(Base):
    """KPI 指标 - 增强三级目标值"""
    # ... 现有字段 ...

    # 三级目标值
    target_value = Column(Numeric(14, 2), comment="达标值（目标值）")
    baseline_value = Column(Numeric(14, 2), comment="底线值")
    stretch_value = Column(Numeric(14, 2), comment="挑战值")

    # 目标设定依据
    target_rationale = Column(Text, comment="目标设定依据/说明")

    # 历史参考
    last_year_actual = Column(Numeric(14, 2), comment="去年实际值")
    industry_benchmark = Column(Numeric(14, 2), comment="行业标杆值")
```

### 4.3 得分计算逻辑

```python
def calculate_kpi_score(actual: float, baseline: float,
                        target: float, stretch: float,
                        direction: str = "UP") -> dict:
    """
    基于三级目标值计算KPI得分

    Returns:
        {
            "score": 85,           # 百分制得分
            "grade": "B+",         # 等级
            "achievement": "达标"   # 达成状态
        }
    """
    if direction == "DOWN":
        # 越低越好的指标，反转计算
        actual, baseline, target, stretch = -actual, -baseline, -target, -stretch

    if actual < baseline:
        # 低于底线：0-60分
        score = max(0, 60 * (actual / baseline)) if baseline > 0 else 0
        grade, achievement = "D", "不合格"
    elif actual < target:
        # 底线到达标：60-80分
        score = 60 + 20 * (actual - baseline) / (target - baseline)
        grade, achievement = "C", "待改进"
    elif actual < stretch:
        # 达标到挑战：80-100分
        score = 80 + 20 * (actual - target) / (stretch - target)
        grade = "B+" if score >= 90 else "B"
        achievement = "达标"
    else:
        # 超越挑战：100-120分（封顶120）
        score = min(120, 100 + 20 * (actual - stretch) / stretch)
        grade, achievement = "A", "卓越"

    return {"score": round(score, 1), "grade": grade, "achievement": achievement}
```

### 4.4 目标值设定建议服务

```python
class KPITargetSuggestionService:
    """KPI目标值建议服务"""

    def suggest_targets(self, kpi_id: int) -> dict:
        """根据历史数据和行业标杆建议三级目标值"""
        kpi = self.get_kpi(kpi_id)

        last_year = kpi.last_year_actual
        history_avg = self.get_history_average(kpi_id, years=3)
        benchmark = kpi.industry_benchmark

        if kpi.direction == "UP":
            baseline = last_year * 0.95      # 底线：去年的95%
            target = max(last_year * 1.05, history_avg * 1.03)
            stretch = max(target * 1.15, benchmark) if benchmark else target * 1.15
        else:
            baseline = last_year * 1.05
            target = last_year * 0.95
            stretch = min(target * 0.85, benchmark) if benchmark else target * 0.85

        return {
            "baseline": round(baseline, 2),
            "target": round(target, 2),
            "stretch": round(stretch, 2),
            "reference": {
                "last_year": last_year,
                "history_avg": history_avg,
                "benchmark": benchmark
            }
        }
```

---

## 五、PBC签署流程

### 5.1 PBC概念

PBC = Personal Business Commitment（个人绩效承诺书），是员工与主管之间对年度绩效目标的正式承诺。

### 5.2 数据模型

```python
class PBCLevel(str, Enum):
    """PBC层级"""
    EXECUTIVE = "EXECUTIVE"     # 高管级
    MANAGER = "MANAGER"         # 中层管理
    STAFF = "STAFF"             # 普通员工


class PBCStatus(str, Enum):
    """PBC状态"""
    DRAFT = "DRAFT"                     # 草稿
    PENDING_EMPLOYEE = "PENDING_EMPLOYEE"   # 待员工确认
    PENDING_MANAGER = "PENDING_MANAGER"     # 待主管确认
    PENDING_APPROVAL = "PENDING_APPROVAL"   # 待审批（仅高管）
    SIGNED = "SIGNED"                   # 已签署
    REVISED = "REVISED"                 # 已修订


class PBC(Base):
    """个人绩效承诺书"""
    __tablename__ = "pbcs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="承诺书编号")

    # 关联
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_year_configs.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))

    # 层级
    level = Column(String(20), nullable=False, comment="层级：EXECUTIVE/MANAGER/STAFF")

    # 内容（JSON格式）
    kpi_items = Column(Text, comment="KPI条目列表")
    # 格式: [
    #   {
    #     "personal_kpi_id": 1,
    #     "name": "项目交付准时率",
    #     "weight": 30,
    #     "baseline": 85,
    #     "target": 92,
    #     "stretch": 98,
    #     "unit": "%"
    #   }
    # ]

    key_tasks = Column(Text, comment="关键任务列表")
    # 格式: [
    #   {"task": "完成XX项目", "deadline": "2026-Q2", "weight": 20}
    # ]

    development_plan = Column(Text, comment="个人发展计划")

    # 签署流程
    status = Column(String(30), default="DRAFT")

    # 员工签署
    employee_signed_at = Column(DateTime)
    employee_signature = Column(String(200), comment="电子签名标识")
    employee_remarks = Column(Text, comment="员工备注")

    # 主管确认
    manager_id = Column(Integer, ForeignKey("users.id"))
    manager_signed_at = Column(DateTime)
    manager_signature = Column(String(200))
    manager_remarks = Column(Text)

    # 高管审批（仅EXECUTIVE级别）
    approver_id = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    approval_remarks = Column(Text)

    # 版本控制
    version = Column(Integer, default=1)
    parent_id = Column(Integer, ForeignKey("pbcs.id"), comment="修订前版本")
    revision_reason = Column(Text, comment="修订原因")

    # 时间戳
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # 关系
    employee = relationship("User", foreign_keys=[employee_id])
    manager = relationship("User", foreign_keys=[manager_id])
    approver = relationship("User", foreign_keys=[approver_id])
    fiscal_year = relationship("FiscalYearConfig")
    attachments = relationship("PBCAttachment", back_populates="pbc", lazy="dynamic")


class PBCAttachment(Base):
    """PBC附件"""
    __tablename__ = "pbc_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pbc_id = Column(Integer, ForeignKey("pbcs.id"), nullable=False)

    # 文件信息
    file_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), comment="文件类型：PDF/IMAGE")
    file_size = Column(Integer, comment="文件大小(bytes)")

    # 上传信息
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime)

    # 关系
    pbc = relationship("PBC", back_populates="attachments")
    uploader = relationship("User")
```

### 5.3 签署流程

**员工级PBC流程：**
```
主管分配KPI → 员工确认 → 员工签署 → 主管确认 → 生效
   DRAFT      PENDING_   PENDING_    SIGNED
             EMPLOYEE    MANAGER
```

**高管级PBC流程：**
```
战略部拟定 → 高管确认 → CEO审批 → 高管签署 → 生效
   DRAFT     PENDING_   PENDING_   SIGNED
            EMPLOYEE   APPROVAL
```

### 5.4 与PersonalKPI的关系

```
PBC (承诺书) - 流程管理层
 ├── 包含多个 PersonalKPI（KPI数据载体）
 ├── 增加三级目标值（baseline/target/stretch）
 ├── 增加关键任务
 ├── 增加签署流程管理
 └── 支持附件上传
```

---

## 六、经营分析会

### 6.1 会议类型

| 会议类型 | 频率 | 参与者 | 核心议题 |
|---------|------|--------|---------|
| **月度经营分析会** | 每月 | 管理层 | KPI达成、异常预警、资源调配 |
| **季度BP审视会** | 每季 | 高管+部门负责人 | 战略执行、目标调整、重大决策 |
| **年度复盘会** | 年末 | 全体管理层 | 年度总结、绩效评价、次年规划 |

### 6.2 数据模型

```python
class MeetingType(str, Enum):
    """会议类型"""
    MONTHLY = "MONTHLY"         # 月度经营分析会
    QUARTERLY = "QUARTERLY"     # 季度BP审视会
    ANNUAL = "ANNUAL"           # 年度复盘会


class MeetingStatus(str, Enum):
    """会议状态"""
    PLANNED = "PLANNED"         # 已计划
    IN_PROGRESS = "IN_PROGRESS" # 进行中
    COMPLETED = "COMPLETED"     # 已完成
    CANCELLED = "CANCELLED"     # 已取消


class BusinessReviewMeeting(Base):
    """经营分析会"""
    __tablename__ = "business_review_meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, comment="会议编号")
    fiscal_year_id = Column(Integer, ForeignKey("fiscal_year_configs.id"), nullable=False)

    # 会议类型与期间
    meeting_type = Column(String(20), nullable=False)
    period = Column(String(20), comment="期间标识，如 2026-Q1、2026-03")

    # 会议安排
    title = Column(String(200), nullable=False, comment="会议主题")
    scheduled_date = Column(DateTime, nullable=False)
    actual_date = Column(DateTime)
    location = Column(String(200))
    duration_minutes = Column(Integer, comment="预计时长(分钟)")

    # 参与者
    chairperson_id = Column(Integer, ForeignKey("users.id"))
    participants = Column(Text, comment="参会人列表(JSON)")

    # 状态
    status = Column(String(20), default="PLANNED")

    # 会议产出
    minutes_summary = Column(Text, comment="会议纪要摘要")
    minutes_detail = Column(Text, comment="详细会议纪要")

    # 时间戳
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # 关系
    fiscal_year = relationship("FiscalYearConfig")
    chairperson = relationship("User")
    agenda_items = relationship("MeetingAgendaItem", back_populates="meeting", lazy="dynamic")
    resolutions = relationship("MeetingResolution", back_populates="meeting", lazy="dynamic")


class AgendaItemCategory(str, Enum):
    """议题类别"""
    KPI_ALERT = "KPI_ALERT"         # KPI预警
    PROJECT_DELAY = "PROJECT_DELAY" # 项目延期
    RESOURCE = "RESOURCE"           # 资源问题
    STRATEGY = "STRATEGY"           # 战略议题
    FOLLOW_UP = "FOLLOW_UP"         # 上次决议回顾
    OTHER = "OTHER"                 # 其他


class MeetingAgendaItem(Base):
    """会议议题"""
    __tablename__ = "meeting_agenda_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("business_review_meetings.id"), nullable=False)

    # 议题信息
    item_type = Column(String(20), default="MANUAL", comment="类型：AUTO_GENERATED/MANUAL")
    category = Column(String(30), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)

    # 关联对象（自动生成议题时）
    related_type = Column(String(30), comment="关联类型：KPI/PROJECT/DEPARTMENT/RESOLUTION")
    related_id = Column(Integer)

    # 排序与状态
    sort_order = Column(Integer, default=0)
    status = Column(String(20), default="PENDING", comment="状态：PENDING/DISCUSSED/DEFERRED")

    # 讨论结果
    discussion_notes = Column(Text)
    conclusion = Column(Text)
    discussed_at = Column(DateTime)

    # 关系
    meeting = relationship("BusinessReviewMeeting", back_populates="agenda_items")


class ResolutionStatus(str, Enum):
    """决议状态"""
    PENDING = "PENDING"         # 待执行
    IN_PROGRESS = "IN_PROGRESS" # 执行中
    COMPLETED = "COMPLETED"     # 已完成
    OVERDUE = "OVERDUE"         # 已逾期
    CANCELLED = "CANCELLED"     # 已取消


class MeetingResolution(Base):
    """会议决议/待办事项"""
    __tablename__ = "meeting_resolutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("business_review_meetings.id"), nullable=False)
    agenda_item_id = Column(Integer, ForeignKey("meeting_agenda_items.id"))

    # 决议信息
    resolution_type = Column(String(20), comment="类型：DECISION/ACTION/FOLLOW_UP")
    title = Column(String(300), nullable=False)
    description = Column(Text)

    # 责任与时限
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    co_owners = Column(Text, comment="协办人(JSON)")
    due_date = Column(Date, nullable=False)
    priority = Column(String(10), default="MEDIUM", comment="优先级：HIGH/MEDIUM/LOW")

    # 跟踪
    status = Column(String(20), default="PENDING")
    progress_percent = Column(Integer, default=0)
    progress_notes = Column(Text)
    completed_at = Column(DateTime)

    # 下次会议回顾
    review_meeting_id = Column(Integer, ForeignKey("business_review_meetings.id"))
    review_status = Column(String(20), comment="回顾状态：REVIEWED/CLOSED")
    review_notes = Column(Text)

    # 时间戳
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    # 关系
    meeting = relationship("BusinessReviewMeeting", foreign_keys=[meeting_id], back_populates="resolutions")
    agenda_item = relationship("MeetingAgendaItem")
    owner = relationship("User", foreign_keys=[owner_id])
    review_meeting = relationship("BusinessReviewMeeting", foreign_keys=[review_meeting_id])
```

### 6.3 议题自动生成规则

```python
class AgendaAutoGenerationService:
    """议题自动生成服务"""

    def generate_monthly_agenda(self, fiscal_year_id: int, month: int) -> List[dict]:
        """生成月度会议议题"""
        agenda_items = []

        # 1. KPI预警议题
        warning_kpis = self.kpi_service.get_warning_kpis(fiscal_year_id)
        for kpi in warning_kpis:
            agenda_items.append({
                "category": "KPI_ALERT",
                "title": f"KPI预警：{kpi.name} 完成率 {kpi.completion_rate}%",
                "description": f"当前值：{kpi.current_value}，目标值：{kpi.target_value}",
                "related_type": "KPI",
                "related_id": kpi.id
            })

        # 2. 延期项目议题
        delayed_projects = self.project_service.get_delayed_projects()
        for project in delayed_projects:
            agenda_items.append({
                "category": "PROJECT_DELAY",
                "title": f"项目延期：{project.name}（延期{project.delay_days}天）",
                "related_type": "PROJECT",
                "related_id": project.id
            })

        # 3. 上次会议待办回顾
        last_meeting = self.get_last_meeting(fiscal_year_id, "MONTHLY")
        if last_meeting:
            pending_resolutions = self.get_pending_resolutions(last_meeting.id)
            for resolution in pending_resolutions:
                agenda_items.append({
                    "category": "FOLLOW_UP",
                    "title": f"决议跟踪：{resolution.title}",
                    "description": f"责任人：{resolution.owner.name}，截止：{resolution.due_date}",
                    "related_type": "RESOLUTION",
                    "related_id": resolution.id
                })

        return agenda_items
```

### 6.4 完整闭环流程

```
会议前                会议中              会议后              下次会议
───────────────────────────────────────────────────────────────────
自动生成议题    →    讨论并记录    →    创建决议/待办  →   回顾决议
  ↓                    ↓                   ↓                 ↓
手动补充议题         记录结论           分配责任人        更新状态
  ↓                    ↓                   ↓                 ↓
发送会议通知         形成纪要           跟踪进展          关闭/延续
```

---

## 七、API设计

```
/api/v1/strategy/
│
├── dste/                              # DSTE日历化流程
│   ├── fiscal-years/                  # 财年配置
│   │   ├── GET    /                   # 财年列表
│   │   ├── POST   /                   # 创建财年
│   │   ├── GET    /{id}               # 财年详情（含阶段）
│   │   ├── PUT    /{id}               # 更新财年
│   │   └── GET    /current            # 当前财年
│   │
│   ├── phases/                        # BP阶段
│   │   ├── GET    /                   # 阶段列表
│   │   └── PUT    /{id}/status        # 更新阶段状态
│   │
│   └── tasks/                         # 阶段任务
│       ├── GET    /                   # 任务列表
│       ├── GET    /my                 # 我的待办任务
│       ├── PUT    /{id}/complete      # 完成任务
│       └── GET    /overdue            # 逾期任务
│
├── responsibility/                    # 责任中心
│   ├── centers/                       # 责任中心配置
│   │   ├── GET    /                   # 配置列表
│   │   ├── POST   /                   # 创建配置
│   │   └── PUT    /{id}               # 更新配置
│   │
│   └── templates/                     # KPI模板
│       ├── GET    /                   # 模板列表
│       ├── POST   /                   # 创建模板
│       └── GET    /{center_type}      # 获取指定类型的KPI模板
│
├── pbc/                               # PBC签署
│   ├── GET    /                       # PBC列表
│   ├── POST   /                       # 创建PBC
│   ├── GET    /{id}                   # PBC详情
│   ├── PUT    /{id}                   # 更新PBC
│   ├── POST   /{id}/employee-sign     # 员工签署
│   ├── POST   /{id}/manager-sign      # 主管确认
│   ├── POST   /{id}/approve           # 高管审批
│   ├── POST   /{id}/revise            # 修订PBC
│   ├── POST   /{id}/attachment        # 上传附件
│   ├── GET    /my                     # 我的PBC
│   └── GET    /pending                # 待我处理的PBC
│
└── meetings/                          # 经营分析会
    ├── GET    /                       # 会议列表
    ├── POST   /                       # 创建会议
    ├── GET    /{id}                   # 会议详情
    ├── PUT    /{id}                   # 更新会议
    ├── POST   /{id}/generate-agenda   # 自动生成议题
    │
    ├── /{id}/agenda/                  # 议题管理
    │   ├── GET    /                   # 议题列表
    │   ├── POST   /                   # 添加议题
    │   ├── PUT    /{item_id}          # 更新议题
    │   └── PUT    /{item_id}/discuss  # 记录讨论结果
    │
    ├── /{id}/resolutions/             # 决议管理
    │   ├── GET    /                   # 决议列表
    │   ├── POST   /                   # 创建决议
    │   ├── PUT    /{res_id}           # 更新决议
    │   └── PUT    /{res_id}/complete  # 完成决议
    │
    └── resolutions/                   # 决议跟踪（跨会议）
        ├── GET    /pending            # 待办决议
        ├── GET    /overdue            # 逾期决议
        └── GET    /my                 # 我的决议
```

---

## 八、前端页面设计

### 8.1 页面清单

| 页面 | 路由 | 主要用户 |
|------|------|---------|
| 财年配置 | /strategy/dste/fiscal-years | 系统管理员 |
| DSTE日历看板 | /strategy/dste/calendar | 管理层/战略部 |
| 我的BP任务 | /strategy/dste/my-tasks | 全员 |
| 责任中心配置 | /strategy/responsibility/config | 系统管理员 |
| PBC管理 | /strategy/pbc | 各级主管 |
| 我的PBC | /strategy/pbc/my | 全员 |
| 经营分析会 | /strategy/meetings | 管理层 |
| 决议跟踪 | /strategy/meetings/resolutions | 管理层 |

### 8.2 DSTE日历看板

```
┌─ DSTE日历看板 - FY2026 ─────────────────────────────────────────┐
│                                                                  │
│  当前阶段: ● BP制定期 (2025-12-01 ~ 2026-01-31)    剩余 15 天    │
│                                                                  │
│  ┌─ 年度时间轴 ───────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  SP输入期        BP制定期         执行期          复盘期   │  │
│  │  ━━━━━━━━       ████████░░       ──────────      ──────   │  │
│  │  ✓ 完成         ● 进行中          待开始         待开始   │  │
│  │  9-11月         12-1月            2-11月         12月     │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ 当前阶段任务 ─────────────────────────────────────────────┐  │
│  │  任务                    责任人        截止日期    状态    │  │
│  │  ─────────────────────────────────────────────────────────  │  │
│  │  ✓ 战略解码完成          战略部        12-15      已完成   │  │
│  │  ✓ 部门KPI草案提交       各部门        12-25      已完成   │  │
│  │  ● BP述职评审            各部门        01-10      进行中   │  │
│  │  ○ PBC分配               各级主管      01-20      待开始   │  │
│  │  ○ PBC签署               全员          01-31      待开始   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ 任务完成统计 ─────────────────────────────────────────────┐  │
│  │  已完成: 8    进行中: 3    待开始: 4    逾期: 1            │  │
│  │  ████████████████████░░░░░░░░░░░░  62%                     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.3 PBC签署页面

```
┌─ 我的PBC - 2026财年 ─────────────────────────────────────────────┐
│                                                                  │
│  员工: 张三          部门: 研发部          主管: 李四            │
│  状态: ● 待签署      截止日期: 2026-01-31                        │
│                                                                  │
│  ┌─ KPI承诺 ──────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  指标              权重    底线值    达标值    挑战值      │  │
│  │  ─────────────────────────────────────────────────────────  │  │
│  │  项目交付准时率     30%     85%      92%       98%        │  │
│  │  设计一次通过率     25%     80%      90%       95%        │  │
│  │  技术文档完整率     20%     90%      100%      100%       │  │
│  │  创新提案数量       15%     1个      3个       5个        │  │
│  │  培训学时          10%     30h      40h       50h        │  │
│  │  ─────────────────────────────────────────────────────────  │  │
│  │  权重合计          100%                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ 关键任务 ─────────────────────────────────────────────────┐  │
│  │  1. 完成新一代ICT测试平台架构设计（Q2）                    │  │
│  │  2. 主导3个重点项目的技术方案评审（全年）                  │  │
│  │  3. 培养1名初级工程师具备独立设计能力（Q4）                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ 承诺声明 ─────────────────────────────────────────────────┐  │
│  │  我承诺在2026财年达成上述绩效目标，并接受基于实际达成      │  │
│  │  情况的绩效评价。                                          │  │
│  │                                                            │  │
│  │  □ 我已阅读并理解上述KPI目标和关键任务                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  上传签署文件: [选择文件]  支持PDF/图片                          │
│                                                                  │
│                                          [保存草稿]  [确认签署]  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.4 经营分析会页面

```
┌─ 经营分析会 - 2026年3月月度会 ───────────────────────────────────┐
│                                                                  │
│  会议编号: BRM-2026-M03    状态: ● 进行中    主持人: 王总        │
│  时间: 2026-03-05 14:00    地点: 3楼会议室                       │
│                                                                  │
│  ┌─ 会议议题 ─────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  # 类型        议题                              状态      │  │
│  │  ──────────────────────────────────────────────────────── │  │
│  │  1 [KPI预警]   营收达成率仅72%，低于目标        ● 讨论中   │  │
│  │  2 [项目延期]  PJ260201项目延期15天             ○ 待讨论   │  │
│  │  3 [决议回顾]  上月决议：增加销售人员           ○ 待讨论   │  │
│  │  4 [其他]      Q2资源调配计划                   ○ 待讨论   │  │
│  │                                                            │  │
│  │                                    [+ 添加议题]            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ 当前议题详情 ─────────────────────────────────────────────┐  │
│  │  议题: 营收达成率仅72%，低于目标                           │  │
│  │  关联: KPI-F-001 (营收达成率)                              │  │
│  │  ─────────────────────────────────────────────────────────  │  │
│  │  讨论记录:                                                 │  │
│  │  ┌────────────────────────────────────────────────────┐   │  │
│  │  │ 主要原因：Q1大客户订单延迟签约                      │   │  │
│  │  │ 应对措施：加快A客户跟进，预计4月可签约              │   │  │
│  │  └────────────────────────────────────────────────────┘   │  │
│  │                                                            │  │
│  │  结论: [下拉选择]  ○需创建决议  ○需持续跟踪  ○已解决      │  │
│  │                                                            │  │
│  │                                [保存] [下一议题]           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ 本次会议决议 ─────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  决议                        责任人    截止日    状态      │  │
│  │  ─────────────────────────────────────────────────────────  │  │
│  │  加快A客户签约推进           销售部张总  04-15   待执行    │  │
│  │  准备B客户备选方案           研发部李工  03-20   待执行    │  │
│  │                                                            │  │
│  │                                    [+ 添加决议]            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│                              [保存草稿]  [结束会议并生成纪要]    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 九、模块集成关系

### 9.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      BEM 战略管理模块                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ 战略规划层 ───────────────────────────────────────────┐    │
│  │  Strategy → CSF(BSC四维度) → KPI(IPOOC+三级目标值)     │    │
│  │                  ↓                                      │    │
│  │            AnnualKeyWork(年度重点工作)                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                     │
│  ┌─ DSTE流程层 [新增] ────────────────────────────────────┐    │
│  │  FiscalYearConfig → BPPhase → BPTask                   │    │
│  │       ↓                                                 │    │
│  │  责任中心 → KPI模板推荐                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                     │
│  ┌─ 目标分解层 ───────────────────────────────────────────┐    │
│  │  DepartmentObjective → PersonalKPI → PBC签署           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                     │
│  ┌─ 横向协同层 ───────────────────────────────────────────┐    │
│  │  ProjectTriangle → CollaborationPerformance            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                     │
│  ┌─ 执行监控层 ───────────────────────────────────────────┐    │
│  │  BusinessReviewMeeting → MeetingResolution             │    │
│  │            ↓                                            │    │
│  │  StrategyReview(战略审视) ← 数据汇聚                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 数据流向

```
SP(战略规划)
    ↓ 输入
FiscalYearConfig(财年配置)
    ↓ 启动
BPPhase + BPTask(BP日历任务)
    ↓ 驱动
Strategy → CSF → KPI(三级目标值)
    ↓ 按责任中心
DepartmentObjective(部门目标)
    ↓ 分解
PersonalKPI → PBC(签署承诺)
    ↓ 执行
KPI数据采集 + 项目执行
    ↓ 监控
BusinessReviewMeeting(经营分析会)
    ↓ 决议跟踪
MeetingResolution → 闭环回顾
    ↓ 年终
PerformanceEvaluation(绩效评价) → 奖金/晋升
```

---

## 十、新增实体汇总

| 实体 | 说明 | 关联 |
|------|------|------|
| FiscalYearConfig | 财年配置 | DSTE日历基础 |
| BPPhase | BP阶段 | 属于财年 |
| BPTask | 阶段任务 | 属于阶段 |
| DepartmentResponsibility | 部门责任中心 | 关联部门+财年 |
| ResponsibilityCenterKPITemplate | 责任中心KPI模板 | 按中心类型 |
| PBC | 个人绩效承诺书 | 关联员工+财年 |
| PBCAttachment | PBC附件 | 属于PBC |
| BusinessReviewMeeting | 经营分析会 | 属于财年 |
| MeetingAgendaItem | 会议议题 | 属于会议 |
| MeetingResolution | 会议决议 | 属于会议 |

---

## 十一、现有实体增强

| 实体 | 增强字段 |
|------|---------|
| KPI | baseline_value, stretch_value, target_rationale, last_year_actual, industry_benchmark |
| DepartmentObjective | responsibility_id, kpi_source |

---

## 十二、设计决策记录

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 财年周期 | 可配置 | 不同公司可能使用不同财年 |
| 责任中心 | 四类（利润/收入/成本/费用）| 与华为体系一致，覆盖常见部门类型 |
| 三级目标值 | 底线/达标/挑战 | 让考核更科学，区分合格与卓越 |
| PBC签署 | 分层管理 | 高管需更正式流程，普通员工可简化 |
| PBC附件 | 支持上传 | 满足正式承诺留档需求 |
| 经营分析会 | 完整闭环 | 议题→决议→跟踪→回顾，确保执行落地 |
| 议题生成 | 自动+手动 | 自动生成提高效率，手动补充保证灵活 |

---

## 附录：参考资料

- 华为BP解码组织绩效方法论
- 华为DSTE（从战略到执行）流程
- 华为BEM（业务战略执行力模型）
- 平衡计分卡（BSC）
- 现有BEM战略管理模块设计文档
