"""
项目知识库同步服务
将项目复盘内容同步到售前知识库
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.ai_client_service import AIClientService
from app.models.project_review import ProjectReview, ProjectLesson, ProjectBestPractice
from app.models.presale_knowledge_case import PresaleKnowledgeCase
from app.models.project import Project


class ProjectKnowledgeSyncer:
    """项目知识库同步器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()
    
    def sync_to_knowledge_base(
        self,
        review_id: int,
        auto_publish: bool = True
    ) -> Dict[str, Any]:
        """
        同步复盘到知识库
        
        Args:
            review_id: 复盘报告ID
            auto_publish: 是否自动发布
            
        Returns:
            同步结果
        """
        # 1. 获取复盘报告
        review = self.db.query(ProjectReview).filter(
            ProjectReview.id == review_id
        ).first()
        
        if not review:
            raise ValueError(f"复盘报告 {review_id} 不存在")
        
        # 2. 生成知识案例
        case_data = self._generate_knowledge_case(review)
        
        # 3. 创建或更新知识库记录
        existing_case = self.db.query(PresaleKnowledgeCase).filter(
            PresaleKnowledgeCase.case_name == case_data['case_name']
        ).first()
        
        if existing_case:
            # 更新现有案例
            for key, value in case_data.items():
                if key != 'id':
                    setattr(existing_case, key, value)
            knowledge_case = existing_case
        else:
            # 创建新案例
            knowledge_case = PresaleKnowledgeCase(**case_data)
            self.db.add(knowledge_case)
        
        # 4. 提交保存
        self.db.commit()
        self.db.refresh(knowledge_case)
        
        # 5. 记录同步日志
        sync_log = {
            'review_id': review_id,
            'knowledge_case_id': knowledge_case.id,
            'sync_type': 'AUTO',
            'sync_status': 'SUCCESS',
            'sync_time': datetime.now()
        }
        
        return {
            'success': True,
            'knowledge_case_id': knowledge_case.id,
            'case_name': knowledge_case.case_name,
            'quality_score': float(knowledge_case.quality_score or 0),
            'sync_log': sync_log
        }
    
    def _generate_knowledge_case(
        self,
        review: ProjectReview
    ) -> Dict[str, Any]:
        """生成知识库案例"""
        project = review.project
        
        # 1. 构建AI提示词来生成摘要
        prompt = self._build_summary_prompt(review, project)
        
        # 2. 调用AI生成摘要
        ai_response = self.ai_client.generate_solution(
            prompt=prompt,
            model="glm-5",
            temperature=0.6,
            max_tokens=1500
        )
        
        # 3. 解析AI响应
        summary_data = self._parse_summary_response(ai_response)
        
        # 4. 提取标签
        tags = self._extract_tags(review, project)
        
        # 5. 计算质量评分
        quality_score = self._calculate_quality_score(review)
        
        # 6. 组装案例数据
        case_data = {
            'case_name': f"{project.code} - {project.name}",
            'industry': getattr(project, 'industry', None),
            'equipment_type': getattr(project, 'equipment_type', None),
            'customer_name': project.customer.name if hasattr(project, 'customer') and project.customer else None,
            'project_amount': review.budget_amount,
            'project_summary': summary_data.get('summary', review.ai_summary or ''),
            'technical_highlights': summary_data.get('technical_highlights', self._extract_technical_highlights(review)),
            'success_factors': review.success_factors,
            'lessons_learned': review.problems,
            'tags': tags,
            'quality_score': quality_score,
            'is_public': True,
            'updated_at': datetime.now()
        }
        
        return case_data
    
    def _build_summary_prompt(
        self,
        review: ProjectReview,
        project: Project
    ) -> str:
        """构建摘要生成提示词"""
        return f"""# 项目案例摘要生成任务

## 项目基本信息
- 项目名称：{project.name}
- 项目编号：{project.code}
- 客户名称：{project.customer.name if hasattr(project, 'customer') and project.customer else '未知'}
- 项目金额：¥{review.budget_amount:,.2f}

## 复盘内容
- 成功因素：{review.success_factors or '无'}
- 问题教训：{review.problems or '无'}
- 最佳实践：{review.best_practices or '无'}
- 客户满意度：{review.customer_satisfaction}/5

## 任务要求

请为这个项目生成一份简洁的案例摘要，用于售前知识库，帮助销售团队快速了解该项目的关键信息。

输出JSON格式：
- summary: 项目摘要（150-250字，包含项目背景、实施内容、关键成果）
- technical_highlights: 技术亮点（3-5条，每条20-40字，突出技术创新点和难点攻克）
- key_success_factors: 关键成功要素（3条，每条15-30字）
- applicable_scenarios: 适用场景（50-100字，说明该案例可复用的场景）

确保内容专业、客观、易于理解。"""
    
    def _parse_summary_response(
        self,
        ai_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析AI摘要响应"""
        content = ai_response.get('content', '{}')
        
        try:
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                content = content[start:end].strip()
            
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                'summary': content[:300],
                'technical_highlights': '',
                'key_success_factors': '',
                'applicable_scenarios': ''
            }
    
    def _extract_tags(
        self,
        review: ProjectReview,
        project: Project
    ) -> List[str]:
        """提取标签"""
        tags = []
        
        # 行业标签
        if hasattr(project, 'industry') and project.industry:
            tags.append(project.industry)
        
        # 项目类型标签
        if hasattr(project, 'project_type') and project.project_type:
            tags.append(project.project_type)
        
        # 规模标签
        if review.budget_amount:
            if review.budget_amount < 500000:
                tags.append('小型项目')
            elif review.budget_amount < 2000000:
                tags.append('中型项目')
            else:
                tags.append('大型项目')
        
        # 质量标签
        if review.customer_satisfaction:
            if review.customer_satisfaction >= 4:
                tags.append('高满意度')
            elif review.customer_satisfaction >= 3:
                tags.append('中等满意度')
        
        # 进度标签
        if review.schedule_variance:
            if review.schedule_variance <= 0:
                tags.append('按期交付')
            elif review.schedule_variance <= 7:
                tags.append('轻微延期')
            else:
                tags.append('显著延期')
        
        # 成本标签
        if review.cost_variance:
            cost_var_pct = (float(review.cost_variance) / float(review.budget_amount or 1)) * 100
            if cost_var_pct <= 5:
                tags.append('成本可控')
            elif cost_var_pct <= 15:
                tags.append('成本超支')
            else:
                tags.append('严重超支')
        
        return list(set(tags))  # 去重
    
    def _extract_technical_highlights(
        self,
        review: ProjectReview
    ) -> str:
        """从最佳实践中提取技术亮点"""
        if not review.best_practices:
            return ''
        
        # 简单提取：取前300字符
        highlights = review.best_practices[:300]
        if len(review.best_practices) > 300:
            highlights += '...'
        
        return highlights
    
    def _calculate_quality_score(
        self,
        review: ProjectReview
    ) -> float:
        """计算案例质量评分"""
        score = 0.5  # 基础分
        
        # 客户满意度权重：30%
        if review.customer_satisfaction:
            score += (review.customer_satisfaction / 5.0) * 0.3
        
        # 进度控制权重：20%
        if review.schedule_variance is not None:
            if review.schedule_variance <= 0:
                score += 0.2  # 按期或提前
            elif review.schedule_variance <= 7:
                score += 0.1  # 轻微延期
            # 延期不加分
        
        # 成本控制权重：20%
        if review.cost_variance is not None and review.budget_amount:
            cost_var_pct = abs(float(review.cost_variance) / float(review.budget_amount or 1)) * 100
            if cost_var_pct <= 5:
                score += 0.2  # 优秀
            elif cost_var_pct <= 10:
                score += 0.1  # 良好
            # 超支不加分
        
        # 变更控制权重：10%
        if review.change_count is not None:
            if review.change_count <= 3:
                score += 0.1
            elif review.change_count <= 5:
                score += 0.05
        
        # 内容完整性权重：20%
        completeness = 0
        if review.success_factors and len(review.success_factors) > 50:
            completeness += 0.05
        if review.problems and len(review.problems) > 50:
            completeness += 0.05
        if review.best_practices and len(review.best_practices) > 50:
            completeness += 0.05
        if review.conclusion and len(review.conclusion) > 50:
            completeness += 0.05
        score += completeness
        
        # 确保分数在0-1之间
        return max(0.0, min(1.0, score))
    
    def update_case_from_lessons(
        self,
        review_id: int,
        case_id: int
    ) -> Dict[str, Any]:
        """从经验教训更新知识库案例"""
        # 获取经验教训
        lessons = self.db.query(ProjectLesson).filter(
            ProjectLesson.review_id == review_id,
            ProjectLesson.ai_confidence >= 0.7
        ).all()
        
        # 获取知识库案例
        case = self.db.query(PresaleKnowledgeCase).filter(
            PresaleKnowledgeCase.id == case_id
        ).first()
        
        if not case:
            raise ValueError(f"知识库案例 {case_id} 不存在")
        
        # 分类整理经验
        success_lessons = [l for l in lessons if l.lesson_type == 'SUCCESS']
        failure_lessons = [l for l in lessons if l.lesson_type == 'FAILURE']
        
        # 更新成功要素和失败教训
        if success_lessons:
            case.success_factors = '\n'.join(
                f"• {l.title}: {l.description}" for l in success_lessons[:5]
            )
        
        if failure_lessons:
            case.lessons_learned = '\n'.join(
                f"• {l.title}: {l.description}" for l in failure_lessons[:5]
            )
        
        # 更新标签
        all_tags = set(case.tags or [])
        for lesson in lessons:
            if lesson.tags:
                all_tags.update(lesson.tags)
        case.tags = list(all_tags)[:10]  # 限制标签数量
        
        # 更新时间
        case.updated_at = datetime.now()
        
        self.db.commit()
        
        return {
            'success': True,
            'updated_fields': ['success_factors', 'lessons_learned', 'tags'],
            'lessons_count': len(lessons)
        }
    
    def get_sync_status(
        self,
        review_id: int
    ) -> Dict[str, Any]:
        """获取同步状态"""
        # 查询是否已同步
        review = self.db.query(ProjectReview).filter(
            ProjectReview.id == review_id
        ).first()
        
        if not review:
            return {'synced': False, 'error': '复盘报告不存在'}
        
        # 查找对应的知识库案例
        case_name = f"{review.project_code} - {review.project.name if review.project else ''}"
        case = self.db.query(PresaleKnowledgeCase).filter(
            PresaleKnowledgeCase.case_name == case_name
        ).first()
        
        if case:
            return {
                'synced': True,
                'case_id': case.id,
                'case_name': case.case_name,
                'quality_score': float(case.quality_score or 0),
                'last_updated': case.updated_at.isoformat() if case.updated_at else None,
                'tags': case.tags
            }
        else:
            return {
                'synced': False,
                'message': '尚未同步到知识库'
            }
