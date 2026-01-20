# -*- coding: utf-8 -*-
"""
测试数据库连接和初始化

验证测试环境是否正确配置
"""

import pytest
from pathlib import Path


@pytest.mark.unit
@pytest.mark.database
class TestDatabaseConnection:
    """数据库连接测试"""

    def test_database_file_exists(self):
        """测试数据库文件存在"""
        db_path = Path("data/app.db")
        assert db_path.exists(), "Database file not found at data/app.db"

    def test_database_not_empty(self):
        """测试数据库不为空"""
        db_path = Path("data/app.db")
        size = db_path.stat().st_size
        assert size > 0, "Database file is empty"

    def test_app_models_importable(self):
        """测试应用模型可导入"""
        try:
            from app.models.user import User
            from app.models.project import Project
            from app.models.base import Base

            print("✓ All models imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import models: {e}")

    def test_engine_creation(self):
        """测试数据库引擎创建"""
        try:
            from app.models.base import get_engine

            engine = get_engine()
            assert engine is not None, "Engine creation failed"
            print(f"✓ Engine created successfully: {engine.dialect.name}")
        except Exception as e:
            pytest.fail(f"Engine creation failed: {e}")

    def test_session_creation(self):
        """测试数据库会话创建"""
        try:
            from app.models.base import SessionLocal

            session = SessionLocal()
            assert session is not None, "Session creation failed"
            session.close()
            print("✓ Session created successfully")
        except Exception as e:
            pytest.fail(f"Session creation failed: {e}")


@pytest.mark.integration
class TestBasicAPIConnection:
    """基本 API 连接测试"""

    def test_import_fastapi(self):
        """测试FastAPI可导入"""
        try:
            from fastapi import FastAPI

            print("✓ FastAPI imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import FastAPI: {e}")

    def test_import_test_client(self):
        """测试TestClient可导入"""
        try:
            from fastapi.testclient import TestClient

            print("✓ TestClient imported successfully")
        except ImportError as e:
            pytest.fail(f"Failed to import TestClient: {e}")
