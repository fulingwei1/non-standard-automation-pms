"""异议处理测试 - 6个用例"""
import pytest
from app.models.sales_script import PresaleAISalesScript, ScenarioType
from app.services.sales_script_service import SalesScriptService


class TestObjectionHandling:
    """异议处理测试"""

    def test_handle_price_objection(self, db_session):
        """测试1: 处理价格异议"""
        script = PresaleAISalesScript(
            presale_ticket_id=301,
            scenario=ScenarioType.OBJECTION_HANDLING,
            objection_type="价格太高",
            recommended_scripts=[
                "价格确实是考量因素，但更重要的是投入产出比",
                "我们可以提供分期付款方案"
            ],
            response_strategy="强调价值和ROI，提供灵活付款方案"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.objection_type == "价格太高"
        assert len(script.recommended_scripts) == 2

    def test_handle_technology_objection(self, db_session):
        """测试2: 处理技术异议"""
        script = PresaleAISalesScript(
            presale_ticket_id=302,
            scenario=ScenarioType.OBJECTION_HANDLING,
            objection_type="技术不成熟",
            recommended_scripts=["我们的技术已在XX家企业稳定运行"],
            response_strategy="提供成功案例和技术白皮书"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.objection_type == "技术不成熟"

    def test_handle_competitor_objection(self, db_session):
        """测试3: 处理竞品异议"""
        script = PresaleAISalesScript(
            presale_ticket_id=303,
            scenario=ScenarioType.OBJECTION_HANDLING,
            objection_type="竞品更好",
            recommended_scripts=["我们在XXX方面有独特优势"],
            response_strategy="突出差异化价值，提供对比分析"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.objection_type == "竞品更好"

    def test_handle_timing_objection(self, db_session):
        """测试4: 处理时机异议"""
        script = PresaleAISalesScript(
            presale_ticket_id=304,
            scenario=ScenarioType.OBJECTION_HANDLING,
            objection_type="暂时不需要",
            recommended_scripts=["提前布局能抢占先机"],
            response_strategy="创造紧迫感，提供试点方案"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.objection_type == "暂时不需要"

    def test_handle_budget_objection(self, db_session):
        """测试5: 处理预算异议"""
        script = PresaleAISalesScript(
            presale_ticket_id=305,
            scenario=ScenarioType.OBJECTION_HANDLING,
            objection_type="预算不足",
            recommended_scripts=[
                "我们支持分期付款",
                "可以先做核心模块"
            ],
            response_strategy="提供灵活方案，调整范围"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.objection_type == "预算不足"
        assert "分期" in script.recommended_scripts[0]

    def test_objection_with_success_cases(self, db_session):
        """测试6: 异议处理包含成功案例"""
        script = PresaleAISalesScript(
            presale_ticket_id=306,
            scenario=ScenarioType.OBJECTION_HANDLING,
            objection_type="数据安全",
            recommended_scripts=["支持私有化部署，数据不出本地"],
            response_strategy="强调安全措施和认证",
            success_case_references=[
                {
                    "case_title": "XX银行案例",
                    "objection": "数据安全担忧",
                    "resolution": "私有化部署+等保认证",
                    "result": "成功上线，0安全事故"
                }
            ]
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.objection_type == "数据安全"
        assert len(script.success_case_references) > 0
        assert script.success_case_references[0]["case_title"] == "XX银行案例"
