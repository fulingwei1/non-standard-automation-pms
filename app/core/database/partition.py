# -*- coding: utf-8 -*-
"""
数据库分区配置

为大表提供 PostgreSQL 分区支持，包括：
- 按时间范围分区（年/月/季度）
- 按状态列表分区
- 分区维护（创建、删除、归档）
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PartitionType(str, Enum):
    """分区类型"""

    RANGE = "RANGE"  # 范围分区（如按日期）
    LIST = "LIST"  # 列表分区（如按状态）
    HASH = "HASH"  # 哈希分区（如按ID取模）


class PartitionInterval(str, Enum):
    """分区间隔（用于时间范围分区）"""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class PartitionConfig:
    """分区配置"""

    table_name: str  # 表名
    partition_type: PartitionType  # 分区类型
    partition_column: str  # 分区列
    interval: Optional[PartitionInterval] = None  # 时间间隔（仅用于 RANGE）
    list_values: Optional[Dict[str, List[str]]] = None  # 列表值映射（仅用于 LIST）
    retention_months: int = 36  # 数据保留月数
    enabled: bool = True  # 是否启用


# 销售模块大表分区配置
SALES_PARTITION_CONFIGS: List[PartitionConfig] = [
    # 合同表 - 按创建时间按月分区
    PartitionConfig(
        table_name="contracts",
        partition_type=PartitionType.RANGE,
        partition_column="created_at",
        interval=PartitionInterval.MONTHLY,
        retention_months=60,  # 5年
    ),
    # 商机表 - 按创建时间按月分区
    PartitionConfig(
        table_name="opportunities",
        partition_type=PartitionType.RANGE,
        partition_column="created_at",
        interval=PartitionInterval.MONTHLY,
        retention_months=36,  # 3年
    ),
    # 线索表 - 按创建时间按月分区
    PartitionConfig(
        table_name="leads",
        partition_type=PartitionType.RANGE,
        partition_column="created_at",
        interval=PartitionInterval.MONTHLY,
        retention_months=24,  # 2年
    ),
    # 发票表 - 按开票日期按月分区
    PartitionConfig(
        table_name="invoices",
        partition_type=PartitionType.RANGE,
        partition_column="invoice_date",
        interval=PartitionInterval.MONTHLY,
        retention_months=84,  # 7年（财务数据保留要求）
    ),
    # 销售操作日志 - 按操作时间按月分区
    PartitionConfig(
        table_name="sales_operation_logs",
        partition_type=PartitionType.RANGE,
        partition_column="created_at",
        interval=PartitionInterval.MONTHLY,
        retention_months=12,  # 1年
    ),
]


class PartitionManager:
    """分区管理器"""

    def __init__(self, db: Session):
        self.db = db

    def is_postgres(self) -> bool:
        """检查是否为 PostgreSQL 数据库"""
        try:
            result = self.db.execute(text("SELECT version()"))
            version = result.scalar()
            return "PostgreSQL" in str(version) if version else False
        except Exception:
            return False

    def get_partition_name(
        self,
        table_name: str,
        year: int,
        month: Optional[int] = None,
        quarter: Optional[int] = None,
    ) -> str:
        """
        生成分区名称

        格式: {table_name}_p{year}[m{month}|q{quarter}]
        """
        if month:
            return f"{table_name}_p{year}m{month:02d}"
        elif quarter:
            return f"{table_name}_p{year}q{quarter}"
        else:
            return f"{table_name}_p{year}"

    def get_date_range_for_partition(
        self,
        year: int,
        month: Optional[int] = None,
        quarter: Optional[int] = None,
        interval: PartitionInterval = PartitionInterval.MONTHLY,
    ) -> Tuple[date, date]:
        """
        获取分区的日期范围

        Returns:
            (start_date, end_date): 分区的起始和结束日期（end_date 为下一个周期的起始日期）
        """
        if interval == PartitionInterval.MONTHLY:
            if month is None:
                raise ValueError("月度分区需要指定 month")
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)

        elif interval == PartitionInterval.QUARTERLY:
            if quarter is None:
                raise ValueError("季度分区需要指定 quarter")
            start_month = (quarter - 1) * 3 + 1
            start_date = date(year, start_month, 1)
            if quarter == 4:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, start_month + 3, 1)

        elif interval == PartitionInterval.YEARLY:
            start_date = date(year, 1, 1)
            end_date = date(year + 1, 1, 1)

        else:
            raise ValueError(f"不支持的分区间隔: {interval}")

        return start_date, end_date

    def create_partitioned_table(self, config: PartitionConfig) -> bool:
        """
        将现有表转换为分区表

        注意：此操作需要在维护窗口执行，会导致表暂时不可用

        Steps:
        1. 重命名原表为 _old
        2. 创建分区父表
        3. 创建默认分区
        4. 迁移数据（按分区批量插入）
        5. 删除旧表

        Returns:
            bool: 是否成功
        """
        if not self.is_postgres():
            logger.warning("分区功能仅支持 PostgreSQL")
            return False

        table_name = config.table_name
        partition_column = config.partition_column

        try:
            # 检查表是否已经是分区表
            check_sql = text("""
                SELECT relkind
                FROM pg_class
                WHERE relname = :table_name
            """)
            result = self.db.execute(check_sql, {"table_name": table_name})
            row = result.fetchone()
            if row and row[0] == "p":
                logger.info(f"表 {table_name} 已经是分区表")
                return True

            logger.info(f"开始将表 {table_name} 转换为分区表...")

            # 1. 获取原表结构
            get_columns_sql = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = :table_name
                ORDER BY ordinal_position
            """)
            columns = self.db.execute(
                get_columns_sql, {"table_name": table_name}
            ).fetchall()

            if not columns:
                logger.error(f"表 {table_name} 不存在")
                return False

            # 2. 重命名原表
            old_table = f"{table_name}_old"
            rename_sql = text(f'ALTER TABLE "{table_name}" RENAME TO "{old_table}"')
            self.db.execute(rename_sql)

            # 3. 创建分区父表
            column_defs = []
            for col in columns:
                col_name, data_type, is_nullable, col_default = col
                nullable = "NOT NULL" if is_nullable == "NO" else ""
                default = f"DEFAULT {col_default}" if col_default else ""
                column_defs.append(f'"{col_name}" {data_type} {nullable} {default}')

            partition_by = (
                f"PARTITION BY {config.partition_type.value} ({partition_column})"
            )
            create_sql = f"""
                CREATE TABLE "{table_name}" (
                    {', '.join(column_defs)}
                ) {partition_by}
            """
            self.db.execute(text(create_sql))

            # 4. 创建默认分区（用于存放不在任何分区范围内的数据）
            default_partition = f"{table_name}_default"
            create_default_sql = text(
                f'CREATE TABLE "{default_partition}" PARTITION OF "{table_name}" DEFAULT'
            )
            self.db.execute(create_default_sql)

            # 5. 创建历史分区（基于现有数据）
            self._create_historical_partitions(config, old_table)

            # 6. 迁移数据
            migrate_sql = text(f'INSERT INTO "{table_name}" SELECT * FROM "{old_table}"')
            self.db.execute(migrate_sql)

            # 7. 删除旧表
            drop_sql = text(f'DROP TABLE "{old_table}"')
            self.db.execute(drop_sql)

            self.db.commit()
            logger.info(f"表 {table_name} 成功转换为分区表")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"转换分区表失败: {e}", exc_info=True)
            return False

    def _create_historical_partitions(
        self, config: PartitionConfig, old_table: str
    ) -> None:
        """根据历史数据创建分区"""
        table_name = config.table_name
        partition_column = config.partition_column

        # 获取数据的时间范围
        get_range_sql = text(f"""
            SELECT
                DATE_TRUNC('month', MIN({partition_column})) as min_date,
                DATE_TRUNC('month', MAX({partition_column})) as max_date
            FROM "{old_table}"
            WHERE {partition_column} IS NOT NULL
        """)
        result = self.db.execute(get_range_sql).fetchone()

        if not result or not result[0]:
            logger.info(f"表 {table_name} 无历史数据，跳过历史分区创建")
            return

        min_date, max_date = result[0], result[1]

        # 创建从最小月份到当前月份的所有分区
        current = min_date
        while current <= max_date:
            year = current.year
            month = current.month
            partition_name = self.get_partition_name(table_name, year, month)
            start_date, end_date = self.get_date_range_for_partition(
                year, month, interval=PartitionInterval.MONTHLY
            )

            create_partition_sql = text(f"""
                CREATE TABLE IF NOT EXISTS "{partition_name}"
                PARTITION OF "{table_name}"
                FOR VALUES FROM ('{start_date}') TO ('{end_date}')
            """)
            self.db.execute(create_partition_sql)

            # 移动到下个月
            if month == 12:
                current = datetime(year + 1, 1, 1)
            else:
                current = datetime(year, month + 1, 1)

    def create_future_partitions(
        self, config: PartitionConfig, months_ahead: int = 3
    ) -> List[str]:
        """
        创建未来的分区

        Args:
            config: 分区配置
            months_ahead: 提前创建多少个月的分区

        Returns:
            创建的分区名称列表
        """
        if not self.is_postgres():
            return []

        created_partitions = []
        table_name = config.table_name
        today = date.today()

        for i in range(months_ahead + 1):
            # 计算目标月份
            target_date = today + timedelta(days=30 * i)
            year = target_date.year
            month = target_date.month

            partition_name = self.get_partition_name(table_name, year, month)
            start_date, end_date = self.get_date_range_for_partition(
                year, month, interval=PartitionInterval.MONTHLY
            )

            try:
                # 检查分区是否已存在
                check_sql = text("""
                    SELECT 1 FROM pg_class WHERE relname = :partition_name
                """)
                exists = self.db.execute(
                    check_sql, {"partition_name": partition_name}
                ).fetchone()

                if not exists:
                    create_sql = text(f"""
                        CREATE TABLE IF NOT EXISTS "{partition_name}"
                        PARTITION OF "{table_name}"
                        FOR VALUES FROM ('{start_date}') TO ('{end_date}')
                    """)
                    self.db.execute(create_sql)
                    created_partitions.append(partition_name)
                    logger.info(f"创建分区: {partition_name}")

            except Exception as e:
                logger.warning(f"创建分区 {partition_name} 失败: {e}")

        if created_partitions:
            self.db.commit()

        return created_partitions

    def archive_old_partitions(
        self, config: PartitionConfig, archive_schema: str = "archive"
    ) -> List[str]:
        """
        归档超过保留期的分区

        Args:
            config: 分区配置
            archive_schema: 归档 schema 名称

        Returns:
            归档的分区名称列表
        """
        if not self.is_postgres():
            return []

        archived_partitions = []
        table_name = config.table_name
        retention_months = config.retention_months

        # 计算截止日期
        cutoff_date = date.today() - timedelta(days=30 * retention_months)

        try:
            # 确保归档 schema 存在
            create_schema_sql = text(
                f'CREATE SCHEMA IF NOT EXISTS "{archive_schema}"'
            )
            self.db.execute(create_schema_sql)

            # 获取所有子分区
            get_partitions_sql = text("""
                SELECT inhrelid::regclass::text as partition_name
                FROM pg_inherits
                WHERE inhparent = :table_name::regclass
            """)
            partitions = self.db.execute(
                get_partitions_sql, {"table_name": table_name}
            ).fetchall()

            for (partition_name,) in partitions:
                # 解析分区名称获取年月
                # 格式: table_name_pYYYYmMM
                if "_p" not in partition_name:
                    continue

                try:
                    parts = partition_name.split("_p")[-1]
                    if "m" in parts:
                        year = int(parts.split("m")[0])
                        month = int(parts.split("m")[1])
                        partition_date = date(year, month, 1)

                        if partition_date < cutoff_date:
                            # 移动到归档 schema
                            archive_sql = text(f"""
                                ALTER TABLE "{partition_name}"
                                SET SCHEMA "{archive_schema}"
                            """)
                            self.db.execute(archive_sql)
                            archived_partitions.append(partition_name)
                            logger.info(f"归档分区: {partition_name}")

                except (ValueError, IndexError):
                    continue

            if archived_partitions:
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"归档分区失败: {e}", exc_info=True)

        return archived_partitions

    def get_partition_stats(self, table_name: str) -> Dict[str, Any]:
        """
        获取分区统计信息

        Returns:
            分区统计信息字典
        """
        if not self.is_postgres():
            return {"error": "仅支持 PostgreSQL"}

        try:
            stats_sql = text("""
                SELECT
                    child.relname as partition_name,
                    pg_size_pretty(pg_relation_size(child.oid)) as size,
                    pg_stat_user_tables.n_live_tup as row_count
                FROM pg_inherits
                JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
                JOIN pg_class child ON pg_inherits.inhrelid = child.oid
                LEFT JOIN pg_stat_user_tables ON child.relname = pg_stat_user_tables.relname
                WHERE parent.relname = :table_name
                ORDER BY child.relname
            """)
            result = self.db.execute(stats_sql, {"table_name": table_name}).fetchall()

            partitions = []
            total_rows = 0
            for row in result:
                partition_info = {
                    "name": row[0],
                    "size": row[1],
                    "row_count": row[2] or 0,
                }
                partitions.append(partition_info)
                total_rows += row[2] or 0

            return {
                "table_name": table_name,
                "partition_count": len(partitions),
                "total_rows": total_rows,
                "partitions": partitions,
            }

        except Exception as e:
            logger.error(f"获取分区统计失败: {e}")
            return {"error": str(e)}


def maintain_all_partitions(db: Session) -> Dict[str, Any]:
    """
    维护所有配置的分区表

    执行：
    1. 创建未来3个月的分区
    2. 归档超过保留期的分区

    Returns:
        维护结果摘要
    """
    manager = PartitionManager(db)

    if not manager.is_postgres():
        return {"status": "skipped", "reason": "仅支持 PostgreSQL"}

    results = {
        "status": "success",
        "created_partitions": [],
        "archived_partitions": [],
        "errors": [],
    }

    for config in SALES_PARTITION_CONFIGS:
        if not config.enabled:
            continue

        try:
            # 创建未来分区
            created = manager.create_future_partitions(config, months_ahead=3)
            results["created_partitions"].extend(created)

            # 归档旧分区
            archived = manager.archive_old_partitions(config)
            results["archived_partitions"].extend(archived)

        except Exception as e:
            results["errors"].append(f"{config.table_name}: {str(e)}")

    if results["errors"]:
        results["status"] = "partial"

    return results
