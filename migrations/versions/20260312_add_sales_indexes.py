# -*- coding: utf-8 -*-
"""
销售模块数据库索引优化

为销售相关表添加关键索引，提升查询性能：
- leads 表：owner_id, status, created_at 索引
- opportunities 表：owner_id, stage, customer_id+stage 复合索引
- contracts 表：customer_id+status 复合索引, opportunity_id, signed_at 索引
- invoices 表：contract_id+status 复合索引, due_date 索引
- customers 表：customer_name 索引
- quote_versions 表：status 索引
- technical_assessments 表：source_type+source_id 复合索引

Revision ID: 20260312_sales_indexes
Create Date: 2026-03-12
"""

import logging

from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection

# revision identifiers
revision = "20260312_sales_indexes"
down_revision = None  # 按实际依赖设置
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def index_exists(connection: Connection, index_name: str) -> bool:
    """检查索引是否存在"""
    try:
        # PostgreSQL
        result = connection.execute(
            text(
                """
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = :index_name
            )
        """
            ),
            {"index_name": index_name},
        )
        return result.scalar()
    except Exception:
        # SQLite fallback
        try:
            result = connection.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name = :index_name
            """
                ),
                {"index_name": index_name},
            )
            return result.fetchone() is not None
        except Exception:
            return False


def table_exists(connection: Connection, table_name: str) -> bool:
    """检查表是否存在"""
    try:
        result = connection.execute(
            text(
                """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = :table_name
            )
        """
            ),
            {"table_name": table_name},
        )
        return result.scalar()
    except Exception:
        return False


def create_index_if_not_exists(
    connection: Connection,
    index_name: str,
    table_name: str,
    columns: list,
    desc: bool = False,
) -> bool:
    """安全创建索引（如不存在）"""
    if not table_exists(connection, table_name):
        logger.info(f"表 {table_name} 不存在，跳过索引 {index_name}")
        return False

    if index_exists(connection, index_name):
        logger.info(f"索引 {index_name} 已存在，跳过")
        return False

    try:
        col_str = ", ".join(columns)
        if desc and len(columns) == 1:
            col_str = f"{columns[0]} DESC"

        sql = f'CREATE INDEX "{index_name}" ON "{table_name}" ({col_str})'
        connection.execute(text(sql))
        logger.info(f"创建索引: {index_name}")
        return True
    except Exception as e:
        logger.warning(f"创建索引 {index_name} 失败: {e}")
        return False


def drop_index_if_exists(connection: Connection, index_name: str) -> bool:
    """安全删除索引（如存在）"""
    if not index_exists(connection, index_name):
        return False

    try:
        connection.execute(text(f'DROP INDEX IF EXISTS "{index_name}"'))
        logger.info(f"删除索引: {index_name}")
        return True
    except Exception as e:
        logger.warning(f"删除索引 {index_name} 失败: {e}")
        return False


# 索引定义：(索引名, 表名, 列列表, 是否降序)
INDEXES = [
    # leads 表 - 高优先级
    ("idx_lead_owner", "leads", ["owner_id"], False),
    ("idx_lead_status", "leads", ["status"], False),
    ("idx_lead_created", "leads", ["created_at"], True),
    # opportunities 表 - 高优先级
    ("idx_opp_owner", "opportunities", ["owner_id"], False),
    ("idx_opp_stage", "opportunities", ["stage"], False),
    ("idx_opp_customer_stage", "opportunities", ["customer_id", "stage"], False),
    # contracts 表 - 高优先级
    ("idx_contract_customer_status", "contracts", ["customer_id", "status"], False),
    ("idx_contract_opportunity", "contracts", ["opportunity_id"], False),
    ("idx_contract_signed_at", "contracts", ["signed_at"], True),
    # invoices 表 - 高优先级
    ("idx_invoice_contract_status", "invoices", ["contract_id", "status"], False),
    ("idx_invoice_due_date", "invoices", ["due_date"], False),
    # customers 表 - 高优先级
    ("idx_customer_name", "customers", ["customer_name"], False),
    # quote_versions 表 - 中优先级
    ("idx_qv_status", "quote_versions", ["status"], False),
    # technical_assessments 表 - 中优先级
    ("idx_assess_source", "technical_assessments", ["source_type", "source_id"], False),
]


def upgrade():
    """升级数据库 - 添加索引"""
    connection = op.get_bind()

    created_count = 0
    skipped_count = 0

    for index_name, table_name, columns, desc in INDEXES:
        if create_index_if_not_exists(connection, index_name, table_name, columns, desc):
            created_count += 1
        else:
            skipped_count += 1

    logger.info(f"索引创建完成: 新建 {created_count} 个, 跳过 {skipped_count} 个")


def downgrade():
    """降级数据库 - 删除索引"""
    connection = op.get_bind()

    dropped_count = 0
    for index_name, _, _, _ in INDEXES:
        if drop_index_if_exists(connection, index_name):
            dropped_count += 1

    logger.info(f"索引删除完成: 删除 {dropped_count} 个")
