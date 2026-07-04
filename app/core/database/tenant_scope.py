# -*- coding: utf-8 -*-
"""
TEN-02: 框架级租户查询过滤（SQLAlchemy 2.0 正确实现）

原 `tenant_query.py` 的 `TenantQuery` 只重写了 `__iter__`，但 SQLAlchemy 2.0 的
`Query.all()/.first()/.one()/.count()/.scalar()` 等常用方法都不经过 `__iter__`
（直接调用内部 `_iter()`），导致该过滤在实践中形同虚设——本仓库对这些方法的调用
数以千计，逐一验证过 `.all()` 之类的方法确实绕过了旧实现。

本模块改用 SQLAlchemy 2.0 官方推荐的 `Session.do_orm_execute` 事件 +
`with_loader_criteria` 全局条件，在查询编译阶段统一注入过滤条件，覆盖所有执行
方式（`.all()/.first()/.one()/.count()/.scalar()/for row in query` 等）。参考
了本仓库 `app/models/progress.py` 中 `_project_task_global_criteria` 的既有实现
模式（同一 SQLAlchemy 版本下已验证可用）。

**关键实现坑（已用最小复现脚本逐一验证，务必保留这个写法，不要"优化"回调用式）**：

1. `with_loader_criteria` 的可调用（callable）参数会被 SQLAlchemy 的
   "lambda SQL" 缓存系统接管：
   - 闭包体内调用外部函数（例如我们自己的 get_current_tenant_id() 等
     ContextVar getter）会被直接拒绝，抛 `InvalidRequestError`。
   - 闭包体内依赖闭包变量做 if/else 分支来决定返回哪种结构不同的 SQL
     表达式，同样会被拒绝（"closure variable ... does not refer to a
     cacheable SQL element"）。
   - 更隐蔽的一个坑：即使用"默认参数值"承载动态字面量（官方文档推荐的写法）
     绕过了上面两个报错，只要这个内层函数是在事件回调里通过 `def` 语句
     **反复重新定义**的，SQLAlchemy 仍可能对结构相同（相同 `__code__`）的
     多次调用复用了第一次编译时缓存的绑定值——导致同一进程内、不同请求/
     不同租户上下文的查询，`.first()` 这类方法拿到*上一次*请求缓存下来的
     _tid，而不是当前请求的真实值（已用两次不同 tenant_id 连续查询复现，
     这是能直接导致跨租户数据泄露的级别的 bug，不是性能问题）。

   唯一验证过安全、且在同一进程内反复用不同租户 ID 连续查询也能正确更新的
   写法：**不要传可调用对象，直接传"计算好的普通 SQL 表达式"**
   （`ModelClass.tenant_id == tenant_id`，不包在任何函数/lambda 里）。因为
   `with_loader_criteria` 只有传入 callable 时才会进入上面这套"lambda SQL"
   缓存机制，传普通表达式则每次都是全新对象，不存在缓存复用的问题。

2. 因此本实现放弃"用一个回调函数处理任意 Base 子类"的写法，改为在事件
   回调里枚举当前已知的、真正带 tenant_id 字段的 mapped class（通过
   `Base.registry.mappers` 反射得到，新增模型只要声明了 tenant_id 就会
   自动被后续查询覆盖，无需手工登记），对每一个都注册一条独立的、值已经
   算好的 `with_loader_criteria`。`with_loader_criteria` 对当前查询没有
   涉及的实体类是零成本的（不会产生额外 JOIN，只在该实体真正出现在查询
   中时才生效），枚举 20 个左右的类不会带来可感知的开销。

行为语义（保留原 TenantQuery 的设计意图，仅修复其失效的技术实现）：
- 无 tenant_id 字段的模型：不受影响。
- 已认证且有租户的用户：按 tenant_id 过滤；对 _SHARED_WHEN_NULL_MODELS 里的
  模型额外放行 tenant_id IS NULL 的行（见下方说明）。
- 超级管理员（tenant_id=None）：跨租户不过滤（TEN-06 既定设计）。
- 无请求上下文（后台任务/脚本/未认证白名单请求）：不过滤，视为系统级调用。
- 已认证非超管但无租户（不应出现的存量异常状态）：按 TENANT_ENFORCE_MODE
  与请求层 TEN-06 保持一致——strict 下过滤到空结果（fail-closed），
  log（灰度默认）下不过滤但记告警。

**tenant_id 可空模型里的"NULL=共享"陷阱**（已用真实回归测试复现）：
`Role`/`ApiPermission`/`DataScopeRule`/`MenuPermission` 这几张表的
`tenant_id` 允许为 NULL，但 NULL 在这里的业务含义是"系统级/全租户共享的
默认配置"（例如系统内置角色、内置权限目录），不是"不属于任何租户"。
`User.tenant_id IS NULL` 则是完全不同的语义——超级管理员账号，不应被当作
"共享数据"泄露给普通租户查询。如果对这几张共享配置表也用严格的
`tenant_id == X` 相等过滤，会把系统内置角色/权限/菜单一并过滤掉，导致
`tests/api/test_role_tenant_isolation_contracts.py::test_tenant_role_list_and_detail_are_scoped`
这类既有回归测试失败（已实测复现）。因此对这几张表改用
`(tenant_id == X) OR (tenant_id IS NULL)`，其余模型维持严格相等。

当前生产代码没有需要绕过此过滤的真实场景，故不提供逃生舱（原 TenantQuery 的
`_skip_tenant_filter` 属性随旧实现一并移除）。
"""

import logging

from sqlalchemy import event, false, or_
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.orm import with_loader_criteria

from app.core.middleware.tenant_middleware import (
    get_current_tenant_id,
    get_current_user_is_superuser,
    get_enforce_mode,
)
from app.models.base import Base

logger = logging.getLogger(__name__)

_tenant_scoped_classes_cache = None

# 这几张表的 tenant_id=NULL 表示"系统级/全租户共享"，不是"不属于任何租户"
# （Role/ApiPermission/DataScopeRule 的模型 docstring 明确写了这个约定，
# ApiPermission/DataScopeRule/MenuPermission 三者原文一致："NULL=系统级
# XX，所有租户共享"；Role 本身虽未在 docstring 写明，但
# test_role_tenant_isolation_contracts.py 的既有回归用例证实了同样约定）。
# 未在此列表的可空 tenant_id 模型（如 User：NULL=超级管理员账号）维持严格
# 相等过滤，不把 NULL 行当共享数据放行。
_SHARED_WHEN_NULL_MODEL_NAMES = frozenset({"Role", "ApiPermission", "DataScopeRule", "MenuPermission"})


def _tenant_scoped_classes():
    """返回所有真正带 tenant_id 字段的 mapped class（惰性缓存，模型集合在
    进程生命周期内不会变化，无需每次查询都重新反射整个 registry）。"""
    global _tenant_scoped_classes_cache
    if _tenant_scoped_classes_cache is None:
        _tenant_scoped_classes_cache = [
            mapper.class_
            for mapper in Base.registry.mappers
            if hasattr(mapper.class_, "tenant_id")
        ]
    return _tenant_scoped_classes_cache


@event.listens_for(OrmSession, "do_orm_execute")
def _apply_tenant_query_filter(execute_state):
    """所有经 ORM 的 SELECT 查询自动按当前租户上下文过滤（TEN-02）。"""
    if not (
        execute_state.is_select
        and not execute_state.is_column_load
        and not execute_state.is_relationship_load
    ):
        return

    tenant_id = get_current_tenant_id()
    if tenant_id is not None:
        options = []
        for cls in _tenant_scoped_classes():
            if cls.__name__ in _SHARED_WHEN_NULL_MODEL_NAMES:
                criteria = or_(cls.tenant_id == tenant_id, cls.tenant_id.is_(None))
            else:
                criteria = cls.tenant_id == tenant_id
            options.append(with_loader_criteria(cls, criteria, include_aliases=True))
        execute_state.statement = execute_state.statement.options(*options)
        return

    is_superuser = get_current_user_is_superuser()
    if is_superuser is None or is_superuser:
        # 无请求上下文（后台任务/脚本/未认证白名单请求）或超级管理员：不过滤
        return

    # 已认证非超管却没有租户——不应出现的存量异常状态，与 TEN-06 请求层口径一致
    if get_enforce_mode() != "strict":
        logger.warning(
            "Tenant fail-open(灰度) at query layer: non-superuser with no "
            "tenant_id（TENANT_ENFORCE_MODE=strict 后将返回空结果）"
        )
        return

    logger.error("Tenant fail-closed at query layer: non-superuser with no tenant_id")
    options = [
        with_loader_criteria(cls, false(), include_aliases=True)
        for cls in _tenant_scoped_classes()
    ]
    execute_state.statement = execute_state.statement.options(*options)
