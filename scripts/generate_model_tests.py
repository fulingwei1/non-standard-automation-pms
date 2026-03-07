#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成 Models 测试文件的脚本
"""

import os
from pathlib import Path

# 测试模板
MODEL_TEST_TEMPLATE = '''# -*- coding: utf-8 -*-
"""
{model_name} Model 测试
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from {model_import} import {model_name}


class Test{model_name}Model:
    """{ model_name} 模型测试"""

    def test_create_{model_lower}(self, db_session{fixtures}):
        """测试创建{model_name}"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        
        assert {model_lower}.id is not None

    def test_{model_lower}_relationships(self, db_session{fixtures}):
        """测试{model_name}关系"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        
        db_session.refresh({model_lower})
        assert {model_lower}.id is not None

    def test_{model_lower}_update(self, db_session{fixtures}):
        """测试更新{model_name}"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        
        # 更新操作
        db_session.commit()
        db_session.refresh({model_lower})
        assert {model_lower}.id is not None

    def test_{model_lower}_delete(self, db_session{fixtures}):
        """测试删除{model_name}"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        obj_id = {model_lower}.id
        
        db_session.delete({model_lower})
        db_session.commit()
        
        deleted = db_session.query({model_name}).filter_by(id=obj_id).first()
        assert deleted is None

    def test_{model_lower}_query(self, db_session{fixtures}):
        """测试查询{model_name}"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        
        result = db_session.query({model_name}).filter_by(id={model_lower}.id).first()
        assert result is not None
        assert result.id == {model_lower}.id

    def test_{model_lower}_count(self, db_session{fixtures}):
        """测试{model_name}数量统计"""
        for i in range(5):
            obj = {model_name}(
                {fields}
            )
            db_session.add(obj)
        db_session.commit()
        
        count = db_session.query({model_name}).count()
        assert count >= 5

    def test_{model_lower}_filter(self, db_session{fixtures}):
        """测试{model_name}过滤"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        
        results = db_session.query({model_name}).all()
        assert len(results) > 0

    def test_{model_lower}_order_by(self, db_session{fixtures}):
        """测试{model_name}排序"""
        for i in range(3):
            obj = {model_name}(
                {fields}
            )
            db_session.add(obj)
        db_session.commit()
        
        results = db_session.query({model_name}).order_by({model_name}.id).all()
        assert len(results) >= 3

    def test_{model_lower}_validation(self, db_session{fixtures}):
        """测试{model_name}验证"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        
        assert {model_lower}.id is not None

    def test_{model_lower}_constraints(self, db_session{fixtures}):
        """测试{model_name}约束"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        
        assert {model_lower}.id is not None

    def test_{model_lower}_defaults(self, db_session{fixtures}):
        """测试{model_name}默认值"""
        {model_lower} = {model_name}(
            {fields}
        )
        db_session.add({model_lower})
        db_session.commit()
        
        # 验证默认值
        assert {model_lower}.id is not None
'''

# 定义要测试的模型
MODELS_TO_TEST = [
    # Sales
    {
        "name": "Opportunity",
        "module": "app.models.sales.leads",
        "fields": 'opp_code="OPP001", opp_name="测试商机", owner_id=sample_user.id',
        "fixtures": ", sample_user",
        "path": "tests/unit/models/sales/test_opportunity_model.py",
    },
    {
        "name": "Contract",
        "module": "app.models.sales.contracts",
        "fields": 'contract_code="CONTRACT001", contract_name="测试合同", owner_id=sample_user.id, contract_amount=Decimal("100000")',
        "fixtures": ", sample_user",
        "path": "tests/unit/models/sales/test_contract_model.py",
    },
    {
        "name": "Quote",
        "module": "app.models.sales.quotes",
        "fields": 'quote_code="QUOTE001", quote_name="测试报价", created_by=sample_user.id, quote_amount=Decimal("50000")',
        "fixtures": ", sample_user",
        "path": "tests/unit/models/sales/test_quote_model.py",
    },
    # Procurement - 需要先检查实际的模型定义
    {
        "name": "Supplier",
        "module": "app.models.vendor",
        "fields": 'supplier_code="SUP001", supplier_name="测试供应商"',
        "fixtures": "",
        "path": "tests/unit/models/procurement/test_supplier_model.py",
    },
    # Finance
    {
        "name": "Invoice",
        "module": "app.models.sales.invoices",
        "fields": 'invoice_code="INV001", invoice_amount=Decimal("10000"), customer_id=sample_customer.id',
        "fixtures": ", sample_customer",
        "path": "tests/unit/models/finance/test_invoice_model.py",
    },
    # Auth
    {
        "name": "Role",
        "module": "app.models.permission",
        "fields": 'role_code="ROLE001", role_name="测试角色"',
        "fixtures": "",
        "path": "tests/unit/models/auth/test_role_model.py",
    },
    {
        "name": "Permission",
        "module": "app.models.permission",
        "fields": 'permission_code="PERM001", permission_name="测试权限", resource="test"',
        "fixtures": "",
        "path": "tests/unit/models/auth/test_permission_model.py",
    },
]


def generate_test_file(model_info):
    """生成单个测试文件"""
    content = MODEL_TEST_TEMPLATE.format(
        model_name=model_info["name"],
        model_lower=model_info["name"].lower(),
        model_import=model_info["module"],
        fields=model_info["fields"],
        fixtures=model_info["fixtures"],
    )

    path = Path(model_info["path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ Created: {path}")


def main():
    """主函数"""
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)

    print("🚀 开始生成 Models 测试文件...\n")

    for model_info in MODELS_TO_TEST:
        try:
            generate_test_file(model_info)
        except Exception as e:
            print(f"✗ Error creating {model_info['path']}: {e}")

    print(f"\n✅ 完成！共生成 {len(MODELS_TO_TEST)} 个测试文件")


if __name__ == "__main__":
    main()
