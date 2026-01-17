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
    - 以 data/app.db 为模板复制一个临时数据库文件，保留完整 schema
    - 清空测试涉及的表，保证数据干净
    - 每个测试函数独享数据库文件，互不影响
    """
    template_path = Path(os.getenv("UNIT_TEST_DB_TEMPLATE", "data/app.db"))
    if not template_path.exists():
        raise FileNotFoundError(f"无法找到基准数据库文件：{template_path}")

    tmp_db = tempfile.NamedTemporaryFile(suffix=".db")
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
