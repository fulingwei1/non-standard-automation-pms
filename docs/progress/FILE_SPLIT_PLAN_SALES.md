# sales.py 文件拆分方案

> **文件大小**: 10,911行  
> **模块数**: 31个功能模块

## 拆分策略

按业务功能将 `sales.py` 拆分为多个独立模块，每个模块负责一个业务领域。

## 拆分方案

### 1. 核心业务模块

| 新文件 | 包含模块 | 预计行数 | 优先级 |
|--------|---------|---------|--------|
| `sales_leads.py` | 线索、线索管理补充 | ~400行 | P0 |
| `sales_opportunities.py` | 商机、商机管理补充 | ~500行 | P0 |
| `sales_quotes.py` | 报价、报价管理补充 | ~850行 | P0 |
| `sales_contracts.py` | 合同、合同管理补充 | ~700行 | P0 |
| `sales_invoices.py` | 发票、开票管理补充 | ~850行 | P0 |
| `sales_payments.py` | 回款管理 | ~850行 | P0 |
| `sales_statistics.py` | 统计报表、销售报表补充 | ~750行 | P1 |
| `sales_approval.py` | 审批工作流、审批工作流管理 | ~500行 | P1 |
| `sales_templates.py` | 模板 & CPQ | ~950行 | P1 |
| `sales_cost_management.py` | 报价成本管理、采购物料成本清单管理、物料成本更新提醒 | ~1,600行 | P1 |
| `sales_technical_assessment.py` | 技术评估 | ~750行 | P2 |
| `sales_requirements.py` | 需求详情管理、需求冻结管理、AI澄清管理 | ~1,200行 | P2 |
| `sales_team.py` | 销售团队管理与业绩排名、销售目标管理 | ~500行 | P2 |
| `sales_export.py` | 数据导出、PDF导出 | ~500行 | P2 |
| `sales_utils.py` | 编码生成函数、阶段门验证函数、公共工具 | ~400行 | P0 |

### 2. 拆分步骤

#### 第一步：提取公共工具（sales_utils.py）
- 编码生成函数（6个）
- 阶段门验证函数
- 其他公共辅助函数

#### 第二步：拆分核心业务模块（P0优先级）
1. `sales_leads.py` - 线索管理
2. `sales_opportunities.py` - 商机管理
3. `sales_quotes.py` - 报价管理
4. `sales_contracts.py` - 合同管理
5. `sales_invoices.py` - 发票管理
6. `sales_payments.py` - 回款管理

#### 第三步：拆分扩展模块（P1优先级）
7. `sales_statistics.py` - 统计报表
8. `sales_approval.py` - 审批工作流
9. `sales_templates.py` - 模板&CPQ
10. `sales_cost_management.py` - 成本管理

#### 第四步：拆分其他模块（P2优先级）
11. `sales_technical_assessment.py` - 技术评估
12. `sales_requirements.py` - 需求管理
13. `sales_team.py` - 销售团队
14. `sales_export.py` - 数据导出

#### 第五步：创建路由聚合文件
- `sales/__init__.py` - 聚合所有子路由

## 文件结构

```
app/api/v1/endpoints/sales/
├── __init__.py              # 路由聚合（~50行）
├── utils.py                 # 公共工具函数（~400行）
├── leads.py                 # 线索管理（~400行）
├── opportunities.py         # 商机管理（~500行）
├── quotes.py                # 报价管理（~850行）
├── contracts.py             # 合同管理（~700行）
├── invoices.py              # 发票管理（~850行）
├── payments.py              # 回款管理（~850行）
├── statistics.py            # 统计报表（~750行）
├── approval.py              # 审批工作流（~500行）
├── templates.py             # 模板&CPQ（~950行）
├── cost_management.py       # 成本管理（~1,600行）
├── technical_assessment.py  # 技术评估（~750行）
├── requirements.py          # 需求管理（~1,200行）
├── team.py                  # 销售团队（~500行）
└── export.py                # 数据导出（~500行）
```

## 路由聚合方式

在 `sales/__init__.py` 中：

```python
from fastapi import APIRouter
from . import leads, opportunities, quotes, contracts, invoices, payments
from . import statistics, approval, templates, cost_management
from . import technical_assessment, requirements, team, export

router = APIRouter()

# 聚合所有子路由
router.include_router(leads.router, tags=["sales-leads"])
router.include_router(opportunities.router, tags=["sales-opportunities"])
router.include_router(quotes.router, tags=["sales-quotes"])
# ... 其他路由
```

## 注意事项

1. **共享导入**: 公共导入放在 `utils.py` 或 `__init__.py`
2. **共享函数**: 公共工具函数放在 `utils.py`
3. **路由前缀**: 保持原有路由路径不变
4. **向后兼容**: 确保API路径不变
