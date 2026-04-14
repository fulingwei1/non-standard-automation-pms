# -*- coding: utf-8 -*-
"""兼容旧 lastfailed 路径，复用当前 contract_enhanced CRUD/审批流回归用例。"""

from tests.unit.test_contract_approval_service_deep import *  # noqa: F401,F403
from tests.unit.test_contract_enhanced_deep import *  # noqa: F401,F403
