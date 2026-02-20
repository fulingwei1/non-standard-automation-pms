# -*- coding: utf-8 -*-
"""
ProjectRiskService 单元测试
覆盖率目标: 58%
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi import HTTPException

from app.services.project_risk.project_risk_service import ProjectRiskService
from app.models.project_risk import ProjectRisk, RiskTypeEnum, RiskStatusEnum
from app.models.project import Project
from app.models.user import User


class TestProjectRiskService(unittest.TestCase):
    """ProjectRiskService 单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.service = ProjectRiskService(self.mock_db)
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = 1
        self.mock_user.username = "testuser"
        self.mock_user.real_name = "Test User"
    
    def test_generate_risk_code_success(self):
        """测试成功生成风险编号"""
        # 准备测试数据
        mock_project = MagicMock(spec=Project)
        mock_project.project_code = "PRJ001"
        
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 5
        self.mock_db.query.return_value = mock_query
        
        # Mock get_or_404
        with patch('app.services.project_risk.project_risk_service.get_or_404') as mock_get:
            mock_get.return_value = mock_project
            
            # 执行测试
            risk_code = self.service.generate_risk_code(project_id=1)
            
            # 验证结果
            self.assertEqual(risk_code, "RISK-PRJ001-0006")
            mock_get.assert_called_once_with(self.mock_db, Project, 1, detail="项目不存在")
    
    def test_create_risk_success(self):
        """测试成功创建风险"""
        # 准备测试数据
        mock_project = MagicMock(spec=Project)
        mock_project.project_code = "PRJ001"
        
        mock_owner = MagicMock(spec=User)
        mock_owner.id = 2
        mock_owner.real_name = "Risk Owner"
        
        mock_risk = MagicMock(spec=ProjectRisk)
        mock_risk.id = 100
        mock_risk.risk_code = "RISK-PRJ001-0001"
        
        # Mock 查询
        mock_count_query = MagicMock()
        mock_count_query.filter.return_value.count.return_value = 0
        
        mock_owner_query = MagicMock()
        mock_owner_query.filter.return_value.first.return_value = mock_owner
        
        def query_side_effect(model):
            if model == ProjectRisk:
                return mock_count_query
            elif model == User:
                return mock_owner_query
            return MagicMock()
        
        self.mock_db.query.side_effect = query_side_effect
        
        with patch('app.services.project_risk.project_risk_service.get_or_404') as mock_get, \
             patch('app.services.project_risk.project_risk_service.save_obj') as mock_save, \
             patch('app.services.project_risk.project_risk_service.ProjectRisk', return_value=mock_risk):
            
            mock_get.return_value = mock_project
            mock_save.return_value = mock_risk
            
            # 执行测试
            result = self.service.create_risk(
                project_id=1,
                risk_name="Test Risk",
                description="Test Description",
                risk_type="TECHNICAL",
                probability=3,
                impact=4,
                mitigation_plan="Test Plan",
                contingency_plan="Test Contingency",
                owner_id=2,
                target_closure_date=datetime(2024, 12, 31),
                current_user=self.mock_user,
            )
            
            # 验证结果
            self.assertEqual(result, mock_risk)
            mock_risk.calculate_risk_score.assert_called_once()
            mock_save.assert_called_once()
    
    def test_get_risk_list_with_filters(self):
        """测试获取风险列表（带筛选条件）"""
        # 准备测试数据
        mock_risks = [MagicMock(spec=ProjectRisk) for _ in range(3)]
        
        mock_query = MagicMock()
        mock_filter_chain = MagicMock()
        mock_filter_chain.filter.return_value = mock_filter_chain
        mock_filter_chain.count.return_value = 3
        mock_filter_chain.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_risks
        
        mock_query.filter.return_value = mock_filter_chain
        self.mock_db.query.return_value = mock_query
        
        with patch('app.services.project_risk.project_risk_service.get_or_404'):
            # 执行测试
            risks, total = self.service.get_risk_list(
                project_id=1,
                risk_type="TECHNICAL",
                risk_level="HIGH",
                status="IDENTIFIED",
                owner_id=2,
                is_occurred=False,
                offset=0,
                limit=10,
            )
            
            # 验证结果
            self.assertEqual(len(risks), 3)
            self.assertEqual(total, 3)
            self.assertEqual(mock_filter_chain.filter.call_count, 6)  # project_id + 5 filters
    
    def test_get_risk_by_id_success(self):
        """测试成功获取风险详情"""
        # 准备测试数据
        mock_risk = MagicMock(spec=ProjectRisk)
        mock_risk.id = 1
        mock_risk.project_id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_risk
        self.mock_db.query.return_value = mock_query
        
        # 执行测试
        result = self.service.get_risk_by_id(project_id=1, risk_id=1)
        
        # 验证结果
        self.assertEqual(result, mock_risk)
    
    def test_get_risk_by_id_not_found(self):
        """测试获取不存在的风险"""
        # 准备测试数据
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # 执行测试并验证异常
        with self.assertRaises(HTTPException) as context:
            self.service.get_risk_by_id(project_id=1, risk_id=999)
        
        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "风险不存在")
    
    def test_update_risk_with_status_closure(self):
        """测试更新风险状态为已关闭"""
        # 准备测试数据
        mock_risk = MagicMock(spec=ProjectRisk)
        mock_risk.id = 1
        mock_risk.project_id = 1
        mock_risk.actual_closure_date = None
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_risk
        self.mock_db.query.return_value = mock_query
        
        update_data = {
            "status": "CLOSED",
            "description": "Updated description"
        }
        
        # 执行测试
        result = self.service.update_risk(
            project_id=1,
            risk_id=1,
            update_data=update_data,
            current_user=self.mock_user,
        )
        
        # 验证结果
        self.assertEqual(result, mock_risk)
        self.assertIsNotNone(mock_risk.actual_closure_date)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_risk)
    
    def test_update_risk_with_probability_impact(self):
        """测试更新风险概率和影响"""
        # 准备测试数据
        mock_risk = MagicMock(spec=ProjectRisk)
        mock_risk.id = 1
        mock_risk.project_id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_risk
        self.mock_db.query.return_value = mock_query
        
        update_data = {
            "probability": 5,
            "impact": 5,
        }
        
        # 执行测试
        result = self.service.update_risk(
            project_id=1,
            risk_id=1,
            update_data=update_data,
            current_user=self.mock_user,
        )
        
        # 验证结果
        mock_risk.calculate_risk_score.assert_called_once()
        self.assertEqual(mock_risk.probability, 5)
        self.assertEqual(mock_risk.impact, 5)
    
    def test_delete_risk_success(self):
        """测试成功删除风险"""
        # 准备测试数据
        mock_risk = MagicMock(spec=ProjectRisk)
        mock_risk.id = 1
        mock_risk.risk_code = "RISK-PRJ001-0001"
        mock_risk.risk_name = "Test Risk"
        mock_risk.risk_type = "TECHNICAL"
        mock_risk.risk_score = 12
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_risk
        self.mock_db.query.return_value = mock_query
        
        with patch('app.services.project_risk.project_risk_service.delete_obj') as mock_delete:
            # 执行测试
            result = self.service.delete_risk(project_id=1, risk_id=1)
            
            # 验证结果
            self.assertEqual(result["risk_code"], "RISK-PRJ001-0001")
            self.assertEqual(result["risk_name"], "Test Risk")
            self.assertEqual(result["risk_type"], "TECHNICAL")
            self.assertEqual(result["risk_score"], 12)
            mock_delete.assert_called_once_with(self.mock_db, mock_risk)
    
    def test_get_risk_matrix_success(self):
        """测试获取风险矩阵"""
        # 准备测试数据
        mock_risks = []
        for i in range(3):
            mock_risk = MagicMock(spec=ProjectRisk)
            mock_risk.id = i + 1
            mock_risk.probability = (i % 5) + 1
            mock_risk.impact = ((i + 1) % 5) + 1
            mock_risk.risk_code = f"RISK-{i+1}"
            mock_risk.risk_name = f"Risk {i+1}"
            mock_risk.risk_type = "TECHNICAL"
            mock_risk.risk_score = 10 + i
            mock_risk.risk_level = "HIGH"
            mock_risks.append(mock_risk)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_risks
        self.mock_db.query.return_value = mock_query
        
        with patch('app.services.project_risk.project_risk_service.get_or_404'):
            # 执行测试
            result = self.service.get_risk_matrix(project_id=1)
            
            # 验证结果
            self.assertIn("matrix", result)
            self.assertIn("summary", result)
            self.assertEqual(len(result["matrix"]), 25)  # 5x5 matrix
            self.assertEqual(result["summary"]["total_risks"], 3)
    
    def test_get_risk_summary_success(self):
        """测试获取风险汇总统计"""
        # 准备测试数据
        mock_risks = []
        for i in range(5):
            mock_risk = MagicMock(spec=ProjectRisk)
            mock_risk.id = i + 1
            mock_risk.risk_type = RiskTypeEnum.TECHNICAL if i % 2 == 0 else RiskTypeEnum.RESOURCE
            mock_risk.risk_level = "HIGH" if i < 2 else "MEDIUM"
            mock_risk.status = RiskStatusEnum.IDENTIFIED if i < 3 else RiskStatusEnum.CLOSED
            mock_risk.is_occurred = i < 1
            mock_risk.risk_score = 10 + i
            mock_risks.append(mock_risk)
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_risks
        self.mock_db.query.return_value = mock_query
        
        with patch('app.services.project_risk.project_risk_service.get_or_404'):
            # 执行测试
            result = self.service.get_risk_summary(project_id=1)
            
            # 验证结果
            self.assertEqual(result["total_risks"], 5)
            self.assertIn("by_type", result)
            self.assertIn("by_level", result)
            self.assertIn("by_status", result)
            self.assertEqual(result["occurred_count"], 1)
            self.assertEqual(result["closed_count"], 2)
            self.assertGreater(result["avg_risk_score"], 0)


if __name__ == "__main__":
    unittest.main()
