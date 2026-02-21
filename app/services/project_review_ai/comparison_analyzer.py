"""
项目对比分析服务
与历史项目进行对比，识别改进点和最佳实践
"""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.services.ai_client_service import AIClientService
from app.models.project_review import ProjectReview, ProjectLesson, ProjectBestPractice
from app.models.project import Project


class ProjectComparisonAnalyzer:
    """项目对比分析器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()
    
    def compare_with_history(
        self,
        review_id: int,
        similarity_type: str = 'industry',
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        与历史项目对比
        
        Args:
            review_id: 复盘报告ID
            similarity_type: 相似度类型 (industry/type/scale)
            limit: 对比项目数量
            
        Returns:
            对比分析结果
        """
        # 1. 获取当前项目复盘
        current_review = self.db.query(ProjectReview).filter(
            ProjectReview.id == review_id
        ).first()
        
        if not current_review:
            raise ValueError(f"复盘报告 {review_id} 不存在")
        
        # 2. 查找相似历史项目
        similar_reviews = self._find_similar_reviews(
            current_review,
            similarity_type,
            limit
        )
        
        # 3. 构建对比数据
        comparison_data = self._build_comparison_data(
            current_review,
            similar_reviews
        )
        
        # 4. AI分析对比结果
        analysis = self._analyze_comparison(comparison_data)
        
        return {
            'current_review': self._format_review(current_review),
            'similar_reviews': [self._format_review(r) for r in similar_reviews],
            'comparison': comparison_data,
            'analysis': analysis,
            'improvements': analysis.get('improvements', []),
            'benchmarks': analysis.get('benchmarks', {})
        }
    
    def identify_improvements(
        self,
        review_id: int
    ) -> List[Dict[str, Any]]:
        """
        识别改进点
        
        基于历史项目的成功经验，识别当前项目可以改进的方面
        """
        # 获取对比分析结果
        comparison = self.compare_with_history(review_id)
        
        # 提取改进建议
        improvements = comparison.get('analysis', {}).get('improvements', [])
        
        # 增强改进建议（添加优先级和可行性）
        enhanced_improvements = []
        for imp in improvements:
            enhanced_improvements.append({
                **imp,
                'priority': self._calculate_priority(imp),
                'feasibility': self._assess_feasibility(imp),
                'estimated_impact': self._estimate_impact(imp)
            })
        
        # 按优先级排序
        enhanced_improvements.sort(
            key=lambda x: (
                {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}.get(x['priority'], 1),
                -x.get('estimated_impact', 0)
            )
        )
        
        return enhanced_improvements
    
    def _find_similar_reviews(
        self,
        current_review: ProjectReview,
        similarity_type: str,
        limit: int
    ) -> List[ProjectReview]:
        """查找相似的历史复盘"""
        query = self.db.query(ProjectReview).filter(
            ProjectReview.id != current_review.id,
            ProjectReview.status == 'PUBLISHED'
        )
        
        current_project = current_review.project
        
        if similarity_type == 'industry':
            # 按行业相似度查找
            query = query.join(Project).filter(
                Project.industry == current_project.industry
            )
        elif similarity_type == 'type':
            # 按项目类型查找
            query = query.join(Project).filter(
                Project.project_type == current_project.project_type
            )
        elif similarity_type == 'scale':
            # 按项目规模查找（预算接近）
            budget = float(current_review.budget_amount or 0)
            query = query.filter(
                and_(
                    ProjectReview.budget_amount >= budget * 0.7,
                    ProjectReview.budget_amount <= budget * 1.3
                )
            )
        
        # 按客户满意度排序（替代不存在的quality_score）
        query = query.order_by(ProjectReview.customer_satisfaction.desc())
        
        return query.limit(limit).all()
    
    def _build_comparison_data(
        self,
        current: ProjectReview,
        similars: List[ProjectReview]
    ) -> Dict[str, Any]:
        """构建对比数据"""
        # 计算平均指标
        avg_schedule_variance = sum(r.schedule_variance or 0 for r in similars) / len(similars) if similars else 0
        avg_cost_variance = sum(float(r.cost_variance or 0) for r in similars) / len(similars) if similars else 0
        avg_change_count = sum(r.change_count or 0 for r in similars) / len(similars) if similars else 0
        avg_satisfaction = sum(r.customer_satisfaction or 0 for r in similars) / len(similars) if similars else 0
        
        return {
            'current': {
                'schedule_variance': current.schedule_variance or 0,
                'cost_variance': float(current.cost_variance or 0),
                'change_count': current.change_count or 0,
                'customer_satisfaction': current.customer_satisfaction or 0,
            },
            'historical_average': {
                'schedule_variance': avg_schedule_variance,
                'cost_variance': avg_cost_variance,
                'change_count': avg_change_count,
                'customer_satisfaction': avg_satisfaction,
            },
            'variance_analysis': {
                'schedule': (current.schedule_variance or 0) - avg_schedule_variance,
                'cost': float(current.cost_variance or 0) - avg_cost_variance,
                'changes': (current.change_count or 0) - avg_change_count,
                'satisfaction': (current.customer_satisfaction or 0) - avg_satisfaction,
            }
        }
    
    def _analyze_comparison(
        self,
        comparison_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI分析对比结果"""
        prompt = f"""# 项目对比分析任务

## 当前项目指标
- 进度偏差：{comparison_data['current']['schedule_variance']}天
- 成本偏差：¥{comparison_data['current']['cost_variance']:,.2f}
- 变更次数：{comparison_data['current']['change_count']}次
- 客户满意度：{comparison_data['current']['customer_satisfaction']}/5

## 历史项目平均指标
- 进度偏差：{comparison_data['historical_average']['schedule_variance']:.1f}天
- 成本偏差：¥{comparison_data['historical_average']['cost_variance']:,.2f}
- 变更次数：{comparison_data['historical_average']['change_count']:.1f}次
- 客户满意度：{comparison_data['historical_average']['customer_satisfaction']:.1f}/5

## 差异分析
- 进度表现：{'优于' if comparison_data['variance_analysis']['schedule'] < 0 else '劣于'}历史平均 {abs(comparison_data['variance_analysis']['schedule']):.1f}天
- 成本控制：{'优于' if comparison_data['variance_analysis']['cost'] < 0 else '劣于'}历史平均 ¥{abs(comparison_data['variance_analysis']['cost']):,.2f}
- 变更管理：{'优于' if comparison_data['variance_analysis']['changes'] < 0 else '劣于'}历史平均 {abs(comparison_data['variance_analysis']['changes']):.1f}次
- 客户满意：{'高于' if comparison_data['variance_analysis']['satisfaction'] > 0 else '低于'}历史平均 {abs(comparison_data['variance_analysis']['satisfaction']):.1f}分

## 任务要求

请作为项目管理专家，基于以上对比数据：

1. **识别优势**（2-3条）
   - 当前项目优于历史平均的方面
   - 分析原因和成功因素

2. **识别劣势**（2-3条）
   - 当前项目劣于历史平均的方面
   - 分析可能的原因

3. **改进建议**（3-5条）
   - 针对劣势提出具体改进措施
   - 每条包含：领域、问题、建议、预期效果

4. **基准对比**
   - 进度管理基准
   - 成本控制基准
   - 质量管理基准

请以JSON格式输出：
- strengths: 优势数组 [{{"area": "领域", "description": "描述", "reason": "原因"}}]
- weaknesses: 劣势数组 [{{"area": "领域", "description": "描述", "cause": "原因"}}]
- improvements: 改进建议数组 [{{"area": "领域", "problem": "问题", "suggestion": "建议", "expected_impact": "预期影响", "priority": "优先级"}}]
- benchmarks: 基准对比 {{"schedule": {{}}, "cost": {{}}, "quality": {{}}}}"""
        
        ai_response = self.ai_client.generate_solution(
            prompt=prompt,
            model="glm-5",
            temperature=0.6,
            max_tokens=2000
        )
        
        # 解析响应
        content = ai_response.get('content', '{}')
        try:
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                content = content[start:end].strip()
            
            analysis = json.loads(content)
        except json.JSONDecodeError:
            analysis = {
                'strengths': [],
                'weaknesses': [],
                'improvements': [],
                'benchmarks': {}
            }
        
        return analysis
    
    def _format_review(self, review: ProjectReview) -> Dict[str, Any]:
        """格式化复盘报告"""
        return {
            'id': review.id,
            'review_no': review.review_no,
            'project_code': review.project_code,
            'schedule_variance': review.schedule_variance,
            'cost_variance': float(review.cost_variance or 0),
            'change_count': review.change_count,
            'customer_satisfaction': review.customer_satisfaction,
            'quality_issues': review.quality_issues or 0,
        }
    
    def _calculate_priority(self, improvement: Dict[str, Any]) -> str:
        """计算改进建议的优先级"""
        # 简化的优先级算法
        impact = improvement.get('expected_impact', '').lower()
        
        if '显著' in impact or '重大' in impact or '大幅' in impact:
            return 'HIGH'
        elif '一定' in impact or '部分' in impact or '改善' in impact:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _assess_feasibility(self, improvement: Dict[str, Any]) -> str:
        """评估可行性"""
        # 简化的可行性评估
        suggestion = improvement.get('suggestion', '').lower()
        
        if '培训' in suggestion or '流程' in suggestion or '制度' in suggestion:
            return 'HIGH'
        elif '工具' in suggestion or '系统' in suggestion:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    def _estimate_impact(self, improvement: Dict[str, Any]) -> float:
        """估算影响（0-1）"""
        priority = improvement.get('priority', 'MEDIUM')
        
        impact_scores = {
            'HIGH': 0.8,
            'MEDIUM': 0.5,
            'LOW': 0.3
        }
        
        return impact_scores.get(priority, 0.5)
