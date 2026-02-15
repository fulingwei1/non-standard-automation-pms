# 工时分析与预测系统 - 快速上手

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r docs/timesheet_analytics_requirements.txt
```

### 2. 数据库迁移

```bash
# 生成迁移脚本
alembic revision --autogenerate -m "Add timesheet analytics models"

# 执行迁移
alembic upgrade head
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问API文档

浏览器打开：`http://localhost:8000/docs`

查找：`工时分析与预测` 标签

---

## 📊 功能概览

### 分析功能（6种）

| 功能 | API端点 | 说明 |
|------|---------|------|
| 工时趋势 | `/analytics/trend` | 多周期趋势分析 |
| 人员负荷 | `/analytics/workload` | 饱和度热力图 |
| 效率对比 | `/analytics/efficiency` | 计划vs实际 |
| 加班统计 | `/analytics/overtime` | 加班分析 |
| 部门对比 | `/analytics/department-comparison` | 部门对比 |
| 项目分布 | `/analytics/project-distribution` | 项目占比 |

### 预测功能（4种）

| 功能 | API端点 | 说明 |
|------|---------|------|
| 项目工时预测 | `/forecast/project` | 3种算法 |
| 完工时间预测 | `/forecast/completion` | 基于进度 |
| 负荷预警 | `/forecast/workload-alert` | 饱和度预警 |
| 缺口分析 | `/forecast/gap-analysis` | 资源缺口 |

---

## 🎯 快速示例

### 示例1: 查看本月工时趋势

```bash
curl -X GET "http://localhost:8000/api/v1/timesheet/analytics/trend?period_type=MONTHLY&start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 示例2: 识别超负荷人员

```bash
curl -X GET "http://localhost:8000/api/v1/timesheet/analytics/workload?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 示例3: 预测新项目工时

```bash
curl -X POST "http://localhost:8000/api/v1/timesheet/analytics/forecast/project" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "新项目A",
    "complexity": "MEDIUM",
    "team_size": 5,
    "duration_days": 30,
    "forecast_method": "LINEAR_REGRESSION"
  }'
```

### 示例4: 查看负荷预警

```bash
curl -X GET "http://localhost:8000/api/v1/timesheet/analytics/forecast/workload-alert?alert_level=HIGH&forecast_days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📚 文档链接

- 📖 [完整指南](./timesheet_analytics_guide.md) - 详细功能说明、算法原理、API文档
- 🧪 [测试用例](../tests/test_timesheet_analytics.py) - 20+测试用例
- 🗂️ [数据模型](../app/models/timesheet_analytics.py) - ORM模型定义
- 📝 [Schema定义](../app/schemas/timesheet_analytics.py) - API数据结构

---

## 🔧 配置说明

### 权限配置

所有API需要权限：`timesheet:read`

在用户权限表中添加：
```sql
INSERT INTO user_permissions (user_id, permission_code)
VALUES (1, 'timesheet:read');
```

### 标准工时配置

在`TimesheetRule`表中配置：
```python
{
  "standard_daily_hours": 8,      # 标准日工时
  "max_daily_hours": 12,          # 最大日工时
  "work_days_per_week": 5         # 每周工作日
}
```

---

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/test_timesheet_analytics.py -v

# 运行特定测试
pytest tests/test_timesheet_analytics.py::test_01_trend_analysis_monthly -v

# 查看覆盖率
pytest tests/test_timesheet_analytics.py --cov=app.services.timesheet_analytics_service --cov-report=html
```

---

## 📈 预测算法对比

| 算法 | 适用场景 | 数据要求 | 准确度 | 速度 |
|------|----------|----------|--------|------|
| 历史平均法 | 有相似项目 | 低 | ⭐⭐⭐ | ⚡⚡⚡ |
| 线性回归 | 数据充足 | 高（≥3项目） | ⭐⭐⭐⭐ | ⚡⚡ |
| 趋势预测 | 考虑趋势 | 中（≥10天） | ⭐⭐⭐⭐ | ⚡⚡ |

**选择建议：**
- 快速估算 → 历史平均法
- 精确预测 → 线性回归
- 在途项目 → 趋势预测

---

## ⚠️ 注意事项

### 数据准备

在使用分析和预测功能前，确保：
1. ✅ 工时记录数据完整（至少1个月）
2. ✅ 工时审批状态正确（APPROVED）
3. ✅ 项目和人员信息准确
4. ✅ 已配置标准工时规则

### 性能优化

- 📌 大数据量查询（>10万条）建议分页
- 📌 频繁查询建议使用缓存（Redis）
- 📌 复杂分析建议异步处理（Celery）

### 数据质量

预测准确度取决于：
- 历史数据质量
- 数据量（越多越准）
- 项目相似度
- 外部因素（需求变更等）

---

## 🐛 故障排查

### 问题1: 预测结果为0或异常

**可能原因：**
- 没有历史数据
- 数据过滤条件过严

**解决方法：**
```python
# 检查数据
SELECT COUNT(*) FROM timesheet 
WHERE work_date >= '2024-01-01' 
  AND status = 'APPROVED';

# 如果数量为0，检查：
# 1. 是否有工时记录
# 2. 审批状态是否正确
# 3. 日期范围是否正确
```

### 问题2: scikit-learn导入失败

**解决方法：**
```bash
pip install scikit-learn
```

如果无法安装，系统会自动使用Fallback方法（简单线性估算）。

### 问题3: 性能慢

**优化建议：**
```python
# 1. 添加数据库索引（已在模型中定义）
# 2. 缩小查询范围
# 3. 使用缓存
from functools import lru_cache

@lru_cache(maxsize=128)
def get_trend(start_date, end_date):
    # ...
```

---

## 📊 数据示例

### 测试数据生成

```python
# 快速生成测试数据
python scripts/generate_test_timesheet_data.py --days 90 --users 10 --projects 5
```

### 示例响应

**工时趋势：**
```json
{
  "total_hours": 1280.5,
  "trend": "INCREASING",
  "change_rate": 8.5,
  "chart_data": {
    "labels": ["2024-01", "2024-02"],
    "datasets": [...]
  }
}
```

**负荷预警：**
```json
[
  {
    "user_name": "张三",
    "workload_saturation": 125.5,
    "alert_level": "CRITICAL",
    "recommendations": [...]
  }
]
```

---

## 🔄 更新日志

### v1.0.0 (2024-01-15)
- ✨ 初始版本
- ✅ 6种分析功能
- ✅ 4种预测功能
- ✅ 3种预测算法
- ✅ 20+测试用例
- ✅ 完整文档

---

## 📞 支持

- 📧 Email: support@example.com
- 📖 文档：`/docs/timesheet_analytics_guide.md`
- 🐛 问题反馈：GitHub Issues

---

## 📄 许可证

Copyright © 2024 工时分析系统开发团队
