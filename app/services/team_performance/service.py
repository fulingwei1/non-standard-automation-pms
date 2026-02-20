# -*- coding: utf-8 -*-
"""
团队绩效服务类
提取自 app/api/v1/endpoints/performance/team.py
"""

from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.performance import PerformancePeriod, PerformanceResult
from app.models.project import Project
from app.models.user import User


class TeamPerformanceService:
    """团队绩效业务逻辑服务"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db

    # ==================== 权限检查 ====================

    def check_performance_view_permission(
        self, current_user: User, target_user_id: int
    ) -> bool:
        """
        检查用户是否有权限查看指定用户的绩效

        规则：
        1. 可以查看自己的绩效
        2. 部门经理可以查看本部门员工的绩效
        3. 项目经理可以查看项目成员的绩效
        4. 管理员可以查看所有人的绩效

        Args:
            current_user: 当前用户
            target_user_id: 目标用户ID

        Returns:
            bool: 是否有权限查看
        """
        if current_user.is_superuser:
            return True

        # 查看自己的绩效
        if current_user.id == target_user_id:
            return True

        # 检查是否是部门经理
        target_user = self.db.query(User).filter(User.id == target_user_id).first()
        if not target_user:
            return False

        # 检查是否有管理角色
        manager_roles = [
            "dept_manager",
            "department_manager",
            "部门经理",
            "pm",
            "project_manager",
            "项目经理",
            "admin",
            "super_admin",
            "管理员",
        ]

        has_manager_role = False
        for user_role in current_user.roles or []:
            role_code = (
                user_role.role.role_code.lower()
                if user_role.role.role_code
                else ""
            )
            role_name = (
                user_role.role.role_name.lower()
                if user_role.role.role_name
                else ""
            )
            if role_code in manager_roles or role_name in manager_roles:
                has_manager_role = True
                break

        if not has_manager_role:
            return False

        # 检查是否是同一部门
        if (
            target_user.department_id
            and current_user.department_id == target_user.department_id
        ):
            return True

        # 检查是否管理同一项目
        user_projects = (
            self.db.query(Project).filter(Project.pm_id == current_user.id).all()
        )
        project_ids = [p.id for p in user_projects]

        target_projects = (
            self.db.query(Project).filter(Project.id.in_(project_ids)).all()
        )
        for project in target_projects:
            # 检查目标用户是否是项目成员
            from app.models.progress import Task

            member_task = (
                self.db.query(Task)
                .filter(Task.project_id == project.id, Task.owner_id == target_user_id)
                .first()
            )
            if member_task:
                return True

        return False

    # ==================== 成员获取 ====================

    def get_team_members(self, team_id: int) -> List[int]:
        """
        获取团队成员ID列表

        Args:
            team_id: 团队ID（暂时使用department_id作为team_id）

        Returns:
            List[int]: 成员ID列表
        """
        # 临时使用部门作为团队
        users = (
            self.db.query(User)
            .filter(User.department_id == team_id, User.is_active)
            .all()
        )
        return [u.id for u in users]

    def get_department_members(self, dept_id: int) -> List[int]:
        """
        获取部门成员ID列表

        Args:
            dept_id: 部门ID

        Returns:
            List[int]: 成员ID列表
        """
        users = (
            self.db.query(User)
            .filter(User.department_id == dept_id, User.is_active)
            .all()
        )
        return [u.id for u in users]

    # ==================== 名称获取 ====================

    def get_team_name(self, team_id: int) -> str:
        """
        获取团队名称

        Args:
            team_id: 团队ID

        Returns:
            str: 团队名称
        """
        dept = self.db.query(Department).filter(Department.id == team_id).first()
        return dept.name if dept else f"团队{team_id}"

    def get_department_name(self, dept_id: int) -> str:
        """
        获取部门名称

        Args:
            dept_id: 部门ID

        Returns:
            str: 部门名称
        """
        dept = self.db.query(Department).filter(Department.id == dept_id).first()
        return dept.name if dept else f"部门{dept_id}"

    # ==================== 周期获取 ====================

    def get_period(self, period_id: Optional[int] = None) -> Optional[PerformancePeriod]:
        """
        获取考核周期

        Args:
            period_id: 周期ID，如果为None则获取最新的已完成周期

        Returns:
            PerformancePeriod: 考核周期对象，如果未找到则返回None
        """
        if period_id:
            return (
                self.db.query(PerformancePeriod)
                .filter(PerformancePeriod.id == period_id)
                .first()
            )
        else:
            return (
                self.db.query(PerformancePeriod)
                .filter(PerformancePeriod.status == "FINALIZED")
                .order_by(desc(PerformancePeriod.end_date))
                .first()
            )

    # ==================== 用户类型判断 ====================

    def get_evaluator_type(self, user: User) -> str:
        """
        判断评价人类型（部门经理/项目经理）

        Args:
            user: 用户对象

        Returns:
            str: 评价人类型（DEPT_MANAGER/PROJECT_MANAGER/BOTH/OTHER）
        """
        is_dept_manager = False
        is_project_manager = False

        for user_role in user.roles or []:
            role_code = (
                user_role.role.role_code.lower()
                if user_role.role.role_code
                else ""
            )
            role_name = (
                user_role.role.role_name.lower()
                if user_role.role.role_name
                else ""
            )

            if role_code in ["dept_manager", "department_manager", "部门经理"] or role_name in [
                "dept_manager",
                "department_manager",
                "部门经理",
            ]:
                is_dept_manager = True
            if role_code in ["pm", "project_manager", "项目经理"] or role_name in [
                "pm",
                "project_manager",
                "项目经理",
            ]:
                is_project_manager = True

        if is_dept_manager and is_project_manager:
            return "BOTH"
        elif is_dept_manager:
            return "DEPT_MANAGER"
        elif is_project_manager:
            return "PROJECT_MANAGER"
        else:
            return "OTHER"

    # ==================== 团队绩效 ====================

    def get_team_performance(
        self, team_id: int, period_id: Optional[int] = None
    ) -> Dict:
        """
        获取团队绩效汇总

        Args:
            team_id: 团队ID
            period_id: 周期ID

        Returns:
            Dict: 团队绩效数据
        """
        # 获取团队名称
        team_name = self.get_team_name(team_id)

        # 获取团队成员
        member_ids = self.get_team_members(team_id)

        # 获取周期
        period = self.get_period(period_id)
        if not period:
            return self._empty_team_performance(team_id, team_name, member_ids)

        # 获取团队成员绩效
        results = (
            self.db.query(PerformanceResult)
            .filter(
                PerformanceResult.period_id == period.id,
                PerformanceResult.user_id.in_(member_ids),
            )
            .all()
        )

        if not results:
            return {
                "team_id": team_id,
                "team_name": team_name,
                "period_id": period.id,
                "period_name": period.period_name,
                "member_count": len(member_ids),
                "avg_score": Decimal("0"),
                "max_score": Decimal("0"),
                "min_score": Decimal("0"),
                "level_distribution": {},
                "members": [],
            }

        # 计算统计数据
        scores = [float(r.total_score) if r.total_score else 0 for r in results]
        avg_score = (
            Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")
        )
        max_score = Decimal(str(max(scores))) if scores else Decimal("0")
        min_score = Decimal(str(min(scores))) if scores else Decimal("0")

        # 等级分布
        level_distribution = {}
        for r in results:
            level = r.level or "QUALIFIED"
            level_distribution[level] = level_distribution.get(level, 0) + 1

        # 成员列表
        members = []
        for r in results:
            user = self.db.query(User).filter(User.id == r.user_id).first()
            members.append(
                {
                    "user_id": r.user_id,
                    "user_name": user.real_name or user.username if user else None,
                    "score": float(r.total_score) if r.total_score else 0,
                    "level": r.level or "QUALIFIED",
                }
            )

        # 按分数排序
        members.sort(key=lambda x: x["score"], reverse=True)

        return {
            "team_id": team_id,
            "team_name": team_name,
            "period_id": period.id,
            "period_name": period.period_name,
            "member_count": len(results),
            "avg_score": avg_score,
            "max_score": max_score,
            "min_score": min_score,
            "level_distribution": level_distribution,
            "members": members,
        }

    def _empty_team_performance(
        self, team_id: int, team_name: str, member_ids: List[int]
    ) -> Dict:
        """返回空的团队绩效数据"""
        return {
            "team_id": team_id,
            "team_name": team_name,
            "period_id": None,
            "period_name": None,
            "member_count": len(member_ids),
            "avg_score": Decimal("0"),
            "max_score": Decimal("0"),
            "min_score": Decimal("0"),
            "level_distribution": {},
            "members": [],
        }

    # ==================== 部门绩效 ====================

    def get_department_performance(
        self, dept_id: int, period_id: Optional[int] = None
    ) -> Dict:
        """
        获取部门绩效汇总

        Args:
            dept_id: 部门ID
            period_id: 周期ID

        Returns:
            Dict: 部门绩效数据
        """
        # 获取部门名称
        department_name = self.get_department_name(dept_id)

        # 获取部门成员
        member_ids = self.get_department_members(dept_id)

        # 获取周期
        period = self.get_period(period_id)
        if not period:
            return None  # 调用方需要处理404

        # 获取部门绩效结果
        results = (
            self.db.query(PerformanceResult)
            .filter(
                PerformanceResult.period_id == period.id,
                PerformanceResult.department_id == dept_id,
            )
            .all()
        )

        if not results:
            return {
                "department_id": dept_id,
                "department_name": department_name,
                "period_id": period.id,
                "period_name": period.period_name,
                "member_count": len(member_ids),
                "avg_score": Decimal("0"),
                "level_distribution": {},
                "teams": [],
            }

        # 计算平均分
        scores = [float(r.total_score) if r.total_score else 0 for r in results]
        avg_score = (
            Decimal(str(sum(scores) / len(scores))) if scores else Decimal("0")
        )

        # 等级分布
        level_distribution = {}
        for r in results:
            level = r.level or "QUALIFIED"
            level_distribution[level] = level_distribution.get(level, 0) + 1

        # 获取子团队列表
        sub_teams = (
            self.db.query(Department).filter(Department.parent_id == dept_id).all()
        )
        teams = [{"team_id": t.id, "team_name": t.name} for t in sub_teams]

        return {
            "department_id": dept_id,
            "department_name": department_name,
            "period_id": period.id,
            "period_name": period.period_name,
            "member_count": len(results),
            "avg_score": avg_score,
            "level_distribution": level_distribution,
            "teams": teams,
        }

    # ==================== 绩效排行榜 ====================

    def get_performance_ranking(
        self, ranking_type: str, period_id: Optional[int] = None
    ) -> Dict:
        """
        获取绩效排行榜

        Args:
            ranking_type: 排行榜类型（TEAM/DEPARTMENT/COMPANY）
            period_id: 周期ID

        Returns:
            Dict: 排行榜数据，如果周期未找到则返回None
        """
        period = self.get_period(period_id)
        if not period:
            return None

        rankings = []

        if ranking_type == "COMPANY":
            rankings = self._get_company_ranking(period.id)
        elif ranking_type == "TEAM":
            rankings = self._get_team_ranking(period.id)
        elif ranking_type == "DEPARTMENT":
            rankings = self._get_department_ranking(period.id)

        return {
            "ranking_type": ranking_type,
            "period_id": period.id,
            "period_name": period.period_name,
            "rankings": rankings,
        }

    def _get_company_ranking(self, period_id: int) -> List[Dict]:
        """获取公司排行榜"""
        results = (
            self.db.query(PerformanceResult)
            .filter(PerformanceResult.period_id == period_id)
            .order_by(desc(PerformanceResult.total_score))
            .limit(100)
            .all()
        )

        rankings = []
        for idx, result in enumerate(results, 1):
            user = self.db.query(User).filter(User.id == result.user_id).first()
            rankings.append(
                {
                    "rank": idx,
                    "user_id": result.user_id,
                    "user_name": user.real_name or user.username if user else None,
                    "department_name": result.department_name,
                    "score": float(result.total_score) if result.total_score else 0,
                    "level": result.level or "QUALIFIED",
                }
            )

        return rankings

    def _get_team_ranking(self, period_id: int) -> List[Dict]:
        """获取团队排行榜"""
        departments = self.db.query(Department).all()
        rankings = []

        for dept in departments:
            dept_results = (
                self.db.query(PerformanceResult)
                .filter(
                    PerformanceResult.period_id == period_id,
                    PerformanceResult.department_id == dept.id,
                )
                .all()
            )

            if dept_results:
                avg_score = sum(
                    float(r.total_score or 0) for r in dept_results
                ) / len(dept_results)
                rankings.append(
                    {
                        "rank": 0,  # 稍后填充
                        "entity_id": dept.id,
                        "entity_name": dept.name,
                        "score": round(avg_score, 2),
                        "member_count": len(dept_results),
                    }
                )

        # 排序并填充排名
        rankings.sort(key=lambda x: x["score"], reverse=True)
        for idx, r in enumerate(rankings, 1):
            r["rank"] = idx

        return rankings

    def _get_department_ranking(self, period_id: int) -> List[Dict]:
        """获取部门排行榜"""
        departments = self.db.query(Department).all()
        rankings = []

        for dept in departments:
            dept_results = (
                self.db.query(PerformanceResult)
                .filter(
                    PerformanceResult.period_id == period_id,
                    PerformanceResult.department_id == dept.id,
                )
                .all()
            )

            if dept_results:
                avg_score = sum(
                    float(r.total_score or 0) for r in dept_results
                ) / len(dept_results)

                # 等级分布
                level_dist = {}
                for r in dept_results:
                    level = r.level or "QUALIFIED"
                    level_dist[level] = level_dist.get(level, 0) + 1

                rankings.append(
                    {
                        "rank": 0,  # 稍后填充
                        "entity_id": dept.id,
                        "entity_name": dept.name,
                        "score": round(avg_score, 2),
                        "member_count": len(dept_results),
                        "level_distribution": level_dist,
                    }
                )

        # 排序并填充排名
        rankings.sort(key=lambda x: x["score"], reverse=True)
        for idx, r in enumerate(rankings, 1):
            r["rank"] = idx

        return rankings
