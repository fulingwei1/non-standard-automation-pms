# -*- coding: utf-8 -*-
"""
项目评价服务
提供项目评价计算、自动评分等功能
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.enums import ProjectEvaluationLevelEnum
from app.models.project import Project
from app.models.project_evaluation import ProjectEvaluation, ProjectEvaluationDimension


class ProjectEvaluationService:
    """项目评价服务"""

    # 默认权重配置（仅作为后备，优先从数据库读取）
    DEFAULT_WEIGHTS = {
        'novelty': Decimal('0.15'),      # 项目新旧 15%
        'new_tech': Decimal('0.20'),     # 新技术 20%
        'difficulty': Decimal('0.30'),    # 难度 30%
        'workload': Decimal('0.20'),     # 工作量 20%
        'amount': Decimal('0.15')        # 金额 15%
    }

    # 默认评价等级阈值（仅作为后备，优先从数据库读取）
    DEFAULT_LEVEL_THRESHOLDS = {
        ProjectEvaluationLevelEnum.S: Decimal('90'),
        ProjectEvaluationLevelEnum.A: Decimal('80'),
        ProjectEvaluationLevelEnum.B: Decimal('70'),
        ProjectEvaluationLevelEnum.C: Decimal('60'),
        ProjectEvaluationLevelEnum.D: Decimal('0')
    }

    def __init__(self, db: Session):
        self.db = db

    def get_dimension_weights(self) -> Dict[str, Decimal]:
        """
        从数据库获取各维度的权重配置

        Returns:
            Dict[str, Decimal]: 权重配置字典
        """
        dimensions = self.db.query(ProjectEvaluationDimension).filter(
            ProjectEvaluationDimension.is_active == True
        ).all()

        if not dimensions:
            # 如果没有配置，返回默认值
            return self.DEFAULT_WEIGHTS

        weights = {}
        total_weight = Decimal('0')

        for dim in dimensions:
            if dim.default_weight:
                weight_decimal = dim.default_weight / Decimal('100')  # 转换为小数
                weights[dim.dimension_type.lower()] = weight_decimal
                total_weight += weight_decimal

        # 如果权重总和不为1，进行归一化
        if total_weight > 0 and total_weight != Decimal('1'):
            for key in weights:
                weights[key] = weights[key] / total_weight

        return weights

    def get_level_thresholds(self) -> Dict[ProjectEvaluationLevelEnum, Decimal]:
        """
        从数据库获取评价等级阈值配置

        首先尝试从 ProjectEvaluationDimension 表中查找 dimension_code='LEVEL_THRESHOLDS' 的配置，
        如果不存在则使用默认值。

        Returns:
            Dict[ProjectEvaluationLevelEnum, Decimal]: 等级阈值字典
        """
        # 尝试从数据库获取等级阈值配置
        config = self.db.query(ProjectEvaluationDimension).filter(
            ProjectEvaluationDimension.dimension_code == 'LEVEL_THRESHOLDS'
        ).first()

        if config and config.scoring_rules:
            try:
                rules = config.scoring_rules
                thresholds = {}
                level_mapping = {
                    'S': ProjectEvaluationLevelEnum.S,
                    'A': ProjectEvaluationLevelEnum.A,
                    'B': ProjectEvaluationLevelEnum.B,
                    'C': ProjectEvaluationLevelEnum.C,
                    'D': ProjectEvaluationLevelEnum.D
                }
                for level, enum_val in level_mapping.items():
                    if level in rules:
                        thresholds[enum_val] = Decimal(str(rules[level]))
                if thresholds:
                    return thresholds
            except (KeyError, ValueError, TypeError):
                pass  # 配置格式错误，使用默认值

        return self.DEFAULT_LEVEL_THRESHOLDS

    def calculate_total_score(
        self,
        novelty_score: Decimal,
        new_tech_score: Decimal,
        difficulty_score: Decimal,
        workload_score: Decimal,
        amount_score: Decimal,
        weights: Optional[Dict[str, Decimal]] = None
    ) -> Decimal:
        """
        计算综合得分（加权平均）

        Args:
            novelty_score: 项目新旧得分
            new_tech_score: 新技术得分
            difficulty_score: 难度得分
            workload_score: 工作量得分
            amount_score: 金额得分
            weights: 权重配置（可选）

        Returns:
            Decimal: 综合得分
        """
        if weights is None:
            weights = self.get_dimension_weights()

        total = (
            novelty_score * weights.get('novelty', Decimal('0.15')) +
            new_tech_score * weights.get('new_tech', Decimal('0.20')) +
            difficulty_score * weights.get('difficulty', Decimal('0.30')) +
            workload_score * weights.get('workload', Decimal('0.20')) +
            amount_score * weights.get('amount', Decimal('0.15'))
        )

        return total

    def determine_evaluation_level(self, total_score: Decimal) -> str:
        """
        根据综合得分确定评价等级

        Args:
            total_score: 综合得分

        Returns:
            str: 评价等级
        """
        thresholds = self.get_level_thresholds()
        for level, threshold in sorted(thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                return level.value
        return ProjectEvaluationLevelEnum.D.value

    def auto_calculate_novelty_score(self, project: Project) -> Optional[Decimal]:
        """
        自动计算项目新旧得分

        规则：
        - 查询历史相似项目（基于项目类型、产品类别、行业）
        - 如果找到完全相同的项目类型且做过3次以上：10分
        - 如果找到类似项目且做过1-2次：7-9分
        - 如果找到类似项目但未完成：4-6分
        - 如果未找到相似项目：1-3分

        Args:
            project: 项目对象

        Returns:
            Optional[Decimal]: 得分（如果无法自动计算则返回None）
        """
        # 查询历史相似项目
        similar_projects = self.db.query(Project).filter(
            Project.id != project.id,
            Project.is_archived == True,  # 只查询已归档的项目
            or_(
                Project.project_type == project.project_type,
                Project.product_category == project.product_category,
                Project.industry == project.industry
            )
        ).all()

        if not similar_projects:
            # 未找到相似项目，全新项目
            return Decimal('2.0')  # 1-3分，取中值

        # 统计相似项目数量
        similar_count = len(similar_projects)

        # 统计已完成的项目数量
        completed_count = sum(1 for p in similar_projects if p.stage == 'S9')

        if completed_count >= 3:
            # 做过3次以上，标准项目
            return Decimal('9.0')
        elif completed_count >= 1:
            # 做过1-2次，类似项目
            return Decimal('6.0')
        else:
            # 有类似项目但未完成，有一定经验
            return Decimal('4.0')

    def auto_calculate_amount_score(self, project: Project) -> Optional[Decimal]:
        """
        自动计算项目金额得分

        规则：
        - >500万：1-3分（超大项目）
        - 200-500万：4-6分（大项目）
        - 50-200万：7-8分（中等项目）
        - <50万：9-10分（小项目）

        Args:
            project: 项目对象

        Returns:
            Optional[Decimal]: 得分
        """
        amount = project.contract_amount or Decimal('0')

        if amount >= Decimal('5000000'):
            return Decimal('2.0')  # 1-3分
        elif amount >= Decimal('2000000'):
            return Decimal('5.0')  # 4-6分
        elif amount >= Decimal('500000'):
            return Decimal('7.5')  # 7-8分
        else:
            return Decimal('9.5')  # 9-10分

    def auto_calculate_workload_score(self, project: Project) -> Optional[Decimal]:
        """
        自动计算项目工作量得分

        规则：
        - 基于预估工时或实际工时
        - >1000人天：1-3分
        - 500-1000人天：4-6分
        - 200-500人天：7-8分
        - <200人天：9-10分

        Args:
            project: 项目对象

        Returns:
            Optional[Decimal]: 得分（如果无法计算则返回None）
        """
        from sqlalchemy import func

        from app.models.timesheet import Timesheet

        # 查询项目的总工时（小时）
        total_hours_result = self.db.query(
            func.coalesce(func.sum(Timesheet.total_hours), 0)
        ).filter(
            Timesheet.project_id == project.id
        ).scalar()

        if total_hours_result and total_hours_result > 0:
            # 将工时转换为人天（8小时/天）
            total_days = float(total_hours_result) / 8

            # 根据人天数计算得分
            if total_days > 1000:
                return Decimal('2')  # 1-3分，取中间值
            elif total_days >= 500:
                return Decimal('5')  # 4-6分
            elif total_days >= 200:
                return Decimal('7.5')  # 7-8分
            else:
                return Decimal('9.5')  # 9-10分

        # 如果没有工时数据，返回None需要手动评价
        return None

    def generate_evaluation_code(self) -> str:
        """生成评价编号"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"PE{timestamp}"

    def create_evaluation(
        self,
        project_id: int,
        novelty_score: Decimal,
        new_tech_score: Decimal,
        difficulty_score: Decimal,
        workload_score: Decimal,
        amount_score: Decimal,
        evaluator_id: int,
        evaluator_name: str,
        weights: Optional[Dict[str, Decimal]] = None,
        evaluation_detail: Optional[Dict[str, Any]] = None,
        evaluation_note: Optional[str] = None
    ) -> ProjectEvaluation:
        """
        创建项目评价记录

        Args:
            project_id: 项目ID
            novelty_score: 项目新旧得分
            new_tech_score: 新技术得分
            difficulty_score: 难度得分
            workload_score: 工作量得分
            amount_score: 金额得分
            evaluator_id: 评价人ID
            evaluator_name: 评价人姓名
            weights: 权重配置
            evaluation_detail: 评价详情
            evaluation_note: 评价说明

        Returns:
            ProjectEvaluation: 评价记录
        """
        # 计算综合得分
        total_score = self.calculate_total_score(
            novelty_score, new_tech_score, difficulty_score,
            workload_score, amount_score, weights
        )

        # 确定评价等级
        evaluation_level = self.determine_evaluation_level(total_score)

        # 如果没有提供权重，从数据库获取
        if weights is None:
            weights = self.get_dimension_weights()

        # 创建评价记录
        evaluation = ProjectEvaluation(
            evaluation_code=self.generate_evaluation_code(),
            project_id=project_id,
            novelty_score=novelty_score,
            new_tech_score=new_tech_score,
            difficulty_score=difficulty_score,
            workload_score=workload_score,
            amount_score=amount_score,
            total_score=total_score,
            evaluation_level=evaluation_level,
            weights=weights,
            evaluation_detail=evaluation_detail,
            evaluation_note=evaluation_note,
            evaluator_id=evaluator_id,
            evaluator_name=evaluator_name,
            evaluation_date=date.today(),
            status='DRAFT'
        )

        return evaluation

    def get_latest_evaluation(self, project_id: int) -> Optional[ProjectEvaluation]:
        """
        获取项目最新评价

        Args:
            project_id: 项目ID

        Returns:
            Optional[ProjectEvaluation]: 最新评价记录
        """
        return self.db.query(ProjectEvaluation).filter(
            ProjectEvaluation.project_id == project_id,
            ProjectEvaluation.status == 'CONFIRMED'
        ).order_by(ProjectEvaluation.evaluation_date.desc()).first()

    def get_bonus_coefficient(self, project: Project) -> Decimal:
        """
        根据项目评价获取奖金系数

        用于奖金计算时调整奖金金额

        Args:
            project: 项目对象

        Returns:
            Decimal: 奖金系数（默认1.0）
        """
        evaluation = self.get_latest_evaluation(project.id)
        if not evaluation:
            return Decimal('1.0')

        # 根据评价等级确定系数
        coefficient_map = {
            ProjectEvaluationLevelEnum.S: Decimal('1.5'),  # S级项目：1.5倍
            ProjectEvaluationLevelEnum.A: Decimal('1.3'),  # A级项目：1.3倍
            ProjectEvaluationLevelEnum.B: Decimal('1.1'),  # B级项目：1.1倍
            ProjectEvaluationLevelEnum.C: Decimal('1.0'),  # C级项目：1.0倍
            ProjectEvaluationLevelEnum.D: Decimal('0.9')   # D级项目：0.9倍
        }

        level = evaluation.evaluation_level
        return coefficient_map.get(level, Decimal('1.0'))

    def get_difficulty_bonus_coefficient(self, project: Project) -> Decimal:
        """
        根据项目难度获取奖金系数

        专门用于难度奖金计算

        Args:
            project: 项目对象

        Returns:
            Decimal: 难度系数
        """
        evaluation = self.get_latest_evaluation(project.id)
        if not evaluation or not evaluation.difficulty_score:
            return Decimal('1.0')

        difficulty_score = float(evaluation.difficulty_score)

        # 难度得分越低，系数越高（难度越大，奖金越多）
        if difficulty_score <= 3:
            return Decimal('1.5')  # 极高难度
        elif difficulty_score <= 6:
            return Decimal('1.3')  # 高难度
        elif difficulty_score <= 8:
            return Decimal('1.1')  # 中等难度
        else:
            return Decimal('1.0')  # 低难度

    def get_new_tech_bonus_coefficient(self, project: Project) -> Decimal:
        """
        根据新技术使用情况获取奖金系数

        使用新技术越多，奖金系数越高

        Args:
            project: 项目对象

        Returns:
            Decimal: 新技术系数
        """
        evaluation = self.get_latest_evaluation(project.id)
        if not evaluation or not evaluation.new_tech_score:
            return Decimal('1.0')

        new_tech_score = float(evaluation.new_tech_score)

        # 新技术得分越低，系数越高（新技术越多，奖金越多）
        if new_tech_score <= 3:
            return Decimal('1.4')  # 大量新技术
        elif new_tech_score <= 6:
            return Decimal('1.2')  # 部分新技术
        else:
            return Decimal('1.0')  # 少量或无新技术

