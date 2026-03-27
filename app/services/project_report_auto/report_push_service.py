# -*- coding: utf-8 -*-
"""
报告推送服务

生成后自动：
- 发送给项目负责人
- 发送给相关干系人
- 支持导出 PDF/Excel
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.project.core import Project
from app.models.project.team import ProjectMember
from app.models.report_center import ReportGeneration
from app.models.user import User
from app.services.channel_handlers.base import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
)
from app.services.unified_notification_service import NotificationService

logger = logging.getLogger(__name__)

# 导出文件存放目录
EXPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "reports", "exports")


class ReportPushService:
    """报告推送服务"""

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def push_report(
        self,
        report_id: int,
        recipient_user_ids: Optional[List[int]] = None,
        channels: Optional[List[str]] = None,
        export_formats: Optional[List[str]] = None,
        send_to_pm: bool = True,
        send_to_stakeholders: bool = True,
    ) -> Dict[str, Any]:
        """
        推送报告

        Args:
            report_id: 报告生成记录ID
            recipient_user_ids: 额外的接收人ID列表
            channels: 通知渠道（默认 system + email）
            export_formats: 导出格式列表，如 ["PDF", "XLSX"]
            send_to_pm: 是否发送给项目经理
            send_to_stakeholders: 是否发送给项目干系人

        Returns:
            推送结果
        """
        generation = (
            self.db.query(ReportGeneration)
            .filter(ReportGeneration.id == report_id)
            .first()
        )
        if not generation:
            raise ValueError(f"报告记录不存在: {report_id}")

        if generation.status not in ("DRAFT", "GENERATED", "REVIEWED"):
            raise ValueError(f"报告状态不允许推送: {generation.status}")

        project_id = generation.scope_id
        report_data = generation.report_data or {}

        # 确定接收人
        recipients = self._resolve_recipients(
            project_id, recipient_user_ids, send_to_pm, send_to_stakeholders
        )

        if not recipients:
            return {
                "success": False,
                "message": "没有找到接收人",
                "recipients": [],
                "exports": [],
            }

        # 导出文件
        export_results = []
        if export_formats:
            export_results = self._export_report(generation, export_formats)

        # 发送通知
        channels = channels or [NotificationChannel.SYSTEM, NotificationChannel.EMAIL]
        notification_results = self._send_notifications(
            generation, recipients, channels, export_results
        )

        # 更新状态
        generation.status = "SENT"
        self.db.commit()

        return {
            "success": True,
            "message": f"报告已推送给 {len(recipients)} 位接收人",
            "report_id": report_id,
            "recipients": [
                {"user_id": u.id, "user_name": getattr(u, "real_name", str(u.id))}
                for u in recipients
            ],
            "exports": export_results,
            "notification_summary": {
                "total": len(notification_results),
                "success": sum(1 for r in notification_results if r.get("success")),
                "failed": sum(1 for r in notification_results if not r.get("success")),
            },
        }

    def export_only(
        self,
        report_id: int,
        formats: List[str],
    ) -> List[Dict[str, Any]]:
        """仅导出报告（不推送）"""
        generation = (
            self.db.query(ReportGeneration)
            .filter(ReportGeneration.id == report_id)
            .first()
        )
        if not generation:
            raise ValueError(f"报告记录不存在: {report_id}")

        return self._export_report(generation, formats)

    def update_report_data(
        self,
        report_id: int,
        updated_data: Dict[str, Any],
        editor_id: int,
    ) -> Dict[str, Any]:
        """
        手动编辑报告数据（编辑后再发送）

        Args:
            report_id: 报告ID
            updated_data: 更新的数据（部分更新，合并到现有 report_data）
            editor_id: 编辑人ID

        Returns:
            更新后的报告数据
        """
        generation = (
            self.db.query(ReportGeneration)
            .filter(ReportGeneration.id == report_id)
            .first()
        )
        if not generation:
            raise ValueError(f"报告记录不存在: {report_id}")

        if generation.status == "SENT":
            raise ValueError("已推送的报告不允许编辑，请重新生成")

        current_data = generation.report_data or {}

        # 合并 sections
        if "sections" in updated_data:
            current_sections = current_data.get("sections", {})
            current_sections.update(updated_data.pop("sections"))
            current_data["sections"] = current_sections

        # 合并 summary
        if "summary" in updated_data:
            current_summary = current_data.get("summary", {})
            current_summary.update(updated_data.pop("summary"))
            current_data["summary"] = current_summary

        # 其余字段直接覆盖
        current_data.update(updated_data)
        current_data["last_edited_by"] = editor_id
        current_data["last_edited_at"] = datetime.now().isoformat()

        generation.report_data = current_data
        generation.status = "REVIEWED"
        self.db.commit()
        self.db.refresh(generation)

        return current_data

    # ===================== internal =====================

    def _resolve_recipients(
        self,
        project_id: Optional[int],
        extra_ids: Optional[List[int]],
        send_to_pm: bool,
        send_to_stakeholders: bool,
    ) -> List[User]:
        """解析接收人列表"""
        user_ids: set = set()

        if extra_ids:
            user_ids.update(extra_ids)

        if project_id:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if project:
                # 项目经理
                if send_to_pm and getattr(project, "pm_id", None):
                    user_ids.add(project.pm_id)

                # 干系人（项目成员中的负责人角色）
                if send_to_stakeholders:
                    members = (
                        self.db.query(ProjectMember)
                        .filter(
                            ProjectMember.project_id == project_id,
                            ProjectMember.is_active == True,  # noqa: E712
                        )
                        .all()
                    )
                    # 包含 lead 和管理角色
                    for m in members:
                        if getattr(m, "is_lead", False):
                            user_ids.add(m.user_id)
                        role = getattr(m, "role_code", "") or ""
                        if role.upper() in (
                            "PM",
                            "PROJECT_MANAGER",
                            "TEAM_LEAD",
                            "DIRECTOR",
                            "SPONSOR",
                        ):
                            user_ids.add(m.user_id)

        if not user_ids:
            return []

        return self.db.query(User).filter(User.id.in_(list(user_ids))).all()

    def _send_notifications(
        self,
        generation: ReportGeneration,
        recipients: List[User],
        channels: List[str],
        export_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """发送通知"""
        results = []
        report_title = generation.report_title or "项目报告"
        report_type_label = (
            "周报" if generation.report_type == "PROJECT_WEEKLY" else "月报"
        )

        # 附件信息
        attachment_info = ""
        if export_results:
            formats = [e["format"] for e in export_results if e.get("success")]
            if formats:
                attachment_info = f"\n导出格式：{', '.join(formats)}"

        for user in recipients:
            try:
                request = NotificationRequest(
                    recipient_id=user.id,
                    notification_type="report_push",
                    category="project",
                    title=f"项目{report_type_label}已生成: {report_title}",
                    content=(
                        f"您收到一份项目{report_type_label}，请查收。\n"
                        f"报告期间：{generation.period_start} ~ {generation.period_end}"
                        f"{attachment_info}"
                    ),
                    priority=NotificationPriority.NORMAL,
                    channels=channels,
                    source_type="report_generation",
                    source_id=generation.id,
                    link_url=f"/report-center/view/{generation.id}",
                    force_send=True,
                )
                result = self.notification_service.send_notification(request)
                results.append(result)
            except Exception as e:
                logger.error(f"发送通知给用户 {user.id} 失败: {e}")
                results.append({"success": False, "error": str(e), "user_id": user.id})

        return results

    def _export_report(
        self, generation: ReportGeneration, formats: List[str]
    ) -> List[Dict[str, Any]]:
        """导出报告为 PDF/Excel"""
        results = []
        report_data = generation.report_data or {}
        report_title = generation.report_title or "项目报告"

        os.makedirs(EXPORT_DIR, exist_ok=True)

        for fmt in formats:
            fmt_upper = fmt.upper()
            try:
                if fmt_upper == "XLSX":
                    result = self._export_excel(generation, report_data, report_title)
                elif fmt_upper == "PDF":
                    result = self._export_pdf(generation, report_data, report_title)
                else:
                    result = {"format": fmt_upper, "success": False, "error": f"不支持的格式: {fmt}"}
                results.append(result)
            except Exception as e:
                logger.error(f"导出 {fmt_upper} 失败: {e}")
                results.append({"format": fmt_upper, "success": False, "error": str(e)})

        # 记录导出信息
        if results:
            successful = [r for r in results if r.get("success")]
            if successful:
                generation.export_format = ",".join(r["format"] for r in successful)
                generation.export_path = successful[0].get("path", "")
                generation.exported_at = datetime.now()
                self.db.commit()

        return results

    def _export_excel(
        self,
        generation: ReportGeneration,
        report_data: Dict[str, Any],
        title: str,
    ) -> Dict[str, Any]:
        """导出 Excel，复用 ReportExcelService"""
        from app.services.report_excel_service import ReportExcelService

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{generation.id}_{timestamp}.xlsx"
        filepath = os.path.join(EXPORT_DIR, filename)

        excel_service = ReportExcelService()
        excel_service.generate_report_excel(
            data=report_data,
            output_path=filepath,
            title=title,
        )

        return {
            "format": "XLSX",
            "success": True,
            "path": filepath,
            "filename": filename,
        }

    def _export_pdf(
        self,
        generation: ReportGeneration,
        report_data: Dict[str, Any],
        title: str,
    ) -> Dict[str, Any]:
        """导出 PDF，复用 PdfExportService"""
        from app.services.pdf_export_service import PdfExportService

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{generation.id}_{timestamp}.pdf"
        filepath = os.path.join(EXPORT_DIR, filename)

        pdf_service = PdfExportService()
        pdf_service.generate_report_pdf(
            data=report_data,
            output_path=filepath,
            title=title,
        )

        return {
            "format": "PDF",
            "success": True,
            "path": filepath,
            "filename": filename,
        }
