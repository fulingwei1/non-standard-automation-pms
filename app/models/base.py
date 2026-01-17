# -*- coding: utf-8 -*-
"""
数据库基础配置和基类模型
"""

import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, create_engine, event, inspect, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# 创建基类
Base = declarative_base()

# 全局引擎和会话工厂
_engine = None
_SessionLocal = None

logger = logging.getLogger(__name__)


def _ensure_sqlite_schema(engine):
    """
    通过轻量的DDL补丁，确保SQLite数据库包含关键字段。
    避免由于历史数据库版本导致的列缺失。
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    # Many models use TimestampMixin (created_at/updated_at). Historical SQLite
    # databases or hand-written migration scripts may omit these columns for
    # some tables, which can cause runtime 500s when ORM queries select/order
    # by them. We patch missing timestamp columns opportunistically.
    for table_name in tables:
        columns = None
        try:
            columns = {col["name"] for col in inspector.get_columns(table_name)}
        except Exception:
            logger.debug("无法读取 SQLite 表字段信息，已跳过", exc_info=True)
        if columns is None:
            continue

        statements = []
        if "created_at" not in columns:
            statements.append(
                f"ALTER TABLE {table_name} "
                "ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            )
        if "updated_at" not in columns:
            statements.append(
                f"ALTER TABLE {table_name} "
                "ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            )

        if statements:
            with engine.begin() as conn:
                for ddl in statements:
                    try:
                        conn.execute(text(ddl))
                    except Exception:
                        # Best-effort patching; some tables/views may not be alterable.
                        logger.debug("SQLite DDL 补丁执行失败，已忽略", exc_info=True)

    if "project_statuses" in tables:
        columns = [col["name"] for col in inspector.get_columns("project_statuses")]
        if "updated_at" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE project_statuses "
                        "ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                    )
                )
    if "task_unified" in tables:
        columns = [col["name"] for col in inspector.get_columns("task_unified")]
        if "is_active" not in columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE task_unified "
                        "ADD COLUMN is_active BOOLEAN DEFAULT 1"
                    )
                )


class TimestampMixin:
    """时间戳混入类，提供创建时间和更新时间字段"""

    created_at = Column(
        DateTime, default=datetime.now, nullable=False, comment="创建时间"
    )
    updated_at = Column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
        comment="更新时间",
    )


def get_database_url() -> str:
    """获取数据库连接URL"""
    # 优先使用 Vercel Postgres
    postgres_url = os.getenv("POSTGRES_URL")
    if postgres_url:
        return postgres_url

    # 其次使用 DATABASE_URL（兼容 Railway 等其他服务）
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # 默认使用SQLite
    db_path = os.getenv("SQLITE_DB_PATH", "data/app.db")
    return f"sqlite:///{db_path}"


def get_engine(database_url: Optional[str] = None, echo: bool = False):
    """
    获取数据库引擎

    Args:
        database_url: 数据库连接URL，默认从环境变量获取
        echo: 是否打印SQL语句

    Returns:
        SQLAlchemy引擎实例
    """
    global _engine

    if _engine is not None:
        return _engine

    url = database_url or get_database_url()

    # SQLite特殊配置
    if url.startswith("sqlite"):
        _engine = create_engine(
            url,
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        # SQLite启用外键约束
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        _ensure_sqlite_schema(_engine)
    elif url.startswith("postgres"):
        # PostgreSQL 配置（Vercel Postgres）
        _engine = create_engine(
            url,
            echo=echo,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
            pool_pre_ping=True,
        )
    else:
        # MySQL配置
        _engine = create_engine(
            url,
            echo=echo,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True,
        )

    return _engine


def get_session_factory():
    """获取session工厂"""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


SessionLocal = get_session_factory()


def get_session() -> Session:
    """获取数据库会话"""
    return SessionLocal()


def get_db():
    """
    FastAPI 依赖使用的数据库会话生成器
    """
    db = get_session()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    数据库会话上下文管理器

    Usage:
        with get_db_session() as session:
            session.query(User).all()
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(database_url: Optional[str] = None, drop_all: bool = False):
    """
    初始化数据库，创建所有表

    Args:
        database_url: 数据库连接URL
        drop_all: 是否先删除所有表
    """
    engine = get_engine(database_url)

    if drop_all:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    return engine


def reset_engine():
    """重置引擎（用于测试）"""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
