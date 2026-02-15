"""
项目经验教训AI提取服务
从项目数据中自动识别和提取关键经验教训
"""
import json
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.ai_client_service import AIClientService
from app.models.project_review import ProjectReview, ProjectLesson


class ProjectLessonExtractor:
    """项目经验教训提取器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()
    
    def extract_lessons(
        self,
        review_id: int,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        从复盘报告中提取经验教训
        
        Args:
            review_id: 复盘报告ID
            min_confidence: 最小置信度阈值
            
        Returns:
            提取的经验教训列表
        """
        # 1. 获取复盘报告
        review = self.db.query(ProjectReview).filter(
            ProjectReview.id == review_id
        ).first()
        
        if not review:
            raise ValueError(f"复盘报告 {review_id} 不存在")
        
        # 2. 构建提示词
        prompt = self._build_extraction_prompt(review)
        
        # 3. 调用AI提取
        ai_response = self.ai_client.generate_solution(
            prompt=prompt,
            model="glm-5",
            temperature=0.5,
            max_tokens=2000
        )
        
        # 4. 解析响应
        lessons = self._parse_lessons(ai_response, review)
        
        # 5. 过滤低置信度结果
        filtered_lessons = [
            lesson for lesson in lessons
            if lesson.get('ai_confidence', 0) >= min_confidence
        ]
        
        return filtered_lessons
    
    def _build_extraction_prompt(self, review: ProjectReview) -> str:
        """构建经验教训提取提示词"""
        prompt = f"""# 项目经验教训提取任务

## 项目信息
- 项目编号：{review.project_code}
- 复盘类型：{review.review_type}
- 进度偏差：{review.schedule_variance}天
- 成本偏差：¥{review.cost_variance}
- 变更次数：{review.change_count}次
- 客户满意度：{review.customer_satisfaction}/5

## 复盘内容

### 成功因素
{review.success_factors or '无'}

### 问题与教训
{review.problems or '无'}

### 改进建议
{review.improvements or '无'}

### 最佳实践
{review.best_practices or '无'}

## 任务要求

请作为项目管理专家，从以上复盘内容中提取结构化的经验教训，包括：

1. **成功经验**（SUCCESS类型）
   - 识别可复用的成功做法
   - 分析成功的根本原因
   - 说明适用场景

2. **失败教训**（FAILURE类型）
   - 识别需要避免的错误
   - 分析失败的根本原因
   - 提出改进措施

### 提取标准
- 每条经验要具体、可操作
- 明确根本原因
- 说明影响范围
- 提供改进措施（针对失败教训）
- 评估置信度（0-1）

### 分类维度
- 进度管理
- 成本控制
- 质量保证
- 沟通协作
- 技术实现
- 风险管理

请以JSON数组格式输出，每条经验包含：
- lesson_type: "SUCCESS" 或 "FAILURE"
- title: 经验标题（10-30字）
- description: 详细描述（50-150字）
- root_cause: 根本原因（30-80字）
- impact: 影响范围（20-50字）
- improvement_action: 改进措施（仅FAILURE类型，30-80字）
- category: 分类（进度/成本/质量/沟通/技术/管理）
- tags: 标签数组（3-5个关键词）
- priority: 优先级（LOW/MEDIUM/HIGH）
- confidence: AI置信度（0-1，表示该经验的可靠性）

至少提取5条，最多10条，按重要性排序。"""
        
        return prompt
    
    def _parse_lessons(
        self,
        ai_response: Dict[str, Any],
        review: ProjectReview
    ) -> List[Dict[str, Any]]:
        """解析AI响应为经验教训列表"""
        content = ai_response.get('content', '[]')
        
        # 提取JSON数组
        try:
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                content = content[start:end].strip()
            elif '```' in content:
                start = content.find('```') + 3
                end = content.find('```', start)
                content = content[start:end].strip()
            
            lessons_data = json.loads(content)
            if not isinstance(lessons_data, list):
                lessons_data = [lessons_data]
        except json.JSONDecodeError:
            return []
        
        # 标准化每条经验
        lessons = []
        for lesson_data in lessons_data:
            lesson = {
                'review_id': review.id,
                'project_id': review.project_id,
                'lesson_type': lesson_data.get('lesson_type', 'SUCCESS'),
                'title': lesson_data.get('title', '')[:200],
                'description': lesson_data.get('description', ''),
                'root_cause': lesson_data.get('root_cause'),
                'impact': lesson_data.get('impact'),
                'improvement_action': lesson_data.get('improvement_action'),
                'category': lesson_data.get('category', '管理'),
                'tags': lesson_data.get('tags', []),
                'priority': lesson_data.get('priority', 'MEDIUM'),
                'ai_extracted': True,
                'ai_confidence': float(lesson_data.get('confidence', 0.7)),
                'status': 'OPEN',
            }
            lessons.append(lesson)
        
        return lessons
    
    def categorize_lessons(
        self,
        lessons: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """按类别分组经验教训"""
        categorized = {
            '进度': [],
            '成本': [],
            '质量': [],
            '沟通': [],
            '技术': [],
            '管理': [],
        }
        
        for lesson in lessons:
            category = lesson.get('category', '管理')
            if category in categorized:
                categorized[category].append(lesson)
        
        return categorized
    
    def rank_lessons_by_priority(
        self,
        lessons: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """按优先级排序经验教训"""
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        
        return sorted(
            lessons,
            key=lambda x: (
                priority_order.get(x.get('priority', 'MEDIUM'), 1),
                -x.get('ai_confidence', 0.5)
            )
        )
    
    def find_similar_lessons(
        self,
        lesson_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """查找相似的历史经验（基于标签和分类）"""
        lesson = self.db.query(ProjectLesson).filter(
            ProjectLesson.id == lesson_id
        ).first()
        
        if not lesson:
            return []
        
        # 查找相同分类和标签的经验
        similar_lessons = self.db.query(ProjectLesson).filter(
            ProjectLesson.id != lesson_id,
            ProjectLesson.category == lesson.category
        ).limit(limit).all()
        
        return [
            {
                'id': l.id,
                'title': l.title,
                'description': l.description,
                'category': l.category,
                'tags': l.tags,
                'confidence': float(l.ai_confidence or 0),
                'project_code': l.review.project_code if l.review else None,
            }
            for l in similar_lessons
        ]
