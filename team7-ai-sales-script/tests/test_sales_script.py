"""话术推荐测试 - 8个用例"""
import pytest
from app.models.sales_script import PresaleAISalesScript, SalesScriptTemplate, ScenarioType
from app.services.sales_script_service import SalesScriptService


class TestSalesScriptRecommendation:
    """话术推荐测试"""

    def test_create_sales_script_first_contact(self, db_session):
        """测试1: 创建首次接触话术"""
        script = PresaleAISalesScript(
            presale_ticket_id=201,
            scenario=ScenarioType.FIRST_CONTACT,
            customer_profile_id=1,
            recommended_scripts=["您好，我是XX公司的..."],
            response_strategy="建立初步联系，了解需求",
            success_case_references=[{"case": "XX公司", "result": "成功签约"}]
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.id is not None
        assert script.scenario == ScenarioType.FIRST_CONTACT
        assert len(script.recommended_scripts) > 0

    def test_create_sales_script_needs_discovery(self, db_session):
        """测试2: 创建需求挖掘话术"""
        script = PresaleAISalesScript(
            presale_ticket_id=202,
            scenario=ScenarioType.NEEDS_DISCOVERY,
            recommended_scripts=["请问贵司在XXX方面..."],
            response_strategy="深入了解客户需求"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.scenario == ScenarioType.NEEDS_DISCOVERY

    def test_create_sales_script_solution_presentation(self, db_session):
        """测试3: 创建方案讲解话术"""
        script = PresaleAISalesScript(
            presale_ticket_id=203,
            scenario=ScenarioType.SOLUTION_PRESENTATION,
            recommended_scripts=["我们的技术架构..."],
            response_strategy="清晰展示方案价值"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.scenario == ScenarioType.SOLUTION_PRESENTATION

    def test_create_sales_script_price_negotiation(self, db_session):
        """测试4: 创建价格谈判话术"""
        script = PresaleAISalesScript(
            presale_ticket_id=204,
            scenario=ScenarioType.PRICE_NEGOTIATION,
            recommended_scripts=["我们的报价已经是底价..."],
            response_strategy="强调价值，灵活调整"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.scenario == ScenarioType.PRICE_NEGOTIATION

    def test_create_sales_script_objection_handling(self, db_session):
        """测试5: 创建异议处理话术"""
        script = PresaleAISalesScript(
            presale_ticket_id=205,
            scenario=ScenarioType.OBJECTION_HANDLING,
            objection_type="价格太高",
            recommended_scripts=["价格确实是考量因素..."],
            response_strategy="强调ROI和长期价值"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.scenario == ScenarioType.OBJECTION_HANDLING
        assert script.objection_type == "价格太高"

    def test_create_sales_script_closing(self, db_session):
        """测试6: 创建成交话术"""
        script = PresaleAISalesScript(
            presale_ticket_id=206,
            scenario=ScenarioType.CLOSING,
            recommended_scripts=["那我们就这样定了？"],
            response_strategy="推进成交，确认细节"
        )
        
        db_session.add(script)
        db_session.commit()
        
        assert script.scenario == ScenarioType.CLOSING

    def test_add_script_template(self, db_session):
        """测试7: 添加话术模板"""
        service = SalesScriptService(db_session)
        
        template = service.add_script_template(
            scenario="first_contact",
            script_content="您好，我是XX公司的技术顾问...",
            customer_type="technical",
            tags=["技术", "专业"],
            success_rate=85.5
        )
        
        assert template.id is not None
        assert template.scenario == ScenarioType.FIRST_CONTACT
        assert template.success_rate == 85.5

    def test_get_scripts_by_scenario(self, db_session):
        """测试8: 获取场景话术"""
        # 创建测试数据
        for i in range(3):
            template = SalesScriptTemplate(
                scenario=ScenarioType.NEEDS_DISCOVERY,
                customer_type="commercial",
                script_content=f"测试话术{i}",
                tags=["测试"],
                success_rate=80.0 + i
            )
            db_session.add(template)
        db_session.commit()
        
        # 测试获取
        service = SalesScriptService(db_session)
        scripts = service.get_scripts_by_scenario(
            scenario="needs_discovery",
            customer_type="commercial",
            limit=10
        )
        
        assert len(scripts) == 3
        # 验证按成功率排序
        assert scripts[0].success_rate >= scripts[1].success_rate


class TestSalesScriptLibrary:
    """话术库测试"""

    def test_script_library_filter_by_scenario(self, db_session):
        """测试9: 按场景筛选话术库"""
        # 创建不同场景的模板
        scenarios = [ScenarioType.FIRST_CONTACT, ScenarioType.CLOSING, ScenarioType.FIRST_CONTACT]
        for i, scenario in enumerate(scenarios):
            template = SalesScriptTemplate(
                scenario=scenario,
                script_content=f"话术{i}",
                success_rate=75.0
            )
            db_session.add(template)
        db_session.commit()
        
        service = SalesScriptService(db_session)
        scripts = service.get_script_library(scenario="first_contact")
        
        assert len(scripts) == 2

    def test_script_library_filter_by_customer_type(self, db_session):
        """测试10: 按客户类型筛选话术库"""
        # 创建不同客户类型的模板
        for customer_type in ["technical", "commercial", "technical"]:
            template = SalesScriptTemplate(
                scenario=ScenarioType.NEEDS_DISCOVERY,
                customer_type=customer_type,
                script_content=f"话术-{customer_type}",
                success_rate=80.0
            )
            db_session.add(template)
        db_session.commit()
        
        service = SalesScriptService(db_session)
        scripts = service.get_script_library(customer_type="technical")
        
        assert len(scripts) == 2
