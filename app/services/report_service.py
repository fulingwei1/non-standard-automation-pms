# -*- coding: utf-8 -*-
"""
工时报表自动生成服务
功能：报表数据生成、Excel导出、报表归档、报表分发
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import (
    ReportTemplate,
    ReportArchive,
    Timesheet,
)
from app.models.report import (
    ReportTypeEnum,
    GeneratedByEnum,
    ArchiveStatusEnum,
)
from app.utils.db_helpers import save_obj

logger = logging.getLogger(__name__)


class ReportService:
    """工时报表生成服务"""
    
    @staticmethod
    def get_active_monthly_templates(db: Session) -> List[ReportTemplate]:
        """获取启用的月度报表模板"""
        return db.query(ReportTemplate).filter(
            ReportTemplate.enabled == True,
            ReportTemplate.frequency == 'MONTHLY'
        ).all()
    
    @staticmethod
    def generate_report(
        db: Session,
        template_id: int,
        period: str,
        generated_by: str = GeneratedByEnum.SYSTEM.value
    ) -> Dict:
        """
        生成报表数据
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            period: 报表周期（如：2026-01）
            generated_by: 生成方式（SYSTEM/用户ID）
            
        Returns:
            报表数据字典
        """
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"报表模板不存在: {template_id}")
        
        # 解析周期
        year, month = map(int, period.split('-'))
        
        # 根据报表类型生成数据
        if template.report_type == ReportTypeEnum.USER_MONTHLY.value:
            data = ReportService._generate_user_monthly_report(db, template, year, month)
        elif template.report_type == ReportTypeEnum.DEPT_MONTHLY.value:
            data = ReportService._generate_dept_monthly_report(db, template, year, month)
        elif template.report_type == ReportTypeEnum.PROJECT_MONTHLY.value:
            data = ReportService._generate_project_monthly_report(db, template, year, month)
        elif template.report_type == ReportTypeEnum.COMPANY_MONTHLY.value:
            data = ReportService._generate_company_monthly_report(db, template, year, month)
        elif template.report_type == ReportTypeEnum.OVERTIME_MONTHLY.value:
            data = ReportService._generate_overtime_monthly_report(db, template, year, month)
        else:
            raise ValueError(f"不支持的报表类型: {template.report_type}")
        
        data['template'] = template
        data['period'] = period
        data['generated_by'] = generated_by
        
        return data
    
    @staticmethod
    def _generate_user_monthly_report(
        db: Session,
        template: ReportTemplate,
        year: int,
        month: int
    ) -> Dict:
        """生成人员月度工时报表"""
        
        # 查询工时数据
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        query = db.query(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name,
            func.sum(Timesheet.hours).label('total_hours'),
            func.sum(
                func.case(
                    (Timesheet.overtime_type == 'NORMAL', Timesheet.hours),
                    else_=0
                )
            ).label('normal_hours'),
            func.sum(
                func.case(
                    (Timesheet.overtime_type != 'NORMAL', Timesheet.hours),
                    else_=0
                )
            ).label('overtime_hours'),
            func.count(func.distinct(Timesheet.work_date)).label('work_days'),
        ).filter(
            and_(
                Timesheet.work_date >= start_date,
                Timesheet.work_date < end_date,
                Timesheet.status == 'APPROVED'
            )
        ).group_by(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name
        )
        
        # 应用配置的筛选条件
        if template.config and 'filters' in template.config:
            filters = template.config['filters']
            if 'department_ids' in filters:
                query = query.filter(Timesheet.department_id.in_(filters['department_ids']))
        
        results = query.all()
        
        # 转换为字典格式
        summary_data = []
        for row in results:
            summary_data.append({
                'user_id': row.user_id,
                'user_name': row.user_name,
                'department': row.department_name,
                'total_hours': float(row.total_hours or 0),
                'normal_hours': float(row.normal_hours or 0),
                'overtime_hours': float(row.overtime_hours or 0),
                'work_days': row.work_days,
                'avg_hours_per_day': round(float(row.total_hours or 0) / row.work_days, 2) if row.work_days > 0 else 0,
            })
        
        # 获取明细数据
        detail_query = db.query(Timesheet).filter(
            and_(
                Timesheet.work_date >= start_date,
                Timesheet.work_date < end_date,
                Timesheet.status == 'APPROVED'
            )
        )
        
        if template.config and 'filters' in template.config:
            filters = template.config['filters']
            if 'department_ids' in filters:
                detail_query = detail_query.filter(Timesheet.department_id.in_(filters['department_ids']))
        
        detail_data = []
        for ts in detail_query.all():
            detail_data.append({
                'user_name': ts.user_name,
                'department': ts.department_name,
                'work_date': ts.work_date.strftime('%Y-%m-%d'),
                'project_name': ts.project_name,
                'task_name': ts.task_name,
                'hours': float(ts.hours),
                'overtime_type': ts.overtime_type,
                'work_content': ts.work_content,
            })
        
        return {
            'summary': summary_data,
            'detail': detail_data,
            'year': year,
            'month': month,
        }
    
    @staticmethod
    def _generate_dept_monthly_report(
        db: Session,
        template: ReportTemplate,
        year: int,
        month: int
    ) -> Dict:
        """生成部门月度工时报表"""
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        query = db.query(
            Timesheet.department_id,
            Timesheet.department_name,
            func.count(func.distinct(Timesheet.user_id)).label('user_count'),
            func.sum(Timesheet.hours).label('total_hours'),
            func.sum(
                func.case(
                    (Timesheet.overtime_type == 'NORMAL', Timesheet.hours),
                    else_=0
                )
            ).label('normal_hours'),
            func.sum(
                func.case(
                    (Timesheet.overtime_type != 'NORMAL', Timesheet.hours),
                    else_=0
                )
            ).label('overtime_hours'),
        ).filter(
            and_(
                Timesheet.work_date >= start_date,
                Timesheet.work_date < end_date,
                Timesheet.status == 'APPROVED'
            )
        ).group_by(
            Timesheet.department_id,
            Timesheet.department_name
        )
        
        results = query.all()
        
        summary_data = []
        for row in results:
            summary_data.append({
                'department_id': row.department_id,
                'department_name': row.department_name,
                'user_count': row.user_count,
                'total_hours': float(row.total_hours or 0),
                'normal_hours': float(row.normal_hours or 0),
                'overtime_hours': float(row.overtime_hours or 0),
                'avg_hours_per_user': round(float(row.total_hours or 0) / row.user_count, 2) if row.user_count > 0 else 0,
            })
        
        return {
            'summary': summary_data,
            'detail': [],
            'year': year,
            'month': month,
        }
    
    @staticmethod
    def _generate_project_monthly_report(
        db: Session,
        template: ReportTemplate,
        year: int,
        month: int
    ) -> Dict:
        """生成项目月度工时报表"""
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        query = db.query(
            Timesheet.project_id,
            Timesheet.project_name,
            func.count(func.distinct(Timesheet.user_id)).label('user_count'),
            func.sum(Timesheet.hours).label('total_hours'),
        ).filter(
            and_(
                Timesheet.work_date >= start_date,
                Timesheet.work_date < end_date,
                Timesheet.status == 'APPROVED',
                Timesheet.project_id.isnot(None)
            )
        ).group_by(
            Timesheet.project_id,
            Timesheet.project_name
        )
        
        results = query.all()
        
        summary_data = []
        for row in results:
            summary_data.append({
                'project_id': row.project_id,
                'project_name': row.project_name,
                'user_count': row.user_count,
                'total_hours': float(row.total_hours or 0),
                'avg_hours_per_user': round(float(row.total_hours or 0) / row.user_count, 2) if row.user_count > 0 else 0,
            })
        
        return {
            'summary': summary_data,
            'detail': [],
            'year': year,
            'month': month,
        }
    
    @staticmethod
    def _generate_company_monthly_report(
        db: Session,
        template: ReportTemplate,
        year: int,
        month: int
    ) -> Dict:
        """生成公司整体工时报表"""
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # 总体统计
        total_stats = db.query(
            func.count(func.distinct(Timesheet.user_id)).label('total_users'),
            func.sum(Timesheet.hours).label('total_hours'),
            func.sum(
                func.case(
                    (Timesheet.overtime_type == 'NORMAL', Timesheet.hours),
                    else_=0
                )
            ).label('normal_hours'),
            func.sum(
                func.case(
                    (Timesheet.overtime_type != 'NORMAL', Timesheet.hours),
                    else_=0
                )
            ).label('overtime_hours'),
        ).filter(
            and_(
                Timesheet.work_date >= start_date,
                Timesheet.work_date < end_date,
                Timesheet.status == 'APPROVED'
            )
        ).first()
        
        summary_data = {
            'total_users': total_stats.total_users,
            'total_hours': float(total_stats.total_hours or 0),
            'normal_hours': float(total_stats.normal_hours or 0),
            'overtime_hours': float(total_stats.overtime_hours or 0),
            'avg_hours_per_user': round(
                float(total_stats.total_hours or 0) / total_stats.total_users, 2
            ) if total_stats.total_users > 0 else 0,
        }
        
        return {
            'summary': [summary_data],
            'detail': [],
            'year': year,
            'month': month,
        }
    
    @staticmethod
    def _generate_overtime_monthly_report(
        db: Session,
        template: ReportTemplate,
        year: int,
        month: int
    ) -> Dict:
        """生成加班统计报表"""
        
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        query = db.query(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name,
            func.sum(
                func.case(
                    (Timesheet.overtime_type == 'OVERTIME', Timesheet.hours),
                    else_=0
                )
            ).label('overtime_hours'),
            func.sum(
                func.case(
                    (Timesheet.overtime_type == 'WEEKEND', Timesheet.hours),
                    else_=0
                )
            ).label('weekend_hours'),
            func.sum(
                func.case(
                    (Timesheet.overtime_type == 'HOLIDAY', Timesheet.hours),
                    else_=0
                )
            ).label('holiday_hours'),
        ).filter(
            and_(
                Timesheet.work_date >= start_date,
                Timesheet.work_date < end_date,
                Timesheet.status == 'APPROVED',
                Timesheet.overtime_type != 'NORMAL'
            )
        ).group_by(
            Timesheet.user_id,
            Timesheet.user_name,
            Timesheet.department_name
        )
        
        results = query.all()
        
        summary_data = []
        for row in results:
            total_overtime = float(row.overtime_hours or 0) + float(row.weekend_hours or 0) + float(row.holiday_hours or 0)
            summary_data.append({
                'user_id': row.user_id,
                'user_name': row.user_name,
                'department': row.department_name,
                'overtime_hours': float(row.overtime_hours or 0),
                'weekend_hours': float(row.weekend_hours or 0),
                'holiday_hours': float(row.holiday_hours or 0),
                'total_overtime': total_overtime,
            })
        
        return {
            'summary': summary_data,
            'detail': [],
            'year': year,
            'month': month,
        }
    
    @staticmethod
    def get_last_month_period() -> str:
        """获取上月周期字符串（如：2026-01）"""
        today = datetime.now()
        if today.month == 1:
            last_month = datetime(today.year - 1, 12, 1)
        else:
            last_month = datetime(today.year, today.month - 1, 1)
        
        return last_month.strftime('%Y-%m')
    
    @staticmethod
    def archive_report(
        db: Session,
        template_id: int,
        period: str,
        file_path: str,
        file_size: int,
        row_count: int,
        generated_by: str = GeneratedByEnum.SYSTEM.value,
        status: str = ArchiveStatusEnum.SUCCESS.value,
        error_message: Optional[str] = None
    ) -> ReportArchive:
        """归档报表"""
        
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"报表模板不存在: {template_id}")
        
        archive = ReportArchive(
            template_id=template_id,
            report_type=template.report_type,
            period=period,
            file_path=file_path,
            file_size=file_size,
            row_count=row_count,
            generated_at=datetime.utcnow(),
            generated_by=generated_by,
            status=status,
            error_message=error_message,
            download_count=0,
        )
        
        save_obj(db, archive)
        
        logger.info(f"✅ 报表归档成功: {template.name} - {period}")
        
        return archive
    
    @staticmethod
    def increment_download_count(db: Session, archive_id: int):
        """增加下载次数"""
        archive = db.query(ReportArchive).filter(
            ReportArchive.id == archive_id
        ).first()
        
        if archive:
            archive.download_count += 1
            db.commit()
