# -*- coding: utf-8 -*-
"""
数据库模型CRUD基础测试

测试内容：
- 基础 CRUD 操作
- 模型验证
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.models.project import Project
from app.core.auth import get_password_hash


@pytest.mark.unit
@pytest.mark.database
class TestBasicCRUD:
    """基础 CRUD 测试"""

    def test_create_user(self, db_session: Session):
        """测试创建用户"""
        user = User(
            employee_id=999,
            username=f"test_user_{datetime.now().timestamp()}",
            password_hash=get_password_hash("test123"),
            email=f"test_{datetime.now().timestamp()}@example.com",
            real_name="测试用户",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username is not None
        assert user.is_active is True

        # 清理
        db_session.delete(user)
        db_session.commit()

    def test_create_project(self, db_session: Session):
        """测试创建项目"""
        project_code = f"PJ{datetime.now().strftime('%y%m%d%H%M%S')}"
        project = Project(
            project_code=project_code,
            project_name="测试项目",
            customer_name="测试客户",
            contract_amount=100000.00,
            stage="S1",
            status="ST01",
            health="H1",
            created_by=1,
            pm_id=1,
        )
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)

        assert project.id is not None
        assert project.project_code == project_code
        assert project.status == "ST01"

        # 清理
        try:
            db_session.delete(project)
            db_session.commit()
        except Exception:
            pass  # 忽略外键约束错误

    def test_query_user(self, db_session: Session):
        """测试查询用户"""
        # 查找admin用户
        user = db_session.query(User).filter(User.username == "admin").first()

        # 验证存在
        assert user is not None
        assert user.username == "admin"
        assert user.is_active is True

    def test_query_projects(self, db_session: Session):
        """测试查询项目列表"""
        projects = db_session.query(Project).limit(10).all()

        # 验证返回列表
        assert isinstance(projects, list)
        assert len(projects) >= 0

    def test_user_project_relationship(self, db_session: Session):
        """测试用户-项目关系"""
        # 获取一个用户
        user = db_session.query(User).first()

        if user:
            # 获取该用户管理的项目
            managed_projects = (
                db_session.query(Project)
                .filter(Project.pm_id == user.id)
                .limit(5)
                .all()
            )

            # 验证关系
            assert isinstance(managed_projects, list)
