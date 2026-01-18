# -*- coding: utf-8 -*-
"""
人员智能匹配服务 - 各维度得分计算
"""

from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Employee
from app.models.staff_matching import (
    HrEmployeeProfile,
    HrEmployeeTagEvaluation,
    HrProjectPerformance,
    HrTagDict,
    TagTypeEnum,
)

from .base import StaffMatchingBase


class SkillScoreCalculator(StaffMatchingBase):
    """技能匹配分计算器"""

    @classmethod
    def calculate_skill_score(
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


class DomainScoreCalculator(StaffMatchingBase):
    """领域匹配分计算器"""

    @classmethod
    def calculate_domain_score(
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


class AttitudeScoreCalculator(StaffMatchingBase):
    """态度评分计算器"""

    @classmethod
    def calculate_attitude_score(
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


class QualityScoreCalculator(StaffMatchingBase):
    """质量评分计算器"""

    @classmethod
    def calculate_quality_score(cls, db: Session, employee_id: int) -> float:
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


class WorkloadScoreCalculator(StaffMatchingBase):
    """工作负载分计算器"""

    @classmethod
    def calculate_workload_score(
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


class SpecialScoreCalculator(StaffMatchingBase):
    """特殊能力分计算器"""

    @classmethod
    def calculate_special_score(
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
