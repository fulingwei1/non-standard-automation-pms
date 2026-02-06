#!/usr/bin/env python3
"""Upgrade local DB schema for project approval."""

from __future__ import annotations

import logging
import os
from typing import Iterable

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalNodeDefinition,
    ApprovalTemplate,
)
from app.models.base import get_engine


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("upgrade_project_approval_schema")


REQUIRED_PROJECT_COLUMNS: Iterable[tuple[str, str]] = (
    ("template_id", "INTEGER"),
    ("template_version_id", "INTEGER"),
)

REQUIRED_INSTANCE_COLUMNS: Iterable[tuple[str, str]] = (
    ("initiator_name", "VARCHAR(100)"),
)

PROJECT_TEMPLATE_CODE = "PROJECT_TEMPLATE"


def ensure_column(engine, table: str, column: str, ddl: str) -> None:
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns(table)}
    if column in columns:
        logger.info("✓ %s.%s already exists", table, column)
        return

    logger.info("→ Adding column %s.%s", table, column)
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
    logger.info("  Added column %s.%s", table, column)


def ensure_schema(engine) -> None:
    for column, ddl in REQUIRED_PROJECT_COLUMNS:
        ensure_column(engine, "projects", column, ddl)

    for column, ddl in REQUIRED_INSTANCE_COLUMNS:
        ensure_column(engine, "approval_instances", column, ddl)


def ensure_template(session) -> None:
    template = (
        session.query(ApprovalTemplate)
        .filter(ApprovalTemplate.template_code == PROJECT_TEMPLATE_CODE)
        .first()
    )
    if template:
        logger.info("✓ Approval template %s already exists", PROJECT_TEMPLATE_CODE)
        return

    logger.info("→ Creating default PROJECT_TEMPLATE")
    template = ApprovalTemplate(
        template_code=PROJECT_TEMPLATE_CODE,
        template_name="项目审批模板",
        category="PROJECT",
        description="默认项目审批流程",
        entity_type="PROJECT",
        is_active=True,
        is_published=True,
    )
    session.add(template)
    session.flush()

    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name="项目审批默认流程",
        description="项目经理审批",
        is_default=True,
        is_active=True,
    )
    session.add(flow)
    session.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code="PM_APPROVAL",
        node_name="项目经理审批",
        node_order=1,
        node_type="APPROVAL",
        approval_mode="SINGLE",
        approver_type="FORM_FIELD",
        approver_config={"field_name": "pm_id"},
    )
    session.add(node)
    session.commit()
    logger.info("  Created default template, flow and node")


def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        logger.info("Using DATABASE_URL=%s", database_url)
    engine = get_engine()

    try:
        ensure_schema(engine)
    except OperationalError as exc:
        logger.error("Failed to update schema: %s", exc)
        return

    Session = sessionmaker(bind=engine)
    with Session() as session:
        try:
            ensure_template(session)
        except OperationalError as exc:
            session.rollback()
            logger.error("Failed to seed template: %s", exc)
            return

    logger.info("Done. You can now re-run the project approval tests.")


if __name__ == "__main__":
    main()
