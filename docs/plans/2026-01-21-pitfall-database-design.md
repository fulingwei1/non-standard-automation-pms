# 项目踩坑库设计文档

## 概述

设计一个独立的踩坑库模块，帮助团队沉淀项目经验，避免重复犯错。

### 核心目标

1. **避免重复犯错** - 新项目遇到类似客户/设备类型时，提前看到历史教训
2. **加速问题解决** - 当前项目卡住时，快速找到类似问题的解决方案
3. **提升报价准确性** - 售前阶段根据历史踩坑点，更准确评估风险和成本
4. **培养新人** - 让新工程师快速了解"前人血泪"，少走弯路

### 设计决策

| 维度 | 决定 |
|------|------|
| 模块定位 | 独立踩坑库模块（轻量集成方案） |
| 录入模式 | 混合（实时/阶段结束/复盘） |
| 分类体系 | 多维度（阶段+设备类型+问题类型+标签） |
| 主动推荐 | 全场景（项目创建/阶段切换/关键字） |
| 字段设计 | 可配置（必填精简，选填完善） |
| 权限模型 | 项目成员录入+全员查看+敏感控制 |

---

## 数据模型

### 核心模型：Pitfall（踩坑记录）

```python
class Pitfall(Base, TimestampMixin):
    """踩坑记录表"""
    __tablename__ = 'pitfalls'

    id = Column(Integer, primary_key=True)
    pitfall_no = Column(String(50), unique=True)  # 编号 PF240121001

    # === 必填字段（降低录入门槛）===
    title = Column(String(200), nullable=False)      # 标题
    description = Column(Text, nullable=False)       # 问题描述
    solution = Column(Text)                          # 解决方案（可后补）

    # === 多维度分类 ===
    stage = Column(String(20))           # 阶段：S1-S9
    equipment_type = Column(String(50))  # 设备类型：ICT/FCT/EOL/...
    problem_type = Column(String(50))    # 问题类型：技术/供应商/沟通/进度/成本
    tags = Column(JSON)                  # 自由标签：["伺服电机", "海康相机", "某客户"]

    # === 选填字段（逐步完善）===
    root_cause = Column(Text)            # 根因分析
    impact = Column(Text)                # 影响范围
    prevention = Column(Text)            # 预防措施
    cost_impact = Column(Numeric(12,2))  # 成本影响（元）
    schedule_impact = Column(Integer)    # 工期影响（天）

    # === 来源追溯 ===
    source_type = Column(String(20))     # 来源：REALTIME/STAGE_END/REVIEW/ECN/ISSUE
    source_project_id = Column(Integer, ForeignKey('projects.id'))
    source_ecn_id = Column(Integer)      # 关联ECN
    source_issue_id = Column(Integer)    # 关联Issue

    # === 权限与状态 ===
    is_sensitive = Column(Boolean, default=False)  # 敏感标记
    sensitive_reason = Column(String(50))          # 敏感原因
    visible_to = Column(JSON)                      # 可见范围（敏感记录）
    status = Column(String(20), default='DRAFT')   # DRAFT/PUBLISHED/ARCHIVED
    verified = Column(Boolean, default=False)      # 已验证（解决方案有效）
    verify_count = Column(Integer, default=0)      # 验证次数（多少项目用过）

    # === 创建人 ===
    created_by = Column(Integer, ForeignKey('users.id'))
```

### 辅助模型：PitfallRecommendation（推荐记录）

```python
class PitfallRecommendation(Base, TimestampMixin):
    """踩坑推荐记录（追踪推荐效果）"""
    __tablename__ = 'pitfall_recommendations'

    id = Column(Integer, primary_key=True)
    pitfall_id = Column(Integer, ForeignKey('pitfalls.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))

    trigger_type = Column(String(20))    # 触发类型：PROJECT_CREATE/STAGE_CHANGE/KEYWORD
    trigger_context = Column(JSON)       # 触发上下文

    is_helpful = Column(Boolean)         # 用户反馈：有用/没用
    feedback = Column(Text)              # 反馈详情
```

### 辅助模型：PitfallLearningProgress（学习进度）

```python
class PitfallLearningProgress(Base, TimestampMixin):
    """踩坑学习进度"""
    __tablename__ = 'pitfall_learning_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    pitfall_id = Column(Integer, ForeignKey('pitfalls.id'))

    read_at = Column(DateTime)           # 阅读时间
    is_marked = Column(Boolean)          # 标记为已掌握
    notes = Column(Text)                 # 学习笔记
```

---

## 录入入口设计

### 入口 1：实时录入（独立入口）

**位置**：顶部导航 → "踩坑库" → "新增记录"

**场景**：工程师遇到问题，随时记录

**表单设计**：
- 必填：标题、问题描述
- 快速分类：阶段（单选）、设备类型（单选）、问题类型（单选）、标签（多选）
- 可选：关联项目、敏感标记
- 操作：保存草稿 / 发布

### 入口 2：阶段切换时录入

**位置**：项目详情 → 阶段切换弹窗 → "记录本阶段踩坑"

**场景**：阶段完成时，回顾该阶段遇到的问题

**交互**：阶段切换前可选添加踩坑记录，自动关联项目和阶段

### 入口 3：复盘时批量导入

**位置**：项目复盘 → "导入踩坑记录"

**场景**：项目结项复盘，把经验教训同步到踩坑库

**交互**：从复盘报告中选择经验教训，批量导入到踩坑库

---

## 推荐引擎设计

### 推荐触发场景

| 触发场景 | 触发时机 | 匹配逻辑 |
|---------|---------|---------|
| 项目创建 | 新建项目保存时 | 客户名 + 设备类型 |
| 阶段切换 | 进入新阶段时 | 阶段 + 设备类型 |
| 关键字触发 | ECN/Issue/问题描述输入时 | 标题+标签 模糊匹配 |
| 主动搜索 | 用户在踩坑库搜索时 | 全文搜索 + 多维度筛选 |

### 推荐算法

```python
class PitfallRecommendationService:
    """踩坑推荐服务"""

    def recommend_for_project_create(self, project: Project) -> List[Pitfall]:
        """项目创建时推荐"""
        # 优先级：客户名匹配 > 设备类型匹配 > 行业匹配
        score_weights = {
            'customer_match': 50,      # 同客户历史踩坑
            'equipment_match': 30,     # 同设备类型踩坑
            'industry_match': 10,      # 同行业踩坑
            'verified_bonus': 10,      # 已验证的加分
        }
        # 返回 Top 10，按相关度排序

    def recommend_for_stage_change(self, project_id: int, new_stage: str) -> List[Pitfall]:
        """阶段切换时推荐"""
        # 匹配条件：阶段 + 设备类型
        # 排序：验证次数 > 最近发生 > 相关度

    def recommend_by_keyword(self, keyword: str, context: dict) -> List[Pitfall]:
        """关键字触发推荐（实时联想）"""
        # 匹配：标题、标签、问题描述
        # 上下文：当前项目的阶段、设备类型（提升相关性）
```

### 推荐展示

- **项目创建后**：弹窗提醒，显示高/中相关踩坑记录
- **阶段切换时**：侧边提示，显示该阶段常见踩坑点
- **输入时**：实时联想下拉，显示相关踩坑记录

### 推荐效果追踪

用户可对推荐结果反馈"有用/没用"，系统根据反馈调整推荐权重。

---

## 售前集成：风险分析

### 功能描述

销售/售前工程师在做项目评估和报价时，能看到类似项目的历史踩坑，提前评估风险和成本。

### 风险分析视图

- 风险等级（高/中/低）
- 历史踩坑数量
- 成本风险：历史平均额外成本、明细
- 工期风险：历史平均延期、明细
- 建议预留：成本风险金、工期缓冲

### API 设计

```python
GET /api/v1/pitfalls/risk-analysis
    ?customer_id=123
    &equipment_type=FCT
    &industry=汽车电子

# 返回
{
    "risk_level": "MEDIUM",
    "pitfall_count": 8,
    "cost_risk": {
        "average_extra_cost": 15000,
        "breakdown": [...]
    },
    "schedule_risk": {
        "average_delay_days": 5,
        "breakdown": [...]
    },
    "suggestions": {
        "cost_buffer": 20000,
        "schedule_buffer_days": 7
    }
}
```

---

## 新人培养：学习中心

### 功能描述

新工程师入职，通过踩坑库快速了解常见问题，少走弯路。

### 学习路径

- 按阶段学习（S1-S9）
- 按设备类型学习（ICT/FCT/EOL/烧录/视觉/组装）
- 热门踩坑 TOP 10
- 新人必读清单

### 学习进度追踪

- 记录阅读时间
- 支持标记"已掌握"
- 支持添加学习笔记

---

## 权限控制

### 权限规则

| 操作 | 权限 |
|------|------|
| 录入 | 项目成员、部门经理、管理员 |
| 查看（非敏感） | 全员 |
| 查看（敏感） | 创建人、项目团队、部门经理、管理员、指定人员 |
| 编辑 | 创建人、部门经理、管理员 |
| 发布 | 创建人、指定审核人 |

### 敏感记录处理

- 支持标记为敏感记录
- 敏感原因：涉及客户信息 / 涉及成本报价 / 涉及供应商问题 / 其他
- 可见范围：本项目团队、部门经理及以上、指定人员

---

## 系统集成

### 集成点

| 集成模块 | 集成方式 | 说明 |
|---------|---------|------|
| 项目管理 | 事件监听 | 项目创建时触发推荐 |
| 阶段系统 | 事件监听 | 阶段切换时触发推荐 + 录入入口 |
| ECN模块 | 双向关联 | ECN可关联踩坑记录，踩坑可来源于ECN |
| Issue模块 | 双向关联 | Issue解决后可转为踩坑记录 |
| 复盘模块 | 数据导入 | 从ProjectLesson批量导入 |
| 售前评估 | API调用 | 风险分析接口 |
| 消息通知 | 推送 | 推荐结果通过系统消息/企业微信推送 |

### 事件集成示例

```python
from app.events import project_created, stage_changed

@project_created.connect
def on_project_created(project: Project):
    """项目创建时推荐踩坑"""
    service = PitfallRecommendationService()
    recommendations = service.recommend_for_project_create(project)

    if recommendations:
        # 创建推荐记录并发送通知
        ...

@stage_changed.connect
def on_stage_changed(project_id: int, old_stage: str, new_stage: str):
    """阶段切换时推荐踩坑"""
    service = PitfallRecommendationService()
    recommendations = service.recommend_for_stage_change(project_id, new_stage)

    if recommendations:
        # 记录并通知...
```

---

## API 设计

### 踩坑记录 CRUD

```
POST   /api/v1/pitfalls                    # 创建
GET    /api/v1/pitfalls                    # 列表（支持多维度筛选）
GET    /api/v1/pitfalls/{id}               # 详情
PUT    /api/v1/pitfalls/{id}               # 更新
DELETE /api/v1/pitfalls/{id}               # 删除
```

### 快捷入口

```
POST   /api/v1/pitfalls/from-stage-change  # 阶段切换时创建
POST   /api/v1/pitfalls/import-from-review # 从复盘导入
```

### 搜索与推荐

```
GET    /api/v1/pitfalls/search             # 全文搜索+标签筛选
GET    /api/v1/pitfalls/recommend          # 获取推荐
POST   /api/v1/pitfall-recommendations/{id}/feedback  # 推荐反馈
```

### 售前风险分析

```
GET    /api/v1/pitfalls/risk-analysis      # 风险分析
```

### 学习中心

```
GET    /api/v1/pitfalls/learning/stats     # 按维度统计
GET    /api/v1/pitfalls/learning/top       # 热门踩坑
GET    /api/v1/pitfalls/learning/checklist # 新人必读清单
GET    /api/v1/pitfalls/learning/progress  # 我的学习进度
POST   /api/v1/pitfalls/{id}/mark-learned  # 标记已学习
```

---

## 目录结构

```
app/
├── models/
│   └── pitfall.py                    # Pitfall, PitfallRecommendation, PitfallLearningProgress
├── schemas/
│   └── pitfall.py                    # Pydantic schemas
├── api/v1/endpoints/
│   └── pitfalls/
│       ├── __init__.py
│       ├── crud.py                   # 基础 CRUD
│       ├── search.py                 # 搜索接口
│       ├── recommendations.py        # 推荐相关
│       ├── learning.py               # 学习中心
│       └── risk_analysis.py          # 售前风险分析
├── services/
│   └── pitfall/
│       ├── __init__.py
│       ├── pitfall_service.py        # 核心业务逻辑
│       ├── recommendation_service.py # 推荐引擎
│       ├── risk_analysis_service.py  # 风险分析
│       └── event_handlers.py         # 事件监听
└── ...

frontend/src/
├── pages/
│   └── Pitfall/
│       ├── index.jsx                 # 踩坑库主页
│       ├── PitfallList.jsx           # 列表页
│       ├── PitfallDetail.jsx         # 详情页
│       ├── PitfallForm.jsx           # 录入表单
│       ├── LearningCenter.jsx        # 学习中心
│       └── RiskAnalysis.jsx          # 风险分析
├── components/
│   └── pitfall/
│       ├── PitfallCard.jsx           # 踩坑卡片
│       ├── PitfallRecommendModal.jsx # 推荐弹窗
│       ├── PitfallQuickAdd.jsx       # 快速录入组件
│       └── PitfallSuggest.jsx        # 关键字联想组件
└── ...

migrations/
└── 20260121_pitfall_sqlite.sql       # 数据库迁移
```

---

## 分阶��实施

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| **P0** | 数据模型 + 基础 CRUD + 录入表单 | 必须 |
| **P1** | 多维度搜索 + 列表页 | 必须 |
| **P2** | 项目创建/阶段切换推荐 | 高 |
| **P3** | 关键字实时联想 | 中 |
| **P4** | 售前风险分析 | 中 |
| **P5** | 学习中心 + 进度追踪 | 低 |
| **P6** | 从复盘/ECN/Issue导入 | 低 |

---

## 数据库迁移

```sql
-- migrations/20260121_pitfall_sqlite.sql

-- 踩坑记录表
CREATE TABLE pitfalls (
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

CREATE INDEX idx_pitfall_stage ON pitfalls(stage);
CREATE INDEX idx_pitfall_equipment ON pitfalls(equipment_type);
CREATE INDEX idx_pitfall_problem ON pitfalls(problem_type);
CREATE INDEX idx_pitfall_status ON pitfalls(status);
CREATE INDEX idx_pitfall_project ON pitfalls(source_project_id);

-- 推荐记录表
CREATE TABLE pitfall_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pitfall_id INTEGER REFERENCES pitfalls(id),
    project_id INTEGER REFERENCES projects(id),

    trigger_type VARCHAR(20),
    trigger_context JSON,

    is_helpful BOOLEAN,
    feedback TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pitfall_rec_project ON pitfall_recommendations(project_id);
CREATE INDEX idx_pitfall_rec_pitfall ON pitfall_recommendations(pitfall_id);

-- 学习进度表
CREATE TABLE pitfall_learning_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    pitfall_id INTEGER REFERENCES pitfalls(id),

    read_at DATETIME,
    is_marked BOOLEAN DEFAULT FALSE,
    notes TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, pitfall_id)
);

CREATE INDEX idx_pitfall_learn_user ON pitfall_learning_progress(user_id);
```
