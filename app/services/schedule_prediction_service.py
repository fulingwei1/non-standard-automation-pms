# -*- coding: utf-8 -*-
"""
项目进度预测服务
使用 GLM-5 进行智能进度预测和赶工方案生成
"""

import json
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.project.schedule_prediction import (
    ProjectSchedulePrediction,
    CatchUpSolution,
    ScheduleAlert,
)
from app.services.ai_client_service import AIClientService
from app.utils.db_helpers import save_obj

logger = logging.getLogger(__name__)


class SchedulePredictionService:
    """进度预测服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()

    def predict_completion_date(
        self,
        project_id: int,
        current_progress: float,
        planned_progress: float,
        remaining_days: int,
        team_size: int,
        project_data: Optional[Dict[str, Any]] = None,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        预测项目完成日期

        Args:
            project_id: 项目ID
            current_progress: 当前进度 (%)
            planned_progress: 计划进度 (%)
            remaining_days: 剩余天数
            team_size: 团队规模
            project_data: 项目详细数据（可选）
            use_ai: 是否使用AI模型预测

        Returns:
            预测结果字典
        """
        try:
            # 1. 提取特征
            features = self._extract_features(
                project_id=project_id,
                current_progress=current_progress,
                planned_progress=planned_progress,
                remaining_days=remaining_days,
                team_size=team_size,
                project_data=project_data,
            )

            # 2. 进行预测
            if use_ai:
                prediction = self._predict_with_ai(features, project_data)
            else:
                prediction = self._predict_linear(features)

            # 3. 评估风险等级
            risk_level = self._assess_risk_level(prediction["delay_days"])

            # 4. 保存预测结果
            prediction_record = ProjectSchedulePrediction(
                project_id=project_id,
                prediction_date=datetime.now(),
                predicted_completion_date=prediction["predicted_date"],
                delay_days=prediction["delay_days"],
                confidence=Decimal(str(prediction["confidence"])),
                risk_level=risk_level,
                features=features,
                prediction_details=prediction.get("details"),
                model_version="glm-5" if use_ai else "linear-v1",
            )
            save_obj(self.db, prediction_record)

            return {
                "prediction_id": prediction_record.id,
                "project_id": project_id,
                "current_progress": current_progress,
                "planned_progress": planned_progress,
                "prediction": {
                    "completion_date": str(prediction["predicted_date"]),
                    "delay_days": prediction["delay_days"],
                    "confidence": float(prediction["confidence"]),
                    "risk_level": risk_level,
                },
                "features": features,
                "details": prediction.get("details"),
            }

        except Exception as e:
            logger.error(f"预测失败: {e}")
            raise

    def _extract_features(
        self,
        project_id: int,
        current_progress: float,
        planned_progress: float,
        remaining_days: int,
        team_size: int,
        project_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """提取预测特征"""
        # 计算进度偏差
        progress_deviation = current_progress - planned_progress

        # 计算日均进度（过去）
        days_elapsed = project_data.get("days_elapsed", 30) if project_data else 30
        avg_daily_progress = current_progress / days_elapsed if days_elapsed > 0 else 0

        # 计算所需日均进度（未来）
        remaining_progress = 100 - current_progress
        required_daily_progress = (
            remaining_progress / remaining_days if remaining_days > 0 else 0
        )

        # 计算速度比率
        velocity_ratio = (
            avg_daily_progress / required_daily_progress
            if required_daily_progress > 0
            else 1.0
        )

        # 提取其他特征
        complexity = project_data.get("complexity", "medium") if project_data else "medium"
        
        # 查询历史类似项目数据
        similar_projects_stats = self._get_similar_projects_stats(
            complexity=complexity,
            team_size=team_size
        )

        features = {
            "current_progress": round(current_progress, 2),
            "planned_progress": round(planned_progress, 2),
            "progress_deviation": round(progress_deviation, 2),
            "remaining_days": remaining_days,
            "remaining_progress": round(remaining_progress, 2),
            "team_size": team_size,
            "avg_daily_progress": round(avg_daily_progress, 3),
            "required_daily_progress": round(required_daily_progress, 3),
            "velocity_ratio": round(velocity_ratio, 3),
            "complexity": complexity,
            "similar_projects_avg_duration": similar_projects_stats.get("avg_duration", 90),
            "similar_projects_delay_rate": similar_projects_stats.get("delay_rate", 0.3),
        }

        return features

    def _predict_with_ai(
        self, features: Dict[str, Any], project_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用AI模型预测"""
        try:
            # 构建提示词
            prompt = self._build_prediction_prompt(features, project_data)

            # 调用 GLM-5
            response = self.ai_client.generate_solution(
                prompt=prompt,
                model="glm-5",
                temperature=0.3,  # 降低随机性，提高准确性
                max_tokens=2000,
            )

            # 解析响应
            content = response["content"]
            prediction = self._parse_ai_prediction(content, features)

            return prediction

        except Exception as e:
            logger.error(f"AI预测失败，降级到线性预测: {e}")
            return self._predict_linear(features)

    def _build_prediction_prompt(
        self, features: Dict[str, Any], project_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建AI预测提示词"""
        project_context = ""
        if project_data:
            project_context = f"""
项目背景:
- 项目名称: {project_data.get('name', '未知')}
- 项目类型: {project_data.get('type', '非标自动化')}
- 客户行业: {project_data.get('industry', '制造业')}
- 关键里程碑: {json.dumps(project_data.get('milestones', []), ensure_ascii=False)}
"""

        prompt = f"""
作为项目管理专家，基于以下信息预测项目完成日期：

{project_context}

当前项目状态:
- 当前进度: {features['current_progress']}%
- 计划进度: {features['planned_progress']}%
- 进度偏差: {features['progress_deviation']}%
- 剩余天数: {features['remaining_days']}天
- 剩余工作量: {features['remaining_progress']}%
- 团队规模: {features['team_size']}人
- 历史日均进度: {features['avg_daily_progress']}%/天
- 所需日均进度: {features['required_daily_progress']}%/天
- 速度比率: {features['velocity_ratio']} (1.0表示刚好按时完成)
- 项目复杂度: {features['complexity']}

历史参考数据:
- 类似项目平均工期: {features['similar_projects_avg_duration']}天
- 类似项目延期率: {features['similar_projects_delay_rate'] * 100}%

请分析并预测:
1. 项目最终完成日期（相对于计划日期的延期天数，可以是负数表示提前）
2. 置信度（0.0-1.0之间的小数）
3. 主要风险因素（列举2-3个）
4. 改进建议（列举2-3条）

请以JSON格式返回结果，格式如下：
{{
    "delay_days": 15,
    "confidence": 0.85,
    "risk_factors": ["团队规模不足", "进度偏差较大"],
    "recommendations": ["增加人力投入", "优化工作流程", "加强进度监控"]
}}

注意：
- delay_days 为正数表示延期，负数表示提前完成
- confidence 应该基于数据质量、历史准确性等因素综合评估
- 只返回JSON，不要有其他说明文字
"""
        return prompt

    def _parse_ai_prediction(
        self, ai_response: str, features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析AI预测结果"""
        try:
            # 尝试提取JSON
            # 查找第一个 { 和最后一个 }
            start_idx = ai_response.find("{")
            end_idx = ai_response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                raise ValueError("无法找到有效的JSON格式")

            delay_days = int(data.get("delay_days", 0))
            confidence = float(data.get("confidence", 0.7))

            # 计算预测完成日期
            predicted_date = date.today() + timedelta(days=features["remaining_days"] + delay_days)

            return {
                "predicted_date": predicted_date,
                "delay_days": delay_days,
                "confidence": confidence,
                "details": {
                    "risk_factors": data.get("risk_factors", []),
                    "recommendations": data.get("recommendations", []),
                    "ai_reasoning": ai_response,
                },
            }

        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            # 降级到简单预测
            return self._predict_linear(features)

    def _predict_linear(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """线性预测（作为AI预测的降级方案）"""
        velocity_ratio = features["velocity_ratio"]
        remaining_days = features["remaining_days"]

        # 简单线性预测
        if velocity_ratio >= 1.0:
            # 速度足够，可能按时或提前完成
            delay_days = 0
            confidence = 0.8
        else:
            # 速度不足，会延期
            # 延期天数 = 剩余天数 * (1/速度比率 - 1)
            delay_days = int(remaining_days * (1.0 / velocity_ratio - 1.0))
            confidence = 0.7

        predicted_date = date.today() + timedelta(days=remaining_days + delay_days)

        return {
            "predicted_date": predicted_date,
            "delay_days": delay_days,
            "confidence": confidence,
            "details": {
                "method": "linear",
                "velocity_ratio": velocity_ratio,
            },
        }

    def _assess_risk_level(self, delay_days: int) -> str:
        """评估风险等级"""
        if delay_days < 0:
            return "low"  # 提前完成
        elif delay_days <= 3:
            return "low"
        elif delay_days <= 7:
            return "medium"
        elif delay_days <= 14:
            return "high"
        else:
            return "critical"

    def _get_similar_projects_stats(
        self, complexity: str, team_size: int
    ) -> Dict[str, Any]:
        """获取类似项目统计数据"""
        try:
            # 查询历史预测记录，获取类似项目的统计
            # 这里简化处理，实际应该查询真实的项目表
            similar_predictions = (
                self.db.query(ProjectSchedulePrediction)
                .filter(
                    and_(
                        ProjectSchedulePrediction.features["complexity"].astext == complexity,
                        ProjectSchedulePrediction.created_at
                        >= datetime.now() - timedelta(days=365),
                    )
                )
                .limit(20)
                .all()
            )

            if similar_predictions:
                avg_delay = sum(p.delay_days or 0 for p in similar_predictions) / len(
                    similar_predictions
                )
                delay_count = sum(
                    1 for p in similar_predictions if (p.delay_days or 0) > 0
                )
                delay_rate = delay_count / len(similar_predictions)

                return {
                    "avg_duration": 90,  # 简化处理
                    "delay_rate": delay_rate,
                    "avg_delay": avg_delay,
                }

            # 默认值
            return {"avg_duration": 90, "delay_rate": 0.3, "avg_delay": 10}

        except Exception as e:
            logger.error(f"获取历史统计失败: {e}")
            return {"avg_duration": 90, "delay_rate": 0.3, "avg_delay": 10}

    def generate_catch_up_solutions(
        self,
        project_id: int,
        prediction_id: int,
        delay_days: int,
        project_data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        生成赶工方案

        Args:
            project_id: 项目ID
            prediction_id: 预测记录ID
            delay_days: 延期天数
            project_data: 项目数据（包含预算、资源等信息）

        Returns:
            赶工方案列表
        """
        try:
            # 使用AI生成赶工方案
            solutions_data = self._generate_solutions_with_ai(
                delay_days=delay_days, project_data=project_data
            )

            # 保存到数据库
            solutions = []
            for idx, sol_data in enumerate(solutions_data):
                solution = CatchUpSolution(
                    project_id=project_id,
                    prediction_id=prediction_id,
                    solution_name=sol_data["name"],
                    solution_type=sol_data.get("type", "hybrid"),
                    description=sol_data.get("description"),
                    actions=sol_data.get("actions", []),
                    estimated_catch_up_days=sol_data.get("estimated_catch_up", 0),
                    additional_cost=Decimal(str(sol_data.get("additional_cost", 0))),
                    risk_level=sol_data.get("risk", "medium"),
                    success_rate=Decimal(str(sol_data.get("success_rate", 0.7))),
                    status="pending",
                    is_recommended=(idx == sol_data.get("recommended_index", 0)),
                    evaluation_details=sol_data.get("evaluation"),
                )
                self.db.add(solution)
                solutions.append(solution)

            self.db.commit()

            # 返回方案列表
            return [
                {
                    "id": sol.id,
                    "name": sol.solution_name,
                    "type": sol.solution_type,
                    "actions": sol.actions,
                    "estimated_catch_up_days": sol.estimated_catch_up_days,
                    "additional_cost": float(sol.additional_cost),
                    "risk_level": sol.risk_level,
                    "success_rate": float(sol.success_rate),
                    "is_recommended": sol.is_recommended,
                }
                for sol in solutions
            ]

        except Exception as e:
            logger.error(f"生成赶工方案失败: {e}")
            raise

    def _generate_solutions_with_ai(
        self, delay_days: int, project_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """使用AI生成赶工方案"""
        try:
            # 构建提示词
            prompt = self._build_solution_prompt(delay_days, project_data)

            # 调用 GLM-5
            response = self.ai_client.generate_solution(
                prompt=prompt, model="glm-5", temperature=0.5, max_tokens=3000
            )

            # 解析响应
            content = response["content"]
            solutions = self._parse_ai_solutions(content)

            return solutions

        except Exception as e:
            logger.error(f"AI生成方案失败，使用默认方案: {e}")
            return self._generate_default_solutions(delay_days, project_data)

    def _build_solution_prompt(
        self, delay_days: int, project_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建赶工方案生成提示词"""
        project_context = ""
        if project_data:
            project_context = f"""
项目约束:
- 预算余额: {project_data.get('budget_remaining', '未知')}元
- 当前团队: {project_data.get('team_size', 5)}人
- 可用资源池: {project_data.get('available_resources', '未知')}
- 客户要求: {project_data.get('customer_requirements', '按时交付')}
"""

        prompt = f"""
作为项目管理专家，为延期{delay_days}天的非标自动化项目生成赶工方案。

{project_context}

请生成至少3个赶工方案，每个方案应包含：
1. 方案名称
2. 方案类型（manpower/overtime/process/hybrid）
3. 具体行动计划（至少2-3条）
4. 预计可追回天数
5. 额外成本估算
6. 风险等级（low/medium/high）
7. 成功率（0.0-1.0）
8. 优缺点分析

请以JSON格式返回，格式如下：
{{
    "solutions": [
        {{
            "name": "增加人力方案",
            "type": "manpower",
            "description": "通过增加团队人员加快项目进度",
            "actions": [
                {{"action": "从项目A借调2名工程师", "priority": 1}},
                {{"action": "新招1名外包工程师", "priority": 2}}
            ],
            "estimated_catch_up": 10,
            "additional_cost": 15000,
            "risk": "medium",
            "success_rate": 0.75,
            "evaluation": {{
                "pros": ["效果明显", "可快速见效"],
                "cons": ["成本较高", "需要时间融入"],
                "prerequisites": ["获得人力资源部门批准"]
            }}
        }}
    ],
    "recommended_index": 0
}}

只返回JSON，不要有其他说明文字。
"""
        return prompt

    def _parse_ai_solutions(self, ai_response: str) -> List[Dict[str, Any]]:
        """解析AI生成的方案"""
        try:
            # 提取JSON
            start_idx = ai_response.find("{")
            end_idx = ai_response.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                data = json.loads(json_str)
                solutions = data.get("solutions", [])

                # 添加推荐标记
                recommended_idx = data.get("recommended_index", 0)
                for idx, sol in enumerate(solutions):
                    sol["recommended_index"] = recommended_idx

                return solutions
            else:
                raise ValueError("无法找到有效的JSON格式")

        except Exception as e:
            logger.error(f"解析AI方案失败: {e}")
            return []

    def _generate_default_solutions(
        self, delay_days: int, project_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """生成默认赶工方案（AI失败时的降级方案）"""
        return [
            {
                "name": "加班赶工方案",
                "type": "overtime",
                "description": "通过增加工作时间追赶进度",
                "actions": [
                    {"action": "周末加班（8小时/天）", "priority": 1},
                    {"action": "平日延长工作1小时", "priority": 2},
                ],
                "estimated_catch_up": min(int(delay_days * 0.6), delay_days),
                "additional_cost": 8000,
                "risk": "low",
                "success_rate": 0.8,
                "evaluation": {
                    "pros": ["成本可控", "易于执行"],
                    "cons": ["可能影响团队士气"],
                },
                "recommended_index": 0,
            },
            {
                "name": "流程优化方案",
                "type": "process",
                "description": "优化工作流程提高效率",
                "actions": [
                    {"action": "简化非关键路径任务", "priority": 1},
                    {"action": "并行执行部分任务", "priority": 2},
                ],
                "estimated_catch_up": min(int(delay_days * 0.4), delay_days),
                "additional_cost": 0,
                "risk": "medium",
                "success_rate": 0.6,
                "evaluation": {
                    "pros": ["零成本", "可持续"],
                    "cons": ["效果有限", "可能影响质量"],
                },
                "recommended_index": 0,
            },
            {
                "name": "增加人力方案",
                "type": "manpower",
                "description": "增加团队人员加快进度",
                "actions": [
                    {"action": "临时借调2名工程师", "priority": 1},
                    {"action": "必要时招聘外包人员", "priority": 2},
                ],
                "estimated_catch_up": min(int(delay_days * 0.8), delay_days),
                "additional_cost": 20000,
                "risk": "medium",
                "success_rate": 0.75,
                "evaluation": {
                    "pros": ["效果显著"],
                    "cons": ["成本高", "需要协调"],
                },
                "recommended_index": 0,
            },
        ]

    def create_alert(
        self,
        project_id: int,
        prediction_id: int,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        alert_details: Optional[Dict[str, Any]] = None,
        notify_users: Optional[List[int]] = None,
    ) -> ScheduleAlert:
        """
        创建进度预警

        Args:
            project_id: 项目ID
            prediction_id: 预测记录ID
            alert_type: 预警类型
            severity: 严重程度
            title: 预警标题
            message: 预警消息
            alert_details: 预警详情
            notify_users: 需要通知的用户ID列表

        Returns:
            ScheduleAlert对象
        """
        # 构建通知用户列表
        notified_users = []
        if notify_users:
            for user_id in notify_users:
                notified_users.append(
                    {
                        "user_id": user_id,
                        "notified_at": datetime.now().isoformat(),
                    }
                )

        alert = ScheduleAlert(
            project_id=project_id,
            prediction_id=prediction_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            alert_details=alert_details,
            notified_users=notified_users,
            notification_channels=["email", "system_message"],
            is_read=False,
            is_resolved=False,
        )

        save_obj(self.db, alert)

        return alert

    def check_and_create_alerts(
        self,
        project_id: int,
        prediction_id: int,
        delay_days: int,
        progress_deviation: float,
        project_data: Optional[Dict[str, Any]] = None,
    ) -> List[ScheduleAlert]:
        """
        检查并创建预警

        根据延期天数和进度偏差自动创建预警

        Args:
            project_id: 项目ID
            prediction_id: 预测记录ID
            delay_days: 延期天数
            progress_deviation: 进度偏差
            project_data: 项目数据

        Returns:
            创建的预警列表
        """
        alerts = []

        # 延期预警
        if delay_days >= 3:
            severity = self._assess_risk_level(delay_days)
            alert = self.create_alert(
                project_id=project_id,
                prediction_id=prediction_id,
                alert_type="delay_warning",
                severity=severity,
                title=f"项目延期预警 - 预计延期{delay_days}天",
                message=f"根据当前进度分析，项目预计将延期{delay_days}天完成。建议立即采取赶工措施。",
                alert_details={
                    "delay_days": delay_days,
                    "progress_deviation": progress_deviation,
                    "trigger_condition": f"delay_days >= 3",
                },
            )
            alerts.append(alert)

        # 进度偏差预警
        if abs(progress_deviation) >= 10:
            severity = "high" if abs(progress_deviation) >= 20 else "medium"
            alert = self.create_alert(
                project_id=project_id,
                prediction_id=prediction_id,
                alert_type="velocity_drop",
                severity=severity,
                title=f"进度偏差预警 - 偏差{progress_deviation:.1f}%",
                message=f"当前进度与计划进度偏差{progress_deviation:.1f}%，需要关注。",
                alert_details={
                    "progress_deviation": progress_deviation,
                    "trigger_condition": "abs(deviation) >= 10",
                },
            )
            alerts.append(alert)

        return alerts

    def get_project_alerts(
        self,
        project_id: int,
        severity: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取项目预警列表

        Args:
            project_id: 项目ID
            severity: 严重程度过滤
            unread_only: 是否只返回未读预警
            limit: 返回数量限制

        Returns:
            预警列表
        """
        query = self.db.query(ScheduleAlert).filter(
            ScheduleAlert.project_id == project_id
        )

        if severity:
            query = query.filter(ScheduleAlert.severity == severity)

        if unread_only:
            query = query.filter(ScheduleAlert.is_read == False)

        alerts = query.order_by(desc(ScheduleAlert.created_at)).limit(limit).all()

        return [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "details": alert.alert_details,
                "is_read": alert.is_read,
                "is_resolved": alert.is_resolved,
                "created_at": alert.created_at.isoformat(),
            }
            for alert in alerts
        ]

    def get_risk_overview(self) -> Dict[str, Any]:
        """
        获取所有项目的风险概览

        Returns:
            风险概览数据
        """
        # 获取最近的预测记录（每个项目最新一条）
        from sqlalchemy import func

        subquery = (
            self.db.query(
                ProjectSchedulePrediction.project_id,
                func.max(ProjectSchedulePrediction.prediction_date).label("max_date"),
            )
            .group_by(ProjectSchedulePrediction.project_id)
            .subquery()
        )

        latest_predictions = (
            self.db.query(ProjectSchedulePrediction)
            .join(
                subquery,
                and_(
                    ProjectSchedulePrediction.project_id == subquery.c.project_id,
                    ProjectSchedulePrediction.prediction_date == subquery.c.max_date,
                ),
            )
            .all()
        )

        # 统计
        total_projects = len(latest_predictions)
        at_risk = sum(
            1
            for p in latest_predictions
            if p.risk_level in ["medium", "high", "critical"]
        )
        critical = sum(1 for p in latest_predictions if p.risk_level == "critical")

        # 构建项目列表
        projects = []
        for pred in latest_predictions:
            if pred.risk_level in ["high", "critical"]:
                projects.append(
                    {
                        "project_id": pred.project_id,
                        "risk_level": pred.risk_level,
                        "delay_days": pred.delay_days,
                        "predicted_completion": (
                            str(pred.predicted_completion_date)
                            if pred.predicted_completion_date
                            else None
                        ),
                    }
                )

        return {
            "total_projects": total_projects,
            "at_risk": at_risk,
            "critical": critical,
            "projects": projects,
        }
