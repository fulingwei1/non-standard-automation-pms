# BEM横向协同指标设计 - 铁三角协同绩效模块

## 概述

基于华为跨部门横向协同指标设定方法论，在现有BEM战略管理模块基础上增加**铁三角协同绩效**子模块，实现从"职能筒仓"到"流程贯通"的转变。

### 设计背景

现有BEM模块已实现**纵向分解**（Strategy → CSF → KPI → Department → Personal），但缺少横向协同机制。如文章所述："没有有效的横向协同指标设计，战略执行就像一辆拆掉传动轴的汽车——每个轮子（部门）都在转，但整车（公司）无法协同前进。"

### 核心理念

- **流程导向原则**：以项目端到端流程（S1-S9）为载体，关联各部门协同
- **互锁共担原则**：铁三角成员对项目经营指标共担责任，一荣俱荣、一损俱损
- **均衡牵引原则**：既考核硬指标（毛利率），也关注过程指标（变更率）

---

## 一、整体架构

### 1.1 模块定位

```
BEM 战略管理模块
├── [现有] 纵向分解
│   └── Strategy → CSF → KPI → Department → Personal
│
└── [新增] 横向协同
    └── 铁三角协同绩效
        ├── 协同指标定义（系统级）
        ├── 权重模板管理（可配置）
        ├── 项目铁三角绑定
        ├── 协同绩效评价
        └── 绩效结果应用
```

### 1.2 设计原则

1. **与项目管理模块深度集成** - 铁三角成员从现有 `ProjectMember` 中识别，不重复维护
2. **指标数据自动采集** - 毛利率、交付率等从项目/财务模块自动获取，减少手工录入
3. **权重模板化** - 提供默认模板，支持按项目类型配置，也支持单项目覆盖
4. **项目结束时触发评价** - 当项目进入S9阶段时，自动生成协同绩效评价单

---

## 二、铁三角定义

### 2.1 角色构成

| 角色 | 职责 | 对应系统角色 |
|------|------|-------------|
| **销售** | 客户关系、需求沟通、商务谈判、回款推进 | ProjectMember.role = "sales" |
| **研发负责人** | 方案设计、技术实现、成本控制 | ProjectMember.role = "rd_lead" |
| **项目经理** | 项目执行、进度协调、交付管理 | ProjectMember.role = "pm" |

### 2.2 共享经营指标

| 指标 | 说明 | 数据来源 | 方向 |
|------|------|---------|------|
| **项目毛利率** | 实际毛利 vs 签单毛利，反映成本控制 | ProjectCost | 越高越好 |
| **准时交付率** | 按合同约定时间交付，反映协同效率 | Project.stages | 越高越好 |
| **需求变更率** | 签单后的变更次数/金额，反映前端需求准确性 | ECN | 越低越好 |
| **回款及时率** | 按里程碑及时回款，反映商务和交付配合 | Payment | 越高越好 |

### 2.3 默认权重分配

| 指标 | 销售 | 研发负责人 | 项目经理 | 说明 |
|------|------|-----------|---------|------|
| 项目毛利率 | 30% | 40% | 30% | 研发成本控制影响最大 |
| 准时交付率 | 20% | 30% | 50% | 项目经理主责协调 |
| 需求变更率 | 50% | 30% | 20% | 销售前端需求确认主责 |
| 回款及时率 | 50% | 20% | 30% | 销售主导商务关系 |

> 注：权重支持模板化配置，不同项目类型可使用不同模板，单项目也可自定义覆盖。

---

## 三、数据模型设计

### 3.1 核心实体

```python
class CollaborationKPI(Base):
    """协同指标定义（系统级）"""
    __tablename__ = "collaboration_kpis"

    id: int                      # 主键
    code: str                    # 指标编码，如 CK-001
    name: str                    # 指标名称，如 "项目毛利率"
    description: str             # 指标说明
    unit: str                    # 单位：%、次、天
    better_direction: str        # higher/lower，越高越好还是越低越好
    calculation_method: str      # 计算方法说明
    data_source_module: str      # 数据来源模块
    data_source_config: JSON     # 数据采集配置
    is_active: bool              # 是否启用
    sort_order: int              # 排序
    created_at: datetime
    updated_at: datetime


class CollaborationWeightTemplate(Base):
    """协同指标权重模板"""
    __tablename__ = "collaboration_weight_templates"

    id: int                      # 主键
    code: str                    # 模板编码
    name: str                    # 模板名称，如 "标准设备项目"、"整线项目"
    description: str             # 模板说明
    project_type: str            # 适用项目类型（可选）
    is_default: bool             # 是否默认模板
    weights: JSON                # 权重配置
    # 格式: {
    #   "sales": {"CK-001": 30, "CK-002": 20, "CK-003": 50, "CK-004": 50},
    #   "rd_lead": {"CK-001": 40, "CK-002": 30, "CK-003": 30, "CK-004": 20},
    #   "pm": {"CK-001": 30, "CK-002": 50, "CK-003": 20, "CK-004": 30}
    # }
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProjectTriangle(Base):
    """项目铁三角配置"""
    __tablename__ = "project_triangles"

    id: int                      # 主键
    project_id: int              # 关联项目（外键）
    sales_user_id: int           # 销售负责人（外键）
    rd_lead_user_id: int         # 研发负责人（外键）
    pm_user_id: int              # 项目经理（外键）
    weight_template_id: int      # 使用的权重模板（外键）
    custom_weights: JSON         # 单项目自定义权重（可选，覆盖模板）
    remarks: str                 # 备注
    created_by: int              # 创建人
    created_at: datetime
    updated_at: datetime

    # 关系
    project: Project
    sales_user: User
    rd_lead_user: User
    pm_user: User
    weight_template: CollaborationWeightTemplate


class CollaborationPerformance(Base):
    """项目协同绩效评价"""
    __tablename__ = "collaboration_performances"

    id: int                      # 主键
    project_id: int              # 关联项目（外键）
    triangle_id: int             # 关联铁三角（外键）
    evaluation_date: date        # 评价日期
    status: str                  # draft/confirmed/archived

    # 指标结果
    kpi_results: JSON            # 指标达成情况
    # 格式: {
    #   "CK-001": {"target": 25, "actual": 22, "score": 88},
    #   "CK-002": {"target": 100, "actual": 100, "score": 100},
    #   ...
    # }

    # 成员得分
    member_scores: JSON          # 成员最终得分
    # 格式: {
    #   "sales": {"user_id": 1, "score": 72, "breakdown": {...}},
    #   "rd_lead": {"user_id": 2, "score": 81, "breakdown": {...}},
    #   "pm": {"user_id": 3, "score": 86, "breakdown": {...}}
    # }

    remarks: str                 # 评价备注
    collected_at: datetime       # 数据采集时间
    confirmed_at: datetime       # 确认时间
    evaluated_by: int            # 评价人
    created_at: datetime
    updated_at: datetime

    # 关系
    project: Project
    triangle: ProjectTriangle
```

### 3.2 枚举定义

```python
class CollaborationKPICode(str, Enum):
    """协同指标编码"""
    PROFIT_MARGIN = "CK-001"      # 项目毛利率
    ON_TIME_DELIVERY = "CK-002"   # 准时交付率
    CHANGE_RATE = "CK-003"        # 需求变更率
    PAYMENT_RATE = "CK-004"       # 回款及时率


class TriangleRole(str, Enum):
    """铁三角角色"""
    SALES = "sales"               # 销售
    RD_LEAD = "rd_lead"           # 研发负责人
    PM = "pm"                     # 项目经理


class PerformanceStatus(str, Enum):
    """绩效评价状态"""
    DRAFT = "draft"               # 草稿
    CONFIRMED = "confirmed"       # 已确认
    ARCHIVED = "archived"         # 已归档


class KPIDirection(str, Enum):
    """指标方向"""
    HIGHER = "higher"             # 越高越好
    LOWER = "lower"               # 越低越好
```

---

## 四、指标数据采集

### 4.1 采集配置

| 指标 | 数据来源 | 计算公式 |
|------|---------|---------|
| 项目毛利率 | `ProjectCost` | (contract_amount - actual_cost) / contract_amount × 100% |
| 准时交付率 | `Project.stages` | S6实际完成日期 ≤ 计划日期 ? 100% : 按延期天数扣分 |
| 需求变更率 | `ECN` | COUNT(project_ecns) 或 SUM(change_amount) / contract_amount |
| 回款及时率 | `Payment` | on_time_received / total_receivable × 100% |

### 4.2 采集服务

```python
class CollaborationKPICollector:
    """协同指标数据采集器"""

    def collect_project_kpis(self, project_id: int) -> Dict[str, KPIResult]:
        """项目结束时自动采集所有协同指标"""
        return {
            "CK-001": self._calc_profit_margin(project_id),
            "CK-002": self._calc_delivery_rate(project_id),
            "CK-003": self._calc_change_rate(project_id),
            "CK-004": self._calc_payment_rate(project_id),
        }

    def _calc_profit_margin(self, project_id: int) -> KPIResult:
        """计算项目毛利率"""
        cost = self.db.query(ProjectCost).filter_by(project_id=project_id).first()
        if not cost:
            return KPIResult(target=0, actual=0, score=0)

        target = cost.planned_margin_rate or 25  # 默认目标25%
        actual = ((cost.contract_amount - cost.actual_cost) / cost.contract_amount) * 100
        score = min(100, (actual / target) * 100) if target > 0 else 0

        return KPIResult(target=target, actual=round(actual, 2), score=round(score, 1))

    def _calc_delivery_rate(self, project_id: int) -> KPIResult:
        """计算准时交付率"""
        project = self.db.query(Project).get(project_id)
        s6_stage = self._get_stage(project_id, "S6")

        if not s6_stage:
            return KPIResult(target=100, actual=0, score=0)

        planned_date = s6_stage.planned_end_date
        actual_date = s6_stage.actual_end_date

        if actual_date <= planned_date:
            return KPIResult(target=100, actual=100, score=100)
        else:
            delay_days = (actual_date - planned_date).days
            # 每延期1天扣5分，最低0分
            score = max(0, 100 - delay_days * 5)
            return KPIResult(target=100, actual=score, score=score)

    def _calc_change_rate(self, project_id: int) -> KPIResult:
        """计算需求变更率"""
        change_count = self.db.query(ECN).filter_by(project_id=project_id).count()
        target = 3  # 目标：变更不超过3次

        if change_count <= target:
            score = 100
        else:
            # 每多1次变更扣20分
            score = max(0, 100 - (change_count - target) * 20)

        return KPIResult(target=target, actual=change_count, score=score)

    def _calc_payment_rate(self, project_id: int) -> KPIResult:
        """计算回款及时率"""
        payments = self.db.query(Payment).filter_by(project_id=project_id).all()

        total_receivable = sum(p.amount for p in payments)
        on_time_received = sum(p.amount for p in payments if p.received_at <= p.due_date)

        if total_receivable == 0:
            return KPIResult(target=100, actual=100, score=100)

        actual = (on_time_received / total_receivable) * 100
        return KPIResult(target=100, actual=round(actual, 2), score=round(actual, 1))
```

### 4.3 采集触发时机

- **自动触发**：项目进入 S9（质保结项）阶段时
- **手动触发**：支持重新采集（数据修正后）

---

## 五、评价流程与得分计算

### 5.1 评价流程

```
项目进入S9 ──→ 检查铁三角配置 ──→ 自动采集指标数据 ──→ 计算成员得分 ──→ 生成评价草稿
                    │                                                          │
                    │ 未配置则提醒                                              ↓
                    └──────────────────────────────────────────────→ 人工确认/调整
                                                                               │
                                                                               ↓
                                                                         评价生效
                                                                               │
                                                                               ↓
                                                                      关联个人KPI/奖金
```

### 5.2 得分计算逻辑

**Step 1: 指标得分**（每个指标0-100分）

```python
def calc_kpi_score(actual: float, target: float, direction: str) -> float:
    """
    计算单个指标得分
    direction: "higher" 越高越好, "lower" 越低越好
    """
    if direction == "higher":
        # 越高越好：实际/目标 * 100，上限100
        return min(100, (actual / target) * 100) if target > 0 else 0
    else:
        # 越低越好：目标/实际 * 100，上限100
        if actual == 0:
            return 100
        return min(100, (target / actual) * 100)
```

**Step 2: 成员得分**（加权计算）

```python
def calc_member_score(kpi_scores: Dict, weights: Dict, role: str) -> float:
    """
    计算成员最终得分
    kpi_scores: {"CK-001": 88, "CK-002": 100, ...}
    weights: {"CK-001": 30, "CK-002": 20, ...}
    """
    role_weights = weights.get(role, {})
    total_weight = sum(role_weights.values())

    if total_weight == 0:
        return 0

    weighted_sum = sum(
        kpi_scores.get(kpi_code, 0) * weight
        for kpi_code, weight in role_weights.items()
    )

    return round(weighted_sum / total_weight, 1)
```

### 5.3 评价结果示例

```json
{
  "project_id": 123,
  "evaluation_date": "2026-01-28",
  "status": "confirmed",
  "kpi_results": {
    "CK-001": {"name": "项目毛利率", "target": 25, "actual": 22, "score": 88},
    "CK-002": {"name": "准时交付率", "target": 100, "actual": 100, "score": 100},
    "CK-003": {"name": "需求变更率", "target": 3, "actual": 5, "score": 60},
    "CK-004": {"name": "回款及时率", "target": 100, "actual": 85, "score": 85}
  },
  "member_scores": {
    "sales": {"user_id": 1, "name": "王小明", "score": 72.3},
    "rd_lead": {"user_id": 2, "name": "李工", "score": 81.5},
    "pm": {"user_id": 3, "name": "张经理", "score": 86.0}
  }
}
```

---

## 六、API 设计

### 6.1 API 端点

```
/api/v1/strategy/collaboration/
│
├── kpis/                           # 协同指标管理
│   ├── GET    /                    # 指标列表
│   ├── POST   /                    # 创建指标
│   ├── GET    /{id}                # 指标详情
│   └── PUT    /{id}                # 更新指标
│
├── templates/                      # 权重模板管理
│   ├── GET    /                    # 模板列表
│   ├── POST   /                    # 创建模板
│   ├── GET    /{id}                # 模板详情
│   ├── PUT    /{id}                # 更新模板
│   └── GET    /{id}/preview        # 预览权重分配
│
├── triangles/                      # 项目铁三角
│   ├── GET    /project/{project_id}    # 获取项目铁三角
│   ├── POST   /project/{project_id}    # 配置项目铁三角
│   ├── PUT    /{id}                    # 更新铁三角
│   ├── DELETE /{id}                    # 删除铁三角
│   └── GET    /my                      # 我参与的铁三角项目
│
└── performance/                    # 协同绩效评价
    ├── GET    /project/{project_id}    # 获取项目协同绩效
    ├── POST   /project/{project_id}/collect  # 触发数据采集
    ├── PUT    /{id}                    # 更新评价（调整备注等）
    ├── POST   /{id}/confirm            # 确认评价
    ├── GET    /summary                 # 协同绩效汇总
    └── GET    /ranking                 # 铁三角排行榜
```

### 6.2 与项目模块集成

```python
# 在项目阶段推进服务中增加触发逻辑
class ProjectStageService:

    async def advance_stage(self, project_id: int, new_stage: str):
        # ... 现有逻辑 ...

        # 当进入S9时，自动触发协同绩效采集
        if new_stage == "S9":
            triangle = await self.get_project_triangle(project_id)
            if triangle:
                await self.collaboration_service.trigger_collection(project_id)
            else:
                # 发送提醒：该项目未配置铁三角
                await self.notification_service.send(
                    title="项目协同绩效提醒",
                    content=f"项目 {project.code} 已进入质保结项阶段，但未配置铁三角，无法生成协同绩效评价。",
                    recipients=[project.pm_id]
                )
```

---

## 七、前端页面设计

### 7.1 页面清单

| 页面 | 路由 | 入口位置 | 主要用户 |
|------|------|---------|---------|
| 协同指标配置 | /strategy/collaboration/kpis | BEM管理后台 | 系统管理员 |
| 权重模板管理 | /strategy/collaboration/templates | BEM管理后台 | 系统管理员 |
| 项目铁三角配置 | 嵌入项目详情页 | 项目详情-协同Tab | 项目经理 |
| 协同绩效评价 | /strategy/collaboration/performance/{id} | 项目详情/消息通知 | 项目经理/管理层 |
| 我的协同绩效 | /strategy/my-strategy | 我的战略页 | 铁三角成员 |
| 协同绩效看板 | /strategy/dashboard/collaboration | BEM仪表板 | 管理层 |

### 7.2 项目铁三角配置（嵌入项目详情页）

```
┌─ 项目铁三角配置 ─────────────────────────────────────────────┐
│                                                              │
│  销售负责人      [王小明 ▼]                                   │
│  研发负责人      [李工 ▼]                                     │
│  项目经理        [张经理 ▼]                                   │
│                                                              │
│  权重模板        [标准设备项目 ▼]     □ 使用自定义权重         │
│                                                              │
│  ┌─ 权重预览 ───────────────────────────────────────────┐   │
│  │ 指标            销售      研发      项目经理          │   │
│  │ ───────────────────────────────────────────────────  │   │
│  │ 项目毛利率       30%      40%       30%              │   │
│  │ 准时交付率       20%      30%       50%              │   │
│  │ 需求变更率       50%      30%       20%              │   │
│  │ 回款及时率       50%      20%       30%              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│                                          [取消]  [保存配置]   │
└──────────────────────────────────────────────────────────────┘
```

### 7.3 协同绩效评价页面

```
┌─ 项目协同绩效评价 ─────────────────────────────────────────────┐
│                                                                │
│  项目编号: PJ260115001          项目名称: XX公司ICT测试设备     │
│  评价状态: ● 草稿               采集时间: 2026-01-28 10:30     │
│                                                                │
│  ┌─ 铁三角成员 ───────────────────────────────────────────┐   │
│  │ 👤 王小明(销售)  👤 李工(研发)  👤 张经理(PM)           │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─ 指标达成情况 ─────────────────────────────────────────┐   │
│  │ 指标            目标        实际        得分    状态    │   │
│  │ ─────────────────────────────────────────────────────  │   │
│  │ 项目毛利率      25%        22%         88分    ⚠       │   │
│  │ 准时交付率      100%       100%        100分   ✓       │   │
│  │ 需求变更率      ≤3次       5次         60分    ✗       │   │
│  │ 回款及时率      100%       85%         85分    ⚠       │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─ 成员得分 ─────────────────────────────────────────────┐   │
│  │                                                        │   │
│  │  王小明(销售)       72分  ████████░░░░░░░░░░░░░░       │   │
│  │  李工(研发)         81分  █████████░░░░░░░░░░░░        │   │
│  │  张经理(PM)         86分  ██████████░░░░░░░░░░         │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  评价备注:                                                     │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ 需求变更较多主要因为客户中途调整了产品规格...            │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│                              [重新采集]  [保存草稿]  [确认评价] │
└────────────────────────────────────────────────────────────────┘
```

### 7.4 协同绩效看板

```
┌─ 协同绩效看板 ──────────────────────────────────────────────────┐
│                                                                  │
│  时间范围: [2026年 ▼]    部门: [全部 ▼]    [导出报告]            │
│                                                                  │
│  ┌─ 概览 ────────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │   已评价项目        平均协同得分        优秀铁三角          │  │
│  │      32              78.5               8                  │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ 指标达成分布 ─────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  项目毛利率    ████████████████░░░░  82%                   │  │
│  │  准时交付率    ██████████████░░░░░░  75%                   │  │
│  │  需求变更率    ████████░░░░░░░░░░░░  65%   ← 需关注        │  │
│  │  回款及时率    ██████████████████░░  88%                   │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ 铁三角排行榜 TOP5 ────────────────────────────────────────┐  │
│  │ 排名   项目            销售    研发    PM      平均得分     │  │
│  │ ─────────────────────────────────────────────────────────  │  │
│  │ 🥇    PJ260108001     王小明  李工   张经理    92.5        │  │
│  │ 🥈    PJ260102003     赵六    陈工   周经理    89.2        │  │
│  │ 🥉    PJ260105002     刘七    吴工   郑经理    87.8        │  │
│  │ 4     PJ260103001     ...     ...    ...       85.3        │  │
│  │ 5     PJ260107002     ...     ...    ...       84.1        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 八、与现有模块集成

### 8.1 与BEM战略模块集成

协同绩效得分可作为个人KPI来源之一：

```python
class PersonalKPI(Base):
    # ... 现有字段 ...
    source_type: str   # 新增选项: "collaboration"
    source_id: int     # 关联 CollaborationPerformance.id
```

### 8.2 与项目管理模块集成

| 集成点 | 方式 |
|--------|------|
| 铁三角成员 | 从 `ProjectMember` 中按角色识别，或独立配置 |
| 阶段触发 | S9阶段推进时自动触发绩效采集 |
| 成本数据 | 从 `ProjectCost` 读取合同金额、实际成本 |
| 交付数据 | 从 `Project.stages` 读取计划/实际完成日期 |
| 变更数据 | 从 `ECN` 统计变更次数和金额 |

### 8.3 与绩效/奖金模块集成

```python
class ProjectBonusAllocation(Base):
    """项目奖金分配"""
    project_id: int
    collaboration_performance_id: int  # 关联协同绩效
    allocation_method: str             # equal / by_score / custom
    allocations: JSON                  # {"user_id": amount, ...}
```

---

## 九、实施建议

### 9.1 分阶段实施

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| **Phase 1** | 数据模型 + 基础API + 铁三角配置页面 | P0 |
| **Phase 2** | 指标采集服务 + 评价流程 | P0 |
| **Phase 3** | 协同绩效看板 + 排行榜 | P1 |
| **Phase 4** | 与绩效/奖金模块集成 | P2 |

### 9.2 初始化数据

系统上线时需初始化：

1. **4个默认协同指标**（项目毛利率、准时交付率、需求变更率、回款及时率）
2. **1个默认权重模板**（可作为基准）
3. **管理后台配置入口**（允许管理员调整指标和模板）

---

## 十、设计决策记录

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 协同模式 | 铁三角 | 与项目管理模块天然契合，效果易验证 |
| 铁三角角色 | 销售+研发负责人+项目经理 | 覆盖签单、设计、交付三大环节 |
| 共享指标 | 4个（毛利率、交付率、变更率、回款率） | 形成完整项目经营闭环 |
| 权重机制 | 模板化+可覆盖 | 兼顾标准化和灵活性 |
| 评价周期 | 项目结束时 | 简化流程，符合非标项目特点 |
| 数据采集 | 自动采集 | 减少手工录入，提高数据准确性 |

---

## 附录：参考资料

- 华为跨部门横向协同指标设定方法（BP→组织绩效）
- 华为铁三角运作机制
- 现有BEM战略管理模块设计文档
