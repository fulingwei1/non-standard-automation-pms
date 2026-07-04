"""
项目复盘报告AI生成服务
使用GLM-5自动生成项目总结报告
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.change_request import ChangeRequest
from app.models.project import Project
from app.models.project.financial import ProjectCost
from app.models.timesheet import Timesheet
from app.services.ai_client_service import AIClientService, is_mock_response
from app.services.cost.cost_basis import actual_project_cost_filter

AI_REVIEW_DEGRADED_REASON = "AI_REVIEW_UNAVAILABLE"


class ProjectReviewReportGenerator:
    """项目复盘报告生成器"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()

    def generate_report(
        self,
        project_id: int,
        review_type: str = "POST_MORTEM",
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成项目复盘报告

        Args:
            project_id: 项目ID
            review_type: 复盘类型 POST_MORTEM/MID_TERM/QUARTERLY
            additional_context: 额外上下文信息

        Returns:
            生成的报告数据
        """
        start_time = datetime.now()

        # 1. 提取项目数据
        project_data = self._extract_project_data(project_id)
        if not project_data:
            raise ValueError(f"项目 {project_id} 不存在或数据不完整")

        # 2. 构建AI提示词
        prompt = self._build_review_prompt(
            project_data, review_type, additional_context
        )

        # 3. 调用GLM-5生成报告
        ai_response = self.ai_client.generate_solution(
            prompt=prompt, model="glm-5", temperature=0.7, max_tokens=3000
        )

        # 4. 解析AI响应
        report_data = self._parse_ai_response(ai_response, project_data)

        # 5. 添加处理元数据
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        degraded = is_mock_response(ai_response)
        usage = ai_response.get("usage") or {}
        report_data["ai_metadata"] = {
            "model": ai_response.get("model") or "glm-5",
            "processing_time_ms": processing_time,
            "token_usage": ai_response.get("token_usage", usage.get("total_tokens", 0)),
            "generated_at": datetime.now().isoformat(),
            "degraded": degraded,
        }
        if degraded:
            report_data["ai_metadata"]["degraded_reason"] = AI_REVIEW_DEGRADED_REASON

        return report_data

    def _extract_project_data(self, project_id: int) -> Optional[Dict[str, Any]]:
        """提取项目相关数据"""
        # 获取项目基本信息
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # 获取工时数据
        timesheets = (
            self.db.query(Timesheet).filter(Timesheet.project_id == project_id).all()
        )

        # 获取成本数据
        costs = (
            self.db.query(ProjectCost)
            .filter(ProjectCost.project_id == project_id, actual_project_cost_filter())
            .all()
        )

        # 获取变更数据
        changes = (
            self.db.query(ChangeRequest)
            .filter(ChangeRequest.project_id == project_id)
            .all()
        )

        # 计算统计数据
        total_hours = sum(t.work_hours or 0 for t in timesheets)
        total_cost = sum(float(c.amount or 0) for c in costs)
        change_count = len(changes)

        # 计算工期
        actual_duration = 0
        if project.actual_end_date and project.actual_start_date:
            actual_duration = (project.actual_end_date - project.actual_start_date).days

        plan_duration = 0
        if project.planned_end_date and project.planned_start_date:
            plan_duration = (project.planned_end_date - project.planned_start_date).days

        return {
            "project": {
                "id": project.id,
                "code": project.project_code,
                "name": project.project_name,
                "description": project.description,
                "customer_name": (
                    project.customer.customer_name
                    if getattr(project, "customer", None)
                    else project.customer_name
                ),
                "status": project.status,
                "type": project.project_type,
                "planned_start": (
                    project.planned_start_date.isoformat()
                    if project.planned_start_date
                    else None
                ),
                "planned_end": (
                    project.planned_end_date.isoformat()
                    if project.planned_end_date
                    else None
                ),
                "actual_start": (
                    project.actual_start_date.isoformat()
                    if project.actual_start_date
                    else None
                ),
                "actual_end": (
                    project.actual_end_date.isoformat()
                    if project.actual_end_date
                    else None
                ),
                "budget": float(project.budget_amount or 0),
            },
            "statistics": {
                "total_hours": total_hours,
                "total_cost": total_cost,
                "change_count": change_count,
                "plan_duration": plan_duration,
                "actual_duration": actual_duration,
                "schedule_variance": actual_duration - plan_duration,
                "cost_variance": total_cost - float(project.budget_amount or 0),
            },
            "team_members": (
                [
                    {
                        "name": member.user.username
                        if hasattr(member, "user")
                        else "Unknown",
                        "role": member.role,
                        "hours": sum(
                            t.work_hours or 0
                            for t in timesheets
                            if t.user_id == member.user_id
                        ),
                    }
                    for member in project.members
                ]
                if hasattr(project, "members")
                else []
            ),
            "changes": [
                {
                    "title": change.title,
                    "type": change.change_type,
                    "impact": change.impact_level,
                    "status": change.status,
                }
                for change in changes
            ],
        }

    def _build_review_prompt(
        self,
        project_data: Dict[str, Any],
        review_type: str,
        additional_context: Optional[str],
    ) -> str:
        """构建AI提示词"""
        project = project_data["project"]
        stats = project_data["statistics"]

        schedule_label = (
            "延期"
            if stats["schedule_variance"] > 0
            else "提前"
            if stats["schedule_variance"] < 0
            else "准时"
        )
        cost_label = (
            "超支"
            if stats["cost_variance"] > 0
            else "结余"
            if stats["cost_variance"] < 0
            else "持平"
        )
        team_size = len(project_data["team_members"])
        changes_text = self._format_changes(project_data["changes"])
        extra_section = (
            f"## 补充信息\n{additional_context}" if additional_context else ""
        )

        prompt = f"""# 项目复盘报告生成任务

## 项目基本信息
- 项目名称：{project["name"]}
- 项目编号：{project["code"]}
- 客户名称：{project["customer_name"]}
- 项目类型：{project["type"]}
- 项目描述：{project["description"]}

## 项目周期
- 计划工期：{stats["plan_duration"]}天
- 实际工期：{stats["actual_duration"]}天
- 进度偏差：{stats["schedule_variance"]}天 ({schedule_label})

## 项目成本
- 预算金额：¥{project["budget"]:,.2f}
- 实际成本：¥{stats["total_cost"]:,.2f}
- 成本偏差：¥{stats["cost_variance"]:,.2f} ({cost_label})

## 项目统计
- 总工时：{stats["total_hours"]}小时
- 变更次数：{stats["change_count"]}次
- 团队人数：{team_size}人

## 主要变更
{changes_text}

## 任务要求
请作为资深项目经理，基于以上数据生成一份专业的项目复盘报告，包含以下内容：

1. **项目总结**（200-300字）
   - 简要概述项目情况
   - 突出关键成果和挑战

2. **成功因素分析**（3-5条）
   - 识别项目成功的关键因素
   - 每条20-50字，要具体可操作

3. **问题与教训**（3-5条）
   - 识别项目中的主要问题
   - 分析根本原因
   - 每条30-60字

4. **改进建议**（3-5条）
   - 针对问题提出具体改进措施
   - 要可执行、可衡量
   - 每条30-60字

5. **最佳实践**（2-3条）
   - 提炼可复用的成功经验
   - 说明适用场景
   - 每条40-80字

6. **复盘结论**（150-200字）
   - 整体评价
   - 关键启示
   - 未来展望

{extra_section}

请以JSON格式输出，包含以下字段：
- summary: 项目总结
- success_factors: 成功因素数组
- problems: 问题与教训数组
- improvements: 改进建议数组
- best_practices: 最佳实践数组
- conclusion: 复盘结论
- insights: AI洞察（其他值得关注的发现）

确保分析客观、专业，基于数据而非猜测。"""

        return prompt

    def _format_changes(self, changes: List[Dict]) -> str:
        """格式化变更列表"""
        if not changes:
            return "无变更记录"

        formatted = []
        for i, change in enumerate(changes[:5], 1):  # 最多显示5条
            formatted.append(
                f"{i}. {change['title']} (类型：{change['type']}，影响：{change['impact']}，状态：{change['status']})"
            )

        if len(changes) > 5:
            formatted.append(f"... 共{len(changes)}条变更")

        return "\n".join(formatted)

    def _parse_ai_response(
        self, ai_response: Dict[str, Any], project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析AI响应"""
        if is_mock_response(ai_response):
            report_content = self._fallback_review_content(project_data)
            ai_generated = False
            ai_generated_at = None
        else:
            report_content = self._extract_review_content(ai_response)
            ai_generated = True
            ai_generated_at = datetime.now()

        # 合并项目数据和AI分析结果
        return {
            "project_id": project_data["project"]["id"],
            "project_code": project_data["project"]["code"],
            "review_type": "POST_MORTEM",
            "review_date": datetime.now().date(),
            # 周期数据
            "plan_duration": project_data["statistics"]["plan_duration"],
            "actual_duration": project_data["statistics"]["actual_duration"],
            "schedule_variance": project_data["statistics"]["schedule_variance"],
            # 成本数据
            "budget_amount": project_data["project"]["budget"],
            "actual_cost": project_data["statistics"]["total_cost"],
            "cost_variance": project_data["statistics"]["cost_variance"],
            # 质量指标
            "change_count": project_data["statistics"]["change_count"],
            "quality_issues": 0,  # 待补充
            "customer_satisfaction": None,  # 待输入
            # AI生成内容
            "success_factors": "\\n".join(report_content.get("success_factors", [])),
            "problems": "\\n".join(report_content.get("problems", [])),
            "improvements": "\\n".join(report_content.get("improvements", [])),
            "best_practices": "\\n".join(report_content.get("best_practices", [])),
            "conclusion": report_content.get("conclusion", ""),
            "ai_summary": report_content.get("summary", ""),
            "ai_insights": report_content.get("insights", {}),
            # AI标记
            "ai_generated": ai_generated,
            "ai_generated_at": ai_generated_at,
        }

    def _extract_review_content(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """从真实 AI 响应中提取复盘内容。"""
        content = ai_response.get("content", "{}")

        # 尝试提取JSON
        try:
            # 如果响应包含```json代码块，提取它
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()

            report_content = json.loads(content)
        except json.JSONDecodeError:
            # 如果解析失败，使用原始文本
            return {
                "summary": content[:500],
                "success_factors": [],
                "problems": [],
                "improvements": [],
                "best_practices": [],
                "conclusion": content[:300],
                "insights": {},
            }

        return report_content

    def _fallback_review_content(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI 不可用时，基于结构化项目数据生成安全兜底复盘。"""
        project = project_data["project"]
        stats = project_data["statistics"]

        summary = (
            f"{project['name']}复盘暂未生成 AI 结论；当前仅基于项目结构化数据形成摘要。"
            f"计划工期 {stats['plan_duration']} 天，实际工期 {stats['actual_duration']} 天，"
            f"进度偏差 {stats['schedule_variance']} 天；预算 {project['budget']}，"
            f"实际成本 {stats['total_cost']}，成本偏差 {stats['cost_variance']}。"
        )

        problems = []
        improvements = []
        if stats["schedule_variance"] > 0:
            problems.append(f"项目较计划延期 {stats['schedule_variance']} 天，需复核延期原因。")
            improvements.append("补充关键路径、资源投入和客户变更记录，明确延期责任与改进动作。")
        if stats["cost_variance"] > 0:
            problems.append(f"项目成本超预算 {stats['cost_variance']}，需复核成本归集和变更影响。")
            improvements.append("复核预算、采购、工时和变更成本口径，形成超支纠偏清单。")
        if stats["change_count"] > 0:
            problems.append(f"项目存在 {stats['change_count']} 次变更，需确认范围和交期影响。")
            improvements.append("将需求变更、审批结论和成本/交期影响纳入复盘证据。")
        if not problems:
            problems.append("结构化数据未显示明显进度或成本异常，仍需人工补充质量、客户反馈和团队协作事实。")
            improvements.append("由项目负责人补充验收、质量、客户反馈和团队协作记录后再发布复盘。")

        return {
            "summary": summary,
            "success_factors": [
                "项目周期、成本、工时和变更数据已完成结构化归集，可作为人工复盘底稿。"
            ],
            "problems": problems,
            "improvements": improvements,
            "best_practices": [],
            "conclusion": "AI 服务不可用，本次结果为规则兜底底稿，需人工确认后发布。",
            "insights": {
                "analysis_source": "rule_fallback",
                "degraded_reason": AI_REVIEW_DEGRADED_REASON,
            },
        }
