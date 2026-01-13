# 技术评估系统快速开始指南

## 一、系统初始化

### 1. 执行数据库迁移

```bash
# SQLite
sqlite3 data/app.db < migrations/20260117_technical_assessment_system_sqlite.sql

# MySQL（生产环境）
mysql -u user -p database < migrations/20260117_technical_assessment_system_mysql.sql
```

### 2. 初始化评分规则

```bash
python3 scripts/seed_scoring_rules.py
```

### 3. 安装依赖（如需要）

```bash
pip install httpx==0.27.0  # AI服务需要
```

## 二、启动服务

### 后端服务

```bash
uvicorn app.main:app --reload
```

### 前端服务（如需要）

```bash
cd frontend && npm run dev
```

## 三、快速测试

### 数据库层测试（不需要服务器）

```bash
python3 scripts/quick_test_assessment.py
```

### API测试（需要服务器运行）

```bash
# 1. 启动服务器
uvicorn app.main:app --reload

# 2. 在另一个终端运行测试
python3 test_technical_assessment.py
```

## 四、使用流程

### 1. 申请技术评估

**线索阶段**:
```
POST /api/v1/sales/leads/{lead_id}/assessments/apply
```

**商机阶段**:
```
POST /api/v1/sales/opportunities/{opp_id}/assessments/apply
```

### 2. 执行技术评估

```
POST /api/v1/sales/assessments/{assessment_id}/evaluate
Body: {
  "requirement_data": {
    "industry": "新能源",
    "customerType": "新客户",
    "budgetStatus": "明确",
    ...
  },
  "enable_ai": false  // 可选，需要配置API密钥
}
```

### 3. 查看评估结果

```
GET /api/v1/sales/assessments/{assessment_id}
```

### 4. 管理未决事项

```
# 创建未决事项
POST /api/v1/sales/leads/{lead_id}/open-items
Body: {
  "item_type": "INTERFACE",
  "description": "接口协议文档尚未提供",
  "responsible_party": "CUSTOMER",
  "blocks_quotation": true
}

# 查看未决事项列表
GET /api/v1/sales/open-items?source_type=LEAD&source_id={lead_id}
```

## 五、前端访问

### 技术评估页面
```
http://localhost:5173/sales/assessments/lead/{lead_id}
http://localhost:5173/sales/assessments/opportunity/{opp_id}
```

### 需求详情页面
```
http://localhost:5173/sales/leads/{lead_id}/requirement
```

### 未决事项管理页面
```
http://localhost:5173/sales/lead/{lead_id}/open-items
http://localhost:5173/sales/opportunity/{opp_id}/open-items
```

## 六、配置AI分析（可选）

### 1. 设置环境变量

```bash
export ALIBABA_API_KEY="your-api-key"
export ALIBABA_MODEL="qwen-plus"  # 可选，默认值
```

### 2. 在评估时启用AI

```json
{
  "requirement_data": {...},
  "enable_ai": true
}
```

## 七、常见问题

### Q: 评估时提示"未找到启用的评分规则"
**A**: 运行 `python3 scripts/seed_scoring_rules.py` 初始化评分规则

### Q: AI分析不可用
**A**: AI分析是可选的，需要配置 `ALIBABA_API_KEY`。未配置时系统正常工作。

### Q: 评估分数为0
**A**: 检查需求数据是否完整，确保字段名称与评分规则中的字段匹配。

### Q: 相似案例匹配不到
**A**: 确保失败案例库中有相关数据，检查行业、产品类型等匹配条件。

## 八、测试数据

### 创建测试线索
```bash
python3 scripts/create_test_lead.py
```

### 查看测试结果
```bash
python3 scripts/quick_test_assessment.py
```

## 九、API文档

启动服务器后访问：
```
http://127.0.0.1:8000/docs
```

查看完整API文档和交互式测试界面。

## 十、下一步

1. ✅ 系统已就绪，可以开始使用
2. 📝 根据实际业务需求调整评分规则
3. 📊 收集使用数据，优化评估算法
4. 🤖 配置AI分析（如需要）
5. 📈 监控评估结果，持续改进

---

**系统状态**: ✅ 已就绪
**测试状态**: ✅ 全部通过
**文档完整度**: ✅ 100%






