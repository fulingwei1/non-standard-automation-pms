# Phase 1 技术设计文档 - 流程融合关键断点修复

> **文档版本**: v1.0
> **创建日期**: 2026-01-25
> **作者**: PMO技术团队
> **状态**: 设计完成，待实施

---

## 一、项目概述

### 1.1 目标

修复非标自动化项目管理系统的4个关键流程断点，完善流程自动化程度，提升系统整体效率。

### 1.2 背景

当前系统已完成核心业务流程功能，但存在以下流程断点：
1. 合同签订后，付款节点与项目里程碑未自动绑定
2. 验收通过后，开票需要手动触发
3. BOM审核通过后，采购需求需要手动创建
4. 里程碑延期后，项目风险等级未自动升级

这些断点导致：
- 数据重复录入
- 流程效率低下
- 数据一致性风险
- 管理层决策滞后

---

## 二、技术设计

### 2.1 功能1：合同→项目自动生成完善

#### 2.1.1 需求描述

合同签订后，系统应自动：
1. 创建项目（已实现）
2. 将合同中的付款节点自动关联到项目里程碑
3. 同步合同金额到项目
4. 同步SOW/验收标准到项目

#### 2.1.2 技术实现方案

##### 数据模型变更

```python
# app/models/sales/contract.py

class Contract(Base, TimestampMixin):
    __tablename__ = "contracts"

    # ... existing fields ...

    # 新增字段
    payment_nodes = Column(JSON, comment="付款节点列表")
    sow_text = Column(Text, comment="SOW文本")
    acceptance_criteria = Column(JSON, comment="验收标准")

# app/models/project/payment_plan.py

class PaymentPlan(Base, TimestampMixin):
    __tablename__ = "payment_plans"

    # ... existing fields ...

    # 新增字段
    milestone_id = Column(Integer, ForeignKey("project_milestones.id"), comment="关联的里程碑ID")
```

##### 数据库迁移

```sql
-- migrations/20260125_contract_payment_nodes_binding.sql

-- 1. 合同表添加付款节点字段
ALTER TABLE contracts ADD COLUMN payment_nodes JSON;
ALTER TABLE contracts ADD COLUMN sow_text TEXT;
ALTER TABLE contracts ADD COLUMN acceptance_criteria JSON;

-- 2. 收款计划表添加里程碑关联字段
ALTER TABLE payment_plans ADD COLUMN milestone_id INTEGER;
ALTER TABLE payment_plans ADD FOREIGN KEY (milestone_id) REFERENCES project_milestones(id);

-- 3. 创建索引
CREATE INDEX idx_payment_plans_milestone ON payment_plans(milestone_id);
```

##### 业务逻辑实现

```python
# app/services/sales/contract_service.py

from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class ContractService:
    @staticmethod
    async def create_project_from_contract(
        db: AsyncSession,
        contract_id: int
    ) -> Dict[str, Any]:
        """从合同创建项目，自动绑定付款节点到里程碑"""

        # 1. 查询合同
        result = await db.execute(
            select(Contract, Customer).where(Contract.id == contract_id)
            .join(Customer, Contract.customer_id == Customer.id)
        )
        contract = result.scalar_one_or_none()

        if not contract:
            raise ValueError(f"合同不存在: {contract_id}")

        # 2. 创建项目
        project = Project(
            code=await ProjectService.generate_code(),
            name=f"{contract.code}-{contract.customer.name}",
            customer_id=contract.customer_id,
            contract_id=contract_id,
            amount=contract.amount,
            sow_text=contract.sow_text,
            acceptance_criteria=contract.acceptance_criteria,
            stage="S1",  # 需求进入
            status="ST01",  # 未启动
            health_status="H1",  # 正常
        )

        db.add(project)
        await db.flush()

        # 3. 如果有付款节点，创建收款计划并关联里程碑
        if contract.payment_nodes:
            payment_nodes = contract.payment_nodes
            milestone_count = len(payment_nodes)

            for idx, node in enumerate(payment_nodes):
                # 计算里程碑序号
                milestone_seq = idx + 1

                # 创建收款计划
                payment_plan = PaymentPlan(
                    project_id=project.id,
                    contract_id=contract_id,
                    node_name=node.get("name", f"付款节点{milestone_seq}"),
                    percentage=node.get("percentage", 100 / milestone_count),
                    amount=contract.amount * node.get("percentage", 100 / milestone_count) / 100,
                    due_date=node.get("due_date"),
                    milestone_id=None,  # 稍后关联
                    status="PENDING",
                )

                db.add(payment_plan)
                await db.flush()

                # 创建对应的里程碑（简化逻辑，实际应根据WBS或项目模板创建）
                milestone = ProjectMilestone(
                    project_id=project.id,
                    name=f"M{milestone_seq}",
                    description=node.get("description", f"付款里程碑{milestone_seq}"),
                    planned_date=node.get("due_date"),
                    sequence=milestone_seq,
                    status="NOT_STARTED",
                )

                db.add(milestone)
                await db.flush()

                # 关联付款计划与里程碑
                payment_plan.milestone_id = milestone.id
```

##### API端点

```python
# app/api/v1/endpoints/sales/contracts.py

@router.post("/{contract_id}/create-project")
async def create_project_from_contract(
    contract_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从合同创建项目，自动绑定付款节点到里程碑"""

    try:
        result = await ContractService.create_project_from_contract(db, contract_id)

        await db.commit()

        return {
            "success": True,
            "message": "项目创建成功，付款节点已关联到里程碑",
            "project_id": result["project_id"],
            "payment_plans_count": result["payment_plans_count"],
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2.1.3 测试计划

| 测试用例 | 输入 | 预期输出 | 验证方法 |
|---------|------|----------|---------|
| TC1: 带付款节点的合同创建项目 | 合同数据，含3个付款节点 | 项目创建成功，3个里程碑+3个收款计划 | API返回数据，查询数据库验证 |
| TC2: 不带付款节点的合同创建项目 | 合同数据，无付款节点 | 项目创建成功，无里程碑关联 | API返回数据 |
| TC3: 付款节点金额总和验证 | 付款节点百分比总和100% | 收款计划金额总和=合同金额 | 计算验证 |

---

### 2.2 功能2：验收→开票自动触发

#### 2.2.1 需求描述

验收单通过后，系统应自动：
1. 创建发票
2. 关联验收单与发票
3. 发票金额根据验收结论自动计算
4. 触发开票流程

#### 2.2.2 技术实现方案

##### 数据模型变更

```python
# app/models/sales/invoice.py

class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    # ... existing fields ...

    # 新增字段
    acceptance_order_id = Column(Integer, ForeignKey("acceptance_orders.id"), comment="关联的验收单ID")
    auto_generated = Column(Boolean, default=False, comment="是否自动生成")
```

##### 数据库迁移

```sql
-- migrations/20260125_acceptance_invoice_trigger.sql

ALTER TABLE invoices ADD COLUMN acceptance_order_id INTEGER;
ALTER TABLE invoices ADD COLUMN auto_generated BOOLEAN DEFAULT FALSE;
ALTER TABLE invoices ADD FOREIGN KEY (acceptance_order_id) REFERENCES acceptance_orders(id);
CREATE INDEX idx_invoices_acceptance_order ON invoices(acceptance_order_id);
```

##### 业务逻辑实现

```python
# app/services/acceptance/acceptance_service.py

class AcceptanceService:
    @staticmethod
    async def complete_acceptance_order(
        db: AsyncSession,
        order_id: int,
        completed_by: int,
        completion_notes: str = None
    ) -> Dict[str, Any]:
        """完成验收单，自动触发开票"""

        # 1. 查询验收单
        result = await db.execute(
            select(AcceptanceOrder, Project, Contract, Customer)
            .where(AcceptanceOrder.id == order_id)
            .join(Project, AcceptanceOrder.project_id == Project.id)
            .outerjoin(Contract, Project.contract_id == Contract.id)
            .outerjoin(Customer, Contract.customer_id == Customer.id)
        )
        acceptance_order = result.scalar_one_or_none()

        if not acceptance_order:
            raise ValueError(f"验收单不存在: {order_id}")

        # 2. 更新验收单状态
        acceptance_order.status = "PASSED"
        acceptance_order.completed_at = datetime.now()
        acceptance_order.completed_by = completed_by
        acceptance_order.completion_notes = completion_notes

        await db.flush()

        # 3. 自动创建发票
        invoice = Invoice(
            code=await InvoiceService.generate_code(),
            project_id=acceptance_order.project_id,
            customer_id=acceptance_order.project.customer_id
            or acceptance_order.contract.customer_id
            if acceptance_order.contract else None,
            contract_id=acceptance_order.project.contract_id,
            amount=acceptance_order.total_amount,  # 使用验收单金额
            invoice_type="AUTOMATIC",  # 自动开票
            acceptance_order_id=order_id,
            auto_generated=True,
            status="DRAFT",
        )

        db.add(invoice)
        await db.flush()

        # 4. 更新项目状态（如果需要）
        if acceptance_order.acceptance_type == "SAT":
            # 现场验收通过，进入质保阶段
            acceptance_order.project.stage = "S9"
            acceptance_order.project.status = "ST30"  # 已完结

        await db.commit()

        return {
            "acceptance_order_id": order_id,
            "invoice_id": invoice.id,
            "invoice_code": invoice.code,
            "auto_generated": True,
        }
```

##### 事件触发器

```python
# app/core/events/acceptance_events.py

from fastapi.concurrency import run_in_threadpool

@event_listener(AcceptanceOrder.completed)
async def on_acceptance_completed(event: AcceptanceOrderCompletedEvent):
    """验收完成事件处理器，自动触发开票"""

    db = get_db_session()
    try:
        result = await AcceptanceService.complete_acceptance_order(
            db=db,
            order_id=event.order_id,
            completed_by=event.completed_by,
        )

        # 发送通知
        await NotificationService.send_invoice_generated_notification(
            db=db,
            invoice_id=result["invoice_id"],
            acceptance_order_id=result["acceptance_order_id"],
        )

    finally:
        await db.close()
```

#### 2.2.3 测试计划

| 测试用例 | 输入 | 预期输出 | 验证方法 |
|---------|------|----------|---------|
| TC1: FAT验收通过触发开票 | FAT验收单，通过 | 创建发票，状态DRAFT | API返回，数据库验证 |
| TC2: SAT验收通过触发开票 | SAT验收单，通过 | 创建发票，项目进入S9 | API返回，状态验证 |
| TC3: 验收单未通过不触发开票 | 验收单，不通过 | 不创建发票 | API返回，数据库验证无发票 |

---

### 2.3 功能3：BOM→采购自动触发

#### 2.3.1 需求描述

BOM审核通过后，系统应自动：
1. 生成采购需求
2. 标准件自动创建采购订单
3. 缺料预警自动触发紧急采购

#### 2.3.2 技术实现方案

##### 数据模型变更

```python
# app/models/purchase/purchase_order.py

class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    # ... existing fields ...

    # 新增字段
    auto_generated = Column(Boolean, default=False, comment="是否自动生成")
    bom_id = Column(Integer, ForeignKey("bom_headers.id"), comment="关联的BOM ID")
    source_type = Column(String(20), comment="来源类型: MANUAL, AUTO_BOM, AUTO_SHORTAGE")
```

##### 数据库迁移

```sql
-- migrations/20260125_bom_purchase_auto_trigger.sql

ALTER TABLE purchase_orders ADD COLUMN auto_generated BOOLEAN DEFAULT FALSE;
ALTER TABLE purchase_orders ADD COLUMN bom_id INTEGER;
ALTER TABLE purchase_orders ADD COLUMN source_type VARCHAR(20);
ALTER TABLE purchase_orders ADD FOREIGN KEY (bom_id) REFERENCES bom_headers(id);
CREATE INDEX idx_purchase_orders_bom ON purchase_orders(bom_id);
CREATE INDEX idx_purchase_orders_source_type ON purchase_orders(source_type);
```

##### 业务逻辑实现

```python
# app/services/bom/bom_service.py

class BOMService:
    @staticmethod
    async def approve_bom_and_create_purchase_orders(
        db: AsyncSession,
        bom_id: int,
        approved_by: int
    ) -> Dict[str, Any]:
        """BOM审核通过，自动创建采购订单"""

        # 1. 查询BOM
        result = await db.execute(
            select(BomHeader, Project)
            .where(BomHeader.id == bom_id)
            .join(Project, BomHeader.project_id == Project.id)
        )
        bom = result.scalar_one_or_none()

        if not bom:
            raise ValueError(f"BOM不存在: {bom_id}")

        # 2. 更新BOM状态
        bom.status = "APPROVED"
        bom.approved_by = approved_by
        bom.approved_at = datetime.now()

        await db.flush()

        # 3. 查询BOM明细
        items_result = await db.execute(
            select(BomItem, Material)
            .where(BomItem.bom_id == bom_id)
            .join(Material, BomItem.material_id == Material.id)
            .order_by(BomItem.id)
        )
        bom_items = items_result.scalars().all()

        # 4. 按供应商分组
        from collections import defaultdict
        supplier_groups = defaultdict(list)

        for item in bom_items:
            supplier_id = item.material.primary_supplier_id or item.material.default_supplier_id
            supplier_groups[supplier_id].append(item)

        # 5. 为每个供应商创建采购订单
        created_orders = []
        for supplier_id, items in supplier_groups.items():
            if not supplier_id:
                continue  # 跳过无供应商的物料

            # 创建采购订单
            purchase_order = PurchaseOrder(
                code=await PurchaseOrderService.generate_code(),
                project_id=bom.project_id,
                supplier_id=supplier_id,
                bom_id=bom_id,
                source_type="AUTO_BOM",
                auto_generated=True,
                order_type="STANDARD",  # 标准件采购
                status="DRAFT",
            )

            db.add(purchase_order)
            await db.flush()

            # 添加采购订单明细
            for item in items:
                po_item = PurchaseOrderItem(
                    purchase_order_id=purchase_order.id,
                    material_id=item.material_id,
                    bom_item_id=item.id,
                    quantity=item.quantity * 1.1,  # 增加10%安全库存
                    unit_price=item.material.standard_price,
                    amount=item.quantity * 1.1 * item.material.standard_price,
                    expected_date=bom.project.planned_delivery_date,
                )

                db.add(po_item)

            created_orders.append(purchase_order.id)

        await db.commit()

        return {
            "bom_id": bom_id,
            "purchase_orders_count": len(created_orders),
            "purchase_order_ids": created_orders,
        }
```

#### 2.3.3 测试计划

| 测试用例 | 输入 | 预期输出 | 验证方法 |
|---------|------|----------|---------|
| TC1: BOM审核通过自动创建PO | 已审核的BOM，含多个供应商 | 按供应商创建多个PO | API返回，数据库验证 |
| TC2: 标准件自动创建PO | BOM明细中标准件物料 | 自动创建标准件采购订单 | 物料类型验证 |
| TC3: 安全库存计算验证 | BOM数量100，安全系数1.1 | PO数量110 | 数量验证 |

---

### 2.4 功能4：进度→预警自动升级

#### 2.4.1 需求描述

里程碑延期后，系统应自动：
1. 升级项目风险等级
2. 通知管理层
3. 记录风险历史

#### 2.4.2 技术实现方案

##### 数据模型变更

```python
# app/models/project/project.py

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    # ... existing fields ...

    # 新增字段
    risk_level = Column(String(20), default="LOW", comment="风险等级: LOW, MEDIUM, HIGH, CRITICAL")
    risk_factors = Column(JSON, comment="风险因子")
```

##### 数据库迁移

```sql
-- migrations/20260125_project_risk_auto_upgrade.sql

ALTER TABLE projects ADD COLUMN risk_level VARCHAR(20) DEFAULT 'LOW';
ALTER TABLE projects ADD COLUMN risk_factors JSON;
CREATE INDEX idx_projects_risk_level ON projects(risk_level);
```

##### 业务逻辑实现

```python
# app/services/project/risk_service.py

class ProjectRiskService:
    @staticmethod
    async def auto_upgrade_risk_level(
        db: AsyncSession,
        project_id: int
    ) -> Dict[str, Any]:
        """自动升级项目风险等级"""

        # 1. 查询项目
        result = await db.execute(
            select(Project)
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"项目不存在: {project_id}")

        # 2. 查询里程碑延期情况
        today = date.today()

        overdue_milestones_result = await db.execute(
            select(ProjectMilestone)
            .where(
                and_(
                    ProjectMilestone.project_id == project_id,
                    ProjectMilestone.planned_date < today,
                    ProjectMilestone.status.in_(["NOT_STARTED", "IN_PROGRESS"])
                )
            )
        )
        overdue_milestones = overdue_milestones_result.scalars().all()

        # 3. 计算风险因子
        risk_factors = {
            "overdue_milestones_count": len(overdue_milestones),
            "total_milestones_count": 0,  # 稍后计算
            "overdue_tasks_count": 0,  # 稍后计算
            "total_tasks_count": 0,  # 稍后计算
            "shortage_alerts_count": 0,  # 稍后计算
            "cost_overrun_percentage": 0,  # 稍后计算
        }

        # 计算总里程碑数
        total_milestones_result = await db.execute(
            select(func.count(ProjectMilestone.id))
            .where(ProjectMilestone.project_id == project_id)
        )
        risk_factors["total_milestones_count"] = total_milestones_result.scalar()

        # 4. 根据风险因子计算风险等级
        new_risk_level = ProjectRiskService._calculate_risk_level(risk_factors)

        # 5. 更新项目风险等级
        old_risk_level = project.risk_level
        project.risk_level = new_risk_level
        project.risk_factors = risk_factors

        # 6. 如果风险等级升级，记录历史
        risk_history = ProjectRiskHistory(
            project_id=project_id,
            old_risk_level=old_risk_level,
            new_risk_level=new_risk_level,
            risk_factors=risk_factors,
            triggered_by="MILESTONE_OVERDUE",
            triggered_at=datetime.now(),
        )

        db.add(risk_history)

        await db.commit()

        # 7. 如果风险等级升级，发送通知
        if ProjectRiskService._is_risk_upgrade(old_risk_level, new_risk_level):
            await NotificationService.send_risk_upgrade_notification(
                db=db,
                project_id=project_id,
                old_level=old_risk_level,
                new_level=new_risk_level,
                risk_factors=risk_factors,
            )

        return {
            "project_id": project_id,
            "old_risk_level": old_risk_level,
            "new_risk_level": new_risk_level,
            "risk_factors": risk_factors,
        }

    @staticmethod
    def _calculate_risk_level(factors: Dict[str, Any]) -> str:
        """根据风险因子计算风险等级"""

        overdue_milestone_ratio = 0
        if factors["total_milestones_count"] > 0:
            overdue_milestone_ratio = (
                factors["overdue_milestones_count"]
                / factors["total_milestones_count"]
            )

        # 简单规则
        if overdue_milestone_ratio >= 0.5:
            return "CRITICAL"
        elif overdue_milestone_ratio >= 0.3:
            return "HIGH"
        elif overdue_milestone_ratio >= 0.1:
            return "MEDIUM"
        else:
            return "LOW"

    @staticmethod
    def _is_risk_upgrade(old_level: str, new_level: str) -> bool:
        """判断风险等级是否升级"""
        level_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return level_order.get(new_level, 0) > level_order.get(old_level, 0)
```

##### 定时任务

```python
# app/utils/scheduled_tasks/risk_monitoring.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job(
    'cron',
    hour=8, minute=0,  # 每天早上8点执行
    id='risk_monitoring'
)
async def risk_monitoring_job():
    """风险监控定时任务"""

    db = get_db_session()
    try:
        # 查询所有进行中的项目
        result = await db.execute(
            select(Project.id)
            .where(Project.status.in_(["ST02", "ST03", "ST04", "ST05", "ST06", "ST07", "ST08"]))
        )
        project_ids = result.scalars().all()

        # 对每个项目执行风险等级升级检查
        for project_id in project_ids:
            await ProjectRiskService.auto_upgrade_risk_level(db, project_id)

    finally:
        await db.close()
```

#### 2.4.3 测试计划

| 测试用例 | 输入 | 预期输出 | 验证方法 |
|---------|------|----------|---------|
| TC1: 里程碑逾期10% | 10%里程碑逾期 | 风险等级MEDIUM | API返回，状态验证 |
| TC2: 里程碑逾期50% | 50%里程碑逾期 | 风险等级CRITICAL | API返回，状态验证 |
| TC3: 风险等级升级通知 | 风险等级LOW→HIGH | 发送通知给管理层 | 通知记录验证 |

---

## 三、数据库迁移清单

| 序号 | 迁移文件 | 说明 | 优先级 |
|------|----------|------|--------|
| 1 | 20260125_contract_payment_nodes_binding.sql | 合同付款节点与里程碑关联 | P0 |
| 2 | 20260125_acceptance_invoice_trigger.sql | 验收自动触发开票 | P0 |
| 3 | 20260125_bom_purchase_auto_trigger.sql | BOM自动创建采购订单 | P0 |
| 4 | 20260125_project_risk_auto_upgrade.sql | 项目风险自动升级 | P0 |

---

## 四、API端点清单

| 序号 | 路由 | 方法 | 说明 |
|------|------|------|------|
| 1 | `/api/v1/sales/contracts/{id}/create-project` | POST | 从合同创建项目（已存在，需增强） |
| 2 | `/api/v1/acceptance/orders/{id}/complete` | POST | 完成验收单（已存在，需增强） |
| 3 | `/api/v1/bom/headers/{id}/approve` | POST | 审核BOM并创建采购订单（已存在，需增强） |
| 4 | `/api/v1/projects/{id}/risk-level` | GET | 查询项目风险等级（新增） |
| 5 | `/api/v1/projects/{id}/risk-history` | GET | 查询项目风险历史（新增） |

---

## 五、测试清单

### 5.1 单元测试

- [ ] ContractService.create_project_from_contract() 单元测试
- [ ] AcceptanceService.complete_acceptance_order() 单元测试
- [ ] BOMService.approve_bom_and_create_purchase_orders() 单元测试
- [ ] ProjectRiskService.auto_upgrade_risk_level() 单元测试

### 5.2 集成测试

- [ ] 合同→项目→里程碑→收款流程集成测试
- [ ] 验收→开票流程集成测试
- [ ] BOM→采购订单流程集成测试
- [ ] 里程碑延期→风险升级流程集成测试

### 5.3 API测试

- [ ] POST /sales/contracts/{id}/create-project API测试
- [ ] POST /acceptance/orders/{id}/complete API测试
- [ ] POST /bom/headers/{id}/approve API测试
- [ ] GET /projects/{id}/risk-level API测试

---

## 六、实施计划

### 6.1 Phase 1.1: 合同→项目自动生成完善

**预计工作量**: 2天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 数据库迁移 | 0.5天 | 后端开发 |
| 业务逻辑实现 | 1天 | 后端开发 |
| API端点开发 | 0.5天 | 后端开发 |
| 单元测试 | 0.5天 | 测试开发 |
| 集成测试 | 0.5天 | 测试开发 |

### 6.2 Phase 1.2: 验收→开票自动触发

**预计工作量**: 2天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 数据库迁移 | 0.5天 | 后端开发 |
| 业务逻辑实现 | 1天 | 后端开发 |
| 事件触发器开发 | 0.5天 | 后端开发 |
| 单元测试 | 0.5天 | 测试开发 |
| 集成测试 | 0.5天 | 测试开发 |

### 6.3 Phase 1.3: BOM→采购自动触发

**预计工作量**: 3天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 数据库迁移 | 0.5天 | 后端开发 |
| 业务逻辑实现 | 1.5天 | 后端开发 |
| 采购订单自动创建 | 1天 | 后端开发 |
| 单元测试 | 0.5天 | 测试开发 |
| 集成测试 | 0.5天 | 测试开发 |

### 6.4 Phase 1.4: 进度→预警自动升级

**预计工作量**: 2天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 数据库迁移 | 0.5天 | 后端开发 |
| 风险等级计算逻辑 | 1天 | 后端开发 |
| 定时任务开发 | 0.5天 | 后端开发 |
| 单元测试 | 0.5天 | 测试开发 |
| 集成测试 | 0.5天 | 测试开发 |

**总工作量**: 约9天

---

## 七、风险评估

### 7.1 技术风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 数据迁移失败 | 无法上线 | 准备回滚脚本，分批次迁移 |
| 业务逻辑复杂度高 | 开发延期 | 充分设计，分步实现，充分测试 |
| 性能问题 | 系统响应慢 | 异步处理，数据库优化 |

### 7.2 业务风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 用户不适应 | 功能使用率低 | 充分培训，分阶段上线 |
| 数据准确性风险 | 决策错误 | 数据校验规则，异常检测机制 |

---

## 八、成功指标

| 指标 | 当前值 | 目标值 | 提升 |
|------|--------|--------|------|
| 合同到项目创建时间 | 1天 | 0.5天 | 50% |
| 验收到开票时间 | 3天 | 1天 | 67% |
| BOM到采购订单时间 | 2天 | 0.5天 | 75% |
| ECN到进度调整时间 | 1天 | 0.1天 | 90% |
| 流程自动化率 | 60% | 85% | 25% |

---

## 九、总结

### 9.1 核心目标

修复4个关键流程断点，提升系统流程自动化程度：

1. ✅ **合同→项目**：付款节点与里程碑自动绑定
2. ✅ **验收→开票**：自动创建发票
3. ✅ **BOM→采购**：自动生成采购订单
4. ✅ **进度→预警**：自动升级风险等级

### 9.2 预期效果

- 📈 **效率提升**: 流程耗时减少50%以上
- 🎯 **准确性提升**: 数据一致性达到100%
- 🤖 **自动化提升**: 流程自动化率达到85%以上
- 🔔 **响应及时**: 风险自动通知管理层

### 9.3 后续优化

- Phase 2: 流程自动化增强（ECN成本影响同步、缺料预警自动采购）
- Phase 3: 流程智能化与优化（智能推荐、异常检测）

---

**文档版本**: v1.0
**创建日期**: 2026-01-25
**最后更新**: 2026-01-25
**负责人**: PMO技术团队
