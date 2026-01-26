#!/usr/bin/env python3
"""
Migrate procurement/kit-rate schema to the new vendor-based structure.
Drops legacy tables and recreates the current models' tables in-place.
"""

import os
import sys

from sqlalchemy import text

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from app.models.assembly_kit import KitRateSnapshot
from app.models.base import Base, get_engine
from app.models.material import BomHeader, BomItem, Material, MaterialCategory, MaterialSupplier
from app.models.purchase import GoodsReceipt, GoodsReceiptItem, PurchaseOrder, PurchaseOrderItem
from app.models.vendor import Vendor


DROP_TABLES = [
    "goods_receipt_items",
    "goods_receipts",
    "purchase_order_items",
    "purchase_orders",
    "bom_items",
    "bom_headers",
    "material_suppliers",
    "materials",
    "material_categories",
    "mes_kit_rate_snapshot",
    "vendors",
    "suppliers",
    "outsourcing_vendors",
    "bom_versions",
]

DROP_INDEXES = [
    "idx_material_type",
    "idx_material_category",
    "idx_bom_project",
    "idx_bom_machine",
    "idx_poi_order",
    "idx_poi_material",
    "idx_po_supplier",
    "idx_po_project",
    "idx_po_status",
    "idx_po_source_request",
    "idx_gr_order",
    "idx_gr_supplier",
    "idx_gr_status",
    "idx_ms_material",
    "idx_ms_supplier",
    "idx_kit_snapshot_project_date",
    "idx_kit_snapshot_machine_date",
    "idx_kit_snapshot_type",
    "idx_kit_snapshot_date",
    "idx_kit_snapshot_project_time",
    "idx_vendor_type",
    "idx_vendor_status",
    "idx_vendor_level",
]


def main() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        for index_name in DROP_INDEXES:
            conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
        for table_name in DROP_TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.execute(text("PRAGMA foreign_keys = ON"))

    Base.metadata.create_all(
        bind=engine,
        tables=[
            Vendor.__table__,
            MaterialCategory.__table__,
            Material.__table__,
            MaterialSupplier.__table__,
            BomHeader.__table__,
            BomItem.__table__,
            PurchaseOrder.__table__,
            PurchaseOrderItem.__table__,
            GoodsReceipt.__table__,
            GoodsReceiptItem.__table__,
            KitRateSnapshot.__table__,
        ],
    )

    print("Procurement/kit-rate schema migration completed.")


if __name__ == "__main__":
    main()
