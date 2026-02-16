# 采购-物料-库存闭环 - Agent Teams 启动计划

**启动时间**: 2026-02-16 08:16  
**目标**: 完善采购到入库的完整流程，实现智能化管理  
**预计耗时**: 1-2小时  
**并行Teams**: 4个

---

## 🎯 总体目标

构建完整的 **采购→入库→领用→消耗** 闭环管理系统，实现：
- 智能采购建议（基于缺料预警）
- 物料全流程跟踪
- 缺料自动预警和处理
- 供应商绩效评估

---

## 📊 现状分析

### 已有基础
- ✅ `app/models/purchase.py` - 采购模型存在
- ✅ `app/models/material.py` - 物料模型存在
- ✅ `app/api/v1/endpoints/purchase/` - 采购API目录存在
- ✅ `app/api/v1/endpoints/materials/` - 物料API目录存在
- ✅ `app/api/v1/endpoints/shortage/` - 缺料管理目录存在

### 缺失部分
- ❌ 智能采购建议系统
- ❌ 物料全流程跟踪
- ❌ 供应商绩效评估
- ❌ 缺料自动预警优化
- ❌ 库存优化算法

---

## Team 1: 智能采购管理系统

### 任务目标
实现智能化采购管理，包括采购建议、供应商管理、采购执行、绩效评估。

### 交付清单

1. **数据模型增强** (3-4个新表)
   ```python
   # app/models/purchase_enhanced.py
   
   class PurchaseSuggestion(Base):
       """采购建议表"""
       id = Column(Integer, primary_key=True)
       material_id = Column(Integer, ForeignKey('materials.id'))
       suggested_quantity = Column(Decimal)
       reason = Column(String)  # SHORTAGE/REORDER/SEASONAL/FORECAST
       urgency = Column(String)  # LOW/MEDIUM/HIGH/CRITICAL
       estimated_lead_time = Column(Integer)  # 预计交期(天)
       suggested_supplier_id = Column(Integer)
       ai_confidence = Column(Float)  # AI推荐置信度
       created_at = Column(DateTime)
       status = Column(String)  # PENDING/APPROVED/REJECTED/ORDERED
   
   class SupplierPerformance(Base):
       """供应商绩效表"""
       id = Column(Integer, primary_key=True)
       supplier_id = Column(Integer, ForeignKey('suppliers.id'))
       evaluation_period = Column(String)  # 2026-Q1
       on_time_delivery_rate = Column(Float)  # 准时交货率
       quality_pass_rate = Column(Float)  # 质量合格率
       price_competitiveness = Column(Float)  # 价格竞争力
       response_speed = Column(Float)  # 响应速度
       overall_score = Column(Float)  # 综合评分
       rank = Column(Integer)  # 排名
   
   class PurchaseOrder(Base):
       """采购订单表（增强）"""
       # 现有字段...
       
       # 新增字段
       expected_delivery_date = Column(Date)
       actual_delivery_date = Column(Date)
       quality_inspection_result = Column(String)
       is_delayed = Column(Boolean, default=False)
       delay_days = Column(Integer)
       delay_reason = Column(Text)
   
   class SupplierQuotation(Base):
       """供应商报价表"""
       id = Column(Integer, primary_key=True)
       purchase_request_id = Column(Integer)
       supplier_id = Column(Integer)
       material_id = Column(Integer)
       unit_price = Column(Decimal)
       delivery_days = Column(Integer)
       minimum_order_quantity = Column(Decimal)
       validity_days = Column(Integer)  # 报价有效期
       created_at = Column(DateTime)
   ```

2. **智能采购建议引擎** (app/services/purchase_suggestion_service.py)
   ```python
   class PurchaseSuggestionService:
       """采购建议引擎"""
       
       def generate_suggestions(self, db: Session) -> List[PurchaseSuggestion]:
           """生成采购建议"""
           suggestions = []
           
           # 1. 基于缺料预警
           shortages = self.get_shortage_alerts(db)
           for shortage in shortages:
               suggestions.append(self.create_suggestion(
                   material=shortage.material,
                   reason="SHORTAGE",
                   urgency="CRITICAL",
                   quantity=shortage.shortage_quantity
               ))
           
           # 2. 基于安全库存
           low_stocks = self.get_low_stock_materials(db)
           for stock in low_stocks:
               suggestions.append(self.create_suggestion(
                   material=stock.material,
                   reason="REORDER",
                   urgency="MEDIUM",
                   quantity=self.calculate_reorder_quantity(stock)
               ))
           
           # 3. 基于历史消耗预测
           forecast = self.forecast_material_demand(db)
           for item in forecast:
               if item.predicted_shortage_date:
                   suggestions.append(self.create_suggestion(
                       material=item.material,
                       reason="FORECAST",
                       urgency="LOW",
                       quantity=item.predicted_quantity
                   ))
           
           # 4. AI推荐供应商
           for suggestion in suggestions:
               suggestion.suggested_supplier_id = self.recommend_supplier(
                   material=suggestion.material,
                   urgency=suggestion.urgency
               )
           
           return suggestions
       
       def recommend_supplier(self, material, urgency):
           """推荐供应商（基于绩效）"""
           suppliers = db.query(Supplier).filter(
               Supplier.materials.contains(material)
           ).all()
           
           # 根据绩效排序
           ranked = sorted(suppliers, key=lambda s: (
               s.performance.overall_score,
               -s.performance.on_time_delivery_rate if urgency == "CRITICAL" else 0
           ), reverse=True)
           
           return ranked[0].id if ranked else None
   ```

3. **供应商绩效评估** (app/services/supplier_performance_service.py)
   ```python
   class SupplierPerformanceService:
       """供应商绩效评估"""
       
       def evaluate_supplier(self, supplier_id: int, period: str) -> SupplierPerformance:
           """评估供应商绩效"""
           
           # 获取该供应商在评估期内的所有采购订单
           orders = db.query(PurchaseOrder).filter(
               PurchaseOrder.supplier_id == supplier_id,
               PurchaseOrder.created_at >= period_start,
               PurchaseOrder.created_at <= period_end
           ).all()
           
           # 1. 准时交货率
           on_time_count = sum(1 for o in orders if not o.is_delayed)
           on_time_rate = on_time_count / len(orders) if orders else 0
           
           # 2. 质量合格率
           pass_count = sum(1 for o in orders if o.quality_inspection_result == "PASS")
           quality_rate = pass_count / len(orders) if orders else 0
           
           # 3. 价格竞争力（与市场均价对比）
           avg_price = self.calculate_average_price(orders)
           market_price = self.get_market_price(supplier_id)
           price_score = min(market_price / avg_price, 1.0) if avg_price > 0 else 0
           
           # 4. 响应速度（报价响应时间）
           response_times = self.get_response_times(supplier_id, period)
           avg_response = sum(response_times) / len(response_times) if response_times else 0
           response_score = max(1 - avg_response / 24, 0)  # 24小时为基准
           
           # 5. 综合评分
           overall_score = (
               on_time_rate * 0.4 +
               quality_rate * 0.3 +
               price_score * 0.2 +
               response_score * 0.1
           ) * 100
           
           return SupplierPerformance(
               supplier_id=supplier_id,
               evaluation_period=period,
               on_time_delivery_rate=on_time_rate,
               quality_pass_rate=quality_rate,
               price_competitiveness=price_score,
               response_speed=response_score,
               overall_score=overall_score
           )
   ```

4. **API接口** (10个)
   - `GET /api/v1/purchase/suggestions` - 获取采购建议列表
   - `POST /api/v1/purchase/suggestions/{id}/approve` - 批准采购建议
   - `POST /api/v1/purchase/suggestions/{id}/create-order` - 采购建议转订单
   - `GET /api/v1/purchase/suppliers/{id}/performance` - 供应商绩效
   - `POST /api/v1/purchase/suppliers/{id}/evaluate` - 触发绩效评估
   - `GET /api/v1/purchase/suppliers/ranking` - 供应商排名
   - `POST /api/v1/purchase/quotations` - 创建报价
   - `GET /api/v1/purchase/quotations/compare` - 比价
   - `GET /api/v1/purchase/orders/{id}/tracking` - 订单跟踪
   - `POST /api/v1/purchase/orders/{id}/receive` - 收货确认

5. **测试用例** (25+)
   - 采购建议生成测试
   - 供应商推荐算法测试
   - 绩效评估计算测试
   - 报价比价测试

6. **文档**
   - 采购管理系统设计文档
   - 供应商绩效评估指南
   - API使用手册

### 技术要求
- 所有模型包含 `tenant_id` 和 `extend_existing=True`
- 供应商推荐算法可配置权重
- 绩效评估支持多维度
- API支持批量操作

### 验收标准
- ✅ 10个API全部可用
- ✅ 采购建议引擎正常运行
- ✅ 供应商绩效评估准确
- ✅ 测试覆盖率 ≥ 80%
- ✅ 文档完整

### 输出文件
- `Agent_Team_1_智能采购管理_交付报告.md`

---

## Team 2: 物料全流程跟踪系统

### 任务目标
实现物料从采购到消耗的全生命周期跟踪，包括入库、领用、消耗、库存盘点。

### 交付清单

1. **数据模型增强** (4个新表)
   ```python
   # app/models/material_tracking.py
   
   class MaterialTransaction(Base):
       """物料交易记录表（全流程跟踪）"""
       id = Column(Integer, primary_key=True)
       material_id = Column(Integer, ForeignKey('materials.id'))
       transaction_type = Column(String)  # PURCHASE_IN/TRANSFER_IN/ISSUE/RETURN/ADJUST/SCRAP
       quantity = Column(Decimal)
       unit_price = Column(Decimal)
       source_location = Column(String)  # 来源位置
       target_location = Column(String)  # 目标位置
       related_order_id = Column(Integer)  # 关联订单（采购单/工单/领料单）
       batch_number = Column(String)  # 批次号
       operator_id = Column(Integer)
       created_at = Column(DateTime)
       remark = Column(Text)
   
   class MaterialStock(Base):
       """物料库存表（实时库存）"""
       id = Column(Integer, primary_key=True)
       material_id = Column(Integer, ForeignKey('materials.id'))
       location = Column(String)  # 仓库位置
       batch_number = Column(String)
       quantity = Column(Decimal)
       available_quantity = Column(Decimal)  # 可用数量（扣除预留）
       reserved_quantity = Column(Decimal)  # 预留数量
       unit_price = Column(Decimal)  # 单价（加权平均）
       last_update = Column(DateTime)
   
   class MaterialReservation(Base):
       """物料预留表"""
       id = Column(Integer, primary_key=True)
       material_id = Column(Integer)
       project_id = Column(Integer)  # 预留给哪个项目
       reserved_quantity = Column(Decimal)
       reservation_date = Column(DateTime)
       expected_use_date = Column(Date)
       status = Column(String)  # ACTIVE/USED/CANCELLED
   
   class StockAdjustment(Base):
       """库存调整表（盘点/损耗）"""
       id = Column(Integer, primary_key=True)
       material_id = Column(Integer)
       location = Column(String)
       original_quantity = Column(Decimal)
       adjusted_quantity = Column(Decimal)
       difference = Column(Decimal)
       adjustment_type = Column(String)  # INVENTORY/DAMAGE/LOSS/CORRECTION
       reason = Column(Text)
       operator_id = Column(Integer)
       approved_by = Column(Integer)
       created_at = Column(DateTime)
   ```

2. **库存管理服务** (app/services/inventory_management_service.py)
   ```python
   class InventoryManagementService:
       """库存管理服务"""
       
       def update_stock(self, transaction: MaterialTransaction):
           """更新库存（基于交易记录）"""
           material_id = transaction.material_id
           location = transaction.target_location
           
           # 查找或创建库存记录
           stock = db.query(MaterialStock).filter(
               MaterialStock.material_id == material_id,
               MaterialStock.location == location,
               MaterialStock.batch_number == transaction.batch_number
           ).first()
           
           if not stock:
               stock = MaterialStock(
                   material_id=material_id,
                   location=location,
                   batch_number=transaction.batch_number,
                   quantity=0,
                   available_quantity=0
               )
               db.add(stock)
           
           # 根据交易类型更新数量
           if transaction.transaction_type in ['PURCHASE_IN', 'TRANSFER_IN', 'RETURN']:
               stock.quantity += transaction.quantity
               stock.available_quantity += transaction.quantity
           elif transaction.transaction_type in ['ISSUE', 'SCRAP']:
               stock.quantity -= transaction.quantity
               stock.available_quantity -= transaction.quantity
           
           # 更新加权平均单价
           if transaction.transaction_type == 'PURCHASE_IN':
               total_value = stock.quantity * stock.unit_price + transaction.quantity * transaction.unit_price
               total_quantity = stock.quantity + transaction.quantity
               stock.unit_price = total_value / total_quantity if total_quantity > 0 else 0
           
           stock.last_update = datetime.utcnow()
           db.commit()
       
       def reserve_material(self, material_id: int, project_id: int, quantity: Decimal):
           """预留物料"""
           # 检查可用库存
           available = self.get_available_quantity(material_id)
           if available < quantity:
               raise InsufficientStockError(f"库存不足：需要{quantity}，可用{available}")
           
           # 创建预留记录
           reservation = MaterialReservation(
               material_id=material_id,
               project_id=project_id,
               reserved_quantity=quantity,
               reservation_date=datetime.utcnow(),
               status="ACTIVE"
           )
           db.add(reservation)
           
           # 更新库存的预留数量
           stocks = db.query(MaterialStock).filter(
               MaterialStock.material_id == material_id
           ).all()
           remaining = quantity
           for stock in stocks:
               if remaining <= 0:
                   break
               reserve_qty = min(stock.available_quantity, remaining)
               stock.reserved_quantity += reserve_qty
               stock.available_quantity -= reserve_qty
               remaining -= reserve_qty
           
           db.commit()
       
       def issue_material(self, material_id: int, quantity: Decimal, work_order_id: int):
           """领料"""
           # 释放预留 + 创建交易记录
           reservation = db.query(MaterialReservation).filter(
               MaterialReservation.material_id == material_id,
               MaterialReservation.status == "ACTIVE"
           ).first()
           
           if reservation:
               reservation.status = "USED"
           
           transaction = MaterialTransaction(
               material_id=material_id,
               transaction_type="ISSUE",
               quantity=quantity,
               related_order_id=work_order_id,
               created_at=datetime.utcnow()
           )
           db.add(transaction)
           
           self.update_stock(transaction)
   ```

3. **库存盘点功能** (app/services/stock_count_service.py)
   ```python
   class StockCountService:
       """库存盘点服务"""
       
       def create_count_task(self, location: str, materials: List[int]):
           """创建盘点任务"""
           task = StockCountTask(
               location=location,
               status="PENDING",
               created_at=datetime.utcnow()
           )
           db.add(task)
           db.commit()
           
           # 创建盘点明细
           for material_id in materials:
               system_qty = self.get_system_quantity(material_id, location)
               detail = StockCountDetail(
                   task_id=task.id,
                   material_id=material_id,
                   system_quantity=system_qty,
                   actual_quantity=None,  # 待录入
                   status="PENDING"
               )
               db.add(detail)
           
           db.commit()
           return task
       
       def record_actual_quantity(self, detail_id: int, actual_qty: Decimal):
           """录入实际数量"""
           detail = db.query(StockCountDetail).get(detail_id)
           detail.actual_quantity = actual_qty
           detail.difference = actual_qty - detail.system_quantity
           detail.status = "COUNTED"
           db.commit()
       
       def approve_adjustment(self, task_id: int, approver_id: int):
           """批准库存调整"""
           task = db.query(StockCountTask).get(task_id)
           details = task.details
           
           for detail in details:
               if detail.difference != 0:
                   # 创建库存调整记录
                   adjustment = StockAdjustment(
                       material_id=detail.material_id,
                       location=task.location,
                       original_quantity=detail.system_quantity,
                       adjusted_quantity=detail.actual_quantity,
                       difference=detail.difference,
                       adjustment_type="INVENTORY",
                       approved_by=approver_id,
                       created_at=datetime.utcnow()
                   )
                   db.add(adjustment)
                   
                   # 创建交易记录
                   transaction = MaterialTransaction(
                       material_id=detail.material_id,
                       transaction_type="ADJUST",
                       quantity=abs(detail.difference),
                       target_location=task.location,
                       created_at=datetime.utcnow()
                   )
                   db.add(transaction)
                   
                   # 更新库存
                   self.update_stock(transaction)
           
           task.status = "COMPLETED"
           db.commit()
   ```

4. **API接口** (12个)
   - `GET /api/v1/inventory/stocks` - 库存查询
   - `GET /api/v1/inventory/stocks/{material_id}/transactions` - 交易记录
   - `POST /api/v1/inventory/reserve` - 预留物料
   - `POST /api/v1/inventory/issue` - 领料
   - `POST /api/v1/inventory/return` - 退料
   - `POST /api/v1/inventory/transfer` - 库存转移
   - `GET /api/v1/inventory/count/tasks` - 盘点任务列表
   - `POST /api/v1/inventory/count/tasks` - 创建盘点任务
   - `PUT /api/v1/inventory/count/details/{id}` - 录入实盘数量
   - `POST /api/v1/inventory/count/tasks/{id}/approve` - 批准调整
   - `GET /api/v1/inventory/analysis/turnover` - 库存周转率
   - `GET /api/v1/inventory/analysis/aging` - 库龄分析

5. **测试用例** (30+)
   - 入库/出库/调拨测试
   - 预留和释放测试
   - 盘点流程测试
   - 库存计算准确性测试

6. **文档**
   - 物料跟踪系统设计文档
   - 库存管理操作手册
   - 盘点流程指南

### 技术要求
- 库存更新使用数据库事务保证一致性
- 支持FIFO/LIFO/加权平均等成本核算方法
- 实时库存计算性能优化
- 支持多仓库/多批次管理

### 验收标准
- ✅ 12个API全部可用
- ✅ 库存数据实时准确
- ✅ 盘点流程完整
- ✅ 测试覆盖率 ≥ 80%
- ✅ 文档完整

### 输出文件
- `Agent_Team_2_物料全流程跟踪_交付报告.md`

---

## Team 3: 智能缺料预警系统

### 任务目标
增强缺料预警能力，实现提前预警、自动处理、影响分析。

### 交付清单

1. **数据模型增强** (3个新表)
   ```python
   # app/models/shortage_enhanced.py
   
   class ShortageAlert(Base):
       """缺料预警表（增强）"""
       id = Column(Integer, primary_key=True)
       material_id = Column(Integer, ForeignKey('materials.id'))
       project_id = Column(Integer)
       shortage_quantity = Column(Decimal)
       required_date = Column(Date)
       alert_level = Column(String)  # INFO/WARNING/CRITICAL/URGENT
       predicted_impact_days = Column(Integer)  # 预计影响天数
       estimated_cost_impact = Column(Decimal)  # 预计成本影响
       affected_work_orders = Column(JSON)  # 受影响的工单列表
       root_cause = Column(String)  # SUPPLIER_DELAY/FORECAST_ERROR/QUALITY_ISSUE
       created_at = Column(DateTime)
       status = Column(String)  # ACTIVE/RESOLVED/IGNORED
   
   class ShortageHandlingPlan(Base):
       """缺料处理方案表"""
       id = Column(Integer, primary_key=True)
       alert_id = Column(Integer, ForeignKey('shortage_alerts.id'))
       solution_type = Column(String)  # EMERGENCY_PURCHASE/SUBSTITUTE/RESCHEDULE/SPLIT_BATCH
       description = Column(Text)
       estimated_cost = Column(Decimal)
       estimated_delay = Column(Integer)  # 预计延期天数
       ai_recommended = Column(Boolean)  # 是否AI推荐
       confidence = Column(Float)  # 方案可信度
       created_at = Column(DateTime)
       selected = Column(Boolean, default=False)
   
   class MaterialDemandForecast(Base):
       """物料需求预测表"""
       id = Column(Integer, primary_key=True)
       material_id = Column(Integer)
       forecast_date = Column(Date)
       predicted_demand = Column(Decimal)
       confidence_interval_lower = Column(Decimal)
       confidence_interval_upper = Column(Decimal)
       model_type = Column(String)  # MOVING_AVERAGE/EXPONENTIAL_SMOOTHING/ML
       accuracy_score = Column(Float)
       created_at = Column(DateTime)
   ```

2. **智能预警引擎** (app/services/shortage_alert_service.py)
   ```python
   class ShortageAlertService:
       """智能缺料预警服务"""
       
       def scan_and_alert(self, db: Session):
           """扫描并生成缺料预警"""
           alerts = []
           
           # 获取所有活跃项目的物料需求
           projects = db.query(Project).filter(
               Project.status.in_(['PLANNING', 'IN_PROGRESS'])
           ).all()
           
           for project in projects:
               # 获取项目BOM
               bom_items = self.get_project_bom(project.id)
               
               for item in bom_items:
                   # 计算需求量
                   required_qty = item.quantity * project.quantity
                   
                   # 获取可用库存（含在途物料）
                   available = self.get_available_stock(item.material_id)
                   on_order = self.get_on_order_quantity(item.material_id)
                   total_available = available + on_order
                   
                   # 判断是否缺料
                   if total_available < required_qty:
                       shortage_qty = required_qty - total_available
                       
                       # 计算预警级别
                       alert_level = self.calculate_alert_level(
                           shortage_qty=shortage_qty,
                           required_date=item.required_date,
                           critical_path=item.on_critical_path
                       )
                       
                       # 预测影响
                       impact = self.predict_impact(
                           material=item.material,
                           shortage_qty=shortage_qty,
                           project=project
                       )
                       
                       # 创建预警
                       alert = ShortageAlert(
                           material_id=item.material_id,
                           project_id=project.id,
                           shortage_quantity=shortage_qty,
                           required_date=item.required_date,
                           alert_level=alert_level,
                           predicted_impact_days=impact['delay_days'],
                           estimated_cost_impact=impact['cost'],
                           affected_work_orders=impact['work_orders'],
                           status="ACTIVE"
                       )
                       db.add(alert)
                       alerts.append(alert)
           
           db.commit()
           return alerts
       
       def generate_solutions(self, alert: ShortageAlert):
           """生成处理方案（AI辅助）"""
           solutions = []
           
           # 方案1: 紧急采购
           emergency_purchase = self.calculate_emergency_purchase(alert)
           solutions.append(emergency_purchase)
           
           # 方案2: 替代料
           substitutes = self.find_substitute_materials(alert.material_id)
           for sub in substitutes:
               solution = self.create_substitute_solution(alert, sub)
               solutions.append(solution)
           
           # 方案3: 重新排期
           reschedule = self.calculate_reschedule_plan(alert)
           solutions.append(reschedule)
           
           # 方案4: 分批生产
           split_batch = self.calculate_split_batch_plan(alert)
           solutions.append(split_batch)
           
           # AI评分和排序
           for solution in solutions:
               solution.confidence = self.ai_evaluate_solution(solution)
           
           solutions.sort(key=lambda x: x.confidence, reverse=True)
           return solutions
   ```

3. **需求预测引擎** (app/services/demand_forecast_service.py)
   ```python
   class DemandForecastService:
       """需求预测服务"""
       
       def forecast_material_demand(self, material_id: int, days: int = 90):
           """预测物料需求"""
           # 获取历史消耗数据
           history = self.get_consumption_history(material_id, days=365)
           
           # 使用移动平均法预测
           forecast = []
           window_size = 30
           
           for i in range(days):
               date = datetime.utcnow().date() + timedelta(days=i)
               
               # 计算移动平均
               recent_consumption = history[-window_size:]
               avg_consumption = sum(recent_consumption) / len(recent_consumption)
               
               # 考虑季节性因素
               seasonal_factor = self.get_seasonal_factor(date)
               predicted = avg_consumption * seasonal_factor
               
               # 计算置信区间
               std_dev = self.calculate_std_dev(recent_consumption)
               lower = predicted - 1.96 * std_dev
               upper = predicted + 1.96 * std_dev
               
               forecast_item = MaterialDemandForecast(
                   material_id=material_id,
                   forecast_date=date,
                   predicted_demand=predicted,
                   confidence_interval_lower=max(0, lower),
                   confidence_interval_upper=upper,
                   model_type="MOVING_AVERAGE",
                   created_at=datetime.utcnow()
               )
               forecast.append(forecast_item)
           
           return forecast
   ```

4. **API接口** (10个)
   - `GET /api/v1/shortage/alerts` - 缺料预警列表
   - `GET /api/v1/shortage/alerts/{id}` - 预警详情
   - `POST /api/v1/shortage/scan` - 触发扫描
   - `GET /api/v1/shortage/alerts/{id}/solutions` - 获取处理方案
   - `POST /api/v1/shortage/alerts/{id}/resolve` - 标记解决
   - `GET /api/v1/shortage/forecast/{material_id}` - 需求预测
   - `GET /api/v1/shortage/analysis/trend` - 缺料趋势分析
   - `GET /api/v1/shortage/analysis/root-cause` - 根因分析
   - `GET /api/v1/shortage/impact/projects` - 缺料对项目的影响
   - `POST /api/v1/shortage/notifications/subscribe` - 订阅预警通知

5. **测试用例** (28+)
   - 预警扫描算法测试
   - 预警级别计算测试
   - 影响预测测试
   - 处理方案生成测试
   - 需求预测准确性测试

6. **文档**
   - 缺料预警系统设计文档
   - 需求预测模型说明
   - 处理方案推荐指南

### 技术要求
- 预警扫描支持定时任务
- 需求预测支持多种算法（移动平均/指数平滑/机器学习）
- 影响分析考虑关键路径
- 处理方案AI评分

### 验收标准
- ✅ 10个API全部可用
- ✅ 预警准确率 ≥ 85%
- ✅ 预测误差 ≤ 15%
- ✅ 测试覆盖率 ≥ 80%
- ✅ 文档完整

### 输出文件
- `Agent_Team_3_智能缺料预警_交付报告.md`

---

## Team 4: 系统集成和测试

### 任务目标
整合前三个Team的成果，确保系统闭环运作，编写集成测试和文档。

### 交付清单

1. **系统集成**
   - 采购建议 → 采购订单 → 入库 → 库存更新
   - 缺料预警 → 采购建议 → 紧急采购
   - 物料预留 → 领料 → 消耗 → 库存更新
   - 盘点 → 库存调整 → 预警重新计算

2. **业务流程测试** (15个场景)
   - 场景1: 完整采购流程
   - 场景2: 缺料预警触发紧急采购
   - 场景3: 物料预留和领用
   - 场景4: 库存盘点和调整
   - 场景5: 供应商绩效评估
   - 场景6: 替代料使用
   - 场景7: 批次追溯
   - 场景8: 库存周转分析
   - 场景9: 需求预测准确性
   - 场景10: 多项目物料竞争
   - 场景11: 紧急插单处理
   - 场景12: 质量问题退货
   - 场景13: 库存转移
   - 场景14: 过期物料处理
   - 场景15: 成本核算准确性

3. **性能测试**
   - 库存实时查询性能（< 100ms）
   - 预警扫描性能（1000个项目 < 5秒）
   - 需求预测性能（1年数据 < 2秒）
   - 并发库存更新测试

4. **完整文档** (5份)
   - **系统架构设计**: 采购-物料-库存闭环架构
   - **业务流程手册**: 采购→入库→领用→消耗完整流程
   - **API集成指南**: 前后端集成说明
   - **运维手册**: 定时任务配置、监控指标
   - **用户手册**: 采购员、仓管员、PMC操作指南

5. **数据初始化脚本**
   - 供应商数据初始化
   - 物料数据初始化
   - 仓库位置初始化
   - 演示数据生成

6. **监控和告警**
   - 库存低于安全库存告警
   - 缺料预警通知
   - 采购订单延期提醒
   - 库存异常波动检测

### 技术要求
- 集成测试覆盖所有关键流程
- 性能测试使用真实数据量
- 文档图文并茂
- 监控指标可配置

### 验收标准
- ✅ 15个业务场景测试通过
- ✅ 性能测试达标
- ✅ 5份文档完整
- ✅ 数据初始化脚本可用
- ✅ 监控告警配置完成

### 输出文件
- `Agent_Team_4_系统集成测试_交付报告.md`

---

## 技术约束

### 通用要求
1. **多租户支持**: 所有表必须包含 `tenant_id` 和 `extend_existing=True`
2. **数据一致性**: 库存更新使用数据库事务
3. **性能要求**: 关键查询 < 100ms，批量操作支持异步
4. **代码质量**: PEP8、类型注解、完整注释
5. **测试覆盖**: ≥ 80%

### 集成要求
1. **与生产模块衔接**: 工单领料 → 库存扣减
2. **与销售模块衔接**: 项目BOM → 物料需求
3. **与财务模块衔接**: 采购成本 → 财务记录
4. **通知系统**: 预警、延期提醒集成通知模块

---

## 验收标准

### 功能验收
- [ ] 采购建议引擎正常运行
- [ ] 供应商绩效评估准确
- [ ] 库存实时更新准确
- [ ] 物料全流程可追溯
- [ ] 缺料预警准确率 ≥ 85%
- [ ] 需求预测误差 ≤ 15%
- [ ] 15个业务场景测试通过

### 测试验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试全部通过
- [ ] 性能测试达标

### 文档验收
- [ ] 架构设计完整
- [ ] API文档完整
- [ ] 用户手册完整
- [ ] 运维手册完整

---

## 时间计划

**启动时间**: 2026-02-16 08:16  
**预计完成**: 2026-02-16 10:16 (2小时)

**并行执行**:
- Team 1-3: 并行开发核心功能 (1-1.5小时)
- Team 4: 在前三个Team完成后集成测试 (0.5-1小时)

**检查点**:
- 1小时后: 检查Teams 1-3进度
- 1.5小时后: 开始集成测试
- 2小时后: 最终验收

---

## 预期成果

### 核心功能
- ✅ 智能采购建议（基于缺料/安全库存/预测）
- ✅ 供应商绩效评估和排名
- ✅ 物料全流程跟踪（采购→入库→领用→消耗）
- ✅ 实时库存管理（多仓库/多批次）
- ✅ 智能缺料预警（提前预警/影响分析）
- ✅ 需求预测（多种算法）
- ✅ 处理方案AI推荐

### 业务价值
- 减少缺料导致的延期（预计减少30-50%）
- 优化库存成本（预计降低20-30%）
- 提高采购效率（预计提升40%）
- 供应商管理科学化（数据驱动决策）

### 交付物
- 32个API接口
- 93+测试用例
- 14份完整文档
- 完整的采购-物料-库存闭环系统

---

**准备启动，等待确认！** 🚀
