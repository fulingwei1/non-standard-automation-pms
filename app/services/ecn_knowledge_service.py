# -*- coding: utf-8 -*-
"""
ECN知识库服务
提供解决方案提取、相似ECN匹配、智能推荐等功能
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import json
import re

from app.models.ecn import (
    Ecn, EcnAffectedMaterial, EcnSolutionTemplate, EcnBomImpact
)
from app.models.project import Project, Machine


class EcnKnowledgeService:
    """ECN知识库服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_solution(
        self,
        ecn_id: int,
        auto_extract: bool = True
    ) -> Dict[str, Any]:
        """
        从ECN中提取解决方案
        
        Args:
            ecn_id: ECN ID
            auto_extract: 是否自动提取（否则手动填写）
        
        Returns:
            提取结果
        """
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError(f"ECN {ecn_id} 不存在")
        
        if auto_extract:
            # 自动提取解决方案
            solution = self._auto_extract_solution(ecn)
        else:
            # 使用手动填写的解决方案
            solution = ecn.solution or ""
        
        # 提取关键词
        keywords = self._extract_keywords(ecn)
        
        # 构建解决方案描述
        solution_description = self._build_solution_description(ecn, solution)
        
        # 提取解决步骤
        solution_steps = self._extract_solution_steps(ecn, solution)
        
        # 估算成本和天数
        estimated_cost = float(ecn.cost_impact or 0)
        estimated_days = ecn.schedule_impact_days or 0
        
        return {
            "ecn_id": ecn_id,
            "solution": solution_description,
            "solution_steps": solution_steps,
            "keywords": keywords,
            "estimated_cost": estimated_cost,
            "estimated_days": estimated_days,
            "ecn_type": ecn.ecn_type,
            "root_cause_category": ecn.root_cause_category,
            "extracted_at": datetime.now().isoformat()
        }
    
    def find_similar_ecns(
        self,
        ecn_id: int,
        top_n: int = 5,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        查找相似的ECN
        
        Args:
            ecn_id: 当前ECN ID
            top_n: 返回数量
            min_similarity: 最小相似度阈值
        
        Returns:
            相似ECN列表
        """
        current_ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not current_ecn:
            raise ValueError(f"ECN {ecn_id} 不存在")
        
        # 获取所有已完成的ECN（排除当前ECN）
        completed_ecns = self.db.query(Ecn).filter(
            Ecn.id != ecn_id,
            Ecn.status.in_(['COMPLETED', 'CLOSED']),
            Ecn.solution.isnot(None),
            Ecn.solution != ''
        ).all()
        
        similar_ecns = []
        
        for ecn in completed_ecns:
            similarity_score = self._calculate_similarity(current_ecn, ecn)
            
            if similarity_score >= min_similarity:
                similar_ecns.append({
                    "ecn_id": ecn.id,
                    "ecn_no": ecn.ecn_no,
                    "ecn_title": ecn.ecn_title,
                    "ecn_type": ecn.ecn_type,
                    "similarity_score": similarity_score,
                    "solution": ecn.solution,
                    "root_cause_category": ecn.root_cause_category,
                    "cost_impact": float(ecn.cost_impact or 0),
                    "schedule_impact_days": ecn.schedule_impact_days or 0,
                    "completed_at": ecn.execution_end.isoformat() if ecn.execution_end else None,
                    "match_reasons": self._get_match_reasons(current_ecn, ecn, similarity_score)
                })
        
        # 按相似度排序
        similar_ecns.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_ecns[:top_n]
    
    def recommend_solutions(
        self,
        ecn_id: int,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        推荐解决方案模板
        
        Args:
            ecn_id: ECN ID
            top_n: 返回数量
        
        Returns:
            推荐方案列表
        """
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError(f"ECN {ecn_id} 不存在")
        
        # 获取所有活跃的解决方案模板
        templates = self.db.query(EcnSolutionTemplate).filter(
            EcnSolutionTemplate.is_active == True
        ).all()
        
        recommendations = []
        
        for template in templates:
            score = self._calculate_template_score(ecn, template)
            
            if score > 0:
                recommendations.append({
                    "template_id": template.id,
                    "template_code": template.template_code,
                    "template_name": template.template_name,
                    "template_category": template.template_category,
                    "solution_description": template.solution_description,
                    "solution_steps": template.solution_steps or [],
                    "score": score,
                    "success_rate": float(template.success_rate or 0),
                    "usage_count": template.usage_count or 0,
                    "estimated_cost": float(template.estimated_cost or 0),
                    "estimated_days": template.estimated_days or 0,
                    "match_reasons": self._get_template_match_reasons(ecn, template, score)
                })
        
        # 按评分排序
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return recommendations[:top_n]
    
    def create_solution_template(
        self,
        ecn_id: int,
        template_data: Dict[str, Any],
        created_by: int
    ) -> EcnSolutionTemplate:
        """
        从ECN创建解决方案模板
        
        Args:
            ecn_id: ECN ID
            template_data: 模板数据
            created_by: 创建人ID
        
        Returns:
            创建的模板
        """
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError(f"ECN {ecn_id} 不存在")
        
        # 生成模板编码
        template_code = self._generate_template_code(ecn)
        
        template = EcnSolutionTemplate(
            template_code=template_code,
            template_name=template_data.get('template_name', f"{ecn.ecn_title} - 解决方案模板"),
            template_category=template_data.get('template_category', ecn.ecn_type),
            ecn_type=ecn.ecn_type,
            root_cause_category=ecn.root_cause_category,
            keywords=template_data.get('keywords', self._extract_keywords(ecn)),
            solution_description=template_data.get('solution_description', ecn.solution or ''),
            solution_steps=template_data.get('solution_steps', []),
            required_resources=template_data.get('required_resources', []),
            estimated_cost=template_data.get('estimated_cost', ecn.cost_impact),
            estimated_days=template_data.get('estimated_days', ecn.schedule_impact_days),
            source_ecn_id=ecn_id,
            created_from='MANUAL',
            is_active=True,
            created_by=created_by
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def apply_solution_template(
        self,
        ecn_id: int,
        template_id: int
    ) -> Dict[str, Any]:
        """
        应用解决方案模板到ECN
        
        Args:
            ecn_id: ECN ID
            template_id: 模板ID
        
        Returns:
            应用结果
        """
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError(f"ECN {ecn_id} 不存在")
        
        template = self.db.query(EcnSolutionTemplate).filter(
            EcnSolutionTemplate.id == template_id
        ).first()
        
        if not template:
            raise ValueError(f"解决方案模板 {template_id} 不存在")
        
        # 应用解决方案
        ecn.solution = template.solution_description
        ecn.solution_template_id = template_id
        ecn.solution_source = 'KNOWLEDGE_BASE'
        
        # 更新模板使用次数
        template.usage_count = (template.usage_count or 0) + 1
        
        self.db.commit()
        
        return {
            "ecn_id": ecn_id,
            "template_id": template_id,
            "solution": template.solution_description,
            "solution_steps": template.solution_steps or [],
            "applied_at": datetime.now().isoformat()
        }
    
    def _auto_extract_solution(self, ecn: Ecn) -> str:
        """自动提取解决方案"""
        # 从执行说明中提取
        if ecn.execution_note:
            return ecn.execution_note
        
        # 从变更描述中提取
        if ecn.change_description:
            # 尝试提取解决方案部分
            solution_keywords = ['解决方案', '解决方法', '处理方式', '解决', '处理']
            for keyword in solution_keywords:
                if keyword in ecn.change_description:
                    # 提取包含关键词的段落
                    parts = ecn.change_description.split(keyword)
                    if len(parts) > 1:
                        return parts[1].strip()
        
        return ""
    
    def _extract_keywords(self, ecn: Ecn) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 从ECN类型
        if ecn.ecn_type:
            keywords.append(ecn.ecn_type)
        
        # 从根本原因分类
        if ecn.root_cause_category:
            keywords.append(ecn.root_cause_category)
        
        # 从变更描述中提取关键词
        if ecn.change_description:
            # 简单的关键词提取（可以后续优化为NLP）
            text = ecn.change_description.lower()
            common_keywords = ['物料', '设计', '工艺', '测试', '质量', '成本', '交期']
            for kw in common_keywords:
                if kw in text:
                    keywords.append(kw)
        
        # 从受影响物料中提取
        affected_materials = self.db.query(EcnAffectedMaterial).filter(
            EcnAffectedMaterial.ecn_id == ecn.id
        ).limit(5).all()
        
        for mat in affected_materials:
            if mat.material_name:
                # 提取物料名称中的关键词
                words = mat.material_name.split()
                keywords.extend(words[:2])  # 取前两个词
        
        # 去重并返回
        return list(set(keywords))[:10]
    
    def _build_solution_description(self, ecn: Ecn, solution: str) -> str:
        """构建解决方案描述"""
        if solution:
            return solution
        
        # 如果没有解决方案，根据ECN信息构建
        description_parts = []
        
        if ecn.change_description:
            description_parts.append(f"变更内容：{ecn.change_description}")
        
        if ecn.root_cause_analysis:
            description_parts.append(f"根本原因：{ecn.root_cause_analysis}")
        
        if ecn.execution_note:
            description_parts.append(f"执行说明：{ecn.execution_note}")
        
        return "\n".join(description_parts) if description_parts else "暂无解决方案描述"
    
    def _extract_solution_steps(self, ecn: Ecn, solution: str) -> List[str]:
        """提取解决步骤"""
        steps = []
        
        if solution:
            # 尝试从解决方案中提取步骤（按序号或换行）
            lines = solution.split('\n')
            for line in lines:
                line = line.strip()
                # 匹配序号格式：1. 2. 3. 或 一、 二、 三、
                if re.match(r'^[\d一二三四五六七八九十]+[\.、]', line):
                    steps.append(line)
                elif line.startswith('-') or line.startswith('•'):
                    steps.append(line)
        
        # 如果没有提取到步骤，从执行任务中提取
        if not steps:
            from app.models.ecn import EcnTask
            tasks = self.db.query(EcnTask).filter(
                EcnTask.ecn_id == ecn.id,
                EcnTask.status.in_(['COMPLETED', 'IN_PROGRESS'])
            ).order_by(EcnTask.planned_start).limit(10).all()
            
            for task in tasks:
                steps.append(f"{task.task_name}: {task.task_description or ''}")
        
        return steps[:10]  # 最多返回10个步骤
    
    def _calculate_similarity(self, ecn1: Ecn, ecn2: Ecn) -> float:
        """计算两个ECN的相似度"""
        score = 0.0
        max_score = 0.0
        
        # 1. ECN类型匹配（权重：30%）
        max_score += 30
        if ecn1.ecn_type == ecn2.ecn_type:
            score += 30
        
        # 2. 根本原因分类匹配（权重：25%）
        max_score += 25
        if ecn1.root_cause_category and ecn2.root_cause_category:
            if ecn1.root_cause_category == ecn2.root_cause_category:
                score += 25
        
        # 3. 变更描述相似度（权重：20%）
        max_score += 20
        if ecn1.change_description and ecn2.change_description:
            text_similarity = self._text_similarity(
                ecn1.change_description,
                ecn2.change_description
            )
            score += 20 * text_similarity
        
        # 4. 受影响物料相似度（权重：15%）
        max_score += 15
        material_similarity = self._material_similarity(ecn1.id, ecn2.id)
        score += 15 * material_similarity
        
        # 5. 成本影响相似度（权重：10%）
        max_score += 10
        cost_similarity = self._cost_similarity(
            float(ecn1.cost_impact or 0),
            float(ecn2.cost_impact or 0)
        )
        score += 10 * cost_similarity
        
        # 归一化到0-1
        return score / max_score if max_score > 0 else 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单的关键词匹配）"""
        if not text1 or not text2:
            return 0.0
        
        # 提取关键词
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard相似度
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _material_similarity(self, ecn_id1: int, ecn_id2: int) -> float:
        """计算受影响物料的相似度"""
        mats1 = self.db.query(EcnAffectedMaterial).filter(
            EcnAffectedMaterial.ecn_id == ecn_id1
        ).all()
        
        mats2 = self.db.query(EcnAffectedMaterial).filter(
            EcnAffectedMaterial.ecn_id == ecn_id2
        ).all()
        
        if not mats1 or not mats2:
            return 0.0
        
        # 物料编码匹配
        codes1 = {mat.material_code for mat in mats1}
        codes2 = {mat.material_code for mat in mats2}
        
        intersection = len(codes1 & codes2)
        union = len(codes1 | codes2)
        
        return intersection / union if union > 0 else 0.0
    
    def _cost_similarity(self, cost1: float, cost2: float) -> float:
        """计算成本相似度"""
        if cost1 == 0 and cost2 == 0:
            return 1.0
        
        if cost1 == 0 or cost2 == 0:
            return 0.0
        
        # 使用相对差异
        diff = abs(cost1 - cost2) / max(abs(cost1), abs(cost2))
        return 1.0 - min(diff, 1.0)
    
    def _get_match_reasons(self, ecn1: Ecn, ecn2: Ecn, similarity: float) -> List[str]:
        """获取匹配原因"""
        reasons = []
        
        if ecn1.ecn_type == ecn2.ecn_type:
            reasons.append(f"相同ECN类型：{ecn1.ecn_type}")
        
        if ecn1.root_cause_category and ecn2.root_cause_category:
            if ecn1.root_cause_category == ecn2.root_cause_category:
                reasons.append(f"相同根本原因分类：{ecn1.root_cause_category}")
        
        if similarity > 0.7:
            reasons.append("高度相似")
        elif similarity > 0.5:
            reasons.append("中等相似")
        else:
            reasons.append("部分相似")
        
        return reasons
    
    def _calculate_template_score(self, ecn: Ecn, template: EcnSolutionTemplate) -> float:
        """计算模板推荐评分"""
        score = 0.0
        
        # 1. ECN类型匹配（30分）
        if ecn.ecn_type == template.ecn_type:
            score += 30.0
        
        # 2. 根本原因分类匹配（25分）
        if ecn.root_cause_category and template.root_cause_category:
            if ecn.root_cause_category == template.root_cause_category:
                score += 25.0
        
        # 3. 关键词匹配（20分）
        if template.keywords:
            ecn_keywords = set(self._extract_keywords(ecn))
            template_keywords = set(template.keywords)
            if ecn_keywords & template_keywords:
                match_ratio = len(ecn_keywords & template_keywords) / len(template_keywords)
                score += 20.0 * match_ratio
        
        # 4. 成功率（15分）
        success_rate = float(template.success_rate or 0)
        score += 15.0 * (success_rate / 100.0)
        
        # 5. 使用频率（10分）
        usage_count = template.usage_count or 0
        if usage_count > 0:
            import math
            usage_score = min(10.0, math.log10(usage_count + 1) * 3)
            score += usage_score
        
        return round(score, 2)
    
    def _get_template_match_reasons(self, ecn: Ecn, template: EcnSolutionTemplate, score: float) -> List[str]:
        """获取模板匹配原因"""
        reasons = []
        
        if ecn.ecn_type == template.ecn_type:
            reasons.append(f"匹配ECN类型：{ecn.ecn_type}")
        
        if ecn.root_cause_category and template.root_cause_category:
            if ecn.root_cause_category == template.root_cause_category:
                reasons.append(f"匹配根本原因分类：{ecn.root_cause_category}")
        
        if template.success_rate and template.success_rate > 80:
            reasons.append(f"高成功率：{template.success_rate}%")
        
        if template.usage_count and template.usage_count > 5:
            reasons.append(f"常用方案：已使用{template.usage_count}次")
        
        return reasons
    
    def _generate_template_code(self, ecn: Ecn) -> str:
        """生成模板编码"""
        timestamp = datetime.now().strftime('%Y%m%d')
        return f"ECN-SOL-{timestamp}-{ecn.id:04d}"
