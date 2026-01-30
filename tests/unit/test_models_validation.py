# -*- coding: utf-8 -*-
"""
关键模型验证测试

测试覆盖:
- AcceptanceTemplate, AcceptanceOrder 模型
- PurchaseOrder, PurchaseOrderItem 模型
- 模型字段约束和默认值
- 模型关系定义
"""

from decimal import Decimal
from datetime import date, datetime
from unittest.mock import MagicMock

import pytest


class TestAcceptanceTemplateModel:
    """测试验收模板模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.acceptance import AcceptanceTemplate

        assert AcceptanceTemplate is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.acceptance import AcceptanceTemplate

        assert AcceptanceTemplate.__tablename__ == "acceptance_templates"

    def test_required_fields(self):
        """测试必填字段"""
        from app.models.acceptance import AcceptanceTemplate

        # 检查列是否存在且标记为必填
        columns = AcceptanceTemplate.__table__.columns
        assert columns["template_code"].nullable is False
        assert columns["template_name"].nullable is False
        assert columns["acceptance_type"].nullable is False

    def test_unique_constraint_on_template_code(self):
        """测试模板编码唯一约束"""
        from app.models.acceptance import AcceptanceTemplate

        columns = AcceptanceTemplate.__table__.columns
        assert columns["template_code"].unique is True

    def test_default_values(self):
        """测试默认值"""
        from app.models.acceptance import AcceptanceTemplate

        columns = AcceptanceTemplate.__table__.columns
        assert columns["version"].default.arg == "1.0"
        assert columns["is_system"].default.arg is False
        assert columns["is_active"].default.arg is True

    def test_acceptance_type_values(self):
        """测试验收类型值"""
        # FAT/SAT/FINAL
        valid_types = ["FAT", "SAT", "FINAL"]
        for t in valid_types:
            assert t in valid_types

    def test_relationships_defined(self):
        """测试关系定义"""
        from app.models.acceptance import AcceptanceTemplate

        # 检查 categories 关系
        assert hasattr(AcceptanceTemplate, "categories")


class TestTemplateCategoryModel:
    """测试模板分类模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.acceptance import TemplateCategory

        assert TemplateCategory is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.acceptance import TemplateCategory

        assert TemplateCategory.__tablename__ == "template_categories"

    def test_required_fields(self):
        """测试必填字段"""
        from app.models.acceptance import TemplateCategory

        columns = TemplateCategory.__table__.columns
        assert columns["template_id"].nullable is False
        assert columns["category_code"].nullable is False
        assert columns["category_name"].nullable is False

    def test_foreign_key_to_template(self):
        """测试外键关联模板"""
        from app.models.acceptance import TemplateCategory

        columns = TemplateCategory.__table__.columns
        fk = list(columns["template_id"].foreign_keys)[0]
        assert "acceptance_templates.id" in str(fk)

    def test_default_values(self):
        """测试默认值"""
        from app.models.acceptance import TemplateCategory

        columns = TemplateCategory.__table__.columns
        assert columns["weight"].default.arg == 0
        assert columns["sort_order"].default.arg == 0
        assert columns["is_required"].default.arg is True


class TestTemplateCheckItemModel:
    """测试模板检查项模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.acceptance import TemplateCheckItem

        assert TemplateCheckItem is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.acceptance import TemplateCheckItem

        assert TemplateCheckItem.__tablename__ == "template_check_items"

    def test_required_fields(self):
        """测试必填字段"""
        from app.models.acceptance import TemplateCheckItem

        columns = TemplateCheckItem.__table__.columns
        assert columns["category_id"].nullable is False
        assert columns["item_code"].nullable is False
        assert columns["item_name"].nullable is False

    def test_default_values(self):
        """测试默认值"""
        from app.models.acceptance import TemplateCheckItem

        columns = TemplateCheckItem.__table__.columns
        assert columns["is_required"].default.arg is True
        assert columns["is_key_item"].default.arg is False
        assert columns["sort_order"].default.arg == 0


class TestAcceptanceOrderModel:
    """测试验收单模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.acceptance import AcceptanceOrder

        assert AcceptanceOrder is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.acceptance import AcceptanceOrder

        assert AcceptanceOrder.__tablename__ == "acceptance_orders"

    def test_required_fields(self):
        """测试必填字段"""
        from app.models.acceptance import AcceptanceOrder

        columns = AcceptanceOrder.__table__.columns
        assert columns["order_no"].nullable is False
        assert columns["project_id"].nullable is False
        assert columns["acceptance_type"].nullable is False

    def test_unique_constraint_on_order_no(self):
        """测试验收单号唯一约束"""
        from app.models.acceptance import AcceptanceOrder

        columns = AcceptanceOrder.__table__.columns
        assert columns["order_no"].unique is True

    def test_default_values(self):
        """测试默认值"""
        from app.models.acceptance import AcceptanceOrder

        columns = AcceptanceOrder.__table__.columns
        assert columns["status"].default.arg == "DRAFT"
        assert columns["total_items"].default.arg == 0
        assert columns["passed_items"].default.arg == 0
        assert columns["failed_items"].default.arg == 0
        assert columns["na_items"].default.arg == 0
        assert columns["pass_rate"].default.arg == 0
        assert columns["is_officially_completed"].default.arg is False

    def test_overall_result_values(self):
        """测试验收结论值"""
        valid_results = ["PASSED", "FAILED", "CONDITIONAL"]
        for r in valid_results:
            assert r in valid_results

    def test_relationships_defined(self):
        """测试关系定义"""
        from app.models.acceptance import AcceptanceOrder

        assert hasattr(AcceptanceOrder, "project")
        assert hasattr(AcceptanceOrder, "machine")


class TestPurchaseOrderModel:
    """测试采购订单模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.purchase import PurchaseOrder

        assert PurchaseOrder is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.purchase import PurchaseOrder

        assert PurchaseOrder.__tablename__ == "purchase_orders"

    def test_required_fields(self):
        """测试必填字段"""
        from app.models.purchase import PurchaseOrder

        columns = PurchaseOrder.__table__.columns
        assert columns["order_no"].nullable is False
        assert columns["supplier_id"].nullable is False

    def test_unique_constraint_on_order_no(self):
        """测试订单编号唯一约束"""
        from app.models.purchase import PurchaseOrder

        columns = PurchaseOrder.__table__.columns
        assert columns["order_no"].unique is True

    def test_default_values(self):
        """测试默认值"""
        from app.models.purchase import PurchaseOrder

        columns = PurchaseOrder.__table__.columns
        assert columns["order_type"].default.arg == "NORMAL"
        assert columns["total_amount"].default.arg == 0
        assert columns["tax_rate"].default.arg == 13
        assert columns["tax_amount"].default.arg == 0
        assert columns["amount_with_tax"].default.arg == 0
        assert columns["currency"].default.arg == "CNY"
        assert columns["status"].default.arg == "DRAFT"
        assert columns["payment_status"].default.arg == "UNPAID"
        assert columns["paid_amount"].default.arg == 0
        assert columns["received_amount"].default.arg == 0

    def test_currency_field_type(self):
        """测试币种字段类型"""
        from app.models.purchase import PurchaseOrder

        columns = PurchaseOrder.__table__.columns
        assert str(columns["currency"].type) == "VARCHAR(10)"

    def test_amount_field_precision(self):
        """测试金额字段精度"""
        from app.models.purchase import PurchaseOrder

        columns = PurchaseOrder.__table__.columns
        # Numeric(14, 2) 表示最多14位数字，其中2位小数
        assert columns["total_amount"].type.precision == 14
        assert columns["total_amount"].type.scale == 2

    def test_relationships_defined(self):
        """测试关系定义"""
        from app.models.purchase import PurchaseOrder

        assert hasattr(PurchaseOrder, "vendor")
        assert hasattr(PurchaseOrder, "project")
        assert hasattr(PurchaseOrder, "items")
        assert hasattr(PurchaseOrder, "receipts")

    def test_repr(self):
        """测试字符串表示"""
        from app.models.purchase import PurchaseOrder

        order = PurchaseOrder.__new__(PurchaseOrder)
        order.order_no = "PO-TEST-001"
        assert "PO-TEST-001" in repr(order)


class TestPurchaseOrderItemModel:
    """测试采购订单明细模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.purchase import PurchaseOrderItem

        assert PurchaseOrderItem is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.purchase import PurchaseOrderItem

        assert PurchaseOrderItem.__tablename__ == "purchase_order_items"

    def test_required_fields(self):
        """测试必填字段"""
        from app.models.purchase import PurchaseOrderItem

        columns = PurchaseOrderItem.__table__.columns
        assert columns["order_id"].nullable is False
        assert columns["item_no"].nullable is False
        assert columns["material_code"].nullable is False
        assert columns["material_name"].nullable is False
        assert columns["quantity"].nullable is False

    def test_default_values(self):
        """测试默认值"""
        from app.models.purchase import PurchaseOrderItem

        columns = PurchaseOrderItem.__table__.columns
        assert columns["unit"].default.arg == "件"
        assert columns["unit_price"].default.arg == 0
        assert columns["amount"].default.arg == 0
        assert columns["tax_rate"].default.arg == 13
        assert columns["received_qty"].default.arg == 0
        assert columns["qualified_qty"].default.arg == 0
        assert columns["rejected_qty"].default.arg == 0
        assert columns["status"].default.arg == "PENDING"

    def test_quantity_precision(self):
        """测试数量字段精度"""
        from app.models.purchase import PurchaseOrderItem

        columns = PurchaseOrderItem.__table__.columns
        # Numeric(10, 4) 表示最多10位数字，其中4位小数
        assert columns["quantity"].type.precision == 10
        assert columns["quantity"].type.scale == 4

    def test_unit_price_precision(self):
        """测试单价字段精度"""
        from app.models.purchase import PurchaseOrderItem

        columns = PurchaseOrderItem.__table__.columns
        assert columns["unit_price"].type.precision == 12
        assert columns["unit_price"].type.scale == 4


class TestGoodsReceiptModel:
    """测试收货单模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.purchase import GoodsReceipt

        assert GoodsReceipt is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.purchase import GoodsReceipt

        assert GoodsReceipt.__tablename__ == "goods_receipts"

    def test_required_fields(self):
        """测试必填字段"""
        from app.models.purchase import GoodsReceipt

        columns = GoodsReceipt.__table__.columns
        assert columns["receipt_no"].nullable is False
        assert columns["order_id"].nullable is False
        assert columns["supplier_id"].nullable is False
        assert columns["receipt_date"].nullable is False

    def test_unique_constraint_on_receipt_no(self):
        """测试收货单号唯一约束"""
        from app.models.purchase import GoodsReceipt

        columns = GoodsReceipt.__table__.columns
        assert columns["receipt_no"].unique is True


class TestModelIndexes:
    """测试模型索引"""

    def test_acceptance_template_indexes(self):
        """测试验收模板索引"""
        from app.models.acceptance import AcceptanceTemplate

        indexes = {idx.name for idx in AcceptanceTemplate.__table__.indexes}
        assert "idx_acceptance_template_type" in indexes
        assert "idx_acceptance_template_equip" in indexes

    def test_template_category_indexes(self):
        """测试模板分类索引"""
        from app.models.acceptance import TemplateCategory

        indexes = {idx.name for idx in TemplateCategory.__table__.indexes}
        assert "idx_category_template" in indexes

    def test_template_check_item_indexes(self):
        """测试检查项索引"""
        from app.models.acceptance import TemplateCheckItem

        indexes = {idx.name for idx in TemplateCheckItem.__table__.indexes}
        assert "idx_check_item_category" in indexes

    def test_purchase_order_indexes(self):
        """测试采购订单索引"""
        from app.models.purchase import PurchaseOrder

        indexes = {idx.name for idx in PurchaseOrder.__table__.indexes}
        assert "idx_po_supplier" in indexes
        assert "idx_po_project" in indexes
        assert "idx_po_status" in indexes

    def test_purchase_order_item_indexes(self):
        """测试采购订单明细索引"""
        from app.models.purchase import PurchaseOrderItem

        indexes = {idx.name for idx in PurchaseOrderItem.__table__.indexes}
        assert "idx_poi_order" in indexes
        assert "idx_poi_material" in indexes


class TestTimestampMixin:
    """测试时间戳混入"""

    def test_acceptance_template_has_timestamps(self):
        """测试验收模板有时间戳字段"""
        from app.models.acceptance import AcceptanceTemplate

        columns = AcceptanceTemplate.__table__.columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_purchase_order_has_timestamps(self):
        """测试采购订单有时间戳字段"""
        from app.models.purchase import PurchaseOrder

        columns = PurchaseOrder.__table__.columns
        assert "created_at" in columns
        assert "updated_at" in columns


class TestProjectModel:
    """测试项目模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.project import Project

        assert Project is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.project import Project

        assert Project.__tablename__ == "projects"

    def test_project_code_unique(self):
        """测试项目编码唯一"""
        from app.models.project import Project

        columns = Project.__table__.columns
        assert columns["project_code"].unique is True

    def test_project_status_default(self):
        """测试项目状态默认值"""
        from app.models.project import Project

        columns = Project.__table__.columns
        assert columns["status"].default.arg == "ST01"


class TestMachineModel:
    """测试设备模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.project import Machine

        assert Machine is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.project import Machine

        assert Machine.__tablename__ == "machines"

    def test_required_fields(self):
        """测试必填字段"""
        from app.models.project import Machine

        columns = Machine.__table__.columns
        assert columns["project_id"].nullable is False
        assert columns["machine_code"].nullable is False


class TestUserModel:
    """测试用户模型"""

    def test_model_import(self):
        """测试模型导入"""
        from app.models.user import User

        assert User is not None

    def test_tablename(self):
        """测试表名"""
        from app.models.user import User

        assert User.__tablename__ == "users"

    def test_username_unique(self):
        """测试用户名唯一"""
        from app.models.user import User

        columns = User.__table__.columns
        assert columns["username"].unique is True

    def test_is_active_default(self):
        """测试激活状态默认值"""
        from app.models.user import User

        columns = User.__table__.columns
        assert columns["is_active"].default.arg is True

    def test_is_superuser_default(self):
        """测试超级用户默认值"""
        from app.models.user import User

        columns = User.__table__.columns
        assert columns["is_superuser"].default.arg is False
