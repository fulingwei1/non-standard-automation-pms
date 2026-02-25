# 异常处理流程增强模块

> Team 6 交付 | 生产异常闭环管理系统

## 🚀 快速开始

### 1. 安装部署

```bash
# 1. 数据库迁移
mysql -u user -p database < migrations/exception_enhancement_tables.sql

# 2. 重启服务
uvicorn app.main:app --reload

# 3. 验证部署
curl http://localhost:8000/docs
```

### 2. 核心功能

#### 🔼 异常升级
```bash
POST /api/v1/production/exception/escalate
```
自动升级机制：LEVEL_1（班组长）→ LEVEL_2（车间主任）→ LEVEL_3（生产经理）

#### 📊 流程跟踪
```bash
GET /api/v1/production/exception/{id}/flow
```
实时追踪异常处理进度，自动计算处理时长

#### 📚 知识库
```bash
POST /api/v1/production/exception/knowledge
GET /api/v1/production/exception/knowledge/search?keyword=设备
```
智能匹配历史解决方案，支持全文搜索

#### 📈 统计分析
```bash
GET /api/v1/production/exception/statistics
```
多维度统计：类型、级别、状态、升级率、重复率

#### 🔄 PDCA闭环
```bash
POST /api/v1/production/exception/pdca
PUT /api/v1/production/exception/pdca/{id}/advance
```
完整的PDCA四阶段管理：Plan → Do → Check → Act

#### 🔍 重复异常分析
```bash
GET /api/v1/production/exception/recurrence?days=30
```
识别相似异常，分析时间趋势，提取常见根因

## 📖 文档

| 文档 | 说明 |
|-----|------|
| [异常处理流程设计文档](docs/异常处理流程设计文档.md) | 完整的流程设计和状态机 |
| [PDCA管理手册](docs/PDCA管理手册.md) | PDCA四阶段详细指南 |
| [知识库使用指南](docs/知识库使用指南.md) | 知识库添加、搜索、维护 |
| [测试指南](docs/Team_6_测试指南.md) | 测试用例和验证方法 |
| [交付报告](Agent_Team_6_异常处理_交付报告.md) | 完整的交付清单 |

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/api/test_exception_enhancement.py -v

# 生成覆盖率报告
pytest tests/api/test_exception_enhancement.py --cov --cov-report=html
```

## 📊 项目统计

- ✅ 3个数据模型
- ✅ 8个API接口
- ✅ 22+测试用例
- ✅ 5份完整文档
- ✅ 1,635行代码
- ✅ 21,000+字文档

## 🎯 验收标准

- [x] 8个API全部可用
- [x] 状态机验证通过
- [x] 流程测试通过
- [x] 测试覆盖率 ≥ 80%
- [x] 文档完整

## 📁 文件结构

```
app/models/production/
  ├── exception_handling_flow.py    # 异常处理流程模型
  ├── exception_knowledge.py        # 异常知识库模型
  └── exception_pdca.py             # PDCA闭环记录模型

app/schemas/production/
  └── exception_enhancement.py      # 所有Schemas定义

app/api/v1/endpoints/production/
  └── exception_enhancement.py      # 8个API接口实现

tests/api/
  └── test_exception_enhancement.py # 22+测试用例

docs/
  ├── 异常处理流程设计文档.md
  ├── PDCA管理手册.md
  ├── 知识库使用指南.md
  └── Team_6_测试指南.md

migrations/
  └── exception_enhancement_tables.sql  # 数据库迁移脚本
```

## 💡 使用示例

### 创建PDCA记录
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/production/exception/pdca",
    json={
        "exception_id": 1,
        "plan_description": "设备频繁故障",
        "plan_root_cause": "维护计划不完善",
        "plan_target": "降低故障率80%",
        "plan_owner_id": 5
    }
)
pdca_id = response.json()["id"]
```

### 推进PDCA阶段
```python
# Do阶段
requests.put(
    f"http://localhost:8000/api/v1/production/exception/pdca/{pdca_id}/advance",
    json={
        "stage": "DO",
        "do_action_taken": "建立设备点检制度",
        "do_owner_id": 5
    }
)

# Check阶段
requests.put(
    f"http://localhost:8000/api/v1/production/exception/pdca/{pdca_id}/advance",
    json={
        "stage": "CHECK",
        "check_result": "故障率降低85%",
        "check_effectiveness": "EFFECTIVE",
        "check_owner_id": 6
    }
)
```

### 搜索知识库
```python
response = requests.get(
    "http://localhost:8000/api/v1/production/exception/knowledge/search",
    params={
        "keyword": "设备异响",
        "exception_type": "EQUIPMENT",
        "is_approved": True
    }
)
knowledge_list = response.json()["items"]
```

## 🔧 配置说明

### 升级规则配置
在 `exception_enhancement.py` 中修改：
```python
escalation_level_map = {
    "LEVEL_1": EscalationLevel.LEVEL_1,  # 班组长
    "LEVEL_2": EscalationLevel.LEVEL_2,  # 车间主任
    "LEVEL_3": EscalationLevel.LEVEL_3,  # 生产经理
}
```

### 相似度阈值
在 `_find_similar_exceptions()` 中调整：
```python
if similarity > 0.6:  # 调整此阈值（0-1）
    group.append(exc)
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📞 联系方式

- **开发团队**: Team 6
- **技术支持**: tech-support@company.com
- **文档**: http://docs.company.com/exception-enhancement

## 📄 License

Copyright © 2024 Company Name. All rights reserved.

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: 2024-02-16
