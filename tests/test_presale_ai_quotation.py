"""
AI报价单自动生成器单元测试
Team 5: AI Quotation Generator Tests
至少24个测试用例
"""
import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.models.base import Base
from app.models.presale_ai_quotation import (
    PresaleAIQuotation, QuotationTemplate, QuotationApproval, QuotationVersion,
    QuotationType, QuotationStatus
)
from app.services.presale_ai_quotation_service import AIQuotationGeneratorService
from app.services.quotation_pdf_service import QuotationPDFService
from app.schemas.presale_ai_quotation import (
    QuotationGenerateRequest, QuotationItem, ThreeTierQuotationRequest,
    QuotationUpdateRequest
)


# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Fixtures
@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_quotation_items():
    """示例报价项"""
    return [
        QuotationItem(
            name="ERP系统开发",
            description="定制化ERP系统",
            quantity=Decimal("1"),
            unit="套",
            unit_price=Decimal("100000"),
            total_price=Decimal("100000"),
            category="软件开发"
        ),
        QuotationItem(
            name="系统部署",
            description="系统部署和培训",
            quantity=Decimal("1"),
            unit="次",
            unit_price=Decimal("5000"),
            total_price=Decimal("5000"),
            category="服务"
        )
    ]


# ========== 报价单生成测试（8个） ==========

class TestQuotationGeneration:
    """报价单生成测试类"""
    
    def test_generate_basic_quotation(self, db_session, sample_quotation_items):
        """测试生成基础版报价单"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            customer_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0"),
            validity_days=30
        )
        
        quotation = service.generate_quotation(request, user_id=1)
        
        assert quotation.id is not None
        assert quotation.quotation_type == QuotationType.BASIC
        assert quotation.subtotal == Decimal("105000")
        assert quotation.tax == Decimal("13650")
        assert quotation.total == Decimal("118650")
        assert quotation.version == 1
        assert quotation.status == QuotationStatus.DRAFT
    
    def test_generate_standard_quotation(self, db_session, sample_quotation_items):
        """测试生成标准版报价单"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.STANDARD,
            items=sample_quotation_items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0.05")
        )
        
        quotation = service.generate_quotation(request, user_id=1)
        
        assert quotation.quotation_type == QuotationType.STANDARD
        assert quotation.discount == Decimal("5250")  # 105000 * 0.05
        assert quotation.total == Decimal("113400")  # 105000 + 13650 - 5250
    
    def test_generate_premium_quotation(self, db_session, sample_quotation_items):
        """测试生成高级版报价单"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.PREMIUM,
            items=sample_quotation_items,
            tax_rate=Decimal("0.13"),
            discount_rate=Decimal("0.10")
        )
        
        quotation = service.generate_quotation(request, user_id=1)
        
        assert quotation.quotation_type == QuotationType.PREMIUM
        assert quotation.discount == Decimal("10500")  # 105000 * 0.10
        assert quotation.total == Decimal("108150")
    
    def test_quotation_number_generation(self, db_session, sample_quotation_items):
        """测试报价单编号生成"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items
        )
        
        quotation1 = service.generate_quotation(request, user_id=1)
        quotation2 = service.generate_quotation(request, user_id=1)
        
        assert quotation1.quotation_number.startswith("QT-")
        assert quotation2.quotation_number.startswith("QT-")
        assert quotation1.quotation_number != quotation2.quotation_number
    
    def test_auto_payment_terms_generation(self, db_session, sample_quotation_items):
        """测试自动生成付款条款"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.STANDARD,
            items=sample_quotation_items
        )
        
        quotation = service.generate_quotation(request, user_id=1)
        
        assert quotation.payment_terms is not None
        assert "总金额" in quotation.payment_terms
        assert "付款方式" in quotation.payment_terms
    
    def test_custom_payment_terms(self, db_session, sample_quotation_items):
        """测试自定义付款条款"""
        service = AIQuotationGeneratorService(db_session)
        custom_terms = "一次性支付全款"
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items,
            payment_terms=custom_terms
        )
        
        quotation = service.generate_quotation(request, user_id=1)
        
        assert quotation.payment_terms == custom_terms
    
    def test_quotation_validity_period(self, db_session, sample_quotation_items):
        """测试报价单有效期"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items,
            validity_days=60
        )
        
        quotation = service.generate_quotation(request, user_id=1)
        
        assert quotation.validity_days == 60
    
    def test_version_snapshot_creation(self, db_session, sample_quotation_items):
        """测试创建版本快照"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items
        )
        
        quotation = service.generate_quotation(request, user_id=1)
        versions = service.get_quotation_versions(quotation.id)
        
        assert len(versions) == 1
        assert versions[0].version == 1
        assert versions[0].change_summary == "初始创建"


# ========== 三档方案生成测试（6个） ==========

class TestThreeTierQuotation:
    """三档方案生成测试类"""
    
    def test_generate_three_tier_quotations(self, db_session):
        """测试生成三档报价方案"""
        service = AIQuotationGeneratorService(db_session)
        request = ThreeTierQuotationRequest(
            presale_ticket_id=1,
            customer_id=1,
            base_requirements="企业需要ERP系统"
        )
        
        basic, standard, premium = service.generate_three_tier_quotations(request, user_id=1)
        
        assert basic.quotation_type == QuotationType.BASIC
        assert standard.quotation_type == QuotationType.STANDARD
        assert premium.quotation_type == QuotationType.PREMIUM
    
    def test_three_tier_price_ascending(self, db_session):
        """测试三档方案价格递增"""
        service = AIQuotationGeneratorService(db_session)
        request = ThreeTierQuotationRequest(
            presale_ticket_id=1,
            base_requirements="企业需要ERP系统"
        )
        
        basic, standard, premium = service.generate_three_tier_quotations(request, user_id=1)
        
        assert basic.total < standard.total < premium.total
    
    def test_three_tier_features_count(self, db_session):
        """测试三档方案功能项数量"""
        service = AIQuotationGeneratorService(db_session)
        request = ThreeTierQuotationRequest(
            presale_ticket_id=1,
            base_requirements="企业需要ERP系统"
        )
        
        basic, standard, premium = service.generate_three_tier_quotations(request, user_id=1)
        
        assert len(basic.items) <= len(standard.items) <= len(premium.items)
    
    def test_three_tier_discount_differences(self, db_session):
        """测试三档方案折扣差异"""
        service = AIQuotationGeneratorService(db_session)
        request = ThreeTierQuotationRequest(
            presale_ticket_id=1,
            base_requirements="企业需要ERP系统"
        )
        
        basic, standard, premium = service.generate_three_tier_quotations(request, user_id=1)
        
        # 基础版无折扣，标准版有折扣，高级版折扣更大
        assert basic.discount == 0
        assert standard.discount > 0
        assert premium.discount >= standard.discount
    
    def test_three_tier_same_ticket(self, db_session):
        """测试三档方案关联同一工单"""
        service = AIQuotationGeneratorService(db_session)
        request = ThreeTierQuotationRequest(
            presale_ticket_id=999,
            base_requirements="企业需要ERP系统"
        )
        
        basic, standard, premium = service.generate_three_tier_quotations(request, user_id=1)
        
        assert basic.presale_ticket_id == 999
        assert standard.presale_ticket_id == 999
        assert premium.presale_ticket_id == 999
    
    def test_three_tier_unique_quotation_numbers(self, db_session):
        """测试三档方案报价单编号唯一性"""
        service = AIQuotationGeneratorService(db_session)
        request = ThreeTierQuotationRequest(
            presale_ticket_id=1,
            base_requirements="企业需要ERP系统"
        )
        
        basic, standard, premium = service.generate_three_tier_quotations(request, user_id=1)
        
        numbers = {basic.quotation_number, standard.quotation_number, premium.quotation_number}
        assert len(numbers) == 3


# ========== PDF导出测试（4个） ==========

class TestPDFExport:
    """PDF导出测试类"""
    
    def test_pdf_generation(self, db_session, sample_quotation_items):
        """测试PDF生成"""
        # 创建报价单
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.STANDARD,
            items=sample_quotation_items
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        # 生成PDF
        pdf_service = QuotationPDFService()
        try:
            pdf_path = pdf_service.generate_pdf(quotation)
            assert pdf_path.endswith('.pdf')
            assert quotation.quotation_number in pdf_path
        except RuntimeError as e:
            # 如果ReportLab未安装，跳过测试
            if "ReportLab is not installed" in str(e):
                pytest.skip("ReportLab not installed")
            raise
    
    def test_pdf_comparison_generation(self, db_session):
        """测试三档对比PDF生成"""
        service = AIQuotationGeneratorService(db_session)
        request = ThreeTierQuotationRequest(
            presale_ticket_id=1,
            base_requirements="企业需要ERP系统"
        )
        
        basic, standard, premium = service.generate_three_tier_quotations(request, user_id=1)
        
        pdf_service = QuotationPDFService()
        try:
            pdf_path = pdf_service.generate_comparison_pdf([basic, standard, premium])
            assert pdf_path.endswith('.pdf')
            assert 'comparison' in pdf_path
        except RuntimeError as e:
            if "ReportLab is not installed" in str(e):
                pytest.skip("ReportLab not installed")
            raise
    
    def test_pdf_url_update(self, db_session, sample_quotation_items):
        """测试PDF URL更新"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        assert quotation.pdf_url is None
        
        # 模拟更新PDF URL
        quotation.pdf_url = "uploads/quotations/test.pdf"
        db_session.commit()
        
        updated_quotation = service.get_quotation(quotation.id)
        assert updated_quotation.pdf_url == "uploads/quotations/test.pdf"
    
    def test_pdf_different_types(self, db_session, sample_quotation_items):
        """测试不同类型报价单PDF生成"""
        service = AIQuotationGeneratorService(db_session)
        pdf_service = QuotationPDFService()
        
        for qtype in [QuotationType.BASIC, QuotationType.STANDARD, QuotationType.PREMIUM]:
            request = QuotationGenerateRequest(
                presale_ticket_id=1,
                quotation_type=qtype,
                items=sample_quotation_items
            )
            quotation = service.generate_quotation(request, user_id=1)
            
            try:
                pdf_path = pdf_service.generate_pdf(quotation)
                assert pdf_path.endswith('.pdf')
            except RuntimeError as e:
                if "ReportLab is not installed" in str(e):
                    pytest.skip("ReportLab not installed")
                raise


# ========== 版本管理测试（6个） ==========

class TestVersionManagement:
    """版本管理测试类"""
    
    def test_update_quotation_items(self, db_session, sample_quotation_items):
        """测试更新报价项"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        # 更新报价项
        new_items = sample_quotation_items[:1]  # 只保留第一项
        update_request = QuotationUpdateRequest(items=new_items)
        
        updated_quotation = service.update_quotation(quotation.id, update_request, user_id=1)
        
        assert updated_quotation.version == 2
        assert len(updated_quotation.items) == 1
    
    def test_update_quotation_tax_rate(self, db_session, sample_quotation_items):
        """测试更新税率"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items,
            tax_rate=Decimal("0.13")
        )
        quotation = service.generate_quotation(request, user_id=1)
        original_tax = quotation.tax
        
        # 更新税率
        update_request = QuotationUpdateRequest(tax_rate=Decimal("0.09"))
        updated_quotation = service.update_quotation(quotation.id, update_request, user_id=1)
        
        assert updated_quotation.tax < original_tax
        assert updated_quotation.version == 2
    
    def test_update_quotation_discount(self, db_session, sample_quotation_items):
        """测试更新折扣"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items,
            discount_rate=Decimal("0")
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        # 更新折扣
        update_request = QuotationUpdateRequest(discount_rate=Decimal("0.10"))
        updated_quotation = service.update_quotation(quotation.id, update_request, user_id=1)
        
        assert updated_quotation.discount > 0
        assert updated_quotation.total < quotation.total
    
    def test_version_history_tracking(self, db_session, sample_quotation_items):
        """测试版本历史追踪"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        # 多次更新
        for i in range(3):
            update_request = QuotationUpdateRequest(
                validity_days=30 + (i + 1) * 10
            )
            service.update_quotation(quotation.id, update_request, user_id=1)
        
        versions = service.get_quotation_versions(quotation.id)
        assert len(versions) == 4  # 1个初始版本 + 3次更新
    
    def test_version_snapshot_data(self, db_session, sample_quotation_items):
        """测试版本快照数据完整性"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        versions = service.get_quotation_versions(quotation.id)
        snapshot = versions[0].snapshot_data
        
        assert 'quotation_number' in snapshot
        assert 'total' in snapshot
        assert 'items' in snapshot
        assert 'status' in snapshot
    
    def test_quotation_status_update(self, db_session, sample_quotation_items):
        """测试报价单状态更新"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.BASIC,
            items=sample_quotation_items
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        # 更新状态
        update_request = QuotationUpdateRequest(status=QuotationStatus.APPROVED)
        updated_quotation = service.update_quotation(quotation.id, update_request, user_id=1)
        
        assert updated_quotation.status == QuotationStatus.APPROVED


# ========== 审批流程测试（额外2个） ==========

class TestApprovalProcess:
    """审批流程测试类"""
    
    def test_approve_quotation(self, db_session, sample_quotation_items):
        """测试审批通过报价单"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.STANDARD,
            items=sample_quotation_items
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        approval = service.approve_quotation(
            quotation_id=quotation.id,
            approver_id=2,
            status="approved",
            comments="方案合理，批准"
        )
        
        assert approval.status == "approved"
        assert approval.comments == "方案合理，批准"
        
        # 验证报价单状态更新
        updated_quotation = service.get_quotation(quotation.id)
        assert updated_quotation.status == QuotationStatus.APPROVED
    
    def test_reject_quotation(self, db_session, sample_quotation_items):
        """测试拒绝报价单"""
        service = AIQuotationGeneratorService(db_session)
        request = QuotationGenerateRequest(
            presale_ticket_id=1,
            quotation_type=QuotationType.PREMIUM,
            items=sample_quotation_items
        )
        quotation = service.generate_quotation(request, user_id=1)
        
        approval = service.approve_quotation(
            quotation_id=quotation.id,
            approver_id=2,
            status="rejected",
            comments="价格过高，需要调整"
        )
        
        assert approval.status == "rejected"
        
        updated_quotation = service.get_quotation(quotation.id)
        assert updated_quotation.status == QuotationStatus.REJECTED


# ========== 边界和错误测试（额外2个） ==========

class TestEdgeCases:
    """边界和错误情况测试"""
    
    def test_get_nonexistent_quotation(self, db_session):
        """测试获取不存在的报价单"""
        service = AIQuotationGeneratorService(db_session)
        quotation = service.get_quotation(99999)
        
        assert quotation is None
    
    def test_update_nonexistent_quotation(self, db_session):
        """测试更新不存在的报价单"""
        service = AIQuotationGeneratorService(db_session)
        update_request = QuotationUpdateRequest(validity_days=60)
        
        with pytest.raises(ValueError, match="not found"):
            service.update_quotation(99999, update_request, user_id=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
