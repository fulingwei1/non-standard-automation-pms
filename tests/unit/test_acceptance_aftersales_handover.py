# -*- coding: utf-8 -*-
"""PROJ-23 契约：SAT 验收通过必须自动移交售后。

1. 移交动作：创建 ACTIVE 质保记录（质保期 = 项目质保月数，缺省 12 个月）、
   回填项目质保起止日期（只补空）、回填机台质保信息与客户归属（只补空）。
2. 幂等：已有 ACTIVE 质保不重复建档。
3. complete_acceptance_order 的 SAT 分支必须接线移交钩子。
"""
import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.after_sales import AfterSalesWarranty
from app.models.base import Base
from app.models.project import Customer, Machine, Project


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _seed(db: AsyncSession, warranty_months=None):
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="移交客户",
        customer_level="A",
        status="ACTIVE",
    )
    db.add(customer)
    await db.flush()
    project = Project(
        project_code=_unique("PJ"),
        project_name="移交项目",
        stage="S9",
        status="ST30",
        health="H1",
        customer_id=customer.id,
        warranty_period_months=warranty_months,
    )
    db.add(project)
    await db.flush()
    machine = Machine(
        project_id=project.id,
        machine_code=_unique("M"),
        machine_name="移交机台",
    )
    db.add(machine)
    await db.commit()
    return customer, project, machine


@pytest.mark.asyncio
async def test_handover_creates_warranty_and_backfills(async_db):
    from app.services.acceptance.acceptance_service import AcceptanceService

    customer, project, machine = await _seed(async_db, warranty_months=24)

    warranty = await AcceptanceService._handover_to_after_sales(async_db, project.id, completed_by=1)

    assert warranty is not None, "SAT 验收通过未创建质保记录"
    assert warranty.status == "ACTIVE"
    assert warranty.customer_id == customer.id
    assert warranty.warranty_months == 24
    assert warranty.warranty_start == date.today()

    refreshed_project = await async_db.get(Project, project.id)
    assert refreshed_project.warranty_start_date == date.today(), "项目质保开始日期未回填"
    assert refreshed_project.warranty_end_date is not None

    refreshed_machine = await async_db.get(Machine, machine.id)
    assert refreshed_machine.warranty, "机台质保信息未回填"
    assert refreshed_machine.customer_id == customer.id, "机台客户归属未回填"


@pytest.mark.asyncio
async def test_handover_is_idempotent(async_db):
    from app.services.acceptance.acceptance_service import AcceptanceService
    from sqlalchemy import func, select

    _, project, _ = await _seed(async_db)

    await AcceptanceService._handover_to_after_sales(async_db, project.id, completed_by=1)
    await AcceptanceService._handover_to_after_sales(async_db, project.id, completed_by=1)

    count = (
        await async_db.execute(
            select(func.count(AfterSalesWarranty.id)).where(
                AfterSalesWarranty.project_id == project.id
            )
        )
    ).scalar()
    assert count == 1, "移交必须幂等，不得重复建质保档"


@pytest.mark.asyncio
async def test_handover_defaults_to_12_months(async_db):
    from app.services.acceptance.acceptance_service import AcceptanceService

    _, project, _ = await _seed(async_db, warranty_months=None)

    warranty = await AcceptanceService._handover_to_after_sales(async_db, project.id, completed_by=1)
    assert warranty.warranty_months == 12


def test_sat_completion_wires_handover():
    import inspect

    from app.services.acceptance.acceptance_service import AcceptanceService

    src = inspect.getsource(AcceptanceService.complete_acceptance_order)
    assert "_handover_to_after_sales" in src, "SAT 验收完成未接线售后移交钩子"
