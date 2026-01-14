# -*- coding: utf-8 -*-
"""
主数据编码生成单元测试

测试员工、客户、物料编码的自动生成功能
"""

import pytest
from sqlalchemy.orm import Session

from app.utils.number_generator import (
    generate_employee_code,
    generate_customer_code,
    generate_material_code,
)
from app.utils.code_config import (
    CODE_PREFIX,
    SEQ_LENGTH,
    get_material_category_code,
    validate_material_category_code,
)
from app.models.organization import Employee
from app.models.project import Customer
from app.models.material import Material, MaterialCategory


class TestCodeGenerator:
    """测试编码生成器"""

    def test_generate_employee_code_first(self, db_session: Session):
        """测试生成第一个员工编号"""
        code = generate_employee_code(db_session)
        assert code.startswith(f"{CODE_PREFIX['EMPLOYEE']}-")
        assert len(code) == len(f"{CODE_PREFIX['EMPLOYEE']}-") + SEQ_LENGTH['EMPLOYEE']
        assert code == f"{CODE_PREFIX['EMPLOYEE']}-00001"

    def test_generate_employee_code_sequential(self, db_session: Session):
        """测试连续生成员工编号"""
        # 创建几个员工
        for i in range(3):
            employee = Employee(
                employee_code=generate_employee_code(db_session),
                name=f"测试员工{i+1}",
            )
            db_session.add(employee)
        db_session.commit()

        # 生成下一个编号
        next_code = generate_employee_code(db_session)
        assert next_code == f"{CODE_PREFIX['EMPLOYEE']}-00004"

    def test_generate_customer_code_first(self, db_session: Session):
        """测试生成第一个客户编号"""
        code = generate_customer_code(db_session)
        assert code.startswith(f"{CODE_PREFIX['CUSTOMER']}-")
        assert len(code) == len(f"{CODE_PREFIX['CUSTOMER']}-") + SEQ_LENGTH['CUSTOMER']
        assert code == f"{CODE_PREFIX['CUSTOMER']}-0000001"

    def test_generate_customer_code_sequential(self, db_session: Session):
        """测试连续生成客户编号"""
        # 创建几个客户
        for i in range(3):
            customer = Customer(
                customer_code=generate_customer_code(db_session),
                customer_name=f"测试客户{i+1}",
            )
            db_session.add(customer)
        db_session.commit()

        # 生成下一个编号
        next_code = generate_customer_code(db_session)
        assert next_code == f"{CODE_PREFIX['CUSTOMER']}-0000004"

    def test_generate_material_code_me(self, db_session: Session):
        """测试生成机械件物料编号"""
        code = generate_material_code(db_session, "ME-01-01")
        assert code.startswith(f"{CODE_PREFIX['MATERIAL']}-ME-")
        assert code == f"{CODE_PREFIX['MATERIAL']}-ME-00001"

    def test_generate_material_code_el(self, db_session: Session):
        """测试生成电气件物料编号"""
        code = generate_material_code(db_session, "EL-02-03")
        assert code.startswith(f"{CODE_PREFIX['MATERIAL']}-EL-")
        assert code == f"{CODE_PREFIX['MATERIAL']}-EL-00001"

    def test_generate_material_code_by_category(self, db_session: Session):
        """测试按类别分别生成物料编号"""
        # 生成机械件
        me_code1 = generate_material_code(db_session, "ME-01-01")
        assert me_code1 == f"{CODE_PREFIX['MATERIAL']}-ME-00001"

        # 生成电气件
        el_code1 = generate_material_code(db_session, "EL-02-03")
        assert el_code1 == f"{CODE_PREFIX['MATERIAL']}-EL-00001"

        # 再次生成机械件，应该是00002
        me_code2 = generate_material_code(db_session, "ME-01-02")
        assert me_code2 == f"{CODE_PREFIX['MATERIAL']}-ME-00002"

        # 再次生成电气件，应该是00002
        el_code2 = generate_material_code(db_session, "EL-03-01")
        assert el_code2 == f"{CODE_PREFIX['MATERIAL']}-EL-00002"

    def test_generate_material_code_no_category(self, db_session: Session):
        """测试无类别时生成物料编号（应使用OT）"""
        code = generate_material_code(db_session, None)
        assert code.startswith(f"{CODE_PREFIX['MATERIAL']}-OT-")
        assert code == f"{CODE_PREFIX['MATERIAL']}-OT-00001"

    def test_generate_material_code_invalid_category(self, db_session: Session):
        """测试无效类别时生成物料编号（应使用OT）"""
        code = generate_material_code(db_session, "INVALID-01-01")
        assert code.startswith(f"{CODE_PREFIX['MATERIAL']}-OT-")

    def test_code_uniqueness(self, db_session: Session):
        """测试编码唯一性"""
        # 生成员工编号
        emp_codes = set()
        for _ in range(10):
            code = generate_employee_code(db_session)
            assert code not in emp_codes, f"员工编号重复: {code}"
            emp_codes.add(code)
            # 创建员工以占用编号
            employee = Employee(employee_code=code, name=f"员工{code}")
            db_session.add(employee)
        db_session.commit()

        # 生成客户编号
        cus_codes = set()
        for _ in range(10):
            code = generate_customer_code(db_session)
            assert code not in cus_codes, f"客户编号重复: {code}"
            cus_codes.add(code)
            # 创建客户以占用编号
            customer = Customer(customer_code=code, customer_name=f"客户{code}")
            db_session.add(customer)
        db_session.commit()


class TestCodeConfig:
    """测试编码配置"""

    def test_get_material_category_code_me(self):
        """测试提取机械件类别码"""
        assert get_material_category_code("ME-01-01") == "ME"
        assert get_material_category_code("ME-02-03") == "ME"

    def test_get_material_category_code_el(self):
        """测试提取电气件类别码"""
        assert get_material_category_code("EL-01-01") == "EL"
        assert get_material_category_code("EL-02-03") == "EL"

    def test_get_material_category_code_invalid(self):
        """测试无效类别码（应返回OT）"""
        assert get_material_category_code("INVALID-01-01") == "OT"
        assert get_material_category_code("") == "OT"
        assert get_material_category_code(None) == "OT"

    def test_validate_material_category_code(self):
        """测试验证物料类别码"""
        assert validate_material_category_code("ME") is True
        assert validate_material_category_code("EL") is True
        assert validate_material_category_code("PN") is True
        assert validate_material_category_code("ST") is True
        assert validate_material_category_code("OT") is True
        assert validate_material_category_code("INVALID") is False
        assert validate_material_category_code("") is False

    def test_code_prefix_constants(self):
        """测试编码前缀常量"""
        assert CODE_PREFIX['EMPLOYEE'] == 'EMP'
        assert CODE_PREFIX['CUSTOMER'] == 'CUS'
        assert CODE_PREFIX['MATERIAL'] == 'MAT'
        assert CODE_PREFIX['PROJECT'] == 'PJ'
        assert CODE_PREFIX['MACHINE'] == 'PN'

    def test_seq_length_constants(self):
        """测试序号长度常量"""
        assert SEQ_LENGTH['EMPLOYEE'] == 5
        assert SEQ_LENGTH['CUSTOMER'] == 7
        assert SEQ_LENGTH['MATERIAL'] == 5
        assert SEQ_LENGTH['PROJECT'] == 3
        assert SEQ_LENGTH['MACHINE'] == 3
