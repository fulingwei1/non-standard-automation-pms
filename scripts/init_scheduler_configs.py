#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化定时服务配置
从 scheduler_config.py 同步所有任务配置到数据库
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import get_db_session, init_db
from app.models.scheduler_config import SchedulerTaskConfig
from app.utils.scheduler_config import SCHEDULER_TASKS
import json


def sync_scheduler_configs(force=False):
    """
    同步定时任务配置到数据库
    
    Args:
        force: 是否强制同步（覆盖已有配置）
    """
    print("=" * 60)
    print("定时服务配置同步")
    print("=" * 60)
    
    # 确保数据库已初始化
    init_db()
    
    synced_count = 0
    created_count = 0
    updated_count = 0
    skipped_count = 0
    
    with get_db_session() as db:
        for task in SCHEDULER_TASKS:
            task_id = task["id"]
            
            # 检查是否已存在
            config = db.query(SchedulerTaskConfig).filter(
                SchedulerTaskConfig.task_id == task_id
            ).first()
            
            # 准备配置数据
            cron_config = task.get("cron", {})
            dependencies_tables = task.get("dependencies_tables", [])
            sla_config = task.get("sla", {})
            
            config_data = {
                "task_id": task_id,
                "task_name": task["name"],
                "module": task["module"],
                "callable_name": task["callable"],
                "owner": task.get("owner"),
                "category": task.get("category"),
                "description": task.get("description"),
                "is_enabled": task.get("enabled", True),
                "cron_config": cron_config,
                "dependencies_tables": dependencies_tables if dependencies_tables else None,
                "risk_level": task.get("risk_level"),
                "sla_config": sla_config if sla_config else None,
            }
            
            if config:
                # 更新现有配置
                if force:
                    for key, value in config_data.items():
                        if key != "task_id":  # 不更新task_id
                            setattr(config, key, value)
                    updated_count += 1
                    print(f"✅ 更新: {task['name']} ({task_id})")
                else:
                    skipped_count += 1
                    print(f"⏭️  跳过: {task['name']} ({task_id}) - 已存在")
            else:
                # 创建新配置
                config = SchedulerTaskConfig(**config_data)
                db.add(config)
                created_count += 1
                print(f"➕ 创建: {task['name']} ({task_id})")
            
            synced_count += 1
        
        db.commit()
    
    print("=" * 60)
    print(f"同步完成:")
    print(f"  - 总任务数: {synced_count}")
    print(f"  - 新建配置: {created_count}")
    print(f"  - 更新配置: {updated_count}")
    print(f"  - 跳过配置: {skipped_count}")
    print("=" * 60)
    
    return {
        "synced_count": synced_count,
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="同步定时服务配置到数据库")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制同步（覆盖已有配置）"
    )
    
    args = parser.parse_args()
    
    try:
        result = sync_scheduler_configs(force=args.force)
        print("\n✅ 配置同步成功！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 配置同步失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
