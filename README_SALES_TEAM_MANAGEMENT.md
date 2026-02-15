# 销售团队管理 - 快速入门

## 🎯 功能概述

销售团队管理模块是一个完整的销售组织架构和目标管理系统，提供：

- **团队组织架构**：多层级团队管理，支持区域/产品/行业分类
- **销售目标管理**：公司/团队/个人三级目标，支持自动分解
- **销售区域管理**：区域划分和团队分配
- **统计分析**：团队排名、个人排名、完成趋势、分布统计

---

## 🚀 快速开始

### 1. 运行数据库迁移

```bash
cd non-standard-automation-pms
alembic upgrade head
```

### 2. 启动服务

```bash
python app/main.py
```

### 3. 访问 API 文档

浏览器打开：`http://localhost:8000/docs`

---

## 📁 项目结构

```
non-standard-automation-pms/
├── app/
│   ├── models/
│   │   └── sales/
│   │       ├── team.py           # 团队模型（现有）
│   │       ├── target_v2.py      # 目标模型 V2（新增）
│   │       └── region.py         # 区域模型（新增）
│   ├── schemas/
│   │   ├── sales_team.py         # 团队 schemas（新增）
│   │   └── sales_target.py       # 目标 schemas（新增）
│   ├── services/
│   │   ├── sales_team_service.py # 团队服务（新增）
│   │   └── sales_target_service.py # 目标服务（新增）
│   └── api/v1/endpoints/
│       ├── sales_teams.py        # 团队 API（新增）
│       ├── sales_targets.py      # 目标 API（新增）
│       └── sales_regions.py      # 区域 API（新增）
├── tests/
│   ├── test_sales_team.py        # 团队测试（新增）
│   ├── test_sales_target.py      # 目标测试（新增）
│   └── test_sales_region.py      # 区域测试（新增）
├── migrations/versions/
│   └── 20260215_sales_team_management.py  # 迁移脚本（新增）
└── docs/
    ├── sales_team_management_api.md       # API 文档（新增）
    ├── sales_team_management_guide.md     # 使用手册（新增）
    └── SALES_TEAM_MANAGEMENT_COMPLETION_REPORT.md  # 完成报告（新增）
```

---

## 🔧 核心 API 端点

### 销售团队

```bash
# 创建团队
POST /api/v1/sales-teams

# 获取团队列表
GET /api/v1/sales-teams

# 获取团队组织树
GET /api/v1/sales-teams/tree

# 添加成员
POST /api/v1/sales-teams/{id}/members

# 获取成员列表
GET /api/v1/sales-teams/{id}/members
```

### 销售目标

```bash
# 创建目标
POST /api/v1/sales-targets

# 获取目标列表
GET /api/v1/sales-targets

# 手动分解目标
POST /api/v1/sales-targets/{id}/breakdown

# 自动分解目标
POST /api/v1/sales-targets/{id}/auto-breakdown

# 获取分解树
GET /api/v1/sales-targets/{id}/breakdown-tree

# 团队排名
GET /api/v1/sales-targets/stats/team-ranking

# 个人排名
GET /api/v1/sales-targets/stats/personal-ranking

# 完成趋势
GET /api/v1/sales-targets/stats/completion-trend

# 完成率分布
GET /api/v1/sales-targets/stats/distribution
```

### 销售区域

```bash
# 创建区域
POST /api/v1/sales-regions

# 获取区域列表
GET /api/v1/sales-regions

# 分配团队
POST /api/v1/sales-regions/{id}/assign-team
```

---

## 💻 使用示例

### 创建团队

```bash
curl -X POST "http://localhost:8000/api/v1/sales-teams" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "team_code": "T001",
    "team_name": "华东团队",
    "team_type": "REGION",
    "description": "负责华东区域销售"
  }'
```

### 设置公司年度目标

```bash
curl -X POST "http://localhost:8000/api/v1/sales-targets" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "target_period": "year",
    "target_year": 2026,
    "target_type": "company",
    "sales_target": "10000000.00",
    "payment_target": "8000000.00",
    "new_customer_target": 50
  }'
```

### 自动分解目标

```bash
curl -X POST "http://localhost:8000/api/v1/sales-targets/1/auto-breakdown" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "breakdown_method": "EQUAL"
  }'
```

### 查看团队排名

```bash
curl -X GET "http://localhost:8000/api/v1/sales-targets/stats/team-ranking?target_year=2026&target_month=3" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/test_sales_*.py -v

# 运行团队测试
pytest tests/test_sales_team.py -v

# 运行目标测试
pytest tests/test_sales_target.py -v

# 运行区域测试
pytest tests/test_sales_region.py -v

# 查看测试覆盖率
pytest tests/test_sales_*.py --cov=app.services --cov=app.models.sales
```

---

## 📚 文档

- **API 文档**：`docs/sales_team_management_api.md`
- **使用手册**：`docs/sales_team_management_guide.md`
- **完成报告**：`docs/SALES_TEAM_MANAGEMENT_COMPLETION_REPORT.md`

---

## 🔑 权限配置

需要在权限系统中配置以下权限：

```sql
-- 销售团队权限
INSERT INTO api_permissions (resource, action, description) VALUES
('sales_team', 'view', '查看销售团队'),
('sales_team', 'create', '创建销售团队'),
('sales_team', 'update', '更新销售团队'),
('sales_team', 'delete', '删除销售团队');

-- 销售目标权限
INSERT INTO api_permissions (resource, action, description) VALUES
('sales_target', 'view', '查看销售目标'),
('sales_target', 'create', '创建销售目标'),
('sales_target', 'update', '更新销售目标'),
('sales_target', 'delete', '删除销售目标');

-- 销售区域权限
INSERT INTO api_permissions (resource, action, description) VALUES
('sales_region', 'view', '查看销售区域'),
('sales_region', 'create', '创建销售区域'),
('sales_region', 'update', '更新销售区域');
```

---

## ❓ 常见问题

### Q: 如何创建层级团队？

A: 在创建子团队时，设置 `parent_team_id` 为上级团队的 ID。

### Q: 目标分解后可以修改吗？

A: 可以。可以直接修改子目标的值，或删除后重新分解。

### Q: 支持跨期间的目标对比吗？

A: 目前支持查询历史目标数据，可以手动对比不同期间的目标。

### Q: 一个人可以有多个目标吗？

A: 可以。可以为同一个人设置不同期间的多个目标（如月度目标、季度目标）。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 License

MIT License

---

**开发完成日期**：2026-02-15  
**版本**：v1.0  
**维护者**：开发团队
