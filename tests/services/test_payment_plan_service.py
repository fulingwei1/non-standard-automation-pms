# -*- coding: utf-8 -*-
"""
PaymentPlanService 单元测试 - 销售模块核心服务
覆盖：根据合同生成收款计划
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.sales.payment_plan_service import PaymentPlanService
from app.models.sales import Contract


def _make_mock_contract(
    contract_id=1,
    project_id=100,
    contract_amount=100000.0,
    signing_date=None,
    payment_terms=None,
):
    """创建模拟合同对象"""
    contract = MagicMock(spec=Contract)
    contract.id = contract_id
    contract.project_id = project_id
    contract.contract_amount = contract_amount
    contract.signing_date = signing_date or date(2025, 1, 1)
    contract.payment_terms = payment_terms
    return contract


def _make_mock_project(
    project_id=100,
    planned_start_date=None,
    planned_end_date=None,
):
    """创建模拟项目对象"""
    project = MagicMock()
    project.id = project_id
    project.planned_start_date = planned_start_date or date(2025, 1, 1)
    project.planned_end_date = planned_end_date or date(2025, 12, 31)
    return project


class TestPaymentPlanService(unittest.TestCase):
    """PaymentPlanService 测试类"""

    def setUp(self):
        self.db = MagicMock()
        self.svc = PaymentPlanService(self.db)

    def _setup_query_results(self, project=None, payment_plan_count=0):
        """设置查询结果"""
        query = MagicMock()
        self.db.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = project
        query.count.return_value = payment_plan_count
        return query

    def test_generate_payment_plans_success(self):
        """测试成功生成收款计划"""
        contract = _make_mock_contract(contract_amount=100000.0)
        project = _make_mock_project()

        self._setup_query_results(project=project, payment_plan_count=0)

        plans = self.svc.generate_payment_plans_from_contract(contract)

        # 验证生成了4个收款计划
        self.assertEqual(len(plans), 4)
        self.assertEqual(self.db.add.call_count, 4)

        # 验证预付款
        self.assertEqual(plans[0].payment_name, "预付款")
        self.assertEqual(plans[0].payment_ratio, 30.0)
        self.assertEqual(plans[0].planned_amount, 30000.0)

        # 验证发货款
        self.assertEqual(plans[1].payment_name, "发货款")
        self.assertEqual(plans[1].payment_ratio, 40.0)
        self.assertEqual(plans[1].planned_amount, 40000.0)

        # 验证验收款
        self.assertEqual(plans[2].payment_name, "验收款")
        self.assertEqual(plans[2].payment_ratio, 25.0)
        self.assertEqual(plans[2].planned_amount, 25000.0)

        # 验证质保款
        self.assertEqual(plans[3].payment_name, "质保款")
        self.assertEqual(plans[3].payment_ratio, 5.0)
        self.assertEqual(plans[3].planned_amount, 5000.0)

    def test_validate_contract_no_project_id(self):
        """测试合同无项目ID时验证失败"""
        contract = _make_mock_contract(project_id=None)
        self._setup_query_results(project=None)

        result = self.svc._validate_contract(contract)

        self.assertFalse(result)

    def test_validate_contract_project_not_exists(self):
        """测试项目不存在时验证失败"""
        contract = _make_mock_contract(project_id=999)
        self._setup_query_results(project=None)

        result = self.svc._validate_contract(contract)

        self.assertFalse(result)

    def test_validate_contract_invalid_amount(self):
        """测试合同金额为0时验证失败"""
        contract = _make_mock_contract(contract_amount=0)
        project = _make_mock_project()

        self._setup_query_results(project=project, payment_plan_count=0)

        result = self.svc._validate_contract(contract)

        self.assertFalse(result)

    def test_validate_contract_already_has_plans(self):
        """测试已有收款计划时验证失败"""
        contract = _make_mock_contract()
        project = _make_mock_project()

        self._setup_query_results(project=project, payment_plan_count=3)

        result = self.svc._validate_contract(contract)

        self.assertFalse(result)

    def test_get_payment_configurations(self):
        """测试获取收款计划配置"""
        configs = self.svc._get_payment_configurations()

        self.assertEqual(len(configs), 4)

        # 验证预付款配置
        self.assertEqual(configs[0]["payment_name"], "预付款")
        self.assertEqual(configs[0]["payment_ratio"], 30.0)

        # 验证发货款配置
        self.assertEqual(configs[1]["payment_name"], "发货款")
        self.assertEqual(configs[1]["payment_ratio"], 40.0)

        # 验证验收款配置
        self.assertEqual(configs[2]["payment_name"], "验收款")
        self.assertEqual(configs[2]["payment_ratio"], 25.0)

        # 验证质保款配置
        self.assertEqual(configs[3]["payment_name"], "质保款")
        self.assertEqual(configs[3]["payment_ratio"], 5.0)

    def test_get_payment_configurations_honors_contract_terms(self):
        """合同付款条款明确为3-3-3-1时，应按合同生成收款比例。"""
        contract = _make_mock_contract(
            payment_terms="30%预付款 + 30%中期款 + 30%验收款 + 10%质保金"
        )

        configs = self.svc._get_payment_configurations(contract)

        self.assertEqual([cfg["payment_ratio"] for cfg in configs], [30.0, 30.0, 30.0, 10.0])
        self.assertEqual([cfg["payment_type"] for cfg in configs], [
            "ADVANCE",
            "DELIVERY",
            "ACCEPTANCE",
            "WARRANTY",
        ])
        self.assertEqual(configs[1]["payment_name"], "中期款")
        self.assertEqual(configs[3]["payment_name"], "质保金")

    def test_calculate_planned_date_advance(self):
        """测试预付款日期计算 - 合同签订后7天"""
        contract = _make_mock_contract(signing_date=date(2025, 1, 1))
        project = _make_mock_project()

        planned_date = self.svc._calculate_planned_date(contract, project, 1)

        self.assertEqual(planned_date, date(2025, 1, 8))

    def test_calculate_planned_date_delivery(self):
        """测试发货款日期计算 - 项目中期"""
        contract = _make_mock_contract()
        project = _make_mock_project(
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 12, 31),
        )

        planned_date = self.svc._calculate_planned_date(contract, project, 2)

        # 项目周期365天，60%约219天，从1月1日开始
        self.assertEqual(planned_date, date(2025, 8, 7))

    def test_calculate_planned_date_acceptance(self):
        """测试验收款日期计算 - 项目结束日期"""
        contract = _make_mock_contract()
        project = _make_mock_project(
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 12, 31),
        )

        planned_date = self.svc._calculate_planned_date(contract, project, 3)

        self.assertEqual(planned_date, date(2025, 12, 31))

    def test_calculate_planned_date_warranty(self):
        """测试质保款日期计算 - 项目结束后1年"""
        contract = _make_mock_contract()
        project = _make_mock_project(
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 12, 31),
        )

        planned_date = self.svc._calculate_planned_date(contract, project, 4)

        self.assertEqual(planned_date, date(2026, 12, 31))

    def test_create_payment_plan_no_project_id(self):
        """测试无项目ID时无法创建收款计划"""
        contract = _make_mock_contract(project_id=None)
        config = {"payment_no": 1, "payment_name": "预付款", "payment_ratio": 30.0}

        plan = self.svc._create_payment_plan(contract, config)

        self.assertIsNone(plan)

    def test_create_payment_plan_with_valid_data(self):
        """测试创建有效的收款计划"""
        contract = _make_mock_contract(
            contract_id=1, project_id=100, contract_amount=100000.0
        )
        project = _make_mock_project(project_id=100)

        self._setup_query_results(project=project)

        config = {
            "payment_no": 1,
            "payment_name": "预付款",
            "payment_type": "ADVANCE",
            "payment_ratio": 30.0,
            "trigger_milestone": "合同签订",
            "trigger_condition": "合同签订后",
        }

        plan = self.svc._create_payment_plan(contract, config)

        self.assertIsNotNone(plan)
        self.assertEqual(plan.project_id, 100)
        self.assertEqual(plan.contract_id, 1)
        self.assertEqual(plan.payment_name, "预付款")
        self.assertEqual(plan.payment_ratio, 30.0)
        self.assertEqual(plan.planned_amount, 30000.0)
        self.assertEqual(plan.status, "PENDING")


class TestPaymentRatioCalculation(unittest.TestCase):
    """收款比例计算测试"""

    def test_payment_ratios_sum_to_100(self):
        """验证收款比例总和为100%"""
        ratios = [30.0, 40.0, 25.0, 5.0]
        self.assertEqual(sum(ratios), 100.0)


if __name__ == "__main__":
    unittest.main()
