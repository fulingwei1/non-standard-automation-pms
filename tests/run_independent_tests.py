#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立测试运行器 - 不依赖 conftest.py
用于测试不依赖复杂关系的模块
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入测试模块
from tests.unit.test_holiday_utils import (
    TestGetHolidayName,
    TestGetWorkType,
    TestHolidayDataStructure,
    TestIsHoliday,
    TestIsWorkdayAdjustment,
)
from tests.unit.test_code_config import (
    TestCodePrefix,
    TestGetMaterialCategoryCode,
    TestMaterialCategoryCodes,
    TestSeqLength,
    TestValidMaterialCategoryCodes,
    TestValidateMaterialCategoryCode,
)
from tests.unit.test_pinyin_utils import (
    TestBatchGeneratePinyinForEmployees,
    TestGenerateInitialPassword,
    TestNameToPinyin,
    TestNameToPinyinInitials,
)


def run_test_class(test_class):
    """运行测试类中的所有测试方法"""
    test_instance = test_class()
    passed = 0
    failed = 0
    errors = 0

    # 获取所有以 test_ 开头的方法
    test_methods = [
        method for method in dir(test_instance) if method.startswith("test_")
    ]

    for method_name in test_methods:
        try:
            method = getattr(test_instance, method_name)
            method()
            print(f"  ✓ {method_name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {method_name} - FAILED")
            print(f"    {str(e)}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {method_name} - ERROR")
            print(f"    {str(e)}")
            errors += 1

    return passed, failed, errors


def main():
    """主函数"""
    print("=" * 60)
    print("独立单元测试运行器")
    print("=" * 60)
    print()

    # 定义测试类列表
    test_classes = [
        ("Holiday Utils - IsHoliday", TestIsHoliday),
        ("Holiday Utils - GetHolidayName", TestGetHolidayName),
        ("Holiday Utils - IsWorkdayAdjustment", TestIsWorkdayAdjustment),
        ("Holiday Utils - GetWorkType", TestGetWorkType),
        ("Holiday Utils - DataStructure", TestHolidayDataStructure),
        ("Code Config - Prefix", TestCodePrefix),
        ("Code Config - SeqLength", TestSeqLength),
        ("Code Config - MaterialCategories", TestMaterialCategoryCodes),
        ("Code Config - ValidCategories", TestValidMaterialCategoryCodes),
        ("Code Config - GetCategoryCode", TestGetMaterialCategoryCode),
        ("Code Config - ValidateCategory", TestValidateMaterialCategoryCode),
        ("Pinyin Utils - NameToPinyin", TestNameToPinyin),
        ("Pinyin Utils - NameToPinyinInitials", TestNameToPinyinInitials),
        ("Pinyin Utils - GenerateInitialPassword", TestGenerateInitialPassword),
        ("Pinyin Utils - BatchGenerate", TestBatchGeneratePinyinForEmployees),
    ]

    total_passed = 0
    total_failed = 0
    total_errors = 0

    # 运行所有测试
    for test_name, test_class in test_classes:
        print(f"\n【{test_name}】")
        passed, failed, errors = run_test_class(test_class)
        total_passed += passed
        total_failed += failed
        total_errors += errors

    # 打印汇总
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    print(f"  Passed:  {total_passed}")
    print(f"  Failed:  {total_failed}")
    print(f"  Errors:  {total_errors}")
    print(f"  Total:   {total_passed + total_failed + total_errors}")
    print("=" * 60)

    # 返回退出代码
    return 0 if total_failed == 0 and total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
