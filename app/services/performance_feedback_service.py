# -*- coding: utf-8 -*-
"""
绩效反馈服务
定期向工程师展示个人五维得分和排名变化
"""

from typing import Any, Dict, List

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.engineer_performance import EngineerProfile
from app.models.performance import PerformancePeriod, PerformanceResult


class PerformanceFeedbackService:
    """绩效反馈服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_engineer_feedback(self, engineer_id: int, period_id: int) -> Dict[str, Any]:
        """
        获取工程师绩效反馈

        Returns:
            包含五维得分、排名变化、亮点和改进建议的反馈信息
        """
        period = self.db.query(PerformancePeriod).filter(PerformancePeriod.id == period_id).first()

        if not period:
            raise ValueError(f"考核周期不存在: {period_id}")

        result = (
            self.db.query(PerformanceResult)
            .filter(
                PerformanceResult.user_id == engineer_id, PerformanceResult.period_id == period_id
            )
            .first()
        )

        if not result:
            return {
                "engineer_id": engineer_id,
                "period_id": period_id,
                "message": "绩效数据尚未计算",
                "has_data": False,
            }

        # 获取历史排名（用于对比）
        previous_result = (
            self.db.query(PerformanceResult)
            .join(PerformancePeriod, PerformanceResult.period_id == PerformancePeriod.id)
            .filter(
                PerformanceResult.user_id == engineer_id,
                PerformancePeriod.end_date < period.start_date,
            )
            .order_by(desc(PerformancePeriod.end_date))
            .first()
        )

        # 获取五维得分（从indicator_scores或重新计算）
        from app.models.engineer_performance import EngineerProfile
        from app.services.engineer_performance.engineer_performance_service import (
            EngineerPerformanceService,
        )

        profile = (
            self.db.query(EngineerProfile).filter(EngineerProfile.user_id == engineer_id).first()
        )

        dimension_scores = {}
        if result.indicator_scores:
            # 从JSON字段获取
            scores = result.indicator_scores
            dimension_scores = {
                "technical": float(scores.get("technical_score", 0)),
                "execution": float(scores.get("execution_score", 0)),
                "cost_quality": float(scores.get("cost_quality_score", 0)),
                "knowledge": float(scores.get("knowledge_score", 0)),
                "collaboration": float(scores.get("collaboration_score", 0)),
            }
        elif profile:
            # 重新计算五维得分
            try:
                service = EngineerPerformanceService(self.db)
                dim_score = service.calculate_dimension_score(
                    engineer_id, period_id, profile.job_type
                )
                dimension_scores = {
                    "technical": float(dim_score.technical_score or 0),
                    "execution": float(dim_score.execution_score or 0),
                    "cost_quality": float(dim_score.cost_quality_score or 0),
                    "knowledge": float(dim_score.knowledge_score or 0),
                    "collaboration": float(dim_score.collaboration_score or 0),
                }
                # 如果是方案工程师，添加方案成功率得分
                if profile.job_type == "solution" and dim_score.solution_success_score:
                    dimension_scores["solution_success"] = float(dim_score.solution_success_score)
            except Exception:
                # 如果计算失败，使用默认值
                dimension_scores = {
                    "technical": 75.0,
                    "execution": 75.0,
                    "cost_quality": 75.0,
                    "knowledge": 75.0,
                    "collaboration": 75.0,
                }
        else:
            # 使用默认值
            dimension_scores = {
                "technical": 75.0,
                "execution": 75.0,
                "cost_quality": 75.0,
                "knowledge": 75.0,
                "collaboration": 75.0,
            }

        # 构建反馈信息
        feedback = {
            "engineer_id": engineer_id,
            "period_id": period_id,
            "period_name": period.period_name,
            "has_data": True,
            "current_performance": {
                "total_score": float(result.total_score or 0),
                "level": result.level,
                "dept_rank": result.dept_rank,
                "company_rank": result.company_rank,
                "dimension_scores": dimension_scores,
            },
            "comparison": {},
            "highlights": result.highlights or [],
            "improvements": result.improvements or [],
        }

        # 对比分析（增强版：包含排名变化原因分析）
        if previous_result:
            score_change = float((result.total_score or 0) - (previous_result.total_score or 0))
            rank_change = (result.company_rank or 0) - (previous_result.company_rank or 0)
            dept_rank_change = (result.dept_rank or 0) - (previous_result.dept_rank or 0)

            # 分析排名变化原因（各维度得分变化）
            previous_dim_scores = {}
            if previous_result.indicator_scores:
                prev_scores = previous_result.indicator_scores
                previous_dim_scores = {
                    "technical": float(prev_scores.get("technical_score", 0)),
                    "execution": float(prev_scores.get("execution_score", 0)),
                    "cost_quality": float(prev_scores.get("cost_quality_score", 0)),
                    "knowledge": float(prev_scores.get("knowledge_score", 0)),
                    "collaboration": float(prev_scores.get("collaboration_score", 0)),
                }

            dimension_changes = {}
            for dim in dimension_scores:
                prev_score = previous_dim_scores.get(dim, 75.0)
                curr_score = dimension_scores[dim]
                dimension_changes[dim] = {
                    "change": round(curr_score - prev_score, 2),
                    "previous": round(prev_score, 2),
                    "current": round(curr_score, 2),
                    "trend": (
                        "improving"
                        if curr_score > prev_score
                        else "declining" if curr_score < prev_score else "stable"
                    ),
                }

            # 识别排名变化的主要原因
            rank_change_reasons = []
            if rank_change < 0:  # 排名上升
                # 找出提升最多的维度
                improving_dims = [
                    dim for dim, change in dimension_changes.items() if change["change"] > 0
                ]
                if improving_dims:
                    top_improving = max(
                        improving_dims, key=lambda d: dimension_changes[d]["change"]
                    )
                    rank_change_reasons.append(f"{self._get_dimension_name(top_improving)}提升显著")
            elif rank_change > 0:  # 排名下降
                # 找出下降最多的维度
                declining_dims = [
                    dim for dim, change in dimension_changes.items() if change["change"] < 0
                ]
                if declining_dims:
                    top_declining = min(
                        declining_dims, key=lambda d: dimension_changes[d]["change"]
                    )
                    rank_change_reasons.append(f"{self._get_dimension_name(top_declining)}需要改进")

            feedback["comparison"] = {
                "score_change": score_change,
                "rank_change": rank_change,
                "dept_rank_change": dept_rank_change,
                "level_change": result.level != previous_result.level,
                "previous_score": float(previous_result.total_score or 0),
                "previous_rank": previous_result.company_rank,
                "previous_dept_rank": previous_result.dept_rank,
                "dimension_changes": dimension_changes,
                "rank_change_reasons": rank_change_reasons,
            }

        return feedback

    def _get_dimension_name(self, dimension: str) -> str:
        """获取维度中文名称"""
        names = {
            "technical": "技术能力",
            "execution": "项目执行",
            "cost_quality": "成本/质量",
            "knowledge": "知识沉淀",
            "collaboration": "团队协作",
            "solution_success": "方案成功率",
        }
        return names.get(dimension, dimension)

    def generate_feedback_message(self, engineer_id: int, period_id: int) -> str:
        """
        生成绩效反馈消息（用于通知）

        Returns:
            反馈消息文本
        """
        feedback = self.get_engineer_feedback(engineer_id, period_id)

        if not feedback.get("has_data"):
            return f"您的{feedback['period_name']}绩效数据尚未计算，请稍后查看。"

        current = feedback["current_performance"]
        comparison = feedback.get("comparison", {})

        message = f"【{feedback['period_name']}绩效反馈】\n\n"
        message += f"综合得分：{current['total_score']:.1f}分（等级：{current['level']}）\n"
        message += f"部门排名：第{current['dept_rank']}名\n"
        message += f"公司排名：第{current['company_rank']}名\n\n"

        if comparison:
            score_change = comparison.get("score_change", 0)
            rank_change = comparison.get("rank_change", 0)

            if score_change > 0:
                message += f"📈 得分提升 {score_change:.1f}分\n"
            elif score_change < 0:
                message += f"📉 得分下降 {abs(score_change):.1f}分\n"

            if rank_change < 0:
                message += f"⬆️ 排名上升 {abs(rank_change)}名\n"
            elif rank_change > 0:
                message += f"⬇️ 排名下降 {rank_change}名\n"

        message += "\n【五维得分】\n"
        dim_scores = current["dimension_scores"]
        message += f"技术能力：{dim_scores.get('technical', 0):.1f}分\n"
        message += f"项目执行：{dim_scores.get('execution', 0):.1f}分\n"
        message += f"成本/质量：{dim_scores.get('cost_quality', 0):.1f}分\n"
        message += f"知识沉淀：{dim_scores.get('knowledge', 0):.1f}分\n"
        message += f"团队协作：{dim_scores.get('collaboration', 0):.1f}分\n"

        # 如果是方案工程师，添加方案成功率得分
        if "solution_success" in dim_scores:
            message += f"方案成功率：{dim_scores['solution_success']:.1f}分\n"

        if feedback.get("highlights"):
            message += "\n【亮点】\n"
            for highlight in feedback["highlights"]:
                message += f"• {highlight}\n"

        if feedback.get("improvements"):
            message += "\n【改进建议】\n"
            for improvement in feedback["improvements"]:
                message += f"• {improvement}\n"

        return message

    def get_dimension_trend(self, engineer_id: int, periods: int = 6) -> Dict[str, List[float]]:
        """
        获取五维得分趋势

        Args:
            engineer_id: 工程师ID
            periods: 历史周期数

        Returns:
            各维度得分趋势数据
        """
        results = (
            self.db.query(PerformanceResult)
            .join(PerformancePeriod, PerformanceResult.period_id == PerformancePeriod.id)
            .filter(PerformanceResult.user_id == engineer_id)
            .order_by(desc(PerformancePeriod.start_date))
            .limit(periods)
            .all()
        )

        if not results:
            return {
                "technical": [],
                "execution": [],
                "cost_quality": [],
                "knowledge": [],
                "collaboration": [],
                "periods": [],
            }

        # 反转顺序（从最早到最新）
        results = list(reversed(results))

        trends = {
            "technical": [],
            "execution": [],
            "cost_quality": [],
            "knowledge": [],
            "collaboration": [],
            "periods": [],
        }

        # 获取工程师档案以确定岗位类型
        self.db.query(EngineerProfile).filter(EngineerProfile.user_id == engineer_id).first()

        for result in results:
            # 从indicator_scores获取五维得分，如果没有则使用默认值
            if result.indicator_scores:
                scores = result.indicator_scores
                trends["technical"].append(float(scores.get("technical_score", 75)))
                trends["execution"].append(float(scores.get("execution_score", 75)))
                trends["cost_quality"].append(float(scores.get("cost_quality_score", 75)))
                trends["knowledge"].append(float(scores.get("knowledge_score", 75)))
                trends["collaboration"].append(float(scores.get("collaboration_score", 75)))
            else:
                # 使用默认值
                trends["technical"].append(75.0)
                trends["execution"].append(75.0)
                trends["cost_quality"].append(75.0)
                trends["knowledge"].append(75.0)
                trends["collaboration"].append(75.0)

            trends["periods"].append(result.period.period_name if result.period else "")

        return trends

    def identify_ability_changes(self, engineer_id: int, periods: int = 6) -> List[Dict[str, Any]]:
        """
        识别能力变化

        Args:
            engineer_id: 工程师ID
            periods: 历史周期数

        Returns:
            能力变化分析列表
        """
        trends = self.get_dimension_trend(engineer_id, periods)

        if len(trends["technical"]) < 2:
            return []

        changes = []

        # 计算各维度的变化趋势
        dimensions = ["technical", "execution", "cost_quality", "knowledge", "collaboration"]
        dimension_names = {
            "technical": "技术能力",
            "execution": "项目执行",
            "cost_quality": "成本/质量",
            "knowledge": "知识沉淀",
            "collaboration": "团队协作",
        }

        for dim in dimensions:
            scores = trends[dim]
            if len(scores) >= 2:
                recent_avg = sum(scores[-3:]) / min(3, len(scores))  # 最近3个周期
                earlier_avg = sum(scores[:3]) / min(3, len(scores))  # 前3个周期

                change = recent_avg - earlier_avg

                if abs(change) > 5:  # 变化超过5分才记录
                    changes.append(
                        {
                            "dimension": dim,
                            "dimension_name": dimension_names[dim],
                            "change": round(change, 2),
                            "trend": "improving" if change > 0 else "declining",
                            "recent_avg": round(recent_avg, 2),
                            "earlier_avg": round(earlier_avg, 2),
                        }
                    )

        return changes

    def generate_personalized_feedback(self, engineer_id: int, period_id: int) -> Dict[str, Any]:
        """
        生成个性化反馈（基于工程师岗位类型）

        Args:
            engineer_id: 工程师ID
            period_id: 考核周期ID

        Returns:
            个性化反馈信息
        """
        from app.models.engineer_performance import EngineerProfile

        profile = (
            self.db.query(EngineerProfile).filter(EngineerProfile.user_id == engineer_id).first()
        )

        feedback = self.get_engineer_feedback(engineer_id, period_id)

        if not feedback.get("has_data"):
            return feedback

        # 根据岗位类型生成个性化建议
        job_type_suggestions = {
            "mechanical": [
                "关注设计一次通过率，减少返工",
                "提高标准件使用率，降低成本",
                "加强设计复用，提升效率",
            ],
            "test": ["提升程序一次调通率", "缩短Bug修复时长", "提高现场响应速度"],
            "electrical": ["提高图纸一次通过率", "提升PLC一次调通率", "加强标准件选型"],
            "solution": ["提高方案中标率", "提升方案质量评分", "加强方案模板复用"],
        }

        suggestions = job_type_suggestions.get(profile.job_type if profile else "mechanical", [])

        # 根据得分情况生成具体建议
        dim_scores = feedback["current_performance"]["dimension_scores"]
        specific_suggestions = []

        if dim_scores.get("technical", 75) < 70:
            specific_suggestions.append("技术能力需要提升，建议加强技术学习和实践")
        if dim_scores.get("execution", 75) < 70:
            specific_suggestions.append("项目执行能力需要改进，建议加强时间管理和任务规划")
        if dim_scores.get("cost_quality", 75) < 70:
            specific_suggestions.append("成本/质量控制需要加强，建议提高标准件使用率和设计复用率")
        if dim_scores.get("knowledge", 75) < 70:
            specific_suggestions.append("知识沉淀不足，建议多分享技术文档和模板")
        if dim_scores.get("collaboration", 75) < 70:
            specific_suggestions.append("团队协作需要改进，建议加强跨部门沟通")

        feedback["personalized_suggestions"] = suggestions + specific_suggestions

        return feedback
