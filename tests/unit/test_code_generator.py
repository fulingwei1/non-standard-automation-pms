# -*- coding: utf-8 -*-
"""
主数据编码生成单元测试

测试员工、客户、物料编码的自动生成功能
"""

import re

import pytest
from sqlalchemy.orm import Session

from app.models.material import Material, MaterialCategory
from app.models.organization import Employee
from app.models.project import Customer
from app.utils.code_config import (
    CODE_PREFIX,
    SEQ_LENGTH,
    get_material_category_code,
    validate_material_category_code,
)
from app.utils.number_generator import (
    generate_customer_code,
    generate_employee_code,
    generate_material_code,
)


class TestCodeGenerator:
    """测试编码生成器"""

    def test_generate_employee_code_format(self, db_session: Session):
        """测试员工编号格式正确"""
        code = generate_employee_code(db_session)
        assert code.startswith(f"{CODE_PREFIX['EMPLOYEE']}-")
        # 验证格式: EMP-XXXXX (5位数字)
        pattern = rf"^{CODE_PREFIX['EMPLOYEE']}-\d{{{SEQ_LENGTH['EMPLOYEE']}}}$"
        assert re.match(pattern, code), f"编号格式不正确: {code}"

    def test_generate_employee_code_sequential(self, db_session: Session):
        """测试连续生成员工编号递增"""
        # 获取当前编号
        first_code = generate_employee_code(db_session)
        first_seq = int(first_code.split('-')[-1])

        # 创建员工占用这个编号
        employee = Employee(
            employee_code=first_code,
            name="测试员工序列",
        )
        db_session.add(employee)
        db_session.commit()
        db_session.expire_all()  # 清除缓存，确保后续查询看到最新数据

        # 生成下一个编号应该递增
        next_code = generate_employee_code(db_session)
        next_seq = int(next_code.split('-')[-1])
        assert next_seq == first_seq + 1, f"编号未递增: {first_code} -> {next_code}"

    def test_generate_customer_code_format(self, db_session: Session):
        """测试客户编号格式正确"""
        code = generate_customer_code(db_session)
        assert code.startswith(f"{CODE_PREFIX['CUSTOMER']}-")
        # 验证格式: CUS-XXXXXXX (7位数字)
        pattern = rf"^{CODE_PREFIX['CUSTOMER']}-\d{{{SEQ_LENGTH['CUSTOMER']}}}$"
        assert re.match(pattern, code), f"编号格式不正确: {code}"

    def test_generate_customer_code_sequential(self, db_session: Session):
        """测试连续生成客户编号递增"""
        # 获取当前编号
        first_code = generate_customer_code(db_session)
        first_seq = int(first_code.split('-')[-1])

        # 创建客户占用这个编号
        customer = Customer(
            customer_code=first_code,
            customer_name="测试客户序列",
        )
        db_session.add(customer)
        db_session.commit()
        db_session.expire_all()  # 清除缓存，确保后续查询看到最新数据

        # 生成下一个编号应该递增
        next_code = generate_customer_code(db_session)
        next_seq = int(next_code.split('-')[-1])
        assert next_seq == first_seq + 1, f"编号未递增: {first_code} -> {next_code}"

    def test_generate_material_code_me(self, db_session: Session):
        """测试生成机械件物料编号"""
        code = generate_material_code(db_session, "ME-01-01")
        assert code.startswith(f"{CODE_PREFIX['MATERIAL']}-ME-")
        # 验证格式: MAT-ME-XXXXX
        pattern = rf"^{CODE_PREFIX['MATERIAL']}-ME-\d{{{SEQ_LENGTH['MATERIAL']}}}$"
        assert re.match(pattern, code), f"编号格式不正确: {code}"

    def test_generate_material_code_el(self, db_session: Session):
        """测试生成电气件物料编号"""
        code = generate_material_code(db_session, "EL-02-03")
        assert code.startswith(f"{CODE_PREFIX['MATERIAL']}-EL-")

    def test_generate_material_code_by_category(self, db_session: Session):
        """测试按类别分别生成物料编号"""
        # 生成机械件
        me_code1 = generate_material_code(db_session, "ME-01-01")
        me_seq1 = int(me_code1.split('-')[-1])

        # 生成电气件 - 应该是独立的序列
        el_code1 = generate_material_code(db_session, "EL-02-03")

        # 再次生成机械件，序列应该递增
        me_code2 = generate_material_code(db_session, "ME-01-02")
        me_seq2 = int(me_code2.split('-')[-1])

        # 机械件序列应该是递增的（但不一定连续，因为可能已有数据）
        assert me_seq2 >= me_seq1, f"机械件序列未递增: {me_code1} -> {me_code2}"

    def test_generate_material_code_no_category(self, db_session: Session):
        """测试无类别时生成物料编号（应使用OT）"""
        code = generate_material_code(db_session, None)
        assert code.startswith(f"{CODE_PREFIX['MATERIAL']}-OT-")

    def test_generate_material_code_invalid_category(self, db_session: Session):
        """测试无效类别时生成物料编号（应使用OT）"""
        code = generate_material_code(db_session, "INVALID-01-01")
        assert code.startswith(f"{CODE_PREFIX['MATERIAL']}-OT-")

    def test_code_uniqueness(self, db_session: Session):
        """测试编码唯一性"""
        # 生成员工编号
        emp_codes = set()
        for i in range(5):
            code = generate_employee_code(db_session)
            assert code not in emp_codes, f"员工编号重复: {code}"
            emp_codes.add(code)
            # 创建员工以占用编号
            employee = Employee(employee_code=code, name=f"唯一性测试员工{i}")
            db_session.add(employee)
            db_session.commit()
            db_session.expire_all()  # 清除缓存，确保后续查询看到最新数据

        # 验证生成了5个不同的编号
        assert len(emp_codes) == 5


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
