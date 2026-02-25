# -*- coding: utf-8 -*-
"""
报表服务层 - 处理所有报表相关的业务逻辑
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import (
    ReportTemplate,
    ReportArchive,
    ReportRecipient,
    Timesheet,
)
from app.models.report import (
    ReportTypeEnum,
    OutputFormatEnum,
    FrequencyEnum,
    GeneratedByEnum,
    ArchiveStatusEnum,
)

logger = logging.getLogger(__name__)


class ReportService:
    """报表业务逻辑服务"""
    
    def __init__(self, db: Session):
        """
        初始化报表服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    # ==================== 模板管理 ====================
    
    def create_template(
        self,
        name: str,
        report_type: str,
        created_by: int,
        description: Optional[str] = None,
        config: Optional[dict] = None,
        output_format: str = OutputFormatEnum.EXCEL.value,
        frequency: str = FrequencyEnum.MONTHLY.value,
        enabled: bool = True,
    ) -> ReportTemplate:
        """创建报表模板"""
        template = ReportTemplate(
            name=name,
            report_type=report_type,
            description=description,
            config=config or {},
            output_format=output_format,
            frequency=frequency,
            enabled=enabled,
            created_by=created_by,
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"创建报表模板: {template.name} (ID: {template.id})")
        
        return template
    
    def list_templates(
        self,
        report_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict:
        """获取报表模板列表（分页）"""
        query = self.db.query(ReportTemplate)
        
        # 筛选条件
        if report_type:
            query = query.filter(ReportTemplate.report_type == report_type)
        if enabled is not None:
            query = query.filter(ReportTemplate.enabled == enabled)
        
        # 分页
        total = query.count()
        templates = query.order_by(ReportTemplate.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'templates': templates,
        }
    
    def get_template(self, template_id: int) -> Optional[ReportTemplate]:
        """获取单个报表模板"""
        return self.db.query(ReportTemplate).filter(
            ReportTemplate.id == template_id
        ).first()
    
    def get_template_with_recipients(self, template_id: int) -> Optional[Dict]:
        """获取报表模板及其收件人列表"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        recipients = self.db.query(ReportRecipient).filter(
            ReportRecipient.template_id == template_id
        ).all()
        
        return {
            'template': template,
            'recipients': recipients,
        }
    
    def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[dict] = None,
        output_format: Optional[str] = None,
        frequency: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[ReportTemplate]:
        """更新报表模板"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        # 更新字段
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if config is not None:
            template.config = config
        if output_format is not None:
            template.output_format = output_format
        if frequency is not None:
            template.frequency = frequency
        if enabled is not None:
            template.enabled = enabled
        
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"更新报表模板: {template.name} (ID: {template.id})")
        
        return template
    
    def delete_template(self, template_id: int) -> bool:
        """删除报表模板"""
        template = self.get_template(template_id)
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        
        logger.info(f"删除报表模板: {template.name} (ID: {template.id})")
        
        return True
    
    def toggle_template(self, template_id: int) -> Optional[Dict]:
        """启用/禁用报表模板"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        template.enabled = not template.enabled
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(f"{'启用' if template.enabled else '禁用'}报表模板: {template.name}")
        
        return {
            'template': template,
            'enabled': template.enabled,
        }
    
    # ==================== 报表生成 ====================
    
    def generate_report_data(
        self,
        template_id: int,
        period: str,
        generated_by: str = GeneratedByEnum.SYSTEM.value
    ) -> Dict:
        """
        生成报表数据
        
        Args:
            template_id: 模板ID
            period: 报表周期（如：2026-01）
            generated_by: 生成方式（SYSTEM/USER_xxx）
            
        Returns:
            报表数据字典
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"报表模板不存在: {template_id}")
        
        # 解析周期
        year, month = map(int, period.split('-'))
        
        # 根据报表类型生成数据
        if template.report_type == ReportTypeEnum.USER_MONTHLY.value:
            data = self._generate_user_monthly_report(template, year, month)
        elif template.report_type == ReportTypeEnum.DEPT_MONTHLY.value:
            data = self._generate_dept_monthly_report(template, year, month)
        elif template.report_type == ReportTypeEnum.PROJECT_MONTHLY.value:
            data = self._generate_project_monthly_report(template, year, month)
        elif template.report_type == ReportTypeEnum.COMPANY_MONTHLY.value:
            data = self._generate_company_monthly_report(template, year, month)
        elif template.report_type == ReportTypeEnum.OVERTIME_MONTHLY.value:
            data = self._generate_overtime_monthly_report(template, year, month)
        else:
            raise ValueError(f"不支持的报表类型: {template.report_type}")
        
        data['template'] = template
        data['period'] = period
        data['generated_by'] = generated_by
        
        logger.info(f"生成报表数据: {template.name} - {period}")
        
        return data
    
    def _generate_user_monthly_report(
        self,
        template: ReportTemplate,
        year: int,
        month: int
    ) -> Dict:
        """生成人员月度工时报表"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        query = self.db.query(
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
        detail_query = self.db.query(Timesheet).filter(
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
    
    def _generate_dept_monthly_report(
        self,
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
        
        query = self.db.query(
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
    
    def _generate_project_monthly_report(
        self,
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
        
        query = self.db.query(
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
    
    def _generate_company_monthly_report(
        self,
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
        total_stats = self.db.query(
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
    
    def _generate_overtime_monthly_report(
        self,
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
        
        query = self.db.query(
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
    
    # ==================== 报表归档 ====================
    
    def archive_report(
        self,
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
        template = self.get_template(template_id)
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
        
        self.db.add(archive)
        self.db.commit()
        self.db.refresh(archive)
        
        logger.info(f"归档报表: {template.name} - {period} (ID: {archive.id})")
        
        return archive
    
    def list_archives(
        self,
        template_id: Optional[int] = None,
        report_type: Optional[str] = None,
        period: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict:
        """获取报表归档列表（分页）"""
        query = self.db.query(ReportArchive)
        
        # 筛选条件
        if template_id:
            query = query.filter(ReportArchive.template_id == template_id)
        if report_type:
            query = query.filter(ReportArchive.report_type == report_type)
        if period:
            query = query.filter(ReportArchive.period == period)
        if status:
            query = query.filter(ReportArchive.status == status)
        
        # 分页
        total = query.count()
        archives = query.order_by(ReportArchive.generated_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            'total': total,
            'page': page,
            'page_size': page_size,
            'archives': archives,
        }
    
    def get_archive(self, archive_id: int) -> Optional[ReportArchive]:
        """获取单个报表归档"""
        return self.db.query(ReportArchive).filter(
            ReportArchive.id == archive_id
        ).first()
    
    def get_archive_with_template(self, archive_id: int) -> Optional[Dict]:
        """获取报表归档及其模板信息"""
        archive = self.get_archive(archive_id)
        if not archive:
            return None
        
        template = self.get_template(archive.template_id)
        
        return {
            'archive': archive,
            'template': template,
        }
    
    def increment_download_count(self, archive_id: int) -> bool:
        """增加下载次数"""
        archive = self.get_archive(archive_id)
        if not archive:
            return False
        
        archive.download_count += 1
        self.db.commit()
        
        logger.info(f"下载报表归档: {archive.period} (ID: {archive.id}, 下载次数: {archive.download_count})")
        
        return True
    
    def get_archives_by_ids(self, archive_ids: List[int]) -> List[ReportArchive]:
        """根据ID列表批量获取归档"""
        return self.db.query(ReportArchive).filter(
            ReportArchive.id.in_(archive_ids)
        ).all()
    
    # ==================== 收件人管理 ====================
    
    def add_recipient(
        self,
        template_id: int,
        recipient_type: str,
        recipient_id: Optional[int] = None,
        recipient_email: Optional[str] = None,
        delivery_method: str = "EMAIL",
        enabled: bool = True,
    ) -> Optional[ReportRecipient]:
        """添加报表收件人"""
        template = self.get_template(template_id)
        if not template:
            return None
        
        recipient = ReportRecipient(
            template_id=template_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            recipient_email=recipient_email,
            delivery_method=delivery_method,
            enabled=enabled,
        )
        
        self.db.add(recipient)
        self.db.commit()
        self.db.refresh(recipient)
        
        logger.info(f"添加收件人: 模板 {template.name} (收件人ID: {recipient.id})")
        
        return recipient
    
    def delete_recipient(self, recipient_id: int) -> bool:
        """删除报表收件人"""
        recipient = self.db.query(ReportRecipient).filter(
            ReportRecipient.id == recipient_id
        ).first()
        
        if not recipient:
            return False
        
        self.db.delete(recipient)
        self.db.commit()
        
        logger.info(f"删除收件人: ID {recipient_id}")
        
        return True
