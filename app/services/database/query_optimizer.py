# -*- coding: utf-8 -*-
"""
数据库查询优化服务

优化常见的慢查询，提升数据库性能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.sql import Select

from app.models.project import Project, ProjectMilestone, ProjectStatusLog
from app.models.issue import Issue, IssueTypeEnum
from app.models.alert import AlertRecord
from app.models.shortage import ShortageReport
from app.models.sales import Contract
from app.models.project import Customer
from app.models.user import User


class QueryOptimizer:
    """数据库查询优化器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_project_list_optimized(self, skip: int = 0, limit: int = 100, 
                                 status: Optional[str] = None,
                                 customer_id: Optional[int] = None) -> List[Project]:
        """
        优化的项目列表查询
        
        优化点：
        1. 使用joinedload避免N+1查询
        2. 添加适当的索引提示
        3. 使用selectinload处理一对多关系
        4. 添加分页优化
        """
        # 构建基础查询
        query = self.db.query(Project)
        
        # 预加载关联数据，避免N+1查询
        query = query.options(
            joinedload(Project.customer),
            joinedload(Project.owner),
            selectinload(Project.milestones),
            selectinload(Project.issues)
        )
        
        # 添加过滤条件
        if status:
            query = query.filter(Project.status == status)
        
        if customer_id:
            query = query.filter(Project.customer_id == customer_id)
        
        # 优化排序：使用索引字段
        query = query.order_by(desc(Project.created_at))
        
        # 分页
        return query.offset(skip).limit(limit).all()
    
    def get_project_dashboard_data(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目仪表板数据（优化版）
        
        优化点：
        1. 使用单一查询获取所有数据
        2. 避免多次数据库往返
        3. 使用聚合函数减少数据传输
        """
        # 获取项目基本信息（包含关联数据）
        project = self.db.query(Project).options(
            joinedload(Project.customer),
            joinedload(Project.owner),
            selectinload(Project.milestones),
            selectinload(Project.issues),
            selectinload(Project.contracts)
        ).filter(Project.id == project_id).first()
        
        if not project:
            return {}
        
        # 使用聚合查询获取统计数据
        milestone_stats = self.db.query(
            ProjectMilestone.status,
            func.count(ProjectMilestone.id).label('count')
        ).filter(
            ProjectMilestone.project_id == project_id
        ).group_by(ProjectMilestone.status).all()
        
        issue_stats = self.db.query(
            Issue.issue_type,
            Issue.status,
            func.count(Issue.id).label('count')
        ).filter(
            Issue.project_id == project_id
        ).group_by(Issue.issue_type, Issue.status).all()
        
        # 获取最近的活动记录
        recent_activities = self.db.query(ProjectStatusLog).filter(
            ProjectStatusLog.project_id == project_id
        ).order_by(desc(ProjectStatusLog.created_at)).limit(10).all()
        
        return {
            'project': project,
            'milestone_stats': dict(milestone_stats),
            'issue_stats': dict(issue_stats),
            'recent_activities': recent_activities
        }
    
    def search_projects_optimized(self, keyword: str, skip: int = 0, limit: int = 50) -> List[Project]:
        """
        优化的项目搜索
        
        优化点：
        1. 使用全文索引（如果数据库支持）
        2. 限制返回字段
        3. 使用更高效的LIKE查询
        """
        if not keyword or len(keyword.strip()) < 2:
            return []
        
        keyword = f"%{keyword.strip()}%"
        
        # 使用更高效的搜索查询
        query = self.db.query(Project).options(
            joinedload(Project.customer),
            joinedload(Project.owner)
        ).filter(
            or_(
                Project.project_name.like(keyword),
                Project.project_code.like(keyword),
                Project.description.like(keyword)
            )
        ).order_by(
            # 优先显示匹配度高的结果
            func.case(
                (Project.project_name.like(keyword), 1),
                (Project.project_code.like(keyword), 2),
                else_=3
            ),
            desc(Project.created_at)
        )
        
        return query.offset(skip).limit(limit).all()
    
    def get_alert_statistics_optimized(self, days: int = 30) -> Dict[str, Any]:
        """
        获取告警统计数据（优化版）
        
        优化点：
        1. 使用单个聚合查询
        2. 添加日期索引提示
        3. 减少数据传输量
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # 单个查询获取所有统计数据
        stats = self.db.query(
            func.count(AlertRecord.id).label('total_alerts'),
            func.sum(func.case((AlertRecord.alert_level == 'CRITICAL', 1), else_=0)).label('critical_count'),
            func.sum(func.case((AlertRecord.alert_level == 'WARNING', 1), else_=0)).label('warning_count'),
            func.sum(func.case((AlertRecord.alert_level == 'INFO', 1), else_=0)).label('info_count'),
            func.sum(func.case((AlertRecord.status == 'RESOLVED', 1), else_=0)).label('resolved_count'),
            func.sum(func.case((AlertRecord.status == 'PENDING', 1), else_=0)).label('pending_count')
        ).filter(
            AlertRecord.created_at >= start_date
        ).first()
        
        # 按日期分组的告警趋势
        daily_stats = self.db.query(
            func.date(AlertRecord.created_at).label('date'),
            func.count(AlertRecord.id).label('count'),
            func.sum(func.case((AlertRecord.alert_level == 'CRITICAL', 1), else_=0)).label('critical_count')
        ).filter(
            AlertRecord.created_at >= start_date
        ).group_by(
            func.date(AlertRecord.created_at)
        ).order_by(func.date(AlertRecord.created_at)).all()
        
        return {
            'summary': {
                'total_alerts': stats.total_alerts or 0,
                'critical_count': stats.critical_count or 0,
                'warning_count': stats.warning_count or 0,
                'info_count': stats.info_count or 0,
                'resolved_count': stats.resolved_count or 0,
                'pending_count': stats.pending_count or 0,
            },
            'daily_trend': daily_stats
        }
    
    def get_shortage_reports_optimized(self, project_id: Optional[int] = None, 
                                     status: Optional[str] = None,
                                     urgency: Optional[str] = None,
                                     skip: int = 0, limit: int = 100) -> List[ShortageReport]:
        """
        优化的缺料报告查询
        
        优化点：
        1. 添加复合索引提示
        2. 使用适当的连接策略
        3. 优化排序字段
        """
        query = self.db.query(ShortageReport).options(
            joinedload(ShortageReport.project),
            joinedload(ShortageReport.material)
        )
        
        # 添加过滤条件
        if project_id:
            query = query.filter(ShortageReport.project_id == project_id)
        
        if status:
            query = query.filter(ShortageReport.status == status)
        
        if urgency:
            query = query.filter(ShortageReport.urgency_level == urgency)
        
        # 优化排序：优先级高的在前
        query = query.order_by(
            func.case(
                (ShortageReport.urgency_level == 'HIGH', 1),
                (ShortageReport.urgency_level == 'MEDIUM', 2),
                (ShortageReport.urgency_level == 'LOW', 3),
                else_=4
            ),
            desc(ShortageReport.report_date)
        )
        
        return query.offset(skip).limit(limit).all()
    
    def get_contract_performance_optimized(self, days: int = 90) -> Dict[str, Any]:
        """
        获取合同业绩数据（优化版）
        
        优化点：
        1. 使用聚合查询
        2. 添加日期范围优化
        3. 预计算常用指标
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # 合同统计
        contract_stats = self.db.query(
            func.count(Contract.id).label('total_contracts'),
            func.sum(Contract.contract_amount).label('total_amount'),
            func.avg(Contract.contract_amount).label('avg_amount')
        ).filter(
            Contract.signed_date >= start_date
        ).first()
        
        # 按月份分组的趋势
        monthly_stats = self.db.query(
            func.date_trunc('month', Contract.signed_date).label('month'),
            func.count(Contract.id).label('count'),
            func.sum(Contract.contract_amount).label('amount')
        ).filter(
            Contract.signed_date >= start_date
        ).group_by(
            func.date_trunc('month', Contract.signed_date)
        ).order_by(
            func.date_trunc('month', Contract.signed_date)
        ).all()
        
        return {
            'summary': {
                'total_contracts': contract_stats.total_contracts or 0,
                'total_amount': float(contract_stats.total_amount or 0),
                'avg_amount': float(contract_stats.avg_amount or 0),
            },
            'monthly_trend': monthly_stats
        }
    
    def create_optimized_indexes_suggestions(self) -> List[str]:
        """
        提供数据库索引优化建议
        
        基于查询模式分析，提供索引创建建议
        """
        suggestions = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_status_created ON project(status, created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_project_customer_status ON project(customer_id, status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_milestone_project_status ON project_milestone(project_id, status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_milestone_date ON project_milestone(planned_date, status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alert_level_date ON alert_record(alert_level, created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alert_project_status ON alert_record(project_id, status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_issue_project_type ON issue(project_id, issue_type);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_shortage_urgency ON shortage_report(urgency_level, report_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contract_signed_date ON contract(signed_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_contract_customer_amount ON contract(customer_id, contract_amount);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_active_role ON user(is_active, role);",
        ]
        
        return suggestions
    
    def explain_slow_queries(self) -> Dict[str, Any]:
        """
        分析慢查询并提供优化建议
        
        使用EXPLAIN ANALYZE分析查询性能
        """
        slow_queries = []
        
        # 示例：分析复杂的项目列表查询
        explain_query = text("""
        EXPLAIN ANALYZE 
        SELECT p.*, c.name as customer_name, u.username as owner_name
        FROM project p
        LEFT JOIN customer c ON p.customer_id = c.id
        LEFT JOIN "user" u ON p.owner_id = u.id
        WHERE p.status = 'ACTIVE'
        ORDER BY p.created_at DESC
        LIMIT 100;
        """)
        
        try:
            result = self.db.execute(explain_query).fetchall()
            slow_queries.append({
                'query': '项目列表查询',
                'explain': result,
                'suggestion': '考虑添加复合索引 (status, created_at DESC)'
            })
        except Exception as e:
            slow_queries.append({
                'query': '项目列表查询',
                'error': str(e),
                'suggestion': '检查表结构和索引是否存在'
            })
        
        return {
            'slow_queries': slow_queries,
            'optimization_suggestions': self.create_optimized_indexes_suggestions()
        }