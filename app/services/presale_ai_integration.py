"""
售前AI系统集成服务
Team 10: 售前AI系统集成与前端UI
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
import json
import asyncio

from app.models.presale_ai import (
    PresaleAIUsageStats,
    PresaleAIFeedback,
    PresaleAIConfig,
    PresaleAIWorkflowLog,
    PresaleAIAuditLog,
    AIFunctionEnum,
    WorkflowStepEnum,
    WorkflowStatusEnum
)
from app.schemas.presale_ai import (
    AIUsageStatsCreate,
    AIUsageStatsUpdate,
    AIFeedbackCreate,
    AIConfigCreate,
    AIConfigUpdate,
    AIWorkflowLogCreate,
    AIAuditLogCreate,
    DashboardStatsResponse,
    WorkflowStatusResponse,
    HealthCheckResponse
)


class PresaleAIIntegrationService:
    """售前AI集成服务"""

    def __init__(self, db: Session):
        self.db = db

    # ============ AI使用统计 ============

    def record_usage(
        self,
        user_id: int,
        ai_function: str,
        success: bool,
        response_time: Optional[int] = None
    ) -> PresaleAIUsageStats:
        """记录AI使用情况"""
        today = date.today()
        
        # 查找今日统计记录
        stat = self.db.query(PresaleAIUsageStats).filter(
            and_(
                PresaleAIUsageStats.user_id == user_id,
                PresaleAIUsageStats.ai_function == ai_function,
                PresaleAIUsageStats.date == today
            )
        ).first()

        if stat:
            # 更新现有记录
            stat.usage_count += 1
            if success:
                stat.success_count += 1
            
            # 更新平均响应时间
            if response_time is not None:
                if stat.avg_response_time:
                    # 加权平均
                    total_time = stat.avg_response_time * (stat.usage_count - 1) + response_time
                    stat.avg_response_time = int(total_time / stat.usage_count)
                else:
                    stat.avg_response_time = response_time
        else:
            # 创建新记录
            stat = PresaleAIUsageStats(
                user_id=user_id,
                ai_function=ai_function,
                usage_count=1,
                success_count=1 if success else 0,
                avg_response_time=response_time,
                date=today
            )
            self.db.add(stat)

        self.db.commit()
        self.db.refresh(stat)
        return stat

    def get_usage_stats(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        ai_functions: Optional[List[str]] = None,
        user_ids: Optional[List[int]] = None
    ) -> List[PresaleAIUsageStats]:
        """获取使用统计"""
        query = self.db.query(PresaleAIUsageStats)

        if start_date:
            query = query.filter(PresaleAIUsageStats.date >= start_date)
        if end_date:
            query = query.filter(PresaleAIUsageStats.date <= end_date)
        if ai_functions:
            query = query.filter(PresaleAIUsageStats.ai_function.in_(ai_functions))
        if user_ids:
            query = query.filter(PresaleAIUsageStats.user_id.in_(user_ids))

        return query.order_by(desc(PresaleAIUsageStats.date)).all()

    def get_dashboard_stats(self, days: int = 30) -> DashboardStatsResponse:
        """获取仪表盘统计数据"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # 总体统计
        total_stats = self.db.query(
            func.sum(PresaleAIUsageStats.usage_count).label('total_usage'),
            func.sum(PresaleAIUsageStats.success_count).label('total_success'),
            func.avg(PresaleAIUsageStats.avg_response_time).label('avg_time')
        ).filter(
            PresaleAIUsageStats.date >= start_date
        ).first()

        total_usage = total_stats.total_usage or 0
        total_success = total_stats.total_success or 0
        success_rate = (total_success / total_usage * 100) if total_usage > 0 else 0
        avg_response_time = total_stats.avg_time or 0

        # Top功能
        top_functions = self.db.query(
            PresaleAIUsageStats.ai_function,
            func.sum(PresaleAIUsageStats.usage_count).label('count'),
            func.sum(PresaleAIUsageStats.success_count).label('success')
        ).filter(
            PresaleAIUsageStats.date >= start_date
        ).group_by(
            PresaleAIUsageStats.ai_function
        ).order_by(
            desc('count')
        ).limit(5).all()

        top_functions_list = [
            {
                'function': item.ai_function,
                'usage_count': item.count,
                'success_count': item.success,
                'success_rate': (item.success / item.count * 100) if item.count > 0 else 0
            }
            for item in top_functions
        ]

        # 使用趋势
        usage_trend = self.db.query(
            PresaleAIUsageStats.date,
            func.sum(PresaleAIUsageStats.usage_count).label('count')
        ).filter(
            PresaleAIUsageStats.date >= start_date
        ).group_by(
            PresaleAIUsageStats.date
        ).order_by(
            PresaleAIUsageStats.date
        ).all()

        usage_trend_list = [
            {
                'date': item.date.isoformat(),
                'count': item.count
            }
            for item in usage_trend
        ]

        # 用户统计
        user_count = self.db.query(
            func.count(func.distinct(PresaleAIUsageStats.user_id))
        ).filter(
            PresaleAIUsageStats.date >= start_date
        ).scalar()

        return DashboardStatsResponse(
            total_usage=total_usage,
            total_success=total_success,
            success_rate=round(success_rate, 2),
            avg_response_time=round(avg_response_time, 2),
            top_functions=top_functions_list,
            usage_trend=usage_trend_list,
            user_stats={'active_users': user_count}
        )

    # ============ AI反馈 ============

    def create_feedback(
        self,
        user_id: int,
        feedback_data: AIFeedbackCreate
    ) -> PresaleAIFeedback:
        """创建AI反馈"""
        feedback = PresaleAIFeedback(
            user_id=user_id,
            **feedback_data.dict()
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def get_feedbacks(
        self,
        ai_function: Optional[str] = None,
        min_rating: Optional[int] = None,
        max_rating: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PresaleAIFeedback]:
        """获取反馈列表"""
        query = self.db.query(PresaleAIFeedback)

        if ai_function:
            query = query.filter(PresaleAIFeedback.ai_function == ai_function)
        if min_rating:
            query = query.filter(PresaleAIFeedback.rating >= min_rating)
        if max_rating:
            query = query.filter(PresaleAIFeedback.rating <= max_rating)
        if start_date:
            query = query.filter(func.date(PresaleAIFeedback.created_at) >= start_date)
        if end_date:
            query = query.filter(func.date(PresaleAIFeedback.created_at) <= end_date)

        return query.order_by(desc(PresaleAIFeedback.created_at)).limit(limit).offset(offset).all()

    # ============ AI配置 ============

    def get_or_create_config(self, ai_function: str) -> PresaleAIConfig:
        """获取或创建AI配置"""
        config = self.db.query(PresaleAIConfig).filter(
            PresaleAIConfig.ai_function == ai_function
        ).first()

        if not config:
            config = PresaleAIConfig(
                ai_function=ai_function,
                enabled=True,
                temperature=0.7,
                max_tokens=2000,
                timeout_seconds=30
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

        return config

    def update_config(
        self,
        ai_function: str,
        config_data: AIConfigUpdate
    ) -> PresaleAIConfig:
        """更新AI配置"""
        config = self.get_or_create_config(ai_function)

        for key, value in config_data.dict(exclude_unset=True).items():
            setattr(config, key, value)

        self.db.commit()
        self.db.refresh(config)
        return config

    def get_all_configs(self) -> List[PresaleAIConfig]:
        """获取所有AI配置"""
        return self.db.query(PresaleAIConfig).all()

    # ============ AI工作流 ============

    def start_workflow(
        self,
        presale_ticket_id: int,
        initial_data: Optional[Dict[str, Any]] = None,
        auto_run: bool = True
    ) -> List[PresaleAIWorkflowLog]:
        """启动AI工作流"""
        workflow_steps = [
            WorkflowStepEnum.REQUIREMENT,
            WorkflowStepEnum.SOLUTION,
            WorkflowStepEnum.COST,
            WorkflowStepEnum.WINRATE,
            WorkflowStepEnum.QUOTATION
        ]

        logs = []
        for step in workflow_steps:
            log = PresaleAIWorkflowLog(
                presale_ticket_id=presale_ticket_id,
                workflow_step=step,
                status=WorkflowStatusEnum.PENDING,
                input_data=initial_data if step == WorkflowStepEnum.REQUIREMENT else None
            )
            self.db.add(log)
            logs.append(log)

        self.db.commit()

        # 如果auto_run，启动第一步
        if auto_run and logs:
            logs[0].status = WorkflowStatusEnum.RUNNING
            logs[0].started_at = datetime.now()
            self.db.commit()

        return logs

    def get_workflow_status(self, presale_ticket_id: int) -> Optional[WorkflowStatusResponse]:
        """获取工作流状态"""
        logs = self.db.query(PresaleAIWorkflowLog).filter(
            PresaleAIWorkflowLog.presale_ticket_id == presale_ticket_id
        ).order_by(PresaleAIWorkflowLog.id).all()

        if not logs:
            return None

        # 计算进度
        total_steps = len(logs)
        completed_steps = sum(1 for log in logs if log.status == WorkflowStatusEnum.SUCCESS)
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        # 确定当前步骤和整体状态
        current_step = "completed"
        overall_status = "completed"
        
        for log in logs:
            if log.status == WorkflowStatusEnum.RUNNING:
                current_step = log.workflow_step
                overall_status = "running"
                break
            elif log.status == WorkflowStatusEnum.PENDING:
                current_step = log.workflow_step
                overall_status = "pending"
                break
            elif log.status == WorkflowStatusEnum.FAILED:
                current_step = log.workflow_step
                overall_status = "failed"
                break

        return WorkflowStatusResponse(
            presale_ticket_id=presale_ticket_id,
            current_step=current_step,
            overall_status=overall_status,
            steps=[log for log in logs],
            progress=round(progress, 2),
            estimated_completion=None  # 可以根据平均时间估算
        )

    def update_workflow_step(
        self,
        log_id: int,
        status: WorkflowStatusEnum,
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> PresaleAIWorkflowLog:
        """更新工作流步骤"""
        log = self.db.query(PresaleAIWorkflowLog).filter(
            PresaleAIWorkflowLog.id == log_id
        ).first()

        if not log:
            raise ValueError(f"Workflow log {log_id} not found")

        log.status = status
        if output_data:
            log.output_data = output_data
        if error_message:
            log.error_message = error_message
        if status == WorkflowStatusEnum.SUCCESS or status == WorkflowStatusEnum.FAILED:
            log.completed_at = datetime.now()

        self.db.commit()
        self.db.refresh(log)
        return log

    # ============ 审计日志 ============

    def create_audit_log(
        self,
        user_id: int,
        action: str,
        ai_function: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PresaleAIAuditLog:
        """创建审计日志"""
        log = PresaleAIAuditLog(
            user_id=user_id,
            action=action,
            ai_function=ai_function,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PresaleAIAuditLog]:
        """获取审计日志"""
        query = self.db.query(PresaleAIAuditLog)

        if user_id:
            query = query.filter(PresaleAIAuditLog.user_id == user_id)
        if action:
            query = query.filter(PresaleAIAuditLog.action == action)
        if start_date:
            query = query.filter(func.date(PresaleAIAuditLog.created_at) >= start_date)
        if end_date:
            query = query.filter(func.date(PresaleAIAuditLog.created_at) <= end_date)

        return query.order_by(desc(PresaleAIAuditLog.created_at)).limit(limit).offset(offset).all()

    # ============ 健康检查 ============

    def health_check(self) -> HealthCheckResponse:
        """AI服务健康检查"""
        services = {}
        overall_status = "healthy"

        # 检查数据库连接
        try:
            self.db.execute("SELECT 1")
            services['database'] = {'status': 'healthy', 'message': 'Connected'}
        except Exception as e:
            services['database'] = {'status': 'unhealthy', 'message': str(e)}
            overall_status = "unhealthy"

        # 检查各AI功能配置
        ai_configs = self.get_all_configs()
        enabled_count = sum(1 for c in ai_configs if c.enabled)
        services['ai_functions'] = {
            'status': 'healthy' if enabled_count > 0 else 'degraded',
            'enabled_count': enabled_count,
            'total_count': len(ai_configs)
        }

        # 检查最近使用情况
        recent_usage = self.db.query(func.count(PresaleAIUsageStats.id)).filter(
            PresaleAIUsageStats.date >= date.today() - timedelta(days=1)
        ).scalar()

        services['recent_activity'] = {
            'status': 'healthy' if recent_usage > 0 else 'degraded',
            'usage_count_24h': recent_usage
        }

        return HealthCheckResponse(
            status=overall_status,
            services=services,
            timestamp=datetime.now()
        )
