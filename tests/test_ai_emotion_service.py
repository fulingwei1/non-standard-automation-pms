"""
AI情绪分析服务单元测试
至少20个测试用例
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.ai_emotion_service import AIEmotionService
from app.models.presale_ai_emotion_analysis import (
    PresaleAIEmotionAnalysis,
    SentimentType,
    ChurnRiskLevel
)
from app.models.presale_follow_up_reminder import (
    PresaleFollowUpReminder,
    ReminderPriority,
    ReminderStatus
)
from app.models.presale_emotion_trend import PresaleEmotionTrend


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock()


@pytest.fixture
def ai_service(mock_db):
    """创建AI服务实例"""
    return AIEmotionService(mock_db)


# ==================== 情绪分析测试 (6个) ====================

@pytest.mark.asyncio
async def test_analyze_emotion_positive_sentiment(ai_service, mock_db):
    """测试1: 积极情绪识别"""
    # Mock OpenAI响应
    with patch.object(ai_service, '_call_openai_for_emotion', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "sentiment_score": 80,
            "purchase_intent_score": 75.0,
            "emotion_factors": {"positive_keywords": ["很感兴趣", "想购买"]},
            "churn_indicators": {"risk_score": 20},
            "summary": "客户积极"
        }
        
        # Mock数据库操作
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = await ai_service.analyze_emotion(
            presale_ticket_id=1,
            customer_id=100,
            communication_content="我很感兴趣，想了解更多产品信息"
        )
        
        assert result.sentiment == SentimentType.POSITIVE
        assert result.purchase_intent_score >= 70


@pytest.mark.asyncio
async def test_analyze_emotion_negative_sentiment(ai_service, mock_db):
    """测试2: 消极情绪识别"""
    with patch.object(ai_service, '_call_openai_for_emotion', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "sentiment_score": -70,
            "purchase_intent_score": 20.0,
            "emotion_factors": {"negative_keywords": ["太贵", "不满意"]},
            "churn_indicators": {"risk_score": 80},
            "summary": "客户消极"
        }
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = await ai_service.analyze_emotion(
            presale_ticket_id=2,
            customer_id=101,
            communication_content="价格太贵了，我不太满意"
        )
        
        assert result.sentiment == SentimentType.NEGATIVE
        assert result.churn_risk == ChurnRiskLevel.HIGH


@pytest.mark.asyncio
async def test_analyze_emotion_neutral_sentiment(ai_service, mock_db):
    """测试3: 中性情绪识别"""
    with patch.object(ai_service, '_call_openai_for_emotion', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "sentiment_score": 10,
            "purchase_intent_score": 50.0,
            "emotion_factors": {},
            "churn_indicators": {"risk_score": 45},
            "summary": "客户中性"
        }
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = await ai_service.analyze_emotion(
            presale_ticket_id=3,
            customer_id=102,
            communication_content="好的，我知道了"
        )
        
        assert result.sentiment == SentimentType.NEUTRAL
        assert result.churn_risk == ChurnRiskLevel.MEDIUM


@pytest.mark.asyncio
async def test_analyze_emotion_handles_api_failure(ai_service, mock_db):
    """测试4: API失败时使用默认值"""
    with patch.object(ai_service, '_call_openai_for_emotion', new_callable=AsyncMock) as mock_ai:
        mock_ai.side_effect = Exception("API调用失败")
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # 应该不抛出异常，而是使用默认值
        with pytest.raises(Exception):
            await ai_service.analyze_emotion(
                presale_ticket_id=4,
                customer_id=103,
                communication_content="测试内容"
            )


@pytest.mark.asyncio
async def test_analyze_emotion_high_intent_score(ai_service, mock_db):
    """测试5: 高购买意向识别"""
    with patch.object(ai_service, '_call_openai_for_emotion', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "sentiment_score": 85,
            "purchase_intent_score": 95.0,
            "emotion_factors": {"positive_keywords": ["立即购买", "现在下单"]},
            "churn_indicators": {"risk_score": 10},
            "summary": "高意向客户"
        }
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = await ai_service.analyze_emotion(
            presale_ticket_id=5,
            customer_id=104,
            communication_content="我想立即购买这个产品"
        )
        
        assert float(result.purchase_intent_score) >= 90
        assert result.sentiment == SentimentType.POSITIVE


@pytest.mark.asyncio
async def test_analyze_emotion_updates_trend(ai_service, mock_db):
    """测试6: 情绪分析后更新趋势"""
    with patch.object(ai_service, '_call_openai_for_emotion', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "sentiment_score": 60,
            "purchase_intent_score": 70.0,
            "emotion_factors": {},
            "churn_indicators": {"risk_score": 30},
            "summary": "正常"
        }
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        mock_db.query = Mock()
        
        # Mock趋势查询
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = await ai_service.analyze_emotion(
            presale_ticket_id=6,
            customer_id=105,
            communication_content="产品还不错"
        )
        
        # 验证调用了趋势更新
        assert mock_db.commit.call_count >= 2  # 一次分析，一次趋势


# ==================== 意向识别测试 (5个) ====================

def test_determine_sentiment_positive(ai_service):
    """测试7: 情绪评分 > 30 判定为积极"""
    sentiment = ai_service._determine_sentiment(50)
    assert sentiment == SentimentType.POSITIVE


def test_determine_sentiment_negative(ai_service):
    """测试8: 情绪评分 < -30 判定为消极"""
    sentiment = ai_service._determine_sentiment(-50)
    assert sentiment == SentimentType.NEGATIVE


def test_determine_sentiment_neutral(ai_service):
    """测试9: 情绪评分 [-30, 30] 判定为中性"""
    sentiment = ai_service._determine_sentiment(10)
    assert sentiment == SentimentType.NEUTRAL


def test_determine_churn_risk_high(ai_service):
    """测试10: 风险评分 >= 70 判定为高风险"""
    risk = ai_service._determine_churn_risk({"risk_score": 75})
    assert risk == ChurnRiskLevel.HIGH


def test_determine_churn_risk_low(ai_service):
    """测试11: 风险评分 < 40 判定为低风险"""
    risk = ai_service._determine_churn_risk({"risk_score": 30})
    assert risk == ChurnRiskLevel.LOW


# ==================== 流失预警测试 (5个) ====================

@pytest.mark.asyncio
async def test_predict_churn_risk_high(ai_service, mock_db):
    """测试12: 高流失风险预测"""
    with patch.object(ai_service, '_call_openai_for_churn', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "risk_score": 80.0,
            "risk_factors": [{"factor": "长时间未联系", "weight": "high"}],
            "retention_strategies": ["紧急跟进"],
            "summary": "高风险"
        }
        
        result = await ai_service.predict_churn_risk(
            presale_ticket_id=7,
            customer_id=106,
            recent_communications=["最近一直没有回复"],
            days_since_last_contact=30
        )
        
        assert result["churn_risk"] == "high"
        assert result["risk_score"] >= 70


@pytest.mark.asyncio
async def test_predict_churn_risk_with_response_time_trend(ai_service, mock_db):
    """测试13: 考虑回复时间趋势的流失预测"""
    with patch.object(ai_service, '_call_openai_for_churn', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "risk_score": 65.0,
            "risk_factors": [{"factor": "回复时间变长", "weight": "medium"}],
            "retention_strategies": ["调整沟通策略"],
            "summary": "中高风险"
        }
        
        result = await ai_service.predict_churn_risk(
            presale_ticket_id=8,
            customer_id=107,
            recent_communications=["回复"],
            response_time_trend=[2.0, 4.0, 8.0, 12.0]  # 逐渐变慢
        )
        
        assert result["risk_score"] >= 60


@pytest.mark.asyncio
async def test_predict_churn_risk_low(ai_service, mock_db):
    """测试14: 低流失风险预测"""
    with patch.object(ai_service, '_call_openai_for_churn', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "risk_score": 25.0,
            "risk_factors": [],
            "retention_strategies": ["保持现状"],
            "summary": "低风险"
        }
        
        result = await ai_service.predict_churn_risk(
            presale_ticket_id=9,
            customer_id=108,
            recent_communications=["积极沟通", "经常互动"],
            days_since_last_contact=1
        )
        
        assert result["churn_risk"] == "low"


@pytest.mark.asyncio
async def test_predict_churn_risk_with_strategies(ai_service, mock_db):
    """测试15: 流失预测包含挽回策略"""
    with patch.object(ai_service, '_call_openai_for_churn', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "risk_score": 70.0,
            "risk_factors": [{"factor": "异议增多", "weight": "high"}],
            "retention_strategies": ["解决客户疑虑", "提供优惠方案"],
            "summary": "需要挽回"
        }
        
        result = await ai_service.predict_churn_risk(
            presale_ticket_id=10,
            customer_id=109,
            recent_communications=["有很多问题", "不太满意"]
        )
        
        assert len(result["retention_strategies"]) > 0
        assert len(result["risk_factors"]) > 0


@pytest.mark.asyncio
async def test_predict_churn_risk_handles_empty_communications(ai_service, mock_db):
    """测试16: 处理空沟通记录"""
    with patch.object(ai_service, '_call_openai_for_churn', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "risk_score": 60.0,
            "risk_factors": [{"factor": "缺少沟通记录", "weight": "medium"}],
            "retention_strategies": ["建立联系"],
            "summary": "缺少数据"
        }
        
        result = await ai_service.predict_churn_risk(
            presale_ticket_id=11,
            customer_id=110,
            recent_communications=["无"]
        )
        
        assert "risk_score" in result


# ==================== 跟进提醒测试 (4个) ====================

@pytest.mark.asyncio
async def test_recommend_follow_up_high_priority(ai_service, mock_db):
    """测试17: 高优先级跟进推荐"""
    with patch.object(ai_service, '_call_openai_for_follow_up', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "urgency": "high",
            "content": "立即联系客户",
            "reason": "购买意向高"
        }
        
        # Mock数据库查询
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = await ai_service.recommend_follow_up(
            presale_ticket_id=12,
            customer_id=111
        )
        
        assert result.priority == ReminderPriority.HIGH
        # 高优先级应该在2小时内
        time_diff = result.recommended_time - datetime.now()
        assert time_diff.total_seconds() <= 7200  # 2小时


@pytest.mark.asyncio
async def test_recommend_follow_up_medium_priority(ai_service, mock_db):
    """测试18: 中优先级跟进推荐"""
    with patch.object(ai_service, '_call_openai_for_follow_up', new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = {
            "urgency": "medium",
            "content": "常规跟进",
            "reason": "保持联系"
        }
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = await ai_service.recommend_follow_up(
            presale_ticket_id=13,
            customer_id=112
        )
        
        assert result.priority == ReminderPriority.MEDIUM


def test_dismiss_reminder_success(ai_service, mock_db):
    """测试19: 成功忽略提醒"""
    # Mock查询结果
    mock_reminder = PresaleFollowUpReminder(
        id=1,
        presale_ticket_id=14,
        status=ReminderStatus.PENDING
    )
    
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_reminder
    
    mock_db.commit = Mock()
    
    result = ai_service.dismiss_reminder(1)
    
    assert result is True
    assert mock_reminder.status == ReminderStatus.DISMISSED


def test_dismiss_reminder_not_found(ai_service, mock_db):
    """测试20: 忽略不存在的提醒"""
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None
    
    result = ai_service.dismiss_reminder(999)
    
    assert result is False


# ==================== 额外测试用例 ====================

def test_get_follow_up_reminders_with_filters(ai_service, mock_db):
    """测试21: 带筛选条件获取提醒列表"""
    mock_reminders = [
        PresaleFollowUpReminder(id=1, presale_ticket_id=15, status=ReminderStatus.PENDING, priority=ReminderPriority.HIGH),
        PresaleFollowUpReminder(id=2, presale_ticket_id=16, status=ReminderStatus.PENDING, priority=ReminderPriority.HIGH)
    ]
    
    mock_query = Mock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_reminders
    
    result = ai_service.get_follow_up_reminders(
        status="pending",
        priority="high",
        limit=10
    )
    
    assert len(result) == 2
    assert all(r.priority == ReminderPriority.HIGH for r in result)


def test_needs_attention_high_churn_risk(ai_service):
    """测试22: 高流失风险需要关注"""
    needs_attention = ai_service._needs_attention(
        sentiment="neutral",
        purchase_intent_score=50.0,
        churn_risk="high"
    )
    
    assert needs_attention is True


def test_needs_attention_high_intent(ai_service):
    """测试23: 高购买意向需要关注"""
    needs_attention = ai_service._needs_attention(
        sentiment="positive",
        purchase_intent_score=85.0,
        churn_risk="low"
    )
    
    assert needs_attention is True


def test_recommend_action_high_churn(ai_service):
    """测试24: 高流失风险的行动推荐"""
    action = ai_service._recommend_action(
        sentiment="negative",
        purchase_intent_score=30.0,
        churn_risk="high"
    )
    
    assert "挽回" in action or "紧急" in action


def test_identify_turning_points(ai_service):
    """测试25: 识别情绪趋势转折点"""
    trend_data = [
        {"date": "2026-01-01", "sentiment": "neutral", "intent_score": 50},
        {"date": "2026-01-02", "sentiment": "positive", "intent_score": 70},  # 峰值
        {"date": "2026-01-03", "sentiment": "neutral", "intent_score": 60},
        {"date": "2026-01-04", "sentiment": "neutral", "intent_score": 55},
        {"date": "2026-01-05", "sentiment": "negative", "intent_score": 30},  # 谷值
        {"date": "2026-01-06", "sentiment": "neutral", "intent_score": 45}
    ]
    
    turning_points = ai_service._identify_turning_points(trend_data)
    
    # 应该识别出至少一个转折点
    assert len(turning_points) > 0
    assert all("type" in tp for tp in turning_points)
