"""
售前AI方案生成服务
Presale AI Solution Generation Service
"""
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models.presale_ai_solution import (
    PresaleAISolution,
    PresaleSolutionTemplate,
    PresaleAIGenerationLog
)
from app.schemas.presale_ai_solution import (
    TemplateMatchRequest,
    SolutionGenerationRequest,
    ArchitectureGenerationRequest,
    BOMGenerationRequest,
    TemplateMatchItem,
    BOMItem
)
from app.services.ai_client_service import AIClientService


class PresaleAIService:
    """售前AI方案生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_client = AIClientService()
    
    # ==================== 模板匹配 ====================
    
    def match_templates(
        self, 
        request: TemplateMatchRequest,
        user_id: int
    ) -> Tuple[List[TemplateMatchItem], int]:
        """
        智能模板匹配
        1. 基于行业和设备类型过滤
        2. 使用TF-IDF进行关键词匹配
        3. 返回TOP K个最佳模板
        """
        start_time = time.time()
        
        # 构建查询
        query = self.db.query(PresaleSolutionTemplate).filter(
            PresaleSolutionTemplate.is_active == 1
        )
        
        # 过滤条件
        if request.industry:
            query = query.filter(PresaleSolutionTemplate.industry == request.industry)
        
        if request.equipment_type:
            query = query.filter(PresaleSolutionTemplate.equipment_type == request.equipment_type)
        
        # 获取候选模板
        templates = query.all()
        
        # 关键词相似度计算
        if request.keywords:
            scored_templates = []
            for template in templates:
                score = self._calculate_similarity(request.keywords, template.keywords or "")
                scored_templates.append((template, score))
            
            # 按相似度排序
            scored_templates.sort(key=lambda x: x[1], reverse=True)
            top_templates = scored_templates[:request.top_k]
        else:
            # 按使用次数排序
            templates = sorted(templates, key=lambda x: x.usage_count or 0, reverse=True)
            top_templates = [(t, 0.0) for t in templates[:request.top_k]]
        
        # 构建响应
        matched_items = []
        for template, score in top_templates:
            matched_items.append(TemplateMatchItem(
                template_id=template.id,
                template_name=template.name,
                similarity_score=score if score > 0 else 0.5,  # 默认0.5
                industry=template.industry,
                equipment_type=template.equipment_type,
                usage_count=template.usage_count or 0,
                avg_quality_score=float(template.avg_quality_score) if template.avg_quality_score else None
            ))
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        return matched_items, search_time_ms
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """简单的TF-IDF相似度计算"""
        # 分词
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Jaccard相似度
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    # ==================== 方案生成 ====================
    
    def generate_solution(
        self,
        request: SolutionGenerationRequest,
        user_id: int
    ) -> Dict[str, Any]:
        """
        AI智能方案生成
        1. 分析需求
        2. 匹配模板
        3. 生成方案描述
        4. 生成架构图 (可选)
        5. 生成BOM清单 (可选)
        """
        start_time = time.time()
        
        # 1. 获取参考模板
        template = None
        matched_template_ids = []
        if request.template_id:
            template = self.db.query(PresaleSolutionTemplate).filter_by(id=request.template_id).first()
            matched_template_ids = [request.template_id]
        
        # 2. 构建AI提示词
        prompt = self._build_solution_prompt(request.requirements, template)
        
        # 3. 调用AI生成方案
        ai_response = self.ai_client.generate_solution(
            prompt=prompt,
            model=request.ai_model
        )
        
        # 4. 解析AI响应
        solution_content = self._parse_solution_response(ai_response)
        
        # 5. 生成架构图 (可选)
        architecture_diagram = None
        if request.generate_architecture:
            arch_response = self.generate_architecture(
                requirements=request.requirements,
                diagram_type="architecture"
            )
            architecture_diagram = arch_response.get("diagram_code")
        
        # 6. 生成BOM (可选)
        bom_list = None
        estimated_cost = None
        if request.generate_bom and "equipment_list" in solution_content:
            bom_response = self.generate_bom(
                equipment_list=solution_content["equipment_list"],
                include_cost=True
            )
            bom_list = bom_response.get("bom_items")
            estimated_cost = bom_response.get("total_cost")
        
        # 7. 计算置信度评分
        confidence_score = self._calculate_confidence(solution_content, template)
        
        # 8. 保存到数据库
        generation_time = time.time() - start_time
        
        ai_solution = PresaleAISolution(
            presale_ticket_id=request.presale_ticket_id,
            requirement_analysis_id=request.requirement_analysis_id,
            matched_template_ids=matched_template_ids,
            generated_solution=solution_content,
            architecture_diagram=architecture_diagram,
            bom_list=bom_list,
            solution_description=solution_content.get("description"),
            technical_parameters=solution_content.get("technical_parameters"),
            process_flow=solution_content.get("process_flow"),
            confidence_score=Decimal(str(confidence_score)),
            estimated_cost=Decimal(str(estimated_cost)) if estimated_cost else None,
            ai_model_used=request.ai_model,
            generation_time_seconds=Decimal(str(round(generation_time, 2))),
            prompt_tokens=ai_response.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=ai_response.get("usage", {}).get("completion_tokens", 0),
            status="draft",
            created_by=user_id
        )
        
        self.db.add(ai_solution)
        self.db.commit()
        self.db.refresh(ai_solution)
        
        # 9. 记录生成日志
        self._log_generation(
            solution_id=ai_solution.id,
            request_type="solution",
            input_data=request.model_dump(),
            output_data=solution_content,
            success=True,
            response_time_ms=int(generation_time * 1000),
            ai_model=request.ai_model,
            tokens_used=ai_response.get("usage", {}).get("total_tokens", 0)
        )
        
        return {
            "solution_id": ai_solution.id,
            "solution": solution_content,
            "architecture_diagram": architecture_diagram,
            "bom_list": bom_list,
            "confidence_score": float(confidence_score),
            "generation_time_seconds": generation_time,
            "ai_model_used": request.ai_model,
            "tokens_used": ai_response.get("usage", {}).get("total_tokens", 0)
        }
    
    def _build_solution_prompt(self, requirements: Dict[str, Any], template: Optional[PresaleSolutionTemplate]) -> str:
        """构建方案生成提示词"""
        prompt = f"""作为非标自动化方案专家，请基于以下需求生成技术方案：

需求信息：
{json.dumps(requirements, ensure_ascii=False, indent=2)}

"""
        if template:
            prompt += f"""
参考模板：
模板名称：{template.name}
行业：{template.industry}
设备类型：{template.equipment_type}
模板内容：
{json.dumps(template.solution_content, ensure_ascii=False, indent=2)}
"""
        
        prompt += """
请生成包含以下内容的完整技术方案（以JSON格式返回）：
1. description: 方案总体描述
2. technical_parameters: 技术参数表
3. equipment_list: 设备清单（包含型号、数量、功能说明）
4. process_flow: 工艺流程说明
5. key_features: 关键特性列表
6. technical_advantages: 技术优势

请确保方案专业、详细、可实施。
"""
        return prompt
    
    def _parse_solution_response(self, ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """解析AI响应"""
        try:
            content = ai_response.get("content", "")
            
            # 尝试从Markdown代码块中提取JSON
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
                return json.loads(json_str)
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                json_str = content[start:end].strip()
                return json.loads(json_str)
            else:
                # 直接解析
                return json.loads(content)
        except Exception as e:
            # 解析失败，返回基本结构
            return {
                "description": ai_response.get("content", ""),
                "technical_parameters": {},
                "equipment_list": [],
                "process_flow": "",
                "key_features": [],
                "technical_advantages": []
            }
    
    def _calculate_confidence(self, solution: Dict[str, Any], template: Optional[PresaleSolutionTemplate]) -> float:
        """计算方案置信度"""
        score = 0.5  # 基础分
        
        # 有模板参考 +0.2
        if template:
            score += 0.2
        
        # 设备清单完整 +0.15
        if solution.get("equipment_list") and len(solution["equipment_list"]) > 0:
            score += 0.15
        
        # 技术参数完整 +0.1
        if solution.get("technical_parameters") and len(solution["technical_parameters"]) > 0:
            score += 0.1
        
        # 工艺流程完整 +0.05
        if solution.get("process_flow"):
            score += 0.05
        
        return min(score, 1.0)
    
    # ==================== 架构图生成 ====================
    
    def generate_architecture(
        self,
        requirements: Dict[str, Any],
        diagram_type: str = "architecture",
        solution_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成系统架构图 (Mermaid格式)
        """
        start_time = time.time()
        
        # 构建提示词
        prompt = self._build_architecture_prompt(requirements, diagram_type)
        
        # 调用AI生成
        ai_response = self.ai_client.generate_architecture(prompt)
        
        # 提取Mermaid代码
        mermaid_code = self._extract_mermaid_code(ai_response.get("content", ""))
        
        # 如果有solution_id，更新数据库
        if solution_id:
            solution = self.db.query(PresaleAISolution).filter_by(id=solution_id).first()
            if solution:
                if diagram_type == "architecture":
                    solution.architecture_diagram = mermaid_code
                elif diagram_type == "topology":
                    solution.topology_diagram = mermaid_code
                elif diagram_type == "signal_flow":
                    solution.signal_flow_diagram = mermaid_code
                
                self.db.commit()
        
        generation_time = time.time() - start_time
        
        return {
            "diagram_code": mermaid_code,
            "diagram_type": diagram_type,
            "format": "mermaid",
            "generation_time_seconds": generation_time
        }
    
    def _build_architecture_prompt(self, requirements: Dict[str, Any], diagram_type: str) -> str:
        """构建架构图生成提示词"""
        diagram_names = {
            "architecture": "系统架构图",
            "topology": "设备拓扑图",
            "signal_flow": "信号流程图"
        }
        
        prompt = f"""请基于以下需求生成{diagram_names.get(diagram_type, '系统架构图')}的Mermaid代码：

需求信息：
{json.dumps(requirements, ensure_ascii=False, indent=2)}

要求：
1. 使用Mermaid语法
2. 图表清晰易懂
3. 包含关键设备和连接关系
4. 标注重要参数

请直接返回Mermaid代码，用```mermaid包裹。
"""
        return prompt
    
    def _extract_mermaid_code(self, content: str) -> str:
        """提取Mermaid代码"""
        if "```mermaid" in content:
            start = content.find("```mermaid") + 10
            end = content.find("```", start)
            return content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            return content[start:end].strip()
        else:
            return content.strip()
    
    # ==================== BOM生成 ====================
    
    def generate_bom(
        self,
        equipment_list: List[Dict[str, Any]],
        include_cost: bool = True,
        include_suppliers: bool = True,
        solution_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        生成BOM清单
        """
        start_time = time.time()
        
        bom_items = []
        total_cost = Decimal("0")
        
        for equipment in equipment_list:
            # 调用AI匹配型号和价格
            bom_item = self._generate_bom_item(
                equipment,
                include_cost=include_cost,
                include_suppliers=include_suppliers
            )
            
            bom_items.append(bom_item)
            
            if bom_item.get("total_price"):
                total_cost += Decimal(str(bom_item["total_price"]))
        
        # 保存到数据库
        if solution_id:
            solution = self.db.query(PresaleAISolution).filter_by(id=solution_id).first()
            if solution:
                solution.bom_list = {"items": bom_items, "total_cost": float(total_cost)}
                solution.estimated_cost = total_cost
                self.db.commit()
        
        generation_time = time.time() - start_time
        
        return {
            "bom_items": bom_items,
            "total_cost": total_cost,
            "item_count": len(bom_items),
            "generation_time_seconds": generation_time
        }
    
    def _generate_bom_item(
        self,
        equipment: Dict[str, Any],
        include_cost: bool,
        include_suppliers: bool
    ) -> Dict[str, Any]:
        """生成单个BOM项"""
        # 基础信息
        item = {
            "item_name": equipment.get("name", "未命名设备"),
            "model": equipment.get("model", "待定型号"),
            "quantity": equipment.get("quantity", 1),
            "unit": equipment.get("unit", "台"),
            "notes": equipment.get("notes", "")
        }
        
        # 成本估算 (这里使用模拟数据，实际应调用AI或数据库)
        if include_cost:
            # TODO: 调用AI或价格数据库
            item["unit_price"] = 10000.00  # 模拟价格
            item["total_price"] = item["unit_price"] * item["quantity"]
        
        # 供应商推荐
        if include_suppliers:
            # TODO: 调用供应商数据库
            item["supplier"] = "推荐供应商A"
            item["lead_time_days"] = 30
        
        return item
    
    # ==================== 日志记录 ====================
    
    def _log_generation(
        self,
        solution_id: Optional[int],
        request_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        success: bool,
        response_time_ms: int,
        ai_model: str,
        tokens_used: int
    ):
        """记录AI生成日志"""
        log = PresaleAIGenerationLog(
            solution_id=solution_id,
            request_type=request_type,
            input_data=input_data,
            output_data=output_data,
            success=1 if success else 0,
            response_time_ms=response_time_ms,
            ai_model=ai_model,
            tokens_used=tokens_used
        )
        
        self.db.add(log)
        self.db.commit()
    
    # ==================== 查询和更新 ====================
    
    def get_solution(self, solution_id: int) -> Optional[PresaleAISolution]:
        """获取方案"""
        return self.db.query(PresaleAISolution).filter_by(id=solution_id).first()
    
    def update_solution(
        self,
        solution_id: int,
        update_data: Dict[str, Any]
    ) -> PresaleAISolution:
        """更新方案"""
        solution = self.get_solution(solution_id)
        if not solution:
            raise ValueError(f"Solution {solution_id} not found")
        
        for key, value in update_data.items():
            if hasattr(solution, key) and value is not None:
                setattr(solution, key, value)
        
        solution.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(solution)
        
        return solution
    
    def review_solution(
        self,
        solution_id: int,
        reviewer_id: int,
        status: str,
        comments: Optional[str] = None
    ) -> PresaleAISolution:
        """审核方案"""
        solution = self.get_solution(solution_id)
        if not solution:
            raise ValueError(f"Solution {solution_id} not found")
        
        solution.status = status
        solution.reviewed_by = reviewer_id
        solution.reviewed_at = datetime.utcnow()
        solution.review_comments = comments
        
        self.db.commit()
        self.db.refresh(solution)
        
        return solution
    
    # ==================== 模板管理 ====================
    
    def get_template_library(
        self,
        industry: Optional[str] = None,
        equipment_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[PresaleSolutionTemplate]:
        """获取模板库"""
        query = self.db.query(PresaleSolutionTemplate)
        
        if is_active:
            query = query.filter(PresaleSolutionTemplate.is_active == 1)
        
        if industry:
            query = query.filter(PresaleSolutionTemplate.industry == industry)
        
        if equipment_type:
            query = query.filter(PresaleSolutionTemplate.equipment_type == equipment_type)
        
        return query.order_by(desc(PresaleSolutionTemplate.usage_count)).all()
