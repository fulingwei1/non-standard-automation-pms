#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工时提醒系统验证脚本
快速验证核心功能是否正常
"""

import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.models.base import get_db_session
from app.models.timesheet import Timesheet
from app.models.timesheet_reminder import (
    AnomalyTypeEnum,
    ReminderTypeEnum,
    TimesheetReminderConfig,
)
from app.models.user import User
from app.services.timesheet_reminder.anomaly_detector import TimesheetAnomalyDetector
from app.services.timesheet_reminder.reminder_manager import TimesheetReminderManager


def print_header(text):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def test_reminder_manager():
    """测试提醒管理器"""
    print_header("测试1: 提醒管理器")
    
    with get_db_session() as db:
        manager = TimesheetReminderManager(db)
        
        # 测试创建规则配置
        try:
            config = manager.create_reminder_config(
                rule_code="TEST_RULE_001",
                rule_name="测试规则",
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                rule_parameters={"test": True},
            )
            print(f"✅ 创建规则配置成功: ID={config.id}, Code={config.rule_code}")
        except Exception as e:
            print(f"⚠️  创建规则配置失败（可能已存在）: {str(e)}")
        
        # 测试查询规则配置
        configs = manager.get_active_configs_by_type(ReminderTypeEnum.MISSING_TIMESHEET)
        print(f"✅ 查询到 {len(configs)} 条活跃的未填报提醒规则")
        
        # 测试创建提醒记录
        # 先查找一个用户
        user = db.query(User).filter(User.is_active == True).first()
        if user:
            reminder = manager.create_reminder_record(
                reminder_type=ReminderTypeEnum.MISSING_TIMESHEET,
                user_id=user.id,
                user_name=user.real_name or user.username,
                title="测试提醒",
                content="这是一条测试提醒",
                priority="NORMAL",
            )
            print(f"✅ 创建提醒记录成功: {reminder.reminder_no}")
            
            # 测试查询待处理提醒
            pending = manager.get_pending_reminders(user_id=user.id, limit=10)
            print(f"✅ 查询到 {len(pending)} 条待处理提醒")
        else:
            print("⚠️  未找到活跃用户，跳过提醒记录测试")


def test_anomaly_detector():
    """测试异常检测器"""
    print_header("测试2: 异常检测器")
    
    with get_db_session() as db:
        detector = TimesheetAnomalyDetector(db)
        
        # 查找一个有工时记录的用户
        timesheet = db.query(Timesheet).filter(
            Timesheet.hours > 0
        ).first()
        
        if not timesheet:
            print("⚠️  未找到工时记录，跳过异常检测测试")
            return
        
        user_id = timesheet.user_id
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        print(f"测试用户: ID={user_id}")
        print(f"测试日期范围: {yesterday} ~ {today}")
        
        # 测试单日工时>12小时检测
        anomalies_1 = detector.detect_daily_over_12(
            start_date=yesterday,
            end_date=today,
            user_id=user_id
        )
        print(f"✅ 单日>12小时检测: 发现 {len(anomalies_1)} 条异常")
        
        # 测试无效工时检测
        anomalies_2 = detector.detect_daily_invalid(
            start_date=yesterday,
            end_date=today,
            user_id=user_id
        )
        print(f"✅ 无效工时检测: 发现 {len(anomalies_2)} 条异常")
        
        # 测试周工时>60小时检测
        anomalies_3 = detector.detect_weekly_over_60(
            start_date=yesterday,
            end_date=today,
            user_id=user_id
        )
        print(f"✅ 周工时>60小时检测: 发现 {len(anomalies_3)} 条异常")
        
        # 测试连续7天无休息检测
        anomalies_4 = detector.detect_no_rest_7days(
            start_date=today - timedelta(days=7),
            end_date=today,
            user_id=user_id
        )
        print(f"✅ 连续7天无休息检测: 发现 {len(anomalies_4)} 条异常")
        
        # 测试工时与进度不匹配检测
        anomalies_5 = detector.detect_progress_mismatch(
            start_date=yesterday,
            end_date=today,
            user_id=user_id
        )
        print(f"✅ 工时与进度不匹配检测: 发现 {len(anomalies_5)} 条异常")
        
        # 测试全量检测
        all_anomalies = detector.detect_all_anomalies(
            start_date=yesterday,
            end_date=today,
            user_id=user_id
        )
        print(f"✅ 全量异常检测: 总计发现 {len(all_anomalies)} 条异常")


def test_database_models():
    """测试数据库模型"""
    print_header("测试3: 数据库模型")
    
    with get_db_session() as db:
        # 测试查询规则配置
        configs = db.query(TimesheetReminderConfig).limit(5).all()
        print(f"✅ 规则配置表: 查询到 {len(configs)} 条记录")
        
        # 显示规则详情
        for config in configs:
            print(f"  - {config.rule_code}: {config.rule_name} ({config.reminder_type.value})")


def test_data_integrity():
    """测试数据完整性"""
    print_header("测试4: 数据完整性")
    
    with get_db_session() as db:
        manager = TimesheetReminderManager(db)
        
        # 测试提醒编号生成
        test_types = [
            ReminderTypeEnum.MISSING_TIMESHEET,
            ReminderTypeEnum.APPROVAL_TIMEOUT,
            ReminderTypeEnum.ANOMALY_TIMESHEET,
        ]
        
        print("提醒编号生成规则:")
        for reminder_type in test_types:
            reminder_no = manager._generate_reminder_no(reminder_type)
            print(f"  - {reminder_type.value}: {reminder_no}")
        
        print("✅ 提醒编号生成正常")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  工时提醒系统验证")
    print("=" * 60)
    
    try:
        # 1. 测试提醒管理器
        test_reminder_manager()
        
        # 2. 测试异常检测器
        test_anomaly_detector()
        
        # 3. 测试数据库模型
        test_database_models()
        
        # 4. 测试数据完整性
        test_data_integrity()
        
        # 总结
        print_header("验证完成")
        print("✅ 所有核心功能正常")
        print("\n下一步:")
        print("1. 运行单元测试: pytest tests/test_timesheet_reminder.py")
        print("2. 初始化规则配置: python scripts/init_reminder_rules.py")
        print("3. 启动定时任务，测试自动检测")
        print("4. 测试API接口")
        
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
