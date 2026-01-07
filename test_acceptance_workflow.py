#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收管理模块端到端测试

使用 FastAPI TestClient 按以下顺序验证接口是否可用：
1. 管理员登录获取 Token
2. 创建项目、机台
3. 创建带分类/检查项的验收模板
4. 基于模板创建验收单并复制检查项
5. 启动验收、更新检查项结果、完成验收
6. 查询最终统计

脚本会自动清理自己创建的数据库记录，方便多次重复执行。
"""

from __future__ import annotations

import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, Optional

from fastapi.testclient import TestClient

from app.main import app
from app.models.base import get_session
from app.models.project import Project, Machine, ProjectStage, ProjectStatus
from app.models.acceptance import (
    AcceptanceTemplate,
    TemplateCategory,
    TemplateCheckItem,
    AcceptanceOrder,
    AcceptanceOrderItem,
    AcceptanceIssue,
    IssueFollowUp,
    AcceptanceSignature,
    AcceptanceReport,
)
from app.core.config import settings


class Colors:
    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    CYAN = "\033[0;36m"
    YELLOW = "\033[0;33m"
    NC = "\033[0m"


def log_success(message: str) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")


def log_info(message: str) -> None:
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.NC}")


def log_warning(message: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")


def log_error(message: str) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.NC}")


def cleanup_records(created: Dict[str, Optional[int]]) -> None:
    session = get_session()
    try:
        if created.get("order_id"):
            issue_ids = [
                iid
                for (iid,) in session.query(AcceptanceIssue.id).filter(
                    AcceptanceIssue.order_id == created["order_id"]
                )
            ]
            if issue_ids:
                session.query(IssueFollowUp).filter(
                    IssueFollowUp.issue_id.in_(issue_ids)
                ).delete(synchronize_session=False)
            reports = session.query(AcceptanceReport).filter(
                AcceptanceReport.order_id == created["order_id"]
            ).all()
            for rpt in reports:
                if rpt.file_path:
                    file_path = os.path.join(settings.UPLOAD_DIR, rpt.file_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            session.query(AcceptanceSignature).filter(
                AcceptanceSignature.order_id == created["order_id"]
            ).delete(synchronize_session=False)
            session.query(AcceptanceReport).filter(
                AcceptanceReport.order_id == created["order_id"]
            ).delete(synchronize_session=False)
            session.query(AcceptanceIssue).filter(
                AcceptanceIssue.order_id == created["order_id"]
            ).delete(synchronize_session=False)
            session.query(AcceptanceOrderItem).filter(
                AcceptanceOrderItem.order_id == created["order_id"]
            ).delete(synchronize_session=False)
            session.query(AcceptanceOrder).filter(
                AcceptanceOrder.id == created["order_id"]
            ).delete(synchronize_session=False)

        if created.get("template_id"):
            category_ids = [
                cid
                for (cid,) in session.query(TemplateCategory.id).filter(
                    TemplateCategory.template_id == created["template_id"]
                )
            ]
            if category_ids:
                session.query(TemplateCheckItem).filter(
                    TemplateCheckItem.category_id.in_(category_ids)
                ).delete(synchronize_session=False)
                session.query(TemplateCategory).filter(
                    TemplateCategory.id.in_(category_ids)
                ).delete(synchronize_session=False)
            session.query(AcceptanceTemplate).filter(
                AcceptanceTemplate.id == created["template_id"]
            ).delete(synchronize_session=False)

        if created.get("machine_id"):
            session.query(Machine).filter(
                Machine.id == created["machine_id"]
            ).delete(synchronize_session=False)

        if created.get("project_id"):
            stage_ids = [
                sid
                for (sid,) in session.query(ProjectStage.id).filter(
                    ProjectStage.project_id == created["project_id"]
                )
            ]
            if stage_ids:
                session.query(ProjectStatus).filter(
                    ProjectStatus.stage_id.in_(stage_ids)
                ).delete(synchronize_session=False)
                session.query(ProjectStage).filter(
                    ProjectStage.id.in_(stage_ids)
                ).delete(synchronize_session=False)
            session.query(Project).filter(
                Project.id == created["project_id"]
            ).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()


def run_acceptance_flow() -> Dict[str, any]:
    created = {"project_id": None, "machine_id": None, "template_id": None, "order_id": None}
    summary: Dict[str, any] = {}

    with TestClient(app) as client:
        try:
            log_info("登录管理员账户...")
            login_resp = client.post(
                "/api/v1/auth/login",
                data={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            login_resp.raise_for_status()
            token = login_resp.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            log_success("登录成功")

            suffix = datetime.now().strftime("%m%d%H%M%S")
            today = date.today()

            log_info("创建测试项目...")
            project_payload = {
                "project_code": f"ACPT-PROJ-{suffix}",
                "project_name": f"验收测试项目{suffix}",
                "short_name": "验收测试",
                "project_type": "CUSTOM",
                "contract_amount": 200000,
                "budget_amount": 150000,
                "planned_start_date": today.isoformat(),
                "planned_end_date": (today + timedelta(days=30)).isoformat(),
                "contract_date": today.isoformat(),
                "machine_count": 1,
                "description": "验收流程自动化测试数据",
            }
            project_resp = client.post("/api/v1/projects/", json=project_payload, headers=headers)
            project_resp.raise_for_status()
            project = project_resp.json()
            created["project_id"] = project["id"]
            log_success(f"项目创建成功：{project['project_code']}")

            log_info("创建机台...")
            machine_payload = {
                "machine_code": f"ACPT-MC-{suffix}",
                "machine_name": "验收测试产线",
                "project_id": created["project_id"],
                "machine_no": 1,
                "machine_type": "装配线",
                "specification": "测试工位",
            }
            machine_resp = client.post("/api/v1/machines/", json=machine_payload, headers=headers)
            machine_resp.raise_for_status()
            machine = machine_resp.json()
            created["machine_id"] = machine["id"]
            log_success(f"机台创建成功：{machine['machine_code']}")

            log_info("创建验收模板（含分类、检查项）...")
            template_payload = {
                "template_code": f"ACPT-TPL-{suffix}",
                "template_name": f"FAT通用模板{suffix}",
                "acceptance_type": "FAT",
                "equipment_type": "装配线",
                "version": "1.0",
                "description": "脚本生成",
                "categories": [
                    {
                        "category_code": "ELEC",
                        "category_name": "电气安全",
                        "weight": 60,
                        "sort_order": 1,
                        "is_required": True,
                        "description": "电气参数检查",
                        "check_items": [
                            {
                                "item_code": "ELEC-001",
                                "item_name": "绝缘电阻",
                                "check_method": "兆欧表测试",
                                "acceptance_criteria": ">= 2MΩ",
                                "standard_value": ">=2MΩ",
                                "tolerance_min": "2MΩ",
                                "unit": "MΩ",
                                "is_required": True,
                                "is_key_item": True,
                                "sort_order": 1,
                            }
                        ],
                    },
                    {
                        "category_code": "FUNC",
                        "category_name": "功能验证",
                        "weight": 40,
                        "sort_order": 2,
                        "is_required": True,
                        "description": "节拍与良率",
                        "check_items": [
                            {
                                "item_code": "FUNC-001",
                                "item_name": "节拍测试",
                                "check_method": "满载运行10分钟",
                                "acceptance_criteria": "节拍<=1.0s",
                                "standard_value": "1.0",
                                "tolerance_max": "1.0",
                                "unit": "s",
                                "is_required": True,
                                "sort_order": 1,
                            }
                        ],
                    },
                ],
            }
            template_resp = client.post("/api/v1/acceptance-templates", json=template_payload, headers=headers)
            template_resp.raise_for_status()
            template = template_resp.json()
            created["template_id"] = template["id"]
            log_success(f"验收模板创建成功：{template['template_code']}")

            log_info("创建验收单并复制检查项...")
            order_payload = {
                "project_id": created["project_id"],
                "machine_id": created["machine_id"],
                "acceptance_type": "FAT",
                "template_id": created["template_id"],
                "planned_date": today.isoformat(),
                "location": "FAT测试车间",
            }
            order_resp = client.post("/api/v1/acceptance-orders", json=order_payload, headers=headers)
            order_resp.raise_for_status()
            order = order_resp.json()
            created["order_id"] = order["id"]
            log_success(f"验收单创建成功：{order['order_no']}，检查项 {order['total_items']}")

            items_resp = client.get(f"/api/v1/acceptance-orders/{order['id']}/items", headers=headers)
            items_resp.raise_for_status()
            items = items_resp.json()
            log_info(f"模板检查项复制完成，共 {len(items)} 条")

            log_info("开始验收...")
            start_resp = client.put(
                f"/api/v1/acceptance-orders/{order['id']}/start",
                json={"location": "FAT测试线"},
                headers=headers,
            )
            start_resp.raise_for_status()
            log_success("验收单状态更新为 IN_PROGRESS")

            for idx, item in enumerate(items, start=1):
                payload = {
                    "result_status": "PASSED" if idx == 1 else "FAILED",
                    "actual_value": "0.98" if idx == 1 else "1.05",
                    "deviation": "0" if idx == 1 else "+0.05",
                    "remark": f"脚本自动更新-序号{idx}",
                }
                result_resp = client.put(
                    f"/api/v1/acceptance-items/{item['id']}",
                    json=payload,
                    headers=headers,
                )
                result_resp.raise_for_status()
            log_success("所有检查项均已更新结果")

            latest_items = client.get(
                f"/api/v1/acceptance-orders/{order['id']}/items", headers=headers
            ).json()
            pending = [i for i in latest_items if i["result_status"] == "PENDING"]
            if pending:
                log_warning(f"仍有 {len(pending)} 个检查项未完成: {pending}")
            issue_summary = None
            failed_item = next((i for i in latest_items if i["result_status"] == "FAILED"), None)
            if failed_item:
                log_info("创建并跟踪验收问题...")
                issue_payload = {
                    "order_id": order["id"],
                    "order_item_id": failed_item["id"],
                    "issue_type": "DEFECT",
                    "severity": "MAJOR",
                    "title": "脚本自动创建-关键缺陷",
                    "description": "脚本检测到失败项，自动创建问题并跟踪整改。",
                    "is_blocking": True,
                }
                issue_resp = client.post(
                    f"/api/v1/acceptance-orders/{order['id']}/issues",
                    json=issue_payload,
                    headers=headers,
                )
                issue_resp.raise_for_status()
                issue = issue_resp.json()
                log_success(f"验收问题创建成功：{issue['issue_no']}")

                issues_list = client.get(
                    f"/api/v1/acceptance-orders/{order['id']}/issues",
                    headers=headers,
                )
                issues_list.raise_for_status()
                log_info(f"当前验收问题数量：{len(issues_list.json())}")

                update_resp = client.put(
                    f"/api/v1/acceptance-issues/{issue['id']}",
                    json={
                        "status": "IN_PROGRESS",
                        "solution": "整改进行中，预计1日内完成",
                    },
                    headers=headers,
                )
                update_resp.raise_for_status()
                log_success("验收问题状态更新为 IN_PROGRESS")

                close_resp = client.put(
                    f"/api/v1/acceptance-issues/{issue['id']}/close",
                    params={"solution": "整改完成，复检通过"},
                    headers=headers,
                )
                close_resp.raise_for_status()
                closed_issue = close_resp.json()
                log_success("验收问题已关闭")

                issue_summary = {
                    "issue_no": closed_issue["issue_no"],
                    "status": closed_issue["status"],
                    "resolved_at": closed_issue["resolved_at"],
                }

            log_info("完成验收并生成结论...")
            overall_result = "FAILED" if any(i["result_status"] == "FAILED" for i in latest_items) else "PASSED"
            complete_payload = {
                "overall_result": overall_result,
                "conclusion": "脚本测试完成，生成验收结论",
                "conditions": "存在失败项需后续整改" if overall_result == "FAILED" else None,
            }
            complete_resp = client.put(
                f"/api/v1/acceptance-orders/{order['id']}/complete",
                json=complete_payload,
                headers=headers,
            )
            complete_resp.raise_for_status()
            log_success("验收单已完成")

            final_order = client.get(f"/api/v1/acceptance-orders/{order['id']}", headers=headers)
            final_order.raise_for_status()
            final_data = final_order.json()

            log_info("为完成的验收单添加签字...")
            signatures_payload = [
                {
                    "order_id": order["id"],
                    "signer_type": "QA",
                    "signer_role": "QA Lead",
                    "signer_name": "系统QA",
                    "signer_company": "内部质检部",
                    "signature_data": "QA_SIGNATURE",
                },
                {
                    "order_id": order["id"],
                    "signer_type": "CUSTOMER",
                    "signer_role": "客户代表",
                    "signer_name": "客户张经理",
                    "signer_company": "客户公司",
                    "signature_data": "CUSTOMER_SIGNATURE",
                },
            ]
            for payload in signatures_payload:
                sig_resp = client.post(
                    f"/api/v1/acceptance-orders/{order['id']}/signatures",
                    json=payload,
                    headers=headers,
                )
                sig_resp.raise_for_status()
            log_success("验收签字已完成")

            signatures_resp = client.get(
                f"/api/v1/acceptance-orders/{order['id']}/signatures",
                headers=headers,
            )
            signatures_resp.raise_for_status()
            signatures_data = signatures_resp.json()
            log_info(f"当前签字记录数：{len(signatures_data)}")

            log_info("生成验收报告...")
            report_resp = client.post(
                f"/api/v1/acceptance-orders/{order['id']}/report",
                json={
                    "report_type": "FINAL",
                    "include_signatures": True,
                },
                headers=headers,
            )
            report_resp.raise_for_status()
            report = report_resp.json()
            log_success(f"验收报告生成成功：{report['report_no']}")

            download_resp = client.get(
                f"/api/v1/acceptance-reports/{report['id']}/download",
                headers=headers,
            )
            download_resp.raise_for_status()
            snippet = download_resp.text[:60].replace("\n", " ")
            log_success(f"验收报告下载接口可用，内容片段：{snippet}...")

            summary = {
                "order_no": final_data["order_no"],
                "status": final_data["status"],
                "passed_items": final_data["passed_items"],
                "failed_items": final_data["failed_items"],
                "pass_rate": float(final_data.get("pass_rate", 0)),
                "overall_result": final_data.get("overall_result"),
                "issues": issue_summary,
                "signature_count": len(signatures_data),
                "report_no": report["report_no"],
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        finally:
            log_info("清理测试数据...")
            cleanup_records(created)
            log_success("测试数据清理完成")
    return summary


if __name__ == "__main__":
    try:
        print("===== 验收管理端到端测试开始 =====")
        summary = run_acceptance_flow()
        log_success("验收流程测试完成")
        print("最终统计：")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    except Exception as exc:
        log_error(f"验收流程测试失败: {exc}")
        raise
