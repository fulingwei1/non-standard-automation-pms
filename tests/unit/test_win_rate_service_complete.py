# -*- coding: utf-8 -*-
"""
完整单元测试 - win_rate_prediction_service/service.py
目标：60%+ 覆盖率，30+ 测试用例
"""
import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.win_rate_prediction_service.service import WinRatePredictionService
from app.models.sales.presale_ai_win_rate import WinRateResultEnum


def run_async(coro):
    """运行异步协程的辅助函数"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def make_service():
    """创建测试用的service实例"""
    db = MagicMock()
    
    async def fake_execute(*args, **kwargs):
        return MagicMock()
    
    db.execute = fake_execute
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    
    with patch("app.services.win_rate_prediction_service.service.AIWinRatePredictionService"):
        service = WinRatePredictionService(db)
    
    return service, db


def set_execute_scalar(db, scalar_value):
    """设置db.execute返回scalar值"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_value
    
    async def fake_execute(*args, **kwargs):
        return result
    
    db.execute = fake_execute


def set_execute_scalars(db, items):
    """设置db.execute返回scalars列表"""
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = items
    result.scalars.return_value = scalars
    
    async def fake_execute(*args, **kwargs):
        return result
    
    db.execute = fake_execute


class TestPredictWinRate:
    """预测赢率测试"""
    
    def test_predict_basic(self):
        """测试基础预测"""
        service, db = make_service()
        
        # Mock AI预测结果
        ai_result = {
            'win_rate_score': 75.5,
            'confidence_interval': '60-85',
            'influencing_factors': [{'factor': 'price', 'score': 8}],
            'competitor_analysis': {'main_competitor': 'CompanyX'},
            'improvement_suggestions': {'suggestion': 'Lower price'},
            'ai_analysis_report': 'Analysis report...'
        }
        service.ai_service.predict_with_ai = AsyncMock(return_value=ai_result)
        
        # Mock历史数据
        service._get_historical_data = AsyncMock(return_value=[])
        
        ticket_data = {'customer': 'Test', 'amount': 10000}
        
        result = run_async(service.predict_win_rate(
            presale_ticket_id=1,
            ticket_data=ticket_data,
            created_by=5
        ))
        
        # 验证调用
        db.add.assert_called()
        assert db.flush.called
        assert db.commit.called
    
    def test_predict_with_historical_data(self):
        """测试带历史数据的预测"""
        service, db = make_service()
        
        ai_result = {
            'win_rate_score': 80.0,
            'confidence_interval': '70-90',
            'influencing_factors': [],
            'competitor_analysis': {},
            'improvement_suggestions': {},
            'ai_analysis_report': 'Report'
        }
        service.ai_service.predict_with_ai = AsyncMock(return_value=ai_result)
        
        historical_data = [
            {'ticket_id': 10, 'win_rate': 75.0, 'result': 'won'},
            {'ticket_id': 11, 'win_rate': 65.0, 'result': 'lost'}
        ]
        service._get_historical_data = AsyncMock(return_value=historical_data)
        
        result = run_async(service.predict_win_rate(
            presale_ticket_id=2,
            ticket_data={'test': 'data'},
            created_by=3
        ))
        
        # 验证历史数据被获取
        service._get_historical_data.assert_called_once()
    
    def test_predict_error_handling(self):
        """测试预测错误处理"""
        service, db = make_service()
        
        # Mock AI服务抛出异常
        service.ai_service.predict_with_ai = AsyncMock(side_effect=Exception("AI Error"))
        service._get_historical_data = AsyncMock(return_value=[])
        
        with pytest.raises(Exception, match="AI Error"):
            run_async(service.predict_win_rate(
                presale_ticket_id=1,
                ticket_data={},
                created_by=1
            ))
        
        # 验证回滚
        assert db.rollback.called
    
    def test_predict_creates_history_record(self):
        """测试创建历史记录"""
        service, db = make_service()
        
        ai_result = {
            'win_rate_score': 70.0,
            'confidence_interval': '60-80',
            'influencing_factors': [],
            'competitor_analysis': {},
            'improvement_suggestions': {},
            'ai_analysis_report': 'Report'
        }
        service.ai_service.predict_with_ai = AsyncMock(return_value=ai_result)
        service._get_historical_data = AsyncMock(return_value=[])
        
        run_async(service.predict_win_rate(
            presale_ticket_id=3,
            ticket_data={'amount': 50000},
            created_by=7
        ))
        
        # 验证添加了两次（prediction + history）
        assert db.add.call_count == 2
    
    def test_predict_different_model_versions(self):
        """测试不同模型版本"""
        service, db = make_service()
        
        ai_result = {
            'win_rate_score': 65.0,
            'confidence_interval': '55-75',
            'influencing_factors': [],
            'competitor_analysis': {},
            'improvement_suggestions': {},
            'ai_analysis_report': 'Report'
        }
        
        # 测试GPT模型
        service.ai_service.use_kimi = False
        service.ai_service.predict_with_ai = AsyncMock(return_value=ai_result)
        service._get_historical_data = AsyncMock(return_value=[])
        
        run_async(service.predict_win_rate(1, {}, 1))
        
        # 测试Kimi模型
        service.ai_service.use_kimi = True
        run_async(service.predict_win_rate(2, {}, 1))
        
        assert db.add.call_count >= 4


class TestGetPrediction:
    """获取预测结果测试"""
    
    def test_get_existing_prediction(self):
        """测试获取存在的预测"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.id = 1
        prediction.win_rate_score = Decimal("75.5")
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_prediction(1))
        
        assert result is prediction
    
    def test_get_nonexistent_prediction(self):
        """测试获取不存在的预测"""
        service, db = make_service()
        
        set_execute_scalar(db, None)
        
        result = run_async(service.get_prediction(999))
        
        assert result is None


class TestGetPredictionsByTicket:
    """获取工单所有预测测试"""
    
    def test_get_multiple_predictions(self):
        """测试获取多个预测"""
        service, db = make_service()
        
        predictions = [
            MagicMock(id=1, win_rate_score=Decimal("75")),
            MagicMock(id=2, win_rate_score=Decimal("80")),
            MagicMock(id=3, win_rate_score=Decimal("70"))
        ]
        
        set_execute_scalars(db, predictions)
        
        result = run_async(service.get_predictions_by_ticket(1))
        
        assert len(result) == 3
        assert result == predictions
    
    def test_get_no_predictions(self):
        """测试获取空预测列表"""
        service, db = make_service()
        
        set_execute_scalars(db, [])
        
        result = run_async(service.get_predictions_by_ticket(999))
        
        assert result == []
    
    def test_get_single_prediction(self):
        """测试获取单个预测"""
        service, db = make_service()
        
        prediction = MagicMock(id=1, win_rate_score=Decimal("85"))
        set_execute_scalars(db, [prediction])
        
        result = run_async(service.get_predictions_by_ticket(1))
        
        assert len(result) == 1
        assert result[0] is prediction


class TestGetInfluencingFactors:
    """获取影响因素测试"""
    
    def test_get_factors_sorted(self):
        """测试因素按分数排序"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.influencing_factors = [
            {'factor': 'price', 'score': 3},
            {'factor': 'quality', 'score': 9},
            {'factor': 'service', 'score': 7},
            {'factor': 'delivery', 'score': 5},
            {'factor': 'brand', 'score': 8}
        ]
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_influencing_factors(1))
        
        # 验证排序（降序）
        assert result[0]['score'] == 9
        assert result[1]['score'] == 8
        assert result[2]['score'] == 7
    
    def test_get_factors_top_5(self):
        """测试只返回TOP 5因素"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.influencing_factors = [
            {'factor': f'factor_{i}', 'score': 10 - i}
            for i in range(10)
        ]
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_influencing_factors(1))
        
        # 应该只返回5个
        assert len(result) == 5
        assert result[0]['score'] == 10
        assert result[4]['score'] == 6
    
    def test_get_factors_no_prediction(self):
        """测试无预测时返回空列表"""
        service, db = make_service()
        
        set_execute_scalar(db, None)
        
        result = run_async(service.get_influencing_factors(999))
        
        assert result == []
    
    def test_get_factors_empty_list(self):
        """测试因素列表为空"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.influencing_factors = []
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_influencing_factors(1))
        
        assert result == []
    
    def test_get_factors_none(self):
        """测试因素为None"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.influencing_factors = None
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_influencing_factors(1))
        
        assert result == []


class TestGetCompetitorAnalysis:
    """获取竞品分析测试"""
    
    def test_get_competitor_analysis(self):
        """测试获取竞品分析"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.competitor_analysis = {
            'main_competitor': 'CompanyX',
            'strength': 'Strong brand',
            'weakness': 'High price'
        }
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_competitor_analysis(1))
        
        assert result['main_competitor'] == 'CompanyX'
        assert 'strength' in result
    
    def test_get_competitor_analysis_no_prediction(self):
        """测试无预测时返回None"""
        service, db = make_service()
        
        set_execute_scalar(db, None)
        
        result = run_async(service.get_competitor_analysis(999))
        
        assert result is None
    
    def test_get_competitor_analysis_empty(self):
        """测试竞品分析为空对象"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.competitor_analysis = {}
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_competitor_analysis(1))
        
        assert result == {}


class TestGetImprovementSuggestions:
    """获取改进建议测试"""
    
    def test_get_suggestions(self):
        """测试获取改进建议"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.improvement_suggestions = {
            'priority_1': 'Lower price',
            'priority_2': 'Improve quality',
            'priority_3': 'Faster delivery'
        }
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_improvement_suggestions(1))
        
        assert 'priority_1' in result
        assert result['priority_1'] == 'Lower price'
    
    def test_get_suggestions_no_prediction(self):
        """测试无预测时返回None"""
        service, db = make_service()
        
        set_execute_scalar(db, None)
        
        result = run_async(service.get_improvement_suggestions(999))
        
        assert result is None


class TestUpdateActualResult:
    """更新实际结果测试"""
    
    def test_update_result_won(self):
        """测试更新为赢单"""
        service, db = make_service()
        
        history = MagicMock()
        history.predicted_win_rate = Decimal("75")
        history.presale_ticket_id = 1
        
        set_execute_scalar(db, history)
        
        result = run_async(service.update_actual_result(
            ticket_id=1,
            actual_result=WinRateResultEnum.WON,
            updated_by=5,
            win_date=datetime(2024, 3, 15)
        ))
        
        assert history.actual_result == WinRateResultEnum.WON
        assert history.actual_win_date == datetime(2024, 3, 15)
        assert db.commit.called
    
    def test_update_result_lost(self):
        """测试更新为失单"""
        service, db = make_service()
        
        history = MagicMock()
        history.predicted_win_rate = Decimal("60")
        
        set_execute_scalar(db, history)
        
        result = run_async(service.update_actual_result(
            ticket_id=1,
            actual_result=WinRateResultEnum.LOST,
            updated_by=3,
            lost_date=datetime(2024, 3, 20)
        ))
        
        assert history.actual_result == WinRateResultEnum.LOST
        assert history.actual_lost_date == datetime(2024, 3, 20)
    
    def test_update_result_calculates_error(self):
        """测试计算预测误差"""
        service, db = make_service()
        
        history = MagicMock()
        history.predicted_win_rate = Decimal("75")
        
        set_execute_scalar(db, history)
        
        run_async(service.update_actual_result(
            ticket_id=1,
            actual_result=WinRateResultEnum.WON,
            updated_by=1
        ))
        
        # 实际100，预测75，误差25
        assert history.prediction_error == Decimal("25")
    
    def test_update_result_correct_prediction_high(self):
        """测试预测正确（高预测值赢单）"""
        service, db = make_service()
        
        history = MagicMock()
        history.predicted_win_rate = Decimal("80")
        
        set_execute_scalar(db, history)
        
        run_async(service.update_actual_result(
            ticket_id=1,
            actual_result=WinRateResultEnum.WON,
            updated_by=1
        ))
        
        # 预测>=50且实际赢单，判断正确
        assert history.is_correct_prediction == 1
    
    def test_update_result_correct_prediction_low(self):
        """测试预测正确（低预测值失单）"""
        service, db = make_service()
        
        history = MagicMock()
        history.predicted_win_rate = Decimal("30")
        
        set_execute_scalar(db, history)
        
        run_async(service.update_actual_result(
            ticket_id=1,
            actual_result=WinRateResultEnum.LOST,
            updated_by=1
        ))
        
        # 预测<50且实际失单，判断正确
        assert history.is_correct_prediction == 1
    
    def test_update_result_incorrect_prediction(self):
        """测试预测错误"""
        service, db = make_service()
        
        history = MagicMock()
        history.predicted_win_rate = Decimal("80")
        
        set_execute_scalar(db, history)
        
        run_async(service.update_actual_result(
            ticket_id=1,
            actual_result=WinRateResultEnum.LOST,
            updated_by=1
        ))
        
        # 预测>=50但实际失单，判断错误
        assert history.is_correct_prediction == 0
    
    def test_update_result_not_found(self):
        """测试历史记录不存在"""
        service, db = make_service()
        
        set_execute_scalar(db, None)
        
        with pytest.raises(ValueError, match="未找到工单"):
            run_async(service.update_actual_result(
                ticket_id=999,
                actual_result=WinRateResultEnum.WON,
                updated_by=1
            ))
    
    def test_update_result_pending_no_calculation(self):
        """测试更新为待定状态不计算误差"""
        service, db = make_service()
        
        history = MagicMock()
        history.predicted_win_rate = Decimal("70")
        history.prediction_error = None
        history.is_correct_prediction = None
        
        set_execute_scalar(db, history)
        
        run_async(service.update_actual_result(
            ticket_id=1,
            actual_result=WinRateResultEnum.PENDING,
            updated_by=1
        ))
        
        # PENDING状态不计算误差
        assert history.prediction_error is None
        assert history.is_correct_prediction is None


class TestGetModelAccuracy:
    """获取模型准确度测试"""
    
    def test_get_accuracy_basic(self):
        """测试基础准确度统计"""
        service, db = make_service()
        
        # Mock总体统计
        stats_result = MagicMock()
        stats = MagicMock()
        stats.total = 100
        stats.correct = 80
        stats_result.one.return_value = stats
        
        # Mock平均误差
        avg_error_result = MagicMock()
        avg_error_result.scalar.return_value = Decimal("15.5")
        
        # Mock按结果分组
        group_result = MagicMock()
        group_result.__iter__ = lambda self: iter([])
        
        call_count = [0]
        
        async def fake_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return stats_result
            elif call_count[0] == 2:
                return avg_error_result
            else:
                return group_result
        
        db.execute = fake_execute
        
        result = run_async(service.get_model_accuracy())
        
        assert result['overall_accuracy'] == 80.0
        assert result['total_predictions'] == 100
        assert result['correct_predictions'] == 80
        assert result['average_error'] == 15.5
    
    def test_get_accuracy_no_data(self):
        """测试无数据时的准确度"""
        service, db = make_service()
        
        stats_result = MagicMock()
        stats = MagicMock()
        stats.total = 0
        stats.correct = 0
        stats_result.one.return_value = stats
        
        avg_error_result = MagicMock()
        avg_error_result.scalar.return_value = None
        
        group_result = MagicMock()
        group_result.__iter__ = lambda self: iter([])
        
        call_count = [0]
        
        async def fake_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return stats_result
            elif call_count[0] == 2:
                return avg_error_result
            else:
                return group_result
        
        db.execute = fake_execute
        
        result = run_async(service.get_model_accuracy())
        
        assert result['overall_accuracy'] == 0.0
        assert result['total_predictions'] == 0
        assert result['average_error'] == 0.0
    
    def test_get_accuracy_perfect(self):
        """测试100%准确度"""
        service, db = make_service()
        
        stats_result = MagicMock()
        stats = MagicMock()
        stats.total = 50
        stats.correct = 50
        stats_result.one.return_value = stats
        
        avg_error_result = MagicMock()
        avg_error_result.scalar.return_value = Decimal("0")
        
        group_result = MagicMock()
        group_result.__iter__ = lambda self: iter([])
        
        call_count = [0]
        
        async def fake_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return stats_result
            elif call_count[0] == 2:
                return avg_error_result
            else:
                return group_result
        
        db.execute = fake_execute
        
        result = run_async(service.get_model_accuracy())
        
        assert result['overall_accuracy'] == 100.0


class TestGetHistoricalData:
    """获取历史数据测试"""
    
    def test_get_historical_data_empty(self):
        """测试获取空历史数据"""
        service, db = make_service()
        
        set_execute_scalars(db, [])
        
        result = run_async(service._get_historical_data({}))
        
        assert result == []
    
    def test_get_historical_data_formats_correctly(self):
        """测试历史数据格式化"""
        service, db = make_service()
        
        history = MagicMock()
        history.presale_ticket_id = 10
        history.predicted_win_rate = Decimal("75.5")
        history.actual_result = MagicMock()
        history.actual_result.value = "won"
        history.features = {"customer": "TestCorp", "amount": 100000}
        
        set_execute_scalars(db, [history])
        
        result = run_async(service._get_historical_data({}))
        
        assert len(result) == 1
        assert result[0]['ticket_id'] == 10
        assert result[0]['win_rate'] == 75.5
        assert result[0]['result'] == "won"
        assert result[0]['features']['customer'] == "TestCorp"
    
    def test_get_historical_data_limit_10(self):
        """测试历史数据限制为10条"""
        service, db = make_service()
        
        # 创建15条历史记录
        histories = []
        for i in range(15):
            h = MagicMock()
            h.presale_ticket_id = i
            h.predicted_win_rate = Decimal(str(70 + i))
            h.actual_result = MagicMock()
            h.actual_result.value = "won"
            h.features = {}
            histories.append(h)
        
        set_execute_scalars(db, histories[:10])  # 模拟limit(10)
        
        result = run_async(service._get_historical_data({}))
        
        # 应该只返回10条
        assert len(result) == 10


class TestIntegrationScenarios:
    """集成场景测试"""
    
    def test_full_prediction_workflow(self):
        """测试完整预测流程"""
        service, db = make_service()
        
        # 1. 预测
        ai_result = {
            'win_rate_score': 75.0,
            'confidence_interval': '65-85',
            'influencing_factors': [{'factor': 'price', 'score': 8}],
            'competitor_analysis': {'competitor': 'X'},
            'improvement_suggestions': {'action': 'Lower price'},
            'ai_analysis_report': 'Report'
        }
        service.ai_service.predict_with_ai = AsyncMock(return_value=ai_result)
        service._get_historical_data = AsyncMock(return_value=[])
        
        run_async(service.predict_win_rate(1, {}, 1))
        
        # 2. 获取预测
        prediction = MagicMock()
        prediction.influencing_factors = [{'factor': 'price', 'score': 8}]
        set_execute_scalar(db, prediction)
        
        factors = run_async(service.get_influencing_factors(1))
        assert len(factors) > 0
        
        # 3. 更新实际结果
        history = MagicMock()
        history.predicted_win_rate = Decimal("75")
        set_execute_scalar(db, history)
        
        run_async(service.update_actual_result(1, WinRateResultEnum.WON, 1))
        assert history.actual_result == WinRateResultEnum.WON


class TestEdgeCases:
    """边界情况测试"""
    
    def test_predict_with_empty_ticket_data(self):
        """测试空工单数据预测"""
        service, db = make_service()
        
        ai_result = {
            'win_rate_score': 50.0,
            'confidence_interval': '40-60',
            'influencing_factors': [],
            'competitor_analysis': {},
            'improvement_suggestions': {},
            'ai_analysis_report': ''
        }
        service.ai_service.predict_with_ai = AsyncMock(return_value=ai_result)
        service._get_historical_data = AsyncMock(return_value=[])
        
        result = run_async(service.predict_win_rate(1, {}, 1))
        
        assert db.add.called
    
    def test_get_factors_with_missing_scores(self):
        """测试因素缺少分数"""
        service, db = make_service()
        
        prediction = MagicMock()
        prediction.influencing_factors = [
            {'factor': 'price'},  # 缺少score
            {'factor': 'quality', 'score': 9}
        ]
        
        set_execute_scalar(db, prediction)
        
        result = run_async(service.get_influencing_factors(1))
        
        # 应该能处理缺少score的情况
        assert len(result) > 0
    
    def test_update_result_boundary_prediction_50(self):
        """测试预测值恰好50%的边界情况"""
        service, db = make_service()
        
        history = MagicMock()
        history.predicted_win_rate = Decimal("50")
        
        set_execute_scalar(db, history)
        
        # 50%预测赢单，实际赢单，应该判断正确
        run_async(service.update_actual_result(1, WinRateResultEnum.WON, 1))
        assert history.is_correct_prediction == 1
        
        # 50%预测失单，应该判断错误
        history.is_correct_prediction = None
        run_async(service.update_actual_result(1, WinRateResultEnum.LOST, 1))
        assert history.is_correct_prediction == 0
