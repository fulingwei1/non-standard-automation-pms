"""
简单测试AI报价单生成器
"""
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 导入模型和服务
from app.models.base import Base
from app.models.presale_ai_quotation import (
    PresaleAIQuotation, QuotationType, QuotationTemplate,
    QuotationApproval, QuotationVersion
)
from app.services.presale_ai_quotation_service import AIQuotationGeneratorService
from app.schemas.presale_ai_quotation import QuotationGenerateRequest, QuotationItem

# 创建测试数据库
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 只创建AI报价单相关的表
PresaleAIQuotation.__table__.create(bind=engine, checkfirst=True)
QuotationTemplate.__table__.create(bind=engine, checkfirst=True)
QuotationApproval.__table__.create(bind=engine, checkfirst=True)
QuotationVersion.__table__.create(bind=engine, checkfirst=True)

# 创建会话
db = SessionLocal()

try:
    # 创建测试报价项
    items = [
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
    
    # 创建服务
    service = AIQuotationGeneratorService(db)
    
    # 测试1: 生成基础版报价单
    print("=" * 60)
    print("测试1: 生成基础版报价单")
    print("=" * 60)
    
    request = QuotationGenerateRequest(
        presale_ticket_id=1,
        customer_id=1,
        quotation_type=QuotationType.BASIC,
        items=items,
        tax_rate=Decimal("0.13"),
        discount_rate=Decimal("0"),
        validity_days=30
    )
    
    quotation = service.generate_quotation(request, user_id=1)
    
    print(f"✅ 报价单生成成功!")
    print(f"   - ID: {quotation.id}")
    print(f"   - 编号: {quotation.quotation_number}")
    print(f"   - 类型: {quotation.quotation_type}")
    print(f"   - 小计: ¥{quotation.subtotal:,.2f}")
    print(f"   - 税费: ¥{quotation.tax:,.2f}")
    print(f"   - 折扣: ¥{quotation.discount:,.2f}")
    print(f"   - 总计: ¥{quotation.total:,.2f}")
    print(f"   - 版本: V{quotation.version}")
    print(f"   - 状态: {quotation.status}")
    print()
    
    # 测试2: 更新报价单
    print("=" * 60)
    print("测试2: 更新报价单（增加折扣）")
    print("=" * 60)
    
    from app.schemas.presale_ai_quotation import QuotationUpdateRequest
    
    update_request = QuotationUpdateRequest(
        discount_rate=Decimal("0.05")
    )
    
    updated_quotation = service.update_quotation(quotation.id, update_request, user_id=1)
    
    print(f"✅ 报价单更新成功!")
    print(f"   - 新折扣: ¥{updated_quotation.discount:,.2f}")
    print(f"   - 新总计: ¥{updated_quotation.total:,.2f}")
    print(f"   - 新版本: V{updated_quotation.version}")
    print()
    
    # 测试3: 查看版本历史
    print("=" * 60)
    print("测试3: 查看版本历史")
    print("=" * 60)
    
    versions = service.get_quotation_versions(quotation.id)
    
    print(f"✅ 版本历史: {len(versions)}个版本")
    for v in versions:
        print(f"   - V{v.version}: {v.change_summary} (创建于 {v.created_at})")
    print()
    
    # 测试4: 生成三档方案
    print("=" * 60)
    print("测试4: 生成三档报价方案")
    print("=" * 60)
    
    from app.schemas.presale_ai_quotation import ThreeTierQuotationRequest
    
    three_tier_request = ThreeTierQuotationRequest(
        presale_ticket_id=2,
        customer_id=2,
        base_requirements="企业需要一套ERP系统"
    )
    
    basic, standard, premium = service.generate_three_tier_quotations(three_tier_request, user_id=1)
    
    print(f"✅ 三档方案生成成功!")
    print(f"\n   【基础版】")
    print(f"   - 编号: {basic.quotation_number}")
    print(f"   - 总计: ¥{basic.total:,.2f}")
    print(f"   - 功能项: {len(basic.items)}个")
    
    print(f"\n   【标准版】⭐ 推荐")
    print(f"   - 编号: {standard.quotation_number}")
    print(f"   - 总计: ¥{standard.total:,.2f}")
    print(f"   - 功能项: {len(standard.items)}个")
    
    print(f"\n   【高级版】")
    print(f"   - 编号: {premium.quotation_number}")
    print(f"   - 总计: ¥{premium.total:,.2f}")
    print(f"   - 功能项: {len(premium.items)}个")
    print()
    
    # 测试5: 审批报价单
    print("=" * 60)
    print("测试5: 审批报价单")
    print("=" * 60)
    
    approval = service.approve_quotation(
        quotation_id=quotation.id,
        approver_id=2,
        status="approved",
        comments="方案合理，批准通过"
    )
    
    print(f"✅ 审批成功!")
    print(f"   - 审批状态: {approval.status}")
    print(f"   - 审批意见: {approval.comments}")
    
    approved_quotation = service.get_quotation(quotation.id)
    print(f"   - 报价单状态: {approved_quotation.status}")
    print()
    
    print("=" * 60)
    print("🎉 所有测试通过！AI报价单自动生成器工作正常！")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
