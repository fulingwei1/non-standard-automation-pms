# -*- coding: utf-8 -*-
"""
ProjectEvaluationService 综合单元测试

测试覆盖:
- get_dimension_weights: 获取维度权重
- get_level_thresholds: 获取评级阈值
- calculate_total_score: 计算综合得分
- determine_evaluation_level: 确定评价等级
- auto_calculate_novelty_score: 自动计算新旧得分
- auto_calculate_amount_score: 自动计算金额得分
- auto_calculate_workload_score: 自动计算工作量得分
- generate_evaluation_code: 生成评价编号
- create_evaluation: 创建评价记录
- get_latest_evaluation: 获取最新评价
- get_bonus_coefficient: 获取奖金系数
- get_difficulty_bonus_coefficient: 获取难度奖金系数
- get_new_tech_bonus_coefficient: 获取新技术奖金系数
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestProjectEvaluationServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        assert service.db == mock_db

    def test_default_weights_exist(self):
        """测试默认权重配置存在"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        assert ProjectEvaluationService.DEFAULT_WEIGHTS is not None
        assert "novelty" in ProjectEvaluationService.DEFAULT_WEIGHTS
        assert "new_tech" in ProjectEvaluationService.DEFAULT_WEIGHTS
        assert "difficulty" in ProjectEvaluationService.DEFAULT_WEIGHTS
        assert "workload" in ProjectEvaluationService.DEFAULT_WEIGHTS
        assert "amount" in ProjectEvaluationService.DEFAULT_WEIGHTS

    def test_default_level_thresholds_exist(self):
        """测试默认等级阈值存在"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        assert ProjectEvaluationService.DEFAULT_LEVEL_THRESHOLDS is not None


class TestGetDimensionWeights:
    """测试 get_dimension_weights 方法"""

    def test_returns_default_when_no_config(self):
        """测试无配置时返回默认值"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ProjectEvaluationService(mock_db)
        result = service.get_dimension_weights()

        assert result == service.DEFAULT_WEIGHTS

    def test_returns_configured_weights(self):
        """测试返回配置的权重"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()

        mock_dim1 = MagicMock()
        mock_dim1.dimension_type = "NOVELTY"
        mock_dim1.default_weight = Decimal("20")
        mock_dim1.is_active = True

        mock_dim2 = MagicMock()
        mock_dim2.dimension_type = "DIFFICULTY"
        mock_dim2.default_weight = Decimal("30")
        mock_dim2.is_active = True

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_dim1,
            mock_dim2,
        ]

        service = ProjectEvaluationService(mock_db)
        result = service.get_dimension_weights()

        assert "novelty" in result
        assert "difficulty" in result

    def test_normalizes_weights(self):
        """测试权重归一化"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()

        # 两个维度，各 50%
        mock_dim1 = MagicMock()
        mock_dim1.dimension_type = "NOVELTY"
        mock_dim1.default_weight = Decimal("50")

        mock_dim2 = MagicMock()
        mock_dim2.dimension_type = "DIFFICULTY"
        mock_dim2.default_weight = Decimal("50")

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_dim1,
            mock_dim2,
        ]

        service = ProjectEvaluationService(mock_db)
        result = service.get_dimension_weights()

        # 应该归一化为各 0.5
        total = sum(result.values())
        assert total == Decimal("1") or abs(float(total) - 1.0) < 0.01


class TestGetLevelThresholds:
    """测试 get_level_thresholds 方法"""

    def test_returns_default_when_no_config(self):
        """测试无配置时返回默认值"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProjectEvaluationService(mock_db)
        result = service.get_level_thresholds()

        assert result == service.DEFAULT_LEVEL_THRESHOLDS

    def test_returns_configured_thresholds(self):
        """测试返回配置的阈值"""
        from app.services.project_evaluation_service import ProjectEvaluationService
        from app.models.enums import ProjectEvaluationLevelEnum

        mock_db = MagicMock()

        mock_config = MagicMock()
        mock_config.scoring_rules = {
            "S": 95,
            "A": 85,
            "B": 75,
            "C": 65,
            "D": 0,
        }

        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        service = ProjectEvaluationService(mock_db)
        result = service.get_level_thresholds()

        assert result[ProjectEvaluationLevelEnum.S] == Decimal("95")
        assert result[ProjectEvaluationLevelEnum.A] == Decimal("85")


class TestCalculateTotalScore:
    """测试 calculate_total_score 方法"""

    def test_calculates_weighted_average(self):
        """测试计算加权平均"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        # 使用默认权重
        weights = {
            "novelty": Decimal("0.20"),
            "new_tech": Decimal("0.20"),
            "difficulty": Decimal("0.20"),
            "workload": Decimal("0.20"),
            "amount": Decimal("0.20"),
        }

        result = service.calculate_total_score(
            novelty_score=Decimal("80"),
            new_tech_score=Decimal("80"),
            difficulty_score=Decimal("80"),
            workload_score=Decimal("80"),
            amount_score=Decimal("80"),
            weights=weights,
        )

        assert result == Decimal("80")

    def test_uses_default_weights_when_not_provided(self):
        """测试未提供权重时使用默认权重"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ProjectEvaluationService(mock_db)

        result = service.calculate_total_score(
            novelty_score=Decimal("80"),
            new_tech_score=Decimal("80"),
            difficulty_score=Decimal("80"),
            workload_score=Decimal("80"),
            amount_score=Decimal("80"),
        )

        assert result == Decimal("80")


class TestDetermineEvaluationLevel:
    """测试 determine_evaluation_level 方法"""

    def test_returns_s_for_high_score(self):
        """测试高分返回 S 级"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProjectEvaluationService(mock_db)
        result = service.determine_evaluation_level(Decimal("95"))

        assert result == "S"

    def test_returns_a_for_good_score(self):
        """测试良好分数返回 A 级"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProjectEvaluationService(mock_db)
        result = service.determine_evaluation_level(Decimal("85"))

        assert result == "A"

    def test_returns_b_for_medium_score(self):
        """测试中等分数返回 B 级"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProjectEvaluationService(mock_db)
        result = service.determine_evaluation_level(Decimal("75"))

        assert result == "B"

    def test_returns_d_for_low_score(self):
        """测试低分返回 D 级"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProjectEvaluationService(mock_db)
        result = service.determine_evaluation_level(Decimal("50"))

        assert result == "D"


class TestAutoCalculateNoveltyScore:
    """测试 auto_calculate_novelty_score 方法"""

    def test_returns_low_score_for_new_project(self):
        """测试全新项目返回低分"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_type = "TYPE_A"
        mock_project.product_category = "CAT_A"
        mock_project.industry = "IND_A"

        result = service.auto_calculate_novelty_score(mock_project)

        assert result == Decimal("2.0")

    def test_returns_high_score_for_standard_project(self):
        """测试标准项目返回高分"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()

        # 模拟 3 个已完成的相似项目
        mock_similar1 = MagicMock()
        mock_similar1.stage = "S9"
        mock_similar2 = MagicMock()
        mock_similar2.stage = "S9"
        mock_similar3 = MagicMock()
        mock_similar3.stage = "S9"

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_similar1,
            mock_similar2,
            mock_similar3,
        ]

        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 10
        mock_project.project_type = "TYPE_A"
        mock_project.product_category = "CAT_A"
        mock_project.industry = "IND_A"

        result = service.auto_calculate_novelty_score(mock_project)

        assert result == Decimal("9.0")

    def test_returns_medium_score_for_similar_project(self):
        """测试有类似项目返回中等分数"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()

        # 模拟 1 个已完成的相似项目
        mock_similar = MagicMock()
        mock_similar.stage = "S9"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_similar]

        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 10

        result = service.auto_calculate_novelty_score(mock_project)

        assert result == Decimal("6.0")


class TestAutoCalculateAmountScore:
    """测试 auto_calculate_amount_score 方法"""

    def test_returns_low_score_for_large_amount(self):
        """测试大金额返回低分"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.contract_amount = Decimal("6000000")

        result = service.auto_calculate_amount_score(mock_project)

        assert result == Decimal("2.0")

    def test_returns_high_score_for_small_amount(self):
        """测试小金额返回高分"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.contract_amount = Decimal("300000")

        result = service.auto_calculate_amount_score(mock_project)

        assert result == Decimal("9.5")

    def test_handles_none_amount(self):
        """测试处理空金额"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.contract_amount = None

        result = service.auto_calculate_amount_score(mock_project)

        assert result == Decimal("9.5")  # 0 金额视为小项目


class TestAutoCalculateWorkloadScore:
    """测试 auto_calculate_workload_score 方法"""

    def test_returns_low_score_for_large_workload(self):
        """测试大工作量返回低分"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        # 模拟 10000 小时 = 1250 人天
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10000

        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        result = service.auto_calculate_workload_score(mock_project)

        assert result == Decimal("2")

    def test_returns_high_score_for_small_workload(self):
        """测试小工作量返回高分"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        # 模拟 800 小时 = 100 人天
        mock_db.query.return_value.filter.return_value.scalar.return_value = 800

        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        result = service.auto_calculate_workload_score(mock_project)

        assert result == Decimal("9.5")

    def test_returns_none_when_no_timesheet_data(self):
        """测试无工时数据时返回 None"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        result = service.auto_calculate_workload_score(mock_project)

        assert result is None


class TestGenerateEvaluationCode:
    """测试 generate_evaluation_code 方法"""

    def test_generates_code_with_prefix(self):
        """测试生成带前缀的编号"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        result = service.generate_evaluation_code()

        assert result.startswith("PE")
        assert len(result) == 16  # PE + 14位时间戳


class TestGetLatestEvaluation:
    """测试 get_latest_evaluation 方法"""

    def test_returns_latest_confirmed_evaluation(self):
        """测试返回最新确认的评价"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_evaluation = MagicMock()
        mock_evaluation.status = "CONFIRMED"

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_evaluation
        )

        service = ProjectEvaluationService(mock_db)
        result = service.get_latest_evaluation(project_id=1)

        assert result == mock_evaluation

    def test_returns_none_when_no_evaluation(self):
        """测试无评价时返回 None"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        service = ProjectEvaluationService(mock_db)
        result = service.get_latest_evaluation(project_id=1)

        assert result is None


class TestGetBonusCoefficient:
    """测试 get_bonus_coefficient 方法"""

    def test_returns_default_when_no_evaluation(self):
        """测试无评价时返回默认系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        with patch.object(service, "get_latest_evaluation", return_value=None):
            result = service.get_bonus_coefficient(mock_project)

        assert result == Decimal("1.0")

    def test_returns_s_coefficient_for_s_level(self):
        """测试 S 级项目返回 1.5 倍系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService
        from app.models.enums import ProjectEvaluationLevelEnum

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        mock_evaluation = MagicMock()
        mock_evaluation.evaluation_level = ProjectEvaluationLevelEnum.S

        with patch.object(
            service, "get_latest_evaluation", return_value=mock_evaluation
        ):
            result = service.get_bonus_coefficient(mock_project)

        assert result == Decimal("1.5")

    def test_returns_d_coefficient_for_d_level(self):
        """测试 D 级项目返回 0.9 倍系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService
        from app.models.enums import ProjectEvaluationLevelEnum

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        mock_evaluation = MagicMock()
        mock_evaluation.evaluation_level = ProjectEvaluationLevelEnum.D

        with patch.object(
            service, "get_latest_evaluation", return_value=mock_evaluation
        ):
            result = service.get_bonus_coefficient(mock_project)

        assert result == Decimal("0.9")


class TestGetDifficultyBonusCoefficient:
    """测试 get_difficulty_bonus_coefficient 方法"""

    def test_returns_default_when_no_evaluation(self):
        """测试无评价时返回默认系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        with patch.object(service, "get_latest_evaluation", return_value=None):
            result = service.get_difficulty_bonus_coefficient(mock_project)

        assert result == Decimal("1.0")

    def test_returns_high_coefficient_for_high_difficulty(self):
        """测试高难度返回高系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        mock_evaluation = MagicMock()
        mock_evaluation.difficulty_score = Decimal("2")  # 极高难度

        with patch.object(
            service, "get_latest_evaluation", return_value=mock_evaluation
        ):
            result = service.get_difficulty_bonus_coefficient(mock_project)

        assert result == Decimal("1.5")

    def test_returns_default_for_low_difficulty(self):
        """测试低难度返回默认系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        mock_evaluation = MagicMock()
        mock_evaluation.difficulty_score = Decimal("9")  # 低难度

        with patch.object(
            service, "get_latest_evaluation", return_value=mock_evaluation
        ):
            result = service.get_difficulty_bonus_coefficient(mock_project)

        assert result == Decimal("1.0")


class TestGetNewTechBonusCoefficient:
    """测试 get_new_tech_bonus_coefficient 方法"""

    def test_returns_default_when_no_evaluation(self):
        """测试无评价时返回默认系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        with patch.object(service, "get_latest_evaluation", return_value=None):
            result = service.get_new_tech_bonus_coefficient(mock_project)

        assert result == Decimal("1.0")

    def test_returns_high_coefficient_for_many_new_tech(self):
        """测试大量新技术返回高系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        mock_evaluation = MagicMock()
        mock_evaluation.new_tech_score = Decimal("2")  # 大量新技术

        with patch.object(
            service, "get_latest_evaluation", return_value=mock_evaluation
        ):
            result = service.get_new_tech_bonus_coefficient(mock_project)

        assert result == Decimal("1.4")

    def test_returns_default_for_few_new_tech(self):
        """测试少量新技术返回默认系数"""
        from app.services.project_evaluation_service import ProjectEvaluationService

        mock_db = MagicMock()
        service = ProjectEvaluationService(mock_db)

        mock_project = MagicMock()
        mock_project.id = 1

        mock_evaluation = MagicMock()
        mock_evaluation.new_tech_score = Decimal("9")  # 少量新技术

        with patch.object(
            service, "get_latest_evaluation", return_value=mock_evaluation
        ):
            result = service.get_new_tech_bonus_coefficient(mock_project)

        assert result == Decimal("1.0")
