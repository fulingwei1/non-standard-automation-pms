# -*- coding: utf-8 -*-
"""
请求上下文模块全面测试

测试 app/common/context.py 中的所有函数
"""
import pytest
from app.common.context import (
    set_audit_context,
    get_audit_context,
    clear_audit_context,
    get_current_tenant_id,
    set_current_tenant_id,
    operator_id_ctx,
    client_ip_ctx,
    user_agent_ctx,
    audit_detail_ctx,
    tenant_id_ctx,
)


class TestAuditContext:
    """测试审计上下文功能"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_audit_context()
    
    def teardown_method(self):
        """每个测试后清理上下文"""
        clear_audit_context()
    
    def test_set_and_get_全部字段(self):
        """测试设置和获取所有字段"""
        set_audit_context(
            operator_id=1,
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            detail={"action": "login"},
            tenant_id=100
        )
        
        context = get_audit_context()
        
        assert context["operator_id"] == 1
        assert context["client_ip"] == "192.168.1.1"
        assert context["user_agent"] == "Mozilla/5.0"
        assert context["detail"] == {"action": "login"}
        assert context["tenant_id"] == 100
    
    def test_set_partial_fields(self):
        """测试设置部分字段"""
        set_audit_context(operator_id=1, client_ip="192.168.1.1")
        
        context = get_audit_context()
        
        assert context["operator_id"] == 1
        assert context["client_ip"] == "192.168.1.1"
        assert context["user_agent"] is None
        assert context["detail"] == {}
        assert context["tenant_id"] is None
    
    def test_set_only_operator_id(self):
        """测试只设置操作人ID"""
        set_audit_context(operator_id=123)
        
        context = get_audit_context()
        assert context["operator_id"] == 123
    
    def test_set_only_tenant_id(self):
        """测试只设置租户ID"""
        set_audit_context(tenant_id=999)
        
        context = get_audit_context()
        assert context["tenant_id"] == 999
    
    def test_overwrite_existing_values(self):
        """测试覆盖已存在的值"""
        set_audit_context(operator_id=1, client_ip="192.168.1.1")
        set_audit_context(operator_id=2, client_ip="192.168.1.2")
        
        context = get_audit_context()
        
        assert context["operator_id"] == 2
        assert context["client_ip"] == "192.168.1.2"
    
    def test_clear_context(self):
        """测试清除上下文"""
        set_audit_context(
            operator_id=1,
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            detail={"action": "login"},
            tenant_id=100
        )
        
        clear_audit_context()
        
        context = get_audit_context()
        
        assert context["operator_id"] is None
        assert context["client_ip"] is None
        assert context["user_agent"] is None
        assert context["detail"] == {}
        assert context["tenant_id"] is None
    
    def test_detail_dict(self):
        """测试详情字典"""
        detail = {
            "action": "update_project",
            "project_id": 123,
            "changes": {"status": "COMPLETED"}
        }
        
        set_audit_context(detail=detail)
        
        context = get_audit_context()
        assert context["detail"] == detail
    
    def test_empty_detail(self):
        """测试空详情"""
        set_audit_context(detail={})
        
        context = get_audit_context()
        assert context["detail"] == {}


class TestTenantContext:
    """测试租户上下文功能"""

    def setup_method(self):
        """每个测试前清理上下文"""
        clear_audit_context()
    
    def teardown_method(self):
        """每个测试后清理上下文"""
        clear_audit_context()
    
    def test_set_and_get_tenant_id(self):
        """测试设置和获取租户ID"""
        set_current_tenant_id(100)
        
        assert get_current_tenant_id() == 100
    
    def test_get_tenant_id_default_none(self):
        """测试默认租户ID为None"""
        assert get_current_tenant_id() is None
    
    def test_set_tenant_id_none(self):
        """测试设置租户ID为None"""
        set_current_tenant_id(100)
        set_current_tenant_id(None)
        
        assert get_current_tenant_id() is None
    
    def test_tenant_id_in_full_context(self):
        """测试租户ID在完整上下文中"""
        set_current_tenant_id(100)
        
        context = get_audit_context()
        assert context["tenant_id"] == 100


class TestContextIsolation:
    """测试上下文隔离"""

    def test_different_calls_isolated(self):
        """测试不同调用之间的隔离"""
        # 第一次设置
        set_audit_context(operator_id=1)
        context1 = get_audit_context()
        
        # 清除
        clear_audit_context()
        
        # 第二次设置
        set_audit_context(operator_id=2)
        context2 = get_audit_context()
        
        assert context1["operator_id"] == 1
        assert context2["operator_id"] == 2


class TestEdgeCases:
    """边界情况测试"""

    def setup_method(self):
        clear_audit_context()
    
    def teardown_method(self):
        clear_audit_context()
    
    def test_zero_operator_id(self):
        """测试操作人ID为0"""
        set_audit_context(operator_id=0)
        assert get_audit_context()["operator_id"] == 0
    
    def test_negative_operator_id(self):
        """测试负数操作人ID"""
        set_audit_context(operator_id=-1)
        assert get_audit_context()["operator_id"] == -1
    
    def test_empty_string_ip(self):
        """测试空字符串IP"""
        set_audit_context(client_ip="")
        assert get_audit_context()["client_ip"] == ""
    
    def test_special_characters_in_user_agent(self):
        """测试User Agent中的特殊字符"""
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) 中文"
        set_audit_context(user_agent=ua)
        assert get_audit_context()["user_agent"] == ua
    
    def test_large_detail_dict(self):
        """测试大型详情字典"""
        detail = {f"key_{i}": f"value_{i}" for i in range(100)}
        set_audit_context(detail=detail)
        assert get_audit_context()["detail"] == detail
    
    def test_nested_detail_dict(self):
        """测试嵌套详情字典"""
        detail = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        set_audit_context(detail=detail)
        assert get_audit_context()["detail"] == detail


class TestRealWorldScenarios:
    """真实业务场景测试"""

    def setup_method(self):
        clear_audit_context()
    
    def teardown_method(self):
        clear_audit_context()
    
    def test_user_login_scenario(self):
        """测试用户登录场景"""
        set_audit_context(
            operator_id=123,
            client_ip="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            detail={
                "action": "login",
                "username": "testuser",
                "success": True
            },
            tenant_id=1
        )
        
        context = get_audit_context()
        
        assert context["operator_id"] == 123
        assert context["detail"]["action"] == "login"
        assert context["detail"]["success"] is True
    
    def test_api_request_tracking(self):
        """测试API请求跟踪场景"""
        set_audit_context(
            operator_id=456,
            client_ip="10.0.0.50",
            user_agent="mobile-app/1.0",
            detail={
                "endpoint": "/api/v1/projects",
                "method": "POST",
                "request_id": "abc-123-def"
            }
        )
        
        context = get_audit_context()
        
        assert context["detail"]["endpoint"] == "/api/v1/projects"
        assert context["detail"]["request_id"] == "abc-123-def"
    
    def test_multi_tenant_scenario(self):
        """测试多租户场景"""
        # 租户A的请求
        set_current_tenant_id(100)
        set_audit_context(operator_id=1)
        context_a = get_audit_context()
        
        # 清除并设置租户B的请求
        clear_audit_context()
        set_current_tenant_id(200)
        set_audit_context(operator_id=2)
        context_b = get_audit_context()
        
        # 验证租户隔离
        assert context_a["tenant_id"] == 100
        assert context_b["tenant_id"] == 200
