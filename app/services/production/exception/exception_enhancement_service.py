# -*- coding: utf-8 -*-
"""
异常处理增强服务
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.production import (
    ExceptionHandlingFlow,
    ExceptionKnowledge,
    ExceptionPDCA,
    FlowStatus,
    EscalationLevel,
    PDCAStage,
    ProductionException,
)
from app.models.user import User
from app.schemas.production.exception_enhancement import (
    ExceptionEscalateResponse,
    FlowTrackingResponse,
    KnowledgeResponse,
    KnowledgeListResponse,
    ExceptionStatisticsResponse,
    PDCAResponse,
    RecurrenceAnalysisResponse,
)
from app.utils.db_helpers import get_or_404, save_obj
from app.common.query_filters import apply_pagination


class ExceptionEnhancementService:
    def __init__(self, db: Session):
        self.db = db

    # ==================== 异常升级 ====================

    def escalate_exception(
        self,
        exception_id: int,
        escalation_level: str,
        reason: str,
        escalated_to_id: Optional[int],
    ) -> ExceptionEscalateResponse:
        """异常升级"""
        exception = get_or_404(self.db, ProductionException, exception_id, "异常不存在")

        # 查询或创建处理流程
        flow = self.db.query(ExceptionHandlingFlow).filter(
            ExceptionHandlingFlow.exception_id == exception_id
        ).first()

        if not flow:
            flow = ExceptionHandlingFlow(
                exception_id=exception_id,
                status=FlowStatus.PENDING,
                pending_at=datetime.now(),
            )
            self.db.add(flow)

        # 升级逻辑
        escalation_level_map = {
            "LEVEL_1": EscalationLevel.LEVEL_1,
            "LEVEL_2": EscalationLevel.LEVEL_2,
            "LEVEL_3": EscalationLevel.LEVEL_3,
        }

        flow.escalation_level = escalation_level_map.get(
            escalation_level,
            EscalationLevel.LEVEL_1
        )
        flow.escalation_reason = reason
        flow.escalated_at = datetime.now()
        flow.escalated_to_id = escalated_to_id

        # 更新异常状态
        if exception.status == "REPORTED":
            exception.status = "PROCESSING"
            exception.handler_id = escalated_to_id
            flow.status = FlowStatus.PROCESSING
            flow.processing_at = datetime.now()

        self.db.commit()
        self.db.refresh(flow)

        # 构造响应
        escalated_to_name = None
        if flow.escalated_to_id:
            escalated_to = self.db.query(User).filter(User.id == flow.escalated_to_id).first()
            if escalated_to:
                escalated_to_name = escalated_to.username

        return ExceptionEscalateResponse(
            id=flow.id,
            exception_id=flow.exception_id,
            status=flow.status.value,
            escalation_level=flow.escalation_level.value,
            escalation_reason=flow.escalation_reason,
            escalated_at=flow.escalated_at,
            escalated_to_id=flow.escalated_to_id,
            escalated_to_name=escalated_to_name,
            created_at=flow.created_at,
            updated_at=flow.updated_at,
        )

    # ==================== 处理流程跟踪 ====================

    def get_exception_flow(self, exception_id: int) -> FlowTrackingResponse:
        """获取异常处理流程跟踪"""
        flow = self.db.query(ExceptionHandlingFlow).options(
            joinedload(ExceptionHandlingFlow.exception),
            joinedload(ExceptionHandlingFlow.escalated_to),
            joinedload(ExceptionHandlingFlow.verifier),
        ).filter(
            ExceptionHandlingFlow.exception_id == exception_id
        ).first()

        if not flow:
            raise HTTPException(status_code=404, detail="未找到处理流程")

        # 计算处理时长
        self.calculate_flow_duration(flow)
        self.db.commit()
        self.db.refresh(flow)

        return FlowTrackingResponse(
            id=flow.id,
            exception_id=flow.exception_id,
            exception_no=flow.exception.exception_no if flow.exception else None,
            exception_title=flow.exception.title if flow.exception else None,
            status=flow.status.value,
            escalation_level=flow.escalation_level.value,
            escalation_reason=flow.escalation_reason,
            escalated_at=flow.escalated_at,
            escalated_to_name=flow.escalated_to.username if flow.escalated_to else None,
            pending_duration_minutes=flow.pending_duration_minutes,
            processing_duration_minutes=flow.processing_duration_minutes,
            total_duration_minutes=flow.total_duration_minutes,
            pending_at=flow.pending_at,
            processing_at=flow.processing_at,
            resolved_at=flow.resolved_at,
            verified_at=flow.verified_at,
            closed_at=flow.closed_at,
            verifier_name=flow.verifier.username if flow.verifier else None,
            verify_result=flow.verify_result,
            verify_comment=flow.verify_comment,
            created_at=flow.created_at,
            updated_at=flow.updated_at,
        )

    def calculate_flow_duration(self, flow: ExceptionHandlingFlow):
        """计算流程时长"""
        now = datetime.now()

        # 待处理时长
        if flow.pending_at:
            end_time = flow.processing_at or now
            flow.pending_duration_minutes = int(
                (end_time - flow.pending_at).total_seconds() / 60
            )

        # 处理中时长
        if flow.processing_at:
            end_time = flow.resolved_at or now
            flow.processing_duration_minutes = int(
                (end_time - flow.processing_at).total_seconds() / 60
            )

        # 总时长
        if flow.pending_at:
            end_time = flow.closed_at or now
            flow.total_duration_minutes = int(
                (end_time - flow.pending_at).total_seconds() / 60
            )

    # ==================== 异常知识库 ====================

    def create_knowledge(self, request, creator_id: int) -> KnowledgeResponse:
        """添加知识库条目"""
        knowledge = ExceptionKnowledge(
            title=request.title,
            exception_type=request.exception_type,
            exception_level=request.exception_level,
            symptom_description=request.symptom_description,
            solution=request.solution,
            solution_steps=request.solution_steps,
            prevention_measures=request.prevention_measures,
            keywords=request.keywords,
            source_exception_id=request.source_exception_id,
            attachments=request.attachments,
            creator_id=creator_id,
        )

        save_obj(self.db, knowledge)

        return self.build_knowledge_response(knowledge)

    def search_knowledge(
        self,
        keyword: Optional[str],
        exception_type: Optional[str],
        exception_level: Optional[str],
        is_approved: Optional[bool],
        offset: int,
        limit: int,
        page: int,
        page_size: int,
    ) -> KnowledgeListResponse:
        """知识库搜索（支持关键词、异常类型匹配）"""
        from sqlalchemy import or_

        query = self.db.query(ExceptionKnowledge)

        # 关键词搜索（标题、症状、解决方案、关键词）
        if keyword:
            keyword_filter = or_(
                ExceptionKnowledge.title.contains(keyword),
                ExceptionKnowledge.symptom_description.contains(keyword),
                ExceptionKnowledge.solution.contains(keyword),
                ExceptionKnowledge.keywords.contains(keyword),
            )
            query = query.filter(keyword_filter)

        # 异常类型过滤
        if exception_type:
            query = query.filter(ExceptionKnowledge.exception_type == exception_type)

        # 异常级别过滤
        if exception_level:
            query = query.filter(ExceptionKnowledge.exception_level == exception_level)

        # 审核状态过滤
        if is_approved is not None:
            query = query.filter(ExceptionKnowledge.is_approved == is_approved)

        # 按引用次数和创建时间排序
        query = query.order_by(
            desc(ExceptionKnowledge.reference_count),
            desc(ExceptionKnowledge.created_at)
        )

        # 分页
        total = query.count()
        items = apply_pagination(query, offset, limit).all()

        return KnowledgeListResponse(
            items=[self.build_knowledge_response(k) for k in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def build_knowledge_response(self, knowledge: ExceptionKnowledge) -> KnowledgeResponse:
        """构建知识库响应"""
        creator_name = None
        if knowledge.creator_id:
            creator = self.db.query(User).filter(User.id == knowledge.creator_id).first()
            if creator:
                creator_name = creator.username

        approver_name = None
        if knowledge.approver_id:
            approver = self.db.query(User).filter(User.id == knowledge.approver_id).first()
            if approver:
                approver_name = approver.username

        return KnowledgeResponse(
            id=knowledge.id,
            title=knowledge.title,
            exception_type=knowledge.exception_type,
            exception_level=knowledge.exception_level,
            symptom_description=knowledge.symptom_description,
            solution=knowledge.solution,
            solution_steps=knowledge.solution_steps,
            prevention_measures=knowledge.prevention_measures,
            keywords=knowledge.keywords,
            source_exception_id=knowledge.source_exception_id,
            reference_count=knowledge.reference_count,
            success_count=knowledge.success_count,
            last_referenced_at=knowledge.last_referenced_at,
            is_approved=knowledge.is_approved,
            approver_name=approver_name,
            approved_at=knowledge.approved_at,
            creator_name=creator_name,
            attachments=knowledge.attachments,
            remark=knowledge.remark,
            created_at=knowledge.created_at,
            updated_at=knowledge.updated_at,
        )

    # ==================== 异常统计分析 ====================

    def get_exception_statistics(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> ExceptionStatisticsResponse:
        """异常统计分析"""
        query = self.db.query(ProductionException)

        # 时间范围过滤
        if start_date:
            query = query.filter(ProductionException.report_time >= start_date)
        if end_date:
            query = query.filter(ProductionException.report_time <= end_date)

        # 总数
        total_count = query.count()

        effective_start = start_date or datetime(2000, 1, 1)
        effective_end = end_date or datetime.now()

        # 按类型统计
        by_type = {}
        type_stats = self.db.query(
            ProductionException.exception_type,
            func.count(ProductionException.id).label('count')
        ).filter(
            ProductionException.report_time >= effective_start,
            ProductionException.report_time <= effective_end
        ).group_by(ProductionException.exception_type).all()

        for type_name, count in type_stats:
            by_type[type_name] = count

        # 按级别统计
        by_level = {}
        level_stats = self.db.query(
            ProductionException.exception_level,
            func.count(ProductionException.id).label('count')
        ).filter(
            ProductionException.report_time >= effective_start,
            ProductionException.report_time <= effective_end
        ).group_by(ProductionException.exception_level).all()

        for level_name, count in level_stats:
            by_level[level_name] = count

        # 按状态统计
        by_status = {}
        status_stats = self.db.query(
            ProductionException.status,
            func.count(ProductionException.id).label('count')
        ).filter(
            ProductionException.report_time >= effective_start,
            ProductionException.report_time <= effective_end
        ).group_by(ProductionException.status).all()

        for status_name, count in status_stats:
            by_status[status_name] = count

        # 平均解决时长
        flows = self.db.query(ExceptionHandlingFlow).join(
            ProductionException,
            ExceptionHandlingFlow.exception_id == ProductionException.id
        ).filter(
            ProductionException.report_time >= effective_start,
            ProductionException.report_time <= effective_end,
            ExceptionHandlingFlow.total_duration_minutes.isnot(None)
        ).all()

        avg_resolution_time = None
        if flows:
            total_minutes = sum(f.total_duration_minutes or 0 for f in flows)
            avg_resolution_time = total_minutes / len(flows)

        # 升级率
        escalated_count = self.db.query(ExceptionHandlingFlow).join(
            ProductionException,
            ExceptionHandlingFlow.exception_id == ProductionException.id
        ).filter(
            ProductionException.report_time >= effective_start,
            ProductionException.report_time <= effective_end,
            ExceptionHandlingFlow.escalation_level != EscalationLevel.NONE
        ).count()

        escalation_rate = (escalated_count / total_count * 100) if total_count > 0 else 0

        # 重复异常率（简化版）
        recurrence_rate = 0.0

        # 高频异常TOP10
        top_exceptions = self.db.query(
            ProductionException.exception_type,
            ProductionException.title,
            func.count(ProductionException.id).label('count')
        ).filter(
            ProductionException.report_time >= effective_start,
            ProductionException.report_time <= effective_end
        ).group_by(
            ProductionException.exception_type,
            ProductionException.title
        ).order_by(desc('count')).limit(10).all()

        top_exceptions_list = [
            {
                "type": exc_type,
                "title": title,
                "count": count
            }
            for exc_type, title, count in top_exceptions
        ]

        return ExceptionStatisticsResponse(
            total_count=total_count,
            by_type=by_type,
            by_level=by_level,
            by_status=by_status,
            avg_resolution_time_minutes=avg_resolution_time,
            escalation_rate=escalation_rate,
            recurrence_rate=recurrence_rate,
            top_exceptions=top_exceptions_list,
        )

    # ==================== PDCA管理 ====================

    def create_pdca(self, request, current_user_id: int) -> PDCAResponse:
        """创建PDCA记录"""
        exception = get_or_404(self.db, ProductionException, request.exception_id, "异常不存在")

        # 生成PDCA编号
        pdca_no = f"PDCA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{request.exception_id}"

        pdca = ExceptionPDCA(
            exception_id=request.exception_id,
            pdca_no=pdca_no,
            current_stage=PDCAStage.PLAN,
            plan_description=request.plan_description,
            plan_root_cause=request.plan_root_cause,
            plan_target=request.plan_target,
            plan_measures=request.plan_measures,
            plan_owner_id=request.plan_owner_id,
            plan_deadline=request.plan_deadline,
            plan_completed_at=datetime.now(),
        )

        save_obj(self.db, pdca)

        return self.build_pdca_response(pdca)

    def advance_pdca_stage(self, pdca_id: int, request) -> PDCAResponse:
        """推进PDCA阶段"""
        pdca = get_or_404(self.db, ExceptionPDCA, pdca_id, detail="PDCA记录不存在")

        stage_map = {
            "DO": PDCAStage.DO,
            "CHECK": PDCAStage.CHECK,
            "ACT": PDCAStage.ACT,
            "COMPLETED": PDCAStage.COMPLETED,
        }

        target_stage = stage_map.get(request.stage)
        if not target_stage:
            raise HTTPException(status_code=400, detail="无效的阶段")

        # 状态机验证
        valid_transitions = {
            PDCAStage.PLAN: [PDCAStage.DO],
            PDCAStage.DO: [PDCAStage.CHECK],
            PDCAStage.CHECK: [PDCAStage.ACT],
            PDCAStage.ACT: [PDCAStage.COMPLETED],
        }

        if target_stage not in valid_transitions.get(pdca.current_stage, []):
            raise HTTPException(
                status_code=400,
                detail=f"不能从 {pdca.current_stage.value} 推进到 {target_stage.value}"
            )

        # 更新对应阶段的数据
        if target_stage == PDCAStage.DO:
            pdca.do_action_taken = request.do_action_taken
            pdca.do_resources_used = request.do_resources_used
            pdca.do_difficulties = request.do_difficulties
            pdca.do_owner_id = request.do_owner_id
            pdca.do_completed_at = datetime.now()

        elif target_stage == PDCAStage.CHECK:
            pdca.check_result = request.check_result
            pdca.check_effectiveness = request.check_effectiveness
            pdca.check_data = request.check_data
            pdca.check_gap = request.check_gap
            pdca.check_owner_id = request.check_owner_id
            pdca.check_completed_at = datetime.now()

        elif target_stage == PDCAStage.ACT:
            pdca.act_standardization = request.act_standardization
            pdca.act_horizontal_deployment = request.act_horizontal_deployment
            pdca.act_remaining_issues = request.act_remaining_issues
            pdca.act_next_cycle = request.act_next_cycle
            pdca.act_owner_id = request.act_owner_id
            pdca.act_completed_at = datetime.now()

        elif target_stage == PDCAStage.COMPLETED:
            pdca.summary = request.summary
            pdca.lessons_learned = request.lessons_learned
            pdca.is_completed = True
            pdca.completed_at = datetime.now()

        pdca.current_stage = target_stage

        self.db.commit()
        self.db.refresh(pdca)

        return self.build_pdca_response(pdca)

    def build_pdca_response(self, pdca: ExceptionPDCA) -> PDCAResponse:
        """构建PDCA响应"""
        exception_no = None
        if pdca.exception_id:
            exception = self.db.query(ProductionException).filter(
                ProductionException.id == pdca.exception_id
            ).first()
            if exception:
                exception_no = exception.exception_no

        def get_user_name(user_id):
            if not user_id:
                return None
            user = self.db.query(User).filter(User.id == user_id).first()
            return user.username if user else None

        return PDCAResponse(
            id=pdca.id,
            exception_id=pdca.exception_id,
            exception_no=exception_no,
            pdca_no=pdca.pdca_no,
            current_stage=pdca.current_stage.value,
            plan_description=pdca.plan_description,
            plan_root_cause=pdca.plan_root_cause,
            plan_target=pdca.plan_target,
            plan_measures=pdca.plan_measures,
            plan_owner_name=get_user_name(pdca.plan_owner_id),
            plan_deadline=pdca.plan_deadline,
            plan_completed_at=pdca.plan_completed_at,
            do_action_taken=pdca.do_action_taken,
            do_resources_used=pdca.do_resources_used,
            do_difficulties=pdca.do_difficulties,
            do_owner_name=get_user_name(pdca.do_owner_id),
            do_completed_at=pdca.do_completed_at,
            check_result=pdca.check_result,
            check_effectiveness=pdca.check_effectiveness,
            check_data=pdca.check_data,
            check_gap=pdca.check_gap,
            check_owner_name=get_user_name(pdca.check_owner_id),
            check_completed_at=pdca.check_completed_at,
            act_standardization=pdca.act_standardization,
            act_horizontal_deployment=pdca.act_horizontal_deployment,
            act_remaining_issues=pdca.act_remaining_issues,
            act_next_cycle=pdca.act_next_cycle,
            act_owner_name=get_user_name(pdca.act_owner_id),
            act_completed_at=pdca.act_completed_at,
            is_completed=pdca.is_completed,
            completed_at=pdca.completed_at,
            summary=pdca.summary,
            lessons_learned=pdca.lessons_learned,
            created_at=pdca.created_at,
            updated_at=pdca.updated_at,
        )

    # ==================== 重复异常分析 ====================

    def analyze_recurrence(
        self,
        exception_type: Optional[str],
        days: int,
    ) -> List[RecurrenceAnalysisResponse]:
        """重复异常分析"""
        start_date = datetime.now() - timedelta(days=days)

        query = self.db.query(ProductionException).filter(
            ProductionException.report_time >= start_date
        )

        if exception_type:
            query = query.filter(ProductionException.exception_type == exception_type)

        exceptions = query.all()

        # 按异常类型分组
        type_groups = {}
        for exc in exceptions:
            if exc.exception_type not in type_groups:
                type_groups[exc.exception_type] = []
            type_groups[exc.exception_type].append(exc)

        results = []
        for exc_type, exc_list in type_groups.items():
            # 查找相似异常（标题相似度 > 60%）
            similar_groups = self.find_similar_exceptions(exc_list)

            # 时间趋势
            time_trend = self.analyze_time_trend(exc_list, days)

            # 常见根因（从PDCA记录中提取）
            common_root_causes = self.extract_common_root_causes(
                [e.id for e in exc_list]
            )

            results.append(RecurrenceAnalysisResponse(
                exception_type=exc_type,
                total_occurrences=len(exc_list),
                similar_exceptions=similar_groups,
                time_trend=time_trend,
                common_root_causes=common_root_causes,
                recommended_actions=[
                    "建立标准作业程序",
                    "加强人员培训",
                    "优化设备维护计划",
                    "建立预警机制",
                ],
            ))

        return results

    def find_similar_exceptions(self, exceptions: list) -> List[dict]:
        """查找相似异常（Jaccard相似度算法）"""
        title_groups = {}
        for exc in exceptions:
            title = exc.title.lower()
            # 简单分词
            words = set(title.split())

            matched = False
            for existing_title, group in title_groups.items():
                existing_words = set(existing_title.split())
                # 计算Jaccard相似度
                intersection = len(words & existing_words)
                union = len(words | existing_words)
                similarity = intersection / union if union > 0 else 0

                if similarity > 0.6:
                    group.append(exc)
                    matched = True
                    break

            if not matched:
                title_groups[title] = [exc]

        # 只返回出现2次以上的
        similar = []
        for title, group in title_groups.items():
            if len(group) >= 2:
                similar.append({
                    "pattern": title,
                    "count": len(group),
                    "exception_ids": [e.id for e in group],
                })

        return sorted(similar, key=lambda x: x['count'], reverse=True)[:10]

    def analyze_time_trend(self, exceptions: list, days: int) -> List[dict]:
        """分析时间趋势"""
        # 按日期分组统计
        date_counts = {}
        for exc in exceptions:
            date_key = exc.report_time.strftime('%Y-%m-%d')
            date_counts[date_key] = date_counts.get(date_key, 0) + 1

        # 生成趋势数据
        trend = []
        start_date = datetime.now() - timedelta(days=days)
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_key = date.strftime('%Y-%m-%d')
            trend.append({
                "date": date_key,
                "count": date_counts.get(date_key, 0),
            })

        return trend

    def extract_common_root_causes(self, exception_ids: List[int]) -> List[str]:
        """提取常见根因"""
        pdca_records = self.db.query(ExceptionPDCA).filter(
            ExceptionPDCA.exception_id.in_(exception_ids),
            ExceptionPDCA.plan_root_cause.isnot(None)
        ).all()

        root_causes = [p.plan_root_cause for p in pdca_records if p.plan_root_cause]

        # 简化版：返回前3个
        return root_causes[:3] if root_causes else ["暂无根因分析"]
