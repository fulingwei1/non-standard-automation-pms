# -*- coding: utf-8 -*-
"""
事件钩子系统

提供事件发布/订阅机制，允许插件在关键业务点注入自定义逻辑。

支持的事件类型：
- 同步事件：按顺序执行所有处理器
- 异步事件：并发执行所有处理器
- 过滤器：允许处理器修改数据

预定义事件：
- contract.creating / contract.created
- contract.updating / contract.updated
- contract.status_changing / contract.status_changed
- opportunity.creating / opportunity.created
- opportunity.stage_changing / opportunity.stage_changed
- quote.creating / quote.created
- quote.approving / quote.approved
- invoice.creating / invoice.created
- payment.received
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型"""

    SYNC = "sync"  # 同步事件
    ASYNC = "async"  # 异步事件
    FILTER = "filter"  # 过滤器（可修改数据）


@dataclass
class EventHook:
    """事件钩子"""

    name: str  # 事件名称
    handler: Callable  # 处理函数
    priority: int = 100  # 优先级（数字越小越先执行）
    event_type: EventType = EventType.SYNC  # 事件类型
    plugin_name: Optional[str] = None  # 所属插件名称
    description: str = ""  # 描述


@dataclass
class EventContext:
    """事件上下文"""

    event_name: str  # 事件名称
    data: Any  # 事件数据
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    cancelled: bool = False  # 是否已取消
    results: List[Any] = field(default_factory=list)  # 处理器返回结果

    def cancel(self) -> None:
        """取消事件（阻止后续处理器执行）"""
        self.cancelled = True


class HookManager:
    """
    钩子管理器

    负责事件的注册、触发和管理。

    Usage:
        manager = HookManager()

        # 注册钩子
        @manager.on("contract.created")
        def on_contract_created(ctx: EventContext):
            contract = ctx.data
            # 处理合同创建事件
            pass

        # 触发事件
        manager.emit("contract.created", contract)
    """

    def __init__(self):
        self._hooks: Dict[str, List[EventHook]] = {}
        self._enabled = True

    def register(
        self,
        event_name: str,
        handler: Callable,
        priority: int = 100,
        event_type: EventType = EventType.SYNC,
        plugin_name: Optional[str] = None,
        description: str = "",
    ) -> EventHook:
        """
        注册事件钩子

        Args:
            event_name: 事件名称
            handler: 处理函数
            priority: 优先级
            event_type: 事件类型
            plugin_name: 所属插件名称
            description: 描述

        Returns:
            注册的钩子对象
        """
        hook = EventHook(
            name=event_name,
            handler=handler,
            priority=priority,
            event_type=event_type,
            plugin_name=plugin_name,
            description=description,
        )

        if event_name not in self._hooks:
            self._hooks[event_name] = []

        self._hooks[event_name].append(hook)
        # 按优先级排序
        self._hooks[event_name].sort(key=lambda h: h.priority)

        logger.debug(f"注册钩子: {event_name} -> {handler.__name__}")
        return hook

    def unregister(
        self,
        event_name: str,
        handler: Optional[Callable] = None,
        plugin_name: Optional[str] = None,
    ) -> int:
        """
        注销事件钩子

        Args:
            event_name: 事件名称
            handler: 处理函数（可选，不指定则注销所有）
            plugin_name: 插件名称（可选，只注销该插件的钩子）

        Returns:
            注销的钩子数量
        """
        if event_name not in self._hooks:
            return 0

        original_count = len(self._hooks[event_name])

        if handler:
            self._hooks[event_name] = [
                h for h in self._hooks[event_name] if h.handler != handler
            ]
        elif plugin_name:
            self._hooks[event_name] = [
                h for h in self._hooks[event_name] if h.plugin_name != plugin_name
            ]
        else:
            self._hooks[event_name] = []

        removed_count = original_count - len(self._hooks[event_name])
        logger.debug(f"注销钩子: {event_name} (移除 {removed_count} 个)")
        return removed_count

    def unregister_plugin(self, plugin_name: str) -> int:
        """
        注销指定插件的所有钩子

        Args:
            plugin_name: 插件名称

        Returns:
            注销的钩子总数
        """
        total_removed = 0
        for event_name in list(self._hooks.keys()):
            total_removed += self.unregister(event_name, plugin_name=plugin_name)
        return total_removed

    def emit(
        self,
        event_name: str,
        data: Any = None,
        **metadata,
    ) -> EventContext:
        """
        触发同步事件

        Args:
            event_name: 事件名称
            data: 事件数据
            **metadata: 元数据

        Returns:
            事件上下文
        """
        ctx = EventContext(event_name=event_name, data=data, metadata=metadata)

        if not self._enabled:
            return ctx

        hooks = self._hooks.get(event_name, [])

        for hook in hooks:
            if ctx.cancelled:
                break

            try:
                result = hook.handler(ctx)
                if result is not None:
                    ctx.results.append(result)

            except Exception as e:
                logger.error(
                    f"钩子执行失败: {event_name} -> {hook.handler.__name__}: {e}",
                    exc_info=True,
                )

        return ctx

    async def emit_async(
        self,
        event_name: str,
        data: Any = None,
        **metadata,
    ) -> EventContext:
        """
        触发异步事件

        Args:
            event_name: 事件名称
            data: 事件数据
            **metadata: 元数据

        Returns:
            事件上下文
        """
        ctx = EventContext(event_name=event_name, data=data, metadata=metadata)

        if not self._enabled:
            return ctx

        hooks = self._hooks.get(event_name, [])

        # 分离同步和异步钩子
        sync_hooks = [h for h in hooks if h.event_type == EventType.SYNC]
        async_hooks = [h for h in hooks if h.event_type == EventType.ASYNC]

        # 先执行同步钩子
        for hook in sync_hooks:
            if ctx.cancelled:
                break
            try:
                result = hook.handler(ctx)
                if result is not None:
                    ctx.results.append(result)
            except Exception as e:
                logger.error(f"同步钩子执行失败: {hook.handler.__name__}: {e}")

        # 并发执行异步钩子
        if async_hooks and not ctx.cancelled:

            async def run_async_hook(hook):
                try:
                    if asyncio.iscoroutinefunction(hook.handler):
                        return await hook.handler(ctx)
                    else:
                        return hook.handler(ctx)
                except Exception as e:
                    logger.error(f"异步钩子执行失败: {hook.handler.__name__}: {e}")
                    return None

            results = await asyncio.gather(
                *[run_async_hook(h) for h in async_hooks], return_exceptions=True
            )
            ctx.results.extend([r for r in results if r is not None])

        return ctx

    def apply_filters(
        self,
        filter_name: str,
        value: Any,
        **context,
    ) -> Any:
        """
        应用过滤器链

        过滤器允许修改数据，每个处理器接收上一个处理器的输出。

        Args:
            filter_name: 过滤器名称
            value: 初始值
            **context: 上下文信息

        Returns:
            经过所有过滤器处理后的值
        """
        if not self._enabled:
            return value

        hooks = self._hooks.get(filter_name, [])
        current_value = value

        for hook in hooks:
            if hook.event_type != EventType.FILTER:
                continue

            try:
                result = hook.handler(current_value, **context)
                if result is not None:
                    current_value = result
            except Exception as e:
                logger.error(
                    f"过滤器执行失败: {filter_name} -> {hook.handler.__name__}: {e}"
                )

        return current_value

    def on(
        self,
        event_name: str,
        priority: int = 100,
        event_type: EventType = EventType.SYNC,
    ) -> Callable:
        """
        装饰器：注册事件钩子

        Usage:
            @hook_manager.on("contract.created")
            def handle_contract(ctx: EventContext):
                pass
        """

        def decorator(func: Callable) -> Callable:
            self.register(
                event_name=event_name,
                handler=func,
                priority=priority,
                event_type=event_type,
            )
            return func

        return decorator

    def filter(self, filter_name: str, priority: int = 100) -> Callable:
        """
        装饰器：注册过滤器

        Usage:
            @hook_manager.filter("quote.amount")
            def apply_discount(amount, **ctx):
                return amount * 0.9
        """

        def decorator(func: Callable) -> Callable:
            self.register(
                event_name=filter_name,
                handler=func,
                priority=priority,
                event_type=EventType.FILTER,
            )
            return func

        return decorator

    def get_hooks(self, event_name: Optional[str] = None) -> Dict[str, List[EventHook]]:
        """
        获取已注册的钩子

        Args:
            event_name: 事件名称（可选，不指定返回所有）

        Returns:
            钩子字典
        """
        if event_name:
            return {event_name: self._hooks.get(event_name, [])}
        return self._hooks.copy()

    def list_events(self) -> List[str]:
        """列出所有已注册的事件名称"""
        return list(self._hooks.keys())

    def enable(self) -> None:
        """启用钩子系统"""
        self._enabled = True

    def disable(self) -> None:
        """禁用钩子系统"""
        self._enabled = False

    def is_enabled(self) -> bool:
        """检查钩子系统是否启用"""
        return self._enabled


# 全局钩子管理器实例
_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """获取全局钩子管理器实例"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager


def hook(
    event_name: str,
    priority: int = 100,
    event_type: EventType = EventType.SYNC,
) -> Callable:
    """
    便捷装饰器：注册事件钩子到全局管理器

    Usage:
        @hook("contract.created")
        def on_contract_created(ctx: EventContext):
            pass
    """

    def decorator(func: Callable) -> Callable:
        manager = get_hook_manager()
        manager.register(
            event_name=event_name,
            handler=func,
            priority=priority,
            event_type=event_type,
        )
        return func

    return decorator


# 预定义事件常量
class SalesEvents:
    """销售模块预定义事件"""

    # 合同事件
    CONTRACT_CREATING = "contract.creating"
    CONTRACT_CREATED = "contract.created"
    CONTRACT_UPDATING = "contract.updating"
    CONTRACT_UPDATED = "contract.updated"
    CONTRACT_STATUS_CHANGING = "contract.status_changing"
    CONTRACT_STATUS_CHANGED = "contract.status_changed"

    # 商机事件
    OPPORTUNITY_CREATING = "opportunity.creating"
    OPPORTUNITY_CREATED = "opportunity.created"
    OPPORTUNITY_STAGE_CHANGING = "opportunity.stage_changing"
    OPPORTUNITY_STAGE_CHANGED = "opportunity.stage_changed"
    OPPORTUNITY_WON = "opportunity.won"
    OPPORTUNITY_LOST = "opportunity.lost"

    # 报价事件
    QUOTE_CREATING = "quote.creating"
    QUOTE_CREATED = "quote.created"
    QUOTE_APPROVING = "quote.approving"
    QUOTE_APPROVED = "quote.approved"
    QUOTE_REJECTED = "quote.rejected"

    # 发票事件
    INVOICE_CREATING = "invoice.creating"
    INVOICE_CREATED = "invoice.created"
    INVOICE_SENT = "invoice.sent"

    # 付款事件
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_OVERDUE = "payment.overdue"


# 预定义过滤器常量
class SalesFilters:
    """销售模块预定义过滤器"""

    QUOTE_AMOUNT = "quote.amount"  # 报价金额
    QUOTE_MARGIN = "quote.margin"  # 报价毛利
    CONTRACT_TERMS = "contract.terms"  # 合同条款
    DISCOUNT_RATE = "discount.rate"  # 折扣率
    WIN_PROBABILITY = "opportunity.win_probability"  # 赢单概率
