# Team 6 - 异常处理流程增强测试指南

## 1. 环境准备

### 1.1 安装依赖
```bash
cd ~/.openclaw/workspace/non-standard-automation-pms
pip install -r requirements.txt
```

### 1.2 数据库迁移
```bash
# 执行迁移脚本
mysql -u your_user -p your_database < migrations/exception_enhancement_tables.sql
```

或使用 Alembic:
```bash
alembic upgrade head
```

## 2. 运行测试

### 2.1 运行所有异常处理增强测试
```bash
pytest tests/api/test_exception_enhancement.py -v
```

### 2.2 运行特定测试类
```bash
# 测试异常升级
pytest tests/api/test_exception_enhancement.py::TestExceptionEscalation -v

# 测试流程跟踪
pytest tests/api/test_exception_enhancement.py::TestFlowTracking -v

# 测试知识库
pytest tests/api/test_exception_enhancement.py::TestKnowledge -v

# 测试统计分析
pytest tests/api/test_exception_enhancement.py::TestStatistics -v

# 测试PDCA
pytest tests/api/test_exception_enhancement.py::TestPDCA -v

# 测试重复异常分析
pytest tests/api/test_exception_enhancement.py::TestRecurrenceAnalysis -v
```

### 2.3 运行特定测试用例
```bash
# 测试异常升级成功
pytest tests/api/test_exception_enhancement.py::TestExceptionEscalation::test_escalate_exception_success -v

# 测试PDCA完整周期
pytest tests/api/test_exception_enhancement.py::TestPDCA::test_pdca_full_cycle -v
```

### 2.4 生成覆盖率报告
```bash
pytest tests/api/test_exception_enhancement.py --cov=app.api.v1.endpoints.production.exception_enhancement --cov-report=html
```

查看报告：
```bash
open htmlcov/index.html
```

## 3. 测试用例清单

### 3.1 异常升级（TestExceptionEscalation）
- ✅ test_escalate_exception_success - 升级成功
- ✅ test_escalate_exception_not_found - 异常不存在
- ✅ test_escalate_multiple_levels - 多级升级

### 3.2 流程跟踪（TestFlowTracking）
- ✅ test_get_flow_tracking - 获取流程跟踪
- ✅ test_get_flow_not_found - 流程不存在

### 3.3 知识库（TestKnowledge）
- ✅ test_create_knowledge - 创建知识
- ✅ test_search_knowledge_by_keyword - 关键词搜索
- ✅ test_search_knowledge_by_type - 类型搜索
- ✅ test_search_knowledge_pagination - 分页查询

### 3.4 统计分析（TestStatistics）
- ✅ test_get_statistics - 获取统计数据
- ✅ test_get_statistics_with_date_range - 日期范围统计

### 3.5 PDCA（TestPDCA）
- ✅ test_create_pdca - 创建PDCA
- ✅ test_advance_pdca_to_do - 推进到Do阶段
- ✅ test_pdca_stage_validation - 阶段验证
- ✅ test_pdca_full_cycle - 完整周期

### 3.6 重复异常分析（TestRecurrenceAnalysis）
- ✅ test_analyze_recurrence - 重复异常分析
- ✅ test_analyze_recurrence_by_type - 按类型分析

**总计：20+ 测试用例**

## 4. 手工测试

### 4.1 使用 Swagger UI
1. 启动应用：`uvicorn app.main:app --reload`
2. 访问：`http://localhost:8000/docs`
3. 找到 `production-exception-enhancement` 标签
4. 测试各个接口

### 4.2 使用 cURL

#### 异常升级
```bash
curl -X POST "http://localhost:8000/api/v1/production/exception/escalate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exception_id": 1,
    "reason": "超过2小时未处理",
    "escalation_level": "LEVEL_1",
    "escalated_to_id": 2
  }'
```

#### 查询流程
```bash
curl -X GET "http://localhost:8000/api/v1/production/exception/1/flow" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 创建知识
```bash
curl -X POST "http://localhost:8000/api/v1/production/exception/knowledge" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "设备故障处理",
    "exception_type": "EQUIPMENT",
    "exception_level": "MAJOR",
    "symptom_description": "设备异响",
    "solution": "更换零件",
    "keywords": "设备,故障"
  }'
```

#### 搜索知识
```bash
curl -X GET "http://localhost:8000/api/v1/production/exception/knowledge/search?keyword=设备" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 统计分析
```bash
curl -X GET "http://localhost:8000/api/v1/production/exception/statistics" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 创建PDCA
```bash
curl -X POST "http://localhost:8000/api/v1/production/exception/pdca" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exception_id": 1,
    "plan_description": "问题描述",
    "plan_root_cause": "根本原因",
    "plan_target": "改善目标",
    "plan_owner_id": 1
  }'
```

#### 推进PDCA
```bash
curl -X PUT "http://localhost:8000/api/v1/production/exception/pdca/1/advance" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "DO",
    "do_action_taken": "实施措施",
    "do_owner_id": 1
  }'
```

#### 重复异常分析
```bash
curl -X GET "http://localhost:8000/api/v1/production/exception/recurrence?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 5. 测试数据准备

### 5.1 创建测试异常
```sql
INSERT INTO production_exception (
    exception_no, exception_type, exception_level,
    title, description, reporter_id, status
) VALUES
    ('EXC-TEST-001', 'EQUIPMENT', 'MAJOR', '设备故障', '主轴异响', 1, 'REPORTED'),
    ('EXC-TEST-002', 'QUALITY', 'CRITICAL', '质量问题', '尺寸超差', 1, 'REPORTED'),
    ('EXC-TEST-003', 'MATERIAL', 'MINOR', '物料短缺', '原材料不足', 1, 'PROCESSING');
```

### 5.2 创建测试用户
```sql
INSERT INTO users (username, email, hashed_password)
VALUES
    ('test_handler', 'handler@test.com', 'hashed_password'),
    ('test_verifier', 'verifier@test.com', 'hashed_password');
```

## 6. 验收标准

### 6.1 功能验收
- ✅ 8个API全部可用
- ✅ 状态机验证通过（PDCA阶段转换）
- ✅ 流程测试通过（异常升级、流程跟踪）
- ✅ 知识库搜索准确
- ✅ 统计数据正确

### 6.2 性能验收
- ✅ API响应时间 < 500ms（95分位）
- ✅ 知识库搜索 < 200ms
- ✅ 统计分析 < 1s

### 6.3 质量验收
- ✅ 测试覆盖率 ≥ 80%
- ✅ 代码无语法错误
- ✅ 所有测试用例通过

## 7. 问题排查

### 7.1 数据库连接失败
检查数据库配置：
```bash
cat .env | grep DATABASE
```

### 7.2 导入错误
检查模型导入：
```python
from app.models.production import (
    ExceptionHandlingFlow,
    ExceptionKnowledge,
    ExceptionPDCA,
)
```

### 7.3 测试失败
查看详细日志：
```bash
pytest tests/api/test_exception_enhancement.py -v -s
```

## 8. 持续集成

### 8.1 GitHub Actions
```yaml
# .github/workflows/test_exception_enhancement.yml
name: Test Exception Enhancement

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/api/test_exception_enhancement.py -v --cov
```

## 9. 文档清单

- ✅ 异常处理流程设计文档.md
- ✅ PDCA管理手册.md
- ✅ 知识库使用指南.md
- ✅ Team_6_测试指南.md
- ✅ 数据库迁移脚本.sql

## 10. 联系方式

如有问题，请联系：
- Team 6 负责人
- 技术支持：tech-support@company.com
