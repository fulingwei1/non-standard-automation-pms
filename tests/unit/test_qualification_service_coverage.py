# -*- coding: utf-8 -*-
"""qualification_service单元测试"""
from app.services.qualification_service import QualificationService


class TestQualificationServiceInit:
    def test_init_with_db(self):
        assert callable(QualificationService.get_employee_qualification)
