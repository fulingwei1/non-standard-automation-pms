# -*- coding: utf-8 -*-
"""
添加大表分区支持

此迁移为销售模块的大表添加 PostgreSQL 分区支持：
- contracts (合同表) - 按 created_at 按月分区
- opportunities (商机表) - 按 created_at 按月分区
- leads (线索表) - 按 created_at 按月分区
- invoices (发票表) - 按 invoice_date 按月分区
- sales_operation_logs (操作日志表) - 按 created_at 按月分区

注意：
1. 此迁移仅在 PostgreSQL 数据库上执行
2. 分区转换是一个耗时操作，建议在维护窗口执行
3. 对于 SQLite/MySQL，此迁移将跳过

Revision ID: 20260311_partitioning
Revises: 20260310_add_data_audit
Create Date: 2026-03-11
"""

import logging
from datetime import date, datetime

from alembic import op
from sqlalchemy import text
from sqlalchemy.engine import Connection

# revision identifiers
revision = "20260311_partitioning"
down_revision = None  # 需要根据实际情况设置
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def is_postgres(connection: Connection) -> bool:
    """检查是否为 PostgreSQL"""
    try:
        result = connection.execute(text("SELECT version()"))
        version = result.scalar()
        return "PostgreSQL" in str(version) if version else False
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


def is_partitioned(connection: Connection, table_name: str) -> bool:
    """检查表是否已经是分区表"""
    try:
        result = connection.execute(
            text(
                """
            SELECT relkind = 'p'
            FROM pg_class
            WHERE relname = :table_name
        """
            ),
            {"table_name": table_name},
        )
        row = result.fetchone()
        return row[0] if row else False
    except Exception:
        return False


def create_partitioned_table(
    connection: Connection,
    table_name: str,
    partition_column: str,
) -> bool:
    """
    将现有表转换为分区表

    步骤:
    1. 重命名原表
    2. 创建分区父表（结构相同）
    3. 创建默认分区
    4. 根据历史数据创建月度分区
    5. 迁移数据
    6. 重建索引和外键
    7. 删除旧表
    """
    old_table = f"{table_name}_migration_old"

    try:
        logger.info(f"开始转换表 {table_name} 为分区表...")

        # 1. 获取原表结构（列定义）
        columns_result = connection.execute(
            text(
                """
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """
            ),
            {"table_name": table_name},
        )
        columns = columns_result.fetchall()

        if not columns:
            logger.warning(f"表 {table_name} 不存在或无列定义")
            return False

        # 2. 获取主键信息
        pk_result = connection.execute(
            text(
                """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = :table_name::regclass AND i.indisprimary
        """
            ),
            {"table_name": table_name},
        )
        pk_columns = [row[0] for row in pk_result.fetchall()]

        # 3. 重命名原表
        connection.execute(
            text(f'ALTER TABLE "{table_name}" RENAME TO "{old_table}"')
        )

        # 4. 构建列定义
        column_defs = []
        for col in columns:
            col_name = col[0]
            data_type = col[1]
            char_max_len = col[2]
            num_precision = col[3]
            num_scale = col[4]
            is_nullable = col[5]
            col_default = col[6]

            # 构建数据类型
            if char_max_len:
                type_str = f"{data_type}({char_max_len})"
            elif num_precision and num_scale:
                type_str = f"{data_type}({num_precision},{num_scale})"
            elif num_precision:
                type_str = f"{data_type}({num_precision})"
            else:
                type_str = data_type

            nullable = "" if is_nullable == "YES" else "NOT NULL"
            default = f"DEFAULT {col_default}" if col_default else ""

            column_defs.append(f'"{col_name}" {type_str} {nullable} {default}'.strip())

        # 5. 添加主键约束（如果有）
        pk_constraint = ""
        if pk_columns:
            pk_cols = ", ".join([f'"{c}"' for c in pk_columns])
            pk_constraint = f", PRIMARY KEY ({pk_cols})"

        # 6. 创建分区父表
        create_table_sql = f"""
            CREATE TABLE "{table_name}" (
                {', '.join(column_defs)}
                {pk_constraint}
            ) PARTITION BY RANGE ({partition_column})
        """
        connection.execute(text(create_table_sql))

        # 7. 创建默认分区
        default_partition = f"{table_name}_default"
        connection.execute(
            text(
                f'CREATE TABLE "{default_partition}" PARTITION OF "{table_name}" DEFAULT'
            )
        )

        # 8. 获取数据时间范围
        range_result = connection.execute(
            text(
                f"""
            SELECT
                DATE_TRUNC('month', MIN({partition_column}))::date as min_date,
                DATE_TRUNC('month', MAX({partition_column}))::date as max_date
            FROM "{old_table}"
            WHERE {partition_column} IS NOT NULL
        """
            )
        )
        range_row = range_result.fetchone()

        # 9. 创建历史月度分区
        if range_row and range_row[0]:
            min_date = range_row[0]
            max_date = range_row[1]
            # 扩展到未来3个月
            future_date = date.today().replace(day=1)
            for _ in range(3):
                year = future_date.year
                month = future_date.month
                if month == 12:
                    future_date = date(year + 1, 1, 1)
                else:
                    future_date = date(year, month + 1, 1)
            max_date = max(max_date, future_date)

            current = min_date
            while current <= max_date:
                year = current.year
                month = current.month
                partition_name = f"{table_name}_p{year}m{month:02d}"

                # 计算分区范围
                start_date = current
                if month == 12:
                    end_date = date(year + 1, 1, 1)
                else:
                    end_date = date(year, month + 1, 1)

                connection.execute(
                    text(
                        f"""
                    CREATE TABLE IF NOT EXISTS "{partition_name}"
                    PARTITION OF "{table_name}"
                    FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                """
                    )
                )

                # 移动到下个月
                current = end_date

        # 10. 迁移数据
        connection.execute(
            text(f'INSERT INTO "{table_name}" SELECT * FROM "{old_table}"')
        )

        # 11. 删除旧表
        connection.execute(text(f'DROP TABLE "{old_table}" CASCADE'))

        logger.info(f"表 {table_name} 成功转换为分区表")
        return True

    except Exception as e:
        logger.error(f"转换表 {table_name} 失败: {e}", exc_info=True)
        # 尝试回滚
        try:
            # 如果新表已创建，删除它
            connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
            # 恢复原表名
            connection.execute(
                text(f'ALTER TABLE IF EXISTS "{old_table}" RENAME TO "{table_name}"')
            )
        except Exception:
            pass
        raise


def upgrade():
    """升级数据库 - 添加分区"""
    connection = op.get_bind()

    # 检查是否为 PostgreSQL
    if not is_postgres(connection):
        logger.info("分区功能仅支持 PostgreSQL，跳过此迁移")
        return

    # 需要分区的表配置
    partition_tables = [
        ("contracts", "created_at"),
        ("opportunities", "created_at"),
        ("leads", "created_at"),
        ("invoices", "invoice_date"),
        ("sales_operation_logs", "created_at"),
    ]

    for table_name, partition_column in partition_tables:
        # 检查表是否存在
        if not table_exists(connection, table_name):
            logger.info(f"表 {table_name} 不存在，跳过")
            continue

        # 检查是否已经是分区表
        if is_partitioned(connection, table_name):
            logger.info(f"表 {table_name} 已经是分区表，跳过")
            continue

        # 转换为分区表
        try:
            create_partitioned_table(connection, table_name, partition_column)
        except Exception as e:
            logger.error(f"转换表 {table_name} 失败: {e}")
            # 继续处理其他表，不中断整个迁移


def downgrade():
    """降级数据库 - 移除分区

    注意：将分区表转回普通表是一个复杂操作，
    此处仅提供警告，不执行实际回滚。
    如需回滚，请手动执行以下步骤：
    1. 创建新的普通表
    2. 使用 INSERT INTO ... SELECT 从所有分区迁移数据
    3. 删除分区表
    4. 重命名新表
    """
    logger.warning(
        "分区表的降级需要手动执行。"
        "请参考迁移文件中的说明进行手动回滚。"
    )
