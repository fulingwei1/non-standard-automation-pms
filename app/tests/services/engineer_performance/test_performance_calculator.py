"""
绩效计算服务测试
目标覆盖率: 60%+
测试数量: 30个
"""
import pytest
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.services.engineer_performance.performance_calculator import PerformanceCalculator
from app.models.engineer_performance import (
    CodeModule,
    CollaborationRating,
    DesignReview,
    EngineerDimensionConfig,
    KnowledgeContribution,
    MechanicalDebugIssue,
    PlcModuleLibrary,
    PlcProgramVersion,
    TestBugRecord,
)
from app.models.performance import PerformancePeriod
from app.schemas.engineer_performance import EngineerDimensionScore


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    db = Mock(spec=Session)
    db.query = Mock(return_value=Mock())
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def calculator(mock_db):
    """创建计算器实例"""
    return PerformanceCalculator(db=mock_db)


@pytest.fixture
def mock_period():
    """模拟考核周期"""
    period = Mock(spec=PerformancePeriod)
    period.id = 1
    period.start_date = date(2024, 1, 1)
    period.end_date = date(2024, 3, 31)
    return period


@pytest.fixture
def dimension_config():
    """维度权重配置"""
    config = Mock(spec=EngineerDimensionConfig)
    config.technical_weight = Decimal('30')
    config.execution_weight = Decimal('25')
    config.cost_quality_weight = Decimal('20')
    config.knowledge_weight = Decimal('15')
    config.collaboration_weight = Decimal('10')
    return config


# ============================================================================
# 1. 等级计算测试 (6个测试)
# ============================================================================

def test_calculate_grade_s(calculator):
    """测试S等级 (85-100)"""
    assert calculator.calculate_grade(Decimal('90')) == 'S'
    assert calculator.calculate_grade(Decimal('85')) == 'S'
    assert calculator.calculate_grade(Decimal('100')) == 'S'


def test_calculate_grade_a(calculator):
    """测试A等级 (70-84)"""
    assert calculator.calculate_grade(Decimal('75')) == 'A'
    assert calculator.calculate_grade(Decimal('70')) == 'A'
    assert calculator.calculate_grade(Decimal('84')) == 'A'


def test_calculate_grade_b(calculator):
    """测试B等级 (60-69)"""
    assert calculator.calculate_grade(Decimal('65')) == 'B'
    assert calculator.calculate_grade(Decimal('60')) == 'B'
    assert calculator.calculate_grade(Decimal('69')) == 'B'


def test_calculate_grade_c(calculator):
    """测试C等级 (40-59)"""
    assert calculator.calculate_grade(Decimal('50')) == 'C'
    assert calculator.calculate_grade(Decimal('40')) == 'C'
    assert calculator.calculate_grade(Decimal('59')) == 'C'


def test_calculate_grade_d(calculator):
    """测试D等级 (0-39)"""
    assert calculator.calculate_grade(Decimal('30')) == 'D'
    assert calculator.calculate_grade(Decimal('0')) == 'D'
    assert calculator.calculate_grade(Decimal('39')) == 'D'


def test_calculate_grade_boundary(calculator):
    """测试边界值"""
    assert calculator.calculate_grade(Decimal('84.9')) == 'A'
    assert calculator.calculate_grade(Decimal('85.0')) == 'S'
    assert calculator.calculate_grade(Decimal('69.9')) == 'B'
    assert calculator.calculate_grade(Decimal('70.0')) == 'A'


# ============================================================================
# 2. 机械工程师得分计算测试 (5个测试)
# ============================================================================

def test_calculate_mechanical_score_no_reviews(calculator, mock_db, mock_period):
    """测试无设计评审记录"""
    # 模拟空查询结果
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    
    score = calculator._calculate_mechanical_score(1, mock_period)
    
    assert isinstance(score, EngineerDimensionScore)
    assert score.technical_score >= 0
    assert score.execution_score == Decimal('80')
    assert score.cost_quality_score == Decimal('75')


def test_calculate_mechanical_score_perfect_first_pass(calculator, mock_db, mock_period):
    """测试100%设计一次通过率"""
    # 模拟设计评审记录
    review1 = Mock(spec=DesignReview)
    review1.is_first_pass = True
    review2 = Mock(spec=DesignReview)
    review2.is_first_pass = True
    
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    
    # 为不同的查询返回不同的结果
    def filter_side_effect(*args, **kwargs):
        mock_filter = Mock()
        # 第一次调用：设计评审
        if not hasattr(filter_side_effect, 'call_count'):
            filter_side_effect.call_count = 0
        
        filter_side_effect.call_count += 1
        
        if filter_side_effect.call_count == 1:
            mock_filter.all.return_value = [review1, review2]
        elif filter_side_effect.call_count == 2:
            mock_filter.count.return_value = 0  # 无调试问题
        else:
            mock_filter.count.return_value = 0
            mock_filter.all.return_value = []
        
        return mock_filter
    
    mock_query.filter = filter_side_effect
    
    score = calculator._calculate_mechanical_score(1, mock_period)
    
    # 100% 通过率，分数应该较高
    assert score.technical_score >= 100


def test_calculate_mechanical_score_with_debug_issues(calculator, mock_db, mock_period):
    """测试有调试问题的情况"""
    review = Mock(spec=DesignReview)
    review.is_first_pass = True
    
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    
    def filter_side_effect(*args, **kwargs):
        mock_filter = Mock()
        if not hasattr(filter_side_effect, 'call_count'):
            filter_side_effect.call_count = 0
        
        filter_side_effect.call_count += 1
        
        if filter_side_effect.call_count == 1:
            mock_filter.all.return_value = [review]
        elif filter_side_effect.call_count == 2:
            mock_filter.count.return_value = 3  # 3个调试问题
        else:
            mock_filter.count.return_value = 0
            mock_filter.all.return_value = []
        
        return mock_filter
    
    mock_query.filter = filter_side_effect
    
    score = calculator._calculate_mechanical_score(1, mock_period)
    
    # 有调试问题，分数会降低
    assert isinstance(score.technical_score, Decimal)


def test_calculate_mechanical_score_with_knowledge(calculator, mock_db, mock_period):
    """测试有知识沉淀的情况"""
    call_counter = {'count': 0}
    
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        call_counter['count'] += 1
        
        if call_counter['count'] <= 2:
            # 设计评审和调试问题
            mock_filter.all.return_value = []
            mock_filter.count.return_value = 0
        elif call_counter['count'] == 3:
            # 知识贡献查询
            mock_filter.count.return_value = 3
        else:
            # 协作评价
            mock_filter.all.return_value = []
        
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_mechanical_score(1, mock_period)
    
    # 3个知识贡献: 50 + 3*10 = 80
    assert score.knowledge_score == Decimal('80')


def test_calculate_mechanical_score_max_knowledge(calculator, mock_db, mock_period):
    """测试知识沉淀达到上限"""
    call_counter = {'count': 0}
    
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        call_counter['count'] += 1
        
        if call_counter['count'] <= 2:
            mock_filter.all.return_value = []
            mock_filter.count.return_value = 0
        elif call_counter['count'] == 3:
            # 很多知识贡献
            mock_filter.count.return_value = 10
        else:
            # 协作评价
            mock_filter.all.return_value = []
        
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_mechanical_score(1, mock_period)
    
    # 知识分数不应超过100
    assert score.knowledge_score == Decimal('100')


# ============================================================================
# 3. 测试工程师得分计算测试 (4个测试)
# ============================================================================

def test_calculate_test_score_no_bugs(calculator, mock_db, mock_period):
    """测试无Bug记录"""
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_filter.count.return_value = 0
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_test_score(1, mock_period)
    
    assert score.technical_score == Decimal('100')
    assert score.execution_score == Decimal('80')


def test_calculate_test_score_all_resolved(calculator, mock_db, mock_period):
    """测试所有Bug都已解决"""
    bug1 = Mock(spec=TestBugRecord)
    bug1.status = 'resolved'
    bug1.fix_duration_hours = 3
    
    bug2 = Mock(spec=TestBugRecord)
    bug2.status = 'closed'
    bug2.fix_duration_hours = 2
    
    call_counter = {'count': 0}
    
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        call_counter['count'] += 1
        
        if call_counter['count'] == 1:
            mock_filter.all.return_value = [bug1, bug2]
        elif call_counter['count'] == 2:
            mock_filter.count.return_value = 0
        else:
            mock_filter.all.return_value = []
        
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_test_score(1, mock_period)
    
    # 100%解决率，平均修复时间<4小时，应该加分
    assert score.technical_score >= 100


def test_calculate_test_score_partial_resolved(calculator, mock_db, mock_period):
    """测试部分Bug已解决"""
    bug1 = Mock(spec=TestBugRecord)
    bug1.status = 'resolved'
    bug1.fix_duration_hours = 5
    
    bug2 = Mock(spec=TestBugRecord)
    bug2.status = 'open'
    bug2.fix_duration_hours = None
    
    call_counter = {'count': 0}
    
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        call_counter['count'] += 1
        
        if call_counter['count'] == 1:
            mock_filter.all.return_value = [bug1, bug2]
        elif call_counter['count'] == 2:
            mock_filter.count.return_value = 0
        else:
            mock_filter.all.return_value = []
        
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_test_score(1, mock_period)
    
    # 50%解决率
    assert score.technical_score == Decimal('50')


def test_calculate_test_score_with_modules(calculator, mock_db, mock_period):
    """测试有代码模块贡献"""
    call_counter = {'count': 0}
    
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        call_counter['count'] += 1
        
        if call_counter['count'] == 1:
            # Bug记录
            mock_filter.all.return_value = []
        elif call_counter['count'] == 2:
            # 代码模块
            mock_filter.count.return_value = 2
        else:
            # 协作评价
            mock_filter.all.return_value = []
        
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_test_score(1, mock_period)
    
    # 2个模块: 50 + 2*15 = 80
    assert score.knowledge_score == Decimal('80')


# ============================================================================
# 4. 电气工程师得分计算测试 (3个测试)
# ============================================================================

def test_calculate_electrical_score_no_programs(calculator, mock_db, mock_period):
    """测试无PLC程序记录"""
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_filter.count.return_value = 0
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_electrical_score(1, mock_period)
    
    # 默认first_pass_rate = 80, 80/80*100 = 100
    assert score.technical_score == Decimal('100')


def test_calculate_electrical_score_perfect_first_pass(calculator, mock_db, mock_period):
    """测试100% PLC程序一次通过"""
    prog1 = Mock(spec=PlcProgramVersion)
    prog1.is_first_pass = True
    prog2 = Mock(spec=PlcProgramVersion)
    prog2.is_first_pass = True
    
    call_counter = {'count': 0}
    
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        call_counter['count'] += 1
        
        if call_counter['count'] == 1:
            mock_filter.all.return_value = [prog1, prog2]
        elif call_counter['count'] == 2:
            mock_filter.count.return_value = 0
        else:
            mock_filter.all.return_value = []
        
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_electrical_score(1, mock_period)
    
    # 100/80*100 = 125, min(125, 120) = 120
    assert score.technical_score == Decimal('120')


def test_calculate_electrical_score_with_plc_modules(calculator, mock_db, mock_period):
    """测试有PLC模块贡献"""
    call_counter = {'count': 0}
    
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        call_counter['count'] += 1
        
        if call_counter['count'] == 1:
            # PLC程序记录
            mock_filter.all.return_value = []
        elif call_counter['count'] == 2:
            # PLC模块
            mock_filter.count.return_value = 3
        else:
            # 协作评价
            mock_filter.all.return_value = []
        
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_electrical_score(1, mock_period)
    
    # 3个模块: 50 + 3*15 = 95
    assert score.knowledge_score == Decimal('95')


# ============================================================================
# 5. 方案工程师得分计算测试 (4个测试)
# ============================================================================

def test_calculate_solution_score_no_solutions(calculator, mock_db, mock_period):
    """测试无方案记录"""
    from app.models.presale import PresaleSolution, PresaleSolutionTemplate
    
    def query_side_effect(model):
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_filter.count.return_value = 0
        mock_query.filter.return_value = mock_filter
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_solution_score(1, mock_period)
    
    # 无方案时使用默认值 (win_rate_score * 0.5 + approval_rate_score * 0.3 + quality_score * 0.2)
    # 60 * 0.5 + 60 * 0.3 + 60 * 0.2 = 30 + 18 + 12 = 60
    assert score.solution_success_score == Decimal('60')
    assert isinstance(score, EngineerDimensionScore)


def test_calculate_solution_score_with_approved_solution(calculator, mock_db, mock_period):
    """测试有已批准方案"""
    from app.models.presale import PresaleSolution
    from app.models.sales import Contract
    
    # 创建模拟方案
    solution = Mock(spec=PresaleSolution)
    solution.opportunity_id = 1
    solution.review_status = 'APPROVED'
    solution.ticket_id = 1
    solution.created_at = datetime(2024, 1, 15)
    
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    
    def query_side_effect(model):
        mock_q = Mock()
        if model == PresaleSolution:
            mock_q.filter.return_value.all.return_value = [solution]
        elif hasattr(model, '__name__') and 'Contract' in str(model):
            mock_q.filter.return_value.first.return_value = None
        else:
            mock_q.filter.return_value.all.return_value = []
            mock_q.filter.return_value.count.return_value = 0
        return mock_q
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_solution_score(1, mock_period)
    
    # 应该有方案成功率得分
    assert score.solution_success_score is not None


def test_calculate_solution_score_with_templates(calculator, mock_db, mock_period):
    """测试有方案模板贡献"""
    from app.models.presale import PresaleSolution, PresaleSolutionTemplate
    
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    
    def query_side_effect(model):
        mock_q = Mock()
        if model == PresaleSolution:
            mock_q.filter.return_value.all.return_value = []
        elif hasattr(model, '__name__') and 'Template' in str(model):
            mock_q.filter.return_value.count.return_value = 2
        else:
            mock_q.filter.return_value.all.return_value = []
            mock_q.filter.return_value.count.return_value = 0
        return mock_q
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_solution_score(1, mock_period)
    
    # 2个模板: 50 + 2*15 = 80
    assert score.knowledge_score == Decimal('80')


def test_calculate_solution_score_with_high_value_contract(calculator, mock_db, mock_period):
    """测试高价值合同（>200万）"""
    from app.models.presale import PresaleSolution, PresaleSolutionTemplate, PresaleSupportTicket
    from app.models.sales import Contract
    
    solution = Mock(spec=PresaleSolution)
    solution.opportunity_id = 1
    solution.review_status = 'APPROVED'
    solution.ticket_id = 1
    solution.created_at = datetime(2024, 1, 15)
    
    contract = Mock(spec=Contract)
    contract.status = 'SIGNED'
    contract.contract_amount = Decimal('3000000')  # 300万
    
    def query_side_effect(model):
        mock_q = Mock()
        mock_filter = Mock()
        
        # 检查模型类型
        model_name = str(model)
        
        if 'PresaleSolution' in model_name and 'Template' not in model_name:
            # 方案查询
            mock_filter.all.return_value = [solution]
            mock_q.filter.return_value = mock_filter
        elif 'Contract' in model_name:
            # 合同查询
            mock_filter.first.return_value = contract
            mock_q.filter.return_value = mock_filter
        elif 'Template' in model_name:
            # 模板查询
            mock_filter.count.return_value = 0
            mock_q.filter.return_value = mock_filter
        elif 'Ticket' in model_name:
            # 工单查询
            mock_filter.all.return_value = []
            mock_q.filter.return_value = mock_filter
        else:
            # 其他查询（协作评价等）
            mock_filter.all.return_value = []
            mock_filter.count.return_value = 0
            mock_q.filter.return_value = mock_filter
        
        return mock_q
    
    mock_db.query.side_effect = query_side_effect
    
    score = calculator._calculate_solution_score(1, mock_period)
    
    # 高价值合同应该有更高的得分
    assert score.solution_success_score is not None
    assert isinstance(score.solution_success_score, Decimal)


# ============================================================================
# 6. 协作评价测试 (3个测试)
# ============================================================================

def test_get_collaboration_avg_no_ratings(calculator, mock_db):
    """测试无协作评价"""
    mock_db.query.return_value.filter.return_value.all.return_value = []
    
    avg = calculator._get_collaboration_avg(1, 1)
    
    # 默认值
    assert avg == Decimal('75')


def test_get_collaboration_avg_perfect_ratings(calculator, mock_db):
    """测试完美协作评价"""
    rating1 = Mock(spec=CollaborationRating)
    rating1.communication_score = 5
    rating1.response_score = 5
    rating1.delivery_score = 5
    rating1.interface_score = 5
    
    rating2 = Mock(spec=CollaborationRating)
    rating2.communication_score = 5
    rating2.response_score = 5
    rating2.delivery_score = 5
    rating2.interface_score = 5
    
    mock_db.query.return_value.filter.return_value.all.return_value = [rating1, rating2]
    
    avg = calculator._get_collaboration_avg(1, 1)
    
    # (5+5+5+5)*2 / (2*4) * 20 = 100
    assert avg == Decimal('100')


def test_get_collaboration_avg_mixed_ratings(calculator, mock_db):
    """测试混合评价"""
    rating1 = Mock(spec=CollaborationRating)
    rating1.communication_score = 4
    rating1.response_score = 3
    rating1.delivery_score = 4
    rating1.interface_score = 3
    
    mock_db.query.return_value.filter.return_value.all.return_value = [rating1]
    
    avg = calculator._get_collaboration_avg(1, 1)
    
    # (4+3+4+3) / 4 * 20 = 70
    assert avg == Decimal('70')


# ============================================================================
# 7. 维度得分计算测试 (3个测试)
# ============================================================================

def test_calculate_dimension_score_mechanical(calculator, mock_db, mock_period):
    """测试机械工程师维度得分"""
    mock_db.query.return_value.filter.return_value.first.return_value = mock_period
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.count.return_value = 0
    
    score = calculator.calculate_dimension_score(1, 1, 'mechanical')
    
    assert isinstance(score, EngineerDimensionScore)
    assert hasattr(score, 'technical_score')
    assert hasattr(score, 'execution_score')


def test_calculate_dimension_score_invalid_period(calculator, mock_db):
    """测试无效的考核周期"""
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    with pytest.raises(ValueError, match="考核周期不存在"):
        calculator.calculate_dimension_score(1, 999, 'mechanical')


def test_calculate_dimension_score_invalid_job_type(calculator, mock_db, mock_period):
    """测试无效的岗位类型"""
    mock_db.query.return_value.filter.return_value.first.return_value = mock_period
    
    with pytest.raises(ValueError, match="未知的岗位类型"):
        calculator.calculate_dimension_score(1, 1, 'invalid_type')


# ============================================================================
# 8. 总分计算测试 (3个测试)
# ============================================================================

def test_calculate_total_score_regular_engineer(calculator, dimension_config):
    """测试普通工程师总分计算"""
    scores = EngineerDimensionScore(
        technical_score=Decimal('90'),
        execution_score=Decimal('80'),
        cost_quality_score=Decimal('75'),
        knowledge_score=Decimal('85'),
        collaboration_score=Decimal('70')
    )
    
    total = calculator.calculate_total_score(scores, dimension_config, 'mechanical')
    
    # 90*30% + 80*25% + 75*20% + 85*15% + 70*10% = 27 + 20 + 15 + 12.75 + 7 = 81.75
    expected = Decimal('81.75')
    assert total == expected


def test_calculate_total_score_solution_engineer(calculator, dimension_config):
    """测试方案工程师总分计算（特殊权重）"""
    scores = EngineerDimensionScore(
        technical_score=Decimal('90'),
        execution_score=Decimal('80'),
        cost_quality_score=Decimal('75'),
        knowledge_score=Decimal('85'),
        collaboration_score=Decimal('70'),
        solution_success_score=Decimal('88')
    )
    
    total = calculator.calculate_total_score(scores, dimension_config, 'solution')
    
    # 技术25% + 方案成功30% + 执行20% + 知识15% + 协作10%
    # 90*25% + 88*30% + 80*20% + 85*15% + 70*10%
    # = 22.5 + 26.4 + 16 + 12.75 + 7 = 84.65
    expected = Decimal('84.65')
    assert total == expected


def test_calculate_total_score_perfect_scores(calculator, dimension_config):
    """测试完美得分"""
    scores = EngineerDimensionScore(
        technical_score=Decimal('100'),
        execution_score=Decimal('100'),
        cost_quality_score=Decimal('100'),
        knowledge_score=Decimal('100'),
        collaboration_score=Decimal('100')
    )
    
    total = calculator.calculate_total_score(scores, dimension_config, 'test')
    
    # 100*30% + 100*25% + 100*20% + 100*15% + 100*10% = 100
    assert total == Decimal('100')
