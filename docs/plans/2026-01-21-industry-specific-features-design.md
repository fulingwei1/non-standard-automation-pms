# 非标自动化行业特定功能设计文档

## 概述

本文档补充项目管理模块整合设计，添加非标自动化行业特定的资源管理功能。

### 设计目标

1. **资源计划** - 按项目阶段规划人员需求
2. **资源冲突检测** - 自动识别跨项目的人员时间冲突
3. **资源利用率分析** - 部门/全局工作负载可视化
4. **技能矩阵** - 按技能快速查找可用人员

### 依赖的现有模型

| 模型 | 用途 |
|------|------|
| `MesProjectStaffingNeed` | 项目人员需求 |
| `HrEmployeeProfile` | 员工档案、工作负载 |
| `HrEmployeeTagEvaluation` | 技能评估 |
| `HrTagDict` | 技能/标签字典 |
| `ProjectStage` | 项目阶段 |
| `ProjectMember` | 项目成员分配 |

---

## 功能一：资源计划（Resource Plan）

### 业务场景

项目经理在项目启动时，需要规划各阶段的人员需求：

```
项目 A (ICT测试设备)
├── S2-方案设计: 机械工程师 1人 (50%), 电气工程师 1人 (30%)
├── S3-采购备料: 采购员 1人 (100%)
├── S4-加工制造: 机械工程师 1人 (80%)
├── S5-装配调试: 电气工程师 2人 (100%), 软件工程师 1人 (100%)
├── S6-出厂验收: 测试工程师 1人 (50%)
└── S8-现场安装: 电气工程师 1人 (100%), 软件工程师 1人 (50%)
```

### 数据模型扩展

```python
# app/models/project/resource_plan.py

class ProjectStageResourcePlan(Base, TimestampMixin):
    """项目阶段资源计划表"""
    __tablename__ = 'project_stage_resource_plan'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    stage_code = Column(String(10), nullable=False, comment='阶段编码 S1-S9')

    # 关联现有的人员需求表
    staffing_need_id = Column(Integer, ForeignKey('mes_project_staffing_need.id'))

    # 冗余字段便于查询
    role_code = Column(String(50), nullable=False, comment='角色编码')
    role_name = Column(String(100), comment='角色名称')
    headcount = Column(Integer, default=1, comment='需求人数')
    allocation_pct = Column(Numeric(5, 2), default=100, comment='分配比例%')

    # 实际分配
    assigned_employee_id = Column(Integer, ForeignKey('employees.id'), comment='已分配员工')
    assignment_status = Column(String(20), default='PENDING',
                               comment='分配状态: PENDING/ASSIGNED/CONFLICT/RELEASED')

    # 时间范围（从阶段计划日期继承或手动覆盖）
    planned_start = Column(Date, comment='计划开始日期')
    planned_end = Column(Date, comment='计划结束日期')

    remark = Column(Text, comment='备注')

    # 关系
    project = relationship('Project', backref='stage_resource_plans')
    staffing_need = relationship('MesProjectStaffingNeed')
    assigned_employee = relationship('Employee')

    __table_args__ = (
        Index('idx_stage_plan_project', 'project_id'),
        Index('idx_stage_plan_stage', 'stage_code'),
        Index('idx_stage_plan_employee', 'assigned_employee_id'),
        Index('idx_stage_plan_status', 'assignment_status'),
    )
```

### API 设计

```
/projects/{project_id}/resource-plan/
├── GET /                           # 获取项目资源计划
├── POST /                          # 创建阶段资源需求
├── GET /summary                    # 资源计划摘要（按阶段汇总）
├── GET /timeline                   # 资源时间线视图
│
├── GET /stages/{stage_code}        # 获取特定阶段的资源需求
├── PUT /stages/{stage_code}        # 更新阶段资源需求
│
├── POST /{plan_id}/assign          # 分配人员
├── POST /{plan_id}/release         # 释放人员
└── GET /{plan_id}/candidates       # 获取候选人员（调用现有AI匹配）
```

### 响应示例

```json
// GET /projects/123/resource-plan/summary
{
  "project_id": 123,
  "project_name": "ICT测试设备-华为项目",
  "stages": [
    {
      "stage_code": "S2",
      "stage_name": "方案设计",
      "planned_start": "2026-02-01",
      "planned_end": "2026-02-28",
      "requirements": [
        {
          "role_code": "ME",
          "role_name": "机械工程师",
          "headcount": 1,
          "allocation_pct": 50,
          "status": "ASSIGNED",
          "assigned_employees": [
            {"id": 101, "name": "张三", "department": "机械部"}
          ]
        },
        {
          "role_code": "EE",
          "role_name": "电气工程师",
          "headcount": 1,
          "allocation_pct": 30,
          "status": "PENDING",
          "assigned_employees": []
        }
      ],
      "fill_rate": 50  // 填充率
    }
  ],
  "overall_fill_rate": 45
}
```

---

## 功能二：资源冲突检测（Resource Conflicts）

### 业务场景

当同一工程师被分配到多个项目的同一时间段时，系统自动检测冲突：

```
张三 (机械工程师)
├── 项目A S5阶段: 2026-03-01 ~ 2026-03-31, 分配100%
├── 项目B S4阶段: 2026-03-15 ~ 2026-04-15, 分配80%  ⚠️ 冲突！
└── 项目C S2阶段: 2026-04-01 ~ 2026-04-30, 分配50%  ⚠️ 冲突！

冲突期间: 2026-03-15 ~ 2026-03-31, 总分配 180% > 100%
```

### API 设计

```
/projects/{project_id}/resource-conflicts/
├── GET /                           # 获取项目的所有资源冲突
├── GET /check                      # 检查当前分配是否有冲突（保存前预检）
└── POST /resolve                   # 标记冲突已解决（手动确认）

/analytics/resource-conflicts/
├── GET /                           # 全局资源冲突列表
├── GET /by-employee/{employee_id}  # 特定员工的冲突
├── GET /by-department/{dept_id}    # 部门内的冲突
└── GET /summary                    # 冲突汇总统计
```

### 冲突检测逻辑

```python
# app/services/project/resource_conflict_service.py

class ResourceConflictService:
    """资源冲突检测服务"""

    @staticmethod
    def detect_conflicts(employee_id: int, db: Session) -> List[ResourceConflict]:
        """检测员工的所有资源冲突"""
        # 获取员工所有分配
        assignments = db.query(ProjectStageResourcePlan).filter(
            ProjectStageResourcePlan.assigned_employee_id == employee_id,
            ProjectStageResourcePlan.assignment_status == 'ASSIGNED',
        ).all()

        conflicts = []

        # 检测时间重叠
        for i, a1 in enumerate(assignments):
            for a2 in assignments[i+1:]:
                overlap = calculate_date_overlap(
                    a1.planned_start, a1.planned_end,
                    a2.planned_start, a2.planned_end
                )
                if overlap:
                    total_allocation = a1.allocation_pct + a2.allocation_pct
                    if total_allocation > 100:
                        conflicts.append(ResourceConflict(
                            employee_id=employee_id,
                            project_a_id=a1.project_id,
                            project_b_id=a2.project_id,
                            overlap_start=overlap[0],
                            overlap_end=overlap[1],
                            total_allocation=total_allocation,
                            over_allocation=total_allocation - 100,
                        ))

        return conflicts

    @staticmethod
    def check_assignment_conflict(
        employee_id: int,
        project_id: int,
        start_date: date,
        end_date: date,
        allocation_pct: Decimal,
        db: Session
    ) -> Optional[ResourceConflict]:
        """检查新分配是否会产生冲突"""
        # 获取员工在时间范围内的现有分配
        existing = db.query(ProjectStageResourcePlan).filter(
            ProjectStageResourcePlan.assigned_employee_id == employee_id,
            ProjectStageResourcePlan.assignment_status == 'ASSIGNED',
            ProjectStageResourcePlan.project_id != project_id,  # 排除本项目
            ProjectStageResourcePlan.planned_end >= start_date,
            ProjectStageResourcePlan.planned_start <= end_date,
        ).all()

        # 计算重叠期间的总分配
        for assignment in existing:
            overlap = calculate_date_overlap(
                start_date, end_date,
                assignment.planned_start, assignment.planned_end
            )
            if overlap:
                total = allocation_pct + assignment.allocation_pct
                if total > 100:
                    return ResourceConflict(...)

        return None
```

### 响应示例

```json
// GET /projects/123/resource-conflicts/
{
  "project_id": 123,
  "conflicts": [
    {
      "id": 1,
      "employee": {"id": 101, "name": "张三", "department": "机械部"},
      "this_project": {
        "stage_code": "S5",
        "stage_name": "装配调试",
        "allocation_pct": 100,
        "period": "2026-03-01 ~ 2026-03-31"
      },
      "conflict_with": {
        "project_id": 456,
        "project_name": "视觉检测线-小米项目",
        "stage_code": "S4",
        "allocation_pct": 80,
        "period": "2026-03-15 ~ 2026-04-15"
      },
      "overlap_period": "2026-03-15 ~ 2026-03-31",
      "total_allocation": 180,
      "over_allocation": 80,
      "severity": "HIGH",  // HIGH: >150%, MEDIUM: >120%, LOW: >100%
      "resolved": false
    }
  ],
  "conflict_count": 1,
  "affected_employees": 1
}
```

---

## 功能三：资源利用率分析（Resource Utilization）

### 业务场景

部门经理需要了解团队的工作负载分布，识别过载和闲置：

```
机械部工作负载分布 (2026年3月)
├── 张三: 180% ⚠️ 严重过载
├── 李四: 95%  ✓ 饱和
├── 王五: 60%  ○ 有余量
└── 赵六: 20%  △ 闲置

部门平均: 89%
```

### API 设计

```
/departments/{dept_id}/workload/
├── GET /summary                    # 部门工作量汇总
├── GET /distribution               # 负载分布（柱状图数据）
├── GET /members/{user_id}          # 成员详细工作量
├── GET /trend                      # 负载趋势（折线图数据）
└── GET /forecast                   # 未来负载预测

/analytics/workload/
├── GET /overview                   # 全局工作量概览
├── GET /bottlenecks                # 资源瓶颈分析
├── GET /by-skill/{skill_code}      # 按技能统计工作量
└── GET /heatmap                    # 部门x时间 热力图数据
```

### 响应示例

```json
// GET /departments/5/workload/summary?month=2026-03
{
  "department": {"id": 5, "name": "机械部"},
  "period": "2026-03",
  "summary": {
    "total_employees": 8,
    "total_capacity_hours": 1408,  // 8人 × 22天 × 8小时
    "allocated_hours": 1250,
    "utilization_rate": 88.8,
    "overloaded_count": 1,         // >100%
    "optimal_count": 4,            // 80-100%
    "underutilized_count": 2,      // 50-80%
    "idle_count": 1                // <50%
  },
  "distribution": [
    {"range": "0-50%", "count": 1, "employees": [{"id": 104, "name": "赵六"}]},
    {"range": "50-80%", "count": 2, "employees": [...]},
    {"range": "80-100%", "count": 4, "employees": [...]},
    {"range": ">100%", "count": 1, "employees": [{"id": 101, "name": "张三", "utilization": 180}]}
  ]
}

// GET /analytics/workload/bottlenecks
{
  "period": "2026-03",
  "bottlenecks": [
    {
      "type": "SKILL_SHORTAGE",
      "skill": {"code": "EMC_DEBUG", "name": "EMC调试"},
      "severity": "HIGH",
      "detail": "仅2人具备该技能，当前负载均>90%",
      "affected_projects": [
        {"id": 123, "name": "ICT测试设备-华为"},
        {"id": 456, "name": "视觉检测线-小米"}
      ],
      "recommendation": "建议安排技能培训或外部招聘"
    },
    {
      "type": "DEPARTMENT_OVERLOAD",
      "department": {"id": 5, "name": "机械部"},
      "severity": "MEDIUM",
      "detail": "部门平均负载120%，3月中旬达到峰值",
      "recommendation": "考虑跨部门借调或外协"
    }
  ]
}
```

---

## 功能四：技能矩阵（Skill Matrix）

### 业务场景

项目经理需要快速找到具备特定技能的可用人员：

```
查询: 需要能做"EMC调试"的电气工程师，3月份可用

结果:
├── 李四 (电气部) - EMC调试:4分, 可用率:40%, 匹配度:85%
├── 王五 (电气部) - EMC调试:3分, 可用率:60%, 匹配度:72%
└── 陈七 (测试部) - EMC调试:5分, 可用率:10%, 匹配度:65% (可用率低)
```

### API 设计

```
/analytics/skill-matrix/
├── GET /                           # 全局技能矩阵
├── GET /skills                     # 技能列表（带人数统计）
├── GET /skills/{skill_code}        # 特定技能的人员列表
├── GET /search                     # 搜索：按技能+可用性查找人员
├── GET /gaps                       # 技能缺口分析
└── GET /coverage                   # 技能覆盖度报告

/departments/{dept_id}/skill-matrix/
├── GET /                           # 部门技能矩阵
└── GET /gaps                       # 部门技能缺口
```

### 搜索参数

```
GET /analytics/skill-matrix/search?
  skills=EMC_DEBUG,VISION_ALGO      # 需要的技能（AND关系）
  min_score=3                        # 最低技能评分
  department_id=5                    # 限定部门（可选）
  available_from=2026-03-01          # 可用时间范围
  available_to=2026-03-31
  min_availability=30                # 最低可用率%
  sort_by=match_score                # 排序: match_score/availability/skill_score
```

### 响应示例

```json
// GET /analytics/skill-matrix/search?skills=EMC_DEBUG&available_from=2026-03-01&available_to=2026-03-31
{
  "query": {
    "skills": ["EMC_DEBUG"],
    "period": "2026-03-01 ~ 2026-03-31",
    "min_availability": 0
  },
  "results": [
    {
      "employee": {
        "id": 102,
        "name": "李四",
        "department": "电气部",
        "title": "高级电气工程师"
      },
      "skill_match": {
        "EMC_DEBUG": {"score": 4, "level": "熟练", "last_used": "2026-01"}
      },
      "availability": {
        "current_allocation": 60,
        "available_pct": 40,
        "available_hours": 70,
        "current_projects": [
          {"id": 789, "name": "老化设备-OPPO", "allocation": 60}
        ]
      },
      "match_score": 85,
      "recommendation": "RECOMMENDED"
    },
    {
      "employee": {"id": 103, "name": "王五", ...},
      "skill_match": {"EMC_DEBUG": {"score": 3, "level": "一般"}},
      "availability": {"available_pct": 60},
      "match_score": 72,
      "recommendation": "ACCEPTABLE"
    }
  ],
  "total_count": 3,
  "skill_summary": {
    "EMC_DEBUG": {
      "total_qualified": 5,        // 具备该技能的总人数
      "currently_available": 3,    // 当前有空闲的人数
      "avg_score": 3.6,
      "coverage_departments": ["电气部", "测试部"]
    }
  }
}

// GET /analytics/skill-matrix/gaps
{
  "analysis_period": "2026-Q1",
  "critical_gaps": [
    {
      "skill": {"code": "VISION_ALGO", "name": "视觉算法"},
      "severity": "CRITICAL",
      "current_headcount": 1,
      "required_headcount": 3,      // 基于项目需求预测
      "gap": 2,
      "affected_projects": [
        {"id": 456, "name": "视觉检测线-小米", "need_date": "2026-02-15"}
      ],
      "recommendation": "紧急招聘或外部顾问"
    },
    {
      "skill": {"code": "PLC_SIEMENS", "name": "西门子PLC编程"},
      "severity": "MEDIUM",
      "current_headcount": 4,
      "required_headcount": 5,
      "gap": 1,
      "recommendation": "安排内部培训，从三菱PLC工程师转型"
    }
  ],
  "training_opportunities": [
    {
      "skill": {"code": "EMC_DEBUG", "name": "EMC调试"},
      "potential_trainees": [
        {"id": 105, "name": "周八", "current_skills": ["EE_DESIGN"], "readiness": 80}
      ]
    }
  ]
}
```

---

## API 路由整合

将上述功能整合到项目模块整合设计中：

```
/projects/{project_id}/
├── ... (现有路由)
│
├── /resource-plan/              # 资源计划 (新增)
│   ├── GET /
│   ├── POST /
│   ├── GET /summary
│   ├── GET /timeline
│   ├── GET /stages/{stage_code}
│   ├── PUT /stages/{stage_code}
│   ├── POST /{plan_id}/assign
│   ├── POST /{plan_id}/release
│   └── GET /{plan_id}/candidates
│
└── /resource-conflicts/         # 资源冲突 (新增)
    ├── GET /
    ├── GET /check
    └── POST /resolve

/departments/{dept_id}/
├── /workload/                   # 工作量 (已有，增强)
│   ├── GET /summary
│   ├── GET /distribution
│   ├── GET /members/{user_id}
│   ├── GET /trend
│   └── GET /forecast
│
└── /skill-matrix/               # 部门技能矩阵 (新增)
    ├── GET /
    └── GET /gaps

/analytics/
├── /workload/                   # 全局工作量 (已有，增强)
│   ├── GET /overview
│   ├── GET /bottlenecks
│   ├── GET /by-skill/{skill_code}
│   └── GET /heatmap
│
├── /resource-conflicts/         # 全局资源冲突 (新增)
│   ├── GET /
│   ├── GET /by-employee/{employee_id}
│   ├── GET /by-department/{dept_id}
│   └── GET /summary
│
└── /skill-matrix/               # 全局技能矩阵 (新增)
    ├── GET /
    ├── GET /skills
    ├── GET /skills/{skill_code}
    ├── GET /search
    ├── GET /gaps
    └── GET /coverage
```

---

## 实施优先级

| 优先级 | 功能 | 依赖 | 工作量 |
|--------|------|------|--------|
| P1 | 资源计划 | 现有 MesProjectStaffingNeed | 中 |
| P1 | 资源冲突检测 | 资源计划 | 中 |
| P2 | 资源利用率分析 | HrEmployeeProfile | 低 |
| P2 | 技能矩阵 | HrTagDict, HrEmployeeTagEvaluation | 低 |

---

## 数据库迁移

需要新增一张表：`project_stage_resource_plan`

```sql
-- migrations/20260121_resource_plan_sqlite.sql

CREATE TABLE IF NOT EXISTS project_stage_resource_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    stage_code VARCHAR(10) NOT NULL,
    staffing_need_id INTEGER REFERENCES mes_project_staffing_need(id),
    role_code VARCHAR(50) NOT NULL,
    role_name VARCHAR(100),
    headcount INTEGER DEFAULT 1,
    allocation_pct DECIMAL(5,2) DEFAULT 100,
    assigned_employee_id INTEGER REFERENCES employees(id),
    assignment_status VARCHAR(20) DEFAULT 'PENDING',
    planned_start DATE,
    planned_end DATE,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stage_plan_project ON project_stage_resource_plan(project_id);
CREATE INDEX idx_stage_plan_stage ON project_stage_resource_plan(stage_code);
CREATE INDEX idx_stage_plan_employee ON project_stage_resource_plan(assigned_employee_id);
CREATE INDEX idx_stage_plan_status ON project_stage_resource_plan(assignment_status);
```
