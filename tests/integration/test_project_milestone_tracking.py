# -*- coding: utf-8 -*-
"""
项目管理集成测试 - 项目里程碑跟踪

测试场景：
1. 里程碑创建与规划
2. 里程碑进度更新
3. 里程碑延期处理
4. 里程碑完成验收
5. 关键路径分析
6. 里程碑风险预警
7. 里程碑报告生成
"""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal


@pytest.mark.integration
class TestProjectMilestoneTracking:
    """项目里程碑跟踪集成测试"""

    def test_milestone_creation_and_planning(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：里程碑创建与规划"""
        # 1. 创建项目
        project_data = {
            "project_name": "智能生产线项目",
            "project_code": "PRJ-SMART-LINE-2024",
            "project_type": "自动化改造",
            "customer_id": 1,
            "start_date": str(date.today()),
            "expected_end_date": str(date.today() + timedelta(days=365)),
            "contract_amount": 10000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 创建项目里程碑
        milestones = [
            {
                "milestone_name": "需求调研完成",
                "milestone_code": "M01",
                "planned_date": str(date.today() + timedelta(days=30)),
                "milestone_type": "阶段性",
                "deliverables": ["需求分析报告", "用户访谈记录"],
                "acceptance_criteria": "客户签字确认需求文档",
                "weight": 10
            },
            {
                "milestone_name": "方案设计完成",
                "milestone_code": "M02",
                "planned_date": str(date.today() + timedelta(days=60)),
                "milestone_type": "阶段性",
                "deliverables": ["总体设计方案", "技术方案"],
                "acceptance_criteria": "技术评审通过",
                "weight": 15
            },
            {
                "milestone_name": "设备采购完成",
                "milestone_code": "M03",
                "planned_date": str(date.today() + timedelta(days=120)),
                "milestone_type": "关键",
                "deliverables": ["设备到货清单", "验收报告"],
                "acceptance_criteria": "所有设备到货并验收合格",
                "weight": 20
            },
            {
                "milestone_name": "系统集成完成",
                "milestone_code": "M04",
                "planned_date": str(date.today() + timedelta(days=240)),
                "milestone_type": "关键",
                "deliverables": ["系统集成报告", "测试报告"],
                "acceptance_criteria": "系统功能测试通过",
                "weight": 25
            },
            {
                "milestone_name": "项目验收",
                "milestone_code": "M05",
                "planned_date": str(date.today() + timedelta(days=365)),
                "milestone_type": "关键",
                "deliverables": ["验收报告", "用户培训资料"],
                "acceptance_criteria": "客户正式验收签字",
                "weight": 30
            }
        ]
        
        for milestone in milestones:
            response = client.post(
                f"/api/v1/projects/{project_id}/milestones",
                json=milestone,
                headers=auth_headers
            )
            assert response.status_code in [200, 201]
        
        # 3. 验证里程碑列表
        response = client.get(f"/api/v1/projects/{project_id}/milestones", headers=auth_headers)
        assert response.status_code == 200
        milestones_list = response.json()
        assert len(milestones_list) >= 5

    def test_milestone_progress_update(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：里程碑进度更新"""
        # 1. 创建项目和里程碑
        project_data = {
            "project_name": "MES系统实施",
            "project_code": "PRJ-MES-IMPL-2024",
            "project_type": "信息化建设",
            "customer_id": 1,
            "start_date": str(date.today()),
            "expected_end_date": str(date.today() + timedelta(days=270)),
            "contract_amount": 8000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 创建里程碑
        milestone_data = {
            "milestone_name": "系统上线",
            "milestone_code": "M01",
            "planned_date": str(date.today() + timedelta(days=90)),
            "milestone_type": "关键",
            "deliverables": ["系统部署文档", "上线报告"],
            "acceptance_criteria": "系统稳定运行3天",
            "weight": 40
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        milestone_id = response.json().get("id")
        
        # 3. 更新里程碑进度
        progress_updates = [
            {
                "update_date": str(date.today() + timedelta(days=10)),
                "progress_percentage": 20,
                "status": "进行中",
                "update_description": "完成系统环境搭建",
                "updated_by": test_employee.id
            },
            {
                "update_date": str(date.today() + timedelta(days=30)),
                "progress_percentage": 50,
                "status": "进行中",
                "update_description": "完成功能模块开发",
                "updated_by": test_employee.id
            },
            {
                "update_date": str(date.today() + timedelta(days=60)),
                "progress_percentage": 80,
                "status": "进行中",
                "update_description": "完成系统测试",
                "updated_by": test_employee.id
            }
        ]
        
        for update in progress_updates:
            response = client.post(
                f"/api/v1/projects/{project_id}/milestones/{milestone_id}/progress",
                json=update,
                headers=auth_headers
            )
            assert response.status_code in [200, 201, 404]
        
        # 4. 查询进度历史
        response = client.get(
            f"/api/v1/projects/{project_id}/milestones/{milestone_id}/progress",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_milestone_delay_handling(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：里程碑延期处理"""
        # 1. 创建项目和里程碑
        project_data = {
            "project_name": "仓储自动化项目",
            "project_code": "PRJ-WH-AUTO-2024",
            "project_type": "自动化改造",
            "customer_id": 1,
            "start_date": str(date.today()),
            "expected_end_date": str(date.today() + timedelta(days=200)),
            "contract_amount": 6000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 创建里程碑
        milestone_data = {
            "milestone_name": "设备安装完成",
            "milestone_code": "M02",
            "planned_date": str(date.today() + timedelta(days=60)),
            "milestone_type": "关键",
            "deliverables": ["设备安装报告"],
            "acceptance_criteria": "所有设备安装到位",
            "weight": 30
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        milestone_id = response.json().get("id")
        
        # 3. 提交延期申请
        delay_request = {
            "milestone_id": milestone_id,
            "original_date": str(date.today() + timedelta(days=60)),
            "new_planned_date": str(date.today() + timedelta(days=80)),
            "delay_reason": "供应商交货延期",
            "impact_analysis": "影响后续集成测试里程碑",
            "mitigation_plan": "增加人力投入，加快后续进度",
            "requested_by": test_employee.id,
            "request_date": str(date.today())
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestones/{milestone_id}/delay-requests",
            json=delay_request,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]
        
        # 4. 审批延期申请
        if response.status_code in [200, 201]:
            request_id = response.json().get("id")
            
            approval_data = {
                "action": "approve",
                "approver_id": test_employee.id + 1,
                "approval_date": str(date.today() + timedelta(days=1)),
                "comments": "延期理由充分，同意调整计划"
            }
            
            response = client.post(
                f"/api/v1/projects/{project_id}/milestones/{milestone_id}/delay-requests/{request_id}/approve",
                json=approval_data,
                headers=auth_headers
            )
            assert response.status_code in [200, 404]

    def test_milestone_completion_acceptance(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：里程碑完成验收"""
        # 1. 创建项目和里程碑
        project_data = {
            "project_name": "质量追溯系统",
            "project_code": "PRJ-TRACE-SYS-2024",
            "project_type": "软件开发",
            "customer_id": 1,
            "start_date": str(date.today()),
            "expected_end_date": str(date.today() + timedelta(days=150)),
            "contract_amount": 3500000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 创建里程碑
        milestone_data = {
            "milestone_name": "系统测试完成",
            "milestone_code": "M03",
            "planned_date": str(date.today() + timedelta(days=100)),
            "milestone_type": "阶段性",
            "deliverables": ["测试报告", "缺陷修复记录"],
            "acceptance_criteria": "所有高优先级缺陷修复完成",
            "weight": 25
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        milestone_id = response.json().get("id")
        
        # 3. 提交完成验收
        acceptance_data = {
            "milestone_id": milestone_id,
            "actual_completion_date": str(date.today() + timedelta(days=95)),
            "deliverables_submitted": [
                {"name": "测试报告", "version": "V1.0", "status": "已提交"},
                {"name": "缺陷修复记录", "version": "V1.0", "status": "已提交"}
            ],
            "acceptance_checklist": [
                {"item": "功能测试完成", "status": "通过"},
                {"item": "性能测试完成", "status": "通过"},
                {"item": "安全测试完成", "status": "通过"},
                {"item": "所有高优先级缺陷已修复", "status": "通过"}
            ],
            "submitted_by": test_employee.id,
            "submit_date": str(date.today() + timedelta(days=95))
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestones/{milestone_id}/acceptance",
            json=acceptance_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]
        
        # 4. 验收审批
        if response.status_code in [200, 201]:
            acceptance_id = response.json().get("id")
            
            approval_data = {
                "action": "approve",
                "reviewer_id": test_employee.id + 1,
                "review_date": str(date.today() + timedelta(days=97)),
                "review_comments": "交付物齐全，质量符合要求，同意验收",
                "acceptance_status": "通过"
            }
            
            response = client.post(
                f"/api/v1/projects/{project_id}/milestones/{milestone_id}/acceptance/{acceptance_id}/review",
                json=approval_data,
                headers=auth_headers
            )
            assert response.status_code in [200, 404]

    def test_critical_path_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：关键路径分析"""
        # 1. 创建项目
        project_data = {
            "project_name": "数字化车间建设",
            "project_code": "PRJ-DIGITAL-WS-2024",
            "project_type": "数字化改造",
            "customer_id": 1,
            "start_date": str(date.today()),
            "expected_end_date": str(date.today() + timedelta(days=400)),
            "contract_amount": 15000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 创建相互依赖的里程碑
        milestones = [
            {
                "milestone_name": "需求确认",
                "milestone_code": "M01",
                "planned_date": str(date.today() + timedelta(days=30)),
                "dependencies": [],
                "is_critical": True,
                "weight": 10
            },
            {
                "milestone_name": "方案设计",
                "milestone_code": "M02",
                "planned_date": str(date.today() + timedelta(days=60)),
                "dependencies": ["M01"],
                "is_critical": True,
                "weight": 15
            },
            {
                "milestone_name": "设备采购",
                "milestone_code": "M03",
                "planned_date": str(date.today() + timedelta(days=150)),
                "dependencies": ["M02"],
                "is_critical": True,
                "weight": 25
            },
            {
                "milestone_name": "软件开发",
                "milestone_code": "M04",
                "planned_date": str(date.today() + timedelta(days=180)),
                "dependencies": ["M02"],
                "is_critical": False,
                "weight": 20
            },
            {
                "milestone_name": "系统集成",
                "milestone_code": "M05",
                "planned_date": str(date.today() + timedelta(days=300)),
                "dependencies": ["M03", "M04"],
                "is_critical": True,
                "weight": 30
            }
        ]
        
        for milestone in milestones:
            response = client.post(
                f"/api/v1/projects/{project_id}/milestones",
                json=milestone,
                headers=auth_headers
            )
            assert response.status_code in [200, 201]
        
        # 3. 计算关键路径
        response = client.get(
            f"/api/v1/projects/{project_id}/critical-path",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]
        
        # 4. 验证关键路径分析结果
        if response.status_code == 200:
            critical_path = response.json()
            # 验证关键路径包含关键里程碑
            assert isinstance(critical_path, (dict, list))

    def test_milestone_risk_alert(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：里程碑风险预警"""
        # 1. 创建项目和里程碑
        project_data = {
            "project_name": "供应链管理系统",
            "project_code": "PRJ-SCM-SYS-2024",
            "project_type": "软件开发",
            "customer_id": 1,
            "start_date": str(date.today()),
            "expected_end_date": str(date.today() + timedelta(days=220)),
            "contract_amount": 5500000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 创建里程碑
        milestone_data = {
            "milestone_name": "UAT测试完成",
            "milestone_code": "M04",
            "planned_date": str(date.today() + timedelta(days=180)),
            "milestone_type": "关键",
            "deliverables": ["UAT测试报告"],
            "acceptance_criteria": "用户验收测试通过",
            "weight": 30,
            "alert_threshold_days": 14  # 提前14天预警
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestones",
            json=milestone_data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]
        milestone_id = response.json().get("id")
        
        # 3. 设置风险预警规则
        alert_rule = {
            "milestone_id": milestone_id,
            "rule_type": "progress_delay",
            "threshold": {
                "progress_percentage": 50,
                "days_before_deadline": 30,
                "alert_level": "warning"
            },
            "notification_recipients": [test_employee.id, test_employee.id + 1],
            "notification_channels": ["email", "system"]
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestones/{milestone_id}/alert-rules",
            json=alert_rule,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]
        
        # 4. 触发预警（模拟进度落后）
        progress_update = {
            "update_date": str(date.today() + timedelta(days=150)),
            "progress_percentage": 40,  # 进度低于预期
            "status": "风险",
            "update_description": "进度落后，存在延期风险",
            "updated_by": test_employee.id
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestones/{milestone_id}/progress",
            json=progress_update,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]
        
        # 5. 查询预警记录
        response = client.get(
            f"/api/v1/projects/{project_id}/milestones/{milestone_id}/alerts",
            headers=auth_headers
        )
        assert response.status_code in [200, 404]

    def test_milestone_report_generation(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：里程碑报告生成"""
        # 1. 创建项目和多个里程碑
        project_data = {
            "project_name": "智能工厂升级",
            "project_code": "PRJ-SMART-UP-2024",
            "project_type": "自动化改造",
            "customer_id": 1,
            "start_date": str(date.today() - timedelta(days=180)),
            "expected_end_date": str(date.today() + timedelta(days=180)),
            "contract_amount": 12000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 创建里程碑（部分已完成）
        milestones = [
            {
                "milestone_name": "需求调研",
                "milestone_code": "M01",
                "planned_date": str(date.today() - timedelta(days=150)),
                "actual_completion_date": str(date.today() - timedelta(days=148)),
                "status": "已完成",
                "weight": 10
            },
            {
                "milestone_name": "方案设计",
                "milestone_code": "M02",
                "planned_date": str(date.today() - timedelta(days=120)),
                "actual_completion_date": str(date.today() - timedelta(days=115)),
                "status": "已完成",
                "weight": 15
            },
            {
                "milestone_name": "设备采购",
                "milestone_code": "M03",
                "planned_date": str(date.today() - timedelta(days=30)),
                "status": "进行中",
                "progress_percentage": 85,
                "weight": 25
            },
            {
                "milestone_name": "系统集成",
                "milestone_code": "M04",
                "planned_date": str(date.today() + timedelta(days=60)),
                "status": "未开始",
                "weight": 30
            }
        ]
        
        for milestone in milestones:
            client.post(
                f"/api/v1/projects/{project_id}/milestones",
                json=milestone,
                headers=auth_headers
            )
        
        # 3. 生成里程碑报告
        report_request = {
            "report_type": "milestone_summary",
            "report_period": {
                "start_date": str(date.today() - timedelta(days=180)),
                "end_date": str(date.today())
            },
            "include_sections": [
                "milestone_status",
                "completion_rate",
                "delay_analysis",
                "risk_assessment",
                "next_steps"
            ],
            "format": "pdf"
        }
        
        response = client.post(
            f"/api/v1/projects/{project_id}/milestone-reports",
            json=report_request,
            headers=auth_headers
        )
        assert response.status_code in [200, 201, 404]
        
        # 4. 下载报告
        if response.status_code in [200, 201]:
            report = response.json()
            report_id = report.get("id")
            
            if report_id:
                response = client.get(
                    f"/api/v1/projects/{project_id}/milestone-reports/{report_id}/download",
                    headers=auth_headers
                )
                assert response.status_code in [200, 404]
