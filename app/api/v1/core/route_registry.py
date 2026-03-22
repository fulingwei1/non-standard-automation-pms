# -*- coding: utf-8 -*-
"""
路由自动发现与注册工具
递归扫描 app/api/v1/endpoints/ 下所有暴露 `router` 属性的模块并批量注册。
"""
import importlib
import logging
import pkgutil
from dataclasses import dataclass
from typing import List

from fastapi import APIRouter

logger = logging.getLogger(__name__)

_ENDPOINTS_PACKAGE = "app.api.v1.endpoints"  # 扫描的根包路径

# 需要跳过的模块（辅助模块、基类等，不含路由）
_SKIP_MODULES: frozenset[str] = frozenset({
    "_shared", "base_crud_router", "base_crud_router_sync",
})
# 必须最后注册的模块（stub 兜底路由，顺序敏感）
_LAST_MODULES: tuple[str, ...] = ("stub_endpoints",)


@dataclass(frozen=True)
class DiscoveredRouter:
    """记录一个被发现的路由及其来源模块"""
    module_path: str
    router: APIRouter


def discover_routers() -> List[DiscoveredRouter]:
    """递归扫描 endpoints 包，收集所有含 `router` 属性的模块。

    规则：跳过 _SKIP_MODULES 和下划线开头的私有模块；
    _LAST_MODULES 中的模块延迟到最后，保证 stub 兜底。
    """
    try:
        root_pkg = importlib.import_module(_ENDPOINTS_PACKAGE)
    except ImportError:
        logger.error("无法导入 endpoints 根包: %s", _ENDPOINTS_PACKAGE)
        return []

    routers: list[DiscoveredRouter] = []
    deferred: list[DiscoveredRouter] = []  # stub 等需要最后注册的路由

    # walk_packages 递归遍历子包和模块
    for _importer, module_name, _is_pkg in pkgutil.walk_packages(
        root_pkg.__path__, prefix=f"{_ENDPOINTS_PACKAGE}.",
    ):
        short_name = module_name.rsplit(".", maxsplit=1)[-1]  # 取末段做黑名单匹配
        if short_name in _SKIP_MODULES or short_name.startswith("_"):
            continue

        try:
            mod = importlib.import_module(module_name)
        except Exception:
            # 导入失败只记警告，不中断启动流程
            logger.warning("跳过模块 %s（导入失败）", module_name, exc_info=True)
            continue

        router_attr = getattr(mod, "router", None)
        if not isinstance(router_attr, APIRouter):
            continue

        entry = DiscoveredRouter(module_path=module_name, router=router_attr)
        if short_name in _LAST_MODULES:
            deferred.append(entry)
        else:
            routers.append(entry)

    routers.extend(deferred)  # 延迟路由追加到末尾
    logger.info("共发现 %d 个路由模块", len(routers))
    return routers


def register_all(parent_router: APIRouter) -> int:
    """将所有发现的路由注册到 parent_router。

    各 endpoint 模块的 router 应已自带 prefix/tags，
    此处以空 prefix 挂载，避免重复拼接路径。
    返回成功注册的数量。
    """
    discovered = discover_routers()
    registered = 0
    for entry in discovered:
        try:
            parent_router.include_router(entry.router)
            logger.info("✓ 已注册: %s", entry.module_path)
            registered += 1
        except Exception:
            logger.error("✗ 注册失败: %s", entry.module_path, exc_info=True)

    logger.info("路由注册完成: %d/%d 成功", registered, len(discovered))
    return registered
