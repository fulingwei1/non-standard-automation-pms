# 物料批次管理操作手册

## 目录
1. [概述](#概述)
2. [批次入库](#批次入库)
3. [批次查询](#批次查询)
4. [批次消耗](#批次消耗)
5. [批次追溯](#批次追溯)
6. [条码扫描](#条码扫描)
7. [常见问题](#常见问题)

---

## 概述

### 什么是批次管理?
批次管理是对物料按批次进行全流程追踪的管理方式。每个批次都有唯一的批次号,记录了物料的来源、生产日期、质检状态、存储位置等信息。

### 为什么需要批次管理?
- ✅ **质量追溯**: 出现质量问题时,可快速定位到具体批次
- ✅ **先进先出**: 按批次管理,优先使用早期批次
- ✅ **过期管理**: 及时发现即将过期的批次
- ✅ **成本核算**: 精确计算每个批次的成本
- ✅ **供应商评估**: 追溯到供应商批次,评估供应商质量

---

## 批次入库

### 场景1: 采购入库

#### 操作步骤

1. **接收物料**
   - 验收物料数量和外观
   - 核对采购订单信息

2. **创建批次记录**
   ```http
   POST /production/material/batch
   {
     "batch_no": "BATCH-20260216-001",
     "material_id": 1,
     "supplier_id": 10,
     "supplier_batch_no": "SUP-BATCH-001",
     "initial_qty": 1000,
     "production_date": "2026-02-10",
     "expire_date": "2027-02-10",
     "warehouse_location": "A-01-01"
   }
   ```

3. **质检**
   - 进行质量检验
   - 更新质检状态
   ```http
   PATCH /production/material/batch/1
   {
     "quality_status": "QUALIFIED",
     "quality_report_no": "QC-20260216-001",
     "quality_inspector_id": 5
   }
   ```

4. **生成条码/二维码**
   - 系统自动生成批次条码
   - 打印粘贴到物料包装上

5. **上架存储**
   - 按照仓库位置存放
   - 更新存储位置信息

#### 注意事项
- ⚠️ 批次号必须唯一
- ⚠️ 生产日期不能晚于入库日期
- ⚠️ 失效日期必须晚于生产日期
- ⚠️ 仓库位置格式: `{区}-{排}-{列}` (如: A-01-01)

---

### 场景2: 生产入库

对于自产物料(半成品、成品),同样需要创建批次:

```http
POST /production/material/batch
{
  "batch_no": "PROD-20260216-001",
  "material_id": 100,
  "production_date": "2026-02-16",
  "initial_qty": 500,
  "quality_status": "QUALIFIED",
  "warehouse_location": "B-02-03"
}
```

---

## 批次查询

### 查询所有批次

**API调用**:
```http
GET /production/material/realtime-stock?material_id=1
```

**响应示例**:
```json
{
  "material_code": "MAT001",
  "material_name": "电机",
  "current_stock": 500,
  "batches": [
    {
      "batch_no": "BATCH-20260215-001",
      "current_qty": 300,
      "available_qty": 280,
      "reserved_qty": 20,
      "warehouse_location": "A-01-01",
      "production_date": "2026-02-10",
      "expire_date": "2027-02-10",
      "quality_status": "QUALIFIED"
    },
    {
      "batch_no": "BATCH-20260216-001",
      "current_qty": 200,
      "available_qty": 200,
      "reserved_qty": 0,
      "warehouse_location": "A-01-02",
      "production_date": "2026-02-15",
      "expire_date": "2027-02-15",
      "quality_status": "QUALIFIED"
    }
  ]
}
```

### 按条件筛选

**按仓库位置**:
```http
GET /production/material/realtime-stock?warehouse_location=A-01
```

**按质检状态**:
```http
GET /production/material/realtime-stock?quality_status=QUALIFIED
```

**按批次状态**:
```http
GET /production/material/realtime-stock?status=ACTIVE
```

---

## 批次消耗

### 生产领料流程

#### 步骤1: 创建领料单
```http
POST /production/material-requisition
{
  "work_order_id": 100,
  "applicant_id": 10,
  "items": [
    {
      "material_id": 1,
      "request_qty": 50
    }
  ]
}
```

#### 步骤2: 审批领料单
```http
PATCH /production/material-requisition/1/approve
{
  "approved_by": 5,
  "approved_qty": 50
}
```

#### 步骤3: 发料并记录消耗
```http
POST /production/material/consumption
{
  "material_id": 1,
  "batch_id": 10,
  "consumption_qty": 50,
  "consumption_type": "PRODUCTION",
  "work_order_id": 100,
  "requisition_id": 1,
  "operator_id": 10,
  "standard_qty": 48
}
```

**响应**:
```json
{
  "code": 0,
  "message": "物料消耗记录成功",
  "data": {
    "id": 1001,
    "consumption_no": "CONS-20260216121530-MAT001",
    "is_waste": false,
    "variance_rate": 4.17
  }
}
```

### 批次选择策略

#### 先进先出 (FIFO)
优先使用生产日期最早的批次:
```sql
SELECT * FROM material_batch
WHERE material_id = 1 AND status = 'ACTIVE'
ORDER BY production_date ASC
LIMIT 1;
```

#### 就近原则
优先使用同一仓库位置的批次:
```sql
SELECT * FROM material_batch
WHERE material_id = 1 AND warehouse_location = 'A-01-01'
ORDER BY current_qty DESC;
```

#### 避免过期
不使用即将过期(30天内)的批次:
```sql
SELECT * FROM material_batch
WHERE material_id = 1
  AND status = 'ACTIVE'
  AND (expire_date IS NULL OR expire_date > CURRENT_DATE + INTERVAL '30 days')
ORDER BY production_date ASC;
```

---

## 批次追溯

### 正向追溯: 批次 → 产品

**场景**: 某批次质量有问题,需要追溯使用了该批次的所有产品

#### 操作步骤

1. **通过批次号查询**
   ```http
   GET /production/material/batch-tracing?batch_no=BATCH-20260215-001
   ```

2. **查看消耗记录**
   ```json
   {
     "batch_info": {
       "batch_no": "BATCH-20260215-001",
       "material_code": "MAT001",
       "material_name": "电机",
       "initial_qty": 1000,
       "consumed_qty": 600
     },
     "consumption_trail": [
       {
         "consumption_no": "CONS-001",
         "consumption_date": "2026-02-16T10:30:00",
         "consumption_qty": 50,
         "project": {
           "id": 10,
           "project_no": "PRJ-2026-001",
           "project_name": "自动化生产线"
         },
         "work_order": {
           "id": 100,
           "work_order_no": "WO-2026-001"
         }
       }
     ],
     "summary": {
       "total_consumptions": 12,
       "projects_count": 3,
       "work_orders_count": 5
     }
   }
   ```

3. **导出追溯报告**
   - 生成PDF/Excel报告
   - 包含完整的追溯链路

#### 应用场景
- 🔍 质量问题追溯
- 🔍 召回管理
- 🔍 客户投诉处理
- 🔍 供应商质量评估

---

### 反向追溯: 产品 → 批次

**场景**: 某产品出现问题,需要查找使用了哪些批次的物料

#### 操作步骤

1. **通过项目/工单查询**
   ```http
   GET /production/material/batch-tracing?project_id=10&trace_direction=backward
   ```

2. **查看物料批次清单**
   ```json
   {
     "project_info": {
       "id": 10,
       "project_no": "PRJ-2026-001",
       "project_name": "自动化生产线"
     },
     "material_batches": [
       {
         "material_code": "MAT001",
         "material_name": "电机",
         "batches": [
           {
             "batch_no": "BATCH-20260215-001",
             "supplier_batch_no": "SUP-001",
             "consumption_qty": 50,
             "supplier": "XX供应商"
           }
         ]
       }
     ]
   }
   ```

#### 应用场景
- 🔍 产品质量分析
- 🔍 成本核算
- 🔍 供应商追溯

---

## 条码扫描

### 扫码录入消耗

#### 操作流程

1. **打开扫码界面**
   - 移动端App或PDA设备
   - Web端摄像头扫码

2. **扫描批次条码**
   ```
   扫描结果: BATCH-20260215-001
   ```

3. **自动填充信息**
   - 系统自动识别批次
   - 显示物料信息、当前库存

4. **输入消耗数量**
   ```
   物料: 电机 (MAT001)
   批次: BATCH-20260215-001
   当前库存: 300件
   消耗数量: [50] 件
   ```

5. **提交消耗**
   ```http
   POST /production/material/consumption
   {
     "barcode": "BATCH-20260215-001",
     "consumption_qty": 50,
     "consumption_type": "PRODUCTION",
     "work_order_id": 100
   }
   ```

### 二维码信息

**扫描二维码可获取**:
- 批次号
- 物料编码和名称
- 数量
- 生产日期
- 失效日期
- 供应商信息

**示例**:
```
批次号: BATCH-20260215-001
物料: 电机 (MAT001)
数量: 1000 件
生产日期: 2026-02-15
失效日期: 2027-02-15
供应商: XX机电有限公司
```

---

## 常见问题

### Q1: 批次号命名规则是什么?

**A**: 批次号格式建议:
```
BATCH-{日期}-{流水号}
示例: BATCH-20260216-001

或按物料分组:
{物料编码}-BATCH-{日期}-{流水号}
示例: MAT001-BATCH-20260216-001
```

**注意**: 批次号必须全局唯一!

---

### Q2: 批次已耗尽还能追溯吗?

**A**: 可以! 批次状态变为`DEPLETED`后,记录仍然保留,可以继续追溯历史消耗记录。

---

### Q3: 如何处理过期批次?

**操作步骤**:

1. **系统自动标记**
   - 每日定时任务检查过期批次
   - 状态自动更新为`EXPIRED`

2. **生成过期预警**
   ```http
   GET /production/material/alerts?alert_type=EXPIRED
   ```

3. **处理方案**
   - 报废: 创建消耗记录,类型为`WASTE`
   - 延期使用: 经审批后修改失效日期
   - 退货: 创建退货单

---

### Q4: 批次库存为负数怎么办?

**A**: 正常情况下不应出现负数。如果出现:

1. **检查数据**
   - 查看消耗记录是否重复
   - 检查是否有误操作

2. **库存调整**
   ```http
   PATCH /production/material/batch/1
   {
     "current_qty": 100,
     "adjustment_reason": "盘点调整",
     "adjusted_by": 5
   }
   ```

3. **预防措施**
   - 开启库存校验: 消耗数量不能超过当前库存
   - 定期盘点核对

---

### Q5: 如何合并多个批次?

**A**: 系统不支持批次合并。原因:
- 批次追溯需要保持独立性
- 不同批次可能有不同的质量状态

**替代方案**:
- 保持批次独立管理
- 通过仓库位置归类
- 使用先进先出策略自然消耗

---

### Q6: 批次号重复了怎么办?

**A**: 批次号是唯一约束,系统会阻止创建重复批次。

如果确实需要修改:
```http
PATCH /production/material/batch/1
{
  "batch_no": "BATCH-20260216-002"
}
```

**注意**: 修改批次号会影响已打印的条码!

---

### Q7: 条码扫不出来?

**排查步骤**:

1. **检查条码清晰度**
   - 是否污损、褪色
   - 打印质量是否合格

2. **检查扫码设备**
   - 扫码枪是否正常
   - 摄像头权限是否开启

3. **手动输入**
   - 暂时手动输入批次号
   - 重新打印条码

---

### Q8: 批次追溯报告如何导出?

**操作**:
```http
GET /production/material/batch-tracing?batch_no=BATCH-20260215-001&format=pdf
```

**报告包含**:
- 批次基本信息
- 消耗记录列表
- 使用项目/工单
- 追溯路径图

---

## 最佳实践

### ✅ DO (推荐做法)

1. **及时录入批次信息**
   - 物料到货后24小时内完成批次创建

2. **规范批次号命名**
   - 使用统一的命名规则
   - 包含日期信息便于查找

3. **定期盘点**
   - 每月盘点核对批次库存
   - 及时发现差异并调整

4. **条码管理**
   - 确保条码清晰可扫
   - 损坏及时补打

5. **先进先出**
   - 优先使用早期批次
   - 避免物料过期

### ❌ DON'T (避免做法)

1. **不录入批次信息**
   - 失去追溯能力

2. **批次号随意命名**
   - 难以管理和查找

3. **忽视过期批次**
   - 造成质量隐患

4. **超量领料不记录**
   - 库存数据不准确

5. **不做批次追溯**
   - 质量问题无法定位

---

## 操作权限

| 操作 | 所需权限 | 备注 |
|-----|---------|------|
| 查看批次信息 | `material:read` | 所有人 |
| 创建批次 | `material:batch:create` | 仓库管理员 |
| 更新批次 | `material:batch:update` | 仓库管理员 |
| 批次消耗 | `material:consume` | 领料人员 |
| 批次追溯 | `material:trace` | 质量/生产人员 |
| 库存调整 | `material:adjust` | 仓库主管 |

---

## 联系支持

如有问题,请联系:
- 📧 Email: support@example.com
- 📱 企业微信: 物料管理支持组
- 🔧 内部工单: 提交IT工单

---

**手册版本**: v1.0  
**更新日期**: 2026-02-16  
**编写**: Team 5 - 物料跟踪系统  
