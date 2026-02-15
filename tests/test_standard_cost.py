# -*- coding: utf-8 -*-
"""
标准成本库管理单元测试
"""

import io
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.standard_cost import StandardCost, StandardCostHistory
from app.models.user import User


class TestStandardCostCRUD:
    """标准成本CRUD测试"""

    def test_create_standard_cost(self, client, admin_headers, db: Session):
        """测试创建标准成本"""
        data = {
            "cost_code": "TEST-001",
            "cost_name": "测试物料",
            "cost_category": "MATERIAL",
            "specification": "测试规格",
            "unit": "kg",
            "standard_cost": 10.50,
            "currency": "CNY",
            "cost_source": "HISTORICAL_AVG",
            "source_description": "测试来源",
            "effective_date": "2026-01-01",
            "description": "测试成本"
        }
        
        response = client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        assert response.status_code == status.HTTP_201_CREATED
        
        result = response.json()
        assert result["cost_code"] == "TEST-001"
        assert result["cost_name"] == "测试物料"
        assert result["version"] == 1
        assert result["is_active"] is True

    def test_create_duplicate_cost_code(self, client, admin_headers, db: Session):
        """测试创建重复成本编码"""
        # 创建第一个
        data = {
            "cost_code": "DUP-001",
            "cost_name": "重复测试",
            "cost_category": "MATERIAL",
            "unit": "件",
            "standard_cost": 5.00,
            "cost_source": "HISTORICAL_AVG",
            "effective_date": "2026-01-01"
        }
        client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        
        # 尝试创建重复的
        response = client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_standard_costs(self, client, admin_headers, db: Session):
        """测试获取标准成本列表"""
        # 创建几个成本项
        for i in range(3):
            data = {
                "cost_code": f"LIST-{i:03d}",
                "cost_name": f"列表测试{i}",
                "cost_category": "MATERIAL",
                "unit": "件",
                "standard_cost": float(10 + i),
                "cost_source": "HISTORICAL_AVG",
                "effective_date": "2026-01-01"
            }
            client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        
        response = client.get("/api/v1/standard-costs/", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert "items" in result
        assert len(result["items"]) >= 3

    def test_list_with_category_filter(self, client, admin_headers, db: Session):
        """测试按类别筛选"""
        # 创建不同类别的成本项
        categories = ["MATERIAL", "LABOR", "OVERHEAD"]
        for cat in categories:
            data = {
                "cost_code": f"CAT-{cat}",
                "cost_name": f"{cat}成本",
                "cost_category": cat,
                "unit": "件",
                "standard_cost": 10.0,
                "cost_source": "HISTORICAL_AVG",
                "effective_date": "2026-01-01"
            }
            client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        
        response = client.get(
            "/api/v1/standard-costs/?cost_category=MATERIAL",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        for item in result["items"]:
            if item["cost_code"].startswith("CAT-"):
                assert item["cost_category"] == "MATERIAL"

    def test_search_standard_costs(self, client, admin_headers, db: Session):
        """测试搜索标准成本"""
        # 创建测试数据
        data = {
            "cost_code": "SEARCH-001",
            "cost_name": "可搜索物料",
            "cost_category": "MATERIAL",
            "specification": "特殊规格",
            "unit": "kg",
            "standard_cost": 15.0,
            "cost_source": "VENDOR_QUOTE",
            "effective_date": "2026-01-01"
        }
        client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        
        # 按编码搜索
        response = client.get(
            "/api/v1/standard-costs/search?keyword=SEARCH",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.json()
        assert any(item["cost_code"] == "SEARCH-001" for item in results)

    def test_get_standard_cost_by_id(self, client, admin_headers, db: Session):
        """测试获取标准成本详情"""
        # 创建成本项
        data = {
            "cost_code": "GET-001",
            "cost_name": "详情测试",
            "cost_category": "MATERIAL",
            "unit": "件",
            "standard_cost": 20.0,
            "cost_source": "HISTORICAL_AVG",
            "effective_date": "2026-01-01"
        }
        create_response = client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        cost_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/standard-costs/{cost_id}", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert result["id"] == cost_id
        assert result["cost_code"] == "GET-001"

    def test_update_standard_cost(self, client, admin_headers, db: Session):
        """测试更新标准成本（创建新版本）"""
        # 创建成本项
        data = {
            "cost_code": "UPD-001",
            "cost_name": "更新测试",
            "cost_category": "MATERIAL",
            "unit": "kg",
            "standard_cost": 10.0,
            "cost_source": "HISTORICAL_AVG",
            "effective_date": "2026-01-01"
        }
        create_response = client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        cost_id = create_response.json()["id"]
        
        # 更新成本
        update_data = {
            "standard_cost": 12.0,
            "notes": "价格上涨"
        }
        response = client.put(
            f"/api/v1/standard-costs/{cost_id}",
            json=update_data,
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert float(result["standard_cost"]) == 12.0
        assert result["version"] == 2
        assert result["parent_id"] == cost_id

    def test_deactivate_standard_cost(self, client, admin_headers, db: Session):
        """测试停用标准成本"""
        # 创建成本项
        data = {
            "cost_code": "DEL-001",
            "cost_name": "停用测试",
            "cost_category": "MATERIAL",
            "unit": "件",
            "standard_cost": 5.0,
            "cost_source": "HISTORICAL_AVG",
            "effective_date": "2026-01-01"
        }
        create_response = client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        cost_id = create_response.json()["id"]
        
        # 停用
        response = client.delete(f"/api/v1/standard-costs/{cost_id}", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        
        # 验证已停用
        get_response = client.get(f"/api/v1/standard-costs/{cost_id}", headers=admin_headers)
        assert get_response.json()["is_active"] is False


class TestStandardCostHistory:
    """标准成本历史记录测试"""

    def test_get_cost_history(self, client, admin_headers, db: Session):
        """测试获取成本历史记录"""
        # 创建并更新成本项
        data = {
            "cost_code": "HIST-001",
            "cost_name": "历史测试",
            "cost_category": "MATERIAL",
            "unit": "kg",
            "standard_cost": 10.0,
            "cost_source": "HISTORICAL_AVG",
            "effective_date": "2026-01-01"
        }
        create_response = client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        cost_id = create_response.json()["id"]
        
        # 获取历史记录
        response = client.get(
            f"/api/v1/standard-costs/{cost_id}/history",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        history = response.json()
        assert len(history) >= 1
        assert history[0]["change_type"] == "CREATE"

    def test_get_cost_versions(self, client, admin_headers, db: Session):
        """测试获取成本版本列表"""
        # 创建成本项
        data = {
            "cost_code": "VER-001",
            "cost_name": "版本测试",
            "cost_category": "MATERIAL",
            "unit": "kg",
            "standard_cost": 10.0,
            "cost_source": "HISTORICAL_AVG",
            "effective_date": "2026-01-01"
        }
        create_response = client.post("/api/v1/standard-costs/", json=data, headers=admin_headers)
        cost_id = create_response.json()["id"]
        
        # 更新几次，创建多个版本
        for i in range(2):
            update_data = {"standard_cost": 10.0 + i}
            update_response = client.put(
                f"/api/v1/standard-costs/{cost_id}",
                json=update_data,
                headers=admin_headers
            )
            cost_id = update_response.json()["id"]
        
        # 获取所有版本
        response = client.get(
            f"/api/v1/standard-costs/{cost_id}/versions",
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        versions = response.json()
        assert len(versions) == 3  # 原版本 + 2次更新


class TestStandardCostImport:
    """标准成本批量导入测试"""

    def test_download_template(self, client, admin_headers):
        """测试下载导入模板"""
        response = client.get("/api/v1/standard-costs/template", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def test_import_excel(self, client, admin_headers, db: Session):
        """测试Excel导入"""
        # 创建测试Excel文件
        data = {
            '成本项编码*': ['IMP-001', 'IMP-002'],
            '成本项名称*': ['导入测试1', '导入测试2'],
            '成本类别*': ['MATERIAL', 'LABOR'],
            '规格型号': ['规格1', ''],
            '单位*': ['kg', '人天'],
            '标准成本*': [15.5, 800.0],
            '币种': ['CNY', 'CNY'],
            '成本来源*': ['HISTORICAL_AVG', 'EXPERT_ESTIMATE'],
            '来源说明': ['测试', '测试'],
            '生效日期*': ['2026-01-01', '2026-01-01'],
            '失效日期': ['', ''],
            '成本说明': ['', ''],
            '备注': ['', '']
        }
        df = pd.DataFrame(data)
        
        # 转换为Excel
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        # 上传导入
        files = {'file': ('test_import.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = client.post(
            "/api/v1/standard-costs/import",
            files=files,
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert result["success_count"] == 2
        assert result["error_count"] == 0

    def test_import_with_errors(self, client, admin_headers, db: Session):
        """测试导入包含错误的数据"""
        # 创建包含错误的测试数据
        data = {
            '成本项编码*': ['ERR-001', ''],  # 第二行编码为空
            '成本项名称*': ['正确数据', '错误数据'],
            '成本类别*': ['MATERIAL', 'INVALID'],  # 第二行类别错误
            '规格型号': ['', ''],
            '单位*': ['kg', 'kg'],
            '标准成本*': [10.0, 20.0],
            '币种': ['CNY', 'CNY'],
            '成本来源*': ['HISTORICAL_AVG', 'INVALID'],  # 第二行来源错误
            '来源说明': ['', ''],
            '生效日期*': ['2026-01-01', '2026-01-01'],
            '失效日期': ['', ''],
            '成本说明': ['', ''],
            '备注': ['', '']
        }
        df = pd.DataFrame(data)
        
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        files = {'file': ('test_errors.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = client.post(
            "/api/v1/standard-costs/import",
            files=files,
            headers=admin_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert result["error_count"] > 0
        assert len(result["errors"]) > 0


class TestProjectIntegration:
    """项目集成测试"""

    def test_apply_standard_cost_to_project(self, client, admin_headers, db: Session):
        """测试应用标准成本到项目预算"""
        # 先创建标准成本
        cost_data = {
            "cost_code": "PROJ-001",
            "cost_name": "项目测试成本",
            "cost_category": "MATERIAL",
            "unit": "kg",
            "standard_cost": 10.0,
            "cost_source": "HISTORICAL_AVG",
            "effective_date": "2026-01-01"
        }
        client.post("/api/v1/standard-costs/", json=cost_data, headers=admin_headers)
        
        # 创建项目（假设已有项目ID为1）
        # 应用标准成本到项目
        apply_data = {
            "project_id": 1,
            "cost_items": [
                {"cost_code": "PROJ-001", "quantity": 100}
            ],
            "budget_name": "基于标准成本的预算",
            "notes": "测试应用"
        }
        
        response = client.post(
            "/api/v1/standard-costs/projects/1/costs/apply-standard",
            json=apply_data,
            headers=admin_headers
        )
        
        # 注意：如果项目不存在，会返回404
        if response.status_code == status.HTTP_404_NOT_FOUND:
            pytest.skip("测试项目不存在")
        else:
            assert response.status_code == status.HTTP_200_OK
            result = response.json()
            assert result["applied_items_count"] == 1


class TestPermissions:
    """权限控制测试"""

    def test_create_without_permission(self, client, db: Session):
        """测试无权限创建"""
        # 使用普通用户（无权限）
        data = {
            "cost_code": "PERM-001",
            "cost_name": "权限测试",
            "cost_category": "MATERIAL",
            "unit": "件",
            "standard_cost": 5.0,
            "cost_source": "HISTORICAL_AVG",
            "effective_date": "2026-01-01"
        }
        
        # 不带认证头
        response = client.post("/api/v1/standard-costs/", json=data)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_read_without_permission(self, client, db: Session):
        """测试无权限读取"""
        # 不带认证头
        response = client.get("/api/v1/standard-costs/")
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
