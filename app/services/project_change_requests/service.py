# -*- coding: utf-8 -*-
"""
项目变更请求服务层
"""

from typing import Any, Optional, List, Dict
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.project import Project
from app.models.change_request import (
    ChangeRequest,
    ChangeApprovalRecord,
    ChangeNotification,
)
from app.models.enums import (
    ChangeStatusEnum,
    ChangeTypeEnum,
    ChangeSourceEnum,
    ApprovalDecisionEnum,
)
from app.schemas.change_request import (
    ChangeRequestCreate,
    ChangeRequestUpdate,
    ChangeApprovalRequest,
    ChangeStatusUpdateRequest,
    ChangeImplementationRequest,
    ChangeVerificationRequest,
    ChangeCloseRequest,
    ChangeRequestStatistics,
)
from app.utils.db_helpers import get_or_404, save_obj
from app.common.query_filters import apply_pagination


class ProjectChangeRequestsService:
    """项目变更请求服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_change_code(self, project_id: int) -> str:
        """生成变更编号"""
        # 获取项目编号
        project = get_or_404(self.db, Project, project_id, detail="项目不存在")
        
        # 获取当前项目的变更数量
        count = self.db.query(func.count(ChangeRequest.id))\
            .filter(ChangeRequest.project_id == project_id)\
            .scalar() or 0
        
        # 格式: CHG-项目编码-序号 (如: CHG-PRJ001-001)
        return f"CHG-{project.project_code}-{count + 1:03d}"
    
    def validate_status_transition(
        self, 
        current_status: ChangeStatusEnum, 
        new_status: ChangeStatusEnum
    ) -> bool:
        """验证状态转换是否合法"""
        # 定义状态机转换规则
        valid_transitions = {
            ChangeStatusEnum.SUBMITTED: [ChangeStatusEnum.ASSESSING, ChangeStatusEnum.CANCELLED],
            ChangeStatusEnum.ASSESSING: [ChangeStatusEnum.PENDING_APPROVAL, ChangeStatusEnum.SUBMITTED, ChangeStatusEnum.CANCELLED],
            ChangeStatusEnum.PENDING_APPROVAL: [ChangeStatusEnum.APPROVED, ChangeStatusEnum.REJECTED, ChangeStatusEnum.ASSESSING, ChangeStatusEnum.CANCELLED],
            ChangeStatusEnum.APPROVED: [ChangeStatusEnum.IMPLEMENTING, ChangeStatusEnum.CANCELLED],
            ChangeStatusEnum.REJECTED: [],  # 已拒绝不能转换到其他状态
            ChangeStatusEnum.IMPLEMENTING: [ChangeStatusEnum.VERIFYING, ChangeStatusEnum.APPROVED],
            ChangeStatusEnum.VERIFYING: [ChangeStatusEnum.CLOSED, ChangeStatusEnum.IMPLEMENTING],
            ChangeStatusEnum.CLOSED: [],  # 已关闭不能转换到其他状态
            ChangeStatusEnum.CANCELLED: [],  # 已取消不能转换到其他状态
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def create_change_request(
        self, 
        change_in: ChangeRequestCreate, 
        current_user: User
    ) -> ChangeRequest:
        """提交变更请求"""
        # 验证项目是否存在
        project = get_or_404(self.db, Project, change_in.project_id, detail="项目不存在")
        
        # 生成变更编号
        change_code = self.generate_change_code(change_in.project_id)
        
        # 创建变更请求
        change_request = ChangeRequest(
            **change_in.model_dump(exclude={"project_id"}),
            change_code=change_code,
            project_id=change_in.project_id,
            submitter_id=current_user.id,
            submitter_name=current_user.real_name or current_user.username,
            status=ChangeStatusEnum.SUBMITTED,
            approval_decision=ApprovalDecisionEnum.PENDING,
        )
        
        save_obj(self.db, change_request)
        
        # 创建通知记录（后续可以扩展发送通知）
        if change_request.notify_team:
            # TODO: 实现团队通知逻辑
            pass
        
        return change_request
    
    def list_change_requests(
        self,
        offset: int,
        limit: int,
        project_id: Optional[int] = None,
        change_type: Optional[ChangeTypeEnum] = None,
        change_source: Optional[ChangeSourceEnum] = None,
        status: Optional[ChangeStatusEnum] = None,
        submitter_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> List[ChangeRequest]:
        """获取变更请求列表"""
        query = self.db.query(ChangeRequest)
        
        # 应用过滤条件
        if project_id:
            query = query.filter(ChangeRequest.project_id == project_id)
        if change_type:
            query = query.filter(ChangeRequest.change_type == change_type)
        if change_source:
            query = query.filter(ChangeRequest.change_source == change_source)
        if status:
            query = query.filter(ChangeRequest.status == status)
        if submitter_id:
            query = query.filter(ChangeRequest.submitter_id == submitter_id)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (ChangeRequest.title.like(search_pattern)) |
                (ChangeRequest.description.like(search_pattern)) |
                (ChangeRequest.change_code.like(search_pattern))
            )
        
        # 排序和分页
        changes = apply_pagination(
            query.order_by(desc(ChangeRequest.submit_date)),
            offset,
            limit
        ).all()
        
        return changes
    
    def get_change_request(self, change_id: int) -> ChangeRequest:
        """获取变更请求详情"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        return change_request
    
    def update_change_request(
        self,
        change_id: int,
        change_in: ChangeRequestUpdate,
    ) -> ChangeRequest:
        """更新变更请求"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        
        # 检查状态：已批准、已拒绝、已关闭的变更不能修改
        if change_request.status in [
            ChangeStatusEnum.APPROVED,
            ChangeStatusEnum.REJECTED,
            ChangeStatusEnum.CLOSED,
            ChangeStatusEnum.CANCELLED,
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"状态为 {change_request.status.value} 的变更请求不能修改"
            )
        
        # 更新字段
        update_data = change_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(change_request, field, value)
        
        save_obj(self.db, change_request)
        
        return change_request
    
    def approve_change_request(
        self,
        change_id: int,
        approval_in: ChangeApprovalRequest,
        current_user: User,
    ) -> ChangeRequest:
        """审批变更请求"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        
        # 检查状态：只有待审批状态才能审批
        if change_request.status != ChangeStatusEnum.PENDING_APPROVAL:
            raise HTTPException(
                status_code=400,
                detail="只有待审批状态的变更请求才能审批"
            )
        
        # 更新审批信息
        change_request.approver_id = current_user.id
        change_request.approver_name = current_user.real_name or current_user.username
        change_request.approval_date = datetime.utcnow()
        change_request.approval_decision = approval_in.decision
        change_request.approval_comments = approval_in.comments
        
        # 根据审批决策更新状态
        if approval_in.decision == ApprovalDecisionEnum.APPROVED:
            change_request.status = ChangeStatusEnum.APPROVED
        elif approval_in.decision == ApprovalDecisionEnum.REJECTED:
            change_request.status = ChangeStatusEnum.REJECTED
        elif approval_in.decision == ApprovalDecisionEnum.RETURNED:
            change_request.status = ChangeStatusEnum.ASSESSING
        
        # 创建审批记录
        approval_record = ChangeApprovalRecord(
            change_request_id=change_request.id,
            approver_id=current_user.id,
            approver_name=current_user.real_name or current_user.username,
            approver_role="PM",  # 可以从用户角色获取
            decision=approval_in.decision,
            comments=approval_in.comments,
            attachments=approval_in.attachments,
        )
        
        self.db.add(change_request)
        self.db.add(approval_record)
        self.db.commit()
        self.db.refresh(change_request)
        
        # 发送通知（后续实现）
        if change_request.notify_team:
            # TODO: 实现审批通知逻辑
            pass
        
        return change_request
    
    def get_approval_records(self, change_id: int) -> List[ChangeApprovalRecord]:
        """获取审批记录"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        
        records = self.db.query(ChangeApprovalRecord)\
            .filter(ChangeApprovalRecord.change_request_id == change_id)\
            .order_by(desc(ChangeApprovalRecord.approval_date))\
            .all()
        
        return records
    
    def update_change_status(
        self,
        change_id: int,
        status_in: ChangeStatusUpdateRequest,
    ) -> tuple[ChangeRequest, str]:
        """更新变更状态，返回变更请求和旧状态"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        
        # 验证状态转换是否合法
        if not self.validate_status_transition(change_request.status, status_in.new_status):
            raise HTTPException(
                status_code=400,
                detail=f"不允许从 {change_request.status.value} 转换到 {status_in.new_status.value}"
            )
        
        # 更新状态
        old_status = change_request.status.value
        change_request.status = status_in.new_status
        
        # 根据新状态更新相关字段
        if status_in.new_status == ChangeStatusEnum.IMPLEMENTING:
            if not change_request.implementation_start_date:
                change_request.implementation_start_date = datetime.utcnow()
        elif status_in.new_status == ChangeStatusEnum.VERIFYING:
            if not change_request.implementation_end_date:
                change_request.implementation_end_date = datetime.utcnow()
        elif status_in.new_status == ChangeStatusEnum.CLOSED:
            change_request.close_date = datetime.utcnow()
            change_request.close_notes = status_in.notes
        
        save_obj(self.db, change_request)
        
        return change_request, old_status
    
    def update_implementation_info(
        self,
        change_id: int,
        impl_in: ChangeImplementationRequest,
    ) -> ChangeRequest:
        """更新实施信息"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        
        # 只有已批准或实施中状态才能更新实施信息
        if change_request.status not in [ChangeStatusEnum.APPROVED, ChangeStatusEnum.IMPLEMENTING]:
            raise HTTPException(
                status_code=400,
                detail="只有已批准或实施中的变更才能更新实施信息"
            )
        
        # 更新实施信息
        update_data = impl_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(change_request, field, value)
        
        # 如果状态是已批准，自动转换为实施中
        if change_request.status == ChangeStatusEnum.APPROVED and impl_in.implementation_start_date:
            change_request.status = ChangeStatusEnum.IMPLEMENTING
        
        save_obj(self.db, change_request)
        
        return change_request
    
    def verify_change_request(
        self,
        change_id: int,
        verify_in: ChangeVerificationRequest,
        current_user: User,
    ) -> ChangeRequest:
        """验证变更"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        
        # 只有验证中状态才能验证
        if change_request.status != ChangeStatusEnum.VERIFYING:
            raise HTTPException(
                status_code=400,
                detail="只有验证中的变更才能进行验证"
            )
        
        # 更新验证信息
        change_request.verification_notes = verify_in.verification_notes
        change_request.verification_date = datetime.utcnow()
        change_request.verified_by_id = current_user.id
        change_request.verified_by_name = current_user.real_name or current_user.username
        change_request.status = ChangeStatusEnum.CLOSED
        change_request.close_date = datetime.utcnow()
        
        save_obj(self.db, change_request)
        
        return change_request
    
    def close_change_request(
        self,
        change_id: int,
        close_in: ChangeCloseRequest,
    ) -> ChangeRequest:
        """关闭变更"""
        change_request = get_or_404(self.db, ChangeRequest, change_id, detail="变更请求不存在")
        
        # 检查状态
        if change_request.status in [ChangeStatusEnum.CLOSED, ChangeStatusEnum.CANCELLED]:
            raise HTTPException(
                status_code=400,
                detail="变更已经关闭或取消"
            )
        
        # 关闭变更
        change_request.status = ChangeStatusEnum.CLOSED
        change_request.close_date = datetime.utcnow()
        change_request.close_notes = close_in.close_notes
        
        save_obj(self.db, change_request)
        
        return change_request
    
    def get_statistics(
        self,
        project_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ChangeRequestStatistics:
        """获取变更统计信息"""
        query = self.db.query(ChangeRequest)
        
        # 应用过滤条件
        if project_id:
            query = query.filter(ChangeRequest.project_id == project_id)
        if start_date:
            query = query.filter(ChangeRequest.submit_date >= start_date)
        if end_date:
            query = query.filter(ChangeRequest.submit_date <= end_date)
        
        all_changes = query.all()
        
        # 统计数据
        total = len(all_changes)
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        by_source: Dict[str, int] = {}
        total_cost_impact = Decimal(0)
        total_time_impact = 0
        
        for change in all_changes:
            # 按状态统计
            status_key = change.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1
            
            # 按类型统计
            type_key = change.change_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # 按来源统计
            source_key = change.change_source.value
            by_source[source_key] = by_source.get(source_key, 0) + 1
            
            # 累加成本和时间影响
            if change.cost_impact:
                total_cost_impact += change.cost_impact
            if change.time_impact:
                total_time_impact += change.time_impact
        
        # 统计审批状态
        pending_approval = by_status.get(ChangeStatusEnum.PENDING_APPROVAL.value, 0)
        approved = by_status.get(ChangeStatusEnum.APPROVED.value, 0)
        rejected = by_status.get(ChangeStatusEnum.REJECTED.value, 0)
        
        statistics = ChangeRequestStatistics(
            total=total,
            by_status=by_status,
            by_type=by_type,
            by_source=by_source,
            pending_approval=pending_approval,
            approved=approved,
            rejected=rejected,
            total_cost_impact=total_cost_impact,
            total_time_impact=total_time_impact,
        )
        
        return statistics
