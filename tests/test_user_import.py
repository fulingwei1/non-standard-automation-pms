# -*- coding: utf-8 -*-
"""
用户批量导入功能测试
"""

import io
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.user_import_service import UserImportService
from app.models.user import User, Role
from app.core.security import get_password_hash


class TestUserImportService:
    """用户导入服务测试"""

    def test_validate_file_format(self):
        """测试文件格式验证"""
        assert UserImportService.validate_file_format("users.xlsx") is True
        assert UserImportService.validate_file_format("users.xls") is True
        assert UserImportService.validate_file_format("users.csv") is True
        assert UserImportService.validate_file_format("users.txt") is False
        assert UserImportService.validate_file_format("users.pdf") is False

    def test_normalize_columns(self):
        """测试列名标准化"""
        df = pd.DataFrame({
            "用户名": ["test1"],
            "真实姓名": ["测试"],
            "邮箱": ["test@example.com"],
        })
        
        normalized_df = UserImportService.normalize_columns(df)
        
        assert "username" in normalized_df.columns
        assert "real_name" in normalized_df.columns
        assert "email" in normalized_df.columns

    def test_validate_dataframe_missing_fields(self):
        """测试必填字段缺失验证"""
        df = pd.DataFrame({
            "username": ["test1"],
            # 缺少 real_name 和 email
        })
        
        errors = UserImportService.validate_dataframe(df)
        assert len(errors) > 0
        assert any("real_name" in err for err in errors)

    def test_validate_dataframe_empty(self):
        """测试空数据验证"""
        df = pd.DataFrame()
        
        errors = UserImportService.validate_dataframe(df)
        assert len(errors) > 0
        assert any("没有数据" in err for err in errors)

    def test_validate_dataframe_exceed_limit(self):
        """测试超过数量限制验证"""
        # 创建超过限制的数据
        data = {
            "username": [f"user{i}" for i in range(600)],
            "real_name": [f"用户{i}" for i in range(600)],
            "email": [f"user{i}@example.com" for i in range(600)],
        }
        df = pd.DataFrame(data)
        
        errors = UserImportService.validate_dataframe(df)
        assert len(errors) > 0
        assert any("不能超过" in err for err in errors)

    def test_generate_template(self):
        """测试模板生成"""
        df = UserImportService.generate_template()
        
        assert len(df) > 0
        assert "用户名" in df.columns
        assert "真实姓名" in df.columns
        assert "邮箱" in df.columns
        assert "密码" in df.columns
        assert "角色" in df.columns

    def test_import_users_success(self, db: Session):
        """测试成功导入用户"""
        # 创建测试角色
        test_role = Role(
            role_code="TEST_USER_ROLE",
            role_name="测试用户角色",
            description="用于测试的角色"
        )
        db.add(test_role)
        
        # 创建操作用户
        operator = User(
            username="test_operator",
            password_hash=get_password_hash("test123"),
            email="operator@test.com",
            real_name="测试操作员"
        )
        db.add(operator)
        db.commit()
        
        # 准备测试数据
        data = {
            "用户名": ["testuser1", "testuser2"],
            "真实姓名": ["测试用户1", "测试用户2"],
            "邮箱": ["testuser1@example.com", "testuser2@example.com"],
            "手机号": ["13800138001", "13800138002"],
            "部门": ["技术部", "产品部"],
            "职位": ["工程师", "产品经理"],
            "角色": [test_role.role_name, test_role.role_name],
        }
        df = pd.DataFrame(data)

        # 执行导入
        result = UserImportService.import_users(
            db=db,
            df=df,
            operator_id=operator.id,
            tenant_id=None,
        )

        # 验证结果
        assert result["success_count"] == 2
        assert result["failed_count"] == 0
        assert len(result["errors"]) == 0

        # 验证数据库
        user1 = db.query(User).filter(User.username == "testuser1").first()
        assert user1 is not None
        assert user1.real_name == "测试用户1"
        assert user1.email == "testuser1@example.com"

    def test_import_users_duplicate_username(self, db: Session):
        """测试重复用户名"""
        # 创建操作用户
        operator = User(
            username="test_operator2",
            password_hash=get_password_hash("test123"),
            email="operator2@test.com",
            real_name="测试操作员2"
        )
        db.add(operator)
        db.commit()
        
        data = {
            "用户名": ["duplicate", "duplicate"],
            "真实姓名": ["用户1", "用户2"],
            "邮箱": ["user1@example.com", "user2@example.com"],
        }
        df = pd.DataFrame(data)

        result = UserImportService.import_users(
            db=db,
            df=df,
            operator_id=operator.id,
            tenant_id=None,
        )

        # 应该验证失败
        assert result["failed_count"] > 0
        assert len(result["errors"]) > 0
        assert any("重复" in str(err) for err in result["errors"])

    def test_import_users_invalid_email(self, db: Session):
        """测试无效邮箱"""
        # 创建操作用户
        operator = User(
            username="test_operator3",
            password_hash=get_password_hash("test123"),
            email="operator3@test.com",
            real_name="测试操作员3"
        )
        db.add(operator)
        db.commit()
        
        data = {
            "用户名": ["testuser"],
            "真实姓名": ["测试用户"],
            "邮箱": ["invalid-email"],  # 无效邮箱
        }
        df = pd.DataFrame(data)

        result = UserImportService.import_users(
            db=db,
            df=df,
            operator_id=operator.id,
            tenant_id=None,
        )

        # 应该验证失败
        assert result["failed_count"] > 0
        assert len(result["errors"]) > 0


class TestUserImportAPI:
    """用户导入API测试"""

    def test_download_template_xlsx(self, client: TestClient, superuser_token_headers: dict):
        """测试下载Excel模板"""
        response = client.get(
            "/api/v1/users/import/template?format=xlsx",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "user_import_template.xlsx" in response.headers.get("content-disposition", "")

    def test_download_template_csv(self, client: TestClient, superuser_token_headers: dict):
        """测试下载CSV模板"""
        response = client.get(
            "/api/v1/users/import/template?format=csv",
            headers=superuser_token_headers
        )
        
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "user_import_template.csv" in response.headers.get("content-disposition", "")

    def test_preview_import_valid_data(self, client: TestClient, superuser_token_headers: dict):
        """测试预览有效数据"""
        # 创建测试Excel文件
        df = pd.DataFrame({
            "用户名": ["preview1", "preview2"],
            "真实姓名": ["预览用户1", "预览用户2"],
            "邮箱": ["preview1@example.com", "preview2@example.com"],
        })
        
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)

        # 发送请求
        response = client.post(
            "/api/v1/users/import/preview",
            headers=superuser_token_headers,
            files={"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 2
        assert data["is_valid"] is True
        assert len(data["preview"]) == 2

    def test_preview_import_invalid_file(self, client: TestClient, superuser_token_headers: dict):
        """测试预览无效文件格式"""
        # 创建文本文件
        text_buffer = io.BytesIO(b"This is not an Excel file")
        
        response = client.post(
            "/api/v1/users/import/preview",
            headers=superuser_token_headers,
            files={"file": ("test.txt", text_buffer, "text/plain")}
        )

        assert response.status_code == 400
        assert "不支持的文件格式" in response.json()["detail"]

    def test_import_users_api(self, client: TestClient, superuser_token_headers: dict, db: Session):
        """测试批量导入API"""
        # 创建测试角色
        test_role = Role(
            role_code="API_TEST_ROLE",
            role_name="API测试角色",
            description="用于API测试的角色"
        )
        db.add(test_role)
        db.commit()
        
        # 创建测试Excel文件
        df = pd.DataFrame({
            "用户名": ["apitest1", "apitest2"],
            "真实姓名": ["API测试1", "API测试2"],
            "邮箱": ["apitest1@example.com", "apitest2@example.com"],
            "角色": [test_role.role_name, test_role.role_name],
        })
        
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_buffer.seek(0)

        # 发送请求
        response = client.post(
            "/api/v1/users/import",
            headers=superuser_token_headers,
            files={"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["success_count"] == 2
        assert data["failed_count"] == 0

        # 验证数据库
        user = db.query(User).filter(User.username == "apitest1").first()
        assert user is not None
        assert user.email == "apitest1@example.com"
