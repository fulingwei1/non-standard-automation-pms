# 报价单样例

本目录包含5个不同场景的报价单样例，供参考和测试使用。

## 样例列表

### 1. sample_01_basic.json - 基础版ERP
- **类型**: 基础版
- **总价**: ¥96,050
- **适用**: 小型企业
- **特点**: 简单实用，满足基本需求

### 2. sample_02_standard.json - 标准版ERP
- **类型**: 标准版
- **总价**: ¥187,110
- **适用**: 中型企业
- **特点**: 功能完整，性价比高

### 3. sample_03_premium.json - 高级版ERP
- **类型**: 高级版
- **总价**: ¥432,450
- **适用**: 大型企业
- **特点**: 全功能，VIP服务

### 4. sample_04_manufacturing.json - 生产管理系统
- **类型**: 标准版
- **总价**: ¥290,760
- **适用**: 制造业
- **特点**: 专业生产管理

### 5. sample_05_cloud_saas.json - 云端SaaS
- **类型**: 标准版
- **总价**: ¥198,170
- **适用**: 任何规模企业
- **特点**: SaaS模式，快速上线

## 使用方法

### 方法1: 通过API导入

```bash
curl -X POST "http://localhost:8000/api/v1/presale/ai/generate-quotation" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @sample_01_basic.json
```

### 方法2: Python脚本

```python
import json
import requests

with open('sample_01_basic.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

response = requests.post(
    'http://localhost:8000/api/v1/presale/ai/generate-quotation',
    headers={'Authorization': 'Bearer YOUR_TOKEN'},
    json=data
)

print(response.json())
```

## 价格计算说明

所有样例中的价格已经按照以下公式计算：

```
小计 = Σ(数量 × 单价)
税费 = 小计 × 税率
折扣 = 小计 × 折扣率
总计 = 小计 + 税费 - 折扣
```

## 修改建议

根据实际情况，您可能需要调整：

1. **presale_ticket_id** - 改为实际的工单ID
2. **customer_id** - 改为实际的客户ID
3. **价格** - 根据市场行情调整
4. **税率** - 根据当地税法调整
5. **折扣率** - 根据销售策略调整

## 测试建议

建议按顺序测试：

1. 先测试基础版（sample_01）
2. 再测试标准版（sample_02）
3. 然后测试高级版（sample_03）
4. 最后测试行业定制版（sample_04、sample_05）

每个样例都应该：
- ✅ 成功创建报价单
- ✅ 生成正确的报价单编号
- ✅ 价格计算准确
- ✅ 能够导出PDF
- ✅ 能够发送邮件
