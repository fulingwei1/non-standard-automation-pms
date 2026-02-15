"""
售前AI知识库服务
"""
import json
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
import logging

from app.models.presale_knowledge_case import PresaleKnowledgeCase
from app.models.presale_ai_qa import PresaleAIQA
from app.schemas.presale_ai_knowledge import (
    KnowledgeCaseCreate,
    KnowledgeCaseUpdate,
    SemanticSearchRequest,
    BestPracticeRequest,
    KnowledgeExtractionRequest,
    AIQARequest,
)

logger = logging.getLogger(__name__)


class PresaleAIKnowledgeService:
    """AI知识库服务"""

    def __init__(self, db: Session):
        self.db = db

    # ============= 案例管理 =============

    def create_case(self, case_data: KnowledgeCaseCreate) -> PresaleKnowledgeCase:
        """创建案例"""
        case = PresaleKnowledgeCase(
            case_name=case_data.case_name,
            industry=case_data.industry,
            equipment_type=case_data.equipment_type,
            customer_name=case_data.customer_name,
            project_amount=case_data.project_amount,
            project_summary=case_data.project_summary,
            technical_highlights=case_data.technical_highlights,
            success_factors=case_data.success_factors,
            lessons_learned=case_data.lessons_learned,
            tags=case_data.tags,
            quality_score=case_data.quality_score or 0.5,
            is_public=case_data.is_public,
        )
        
        # 生成嵌入向量
        if case_data.project_summary:
            embedding = self._generate_embedding(case_data.project_summary)
            case.embedding = self._serialize_embedding(embedding)
        
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        
        logger.info(f"创建案例成功: {case.id} - {case.case_name}")
        return case

    def update_case(self, case_id: int, update_data: KnowledgeCaseUpdate) -> Optional[PresaleKnowledgeCase]:
        """更新案例"""
        case = self.db.query(PresaleKnowledgeCase).filter(PresaleKnowledgeCase.id == case_id).first()
        if not case:
            return None

        update_dict = update_data.model_dump(exclude_unset=True)
        
        # 如果更新了摘要，重新生成嵌入
        if 'project_summary' in update_dict and update_dict['project_summary']:
            embedding = self._generate_embedding(update_dict['project_summary'])
            case.embedding = self._serialize_embedding(embedding)
        
        for key, value in update_dict.items():
            setattr(case, key, value)
        
        self.db.commit()
        self.db.refresh(case)
        
        logger.info(f"更新案例成功: {case_id}")
        return case

    def get_case(self, case_id: int) -> Optional[PresaleKnowledgeCase]:
        """获取案例详情"""
        return self.db.query(PresaleKnowledgeCase).filter(PresaleKnowledgeCase.id == case_id).first()

    def delete_case(self, case_id: int) -> bool:
        """删除案例"""
        case = self.get_case(case_id)
        if not case:
            return False
        
        self.db.delete(case)
        self.db.commit()
        
        logger.info(f"删除案例成功: {case_id}")
        return True

    # ============= 语义搜索 =============

    def semantic_search(self, search_request: SemanticSearchRequest) -> Tuple[List[PresaleKnowledgeCase], int]:
        """
        语义搜索相似案例
        返回: (案例列表, 总数)
        """
        query = search_request.query
        
        # 构建基础查询条件
        filters = [PresaleKnowledgeCase.is_public == True]
        
        if search_request.industry:
            filters.append(PresaleKnowledgeCase.industry == search_request.industry)
        
        if search_request.equipment_type:
            filters.append(PresaleKnowledgeCase.equipment_type == search_request.equipment_type)
        
        if search_request.min_amount is not None:
            filters.append(PresaleKnowledgeCase.project_amount >= search_request.min_amount)
        
        if search_request.max_amount is not None:
            filters.append(PresaleKnowledgeCase.project_amount <= search_request.max_amount)
        
        # 查询所有符合条件的案例
        base_query = self.db.query(PresaleKnowledgeCase).filter(and_(*filters))
        all_cases = base_query.all()
        
        if not all_cases:
            return [], 0
        
        # 生成查询向量
        query_embedding = self._generate_embedding(query)
        
        # 计算相似度
        cases_with_similarity = []
        for case in all_cases:
            if case.embedding:
                case_embedding = self._deserialize_embedding(case.embedding)
                similarity = self._cosine_similarity(query_embedding, case_embedding)
            else:
                # 如果没有嵌入，使用关键词匹配作为fallback
                similarity = self._keyword_similarity(query, case)
            
            cases_with_similarity.append((case, similarity))
        
        # 按相似度排序
        cases_with_similarity.sort(key=lambda x: x[1], reverse=True)
        
        # 返回TOP K
        top_k = min(search_request.top_k, len(cases_with_similarity))
        top_cases = []
        for case, similarity in cases_with_similarity[:top_k]:
            # 添加相似度属性
            case.similarity_score = similarity
            top_cases.append(case)
        
        logger.info(f"语义搜索完成: query='{query}', 找到{len(top_cases)}个结果")
        return top_cases, len(all_cases)

    # ============= 最佳实践推荐 =============

    def recommend_best_practices(self, request: BestPracticeRequest) -> Dict[str, Any]:
        """推荐最佳实践"""
        # 先通过语义搜索找到相关案例
        search_req = SemanticSearchRequest(
            query=request.scenario,
            industry=request.industry,
            equipment_type=request.equipment_type,
            top_k=request.top_k * 2,  # 多取一些再筛选
        )
        
        cases, _ = self.semantic_search(search_req)
        
        # 筛选高质量案例
        high_quality_cases = [c for c in cases if c.quality_score >= 0.7]
        
        if not high_quality_cases:
            # 如果没有高质量案例，降低标准
            high_quality_cases = cases[:request.top_k]
        else:
            high_quality_cases = high_quality_cases[:request.top_k]
        
        # 分析成功模式
        success_pattern_analysis = self._analyze_success_patterns(high_quality_cases)
        
        # 提取风险警告
        risk_warnings = self._extract_risk_warnings(high_quality_cases)
        
        logger.info(f"最佳实践推荐完成: scenario='{request.scenario}', 推荐{len(high_quality_cases)}个案例")
        
        return {
            'recommended_cases': high_quality_cases,
            'success_pattern_analysis': success_pattern_analysis,
            'risk_warnings': risk_warnings,
        }

    # ============= 知识提取 =============

    def extract_case_knowledge(self, request: KnowledgeExtractionRequest) -> Dict[str, Any]:
        """从项目数据中提取案例知识"""
        project_data = request.project_data
        
        # 提取关键信息（模拟AI提取）
        extracted_case = KnowledgeCaseCreate(
            case_name=project_data.get('project_name', '未命名项目'),
            industry=project_data.get('industry'),
            equipment_type=project_data.get('equipment_type'),
            customer_name=project_data.get('customer_name'),
            project_amount=project_data.get('amount'),
            project_summary=self._generate_summary(project_data),
            technical_highlights=self._extract_highlights(project_data),
            success_factors=self._extract_success_factors(project_data),
            lessons_learned=self._extract_lessons(project_data),
            tags=self._suggest_tags(project_data),
            quality_score=self._assess_quality(project_data),
        )
        
        # 计算提取置信度
        extraction_confidence = self._calculate_extraction_confidence(project_data)
        
        # 如果设置了自动保存且置信度足够高，保存到知识库
        if request.auto_save and extraction_confidence >= 0.7:
            saved_case = self.create_case(extracted_case)
            logger.info(f"自动保存案例到知识库: {saved_case.id}")
        
        quality_assessment = self._generate_quality_assessment(extracted_case, extraction_confidence)
        
        return {
            'extracted_case': extracted_case,
            'extraction_confidence': extraction_confidence,
            'suggested_tags': extracted_case.tags or [],
            'quality_assessment': quality_assessment,
        }

    # ============= 智能问答 =============

    def ask_question(self, request: AIQARequest, user_id: Optional[int] = None) -> Dict[str, Any]:
        """智能问答"""
        question = request.question
        context = request.context or {}
        
        # 搜索相关案例
        search_req = SemanticSearchRequest(
            query=question,
            top_k=5,
        )
        matched_cases, _ = self.semantic_search(search_req)
        
        # 生成答案（模拟AI生成）
        answer = self._generate_answer(question, matched_cases, context)
        
        # 计算置信度
        confidence_score = self._calculate_qa_confidence(matched_cases)
        
        # 保存问答记录
        qa_record = PresaleAIQA(
            question=question,
            answer=answer,
            matched_cases=[c.id for c in matched_cases],
            confidence_score=confidence_score,
            created_by=user_id,
        )
        self.db.add(qa_record)
        self.db.commit()
        
        sources = [f"案例#{c.id}: {c.case_name}" for c in matched_cases[:3]]
        
        logger.info(f"智能问答完成: question='{question[:50]}...', confidence={confidence_score:.2f}")
        
        return {
            'answer': answer,
            'matched_cases': matched_cases,
            'confidence_score': confidence_score,
            'sources': sources,
            'qa_id': qa_record.id,
        }

    def submit_qa_feedback(self, qa_id: int, feedback_score: int, feedback_comment: Optional[str] = None) -> bool:
        """提交问答反馈"""
        qa = self.db.query(PresaleAIQA).filter(PresaleAIQA.id == qa_id).first()
        if not qa:
            return False
        
        qa.feedback_score = feedback_score
        self.db.commit()
        
        logger.info(f"问答反馈已提交: qa_id={qa_id}, score={feedback_score}")
        return True

    # ============= 知识库搜索和管理 =============

    def search_knowledge_base(
        self,
        keyword: Optional[str] = None,
        tags: Optional[List[str]] = None,
        industry: Optional[str] = None,
        equipment_type: Optional[str] = None,
        min_quality_score: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[PresaleKnowledgeCase], int]:
        """知识库搜索"""
        query = self.db.query(PresaleKnowledgeCase)
        
        # 构建筛选条件
        if keyword:
            keyword_filter = or_(
                PresaleKnowledgeCase.case_name.like(f'%{keyword}%'),
                PresaleKnowledgeCase.project_summary.like(f'%{keyword}%'),
                PresaleKnowledgeCase.technical_highlights.like(f'%{keyword}%'),
            )
            query = query.filter(keyword_filter)
        
        if tags:
            # JSON数组筛选（简化版）
            for tag in tags:
                query = query.filter(PresaleKnowledgeCase.tags.contains(tag))
        
        if industry:
            query = query.filter(PresaleKnowledgeCase.industry == industry)
        
        if equipment_type:
            query = query.filter(PresaleKnowledgeCase.equipment_type == equipment_type)
        
        if min_quality_score is not None:
            query = query.filter(PresaleKnowledgeCase.quality_score >= min_quality_score)
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        cases = query.order_by(PresaleKnowledgeCase.quality_score.desc(), 
                               PresaleKnowledgeCase.created_at.desc()) \
                     .offset(offset).limit(page_size).all()
        
        return cases, total

    def get_all_tags(self) -> Dict[str, Any]:
        """获取所有标签"""
        cases = self.db.query(PresaleKnowledgeCase).all()
        
        tag_counter = {}
        all_tags = set()
        
        for case in cases:
            if case.tags:
                for tag in case.tags:
                    all_tags.add(tag)
                    tag_counter[tag] = tag_counter.get(tag, 0) + 1
        
        return {
            'tags': sorted(list(all_tags)),
            'tag_counts': tag_counter,
        }

    # ============= 辅助方法 =============

    def _generate_embedding(self, text: str) -> np.ndarray:
        """
        生成文本嵌入向量
        实际应用中应该调用OpenAI API或其他嵌入服务
        这里使用简化的模拟实现
        """
        # 模拟: 使用简单的hash + 随机向量
        # 实际应该调用: openai.Embedding.create(model="text-embedding-ada-002", input=text)
        np.random.seed(hash(text) % (2**32))
        embedding = np.random.randn(384)  # 384维向量
        # 归一化
        embedding = embedding / np.linalg.norm(embedding)
        return embedding

    def _serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """序列化嵌入向量为BLOB"""
        return embedding.astype(np.float32).tobytes()

    def _deserialize_embedding(self, blob: bytes) -> np.ndarray:
        """反序列化BLOB为嵌入向量"""
        return np.frombuffer(blob, dtype=np.float32)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    def _keyword_similarity(self, query: str, case: PresaleKnowledgeCase) -> float:
        """关键词相似度（fallback）"""
        query_lower = query.lower()
        score = 0.0
        
        # 检查各个字段
        if case.case_name and query_lower in case.case_name.lower():
            score += 0.3
        if case.project_summary and query_lower in case.project_summary.lower():
            score += 0.4
        if case.technical_highlights and query_lower in case.technical_highlights.lower():
            score += 0.2
        if case.tags:
            for tag in case.tags:
                if query_lower in tag.lower():
                    score += 0.1
        
        return min(score, 1.0)

    def _analyze_success_patterns(self, cases: List[PresaleKnowledgeCase]) -> str:
        """分析成功模式"""
        if not cases:
            return "暂无足够案例进行分析"
        
        # 提取共同的成功要素
        common_factors = []
        all_factors = []
        
        for case in cases:
            if case.success_factors:
                all_factors.append(case.success_factors)
        
        if all_factors:
            analysis = f"基于{len(cases)}个高质量案例的分析，主要成功模式包括：\n"
            analysis += "1. 技术方案的准确性和可行性\n"
            analysis += "2. 与客户需求的高度契合\n"
            analysis += "3. 团队经验和技术储备\n"
            analysis += "4. 项目管理和进度控制\n"
            return analysis
        
        return "成功要素数据不足，建议补充案例详情"

    def _extract_risk_warnings(self, cases: List[PresaleKnowledgeCase]) -> List[str]:
        """提取风险警告"""
        warnings = []
        
        for case in cases:
            if case.lessons_learned:
                # 简化版：将教训转换为警告
                warnings.append(f"注意：{case.lessons_learned[:100]}")
        
        # 去重并限制数量
        warnings = list(set(warnings))[:5]
        
        if not warnings:
            warnings = ["建议仔细评估技术可行性", "注意客户需求的准确理解"]
        
        return warnings

    def _generate_summary(self, project_data: Dict) -> str:
        """生成项目摘要"""
        summary_parts = []
        
        if project_data.get('project_name'):
            summary_parts.append(f"项目名称：{project_data['project_name']}")
        
        if project_data.get('description'):
            summary_parts.append(f"项目描述：{project_data['description']}")
        
        if project_data.get('objectives'):
            summary_parts.append(f"项目目标：{project_data['objectives']}")
        
        return " | ".join(summary_parts) if summary_parts else "项目摘要待补充"

    def _extract_highlights(self, project_data: Dict) -> str:
        """提取技术亮点"""
        highlights = project_data.get('technical_highlights', project_data.get('highlights', ''))
        return highlights if highlights else "技术亮点待补充"

    def _extract_success_factors(self, project_data: Dict) -> str:
        """提取成功要素"""
        if project_data.get('status') == 'completed' and project_data.get('success_rate', 0) > 0.8:
            return "项目成功完成，达到预期目标"
        return "成功要素待项目完成后总结"

    def _extract_lessons(self, project_data: Dict) -> str:
        """提取失败教训"""
        lessons = project_data.get('lessons_learned', '')
        return lessons if lessons else "暂无失败教训记录"

    def _suggest_tags(self, project_data: Dict) -> List[str]:
        """建议标签"""
        tags = []
        
        if project_data.get('industry'):
            tags.append(project_data['industry'])
        
        if project_data.get('equipment_type'):
            tags.append(project_data['equipment_type'])
        
        if project_data.get('technology'):
            tags.append(project_data['technology'])
        
        # 添加一些通用标签
        if project_data.get('amount', 0) > 1000000:
            tags.append('大型项目')
        
        return tags or ['通用案例']

    def _assess_quality(self, project_data: Dict) -> float:
        """评估案例质量"""
        score = 0.5  # 基础分
        
        # 有完整描述+0.2
        if project_data.get('description'):
            score += 0.2
        
        # 有技术亮点+0.1
        if project_data.get('technical_highlights'):
            score += 0.1
        
        # 项目成功+0.2
        if project_data.get('status') == 'completed':
            score += 0.2
        
        return min(score, 1.0)

    def _calculate_extraction_confidence(self, project_data: Dict) -> float:
        """计算提取置信度"""
        confidence = 0.3  # 基础置信度
        
        required_fields = ['project_name', 'description', 'industry', 'equipment_type']
        for field in required_fields:
            if project_data.get(field):
                confidence += 0.15
        
        return min(confidence, 1.0)

    def _generate_quality_assessment(self, case: KnowledgeCaseCreate, confidence: float) -> str:
        """生成质量评估"""
        if confidence >= 0.8:
            return f"高质量案例（置信度{confidence:.0%}），建议保存到知识库"
        elif confidence >= 0.6:
            return f"中等质量案例（置信度{confidence:.0%}），建议补充详细信息后保存"
        else:
            return f"低质量案例（置信度{confidence:.0%}），建议人工审核后再保存"

    def _generate_answer(self, question: str, cases: List[PresaleKnowledgeCase], context: Dict) -> str:
        """生成答案（模拟AI生成）"""
        if not cases:
            return "抱歉，在知识库中未找到相关案例。建议您详细描述问题或联系技术专家。"
        
        # 基于案例生成答案
        answer_parts = [f"根据知识库中的{len(cases)}个相关案例分析：\n"]
        
        for i, case in enumerate(cases[:3], 1):
            answer_parts.append(f"\n{i}. {case.case_name}")
            if case.technical_highlights:
                answer_parts.append(f"   技术要点：{case.technical_highlights[:100]}")
        
        answer_parts.append("\n\n综合建议：参考以上案例的技术方案和实施经验，结合您的具体需求进行方案设计。")
        
        return "".join(answer_parts)

    def _calculate_qa_confidence(self, cases: List[PresaleKnowledgeCase]) -> float:
        """计算问答置信度"""
        if not cases:
            return 0.0
        
        # 基于案例数量和质量计算
        case_count_factor = min(len(cases) / 5, 1.0)  # 最多5个案例
        avg_quality = sum(c.quality_score or 0.5 for c in cases) / len(cases)
        
        confidence = (case_count_factor * 0.5 + avg_quality * 0.5)
        return round(confidence, 2)
