"""
AI情绪分析服务
集成OpenAI GPT-4进行情感分析、意向识别、流失预警
"""
import json
import httpx
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.presale_ai_emotion_analysis import PresaleAIEmotionAnalysis, SentimentType, ChurnRiskLevel
from app.models.presale_follow_up_reminder import PresaleFollowUpReminder, ReminderPriority, ReminderStatus
from app.models.presale_emotion_trend import PresaleEmotionTrend
from app.utils.db_helpers import save_obj


class AIEmotionService:
    """AI情绪分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    async def analyze_emotion(
        self, 
        presale_ticket_id: int,
        customer_id: int,
        communication_content: str
    ) -> PresaleAIEmotionAnalysis:
        """
        分析客户情绪
        """
        # 调用AI进行情绪分析
        analysis_result = await self._call_openai_for_emotion(communication_content)
        
        # 解析AI返回结果
        sentiment = self._determine_sentiment(analysis_result.get('sentiment_score', 0))
        purchase_intent_score = Decimal(str(analysis_result.get('purchase_intent_score', 50.0)))
        churn_risk = self._determine_churn_risk(analysis_result.get('churn_indicators', {}))
        
        # 保存分析记录
        emotion_analysis = PresaleAIEmotionAnalysis(
            presale_ticket_id=presale_ticket_id,
            customer_id=customer_id,
            communication_content=communication_content,
            sentiment=sentiment,
            purchase_intent_score=purchase_intent_score,
            churn_risk=churn_risk,
            emotion_factors=analysis_result.get('emotion_factors', {}),
            analysis_result=json.dumps(analysis_result, ensure_ascii=False)
        )
        
        save_obj(self.db, emotion_analysis)
        
        # 更新情绪趋势
        await self._update_emotion_trend(presale_ticket_id, customer_id, sentiment, purchase_intent_score)
        
        return emotion_analysis
    
    async def predict_churn_risk(
        self,
        presale_ticket_id: int,
        customer_id: int,
        recent_communications: List[str],
        days_since_last_contact: Optional[int] = None,
        response_time_trend: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        预测客户流失风险
        """
        # 构建分析上下文
        context = {
            "communications": recent_communications,
            "days_since_last_contact": days_since_last_contact,
            "response_time_trend": response_time_trend
        }
        
        # 调用AI分析流失风险
        churn_analysis = await self._call_openai_for_churn(context)
        
        # 解析风险等级
        risk_score = churn_analysis.get('risk_score', 50.0)
        churn_risk = self._determine_churn_risk({'risk_score': risk_score})
        
        return {
            "presale_ticket_id": presale_ticket_id,
            "customer_id": customer_id,
            "churn_risk": churn_risk.value,
            "risk_score": risk_score,
            "risk_factors": churn_analysis.get('risk_factors', []),
            "retention_strategies": churn_analysis.get('retention_strategies', []),
            "analysis_summary": churn_analysis.get('summary', '')
        }
    
    async def recommend_follow_up(
        self,
        presale_ticket_id: int,
        customer_id: int,
        latest_emotion_analysis_id: Optional[int] = None
    ) -> PresaleFollowUpReminder:
        """
        推荐跟进时机
        """
        # 获取最新情绪分析
        if latest_emotion_analysis_id:
            emotion_analysis = self.db.query(PresaleAIEmotionAnalysis).filter(
                PresaleAIEmotionAnalysis.id == latest_emotion_analysis_id
            ).first()
        else:
            emotion_analysis = self.db.query(PresaleAIEmotionAnalysis).filter(
                PresaleAIEmotionAnalysis.presale_ticket_id == presale_ticket_id
            ).order_by(desc(PresaleAIEmotionAnalysis.created_at)).first()
        
        # 调用AI推荐跟进策略
        if emotion_analysis:
            follow_up_recommendation = await self._call_openai_for_follow_up({
                "sentiment": emotion_analysis.sentiment.value if emotion_analysis.sentiment else "neutral",
                "purchase_intent_score": float(emotion_analysis.purchase_intent_score) if emotion_analysis.purchase_intent_score else 50.0,
                "churn_risk": emotion_analysis.churn_risk.value if emotion_analysis.churn_risk else "medium",
                "emotion_factors": emotion_analysis.emotion_factors or {}
            })
        else:
            follow_up_recommendation = await self._call_openai_for_follow_up({
                "sentiment": "neutral",
                "purchase_intent_score": 50.0,
                "churn_risk": "medium",
                "emotion_factors": {}
            })
        
        # 计算推荐时间
        recommended_time = self._calculate_recommended_time(
            follow_up_recommendation.get('urgency', 'medium')
        )
        
        # 确定优先级
        priority = self._determine_priority(follow_up_recommendation.get('urgency', 'medium'))
        
        # 保存提醒
        reminder = PresaleFollowUpReminder(
            presale_ticket_id=presale_ticket_id,
            recommended_time=recommended_time,
            priority=priority,
            follow_up_content=follow_up_recommendation.get('content', ''),
            reason=follow_up_recommendation.get('reason', ''),
            status=ReminderStatus.PENDING
        )
        
        save_obj(self.db, reminder)
        
        return reminder
    
    def get_emotion_trend(self, presale_ticket_id: int) -> Optional[PresaleEmotionTrend]:
        """
        获取情绪趋势
        """
        return self.db.query(PresaleEmotionTrend).filter(
            PresaleEmotionTrend.presale_ticket_id == presale_ticket_id
        ).first()
    
    def get_follow_up_reminders(
        self, 
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50
    ) -> List[PresaleFollowUpReminder]:
        """
        获取跟进提醒列表
        """
        query = self.db.query(PresaleFollowUpReminder)
        
        if status:
            query = query.filter(PresaleFollowUpReminder.status == status)
        if priority:
            query = query.filter(PresaleFollowUpReminder.priority == priority)
        
        return query.order_by(desc(PresaleFollowUpReminder.recommended_time)).limit(limit).all()
    
    def dismiss_reminder(self, reminder_id: int) -> bool:
        """
        忽略提醒
        """
        reminder = self.db.query(PresaleFollowUpReminder).filter(
            PresaleFollowUpReminder.id == reminder_id
        ).first()
        
        if reminder:
            reminder.status = ReminderStatus.DISMISSED
            self.db.commit()
            return True
        return False
    
    async def batch_analyze_customers(
        self,
        customer_ids: List[int],
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """
        批量分析客户
        """
        summaries = []
        success_count = 0
        failed_count = 0
        
        for customer_id in customer_ids:
            try:
                # 获取该客户最新的情绪分析
                latest_analysis = self.db.query(PresaleAIEmotionAnalysis).filter(
                    PresaleAIEmotionAnalysis.customer_id == customer_id
                ).order_by(desc(PresaleAIEmotionAnalysis.created_at)).first()
                
                if latest_analysis:
                    sentiment = latest_analysis.sentiment.value if latest_analysis.sentiment else None
                    purchase_intent_score = float(latest_analysis.purchase_intent_score) if latest_analysis.purchase_intent_score else None
                    churn_risk = latest_analysis.churn_risk.value if latest_analysis.churn_risk else None
                else:
                    sentiment = None
                    purchase_intent_score = None
                    churn_risk = None
                
                # 判断是否需要关注
                needs_attention = self._needs_attention(sentiment, purchase_intent_score, churn_risk)
                
                # 推荐行动
                recommended_action = self._recommend_action(sentiment, purchase_intent_score, churn_risk)
                
                summaries.append({
                    "customer_id": customer_id,
                    "latest_sentiment": sentiment,
                    "purchase_intent_score": purchase_intent_score,
                    "churn_risk": churn_risk,
                    "needs_attention": needs_attention,
                    "recommended_action": recommended_action
                })
                success_count += 1
            except Exception as e:
                print(f"分析客户 {customer_id} 失败: {str(e)}")
                failed_count += 1
        
        return {
            "total_analyzed": len(customer_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "summaries": summaries,
            "analysis_timestamp": datetime.now()
        }
    
    # ==================== 私有方法 ====================
    
    async def _call_openai_for_emotion(self, content: str) -> Dict[str, Any]:
        """
        调用OpenAI进行情绪分析
        """
        prompt = f"""
请分析以下客户沟通内容的情绪和购买意向：

客户沟通内容:
{content}

请以JSON格式返回分析结果，包含以下字段：
1. sentiment_score: 情绪评分(-100到100，负数表示消极，正数表示积极)
2. purchase_intent_score: 购买意向评分(0-100)
3. emotion_factors: 影响情绪的关键因素(对象格式)
4. churn_indicators: 流失风险指标(对象格式，包含risk_score)
5. summary: 简要分析总结

示例格式:
{{
    "sentiment_score": 75,
    "purchase_intent_score": 85,
    "emotion_factors": {{"positive_keywords": ["感兴趣", "想了解"], "concerns": []}},
    "churn_indicators": {{"risk_score": 20, "signals": []}},
    "summary": "客户表现出较高兴趣..."
}}
"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个专业的客户情绪分析专家。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content_text = result['choices'][0]['message']['content']
                    
                    # 尝试解析JSON
                    try:
                        # 去除可能的markdown代码块标记
                        if content_text.strip().startswith('```'):
                            content_text = content_text.strip().split('```')[1]
                            if content_text.startswith('json'):
                                content_text = content_text[4:]
                        
                        return json.loads(content_text.strip())
                    except json.JSONDecodeError:
                        # 如果解析失败，返回默认值
                        return self._get_default_emotion_result()
                else:
                    return self._get_default_emotion_result()
        except Exception as e:
            print(f"调用OpenAI失败: {str(e)}")
            return self._get_default_emotion_result()
    
    async def _call_openai_for_churn(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用OpenAI分析流失风险
        """
        prompt = f"""
请分析以下客户情况的流失风险：

客户沟通历史: {json.dumps(context.get('communications', []), ensure_ascii=False)}
距离上次联系天数: {context.get('days_since_last_contact', '未知')}
回复时间趋势: {context.get('response_time_trend', '未知')}

请以JSON格式返回分析结果，包含：
1. risk_score: 流失风险评分(0-100)
2. risk_factors: 风险因素列表
3. retention_strategies: 挽回策略建议列表
4. summary: 分析摘要

示例:
{{
    "risk_score": 65,
    "risk_factors": [{{"factor": "长时间未联系", "weight": "high"}}],
    "retention_strategies": ["及时跟进", "提供优惠"],
    "summary": "客户流失风险较高..."
}}
"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个客户流失预警专家。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content_text = result['choices'][0]['message']['content']
                    
                    try:
                        if content_text.strip().startswith('```'):
                            content_text = content_text.strip().split('```')[1]
                            if content_text.startswith('json'):
                                content_text = content_text[4:]
                        
                        return json.loads(content_text.strip())
                    except json.JSONDecodeError:
                        return self._get_default_churn_result()
                else:
                    return self._get_default_churn_result()
        except Exception as e:
            print(f"调用OpenAI失败: {str(e)}")
            return self._get_default_churn_result()
    
    async def _call_openai_for_follow_up(self, emotion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用OpenAI推荐跟进策略
        """
        prompt = f"""
基于以下客户情绪分析数据，推荐最佳跟进时机和内容：

客户情绪: {emotion_data.get('sentiment', 'neutral')}
购买意向评分: {emotion_data.get('purchase_intent_score', 50)}
流失风险: {emotion_data.get('churn_risk', 'medium')}
情绪因素: {json.dumps(emotion_data.get('emotion_factors', {}), ensure_ascii=False)}

请以JSON格式返回：
1. urgency: 紧急程度(high/medium/low)
2. content: 建议的跟进内容
3. reason: 为什么现在是最佳时机

示例:
{{
    "urgency": "high",
    "content": "您好，关于您之前咨询的产品...",
    "reason": "客户购买意向高，需要及时跟进促成交易"
}}
"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "你是一个销售跟进策略专家。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.5
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content_text = result['choices'][0]['message']['content']
                    
                    try:
                        if content_text.strip().startswith('```'):
                            content_text = content_text.strip().split('```')[1]
                            if content_text.startswith('json'):
                                content_text = content_text[4:]
                        
                        return json.loads(content_text.strip())
                    except json.JSONDecodeError:
                        return self._get_default_follow_up_result()
                else:
                    return self._get_default_follow_up_result()
        except Exception as e:
            print(f"调用OpenAI失败: {str(e)}")
            return self._get_default_follow_up_result()
    
    def _determine_sentiment(self, sentiment_score: float) -> SentimentType:
        """根据评分确定情绪类型"""
        if sentiment_score > 30:
            return SentimentType.POSITIVE
        elif sentiment_score < -30:
            return SentimentType.NEGATIVE
        else:
            return SentimentType.NEUTRAL
    
    def _determine_churn_risk(self, churn_indicators: Dict[str, Any]) -> ChurnRiskLevel:
        """确定流失风险等级"""
        risk_score = churn_indicators.get('risk_score', 50)
        
        if risk_score >= 70:
            return ChurnRiskLevel.HIGH
        elif risk_score >= 40:
            return ChurnRiskLevel.MEDIUM
        else:
            return ChurnRiskLevel.LOW
    
    def _determine_priority(self, urgency: str) -> ReminderPriority:
        """确定优先级"""
        if urgency == "high":
            return ReminderPriority.HIGH
        elif urgency == "low":
            return ReminderPriority.LOW
        else:
            return ReminderPriority.MEDIUM
    
    def _calculate_recommended_time(self, urgency: str) -> datetime:
        """计算推荐跟进时间"""
        now = datetime.now()
        
        if urgency == "high":
            # 高优先级：2小时内
            return now + timedelta(hours=2)
        elif urgency == "low":
            # 低优先级：3天后
            return now + timedelta(days=3)
        else:
            # 中优先级：1天后
            return now + timedelta(days=1)
    
    async def _update_emotion_trend(
        self, 
        presale_ticket_id: int,
        customer_id: int,
        sentiment: SentimentType,
        purchase_intent_score: Decimal
    ):
        """更新情绪趋势"""
        trend = self.db.query(PresaleEmotionTrend).filter(
            PresaleEmotionTrend.presale_ticket_id == presale_ticket_id
        ).first()
        
        new_data_point = {
            "date": datetime.now().isoformat(),
            "sentiment": sentiment.value,
            "intent_score": float(purchase_intent_score)
        }
        
        if trend:
            # 更新已有趋势
            trend_data = trend.trend_data or []
            trend_data.append(new_data_point)
            trend.trend_data = trend_data
            
            # 识别关键转折点
            trend.key_turning_points = self._identify_turning_points(trend_data)
        else:
            # 创建新趋势
            trend = PresaleEmotionTrend(
                presale_ticket_id=presale_ticket_id,
                customer_id=customer_id,
                trend_data=[new_data_point],
                key_turning_points=[]
            )
            self.db.add(trend)
        
        self.db.commit()
    
    def _identify_turning_points(self, trend_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """识别关键转折点"""
        turning_points = []
        
        if len(trend_data) < 3:
            return turning_points
        
        # 简单的转折点识别：情绪或意向发生显著变化
        for i in range(1, len(trend_data) - 1):
            prev_score = trend_data[i - 1].get('intent_score', 50)
            curr_score = trend_data[i].get('intent_score', 50)
            next_score = trend_data[i + 1].get('intent_score', 50)
            
            # 如果当前点是局部极值
            if (curr_score > prev_score and curr_score > next_score) or \
               (curr_score < prev_score and curr_score < next_score):
                turning_points.append({
                    "date": trend_data[i]['date'],
                    "type": "peak" if curr_score > prev_score else "valley",
                    "sentiment": trend_data[i]['sentiment'],
                    "intent_score": curr_score
                })
        
        return turning_points[-5:]  # 只保留最近5个转折点
    
    def _needs_attention(
        self,
        sentiment: Optional[str],
        purchase_intent_score: Optional[float],
        churn_risk: Optional[str]
    ) -> bool:
        """判断是否需要关注"""
        if churn_risk == "high":
            return True
        if sentiment == "negative":
            return True
        if purchase_intent_score and purchase_intent_score >= 80:
            return True
        return False
    
    def _recommend_action(
        self,
        sentiment: Optional[str],
        purchase_intent_score: Optional[float],
        churn_risk: Optional[str]
    ) -> str:
        """推荐行动"""
        if churn_risk == "high":
            return "紧急跟进，制定挽回策略"
        if purchase_intent_score and purchase_intent_score >= 80:
            return "高意向客户，建议立即联系促成交易"
        if sentiment == "negative":
            return "客户情绪消极，需要了解问题并解决"
        if sentiment == "positive" and purchase_intent_score and purchase_intent_score >= 60:
            return "保持跟进节奏，提供更多产品信息"
        return "正常跟进，保持联系"
    
    def _get_default_emotion_result(self) -> Dict[str, Any]:
        """获取默认情绪分析结果"""
        return {
            "sentiment_score": 0,
            "purchase_intent_score": 50.0,
            "emotion_factors": {},
            "churn_indicators": {"risk_score": 50},
            "summary": "分析失败，使用默认值"
        }
    
    def _get_default_churn_result(self) -> Dict[str, Any]:
        """获取默认流失分析结果"""
        return {
            "risk_score": 50.0,
            "risk_factors": [],
            "retention_strategies": ["建议及时跟进"],
            "summary": "分析失败，使用默认值"
        }
    
    def _get_default_follow_up_result(self) -> Dict[str, Any]:
        """获取默认跟进建议"""
        return {
            "urgency": "medium",
            "content": "建议与客户保持联系，了解需求",
            "reason": "常规跟进"
        }
