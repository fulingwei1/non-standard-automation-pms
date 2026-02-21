# -*- coding: utf-8 -*-
"""
schedule_prediction_service 增强单元测试
目标：40-50个测试用例，覆盖率70%+
"""

import json
import unittest
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from app.services.schedule_prediction_service import SchedulePredictionService
from app.models.project.schedule_prediction import (
    ProjectSchedulePrediction,
    CatchUpSolution,
    ScheduleAlert,
)


class TestSchedulePredictionService(unittest.TestCase):
    """SchedulePredictionService 测试类"""

    def setUp(self):
        """每个测试前的设置"""
        self.db_mock = MagicMock()
        self.service = SchedulePredictionService(db=self.db_mock)
        
        # Mock AI client
        self.service.ai_client = MagicMock()

    def tearDown(self):
        """每个测试后的清理"""
        self.db_mock.reset_mock()

    # ========== predict_completion_date 测试 ==========
    
    def test_predict_completion_date_with_ai_success(self):
        """测试使用AI成功预测完成日期"""
        # Mock AI response
        ai_response = {
            "content": '{"delay_days": 10, "confidence": 0.85, "risk_factors": ["进度偏差"], "recommendations": ["加班"]}'
        }
        self.service.ai_client.generate_solution.return_value = ai_response
        
        # Mock 数据库保存
        prediction_record = MagicMock()
        prediction_record.id = 123
        
        with patch('app.services.schedule_prediction_service.save_obj') as mock_save, \
             patch('app.services.schedule_prediction_service.ProjectSchedulePrediction', return_value=prediction_record):
            
            result = self.service.predict_completion_date(
                project_id=1,
                current_progress=50.0,
                planned_progress=60.0,
                remaining_days=30,
                team_size=5,
                use_ai=True
            )
        
        # 验证结果
        self.assertEqual(result['project_id'], 1)
        self.assertEqual(result['prediction']['delay_days'], 10)
        self.assertEqual(result['prediction']['confidence'], 0.85)
        self.assertIn('risk_level', result['prediction'])
        mock_save.assert_called_once()

    def test_predict_completion_date_without_ai(self):
        """测试不使用AI的线性预测"""
        prediction_record = MagicMock()
        prediction_record.id = 124
        
        with patch('app.services.schedule_prediction_service.save_obj'), \
             patch('app.services.schedule_prediction_service.ProjectSchedulePrediction', return_value=prediction_record):
            
            result = self.service.predict_completion_date(
                project_id=2,
                current_progress=80.0,
                planned_progress=80.0,
                remaining_days=20,
                team_size=3,
                use_ai=False
            )
        
        self.assertEqual(result['project_id'], 2)
        self.assertIsNotNone(result['prediction']['delay_days'])

    def test_predict_completion_date_with_project_data(self):
        """测试带项目详细数据的预测"""
        project_data = {
            'name': '测试项目',
            'type': '非标自动化',
            'days_elapsed': 40,
            'complexity': 'high'
        }
        
        ai_response = {
            "content": '{"delay_days": 5, "confidence": 0.9, "risk_factors": [], "recommendations": []}'
        }
        self.service.ai_client.generate_solution.return_value = ai_response
        
        prediction_record = MagicMock()
        prediction_record.id = 125
        
        with patch('app.services.schedule_prediction_service.save_obj'), \
             patch('app.services.schedule_prediction_service.ProjectSchedulePrediction', return_value=prediction_record):
            
            result = self.service.predict_completion_date(
                project_id=3,
                current_progress=70.0,
                planned_progress=75.0,
                remaining_days=15,
                team_size=8,
                project_data=project_data,
                use_ai=True
            )
        
        self.assertEqual(result['features']['complexity'], 'high')
        self.assertIn('days_elapsed', project_data)

    def test_predict_completion_date_exception_handling(self):
        """测试预测过程中的异常处理（降级到线性预测）"""
        self.service.ai_client.generate_solution.side_effect = Exception("AI服务异常")
        
        prediction_record = MagicMock()
        prediction_record.id = 126
        
        with patch('app.services.schedule_prediction_service.save_obj'), \
             patch('app.services.schedule_prediction_service.ProjectSchedulePrediction', return_value=prediction_record):
            
            # AI失败时应该降级到线性预测，而不是抛异常
            result = self.service.predict_completion_date(
                project_id=4,
                current_progress=50.0,
                planned_progress=60.0,
                remaining_days=30,
                team_size=5,
                use_ai=True
            )
            
            # 验证结果存在并包含必要字段
            self.assertIsNotNone(result)
            self.assertIn('prediction', result)
            self.assertIn('delay_days', result['prediction'])

    # ========== _extract_features 测试 ==========
    
    def test_extract_features_basic(self):
        """测试基本特征提取"""
        # Mock similar projects stats
        self.service._get_similar_projects_stats = MagicMock(return_value={
            'avg_duration': 90,
            'delay_rate': 0.3
        })
        
        features = self.service._extract_features(
            project_id=1,
            current_progress=50.0,
            planned_progress=60.0,
            remaining_days=30,
            team_size=5
        )
        
        self.assertEqual(features['current_progress'], 50.0)
        self.assertEqual(features['planned_progress'], 60.0)
        self.assertEqual(features['progress_deviation'], -10.0)
        self.assertEqual(features['remaining_progress'], 50.0)
        self.assertEqual(features['team_size'], 5)
        self.assertIn('velocity_ratio', features)

    def test_extract_features_with_project_data(self):
        """测试带项目数据的特征提取"""
        self.service._get_similar_projects_stats = MagicMock(return_value={
            'avg_duration': 90,
            'delay_rate': 0.3
        })
        
        project_data = {
            'days_elapsed': 50,
            'complexity': 'high'
        }
        
        features = self.service._extract_features(
            project_id=2,
            current_progress=75.0,
            planned_progress=70.0,
            remaining_days=20,
            team_size=10,
            project_data=project_data
        )
        
        self.assertEqual(features['complexity'], 'high')
        self.assertAlmostEqual(features['avg_daily_progress'], 75.0 / 50, places=2)

    def test_extract_features_zero_remaining_days(self):
        """测试剩余天数为0的边界情况"""
        self.service._get_similar_projects_stats = MagicMock(return_value={
            'avg_duration': 90,
            'delay_rate': 0.3
        })
        
        features = self.service._extract_features(
            project_id=3,
            current_progress=95.0,
            planned_progress=100.0,
            remaining_days=0,
            team_size=5
        )
        
        self.assertEqual(features['remaining_days'], 0)
        self.assertEqual(features['required_daily_progress'], 0)

    def test_extract_features_zero_days_elapsed(self):
        """测试已用天数为0的边界情况"""
        self.service._get_similar_projects_stats = MagicMock(return_value={
            'avg_duration': 90,
            'delay_rate': 0.3
        })
        
        project_data = {'days_elapsed': 0}
        
        features = self.service._extract_features(
            project_id=4,
            current_progress=10.0,
            planned_progress=5.0,
            remaining_days=50,
            team_size=3,
            project_data=project_data
        )
        
        self.assertEqual(features['avg_daily_progress'], 0)

    def test_extract_features_velocity_ratio_calculation(self):
        """测试速度比率计算"""
        self.service._get_similar_projects_stats = MagicMock(return_value={
            'avg_duration': 90,
            'delay_rate': 0.3
        })
        
        project_data = {'days_elapsed': 40}
        
        features = self.service._extract_features(
            project_id=5,
            current_progress=60.0,
            planned_progress=60.0,
            remaining_days=30,
            team_size=5,
            project_data=project_data
        )
        
        # avg_daily = 60/40 = 1.5
        # required_daily = 40/30 = 1.33
        # ratio = 1.5/1.33 ≈ 1.125
        self.assertGreater(features['velocity_ratio'], 1.0)

    # ========== _predict_with_ai 测试 ==========
    
    def test_predict_with_ai_success(self):
        """测试AI预测成功"""
        features = {
            'current_progress': 50.0,
            'planned_progress': 60.0,
            'remaining_days': 30,
            'remaining_progress': 50.0,
            'velocity_ratio': 0.8,
            'progress_deviation': -10.0,
            'team_size': 5,
            'avg_daily_progress': 1.25,
            'required_daily_progress': 1.67,
            'complexity': 'medium',
            'similar_projects_avg_duration': 90,
            'similar_projects_delay_rate': 0.3
        }
        
        ai_response = {
            "content": '{"delay_days": 15, "confidence": 0.82, "risk_factors": ["速度不足"], "recommendations": ["增加人力"]}'
        }
        self.service.ai_client.generate_solution.return_value = ai_response
        
        result = self.service._predict_with_ai(features)
        
        self.assertEqual(result['delay_days'], 15)
        self.assertEqual(result['confidence'], 0.82)
        self.assertIn('predicted_date', result)

    def test_predict_with_ai_fallback_to_linear(self):
        """测试AI失败时降级到线性预测"""
        features = {
            'current_progress': 50.0,
            'velocity_ratio': 0.9,
            'remaining_days': 30
        }
        
        # Mock AI client to raise exception
        self.service.ai_client.generate_solution.side_effect = Exception("AI服务不可用")
        
        result = self.service._predict_with_ai(features)
        
        # Should fallback to linear prediction
        self.assertIn('delay_days', result)
        self.assertIn('confidence', result)

    def test_predict_with_ai_invalid_json_response(self):
        """测试AI返回无效JSON时的处理"""
        features = {
            'current_progress': 50.0,
            'velocity_ratio': 0.8,
            'remaining_days': 30
        }
        
        ai_response = {
            "content": '这不是有效的JSON格式'
        }
        self.service.ai_client.generate_solution.return_value = ai_response
        
        result = self.service._predict_with_ai(features)
        
        # Should fallback to linear prediction
        self.assertIn('delay_days', result)

    # ========== _parse_ai_prediction 测试 ==========
    
    def test_parse_ai_prediction_valid_json(self):
        """测试解析有效的AI响应"""
        ai_response = '{"delay_days": 10, "confidence": 0.85, "risk_factors": ["test"], "recommendations": ["test"]}'
        features = {'remaining_days': 30}
        
        result = self.service._parse_ai_prediction(ai_response, features)
        
        self.assertEqual(result['delay_days'], 10)
        self.assertEqual(result['confidence'], 0.85)
        self.assertIsInstance(result['predicted_date'], date)

    def test_parse_ai_prediction_json_with_extra_text(self):
        """测试带额外文本的AI响应"""
        ai_response = '这是一些说明文字 {"delay_days": 5, "confidence": 0.9} 这是结尾'
        features = {'remaining_days': 20}
        
        result = self.service._parse_ai_prediction(ai_response, features)
        
        self.assertEqual(result['delay_days'], 5)
        self.assertEqual(result['confidence'], 0.9)

    def test_parse_ai_prediction_missing_fields(self):
        """测试缺少字段的AI响应"""
        ai_response = '{"delay_days": 7}'
        features = {'remaining_days': 25}
        
        result = self.service._parse_ai_prediction(ai_response, features)
        
        self.assertEqual(result['delay_days'], 7)
        self.assertIn('confidence', result)  # Should have default value

    def test_parse_ai_prediction_invalid_format(self):
        """测试完全无效的响应格式"""
        ai_response = '完全没有JSON的纯文本'
        features = {'remaining_days': 30, 'velocity_ratio': 0.8}
        
        result = self.service._parse_ai_prediction(ai_response, features)
        
        # Should fallback to linear prediction
        self.assertIn('delay_days', result)
        self.assertIn('details', result)

    # ========== _predict_linear 测试 ==========
    
    def test_predict_linear_on_schedule(self):
        """测试线性预测 - 按计划进行"""
        features = {
            'velocity_ratio': 1.0,
            'remaining_days': 30
        }
        
        result = self.service._predict_linear(features)
        
        self.assertEqual(result['delay_days'], 0)
        self.assertEqual(result['confidence'], 0.8)

    def test_predict_linear_ahead_schedule(self):
        """测试线性预测 - 进度超前"""
        features = {
            'velocity_ratio': 1.5,
            'remaining_days': 20
        }
        
        result = self.service._predict_linear(features)
        
        self.assertEqual(result['delay_days'], 0)

    def test_predict_linear_behind_schedule(self):
        """测试线性预测 - 进度滞后"""
        features = {
            'velocity_ratio': 0.5,
            'remaining_days': 30
        }
        
        result = self.service._predict_linear(features)
        
        self.assertGreater(result['delay_days'], 0)
        self.assertEqual(result['confidence'], 0.7)

    def test_predict_linear_calculation_accuracy(self):
        """测试线性预测计算准确性"""
        features = {
            'velocity_ratio': 0.8,
            'remaining_days': 40
        }
        
        result = self.service._predict_linear(features)
        
        # delay = 40 * (1/0.8 - 1) = 40 * 0.25 = 10
        expected_delay = int(40 * (1.0 / 0.8 - 1.0))
        self.assertEqual(result['delay_days'], expected_delay)

    # ========== _assess_risk_level 测试 ==========
    
    def test_assess_risk_level_low_early_completion(self):
        """测试风险评估 - 提前完成"""
        risk = self.service._assess_risk_level(-5)
        self.assertEqual(risk, 'low')

    def test_assess_risk_level_low_minor_delay(self):
        """测试风险评估 - 轻微延期"""
        risk = self.service._assess_risk_level(2)
        self.assertEqual(risk, 'low')

    def test_assess_risk_level_medium(self):
        """测试风险评估 - 中等延期"""
        risk = self.service._assess_risk_level(5)
        self.assertEqual(risk, 'medium')

    def test_assess_risk_level_high(self):
        """测试风险评估 - 高延期"""
        risk = self.service._assess_risk_level(10)
        self.assertEqual(risk, 'high')

    def test_assess_risk_level_critical(self):
        """测试风险评估 - 严重延期"""
        risk = self.service._assess_risk_level(20)
        self.assertEqual(risk, 'critical')

    def test_assess_risk_level_boundary_values(self):
        """测试风险评估边界值"""
        self.assertEqual(self.service._assess_risk_level(0), 'low')
        self.assertEqual(self.service._assess_risk_level(3), 'low')
        self.assertEqual(self.service._assess_risk_level(4), 'medium')
        self.assertEqual(self.service._assess_risk_level(7), 'medium')
        self.assertEqual(self.service._assess_risk_level(8), 'high')
        self.assertEqual(self.service._assess_risk_level(14), 'high')
        self.assertEqual(self.service._assess_risk_level(15), 'critical')

    # ========== _get_similar_projects_stats 测试 ==========
    
    def test_get_similar_projects_stats_with_data(self):
        """测试获取类似项目统计 - 有数据"""
        # Mock database query
        mock_predictions = [
            MagicMock(delay_days=5),
            MagicMock(delay_days=10),
            MagicMock(delay_days=0),
            MagicMock(delay_days=-2),
        ]
        
        query_mock = MagicMock()
        self.db_mock.query.return_value.filter.return_value.limit.return_value.all.return_value = mock_predictions
        
        stats = self.service._get_similar_projects_stats('medium', 5)
        
        self.assertIn('delay_rate', stats)
        self.assertIn('avg_delay', stats)

    def test_get_similar_projects_stats_no_data(self):
        """测试获取类似项目统计 - 无数据"""
        self.db_mock.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        stats = self.service._get_similar_projects_stats('high', 10)
        
        # Should return default values
        self.assertEqual(stats['avg_duration'], 90)
        self.assertEqual(stats['delay_rate'], 0.3)

    def test_get_similar_projects_stats_exception_handling(self):
        """测试获取统计时的异常处理"""
        self.db_mock.query.side_effect = Exception("Database error")
        
        stats = self.service._get_similar_projects_stats('low', 3)
        
        # Should return default values
        self.assertEqual(stats['avg_duration'], 90)
        self.assertEqual(stats['delay_rate'], 0.3)

    # ========== generate_catch_up_solutions 测试 ==========
    
    def test_generate_catch_up_solutions_success(self):
        """测试成功生成赶工方案"""
        ai_response = {
            "content": json.dumps({
                "solutions": [
                    {
                        "name": "加班方案",
                        "type": "overtime",
                        "description": "通过加班追赶进度",
                        "actions": [{"action": "周末加班", "priority": 1}],
                        "estimated_catch_up": 5,
                        "additional_cost": 5000,
                        "risk": "low",
                        "success_rate": 0.8,
                        "evaluation": {"pros": ["成本低"], "cons": []}
                    }
                ],
                "recommended_index": 0
            })
        }
        self.service.ai_client.generate_solution.return_value = ai_response
        
        # Mock database - 设置具体属性而非MagicMock
        solution_mock = MagicMock()
        solution_mock.id = 1
        solution_mock.solution_name = "加班方案"
        solution_mock.solution_type = "overtime"
        solution_mock.actions = [{"action": "周末加班", "priority": 1}]
        solution_mock.estimated_catch_up_days = 5
        solution_mock.additional_cost = Decimal("5000")
        solution_mock.risk_level = "low"
        solution_mock.success_rate = Decimal("0.8")
        solution_mock.is_recommended = True
        
        self.db_mock.add = MagicMock()
        self.db_mock.commit = MagicMock()
        
        with patch('app.services.schedule_prediction_service.CatchUpSolution', return_value=solution_mock):
            solutions = self.service.generate_catch_up_solutions(
                project_id=1,
                prediction_id=100,
                delay_days=10
            )
        
        self.assertGreater(len(solutions), 0)
        self.assertEqual(solutions[0]['name'], '加班方案')

    def test_generate_catch_up_solutions_with_project_data(self):
        """测试带项目数据生成赶工方案"""
        project_data = {
            'budget_remaining': 50000,
            'team_size': 5,
            'available_resources': '外包人员池'
        }
        
        ai_response = {
            "content": json.dumps({
                "solutions": [
                    {
                        "name": "增加人力",
                        "type": "manpower",
                        "description": "临时增加人员",
                        "actions": [{"action": "招聘外包", "priority": 1}],
                        "estimated_catch_up": 8,
                        "additional_cost": 20000,
                        "risk": "medium",
                        "success_rate": 0.75,
                        "evaluation": {"pros": [], "cons": []}
                    }
                ],
                "recommended_index": 0
            })
        }
        self.service.ai_client.generate_solution.return_value = ai_response
        
        solution_mock = MagicMock()
        solution_mock.id = 2
        self.db_mock.add = MagicMock()
        self.db_mock.commit = MagicMock()
        
        with patch('app.services.schedule_prediction_service.CatchUpSolution', return_value=solution_mock):
            solutions = self.service.generate_catch_up_solutions(
                project_id=2,
                prediction_id=101,
                delay_days=15,
                project_data=project_data
            )
        
        self.assertGreater(len(solutions), 0)

    def test_generate_catch_up_solutions_ai_fallback(self):
        """测试生成赶工方案AI失败时降级到默认方案"""
        self.service.ai_client.generate_solution.side_effect = Exception("AI失败")
        
        # Mock database
        solution_mock = MagicMock()
        solution_mock.id = 3
        solution_mock.solution_name = "加班赶工方案"
        solution_mock.solution_type = "overtime"
        solution_mock.actions = []
        solution_mock.estimated_catch_up_days = 6
        solution_mock.additional_cost = Decimal("8000")
        solution_mock.risk_level = "low"
        solution_mock.success_rate = Decimal("0.8")
        solution_mock.is_recommended = True
        
        self.db_mock.add = MagicMock()
        self.db_mock.commit = MagicMock()
        
        with patch('app.services.schedule_prediction_service.CatchUpSolution', return_value=solution_mock):
            # AI失败时应降级到默认方案，而非抛出异常
            solutions = self.service.generate_catch_up_solutions(
                project_id=3,
                prediction_id=102,
                delay_days=10
            )
            
            # 验证返回了默认方案
            self.assertGreater(len(solutions), 0)

    # ========== _generate_solutions_with_ai 测试 ==========
    
    def test_generate_solutions_with_ai_success(self):
        """测试AI生成方案成功"""
        ai_response = {
            "content": json.dumps({
                "solutions": [
                    {
                        "name": "方案1",
                        "type": "overtime",
                        "estimated_catch_up": 5,
                        "additional_cost": 5000,
                        "risk": "low",
                        "success_rate": 0.8
                    }
                ],
                "recommended_index": 0
            })
        }
        self.service.ai_client.generate_solution.return_value = ai_response
        
        solutions = self.service._generate_solutions_with_ai(10)
        
        self.assertGreater(len(solutions), 0)
        self.assertEqual(solutions[0]['name'], '方案1')

    def test_generate_solutions_with_ai_fallback(self):
        """测试AI失败时降级到默认方案"""
        self.service.ai_client.generate_solution.side_effect = Exception("AI不可用")
        
        solutions = self.service._generate_solutions_with_ai(10)
        
        # Should return default solutions
        self.assertGreater(len(solutions), 0)
        self.assertIn('name', solutions[0])

    # ========== _parse_ai_solutions 测试 ==========
    
    def test_parse_ai_solutions_valid(self):
        """测试解析有效的AI方案"""
        ai_response = json.dumps({
            "solutions": [
                {"name": "方案A", "type": "overtime"},
                {"name": "方案B", "type": "manpower"}
            ],
            "recommended_index": 1
        })
        
        solutions = self.service._parse_ai_solutions(ai_response)
        
        self.assertEqual(len(solutions), 2)
        self.assertEqual(solutions[0]['recommended_index'], 1)

    def test_parse_ai_solutions_invalid(self):
        """测试解析无效的AI方案响应"""
        ai_response = "这不是有效的JSON"
        
        solutions = self.service._parse_ai_solutions(ai_response)
        
        self.assertEqual(solutions, [])

    # ========== _generate_default_solutions 测试 ==========
    
    def test_generate_default_solutions(self):
        """测试生成默认赶工方案"""
        solutions = self.service._generate_default_solutions(10)
        
        self.assertEqual(len(solutions), 3)
        self.assertIn('name', solutions[0])
        self.assertIn('type', solutions[0])
        self.assertIn('estimated_catch_up', solutions[0])

    def test_generate_default_solutions_large_delay(self):
        """测试大延期情况的默认方案"""
        solutions = self.service._generate_default_solutions(30)
        
        self.assertEqual(len(solutions), 3)
        # Check that catch up days are capped
        for sol in solutions:
            self.assertLessEqual(sol['estimated_catch_up'], 30)

    # ========== create_alert 测试 ==========
    
    def test_create_alert_basic(self):
        """测试创建基本预警"""
        alert_mock = MagicMock()
        alert_mock.id = 1
        
        with patch('app.services.schedule_prediction_service.save_obj'), \
             patch('app.services.schedule_prediction_service.ScheduleAlert', return_value=alert_mock):
            
            alert = self.service.create_alert(
                project_id=1,
                prediction_id=100,
                alert_type='delay_warning',
                severity='high',
                title='延期预警',
                message='项目预计延期10天'
            )
        
        self.assertEqual(alert.id, 1)

    def test_create_alert_with_notify_users(self):
        """测试创建预警并通知用户"""
        alert_mock = MagicMock()
        alert_mock.id = 2
        
        with patch('app.services.schedule_prediction_service.save_obj'), \
             patch('app.services.schedule_prediction_service.ScheduleAlert', return_value=alert_mock) as mock_alert:
            
            alert = self.service.create_alert(
                project_id=2,
                prediction_id=101,
                alert_type='velocity_drop',
                severity='medium',
                title='速度下降',
                message='进度放缓',
                notify_users=[1, 2, 3]
            )
        
        # Verify notified_users was passed
        call_kwargs = mock_alert.call_args[1]
        self.assertEqual(len(call_kwargs['notified_users']), 3)

    def test_create_alert_with_details(self):
        """测试创建带详情的预警"""
        alert_mock = MagicMock()
        alert_details = {'delay_days': 10, 'velocity': 0.8}
        
        with patch('app.services.schedule_prediction_service.save_obj'), \
             patch('app.services.schedule_prediction_service.ScheduleAlert', return_value=alert_mock):
            
            alert = self.service.create_alert(
                project_id=3,
                prediction_id=102,
                alert_type='delay_warning',
                severity='critical',
                title='严重延期',
                message='项目严重滞后',
                alert_details=alert_details
            )
        
        self.assertIsNotNone(alert)

    # ========== check_and_create_alerts 测试 ==========
    
    def test_check_and_create_alerts_delay_warning(self):
        """测试延期预警创建"""
        alert_mock = MagicMock()
        
        with patch.object(self.service, 'create_alert', return_value=alert_mock) as mock_create:
            alerts = self.service.check_and_create_alerts(
                project_id=1,
                prediction_id=100,
                delay_days=10,
                progress_deviation=-5.0
            )
        
        self.assertGreater(len(alerts), 0)
        # Should create delay warning
        self.assertTrue(any(call_args[1]['alert_type'] == 'delay_warning' 
                           for call_args in mock_create.call_args_list))

    def test_check_and_create_alerts_progress_deviation(self):
        """测试进度偏差预警"""
        alert_mock = MagicMock()
        
        with patch.object(self.service, 'create_alert', return_value=alert_mock) as mock_create:
            alerts = self.service.check_and_create_alerts(
                project_id=2,
                prediction_id=101,
                delay_days=1,
                progress_deviation=-15.0
            )
        
        # Should create velocity drop alert
        self.assertTrue(any(call_args[1]['alert_type'] == 'velocity_drop' 
                           for call_args in mock_create.call_args_list))

    def test_check_and_create_alerts_multiple_alerts(self):
        """测试同时创建多个预警"""
        alert_mock = MagicMock()
        
        with patch.object(self.service, 'create_alert', return_value=alert_mock) as mock_create:
            alerts = self.service.check_and_create_alerts(
                project_id=3,
                prediction_id=102,
                delay_days=15,
                progress_deviation=-20.0
            )
        
        # Should create both alerts
        self.assertEqual(len(alerts), 2)

    def test_check_and_create_alerts_no_alerts(self):
        """测试不需要创建预警的情况"""
        with patch.object(self.service, 'create_alert') as mock_create:
            alerts = self.service.check_and_create_alerts(
                project_id=4,
                prediction_id=103,
                delay_days=1,
                progress_deviation=2.0
            )
        
        # Should not create any alerts
        self.assertEqual(len(alerts), 0)
        mock_create.assert_not_called()

    # ========== get_project_alerts 测试 ==========
    
    def test_get_project_alerts_basic(self):
        """测试获取项目预警列表"""
        mock_alerts = [
            MagicMock(
                id=1,
                alert_type='delay_warning',
                severity='high',
                title='延期预警',
                message='延期10天',
                alert_details={'delay': 10},
                is_read=False,
                is_resolved=False,
                created_at=datetime.now()
            )
        ]
        
        self.db_mock.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_alerts
        
        alerts = self.service.get_project_alerts(project_id=1)
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['type'], 'delay_warning')

    def test_get_project_alerts_with_severity_filter(self):
        """测试按严重程度过滤预警"""
        mock_alerts = []
        self.db_mock.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_alerts
        
        alerts = self.service.get_project_alerts(project_id=2, severity='critical')
        
        self.assertEqual(len(alerts), 0)

    def test_get_project_alerts_unread_only(self):
        """测试只获取未读预警"""
        mock_alerts = [
            MagicMock(
                id=1,
                alert_type='delay_warning',
                severity='medium',
                title='预警',
                message='消息',
                alert_details={},
                is_read=False,
                is_resolved=False,
                created_at=datetime.now()
            )
        ]
        
        self.db_mock.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_alerts
        
        alerts = self.service.get_project_alerts(project_id=3, unread_only=True)
        
        self.assertEqual(len(alerts), 1)

    # ========== get_risk_overview 测试 ==========
    
    def test_get_risk_overview_with_projects(self):
        """测试获取风险概览 - 有项目"""
        mock_predictions = [
            MagicMock(
                project_id=1,
                risk_level='critical',
                delay_days=20,
                predicted_completion_date=date.today() + timedelta(days=50)
            ),
            MagicMock(
                project_id=2,
                risk_level='high',
                delay_days=10,
                predicted_completion_date=date.today() + timedelta(days=30)
            ),
            MagicMock(
                project_id=3,
                risk_level='low',
                delay_days=0,
                predicted_completion_date=date.today() + timedelta(days=20)
            )
        ]
        
        # Mock the query chain
        self.db_mock.query.return_value.join.return_value.all.return_value = mock_predictions
        
        overview = self.service.get_risk_overview()
        
        self.assertEqual(overview['total_projects'], 3)
        self.assertEqual(overview['at_risk'], 2)  # critical + high
        self.assertEqual(overview['critical'], 1)
        self.assertEqual(len(overview['projects']), 2)  # Only high and critical

    def test_get_risk_overview_empty(self):
        """测试获取风险概览 - 无项目"""
        # Mock the query chain
        self.db_mock.query.return_value.join.return_value.all.return_value = []
        
        overview = self.service.get_risk_overview()
        
        self.assertEqual(overview['total_projects'], 0)
        self.assertEqual(overview['at_risk'], 0)
        self.assertEqual(overview['critical'], 0)


if __name__ == '__main__':
    unittest.main()
