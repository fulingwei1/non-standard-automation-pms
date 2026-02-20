# -*- coding: utf-8 -*-
"""
质量风险管理服务层
处理质量风险检测、测试推荐、质量报告的业务逻辑
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.quality_risk_detection import (
    QualityRiskDetection,
    QualityTestRecommendation,
)
from app.models.timesheet import Timesheet
from app.services.quality_risk_ai import (
    QualityRiskAnalyzer,
    TestRecommendationEngine,
)

logger = logging.getLogger(__name__)


class QualityRiskManagementService:
    """质量风险管理服务"""
    
    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.analyzer = QualityRiskAnalyzer(db)
        self.recommendation_engine = TestRecommendationEngine()
    
    # ==================== 质量风险检测业务逻辑 ====================
    
    def analyze_work_logs(
        self,
        project_id: int,
        start_date: Optional[date],
        end_date: Optional[date],
        module_name: Optional[str],
        user_ids: Optional[List[int]],
        current_user_id: int
    ) -> QualityRiskDetection:
        """
        分析工作日志并检测质量风险
        
        Args:
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期
            module_name: 模块名称
            user_ids: 用户ID列表
            current_user_id: 当前用户ID
            
        Returns:
            QualityRiskDetection: 检测记录
            
        Raises:
            ValueError: 当未找到工作日志时
        """
        # 设置默认日期范围
        end_date = end_date or date.today()
        start_date = start_date or (end_date - timedelta(days=7))
        
        # 查询工作日志
        query = self.db.query(Timesheet).filter(
            Timesheet.project_id == project_id,
            Timesheet.work_date >= start_date,
            Timesheet.work_date <= end_date
        )
        
        if module_name:
            query = query.filter(Timesheet.task_name.contains(module_name))
        
        if user_ids:
            query = query.filter(Timesheet.user_id.in_(user_ids))
        
        work_logs = query.all()
        
        if not work_logs:
            raise ValueError("未找到符合条件的工作日志")
        
        # 转换为字典格式
        log_dicts = [
            {
                'work_date': str(log.work_date),
                'user_name': log.user_name,
                'task_name': log.task_name,
                'work_content': log.work_content or '',
                'work_result': log.work_result or '',
                'hours': float(log.hours) if log.hours else 0
            }
            for log in work_logs
        ]
        
        # AI分析
        analysis_result = self.analyzer.analyze_work_logs(log_dicts)
        
        # 创建检测记录
        detection = QualityRiskDetection(
            project_id=project_id,
            module_name=module_name,
            detection_date=end_date,
            source_type='WORK_LOG',
            risk_signals=analysis_result.get('risk_signals', []),
            risk_keywords=analysis_result.get('risk_keywords', {}),
            abnormal_patterns=analysis_result.get('abnormal_patterns', []),
            risk_level=analysis_result.get('risk_level'),
            risk_score=analysis_result.get('risk_score'),
            risk_category=analysis_result.get('risk_category'),
            predicted_issues=analysis_result.get('predicted_issues', []),
            rework_probability=analysis_result.get('rework_probability'),
            estimated_impact_days=analysis_result.get('estimated_impact_days'),
            ai_analysis=analysis_result.get('ai_analysis'),
            ai_confidence=analysis_result.get('ai_confidence'),
            analysis_model=analysis_result.get('analysis_model'),
            status='DETECTED',
            created_by=current_user_id
        )
        
        self.db.add(detection)
        self.db.commit()
        self.db.refresh(detection)
        
        logger.info(
            f"创建质量风险检测记录 ID={detection.id}, "
            f"项目={project_id}, 风险等级={detection.risk_level}"
        )
        
        return detection
    
    def list_detections(
        self,
        project_id: Optional[int] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[QualityRiskDetection]:
        """
        查询质量风险检测记录列表
        
        Args:
            project_id: 项目ID
            risk_level: 风险等级
            status: 状态
            start_date: 开始日期
            end_date: 结束日期
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            List[QualityRiskDetection]: 检测记录列表
        """
        query = self.db.query(QualityRiskDetection)
        
        if project_id:
            query = query.filter(QualityRiskDetection.project_id == project_id)
        
        if risk_level:
            query = query.filter(QualityRiskDetection.risk_level == risk_level)
        
        if status:
            query = query.filter(QualityRiskDetection.status == status)
        
        if start_date:
            query = query.filter(QualityRiskDetection.detection_date >= start_date)
        
        if end_date:
            query = query.filter(QualityRiskDetection.detection_date <= end_date)
        
        query = query.order_by(desc(QualityRiskDetection.detection_date))
        
        return query.offset(skip).limit(limit).all()
    
    def get_detection(self, detection_id: int) -> Optional[QualityRiskDetection]:
        """
        获取质量风险检测详情
        
        Args:
            detection_id: 检测记录ID
            
        Returns:
            Optional[QualityRiskDetection]: 检测记录，不存在时返回None
        """
        return self.db.query(QualityRiskDetection).filter(
            QualityRiskDetection.id == detection_id
        ).first()
    
    def update_detection(
        self,
        detection_id: int,
        status: Optional[str] = None,
        resolution_note: Optional[str] = None,
        current_user_id: Optional[int] = None
    ) -> Optional[QualityRiskDetection]:
        """
        更新质量风险检测状态
        
        Args:
            detection_id: 检测记录ID
            status: 状态
            resolution_note: 解决备注
            current_user_id: 当前用户ID
            
        Returns:
            Optional[QualityRiskDetection]: 更新后的检测记录，不存在时返回None
        """
        detection = self.get_detection(detection_id)
        
        if not detection:
            return None
        
        # 更新字段
        if status:
            detection.status = status
            if status in ['CONFIRMED', 'FALSE_POSITIVE', 'RESOLVED']:
                detection.confirmed_by = current_user_id
                detection.confirmed_at = datetime.now()
        
        if resolution_note:
            detection.resolution_note = resolution_note
        
        self.db.commit()
        self.db.refresh(detection)
        
        logger.info(f"更新质量风险检测 ID={detection_id}, 状态={detection.status}")
        
        return detection
    
    # ==================== 测试推荐业务逻辑 ====================
    
    def generate_test_recommendation(
        self,
        detection_id: int,
        current_user_id: int
    ) -> Optional[QualityTestRecommendation]:
        """
        基于质量风险检测结果，生成测试推荐
        
        Args:
            detection_id: 质量风险检测ID
            current_user_id: 当前用户ID
            
        Returns:
            Optional[QualityTestRecommendation]: 测试推荐记录，检测记录不存在时返回None
        """
        # 查询检测记录
        detection = self.get_detection(detection_id)
        
        if not detection:
            return None
        
        # 构建风险分析结果
        risk_analysis = {
            'risk_level': detection.risk_level,
            'risk_score': float(detection.risk_score),
            'risk_category': detection.risk_category,
            'risk_signals': detection.risk_signals or [],
            'risk_keywords': detection.risk_keywords or {},
            'abnormal_patterns': detection.abnormal_patterns or [],
            'predicted_issues': detection.predicted_issues or [],
            'rework_probability': float(detection.rework_probability) if detection.rework_probability else 0,
            'estimated_impact_days': detection.estimated_impact_days or 0
        }
        
        # 项目信息（简化版）
        project_info = {
            'project_id': detection.project_id
        }
        
        # 生成推荐
        recommendation_data = self.recommendation_engine.generate_recommendations(
            risk_analysis, project_info
        )
        
        # 创建推荐记录
        recommendation = QualityTestRecommendation(
            project_id=detection.project_id,
            detection_id=detection.id,
            recommendation_date=date.today(),
            focus_areas=recommendation_data['focus_areas'],
            priority_modules=recommendation_data.get('priority_modules'),
            risk_modules=recommendation_data.get('risk_modules'),
            test_types=recommendation_data.get('test_types'),
            test_scenarios=recommendation_data.get('test_scenarios'),
            test_coverage_target=recommendation_data.get('test_coverage_target'),
            recommended_testers=recommendation_data.get('recommended_testers'),
            recommended_days=recommendation_data.get('recommended_days'),
            priority_level=recommendation_data['priority_level'],
            ai_reasoning=recommendation_data.get('ai_reasoning'),
            risk_summary=recommendation_data.get('risk_summary'),
            status='PENDING',
            created_by=current_user_id
        )
        
        self.db.add(recommendation)
        self.db.commit()
        self.db.refresh(recommendation)
        
        logger.info(
            f"生成测试推荐 ID={recommendation.id}, "
            f"检测={detection_id}, 优先级={recommendation.priority_level}"
        )
        
        return recommendation
    
    def list_recommendations(
        self,
        project_id: Optional[int] = None,
        priority_level: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[QualityTestRecommendation]:
        """
        查询测试推荐列表
        
        Args:
            project_id: 项目ID
            priority_level: 优先级
            status: 状态
            skip: 跳过记录数
            limit: 返回记录数
            
        Returns:
            List[QualityTestRecommendation]: 推荐列表
        """
        query = self.db.query(QualityTestRecommendation)
        
        if project_id:
            query = query.filter(QualityTestRecommendation.project_id == project_id)
        
        if priority_level:
            query = query.filter(QualityTestRecommendation.priority_level == priority_level)
        
        if status:
            query = query.filter(QualityTestRecommendation.status == status)
        
        query = query.order_by(desc(QualityTestRecommendation.recommendation_date))
        
        return query.offset(skip).limit(limit).all()
    
    def update_recommendation(
        self,
        recommendation_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[QualityTestRecommendation]:
        """
        更新测试推荐
        
        Args:
            recommendation_id: 推荐ID
            update_data: 更新数据字典
            
        Returns:
            Optional[QualityTestRecommendation]: 更新后的推荐记录，不存在时返回None
        """
        recommendation = self.db.query(QualityTestRecommendation).filter(
            QualityTestRecommendation.id == recommendation_id
        ).first()
        
        if not recommendation:
            return None
        
        # 更新字段
        for field, value in update_data.items():
            if hasattr(recommendation, field):
                setattr(recommendation, field, value)
        
        self.db.commit()
        self.db.refresh(recommendation)
        
        logger.info(f"更新测试推荐 ID={recommendation_id}, 状态={recommendation.status}")
        
        return recommendation
    
    # ==================== 质量报告业务逻辑 ====================
    
    def generate_quality_report(
        self,
        project_id: int,
        start_date: date,
        end_date: date,
        include_recommendations: bool = False
    ) -> Dict[str, Any]:
        """
        生成项目质量分析报告
        
        Args:
            project_id: 项目ID
            start_date: 开始日期
            end_date: 结束日期
            include_recommendations: 是否包含推荐
            
        Returns:
            Dict[str, Any]: 质量报告数据
            
        Raises:
            ValueError: 当没有检测数据时
        """
        # 查询检测记录
        detections = self.db.query(QualityRiskDetection).filter(
            QualityRiskDetection.project_id == project_id,
            QualityRiskDetection.detection_date >= start_date,
            QualityRiskDetection.detection_date <= end_date
        ).all()
        
        if not detections:
            raise ValueError("指定时间段内没有质量风险检测数据")
        
        # 统计风险分布
        risk_distribution = {}
        for detection in detections:
            level = detection.risk_level
            risk_distribution[level] = risk_distribution.get(level, 0) + 1
        
        # 确定总体风险等级
        overall_risk = self._calculate_overall_risk(risk_distribution)
        
        # 提取高风险模块
        top_risk_modules = self._extract_top_risk_modules(detections)
        
        # 趋势分析
        trend_data = self._analyze_trends(detections)
        
        # 查询推荐（如果需要）
        recommendations_data = None
        if include_recommendations:
            recommendations_data = self._get_recommendations_data(
                project_id, start_date, end_date
            )
        
        # 生成报告摘要
        summary = self._generate_report_summary(
            start_date, end_date, detections, overall_risk, risk_distribution
        )
        
        report = {
            'project_id': project_id,
            'project_name': f"项目 {project_id}",  # TODO: 从Project表查询
            'report_period': f"{start_date} 至 {end_date}",
            'overall_risk_level': overall_risk,
            'total_detections': len(detections),
            'risk_distribution': risk_distribution,
            'top_risk_modules': top_risk_modules,
            'trend_analysis': trend_data,
            'recommendations': recommendations_data,
            'summary': summary,
            'generated_at': datetime.now()
        }
        
        logger.info(
            f"生成质量报告: 项目={project_id}, "
            f"检测数={len(detections)}, 风险等级={overall_risk}"
        )
        
        return report
    
    def _calculate_overall_risk(self, risk_distribution: Dict[str, int]) -> str:
        """计算总体风险等级"""
        if risk_distribution.get('CRITICAL', 0) > 0:
            return 'CRITICAL'
        elif risk_distribution.get('HIGH', 0) >= 3:
            return 'HIGH'
        elif risk_distribution.get('MEDIUM', 0) >= 5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _extract_top_risk_modules(
        self, detections: List[QualityRiskDetection]
    ) -> List[Dict[str, Any]]:
        """提取高风险模块"""
        top_risk_modules = []
        for detection in sorted(detections, key=lambda x: x.risk_score, reverse=True)[:5]:
            top_risk_modules.append({
                'module': detection.module_name or '未知模块',
                'risk_score': float(detection.risk_score),
                'risk_level': detection.risk_level,
                'detection_date': str(detection.detection_date)
            })
        return top_risk_modules
    
    def _analyze_trends(
        self, detections: List[QualityRiskDetection]
    ) -> Dict[str, Dict[str, Any]]:
        """分析趋势数据"""
        trend_data = {}
        for detection in detections:
            date_key = str(detection.detection_date)
            if date_key not in trend_data:
                trend_data[date_key] = {'count': 0, 'avg_score': 0, 'scores': []}
            trend_data[date_key]['count'] += 1
            trend_data[date_key]['scores'].append(float(detection.risk_score))
        
        for date_key in trend_data:
            scores = trend_data[date_key]['scores']
            trend_data[date_key]['avg_score'] = sum(scores) / len(scores)
        
        return trend_data
    
    def _get_recommendations_data(
        self, project_id: int, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """获取推荐数据"""
        recommendations = self.db.query(QualityTestRecommendation).filter(
            QualityTestRecommendation.project_id == project_id,
            QualityTestRecommendation.recommendation_date >= start_date,
            QualityTestRecommendation.recommendation_date <= end_date
        ).all()
        
        return [
            {
                'id': rec.id,
                'priority': rec.priority_level,
                'status': rec.status,
                'recommended_days': rec.recommended_days,
                'ai_reasoning': rec.ai_reasoning
            }
            for rec in recommendations
        ]
    
    def _generate_report_summary(
        self,
        start_date: date,
        end_date: date,
        detections: List[QualityRiskDetection],
        overall_risk: str,
        risk_distribution: Dict[str, int]
    ) -> str:
        """生成报告摘要"""
        summary = f"在{start_date}至{end_date}期间，共检测到{len(detections)}个质量风险，"
        summary += f"总体风险等级为{overall_risk}。"
        if risk_distribution.get('CRITICAL', 0) > 0:
            summary += f"其中包含{risk_distribution['CRITICAL']}个严重风险，需立即关注。"
        return summary
    
    # ==================== 统计分析业务逻辑 ====================
    
    def get_statistics_summary(
        self,
        project_id: Optional[int] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取质量风险统计摘要
        
        Args:
            project_id: 项目ID
            days: 统计天数
            
        Returns:
            Dict[str, Any]: 统计摘要数据
        """
        start_date = date.today() - timedelta(days=days)
        
        query = self.db.query(QualityRiskDetection).filter(
            QualityRiskDetection.detection_date >= start_date
        )
        
        if project_id:
            query = query.filter(QualityRiskDetection.project_id == project_id)
        
        detections = query.all()
        
        # 统计
        total = len(detections)
        by_level = {}
        by_status = {}
        avg_score = 0
        
        for detection in detections:
            by_level[detection.risk_level] = by_level.get(detection.risk_level, 0) + 1
            by_status[detection.status] = by_status.get(detection.status, 0) + 1
            avg_score += float(detection.risk_score)
        
        avg_score = avg_score / total if total > 0 else 0
        
        return {
            'total_detections': total,
            'average_risk_score': round(avg_score, 2),
            'by_risk_level': by_level,
            'by_status': by_status,
            'period_days': days,
            'start_date': str(start_date),
            'end_date': str(date.today())
        }
