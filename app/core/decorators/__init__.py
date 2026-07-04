# -*- coding: utf-8 -*-
"""
装饰器模块

原租户隔离装饰器（require_tenant_isolation/allow_cross_tenant/
tenant_resource_check）已随 TEN-05 删除：全仓零真实调用点，租户隔离
统一由 TEN-02 的框架级查询过滤（app/core/database/tenant_scope.py）承担。
"""
