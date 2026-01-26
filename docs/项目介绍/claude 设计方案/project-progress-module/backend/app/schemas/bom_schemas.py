"""
BOM管理模块 - Pydantic Schema定义
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ==================== 物料相关Schema ====================

class MaterialBase(BaseModel):
    """物料基础信息"""
    material_code: str = Field(..., max_length=30, description="物料编码")
    material_name: str = Field(..., max_length=200, description="物料名称")
    specification: Optional[str] = Field(None, max_length=200, description="规格型号")
    brand: Optional[str] = Field(None, max_length=50, description="品牌")
    category: str = Field(..., max_length=20, description="大类：ME/EL/PN/ST/OT/TR")
    sub_category: Optional[str] = Field(None, max_length=50, description="子类别")
    unit: str = Field("pcs", max_length=20, description="单位")
    reference_price: Optional[Decimal] = Field(None, description="参考单价")
    default_supplier_id: Optional[int] = Field(None, description="默认供应商ID")
    default_supplier_name: Optional[str] = Field(None, max_length=100, description="默认供应商")
    lead_time: int = Field(7, description="标准采购周期(天)")
    min_order_qty: Decimal = Field(1, description="最小起订量")
    is_standard: int = Field(0, description="是否标准件")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class MaterialCreate(MaterialBase):
    """创建物料"""
    pass


class MaterialUpdate(BaseModel):
    """更新物料"""
    material_name: Optional[str] = Field(None, max_length=200)
    specification: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=20)
    sub_category: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field(None, max_length=20)
    reference_price: Optional[Decimal] = None
    default_supplier_id: Optional[int] = None
    default_supplier_name: Optional[str] = Field(None, max_length=100)
    lead_time: Optional[int] = None
    min_order_qty: Optional[Decimal] = None
    is_standard: Optional[int] = None
    status: Optional[str] = Field(None, max_length=20)
    remark: Optional[str] = Field(None, max_length=500)


class MaterialResponse(MaterialBase):
    """物料响应"""
    material_id: int
    status: str
    created_by: int
    created_time: datetime
    updated_time: Optional[datetime]
    category_name: Optional[str] = None

    class Config:
        from_attributes = True


class MaterialListResponse(BaseModel):
    """物料列表响应"""
    total: int
    items: List[MaterialResponse]


# ==================== BOM明细相关Schema ====================

class BomItemBase(BaseModel):
    """BOM明细基础信息"""
    line_no: int = Field(..., description="行号")
    material_id: Optional[int] = Field(None, description="物料ID")
    material_code: str = Field(..., max_length=30, description="物料编码")
    material_name: str = Field(..., max_length=200, description="物料名称")
    specification: Optional[str] = Field(None, max_length=200, description="规格型号")
    brand: Optional[str] = Field(None, max_length=50, description="品牌")
    category: str = Field(..., max_length=30, description="物料类别")
    unit: str = Field("pcs", max_length=20, description="单位")
    quantity: Decimal = Field(..., description="需求数量")
    unit_price: Optional[Decimal] = Field(None, description="单价")
    supplier_id: Optional[int] = Field(None, description="供应商ID")
    supplier_name: Optional[str] = Field(None, max_length=100, description="供应商名称")
    lead_time: Optional[int] = Field(None, description="采购周期(天)")
    is_long_lead: int = Field(0, description="是否长周期")
    is_key_part: int = Field(0, description="是否关键件")
    required_date: Optional[date] = Field(None, description="需求日期")
    drawing_no: Optional[str] = Field(None, max_length=50, description="图纸号")
    position_no: Optional[str] = Field(None, max_length=50, description="位置号")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class BomItemCreate(BomItemBase):
    """创建BOM明细"""
    pass


class BomItemUpdate(BaseModel):
    """更新BOM明细"""
    material_id: Optional[int] = None
    material_code: Optional[str] = Field(None, max_length=30)
    material_name: Optional[str] = Field(None, max_length=200)
    specification: Optional[str] = Field(None, max_length=200)
    brand: Optional[str] = Field(None, max_length=50)
    category: Optional[str] = Field(None, max_length=30)
    unit: Optional[str] = Field(None, max_length=20)
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = Field(None, max_length=100)
    lead_time: Optional[int] = None
    is_long_lead: Optional[int] = None
    is_key_part: Optional[int] = None
    required_date: Optional[date] = None
    drawing_no: Optional[str] = Field(None, max_length=50)
    position_no: Optional[str] = Field(None, max_length=50)
    remark: Optional[str] = Field(None, max_length=500)


class BomItemResponse(BomItemBase):
    """BOM明细响应"""
    item_id: int
    bom_id: int
    project_id: int
    category_name: Optional[str] = None
    amount: Optional[Decimal] = None
    ordered_qty: Decimal = 0
    received_qty: Decimal = 0
    stock_qty: Decimal = 0
    shortage_qty: Decimal = 0
    procurement_status: str = "待采购"
    version: str = "V1.0"
    created_time: datetime
    updated_time: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== BOM头表相关Schema ====================

class BomHeaderBase(BaseModel):
    """BOM头表基础信息"""
    project_id: int = Field(..., description="项目ID")
    project_code: str = Field(..., max_length=30, description="项目编号")
    machine_no: str = Field(..., max_length=30, description="机台号")
    machine_name: Optional[str] = Field(None, max_length=100, description="机台名称")
    bom_type: str = Field("整机", max_length=20, description="BOM类型")
    designer_id: int = Field(..., description="设计人ID")
    designer_name: str = Field(..., max_length=50, description="设计人")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class BomHeaderCreate(BomHeaderBase):
    """创建BOM"""
    items: Optional[List[BomItemCreate]] = Field(None, description="BOM明细列表")


class BomHeaderUpdate(BaseModel):
    """更新BOM头表"""
    machine_name: Optional[str] = Field(None, max_length=100)
    bom_type: Optional[str] = Field(None, max_length=20)
    designer_id: Optional[int] = None
    designer_name: Optional[str] = Field(None, max_length=50)
    remark: Optional[str] = Field(None, max_length=500)


class BomHeaderResponse(BomHeaderBase):
    """BOM头表响应"""
    bom_id: int
    current_version: str
    status: str
    total_items: int
    total_cost: Decimal
    kit_rate: Decimal
    reviewer_id: Optional[int]
    reviewer_name: Optional[str]
    review_time: Optional[datetime]
    publish_time: Optional[datetime]
    created_by: int
    created_time: datetime
    updated_time: Optional[datetime]

    class Config:
        from_attributes = True


class BomDetailResponse(BomHeaderResponse):
    """BOM详情响应（含明细）"""
    items: List[BomItemResponse] = []


class BomListResponse(BaseModel):
    """BOM列表响应"""
    total: int
    items: List[BomHeaderResponse]


# ==================== BOM版本相关Schema ====================

class BomVersionCreate(BaseModel):
    """创建BOM版本"""
    version_type: str = Field(..., max_length=20, description="版本类型：初始/变更/修订")
    ecn_id: Optional[int] = Field(None, description="关联ECN ID")
    ecn_code: Optional[str] = Field(None, max_length=30, description="ECN编号")
    change_summary: Optional[str] = Field(None, max_length=500, description="变更摘要")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class BomVersionResponse(BaseModel):
    """BOM版本响应"""
    version_id: int
    bom_id: int
    version: str
    version_type: str
    ecn_id: Optional[int]
    ecn_code: Optional[str]
    change_summary: Optional[str]
    total_items: int
    total_cost: Decimal
    published_by: int
    published_name: str
    published_time: datetime
    remark: Optional[str]

    class Config:
        from_attributes = True


class BomVersionListResponse(BaseModel):
    """版本列表响应"""
    total: int
    items: List[BomVersionResponse]


# ==================== BOM统计相关Schema ====================

class BomStatistics(BaseModel):
    """BOM统计信息"""
    total_bom: int = Field(..., description="BOM总数")
    draft_count: int = Field(..., description="草稿数量")
    reviewing_count: int = Field(..., description="评审中数量")
    published_count: int = Field(..., description="已发布数量")
    frozen_count: int = Field(..., description="已冻结数量")


class CategoryStatistics(BaseModel):
    """物料类别统计"""
    category: str
    category_name: str
    count: int
    amount: Decimal


class KitRateStatistics(BaseModel):
    """齐套率统计"""
    bom_id: int
    machine_no: str
    total_items: int
    completed_items: int
    kit_rate: Decimal
    shortage_items: int


class ShortageItem(BaseModel):
    """缺料物料"""
    item_id: int
    bom_id: int
    machine_no: str
    material_code: str
    material_name: str
    specification: Optional[str]
    category: str
    quantity: Decimal
    received_qty: Decimal
    shortage_qty: Decimal
    required_date: Optional[date]
    lead_time: Optional[int]
    supplier_name: Optional[str]


class ShortageListResponse(BaseModel):
    """缺料清单响应"""
    total: int
    items: List[ShortageItem]


# ==================== BOM操作相关Schema ====================

class BomReviewRequest(BaseModel):
    """BOM评审请求"""
    action: str = Field(..., description="操作：submit/approve/reject")
    reviewer_id: Optional[int] = Field(None, description="审核人ID")
    reviewer_name: Optional[str] = Field(None, max_length=50, description="审核人")
    comment: Optional[str] = Field(None, max_length=500, description="评审意见")


class BomPublishRequest(BaseModel):
    """BOM发布请求"""
    version_type: str = Field("初始", description="版本类型")
    change_summary: Optional[str] = Field(None, max_length=500, description="变更摘要")


class BomImportRequest(BaseModel):
    """BOM导入请求"""
    bom_id: int = Field(..., description="目标BOM ID")
    file_type: str = Field("excel", description="文件类型：excel/csv")
    update_mode: str = Field("append", description="更新模式：append/replace")


class BomExportRequest(BaseModel):
    """BOM导出请求"""
    bom_ids: List[int] = Field(..., description="BOM ID列表")
    file_type: str = Field("excel", description="文件类型：excel/csv/pdf")
    include_price: bool = Field(False, description="是否包含价格")


class BomCompareRequest(BaseModel):
    """BOM版本对比请求"""
    version_id_1: int = Field(..., description="版本1 ID")
    version_id_2: int = Field(..., description="版本2 ID")


class BomCompareItem(BaseModel):
    """BOM对比明细"""
    material_code: str
    material_name: str
    change_type: str  # added/removed/modified
    old_quantity: Optional[Decimal]
    new_quantity: Optional[Decimal]
    old_price: Optional[Decimal]
    new_price: Optional[Decimal]


class BomCompareResponse(BaseModel):
    """BOM版本对比响应"""
    version_1: str
    version_2: str
    added_count: int
    removed_count: int
    modified_count: int
    items: List[BomCompareItem]


# ==================== 批量操作Schema ====================

class BatchUpdateProcurementStatus(BaseModel):
    """批量更新采购状态"""
    item_ids: List[int] = Field(..., description="明细ID列表")
    procurement_status: str = Field(..., description="采购状态")
    ordered_qty: Optional[Decimal] = Field(None, description="下单数量")
    received_qty: Optional[Decimal] = Field(None, description="到货数量")


class BatchUpdateSupplier(BaseModel):
    """批量更新供应商"""
    item_ids: List[int] = Field(..., description="明细ID列表")
    supplier_id: int = Field(..., description="供应商ID")
    supplier_name: str = Field(..., max_length=100, description="供应商名称")


class BatchDeleteItems(BaseModel):
    """批量删除明细"""
    item_ids: List[int] = Field(..., description="明细ID列表")
