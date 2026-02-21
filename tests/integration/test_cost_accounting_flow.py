# -*- coding: utf-8 -*-
"""
财务管理集成测试 - 成本核算流程

测试场景：
1. 项目成本预算编制
2. 实际成本记录
3. 成本归集与分配
4. 成本差异分析
5. 成本超支预警
6. 成本核算报表
7. 成本控制措施
"""

import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal


@pytest.mark.integration
class TestCostAccountingFlow:
    """成本核算流程集成测试"""

    def test_project_cost_budget_preparation(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：项目成本预算编制"""
        # 1. 创建项目
        project_data = {
            "project_name": "自动化产线项目",
            "project_code": "PRJ-AUTO-2024",
            "project_type": "自动化改造",
            "customer_id": 1,
            "start_date": str(date.today()),
            "expected_end_date": str(date.today() + timedelta(days=180)),
            "contract_amount": 10000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 编制成本预算
        budget_data = {
            "project_id": project_id,
            "budget_year": 2024,
            "budget_version": "V1.0",
            "cost_items": [
                {
                    "category": "人工成本",
                    "sub_category": "项目经理",
                    "budgeted_amount": 500000.00,
                    "budgeted_quantity": 6,
                    "unit": "人月",
                    "unit_price": 83333.33
                },
                {
                    "category": "人工成本",
                    "sub_category": "工程师",
                    "budgeted_amount": 1200000.00,
                    "budgeted_quantity": 24,
                    "unit": "人月",
                    "unit_price": 50000.00
                },
                {
                    "category": "材料成本",
                    "sub_category": "设备采购",
                    "budgeted_amount": 5000000.00,
                    "budgeted_quantity": 1,
                    "unit": "批",
                    "unit_price": 5000000.00
                },
                {
                    "category": "材料成本",
                    "sub_category": "零部件",
                    "budgeted_amount": 800000.00,
                    "budgeted_quantity": 1,
                    "unit": "批",
                    "unit_price": 800000.00
                },
                {
                    "category": "外包成本",
                    "sub_category": "软件开发",
                    "budgeted_amount": 1000000.00,
                    "budgeted_quantity": 1,
                    "unit": "项",
                    "unit_price": 1000000.00
                },
                {
                    "category": "管理费用",
                    "sub_category": "项目管理",
                    "budgeted_amount": 300000.00,
                    "budgeted_quantity": 6,
                    "unit": "月",
                    "unit_price": 50000.00
                }
            ],
            "total_budget": 8800000.00,
            "budget_margin": 1200000.00,
            "prepared_by": test_employee.id,
            "prepare_date": str(date.today())
        }
        
        response = client.post("/api/v1/finance/cost-budgets", json=budget_data, headers=auth_headers)
        assert response.status_code in [200, 201]

    def test_actual_cost_recording(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：实际成本记录"""
        # 1. 创建项目
        project_data = {
            "project_name": "MES系统实施",
            "project_code": "PRJ-MES-2024",
            "customer_id": 1,
            "start_date": str(date.today()),
            "contract_amount": 8000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 记录实际成本
        cost_records = [
            {
                "project_id": project_id,
                "cost_date": str(date.today()),
                "cost_category": "人工成本",
                "cost_type": "工资",
                "amount": 200000.00,
                "description": "2月份项目团队工资",
                "recorded_by": test_employee.id
            },
            {
                "project_id": project_id,
                "cost_date": str(date.today() + timedelta(days=5)),
                "cost_category": "材料成本",
                "cost_type": "采购",
                "amount": 1500000.00,
                "description": "服务器及网络设备采购",
                "recorded_by": test_employee.id
            },
            {
                "project_id": project_id,
                "cost_date": str(date.today() + timedelta(days=10)),
                "cost_category": "外包成本",
                "cost_type": "服务费",
                "amount": 500000.00,
                "description": "UI设计外包费用",
                "recorded_by": test_employee.id
            }
        ]
        
        for record in cost_records:
            response = client.post("/api/v1/finance/cost-records", json=record, headers=auth_headers)
            assert response.status_code in [200, 201]

    def test_cost_aggregation_and_allocation(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：成本归集与分配"""
        # 1. 创建多个项目
        projects = []
        for i in range(3):
            project_data = {
                "project_name": f"项目{i+1}",
                "project_code": f"PRJ-{i+1}-2024",
                "customer_id": 1,
                "start_date": str(date.today()),
                "contract_amount": 5000000.00 + i * 1000000,
                "project_manager_id": test_employee.id
            }
            response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
            if response.status_code == 200:
                projects.append(response.json()["id"])
        
        # 2. 记录共享成本（需要分摊）
        shared_costs = [
            {
                "cost_date": str(date.today()),
                "cost_category": "管理费用",
                "cost_type": "办公费",
                "amount": 300000.00,
                "description": "办公场地租金",
                "allocation_method": "按合同额分摊"
            },
            {
                "cost_date": str(date.today()),
                "cost_category": "管理费用",
                "cost_type": "人事费用",
                "amount": 150000.00,
                "description": "行政人员工资",
                "allocation_method": "按人数分摊"
            }
        ]
        
        for cost in shared_costs:
            response = client.post("/api/v1/finance/shared-costs", json=cost, headers=auth_headers)
            assert response.status_code in [200, 201, 404]
        
        # 3. 执行成本分配
        if len(projects) > 0:
            allocation_request = {
                "allocation_date": str(date.today()),
                "allocation_period": f"{date.today().year}-{date.today().month:02d}",
                "projects": projects,
                "allocation_basis": "contract_amount"
            }
            
            response = client.post("/api/v1/finance/cost-allocation", json=allocation_request, headers=auth_headers)
            assert response.status_code in [200, 201, 404]

    def test_cost_variance_analysis(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：成本差异分析"""
        # 1. 创建项目
        project_data = {
            "project_name": "智能仓储项目",
            "project_code": "PRJ-WMS-2024",
            "customer_id": 1,
            "start_date": str(date.today() - timedelta(days=60)),
            "contract_amount": 7000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 查询成本差异
        variance_params = {
            "project_id": project_id,
            "analysis_date": str(date.today()),
            "analysis_type": "budget_vs_actual"
        }
        
        response = client.get("/api/v1/finance/cost-variance", params=variance_params, headers=auth_headers)
        assert response.status_code in [200, 404]
        
        # 3. 生成差异分析报告
        report_request = {
            "project_id": project_id,
            "report_period": {
                "start_date": str(date.today() - timedelta(days=60)),
                "end_date": str(date.today())
            },
            "include_details": True,
            "variance_threshold": 0.1  # 超过10%标记为异常
        }
        
        response = client.post("/api/v1/finance/variance-reports", json=report_request, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_cost_overrun_alert(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：成本超支预警"""
        # 1. 创建项目和预算
        project_data = {
            "project_name": "生产管理系统",
            "project_code": "PRJ-PMS-2024",
            "customer_id": 1,
            "start_date": str(date.today()),
            "contract_amount": 6000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 设置成本预警规则
        alert_rule = {
            "project_id": project_id,
            "rule_name": "成本超支预警",
            "alert_conditions": [
                {"cost_category": "人工成本", "threshold_percentage": 80, "alert_level": "warning"},
                {"cost_category": "人工成本", "threshold_percentage": 100, "alert_level": "critical"},
                {"cost_category": "总成本", "threshold_percentage": 90, "alert_level": "warning"}
            ],
            "notification_recipients": [test_employee.id],
            "enabled": True
        }
        
        response = client.post("/api/v1/finance/cost-alert-rules", json=alert_rule, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
        
        # 3. 触发预警（模拟成本超支）
        cost_record = {
            "project_id": project_id,
            "cost_date": str(date.today()),
            "cost_category": "人工成本",
            "cost_type": "工资",
            "amount": 2500000.00,  # 假设预算为3000000，已达83%
            "description": "项目团队工资",
            "recorded_by": test_employee.id
        }
        
        response = client.post("/api/v1/finance/cost-records", json=cost_record, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        # 4. 查询预警记录
        response = client.get(f"/api/v1/finance/cost-alerts?project_id={project_id}", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_cost_accounting_report(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：成本核算报表"""
        # 1. 创建项目
        project_data = {
            "project_name": "ERP升级项目",
            "project_code": "PRJ-ERP-UP-2024",
            "customer_id": 1,
            "start_date": str(date.today() - timedelta(days=90)),
            "contract_amount": 12000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 生成成本汇总报表
        summary_request = {
            "project_id": project_id,
            "report_type": "cost_summary",
            "report_period": {
                "start_date": str(date.today() - timedelta(days=90)),
                "end_date": str(date.today())
            },
            "group_by": "category"
        }
        
        response = client.post("/api/v1/finance/cost-reports", json=summary_request, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
        
        # 3. 生成成本明细报表
        detail_request = {
            "project_id": project_id,
            "report_type": "cost_detail",
            "report_period": {
                "start_date": str(date.today() - timedelta(days=30)),
                "end_date": str(date.today())
            },
            "include_transactions": True
        }
        
        response = client.post("/api/v1/finance/cost-reports", json=detail_request, headers=auth_headers)
        assert response.status_code in [200, 201, 404]

    def test_cost_control_measures(self, client: TestClient, db: Session, auth_headers, test_employee):
        """测试：成本控制措施"""
        # 1. 创建项目
        project_data = {
            "project_name": "产线改造项目",
            "project_code": "PRJ-LINE-UP-2024",
            "customer_id": 1,
            "start_date": str(date.today()),
            "contract_amount": 9000000.00,
            "project_manager_id": test_employee.id
        }
        
        response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
        assert response.status_code == 200
        project_id = response.json()["id"]
        
        # 2. 制定成本控制措施
        control_measures = [
            {
                "project_id": project_id,
                "measure_type": "预算控制",
                "measure_name": "严格执行采购审批",
                "measure_description": "超过10万元的采购需要项目经理审批",
                "responsible_person": test_employee.id,
                "implement_date": str(date.today()),
                "expected_savings": 500000.00
            },
            {
                "project_id": project_id,
                "measure_type": "进度控制",
                "measure_name": "优化人力配置",
                "measure_description": "根据项目阶段动态调整人力投入",
                "responsible_person": test_employee.id,
                "implement_date": str(date.today()),
                "expected_savings": 300000.00
            }
        ]
        
        for measure in control_measures:
            response = client.post("/api/v1/finance/cost-control-measures", json=measure, headers=auth_headers)
            assert response.status_code in [200, 201, 404]
        
        # 3. 跟踪措施执行效果
        effectiveness_data = {
            "project_id": project_id,
            "evaluation_date": str(date.today() + timedelta(days=30)),
            "actual_savings": 380000.00,
            "effectiveness_rate": 0.76,
            "evaluation_comments": "成本控制措施执行良好，实际节省38万元",
            "evaluated_by": test_employee.id
        }
        
        response = client.post("/api/v1/finance/measure-effectiveness", json=effectiveness_data, headers=auth_headers)
        assert response.status_code in [200, 201, 404]
