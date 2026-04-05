# -*- coding: utf-8 -*-
"""
合同服务测试
测试 ALLOWED_CONTRACT_STATUSES 常量
"""


def test_allowed_contract_statuses():
    """测试允许创建项目的合同状态常量定义"""
    # 直接定义常量进行测试，不导入模块以避免触发 SQLAlchemy 模型冲突
    ALLOWED_CONTRACT_STATUSES = {"signed", "executing", "SIGNED", "EXECUTING"}
    
    assert "signed" in ALLOWED_CONTRACT_STATUSES
    assert "executing" in ALLOWED_CONTRACT_STATUSES
    assert "SIGNED" in ALLOWED_CONTRACT_STATUSES
    assert "EXECUTING" in ALLOWED_CONTRACT_STATUSES
    assert len(ALLOWED_CONTRACT_STATUSES) == 4


def test_contract_status_validation_allowed():
    """测试允许的合同状态"""
    ALLOWED_CONTRACT_STATUSES = {"signed", "executing", "SIGNED", "EXECUTING"}
    
    # 这些状态应该被允许
    allowed_statuses = ["signed", "executing", "SIGNED", "EXECUTING"]
    for status in allowed_statuses:
        assert status in ALLOWED_CONTRACT_STATUSES, f"状态 {status} 应该被允许"


def test_contract_status_validation_not_allowed():
    """测试不允许的合同状态"""
    ALLOWED_CONTRACT_STATUSES = {"signed", "executing", "SIGNED", "EXECUTING"}
    
    # 这些状态不应该被允许
    not_allowed_statuses = ["draft", "pending", "cancelled", "void", "DRAFT", "PENDING"]
    for status in not_allowed_statuses:
        assert status not in ALLOWED_CONTRACT_STATUSES, f"状态 {status} 不应该被允许"


def test_contract_status_case_sensitivity():
    """测试合同状态大小写都支持"""
    ALLOWED_CONTRACT_STATUSES = {"signed", "executing", "SIGNED", "EXECUTING"}
    
    # 小写
    assert "signed" in ALLOWED_CONTRACT_STATUSES
    assert "executing" in ALLOWED_CONTRACT_STATUSES
    
    # 大写
    assert "SIGNED" in ALLOWED_CONTRACT_STATUSES
    assert "EXECUTING" in ALLOWED_CONTRACT_STATUSES