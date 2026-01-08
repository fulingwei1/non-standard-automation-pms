# P1 功能快速参考卡

**版本**: 1.0 | **日期**: 2026-01-07

---

## 🚀 快速开始

### 启动服务

```bash
# 启动后端
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 检查健康状态
curl http://localhost:8000/health

# 查看 API 文档
open http://localhost:8000/docs
```

---

## 📚 核心服务 API

### PerformanceService 类

位置: `app/services/performance_service.py`

```python
from app.services.performance_service import PerformanceService

# 1. 判断用户角色
roles = PerformanceService.get_user_manager_roles(db, user)
# 返回: {'is_dept_manager': bool, 'is_project_manager': bool, ...}

# 2. 获取可管理员工
employee_ids = PerformanceService.get_manageable_employees(db, user, "2026-01")
# 返回: [1, 2, 3, ...]

# 3. 自动创建评价任务
records = PerformanceService.create_evaluation_tasks(db, summary)
# 返回: [PerformanceEvaluationRecord, ...]

# 4. 计算最终分数
result = PerformanceService.calculate_final_score(db, summary_id, "2026-01")
# 返回: {'final_score': 88.5, 'dept_score': 90, 'project_score': 87, ...}

# 5. 计算季度分数
quarterly = PerformanceService.calculate_quarterly_score(db, employee_id, "2026-01")
# 返回: 88.2

# 6. 获取等级
level = PerformanceService.get_score_level(88.5)
# 返回: "B+"

# 7. 查询历史绩效
history = PerformanceService.get_historical_performance(db, employee_id, 3)
# 返回: [{'period': '2026-01', 'final_score': 88.5, ...}, ...]
```

---

## 🔌 API 端点

### 员工端

```bash
# 提交工作总结（自动创建评价任务）
POST /api/v1/performance/monthly-summary
{
  "period": "2026-01",
  "work_content": "...",
  "self_evaluation": "..."
}

# 保存草稿
PUT /api/v1/performance/monthly-summary/draft?period=2026-01
{
  "work_content": "...",
  "self_evaluation": "..."
}

# 查看我的绩效（含分数计算和趋势）
GET /api/v1/performance/my-performance
```

### 经理端

```bash
# 查看待评价任务（自动权限过滤）
GET /api/v1/performance/evaluation-tasks?period=2026-01&status_filter=PENDING

# 查看评价详情（含历史绩效）
GET /api/v1/performance/evaluation/123

# 提交评价
POST /api/v1/performance/evaluation/123
{
  "score": 90,
  "comment": "..."
}
```

### HR 端

```bash
# 查看权重配置
GET /api/v1/performance/weight-config

# 更新权重配置
PUT /api/v1/performance/weight-config
{
  "dept_manager_weight": 60,
  "project_manager_weight": 40,
  "effective_date": "2026-02-01",
  "reason": "调整原因"
}
```

---

## 🧮 算法公式

### 最终分数

```
最终分数 = 部门分数 × 部门权重% + 项目平均分 × 项目权重%
```

### 项目加权平均

```
项目平均分 = Σ(项目分数 × 项目权重) / Σ(项目权重)
```

### 季度分数

```
季度分数 = Σ(最近3个月最终分数) / 3
```

### 等级划分

| 分数范围 | 等级 | 说明 |
|----------|------|------|
| 95-100 | A+ | 优秀+ |
| 90-94 | A | 优秀 |
| 85-89 | B+ | 良好+ |
| 80-84 | B | 良好 |
| 75-79 | C+ | 合格+ |
| 70-74 | C | 合格 |
| <70 | D | 待改进 |

---

## 🔐 权限控制

### 角色判断逻辑

```python
# 部门经理
User.employee_id → Employee → Department.manager_id (匹配)

# 项目经理
Project.pm_id == User.id
```

### 数据权限

| 角色 | 可见数据 |
|------|----------|
| 部门经理 | 本部门所有员工 |
| 项目经理 | 所管理项目的成员 |
| 普通员工 | 仅自己的数据 |
| HR | 全部数据 |

---

## 📋 数据模型

### MonthlyWorkSummary (月度工作总结)

```python
employee_id: int       # 员工ID
period: str            # 周期 (YYYY-MM)
work_content: str      # 工作内容
self_evaluation: str   # 自我评价
status: str            # DRAFT/SUBMITTED/EVALUATING/COMPLETED
submit_date: datetime  # 提交时间
```

### PerformanceEvaluationRecord (评价记录)

```python
summary_id: int        # 总结ID
evaluator_id: int      # 评价人ID
evaluator_type: str    # DEPT_MANAGER/PROJECT_MANAGER
project_id: int        # 项目ID (可选)
project_weight: int    # 项目权重 (可选)
score: int             # 分数 (60-100)
comment: str           # 评价意见
status: str            # PENDING/COMPLETED
evaluated_at: datetime # 评价时间
```

### EvaluationWeightConfig (权重配置)

```python
dept_manager_weight: int      # 部门权重 (%)
project_manager_weight: int   # 项目权重 (%)
effective_date: date          # 生效日期
operator_id: int              # 操作人ID
reason: str                   # 调整原因
```

---

## 🔄 业务流程

### 1. 员工提交流程

```
员工编写总结 → 提交 → 创建部门经理任务 → 创建项目经理任务 → 通知经理
```

### 2. 经理评价流程

```
经理登录 → 查看任务列表 → 选择员工 → 查看总结+历史 → 打分评价 → 提交
```

### 3. 分数计算流程

```
所有评价完成 → 获取权重配置 → 计算部门分数 → 计算项目平均 → 加权汇总 → 确定等级
```

---

## 🐛 常见问题

### Q1: 如何判断用户是否为经理？

```python
roles = PerformanceService.get_user_manager_roles(db, user)
if roles['is_dept_manager'] or roles['is_project_manager']:
    print("用户是经理")
```

### Q2: 如何获取用户可评价的员工？

```python
employee_ids = PerformanceService.get_manageable_employees(db, user, period)
```

### Q3: 提交总结后评价任务没有创建？

检查：
1. 员工是否有 `employee_id`
2. 员工所属部门是否有经理
3. 员工是否参与项目
4. 项目是否有 PM

### Q4: 分数计算结果为 None？

原因：
- 评价记录状态不是 `COMPLETED`
- 没有任何评价记录

### Q5: 季度趋势没有数据？

原因：
- 工作总结状态不是 `COMPLETED`
- 最近3个月没有提交总结

---

## 🎯 使用示例

### 示例1: 在 API 中使用服务

```python
from app.services.performance_service import PerformanceService

@router.get("/my-stats")
def get_my_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    # 获取最近3个月绩效
    history = PerformanceService.get_historical_performance(db, current_user.id, 3)

    # 计算本季度分数
    current_period = date.today().strftime("%Y-%m")
    quarterly = PerformanceService.calculate_quarterly_score(db, current_user.id, current_period)

    return {
        "history": history,
        "quarterly_score": quarterly
    }
```

### 示例2: 自定义权重计算

```python
# 创建评价任务时指定项目权重
from app.models.performance import PerformanceEvaluationRecord

eval_record = PerformanceEvaluationRecord(
    summary_id=summary.id,
    evaluator_id=pm_user.id,
    evaluator_type="PROJECT_MANAGER",
    project_id=project.id,
    project_weight=60,  # 指定该项目占60%权重
    score=0,
    comment="",
    status="PENDING"
)
db.add(eval_record)
db.commit()
```

---

## 📊 测试命令

```bash
# 健康检查
curl http://localhost:8000/health

# 查看待评价任务 (需要 Token)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/performance/evaluation-tasks?period=2026-01

# 提交工作总结 (需要 Token)
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"period":"2026-01","work_content":"...","self_evaluation":"..."}' \
  http://localhost:8000/api/v1/performance/monthly-summary
```

---

## 📖 文档索引

- [P1_FEATURES_COMPLETION_REPORT.md](./P1_FEATURES_COMPLETION_REPORT.md) - 完整技术文档
- [P1_IMPLEMENTATION_SUMMARY.md](./P1_IMPLEMENTATION_SUMMARY.md) - 实现总结
- [DELIVERY_CHECKLIST.md](./DELIVERY_CHECKLIST.md) - 交付清单
- [http://localhost:8000/docs](http://localhost:8000/docs) - API 交互文档

---

**快速参考卡 v1.0** | 更新于 2026-01-07
