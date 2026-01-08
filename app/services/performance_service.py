# -*- coding: utf-8 -*-
"""
绩效管理服务层
包含角色判断、权限过滤、分数计算等核心业务逻辑
"""

from typing import List, Tuple, Optional, Dict, Any
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from app.models.project import ProjectMember, Project
from app.models.organization import Department, Employee
from app.models.performance import (
    MonthlyWorkSummary,
    PerformanceEvaluationRecord,
    EvaluationWeightConfig,
    EvaluatorTypeEnum,
    EvaluationStatusEnum
)


class PerformanceService:
    """绩效管理服务"""

    @staticmethod
    def get_user_manager_roles(db: Session, user: User) -> Dict[str, Any]:
        """
        判断用户的经理角色

        Returns:
            {
                'is_dept_manager': bool,  # 是否部门经理
                'is_project_manager': bool,  # 是否项目经理
                'managed_dept_id': Optional[int],  # 管理的部门ID
                'managed_project_ids': List[int]  # 管理的项目ID列表
            }
        """
        result = {
            'is_dept_manager': False,
            'is_project_manager': False,
            'managed_dept_id': None,
            'managed_project_ids': []
        }

        # 1. 检查是否是部门经理
        # 查找该用户是否是某个部门的负责人
        # 通过 User.employee_id -> Employee -> Department.manager_id
        if user.employee_id:
            dept = db.query(Department).filter(
                Department.manager_id == user.employee_id,
                Department.is_active == True
            ).first()

            if dept:
                result['is_dept_manager'] = True
                result['managed_dept_id'] = dept.id

        # 2. 检查是否是项目经理
        # 查找该用户作为PM的所有活跃项目
        managed_projects = db.query(Project).filter(
            Project.pm_id == user.id,
            Project.is_active == True
        ).all()

        if managed_projects:
            result['is_project_manager'] = True
            result['managed_project_ids'] = [p.id for p in managed_projects]

        return result

    @staticmethod
    def get_manageable_employees(
        db: Session,
        user: User,
        period: Optional[str] = None
    ) -> List[int]:
        """
        获取经理可以评价的员工ID列表

        Args:
            db: 数据库会话
            user: 当前用户
            period: 评价周期 (YYYY-MM)，用于筛选该周期活跃的项目成员

        Returns:
            员工ID列表
        """
        roles = PerformanceService.get_user_manager_roles(db, user)
        employee_ids = set()

        # 1. 如果是部门经理，获取部门下所有员工
        if roles['is_dept_manager'] and roles['managed_dept_id']:
            # 通过 Department -> Employee -> User 获取部门员工
            dept = db.query(Department).get(roles['managed_dept_id'])
            if dept:
                # 查找该部门的所有员工
                employees = db.query(Employee).filter(
                    Employee.department == dept.dept_name,  # 使用字符串字段匹配
                    Employee.is_active == True
                ).all()

                # 通过员工ID找到对应的用户
                for emp in employees:
                    user_obj = db.query(User).filter(
                        User.employee_id == emp.id,
                        User.is_active == True
                    ).first()
                    if user_obj:
                        employee_ids.add(user_obj.id)

        # 2. 如果是项目经理，获取项目成员
        if roles['is_project_manager'] and roles['managed_project_ids']:
            query = db.query(ProjectMember).filter(
                ProjectMember.project_id.in_(roles['managed_project_ids']),
                ProjectMember.is_active == True
            )

            # 如果指定了周期，只查询该周期内活跃的成员
            if period:
                # 将 YYYY-MM 转换为日期范围
                year, month = map(int, period.split('-'))
                period_start = date(year, month, 1)
                period_end = date(year, month, 28)  # 简化处理，用28号代表月末

                query = query.filter(
                    or_(
                        ProjectMember.start_date.is_(None),
                        ProjectMember.start_date <= period_end
                    ),
                    or_(
                        ProjectMember.end_date.is_(None),
                        ProjectMember.end_date >= period_start
                    )
                )

            members = query.all()
            employee_ids.update([m.user_id for m in members])

        return list(employee_ids)

    @staticmethod
    def create_evaluation_tasks(
        db: Session,
        summary: MonthlyWorkSummary
    ) -> List[PerformanceEvaluationRecord]:
        """
        员工提交工作总结后，自动创建评价任务

        Args:
            db: 数据库会话
            summary: 工作总结对象

        Returns:
            创建的评价记录列表
        """
        created_records = []
        employee = db.query(User).get(summary.employee_id)

        if not employee:
            return created_records

        # 1. 创建部门经理评价任务
        if employee.employee_id:
            # 找到员工所属部门的经理
            emp_obj = db.query(Employee).get(employee.employee_id)
            if emp_obj and emp_obj.department:
                dept = db.query(Department).filter(
                    Department.dept_name == emp_obj.department,
                    Department.is_active == True
                ).first()

                if dept and dept.manager_id:
                    # 找到经理的User对象
                    manager_emp = db.query(Employee).get(dept.manager_id)
                    if manager_emp:
                        manager_user = db.query(User).filter(
                            User.employee_id == manager_emp.id,
                            User.is_active == True
                        ).first()

                        if manager_user:
                            # 检查是否已存在评价记录
                            existing = db.query(PerformanceEvaluationRecord).filter(
                                PerformanceEvaluationRecord.summary_id == summary.id,
                                PerformanceEvaluationRecord.evaluator_id == manager_user.id,
                                PerformanceEvaluationRecord.evaluator_type == EvaluatorTypeEnum.DEPT_MANAGER
                            ).first()

                            if not existing:
                                dept_eval = PerformanceEvaluationRecord(
                                    summary_id=summary.id,
                                    evaluator_id=manager_user.id,
                                    evaluator_type=EvaluatorTypeEnum.DEPT_MANAGER,
                                    project_id=None,
                                    project_weight=None,
                                    score=0,  # 默认0，待评价
                                    comment="",
                                    status=EvaluationStatusEnum.PENDING
                                )
                                db.add(dept_eval)
                                created_records.append(dept_eval)

        # 2. 创建项目经理评价任务
        # 查找员工参与的所有活跃项目
        year, month = map(int, summary.period.split('-'))
        period_start = date(year, month, 1)
        period_end = date(year, month, 28)

        project_members = db.query(ProjectMember).filter(
            ProjectMember.user_id == summary.employee_id,
            ProjectMember.is_active == True,
            or_(
                ProjectMember.start_date.is_(None),
                ProjectMember.start_date <= period_end
            ),
            or_(
                ProjectMember.end_date.is_(None),
                ProjectMember.end_date >= period_start
            )
        ).all()

        for member in project_members:
            project = db.query(Project).filter(
                Project.id == member.project_id,
                Project.is_active == True
            ).first()

            if project and project.pm_id:
                # 检查是否已存在评价记录
                existing = db.query(PerformanceEvaluationRecord).filter(
                    PerformanceEvaluationRecord.summary_id == summary.id,
                    PerformanceEvaluationRecord.evaluator_id == project.pm_id,
                    PerformanceEvaluationRecord.evaluator_type == EvaluatorTypeEnum.PROJECT_MANAGER,
                    PerformanceEvaluationRecord.project_id == project.id
                ).first()

                if not existing:
                    # 计算项目权重（如果有多个项目，默认平均分配）
                    project_weight = 100 // len(project_members) if len(project_members) > 0 else 100

                    proj_eval = PerformanceEvaluationRecord(
                        summary_id=summary.id,
                        evaluator_id=project.pm_id,
                        evaluator_type=EvaluatorTypeEnum.PROJECT_MANAGER,
                        project_id=project.id,
                        project_weight=project_weight,
                        score=0,  # 默认0，待评价
                        comment="",
                        status=EvaluationStatusEnum.PENDING
                    )
                    db.add(proj_eval)
                    created_records.append(proj_eval)

        # 提交到数据库
        if created_records:
            db.commit()
            for record in created_records:
                db.refresh(record)

        return created_records

    @staticmethod
    def calculate_final_score(
        db: Session,
        summary_id: int,
        period: str
    ) -> Optional[Dict[str, Any]]:
        """
        计算员工的最终绩效分数

        算法：
        1. 获取该周期的权重配置
        2. 计算部门经理评分 * 部门权重%
        3. 计算所有项目经理评分的加权平均 * 项目权重%
        4. 最终分数 = 部门分数 + 项目分数

        Args:
            db: 数据库会话
            summary_id: 工作总结ID
            period: 评价周期

        Returns:
            {
                'final_score': float,  # 最终分数
                'dept_score': Optional[float],  # 部门经理评分
                'project_score': Optional[float],  # 项目经理加权平均分
                'dept_weight': int,  # 部门权重%
                'project_weight': int,  # 项目权重%
                'details': List[dict]  # 各评价详情
            }
        """
        # 1. 获取权重配置
        year, month = map(int, period.split('-'))
        period_date = date(year, month, 1)

        weight_config = db.query(EvaluationWeightConfig).filter(
            EvaluationWeightConfig.effective_date <= period_date
        ).order_by(EvaluationWeightConfig.effective_date.desc()).first()

        if not weight_config:
            # 使用默认权重 50:50
            dept_weight = 50
            project_weight = 50
        else:
            dept_weight = weight_config.dept_manager_weight
            project_weight = weight_config.project_manager_weight

        # 2. 获取所有评价记录
        evaluations = db.query(PerformanceEvaluationRecord).filter(
            PerformanceEvaluationRecord.summary_id == summary_id,
            PerformanceEvaluationRecord.status == EvaluationStatusEnum.COMPLETED
        ).all()

        if not evaluations:
            return None

        # 3. 分离部门和项目评价
        dept_evaluations = [e for e in evaluations if e.evaluator_type == EvaluatorTypeEnum.DEPT_MANAGER]
        project_evaluations = [e for e in evaluations if e.evaluator_type == EvaluatorTypeEnum.PROJECT_MANAGER]

        # 4. 计算部门经理分数
        dept_score = None
        if dept_evaluations:
            # 通常只有一个部门经理评价
            dept_score = float(dept_evaluations[0].score)

        # 5. 计算项目经理加权平均分
        project_score = None
        if project_evaluations:
            # 使用项目权重进行加权平均
            total_weight = sum([e.project_weight or 0 for e in project_evaluations])
            if total_weight > 0:
                weighted_sum = sum([e.score * (e.project_weight or 0) for e in project_evaluations])
                project_score = float(weighted_sum) / total_weight
            else:
                # 如果没有设置项目权重，使用简单平均
                project_score = float(sum([e.score for e in project_evaluations])) / len(project_evaluations)

        # 6. 计算最终分数
        final_score = 0.0

        if dept_score is not None:
            final_score += dept_score * (dept_weight / 100.0)

        if project_score is not None:
            final_score += project_score * (project_weight / 100.0)

        # 7. 如果只有部门评价或只有项目评价，使用该评价的100%
        if dept_score is not None and project_score is None:
            final_score = dept_score
        elif dept_score is None and project_score is not None:
            final_score = project_score

        # 8. 构建详情
        details = []
        for e in evaluations:
            details.append({
                'evaluator_type': e.evaluator_type,
                'evaluator_id': e.evaluator_id,
                'project_id': e.project_id,
                'project_weight': e.project_weight,
                'score': e.score,
                'comment': e.comment,
                'evaluated_at': e.evaluated_at
            })

        return {
            'final_score': round(final_score, 2),
            'dept_score': dept_score,
            'project_score': round(project_score, 2) if project_score else None,
            'dept_weight': dept_weight,
            'project_weight': project_weight,
            'details': details
        }

    @staticmethod
    def calculate_quarterly_score(
        db: Session,
        employee_id: int,
        end_period: str
    ) -> Optional[float]:
        """
        计算季度绩效分数（最近3个月的加权平均）

        Args:
            db: 数据库会话
            employee_id: 员工ID
            end_period: 结束周期 (YYYY-MM)

        Returns:
            季度平均分数
        """
        year, month = map(int, end_period.split('-'))
        end_date = date(year, month, 1)

        # 计算前3个月
        periods = []
        for i in range(3):
            period_date = end_date - relativedelta(months=i)
            periods.append(period_date.strftime("%Y-%m"))

        # 获取这3个月的工作总结
        summaries = db.query(MonthlyWorkSummary).filter(
            MonthlyWorkSummary.employee_id == employee_id,
            MonthlyWorkSummary.period.in_(periods),
            MonthlyWorkSummary.status == 'COMPLETED'
        ).all()

        if not summaries:
            return None

        # 计算每个月的最终分数
        monthly_scores = []
        for summary in summaries:
            score_result = PerformanceService.calculate_final_score(
                db, summary.id, summary.period
            )
            if score_result and score_result['final_score'] > 0:
                monthly_scores.append(score_result['final_score'])

        if not monthly_scores:
            return None

        # 计算平均分
        quarterly_avg = sum(monthly_scores) / len(monthly_scores)
        return round(quarterly_avg, 2)

    @staticmethod
    def get_score_level(score: float) -> str:
        """
        根据分数获取等级

        Args:
            score: 分数 (60-100)

        Returns:
            等级: A+/A/B+/B/C+/C/D
        """
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        else:
            return 'D'

    @staticmethod
    def get_historical_performance(
        db: Session,
        employee_id: int,
        months: int = 3
    ) -> List[Dict[str, Any]]:
        """
        获取员工的历史绩效记录

        Args:
            db: 数据库会话
            employee_id: 员工ID
            months: 查询最近几个月

        Returns:
            历史绩效列表
        """
        # 计算开始周期
        today = date.today()
        periods = []
        for i in range(months):
            period_date = today - relativedelta(months=i+1)
            periods.append(period_date.strftime("%Y-%m"))

        # 查询工作总结
        summaries = db.query(MonthlyWorkSummary).filter(
            MonthlyWorkSummary.employee_id == employee_id,
            MonthlyWorkSummary.period.in_(periods),
            MonthlyWorkSummary.status == 'COMPLETED'
        ).order_by(MonthlyWorkSummary.period.desc()).all()

        history = []
        for summary in summaries:
            score_result = PerformanceService.calculate_final_score(
                db, summary.id, summary.period
            )

            if score_result:
                history.append({
                    'period': summary.period,
                    'final_score': score_result['final_score'],
                    'level': PerformanceService.get_score_level(score_result['final_score']),
                    'dept_score': score_result['dept_score'],
                    'project_score': score_result['project_score']
                })

        return history
