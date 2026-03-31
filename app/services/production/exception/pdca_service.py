# -*- coding: utf-8 -*-
"""
异常PDCA管理服务
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.production import (
    ExceptionPDCA,
    PDCAStage,
    ProductionException,
)
from app.models.user import User
from app.schemas.production.exception_enhancement import PDCAResponse
from app.utils.db_helpers import get_or_404, save_obj


class PDCAService:
    def __init__(self, db: Session):
        self.db = db

    def create_pdca(self, request, current_user_id: int) -> PDCAResponse:
        """创建PDCA记录"""
        get_or_404(self.db, ProductionException, request.exception_id, "异常不存在")

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
                detail=f"不能从 {pdca.current_stage.value} 推进到 {target_stage.value}",
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
            exception = (
                self.db.query(ProductionException)
                .filter(ProductionException.id == pdca.exception_id)
                .first()
            )
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
