# -*- coding: utf-8 -*-
"""
数据库基础配置和基类模型
"""

import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    event,
    inspect,
    text,
)

FK = ForeignKey  # 别名，简化代码
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

# 创建基类
Base = declarative_base()

# 全局引擎和会话工厂
_engine = None
_SessionLocal = None

logger = logging.getLogger(__name__)


WAREHOUSE_CORE_TABLE_DDLS = (
    """
    CREATE TABLE IF NOT EXISTS warehouses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_code VARCHAR(50) NOT NULL UNIQUE,
        warehouse_name VARCHAR(200) NOT NULL,
        warehouse_type VARCHAR(50) DEFAULT 'NORMAL',
        address VARCHAR(500),
        manager VARCHAR(100),
        contact_phone VARCHAR(50),
        capacity NUMERIC(12, 2),
        description TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME,
        updated_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS warehouse_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id INTEGER NOT NULL,
        location_code VARCHAR(50) NOT NULL,
        location_name VARCHAR(200),
        zone VARCHAR(50),
        aisle VARCHAR(20),
        shelf VARCHAR(20),
        level VARCHAR(20),
        position VARCHAR(20),
        capacity NUMERIC(12, 2),
        location_type VARCHAR(50) DEFAULT 'STORAGE',
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inbound_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no VARCHAR(50) NOT NULL UNIQUE,
        order_type VARCHAR(50) DEFAULT 'PURCHASE',
        warehouse_id INTEGER,
        source_no VARCHAR(50),
        supplier_name VARCHAR(200),
        status VARCHAR(20) DEFAULT 'DRAFT',
        planned_date DATE,
        actual_date DATE,
        operator VARCHAR(100),
        remark TEXT,
        total_quantity NUMERIC(12, 2) DEFAULT 0,
        received_quantity NUMERIC(12, 2) DEFAULT 0,
        created_by INTEGER,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inbound_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        material_code VARCHAR(50) NOT NULL,
        material_name VARCHAR(200),
        specification VARCHAR(500),
        unit VARCHAR(20) DEFAULT '件',
        planned_quantity NUMERIC(12, 2) NOT NULL,
        received_quantity NUMERIC(12, 2) DEFAULT 0,
        location_id INTEGER,
        remark TEXT,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(order_id) REFERENCES inbound_orders(id),
        FOREIGN KEY(location_id) REFERENCES warehouse_locations(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS outbound_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_no VARCHAR(50) NOT NULL UNIQUE,
        order_type VARCHAR(50) DEFAULT 'PRODUCTION',
        warehouse_id INTEGER,
        target_no VARCHAR(50),
        department VARCHAR(200),
        status VARCHAR(20) DEFAULT 'DRAFT',
        planned_date DATE,
        actual_date DATE,
        operator VARCHAR(100),
        remark TEXT,
        total_quantity NUMERIC(12, 2) DEFAULT 0,
        picked_quantity NUMERIC(12, 2) DEFAULT 0,
        created_by INTEGER,
        is_urgent BOOLEAN DEFAULT 0,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS outbound_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        material_code VARCHAR(50) NOT NULL,
        material_name VARCHAR(200),
        specification VARCHAR(500),
        unit VARCHAR(20) DEFAULT '件',
        planned_quantity NUMERIC(12, 2) NOT NULL,
        picked_quantity NUMERIC(12, 2) DEFAULT 0,
        location_id INTEGER,
        remark TEXT,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(order_id) REFERENCES outbound_orders(id),
        FOREIGN KEY(location_id) REFERENCES warehouse_locations(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id INTEGER NOT NULL,
        location_id INTEGER,
        material_code VARCHAR(50) NOT NULL,
        material_name VARCHAR(200),
        specification VARCHAR(500),
        unit VARCHAR(20) DEFAULT '件',
        quantity NUMERIC(12, 2) DEFAULT 0,
        reserved_quantity NUMERIC(12, 2) DEFAULT 0,
        available_quantity NUMERIC(12, 2) DEFAULT 0,
        min_stock NUMERIC(12, 2) DEFAULT 0,
        max_stock NUMERIC(12, 2) DEFAULT 0,
        batch_no VARCHAR(100),
        last_inbound_date DATETIME,
        last_outbound_date DATETIME,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(warehouse_id) REFERENCES warehouses(id),
        FOREIGN KEY(location_id) REFERENCES warehouse_locations(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_count_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        count_no VARCHAR(50) NOT NULL UNIQUE,
        warehouse_id INTEGER,
        count_type VARCHAR(50) DEFAULT 'FULL',
        status VARCHAR(20) DEFAULT 'DRAFT',
        planned_date DATE,
        actual_date DATE,
        operator VARCHAR(100),
        remark TEXT,
        total_items INTEGER DEFAULT 0,
        matched_items INTEGER DEFAULT 0,
        diff_items INTEGER DEFAULT 0,
        created_by INTEGER,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(warehouse_id) REFERENCES warehouses(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS stock_count_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        material_code VARCHAR(50) NOT NULL,
        material_name VARCHAR(200),
        location_id INTEGER,
        system_quantity NUMERIC(12, 2) DEFAULT 0,
        actual_quantity NUMERIC(12, 2),
        diff_quantity NUMERIC(12, 2),
        diff_reason TEXT,
        created_at DATETIME,
        updated_at DATETIME,
        FOREIGN KEY(order_id) REFERENCES stock_count_orders(id),
        FOREIGN KEY(location_id) REFERENCES warehouse_locations(id)
    )
    """,
)

WAREHOUSE_CORE_INDEX_DDLS = (
    "CREATE UNIQUE INDEX IF NOT EXISTS ix_warehouse_location_code "
    "ON warehouse_locations(warehouse_id, location_code)",
    "CREATE INDEX IF NOT EXISTS ix_inventory_material "
    "ON inventory(warehouse_id, material_code, batch_no)",
)


def _ensure_sqlite_warehouse_tables(engine, tables: list[str]) -> list[str]:
    """补建仓储模块在旧 SQLite 库中缺失的核心表。"""
    required_tables = {
        "warehouses",
        "warehouse_locations",
        "inbound_orders",
        "inbound_order_items",
        "outbound_orders",
        "outbound_order_items",
        "inventory",
        "stock_count_orders",
        "stock_count_items",
    }
    if required_tables.issubset(set(tables)):
        return tables

    with engine.begin() as conn:
        for ddl in WAREHOUSE_CORE_TABLE_DDLS:
            try:
                conn.execute(text(ddl))
            except Exception:
                logger.debug("warehouse 核心表补丁跳过", exc_info=True)
        for ddl in WAREHOUSE_CORE_INDEX_DDLS:
            try:
                conn.execute(text(ddl))
            except Exception:
                logger.debug("warehouse 核心索引补丁跳过", exc_info=True)

    return inspect(engine).get_table_names()


class RuntimePatchedSession(Session):
    """
    自定义 Session，确保 SQLite 关键补丁在运行期也会被应用。

    某些测试/开发环境可能复用历史数据库文件，缺少最新字段（例如
    api_permissions.group_id）。当使用 SessionLocal() 直接创建会话时，
    我们在第一次初始化时检查并补齐缺失列，避免 API 请求报错。
    """

    _sqlite_patches_applied = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ensure_runtime_patches()

    def _ensure_runtime_patches(self):
        if RuntimePatchedSession._sqlite_patches_applied:
            return

        bind = self.bind
        if bind is None:
            try:
                bind = self.get_bind()
            except Exception:
                bind = None

        if bind is None or bind.dialect.name != "sqlite":
            logger.debug(
                "Runtime SQLite patch skipped: bind=%s, dialect=%s",
                bind,
                getattr(bind, "dialect", None),
            )
            RuntimePatchedSession._sqlite_patches_applied = True
            return

        logger.debug("Runtime SQLite patch using database URL: %s", bind.url)

        inspector = inspect(bind)
        tables = inspector.get_table_names()
        logger.debug("Runtime SQLite patch inspecting tables: %s", tables[:5])
        if "api_permissions" not in tables:
            # 表尚未创建，等下次会话再检查
            return

        columns = {col["name"] for col in inspector.get_columns("api_permissions")}
        logger.debug("Runtime SQLite patch api_permissions columns: %s", columns)
        if "group_id" not in columns:
            logger.warning(
                "Detected legacy SQLite schema missing api_permissions.group_id; applying runtime patch."
            )
            with bind.begin() as conn:
                conn.execute(
                    text("ALTER TABLE api_permissions ADD COLUMN group_id INTEGER")
                )

        if "role_templates" in tables:
            role_template_columns = {
                col["name"] for col in inspector.get_columns("role_templates")
            }
            role_template_ddls = []
            if "version" not in role_template_columns:
                role_template_ddls.append(
                    "ALTER TABLE role_templates ADD COLUMN version INTEGER DEFAULT 1"
                )
            if "version_note" not in role_template_columns:
                role_template_ddls.append(
                    "ALTER TABLE role_templates ADD COLUMN version_note VARCHAR(200)"
                )
            if "source_role_id" not in role_template_columns:
                role_template_ddls.append(
                    "ALTER TABLE role_templates ADD COLUMN source_role_id INTEGER"
                )
            if "source_role_name" not in role_template_columns:
                role_template_ddls.append(
                    "ALTER TABLE role_templates ADD COLUMN source_role_name VARCHAR(100)"
                )
            if "tenant_id" not in role_template_columns:
                role_template_ddls.append(
                    "ALTER TABLE role_templates ADD COLUMN tenant_id INTEGER"
                )
            if role_template_ddls:
                logger.warning(
                    "Detected legacy SQLite schema missing role_templates version/source/tenant columns; applying runtime patch."
                )
                with bind.begin() as conn:
                    for ddl in role_template_ddls:
                        conn.execute(text(ddl))

        RuntimePatchedSession._sqlite_patches_applied = True


def _ensure_sqlite_schema(engine):
    """
    通过轻量的DDL补丁，确保SQLite数据库包含关键字段。
    避免由于历史数据库版本导致的列缺失。
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    tables = _ensure_sqlite_warehouse_tables(engine, tables)
    inspector = inspect(engine)

    project_delivery_tables = [
        "project_delivery_schedules",
        "project_delivery_tasks",
        "project_delivery_long_cycle_purchases",
        "project_delivery_mechanical_designs",
        "project_delivery_change_logs",
        "project_delivery_dependencies",
    ]
    missing_project_delivery_tables = [
        table_name for table_name in project_delivery_tables if table_name not in tables
    ]
    if missing_project_delivery_tables:
        try:
            import importlib

            importlib.import_module("app.models.project_delivery")
            metadata_tables = [
                Base.metadata.tables[table_name]
                for table_name in missing_project_delivery_tables
                if table_name in Base.metadata.tables
            ]
            if metadata_tables:
                Base.metadata.create_all(bind=engine, tables=metadata_tables)
                inspector = inspect(engine)
                tables = inspector.get_table_names()
        except Exception:
            logger.debug("project_delivery 表补丁跳过", exc_info=True)

    optional_model_modules = [
        "app.models.project",
        "app.models.user",
        "app.models.ecn.material_impact",
        "app.models.ecn.cost_record",
        "app.models.project_template_config",
        "app.models.project_requirements",
    ]
    optional_tables = [
        "ecn_material_dispositions",
        "ecn_execution_progress",
        "ecn_stakeholders",
        "ecn_cost_records",
        "project_template_configs",
        "stage_configs",
        "node_configs",
        "project_requirements",
        "engineer_recommendations",
    ]
    missing_optional_tables = [
        table_name for table_name in optional_tables if table_name not in tables
    ]
    if missing_optional_tables:
        try:
            import importlib

            for module_name in optional_model_modules:
                importlib.import_module(module_name)
            metadata_tables = [
                Base.metadata.tables[table_name]
                for table_name in missing_optional_tables
                if table_name in Base.metadata.tables
            ]
            if metadata_tables:
                Base.metadata.create_all(bind=engine, tables=metadata_tables)
                inspector = inspect(engine)
                tables = inspector.get_table_names()
        except Exception:
            logger.debug("ECN/模板配置历史表补丁跳过", exc_info=True)

    # OTD 智能体阈值配置表 + 风险快照表 + 毛利率快照表（新增表，对历史 DB 补建）
    otd_tables = [
        "otd_threshold_configs",
        "otd_risk_snapshots",
        "project_margin_snapshots",
    ]
    missing_otd_tables = [
        table_name for table_name in otd_tables if table_name not in tables
    ]
    if missing_otd_tables:
        try:
            import importlib

            importlib.import_module("app.models.otd_threshold_config")
            importlib.import_module("app.models.otd_risk_snapshot")
            importlib.import_module("app.models.project_margin_snapshot")
            metadata_tables = [
                Base.metadata.tables[table_name]
                for table_name in missing_otd_tables
                if table_name in Base.metadata.tables
            ]
            if metadata_tables:
                Base.metadata.create_all(bind=engine, tables=metadata_tables)
                inspector = inspect(engine)
                tables = inspector.get_table_names()
        except Exception:
            logger.debug("OTD 阈值配置/风险快照/毛利率快照表补丁跳过", exc_info=True)

    # Many models use TimestampMixin (created_at/updated_at). Historical SQLite
    # databases or hand-written migration scripts may omit these columns for
    # some tables, which can cause runtime 500s when ORM queries select/order
    # by them. SQLite 不支持在 ALTER TABLE ADD COLUMN 时使用
    # DEFAULT CURRENT_TIMESTAMP，所以这里只补可查询/可写入的裸 DATETIME 列；
    # 后续 ORM 插入会由 Python 侧默认值写入时间。
    for table_name in tables:
        columns = None
        try:
            columns = {col["name"] for col in inspector.get_columns(table_name)}
        except Exception:
            logger.debug("无法读取 SQLite 表字段信息，已跳过", exc_info=True)
        if columns is None:
            continue

        statements = []
        if "created_at" not in columns:
            statements.append(
                f"ALTER TABLE {table_name} ADD COLUMN created_at DATETIME"
            )
        if "updated_at" not in columns:
            statements.append(
                f"ALTER TABLE {table_name} ADD COLUMN updated_at DATETIME"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        # Best-effort patching; some tables/views may not be alterable.
                        logger.debug("SQLite DDL 补丁执行失败，已忽略", exc_info=True)

    if "project_statuses" in tables:
        try:
            columns = [col["name"] for col in inspector.get_columns("project_statuses")]
            if "updated_at" not in columns:
                with engine.begin() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE project_statuses ADD COLUMN updated_at DATETIME"
                        )
                    )
        except Exception:
            # Column already exists or table cannot be altered
            logger.debug("project_statuses 列补丁跳过", exc_info=True)
    if "task_unified" in tables:
        columns = [col["name"] for col in inspector.get_columns("task_unified")]
        if "is_active" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE task_unified "
                        "ADD COLUMN is_active BOOLEAN DEFAULT 1"
                    )
                )

    if "project_costs" in tables:
        try:
            columns = [col["name"] for col in inspector.get_columns("project_costs")]
            with engine.begin() as conn:
                if "cost_basis" not in columns:
                    conn.execute(
                        text(
                            "ALTER TABLE project_costs "
                            "ADD COLUMN cost_basis VARCHAR(20) DEFAULT 'ACTUAL'"
                        )
                    )
                conn.execute(
                    text(
                        """
                        UPDATE project_costs
                        SET cost_basis = 'PLAN'
                        WHERE UPPER(COALESCE(source_type, '')) = 'BOM_COST'
                           OR UPPER(COALESCE(source_module, '')) = 'BOM'
                        """
                    )
                )
        except Exception:
            logger.debug("project_costs 成本口径列补丁跳过", exc_info=True)

    if "api_permissions" in tables:
        columns = {col["name"] for col in inspector.get_columns("api_permissions")}
        if "group_id" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE api_permissions ADD COLUMN group_id INTEGER")
                )

    if "role_templates" in tables:
        columns = {col["name"] for col in inspector.get_columns("role_templates")}
        statements = []
        if "version" not in columns:
            statements.append(
                "ALTER TABLE role_templates ADD COLUMN version INTEGER DEFAULT 1"
            )
        if "version_note" not in columns:
            statements.append(
                "ALTER TABLE role_templates ADD COLUMN version_note VARCHAR(200)"
            )
        if "source_role_id" not in columns:
            statements.append(
                "ALTER TABLE role_templates ADD COLUMN source_role_id INTEGER"
            )
        if "source_role_name" not in columns:
            statements.append(
                "ALTER TABLE role_templates ADD COLUMN source_role_name VARCHAR(100)"
            )
        if "tenant_id" not in columns:
            statements.append("ALTER TABLE role_templates ADD COLUMN tenant_id INTEGER")

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug(
                            "role_templates 版本/租户字段补丁跳过", exc_info=True
                        )

    if "project_reviews" in tables:
        columns = {col["name"] for col in inspector.get_columns("project_reviews")}
        statements = []
        if "ai_generated_at" not in columns:
            statements.append(
                "ALTER TABLE project_reviews ADD COLUMN ai_generated_at DATETIME"
            )
        if "ai_summary" not in columns:
            statements.append("ALTER TABLE project_reviews ADD COLUMN ai_summary TEXT")
        if "ai_insights" not in columns:
            statements.append("ALTER TABLE project_reviews ADD COLUMN ai_insights JSON")
        if "ai_metadata" not in columns:
            statements.append("ALTER TABLE project_reviews ADD COLUMN ai_metadata JSON")
        if "quality_score" not in columns:
            statements.append(
                "ALTER TABLE project_reviews ADD COLUMN quality_score NUMERIC(5, 2)"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug("project_reviews AI 字段补丁跳过", exc_info=True)

    if "project_lessons" in tables:
        columns = {col["name"] for col in inspector.get_columns("project_lessons")}
        statements = []
        if "ai_extracted" not in columns:
            statements.append(
                "ALTER TABLE project_lessons ADD COLUMN ai_extracted BOOLEAN DEFAULT 0"
            )
        if "ai_confidence" not in columns:
            statements.append(
                "ALTER TABLE project_lessons ADD COLUMN ai_confidence NUMERIC(5, 4)"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug("project_lessons AI 字段补丁跳过", exc_info=True)

    if "alert_rules" in tables:
        columns = {col["name"] for col in inspector.get_columns("alert_rules")}
        statements = []
        if "enforcement_mode" not in columns:
            statements.append(
                "ALTER TABLE alert_rules "
                "ADD COLUMN enforcement_mode VARCHAR(20) DEFAULT 'WARN'"
            )
        if "is_active" not in columns:
            statements.append(
                "ALTER TABLE alert_rules ADD COLUMN is_active BOOLEAN DEFAULT 1"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug("alert_rules 列补丁跳过", exc_info=True)

    if "users" in tables:
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "department_id" not in columns:
            with engine.begin() as conn:
                try:
                    conn.execute(
                        text("ALTER TABLE users ADD COLUMN department_id INTEGER")
                    )
                except Exception:
                    logger.debug("users.department_id 列补丁跳过", exc_info=True)

    if "projects" in tables:
        columns = {col["name"] for col in inspector.get_columns("projects")}
        statements = []
        if "kitting_rate" not in columns:
            statements.append(
                "ALTER TABLE projects ADD COLUMN kitting_rate NUMERIC(5, 1) DEFAULT 0"
            )
        if "material_status" not in columns:
            statements.append(
                "ALTER TABLE projects ADD COLUMN material_status VARCHAR(20) DEFAULT '待采购'"
            )
        if "shortage_items_count" not in columns:
            statements.append(
                "ALTER TABLE projects ADD COLUMN shortage_items_count INTEGER DEFAULT 0"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug("projects 物料字段补丁跳过", exc_info=True)

    if "annual_key_works" in tables:
        columns = {col["name"] for col in inspector.get_columns("annual_key_works")}
        if "progress_description" not in columns:
            with engine.begin() as conn:
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE annual_key_works ADD COLUMN progress_description TEXT"
                        )
                    )
                except Exception:
                    logger.debug(
                        "annual_key_works.progress_description 列补丁跳过",
                        exc_info=True,
                    )

    if "annual_key_work_project_links" in tables:
        columns = {
            col["name"]
            for col in inspector.get_columns("annual_key_work_project_links")
        }
        if "is_active" not in columns:
            with engine.begin() as conn:
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE annual_key_work_project_links "
                            "ADD COLUMN is_active BOOLEAN DEFAULT 1"
                        )
                    )
                except Exception:
                    logger.debug(
                        "annual_key_work_project_links.is_active 列补丁跳过",
                        exc_info=True,
                    )

    if "bom_items" in tables:
        columns = {col["name"] for col in inspector.get_columns("bom_items")}
        statements = []
        if "parent_item_id" not in columns:
            statements.append("ALTER TABLE bom_items ADD COLUMN parent_item_id INTEGER")
        if "material_id" not in columns:
            statements.append("ALTER TABLE bom_items ADD COLUMN material_id INTEGER")
        if "specification" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN specification VARCHAR(500)"
            )
        if "drawing_no" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN drawing_no VARCHAR(100)"
            )
        if "unit" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN unit VARCHAR(20) DEFAULT '件'"
            )
        if "unit_price" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN unit_price NUMERIC(12, 4) DEFAULT 0"
            )
        if "amount" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN amount NUMERIC(14, 2) DEFAULT 0"
            )
        if "source_type" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN source_type VARCHAR(20) DEFAULT 'PURCHASE'"
            )
        if "supplier_id" not in columns:
            statements.append("ALTER TABLE bom_items ADD COLUMN supplier_id INTEGER")
        if "required_date" not in columns:
            statements.append("ALTER TABLE bom_items ADD COLUMN required_date DATE")
        if "purchased_qty" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN purchased_qty NUMERIC(10, 4) DEFAULT 0"
            )
        if "received_qty" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN received_qty NUMERIC(10, 4) DEFAULT 0"
            )
        if "kitting_status" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN kitting_status VARCHAR(20) DEFAULT 'PENDING'"
            )
        if "expected_arrival_date" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN expected_arrival_date DATE"
            )
        if "actual_arrival_date" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN actual_arrival_date DATE"
            )
        if "level" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN level INTEGER DEFAULT 1"
            )
        if "sort_order" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN sort_order INTEGER DEFAULT 0"
            )
        if "is_key_item" not in columns:
            statements.append(
                "ALTER TABLE bom_items ADD COLUMN is_key_item BOOLEAN DEFAULT 0"
            )
        if "remark" not in columns:
            statements.append("ALTER TABLE bom_items ADD COLUMN remark TEXT")

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug("bom_items 兼容字段补丁跳过", exc_info=True)

    if "stage_templates" in tables:
        columns = {col["name"] for col in inspector.get_columns("stage_templates")}
        statements = []
        if "updated_by" not in columns:
            statements.append(
                "ALTER TABLE stage_templates ADD COLUMN updated_by INTEGER"
            )
        if "change_description" not in columns:
            statements.append(
                "ALTER TABLE stage_templates ADD COLUMN change_description TEXT"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug("stage_templates 列补丁跳过", exc_info=True)

    if "quotes" in tables:
        columns = {col["name"] for col in inspector.get_columns("quotes")}
        if "delivery_date" not in columns:
            with engine.begin() as conn:
                try:
                    conn.execute(
                        text("ALTER TABLE quotes ADD COLUMN delivery_date DATE")
                    )
                except Exception:
                    logger.debug("quotes.delivery_date 列补丁跳过", exc_info=True)

    if "quote_versions" in tables:
        columns = {col["name"] for col in inspector.get_columns("quote_versions")}
        statements = []
        if "presale_solution_id" not in columns:
            statements.append(
                "ALTER TABLE quote_versions ADD COLUMN presale_solution_id INTEGER"
            )
        if "presale_ticket_id" not in columns:
            statements.append(
                "ALTER TABLE quote_versions ADD COLUMN presale_ticket_id INTEGER"
            )

        with engine.begin() as conn:
            for ddl in statements:
                try:
                    conn.execute(text(ddl))
                except Exception:
                    logger.debug("quote_versions 售前上下文字段补丁跳过", exc_info=True)
            for ddl in (
                "CREATE INDEX IF NOT EXISTS idx_qv_presale_solution "
                "ON quote_versions(presale_solution_id)",
                "CREATE INDEX IF NOT EXISTS idx_qv_presale_ticket "
                "ON quote_versions(presale_ticket_id)",
            ):
                try:
                    conn.execute(text(ddl))
                except Exception:
                    logger.debug("quote_versions 售前上下文索引补丁跳过", exc_info=True)

    if "technical_assessments" in tables:
        columns = {
            col["name"] for col in inspector.get_columns("technical_assessments")
        }
        statements = []
        if "presale_ticket_id" not in columns:
            statements.append(
                "ALTER TABLE technical_assessments ADD COLUMN presale_ticket_id INTEGER"
            )
        if "template_id" not in columns:
            statements.append(
                "ALTER TABLE technical_assessments ADD COLUMN template_id INTEGER"
            )
        if "version_no" not in columns:
            statements.append(
                "ALTER TABLE technical_assessments ADD COLUMN version_no VARCHAR(20) DEFAULT 'V1.0'"
            )
        if "is_latest" not in columns:
            statements.append(
                "ALTER TABLE technical_assessments ADD COLUMN is_latest BOOLEAN DEFAULT 1"
            )
        if "previous_version_id" not in columns:
            statements.append(
                "ALTER TABLE technical_assessments ADD COLUMN previous_version_id INTEGER"
            )
        if "item_scores" not in columns:
            statements.append(
                "ALTER TABLE technical_assessments ADD COLUMN item_scores TEXT"
            )
        if "auto_generated" not in columns:
            statements.append(
                "ALTER TABLE technical_assessments ADD COLUMN auto_generated BOOLEAN DEFAULT 0"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug("technical_assessments 列补丁跳过", exc_info=True)

        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_assessment_ticket ON technical_assessments(presale_ticket_id)",
            "CREATE INDEX IF NOT EXISTS idx_assessment_template ON technical_assessments(template_id)",
            "CREATE INDEX IF NOT EXISTS idx_assessment_version ON technical_assessments(version_no)",
        ]
        with engine.begin() as conn:
            for ddl in index_statements:
                try:
                    conn.execute(text(ddl))
                except Exception:
                    logger.debug("technical_assessments 索引补丁跳过", exc_info=True)

    if "presale_tender_record" in tables:
        columns = {
            col["name"] for col in inspector.get_columns("presale_tender_record")
        }
        statements = []
        if "project_id" not in columns:
            statements.append(
                "ALTER TABLE presale_tender_record ADD COLUMN project_id INTEGER"
            )

        with engine.begin() as conn:
            for ddl in statements:
                try:
                    conn.execute(text(ddl))
                except Exception:
                    logger.debug(
                        "presale_tender_record 项目字段补丁跳过", exc_info=True
                    )
            try:
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_tender_project "
                        "ON presale_tender_record(project_id)"
                    )
                )
            except Exception:
                logger.debug("presale_tender_record 项目索引补丁跳过", exc_info=True)

    if "presale_ticket_deliverable" in tables:
        columns = {
            col["name"] for col in inspector.get_columns("presale_ticket_deliverable")
        }
        if "is_required" not in columns:
            with engine.begin() as conn:
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE presale_ticket_deliverable "
                            "ADD COLUMN is_required BOOLEAN DEFAULT 1"
                        )
                    )
                except Exception:
                    logger.debug(
                        "presale_ticket_deliverable 必交标记补丁跳过", exc_info=True
                    )

    if "presale_expenses" in tables:
        columns = {col["name"] for col in inspector.get_columns("presale_expenses")}
        statements = []
        if "ticket_id" not in columns:
            statements.append(
                "ALTER TABLE presale_expenses ADD COLUMN ticket_id INTEGER"
            )
        if "approval_status" not in columns:
            statements.append(
                "ALTER TABLE presale_expenses "
                "ADD COLUMN approval_status VARCHAR(20) DEFAULT 'PENDING'"
            )
        if "approved_by" not in columns:
            statements.append(
                "ALTER TABLE presale_expenses ADD COLUMN approved_by INTEGER"
            )
        if "approved_at" not in columns:
            statements.append(
                "ALTER TABLE presale_expenses ADD COLUMN approved_at DATETIME"
            )
        if "approval_note" not in columns:
            statements.append(
                "ALTER TABLE presale_expenses ADD COLUMN approval_note TEXT"
            )

        with engine.begin() as conn:
            for ddl in statements:
                try:
                    conn.execute(text(ddl))
                except Exception:
                    logger.debug("presale_expenses 审批字段补丁跳过", exc_info=True)
            for ddl in (
                "CREATE INDEX IF NOT EXISTS idx_presale_expense_ticket "
                "ON presale_expenses(ticket_id)",
                "CREATE INDEX IF NOT EXISTS idx_presale_expense_approval_status "
                "ON presale_expenses(approval_status)",
            ):
                try:
                    conn.execute(text(ddl))
                except Exception:
                    logger.debug("presale_expenses 索引补丁跳过", exc_info=True)

    if "presale_knowledge_case" in tables:
        case_columns = {
            col["name"] for col in inspector.get_columns("presale_knowledge_case")
        }
        case_statements = []
        if "source_project_id" not in case_columns:
            case_statements.append(
                "ALTER TABLE presale_knowledge_case ADD COLUMN source_project_id INTEGER"
            )

        if case_statements:
            with engine.begin() as conn:
                for ddl in case_statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug(
                            "presale_knowledge_case.source_project_id 列补丁跳过",
                            exc_info=True,
                        )
                try:
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_presale_case_source_project "
                            "ON presale_knowledge_case(source_project_id)"
                        )
                    )
                except Exception:
                    logger.debug("presale_knowledge_case 来源项目索引补丁跳过", exc_info=True)

    if "presale_agent_metrics" not in tables:
        # 表不存在则用 ORM metadata 建表（含索引）
        try:
            import importlib
            importlib.import_module("app.models.presale_agent_metric")
            metadata_tables = [
                Base.metadata.tables[name]
                for name in ("presale_agent_metrics",)
                if name in Base.metadata.tables
            ]
            if metadata_tables:
                Base.metadata.create_all(bind=engine, tables=metadata_tables)
                tables = inspect(engine).get_table_names()
        except Exception:
            logger.debug("presale_agent_metrics 建表补丁跳过", exc_info=True)

    if "presale_agent_revisions" not in tables:
        try:
            import importlib
            importlib.import_module("app.models.presale_agent_revision")
            metadata_tables = [
                Base.metadata.tables[name]
                for name in ("presale_agent_revisions",)
                if name in Base.metadata.tables
            ]
            if metadata_tables:
                Base.metadata.create_all(bind=engine, tables=metadata_tables)
                tables = inspect(engine).get_table_names()
        except Exception:
            logger.debug("presale_agent_revisions 建表补丁跳过", exc_info=True)

    if "ecn" in tables:
        columns = {col["name"] for col in inspector.get_columns("ecn")}
        statements = []
        if "applicant_name" not in columns:
            statements.append("ALTER TABLE ecn ADD COLUMN applicant_name VARCHAR(50)")
        if "approval_instance_id" not in columns:
            statements.append("ALTER TABLE ecn ADD COLUMN approval_instance_id INTEGER")
        if "approval_status" not in columns:
            statements.append("ALTER TABLE ecn ADD COLUMN approval_status VARCHAR(20)")
        if "approval_date" not in columns:
            statements.append("ALTER TABLE ecn ADD COLUMN approval_date DATETIME")
        if "final_approver_id" not in columns:
            statements.append("ALTER TABLE ecn ADD COLUMN final_approver_id INTEGER")
        if "impact_analysis" not in columns:
            statements.append("ALTER TABLE ecn ADD COLUMN impact_analysis TEXT")

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug("ecn 审批兼容列补丁跳过", exc_info=True)

    if "ecn_approval_matrix" in tables:
        columns = {col["name"] for col in inspector.get_columns("ecn_approval_matrix")}
        if "condition_type" in columns:
            with engine.begin() as conn:
                try:
                    conn.execute(
                        text(
                            "UPDATE ecn_approval_matrix "
                            "SET condition_type = 'ALWAYS' "
                            "WHERE condition_type IS NULL OR condition_type = ''"
                        )
                    )
                except Exception:
                    logger.debug("ecn_approval_matrix 条件类型回填跳过", exc_info=True)

    if "report_template" in tables:
        columns = {col["name"] for col in inspector.get_columns("report_template")}
        if "name" in columns and "template_name" in columns:
            with engine.begin() as conn:
                try:
                    conn.execute(
                        text(
                            "UPDATE report_template "
                            "SET name = template_name "
                            "WHERE (name IS NULL OR name = '') "
                            "AND template_name IS NOT NULL"
                        )
                    )
                except Exception:
                    logger.debug("report_template.name 数据回填跳过", exc_info=True)

    if "engineer_dimension_config" in tables:
        columns = {
            col["name"] for col in inspector.get_columns("engineer_dimension_config")
        }
        statements = []
        if "department_id" not in columns:
            statements.append(
                "ALTER TABLE engineer_dimension_config ADD COLUMN department_id INTEGER"
            )
        if "is_global" not in columns:
            statements.append(
                "ALTER TABLE engineer_dimension_config "
                "ADD COLUMN is_global BOOLEAN DEFAULT 1"
            )
        if "approval_status" not in columns:
            statements.append(
                "ALTER TABLE engineer_dimension_config "
                "ADD COLUMN approval_status VARCHAR(20) DEFAULT 'APPROVED'"
            )
        if "approval_reason" not in columns:
            statements.append(
                "ALTER TABLE engineer_dimension_config ADD COLUMN approval_reason TEXT"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        logger.debug(
                            "engineer_dimension_config 列补丁跳过", exc_info=True
                        )


class TimestampMixin:
    """时间戳混入类，提供创建时间和更新时间字段"""

    created_at = Column(
        DateTime, default=datetime.now, nullable=False, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        comment="更新时间",
    )


class FinancialAmountMixin:
    """
    财务金额混入类 - 消除金额字段重复

    用于：采购订单、外协订单、BOM表头、订单明细等涉及金额的表
    """

    total_amount = Column(Numeric(14, 2), default=0, comment="总金额")
    tax_rate = Column(Numeric(5, 2), default=13, comment="税率(%)")
    tax_amount = Column(Numeric(14, 2), default=0, comment="税额")
    amount_with_tax = Column(Numeric(14, 2), default=0, comment="含税金额")
    paid_amount = Column(Numeric(14, 2), default=0, comment="已付金额")


class ApprovalWorkflowMixin:
    """
    审批流程混入类 - 消除审批字段重复

    用于：采购订单、采购申请、BOM表头等需要审批的表
    """

    submitted_at = Column(DateTime, comment="提交时间")
    approved_by = Column(Integer, FK("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")
    approval_note = Column(Text, comment="审批意见")


class QualityInspectionMixin:
    """
    质检字段混入类 - 消除质检字段重复

    用于：收货单明细、外协交付明细、外协质检记录等
    """

    inspect_qty = Column(Numeric(10, 4), default=0, comment="送检数量")
    qualified_qty = Column(Numeric(10, 4), default=0, comment="合格数量")
    rejected_qty = Column(Numeric(10, 4), default=0, comment="不合格数量")
    inspect_result = Column(String(20), comment="质检结果")
    inspect_note = Column(Text, comment="质检说明")


class OrderItemMixin:
    """
    订单明细混入类 - 消除明细字段重复

    用于：采购订单明细、外协订单明细、BOM明细、采购申请明细
    """

    material_id = Column(Integer, FK("materials.id"), comment="物料ID")
    material_code = Column(String(50), comment="物料编码")
    material_name = Column(String(200), comment="物料名称")
    specification = Column(String(500), comment="规格型号")
    unit = Column(String(20), default="件", comment="单位")
    quantity = Column(Numeric(10, 4), comment="数量")
    unit_price = Column(Numeric(12, 4), default=0, comment="单价")
    amount = Column(Numeric(14, 2), default=0, comment="金额")


class VendorBaseMixin:
    """
    供应商/外协商基础混入类 - 消除供应商字段重复

    用于：suppliers, outsourcing_vendors（未来合并为vendors）
    """

    # 基本信息
    supplier_code = Column(String(50), comment="供应商编码")
    supplier_name = Column(String(200), comment="供应商名称")
    supplier_short_name = Column(String(50), comment="简称")
    supplier_type = Column(String(20), comment="供应商类型")

    # 联系信息
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(30), comment="联系电话")
    contact_email = Column(String(100), comment="邮箱")
    address = Column(String(500), comment="地址")

    # 财务信息
    bank_name = Column(String(100), comment="开户行")
    bank_account = Column(String(50), comment="银行账号")
    tax_number = Column(String(50), comment="税号")

    # 评价字段
    quality_rating = Column(Numeric(3, 2), default=0, comment="质量评分")
    delivery_rating = Column(Numeric(3, 2), default=0, comment="交期评分")
    service_rating = Column(Numeric(3, 2), default=0, comment="服务评分")
    overall_rating = Column(Numeric(3, 2), default=0, comment="综合评分")

    # 状态
    status = Column(String(20), default="ACTIVE", comment="状态")
    cooperation_start = Column(DateTime, comment="合作开始日期")
    last_order_date = Column(DateTime, comment="最后订单日期")


def get_database_url() -> str:
    """获取数据库连接URL"""
    # 优先使用 Vercel Postgres
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        return postgres_url

    # 其次使用 DATABASE_URL（兼容 Railway 等其他服务）
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # 默认使用SQLite
    db_path = os.getenv("SQLITE_DB_PATH", "data/app.db")
    return f"sqlite:///{db_path}"


def get_engine(database_url: Optional[str] = None, echo: bool = False):
    """
    获取数据库引擎

    Args:
        database_url: 数据库连接URL，默认从环境变量获取
        echo: 是否打印SQL语句

    Returns:
        SQLAlchemy引擎实例
    """
    global _engine

    if _engine is not None:
        return _engine

    url = database_url or get_database_url()

    # SQLite特殊配置
    if url.startswith("sqlite"):
        if ":memory:" in url or "mode=memory" in url:
            # 内存数据库必须用 StaticPool，确保所有连接共享同一个数据库实例
            # NullPool + :memory: 会导致每次连接都创建新的空数据库，表会丢失
            _engine = create_engine(
                url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            _engine = create_engine(
                url,
                echo=echo,
                connect_args={"check_same_thread": False},
                poolclass=NullPool,
                pool_pre_ping=True,  # 在使用连接前检查连接是否有效
            )

        # SQLite启用外键约束
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            # 使用 WAL 模式，更好的并发性能和权限兼容性
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            # 设置临时文件目录为数据库所在目录，避免 macOS 权限问题
            cursor.execute(
                "PRAGMA temp_store_directory = ''"
            )  # 空字符串表示使用默认位置
            cursor.execute("PRAGMA temp_store = MEMORY")  # 使用内存存储临时数据
            cursor.close()

        _ensure_sqlite_schema(_engine)
    elif url.startswith("postgres"):
        # PostgreSQL 配置（Vercel Postgres）
        _engine = create_engine(
            url,
            echo=echo,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
            pool_pre_ping=True,
        )
    else:
        # MySQL配置
        _engine = create_engine(
            url,
            echo=echo,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True,
        )

    return _engine


def get_session_factory():
    """获取session工厂"""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        # 导入 TenantQuery - 框架级租户过滤
        from app.core.database.tenant_query import TenantQuery

        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=RuntimePatchedSession,
            query_cls=TenantQuery,  # 使用租户感知的Query类
        )
    return _SessionLocal


SessionLocal = get_session_factory()


def get_session() -> Session:
    """获取数据库会话"""
    return SessionLocal()


def get_db():
    """
    FastAPI 依赖使用的数据库会话生成器
    """
    db = get_session()
    try:
        yield db
    finally:
        # 显式回滚任何未提交的更改，避免 macOS SQLite 权限问题
        try:
            db.rollback()
        except Exception:
            pass
        db.close()


@contextmanager
def get_db_session():
    """
    数据库会话上下文管理器

    Usage:
        with get_db_session() as session:
            session.query(User).all()
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(database_url: Optional[str] = None, drop_all: bool = False):
    """
    初始化数据库，创建所有表

    Args:
        database_url: 数据库连接URL
        drop_all: 是否先删除所有表
    """
    engine = get_engine(database_url)

    if drop_all:
        # 对于 SQLite，在 drop_all 前禁用外键约束，避免表删除顺序导致的外键约束失败
        url = str(engine.url)
        if url.startswith("sqlite"):
            with engine.begin() as conn:
                conn.execute(text("PRAGMA foreign_keys=OFF"))

        Base.metadata.drop_all(bind=engine)

        # 重新启用外键约束
        if url.startswith("sqlite"):
            with engine.begin() as conn:
                conn.execute(text("PRAGMA foreign_keys=ON"))

    Base.metadata.create_all(bind=engine)

    url = str(engine.url)
    if url.startswith("sqlite"):
        _ensure_sqlite_schema(engine)

    return engine


def reset_engine():
    """重置引擎（用于测试）"""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
