# -*- coding: utf-8 -*-
"""
AI 智能优化分析服务

分析哪些环节可以节省时间，自动复用历史项目内容
"""

from typing import Any, Dict, List, Optional
from datetime import date, timedelta
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.project import Project
from app.models.material import BomHeader, BomItem
from app.models.purchase import PurchaseOrder, PurchaseOrderItem


class ScheduleOptimizationService:
    """AI 智能优化分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_optimization_potential(self, project_id: int) -> Dict[str, Any]:
        """
        分析项目优化潜力
        
        返回：
        - 可节省时间的环节
        - 可复用的模块/内容
        - 自动化建议
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {'error': '项目不存在'}
        
        # 1. 查找相似历史项目
        similar_projects = self._find_similar_projects(project)
        
        # 2. 分析各环节优化潜力
        optimization_analysis = self._analyze_phases_optimization(project, similar_projects)
        
        # 3. 识别可复用内容
        reusable_content = self._identify_reusable_content(project, similar_projects)
        
        # 4. 生成自动化建议
        automation_suggestions = self._generate_automation_suggestions(
            project, optimization_analysis, reusable_content
        )
        
        # 5. 计算可节省时间
        time_savings = self._calculate_time_savings(optimization_analysis)
        
        return {
            'project_id': project_id,
            'project_name': project.project_name,
            'similar_projects_count': len(similar_projects),
            'optimization_analysis': optimization_analysis,
            'reusable_content': reusable_content,
            'automation_suggestions': automation_suggestions,
            'time_savings': time_savings,
            'overall_optimization_score': self._calculate_optimization_score(
                optimization_analysis, reusable_content
            ),
        }
    
    def _find_similar_projects(self, project: Project) -> List[Project]:
        """查找相似历史项目"""
        
        similar = self.db.query(Project)\
            .filter(
                Project.product_category == project.product_category,
                Project.industry == project.industry,
                Project.id != project.id,
                Project.status.in_(['COMPLETED', 'DELIVERED']),
            )\
            .order_by(Project.created_at.desc())\
            .limit(5)\
            .all()
        
        return similar
    
    def _analyze_phases_optimization(
        self,
        project: Project,
        similar_projects: List[Project],
    ) -> Dict[str, Any]:
        """分析各环节优化潜力"""
        
        phases_analysis = {
            'engineering': self._analyze_engineering_optimization(project, similar_projects),
            'procurement': self._analyze_procurement_optimization(project, similar_projects),
            'production': self._analyze_production_optimization(project, similar_projects),
            'shipping': self._analyze_shipping_optimization(project, similar_projects),
            'acceptance': self._analyze_acceptance_optimization(project, similar_projects),
        }
        
        return phases_analysis
    
    def _analyze_engineering_optimization(
        self,
        project: Project,
        similar_projects: List[Project],
    ) -> Dict[str, Any]:
        """分析工程技术部优化潜力"""
        
        optimizations = []
        reusable_items = []
        
        # 1. 检查是否有相似设计方案
        if similar_projects:
            optimizations.append({
                'type': 'DESIGN_REUSE',
                'title': '设计方案复用',
                'description': f'发现{len(similar_projects)}个相似项目，可复用其设计方案',
                'potential_savings_days': 3,
                'confidence': 'HIGH' if len(similar_projects) >= 3 else 'MEDIUM',
                'action': '自动加载相似项目的设计文档和 BOM 清单',
            })
            
            # 可复用的设计模块
            reusable_items.append({
                'category': '设计文档',
                'items': ['技术方案模板', '设计规范', '评审检查表'],
                'reuse_rate': 80,
            })
        
        # 2. 标准化模块检查
        optimizations.append({
            'type': 'STANDARD_MODULES',
            'title': '标准化模块应用',
            'description': '使用标准化设计模块，减少重复设计工作',
            'potential_savings_days': 2,
            'confidence': 'MEDIUM',
            'action': '应用公司标准模块库',
        })
        
        # 3. AI 辅助设计
        optimizations.append({
            'type': 'AI_ASSISTED_DESIGN',
            'title': 'AI 辅助设计',
            'description': '使用 AI 生成初步设计方案和 BOM 清单',
            'potential_savings_days': 2,
            'confidence': 'MEDIUM',
            'action': '启用 AI 设计助手',
        })
        
        return {
            'phase': 'engineering',
            'phase_name': '工程技术部',
            'current_duration': 15,
            'optimizable_duration': 8,
            'potential_savings': 7,
            'optimizations': optimizations,
            'reusable_items': reusable_items,
        }
    
    def _analyze_procurement_optimization(
        self,
        project: Project,
        similar_projects: List[Project],
    ) -> Dict[str, Any]:
        """分析采购优化潜力"""
        
        optimizations = []
        reusable_items = []
        
        # 1. 相似物料采购
        if similar_projects:
            optimizations.append({
                'type': 'SIMILAR_MATERIALS',
                'title': '相似物料自动采购',
                'description': '基于历史项目 BOM，自动生成采购清单',
                'potential_savings_days': 2,
                'confidence': 'HIGH',
                'action': '自动加载相似项目 BOM 并生成采购申请',
            })
            
            reusable_items.append({
                'category': '采购清单',
                'items': ['标准件清单', '常用供应商列表', '历史价格参考'],
                'reuse_rate': 70,
            })
        
        # 2. 框架协议物料
        optimizations.append({
            'type': 'FRAMEWORK_AGREEMENT',
            'title': '框架协议物料',
            'description': '使用框架协议供应商，缩短询价时间',
            'potential_savings_days': 2,
            'confidence': 'MEDIUM',
            'action': '优先选择框架协议供应商',
        })
        
        # 3. 自动询价
        optimizations.append({
            'type': 'AUTO_RFQ',
            'title': '自动询价',
            'description': '向供应商自动发送询价单',
            'potential_savings_days': 1,
            'confidence': 'MEDIUM',
            'action': '启用自动询价系统',
        })
        
        return {
            'phase': 'procurement',
            'phase_name': '采购',
            'current_duration': 12,
            'optimizable_duration': 7,
            'potential_savings': 5,
            'optimizations': optimizations,
            'reusable_items': reusable_items,
        }
    
    def _analyze_production_optimization(
        self,
        project: Project,
        similar_projects: List[Project],
    ) -> Dict[str, Any]:
        """分析生产优化潜力"""
        
        optimizations = []
        
        # 1. 标准装配流程
        optimizations.append({
            'type': 'STANDARD_ASSEMBLY',
            'title': '标准装配流程',
            'description': '使用标准装配工艺，减少调试时间',
            'potential_savings_days': 2,
            'confidence': 'MEDIUM',
            'action': '应用标准装配工艺卡',
        })
        
        # 2. 并行作业
        optimizations.append({
            'type': 'PARALLEL_WORK',
            'title': '并行作业',
            'description': '机械和电气装配并行进行',
            'potential_savings_days': 3,
            'confidence': 'HIGH',
            'action': '安排两个装配组同时作业',
        })
        
        # 3. 预调试
        optimizations.append({
            'type': 'PRE_DEBUGGING',
            'title': '模块预调试',
            'description': '装配过程中进行模块预调试',
            'potential_savings_days': 2,
            'confidence': 'MEDIUM',
            'action': '实施边装配边调试策略',
        })
        
        return {
            'phase': 'production',
            'phase_name': '生产',
            'current_duration': 18,
            'optimizable_duration': 11,
            'potential_savings': 7,
            'optimizations': optimizations,
            'reusable_items': [],
        }
    
    def _analyze_shipping_optimization(
        self,
        project: Project,
        similar_projects: List[Project],
    ) -> Dict[str, Any]:
        """分析发货优化潜力"""
        
        optimizations = []
        
        # 1. 标准包装方案
        optimizations.append({
            'type': 'STANDARD_PACKING',
            'title': '标准包装方案',
            'description': '使用标准包装方案，减少包装时间',
            'potential_savings_days': 1,
            'confidence': 'MEDIUM',
            'action': '应用标准包装设计',
        })
        
        # 2. 物流预约
        optimizations.append({
            'type': 'LOGISTICS_BOOKING',
            'title': '物流提前预约',
            'description': '提前预约物流车辆，避免等待',
            'potential_savings_days': 1,
            'confidence': 'HIGH',
            'action': '提前 3 天预约物流',
        })
        
        return {
            'phase': 'shipping',
            'phase_name': '发货',
            'current_duration': 6,
            'optimizable_duration': 4,
            'potential_savings': 2,
            'optimizations': optimizations,
            'reusable_items': [],
        }
    
    def _analyze_acceptance_optimization(
        self,
        project: Project,
        similar_projects: List[Project],
    ) -> Dict[str, Any]:
        """分析验收优化潜力"""
        
        optimizations = []
        reusable_items = []
        
        # 1. 标准验收文档
        if similar_projects:
            optimizations.append({
                'type': 'STANDARD_DOCUMENTS',
                'title': '标准验收文档',
                'description': '复用相似项目的验收文档模板',
                'potential_savings_days': 1,
                'confidence': 'HIGH',
                'action': '自动加载验收文档模板',
            })
            
            reusable_items.append({
                'category': '验收文档',
                'items': ['FAT 测试大纲', 'SAT 测试大纲', '培训材料', '验收报告模板'],
                'reuse_rate': 85,
            })
        
        # 2. 远程预验收
        optimizations.append({
            'type': 'REMOTE_PREACCEPTANCE',
            'title': '远程预验收',
            'description': '通过视频进行预验收，减少现场时间',
            'potential_savings_days': 1,
            'confidence': 'MEDIUM',
            'action': '安排远程预验收会议',
        })
        
        # 3. 标准化调试流程
        optimizations.append({
            'type': 'STANDARD_DEBUGGING',
            'title': '标准化调试流程',
            'description': '使用标准化调试检查表',
            'potential_savings_days': 1,
            'confidence': 'MEDIUM',
            'action': '应用标准调试流程',
        })
        
        return {
            'phase': 'acceptance',
            'phase_name': '验收',
            'current_duration': 9,
            'optimizable_duration': 6,
            'potential_savings': 3,
            'optimizations': optimizations,
            'reusable_items': reusable_items,
        }
    
    def _identify_reusable_content(
        self,
        project: Project,
        similar_projects: List[Project],
    ) -> Dict[str, Any]:
        """识别可复用内容"""
        
        reusable = {
            'design_documents': [],
            'bom_templates': [],
            'procurement_lists': [],
            'test_procedures': [],
            'documentation': [],
        }
        
        for sp in similar_projects[:3]:  # 只看前 3 个最相似的
            # 设计文档
            reusable['design_documents'].append({
                'project_name': sp.project_name,
                'similarity': 'HIGH' if sp.product_category == project.product_category else 'MEDIUM',
                'items': ['技术方案', '设计图纸', 'BOM 清单'],
            })
            
            # 采购清单
            reusable['procurement_lists'].append({
                'project_name': sp.project_name,
                'reuse_rate': 70,
                'items': ['标准件', '通用物料'],
            })
        
        return reusable
    
    def _generate_automation_suggestions(
        self,
        project: Project,
        optimization_analysis: Dict,
        reusable_content: Dict,
    ) -> List[Dict[str, Any]]:
        """生成自动化建议"""
        
        suggestions = []
        
        # 1. BOM 自动生成
        suggestions.append({
            'type': 'AUTO_BOM',
            'title': 'BOM 自动生成',
            'description': '基于相似项目自动生成 BOM 清单',
            'impact': 'HIGH',
            'effort': 'LOW',
            'savings_days': 2,
            'action': '点击"自动生成 BOM"按钮',
        })
        
        # 2. 采购申请自动创建
        suggestions.append({
            'type': 'AUTO_PURCHASE_REQUEST',
            'title': '采购申请自动创建',
            'description': '基于 BOM 自动生成采购申请',
            'impact': 'MEDIUM',
            'effort': 'LOW',
            'savings_days': 1,
            'action': '启用自动采购申请',
        })
        
        # 3. 文档模板自动填充
        suggestions.append({
            'type': 'AUTO_DOCUMENTATION',
            'title': '文档模板自动填充',
            'description': '自动填充标准文档模板',
            'impact': 'MEDIUM',
            'effort': 'LOW',
            'savings_days': 1,
            'action': '使用文档自动生成',
        })
        
        return suggestions
    
    def _calculate_time_savings(self, optimization_analysis: Dict) -> Dict[str, Any]:
        """计算可节省时间"""
        
        total_savings = sum(
            phase.get('potential_savings', 0)
            for phase in optimization_analysis.values()
        )
        
        total_current = sum(
            phase.get('current_duration', 0)
            for phase in optimization_analysis.values()
        )
        
        return {
            'total_current_days': total_current,
            'total_optimizable_days': total_current - total_savings,
            'total_savings_days': total_savings,
            'savings_percentage': round(total_savings / total_current * 100, 1) if total_current > 0 else 0,
            'by_phase': {
                phase: data.get('potential_savings', 0)
                for phase, data in optimization_analysis.items()
            },
        }
    
    def _calculate_optimization_score(
        self,
        optimization_analysis: Dict,
        reusable_content: Dict,
    ) -> float:
        """计算优化潜力评分"""
        
        # 基于可节省时间和可复用内容计算
        total_savings = sum(
            phase.get('potential_savings', 0)
            for phase in optimization_analysis.values()
        )
        
        total_current = sum(
            phase.get('current_duration', 0)
            for phase in optimization_analysis.values()
        )
        
        # 可复用内容加分
        reusable_bonus = len(reusable_content.get('design_documents', [])) * 2
        reusable_bonus += len(reusable_content.get('procurement_lists', [])) * 1.5
        
        base_score = (total_savings / total_current * 100) if total_current > 0 else 0
        
        return min(100, base_score + reusable_bonus)
