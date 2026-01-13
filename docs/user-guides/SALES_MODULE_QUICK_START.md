# 销售模块快速开始指南

## 快速测试

### 1. 启动服务器

```bash
cd 非标自动化项目管理系统
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. 初始化数据库（如果还没有）

```bash
python3 init_db.py
```

### 3. 运行测试脚本

**Python版本（推荐）：**
```bash
python3 test_sales_apis.py
```

**Bash版本：**
```bash
bash test_sales_apis.sh
```

## API 快速参考

### 认证

```bash
# 登录获取Token
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### 线索管理

```bash
# 创建线索（自动生成编码）
curl -X POST "http://127.0.0.1:8000/api/v1/sales/leads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "测试客户",
    "contact_name": "张三",
    "contact_phone": "13800138000",
    "demand_summary": "需要自动化测试设备"
  }'

# 获取线索列表
curl -X GET "http://127.0.0.1:8000/api/v1/sales/leads?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# 线索转商机
curl -X POST "http://127.0.0.1:8000/api/v1/sales/leads/{lead_id}/convert?customer_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

### 商机管理

```bash
# 创建商机（自动生成编码）
curl -X POST "http://127.0.0.1:8000/api/v1/sales/opportunities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "opp_name": "测试客户 - 自动化测试设备项目",
    "stage": "DISCOVERY",
    "est_amount": 100000,
    "requirement": {
      "product_object": "PCB板",
      "ct_seconds": 1,
      "acceptance_criteria": "节拍≤1秒"
    }
  }'

# 提交阶段门
curl -X POST "http://127.0.0.1:8000/api/v1/sales/opportunities/{opp_id}/gate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "gate_status": "PASS",
    "remark": "通过G1阶段门"
  }'
```

### 报价管理

```bash
# 创建报价（自动生成编码）
curl -X POST "http://127.0.0.1:8000/api/v1/sales/quotes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_id": 1,
    "customer_id": 1,
    "version": {
      "version_no": "V1",
      "total_price": 100000,
      "cost_total": 70000,
      "gross_margin": 30,
      "items": [
        {
          "item_type": "MODULE",
          "item_name": "测试模块",
          "qty": 1,
          "unit_price": 50000,
          "cost": 35000
        }
      ]
    }
  }'

# 审批报价
curl -X POST "http://127.0.0.1:8000/api/v1/sales/quotes/{quote_id}/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "remark": "审批通过"
  }'
```

### 合同管理

```bash
# 创建合同（自动生成编码）
curl -X POST "http://127.0.0.1:8000/api/v1/sales/contracts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "opportunity_id": 1,
    "customer_id": 1,
    "contract_amount": 100000,
    "deliverables": [
      {
        "deliverable_name": "FAT报告",
        "deliverable_type": "验收报告",
        "required_for_payment": true
      }
    ]
  }'

# 合同签订
curl -X POST "http://127.0.0.1:8000/api/v1/sales/contracts/{contract_id}/sign" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "signed_date": "2025-01-15"
  }'

# 合同生成项目
curl -X POST "http://127.0.0.1:8000/api/v1/sales/contracts/{contract_id}/project" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_code": "PJ250115001",
    "project_name": "测试客户自动化测试设备项目",
    "pm_id": 1
  }'
```

### 发票管理

```bash
# 创建发票（自动生成编码）
curl -X POST "http://127.0.0.1:8000/api/v1/sales/invoices" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "contract_id": 1,
    "invoice_type": "SPECIAL",
    "amount": 30000,
    "tax_rate": 13,
    "buyer_name": "测试客户",
    "buyer_tax_no": "91110000MA01234567"
  }'

# 开票
curl -X POST "http://127.0.0.1:8000/api/v1/sales/invoices/{invoice_id}/issue" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_date": "2025-01-15"
  }'
```

### 统计报表

```bash
# 销售漏斗统计
curl -X GET "http://127.0.0.1:8000/api/v1/sales/statistics/funnel" \
  -H "Authorization: Bearer $TOKEN"

# 按阶段统计商机
curl -X GET "http://127.0.0.1:8000/api/v1/sales/statistics/opportunities-by-stage" \
  -H "Authorization: Bearer $TOKEN"

# 收入预测
curl -X GET "http://127.0.0.1:8000/api/v1/sales/statistics/revenue-forecast?months=3" \
  -H "Authorization: Bearer $TOKEN"
```

## 编码规则

所有编码支持自动生成，规则如下：

- **线索编码**：`L2507-001`（L + 年月 + 3位序号）
- **商机编码**：`O2507-001`（O + 年月 + 3位序号）
- **报价编码**：`Q2507-001`（Q + 年月 + 3位序号）
- **合同编码**：`HT2507-001`（HT + 年月 + 3位序号）
- **发票编码**：`INV-yymmdd-xxx`（INV + 日期 + 3位序号）

创建时可以不提供编码，系统会自动生成。

## API 文档

启动服务器后，访问：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 常见问题

### 1. 如何获取客户ID？

```bash
# 获取客户列表
curl -X GET "http://127.0.0.1:8000/api/v1/customers?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. 如何查看完整的业务流程？

运行测试脚本会演示完整的业务流程：
```bash
python3 test_sales_apis.py
```

### 3. 数据库迁移失败怎么办？

确保已运行数据库初始化：
```bash
python3 init_db.py
```

如果仍有问题，检查迁移文件是否正确，特别是外键引用。

### 4. Token 过期怎么办？

重新登录获取新的Token：
```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

## 下一步

1. 查看完整文档：`SALES_MODULE_SUMMARY.md`
2. 运行测试脚本验证功能
3. 开始前端开发
4. 配置权限控制



