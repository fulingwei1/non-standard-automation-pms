# 成本-方案-报价绑定：数据模型重构方案

> 生成日期：2026-03-12
> 优先级：P0
> 预计工时：32h

---

## 一、现状分析

### 1.1 现有数据模型

```
┌─────────────────────────┐     ┌─────────────────────────┐     ┌─────────────────────────┐
│  PresaleAISolution      │     │ PresaleAICostEstimation │     │     QuoteVersion        │
├─────────────────────────┤     ├─────────────────────────┤     ├─────────────────────────┤
│ presale_ticket_id       │     │ presale_ticket_id       │     │ quote_id                │
│ estimated_cost (冗余)   │◄────┤ solution_id (nullable)  │     │ cost_total (独立输入)   │
│ cost_breakdown (冗余)   │     │ total_cost              │     │ cost_template_id        │
│ status                  │     │ hardware_cost           │     │ total_price             │
│ generated_solution      │     │ software_cost           │     │ gross_margin            │
│ bom_list                │     │ installation_cost       │     │                         │
│ 【无版本控制】          │     │ 【无版本控制】          │     │ 【有版本控制】          │
└─────────────────────────┘     └─────────────────────────┘     └─────────────────────────┘
         ↑                               ↑                               ↑
         │                               │                               │
         └───────────────────────────────┴───────────────────────────────┘
                                    【完全解耦】
```

### 1.2 核心问题

| 问题 | 影响 | 风险等级 |
|------|------|----------|
| **方案无版本控制** | 修改直接覆盖，无法追溯历史 | 🔴 高 |
| **成本与报价解耦** | 报价的 cost_total 可与成本估算不一致 | 🔴 高 |
| **无绑定约束** | 方案变更不触发成本重估，成本变更不触发报价更新 | 🔴 高 |
| **数据冗余** | 成本信息在 3 处重复存储，易不一致 | 🟡 中 |
| **无审计追踪** | 无法回答"这个报价基于哪个版本的方案和成本？" | 🟡 中 |

---

## 二、目标架构

### 2.1 新数据模型关系图

```
┌─────────────────────────┐
│   PresaleAISolution     │  ← 方案主表（保持不变）
│   (方案主表)            │
├─────────────────────────┤
│ id                      │
│ presale_ticket_id       │
│ current_version_id ──────┼──────┐
└─────────────────────────┘      │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        SolutionVersion (新建)                            │
│                           方案版本表                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ id                      │ solution_id (FK)        │ version_no           │
│ generated_solution      │ bom_list                │ architecture_diagram │
│ status (draft/approved) │ created_by              │ created_at           │
│ approved_by             │ approved_at             │ change_summary       │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   PresaleAICostEstimation (重构)                         │
│                        成本估算表                                         │
├─────────────────────────────────────────────────────────────────────────┤
│ id                      │ solution_version_id (FK) ← 【新增：绑定方案版本】│
│ version_no (新增)       │ presale_ticket_id        │                     │
│ hardware_cost           │ software_cost            │ installation_cost    │
│ service_cost            │ risk_reserve             │ total_cost           │
│ status (新增)           │ approved_by (新增)       │ approved_at (新增)   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    │ 1:N
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        QuoteVersion (重构)                               │
│                         报价版本表                                        │
├─────────────────────────────────────────────────────────────────────────┤
│ id                      │ quote_id (FK)             │ version_no          │
│ solution_version_id (FK)│ cost_estimation_id (FK)  ← 【新增：绑定成本估算】│
│ total_price             │ cost_total (只读，从估算同步)                   │
│ gross_margin            │ status                    │                     │
│ binding_status (新增)   │ binding_validated_at (新增)                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 绑定关系说明

**三位一体绑定**：

```
QuoteVersion.V3
    ├── cost_estimation_id → CostEstimation.V2
    │       └── solution_version_id → SolutionVersion.V1
    └── solution_version_id → SolutionVersion.V1 (冗余，用于快速查询)
```

**绑定规则**：

1. **QuoteVersion 必须绑定 CostEstimation**：不允许创建未绑定成本的报价
2. **CostEstimation 必须绑定 SolutionVersion**：不允许创建未绑定方案的成本
3. **绑定验证**：`QuoteVersion.cost_total` 必须等于 `CostEstimation.total_cost`
4. **级联提醒**：方案变更时，提醒重估成本；成本变更时，提醒更新报价

---

## 三、详细设计

### 3.1 新建模型：SolutionVersion

```python
# app/models/sales/solution_version.py

class SolutionVersion(Base, TimestampMixin):
    """方案版本表

    为 PresaleAISolution 提供版本控制能力。
    每次方案修改生成新版本，不覆盖旧版本。
    """

    __tablename__ = "solution_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    solution_id = Column(
        Integer,
        ForeignKey("presale_ai_solution.id"),
        nullable=False,
        comment="方案ID"
    )
    version_no = Column(String(20), nullable=False, comment="版本号，如 V1.0, V1.1")

    # === 方案内容（从 PresaleAISolution 迁移）===
    generated_solution = Column(JSON, comment="生成的完整方案")
    architecture_diagram = Column(Text, comment="系统架构图 Mermaid 代码")
    topology_diagram = Column(Text, comment="设备拓扑图")
    signal_flow_diagram = Column(Text, comment="信号流程图")
    bom_list = Column(JSON, comment="BOM清单")
    technical_parameters = Column(JSON, comment="技术参数表")

    # === 变更信息 ===
    change_summary = Column(Text, comment="变更摘要")
    change_reason = Column(String(200), comment="变更原因")
    parent_version_id = Column(
        Integer,
        ForeignKey("solution_versions.id"),
        comment="父版本ID（用于版本树）"
    )

    # === 审批状态 ===
    status = Column(
        String(20),
        default="draft",
        comment="状态：draft/pending_review/approved/rejected"
    )
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")
    approval_comments = Column(Text, comment="审批意见")

    # === AI 元数据 ===
    ai_model_used = Column(String(100), comment="使用的AI模型")
    confidence_score = Column(DECIMAL(3, 2), comment="方案置信度")
    quality_score = Column(DECIMAL(3, 2), comment="方案质量评分")

    # === 关系 ===
    solution = relationship("PresaleAISolution", back_populates="versions")
    parent_version = relationship("SolutionVersion", remote_side=[id])
    cost_estimations = relationship("PresaleAICostEstimation", back_populates="solution_version")
    quote_versions = relationship("QuoteVersion", back_populates="solution_version")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        Index("idx_sv_solution_id", "solution_id"),
        Index("idx_sv_status", "status"),
        UniqueConstraint("solution_id", "version_no", name="uq_solution_version"),
    )
```

### 3.2 重构模型：PresaleAICostEstimation

```python
# app/models/sales/presale_ai_cost.py（修改）

class PresaleAICostEstimation(Base):
    """AI成本估算记录表（重构版）

    【变更】：
    1. 新增 solution_version_id，替代原 solution_id
    2. 新增 version_no，支持同一方案版本多次估算
    3. 新增审批流程字段
    4. 新增绑定状态字段
    """

    __tablename__ = "presale_ai_cost_estimation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    presale_ticket_id = Column(Integer, nullable=False, comment="售前工单ID")

    # === 【新增】方案版本绑定 ===
    solution_version_id = Column(
        Integer,
        ForeignKey("solution_versions.id"),
        nullable=False,  # 强制绑定
        comment="方案版本ID"
    )
    version_no = Column(String(20), default="V1", comment="成本估算版本号")

    # === 成本分解（保持不变）===
    hardware_cost = Column(DECIMAL(12, 2), comment="硬件成本")
    software_cost = Column(DECIMAL(12, 2), comment="软件成本")
    installation_cost = Column(DECIMAL(12, 2), comment="安装调试成本")
    service_cost = Column(DECIMAL(12, 2), comment="售后服务成本")
    risk_reserve = Column(DECIMAL(12, 2), comment="风险储备金")
    total_cost = Column(DECIMAL(12, 2), nullable=False, comment="总成本")

    # === AI分析结果（保持不变）===
    optimization_suggestions = Column(JSON, comment="成本优化建议")
    pricing_recommendations = Column(JSON, comment="定价推荐")
    confidence_score = Column(DECIMAL(3, 2), comment="置信度评分")

    # === 【新增】审批流程 ===
    status = Column(
        String(20),
        default="draft",
        comment="状态：draft/pending_review/approved/rejected"
    )
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")
    approval_comments = Column(Text, comment="审批意见")

    # === 【新增】绑定状态 ===
    is_bound_to_quote = Column(Boolean, default=False, comment="是否已绑定报价")
    bound_quote_version_id = Column(Integer, comment="绑定的报价版本ID（反向引用）")

    # === 关系 ===
    solution_version = relationship("SolutionVersion", back_populates="cost_estimations")
    quote_versions = relationship("QuoteVersion", back_populates="cost_estimation")

    __table_args__ = (
        Index("idx_ce_solution_version", "solution_version_id"),
        Index("idx_ce_status", "status"),
        UniqueConstraint(
            "solution_version_id", "version_no",
            name="uq_cost_estimation_version"
        ),
    )
```

### 3.3 重构模型：QuoteVersion

```python
# app/models/sales/quotes.py（修改 QuoteVersion）

class QuoteVersion(Base, TimestampMixin):
    """报价版本表（重构版）

    【变更】：
    1. 新增 solution_version_id，绑定方案版本
    2. 新增 cost_estimation_id，绑定成本估算
    3. 新增绑定验证字段
    4. cost_total 改为只读（从绑定的成本估算同步）
    """

    __tablename__ = "quote_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    version_no = Column(String(10), nullable=False, comment="版本号")

    # === 【新增】三位一体绑定 ===
    solution_version_id = Column(
        Integer,
        ForeignKey("solution_versions.id"),
        nullable=False,  # 强制绑定
        comment="方案版本ID"
    )
    cost_estimation_id = Column(
        Integer,
        ForeignKey("presale_ai_cost_estimation.id"),
        nullable=False,  # 强制绑定
        comment="成本估算ID"
    )

    # === 定价信息 ===
    total_price = Column(Numeric(12, 2), comment="报价总价")
    cost_total = Column(Numeric(12, 2), comment="成本总计（只读，从估算同步）")
    gross_margin = Column(Numeric(5, 2), comment="毛利率")

    # === 【新增】绑定验证 ===
    binding_status = Column(
        String(20),
        default="valid",
        comment="绑定状态：valid/outdated/invalid"
    )
    binding_validated_at = Column(DateTime, comment="最后验证时间")
    binding_warning = Column(Text, comment="绑定警告信息")

    # === 现有字段（保持不变）===
    lead_time_days = Column(Integer, comment="交期(天)")
    risk_terms = Column(Text, comment="风险条款")
    delivery_date = Column(Date, comment="交付日期")
    created_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)

    # === 关系 ===
    quote = relationship("Quote", back_populates="versions", foreign_keys=[quote_id])
    solution_version = relationship("SolutionVersion", back_populates="quote_versions")
    cost_estimation = relationship("PresaleAICostEstimation", back_populates="quote_versions")

    __table_args__ = (
        Index("idx_qv_solution_version", "solution_version_id"),
        Index("idx_qv_cost_estimation", "cost_estimation_id"),
        Index("idx_qv_binding_status", "binding_status"),
    )
```

### 3.4 重构模型：PresaleAISolution

```python
# app/models/presale_ai_solution.py（修改）

class PresaleAISolution(Base):
    """AI方案生成记录表（重构版）

    【变更】：
    1. 新增 current_version_id，指向当前生效版本
    2. 方案内容字段迁移到 SolutionVersion
    3. 保留元数据和创建信息
    """

    __tablename__ = "presale_ai_solution"

    id = Column(Integer, primary_key=True, autoincrement=True)
    presale_ticket_id = Column(Integer, nullable=False, comment="售前工单ID")
    requirement_analysis_id = Column(
        Integer,
        ForeignKey("presale_ai_requirement_analysis.id")
    )

    # === 【新增】当前版本 ===
    current_version_id = Column(
        Integer,
        ForeignKey("solution_versions.id"),
        comment="当前生效版本ID"
    )

    # === 模板匹配结果（保留）===
    matched_template_ids = Column(JSON, comment="匹配的模板ID列表")

    # === 以下字段迁移到 SolutionVersion ===
    # generated_solution → SolutionVersion
    # architecture_diagram → SolutionVersion
    # bom_list → SolutionVersion
    # estimated_cost → 从绑定的 CostEstimation 获取
    # cost_breakdown → 从绑定的 CostEstimation 获取

    # === 保留：创建信息 ===
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # === 关系 ===
    versions = relationship(
        "SolutionVersion",
        back_populates="solution",
        cascade="all, delete-orphan",
        foreign_keys="SolutionVersion.solution_id"
    )
    current_version = relationship(
        "SolutionVersion",
        foreign_keys=[current_version_id],
        post_update=True
    )
```

---

## 四、迁移策略

### 4.1 数据迁移步骤

```sql
-- Step 1: 创建新表 solution_versions
CREATE TABLE solution_versions (...);

-- Step 2: 迁移现有方案数据到版本表
INSERT INTO solution_versions (
    solution_id, version_no, generated_solution, architecture_diagram,
    bom_list, technical_parameters, status, created_by, created_at
)
SELECT
    id, 'V1.0', generated_solution, architecture_diagram,
    bom_list, technical_parameters,
    CASE status WHEN 'approved' THEN 'approved' ELSE 'draft' END,
    created_by, created_at
FROM presale_ai_solution;

-- Step 3: 更新 presale_ai_solution.current_version_id
UPDATE presale_ai_solution s
SET current_version_id = (
    SELECT id FROM solution_versions sv
    WHERE sv.solution_id = s.id
    ORDER BY sv.created_at DESC LIMIT 1
);

-- Step 4: 为现有 CostEstimation 关联 SolutionVersion
UPDATE presale_ai_cost_estimation ce
SET solution_version_id = (
    SELECT sv.id FROM solution_versions sv
    WHERE sv.solution_id = ce.solution_id
    ORDER BY sv.created_at DESC LIMIT 1
)
WHERE ce.solution_id IS NOT NULL;

-- Step 5: 为现有 QuoteVersion 创建绑定关系
-- 注意：这一步需要人工审核，因为历史数据可能无法自动匹配
ALTER TABLE quote_versions
ADD COLUMN solution_version_id INTEGER,
ADD COLUMN cost_estimation_id INTEGER;

-- 尝试通过 opportunity_id 关联
UPDATE quote_versions qv
SET solution_version_id = (
    SELECT sv.id FROM solution_versions sv
    JOIN presale_ai_solution s ON sv.solution_id = s.id
    JOIN quotes q ON qv.quote_id = q.id
    WHERE s.presale_ticket_id = (
        -- 通过商机找到售前工单（需要根据实际关联逻辑调整）
        SELECT presale_ticket_id FROM opportunities WHERE id = q.opportunity_id
    )
    ORDER BY sv.created_at DESC LIMIT 1
);
```

### 4.2 迁移脚本

```python
# migrations/versions/20260312_add_solution_version_binding.py

"""add solution version and cost binding

Revision ID: 20260312_binding
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    # 1. 创建 solution_versions 表
    op.create_table(
        'solution_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('solution_id', sa.Integer(), nullable=False),
        sa.Column('version_no', sa.String(20), nullable=False),
        sa.Column('generated_solution', sa.JSON(), nullable=True),
        sa.Column('architecture_diagram', sa.Text(), nullable=True),
        sa.Column('topology_diagram', sa.Text(), nullable=True),
        sa.Column('signal_flow_diagram', sa.Text(), nullable=True),
        sa.Column('bom_list', sa.JSON(), nullable=True),
        sa.Column('technical_parameters', sa.JSON(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('change_reason', sa.String(200), nullable=True),
        sa.Column('parent_version_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approval_comments', sa.Text(), nullable=True),
        sa.Column('ai_model_used', sa.String(100), nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('quality_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['solution_id'], ['presale_ai_solution.id']),
        sa.ForeignKeyConstraint(['parent_version_id'], ['solution_versions.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('solution_id', 'version_no', name='uq_solution_version'),
    )
    op.create_index('idx_sv_solution_id', 'solution_versions', ['solution_id'])
    op.create_index('idx_sv_status', 'solution_versions', ['status'])

    # 2. 添加 presale_ai_solution.current_version_id
    op.add_column(
        'presale_ai_solution',
        sa.Column('current_version_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_solution_current_version',
        'presale_ai_solution', 'solution_versions',
        ['current_version_id'], ['id']
    )

    # 3. 添加 presale_ai_cost_estimation 新字段
    op.add_column(
        'presale_ai_cost_estimation',
        sa.Column('solution_version_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'presale_ai_cost_estimation',
        sa.Column('version_no', sa.String(20), default='V1')
    )
    op.add_column(
        'presale_ai_cost_estimation',
        sa.Column('status', sa.String(20), default='draft')
    )
    op.add_column(
        'presale_ai_cost_estimation',
        sa.Column('approved_by', sa.Integer(), nullable=True)
    )
    op.add_column(
        'presale_ai_cost_estimation',
        sa.Column('approved_at', sa.DateTime(), nullable=True)
    )
    op.create_index(
        'idx_ce_solution_version',
        'presale_ai_cost_estimation',
        ['solution_version_id']
    )

    # 4. 添加 quote_versions 新字段
    op.add_column(
        'quote_versions',
        sa.Column('solution_version_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'quote_versions',
        sa.Column('cost_estimation_id', sa.Integer(), nullable=True)
    )
    op.add_column(
        'quote_versions',
        sa.Column('binding_status', sa.String(20), default='valid')
    )
    op.add_column(
        'quote_versions',
        sa.Column('binding_validated_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'quote_versions',
        sa.Column('binding_warning', sa.Text(), nullable=True)
    )
    op.create_index(
        'idx_qv_solution_version',
        'quote_versions',
        ['solution_version_id']
    )
    op.create_index(
        'idx_qv_cost_estimation',
        'quote_versions',
        ['cost_estimation_id']
    )


def downgrade():
    # 回滚（注意：数据迁移不可逆）
    op.drop_index('idx_qv_cost_estimation', 'quote_versions')
    op.drop_index('idx_qv_solution_version', 'quote_versions')
    op.drop_column('quote_versions', 'binding_warning')
    op.drop_column('quote_versions', 'binding_validated_at')
    op.drop_column('quote_versions', 'binding_status')
    op.drop_column('quote_versions', 'cost_estimation_id')
    op.drop_column('quote_versions', 'solution_version_id')

    op.drop_index('idx_ce_solution_version', 'presale_ai_cost_estimation')
    op.drop_column('presale_ai_cost_estimation', 'approved_at')
    op.drop_column('presale_ai_cost_estimation', 'approved_by')
    op.drop_column('presale_ai_cost_estimation', 'status')
    op.drop_column('presale_ai_cost_estimation', 'version_no')
    op.drop_column('presale_ai_cost_estimation', 'solution_version_id')

    op.drop_constraint('fk_solution_current_version', 'presale_ai_solution')
    op.drop_column('presale_ai_solution', 'current_version_id')

    op.drop_index('idx_sv_status', 'solution_versions')
    op.drop_index('idx_sv_solution_id', 'solution_versions')
    op.drop_table('solution_versions')
```

---

## 五、服务层变更

### 5.1 新建服务：SolutionVersionService

```python
# app/services/sales/solution_version_service.py

class SolutionVersionService:
    """方案版本服务"""

    def __init__(self, db: Session):
        self.db = db

    async def create_version(
        self,
        solution_id: int,
        content: SolutionVersionCreate,
        created_by: int
    ) -> SolutionVersion:
        """创建新版本

        规则：
        1. 自动计算版本号（V1.0, V1.1, V2.0...）
        2. 主版本号：approved 状态变更时递增
        3. 次版本号：draft 状态下递增
        """
        # 获取最新版本号
        latest = self._get_latest_version(solution_id)
        version_no = self._calculate_next_version(latest)

        version = SolutionVersion(
            solution_id=solution_id,
            version_no=version_no,
            parent_version_id=latest.id if latest else None,
            **content.dict(),
            created_by=created_by
        )
        self.db.add(version)
        self.db.commit()

        return version

    async def approve_version(
        self,
        version_id: int,
        approved_by: int,
        comments: str = None
    ) -> SolutionVersion:
        """审批版本

        审批通过后：
        1. 更新 solution.current_version_id
        2. 触发成本重估提醒（如果绑定的成本估算已过期）
        """
        version = self.db.query(SolutionVersion).get(version_id)
        if version.status != "pending_review":
            raise ValueError("只能审批待审核状态的版本")

        version.status = "approved"
        version.approved_by = approved_by
        version.approved_at = datetime.now()
        version.approval_comments = comments

        # 更新主表当前版本
        solution = self.db.query(PresaleAISolution).get(version.solution_id)
        solution.current_version_id = version.id

        self.db.commit()

        # 触发绑定检查
        await self._check_cost_binding_freshness(version)

        return version

    async def _check_cost_binding_freshness(self, version: SolutionVersion):
        """检查绑定的成本估算是否需要更新"""
        old_estimations = (
            self.db.query(PresaleAICostEstimation)
            .filter(PresaleAICostEstimation.solution_version_id == version.parent_version_id)
            .all()
        )

        if old_estimations:
            # 发送提醒：方案已更新，成本估算可能需要重估
            # TODO: 集成通知服务
            pass
```

### 5.2 重构服务：BindingValidationService

```python
# app/services/sales/binding_validation_service.py

class BindingValidationService:
    """绑定验证服务

    确保 方案-成本-报价 三位一体绑定的一致性
    """

    def __init__(self, db: Session):
        self.db = db

    async def validate_quote_binding(
        self,
        quote_version_id: int
    ) -> BindingValidationResult:
        """验证报价版本的绑定状态

        检查项：
        1. 方案版本是否已审批
        2. 成本估算是否已审批
        3. 成本估算是否绑定正确的方案版本
        4. 报价金额是否与成本一致
        """
        qv = self.db.query(QuoteVersion).get(quote_version_id)

        issues = []

        # 检查方案版本
        if not qv.solution_version_id:
            issues.append(BindingIssue(
                level="error",
                code="SOLUTION_NOT_BOUND",
                message="报价未绑定方案版本"
            ))
        else:
            sv = qv.solution_version
            if sv.status != "approved":
                issues.append(BindingIssue(
                    level="warning",
                    code="SOLUTION_NOT_APPROVED",
                    message=f"方案版本 {sv.version_no} 未审批"
                ))

        # 检查成本估算
        if not qv.cost_estimation_id:
            issues.append(BindingIssue(
                level="error",
                code="COST_NOT_BOUND",
                message="报价未绑定成本估算"
            ))
        else:
            ce = qv.cost_estimation
            if ce.status != "approved":
                issues.append(BindingIssue(
                    level="warning",
                    code="COST_NOT_APPROVED",
                    message="成本估算未审批"
                ))

            # 检查成本估算是否绑定正确的方案版本
            if ce.solution_version_id != qv.solution_version_id:
                issues.append(BindingIssue(
                    level="error",
                    code="COST_SOLUTION_MISMATCH",
                    message="成本估算绑定的方案版本与报价不一致"
                ))

            # 检查金额一致性
            if qv.cost_total and qv.cost_total != ce.total_cost:
                issues.append(BindingIssue(
                    level="error",
                    code="COST_AMOUNT_MISMATCH",
                    message=f"报价成本 {qv.cost_total} 与估算成本 {ce.total_cost} 不一致"
                ))

        # 更新绑定状态
        if any(i.level == "error" for i in issues):
            qv.binding_status = "invalid"
        elif issues:
            qv.binding_status = "outdated"
        else:
            qv.binding_status = "valid"

        qv.binding_validated_at = datetime.now()
        qv.binding_warning = "\n".join(i.message for i in issues) if issues else None

        self.db.commit()

        return BindingValidationResult(
            quote_version_id=quote_version_id,
            status=qv.binding_status,
            issues=issues,
            validated_at=qv.binding_validated_at
        )

    async def sync_cost_to_quote(
        self,
        quote_version_id: int
    ) -> QuoteVersion:
        """同步成本到报价

        从绑定的 CostEstimation 同步 cost_total 到 QuoteVersion
        并重新计算毛利率
        """
        qv = self.db.query(QuoteVersion).get(quote_version_id)
        ce = qv.cost_estimation

        if not ce:
            raise ValueError("报价未绑定成本估算")

        qv.cost_total = ce.total_cost

        # 重新计算毛利率
        if qv.total_price and qv.cost_total:
            qv.gross_margin = (
                (qv.total_price - qv.cost_total) / qv.total_price * 100
            )

        qv.binding_status = "valid"
        qv.binding_validated_at = datetime.now()
        qv.binding_warning = None

        self.db.commit()

        return qv
```

---

## 六、API 变更

### 6.1 新增 API

```python
# app/api/v1/solution_versions.py

@router.post("/solutions/{solution_id}/versions")
async def create_solution_version(
    solution_id: int,
    content: SolutionVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建方案新版本"""
    service = SolutionVersionService(db)
    return await service.create_version(solution_id, content, current_user.id)


@router.post("/solution-versions/{version_id}/approve")
async def approve_solution_version(
    version_id: int,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审批方案版本"""
    service = SolutionVersionService(db)
    return await service.approve_version(
        version_id, current_user.id, request.comments
    )


@router.get("/solution-versions/{version_id}/cost-estimations")
async def get_version_cost_estimations(
    version_id: int,
    db: Session = Depends(get_db)
):
    """获取方案版本关联的成本估算"""
    return (
        db.query(PresaleAICostEstimation)
        .filter(PresaleAICostEstimation.solution_version_id == version_id)
        .all()
    )


@router.post("/quote-versions/{version_id}/validate-binding")
async def validate_quote_binding(
    version_id: int,
    db: Session = Depends(get_db)
):
    """验证报价绑定状态"""
    service = BindingValidationService(db)
    return await service.validate_quote_binding(version_id)


@router.post("/quote-versions/{version_id}/sync-cost")
async def sync_cost_to_quote(
    version_id: int,
    db: Session = Depends(get_db)
):
    """同步成本到报价"""
    service = BindingValidationService(db)
    return await service.sync_cost_to_quote(version_id)
```

### 6.2 修改现有 API

```python
# app/api/v1/quotes.py（修改）

@router.post("/quotes/{quote_id}/versions")
async def create_quote_version(
    quote_id: int,
    request: QuoteVersionCreateRequest,  # 新增必填字段
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建报价版本（修改版）

    必填参数：
    - solution_version_id: 方案版本ID
    - cost_estimation_id: 成本估算ID
    """
    # 验证绑定关系
    ce = db.query(PresaleAICostEstimation).get(request.cost_estimation_id)
    if ce.solution_version_id != request.solution_version_id:
        raise HTTPException(
            status_code=400,
            detail="成本估算绑定的方案版本与指定的方案版本不一致"
        )

    # 创建报价版本
    qv = QuoteVersion(
        quote_id=quote_id,
        solution_version_id=request.solution_version_id,
        cost_estimation_id=request.cost_estimation_id,
        cost_total=ce.total_cost,  # 自动同步
        **request.dict(exclude={'solution_version_id', 'cost_estimation_id'})
    )

    db.add(qv)
    db.commit()

    return qv
```

---

## 七、实施计划

### 7.1 阶段划分

| 阶段 | 任务 | 工时 | 依赖 |
|------|------|------|------|
| **Phase 1** | 创建 SolutionVersion 模型和迁移 | 8h | - |
| **Phase 2** | 重构 CostEstimation 模型 | 4h | Phase 1 |
| **Phase 3** | 重构 QuoteVersion 模型 | 4h | Phase 1 |
| **Phase 4** | 数据迁移脚本开发和执行 | 8h | Phase 1-3 |
| **Phase 5** | 服务层开发 | 4h | Phase 4 |
| **Phase 6** | API 变更和测试 | 4h | Phase 5 |

**总计**：32h

### 7.2 文件清单

**新建文件**：
- `app/models/sales/solution_version.py` - 方案版本模型
- `app/services/sales/solution_version_service.py` - 方案版本服务
- `app/services/sales/binding_validation_service.py` - 绑定验证服务
- `app/schemas/sales/solution_version.py` - Schema 定义
- `app/api/v1/solution_versions.py` - API 路由
- `migrations/versions/20260312_add_solution_version_binding.py` - 迁移脚本

**修改文件**：
- `app/models/presale_ai_solution.py` - 添加 current_version_id
- `app/models/sales/presale_ai_cost.py` - 添加 solution_version_id
- `app/models/sales/quotes.py` - QuoteVersion 添加绑定字段
- `app/api/v1/quotes.py` - 修改创建报价版本 API
- `app/services/sales/ai_cost_estimation_service.py` - 绑定方案版本

---

## 八、验证方案

### 8.1 单元测试

```python
# tests/unit/services/sales/test_binding_validation.py

class TestBindingValidation:
    """绑定验证测试"""

    def test_valid_binding(self, db, sample_data):
        """完整绑定应通过验证"""
        qv = create_quote_version_with_binding(db)

        service = BindingValidationService(db)
        result = service.validate_quote_binding(qv.id)

        assert result.status == "valid"
        assert len(result.issues) == 0

    def test_missing_cost_binding(self, db):
        """缺少成本绑定应报错"""
        qv = QuoteVersion(cost_estimation_id=None, ...)

        result = service.validate_quote_binding(qv.id)

        assert result.status == "invalid"
        assert any(i.code == "COST_NOT_BOUND" for i in result.issues)

    def test_cost_solution_mismatch(self, db):
        """成本与方案不匹配应报错"""
        sv1 = create_solution_version(db)
        sv2 = create_solution_version(db)
        ce = create_cost_estimation(db, solution_version_id=sv1.id)
        qv = create_quote_version(db, solution_version_id=sv2.id, cost_estimation_id=ce.id)

        result = service.validate_quote_binding(qv.id)

        assert result.status == "invalid"
        assert any(i.code == "COST_SOLUTION_MISMATCH" for i in result.issues)
```

### 8.2 集成测试

```python
# tests/integration/test_cost_solution_quote_flow.py

async def test_full_flow(db):
    """完整流程测试：方案 → 成本 → 报价"""

    # 1. 创建方案并审批
    solution = await create_solution(db)
    sv = await create_solution_version(db, solution.id)
    await approve_solution_version(db, sv.id)

    # 2. 基于方案版本创建成本估算
    ce = await create_cost_estimation(db, solution_version_id=sv.id)
    await approve_cost_estimation(db, ce.id)

    # 3. 基于方案版本和成本估算创建报价
    quote = await create_quote(db)
    qv = await create_quote_version(
        db,
        quote_id=quote.id,
        solution_version_id=sv.id,
        cost_estimation_id=ce.id
    )

    # 4. 验证绑定
    result = await validate_quote_binding(db, qv.id)
    assert result.status == "valid"
    assert qv.cost_total == ce.total_cost
```

---

## 九、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 历史数据迁移失败 | 🔴 高 | 分批迁移，保留原字段作为备份 |
| API 破坏性变更 | 🟡 中 | 使用版本化 API，新旧并存过渡期 |
| 性能下降（多表关联） | 🟡 中 | 添加索引，使用 joinedload |
| 团队培训成本 | 🟡 中 | 编写操作手册和培训文档 |

---

## 十、预期收益

| 指标 | 改进前 | 改进后 |
|------|--------|--------|
| 方案版本追溯 | ❌ 不可追溯 | ✅ 完整版本历史 |
| 成本-报价一致性 | ❌ 手工维护 | ✅ 自动验证 |
| 变更影响分析 | ❌ 无法分析 | ✅ 级联提醒 |
| 审计合规 | ❌ 无审计轨迹 | ✅ 完整审计链 |
| 报价准确率 | 基准 | 预计 +15% |
