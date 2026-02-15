# -*- coding: utf-8 -*-
"""
AI赢率预测服务 - 主服务层
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.sales.presale_ai_win_rate import (
    PresaleAIWinRate,
    PresaleWinRateHistory,
    WinRateResultEnum,
)
from .ai_service import AIWinRatePredictionService

logger = logging.getLogger(__name__)


class WinRatePredictionService:
    """完整的赢率预测服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIWinRatePredictionService()
    
    async def predict_win_rate(
        self,
        presale_ticket_id: int,
        ticket_data: Dict[str, Any],
        created_by: int
    ) -> PresaleAIWinRate:
        """
        预测赢率
        
        Args:
            presale_ticket_id: 售前工单ID
            ticket_data: 工单相关数据
            created_by: 创建人ID
            
        Returns:
            PresaleAIWinRate对象
        """
        try:
            # 1. 获取历史数据作为参考
            historical_data = await self._get_historical_data(ticket_data)
            
            # 2. 使用AI进行预测
            ai_result = await self.ai_service.predict_with_ai(ticket_data, historical_data)
            
            # 3. 创建预测记录
            prediction = PresaleAIWinRate(
                presale_ticket_id=presale_ticket_id,
                win_rate_score=Decimal(str(ai_result['win_rate_score'])),
                confidence_interval=ai_result['confidence_interval'],
                influencing_factors=ai_result['influencing_factors'],
                competitor_analysis=ai_result['competitor_analysis'],
                improvement_suggestions=ai_result['improvement_suggestions'],
                ai_analysis_report=ai_result['ai_analysis_report'],
                model_version="gpt-4" if not self.ai_service.use_kimi else "kimi-v1",
                predicted_at=datetime.now(),
                created_by=created_by
            )
            
            self.db.add(prediction)
            await self.db.flush()
            
            # 4. 创建历史记录用于后续模型训练
            history = PresaleWinRateHistory(
                presale_ticket_id=presale_ticket_id,
                predicted_win_rate=Decimal(str(ai_result['win_rate_score'])),
                prediction_id=prediction.id,
                actual_result=WinRateResultEnum.PENDING,
                features=ticket_data
            )
            
            self.db.add(history)
            await self.db.commit()
            await self.db.refresh(prediction)
            
            logger.info(f"赢率预测完成: ticket_id={presale_ticket_id}, score={ai_result['win_rate_score']}")
            
            return prediction
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"赢率预测失败: {e}")
            raise
    
    async def get_prediction(self, prediction_id: int) -> Optional[PresaleAIWinRate]:
        """获取预测结果"""
        
        result = await self.db.execute(
            select(PresaleAIWinRate).where(PresaleAIWinRate.id == prediction_id)
        )
        return result.scalar_one_or_none()
    
    async def get_predictions_by_ticket(self, presale_ticket_id: int) -> List[PresaleAIWinRate]:
        """获取工单的所有预测记录"""
        
        result = await self.db.execute(
            select(PresaleAIWinRate)
            .where(PresaleAIWinRate.presale_ticket_id == presale_ticket_id)
            .order_by(PresaleAIWinRate.predicted_at.desc())
        )
        return result.scalars().all()
    
    async def get_influencing_factors(self, ticket_id: int) -> List[Dict[str, Any]]:
        """获取影响因素分析"""
        
        result = await self.db.execute(
            select(PresaleAIWinRate)
            .where(PresaleAIWinRate.presale_ticket_id == ticket_id)
            .order_by(PresaleAIWinRate.predicted_at.desc())
            .limit(1)
        )
        
        prediction = result.scalar_one_or_none()
        if not prediction:
            return []
        
        factors = prediction.influencing_factors or []
        
        # 按影响程度排序，返回TOP 5
        sorted_factors = sorted(
            factors,
            key=lambda x: x.get('score', 0),
            reverse=True
        )
        
        return sorted_factors[:5]
    
    async def get_competitor_analysis(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """获取竞品分析"""
        
        result = await self.db.execute(
            select(PresaleAIWinRate)
            .where(PresaleAIWinRate.presale_ticket_id == ticket_id)
            .order_by(PresaleAIWinRate.predicted_at.desc())
            .limit(1)
        )
        
        prediction = result.scalar_one_or_none()
        if not prediction:
            return None
        
        return prediction.competitor_analysis
    
    async def get_improvement_suggestions(self, ticket_id: int) -> Optional[Dict[str, Any]]:
        """获取改进建议"""
        
        result = await self.db.execute(
            select(PresaleAIWinRate)
            .where(PresaleAIWinRate.presale_ticket_id == ticket_id)
            .order_by(PresaleAIWinRate.predicted_at.desc())
            .limit(1)
        )
        
        prediction = result.scalar_one_or_none()
        if not prediction:
            return None
        
        return prediction.improvement_suggestions
    
    async def update_actual_result(
        self,
        ticket_id: int,
        actual_result: WinRateResultEnum,
        updated_by: int,
        win_date: Optional[datetime] = None,
        lost_date: Optional[datetime] = None
    ) -> PresaleWinRateHistory:
        """
        更新实际结果（用于模型学习）
        
        Args:
            ticket_id: 工单ID
            actual_result: 实际结果（won/lost/pending）
            updated_by: 更新人ID
            win_date: 赢单日期（可选）
            lost_date: 失单日期（可选）
            
        Returns:
            更新后的历史记录
        """
        try:
            # 获取最新的历史记录
            result = await self.db.execute(
                select(PresaleWinRateHistory)
                .where(PresaleWinRateHistory.presale_ticket_id == ticket_id)
                .order_by(PresaleWinRateHistory.created_at.desc())
                .limit(1)
            )
            
            history = result.scalar_one_or_none()
            if not history:
                raise ValueError(f"未找到工单 {ticket_id} 的预测记录")
            
            # 更新结果
            history.actual_result = actual_result
            history.result_updated_at = datetime.now()
            history.updated_by = updated_by
            
            if win_date:
                history.actual_win_date = win_date
            if lost_date:
                history.actual_lost_date = lost_date
            
            # 计算预测误差和准确性
            if actual_result != WinRateResultEnum.PENDING:
                actual_score = 100.0 if actual_result == WinRateResultEnum.WON else 0.0
                predicted_score = float(history.predicted_win_rate)
                
                history.prediction_error = Decimal(str(abs(actual_score - predicted_score)))
                
                # 判断预测是否正确（阈值为50%）
                if (predicted_score >= 50 and actual_result == WinRateResultEnum.WON) or \
                   (predicted_score < 50 and actual_result == WinRateResultEnum.LOST):
                    history.is_correct_prediction = 1
                else:
                    history.is_correct_prediction = 0
            
            await self.db.commit()
            await self.db.refresh(history)
            
            logger.info(f"实际结果已更新: ticket_id={ticket_id}, result={actual_result}")
            
            return history
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新实际结果失败: {e}")
            raise
    
    async def get_model_accuracy(self) -> Dict[str, Any]:
        """获取模型准确度统计"""
        
        # 1. 总体准确率
        result = await self.db.execute(
            select(
                func.count(PresaleWinRateHistory.id).label('total'),
                func.sum(PresaleWinRateHistory.is_correct_prediction).label('correct')
            )
            .where(PresaleWinRateHistory.actual_result != WinRateResultEnum.PENDING)
        )
        
        stats = result.one()
        total = stats.total or 0
        correct = stats.correct or 0
        
        accuracy = (correct / total * 100) if total > 0 else 0.0
        
        # 2. 平均预测误差
        result = await self.db.execute(
            select(func.avg(PresaleWinRateHistory.prediction_error))
            .where(PresaleWinRateHistory.actual_result != WinRateResultEnum.PENDING)
        )
        
        avg_error = result.scalar() or 0.0
        
        # 3. 按结果分组统计
        result = await self.db.execute(
            select(
                PresaleWinRateHistory.actual_result,
                func.count(PresaleWinRateHistory.id).label('count'),
                func.avg(PresaleWinRateHistory.predicted_win_rate).label('avg_predicted'),
                func.avg(PresaleWinRateHistory.prediction_error).label('avg_error')
            )
            .where(PresaleWinRateHistory.actual_result != WinRateResultEnum.PENDING)
            .group_by(PresaleWinRateHistory.actual_result)
        )
        
        by_result = {}
        for row in result:
            by_result[row.actual_result.value] = {
                'count': row.count,
                'avg_predicted_score': float(row.avg_predicted or 0),
                'avg_error': float(row.avg_error or 0)
            }
        
        return {
            'overall_accuracy': round(accuracy, 2),
            'total_predictions': total,
            'correct_predictions': correct,
            'average_error': round(float(avg_error), 2),
            'by_result': by_result,
            'last_updated': datetime.now().isoformat()
        }
    
    async def _get_historical_data(self, ticket_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取历史相似案例"""
        
        # 这里可以根据相似度算法获取历史数据
        # 简化实现：获取最近10条已完成的预测记录
        result = await self.db.execute(
            select(PresaleWinRateHistory)
            .where(PresaleWinRateHistory.actual_result != WinRateResultEnum.PENDING)
            .order_by(PresaleWinRateHistory.created_at.desc())
            .limit(10)
        )
        
        histories = result.scalars().all()
        
        return [
            {
                'ticket_id': h.presale_ticket_id,
                'win_rate': float(h.predicted_win_rate),
                'result': h.actual_result.value,
                'features': h.features
            }
            for h in histories
        ]


__all__ = ["WinRatePredictionService"]
