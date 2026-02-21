# -*- coding: utf-8 -*-
"""
项目风险服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率（509行）

参考：tests/unit/test_condition_parser_rewrite.py
创建日期：2026-02-21
"""

import unittest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

from app.services.project.project_risk_service import ProjectRiskService


class TestProjectRiskServiceCore(unittest.TestCase):
    """测试核心风险计算方法"""

    def setUp(self):
        """每个测试前初始化"""
        self.db = MagicMock()
        self.service = ProjectRiskService(self.db)

    # ========== calculate_project_risk() 主方法测试 ==========

    def test_calculate_project_risk_success(self):
        """测试成功计算项目风险"""
        # Mock项目对象
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PRJ001"
        mock_project.progress_pct = 50.0
        mock_project.planned_end_date = date.today() + timedelta(days=30)
        mock_project.planned_start_date = date.today() - timedelta(days=30)
        mock_project.contract_date = date.today() - timedelta(days=60)
        mock_project.actual_start_date = date.today() - timedelta(days=30)

        # Mock calculate helpers
        with patch.object(self.service, '_calculate_milestone_factors') as mock_milestone:
            with patch.object(self.service, '_calculate_pmo_risk_factors') as mock_pmo:
                with patch.object(self.service, '_calculate_progress_factors') as mock_progress:
                    # Mock数据库查询
                    self.db.query.return_value.filter.return_value.first.return_value = mock_project
                    
                    # Mock各因子计算结果
                    mock_milestone.return_value = {
                        "total_milestones_count": 10,
                        "overdue_milestones_count": 1,
                        "overdue_milestone_ratio": 0.1,
                        "max_overdue_days": 5,
                    }
                    mock_pmo.return_value = {
                        "open_risks_count": 2,
                        "high_risks_count": 1,
                        "critical_risks_count": 0,
                    }
                    mock_progress.return_value = {
                        "progress_pct": 50.0,
                        "schedule_variance": 0,
                    }

                    # 执行测试
                    result = self.service.calculate_project_risk(1)

                    # 验证结果
                    self.assertEqual(result["project_id"], 1)
                    self.assertEqual(result["project_code"], "PRJ001")
                    self.assertIn(result["risk_level"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
                    self.assertIn("risk_factors", result)
                    self.assertIn("calculated_at", result["risk_factors"])

    def test_calculate_project_risk_project_not_found(self):
        """测试项目不存在时抛出异常"""
        self.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.service.calculate_project_risk(999)
        
        self.assertIn("项目不存在", str(context.exception))

    # ========== _calculate_milestone_factors() 测试 ==========

    def test_calculate_milestone_factors_no_milestones(self):
        """测试无里程碑情况"""
        self.db.query.return_value.filter.return_value.scalar.return_value = 0
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service._calculate_milestone_factors(1, date.today())

        self.assertEqual(result["total_milestones_count"], 0)
        self.assertEqual(result["overdue_milestones_count"], 0)
        self.assertEqual(result["overdue_milestone_ratio"], 0)
        self.assertEqual(result["max_overdue_days"], 0)

    def test_calculate_milestone_factors_with_overdue(self):
        """测试有逾期里程碑"""
        # Mock总数查询
        self.db.query.return_value.filter.return_value.scalar.return_value = 5
        
        # Mock逾期里程碑
        mock_m1 = MagicMock()
        mock_m1.planned_date = date.today() - timedelta(days=10)
        mock_m2 = MagicMock()
        mock_m2.planned_date = date.today() - timedelta(days=5)
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_m1, mock_m2]

        result = self.service._calculate_milestone_factors(1, date.today())

        self.assertEqual(result["total_milestones_count"], 5)
        self.assertEqual(result["overdue_milestones_count"], 2)
        self.assertEqual(result["overdue_milestone_ratio"], 0.4)  # 2/5 = 0.4
        self.assertEqual(result["max_overdue_days"], 10)

    def test_calculate_milestone_factors_no_overdue(self):
        """测试无逾期里程碑"""
        self.db.query.return_value.filter.return_value.scalar.return_value = 3
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service._calculate_milestone_factors(1, date.today())

        self.assertEqual(result["overdue_milestones_count"], 0)
        self.assertEqual(result["overdue_milestone_ratio"], 0)
        self.assertEqual(result["max_overdue_days"], 0)

    # ========== _calculate_pmo_risk_factors() 测试 ==========

    def test_calculate_pmo_risk_factors_no_risks(self):
        """测试无PMO风险"""
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.service._calculate_pmo_risk_factors(1)

        self.assertEqual(result["open_risks_count"], 0)
        self.assertEqual(result["high_risks_count"], 0)
        self.assertEqual(result["critical_risks_count"], 0)

    def test_calculate_pmo_risk_factors_with_risks(self):
        """测试有PMO风险"""
        mock_r1 = MagicMock()
        mock_r1.risk_level = "CRITICAL"
        mock_r2 = MagicMock()
        mock_r2.risk_level = "HIGH"
        mock_r3 = MagicMock()
        mock_r3.risk_level = "HIGH"
        mock_r4 = MagicMock()
        mock_r4.risk_level = "MEDIUM"
        
        self.db.query.return_value.filter.return_value.all.return_value = [
            mock_r1, mock_r2, mock_r3, mock_r4
        ]

        result = self.service._calculate_pmo_risk_factors(1)

        self.assertEqual(result["open_risks_count"], 4)
        self.assertEqual(result["high_risks_count"], 3)  # HIGH + CRITICAL
        self.assertEqual(result["critical_risks_count"], 1)

    # ========== _calculate_progress_factors() 测试 ==========

    def test_calculate_progress_factors_no_planned_end_date(self):
        """测试无计划结束日期"""
        mock_project = MagicMock()
        mock_project.progress_pct = 50.0
        mock_project.planned_end_date = None

        result = self.service._calculate_progress_factors(mock_project)

        self.assertEqual(result["progress_pct"], 50.0)
        self.assertEqual(result["schedule_variance"], 0)

    def test_calculate_progress_factors_with_positive_variance(self):
        """测试进度超前（正偏差）"""
        mock_project = MagicMock()
        mock_project.progress_pct = 80.0
        mock_project.planned_end_date = date.today() + timedelta(days=50)
        mock_project.planned_start_date = date.today() - timedelta(days=50)
        mock_project.contract_date = date.today() - timedelta(days=100)
        mock_project.actual_start_date = date.today() - timedelta(days=50)

        result = self.service._calculate_progress_factors(mock_project)

        self.assertEqual(result["progress_pct"], 80.0)
        # 已过50天，总100天，预期50%，实际80%，偏差30%
        self.assertGreater(result["schedule_variance"], 0)

    def test_calculate_progress_factors_with_negative_variance(self):
        """测试进度滞后（负偏差）"""
        mock_project = MagicMock()
        mock_project.progress_pct = 20.0
        mock_project.planned_end_date = date.today() + timedelta(days=50)
        mock_project.planned_start_date = date.today() - timedelta(days=50)
        mock_project.contract_date = date.today() - timedelta(days=100)
        mock_project.actual_start_date = date.today() - timedelta(days=50)

        result = self.service._calculate_progress_factors(mock_project)

        self.assertEqual(result["progress_pct"], 20.0)
        # 已过50天，总100天，预期50%，实际20%，偏差-30%
        self.assertLess(result["schedule_variance"], 0)

    def test_calculate_progress_factors_none_progress(self):
        """测试进度为None"""
        mock_project = MagicMock()
        mock_project.progress_pct = None
        mock_project.planned_end_date = None

        result = self.service._calculate_progress_factors(mock_project)

        self.assertEqual(result["progress_pct"], 0.0)

    # ========== _calculate_risk_level() 测试 ==========

    def test_calculate_risk_level_critical_overdue(self):
        """测试CRITICAL等级 - 逾期里程碑>=50%"""
        factors = {
            "overdue_milestone_ratio": 0.6,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": 0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "CRITICAL")

    def test_calculate_risk_level_critical_risk(self):
        """测试CRITICAL等级 - 有CRITICAL风险"""
        factors = {
            "overdue_milestone_ratio": 0.1,
            "critical_risks_count": 1,
            "high_risks_count": 1,
            "schedule_variance": 0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "CRITICAL")

    def test_calculate_risk_level_high_overdue(self):
        """测试HIGH等级 - 逾期里程碑>=30%"""
        factors = {
            "overdue_milestone_ratio": 0.35,
            "critical_risks_count": 0,
            "high_risks_count": 1,
            "schedule_variance": 0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "HIGH")

    def test_calculate_risk_level_high_risks(self):
        """测试HIGH等级 - 高风险>=2"""
        factors = {
            "overdue_milestone_ratio": 0.1,
            "critical_risks_count": 0,
            "high_risks_count": 2,
            "schedule_variance": 0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "HIGH")

    def test_calculate_risk_level_high_schedule_variance(self):
        """测试HIGH等级 - 进度偏差<-20%"""
        factors = {
            "overdue_milestone_ratio": 0.05,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": -25.0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "HIGH")

    def test_calculate_risk_level_medium_overdue(self):
        """测试MEDIUM等级 - 逾期里程碑>=10%"""
        factors = {
            "overdue_milestone_ratio": 0.15,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": 0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "MEDIUM")

    def test_calculate_risk_level_medium_one_high_risk(self):
        """测试MEDIUM等级 - 有1个高风险"""
        factors = {
            "overdue_milestone_ratio": 0.05,
            "critical_risks_count": 0,
            "high_risks_count": 1,
            "schedule_variance": 0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "MEDIUM")

    def test_calculate_risk_level_medium_schedule_variance(self):
        """测试MEDIUM等级 - 进度偏差<-10%"""
        factors = {
            "overdue_milestone_ratio": 0.05,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": -15.0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "MEDIUM")

    def test_calculate_risk_level_low(self):
        """测试LOW等级 - 所有指标正常"""
        factors = {
            "overdue_milestone_ratio": 0.05,
            "critical_risks_count": 0,
            "high_risks_count": 0,
            "schedule_variance": 5.0,
        }
        result = self.service._calculate_risk_level(factors)
        self.assertEqual(result, "LOW")

    def test_calculate_risk_level_empty_factors(self):
        """测试空因子（应返回LOW）"""
        result = self.service._calculate_risk_level({})
        self.assertEqual(result, "LOW")

    # ========== _is_risk_upgrade() 测试 ==========

    def test_is_risk_upgrade_true(self):
        """测试风险升级检测 - 升级"""
        self.assertTrue(self.service._is_risk_upgrade("LOW", "MEDIUM"))
        self.assertTrue(self.service._is_risk_upgrade("LOW", "HIGH"))
        self.assertTrue(self.service._is_risk_upgrade("MEDIUM", "HIGH"))
        self.assertTrue(self.service._is_risk_upgrade("HIGH", "CRITICAL"))

    def test_is_risk_upgrade_false(self):
        """测试风险升级检测 - 未升级"""
        self.assertFalse(self.service._is_risk_upgrade("MEDIUM", "LOW"))
        self.assertFalse(self.service._is_risk_upgrade("HIGH", "MEDIUM"))
        self.assertFalse(self.service._is_risk_upgrade("CRITICAL", "HIGH"))

    def test_is_risk_upgrade_same_level(self):
        """测试风险升级检测 - 相同等级"""
        self.assertFalse(self.service._is_risk_upgrade("LOW", "LOW"))
        self.assertFalse(self.service._is_risk_upgrade("MEDIUM", "MEDIUM"))
        self.assertFalse(self.service._is_risk_upgrade("HIGH", "HIGH"))

    def test_is_risk_upgrade_invalid_level(self):
        """测试风险升级检测 - 无效等级（返回0，不会升级）"""
        # 无效等级的order为0，比较时会有如下结果：
        # "INVALID"(0) -> "LOW"(1): 1 > 0 = True (被判定为升级)
        # "LOW"(1) -> "INVALID"(0): 0 > 1 = False (不是升级)
        result1 = self.service._is_risk_upgrade("INVALID", "LOW")
        result2 = self.service._is_risk_upgrade("LOW", "INVALID")
        self.assertTrue(result1)   # INVALID(0) -> LOW(1) 被判定为升级
        self.assertFalse(result2)  # LOW(1) -> INVALID(0) 不是升级

    # ========== auto_upgrade_risk_level() 测试 ==========

    def test_auto_upgrade_risk_level_first_time(self):
        """测试首次计算风险（无历史记录）"""
        # Mock calculate_project_risk
        with patch.object(self.service, 'calculate_project_risk') as mock_calc:
            mock_calc.return_value = {
                "project_id": 1,
                "project_code": "PRJ001",
                "risk_level": "LOW",
                "risk_factors": {
                    "overdue_milestones_count": 0,
                    "total_milestones_count": 5,
                }
            }

            # Mock无历史记录
            self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

            # Mock项目查询（用于通知）
            mock_project = MagicMock()
            mock_project.project_name = "测试项目"
            self.db.query.return_value.filter.return_value.first.return_value = mock_project

            # 执行测试
            result = self.service.auto_upgrade_risk_level(1)

            # 验证
            self.assertEqual(result["project_id"], 1)
            self.assertEqual(result["old_risk_level"], "LOW")  # 默认LOW
            self.assertEqual(result["new_risk_level"], "LOW")
            self.assertFalse(result["is_upgrade"])
            self.db.add.assert_called_once()  # 添加历史记录
            self.db.commit.assert_called_once()

    def test_auto_upgrade_risk_level_with_upgrade(self):
        """测试风险升级"""
        # Mock calculate_project_risk返回HIGH风险
        with patch.object(self.service, 'calculate_project_risk') as mock_calc:
            with patch('app.services.project.project_risk_service.logger'):
                mock_calc.return_value = {
                    "project_id": 1,
                    "project_code": "PRJ001",
                    "risk_level": "HIGH",  # 新风险等级HIGH
                    "risk_factors": {
                        "overdue_milestones_count": 3,
                        "total_milestones_count": 10,
                        "overdue_milestone_ratio": 0.3,
                    }
                }

                # Mock历史记录（上次是LOW）
                mock_last_history = MagicMock()
                mock_last_history.new_risk_level = "LOW"
                self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_last_history

                # Mock项目查询（用于通知）
                mock_project = MagicMock()
                mock_project.project_name = "测试项目"
                self.db.query.return_value.filter.return_value.first.return_value = mock_project

                # Mock通知函数
                with patch.object(self.service, '_send_risk_upgrade_notification'):
                    # 执行测试
                    result = self.service.auto_upgrade_risk_level(1)

                    # 验证
                    self.assertEqual(result["old_risk_level"], "LOW")
                    self.assertEqual(result["new_risk_level"], "HIGH")
                    self.assertTrue(result["is_upgrade"])

    # ========== batch_calculate_risks() 测试 ==========

    def test_batch_calculate_risks_all_projects(self):
        """测试批量计算所有项目"""
        # Mock项目列表
        mock_p1 = MagicMock()
        mock_p1.id = 1
        mock_p1.project_code = "PRJ001"
        mock_p1.is_active = True
        
        mock_p2 = MagicMock()
        mock_p2.id = 2
        mock_p2.project_code = "PRJ002"
        mock_p2.is_active = True

        self.db.query.return_value.filter.return_value.all.return_value = [mock_p1, mock_p2]

        # Mock auto_upgrade_risk_level
        with patch.object(self.service, 'auto_upgrade_risk_level') as mock_upgrade:
            mock_upgrade.side_effect = [
                {"project_id": 1, "project_code": "PRJ001"},
                {"project_id": 2, "project_code": "PRJ002"},
            ]

            results = self.service.batch_calculate_risks()

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["project_id"], 1)
        self.assertEqual(results[1]["project_id"], 2)

    def test_batch_calculate_risks_specific_projects(self):
        """测试批量计算指定项目"""
        mock_p1 = MagicMock()
        mock_p1.id = 1
        mock_p1.project_code = "PRJ001"

        self.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_p1]

        with patch.object(self.service, 'auto_upgrade_risk_level') as mock_upgrade:
            mock_upgrade.return_value = {"project_id": 1, "project_code": "PRJ001"}

            results = self.service.batch_calculate_risks(project_ids=[1])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["project_id"], 1)

    def test_batch_calculate_risks_with_error(self):
        """测试批量计算中某个项目出错"""
        mock_p1 = MagicMock()
        mock_p1.id = 1
        mock_p1.project_code = "PRJ001"
        
        mock_p2 = MagicMock()
        mock_p2.id = 2
        mock_p2.project_code = "PRJ002"

        self.db.query.return_value.filter.return_value.all.return_value = [mock_p1, mock_p2]

        with patch.object(self.service, 'auto_upgrade_risk_level') as mock_upgrade:
            mock_upgrade.side_effect = [
                {"project_id": 1, "project_code": "PRJ001"},
                Exception("计算失败"),
            ]

            with patch('app.services.project.project_risk_service.logger'):
                results = self.service.batch_calculate_risks()

        # 验证错误处理
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["project_id"], 1)
        self.assertEqual(results[1]["project_id"], 2)
        self.assertIn("error", results[1])

    def test_batch_calculate_risks_inactive_projects(self):
        """测试批量计算包含非激活项目"""
        mock_p1 = MagicMock()
        mock_p1.id = 1
        mock_p1.is_active = True
        
        self.db.query.return_value.all.return_value = [mock_p1]

        with patch.object(self.service, 'auto_upgrade_risk_level') as mock_upgrade:
            mock_upgrade.return_value = {"project_id": 1}
            
            results = self.service.batch_calculate_risks(active_only=False)

        self.assertEqual(len(results), 1)

    # ========== create_risk_snapshot() 测试 ==========

    def test_create_risk_snapshot_success(self):
        """测试创建风险快照"""
        with patch.object(self.service, 'calculate_project_risk') as mock_calc:
            mock_calc.return_value = {
                "project_id": 1,
                "risk_level": "MEDIUM",
                "risk_factors": {
                    "overdue_milestones_count": 2,
                    "total_milestones_count": 10,
                    "overdue_tasks_count": 5,
                    "open_risks_count": 3,
                    "high_risks_count": 1,
                }
            }

            snapshot = self.service.create_risk_snapshot(1)

        # 验证快照被添加并提交
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    # ========== get_risk_history() 测试 ==========

    def test_get_risk_history_success(self):
        """测试获取风险历史"""
        mock_h1 = MagicMock()
        mock_h2 = MagicMock()
        
        self.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_h1, mock_h2
        ]

        result = self.service.get_risk_history(1, limit=10)

        self.assertEqual(len(result), 2)

    def test_get_risk_history_empty(self):
        """测试获取空历史"""
        self.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = self.service.get_risk_history(1)

        self.assertEqual(len(result), 0)

    # ========== get_risk_trend() 测试 ==========

    def test_get_risk_trend_success(self):
        """测试获取风险趋势"""
        mock_s1 = MagicMock()
        mock_s1.snapshot_date = datetime.now() - timedelta(days=5)
        mock_s1.risk_level = "LOW"
        mock_s1.overdue_milestones_count = 0
        mock_s1.open_risks_count = 0
        mock_s1.high_risks_count = 0

        mock_s2 = MagicMock()
        mock_s2.snapshot_date = datetime.now() - timedelta(days=2)
        mock_s2.risk_level = "MEDIUM"
        mock_s2.overdue_milestones_count = 2
        mock_s2.open_risks_count = 1
        mock_s2.high_risks_count = 1

        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_s1, mock_s2
        ]

        result = self.service.get_risk_trend(1, days=7)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["risk_level"], "LOW")
        self.assertEqual(result[1]["risk_level"], "MEDIUM")
        self.assertIn("date", result[0])
        self.assertIn("overdue_milestones", result[0])

    def test_get_risk_trend_empty(self):
        """测试空趋势数据"""
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = self.service.get_risk_trend(1, days=30)

        self.assertEqual(len(result), 0)

    # ========== _send_risk_upgrade_notification() 测试 ==========

    def test_send_risk_upgrade_notification_success(self):
        """测试发送风险升级通知"""
        with patch('app.services.project.project_risk_service.logger'):
            with patch('app.utils.scheduled_tasks.base.send_notification_for_alert'):
                self.service._send_risk_upgrade_notification(
                    project_id=1,
                    project_code="PRJ001",
                    project_name="测试项目",
                    old_level="LOW",
                    new_level="HIGH",
                    risk_factors={
                        "overdue_milestones_count": 3,
                        "high_risks_count": 2,
                        "schedule_variance": -15.0,
                    }
                )

                # 验证添加了预警记录
                self.db.add.assert_called_once()
                self.db.flush.assert_called_once()

    def test_send_risk_upgrade_notification_critical_level(self):
        """测试CRITICAL级别通知"""
        with patch('app.services.project.project_risk_service.logger'):
            with patch('app.utils.scheduled_tasks.base.send_notification_for_alert'):
                self.service._send_risk_upgrade_notification(
                    project_id=1,
                    project_code="PRJ001",
                    project_name="测试项目",
                    old_level="MEDIUM",
                    new_level="CRITICAL",
                    risk_factors={}
                )

                self.db.add.assert_called_once()

    def test_send_risk_upgrade_notification_exception(self):
        """测试通知发送异常（不影响主流程）"""
        with patch('app.services.project.project_risk_service.logger') as mock_logger:
            self.db.add.side_effect = Exception("数据库错误")

            # 不应抛出异常
            self.service._send_risk_upgrade_notification(
                project_id=1,
                project_code="PRJ001",
                project_name="测试项目",
                old_level="LOW",
                new_level="HIGH",
                risk_factors={}
            )

            # 验证记录了错误日志
            mock_logger.error.assert_called()


class TestProjectRiskServiceEdgeCases(unittest.TestCase):
    """测试边界情况和异常处理"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ProjectRiskService(self.db)

    def test_risk_level_order_constant(self):
        """测试风险等级顺序常量"""
        self.assertEqual(self.service.RISK_LEVEL_ORDER["LOW"], 1)
        self.assertEqual(self.service.RISK_LEVEL_ORDER["MEDIUM"], 2)
        self.assertEqual(self.service.RISK_LEVEL_ORDER["HIGH"], 3)
        self.assertEqual(self.service.RISK_LEVEL_ORDER["CRITICAL"], 4)

    def test_calculate_milestone_factors_milestone_without_planned_date(self):
        """测试里程碑无计划日期"""
        self.db.query.return_value.filter.return_value.scalar.return_value = 1
        
        mock_m = MagicMock()
        mock_m.planned_date = None
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_m]

        result = self.service._calculate_milestone_factors(1, date.today())

        # 无计划日期的里程碑不计入逾期
        self.assertEqual(result["max_overdue_days"], 0)

    def test_calculate_progress_factors_zero_duration(self):
        """测试项目总工期为0"""
        mock_project = MagicMock()
        mock_project.progress_pct = 50.0
        mock_project.planned_end_date = date.today()
        mock_project.planned_start_date = date.today()  # 同一天
        mock_project.contract_date = date.today()
        mock_project.actual_start_date = date.today()

        result = self.service._calculate_progress_factors(mock_project)

        # 总工期为0时，不计算偏差
        self.assertEqual(result["schedule_variance"], 0)

    def test_calculate_risk_level_boundary_values(self):
        """测试边界值判断"""
        # 恰好50%逾期 -> CRITICAL
        factors = {"overdue_milestone_ratio": 0.5, "critical_risks_count": 0, "high_risks_count": 0, "schedule_variance": 0}
        self.assertEqual(self.service._calculate_risk_level(factors), "CRITICAL")

        # 49%逾期 -> HIGH
        factors = {"overdue_milestone_ratio": 0.49, "critical_risks_count": 0, "high_risks_count": 0, "schedule_variance": 0}
        self.assertNotEqual(self.service._calculate_risk_level(factors), "CRITICAL")

        # 恰好30%逾期 -> HIGH
        factors = {"overdue_milestone_ratio": 0.3, "critical_risks_count": 0, "high_risks_count": 0, "schedule_variance": 0}
        self.assertEqual(self.service._calculate_risk_level(factors), "HIGH")

        # 恰好10%逾期 -> MEDIUM
        factors = {"overdue_milestone_ratio": 0.1, "critical_risks_count": 0, "high_risks_count": 0, "schedule_variance": 0}
        self.assertEqual(self.service._calculate_risk_level(factors), "MEDIUM")

    def test_progress_expected_exceeds_100(self):
        """测试预期进度超过100%的情况"""
        mock_project = MagicMock()
        mock_project.progress_pct = 80.0
        mock_project.planned_end_date = date.today() - timedelta(days=10)  # 已过期
        mock_project.planned_start_date = date.today() - timedelta(days=100)
        mock_project.contract_date = date.today() - timedelta(days=150)
        mock_project.actual_start_date = date.today() - timedelta(days=100)

        result = self.service._calculate_progress_factors(mock_project)

        # 预期进度会被min限制在100%
        self.assertIsNotNone(result["schedule_variance"])


if __name__ == "__main__":
    unittest.main()
