# 技术评估系统测试指南

## 一、测试前准备

### 1. 数据库迁移

确保已执行数据库迁移：

```bash
# SQLite 数据库迁移
sqlite3 data/app.db < migrations/20260117_technical_assessment_system_sqlite.sql

# 或使用 Python 执行
python3 -c "from app.models.base import init_db; init_db()"
```

### 2. 初始化评分规则

```bash
python3 scripts/seed_scoring_rules.py
```

### 3. 启动服务器

```bash
uvicorn app.main:app --reload
```

## 二、API 测试

### 1. 使用测试脚本

```bash
python3 test_technical_assessment.py
```

### 2. 手动测试步骤

#### 步骤1: 登录获取Token

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

#### 步骤2: 获取评分规则列表

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/sales/scoring-rules" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 步骤3: 创建失败案例

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/sales/failure-cases" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "case_code": "FC-20260117-001",
    "project_name": "测试失败项目",
    "industry": "新能源",
    "failure_tags": "[\"需求不明确\"]",
    "core_failure_reason": "客户需求频繁变更",
    "early_warning_signals": "[\"需求文档不完整\"]",
    "lesson_learned": "需要在项目前期充分沟通需求",
    "keywords": "[\"需求变更\"]"
  }'
```

#### 步骤4: 申请技术评估（线索）

```bash
# 先获取一个线索ID
curl -X GET "http://127.0.0.1:8000/api/v1/sales/leads?page=1&page_size=1" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 申请评估（替换 LEAD_ID）
curl -X POST "http://127.0.0.1:8000/api/v1/sales/leads/LEAD_ID/assessments/apply" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### 步骤5: 执行技术评估

```bash
# 替换 ASSESSMENT_ID
curl -X POST "http://127.0.0.1:8000/api/v1/sales/assessments/ASSESSMENT_ID/evaluate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "requirement_data": {
      "industry": "新能源",
      "customerType": "新客户",
      "budgetStatus": "明确",
      "techRequirements": "电池测试设备",
      "requirementMaturity": 3
    },
    "enable_ai": false
  }'
```

#### 步骤6: 获取评估结果

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/sales/assessments/ASSESSMENT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 步骤7: 创建未决事项

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/sales/leads/LEAD_ID/open-items" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "item_type": "INTERFACE",
    "description": "接口协议文档尚未提供",
    "responsible_party": "CUSTOMER",
    "due_date": "2026-02-01T00:00:00",
    "blocks_quotation": true
  }'
```

## 三、功能验证清单

### ✅ 数据模型
- [x] TechnicalAssessment 表已创建
- [x] ScoringRule 表已创建
- [x] FailureCase 表已创建
- [x] LeadRequirementDetail 表已创建
- [x] OpenItem 表已创建
- [x] Lead 和 Opportunity 表已扩展

### ✅ API端点
- [x] 申请技术评估（线索/商机）
- [x] 执行技术评估
- [x] 获取评估列表和详情
- [x] 评分规则管理
- [x] 失败案例库管理
- [x] 未决事项管理
- [x] 相似案例查找

### ✅ 评估引擎
- [x] 五维评分计算
- [x] 一票否决检查
- [x] 相似案例匹配
- [x] 决策建议生成
- [x] 风险分析

### ✅ 阶段门集成
- [x] G1阶段门可选检查技术评估状态
- [x] 未决事项阻塞检查

### ✅ 权限控制
- [x] 技术评估权限检查
- [x] 角色权限映射

## 四、前端测试

### 1. 访问技术评估页面

```
http://localhost:5173/sales/assessments/lead/LEAD_ID
http://localhost:5173/sales/assessments/opportunity/OPP_ID
```

### 2. 访问需求详情页面

```
http://localhost:5173/sales/leads/LEAD_ID/requirement
```

### 3. 访问未决事项管理页面

```
http://localhost:5173/sales/lead/LEAD_ID/open-items
http://localhost:5173/sales/opportunity/OPP_ID/open-items
```

## 五、常见问题

### 1. 评估时提示"未找到启用的评分规则"

**解决**: 运行 `python3 scripts/seed_scoring_rules.py` 初始化评分规则

### 2. AI分析不可用

**说明**: AI分析是可选的，需要配置 `ALIBABA_API_KEY` 环境变量。未配置时系统正常工作，只是不提供AI分析。

### 3. 评估结果为空

**检查**:
- 评分规则是否正确加载
- 需求数据是否完整
- 评估服务是否正常执行

## 六、性能测试

### 评估执行时间

正常情况下，一次技术评估应在 1-3 秒内完成（不含AI分析）。

### 并发测试

```bash
# 使用 ab 工具测试并发
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
  http://127.0.0.1:8000/api/v1/sales/scoring-rules
```

## 七、数据验证

### 检查评估数据完整性

```python
from app.models.base import get_session
from app.models.sales import TechnicalAssessment

db = get_session()
assessments = db.query(TechnicalAssessment).all()
for a in assessments:
    print(f"ID: {a.id}, 来源: {a.source_type}:{a.source_id}, 总分: {a.total_score}, 决策: {a.decision}")
```

## 八、下一步

1. 完善前端界面交互
2. 添加更多测试用例
3. 优化评估算法
4. 集成AI分析（如需要）
5. 添加评估历史记录查看






