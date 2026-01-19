"""
Unit tests fixtures - 不依赖完整应用程序
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_engine():
    """
    为单元测试提供隔离的 SQLite 引擎：
    - 优先使用 data/test_app.db（由主 conftest 创建）
    - 如果不存在则使用 data/app.db 作为模板
    - 清空测试涉及的表，保证数据干净
    - 每个测试函数独享数据库文件，互不影响
    """
    # 优先使用 test_app.db（由主 conftest 创建），其次使用 app.db
    test_db_path = Path("data/test_app.db")
    app_db_path = Path("data/app.db")
    env_template = os.getenv("UNIT_TEST_DB_TEMPLATE", "")
    template_path = Path(env_template) if env_template else None

    if template_path and template_path.exists() and template_path.is_file():
        pass  # 使用环境变量指定的模板
    elif test_db_path.exists() and test_db_path.is_file():
        template_path = test_db_path
    elif app_db_path.exists() and app_db_path.is_file():
        template_path = app_db_path
    else:
        # 如果都不存在，创建一个内存数据库并初始化表结构
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        # 导入所有模型以确保表结构被注册
        import app.models  # noqa: F401
        from app.models.base import Base
        Base.metadata.create_all(bind=engine)
        yield engine
        engine.dispose()
        return

    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    shutil.copyfile(template_path, tmp_db.name)

    engine = create_engine(
        f"sqlite:///{tmp_db.name}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        # Clean up test tables
        try:
            conn.execute(text("DELETE FROM task_unified"))
        except Exception:
            pass  # Table may not exist
        try:
            conn.execute(text("DELETE FROM projects"))
        except Exception:
            pass
        try:
            conn.execute(text("DELETE FROM project_stages"))
        except Exception:
            pass
        # 清理员工表中的非标准格式编码（用于编号生成测试）
        try:
            conn.execute(text("DELETE FROM employees WHERE employee_code LIKE 'EMP-%'"))
        except Exception:
            pass
        # 清理客户表中的测试数据
        try:
            conn.execute(text("DELETE FROM customers WHERE customer_code LIKE 'CUS-%'"))
        except Exception:
            pass
        # Reset auto-increment counters if sqlite_sequence table exists
        try:
            conn.execute(
                text(
                    "DELETE FROM sqlite_sequence "
                    "WHERE name IN ('task_unified', 'projects', 'project_stages')"
                )
            )
        except Exception:
            pass  # sqlite_sequence may not exist if no AUTOINCREMENT columns were used
        conn.execute(text("PRAGMA foreign_keys=ON"))

    yield engine

    engine.dispose()
    tmp_db.close()
    try:
        os.unlink(tmp_db.name)
    except Exception:
        pass


@pytest.fixture(scope="function")
def db_session(db_engine) -> Session:
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
