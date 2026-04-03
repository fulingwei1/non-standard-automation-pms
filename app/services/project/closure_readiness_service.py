# -*- coding: utf-8 -*-
"""
项目结项准备度自动检查服务

功能：
- 自动检查结项条件（阶段完成、交付物、客户验收、成本归集、文档齐全）
- 可配置规则引擎
- 输出 closure_readiness 结构

输出格式：
    {
        "ready": bool,
        "score": int,  # 0-100
        "checks": [...],
        "missing_items": [...],
        "recommendations": [...]
    }
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.approval.instance import ApprovalInstance
from app.models.notification import Notification
from app.models.project.core import Project
from app.models.project.document import ProjectDocument
from app.models.project.financial import ProjectCost
from app.models.project.lifecycle import ProjectStage
from app.models.project_review import ProjectBestPractice, ProjectLesson, ProjectReview
from app.models.stage_instance import ProjectNodeInstance, ProjectStageInstance


# ============================================================================
# 默认结项检查规则配置
# ============================================================================

DEFAULT_CLOSURE_RULES = {
    "stage_completion": {
        "enabled": True,
        "weight": 25,
        "label": "阶段完成检查",
        "description": "所有项目阶段是否已完成",
        "required_stages": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"],
    },
    "deliverable_upload": {
        "enabled": True,
        "weight": 20,
        "label": "关键交付物检查",
        "description": "关键交付物是否已上传",
        "required_doc_types": [
            "设计文档",
            "测试报告",
            "验收报告",
            "用户手册",
        ],
    },
    "customer_acceptance": {
        "enabled": True,
        "weight": 25,
        "label": "客户验收检查",
        "description": "客户验收是否已签署",
    },
    "cost_settlement": {
        "enabled": True,
        "weight": 15,
        "label": "成本归集检查",
        "description": "项目成本是否归集完成",
        "cost_variance_threshold": 0.1,  # 10% 允许偏差
    },
    "document_completeness": {
        "enabled": True,
        "weight": 15,
        "label": "项目文档检查",
        "description": "项目文档是否齐全",
        "min_doc_count": 5,
        "required_categories": ["设计", "测试", "验收", "培训"],
    },
}


class ClosureReadinessService:
    """结项准备度检查服务"""

    def __init__(self, db: Session):
        self.db = db

    def check_readiness(
        self,
        project_id: int,
        rules: Optional[dict] = None,
    ) -> dict:
        """
        执行结项准备度检查

        Args:
            project_id: 项目ID
            rules: 自定义规则配置，为 None 时使用默认规则

        Returns:
            closure_readiness 结构
        """
        rules = rules or DEFAULT_CLOSURE_RULES

        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {
                "ready": False,
                "score": 0,
                "checks": [],
                "missing_items": ["项目不存在"],
                "recommendations": [],
            }

        checks = []
        missing_items = []
        recommendations = []
        total_weight = 0
        earned_weight = 0

        # 1. 阶段完成检查
        if rules.get("stage_completion", {}).get("enabled", True):
            result = self._check_stages(project, rules["stage_completion"])
            checks.append(result)
            w = rules["stage_completion"]["weight"]
            total_weight += w
            if result["passed"]:
                earned_weight += w
            else:
                missing_items.extend(result.get("missing", []))
                recommendations.extend(result.get("recommendations", []))

        # 2. 关键交付物检查
        if rules.get("deliverable_upload", {}).get("enabled", True):
            result = self._check_deliverables(project, rules["deliverable_upload"])
            checks.append(result)
            w = rules["deliverable_upload"]["weight"]
            total_weight += w
            if result["passed"]:
                earned_weight += w
            else:
                missing_items.extend(result.get("missing", []))
                recommendations.extend(result.get("recommendations", []))

        # 3. 客户验收检查
        if rules.get("customer_acceptance", {}).get("enabled", True):
            result = self._check_customer_acceptance(project, rules["customer_acceptance"])
            checks.append(result)
            w = rules["customer_acceptance"]["weight"]
            total_weight += w
            if result["passed"]:
                earned_weight += w
            else:
                missing_items.extend(result.get("missing", []))
                recommendations.extend(result.get("recommendations", []))

        # 4. 成本归集检查
        if rules.get("cost_settlement", {}).get("enabled", True):
            result = self._check_cost_settlement(project, rules["cost_settlement"])
            checks.append(result)
            w = rules["cost_settlement"]["weight"]
            total_weight += w
            if result["passed"]:
                earned_weight += w
            else:
                missing_items.extend(result.get("missing", []))
                recommendations.extend(result.get("recommendations", []))

        # 5. 项目文档检查
        if rules.get("document_completeness", {}).get("enabled", True):
            result = self._check_documents(project, rules["document_completeness"])
            checks.append(result)
            w = rules["document_completeness"]["weight"]
            total_weight += w
            if result["passed"]:
                earned_weight += w
            else:
                missing_items.extend(result.get("missing", []))
                recommendations.extend(result.get("recommendations", []))

        score = int((earned_weight / total_weight * 100) if total_weight > 0 else 0)
        ready = score == 100

        return {
            "ready": ready,
            "score": score,
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "checked_at": datetime.now().isoformat(),
            "checks": checks,
            "missing_items": missing_items,
            "recommendations": recommendations,
        }

    # ========================================================================
    # 各检查项实现
    # ========================================================================

    def _check_stages(self, project: Project, rule: dict) -> dict:
        """检查所有阶段是否完成"""
        required = rule.get("required_stages", ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"])

        # 优先检查阶段实例表（模板化阶段）
        stage_instances = (
            self.db.query(ProjectStageInstance)
            .filter(ProjectStageInstance.project_id == project.id)
            .all()
        )

        missing = []
        completed_stages = set()

        if stage_instances:
            for si in stage_instances:
                if si.status == "COMPLETED":
                    completed_stages.add(si.stage_code)
            for code in required:
                if code not in completed_stages:
                    missing.append(f"阶段 {code} 未完成")
        else:
            # 回退到传统阶段表
            stages = (
                self.db.query(ProjectStage)
                .filter(ProjectStage.project_id == project.id)
                .all()
            )
            for s in stages:
                if s.actual_end_date is not None:
                    completed_stages.add(s.stage_code)
            for code in required:
                if code not in completed_stages:
                    missing.append(f"阶段 {code} 未完成")

        passed = len(missing) == 0
        recs = []
        if not passed:
            recs.append(f"请完成剩余 {len(missing)} 个阶段后再提交结项")

        return {
            "key": "stage_completion",
            "label": rule.get("label", "阶段完成检查"),
            "passed": passed,
            "detail": f"已完成 {len(completed_stages)}/{len(required)} 个阶段",
            "completed_count": len(completed_stages),
            "total_count": len(required),
            "missing": missing,
            "recommendations": recs,
        }

    def _check_deliverables(self, project: Project, rule: dict) -> dict:
        """检查关键交付物是否上传"""
        required_types = rule.get("required_doc_types", [])

        # 检查节点交付物
        node_instances = (
            self.db.query(ProjectNodeInstance)
            .filter(
                ProjectNodeInstance.project_id == project.id,
                ProjectNodeInstance.node_type == "DELIVERABLE",
            )
            .all()
        )

        # 检查项目文档
        docs = (
            self.db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == project.id)
            .all()
        )

        uploaded_types = set()
        for doc in docs:
            if doc.doc_type:
                uploaded_types.add(doc.doc_type)
            if doc.doc_category:
                uploaded_types.add(doc.doc_category)

        # 节点交付物中已完成的也算
        completed_deliverable_nodes = sum(
            1 for n in node_instances if n.status == "COMPLETED"
        )
        total_deliverable_nodes = len(node_instances)

        missing = []
        for rt in required_types:
            if rt not in uploaded_types:
                missing.append(f"缺少交付物: {rt}")

        # 如果有交付物节点未完成也算缺失
        if total_deliverable_nodes > 0 and completed_deliverable_nodes < total_deliverable_nodes:
            missing.append(
                f"交付物节点未全部完成 ({completed_deliverable_nodes}/{total_deliverable_nodes})"
            )

        passed = len(missing) == 0
        recs = []
        if not passed:
            recs.append("请上传缺失的关键交付物文档")

        return {
            "key": "deliverable_upload",
            "label": rule.get("label", "关键交付物检查"),
            "passed": passed,
            "detail": f"已上传 {len(uploaded_types)} 类文档，交付物节点 {completed_deliverable_nodes}/{total_deliverable_nodes}",
            "uploaded_types": list(uploaded_types),
            "missing": missing,
            "recommendations": recs,
        }

    def _check_customer_acceptance(self, project: Project, rule: dict) -> dict:
        """检查客户验收是否签署"""
        missing = []

        # 方式1：检查审批实例中是否有验收类型已通过的
        acceptance_approval = (
            self.db.query(ApprovalInstance)
            .filter(
                ApprovalInstance.entity_type == "ACCEPTANCE",
                ApprovalInstance.entity_id == project.id,
                ApprovalInstance.status == "APPROVED",
            )
            .first()
        )

        # 方式2：检查项目文档中是否有验收报告
        acceptance_doc = (
            self.db.query(ProjectDocument)
            .filter(
                ProjectDocument.project_id == project.id,
                ProjectDocument.doc_type.in_(["验收报告", "验收签字", "ACCEPTANCE", "FINAL_ACCEPTANCE"]),
            )
            .first()
        )

        # 方式3：检查节点实例中验收相关节点
        acceptance_nodes = (
            self.db.query(ProjectNodeInstance)
            .filter(
                ProjectNodeInstance.project_id == project.id,
                ProjectNodeInstance.node_code.in_(["S06N01", "S08N01", "S21N01"]),
            )
            .all()
        )
        acceptance_node_completed = any(n.status == "COMPLETED" for n in acceptance_nodes)

        has_acceptance = bool(acceptance_approval or acceptance_doc or acceptance_node_completed)

        if not has_acceptance:
            missing.append("客户验收未签署或验收报告未上传")

        recs = []
        if not has_acceptance:
            recs.append("请完成客户验收流程并上传验收签字文件")

        return {
            "key": "customer_acceptance",
            "label": rule.get("label", "客户验收检查"),
            "passed": has_acceptance,
            "detail": "客户验收已完成" if has_acceptance else "客户验收未完成",
            "missing": missing,
            "recommendations": recs,
        }

    def _check_cost_settlement(self, project: Project, rule: dict) -> dict:
        """检查成本是否归集完成"""
        threshold = rule.get("cost_variance_threshold", 0.1)
        missing = []

        budget = float(project.budget_amount or 0)
        actual = float(project.actual_cost or 0)

        # 检查是否有成本记录
        cost_count = (
            self.db.query(func.count(ProjectCost.id))
            .filter(ProjectCost.project_id == project.id)
            .scalar()
        )

        has_cost_records = cost_count > 0

        # 检查成本偏差
        if budget > 0:
            variance_ratio = abs(budget - actual) / budget
            cost_reasonable = variance_ratio <= threshold
        else:
            cost_reasonable = actual == 0

        # 检查是否已开票 & 结尾款
        invoice_ok = project.invoice_issued or False
        payment_ok = project.final_payment_completed or False

        passed = has_cost_records and cost_reasonable
        if not has_cost_records:
            missing.append("项目无成本记录，成本尚未归集")
        if not cost_reasonable:
            variance_pct = (
                f"{variance_ratio * 100:.1f}%" if budget > 0 else "预算为0"
            )
            missing.append(f"成本偏差超过阈值 ({variance_pct} > {threshold * 100:.0f}%)")
        if not invoice_ok:
            missing.append("项目尚未开票")
        if not payment_ok:
            missing.append("尾款尚未结清")

        recs = []
        if not passed:
            recs.append("请确认所有成本已归集，并完成开票和尾款结算")

        return {
            "key": "cost_settlement",
            "label": rule.get("label", "成本归集检查"),
            "passed": passed,
            "detail": f"预算 {budget:,.0f}，实际 {actual:,.0f}，成本记录 {cost_count} 条",
            "budget": budget,
            "actual_cost": actual,
            "cost_records": cost_count,
            "invoice_issued": invoice_ok,
            "payment_completed": payment_ok,
            "missing": missing,
            "recommendations": recs,
        }

    def _check_documents(self, project: Project, rule: dict) -> dict:
        """检查项目文档是否齐全"""
        min_count = rule.get("min_doc_count", 5)
        required_cats = rule.get("required_categories", [])

        docs = (
            self.db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == project.id)
            .all()
        )

        doc_count = len(docs)
        existing_cats = set()
        for doc in docs:
            if doc.doc_category:
                existing_cats.add(doc.doc_category)
            if doc.doc_type:
                existing_cats.add(doc.doc_type)

        missing = []
        if doc_count < min_count:
            missing.append(f"文档数量不足 ({doc_count}/{min_count})")

        for cat in required_cats:
            if cat not in existing_cats:
                missing.append(f"缺少 {cat} 类文档")

        passed = len(missing) == 0
        recs = []
        if not passed:
            recs.append("请补充缺失的项目文档，确保文档归档完整")

        return {
            "key": "document_completeness",
            "label": rule.get("label", "项目文档检查"),
            "passed": passed,
            "detail": f"共 {doc_count} 份文档，覆盖 {len(existing_cats)} 个分类",
            "doc_count": doc_count,
            "categories": list(existing_cats),
            "missing": missing,
            "recommendations": recs,
        }


class ClosureNotificationService:
    """结项提醒自动推送服务"""

    def __init__(self, db: Session):
        self.db = db

    def notify_if_ready(self, project_id: int, readiness: dict) -> list[int]:
        """
        当项目满足结项条件时自动通知项目负责人

        Args:
            project_id: 项目ID
            readiness: check_readiness 的返回结果

        Returns:
            创建的通知ID列表
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return []

        notification_ids = []

        if readiness["ready"]:
            # 通知项目经理
            if project.pm_id:
                notif = self._create_notification(
                    user_id=project.pm_id,
                    project=project,
                    title=f"项目 {project.project_code} 已满足结项条件",
                    content=(
                        f"项目「{project.project_name}」已通过所有结项检查（得分 {readiness['score']}/100），"
                        f"可以提交结项申请。"
                    ),
                    priority="HIGH",
                    notification_type="PROJECT_CLOSURE_READY",
                )
                notification_ids.append(notif.id)

            # 通知创建人（如果不同于 PM）
            if project.created_by and project.created_by != project.pm_id:
                notif = self._create_notification(
                    user_id=project.created_by,
                    project=project,
                    title=f"项目 {project.project_code} 已满足结项条件",
                    content=(
                        f"项目「{project.project_name}」已通过所有结项检查，"
                        f"请通知项目经理提交结项申请。"
                    ),
                    priority="NORMAL",
                    notification_type="PROJECT_CLOSURE_READY",
                )
                notification_ids.append(notif.id)
        else:
            # 准备度 >= 80 但未完全通过，发提醒
            if readiness["score"] >= 80 and project.pm_id:
                missing_summary = "、".join(readiness["missing_items"][:3])
                notif = self._create_notification(
                    user_id=project.pm_id,
                    project=project,
                    title=f"项目 {project.project_code} 接近结项条件",
                    content=(
                        f"项目「{project.project_name}」结项准备度 {readiness['score']}%，"
                        f"还需完成: {missing_summary}"
                    ),
                    priority="NORMAL",
                    notification_type="PROJECT_CLOSURE_REMINDER",
                )
                notification_ids.append(notif.id)

        self.db.commit()
        return notification_ids

    def _create_notification(
        self,
        user_id: int,
        project: Project,
        title: str,
        content: str,
        priority: str,
        notification_type: str,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            notification_type=notification_type,
            source_type="project",
            source_id=project.id,
            title=title,
            content=content,
            priority=priority,
            link_url=f"/pmo/closure/{project.id}",
            link_params={"project_id": project.id},
            extra_data={
                "project_code": project.project_code,
                "project_name": project.project_name,
            },
        )
        self.db.add(notif)
        return notif


class LessonsCollectionService:
    """经验沉淀自动收集服务 — 结项时自动触发"""

    def __init__(self, db: Session):
        self.db = db

    def auto_collect(self, project_id: int, triggered_by: int) -> dict:
        """
        结项时自动触发经验沉淀收集

        Args:
            project_id: 项目ID
            triggered_by: 触发人ID

        Returns:
            收集结果: {review, lessons_count, best_practices_count}
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"error": "项目不存在"}

        # 检查是否已有结项复盘
        existing_review = (
            self.db.query(ProjectReview)
            .filter(
                ProjectReview.project_id == project_id,
                ProjectReview.review_type == "POST_MORTEM",
            )
            .first()
        )

        if existing_review:
            return {
                "review_id": existing_review.id,
                "review_no": existing_review.review_no,
                "already_exists": True,
                "message": "结项复盘报告已存在",
            }

        # 自动创建结项复盘报告模板
        review = self._create_review_template(project, triggered_by)

        # 自动生成经验教训条目（从项目数据中提取）
        lessons = self._extract_lessons(project, review)

        # 自动生成最佳实践建议
        practices = self._extract_best_practices(project, review)

        self.db.commit()

        return {
            "review_id": review.id,
            "review_no": review.review_no,
            "already_exists": False,
            "lessons_count": len(lessons),
            "best_practices_count": len(practices),
            "message": "已自动创建结项复盘模板并提取经验数据",
        }

    def _create_review_template(self, project: Project, triggered_by: int) -> ProjectReview:
        """创建结项复盘报告模板"""
        # 生成编号
        count = (
            self.db.query(func.count(ProjectReview.id))
            .filter(ProjectReview.project_id == project.id)
            .scalar()
        )
        review_no = f"REV-{project.project_code}-{count + 1:03d}"

        # 计算周期
        plan_days = None
        actual_days = None
        schedule_var = None
        if project.planned_start_date and project.planned_end_date:
            plan_days = (project.planned_end_date - project.planned_start_date).days
        if project.actual_start_date:
            end = project.actual_end_date or date.today()
            actual_days = (end - project.actual_start_date).days
        if plan_days and actual_days:
            schedule_var = actual_days - plan_days

        review = ProjectReview(
            review_no=review_no,
            project_id=project.id,
            project_code=project.project_code,
            review_date=date.today(),
            review_type="POST_MORTEM",
            plan_duration=plan_days,
            actual_duration=actual_days,
            schedule_variance=schedule_var,
            budget_amount=project.budget_amount,
            actual_cost=project.actual_cost,
            cost_variance=(
                project.budget_amount - project.actual_cost
                if project.budget_amount and project.actual_cost
                else None
            ),
            reviewer_id=triggered_by,
            reviewer_name="",  # 由前端/调用方填充
            status="DRAFT",
            ai_generated=True,
            success_factors="[待填写] 请总结项目成功因素",
            problems="[待填写] 请总结项目问题与教训",
            improvements="[待填写] 请提出改进建议",
            best_practices="[待填写] 请提炼最佳实践",
            conclusion="[待填写] 请填写复盘结论",
        )
        self.db.add(review)
        self.db.flush()  # 获取 ID
        return review

    def _extract_lessons(self, project: Project, review: ProjectReview) -> list[ProjectLesson]:
        """从项目数据中自动提取经验教训"""
        lessons = []

        # 1. 进度偏差分析
        if project.planned_end_date and project.actual_end_date:
            if project.actual_end_date > project.planned_end_date:
                delay_days = (project.actual_end_date - project.planned_end_date).days
                lessons.append(
                    ProjectLesson(
                        review_id=review.id,
                        project_id=project.id,
                        lesson_type="FAILURE",
                        title=f"项目延期 {delay_days} 天",
                        description=f"项目实际完成日期晚于计划 {delay_days} 天，需分析延期原因。",
                        category="schedule",
                        priority="HIGH" if delay_days > 30 else "MEDIUM",
                        improvement_action="[待填写] 请分析延期根因并提出改进措施",
                        status="OPEN",
                        ai_confidence=Decimal("0.8"),
                    )
                )

        # 2. 成本偏差分析
        budget = float(project.budget_amount or 0)
        actual = float(project.actual_cost or 0)
        if budget > 0 and actual > budget:
            overrun_pct = (actual - budget) / budget * 100
            lessons.append(
                ProjectLesson(
                    review_id=review.id,
                    project_id=project.id,
                    lesson_type="FAILURE",
                    title=f"成本超支 {overrun_pct:.1f}%",
                    description=f"实际成本 {actual:,.0f} 超出预算 {budget:,.0f}，超支率 {overrun_pct:.1f}%。",
                    category="cost",
                    priority="HIGH" if overrun_pct > 20 else "MEDIUM",
                    improvement_action="[待填写] 请分析超支原因并提出管控措施",
                    status="OPEN",
                    ai_confidence=Decimal("0.85"),
                )
            )
        elif budget > 0 and actual <= budget:
            savings_pct = (budget - actual) / budget * 100
            if savings_pct >= 5:
                lessons.append(
                    ProjectLesson(
                        review_id=review.id,
                        project_id=project.id,
                        lesson_type="SUCCESS",
                        title=f"成本节约 {savings_pct:.1f}%",
                        description=f"实际成本低于预算，节约率 {savings_pct:.1f}%，可总结成本管控经验。",
                        category="cost",
                        priority="LOW",
                        status="OPEN",
                        ai_confidence=Decimal("0.75"),
                    )
                )

        # 3. 按时完成经验
        if project.planned_end_date and project.actual_end_date:
            if project.actual_end_date <= project.planned_end_date:
                lessons.append(
                    ProjectLesson(
                        review_id=review.id,
                        project_id=project.id,
                        lesson_type="SUCCESS",
                        title="项目按时完成",
                        description="项目在计划工期内完成，请总结进度管控的成功经验。",
                        category="schedule",
                        priority="MEDIUM",
                        status="OPEN",
                        ai_confidence=Decimal("0.9"),
                    )
                )

        for lesson in lessons:
            self.db.add(lesson)

        return lessons

    def _extract_best_practices(
        self, project: Project, review: ProjectReview
    ) -> list[ProjectBestPractice]:
        """自动生成最佳实践建议条目"""
        practices = []

        # 按时且不超预算 → 管理最佳实践
        budget = float(project.budget_amount or 0)
        actual = float(project.actual_cost or 0)
        on_time = (
            project.planned_end_date
            and project.actual_end_date
            and project.actual_end_date <= project.planned_end_date
        )
        on_budget = budget > 0 and actual <= budget

        if on_time and on_budget:
            practices.append(
                ProjectBestPractice(
                    review_id=review.id,
                    project_id=project.id,
                    title="按时按预算交付",
                    description="项目在计划工期和预算范围内完成，具备良好的管控实践。",
                    context=f"项目类型: {project.project_type or '未知'}，行业: {project.industry or '未知'}",
                    implementation="[待填写] 请描述具体管控方法",
                    benefits="按时交付提升客户满意度，预算内完成保障利润",
                    category="管理",
                    is_reusable=True,
                    applicable_project_types=[project.project_type] if project.project_type else [],
                    validation_status="PENDING",
                    status="ACTIVE",
                )
            )

        for p in practices:
            self.db.add(p)

        return practices
