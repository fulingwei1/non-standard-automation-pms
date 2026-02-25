# -*- coding: utf-8 -*-
"""
租户过滤Query类 - 框架级强制租户隔离

这个模块实现了自动租户过滤的Query类，确保所有数据库查询自动添加 tenant_id 条件，
从而在框架层面强制执行多租户数据隔离。

核心特性：
1. 自动过滤：所有查询自动添加 tenant_id 条件
2. 超级管理员支持：tenant_id=None 且 is_superuser=True 的用户可访问所有数据
3. 防御性编程：无效状态会抛出异常，防止数据泄露
4. 性能优化：查询编译时自动添加条件，无需手动处理

技术实现：
- 继承 SQLAlchemy 的 Query 类
- 重写 __iter__ 方法在查询执行前自动添加过滤条件
- 使用上下文变量获取当前租户信息
- 支持禁用自动过滤（用于系统级操作）

使用场景：
- 所有业务查询自动隔离
- 防止开发人员遗漏租户过滤
- 简化代码，减少重复逻辑

Author: Team 3 - 租户隔离小组
Date: 2026-02-16
"""

import logging

from sqlalchemy.orm import Query

from app.core.middleware.tenant_middleware import get_current_tenant_id

logger = logging.getLogger(__name__)


class TenantQuery(Query):
    """
    自动添加租户过滤的Query类
    
    这个类会在查询执行前自动检查模型是否有 tenant_id 字段，
    如果有则自动添加过滤条件，确保数据隔离。
    
    特殊情况处理：
    1. 超级管理员（tenant_id=None 且 is_superuser=True）可以访问所有数据
    2. 系统级资源（模型没有 tenant_id 字段）不受影响
    3. 可以通过 _skip_tenant_filter 属性禁用自动过滤
    
    使用方法：
        # 自动过滤（推荐）
        projects = db.query(Project).filter(Project.status == "active").all()
        
        # 禁用自动过滤（谨慎使用）
        query = db.query(Project)
        query._skip_tenant_filter = True
        all_projects = query.all()
    """
    
    def __iter__(self):
        """
        重写迭代器方法，在查询执行前自动添加租户过滤
        
        这个方法会在查询实际执行时被调用（例如 .all(), .first(), list(query) 等）
        我们在这里统一添加租户过滤条件，确保不会遗漏。
        """
        # 检查是否显式禁用自动过滤
        if getattr(self, '_skip_tenant_filter', False):
            logger.debug("Tenant filter explicitly disabled for this query")
            return super().__iter__()
        
        # 应用租户过滤
        return self._apply_tenant_filter().__iter__()
    
    def _apply_tenant_filter(self):
        """
        应用租户过滤逻辑
        
        核心逻辑：
        1. 获取当前租户ID
        2. 检查模型是否有 tenant_id 字段
        3. 验证用户权限
        4. 添加过滤条件
        
        Returns:
            Query: 添加过滤条件后的查询对象
        """
        # 获取当前租户ID
        tenant_id = get_current_tenant_id()
        
        # 获取查询的模型类
        # column_descriptions 包含查询中所有实体的信息
        if not self.column_descriptions:
            logger.debug("No column descriptions, skipping tenant filter")
            return self
        
        model = self.column_descriptions[0].get('type')
        if model is None:
            logger.debug("No model type found, skipping tenant filter")
            return self
        
        # 检查模型是否有 tenant_id 字段
        if not hasattr(model, 'tenant_id'):
            logger.debug(f"Model {model.__name__} has no tenant_id field, skipping filter")
            return self
        
        # 处理超级管理员
        if tenant_id is None:
            # tenant_id=None 只允许超级管理员
            # 这里我们需要从上下文获取用户信息
            user = self._get_current_user_from_context()
            
            if user is None:
                # 未认证用户，可能是系统初始化或公开API
                logger.warning(
                    f"Query on {model.__name__} with no tenant_id and no authenticated user. "
                    "This may be a system operation."
                )
                return self
            
            if not getattr(user, 'is_superuser', False):
                # 非超级管理员却没有 tenant_id，这是无效状态
                error_msg = (
                    f"Invalid user state: user_id={user.id}, tenant_id=None, "
                    f"is_superuser=False. Cannot query {model.__name__}."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # 超级管理员，允许访问所有数据
            logger.debug(
                f"Superuser {user.id} accessing {model.__name__} without tenant filter"
            )
            return self
        
        # 普通用户，添加租户过滤
        logger.debug(
            f"Applying tenant filter: model={model.__name__}, tenant_id={tenant_id}"
        )
        
        # 检查是否已经有 tenant_id 过滤条件
        # 避免重复添加
        filter_applied = self._has_tenant_filter(model)
        if filter_applied:
            logger.debug(f"Tenant filter already applied for {model.__name__}")
            return self
        
        # 添加租户过滤条件
        return self.filter(model.tenant_id == tenant_id)
    
    def _get_current_user_from_context(self):
        """
        从请求上下文获取当前用户
        
        这个方法尝试从FastAPI的请求状态中获取用户信息。
        在某些情况下（如后台任务、测试），可能获取不到。
        
        Returns:
            User对象或None
        """
        try:
            from starlette_context import context
            
            # 尝试从starlette-context获取
            request = context.get('request', None)
            if request and hasattr(request.state, 'user'):
                return request.state.user
        except (ImportError, LookupError, RuntimeError):
            pass
        
        # 尝试从数据库会话的info字段获取（如果设置了）
        try:
            if hasattr(self.session, 'info') and 'current_user' in self.session.info:
                return self.session.info['current_user']
        except Exception:
            pass
        
        return None
    
    def _has_tenant_filter(self, model) -> bool:
        """
        检查查询是否已经包含 tenant_id 过滤条件
        
        Args:
            model: SQLAlchemy模型类
            
        Returns:
            bool: 是否已经有租户过滤
        """
        try:
            # 获取查询的 WHERE 子句
            whereclause = self.whereclause
            if whereclause is None:
                return False
            
            # 检查是否包含 tenant_id 列
            # 这是一个简化的检查，实际可能需要更复杂的逻辑
            whereclause_str = str(whereclause.compile(compile_kwargs={"literal_binds": True}))
            return 'tenant_id' in whereclause_str
        except Exception as e:
            logger.debug(f"Error checking tenant filter: {e}")
            return False
    
    def skip_tenant_filter(self):
        """
        禁用自动租户过滤
        
        这个方法应该谨慎使用，仅用于以下场景：
        1. 系统管理员操作
        2. 数据迁移脚本
        3. 跨租户统计
        
        Returns:
            Query: 返回自身，支持链式调用
        
        Example:
            # 获取所有租户的项目数量
            total = db.query(Project).skip_tenant_filter().count()
        """
        self._skip_tenant_filter = True
        logger.warning("Tenant filter disabled for this query - ensure this is intentional")
        return self


def create_tenant_aware_session(session_class):
    """
    创建租户感知的Session类
    
    这个函数用于在测试或特殊场景中创建临时的租户感知Session。
    
    Args:
        session_class: 基础Session类
        
    Returns:
        配置了TenantQuery的Session类
    """
    from sqlalchemy.orm import sessionmaker
    
    return sessionmaker(
        bind=session_class.kw.get('bind'),
        query_cls=TenantQuery,
        autocommit=False,
        autoflush=False,
    )


# 导出公共接口
__all__ = [
    'TenantQuery',
    'create_tenant_aware_session',
]
