# -*- coding: utf-8 -*-
"""权限审计服务的安全与追溯测试。"""

import json
from unittest.mock import MagicMock, patch

from app.services.permission_audit_service import PermissionAuditService


def test_log_audit_enriches_detail_with_context_tenant_and_request_meta():
    db = MagicMock()

    with patch(
        "app.services.permission_audit_service.get_audit_context",
        return_value={
            "tenant_id": 9,
            "client_ip": "10.0.0.1",
            "user_agent": "pytest-agent",
        },
    ), patch("app.services.permission_audit_service.save_obj") as mock_save:
        PermissionAuditService.log_audit(
            db=db,
            operator_id=1,
            action="ROLE_UPDATED",
            target_type="role",
            target_id=3,
            detail={"changes": {"role_name": "项目经理"}},
        )

    audit = mock_save.call_args.args[1]
    assert audit.ip_address == "10.0.0.1"
    assert audit.user_agent == "pytest-agent"
    assert json.loads(audit.detail)["tenant_id"] == 9
