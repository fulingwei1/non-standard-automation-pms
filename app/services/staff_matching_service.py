# -*- coding: utf-8 -*-
"""
AI驱动人员智能匹配服务
实现6维度加权匹配算法
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.staff_matching import (
    HrTagDict, HrEmployeeTagEvaluation, HrEmployeeProfile,
    HrProjectPerformance, MesProjectStaffingNeed, HrAIMatchingLog,
    TagTypeEnum, StaffingPriorityEnum, RecommendationTypeEnum
)
from app.models.organization import Employee
from app.models.project import Project, ProjectMember
from app.models.user import User


class StaffMatchingService:
    """人员智能匹配服务"""

    # 维度权重配置
    DIMENSION_WEIGHTS = {
        'skill': 0.30,      # 技能匹配 30%
        'domain': 0.15,     # 领域匹配 15%
        'attitude': 0.20,   # 态度评分 20%
        'quality': 0.15,    # 质量评分 15%
        'workload': 0.15,   # 工作负载 15%
        'special': 0.05     # 特殊能力 5%
    }

    # 优先级对应的最低分阈值
    PRIORITY_THRESHOLDS = {
        'P1': 85,  # 最高优先级
        'P2': 75,
        'P3': 65,
        'P4': 55,
        'P5': 50   # 最低优先级
    }

    @classmethod
    def get_priority_threshold(cls, priority: str) -> int:
        """获取优先级对应的最低分阈值"""
        return cls.PRIORITY_THRESHOLDS.get(priority, 65)

    @classmethod
    def classify_recommendation(cls, total_score: float, threshold: int) -> str:
        """根据得分和阈值分类推荐类型"""
        if total_score >= threshold + 15:
            return RecommendationTypeEnum.STRONG.value
        elif total_score >= threshold:
            return RecommendationTypeEnum.RECOMMENDED.value
        elif total_score >= threshold - 10:
            return RecommendationTypeEnum.ACCEPTABLE.value
        else:
            return RecommendationTypeEnum.WEAK.value

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
        ).filter(Employee.is_active == True)

        # 如果不包含超负荷员工，过滤工作负载
        if not include_overloaded:
            required_allocation = float(staffing_need.allocation_pct or 100)
            # 员工当前负载 + 需求分配比例 <= 100%，或者没有档案记录的员工
            query = query.filter(
                or_(
                    HrEmployeeProfile.id == None,  # 没有档案的员工（假设可用）
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
        skill_result = cls._calculate_skill_score(
            db, employee.id, profile,
            staffing_need.required_skills or [],
            staffing_need.preferred_skills or []
        )
        scores['skill'] = skill_result['score']
        scores['matched_skills'] = skill_result.get('matched', [])
        scores['missing_skills'] = skill_result.get('missing', [])

        # 2. 计算领域匹配分
        scores['domain'] = cls._calculate_domain_score(
            db, employee.id, profile,
            staffing_need.required_domains or []
        )

        # 3. 计算态度评分
        scores['attitude'] = cls._calculate_attitude_score(
            db, employee.id, profile,
            staffing_need.required_attitudes or []
        )

        # 4. 计算质量评分（从历史绩效）
        scores['quality'] = cls._calculate_quality_score(db, employee.id)

        # 5. 计算工作负载分
        scores['workload'] = cls._calculate_workload_score(
            profile, float(staffing_need.allocation_pct or 100)
        )

        # 6. 计算特殊能力分
        scores['special'] = cls._calculate_special_score(db, employee.id, profile)

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

    @classmethod
    def _calculate_skill_score(
        cls,
        db: Session,
        employee_id: int,
        profile: Optional[HrEmployeeProfile],
        required_skills: List[dict],
        preferred_skills: List[dict]
    ) -> Dict:
        """
        计算技能匹配分 (0-100)
        - 必需技能: 加权平均，占80分
        - 优选技能: 每个5分奖励，最多20分
        """
        result = {'score': 0.0, 'matched': [], 'missing': []}

        if not required_skills:
            # 没有技能要求，给60分基础分
            return {'score': 60.0, 'matched': [], 'missing': []}

        # 获取员工的技能评估
        employee_skills = {}
        skill_evals = db.query(HrEmployeeTagEvaluation).join(HrTagDict).filter(
            HrEmployeeTagEvaluation.employee_id == employee_id,
            HrEmployeeTagEvaluation.is_valid == True,
            HrTagDict.tag_type == TagTypeEnum.SKILL.value
        ).all()

        for eval in skill_evals:
            employee_skills[eval.tag_id] = {
                'score': eval.score,
                'tag_name': eval.tag.tag_name if eval.tag else ''
            }

        # 计算必需技能分数
        required_score = 0.0
        total_weight = 0.0
        for req in required_skills:
            tag_id = req.get('tag_id')
            min_score = req.get('min_score', 3)
            tag_name = req.get('tag_name', '')

            if tag_id in employee_skills:
                emp_score = employee_skills[tag_id]['score']
                # 计算得分比例
                score_ratio = min(emp_score / 5.0, 1.0)  # 最高5分
                if emp_score >= min_score:
                    required_score += score_ratio * 100
                    result['matched'].append(employee_skills[tag_id]['tag_name'] or tag_name)
                else:
                    required_score += score_ratio * 50  # 未达标减半
                    result['missing'].append(f"{tag_name}(需{min_score}分,实{emp_score}分)")
            else:
                result['missing'].append(tag_name or f"Tag-{tag_id}")
            total_weight += 1

        # 归一化必需技能分数 (最高80分)
        if total_weight > 0:
            base_score = (required_score / total_weight) * 0.8
        else:
            base_score = 60.0

        # 计算优选技能奖励 (最多20分)
        bonus_score = 0.0
        if preferred_skills:
            for pref in preferred_skills[:4]:  # 最多4个优选技能
                tag_id = pref.get('tag_id')
                if tag_id in employee_skills and employee_skills[tag_id]['score'] >= 3:
                    bonus_score += 5.0

        result['score'] = min(100, base_score + bonus_score)
        return result

    @classmethod
    def _calculate_domain_score(
        cls,
        db: Session,
        employee_id: int,
        profile: Optional[HrEmployeeProfile],
        required_domains: List[dict]
    ) -> float:
        """计算领域匹配分 (0-100)"""
        if not required_domains:
            return 60.0  # 没有领域要求，给60分基础分

        # 获取员工的领域评估
        domain_evals = db.query(HrEmployeeTagEvaluation).join(HrTagDict).filter(
            HrEmployeeTagEvaluation.employee_id == employee_id,
            HrEmployeeTagEvaluation.is_valid == True,
            HrTagDict.tag_type == TagTypeEnum.DOMAIN.value
        ).all()

        employee_domains = {eval.tag_id: eval.score for eval in domain_evals}

        # 计算匹配分数
        total_score = 0.0
        matched_count = 0
        for req in required_domains:
            tag_id = req.get('tag_id')
            min_score = req.get('min_score', 3)
            if tag_id in employee_domains:
                emp_score = employee_domains[tag_id]
                if emp_score >= min_score:
                    total_score += (emp_score / 5.0) * 100
                else:
                    total_score += (emp_score / 5.0) * 50
                matched_count += 1

        if len(required_domains) > 0:
            return total_score / len(required_domains)
        return 60.0

    @classmethod
    def _calculate_attitude_score(
        cls,
        db: Session,
        employee_id: int,
        profile: Optional[HrEmployeeProfile],
        required_attitudes: List[dict]
    ) -> float:
        """计算态度评分 (0-100)"""
        # 先尝试从档案获取聚合态度分
        if profile and profile.attitude_score:
            base_score = float(profile.attitude_score)
        else:
            # 从评估记录计算
            attitude_evals = db.query(HrEmployeeTagEvaluation).join(HrTagDict).filter(
                HrEmployeeTagEvaluation.employee_id == employee_id,
                HrEmployeeTagEvaluation.is_valid == True,
                HrTagDict.tag_type == TagTypeEnum.ATTITUDE.value
            ).all()

            if attitude_evals:
                avg_score = sum(eval.score for eval in attitude_evals) / len(attitude_evals)
                base_score = (avg_score / 5.0) * 100
            else:
                base_score = 60.0  # 没有评估记录，给60分基础分

        # 如果有特定态度要求，检查匹配度
        if required_attitudes:
            employee_attitudes = {}
            evals = db.query(HrEmployeeTagEvaluation).filter(
                HrEmployeeTagEvaluation.employee_id == employee_id,
                HrEmployeeTagEvaluation.is_valid == True
            ).all()
            for eval in evals:
                employee_attitudes[eval.tag_id] = eval.score

            match_bonus = 0
            for req in required_attitudes:
                tag_id = req.get('tag_id')
                min_score = req.get('min_score', 3)
                if tag_id in employee_attitudes and employee_attitudes[tag_id] >= min_score:
                    match_bonus += 5

            base_score = min(100, base_score + match_bonus)

        return base_score

    @classmethod
    def _calculate_quality_score(cls, db: Session, employee_id: int) -> float:
        """
        计算质量评分 (0-100)
        基于历史项目绩效
        """
        # 获取员工的历史项目绩效
        performances = db.query(HrProjectPerformance).filter(
            HrProjectPerformance.employee_id == employee_id
        ).all()

        if not performances:
            return 60.0  # 没有历史绩效，给60分基础分

        # 计算加权平均分
        total_score = 0.0
        total_weight = 0.0
        for perf in performances:
            # 贡献等级权重
            level_weights = {'CORE': 1.5, 'MAJOR': 1.2, 'NORMAL': 1.0, 'MINOR': 0.8}
            weight = level_weights.get(perf.contribution_level, 1.0)

            # 综合得分 = (绩效分 + 质量分 + 协作分) / 3
            scores = []
            if perf.performance_score:
                scores.append(float(perf.performance_score))
            if perf.quality_score:
                scores.append(float(perf.quality_score))
            if perf.collaboration_score:
                scores.append(float(perf.collaboration_score))

            if scores:
                avg = sum(scores) / len(scores)
                total_score += avg * weight
                total_weight += weight

        if total_weight > 0:
            return min(100, total_score / total_weight)
        return 60.0

    @classmethod
    def _calculate_workload_score(
        cls,
        profile: Optional[HrEmployeeProfile],
        required_allocation: float
    ) -> float:
        """
        计算工作负载分 (0-100)
        基于当前工作负载和需求分配比例
        """
        if not profile:
            return 80.0  # 没有档案记录，假设80%可用

        current_workload = float(profile.current_workload_pct or 0)
        available = 100 - current_workload

        if available >= required_allocation:
            # 完全可用
            return 100.0
        elif available >= required_allocation * 0.8:
            # 基本可用 (80%以上)
            return 80.0
        elif available >= required_allocation * 0.5:
            # 部分可用
            return 50.0
        elif available > 0:
            # 有限可用
            return (available / required_allocation) * 100
        else:
            # 不可用
            return 0.0

    @classmethod
    def _calculate_special_score(
        cls,
        db: Session,
        employee_id: int,
        profile: Optional[HrEmployeeProfile]
    ) -> float:
        """
        计算特殊能力分 (0-100)
        """
        # 获取员工的特殊能力评估
        special_evals = db.query(HrEmployeeTagEvaluation).join(HrTagDict).filter(
            HrEmployeeTagEvaluation.employee_id == employee_id,
            HrEmployeeTagEvaluation.is_valid == True,
            HrTagDict.tag_type == TagTypeEnum.SPECIAL.value
        ).all()

        if not special_evals:
            return 50.0  # 没有特殊能力，给50分基础分

        # 有特殊能力加分
        total_score = 50.0
        for eval in special_evals:
            # 每个特殊能力根据评分加分
            bonus = (eval.score / 5.0) * 10  # 最高10分/项
            total_score += bonus

        return min(100, total_score)

    @classmethod
    def aggregate_employee_profile(cls, db: Session, employee_id: int) -> HrEmployeeProfile:
        """
        聚合员工标签到档案
        """
        # 获取或创建档案
        profile = db.query(HrEmployeeProfile).filter(
            HrEmployeeProfile.employee_id == employee_id
        ).first()

        if not profile:
            profile = HrEmployeeProfile(employee_id=employee_id)
            db.add(profile)

        # 按类型聚合标签
        tag_types = [
            (TagTypeEnum.SKILL.value, 'skill_tags'),
            (TagTypeEnum.DOMAIN.value, 'domain_tags'),
            (TagTypeEnum.ATTITUDE.value, 'attitude_tags'),
            (TagTypeEnum.CHARACTER.value, 'character_tags'),
            (TagTypeEnum.SPECIAL.value, 'special_tags')
        ]

        for tag_type, field_name in tag_types:
            evals = db.query(HrEmployeeTagEvaluation).join(HrTagDict).filter(
                HrEmployeeTagEvaluation.employee_id == employee_id,
                HrEmployeeTagEvaluation.is_valid == True,
                HrTagDict.tag_type == tag_type
            ).all()

            tags_data = []
            for eval in evals:
                tags_data.append({
                    'tag_id': eval.tag_id,
                    'tag_code': eval.tag.tag_code if eval.tag else '',
                    'tag_name': eval.tag.tag_name if eval.tag else '',
                    'score': eval.score,
                    'weight': float(eval.tag.weight) if eval.tag else 1.0
                })

            setattr(profile, field_name, tags_data)

        # 计算态度聚合分
        attitude_evals = db.query(HrEmployeeTagEvaluation).join(HrTagDict).filter(
            HrEmployeeTagEvaluation.employee_id == employee_id,
            HrEmployeeTagEvaluation.is_valid == True,
            HrTagDict.tag_type == TagTypeEnum.ATTITUDE.value
        ).all()

        if attitude_evals:
            avg_attitude = sum(e.score for e in attitude_evals) / len(attitude_evals)
            profile.attitude_score = Decimal(str(round((avg_attitude / 5.0) * 100, 2)))

        # 计算质量聚合分（从项目绩效）
        performances = db.query(HrProjectPerformance).filter(
            HrProjectPerformance.employee_id == employee_id
        ).all()

        if performances:
            quality_scores = [float(p.quality_score) for p in performances if p.quality_score]
            if quality_scores:
                profile.quality_score = Decimal(str(round(sum(quality_scores) / len(quality_scores), 2)))

            # 统计项目数
            profile.total_projects = len(performances)

            # 计算平均绩效
            perf_scores = [float(p.performance_score) for p in performances if p.performance_score]
            if perf_scores:
                profile.avg_performance_score = Decimal(str(round(sum(perf_scores) / len(perf_scores), 2)))

        profile.profile_updated_at = datetime.now()
        db.commit()

        return profile

    @classmethod
    def update_employee_workload(cls, db: Session, employee_id: int) -> None:
        """
        更新员工当前工作负载
        基于ProjectMember的分配比例
        """
        # 获取或创建档案
        profile = db.query(HrEmployeeProfile).filter(
            HrEmployeeProfile.employee_id == employee_id
        ).first()

        if not profile:
            profile = HrEmployeeProfile(employee_id=employee_id)
            db.add(profile)

        # 获取员工关联的User
        from app.models.user import User
        user = db.query(User).filter(User.employee_id == employee_id).first()

        if user:
            # 计算当前活跃项目的分配比例总和
            today = datetime.now().date()
            active_assignments = db.query(ProjectMember).filter(
                ProjectMember.user_id == user.id,
                ProjectMember.is_active == True,
                or_(
                    ProjectMember.end_date == None,
                    ProjectMember.end_date >= today
                )
            ).all()

            total_allocation = sum(
                float(a.allocation_pct or 0) for a in active_assignments
            )
            profile.current_workload_pct = Decimal(str(min(100, total_allocation)))

            # 计算可用工时 (假设每月160小时)
            available_pct = max(0, 100 - total_allocation)
            profile.available_hours = Decimal(str(round(160 * available_pct / 100, 2)))

        profile.profile_updated_at = datetime.now()
        db.commit()

    @classmethod
    def accept_candidate(
        cls,
        db: Session,
        matching_log_id: int,
        acceptor_id: int
    ) -> bool:
        """采纳候选人"""
        log = db.query(HrAIMatchingLog).filter(HrAIMatchingLog.id == matching_log_id).first()
        if not log:
            return False

        log.is_accepted = True
        log.accept_time = datetime.now()
        log.acceptor_id = acceptor_id

        # 更新需求的已填充人数
        staffing_need = db.query(MesProjectStaffingNeed).filter(
            MesProjectStaffingNeed.id == log.staffing_need_id
        ).first()

        if staffing_need:
            staffing_need.filled_count = (staffing_need.filled_count or 0) + 1
            if staffing_need.filled_count >= staffing_need.headcount:
                staffing_need.status = 'FILLED'

        db.commit()
        return True

    @classmethod
    def reject_candidate(
        cls,
        db: Session,
        matching_log_id: int,
        reject_reason: str
    ) -> bool:
        """拒绝候选人"""
        log = db.query(HrAIMatchingLog).filter(HrAIMatchingLog.id == matching_log_id).first()
        if not log:
            return False

        log.is_accepted = False
        log.reject_reason = reject_reason
        db.commit()
        return True

    @classmethod
    def get_matching_history(
        cls,
        db: Session,
        project_id: Optional[int] = None,
        staffing_need_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        limit: int = 50
    ) -> List[HrAIMatchingLog]:
        """获取匹配历史"""
        query = db.query(HrAIMatchingLog)

        if project_id:
            query = query.filter(HrAIMatchingLog.project_id == project_id)
        if staffing_need_id:
            query = query.filter(HrAIMatchingLog.staffing_need_id == staffing_need_id)
        if employee_id:
            query = query.filter(HrAIMatchingLog.candidate_employee_id == employee_id)

        return query.order_by(HrAIMatchingLog.matching_time.desc()).limit(limit).all()
