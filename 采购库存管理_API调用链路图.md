# 采购库存管理系统 - API调用链路图

**生成时间**: 2026-02-16 10:26

---

## 📊 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React)                          │
│  23个页面 + 37个组件 + 3个API Service                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP/JSON (32个API)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   后端API层 (FastAPI)                        │
│  10个采购API + 12个库存API + 10个预警API                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ SQLAlchemy ORM
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  核心服务层 (Services)                        │
│  智能采购引擎 + 库存管理服务 + 智能预警引擎                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Database Operations
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   数据库 (PostgreSQL)                        │
│  13个业务表 + 索引 + 外键约束                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔗 API调用链路详解

### 模块1: 智能采购管理 (10条链路)

#### 链路1: 采购建议列表查询
```
前端页面:
  SuggestionsList.tsx
    ↓
API调用:
  GET /api/v1/purchase/suggestions?status=PENDING&limit=20
    ↓
后端路由:
  app/api/v1/endpoints/purchase_intelligence.py::get_purchase_suggestions()
    ↓
核心服务:
  app/services/purchase_suggestion_engine.py::PurchaseSuggestionEngine
    ↓
数据库查询:
  SELECT * FROM purchase_suggestions WHERE tenant_id=? AND status=? LIMIT 20
    ↓
返回数据:
  {
    "data": [
      {
        "id": 1,
        "suggestion_no": "PS001",
        "material_id": 101,
        "required_qty": 500,
        "urgency_level": "CRITICAL",
        "recommended_supplier_id": 5,
        "confidence": 92.0,
        "status": "PENDING"
      }
    ],
    "total": 45
  }
```

#### 链路2: 批准采购建议
```
前端组件:
  ApprovalDialog.tsx
    ↓
API调用:
  POST /api/v1/purchase/suggestions/1/approve
  Body: { "approved": true, "note": "批准" }
    ↓
后端路由:
  purchase_intelligence.py::approve_suggestion(suggestion_id=1)
    ↓
核心服务:
  PurchaseSuggestionEngine.update_status()
    ↓
数据库操作:
  UPDATE purchase_suggestions 
  SET status='APPROVED', approved_by=?, approved_at=NOW()
  WHERE id=1
    ↓
触发后续操作:
  可选: 自动创建采购订单
    ↓
返回数据:
  {
    "success": true,
    "message": "采购建议已批准",
    "suggestion_id": 1
  }
```

#### 链路3: 建议转采购订单
```
前端页面:
  SuggestionDetail.tsx
    ↓
API调用:
  POST /api/v1/purchase/suggestions/1/create-order
    ↓
后端路由:
  purchase_intelligence.py::create_order_from_suggestion()
    ↓
核心服务:
  1. 读取采购建议详情
  2. 创建采购订单 (PurchaseOrder)
  3. 创建订单明细 (PurchaseOrderItem)
  4. 更新建议状态为 "ORDERED"
    ↓
数据库操作:
  BEGIN TRANSACTION;
  INSERT INTO purchase_orders (...) VALUES (...);
  INSERT INTO purchase_order_items (...) VALUES (...);
  UPDATE purchase_suggestions SET status='ORDERED' WHERE id=1;
  COMMIT;
    ↓
返回数据:
  {
    "success": true,
    "order_id": 2001,
    "order_no": "PO20260216001",
    "message": "采购订单已创建"
  }
```

#### 链路4: 供应商绩效查询
```
前端页面:
  PerformanceManagement.tsx
    ↓
API调用:
  GET /api/v1/purchase/suppliers/5/performance?evaluation_period=2026-01
    ↓
后端路由:
  purchase_intelligence.py::get_supplier_performance()
    ↓
核心服务:
  app/services/supplier_performance_evaluator.py::SupplierPerformanceEvaluator
    ↓
数据库查询:
  SELECT * FROM supplier_performances 
  WHERE supplier_id=5 AND evaluation_period='2026-01'
    ↓
返回数据:
  {
    "supplier_id": 5,
    "supplier_name": "上海金属材料有限公司",
    "evaluation_period": "2026-01",
    "on_time_delivery_rate": 92.0,
    "quality_rate": 98.5,
    "price_competitiveness": 85.0,
    "response_time_score": 88.0,
    "overall_score": 90.8,
    "grade": "A+"
  }
```

#### 链路5: 触发供应商评估
```
前端页面:
  PerformanceManagement.tsx
    ↓
API调用:
  POST /api/v1/purchase/suppliers/5/evaluate
  Body: { "evaluation_period": "2026-01" }
    ↓
后端路由:
  purchase_intelligence.py::trigger_evaluation()
    ↓
核心服务:
  SupplierPerformanceEvaluator.evaluate_supplier()
    ↓
业务逻辑:
  1. 查询该供应商在指定期间的所有订单
  2. 计算准时交货率 = on_time_orders / total_orders
  3. 计算质量合格率 = qualified_qty / total_received_qty
  4. 计算价格竞争力 (vs 市场价)
  5. 计算响应速度 (平均响应时间)
  6. 综合评分 = Σ(指标 × 权重)
  7. 确定评级 (A+/A/B/C/D)
    ↓
数据库操作:
  INSERT INTO supplier_performances (...) VALUES (...)
  ON CONFLICT (supplier_id, evaluation_period) DO UPDATE
    ↓
返回数据:
  {
    "success": true,
    "performance_id": 123,
    "overall_score": 90.8,
    "grade": "A+",
    "message": "评估完成"
  }
```

#### 链路6: 供应商排名查询
```
前端页面:
  SupplierRanking.tsx
    ↓
API调用:
  GET /api/v1/purchase/suppliers/ranking?evaluation_period=2026-01&limit=10
    ↓
后端路由:
  purchase_intelligence.py::get_supplier_ranking()
    ↓
核心服务:
  SupplierPerformanceEvaluator.get_supplier_ranking()
    ↓
数据库查询:
  SELECT sp.*, s.name as supplier_name
  FROM supplier_performances sp
  JOIN suppliers s ON sp.supplier_id = s.id
  WHERE sp.evaluation_period = '2026-01'
  ORDER BY sp.overall_score DESC
  LIMIT 10
    ↓
返回数据:
  {
    "data": [
      { "rank": 1, "supplier_name": "上海金属", "score": 92.0, "grade": "A+" },
      { "rank": 2, "supplier_name": "广东铝材", "score": 88.5, "grade": "A" },
      { "rank": 3, "supplier_name": "江苏电机", "score": 85.2, "grade": "A" }
    ]
  }
```

#### 链路7-10: 其他采购API
- **链路7**: 创建报价 (POST /quotations)
- **链路8**: 报价比价 (GET /quotations/compare)
- **链路9**: 订单跟踪 (GET /orders/{id}/tracking)
- **链路10**: 收货确认 (POST /orders/{id}/receive)

---

### 模块2: 物料库存管理 (12条链路)

#### 链路11: 库存查询
```
前端页面:
  StockList.tsx
    ↓
API调用:
  GET /api/v1/inventory/stocks?material_id=101&location=仓库A
    ↓
后端路由:
  app/api/v1/endpoints/inventory/inventory_router.py::get_stocks()
    ↓
核心服务:
  app/services/inventory_management_service.py::InventoryManagementService
    ↓
数据库查询:
  SELECT ms.*, m.code, m.name, m.spec
  FROM material_stocks ms
  JOIN materials m ON ms.material_id = m.id
  WHERE ms.material_id = 101 AND ms.location LIKE '%仓库A%'
    ↓
返回数据:
  {
    "data": [
      {
        "id": 1,
        "material_id": 101,
        "material_code": "M001",
        "material_name": "不锈钢板 304",
        "quantity": 500,
        "available_quantity": 450,  // 可用 = 总量 - 预留
        "reserved_quantity": 50,
        "unit_price": 58.50,
        "location": "仓库A-01货架",
        "batch_number": "BATCH-20260216-001"
      }
    ]
  }
```

#### 链路12: 交易记录查询
```
前端页面:
  TransactionHistory.tsx
    ↓
API调用:
  GET /api/v1/inventory/stocks/1/transactions?limit=50
    ↓
后端路由:
  inventory_router.py::get_transactions()
    ↓
核心服务:
  InventoryManagementService.get_transactions()
    ↓
数据库查询:
  SELECT mt.*, u.name as operator_name
  FROM material_transactions mt
  LEFT JOIN users u ON mt.created_by = u.id
  WHERE mt.material_id = 101
  ORDER BY mt.created_at DESC
  LIMIT 50
    ↓
返回数据:
  {
    "data": [
      {
        "id": 501,
        "transaction_no": "T20260216001",
        "transaction_type": "ISSUE",  // 领料
        "quantity": 50,
        "unit_price": 58.50,
        "total_cost": 2925.00,
        "work_order_id": 3001,
        "created_by": 10,
        "operator_name": "张三",
        "created_at": "2026-02-16T08:30:00"
      }
    ]
  }
```

#### 链路13: 物料预留
```
前端页面:
  MaterialReservation.tsx
    ↓
API调用:
  POST /api/v1/inventory/reserve
  Body: {
    "material_id": 101,
    "quantity": 200,
    "project_id": 5,
    "expected_use_date": "2026-03-01"
  }
    ↓
后端路由:
  inventory_router.py::reserve_material()
    ↓
核心服务:
  InventoryManagementService.reserve_material()
    ↓
业务逻辑:
  1. 检查库存是否充足 (available_quantity >= 200)
  2. 创建预留记录 (MaterialReservation)
  3. 扣减可用库存 (available_quantity -= 200)
  4. 增加预留库存 (reserved_quantity += 200)
    ↓
数据库操作:
  BEGIN TRANSACTION;
  INSERT INTO material_reservations (...) VALUES (...);
  UPDATE material_stocks 
  SET available_quantity = available_quantity - 200,
      reserved_quantity = reserved_quantity + 200
  WHERE material_id = 101;
  COMMIT;
    ↓
返回数据:
  {
    "success": true,
    "reservation_id": 301,
    "reservation_no": "RES20260216001",
    "message": "物料预留成功"
  }
```

#### 链路14: 领料出库
```
前端页面:
  MaterialIssue.tsx
    ↓
API调用:
  POST /api/v1/inventory/issue
  Body: {
    "material_id": 101,
    "quantity": 150,
    "work_order_id": 3001,
    "cost_method": "FIFO"  // 先进先出
  }
    ↓
后端路由:
  inventory_router.py::issue_material()
    ↓
核心服务:
  InventoryManagementService.issue_material()
    ↓
业务逻辑:
  1. 检查库存是否充足
  2. 根据成本核算方法 (FIFO/LIFO/加权平均) 选择批次
  3. 创建交易记录 (MaterialTransaction, type=ISSUE)
  4. 扣减库存数量
  5. 如有预留，释放预留
    ↓
数据库操作 (FIFO示例):
  BEGIN TRANSACTION;
  -- 查询最早批次
  SELECT * FROM material_stocks 
  WHERE material_id=101 AND quantity > 0
  ORDER BY last_in_date ASC
  LIMIT 1;
  -- 创建交易记录
  INSERT INTO material_transactions (type='ISSUE', ...) VALUES (...);
  -- 扣减库存
  UPDATE material_stocks SET quantity = quantity - 150 WHERE id=1;
  -- 释放预留 (如有)
  UPDATE material_reservations SET status='USED' WHERE ...;
  COMMIT;
    ↓
返回数据:
  {
    "success": true,
    "transaction_id": 502,
    "batches": [
      { "batch_no": "BATCH001", "quantity": 150, "unit_price": 58.50 }
    ],
    "total_cost": 8775.00,
    "message": "领料成功"
  }
```

#### 链路15: 退料入库
```
前端页面:
  MaterialReturn.tsx
    ↓
API调用:
  POST /api/v1/inventory/return
  Body: {
    "material_id": 101,
    "quantity": 20,
    "reason": "项目取消",
    "original_work_order_id": 3001
  }
    ↓
后端路由:
  inventory_router.py::return_material()
    ↓
核心服务:
  InventoryManagementService.return_material()
    ↓
业务逻辑:
  1. 创建交易记录 (type=RETURN)
  2. 增加库存数量
  3. 更新可用库存
    ↓
数据库操作:
  BEGIN TRANSACTION;
  INSERT INTO material_transactions (type='RETURN', ...) VALUES (...);
  UPDATE material_stocks 
  SET quantity = quantity + 20,
      available_quantity = available_quantity + 20
  WHERE material_id = 101;
  COMMIT;
    ↓
返回数据:
  {
    "success": true,
    "transaction_id": 503,
    "message": "退料成功"
  }
```

#### 链路16: 库存转移
```
前端页面:
  StockTransfer.tsx
    ↓
API调用:
  POST /api/v1/inventory/transfer
  Body: {
    "material_id": 101,
    "quantity": 100,
    "from_location": "仓库A-01",
    "to_location": "仓库B-05"
  }
    ↓
后端路由:
  inventory_router.py::transfer_stock()
    ↓
核心服务:
  InventoryManagementService.transfer_stock()
    ↓
业务逻辑:
  1. 从源位置扣减库存
  2. 向目标位置增加库存
  3. 创建2条交易记录 (OUT + IN)
    ↓
数据库操作:
  BEGIN TRANSACTION;
  -- 源位置扣减
  UPDATE material_stocks 
  SET quantity = quantity - 100
  WHERE material_id=101 AND location='仓库A-01';
  -- 目标位置增加
  UPDATE material_stocks 
  SET quantity = quantity + 100
  WHERE material_id=101 AND location='仓库B-05';
  -- 创建交易记录
  INSERT INTO material_transactions (type='TRANSFER_OUT', ...) VALUES (...);
  INSERT INTO material_transactions (type='TRANSFER_IN', ...) VALUES (...);
  COMMIT;
    ↓
返回数据:
  {
    "success": true,
    "from_transaction_id": 504,
    "to_transaction_id": 505,
    "message": "库存转移成功"
  }
```

#### 链路17: 盘点任务列表
```
前端页面:
  CountTasks.tsx
    ↓
API调用:
  GET /api/v1/inventory/count/tasks?status=IN_PROGRESS
    ↓
后端路由:
  inventory_router.py::get_count_tasks()
    ↓
核心服务:
  app/services/stock_count_service.py::StockCountService
    ↓
数据库查询:
  SELECT sct.*, u.name as creator_name
  FROM stock_count_tasks sct
  LEFT JOIN users u ON sct.created_by = u.id
  WHERE sct.status = 'IN_PROGRESS'
  ORDER BY sct.count_date DESC
    ↓
返回数据:
  {
    "data": [
      {
        "id": 10,
        "task_no": "CT20260216001",
        "count_type": "FULL",  // 全盘
        "count_date": "2026-02-20",
        "status": "IN_PROGRESS",
        "total_items": 16,
        "counted_items": 2,
        "created_by": 1,
        "creator_name": "管理员"
      }
    ]
  }
```

#### 链路18: 创建盘点任务
```
前端组件:
  CreateTaskDialog.tsx
    ↓
API调用:
  POST /api/v1/inventory/count/tasks
  Body: {
    "count_type": "FULL",
    "count_date": "2026-02-20",
    "location": "仓库A"
  }
    ↓
后端路由:
  inventory_router.py::create_count_task()
    ↓
核心服务:
  StockCountService.create_count_task()
    ↓
业务逻辑:
  1. 创建盘点任务记录
  2. 查询该仓库的所有物料
  3. 为每个物料创建盘点明细 (账面数量快照)
    ↓
数据库操作:
  BEGIN TRANSACTION;
  -- 创建任务
  INSERT INTO stock_count_tasks (...) VALUES (...);
  -- 查询物料
  SELECT * FROM material_stocks WHERE location LIKE '%仓库A%';
  -- 批量创建明细
  INSERT INTO stock_count_details (task_id, material_id, system_quantity, ...)
  VALUES 
    (10, 101, 500),
    (10, 102, 300),
    ...;
  COMMIT;
    ↓
返回数据:
  {
    "success": true,
    "task_id": 10,
    "task_no": "CT20260216001",
    "total_items": 16,
    "message": "盘点任务已创建"
  }
```

#### 链路19: 录入实盘数量
```
前端组件:
  CountInputForm.tsx
    ↓
API调用:
  PUT /api/v1/inventory/count/details/101
  Body: {
    "actual_quantity": 495,
    "counted_by": 10
  }
    ↓
后端路由:
  inventory_router.py::record_actual_quantity()
    ↓
核心服务:
  StockCountService.record_actual_quantity()
    ↓
业务逻辑:
  1. 更新实盘数量
  2. 计算差异 = actual - system
  3. 计算差异金额 = 差异 × 单价
  4. 更新盘点明细状态
    ↓
数据库操作:
  UPDATE stock_count_details
  SET actual_quantity = 495,
      difference_quantity = 495 - 500,  -- -5
      difference_value = -5 * 58.50,    -- -292.50
      counted_by = 10,
      counted_at = NOW()
  WHERE id = 101;
    ↓
返回数据:
  {
    "success": true,
    "detail_id": 101,
    "difference_quantity": -5,
    "difference_value": -292.50,
    "message": "实盘数量已录入"
  }
```

#### 链路20: 批准库存调整
```
前端组件:
  AdjustmentApproval.tsx
    ↓
API调用:
  POST /api/v1/inventory/count/tasks/10/approve
  Body: {
    "auto_adjust": true,
    "approved_by": 2
  }
    ↓
后端路由:
  inventory_router.py::approve_adjustment()
    ↓
核心服务:
  StockCountService.approve_adjustment()
    ↓
业务逻辑:
  1. 遍历所有盘点明细
  2. 对有差异的物料:
     a. 创建库存调整记录 (StockAdjustment)
     b. 创建交易记录 (MaterialTransaction, type=ADJUSTMENT)
     c. 更新库存数量 (quantity += difference)
  3. 更新盘点任务状态为 "COMPLETED"
    ↓
数据库操作:
  BEGIN TRANSACTION;
  -- 创建调整记录
  INSERT INTO stock_adjustments (detail_id, adjustment_qty, ...) VALUES (...);
  -- 创建交易记录
  INSERT INTO material_transactions (type='ADJUSTMENT', ...) VALUES (...);
  -- 更新库存
  UPDATE material_stocks 
  SET quantity = quantity + (-5)  -- 实盘少了5
  WHERE material_id = 101;
  -- 更新任务状态
  UPDATE stock_count_tasks SET status='COMPLETED' WHERE id=10;
  COMMIT;
    ↓
返回数据:
  {
    "success": true,
    "total_adjustments": 3,
    "total_diff_value": -450.00,
    "message": "库存调整已完成"
  }
```

#### 链路21: 库存周转率分析
```
前端页面:
  TurnoverAnalysis.tsx
    ↓
API调用:
  GET /api/v1/inventory/analysis/turnover?start_date=2025-12-01&end_date=2026-02-29
    ↓
后端路由:
  inventory_router.py::get_turnover_analysis()
    ↓
核心服务:
  InventoryManagementService.calculate_turnover()
    ↓
业务逻辑:
  1. 计算期间内的出库总额
  2. 计算平均库存金额
  3. 周转率 = 出库总额 / 平均库存
  4. 周转天数 = 365 / 周转率
    ↓
数据库查询:
  -- 出库总额
  SELECT SUM(total_cost) as total_issue
  FROM material_transactions
  WHERE type='ISSUE' AND created_at BETWEEN '2025-12-01' AND '2026-02-29';
  
  -- 平均库存
  SELECT AVG(quantity * unit_price) as avg_inventory
  FROM material_stocks;
    ↓
返回数据:
  {
    "turnover_rate": 6.5,  // 周转率
    "turnover_days": 56,   // 周转天数
    "total_issue": 2500000,
    "avg_inventory": 384615,
    "trend_data": [
      { "month": "2025-12", "rate": 6.2 },
      { "month": "2026-01", "rate": 6.8 },
      { "month": "2026-02", "rate": 6.5 }
    ]
  }
```

#### 链路22: 库龄分析
```
前端页面:
  AgingAnalysis.tsx
    ↓
API调用:
  GET /api/v1/inventory/analysis/aging
    ↓
后端路由:
  inventory_router.py::get_aging_analysis()
    ↓
核心服务:
  InventoryManagementService.analyze_aging()
    ↓
业务逻辑:
  1. 查询所有库存批次
  2. 计算库龄 = 当前日期 - last_in_date
  3. 分类统计:
     - 0-30天
     - 31-90天
     - 91-180天
     - 180+天 (呆滞)
    ↓
数据库查询:
  SELECT 
    CASE
      WHEN DATEDIFF(NOW(), last_in_date) <= 30 THEN '0-30天'
      WHEN DATEDIFF(NOW(), last_in_date) <= 90 THEN '31-90天'
      WHEN DATEDIFF(NOW(), last_in_date) <= 180 THEN '91-180天'
      ELSE '180+天'
    END as age_range,
    COUNT(*) as count,
    SUM(quantity * unit_price) as total_value
  FROM material_stocks
  GROUP BY age_range;
    ↓
返回数据:
  {
    "distribution": [
      { "range": "0-30天", "count": 8, "value": 150000, "percentage": 45% },
      { "range": "31-90天", "count": 5, "value": 100000, "percentage": 30% },
      { "range": "91-180天", "count": 2, "value": 50000, "percentage": 15% },
      { "range": "180+天", "count": 1, "value": 30000, "percentage": 10% }
    ],
    "slow_moving_items": [
      { "material": "旧型号电机", "age": 200, "value": 30000 }
    ]
  }
```

---

### 模块3: 智能缺料预警 (10条链路)

#### 链路23: 预警列表查询
```
前端页面:
  AlertDashboard.jsx
    ↓
API调用:
  GET /api/v1/shortage/smart/alerts?alert_level=URGENT&status=PENDING
    ↓
后端路由:
  app/api/v1/endpoints/shortage/smart_alerts.py::get_shortage_alerts()
    ↓
核心服务:
  app/services/shortage/smart_alert_engine.py::SmartAlertEngine
    ↓
数据库查询:
  SELECT sa.*, m.code, m.name
  FROM shortage_alerts_enhanced sa
  JOIN materials m ON sa.material_id = m.id
  WHERE sa.alert_level = 'URGENT' AND sa.status = 'PENDING'
  ORDER BY sa.alert_date DESC
    ↓
返回数据:
  {
    "data": [
      {
        "id": 1,
        "alert_no": "SA001",
        "alert_level": "URGENT",
        "material_id": 101,
        "material_code": "M001",
        "material_name": "不锈钢板 304",
        "required_qty": 500,
        "available_qty": 50,
        "shortage_qty": 450,
        "required_date": "2026-02-18",
        "estimated_delay_days": 3,
        "estimated_cost_impact": 26325.00,
        "risk_score": 89,
        "status": "PENDING"
      }
    ]
  }
```

#### 链路24: 预警详情查询
```
前端页面:
  AlertDetail.jsx
    ↓
API调用:
  GET /api/v1/shortage/smart/alerts/1
    ↓
后端路由:
  smart_alerts.py::get_alert_detail()
    ↓
核心服务:
  SmartAlertEngine.get_alert_with_impact()
    ↓
数据库查询:
  SELECT sa.*, 
         m.code, m.name, m.unit_price,
         p.name as project_name
  FROM shortage_alerts_enhanced sa
  JOIN materials m ON sa.material_id = m.id
  LEFT JOIN projects p ON sa.project_id = p.id
  WHERE sa.id = 1;
    ↓
返回数据:
  {
    "alert": { ... },
    "impact_analysis": {
      "estimated_delay_days": 3,
      "estimated_cost_impact": 26325.00,
      "affected_projects": [
        { "id": 5, "name": "项目A", "delay_impact": 2 },
        { "id": 6, "name": "项目B", "delay_impact": 1 }
      ],
      "risk_score": 89,
      "risk_level": "HIGH"
    }
  }
```

#### 链路25: 触发缺料扫描
```
前端组件:
  QuickScanButton.jsx
    ↓
API调用:
  POST /api/v1/shortage/smart/scan
  Body: {
    "days_ahead": 30,
    "project_id": null  // 全局扫描
  }
    ↓
后端路由:
  smart_alerts.py::trigger_scan()
    ↓
核心服务:
  SmartAlertEngine.scan_and_alert()
    ↓
业务逻辑:
  1. 收集未来30天的物料需求 (从WorkOrder, BOM)
  2. 查询当前库存和在途数量
  3. 计算缺料:
     shortage = required - (stock + in_transit)
  4. 对每个缺料物料:
     a. 计算预警级别 (URGENT/CRITICAL/WARNING/INFO)
     b. 预测影响 (延期天数、成本)
     c. 计算风险评分
     d. 创建预警记录
  5. 对 CRITICAL/URGENT 预警自动生成处理方案
    ↓
数据库操作:
  BEGIN TRANSACTION;
  -- 查询需求
  SELECT material_id, SUM(required_qty) as total_required
  FROM work_orders
  WHERE required_date BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 30 DAY)
  GROUP BY material_id;
  
  -- 查询库存
  SELECT material_id, SUM(available_quantity) as total_stock
  FROM material_stocks
  GROUP BY material_id;
  
  -- 批量创建预警
  INSERT INTO shortage_alerts_enhanced (...) VALUES (...), (...), ...;
  COMMIT;
    ↓
返回数据:
  {
    "success": true,
    "scanned_materials": 150,
    "new_alerts": 12,
    "alert_breakdown": {
      "URGENT": 3,
      "CRITICAL": 5,
      "WARNING": 4
    },
    "message": "扫描完成，发现12个缺料预警"
  }
```

#### 链路26: 获取AI处理方案
```
前端页面:
  SolutionRecommendation.jsx
    ↓
API调用:
  GET /api/v1/shortage/smart/alerts/1/solutions
    ↓
后端路由:
  smart_alerts.py::get_handling_solutions()
    ↓
核心服务:
  SmartAlertEngine.generate_solutions()
    ↓
业务逻辑:
  对预警生成5类处理方案:
  
  1. URGENT_PURCHASE (紧急采购)
     - 可行性: 检查供应商是否能加急
     - 成本: 正常价 × 1.2 (加急费)
     - 时间: 平均交期 / 2
     - 风险: 供应商可靠性
  
  2. SUBSTITUTE (替代料)
     - 可行性: 查询替代料库存
     - 成本: 替代料价格差异
     - 时间: 0 (立即可用)
     - 风险: 技术风险、客户接受度
  
  3. TRANSFER (项目间调拨)
     - 可行性: 查询其他项目预留
     - 成本: 0 (内部调拨)
     - 时间: 1天
     - 风险: 其他项目延期风险
  
  4. PARTIAL_DELIVERY (分批交付)
     - 可行性: 客户是否接受
     - 成本: 0
     - 时间: 部分延期
     - 风险: 客户满意度
  
  5. RESCHEDULE (生产重排期)
     - 可行性: 生产计划灵活性
     - 成本: 重排成本
     - 时间: 等待交期
     - 风险: 整体进度影响
  
  每个方案计算AI综合评分:
  AI_Score = feasibility×0.3 + cost×0.3 + time×0.3 + risk×0.1
    ↓
数据库操作:
  -- 如果方案已存在，直接查询
  SELECT * FROM shortage_handling_plans WHERE alert_id = 1;
  
  -- 否则，生成并保存
  INSERT INTO shortage_handling_plans (...) VALUES (...), (...), ...;
    ↓
返回数据:
  {
    "alert_id": 1,
    "solutions": [
      {
        "id": 1,
        "plan_no": "HP001",
        "solution_type": "URGENT_PURCHASE",
        "solution_name": "紧急采购",
        "ai_score": 85.5,
        "feasibility_score": 90,
        "cost_score": 75,
        "time_score": 95,
        "risk_score": 85,
        "advantages": ["快速解决", "质量保证"],
        "disadvantages": ["成本增加20%"],
        "risks": ["供应商产能不足"],
        "is_recommended": true,
        "recommendation_rank": 1
      },
      {
        "id": 2,
        "solution_type": "SUBSTITUTE",
        "ai_score": 72.0,
        "is_recommended": false,
        "recommendation_rank": 2
      }
      // ... 其他3个方案
    ]
  }
```

#### 链路27: 标记预警已解决
```
前端页面:
  AlertDetail.jsx
    ↓
API调用:
  POST /api/v1/shortage/smart/alerts/1/resolve
  Body: {
    "solution_id": 1,
    "note": "已紧急采购"
  }
    ↓
后端路由:
  smart_alerts.py::resolve_alert()
    ↓
核心服务:
  SmartAlertEngine.mark_resolved()
    ↓
数据库操作:
  UPDATE shortage_alerts_enhanced
  SET status = 'RESOLVED',
      resolved_solution_id = 1,
      resolved_at = NOW(),
      resolve_note = '已紧急采购'
  WHERE id = 1;
    ↓
返回数据:
  {
    "success": true,
    "alert_id": 1,
    "message": "预警已标记为解决"
  }
```

#### 链路28: 物料需求预测
```
前端页面:
  DemandForecast.jsx
    ↓
API调用:
  GET /api/v1/shortage/smart/forecast/101?algorithm=EXP_SMOOTHING&forecast_horizon_days=30
    ↓
后端路由:
  smart_alerts.py::get_material_forecast()
    ↓
核心服务:
  app/services/shortage/demand_forecast_engine.py::DemandForecastEngine
    ↓
业务逻辑:
  1. 查询历史需求数据 (过去90天)
  2. 选择预测算法:
     - MOVING_AVERAGE (移动平均)
     - EXP_SMOOTHING (指数平滑) ⭐ 推荐
     - LINEAR_REGRESSION (线性回归)
  3. 执行预测
  4. 计算95%置信区间
  5. 检测季节性因素
  6. 验证准确率 (MAE/MAPE)
    ↓
数据库查询:
  SELECT 
    DATE(created_at) as date,
    SUM(quantity) as demand
  FROM material_transactions
  WHERE material_id = 101 
    AND type = 'ISSUE'
    AND created_at >= DATE_SUB(NOW(), INTERVAL 90 DAY)
  GROUP BY DATE(created_at)
  ORDER BY date ASC;
    ↓
预测算法 (指数平滑):
  S_t = α × Y_t + (1 - α) × S_{t-1}
  其中: α = 0.3 (平滑系数)
    ↓
数据库操作:
  INSERT INTO material_demand_forecasts (...) VALUES (...);
    ↓
返回数据:
  {
    "material_id": 101,
    "algorithm": "EXP_SMOOTHING",
    "forecasted_demand": 450,
    "lower_bound": 400,  // 95% 置信区间下限
    "upper_bound": 500,  // 95% 置信区间上限
    "confidence_interval": 95,
    "historical_avg": 420,
    "seasonal_factor": 1.05,
    "accuracy_score": 87.5,  // 准确率
    "mae": 25.3,             // 平均绝对误差
    "mape": 6.2,             // 平均绝对百分比误差
    "forecast_data": [
      { "date": "2026-02-17", "predicted": 450, "lower": 400, "upper": 500 },
      { "date": "2026-02-18", "predicted": 455, "lower": 405, "upper": 505 },
      // ... 未来30天
    ]
  }
```

#### 链路29: 缺料趋势分析
```
前端页面:
  TrendAnalysis.jsx
    ↓
API调用:
  GET /api/v1/shortage/smart/analysis/trend?start_date=2026-01-01&end_date=2026-02-16
    ↓
后端路由:
  smart_alerts.py::get_shortage_trend()
    ↓
核心服务:
  SmartAlertEngine.analyze_trend()
    ↓
数据库查询:
  -- 总体统计
  SELECT 
    COUNT(*) as total_alerts,
    AVG(TIMESTAMPDIFF(HOUR, detected_at, resolved_at)) as avg_response_hours,
    SUM(CASE WHEN status='RESOLVED' THEN 1 ELSE 0 END) / COUNT(*) as resolution_rate
  FROM shortage_alerts_enhanced
  WHERE detected_at BETWEEN '2026-01-01' AND '2026-02-16';
  
  -- 按级别分布
  SELECT alert_level, COUNT(*) as count
  FROM shortage_alerts_enhanced
  WHERE detected_at BETWEEN '2026-01-01' AND '2026-02-16'
  GROUP BY alert_level;
  
  -- 按状态分布
  SELECT status, COUNT(*) as count
  FROM shortage_alerts_enhanced
  WHERE detected_at BETWEEN '2026-01-01' AND '2026-02-16'
  GROUP BY status;
  
  -- 每日趋势
  SELECT 
    DATE(detected_at) as date,
    COUNT(*) as new_alerts,
    SUM(CASE WHEN status='RESOLVED' THEN 1 ELSE 0 END) as resolved_alerts
  FROM shortage_alerts_enhanced
  WHERE detected_at BETWEEN '2026-01-01' AND '2026-02-16'
  GROUP BY DATE(detected_at);
    ↓
返回数据:
  {
    "summary": {
      "total_alerts": 188,
      "avg_response_hours": 12.5,
      "resolution_rate": 0.76  // 76%
    },
    "by_level": [
      { "level": "URGENT", "count": 25, "percentage": 13 },
      { "level": "CRITICAL", "count": 48, "percentage": 26 },
      { "level": "WARNING", "count": 72, "percentage": 38 },
      { "level": "INFO", "count": 43, "percentage": 23 }
    ],
    "by_status": [
      { "status": "RESOLVED", "count": 143, "percentage": 76 },
      { "status": "PENDING", "count": 28, "percentage": 15 },
      { "status": "IN_PROGRESS", "count": 17, "percentage": 9 }
    ],
    "daily_trend": [
      { "date": "2026-02-10", "new": 8, "resolved": 6 },
      { "date": "2026-02-11", "new": 12, "resolved": 10 },
      // ... 每日数据
    ]
  }
```

#### 链路30: 根因分析
```
前端页面:
  RootCauseAnalysis.jsx
    ↓
API调用:
  GET /api/v1/shortage/smart/analysis/root-cause
    ↓
后端路由:
  smart_alerts.py::get_root_cause()
    ↓
核心服务:
  SmartAlertEngine.analyze_root_cause()
    ↓
业务逻辑:
  自动识别缺料原因:
  1. 需求预测不准 - 实际需求 > 预测需求 × 1.2
  2. 供应商延期 - 实际到货日期 > 承诺日期
  3. 质量问题退货 - 存在退货记录
  4. 紧急插单 - 订单创建日期距离需求日期 < 7天
  5. 其他
    ↓
数据库查询:
  -- 分析每个预警的原因
  SELECT 
    CASE
      WHEN sa.required_qty > f.forecasted_demand * 1.2 THEN '需求预测不准'
      WHEN po.actual_delivery_date > po.promised_date THEN '供应商延期'
      WHEN EXISTS (SELECT 1 FROM material_transactions mt WHERE mt.type='RETURN' AND mt.material_id=sa.material_id) THEN '质量问题退货'
      WHEN DATEDIFF(sa.required_date, wo.created_at) < 7 THEN '紧急插单'
      ELSE '其他'
    END as root_cause,
    COUNT(*) as frequency,
    SUM(sa.estimated_cost_impact) as total_impact
  FROM shortage_alerts_enhanced sa
  LEFT JOIN material_demand_forecasts f ON sa.material_id = f.material_id
  LEFT JOIN work_orders wo ON sa.work_order_id = wo.id
  LEFT JOIN purchase_orders po ON sa.material_id = po.material_id
  GROUP BY root_cause;
    ↓
返回数据:
  {
    "root_causes": [
      {
        "cause": "需求预测不准",
        "frequency": 45,
        "percentage": 24,
        "total_cost_impact": 125000,
        "avg_cost_impact": 2778,
        "improvement_suggestions": [
          "优化预测算法",
          "增加历史数据样本",
          "考虑季节性因素"
        ]
      },
      {
        "cause": "供应商延期",
        "frequency": 38,
        "percentage": 20,
        "total_cost_impact": 98000,
        "improvement_suggestions": [
          "加强供应商管理",
          "建立备选供应商",
          "提前下单"
        ]
      },
      {
        "cause": "紧急插单",
        "frequency": 32,
        "percentage": 17,
        "total_cost_impact": 85000,
        "improvement_suggestions": [
          "限制紧急订单比例",
          "增加安全库存",
          "建立快速响应机制"
        ]
      }
      // ... 其他原因
    ]
  }
```

#### 链路31-32: 其他预警API
- **链路31**: 项目影响分析 (GET /impact/projects)
- **链路32**: 订阅通知 (POST /notifications/subscribe)

---

## 🎯 API调用时序图

### 典型场景1: 缺料预警 → AI方案 → 紧急采购 → 订单跟踪

```
用户                前端                 后端API            核心服务           数据库
 │                   │                    │                   │                  │
 │ 1. 触发扫描       │                    │                   │                  │
 ├──────────────────>│                    │                   │                  │
 │                   │ POST /scan         │                   │                  │
 │                   ├───────────────────>│                   │                  │
 │                   │                    │ scan_and_alert()  │                  │
 │                   │                    ├──────────────────>│                  │
 │                   │                    │                   │ INSERT alerts    │
 │                   │                    │                   ├─────────────────>│
 │                   │ {12 new alerts}    │                   │                  │
 │                   │<───────────────────┤                   │                  │
 │                   │                    │                   │                  │
 │ 2. 查看预警详情   │                    │                   │                  │
 ├──────────────────>│                    │                   │                  │
 │                   │ GET /alerts/1      │                   │                  │
 │                   ├───────────────────>│                   │                  │
 │                   │                    │                   │ SELECT alert     │
 │                   │                    │                   ├─────────────────>│
 │                   │ {alert + impact}   │                   │                  │
 │                   │<───────────────────┤                   │                  │
 │                   │                    │                   │                  │
 │ 3. 查看AI方案     │                    │                   │                  │
 ├──────────────────>│                    │                   │                  │
 │                   │ GET /alerts/1/solutions                │                  │
 │                   ├───────────────────>│                   │                  │
 │                   │                    │ generate_solutions│                  │
 │                   │                    ├──────────────────>│                  │
 │                   │                    │                   │ INSERT plans     │
 │                   │                    │                   ├─────────────────>│
 │                   │ {5 solutions}      │                   │                  │
 │                   │<───────────────────┤                   │                  │
 │                   │                    │                   │                  │
 │ 4. 选择紧急采购   │                    │                   │                  │
 │    创建采购订单   │                    │                   │                  │
 ├──────────────────>│                    │                   │                  │
 │                   │ POST /purchase/suggestions/1/create-order                 │
 │                   ├───────────────────>│                   │                  │
 │                   │                    │                   │ BEGIN TXN        │
 │                   │                    │                   ├─────────────────>│
 │                   │                    │                   │ INSERT order     │
 │                   │                    │                   ├─────────────────>│
 │                   │                    │                   │ UPDATE alert     │
 │                   │                    │                   ├─────────────────>│
 │                   │                    │                   │ COMMIT           │
 │                   │                    │                   ├─────────────────>│
 │                   │ {order_id: 2001}   │                   │                  │
 │                   │<───────────────────┤                   │                  │
 │                   │                    │                   │                  │
 │ 5. 跟踪订单       │                    │                   │                  │
 ├──────────────────>│                    │                   │                  │
 │                   │ GET /purchase/orders/2001/tracking     │                  │
 │                   ├───────────────────>│                   │                  │
 │                   │                    │                   │ SELECT tracking  │
 │                   │                    │                   ├─────────────────>│
 │                   │ {timeline events}  │                   │                  │
 │                   │<───────────────────┤                   │                  │
```

---

## 🔧 关键技术点

### 1. 认证与授权
```
前端: localStorage.getItem('access_token')
   ↓
请求头: Authorization: Bearer {token}
   ↓
后端中间件: verify_token()
   ↓
提取: current_user, tenant_id
   ↓
后续查询: WHERE tenant_id = current_user.tenant_id
```

### 2. 数据库事务
```python
# 关键操作使用事务保证一致性
with db.begin():
    # 1. 创建交易记录
    transaction = MaterialTransaction(...)
    db.add(transaction)
    
    # 2. 更新库存
    stock.quantity -= issued_qty
    
    # 3. 释放预留
    reservation.status = 'USED'
    
    db.commit()  # 全部成功或全部回滚
```

### 3. AI算法集成
```python
# 供应商推荐
supplier_score = (
    performance_score * 0.4 +
    price_score * 0.3 +
    delivery_score * 0.2 +
    history_score * 0.1
)

# 需求预测
forecasted = alpha * actual + (1 - alpha) * previous_forecast

# 方案评分
ai_score = (
    feasibility * 0.3 +
    cost * 0.3 +
    time * 0.3 +
    risk * 0.1
)
```

### 4. 性能优化
```python
# 1. 索引优化
CREATE INDEX idx_material_id ON material_stocks(material_id);
CREATE INDEX idx_status_date ON shortage_alerts(status, alert_date);

# 2. 批量操作
db.bulk_insert_mappings(StockCountDetail, details_data)

# 3. 分页查询
.limit(page_size).offset((page - 1) * page_size)

# 4. 关联查询优化
.join(Material).options(joinedload(MaterialStock.material))
```

---

## 📊 API调用统计

| 模块 | API数量 | 数据库表 | 核心服务 | 前端页面 |
|------|---------|----------|----------|----------|
| 智能采购管理 | 10 | 4 | 2 | 6 |
| 物料库存管理 | 12 | 6 | 2 | 10 |
| 智能缺料预警 | 10 | 3 | 2 | 7 |
| **总计** | **32** | **13** | **6** | **23** |

---

## 🚀 快速测试指南

### 测试场景1: 智能采购建议生成
```bash
# 1. 触发缺料扫描
curl -X POST http://localhost:8000/api/v1/shortage/smart/scan \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days_ahead": 30}'

# 2. 查看采购建议
curl -X GET http://localhost:8000/api/v1/purchase/suggestions \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 批准建议
curl -X POST http://localhost:8000/api/v1/purchase/suggestions/1/approve \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

### 测试场景2: 库存盘点流程
```bash
# 1. 创建盘点任务
curl -X POST http://localhost:8000/api/v1/inventory/count/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "count_type": "FULL",
    "count_date": "2026-02-20",
    "location": "仓库A"
  }'

# 2. 录入实盘数量
curl -X PUT http://localhost:8000/api/v1/inventory/count/details/101 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "actual_quantity": 495,
    "counted_by": 10
  }'

# 3. 批准调整
curl -X POST http://localhost:8000/api/v1/inventory/count/tasks/10/approve \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_adjust": true,
    "approved_by": 2
  }'
```

---

**文档生成时间**: 2026-02-16 10:26  
**版本**: v1.0  
**维护者**: M5
