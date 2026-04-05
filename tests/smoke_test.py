"""
冒烟测试 (Smoke Test)

快速验证系统核心功能是否正常，确保基本可用性。
执行时间：5-10 分钟

运行方式：
    pytest tests/smoke_test.py -v

或者包含输出：
    pytest tests/smoke_test.py -v -s
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestCoreModels:
    """核心模型测试"""

    def test_import_models(self):
        """验证核心模型可以导入"""
        try:
            from app.models.user import User
            from app.models.project import Project
            from app.models.timesheet import Timesheet
            assert True
        except ImportError as e:
            pytest.fail(f"模型导入失败：{e}")


class TestDatabaseConnection:
    """数据库连接测试"""

    def test_database_connection(self):
        """验证数据库连接正常"""
        from app.core.database import get_db
        from app.models.user import User
        
        db = next(get_db())
        try:
            # 尝试查询用户表
            count = db.query(User).count()
            assert count >= 0, "数据库查询成功"
        except Exception as e:
            pytest.fail(f"数据库连接失败：{e}")
        finally:
            db.close()


class TestAPIEndpoints:
    """核心 API 端点测试"""

    def test_health_check(self):
        """健康检查端点"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"

    def test_openapi_schema(self):
        """OpenAPI 文档可访问"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data


class TestAuthentication:
    """认证模块测试"""

    def test_jwt_token_generation(self):
        """JWT 令牌生成"""
        from app.core.security import create_access_token
        
        token = create_access_token(data={"sub": "test_user"})
        assert token is not None
        assert len(token) > 50

    def test_password_hashing(self):
        """密码哈希"""
        from app.core.security import verify_password, get_password_hash
        
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed)


class TestCoreServices:
    """核心服务测试"""

    def test_user_service(self):
        """用户服务基本功能"""
        from app.services.user_service import UserService
        from app.core.database import get_db
        
        service = UserService()
        db = next(get_db())
        
        try:
            # 获取用户列表
            users = service.get_users(db, skip=0, limit=10)
            assert users is not None
        except Exception as e:
            pytest.fail(f"用户服务失败：{e}")
        finally:
            db.close()

    def test_project_service(self):
        """项目服务基本功能"""
        from app.services.project_service import ProjectService
        from app.core.database import get_db
        
        service = ProjectService()
        db = next(get_db())
        
        try:
            # 获取项目列表
            projects = service.get_projects(db, skip=0, limit=10)
            assert projects is not None
        except Exception as e:
            pytest.fail(f"项目服务失败：{e}")
        finally:
            db.close()


class TestConfiguration:
    """配置加载测试"""

    def test_settings_load(self):
        """验证配置正确加载"""
        from app.core.config import settings
        
        assert settings.DATABASE_URL is not None
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) >= 32


class TestUtilities:
    """工具函数测试"""

    def test_logger_configured(self):
        """日志系统配置"""
        import logging
        
        logger = logging.getLogger("app")
        assert logger is not None
        assert logger.handlers is not None


# ============================================
# 冒烟测试执行入口
# ============================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--maxfail=3",  # 最多 3 个失败就停止
        "-x"  # 第一个失败就停止
    ])
