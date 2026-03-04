#!/usr/bin/env python3
"""
现有数据加密迁移工具

用法:
  python scripts/encrypt_existing_data.py --table employees --columns id_card,bank_account
  python scripts/encrypt_existing_data.py --table employees --columns id_card,bank_account --dry-run
"""

import os
import sys

import click
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.encryption import data_encryption


def get_db_session():
    """获取数据库会话"""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def is_encrypted(value: str) -> bool:
    """
    检查值是否已加密

    AES-GCM加密后的Base64字符串通常以特定模式开头
    这里简单检查是否包含Base64字符和长度
    """
    if not value:
        return False

    # 检查是否是Base64字符串（只包含A-Za-z0-9_-=）
    import re

    if not re.match(r"^[A-Za-z0-9_\-=]+$", value):
        return False

    # 加密后长度通常是原始长度的1.5-2倍以上
    # 这里简单检查长度是否大于50（大部分明文不会这么长）
    return len(value) > 50


@click.command()
@click.option("--table", required=True, help="表名")
@click.option("--columns", required=True, help="字段名（逗号分隔）")
@click.option("--dry-run", is_flag=True, help="仅模拟，不实际修改")
@click.option("--batch-size", default=100, help="批量处理大小（默认100）")
def encrypt_data(table: str, columns: str, dry_run: bool, batch_size: int):
    """
    加密现有数据

    Args:
        table: 表名
        columns: 字段名（逗号分隔）
        dry_run: 仅模拟，不实际修改
        batch_size: 批量处理大小
    """
    db = get_db_session()
    column_list = [c.strip() for c in columns.split(",")]

    click.echo(f"\n{'='*60}")
    click.echo(f"📊 数据加密迁移工具")
    click.echo(f"{'='*60}")
    click.echo(f"表名: {table}")
    click.echo(f"字段: {', '.join(column_list)}")
    click.echo(f"模式: {'🔍 DRY RUN（仅模拟）' if dry_run else '✅ 正式加密'}")
    click.echo(f"批量大小: {batch_size}")
    click.echo(f"{'='*60}\n")

    try:
        # 获取所有记录
        query_columns = ", ".join(["id"] + column_list)
        query = text(f"SELECT {query_columns} FROM {table}")
        results = db.execute(query).fetchall()

        total = len(results)
        encrypted_count = 0
        skipped_count = 0
        error_count = 0

        click.echo(f"📦 找到 {total} 条记录")

        if total == 0:
            click.echo("⚠️  没有数据需要加密")
            return

        # 确认是否继续
        if not dry_run:
            if not click.confirm(f"\n⚠️  即将加密 {total} 条记录，是否继续？"):
                click.echo("❌ 操作已取消")
                return

        click.echo("\n开始处理...\n")

        # 批量处理
        for i, row in enumerate(results, 1):
            record_id = row[0]
            updates = {}
            has_update = False

            # 进度显示
            if i % batch_size == 0 or i == total:
                click.echo(f"进度: {i}/{total} ({i*100//total}%)")

            # 检查每个字段
            for idx, col in enumerate(column_list):
                old_value = row[idx + 1]

                if not old_value:
                    continue  # 跳过空值

                # 检查是否已加密
                if is_encrypted(str(old_value)):
                    if i <= 5:  # 只显示前5条
                        click.echo(f"  ⏭️  [跳过] ID={record_id}, {col}: 已加密")
                    skipped_count += 1
                    continue

                try:
                    # 加密
                    new_value = data_encryption.encrypt(str(old_value))
                    updates[col] = new_value
                    has_update = True

                    if dry_run and i <= 5:  # 只显示前5条
                        preview = (
                            str(old_value)[:20] + "..."
                            if len(str(old_value)) > 20
                            else str(old_value)
                        )
                        click.echo(f"  🔒 [DRY RUN] ID={record_id}, {col}: {preview} → 加密")

                except Exception as e:
                    click.echo(f"  ❌ [错误] ID={record_id}, {col}: {e}")
                    error_count += 1
                    continue

            # 更新数据库
            if has_update:
                if not dry_run:
                    try:
                        # 构建更新语句
                        set_clause = ", ".join([f"{col} = :{col}" for col in updates.keys()])
                        update_query = text(f"UPDATE {table} SET {set_clause} WHERE id = :id")
                        db.execute(update_query, {"id": record_id, **updates})
                        encrypted_count += len(updates)
                    except Exception as e:
                        click.echo(f"  ❌ [更新失败] ID={record_id}: {e}")
                        error_count += 1
                else:
                    encrypted_count += len(updates)

        # 提交事务
        if not dry_run:
            db.commit()
            click.echo("\n✅ 事务已提交")

        # 统计结果
        click.echo(f"\n{'='*60}")
        click.echo(f"📊 处理完成！")
        click.echo(f"{'='*60}")
        click.echo(f"总记录数: {total}")
        click.echo(f"✅ 已加密: {encrypted_count} 个字段")
        click.echo(f"⏭️  已跳过: {skipped_count} 个字段（已加密）")
        click.echo(f"❌ 错误数: {error_count} 个字段")

        if dry_run:
            click.echo(f"\n🔍 [DRY RUN] 未实际修改数据库")
            click.echo(f"如需正式加密，请去掉 --dry-run 参数")
        else:
            click.echo(f"\n✅ 数据已成功加密！")

        click.echo(f"{'='*60}\n")

    except Exception as e:
        click.echo(f"\n❌ 发生错误: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    encrypt_data()
