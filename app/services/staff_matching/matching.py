# -*- coding: utf-8 -*-
"""
人员智能匹配服务 - 主匹配逻辑
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.organization import Employee
from app.models.project import Project
from app.models.staff_matching import (
    HrAIMatchingLog,
    HrEmployeeProfile,
    MesProjectStaffingNeed,
)

from .base import StaffMatchingBase
from .score_calculators import (
    AttitudeScoreCalculator,
    DomainScoreCalculator,
    QualityScoreCalculator,
    SkillScoreCalculator,
    SpecialScoreCalculator,
    WorkloadScoreCalculator,
)


class MatchingEngine(StaffMatchingBase):
    """匹配引擎 - 执行主匹配算法"""

    @classmethod
    def match_candidates(
        cls,
        db: Session,
        staffing_need_id: int,
        top_n: int = 10,
        include_overloaded: bool = False
    ) -> Dict:
        """
        执行AI匹配算法

        Args:
            db: 数据库会话
            staffing_need_id: 人员需求ID
            top_n: 返回候选人数量
            include_overloaded: 是否包含超负荷员工

        Returns:
            匹配结果字典
        """
        # 获取人员需求
        staffing_need = db.query(MesProjectStaffingNeed).filter(
            MesProjectStaffingNeed.id == staffing_need_id
        ).first()

        if not staffing_need:
            raise ValueError(f"人员需求不存在: {staffing_need_id}")

        # 获取项目信息
        project = db.query(Project).filter(Project.id == staffing_need.project_id).first()

        # 生成请求ID
        request_id = f"MATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

        # 获取所有活跃员工及其档案
        candidates = cls._get_candidate_employees(db, staffing_need, include_overloaded)

        # 计算每个候选人的得分
        scored_candidates = []
        for employee, profile in candidates:
            scores = cls._calculate_candidate_scores(
                db, employee, profile, staffing_need
            )
            scored_candidates.append({
                'employee': employee,
                'profile': profile,
                'scores': scores,
                'total_score': scores['total']
            })

        # 按总分排序
        scored_candidates.sort(key=lambda x: x['total_score'], reverse=True)

        # 获取优先级阈值
        threshold = cls.get_priority_threshold(staffing_need.priority)

        # 构建结果
        result_candidates = []
        for rank, candidate in enumerate(scored_candidates[:top_n], 1):
            employee = candidate['employee']
            profile = candidate['profile']
            scores = candidate['scores']

            # 分类推荐类型
            recommendation_type = cls.classify_recommendation(scores['total'], threshold)

            # 保存匹配日志
            log = HrAIMatchingLog(
                request_id=request_id,
                project_id=staffing_need.project_id,
                staffing_need_id=staffing_need_id,
                candidate_employee_id=employee.id,
                total_score=Decimal(str(round(scores['total'], 2))),
                dimension_scores={
                    'skill': round(scores['skill'], 2),
                    'domain': round(scores['domain'], 2),
                    'attitude': round(scores['attitude'], 2),
                    'quality': round(scores['quality'], 2),
                    'workload': round(scores['workload'], 2),
                    'special': round(scores['special'], 2)
                },
                rank=rank,
                recommendation_type=recommendation_type,
                matching_time=datetime.now()
            )
            db.add(log)

            # 构建候选人信息
            result_candidates.append({
                'employee_id': employee.id,
                'employee_name': employee.name,
                'employee_code': employee.employee_code,
                'department': employee.department,
                'total_score': round(scores['total'], 2),
                'dimension_scores': {
                    'skill': round(scores['skill'], 2),
                    'domain': round(scores['domain'], 2),
                    'attitude': round(scores['attitude'], 2),
                    'quality': round(scores['quality'], 2),
                    'workload': round(scores['workload'], 2),
                    'special': round(scores['special'], 2)
                },
                'rank': rank,
                'recommendation_type': recommendation_type,
                'matched_skills': scores.get('matched_skills', []),
                'missing_skills': scores.get('missing_skills', []),
                'current_workload_pct': float(profile.current_workload_pct) if profile else 0,
                'available_hours': float(profile.available_hours) if profile else 0
            })

        # 更新需求状态为匹配中
        staffing_need.status = 'MATCHING'
        db.commit()

        # 统计达到阈值的候选人数
        qualified_count = sum(1 for c in result_candidates if c['total_score'] >= threshold)

        return {
            'request_id': request_id,
            'staffing_need_id': staffing_need_id,
            'project_id': staffing_need.project_id,
            'project_name': project.name if project else None,
            'role_code': staffing_need.role_code,
            'role_name': staffing_need.role_name,
            'priority': staffing_need.priority,
            'priority_threshold': threshold,
            'candidates': result_candidates,
            'total_candidates': len(scored_candidates),
            'qualified_count': qualified_count,
            'matching_time': datetime.now().isoformat()
        }

    @classmethod
    def _get_candidate_employees(
        cls,
        db: Session,
        staffing_need: MesProjectStaffingNeed,
        include_overloaded: bool
    ) -> List[Tuple[Employee, Optional[HrEmployeeProfile]]]:
        """获取候选员工列表"""
        # 基础查询：活跃员工
        query = db.query(Employee, HrEmployeeProfile).outerjoin(
            HrEmployeeProfile, Employee.id == HrEmployeeProfile.employee_id
        ).filter(Employee.is_active)

        # 如果不包含超负荷员工，过滤工作负载
        if not include_overloaded:
            required_allocation = float(staffing_need.allocation_pct or 100)
            # 员工当前负载 + 需求分配比例 <= 100%，或者没有档案记录的员工
            query = query.filter(
                or_(
                    HrEmployeeProfile.id is None,  # 没有档案的员工（假设可用）
                    HrEmployeeProfile.current_workload_pct <= (100 - required_allocation * 0.5)
                )
            )

        return query.all()

    @classmethod
    def _calculate_candidate_scores(
        cls,
        db: Session,
        employee: Employee,
        profile: Optional[HrEmployeeProfile],
        staffing_need: MesProjectStaffingNeed
    ) -> Dict:
        """计算候选人各维度得分"""
        scores = {
            'skill': 0.0,
            'domain': 0.0,
            'attitude': 0.0,
            'quality': 0.0,
            'workload': 0.0,
            'special': 0.0,
            'matched_skills': [],
            'missing_skills': []
        }

        # 1. 计算技能匹配分
        skill_result = SkillScoreCalculator.calculate_skill_score(
            db, employee.id, profile,
            staffing_need.required_skills or [],
            staffing_need.preferred_skills or []
        )
        scores['skill'] = skill_result['score']
        scores['matched_skills'] = skill_result.get('matched', [])
        scores['missing_skills'] = skill_result.get('missing', [])

        # 2. 计算领域匹配分
        scores['domain'] = DomainScoreCalculator.calculate_domain_score(
            db, employee.id, profile,
            staffing_need.required_domains or []
        )

        # 3. 计算态度评分
        scores['attitude'] = AttitudeScoreCalculator.calculate_attitude_score(
            db, employee.id, profile,
            staffing_need.required_attitudes or []
        )

        # 4. 计算质量评分（从历史绩效）
        scores['quality'] = QualityScoreCalculator.calculate_quality_score(db, employee.id)

        # 5. 计算工作负载分
        scores['workload'] = WorkloadScoreCalculator.calculate_workload_score(
            profile, float(staffing_need.allocation_pct or 100)
        )

        # 6. 计算特殊能力分
        scores['special'] = SpecialScoreCalculator.calculate_special_score(db, employee.id, profile)

        # 计算加权总分
        scores['total'] = (
            scores['skill'] * cls.DIMENSION_WEIGHTS['skill'] +
            scores['domain'] * cls.DIMENSION_WEIGHTS['domain'] +
            scores['attitude'] * cls.DIMENSION_WEIGHTS['attitude'] +
            scores['quality'] * cls.DIMENSION_WEIGHTS['quality'] +
            scores['workload'] * cls.DIMENSION_WEIGHTS['workload'] +
            scores['special'] * cls.DIMENSION_WEIGHTS['special']
        )

        return scores
