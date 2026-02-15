#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化工时提醒规则配置
创建默认的提醒规则
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.base import get_db_session
from app.models.timesheet_reminder import ReminderTypeEnum
from app.services.timesheet_reminder.reminder_manager import TimesheetReminderManager


def init_default_rules():
    """初始化默认提醒规则"""
    
    with get_db_session() as db:
        manager = TimesheetReminderManager(db)
        
        print("开始初始化工时提醒规则...")
        
        # 1. 未填报工时提醒规则
        try:
            config1 = manager.create_reminder_config(
                rule_code="DEFAULT_MISSING_DAILY",
                rule_name="每日工时填报提醒",
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                rule_parameters={
                    "check_days_ago": 1,
                    "remind_time": "09:00",
                    "skip_weekends": True,
                    "skip_holidays": True,
                },
                notification_channels=["SYSTEM", "EMAIL"],
                remind_frequency="ONCE_DAILY",
                max_reminders_per_day=1,
                priority="NORMAL",
            )
            print(f"✅ 创建规则: {config1.rule_name}")
        except Exception as e:
            print(f"⚠️  规则已存在或创建失败: DEFAULT_MISSING_DAILY - {str(e)}")
        
        # 2. 审批超时提醒规则
        try:
            config2 = manager.create_reminder_config(
                rule_code="DEFAULT_APPROVAL_TIMEOUT",
                rule_name="工时审批超时提醒",
                reminder_type=ReminderTypeEnum.APPROVAL_TIMEOUT,
                rule_parameters={
                    "timeout_days": 3,
                    "remind_approvers": True,
                },
                notification_channels=["SYSTEM", "EMAIL"],
                remind_frequency="TWICE_DAILY",
                max_reminders_per_day=2,
                priority="HIGH",
            )
            print(f"✅ 创建规则: {config2.rule_name}")
        except Exception as e:
            print(f"⚠️  规则已存在或创建失败: DEFAULT_APPROVAL_TIMEOUT - {str(e)}")
        
        # 3. 异常工时检测规则
        try:
            config3 = manager.create_reminder_config(
                rule_code="DEFAULT_ANOMALY_DETECTION",
                rule_name="异常工时自动检测",
                reminder_type=ReminderTypeEnum.ANOMALY_TIMESHEET,
                rule_parameters={
                    "daily_max_hours": 12,
                    "daily_valid_range": [0, 24],
                    "weekly_max_hours": 60,
                    "consecutive_work_days": 7,
                    "check_progress_mismatch": True,
                },
                notification_channels=["SYSTEM", "EMAIL"],
                remind_frequency="ONCE_DAILY",
                max_reminders_per_day=1,
                priority="HIGH",
            )
            print(f"✅ 创建规则: {config3.rule_name}")
        except Exception as e:
            print(f"⚠️  规则已存在或创建失败: DEFAULT_ANOMALY_DETECTION - {str(e)}")
        
        # 4. 周工时提醒规则
        try:
            config4 = manager.create_reminder_config(
                rule_code="DEFAULT_WEEKLY_REMINDER",
                rule_name="周工时填报提醒",
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                rule_parameters={
                    "check_weekly": True,
                    "remind_day": "Monday",
                    "remind_time": "10:00",
                },
                notification_channels=["SYSTEM"],
                remind_frequency="ONCE_DAILY",
                max_reminders_per_day=1,
                priority="NORMAL",
            )
            print(f"✅ 创建规则: {config4.rule_name}")
        except Exception as e:
            print(f"⚠️  规则已存在或创建失败: DEFAULT_WEEKLY_REMINDER - {str(e)}")
        
        # 5. 周末工时提醒（可选）
        try:
            config5 = manager.create_reminder_config(
                rule_code="DEFAULT_WEEKEND_WORK",
                rule_name="周末工时提醒",
                reminder_type=ReminderTypeEnum.WEEKEND_WORK,
                rule_parameters={
                    "notify_manager": True,
                    "require_approval": True,
                },
                notification_channels=["SYSTEM"],
                remind_frequency="ONCE_DAILY",
                max_reminders_per_day=1,
                priority="NORMAL",
                is_active=False,  # 默认不启用
            )
            print(f"✅ 创建规则: {config5.rule_name} (默认未启用)")
        except Exception as e:
            print(f"⚠️  规则已存在或创建失败: DEFAULT_WEEKEND_WORK - {str(e)}")
        
        print("\n初始化完成！")
        print("\n提示：")
        print("- 可以通过 API 接口修改规则配置")
        print("- 可以通过 is_active 字段启用/禁用规则")
        print("- 可以自定义适用范围（部门/角色/用户）")


if __name__ == "__main__":
    init_default_rules()
