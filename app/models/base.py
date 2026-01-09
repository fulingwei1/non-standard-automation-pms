# -*- coding: utf-8 -*-
"""
数据库基础配置和基类模型
"""

import os
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, DateTime, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import StaticPool

# 创建基类
Base = declarative_base()

# 全局引擎和会话工厂
_engine = None
_SessionLocal = None


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
    # 优先使用环境变量
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
