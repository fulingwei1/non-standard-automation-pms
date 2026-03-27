# -*- coding: utf-8 -*-
"""物料采购管理 P3 增强接口测试"""

from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from fastapi.testclient import TestClient

from app.models.ecn.core import Ecn
from app.models.ecn.impact import EcnAffectedMaterial
from app.models.inventory_tracking import MaterialStock, MaterialTransaction
from app.models.material import BomHeader, BomItem, Material, MaterialShortage
from app.models.project import Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, PurchaseRequest, PurchaseRequestItem
from app.models.vendor import Vendor


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _u(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:6].upper()}"


class TestMaterialProcurementOptimization:
    def test_shortage_waste_calculation(self, client: TestClient, admin_token: str):
        headers = _auth_headers(admin_token)
        payload = {
            "waiting_workers": 5,
            "labor_hourly_rate": 100,
            "waiting_hours": 8,
            "idle_machines": 2,
            "machine_hourly_rate": 150,
            "contract_amount": 100000,
            "delay_days": 3,
            "daily_penalty_rate": 0.001,
            "daily_output_value": 5000,
            "include_management_buffer": True,
            "management_buffer_rate": 0.1,
        }
        response = client.post(
            "/api/v1/material/shortage-waste-calculation", json=payload, headers=headers
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["cost_breakdown"]["labor_idle_cost"] == "4000.00"
        assert data["cost_breakdown"]["machine_idle_cost"] == "2400.00"
        assert data["cost_breakdown"]["delay_penalty"] == "300.00"
        assert data["cost_breakdown"]["opportunity_cost"] == "15000.00"
        assert data["total_waste_amount"] == "23870.00"
        assert data["daily_waste_amount"] == "7956.67"

    def test_safety_stock_alerts(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)

        material = Material(
            material_code=_u("MAT"),
            material_name="安全库存测试料",
            specification="SS-01",
            unit="件",
            lead_time_days=10,
            min_order_qty=Decimal("20"),
            current_stock=Decimal("10"),
            is_active=True,
        )
        db.add(material)
        db.flush()

        stock = MaterialStock(
            tenant_id=1,
            material_id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            location="主仓",
            batch_number=_u("BATCH"),
            quantity=Decimal("10"),
            available_quantity=Decimal("10"),
            unit="件",
        )
        db.add(stock)

        for days_ago in (10, 20, 30):
            db.add(
                MaterialTransaction(
                    tenant_id=1,
                    material_id=material.id,
                    material_code=material.material_code,
                    material_name=material.material_name,
                    transaction_type="ISSUE",
                    quantity=Decimal("-30"),
                    unit="件",
                    transaction_date=datetime.now() - timedelta(days=days_ago),
                )
            )
            db.add(
                MaterialShortage(
                    project_id=1,
                    material_id=material.id,
                    material_code=material.material_code,
                    material_name=material.material_name,
                    required_qty=Decimal("50"),
                    available_qty=Decimal("10"),
                    shortage_qty=Decimal("40"),
                    created_at=datetime.now() - timedelta(days=days_ago),
                )
            )
        db.commit()

        response = client.get(
            "/api/v1/material/safety-stock-alerts",
            params={"days": 90, "safety_factor": 1.5, "focus_shortage_threshold": 2},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        matched = [x for x in data["items"] if x["material_id"] == material.id]
        assert matched, data
        item = matched[0]
        assert item["alert_level"] in ["紧急", "警告"]
        assert item["is_high_frequency_shortage"] is True
        assert Decimal(item["calculated_safety_stock"]) > Decimal("0")
        assert Decimal(item["suggested_replenishment_qty"]) >= Decimal("20")

    def test_check_duplicate_purchase(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)

        vendor = Vendor(
            supplier_code=_u("SUP"),
            supplier_name="重复采购供应商",
            vendor_type="MATERIAL",
            status="ACTIVE",
        )
        db.add(vendor)
        db.flush()

        project = Project(
            project_code=_u("PJ"),
            project_name="重复采购项目",
            customer_name="测试客户",
            stage="S1",
            status="ST01",
            health="H1",
        )
        db.add(project)
        db.flush()

        material = Material(
            material_code=_u("MAT"),
            material_name="重复采购物料",
            specification="DP-01",
            unit="件",
            is_active=True,
        )
        db.add(material)
        db.flush()

        bom = BomHeader(
            bom_no=_u("BOM"),
            bom_name="重复采购BOM",
            project_id=project.id,
            version="1.1",
            is_latest=True,
            status="APPROVED",
        )
        db.add(bom)
        db.flush()

        db.add(
            BomItem(
                bom_id=bom.id,
                item_no=1,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                quantity=Decimal("15"),
                unit="件",
                source_type="PURCHASE",
            )
        )

        pr = PurchaseRequest(
            request_no=_u("PR"),
            project_id=project.id,
            supplier_id=vendor.id,
            request_type="NORMAL",
            status="APPROVED",
        )
        db.add(pr)
        db.flush()
        db.add(
            PurchaseRequestItem(
                request_id=pr.id,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                quantity=Decimal("20"),
                unit="件",
            )
        )

        po = PurchaseOrder(
            order_no=_u("PO"),
            supplier_id=vendor.id,
            project_id=project.id,
            order_type="NORMAL",
            status="APPROVED",
        )
        db.add(po)
        db.flush()
        db.add(
            PurchaseOrderItem(
                order_id=po.id,
                item_no=1,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                quantity=Decimal("30"),
                unit="件",
                received_qty=Decimal("5"),
                status="PENDING",
            )
        )
        db.commit()

        response = client.post(
            "/api/v1/material/check-duplicate-purchase",
            json={
                "project_id": project.id,
                "material_id": material.id,
                "material_code": material.material_code,
                "specification": material.specification,
                "requested_quantity": 10,
                "requested_bom_version": "1.0",
            },
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["duplicate_found"] is True
        assert len(data["duplicate_purchase_requests"]) >= 1
        assert len(data["duplicate_purchase_orders"]) >= 1
        assert data["bom_consistency"]["version_conflict"] is True

    def test_slow_moving_analysis(self, client: TestClient, admin_token: str, db):
        headers = _auth_headers(admin_token)

        material = Material(
            material_code=_u("MAT"),
            material_name="呆滞测试物料",
            specification="SM-01",
            unit="件",
            current_stock=Decimal("50"),
            last_price=Decimal("100"),
            is_active=True,
        )
        db.add(material)
        db.flush()

        db.add(
            MaterialStock(
                tenant_id=1,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                location="主仓",
                batch_number=_u("BAT"),
                quantity=Decimal("50"),
                available_quantity=Decimal("50"),
                unit="件",
                unit_price=Decimal("100"),
                total_value=Decimal("5000"),
            )
        )
        db.add(
            MaterialTransaction(
                tenant_id=1,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                transaction_type="ISSUE",
                quantity=Decimal("-5"),
                unit="件",
                transaction_date=datetime.now() - timedelta(days=220),
            )
        )

        ecn = Ecn(
            ecn_no=_u("ECN"),
            ecn_title="设计淘汰",
            status="APPROVED",
        )
        db.add(ecn)
        db.flush()
        db.add(
            EcnAffectedMaterial(
                ecn_id=ecn.id,
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                change_type="DELETE",
                is_obsolete_risk=True,
                obsolete_risk_level="HIGH",
                status="PENDING",
            )
        )
        db.commit()

        response = client.get("/api/v1/material/slow-moving-analysis", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        matched = [x for x in data["items"] if x["material_id"] == material.id]
        assert matched, data
        item = matched[0]
        assert item["category"] in ["呆滞", "报废"]
        assert item["reason"] in ["ECN变更/设计淘汰", "需求下降导致慢动", "长期无消耗", "采购过量", "质量问题", "项目取消或停滞"]
        assert Decimal(item["potential_recovery_amount"]) >= Decimal("0")
