# -*- coding: utf-8 -*-
"""
解决方案库服务
支持解决方案模板的创建、查询、复用
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.issue import Issue, SolutionTemplate
from app.models.project import Project


class ProjectSolutionService:
    """项目解决方案服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_project_solutions(
        self,
        project_id: int,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取项目已解决的问题及解决方案
        
        Args:
            project_id: 项目ID
            status: 问题状态（默认只返回已解决的）
            issue_type: 问题类型（可选）
            category: 问题分类（可选）
            
        Returns:
            解决方案列表，包含问题信息和解决方案
        """
        query = self.db.query(Issue).filter(
            Issue.project_id == project_id,
            Issue.solution.isnot(None),
            Issue.solution != ''
        )
        
        if status:
            query = query.filter(Issue.status == status)
        else:
            # 默认只返回已解决或已关闭的
            query = query.filter(
                Issue.status.in_(['RESOLVED', 'CLOSED', 'VERIFIED'])
            )
        
        if issue_type:
            query = query.filter(Issue.issue_type == issue_type)
        
        if category:
            query = query.filter(Issue.category == category)
        
        issues = query.order_by(Issue.resolved_at.desc()).all()
        
        solutions = []
        for issue in issues:
            solutions.append({
                'issue_id': issue.id,
                'issue_no': issue.issue_no,
                'title': issue.title,
                'issue_type': issue.issue_type,
                'category': issue.category,
                'severity': issue.severity,
                'solution': issue.solution,
                'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None,
                'resolved_by': issue.resolved_by_name,
                'tags': issue.tags if isinstance(issue.tags, list) else []
            })
        
        return solutions
    
    def get_solution_templates(
        self,
        issue_type: Optional[str] = None,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        is_active: bool = True,
        keyword: Optional[str] = None
    ) -> List[SolutionTemplate]:
        """
        获取解决方案模板列表
        
        Args:
            issue_type: 问题类型（可选）
            category: 问题分类（可选）
            is_public: 是否公开（可选）
            is_active: 是否启用（默认True）
            keyword: 关键词搜索（可选）
            
        Returns:
            解决方案模板列表
        """
        query = self.db.query(SolutionTemplate)
        
        if is_active:
            query = query.filter(SolutionTemplate.is_active == True)
        
        if issue_type:
            query = query.filter(SolutionTemplate.issue_type == issue_type)
        
        if category:
            query = query.filter(SolutionTemplate.category == category)
        
        if is_public is not None:
            query = query.filter(SolutionTemplate.is_public == is_public)
        
        if keyword:
            query = query.filter(
                or_(
                    SolutionTemplate.template_name.contains(keyword),
                    SolutionTemplate.solution.contains(keyword)
                )
            )
        
        return query.order_by(
            SolutionTemplate.usage_count.desc(),
            SolutionTemplate.created_at.desc()
        ).all()
    
    def create_solution_template_from_issue(
        self,
        issue_id: int,
        template_name: str,
        template_code: Optional[str] = None,
        is_public: bool = True,
        created_by: int = None
    ) -> Optional[SolutionTemplate]:
        """
        从已解决的问题创建解决方案模板
        
        Args:
            issue_id: 问题ID
            template_name: 模板名称
            template_code: 模板编码（可选，自动生成）
            is_public: 是否公开
            created_by: 创建人ID
            
        Returns:
            创建的模板对象
        """
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue or not issue.solution:
            return None
        
        # 生成模板编码
        if not template_code:
            from datetime import datetime
            template_code = f'ST{datetime.now().strftime("%y%m%d%H%M%S")}'
        
        template = SolutionTemplate(
            template_name=template_name,
            template_code=template_code,
            issue_type=issue.issue_type,
            category=issue.category,
            severity=issue.severity,
            solution=issue.solution,
            tags=issue.tags if isinstance(issue.tags, list) else [],
            source_issue_id=issue_id,
            created_by=created_by,
            is_public=is_public,
            is_active=True
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def apply_solution_template(
        self,
        template_id: int,
        issue_id: int,
        user_id: int
    ) -> bool:
        """
        应用解决方案模板到问题
        
        Args:
            template_id: 模板ID
            issue_id: 问题ID
            user_id: 操作用户ID
            
        Returns:
            是否成功
        """
        template = self.db.query(SolutionTemplate).filter(
            SolutionTemplate.id == template_id
        ).first()
        
        issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
        
        if not template or not issue:
            return False
        
        # 应用解决方案
        issue.solution = template.solution
        
        # 增加模板使用次数
        template.usage_count = (template.usage_count or 0) + 1
        
        self.db.commit()
        return True
    
    def get_project_solution_statistics(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取项目解决方案统计信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            统计信息字典
        """
        # 获取所有项目问题
        all_issues = self.db.query(Issue).filter(
            Issue.project_id == project_id
        ).all()
        
        total_issues = len(all_issues)
        resolved_issues = len([
            i for i in all_issues 
            if i.status in ['RESOLVED', 'CLOSED', 'VERIFIED']
        ])
        issues_with_solution = len([
            i for i in all_issues 
            if i.solution and i.solution.strip()
        ])
        
        # 按类型统计
        by_type = {}
        by_category = {}
        
        for issue in all_issues:
            # 按类型
            issue_type = issue.issue_type
            if issue_type not in by_type:
                by_type[issue_type] = {'total': 0, 'resolved': 0, 'with_solution': 0}
            by_type[issue_type]['total'] += 1
            if issue.status in ['RESOLVED', 'CLOSED', 'VERIFIED']:
                by_type[issue_type]['resolved'] += 1
            if issue.solution and issue.solution.strip():
                by_type[issue_type]['with_solution'] += 1
            
            # 按分类
            category = issue.category
            if category not in by_category:
                by_category[category] = {'total': 0, 'resolved': 0, 'with_solution': 0}
            by_category[category]['total'] += 1
            if issue.status in ['RESOLVED', 'CLOSED', 'VERIFIED']:
                by_category[category]['resolved'] += 1
            if issue.solution and issue.solution.strip():
                by_category[category]['with_solution'] += 1
        
        return {
            'total_issues': total_issues,
            'resolved_issues': resolved_issues,
            'issues_with_solution': issues_with_solution,
            'resolution_rate': (
                resolved_issues / total_issues * 100 
                if total_issues > 0 else 0
            ),
            'solution_coverage': (
                issues_with_solution / resolved_issues * 100
                if resolved_issues > 0 else 0
            ),
            'by_type': by_type,
            'by_category': by_category
        }
