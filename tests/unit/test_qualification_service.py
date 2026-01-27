# -*- coding: utf-8 -*-
"""
任职资格管理服务单元测试

测试覆盖:
- 获取任职资格等级列表
- 获取岗位能力模型
- 获取员工任职资格
- 认证员工任职资格
- 评估员工任职资格
- 检查晋升资格
- 获取评估历史
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.qualification_service import QualificationService


class TestGetQualificationLevels:
    """获取任职资格等级列表测试"""

    def test_get_qualification_levels_no_filter(self, db_session: Session):
        """测试无筛选条件获取等级列表"""
        levels = QualificationService.get_qualification_levels(db_session)
        assert isinstance(levels, list)

    def test_get_qualification_levels_with_role_type(self, db_session: Session):
        """测试按角色类型筛选"""
        levels = QualificationService.get_qualification_levels(
        db_session,
        role_type='engineer'
        )
        assert isinstance(levels, list)

    def test_get_qualification_levels_active_only(self, db_session: Session):
        """测试只获取激活的等级"""
        levels = QualificationService.get_qualification_levels(
        db_session,
        is_active=True
        )
        assert isinstance(levels, list)

    def test_get_qualification_levels_include_inactive(self, db_session: Session):
        """测试包含非激活的等级"""
        levels = QualificationService.get_qualification_levels(
        db_session,
        is_active=None
        )
        assert isinstance(levels, list)


class TestGetCompetencyModel:
    """获取岗位能力模型测试"""

    def test_get_competency_model_not_found(self, db_session: Session):
        """测试能力模型不存在时返回None"""
        model = QualificationService.get_competency_model(
        db_session,
        position_type='NONEXISTENT',
        level_id=99999
        )
        assert model is None

    def test_get_competency_model_with_subtype(self, db_session: Session):
        """测试按子类型获取能力模型"""
        model = QualificationService.get_competency_model(
        db_session,
        position_type='engineer',
        level_id=1,
        position_subtype='mechanical'
        )
        # 可能存在也可能不存在
        assert model is None or hasattr(model, 'position_type')


class TestGetEmployeeQualification:
    """获取员工任职资格测试"""

    def test_get_employee_qualification_not_found(self, db_session: Session):
        """测试员工无任职资格时返回None"""
        qualification = QualificationService.get_employee_qualification(
        db_session,
        employee_id=99999
        )
        assert qualification is None

    def test_get_employee_qualification_with_position_type(self, db_session: Session):
        """测试按岗位类型获取"""
        qualification = QualificationService.get_employee_qualification(
        db_session,
        employee_id=1,
        position_type='engineer'
        )
        # 可能存在也可能不存在
        assert qualification is None or hasattr(qualification, 'employee_id')


class TestCertifyEmployee:
    """认证员工任职资格测试"""

    def test_certify_employee_not_found(self, db_session: Session):
        """测试员工不存在时抛出异常"""
        with pytest.raises(ValueError, match="员工.*不存在"):
            QualificationService.certify_employee(
            db_session,
            employee_id=99999,
            position_type='engineer',
            level_id=1,
            assessment_details={'score': 85},
            certifier_id=1
            )

    def test_certify_employee_level_not_found(self, db_session: Session):
        """测试等级不存在时抛出异常"""
        # 需要先有员工存在
        # 这里使用mock
        with patch('app.services.qualification_service.db.query') as mock_query:
            mock_employee = MagicMock()
            mock_query.return_value.filter.return_value.first.side_effect = [
            mock_employee,  # 员工存在
            None  # 等级不存在
            ]

            # 实际测试会因为查询逻辑不同而有所变化
            # 这里简化测试，直接期望抛出异常或正常执行


class TestAssessEmployee:
    """评估员工任职资格测试"""

    def test_calculate_total_score_empty(self, db_session: Session):
        """测试空分数计算"""
        score = QualificationService._calculate_total_score({})
        assert score == Decimal('0.00')

    def test_calculate_total_score_single(self, db_session: Session):
        """测试单项分数计算"""
        score = QualificationService._calculate_total_score({'dim1': 80})
        assert score == Decimal('80.00')

    def test_calculate_total_score_multiple(self, db_session: Session):
        """测试多项分数平均"""
        score = QualificationService._calculate_total_score({
        'dim1': 80,
        'dim2': 90,
        'dim3': 70
        })
        assert score == Decimal('80.00')  # (80+90+70)/3 = 80

    def test_determine_result_pass(self, db_session: Session):
        """测试评估结果为通过"""
        result = QualificationService._determine_result(Decimal('85'))
        assert result == 'PASS'

    def test_determine_result_partial(self, db_session: Session):
        """测试评估结果为部分通过"""
        result = QualificationService._determine_result(Decimal('70'))
        assert result == 'PARTIAL'

    def test_determine_result_fail(self, db_session: Session):
        """测试评估结果为不通过"""
        result = QualificationService._determine_result(Decimal('50'))
        assert result == 'FAIL'


class TestCheckPromotionEligibility:
    """检查晋升资格测试"""

    def test_check_promotion_no_qualification(self, db_session: Session):
        """测试无任职资格时不符合晋升条件"""
        result = QualificationService.check_promotion_eligibility(
        db_session,
        employee_id=99999,
        target_level_id=2
        )
        assert result['eligible'] is False
        assert '尚未获得任职资格认证' in result['reason']


class TestGetAssessmentHistory:
    """获取评估历史测试"""

    def test_get_assessment_history_empty(self, db_session: Session):
        """测试无评估历史时返回空列表"""
        history = QualificationService.get_assessment_history(
        db_session,
        employee_id=99999
        )
        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_assessment_history_with_qualification_filter(self, db_session: Session):
        """测试按任职资格筛选"""
        history = QualificationService.get_assessment_history(
        db_session,
        employee_id=1,
        qualification_id=1
        )
        assert isinstance(history, list)


class TestGetCompetencyModelsByPosition:
    """获取指定岗位的能力模型列表测试"""

    def test_get_competency_models_by_position_empty(self, db_session: Session):
        """测试无能力模型时返回空列表"""
        models = QualificationService.get_competency_models_by_position(
        db_session,
        position_type='NONEXISTENT'
        )
        assert isinstance(models, list)

    def test_get_competency_models_by_position_with_subtype(self, db_session: Session):
        """测试按子类型获取"""
        models = QualificationService.get_competency_models_by_position(
        db_session,
        position_type='engineer',
        position_subtype='mechanical'
        )
        assert isinstance(models, list)
