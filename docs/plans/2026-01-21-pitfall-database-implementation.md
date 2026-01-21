# Pitfall Database Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an independent pitfall knowledge base module for capturing, searching, and recommending project lessons learned.

**Architecture:** Lightweight integration approach - independent Pitfall model with event-based recommendations. Loose coupling with existing project/stage systems via event handlers.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, SQLite/MySQL

---

## Phase P0: Data Model + Basic CRUD

### Task 1: Create Pitfall Enums

**Files:**
- Create: `app/models/enums/pitfall.py`
- Modify: `app/models/enums/__init__.py`

**Step 1: Write the enum file**

```python
# app/models/enums/pitfall.py
# -*- coding: utf-8 -*-
"""
踩坑库枚举定义
"""

from enum import Enum


class PitfallStage(str, Enum):
    """踩坑发生阶段"""
    S1 = "S1"  # 需求进入
    S2 = "S2"  # 方案设计
    S3 = "S3"  # 采购备料
    S4 = "S4"  # 加工制造
    S5 = "S5"  # 装配调试
    S6 = "S6"  # 出厂验收
    S7 = "S7"  # 包装发运
    S8 = "S8"  # 现场安装
    S9 = "S9"  # 质保结项


class PitfallEquipmentType(str, Enum):
    """设备类型"""
    ICT = "ICT"          # ICT测试设备
    FCT = "FCT"          # FCT测试设备
    EOL = "EOL"          # EOL测试设备
    BURNING = "BURNING"  # 烧录设备
    AGING = "AGING"      # 老化设备
    VISION = "VISION"    # 视觉检测设备
    ASSEMBLY = "ASSEMBLY"  # 自动化组装线
    OTHER = "OTHER"      # 其他


class PitfallProblemType(str, Enum):
    """问题类型"""
    TECHNICAL = "TECHNICAL"    # 技术问题
    SUPPLIER = "SUPPLIER"      # 供应商问题
    COMMUNICATION = "COMMUNICATION"  # 沟通问题
    SCHEDULE = "SCHEDULE"      # 进度问题
    COST = "COST"              # 成本问题
    QUALITY = "QUALITY"        # 质量问题
    OTHER = "OTHER"            # 其他


class PitfallSourceType(str, Enum):
    """踩坑来源"""
    REALTIME = "REALTIME"      # 实时录入
    STAGE_END = "STAGE_END"    # 阶段结束录入
    REVIEW = "REVIEW"          # 复盘导入
    ECN = "ECN"                # ECN关联
    ISSUE = "ISSUE"            # Issue关联


class PitfallStatus(str, Enum):
    """踩坑状态"""
    DRAFT = "DRAFT"            # 草稿
    PUBLISHED = "PUBLISHED"    # 已发布
    ARCHIVED = "ARCHIVED"      # 已归档


class PitfallSensitiveReason(str, Enum):
    """敏感原因"""
    CUSTOMER = "CUSTOMER"      # 涉及客户信息
    COST = "COST"              # 涉及成本/报价
    SUPPLIER = "SUPPLIER"      # 涉及供应商问题
    OTHER = "OTHER"            # 其他


class RecommendationTriggerType(str, Enum):
    """推荐触发类型"""
    PROJECT_CREATE = "PROJECT_CREATE"  # 项目创建
    STAGE_CHANGE = "STAGE_CHANGE"      # 阶段切换
    KEYWORD = "KEYWORD"                # 关键字触发
    MANUAL = "MANUAL"                  # 手动搜索
```

**Step 2: Export enums in __init__.py**

Add to `app/models/enums/__init__.py`:

```python
from .pitfall import (
    PitfallStage,
    PitfallEquipmentType,
    PitfallProblemType,
    PitfallSourceType,
    PitfallStatus,
    PitfallSensitiveReason,
    RecommendationTriggerType,
)
```

**Step 3: Commit**

```bash
git add app/models/enums/pitfall.py app/models/enums/__init__.py
git commit -m "feat(pitfall): add pitfall enum definitions"
```

---

### Task 2: Create Pitfall Model

**Files:**
- Create: `app/models/pitfall.py`
- Modify: `app/models/__init__.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_pitfall_model.py
# -*- coding: utf-8 -*-
"""踩坑模型单元测试"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.models.pitfall import Pitfall, PitfallRecommendation, PitfallLearningProgress


class TestPitfallModel:
    """踩坑记录模型测试"""

    def test_create_pitfall_minimal(self):
        """测试创建最小踩坑记录"""
        pitfall = Pitfall(
            pitfall_no="PF260121001",
            title="伺服电机选型功率不足",
            description="项目使用200W伺服电机，实际负载需要400W",
        )
        assert pitfall.pitfall_no == "PF260121001"
        assert pitfall.title == "伺服电机选型功率不足"
        assert pitfall.status == "DRAFT"
        assert pitfall.verified is False
        assert pitfall.verify_count == 0

    def test_create_pitfall_full(self):
        """测试创建完整踩坑记录"""
        pitfall = Pitfall(
            pitfall_no="PF260121002",
            title="供应商交期延迟",
            description="某供应商承诺2周交货，实际4周",
            solution="更换备选供应商",
            stage="S3",
            equipment_type="FCT",
            problem_type="SUPPLIER",
            tags=["供应商A", "交期"],
            root_cause="供应商产能不足",
            impact="项目延期1周",
            prevention="建立供应商备选库",
            cost_impact=Decimal("5000.00"),
            schedule_impact=7,
            source_type="REALTIME",
            source_project_id=1,
            is_sensitive=True,
            sensitive_reason="SUPPLIER",
            created_by=1,
        )
        assert pitfall.stage == "S3"
        assert pitfall.equipment_type == "FCT"
        assert pitfall.cost_impact == Decimal("5000.00")
        assert pitfall.is_sensitive is True


class TestPitfallRecommendationModel:
    """推荐记录模型测试"""

    def test_create_recommendation(self):
        """测试创建推荐记录"""
        rec = PitfallRecommendation(
            pitfall_id=1,
            project_id=2,
            trigger_type="PROJECT_CREATE",
            trigger_context={"customer_name": "XX公司", "equipment_type": "FCT"},
        )
        assert rec.trigger_type == "PROJECT_CREATE"
        assert rec.is_helpful is None


class TestPitfallLearningProgressModel:
    """学习进度模型测试"""

    def test_create_learning_progress(self):
        """测试创建学习进度"""
        progress = PitfallLearningProgress(
            user_id=1,
            pitfall_id=1,
            read_at=datetime.now(),
            is_marked=True,
            notes="重要教训，需要注意",
        )
        assert progress.is_marked is True
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_pitfall_model.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.pitfall'"

**Step 3: Write the model**

```python
# app/models/pitfall.py
# -*- coding: utf-8 -*-
"""
踩坑库 ORM 模型
包含：踩坑记录、推荐记录、学习进度
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Pitfall(Base, TimestampMixin):
    """踩坑记录表"""
    __tablename__ = 'pitfalls'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    pitfall_no = Column(String(50), unique=True, nullable=False, comment='踩坑编号')

    # === 必填字段（降低录入门槛）===
    title = Column(String(200), nullable=False, comment='标题')
    description = Column(Text, nullable=False, comment='问题描述')
    solution = Column(Text, comment='解决方案')

    # === 多维度分类 ===
    stage = Column(String(20), comment='阶段：S1-S9')
    equipment_type = Column(String(50), comment='设备类型')
    problem_type = Column(String(50), comment='问题类型')
    tags = Column(JSON, comment='标签列表')

    # === 选填字段（逐步完善）===
    root_cause = Column(Text, comment='根因分析')
    impact = Column(Text, comment='影响范围')
    prevention = Column(Text, comment='预防措施')
    cost_impact = Column(Numeric(12, 2), comment='成本影响（元）')
    schedule_impact = Column(Integer, comment='工期影响（天）')

    # === 来源追溯 ===
    source_type = Column(String(20), comment='来源类型')
    source_project_id = Column(Integer, ForeignKey('projects.id'), comment='来源项目ID')
    source_ecn_id = Column(Integer, comment='关联ECN ID')
    source_issue_id = Column(Integer, comment='关联Issue ID')

    # === 权限与状态 ===
    is_sensitive = Column(Boolean, default=False, comment='是否敏感')
    sensitive_reason = Column(String(50), comment='敏感原因')
    visible_to = Column(JSON, comment='可见范围（敏感记录）')
    status = Column(String(20), default='DRAFT', comment='状态')
    verified = Column(Boolean, default=False, comment='是否已验证')
    verify_count = Column(Integer, default=0, comment='验证次数')

    # === 创建人 ===
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # === 关系 ===
    source_project = relationship('Project', foreign_keys=[source_project_id])
    creator = relationship('User', foreign_keys=[created_by])
    recommendations = relationship('PitfallRecommendation', back_populates='pitfall')
    learning_progress = relationship('PitfallLearningProgress', back_populates='pitfall')

    __table_args__ = (
        Index('idx_pitfall_stage', 'stage'),
        Index('idx_pitfall_equipment', 'equipment_type'),
        Index('idx_pitfall_problem', 'problem_type'),
        Index('idx_pitfall_status', 'status'),
        Index('idx_pitfall_project', 'source_project_id'),
        Index('idx_pitfall_created_by', 'created_by'),
        {'comment': '踩坑记录表'}
    )

    def __repr__(self):
        return f'<Pitfall {self.pitfall_no}: {self.title}>'


class PitfallRecommendation(Base, TimestampMixin):
    """踩坑推荐记录表"""
    __tablename__ = 'pitfall_recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    pitfall_id = Column(Integer, ForeignKey('pitfalls.id'), nullable=False, comment='踩坑ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    trigger_type = Column(String(20), nullable=False, comment='触发类型')
    trigger_context = Column(JSON, comment='触发上下文')

    is_helpful = Column(Boolean, comment='是否有帮助')
    feedback = Column(Text, comment='反馈详情')

    # === 关系 ===
    pitfall = relationship('Pitfall', back_populates='recommendations')
    project = relationship('Project')

    __table_args__ = (
        Index('idx_pitfall_rec_project', 'project_id'),
        Index('idx_pitfall_rec_pitfall', 'pitfall_id'),
        {'comment': '踩坑推荐记录表'}
    )

    def __repr__(self):
        return f'<PitfallRecommendation pitfall={self.pitfall_id} project={self.project_id}>'


class PitfallLearningProgress(Base, TimestampMixin):
    """踩坑学习进度表"""
    __tablename__ = 'pitfall_learning_progress'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    pitfall_id = Column(Integer, ForeignKey('pitfalls.id'), nullable=False, comment='踩坑ID')

    read_at = Column(DateTime, comment='阅读时间')
    is_marked = Column(Boolean, default=False, comment='是否标记已掌握')
    notes = Column(Text, comment='学习笔记')

    # === 关系 ===
    user = relationship('User')
    pitfall = relationship('Pitfall', back_populates='learning_progress')

    __table_args__ = (
        Index('idx_pitfall_learn_user', 'user_id'),
        Index('idx_pitfall_learn_pitfall', 'pitfall_id'),
        {'comment': '踩坑学习进度表'}
    )

    def __repr__(self):
        return f'<PitfallLearningProgress user={self.user_id} pitfall={self.pitfall_id}>'
```

**Step 4: Export in models/__init__.py**

Add to `app/models/__init__.py`:

```python
from .pitfall import (
    Pitfall,
    PitfallRecommendation,
    PitfallLearningProgress,
)
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/unit/test_pitfall_model.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add app/models/pitfall.py app/models/__init__.py tests/unit/test_pitfall_model.py
git commit -m "feat(pitfall): add Pitfall, PitfallRecommendation, PitfallLearningProgress models"
```

---

### Task 3: Create Database Migration

**Files:**
- Create: `migrations/20260121_pitfall_sqlite.sql`

**Step 1: Write the migration file**

```sql
-- migrations/20260121_pitfall_sqlite.sql
-- 踩坑库数据库迁移

-- 踩坑记录表
CREATE TABLE IF NOT EXISTS pitfalls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitfall_no VARCHAR(50) UNIQUE NOT NULL,

    -- 必填字段
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    solution TEXT,

    -- 多维度分类
    stage VARCHAR(20),
    equipment_type VARCHAR(50),
    problem_type VARCHAR(50),
    tags JSON,

    -- 选填字段
    root_cause TEXT,
    impact TEXT,
    prevention TEXT,
    cost_impact DECIMAL(12,2),
    schedule_impact INTEGER,

    -- 来源追溯
    source_type VARCHAR(20),
    source_project_id INTEGER REFERENCES projects(id),
    source_ecn_id INTEGER,
    source_issue_id INTEGER,

    -- 权限与状态
    is_sensitive BOOLEAN DEFAULT FALSE,
    sensitive_reason VARCHAR(50),
    visible_to JSON,
    status VARCHAR(20) DEFAULT 'DRAFT',
    verified BOOLEAN DEFAULT FALSE,
    verify_count INTEGER DEFAULT 0,

    -- 创建人
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pitfall_stage ON pitfalls(stage);
CREATE INDEX IF NOT EXISTS idx_pitfall_equipment ON pitfalls(equipment_type);
CREATE INDEX IF NOT EXISTS idx_pitfall_problem ON pitfalls(problem_type);
CREATE INDEX IF NOT EXISTS idx_pitfall_status ON pitfalls(status);
CREATE INDEX IF NOT EXISTS idx_pitfall_project ON pitfalls(source_project_id);
CREATE INDEX IF NOT EXISTS idx_pitfall_created_by ON pitfalls(created_by);

-- 推荐记录表
CREATE TABLE IF NOT EXISTS pitfall_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitfall_id INTEGER NOT NULL REFERENCES pitfalls(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),

    trigger_type VARCHAR(20) NOT NULL,
    trigger_context JSON,

    is_helpful BOOLEAN,
    feedback TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pitfall_rec_project ON pitfall_recommendations(project_id);
CREATE INDEX IF NOT EXISTS idx_pitfall_rec_pitfall ON pitfall_recommendations(pitfall_id);

-- 学习进度表
CREATE TABLE IF NOT EXISTS pitfall_learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    pitfall_id INTEGER NOT NULL REFERENCES pitfalls(id),

    read_at DATETIME,
    is_marked BOOLEAN DEFAULT FALSE,
    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, pitfall_id)
);

CREATE INDEX IF NOT EXISTS idx_pitfall_learn_user ON pitfall_learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_pitfall_learn_pitfall ON pitfall_learning_progress(pitfall_id);
```

**Step 2: Commit**

```bash
git add migrations/20260121_pitfall_sqlite.sql
git commit -m "feat(pitfall): add database migration for pitfall tables"
```

---

### Task 4: Create Pydantic Schemas

**Files:**
- Create: `app/schemas/pitfall.py`
- Modify: `app/schemas/__init__.py`

**Step 1: Write the schemas**

```python
# app/schemas/pitfall.py
# -*- coding: utf-8 -*-
"""
踩坑库 Pydantic Schema
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 踩坑记录 ====================

class PitfallCreate(BaseModel):
    """创建踩坑记录"""
    title: str = Field(..., max_length=200, description="标题")
    description: str = Field(..., description="问题描述")
    solution: Optional[str] = Field(None, description="解决方案")

    # 多维度分类
    stage: Optional[str] = Field(None, description="阶段：S1-S9")
    equipment_type: Optional[str] = Field(None, description="设备类型")
    problem_type: Optional[str] = Field(None, description="问题类型")
    tags: Optional[List[str]] = Field(None, description="标签列表")

    # 选填字段
    root_cause: Optional[str] = Field(None, description="根因分析")
    impact: Optional[str] = Field(None, description="影响范围")
    prevention: Optional[str] = Field(None, description="预防措施")
    cost_impact: Optional[Decimal] = Field(None, description="成本影响（元）")
    schedule_impact: Optional[int] = Field(None, description="工期影响（天）")

    # 来源追溯
    source_type: Optional[str] = Field(None, description="来源类型")
    source_project_id: Optional[int] = Field(None, description="来源项目ID")
    source_ecn_id: Optional[int] = Field(None, description="关联ECN ID")
    source_issue_id: Optional[int] = Field(None, description="关联Issue ID")

    # 权限
    is_sensitive: bool = Field(False, description="是否敏感")
    sensitive_reason: Optional[str] = Field(None, description="敏感原因")
    visible_to: Optional[List[int]] = Field(None, description="可见范围")


class PitfallUpdate(BaseModel):
    """更新踩坑记录"""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    solution: Optional[str] = None

    stage: Optional[str] = None
    equipment_type: Optional[str] = None
    problem_type: Optional[str] = None
    tags: Optional[List[str]] = None

    root_cause: Optional[str] = None
    impact: Optional[str] = None
    prevention: Optional[str] = None
    cost_impact: Optional[Decimal] = None
    schedule_impact: Optional[int] = None

    is_sensitive: Optional[bool] = None
    sensitive_reason: Optional[str] = None
    visible_to: Optional[List[int]] = None

    status: Optional[str] = None


class PitfallResponse(BaseModel):
    """踩坑记录响应"""
    id: int
    pitfall_no: str
    title: str
    description: str
    solution: Optional[str]

    stage: Optional[str]
    equipment_type: Optional[str]
    problem_type: Optional[str]
    tags: Optional[List[str]]

    root_cause: Optional[str]
    impact: Optional[str]
    prevention: Optional[str]
    cost_impact: Optional[Decimal]
    schedule_impact: Optional[int]

    source_type: Optional[str]
    source_project_id: Optional[int]

    is_sensitive: bool
    status: str
    verified: bool
    verify_count: int

    created_by: Optional[int]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PitfallListItem(BaseModel):
    """踩坑列表项（精简）"""
    id: int
    pitfall_no: str
    title: str
    stage: Optional[str]
    equipment_type: Optional[str]
    problem_type: Optional[str]
    tags: Optional[List[str]]
    status: str
    verified: bool
    verify_count: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== 推荐记录 ====================

class RecommendationFeedback(BaseModel):
    """推荐反馈"""
    is_helpful: bool = Field(..., description="是否有帮助")
    feedback: Optional[str] = Field(None, description="反馈详情")


class RecommendationResponse(BaseModel):
    """推荐响应"""
    id: int
    pitfall_id: int
    pitfall: PitfallListItem
    trigger_type: str
    relevance_score: Optional[float] = Field(None, description="相关度分数")

    class Config:
        from_attributes = True


# ==================== 搜索与筛选 ====================

class PitfallSearchParams(BaseModel):
    """搜索参数"""
    keyword: Optional[str] = Field(None, description="关键词")
    stage: Optional[str] = Field(None, description="阶段筛选")
    equipment_type: Optional[str] = Field(None, description="设备类型筛选")
    problem_type: Optional[str] = Field(None, description="问题类型筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    status: Optional[str] = Field(None, description="状态筛选")
    verified_only: bool = Field(False, description="仅显示已验证")


# ==================== 学习进度 ====================

class LearningProgressCreate(BaseModel):
    """标记学习"""
    notes: Optional[str] = Field(None, description="学习笔记")


class LearningProgressResponse(BaseModel):
    """学习进度响应"""
    id: int
    user_id: int
    pitfall_id: int
    read_at: Optional[datetime]
    is_marked: bool
    notes: Optional[str]

    class Config:
        from_attributes = True
```

**Step 2: Export in schemas/__init__.py**

Add to `app/schemas/__init__.py`:

```python
from .pitfall import (
    PitfallCreate,
    PitfallUpdate,
    PitfallResponse,
    PitfallListItem,
    PitfallSearchParams,
    RecommendationFeedback,
    RecommendationResponse,
    LearningProgressCreate,
    LearningProgressResponse,
)
```

**Step 3: Commit**

```bash
git add app/schemas/pitfall.py app/schemas/__init__.py
git commit -m "feat(pitfall): add Pydantic schemas for pitfall API"
```

---

### Task 5: Create Pitfall Service

**Files:**
- Create: `app/services/pitfall/__init__.py`
- Create: `app/services/pitfall/pitfall_service.py`

**Step 1: Write the failing test**

```python
# tests/unit/test_pitfall_service.py
# -*- coding: utf-8 -*-
"""踩坑服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.services.pitfall.pitfall_service import PitfallService


class TestPitfallService:
    """踩坑服务测试"""

    def setup_method(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.service = PitfallService(self.mock_db)

    def test_generate_pitfall_no(self):
        """测试生成踩坑编号"""
        # Mock 查询返回空（没有今天的记录）
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        pitfall_no = self.service.generate_pitfall_no()

        # 格式: PFyymmdd001
        assert pitfall_no.startswith("PF")
        assert len(pitfall_no) == 11
        assert pitfall_no.endswith("001")

    def test_generate_pitfall_no_increment(self):
        """测试踩坑编号递增"""
        # Mock 返回今天已有的最后一条记录
        mock_last = MagicMock()
        today = datetime.now()
        mock_last.pitfall_no = f"PF{today.strftime('%y%m%d')}005"
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last

        pitfall_no = self.service.generate_pitfall_no()

        assert pitfall_no.endswith("006")

    def test_create_pitfall(self):
        """测试创建踩坑记录"""
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = self.service.create_pitfall(
            title="测试踩坑",
            description="测试描述",
            created_by=1,
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_get_pitfall_by_id(self):
        """测试按ID获取踩坑"""
        mock_pitfall = MagicMock()
        mock_pitfall.id = 1
        mock_pitfall.is_sensitive = False
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_pitfall

        result = self.service.get_pitfall(1, user_id=1)

        assert result is not None

    def test_get_sensitive_pitfall_no_permission(self):
        """测试获取敏感踩坑无权限"""
        mock_pitfall = MagicMock()
        mock_pitfall.id = 1
        mock_pitfall.is_sensitive = True
        mock_pitfall.created_by = 2
        mock_pitfall.visible_to = [3, 4]
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_pitfall

        result = self.service.get_pitfall(1, user_id=1)

        assert result is None  # 无权限时返回None
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_pitfall_service.py -v
```

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write the service**

```python
# app/services/pitfall/__init__.py
# -*- coding: utf-8 -*-
"""踩坑库服务包"""

from .pitfall_service import PitfallService

__all__ = ['PitfallService']
```

```python
# app/services/pitfall/pitfall_service.py
# -*- coding: utf-8 -*-
"""
踩坑服务
提供踩坑记录的CRUD和搜索功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.models.pitfall import Pitfall, PitfallLearningProgress, PitfallRecommendation


class PitfallService:
    """踩坑服务"""

    def __init__(self, db: Session):
        self.db = db

    def generate_pitfall_no(self) -> str:
        """
        生成踩坑编号
        格式: PFyymmdd001
        """
        today = datetime.now()
        prefix = f"PF{today.strftime('%y%m%d')}"

        # 查询今天最后一条记录
        last_pitfall = (
            self.db.query(Pitfall)
            .filter(Pitfall.pitfall_no.like(f"{prefix}%"))
            .order_by(desc(Pitfall.pitfall_no))
            .first()
        )

        if last_pitfall:
            # 提取序号并+1
            last_no = int(last_pitfall.pitfall_no[-3:])
            new_no = last_no + 1
        else:
            new_no = 1

        return f"{prefix}{new_no:03d}"

    def create_pitfall(
        self,
        title: str,
        description: str,
        created_by: int,
        solution: Optional[str] = None,
        stage: Optional[str] = None,
        equipment_type: Optional[str] = None,
        problem_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        root_cause: Optional[str] = None,
        impact: Optional[str] = None,
        prevention: Optional[str] = None,
        cost_impact: Optional[float] = None,
        schedule_impact: Optional[int] = None,
        source_type: Optional[str] = None,
        source_project_id: Optional[int] = None,
        source_ecn_id: Optional[int] = None,
        source_issue_id: Optional[int] = None,
        is_sensitive: bool = False,
        sensitive_reason: Optional[str] = None,
        visible_to: Optional[List[int]] = None,
    ) -> Pitfall:
        """创建踩坑记录"""
        pitfall = Pitfall(
            pitfall_no=self.generate_pitfall_no(),
            title=title,
            description=description,
            solution=solution,
            stage=stage,
            equipment_type=equipment_type,
            problem_type=problem_type,
            tags=tags,
            root_cause=root_cause,
            impact=impact,
            prevention=prevention,
            cost_impact=cost_impact,
            schedule_impact=schedule_impact,
            source_type=source_type or "REALTIME",
            source_project_id=source_project_id,
            source_ecn_id=source_ecn_id,
            source_issue_id=source_issue_id,
            is_sensitive=is_sensitive,
            sensitive_reason=sensitive_reason,
            visible_to=visible_to,
            created_by=created_by,
            status="DRAFT",
        )

        self.db.add(pitfall)
        self.db.commit()
        self.db.refresh(pitfall)

        return pitfall

    def get_pitfall(
        self, pitfall_id: int, user_id: int, is_admin: bool = False
    ) -> Optional[Pitfall]:
        """
        获取踩坑记录
        敏感记录需要权限检查
        """
        pitfall = (
            self.db.query(Pitfall)
            .filter(Pitfall.id == pitfall_id)
            .first()
        )

        if not pitfall:
            return None

        # 敏感记录权限检查
        if pitfall.is_sensitive and not is_admin:
            if pitfall.created_by != user_id:
                if pitfall.visible_to and user_id not in pitfall.visible_to:
                    return None  # 无权限

        return pitfall

    def update_pitfall(
        self, pitfall_id: int, user_id: int, **kwargs
    ) -> Optional[Pitfall]:
        """更新踩坑记录"""
        pitfall = self.get_pitfall(pitfall_id, user_id)
        if not pitfall:
            return None

        # 只有创建人或管理员可以编辑
        if pitfall.created_by != user_id:
            return None

        for key, value in kwargs.items():
            if hasattr(pitfall, key) and value is not None:
                setattr(pitfall, key, value)

        self.db.commit()
        self.db.refresh(pitfall)

        return pitfall

    def delete_pitfall(self, pitfall_id: int, user_id: int) -> bool:
        """删除踩坑记录"""
        pitfall = self.get_pitfall(pitfall_id, user_id)
        if not pitfall:
            return False

        # 只有创建人可以删除
        if pitfall.created_by != user_id:
            return False

        self.db.delete(pitfall)
        self.db.commit()

        return True

    def list_pitfalls(
        self,
        user_id: int,
        keyword: Optional[str] = None,
        stage: Optional[str] = None,
        equipment_type: Optional[str] = None,
        problem_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        verified_only: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Pitfall], int]:
        """
        获取踩坑列表
        支持多维度筛选
        """
        query = self.db.query(Pitfall)

        # 状态筛选（默认只显示已发布）
        if status:
            query = query.filter(Pitfall.status == status)
        else:
            query = query.filter(Pitfall.status == "PUBLISHED")

        # 关键词搜索
        if keyword:
            query = query.filter(
                or_(
                    Pitfall.title.contains(keyword),
                    Pitfall.description.contains(keyword),
                    Pitfall.solution.contains(keyword),
                )
            )

        # 多维度筛选
        if stage:
            query = query.filter(Pitfall.stage == stage)
        if equipment_type:
            query = query.filter(Pitfall.equipment_type == equipment_type)
        if problem_type:
            query = query.filter(Pitfall.problem_type == problem_type)
        if verified_only:
            query = query.filter(Pitfall.verified == True)

        # 排除无权限的敏感记录
        query = query.filter(
            or_(
                Pitfall.is_sensitive == False,
                Pitfall.created_by == user_id,
            )
        )

        total = query.count()
        pitfalls = (
            query.order_by(desc(Pitfall.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return pitfalls, total

    def publish_pitfall(self, pitfall_id: int, user_id: int) -> Optional[Pitfall]:
        """发布踩坑记录"""
        return self.update_pitfall(pitfall_id, user_id, status="PUBLISHED")

    def verify_pitfall(self, pitfall_id: int) -> Optional[Pitfall]:
        """验证踩坑记录（增加验证次数）"""
        pitfall = self.db.query(Pitfall).filter(Pitfall.id == pitfall_id).first()
        if pitfall:
            pitfall.verified = True
            pitfall.verify_count = (pitfall.verify_count or 0) + 1
            self.db.commit()
            self.db.refresh(pitfall)
        return pitfall
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_pitfall_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add app/services/pitfall/ tests/unit/test_pitfall_service.py
git commit -m "feat(pitfall): add PitfallService with CRUD operations"
```

---

### Task 6: Create Pitfall API Endpoints

**Files:**
- Create: `app/api/v1/endpoints/pitfalls/__init__.py`
- Create: `app/api/v1/endpoints/pitfalls/crud.py`
- Modify: `app/api/v1/api.py`

**Step 1: Write the API endpoints**

```python
# app/api/v1/endpoints/pitfalls/__init__.py
# -*- coding: utf-8 -*-
"""踩坑库 API 路由"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()
router.include_router(crud_router, tags=["pitfalls"])
```

```python
# app/api/v1/endpoints/pitfalls/crud.py
# -*- coding: utf-8 -*-
"""
踩坑记录 CRUD API
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.pitfall import (
    PitfallCreate,
    PitfallListItem,
    PitfallResponse,
    PitfallUpdate,
)
from app.services.pitfall import PitfallService

router = APIRouter()


@router.post("", response_model=ResponseModel)
def create_pitfall(
    data: PitfallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建踩坑记录

    必填字段：title, description
    其他字段可选，支持后续补充完善
    """
    service = PitfallService(db)

    pitfall = service.create_pitfall(
        title=data.title,
        description=data.description,
        solution=data.solution,
        stage=data.stage,
        equipment_type=data.equipment_type,
        problem_type=data.problem_type,
        tags=data.tags,
        root_cause=data.root_cause,
        impact=data.impact,
        prevention=data.prevention,
        cost_impact=data.cost_impact,
        schedule_impact=data.schedule_impact,
        source_type=data.source_type,
        source_project_id=data.source_project_id,
        source_ecn_id=data.source_ecn_id,
        source_issue_id=data.source_issue_id,
        is_sensitive=data.is_sensitive,
        sensitive_reason=data.sensitive_reason,
        visible_to=data.visible_to,
        created_by=current_user.id,
    )

    return ResponseModel(
        code=200,
        message="踩坑记录创建成功",
        data={"id": pitfall.id, "pitfall_no": pitfall.pitfall_no},
    )


@router.get("", response_model=ResponseModel)
def list_pitfalls(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    problem_type: Optional[str] = Query(None, description="问题类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    verified_only: bool = Query(False, description="仅显示已验证"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取踩坑列表

    支持多维度筛选和关键词搜索
    """
    service = PitfallService(db)

    pitfalls, total = service.list_pitfalls(
        user_id=current_user.id,
        keyword=keyword,
        stage=stage,
        equipment_type=equipment_type,
        problem_type=problem_type,
        status=status,
        verified_only=verified_only,
        skip=skip,
        limit=limit,
    )

    items = [
        {
            "id": p.id,
            "pitfall_no": p.pitfall_no,
            "title": p.title,
            "stage": p.stage,
            "equipment_type": p.equipment_type,
            "problem_type": p.problem_type,
            "tags": p.tags,
            "status": p.status,
            "verified": p.verified,
            "verify_count": p.verify_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in pitfalls
    ]

    return ResponseModel(
        code=200,
        message="获取踩坑列表成功",
        data={"total": total, "items": items},
    )


@router.get("/{pitfall_id}", response_model=ResponseModel)
def get_pitfall(
    pitfall_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取踩坑详情

    敏感记录需要相应权限
    """
    service = PitfallService(db)

    pitfall = service.get_pitfall(pitfall_id, current_user.id)
    if not pitfall:
        raise HTTPException(status_code=404, detail="踩坑记录不存在或无权限查看")

    return ResponseModel(
        code=200,
        message="获取踩坑详情成功",
        data={
            "id": pitfall.id,
            "pitfall_no": pitfall.pitfall_no,
            "title": pitfall.title,
            "description": pitfall.description,
            "solution": pitfall.solution,
            "stage": pitfall.stage,
            "equipment_type": pitfall.equipment_type,
            "problem_type": pitfall.problem_type,
            "tags": pitfall.tags,
            "root_cause": pitfall.root_cause,
            "impact": pitfall.impact,
            "prevention": pitfall.prevention,
            "cost_impact": float(pitfall.cost_impact) if pitfall.cost_impact else None,
            "schedule_impact": pitfall.schedule_impact,
            "source_type": pitfall.source_type,
            "source_project_id": pitfall.source_project_id,
            "is_sensitive": pitfall.is_sensitive,
            "status": pitfall.status,
            "verified": pitfall.verified,
            "verify_count": pitfall.verify_count,
            "created_by": pitfall.created_by,
            "created_at": pitfall.created_at.isoformat() if pitfall.created_at else None,
            "updated_at": pitfall.updated_at.isoformat() if pitfall.updated_at else None,
        },
    )


@router.put("/{pitfall_id}", response_model=ResponseModel)
def update_pitfall(
    pitfall_id: int,
    data: PitfallUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新踩坑记录

    只有创建人可以编辑
    """
    service = PitfallService(db)

    update_data = data.model_dump(exclude_unset=True)
    pitfall = service.update_pitfall(pitfall_id, current_user.id, **update_data)

    if not pitfall:
        raise HTTPException(status_code=404, detail="踩坑记录不存在或无权限编辑")

    return ResponseModel(
        code=200,
        message="踩坑记录更新成功",
        data={"id": pitfall.id},
    )


@router.delete("/{pitfall_id}", response_model=ResponseModel)
def delete_pitfall(
    pitfall_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除踩坑记录

    只有创建人可以删除
    """
    service = PitfallService(db)

    success = service.delete_pitfall(pitfall_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="踩坑记录不存在或无权限删除")

    return ResponseModel(
        code=200,
        message="踩坑记录删除成功",
        data={"id": pitfall_id},
    )


@router.post("/{pitfall_id}/publish", response_model=ResponseModel)
def publish_pitfall(
    pitfall_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    发布踩坑记录

    草稿状态 -> 已发布
    """
    service = PitfallService(db)

    pitfall = service.publish_pitfall(pitfall_id, current_user.id)
    if not pitfall:
        raise HTTPException(status_code=404, detail="踩坑记录不存在或无权限发布")

    return ResponseModel(
        code=200,
        message="踩坑记录发布成功",
        data={"id": pitfall.id, "status": pitfall.status},
    )
```

**Step 2: Register router in api.py**

Add to `app/api/v1/api.py`:

```python
# 踩坑库模块
from app.api.v1.endpoints.pitfalls import router as pitfalls_router

api_router.include_router(pitfalls_router, prefix="/pitfalls", tags=["pitfalls"])
```

**Step 3: Write API test**

```python
# tests/unit/test_pitfall_api.py
# -*- coding: utf-8 -*-
"""踩坑 API 单元测试"""

import pytest
from unittest.mock import MagicMock, patch


class TestPitfallAPI:
    """踩坑 API 测试"""

    def test_create_pitfall_schema(self):
        """测试创建踩坑的 schema 验证"""
        from app.schemas.pitfall import PitfallCreate

        # 最小必填字段
        data = PitfallCreate(
            title="测试踩坑",
            description="测试描述",
        )
        assert data.title == "测试踩坑"
        assert data.is_sensitive is False

    def test_create_pitfall_full_schema(self):
        """测试创建踩坑的完整 schema"""
        from app.schemas.pitfall import PitfallCreate
        from decimal import Decimal

        data = PitfallCreate(
            title="伺服电机选型错误",
            description="选用200W伺服，实际需要400W",
            solution="更换400W伺服电机",
            stage="S2",
            equipment_type="FCT",
            problem_type="TECHNICAL",
            tags=["伺服电机", "选型"],
            cost_impact=Decimal("5000.00"),
            schedule_impact=3,
            is_sensitive=True,
            sensitive_reason="COST",
        )
        assert data.stage == "S2"
        assert data.cost_impact == Decimal("5000.00")

    def test_update_pitfall_schema(self):
        """测试更新踩坑的 schema"""
        from app.schemas.pitfall import PitfallUpdate

        data = PitfallUpdate(solution="新的解决方案")
        assert data.solution == "新的解决方案"
        assert data.title is None  # 未设置的字段为 None
```

**Step 4: Run tests**

```bash
pytest tests/unit/test_pitfall_api.py -v
```

**Step 5: Commit**

```bash
git add app/api/v1/endpoints/pitfalls/ app/api/v1/api.py tests/unit/test_pitfall_api.py
git commit -m "feat(pitfall): add CRUD API endpoints for pitfall"
```

---

## Phase P1: Search & List Page (Future)

> Tasks for P1 will be defined after P0 is complete and validated.

**Planned features:**
- Full-text search with relevance scoring
- Tag-based filtering with autocomplete
- Frontend list page with filters

---

## Phase P2: Recommendation Engine (Future)

> Tasks for P2 will be defined after P1 is complete.

**Planned features:**
- Project create recommendation
- Stage change recommendation
- Keyword trigger recommendation

---

## Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| P0 | 6 tasks (Enums, Model, Migration, Schema, Service, API) | Ready |
| P1 | TBD | Planned |
| P2 | TBD | Planned |

**Total P0 implementation:** 6 tasks, each with 3-6 steps following TDD approach.
