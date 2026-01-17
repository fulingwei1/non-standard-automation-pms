# -*- coding: utf-8 -*-
"""
绩效计算服务
负责各岗位工程师的绩效得分计算
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.engineer_performance import (
    CodeModule,
    CollaborationRating,
    DesignReview,
    EngineerDimensionConfig,
    KnowledgeContribution,
    MechanicalDebugIssue,
    PlcModuleLibrary,
    PlcProgramVersion,
    TestBugRecord,
)
from app.models.performance import PerformancePeriod
from app.schemas.engineer_performance import EngineerDimensionScore


class PerformanceCalculator:
    """绩效计算服务"""

    # 等级划分规则
    GRADE_RULES = {
        'S': (85, 100),   # 优秀
        'A': (70, 84),    # 良好
        'B': (60, 69),    # 合格
        'C': (40, 59),    # 待改进
        'D': (0, 39),     # 不合格
    }

    def __init__(self, db: Session):
        self.db = db

    def calculate_grade(self, score: Decimal) -> str:
        """根据分数计算等级"""
        score_int = int(score)
        for grade, (min_score, max_score) in self.GRADE_RULES.items():
            if min_score <= score_int <= max_score:
                return grade
        return 'D'

    def calculate_dimension_score(
        self,
        engineer_id: int,
        period_id: int,
        job_type: str
    ) -> EngineerDimensionScore:
        """计算工程师五维得分"""
        # 获取考核周期
        period = self.db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        # 根据岗位类型调用不同的计算方法
        if job_type == 'mechanical':
            return self._calculate_mechanical_score(engineer_id, period)
        elif job_type == 'test':
            return self._calculate_test_score(engineer_id, period)
        elif job_type == 'electrical':
            return self._calculate_electrical_score(engineer_id, period)
        elif job_type == 'solution':
            return self._calculate_solution_score(engineer_id, period)
        else:
            raise ValueError(f"未知的岗位类型: {job_type}")

    def _calculate_mechanical_score(
        self, engineer_id: int, period: PerformancePeriod
    ) -> EngineerDimensionScore:
        """计算机械工程师五维得分"""
        # 技术能力：设计一次通过率、ECN责任率、调试问题密度
        design_reviews = self.db.query(DesignReview).filter(
            DesignReview.designer_id == engineer_id,
            DesignReview.review_date.between(period.start_date, period.end_date)
        ).all()

        if design_reviews:
            first_pass_count = sum(1 for r in design_reviews if r.is_first_pass)
            first_pass_rate = first_pass_count / len(design_reviews) * 100
        else:
            first_pass_rate = 85  # 默认值

        # 调试问题数量
        debug_issues = self.db.query(MechanicalDebugIssue).filter(
            MechanicalDebugIssue.responsible_id == engineer_id,
            MechanicalDebugIssue.found_date.between(period.start_date, period.end_date)
        ).count()

        # 技术得分计算
        technical_score = min(first_pass_rate / 85 * 100, 120)
        if debug_issues > 0:
            technical_score = max(technical_score - debug_issues * 5, 0)

        # 项目执行：简化计算
        execution_score = Decimal('80')

        # 成本/质量：简化计算
        cost_quality_score = Decimal('75')

        # 知识沉淀
        contributions = self.db.query(KnowledgeContribution).filter(
            KnowledgeContribution.contributor_id == engineer_id,
            KnowledgeContribution.job_type == 'mechanical',
            KnowledgeContribution.status == 'approved',
            KnowledgeContribution.created_at.between(period.start_date, period.end_date)
        ).count()

        knowledge_score = min(50 + contributions * 10, 100)

        # 团队协作
        collaboration_avg = self._get_collaboration_avg(engineer_id, period.id)

        return EngineerDimensionScore(
            technical_score=Decimal(str(round(technical_score, 2))),
            execution_score=execution_score,
            cost_quality_score=cost_quality_score,
            knowledge_score=Decimal(str(knowledge_score)),
            collaboration_score=collaboration_avg
        )

    def _calculate_test_score(
        self, engineer_id: int, period: PerformancePeriod
    ) -> EngineerDimensionScore:
        """计算测试工程师五维得分"""
        # Bug修复统计
        bugs = self.db.query(TestBugRecord).filter(
            TestBugRecord.assignee_id == engineer_id,
            TestBugRecord.found_time.between(period.start_date, period.end_date)
        ).all()

        if bugs:
            resolved_bugs = [b for b in bugs if b.status in ('resolved', 'closed')]
            resolve_rate = len(resolved_bugs) / len(bugs) * 100 if bugs else 100

            # 平均修复时长
            fix_times = [b.fix_duration_hours for b in resolved_bugs if b.fix_duration_hours]
            avg_fix_time = sum(fix_times) / len(fix_times) if fix_times else 4
        else:
            resolve_rate = 100
            avg_fix_time = 4

        # 技术得分
        technical_score = min(resolve_rate, 100)
        if avg_fix_time < 4:
            technical_score = min(technical_score + 10, 120)
        elif avg_fix_time > 8:
            technical_score = max(technical_score - 10, 0)

        # 代码模块贡献
        modules = self.db.query(CodeModule).filter(
            CodeModule.contributor_id == engineer_id,
            CodeModule.created_at.between(period.start_date, period.end_date)
        ).count()

        knowledge_score = min(50 + modules * 15, 100)

        # 团队协作
        collaboration_avg = self._get_collaboration_avg(engineer_id, period.id)

        return EngineerDimensionScore(
            technical_score=Decimal(str(round(technical_score, 2))),
            execution_score=Decimal('80'),
            cost_quality_score=Decimal('75'),
            knowledge_score=Decimal(str(knowledge_score)),
            collaboration_score=collaboration_avg
        )

    def _calculate_electrical_score(
        self, engineer_id: int, period: PerformancePeriod
    ) -> EngineerDimensionScore:
        """计算电气工程师五维得分"""
        # PLC程序调试统计
        plc_programs = self.db.query(PlcProgramVersion).filter(
            PlcProgramVersion.programmer_id == engineer_id,
            PlcProgramVersion.first_debug_date.between(period.start_date, period.end_date)
        ).all()

        if plc_programs:
            first_pass_count = sum(1 for p in plc_programs if p.is_first_pass)
            first_pass_rate = first_pass_count / len(plc_programs) * 100
        else:
            first_pass_rate = 80

        technical_score = min(first_pass_rate / 80 * 100, 120)

        # PLC模块贡献
        modules = self.db.query(PlcModuleLibrary).filter(
            PlcModuleLibrary.contributor_id == engineer_id,
            PlcModuleLibrary.created_at.between(period.start_date, period.end_date)
        ).count()

        knowledge_score = min(50 + modules * 15, 100)

        # 团队协作
        collaboration_avg = self._get_collaboration_avg(engineer_id, period.id)

        return EngineerDimensionScore(
            technical_score=Decimal(str(round(technical_score, 2))),
            execution_score=Decimal('80'),
            cost_quality_score=Decimal('75'),
            knowledge_score=Decimal(str(knowledge_score)),
            collaboration_score=collaboration_avg
        )

    def _calculate_solution_score(
        self, engineer_id: int, period: PerformancePeriod
    ) -> EngineerDimensionScore:
        """计算方案工程师得分（六维：技术能力+方案成功率+项目执行+成本/质量+知识沉淀+团队协作）"""
        from app.models.presale import (
            PresaleSolution,
            PresaleSolutionTemplate,
            PresaleSupportTicket,
        )
        from app.models.sales import Contract

        # 1. 方案成功率维度（30%权重）
        solutions = self.db.query(PresaleSolution).filter(
            PresaleSolution.author_id == engineer_id,
            PresaleSolution.created_at.between(period.start_date, period.end_date)
        ).all()

        if not solutions:
            win_rate_score = Decimal('60.0')  # 默认值
            approval_rate_score = Decimal('60.0')
            quality_score = Decimal('60.0')
        else:
            # 方案中标率（支持高价值方案加权、低价值方案降权）
            won_solutions = []
            high_value_won = 0  # 高价值方案中标数（>200万）
            low_value_won = 0   # 低价值方案中标数（<50万）
            normal_value_won = 0  # 正常价值方案中标数

            for solution in solutions:
                # 检查是否关联了合同（中标）
                contract_amount = Decimal('0')
                if solution.opportunity_id:
                    contract = self.db.query(Contract).filter(
                        Contract.opportunity_id == solution.opportunity_id,
                        Contract.status == 'SIGNED'
                    ).first()
                    if contract:
                        won_solutions.append(solution)
                        contract_amount = contract.contract_amount or Decimal('0')

                        # 分类统计
                        if contract_amount > Decimal('2000000'):  # >200万
                            high_value_won += 1
                        elif contract_amount < Decimal('500000'):  # <50万
                            low_value_won += 1
                        else:
                            normal_value_won += 1

            # 计算加权中标率
            total_won = len(won_solutions)
            if total_won > 0:
                # 高价值方案权重×1.2，低价值方案权重×0.8
                weighted_won = high_value_won * Decimal('1.2') + low_value_won * Decimal('0.8') + normal_value_won
                weighted_win_rate = (weighted_won / len(solutions) * 100) if solutions else 0
            else:
                weighted_win_rate = 0

            win_rate = total_won / len(solutions) * 100 if solutions else 0
            win_rate_score = min(Decimal(str(weighted_win_rate)) / 40 * 100, 120)  # 目标40%，使用加权值

            # 方案通过率
            approved_solutions = [s for s in solutions if s.review_status == 'APPROVED']
            approval_rate = len(approved_solutions) / len(solutions) * 100 if solutions else 0
            approval_rate_score = min(Decimal(str(approval_rate)) / 80 * 100, 120)  # 目标80%

            # 方案质量评分（从工单满意度获取，支持高质量方案补偿）
            ticket_ids = [s.ticket_id for s in solutions if s.ticket_id]
            high_quality_unwon = 0  # 高质量但未中标的方案数
            if ticket_ids:
                tickets = self.db.query(PresaleSupportTicket).filter(
                    PresaleSupportTicket.id.in_(ticket_ids),
                    PresaleSupportTicket.satisfaction_score.isnot(None)
                ).all()
                if tickets:
                    satisfaction_scores = []
                    for ticket in tickets:
                        score = ticket.satisfaction_score
                        satisfaction_scores.append(score)

                        # 检查是否高质量但未中标（质量评分≥4.5但未中标）
                        if score >= 4.5:
                            # 检查对应的方案是否中标
                            solution = next((s for s in solutions if s.ticket_id == ticket.id), None)
                            if solution and solution not in won_solutions:
                                high_quality_unwon += 1

                    avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
                    quality_score = Decimal(str(avg_satisfaction)) / 5 * 100  # 5分制转百分制
                else:
                    quality_score = Decimal('75.0')
            else:
                quality_score = Decimal('75.0')

            # 高质量方案补偿（未中标但质量评分≥4.5，给予50%基础分补偿）
            if high_quality_unwon > 0:
                compensation = Decimal(str(high_quality_unwon)) * Decimal('0.5') * Decimal('10')  # 每个补偿5分
                quality_score = min(quality_score + compensation, 100)

        solution_success_score = (
            win_rate_score * Decimal('0.5') +
            approval_rate_score * Decimal('0.3') +
            quality_score * Decimal('0.2')
        )

        # 2. 技术能力维度（25%权重）
        # 方案技术可行性（从交付项目的ECN记录统计）
        # 简化计算，使用方案通过率作为技术能力指标
        technical_score = approval_rate_score

        # 3. 项目执行维度（20%权重）
        # 方案交付及时率
        on_time_solutions = sum(
            1 for s in solutions
            if s.ticket_id and s.created_at
        )
        delivery_rate = on_time_solutions / len(solutions) * 100 if solutions else 90
        execution_score = Decimal(str(min(delivery_rate / 90 * 100, 120)))  # 目标90%

        # 4. 成本/质量维度（使用cost_quality_score，但方案工程师权重较低）
        cost_quality_score = Decimal('75.0')  # 简化计算

        # 5. 知识沉淀维度（15%权重）
        # 方案模板贡献
        templates = self.db.query(PresaleSolutionTemplate).filter(
            PresaleSolutionTemplate.created_by == engineer_id,
            PresaleSolutionTemplate.created_at.between(period.start_date, period.end_date)
        ).count()

        knowledge_score = min(Decimal('50') + Decimal(str(templates)) * Decimal('15'), 100)

        # 6. 团队协作维度（10%权重）
        collaboration_avg = self._get_collaboration_avg(engineer_id, period.id)

        return EngineerDimensionScore(
            technical_score=technical_score,
            execution_score=execution_score,
            cost_quality_score=cost_quality_score,
            knowledge_score=knowledge_score,
            collaboration_score=collaboration_avg,
            solution_success_score=solution_success_score
        )

    def _get_collaboration_avg(self, engineer_id: int, period_id: int) -> Decimal:
        """获取协作评价平均分"""
        ratings = self.db.query(CollaborationRating).filter(
            CollaborationRating.ratee_id == engineer_id,
            CollaborationRating.period_id == period_id
        ).all()

        if not ratings:
            return Decimal('75')

        total = sum(
            (r.communication_score or 0) + (r.response_score or 0) +
            (r.delivery_score or 0) + (r.interface_score or 0)
            for r in ratings
        )
        avg = total / (len(ratings) * 4) * 20  # 转换为百分制
        return Decimal(str(round(avg, 2)))

    def calculate_total_score(
        self,
        dimension_scores: EngineerDimensionScore,
        config: EngineerDimensionConfig,
        job_type: Optional[str] = None
    ) -> Decimal:
        """计算加权总分（支持方案工程师的方案成功率维度）"""
        # 如果是方案工程师，使用特殊权重
        if job_type == 'solution' and dimension_scores.solution_success_score is not None:
            # 方案工程师权重：技术能力25% + 方案成功率30% + 项目执行20% + 知识沉淀15% + 团队协作10%
            total = (
                dimension_scores.technical_score * 25 / 100 +
                dimension_scores.solution_success_score * 30 / 100 +
                dimension_scores.execution_score * 20 / 100 +
                dimension_scores.knowledge_score * 15 / 100 +
                dimension_scores.collaboration_score * 10 / 100
            )
        else:
            # 其他工程师使用配置的权重
            total = (
                dimension_scores.technical_score * config.technical_weight / 100 +
                dimension_scores.execution_score * config.execution_weight / 100 +
                dimension_scores.cost_quality_score * config.cost_quality_weight / 100 +
                dimension_scores.knowledge_score * config.knowledge_weight / 100 +
                dimension_scores.collaboration_score * config.collaboration_weight / 100
            )

        return Decimal(str(round(total, 2)))
