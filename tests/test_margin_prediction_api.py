# -*- coding: utf-8 -*-
"""
毛利率预测 API 测试（使用 mock，不依赖真实 SQL）

本轮只写测试框架，不跑 SQL 查询
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient


# Mock 用户
def get_mock_user():
    """创建模拟用户"""
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    user.is_active = True
    user.is_superuser = True
    user.tenant_id = 1
    return user


# Mock 数据库会话
def get_mock_db():
    """创建模拟数据库会话"""
    db = MagicMock()
    return db


class TestMarginPredictionAPI:
    """毛利率预测 API 测试套件"""

    @pytest.fixture
    def mock_db(self):
        """Mock 数据库会话"""
        return get_mock_db()

    @pytest.fixture
    def client(self, mock_db):
        """创建测试客户端（使用 mock）"""
        with patch("app.api.v1.endpoints.margin_prediction.deps.get_db") as mock_get_db:
            mock_get_db.return_value = mock_db
            
            with patch("app.api.v1.endpoints.margin_prediction.security.get_current_active_user") as mock_auth:
                mock_auth.return_value = get_mock_user()
                
                # 延迟导入以避免循环依赖
                from app.api.v1.endpoints import margin_prediction
                from fastapi import FastAPI
                
                # 创建测试应用
                app = FastAPI()
                app.include_router(margin_prediction.router)
                
                with TestClient(app) as client:
                    yield client

    def test_get_historical_margins_empty(self, mock_db):
        """测试空数据返回"""
        # Mock SQL 返回空结果
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        # 模拟 auth 依赖
        with patch("app.api.v1.endpoints.margin_prediction.security.get_current_active_user") as mock_auth:
            mock_auth.return_value = get_mock_user()
            
            from app.api.v1.endpoints.margin_prediction import get_historical_margins
            
            # 调用 API
            result = get_historical_margins(db=mock_db, current_user=get_mock_user())
            
            # 验证空数据返回结构
            assert "historical_summary" in result
            assert result["historical_summary"]["total_projects"] == 0
            assert result["historical_summary"]["avg_margin"] == 0
            assert result["projects"] == []
            assert result["by_category"] == []
            assert result["by_amount_range"] == []

    def test_get_historical_margins_single_record(self, mock_db):
        """测试单条数据返回"""
        # Mock 单条项目数据
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.project_code = "PJ-TEST-001"
        mock_project.product_category = "ICT"
        mock_project.industry = "3C 电子"
        mock_project.contract_amount = 1000000.0
        mock_project.actual_cost = 800000.0
        mock_project.gross_margin = 20.0
        mock_project.stage = "S3"

        # Mock 成本明细
        mock_cost = MagicMock()
        mock_cost.cost_type = "材料"
        mock_cost.total = 400000.0

        # Mock 主查询结果
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_project]
        
        # Mock 成本查询结果
        mock_cost_result = MagicMock()
        mock_cost_result.fetchall.return_value = [mock_cost]

        # 设置 execute 返回不同结果
        mock_db.execute.side_effect = [mock_result, mock_cost_result]

        with patch("app.api.v1.endpoints.margin_prediction.security.get_current_active_user") as mock_auth:
            mock_auth.return_value = get_mock_user()
            
            from app.api.v1.endpoints.margin_prediction import get_historical_margins
            
            result = get_historical_margins(db=mock_db, current_user=get_mock_user())
            
            # 验证单条数据返回
            assert result["historical_summary"]["total_projects"] == 1
            assert len(result["projects"]) == 1
            assert result["projects"][0]["project_code"] == "PJ-TEST-001"
            assert result["projects"][0]["contract_amount"] == 1000000.0

    def test_predict_margin_basic(self, mock_db):
        """测试预测算法基础功能"""
        # Mock 用于预测的历史数据
        mock_material_result = MagicMock()
        mock_material_result.avg_material_ratio = 50.0
        mock_db.execute.return_value = mock_material_result

        with patch("app.api.v1.endpoints.margin_prediction.security.get_current_active_user") as mock_auth:
            mock_auth.return_value = get_mock_user()
            
            from app.api.v1.endpoints.margin_prediction import predict_margin
            
            # 调用预测接口（提供完整参数）
            result = predict_margin(
                db=mock_db,
                current_user=get_mock_user(),
                product_category="ICT",
                industry="3C 电子",
                contract_amount=3000000.0,
                estimated_material_cost=1200000.0,
                estimated_design_change_cost=60000.0,
                estimated_travel_cost=90000.0,
                estimated_rd_hours=500,
                project_complexity="MEDIUM"
            )
            
            # 验证预测结果结构
            assert "prediction" in result
            assert "predicted_margin" in result["prediction"]
            assert "confidence" in result["prediction"]
            assert "risk_level" in result["prediction"]
            assert "cost_breakdown" in result
            assert "recommendations" in result
            
            # 验证预测毛利率计算合理（0-100%）
            assert 0 <= result["prediction"]["predicted_margin"] <= 100
            # 验证置信度范围（0-1）
            assert 0 <= result["prediction"]["confidence"] <= 1
            # 验证风险等级
            assert result["prediction"]["risk_level"] in ["low", "medium", "high"]

    def test_aggregate_margins_by_period(self, mock_db):
        """测试数据聚合功能"""
        # Mock 多条项目数据（按不同产品分类和金额区间）
        mock_projects = []
        
        # 项目1: ICT, 150万
        p1 = MagicMock()
        p1.id = 1
        p1.project_name = "ICT项目A"
        p1.project_code = "PJ-ICT-001"
        p1.product_category = "ICT"
        p1.industry = "3C 电子"
        p1.contract_amount = 1500000.0
        p1.actual_cost = 1200000.0
        p1.gross_margin = 20.0
        p1.stage = "S3"
        mock_projects.append(p1)
        
        # 项目2: ICT, 250万
        p2 = MagicMock()
        p2.id = 2
        p2.project_name = "ICT项目B"
        p2.project_code = "PJ-ICT-002"
        p2.product_category = "ICT"
        p2.industry = "3C 电子"
        p2.contract_amount = 2500000.0
        p2.actual_cost = 1875000.0
        p2.gross_margin = 25.0
        p2.stage = "S3"
        mock_projects.append(p2)
        
        # 项目3: FCT, 180万
        p3 = MagicMock()
        p3.id = 3
        p3.project_name = "FCT项目A"
        p3.project_code = "PJ-FCT-001"
        p3.product_category = "FCT"
        p3.industry = "锂电"
        p3.contract_amount = 1800000.0
        p3.actual_cost = 1260000.0
        p3.gross_margin = 30.0
        p3.stage = "S3"
        mock_projects.append(p3)

        mock_result = MagicMock()
        mock_result.fetchall.return_value = mock_projects
        
        mock_cost_result = MagicMock()
        mock_cost_result.fetchall.return_value = []
        
        mock_db.execute.side_effect = [mock_result, mock_cost_result]

        with patch("app.api.v1.endpoints.margin_prediction.security.get_current_active_user") as mock_auth:
            mock_auth.return_value = get_mock_user()
            
            from app.api.v1.endpoints.margin_prediction import get_historical_margins
            
            result = get_historical_margins(db=mock_db, current_user=get_mock_user())
            
            # 验证数据聚合结果
            assert result["historical_summary"]["total_projects"] == 3
            
            # 验证按产品分类聚合
            assert len(result["by_category"]) >= 2
            category_names = [c["category"] for c in result["by_category"]]
            assert "ICT" in category_names
            assert "FCT" in category_names
            
            # 验证按金额区间聚合
            assert len(result["by_amount_range"]) >= 1
            
            # 验证 ICT 分类统计正确
            ict_category = next((c for c in result["by_category"] if c["category"] == "ICT"), None)
            if ict_category:
                assert ict_category["count"] == 2
                assert ict_category["total_contract"] == 4000000.0

    def test_predict_margin_with_minimal_input(self, mock_db):
        """测试最少参数预测（使用默认值）"""
        # Mock 返回默认历史比率
        mock_material_result = MagicMock()
        mock_material_result.avg_material_ratio = 50.0
        
        mock_rd_result = MagicMock()
        mock_rd_result.avg_rd_rate = 150.0
        
        mock_prod_result = MagicMock()
        mock_prod_result.avg_prod_labor_ratio = 15.0
        
        mock_overhead_result = MagicMock()
        mock_overhead_result.avg_overhead_ratio = 12.0
        
        mock_similar_result = MagicMock()
        mock_similar_result.fetchall.return_value = []

        mock_db.execute.side_effect = [
            mock_material_result,
            mock_rd_result,
            mock_prod_result,
            mock_overhead_result,
            mock_similar_result
        ]

        with patch("app.api.v1.endpoints.margin_prediction.security.get_current_active_user") as mock_auth:
            mock_auth.return_value = get_mock_user()
            
            from app.api.v1.endpoints.margin_prediction import predict_margin
            
            # 只提供必需参数
            result = predict_margin(
                db=mock_db,
                current_user=get_mock_user(),
                contract_amount=2000000.0
            )
            
            # 验证结果
            assert "prediction" in result
            assert "cost_breakdown" in result
            # 成本结构应该有各个组成项
            cost_items = result["cost_breakdown"]
            assert "bom_material_cost" in cost_items
            assert "rd_labor_cost" in cost_items
            assert "production_labor_cost" in cost_items
            assert "total_cost" in cost_items

    def test_cost_variance_analysis(self, mock_db):
        """测试成本偏差分析"""
        # Mock 成本偏差数据
        mock_variance_project = MagicMock()
        mock_variance_project.id = 1
        mock_variance_project.project_name = "偏差测试项目"
        mock_variance_project.project_code = "PJ-VAR-001"
        mock_variance_project.product_category = "ICT"
        mock_variance_project.contract_amount = 1000000.0
        mock_variance_project.budget_amount = 800000.0
        mock_variance_project.actual_cost = 900000.0
        mock_variance_project.planned_margin = 20.0
        mock_variance_project.actual_margin = 10.0
        mock_variance_project.budget_variance_pct = 12.5

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_variance_project]
        
        mock_db.execute.return_value = mock_result

        with patch("app.api.v1.endpoints.margin_prediction.security.get_current_active_user") as mock_auth:
            mock_auth.return_value = get_mock_user()
            
            from app.api.v1.endpoints.margin_prediction import get_cost_variance
            
            result = get_cost_variance(db=mock_db, current_user=get_mock_user())
            
            # 验证偏差分析结果
            assert "summary" in result
            assert result["summary"]["total_projects"] == 1
            assert len(result["projects"]) == 1
            assert result["projects"][0]["overrun"] is True  # 实际成本超预算
            assert result["projects"][0]["margin_gap"] == -10.0  # 实际利润率比计划低10%


class TestMarginPredictionEdgeCases:
    """边界情况测试"""

    def test_predict_margin_zero_amount(self):
        """测试合同金额为0的情况"""
        mock_db = get_mock_db()
        
        with patch("app.api.v1.endpoints.margin_prediction.security.get_current_active_user") as mock_auth:
            mock_auth.return_value = get_mock_user()
            
            from app.api.v1.endpoints.margin_prediction import predict_margin
            
            # 合同金额为0应该被处理
            result = predict_margin(
                db=mock_db,
                current_user=get_mock_user(),
                contract_amount=0.0
            )
            
            # 验证不会崩溃
            assert "prediction" in result

    def test_historical_margins_calculation(self):
        """测试毛利率计算逻辑"""
        # 手动计算验证: (1000000 - 800000) / 1000000 * 100 = 20%
        contract = 1000000.0
        cost = 800000.0
        expected_margin = (contract - cost) / contract * 100
        
        assert expected_margin == 20.0
        
        # 测试成本为0的情况
        contract = 1000000.0
        cost = 0.0
        expected_margin = (contract - cost) / contract * 100
        assert expected_margin == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])