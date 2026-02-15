# -*- coding: utf-8 -*-
"""
异常工时检测服务
实现5种异常检测规则
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.timesheet import Timesheet
from app.models.timesheet_reminder import AnomalyTypeEnum, TimesheetAnomalyRecord
from app.services.timesheet_reminder.reminder_manager import TimesheetReminderManager

logger = logging.getLogger(__name__)


class TimesheetAnomalyDetector:
    """工时异常检测器"""

    def __init__(self, db: Session):
        self.db = db
        self.reminder_manager = TimesheetReminderManager(db)

    def detect_all_anomalies(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        user_id: Optional[int] = None
    ) -> List[TimesheetAnomalyRecord]:
        """
        检测所有异常
        
        Args:
            start_date: 开始日期（默认昨天）
            end_date: 结束日期（默认今天）
            user_id: 用户ID（可选）
            
        Returns:
            异常记录列表
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=1)
        if end_date is None:
            end_date = date.today()

        anomalies = []

        # 1. 单日工时 > 12小时
        anomalies.extend(self.detect_daily_over_12(start_date, end_date, user_id))

        # 2. 单日工时 < 0 或 > 24
        anomalies.extend(self.detect_daily_invalid(start_date, end_date, user_id))

        # 3. 周工时 > 60小时
        anomalies.extend(self.detect_weekly_over_60(start_date, end_date, user_id))

        # 4. 连续7天无休息
        anomalies.extend(self.detect_no_rest_7days(start_date, end_date, user_id))

        # 5. 工时与进度不匹配
        anomalies.extend(self.detect_progress_mismatch(start_date, end_date, user_id))

        logger.info(f"异常检测完成: 发现 {len(anomalies)} 条异常")
        return anomalies

    def detect_daily_over_12(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> List[TimesheetAnomalyRecord]:
        """
        检测单日工时 > 12小时
        
        规则：单日总工时超过12小时视为异常
        """
        anomalies = []
        threshold = Decimal('12.0')

        # 按用户和日期分组统计
        query = self.db.query(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.work_date,
            func.sum(Timesheet.hours).label('total_hours'),
            func.group_concat(Timesheet.id).label('timesheet_ids')
        ).filter(
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status != 'CANCELLED'
        ).group_by(
            Timesheet.user_id,
            Timesheet.work_date
        )

        if user_id:
            query = query.filter(Timesheet.user_id == user_id)

        results = query.having(func.sum(Timesheet.hours) > threshold).all()

        for result in results:
            # 检查是否已存在该异常记录
            timesheet_ids = [int(x) for x in result.timesheet_ids.split(',')]
            first_timesheet_id = timesheet_ids[0]

            existing = self.db.query(TimesheetAnomalyRecord).filter(
                TimesheetAnomalyRecord.timesheet_id == first_timesheet_id,
                TimesheetAnomalyRecord.anomaly_type == AnomalyTypeEnum.DAILY_OVER_12,
                TimesheetAnomalyRecord.is_resolved == False
            ).first()

            if existing:
                continue

            # 创建异常记录
            anomaly = self.reminder_manager.create_anomaly_record(
                timesheet_id=first_timesheet_id,
                user_id=result.user_id,
                user_name=result.user_name,
                anomaly_type=AnomalyTypeEnum.DAILY_OVER_12,
                description=f"单日工时超标：{result.work_date} 填报 {result.total_hours} 小时（超过12小时阈值）",
                anomaly_data={
                    'work_date': result.work_date.isoformat(),
                    'total_hours': float(result.total_hours),
                    'threshold': float(threshold),
                    'timesheet_ids': timesheet_ids,
                },
                severity='WARNING'
            )
            anomalies.append(anomaly)

        logger.info(f"检测单日工时>12小时: 发现 {len(anomalies)} 条异常")
        return anomalies

    def detect_daily_invalid(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> List[TimesheetAnomalyRecord]:
        """
        检测单日工时 < 0 或 > 24
        
        规则：单日总工时小于0或大于24视为错误数据
        """
        anomalies = []

        # 按用户和日期分组统计
        query = self.db.query(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.work_date,
            func.sum(Timesheet.hours).label('total_hours'),
            func.group_concat(Timesheet.id).label('timesheet_ids')
        ).filter(
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status != 'CANCELLED'
        ).group_by(
            Timesheet.user_id,
            Timesheet.work_date
        )

        if user_id:
            query = query.filter(Timesheet.user_id == user_id)

        results = query.having(
            or_(
                func.sum(Timesheet.hours) < 0,
                func.sum(Timesheet.hours) > 24
            )
        ).all()

        for result in results:
            timesheet_ids = [int(x) for x in result.timesheet_ids.split(',')]
            first_timesheet_id = timesheet_ids[0]

            existing = self.db.query(TimesheetAnomalyRecord).filter(
                TimesheetAnomalyRecord.timesheet_id == first_timesheet_id,
                TimesheetAnomalyRecord.anomaly_type == AnomalyTypeEnum.DAILY_INVALID,
                TimesheetAnomalyRecord.is_resolved == False
            ).first()

            if existing:
                continue

            anomaly = self.reminder_manager.create_anomaly_record(
                timesheet_id=first_timesheet_id,
                user_id=result.user_id,
                user_name=result.user_name,
                anomaly_type=AnomalyTypeEnum.DAILY_INVALID,
                description=f"无效工时数据：{result.work_date} 填报 {result.total_hours} 小时（有效范围0-24）",
                anomaly_data={
                    'work_date': result.work_date.isoformat(),
                    'total_hours': float(result.total_hours),
                    'timesheet_ids': timesheet_ids,
                },
                severity='ERROR'
            )
            anomalies.append(anomaly)

        logger.info(f"检测无效工时数据: 发现 {len(anomalies)} 条异常")
        return anomalies

    def detect_weekly_over_60(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> List[TimesheetAnomalyRecord]:
        """
        检测周工时 > 60小时
        
        规则：一周（7天）总工时超过60小时视为异常
        """
        anomalies = []
        threshold = Decimal('60.0')

        # 计算周范围
        current_date = start_date
        while current_date <= end_date:
            # 找到这周的周一
            week_start = current_date - timedelta(days=current_date.weekday())
            week_end = week_start + timedelta(days=6)

            # 按用户统计该周工时
            query = self.db.query(
                Timesheet.user_id,
                Timesheet.user_name,
                func.sum(Timesheet.hours).label('weekly_hours'),
                func.group_concat(Timesheet.id).label('timesheet_ids')
            ).filter(
                Timesheet.work_date >= week_start,
                Timesheet.work_date <= week_end,
                Timesheet.status != 'CANCELLED'
            ).group_by(
                Timesheet.user_id
            )

            if user_id:
                query = query.filter(Timesheet.user_id == user_id)

            results = query.having(func.sum(Timesheet.hours) > threshold).all()

            for result in results:
                timesheet_ids = [int(x) for x in result.timesheet_ids.split(',')]
                first_timesheet_id = timesheet_ids[0]

                # 检查本周是否已有该类型异常
                existing = self.db.query(TimesheetAnomalyRecord).filter(
                    TimesheetAnomalyRecord.user_id == result.user_id,
                    TimesheetAnomalyRecord.anomaly_type == AnomalyTypeEnum.WEEKLY_OVER_60,
                    TimesheetAnomalyRecord.is_resolved == False,
                    TimesheetAnomalyRecord.anomaly_data['week_start'].astext == week_start.isoformat()
                ).first()

                if existing:
                    continue

                anomaly = self.reminder_manager.create_anomaly_record(
                    timesheet_id=first_timesheet_id,
                    user_id=result.user_id,
                    user_name=result.user_name,
                    anomaly_type=AnomalyTypeEnum.WEEKLY_OVER_60,
                    description=f"周工时超标：{week_start} ~ {week_end} 填报 {result.weekly_hours} 小时（超过60小时阈值）",
                    anomaly_data={
                        'week_start': week_start.isoformat(),
                        'week_end': week_end.isoformat(),
                        'weekly_hours': float(result.weekly_hours),
                        'threshold': float(threshold),
                        'timesheet_ids': timesheet_ids,
                    },
                    severity='WARNING'
                )
                anomalies.append(anomaly)

            # 移动到下一周
            current_date = week_end + timedelta(days=1)

        logger.info(f"检测周工时>60小时: 发现 {len(anomalies)} 条异常")
        return anomalies

    def detect_no_rest_7days(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> List[TimesheetAnomalyRecord]:
        """
        检测连续7天无休息
        
        规则：连续7天都有工时记录视为异常（过度加班）
        """
        anomalies = []

        # 获取需要检查的用户列表
        query = self.db.query(Timesheet.user_id, Timesheet.user_name).filter(
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status != 'CANCELLED'
        ).distinct()

        if user_id:
            query = query.filter(Timesheet.user_id == user_id)

        users = query.all()

        for user in users:
            # 获取该用户在这段时间的所有工作日期
            work_dates = [
                row.work_date for row in self.db.query(Timesheet.work_date).filter(
                    Timesheet.user_id == user.user_id,
                    Timesheet.work_date >= start_date,
                    Timesheet.work_date <= end_date,
                    Timesheet.status != 'CANCELLED'
                ).distinct().order_by(Timesheet.work_date).all()
            ]

            if len(work_dates) < 7:
                continue

            # 检查是否有连续7天
            consecutive_days = 1
            for i in range(1, len(work_dates)):
                if (work_dates[i] - work_dates[i-1]).days == 1:
                    consecutive_days += 1
                    if consecutive_days >= 7:
                        # 发现连续7天
                        period_end = work_dates[i]
                        period_start = period_end - timedelta(days=6)

                        # 检查是否已存在该异常
                        existing = self.db.query(TimesheetAnomalyRecord).filter(
                            TimesheetAnomalyRecord.user_id == user.user_id,
                            TimesheetAnomalyRecord.anomaly_type == AnomalyTypeEnum.NO_REST_7DAYS,
                            TimesheetAnomalyRecord.is_resolved == False,
                            TimesheetAnomalyRecord.anomaly_data['period_start'].astext == period_start.isoformat()
                        ).first()

                        if existing:
                            continue

                        # 获取这7天的工时记录ID
                        timesheet_ids = [
                            row.id for row in self.db.query(Timesheet.id).filter(
                                Timesheet.user_id == user.user_id,
                                Timesheet.work_date >= period_start,
                                Timesheet.work_date <= period_end,
                                Timesheet.status != 'CANCELLED'
                            ).all()
                        ]

                        if not timesheet_ids:
                            continue

                        anomaly = self.reminder_manager.create_anomaly_record(
                            timesheet_id=timesheet_ids[0],
                            user_id=user.user_id,
                            user_name=user.user_name,
                            anomaly_type=AnomalyTypeEnum.NO_REST_7DAYS,
                            description=f"连续工作无休息：{period_start} ~ {period_end} 连续7天工作",
                            anomaly_data={
                                'period_start': period_start.isoformat(),
                                'period_end': period_end.isoformat(),
                                'consecutive_days': 7,
                                'timesheet_ids': timesheet_ids,
                            },
                            severity='WARNING'
                        )
                        anomalies.append(anomaly)
                        break
                else:
                    consecutive_days = 1

        logger.info(f"检测连续7天无休息: 发现 {len(anomalies)} 条异常")
        return anomalies

    def detect_progress_mismatch(
        self,
        start_date: date,
        end_date: date,
        user_id: Optional[int] = None
    ) -> List[TimesheetAnomalyRecord]:
        """
        检测工时与进度不匹配
        
        规则：
        1. 填报工时但进度未更新
        2. 填报大量工时但进度增加很少
        """
        anomalies = []

        # 查询有进度字段的工时记录
        query = self.db.query(Timesheet).filter(
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date,
            Timesheet.status != 'CANCELLED',
            Timesheet.task_id.isnot(None)
        )

        if user_id:
            query = query.filter(Timesheet.user_id == user_id)

        timesheets = query.all()

        for timesheet in timesheets:
            # 检查1: 有工时但进度未更新
            if (timesheet.progress_before is not None and 
                timesheet.progress_after is not None):
                
                progress_change = timesheet.progress_after - timesheet.progress_before
                hours = float(timesheet.hours)

                # 填报超过4小时但进度没变化
                if hours >= 4 and progress_change == 0:
                    existing = self.db.query(TimesheetAnomalyRecord).filter(
                        TimesheetAnomalyRecord.timesheet_id == timesheet.id,
                        TimesheetAnomalyRecord.anomaly_type == AnomalyTypeEnum.PROGRESS_MISMATCH,
                        TimesheetAnomalyRecord.is_resolved == False
                    ).first()

                    if existing:
                        continue

                    anomaly = self.reminder_manager.create_anomaly_record(
                        timesheet_id=timesheet.id,
                        user_id=timesheet.user_id,
                        user_name=timesheet.user_name,
                        anomaly_type=AnomalyTypeEnum.PROGRESS_MISMATCH,
                        description=f"工时与进度不匹配：{timesheet.work_date} 填报 {hours} 小时但进度未更新",
                        anomaly_data={
                            'work_date': timesheet.work_date.isoformat(),
                            'hours': hours,
                            'progress_before': timesheet.progress_before,
                            'progress_after': timesheet.progress_after,
                            'progress_change': progress_change,
                            'task_id': timesheet.task_id,
                        },
                        severity='INFO'
                    )
                    anomalies.append(anomaly)

                # 填报超过8小时但进度增加少于10%
                elif hours >= 8 and 0 < progress_change < 10:
                    existing = self.db.query(TimesheetAnomalyRecord).filter(
                        TimesheetAnomalyRecord.timesheet_id == timesheet.id,
                        TimesheetAnomalyRecord.anomaly_type == AnomalyTypeEnum.PROGRESS_MISMATCH,
                        TimesheetAnomalyRecord.is_resolved == False
                    ).first()

                    if existing:
                        continue

                    anomaly = self.reminder_manager.create_anomaly_record(
                        timesheet_id=timesheet.id,
                        user_id=timesheet.user_id,
                        user_name=timesheet.user_name,
                        anomaly_type=AnomalyTypeEnum.PROGRESS_MISMATCH,
                        description=f"工时与进度不匹配：{timesheet.work_date} 填报 {hours} 小时但进度仅增加 {progress_change}%",
                        anomaly_data={
                            'work_date': timesheet.work_date.isoformat(),
                            'hours': hours,
                            'progress_before': timesheet.progress_before,
                            'progress_after': timesheet.progress_after,
                            'progress_change': progress_change,
                            'task_id': timesheet.task_id,
                        },
                        severity='INFO'
                    )
                    anomalies.append(anomaly)

        logger.info(f"检测工时与进度不匹配: 发现 {len(anomalies)} 条异常")
        return anomalies
