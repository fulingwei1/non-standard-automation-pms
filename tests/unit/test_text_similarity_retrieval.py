# -*- coding: utf-8 -*-
"""详#16 契约：中文检索三处失效修复（RAG 短期方案）。

1. 共享 bigram 余弦相似度：中文近义句高分、无关句低分（Jaccard 按空格分词对中文恒 0）。
2. 模板匹配 _calculate_similarity 回退不再用空格 Jaccard。
3. 知识库哈希向量：语序敏感（bigram）且跨进程稳定（不得用内建 hash()）。
4. 商机相似案例：LIKE 放宽 + 相似度排序；空设备类型不得全库乱配。
"""
import uuid
from decimal import Decimal

from app.models.sales import Customer
from app.models.sales.leads import Opportunity
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def test_bigram_cosine_handles_chinese():
    from app.utils.text_similarity import cosine_similarity

    assert cosine_similarity("视觉检测设备", "视觉检测系统") > 0.5, "中文近义句应高分"
    assert cosine_similarity("视觉检测设备", "回款计划管理") < 0.15, "无关句应低分"
    assert cosine_similarity("FCT测试线", "fct 测试线") > 0.6, "大小写/空格应归一"
    assert cosine_similarity("", "任何内容") == 0.0


def test_presale_template_similarity_fallback_works_for_chinese(db_session):
    from app.services.presale.presale_ai_service import PresaleAIService

    service = PresaleAIService(db_session)
    service.embedding_model = None
    service.use_semantic_search = False

    score = service._calculate_similarity("视觉检测设备方案", "视觉检测系统方案")
    assert score > 0.4, "中文模板匹配回退仍然失效（空格 Jaccard 恒 0）"
    assert service._calculate_similarity("视觉检测设备", "回款计划管理") < 0.15


def test_knowledge_hash_vector_is_order_sensitive_and_stable(db_session):
    import numpy as np

    from app.services.presale.presale_ai_knowledge_service import PresaleAIKnowledgeService

    service = PresaleAIKnowledgeService(db_session)
    # 强制走哈希回退
    type(service)._embedding_model = None
    type(service)._embedding_model_checked = True
    service.embedding_model = None

    v1 = service._generate_embedding("视觉检测设备")
    v2 = service._generate_embedding("视觉检测设备")
    assert np.allclose(v1, v2), "同文本向量必须确定性一致"

    v3 = service._generate_embedding("备设测检觉视")  # 同字符不同语序
    assert not np.allclose(v1, v3), "单字符哈希对语序不敏感——必须用 bigram"

    # 不得使用进程随机化的内建 hash()
    import inspect

    src = inspect.getsource(type(service)._generate_embedding)
    assert "hash(" not in src.replace("stable_token_hash(", ""), "不得用内建 hash()（跨进程随机化）"


def test_similar_cases_fuzzy_match_and_no_empty_wildcard(db_session):
    from app.api.v1.endpoints.sales.opportunity_workflow import similar_cases

    user = _get_or_create_user(
        db_session,
        username=_unique("sim").lower(),
        password="test123",
        real_name="相似案例用户",
        department="销售部",
    )
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="相似案例客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db_session.add(customer)
    db_session.flush()

    base = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="家电整机FCT功能测试线",
        equipment_type="FCT测试",
        stage="PROPOSAL",
        owner_id=user.id,
    )
    similar = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="小家电FCT功能测试设备",
        equipment_type="FCT",  # 旧词表：非精确相等，必须模糊命中
        stage="WON",
        est_amount=Decimal("1500000"),
        owner_id=user.id,
    )
    unrelated = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="仓储物流AGV调度",
        equipment_type="AGV",
        stage="WON",
        owner_id=user.id,
    )
    empty_et = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="空设备类型商机",
        equipment_type=None,
        stage="PROPOSAL",
        owner_id=user.id,
    )
    db_session.add_all([base, similar, unrelated, empty_et])
    db_session.commit()

    result = similar_cases(db=db_session, opp_id=base.id, current_user=user)
    data = result.data if hasattr(result, "data") else result
    names = [c["name"] for c in data["cases"]]
    assert "小家电FCT功能测试设备" in names, "同族设备类型（FCT vs FCT测试）未模糊命中"
    assert "仓储物流AGV调度" not in names, "无关设备类型不应命中"

    # 空设备类型的商机：不得因为 ''='' 全库乱配
    result_empty = similar_cases(db=db_session, opp_id=empty_et.id, current_user=user)
    data_empty = result_empty.data if hasattr(result_empty, "data") else result_empty
    empty_names = [c["name"] for c in data_empty["cases"]]
    assert "仓储物流AGV调度" not in empty_names or len(empty_names) == 0
