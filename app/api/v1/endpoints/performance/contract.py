# -*- coding: utf-8 -*-
"""
绩效合约管理 API 端点

绩效合约体系：
- L1: 公司↔高管 — 年度经营目标合约
- L2: 高管↔部门经理 — 部门目标合约
- L3: 部门经理↔员工 — 个人绩效合约
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.params import Param
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.models.performance.contract import PerformanceContract, PerformanceContractItem
from app.schemas.common import ResponseModel

router = APIRouter()

DB_PATH = settings.SQLITE_DB_PATH
VALID_CONTRACT_TYPES = {"L1", "L2", "L3"}
VALID_CONTRACT_STATUSES = {
    "draft",
    "pending_review",
    "pending_sign",
    "active",
    "completed",
    "terminated",
}
VALID_ITEM_CATEGORIES = {"业绩指标", "管理指标", "能力指标", "态度指标"}
VALID_SOURCE_TYPES = {"kpi", "work", "custom"}


def _now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _to_dict(obj: Any, *, include_items: bool = False) -> Dict[str, Any]:
    data = {column.name: getattr(obj, column.name) for column in obj.__table__.columns}
    if include_items:
        data["items"] = [_to_dict(item) for item in obj.items]
    return data


def _optional(value: Any) -> Any:
    return None if isinstance(value, Param) else value


def _get_contract_or_404(db: Session, contract_id: int) -> PerformanceContract:
    contract = db.query(PerformanceContract).filter(PerformanceContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合约不存在")
    return contract


def _get_item_or_404(
    db: Session, contract_id: int, item_id: int
) -> PerformanceContractItem:
    item = (
        db.query(PerformanceContractItem)
        .filter(
            PerformanceContractItem.id == item_id,
            PerformanceContractItem.contract_id == contract_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="指标条目不存在或不属于该合约")
    return item


def _calculate_total_weight(db: Session, contract_id: int) -> float:
    total = (
        db.query(func.coalesce(func.sum(PerformanceContractItem.weight), 0))
        .filter(PerformanceContractItem.contract_id == contract_id)
        .scalar()
    )
    return float(total or 0)


def _refresh_total_weight(db: Session, contract_id: int) -> float:
    total_weight = _calculate_total_weight(db, contract_id)
    contract = _get_contract_or_404(db, contract_id)
    contract.total_weight = total_weight
    return total_weight


def generate_contract_no(contract_type: str, year: int) -> str:
    """生成合约编号"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"PC-{contract_type}-{year}-{timestamp}"


def calculate_total_weight(contract_id: int, db: Session = Depends(deps.get_db)) -> float:
    """计算合约总权重"""
    return _calculate_total_weight(db, contract_id)


# ============================================
# 合约 CRUD
# ============================================


@router.post("", response_model=ResponseModel)
def create_contract(
    contract_no: str = Query(..., description="合约编号"),
    contract_type: str = Query(..., description="合约类型 (L1/L2/L3)"),
    year: int = Query(..., description="年度"),
    quarter: Optional[int] = Query(None, description="季度 (可选)"),
    signer_id: Optional[int] = Query(None, description="签约人 ID"),
    signer_name: str = Query(..., description="签约人姓名"),
    signer_title: Optional[str] = Query(None, description="签约人职位"),
    counterpart_id: Optional[int] = Query(None, description="对方/上级 ID"),
    counterpart_name: str = Query(..., description="对方/上级姓名"),
    counterpart_title: Optional[str] = Query(None, description="对方/上级职位"),
    department_id: Optional[int] = Query(None, description="部门 ID"),
    department_name: Optional[str] = Query(None, description="部门名称"),
    strategy_id: Optional[int] = Query(None, description="关联战略 ID"),
    status: str = Query("draft", description="状态"),
    sign_date: Optional[str] = Query(None, description="签署日期"),
    effective_date: Optional[str] = Query(None, description="生效日期"),
    expiry_date: Optional[str] = Query(None, description="到期日期"),
    remarks: Optional[str] = Query(None, description="备注"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """创建绩效合约"""
    if contract_type not in VALID_CONTRACT_TYPES:
        raise HTTPException(status_code=400, detail="合约类型必须是 L1/L2/L3")
    if status not in VALID_CONTRACT_STATUSES:
        raise HTTPException(status_code=400, detail="状态无效")
    if db.query(PerformanceContract.id).filter_by(contract_no=contract_no).first():
        raise HTTPException(status_code=400, detail="合约编号已存在")

    contract = PerformanceContract(
        contract_no=contract_no,
        contract_type=contract_type,
        year=year,
        quarter=quarter,
        signer_id=signer_id,
        signer_name=signer_name,
        signer_title=signer_title,
        counterpart_id=counterpart_id,
        counterpart_name=counterpart_name,
        counterpart_title=counterpart_title,
        department_id=department_id,
        department_name=department_name,
        strategy_id=strategy_id,
        status=status,
        sign_date=sign_date,
        effective_date=effective_date,
        expiry_date=expiry_date,
        remarks=remarks,
        created_by=current_user.id,
    )
    db.add(contract)
    try:
        db.commit()
        db.refresh(contract)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败：{str(e)}")

    return ResponseModel(code=200, message="创建成功", data=_to_dict(contract))


@router.get("", response_model=ResponseModel)
def list_contracts(
    contract_type: Optional[str] = Query(None, description="合约类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    year: Optional[int] = Query(None, description="年度筛选"),
    signer_id: Optional[int] = Query(None, description="签约人 ID 筛选"),
    department_id: Optional[int] = Query(None, description="部门 ID 筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """获取绩效合约列表"""
    query = db.query(PerformanceContract)
    if contract_type:
        query = query.filter(PerformanceContract.contract_type == contract_type)
    if status:
        query = query.filter(PerformanceContract.status == status)
    if year:
        query = query.filter(PerformanceContract.year == year)
    if signer_id:
        query = query.filter(PerformanceContract.signer_id == signer_id)
    if department_id:
        query = query.filter(PerformanceContract.department_id == department_id)

    total = query.count()
    contracts = (
        query.order_by(PerformanceContract.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "items": [_to_dict(contract) for contract in contracts],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
    )


@router.get("/dashboard", response_model=ResponseModel)
def get_dashboard(
    year: Optional[int] = Query(None, description="年度筛选"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """获取绩效合约总览"""
    base_query = db.query(PerformanceContract)
    if year:
        base_query = base_query.filter(PerformanceContract.year == year)

    type_status_counts: Dict[str, Dict[str, int]] = {}
    for contract_type, status, count in (
        base_query.with_entities(
            PerformanceContract.contract_type,
            PerformanceContract.status,
            func.count(PerformanceContract.id),
        )
        .group_by(PerformanceContract.contract_type, PerformanceContract.status)
        .all()
    ):
        type_status_counts.setdefault(contract_type, {})[status] = count

    summary = {
        "total": base_query.count(),
        "pending_sign": base_query.filter(PerformanceContract.status == "pending_sign").count(),
        "active": base_query.filter(PerformanceContract.status == "active").count(),
        "completed": base_query.filter(PerformanceContract.status == "completed").count(),
        "avg_weight": base_query.with_entities(func.avg(PerformanceContract.total_weight)).scalar()
        or 0,
    }

    avg_score_query = db.query(func.avg(PerformanceContractItem.score)).join(
        PerformanceContract,
        PerformanceContract.id == PerformanceContractItem.contract_id,
    )
    signing_query = db.query(PerformanceContract).filter(
        PerformanceContract.status.in_(["pending_sign", "active"])
    )
    if year:
        avg_score_query = avg_score_query.filter(PerformanceContract.year == year)
        signing_query = signing_query.filter(PerformanceContract.year == year)

    avg_score = avg_score_query.filter(PerformanceContractItem.score.isnot(None)).scalar() or 0
    signing_contracts = signing_query.all()
    signing_progress = {
        "total": len(signing_contracts),
        "signer_signed": sum(1 for c in signing_contracts if c.signer_signature),
        "counterpart_signed": sum(1 for c in signing_contracts if c.counterpart_signature),
        "fully_signed": sum(
            1 for c in signing_contracts if c.signer_signature and c.counterpart_signature
        ),
    }

    return ResponseModel(
        code=200,
        message="查询成功",
        data={
            "summary": summary,
            "avg_score": avg_score,
            "type_status_breakdown": type_status_counts,
            "signing_progress": signing_progress,
        },
    )


@router.get("/{contract_id}", response_model=ResponseModel)
def get_contract(
    contract_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """获取绩效合约详情（含指标条目）"""
    contract = _get_contract_or_404(db, contract_id)
    return ResponseModel(code=200, message="查询成功", data=_to_dict(contract, include_items=True))


@router.put("/{contract_id}", response_model=ResponseModel)
def update_contract(
    contract_id: int,
    contract_no: Optional[str] = Query(None, description="合约编号"),
    contract_type: Optional[str] = Query(None, description="合约类型"),
    year: Optional[int] = Query(None, description="年度"),
    quarter: Optional[int] = Query(None, description="季度"),
    signer_id: Optional[int] = Query(None, description="签约人 ID"),
    signer_name: Optional[str] = Query(None, description="签约人姓名"),
    signer_title: Optional[str] = Query(None, description="签约人职位"),
    counterpart_id: Optional[int] = Query(None, description="对方 ID"),
    counterpart_name: Optional[str] = Query(None, description="对方姓名"),
    counterpart_title: Optional[str] = Query(None, description="对方职位"),
    department_id: Optional[int] = Query(None, description="部门 ID"),
    department_name: Optional[str] = Query(None, description="部门名称"),
    strategy_id: Optional[int] = Query(None, description="战略 ID"),
    status: Optional[str] = Query(None, description="状态"),
    sign_date: Optional[str] = Query(None, description="签署日期"),
    effective_date: Optional[str] = Query(None, description="生效日期"),
    expiry_date: Optional[str] = Query(None, description="到期日期"),
    remarks: Optional[str] = Query(None, description="备注"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """更新绩效合约"""
    contract_no = _optional(contract_no)
    contract_type = _optional(contract_type)
    year = _optional(year)
    quarter = _optional(quarter)
    signer_id = _optional(signer_id)
    signer_name = _optional(signer_name)
    signer_title = _optional(signer_title)
    counterpart_id = _optional(counterpart_id)
    counterpart_name = _optional(counterpart_name)
    counterpart_title = _optional(counterpart_title)
    department_id = _optional(department_id)
    department_name = _optional(department_name)
    strategy_id = _optional(strategy_id)
    status = _optional(status)
    sign_date = _optional(sign_date)
    effective_date = _optional(effective_date)
    expiry_date = _optional(expiry_date)
    remarks = _optional(remarks)
    contract = _get_contract_or_404(db, contract_id)
    if contract_type is not None and contract_type not in VALID_CONTRACT_TYPES:
        raise HTTPException(status_code=400, detail="合约类型必须是 L1/L2/L3")
    if status is not None and status not in VALID_CONTRACT_STATUSES:
        raise HTTPException(status_code=400, detail="状态无效")
    if contract_no and contract_no != contract.contract_no:
        existing = db.query(PerformanceContract.id).filter_by(contract_no=contract_no).first()
        if existing:
            raise HTTPException(status_code=400, detail="合约编号已存在")

    field_mappings = {
        "contract_no": contract_no,
        "contract_type": contract_type,
        "year": year,
        "quarter": quarter,
        "signer_id": signer_id,
        "signer_name": signer_name,
        "signer_title": signer_title,
        "counterpart_id": counterpart_id,
        "counterpart_name": counterpart_name,
        "counterpart_title": counterpart_title,
        "department_id": department_id,
        "department_name": department_name,
        "strategy_id": strategy_id,
        "status": status,
        "sign_date": sign_date,
        "effective_date": effective_date,
        "expiry_date": expiry_date,
        "remarks": remarks,
    }
    updates = {field: value for field, value in field_mappings.items() if value is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="没有要更新的字段")

    for field, value in updates.items():
        setattr(contract, field, value)
    try:
        db.commit()
        db.refresh(contract)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败：{str(e)}")
    return ResponseModel(code=200, message="更新成功", data=_to_dict(contract))


# ============================================
# 指标条目管理
# ============================================


@router.post("/{contract_id}/items", response_model=ResponseModel)
def add_contract_item(
    contract_id: int,
    sort_order: int = Query(0, description="排序"),
    category: str = Query(..., description="指标类别"),
    indicator_name: str = Query(..., description="指标名称"),
    indicator_description: Optional[str] = Query(None, description="指标描述"),
    weight: float = Query(..., description="权重"),
    unit: Optional[str] = Query(None, description="单位"),
    target_value: Optional[str] = Query(None, description="目标值"),
    challenge_value: Optional[str] = Query(None, description="挑战值"),
    baseline_value: Optional[str] = Query(None, description="底线值"),
    scoring_rule: Optional[str] = Query(None, description="评分规则"),
    data_source: Optional[str] = Query(None, description="数据来源"),
    evaluation_method: Optional[str] = Query(None, description="评估方式"),
    source_type: Optional[str] = Query(None, description="来源类型"),
    source_id: Optional[int] = Query(None, description="来源 ID"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """添加合约指标条目"""
    if category not in VALID_ITEM_CATEGORIES:
        raise HTTPException(status_code=400, detail="指标类别无效")
    if source_type and source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(status_code=400, detail="来源类型无效")
    _get_contract_or_404(db, contract_id)

    item = PerformanceContractItem(
        contract_id=contract_id,
        sort_order=sort_order,
        category=category,
        indicator_name=indicator_name,
        indicator_description=indicator_description,
        weight=weight,
        unit=unit,
        target_value=target_value,
        challenge_value=challenge_value,
        baseline_value=baseline_value,
        scoring_rule=scoring_rule,
        data_source=data_source,
        evaluation_method=evaluation_method,
        source_type=source_type,
        source_id=source_id,
    )
    db.add(item)
    try:
        db.flush()
        _refresh_total_weight(db, contract_id)
        db.commit()
        db.refresh(item)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加失败：{str(e)}")
    return ResponseModel(code=200, message="添加成功", data=_to_dict(item))


@router.put("/{contract_id}/items/{item_id}", response_model=ResponseModel)
def update_contract_item(
    contract_id: int,
    item_id: int,
    sort_order: Optional[int] = Query(None, description="排序"),
    category: Optional[str] = Query(None, description="指标类别"),
    indicator_name: Optional[str] = Query(None, description="指标名称"),
    indicator_description: Optional[str] = Query(None, description="指标描述"),
    weight: Optional[float] = Query(None, description="权重"),
    unit: Optional[str] = Query(None, description="单位"),
    target_value: Optional[str] = Query(None, description="目标值"),
    challenge_value: Optional[str] = Query(None, description="挑战值"),
    baseline_value: Optional[str] = Query(None, description="底线值"),
    scoring_rule: Optional[str] = Query(None, description="评分规则"),
    data_source: Optional[str] = Query(None, description="数据来源"),
    evaluation_method: Optional[str] = Query(None, description="评估方式"),
    actual_value: Optional[str] = Query(None, description="实际值"),
    score: Optional[float] = Query(None, description="得分"),
    evaluator_comment: Optional[str] = Query(None, description="评估意见"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """更新合约指标条目"""
    item = _get_item_or_404(db, contract_id, item_id)
    if category is not None and category not in VALID_ITEM_CATEGORIES:
        raise HTTPException(status_code=400, detail="指标类别无效")

    field_mappings = {
        "sort_order": sort_order,
        "category": category,
        "indicator_name": indicator_name,
        "indicator_description": indicator_description,
        "weight": weight,
        "unit": unit,
        "target_value": target_value,
        "challenge_value": challenge_value,
        "baseline_value": baseline_value,
        "scoring_rule": scoring_rule,
        "data_source": data_source,
        "evaluation_method": evaluation_method,
        "actual_value": actual_value,
        "score": score,
        "evaluator_comment": evaluator_comment,
    }
    updates = {field: value for field, value in field_mappings.items() if value is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="没有要更新的字段")

    for field, value in updates.items():
        setattr(item, field, value)
    try:
        if weight is not None:
            db.flush()
            _refresh_total_weight(db, contract_id)
        db.commit()
        db.refresh(item)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败：{str(e)}")
    return ResponseModel(code=200, message="更新成功", data=_to_dict(item))


@router.delete("/{contract_id}/items/{item_id}", response_model=ResponseModel)
def delete_contract_item(
    contract_id: int,
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """删除合约指标条目"""
    item = _get_item_or_404(db, contract_id, item_id)
    try:
        db.delete(item)
        db.flush()
        _refresh_total_weight(db, contract_id)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败：{str(e)}")
    return ResponseModel(code=200, message="删除成功")


# ============================================
# 合约流程操作
# ============================================


@router.post("/{contract_id}/submit", response_model=ResponseModel)
def submit_contract(
    contract_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """提交合约审批"""
    contract = _get_contract_or_404(db, contract_id)
    if contract.status != "draft":
        raise HTTPException(status_code=400, detail="只有草稿状态的合约可以提交")
    if abs((contract.total_weight or 0) - 100.0) > 0.01:
        raise HTTPException(
            status_code=400, detail=f"权重总和必须为 100，当前为{contract.total_weight}"
        )

    contract.status = "pending_review"
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交失败：{str(e)}")
    return ResponseModel(code=200, message="提交成功")


@router.post("/{contract_id}/sign", response_model=ResponseModel)
def sign_contract(
    contract_id: int,
    sign_as: str = Query(..., description="签署身份 (signer/counterpart)"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """签署合约"""
    contract = _get_contract_or_404(db, contract_id)
    if contract.status not in ["pending_sign", "active"]:
        raise HTTPException(status_code=400, detail="合约状态不允许签署")
    if sign_as == "signer":
        contract.signer_signature = _now_string()
    elif sign_as == "counterpart":
        contract.counterpart_signature = _now_string()
    else:
        raise HTTPException(status_code=400, detail="签署身份必须是 signer 或 counterpart")

    if contract.signer_signature and contract.counterpart_signature:
        contract.status = "active"
        contract.sign_date = datetime.now().date().isoformat()

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"签署失败：{str(e)}")
    return ResponseModel(code=200, message="签署成功")


@router.post("/{contract_id}/evaluate", response_model=ResponseModel)
def evaluate_contract(
    contract_id: int,
    evaluations: List[Dict[str, Any]],
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """批量评分（更新指标条目的实际值和得分）"""
    _get_contract_or_404(db, contract_id)
    try:
        for eval_item in evaluations:
            item_id = eval_item.get("item_id")
            if not item_id:
                continue
            item = (
                db.query(PerformanceContractItem)
                .filter(
                    PerformanceContractItem.id == item_id,
                    PerformanceContractItem.contract_id == contract_id,
                )
                .first()
            )
            if not item:
                continue
            if eval_item.get("actual_value") is not None:
                item.actual_value = str(eval_item.get("actual_value"))
            if eval_item.get("score") is not None:
                item.score = eval_item.get("score")
            if eval_item.get("evaluator_comment") is not None:
                item.evaluator_comment = eval_item.get("evaluator_comment")
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"评分失败：{str(e)}")
    return ResponseModel(code=200, message="评分成功")


# ============================================
# Dashboard 总览
# ============================================


@router.post("/{contract_id}/generate-from-strategy", response_model=ResponseModel)
def generate_from_strategy(
    contract_id: int,
    strategy_id: int,
    include_kpis: bool = Query(True, description="是否包含 KPI"),
    include_annual_works: bool = Query(True, description="是否包含年度工作"),
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """从战略分解自动生成合约条目"""
    _get_contract_or_404(db, contract_id)
    try:
        items_created = []
        sort_order = 0

        if include_kpis:
            rows = db.execute(
                text(
                    """
                    SELECT k.*, c.name as csf_name
                    FROM strategy_kpis k
                    LEFT JOIN strategy_csfs c ON k.csf_id = c.id
                    WHERE k.strategy_id = :strategy_id AND k.is_deleted = 0
                    """
                ),
                {"strategy_id": strategy_id},
            ).mappings()

            for kpi in rows:
                sort_order += 1
                item = PerformanceContractItem(
                    contract_id=contract_id,
                    sort_order=sort_order,
                    category="业绩指标",
                    indicator_name=kpi["name"],
                    indicator_description=kpi.get("description"),
                    weight=0,
                    unit=kpi.get("unit"),
                    target_value=str(kpi.get("target_value")),
                    challenge_value=str(kpi.get("challenge_value")),
                    baseline_value=str(kpi.get("baseline_value")),
                    scoring_rule=kpi.get("scoring_rule"),
                    data_source=kpi.get("data_source"),
                    evaluation_method="系统采集",
                    source_type="kpi",
                    source_id=kpi["id"],
                )
                db.add(item)
                items_created.append({"type": "kpi", "id": kpi["id"], "name": kpi["name"]})

        if include_annual_works:
            rows = db.execute(
                text(
                    """
                    SELECT *
                    FROM strategy_annual_works
                    WHERE strategy_id = :strategy_id
                    """
                ),
                {"strategy_id": strategy_id},
            ).mappings()

            for work in rows:
                sort_order += 1
                item = PerformanceContractItem(
                    contract_id=contract_id,
                    sort_order=sort_order,
                    category="管理指标",
                    indicator_name=work["name"],
                    indicator_description=work.get("description"),
                    weight=0,
                    unit="进度%",
                    target_value="100%",
                    scoring_rule="按进度评分",
                    data_source="项目管理系统",
                    evaluation_method="进度同步",
                    source_type="work",
                    source_id=work["id"],
                )
                db.add(item)
                items_created.append(
                    {"type": "annual_work", "id": work["id"], "name": work["name"]}
                )

        contract = _get_contract_or_404(db, contract_id)
        contract.strategy_id = strategy_id
        db.flush()
        total_weight = _refresh_total_weight(db, contract_id)
        db.commit()

        return ResponseModel(
            code=200,
            message=f"生成成功，共创建{len(items_created)}个指标条目",
            data={
                "items_created": items_created,
                "total_items": sort_order,
                "total_weight": total_weight,
            },
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成失败：{str(e)}")
