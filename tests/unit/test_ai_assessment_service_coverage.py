# -*- coding: utf-8 -*-
"""ai_assessment_service单元测试"""

from app.services.ai_assessment_service import AIAssessmentService


class TestAIAssessmentServiceInit:
    def test_init_no_args(self):
        service = AIAssessmentService()
        assert service is not None
        assert hasattr(service, "is_available")
