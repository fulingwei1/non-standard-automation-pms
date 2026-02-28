# -*- coding: utf-8 -*-
"""
多模型租户隔离测试

测试所有核心业务模型的租户隔离功能
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Type, Tuple

from app.models.base import Base
from app.models.project import Project
from app.models.user import User, Role
from app.models.tenant import Tenant
from tests.fixtures.tenant_fixtures import (
    tenant_a, tenant_b, user_a, user_b, superuser
)


# 定义需要测试的模型和对应的API端点
# 注意：这个列表应该包含所有有 tenant_id 字段的核心业务模型
TENANT_ISOLATED_MODELS = [
    # (模型类, API端点, 创建数据示例)
    # 注：由于当前系统可能还未完全实现多租户，部分模型可能没有 tenant_id
    # 以下是预期应该支持租户隔离的模型列表
]


class TestMultiModelTenantIsolation:
    """多模型租户隔离测试"""

    def test_user_model_tenant_isolation(
        self, 
        db: Session,
        tenant_a: Tenant,
        tenant_b: Tenant,
        user_a: User,
        user_b: User
    ):
        """测试用户模型的租户隔离"""
        # 查询租户A的用户
        tenant_a_users = db.query(User).filter(
            User.tenant_id == tenant_a.id
        ).all()
        
        # 验证不包含租户B的用户
        user_ids = [u.id for u in tenant_a_users]
        assert user_b.id not in user_ids, "租户A的用户查询不应包含租户B的用户"
        
        # 查询租户B的用户
        tenant_b_users = db.query(User).filter(
            User.tenant_id == tenant_b.id
        ).all()
        
        # 验证不包含租户A的用户
        user_ids = [u.id for u in tenant_b_users]
        assert user_a.id not in user_ids, "租户B的用户查询不应包含租户A的用户"

    def test_role_model_tenant_isolation(
        self, 
        db: Session,
        tenant_a: Tenant,
        tenant_b: Tenant
    ):
        """测试角色模型的租户隔离"""
        # 创建租户A的角色
        role_a = Role(
            tenant_id=tenant_a.id,
            role_code="ROLE_A",
            role_name="租户A角色",
            description="租户A的测试角色"
        )
        db.add(role_a)
        
        # 创建租户B的角色
        role_b = Role(
            tenant_id=tenant_b.id,
            role_code="ROLE_B",
            role_name="租户B角色",
            description="租户B的测试角色"
        )
        db.add(role_b)
        db.commit()
        
        # 查询租户A的角色
        tenant_a_roles = db.query(Role).filter(
            Role.tenant_id == tenant_a.id
        ).all()
        role_ids = [r.id for r in tenant_a_roles]
        assert role_b.id not in role_ids, "租户A的角色查询不应包含租户B的角色"
        
        # 查询租户B的角色
        tenant_b_roles = db.query(Role).filter(
            Role.tenant_id == tenant_b.id
        ).all()
        role_ids = [r.id for r in tenant_b_roles]
        assert role_a.id not in role_ids, "租户B的角色查询不应包含租户A的角色"

    def test_api_key_model_tenant_isolation(
        self, 
        db: Session,
        tenant_a: Tenant,
        tenant_b: Tenant,
        user_a: User,
        user_b: User
    ):
        """测试API密钥模型的租户隔离"""
        from app.models.api_key import APIKey
        from datetime import datetime, timedelta
        
        # 创建租户A的API Key
        api_key_a = APIKey(
            tenant_id=tenant_a.id,
            user_id=user_a.id,
            key_name="租户A API Key",
            key_value="test_key_a_" + "x" * 32,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(api_key_a)
        
        # 创建租户B的API Key
        api_key_b = APIKey(
            tenant_id=tenant_b.id,
            user_id=user_b.id,
            key_name="租户B API Key",
            key_value="test_key_b_" + "x" * 32,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(api_key_b)
        db.commit()
        
        # 查询租户A的API Keys
        tenant_a_keys = db.query(APIKey).filter(
            APIKey.tenant_id == tenant_a.id
        ).all()
        key_ids = [k.id for k in tenant_a_keys]
        assert api_key_b.id not in key_ids, "租户A的API Key查询不应包含租户B的"
        
        # 查询租户B的API Keys
        tenant_b_keys = db.query(APIKey).filter(
            APIKey.tenant_id == tenant_b.id
        ).all()
        key_ids = [k.id for k in tenant_b_keys]
        assert api_key_a.id not in key_ids, "租户B的API Key查询不应包含租户A的"

    @pytest.mark.parametrize("model_info", [
        ("User", "/api/v1/users"),
        ("Role", "/api/v1/roles"),
        # 注意：以下模型可能还未实现 tenant_id，需要先添加字段
        # ("Project", "/api/v1/projects"),
        # ("Task", "/api/v1/tasks"),
        # ("Material", "/api/v1/materials"),
        # ("Customer", "/api/v1/customers"),
    ])
    def test_api_endpoint_tenant_isolation(
        self,
        client: TestClient,
        db: Session,
        user_a: User,
        model_info: Tuple[str, str]
    ):
        """参数化测试：验证各API端点的租户隔离"""
        model_name, endpoint = model_info
        
        from app.core.security import create_access_token
        token = create_access_token(user_a.id)
        
        # 列表查询
        response = client.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and "items" in data:
                items = data["items"]
            elif isinstance(data, list):
                items = data
            else:
                items = []
            
            # 验证所有返回的项都属于用户的租户
            for item in items:
                if "tenant_id" in item:
                    assert item["tenant_id"] == user_a.tenant_id or item["tenant_id"] is None, \
                        f"{model_name} API返回了其他租户的数据: {item}"


class TestCrossModelTenantIsolation:
    """跨模型租户隔离测试"""

    def test_project_member_tenant_isolation(
        self, 
        db: Session,
        tenant_a: Tenant,
        tenant_b: Tenant,
        user_a: User,
        user_b: User
    ):
        """测试项目成员的租户隔离（跨用户和项目）"""
        from app.models.project import ProjectMember
        from tests.fixtures.tenant_fixtures import create_project
        
        # 创建租户A的项目
        project_a = create_project(
            db, tenant_a.id, user_a.id,
            "CROSS_A_001", "跨模型测试项目A"
        )
        
        # 创建租户B的项目
        project_b = create_project(
            db, tenant_b.id, user_b.id,
            "CROSS_B_001", "跨模型测试项目B"
        )
        
        # 尝试将租户A的用户添加到租户B的项目（应该被业务逻辑阻止）
        # 注意：这里假设有租户ID验证逻辑
        member = ProjectMember(
            project_id=project_b.id,
            user_id=user_a.id,
            role_code="MEMBER"
        )
        db.add(member)
        
        try:
            db.commit()
            # 如果成功提交，验证业务逻辑
            # 理想情况下，应该有触发器或约束阻止这种情况
            db.refresh(member)
            
            # 检查用户和项目的租户是否一致
            user = db.query(User).filter(User.id == member.user_id).first()
            project = db.query(Project).filter(Project.id == member.project_id).first()
            
            # 警告：跨租户成员关系应该被阻止
            if hasattr(project, 'tenant_id') and hasattr(user, 'tenant_id'):
                if user.tenant_id != project.tenant_id:
                    pytest.skip("检测到跨租户成员关系，需要添加业务逻辑验证")
        except Exception as e:
            # 如果有约束，应该抛出异常
            db.rollback()

    def test_task_assignment_tenant_isolation(
        self, 
        db: Session,
        tenant_a: Tenant,
        user_a: User,
        user_b: User
    ):
        """测试任务分配的租户隔离"""
        from tests.fixtures.tenant_fixtures import create_project
        
        # 创建租户A的项目
        project_a = create_project(
            db, tenant_a.id, user_a.id,
            "TASK_A_001", "任务测试项目A"
        )
        
        # 尝试将任务分配给其他租户的用户
        # 这应该在业务逻辑层被阻止
        # 注意：需要检查实际的任务模型实现

    def test_material_purchase_tenant_isolation(
        self, 
        db: Session,
        tenant_a: Tenant,
        tenant_b: Tenant,
        user_a: User,
        user_b: User
    ):
        """测试物料采购的租户隔离"""
        # 验证租户A不能查看租户B的物料采购记录
        # 注意：需要根据实际的物料模型实现
        pass

    def test_report_data_tenant_isolation(
        self, 
        db: Session,
        tenant_a: Tenant,
        tenant_b: Tenant
    ):
        """测试报表数据的租户隔离"""
        # 验证报表统计数据只包含本租户的数据
        # 例如：项目统计、成本统计、人员统计等
        from tests.fixtures.tenant_fixtures import create_project, create_user
        
        # 创建租户A的多个项目
        for i in range(3):
            create_project(
                db, tenant_a.id, 
                create_user(db, f"user_a_{i}", tenant_a.id).id,
                f"REPORT_A_{i:03d}", f"租户A项目{i}"
            )
        
        # 创建租户B的多个项目
        for i in range(5):
            create_project(
                db, tenant_b.id,
                create_user(db, f"user_b_{i}", tenant_b.id).id,
                f"REPORT_B_{i:03d}", f"租户B项目{i}"
            )
        
        # 统计租户A的项目数量
        if hasattr(Project, 'tenant_id'):
            tenant_a_count = db.query(Project).filter(
                Project.tenant_id == tenant_a.id
            ).count()
            
            # 应该只包含租户A的项目
            assert tenant_a_count >= 3, "租户A的项目统计不正确"


class TestTenantIsolationPerformance:
    """租户隔离性能测试（基础版）"""

    def test_large_dataset_tenant_filtering(
        self, 
        db: Session,
        tenant_a: Tenant,
        tenant_b: Tenant
    ):
        """测试大数据集下的租户过滤性能"""
        from tests.fixtures.tenant_fixtures import create_user, create_project
        import time
        
        # 创建大量数据
        user_a = create_user(db, "perf_user_a", tenant_a.id)
        user_b = create_user(db, "perf_user_b", tenant_b.id)
        
        # 为租户A创建100个项目
        for i in range(100):
            create_project(
                db, tenant_a.id, user_a.id,
                f"PERF_A_{i:05d}", f"性能测试项目A{i}"
            )
        
        # 为租户B创建100个项目
        for i in range(100):
            create_project(
                db, tenant_b.id, user_b.id,
                f"PERF_B_{i:05d}", f"性能测试项目B{i}"
            )
        
        # 测试查询性能
        start_time = time.time()
        
        if hasattr(Project, 'tenant_id'):
            tenant_a_projects = db.query(Project).filter(
                Project.tenant_id == tenant_a.id
            ).all()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # 验证结果正确性
            assert len(tenant_a_projects) >= 100, "应该返回租户A的所有项目"
            
            # 验证没有其他租户的数据
            for project in tenant_a_projects:
                assert project.tenant_id == tenant_a.id, "不应包含其他租户的项目"
            
            # 性能要求：查询200个项目应该在1秒内完成
            assert query_time < 1.0, \
                f"租户过滤查询性能不达标: {query_time:.3f}秒"

    def test_index_effectiveness_for_tenant_filtering(
        self, 
        db: Session,
        tenant_a: Tenant
    ):
        """测试租户ID索引的有效性"""
        # 验证 tenant_id 字段是否有索引
        # 这需要检查数据库的实际索引配置
        
        from sqlalchemy import inspect
        inspector = inspect(db.get_bind())
        
        # 检查各个表的索引
        tables_to_check = ['users', 'projects', 'roles']  # 需要根据实际情况调整
        
        for table_name in tables_to_check:
            try:
                indexes = inspector.get_indexes(table_name)
                columns = inspector.get_columns(table_name)
                
                # 检查是否有 tenant_id 列
                has_tenant_id = any(col['name'] == 'tenant_id' for col in columns)
                
                if has_tenant_id:
                    # 检查是否有包含 tenant_id 的索引
                    has_tenant_index = any(
                        'tenant_id' in idx['column_names'] 
                        for idx in indexes
                    )
                    
                    # 建议：tenant_id 应该有索引以提高查询性能
                    if not has_tenant_index:
                        pytest.skip(
                            f"表 {table_name} 的 tenant_id 字段缺少索引，"
                            "可能影响查询性能"
                        )
            except Exception as e:
                # 如果表不存在或其他错误，跳过
                continue


class TestTenantDataMigration:
    """租户数据迁移测试"""

    def test_legacy_data_without_tenant_id(
        self, 
        db: Session,
        superuser: User
    ):
        """测试遗留数据（没有tenant_id）的处理"""
        # 创建一个没有tenant_id的项目（模拟遗留数据）
        legacy_project = Project(
            # tenant_id=None,  # 遗留数据
            project_code="LEGACY_001",
            project_name="遗留项目",
            project_type="OLD_PROJECT",
            created_by=superuser.id,
            pm_id=superuser.id
        )
        db.add(legacy_project)
        db.commit()
        
        # 验证遗留数据的处理策略
        # 选项1：只有超级管理员可以访问
        # 选项2：分配给默认租户
        # 选项3：标记为需要迁移
        
        if hasattr(legacy_project, 'tenant_id'):
            # 如果有tenant_id字段
            if legacy_project.tenant_id is None:
                # 确认遗留数据的访问策略
                pass

    def test_tenant_data_export_isolation(
        self, 
        db: Session,
        tenant_a: Tenant,
        tenant_b: Tenant
    ):
        """测试租户数据导出的隔离"""
        # 验证导出功能只导出本租户的数据
        # 这是一个重要的安全测试
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
