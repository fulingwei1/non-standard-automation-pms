# 标准成本库管理 - 快速开始

## 🚀 5分钟快速上手

### 步骤1：确认数据库迁移已运行

```bash
cd ~/.openclaw/workspace/non-standard-automation-pms
sqlite3 data/pms.db < migrations/20260214_standard_cost_sqlite.sql
```

### 步骤2：查看示例数据

系统已预置15条示例标准成本数据：

**物料成本（5条）**
- MAT-001: 钢板Q235 (4.50元/kg)
- MAT-002: 不锈钢304 (15.80元/kg)
- MAT-003: 铝合金6061 (22.50元/kg)
- MAT-004: M8螺栓 (0.35元/个)
- MAT-005: 电焊条 (12.00元/kg)

**人工成本（5条）**
- LAB-001: 高级工程师 (1200元/人天)
- LAB-002: 中级工程师 (800元/人天)
- LAB-003: 初级工程师 (500元/人天)
- LAB-004: 高级技工 (600元/人天)
- LAB-005: 普通技工 (400元/人天)

**制造费用（5条）**
- OVH-001: 设备折旧 (50元/台时)
- OVH-002: 电费 (0.65元/度)
- OVH-003: 车间管理费 (20%)
- OVH-004: 质检成本 (2%)
- OVH-005: 工具损耗 (5%)

### 步骤3：API快速测试

#### 获取标准成本列表
```bash
curl -X GET "http://localhost:8000/api/v1/standard-costs/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 搜索钢材成本
```bash
curl -X GET "http://localhost:8000/api/v1/standard-costs/search?keyword=钢" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 创建新成本项
```bash
curl -X POST "http://localhost:8000/api/v1/standard-costs/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cost_code": "MAT-NEW-001",
    "cost_name": "新物料",
    "cost_category": "MATERIAL",
    "unit": "件",
    "standard_cost": 25.00,
    "cost_source": "VENDOR_QUOTE",
    "effective_date": "2026-03-01"
  }'
```

### 步骤4：批量导入

#### 下载模板
```bash
curl -X GET "http://localhost:8000/api/v1/standard-costs/template" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o standard_cost_template.xlsx
```

#### 上传导入
```python
import requests

url = "http://localhost:8000/api/v1/standard-costs/import"
headers = {"Authorization": "Bearer YOUR_TOKEN"}
files = {"file": open("my_costs.xlsx", "rb")}

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

---

## 📚 完整文档

- **用户指南:** `docs/standard_cost_user_guide.md`
- **API文档:** `docs/standard_cost_api.md`
- **导入指南:** `docs/standard_cost_import_guide.md`
- **完成报告:** `标准成本库管理-实现完成报告.md`

---

## 🔑 权限说明

### 需要的权限

- **cost:read** - 查看标准成本（所有GET端点）
- **cost:manage** - 管理标准成本（POST/PUT/DELETE端点）

### 如何分配权限

1. 登录系统管理后台
2. 进入"角色管理"
3. 为目标角色添加 `cost:read` 和/或 `cost:manage` 权限
4. 将角色分配给用户

---

## ❓ 常见问题

### Q: 成本编码有什么规范？

**A:** 建议使用以下格式：
- 物料成本：MAT-XXX
- 人工成本：LAB-XXX
- 制造费用：OVH-XXX

### Q: 如何更新标准成本？

**A:** 使用PUT请求更新，系统会自动创建新版本，保留历史版本。

```bash
curl -X PUT "http://localhost:8000/api/v1/standard-costs/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"standard_cost": 5.00, "notes": "价格上涨"}'
```

### Q: 批量导入支持多少条数据？

**A:** 
- 推荐：每次100-500条
- 上限：建议不超过1000条
- 超过1000条建议分批导入

### Q: 如何应用标准成本到项目？

**A:** 使用项目集成API：

```bash
curl -X POST "http://localhost:8000/api/v1/standard-costs/projects/1/costs/apply-standard" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "cost_items": [
      {"cost_code": "MAT-001", "quantity": 100}
    ],
    "budget_name": "标准成本预算"
  }'
```

---

## 🎯 下一步

1. **探索API** - 查看完整API文档
2. **导入数据** - 使用批量导入功能
3. **项目集成** - 将标准成本应用到项目预算
4. **成本分析** - 使用成本对比功能

---

## 📞 获取帮助

- **技术支持:** support@company.com
- **API文档:** `/api/v1/docs` (Swagger UI)
- **用户指南:** 见上述文档链接

Happy Coding! 🎉
