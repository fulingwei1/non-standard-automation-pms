#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户批量导入功能集成测试脚本
"""

import sys
import requests
import pandas as pd
from pathlib import Path
from io import BytesIO

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# API 配置
API_BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def login():
    """登录获取 token"""
    print_info("正在登录...")
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD,
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_success(f"登录成功，token: {token[:20]}...")
        return token
    else:
        print_error(f"登录失败: {response.text}")
        sys.exit(1)

def test_download_template(token):
    """测试下载模板"""
    print_info("\n【测试1】下载 Excel 模板")
    
    response = requests.get(
        f"{API_BASE_URL}/api/v1/users/import/template?format=xlsx",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        print_success(f"下载成功，文件大小: {len(response.content)} 字节")
        
        # 保存文件
        output_path = ROOT_DIR / "data" / "downloaded_template.xlsx"
        output_path.write_bytes(response.content)
        print_success(f"已保存到: {output_path}")
        
        # 验证文件内容
        df = pd.read_excel(BytesIO(response.content))
        print_success(f"模板包含 {len(df)} 行示例数据，{len(df.columns)} 个字段")
        return True
    else:
        print_error(f"下载失败: {response.text}")
        return False

def test_preview_valid_data(token):
    """测试预览有效数据"""
    print_info("\n【测试2】预览有效数据")
    
    # 创建测试数据
    df = pd.DataFrame({
        "用户名": ["test_preview_1", "test_preview_2"],
        "真实姓名": ["预览测试1", "预览测试2"],
        "邮箱": ["preview1@test.com", "preview2@test.com"],
        "部门": ["技术部", "产品部"],
        "角色": ["普通用户", "普通用户"],
    })
    
    # 转换为 Excel
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users/import/preview",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    if response.status_code == 200:
        data = response.json()["data"]
        print_success(f"预览成功: 总数 {data['total']}，有效: {data['is_valid']}")
        print_info(f"预览数据: {len(data['preview'])} 条")
        
        if data['errors']:
            print_warning(f"发现错误: {len(data['errors'])} 条")
            for err in data['errors'][:3]:
                print_warning(f"  - {err}")
        
        return data['is_valid']
    else:
        print_error(f"预览失败: {response.text}")
        return False

def test_preview_invalid_data(token):
    """测试预览无效数据"""
    print_info("\n【测试3】预览无效数据（缺少必填字段）")
    
    # 创建缺少必填字段的数据
    df = pd.DataFrame({
        "用户名": ["test_invalid"],
        # 缺少 real_name 和 email
    })
    
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users/import/preview",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    if response.status_code == 200:
        data = response.json()["data"]
        if not data['is_valid'] and len(data['errors']) > 0:
            print_success("正确检测到数据无效")
            print_info(f"错误信息: {data['errors'][0]}")
            return True
        else:
            print_error("应该检测到数据无效，但未检测到")
            return False
    else:
        print_error(f"预览失败: {response.text}")
        return False

def test_import_users(token):
    """测试批量导入用户"""
    print_info("\n【测试4】批量导入用户")
    
    # 创建测试数据（使用唯一的用户名和邮箱）
    import time
    timestamp = int(time.time())
    
    df = pd.DataFrame({
        "用户名": [f"test_import_{timestamp}_1", f"test_import_{timestamp}_2"],
        "密码": ["Test@123", "Test@456"],
        "真实姓名": ["导入测试1", "导入测试2"],
        "邮箱": [f"import{timestamp}_1@test.com", f"import{timestamp}_2@test.com"],
        "手机号": ["13800000001", "13800000002"],
        "工号": [f"IMP{timestamp}1", f"IMP{timestamp}2"],
        "部门": ["技术部", "产品部"],
        "职位": ["工程师", "产品经理"],
        "角色": ["普通用户", "普通用户"],
        "是否启用": ["是", "是"],
    })
    
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users/import",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    if response.status_code == 200:
        data = response.json()["data"]
        print_success(f"导入完成: 成功 {data['success_count']}，失败 {data['failed_count']}")
        
        if data['success_users']:
            print_info("成功导入的用户:")
            for user in data['success_users']:
                print_info(f"  - {user['username']} ({user['real_name']}) - {user['email']}")
        
        if data['errors']:
            print_warning(f"导入错误: {len(data['errors'])} 条")
            for err in data['errors'][:3]:
                print_warning(f"  - {err}")
        
        return data['success_count'] > 0
    else:
        print_error(f"导入失败: {response.text}")
        return False

def test_import_duplicate(token):
    """测试重复数据导入（应该失败）"""
    print_info("\n【测试5】导入重复数据（应该失败）")
    
    # 创建包含重复用户名的数据
    df = pd.DataFrame({
        "用户名": ["duplicate_test", "duplicate_test"],  # 重复
        "真实姓名": ["重复测试1", "重复测试2"],
        "邮箱": ["dup1@test.com", "dup2@test.com"],
    })
    
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/users/import",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    )
    
    if response.status_code == 200:
        data = response.json()["data"]
        if data['failed_count'] > 0 and any("重复" in str(err) for err in data['errors']):
            print_success("正确检测到重复数据并拒绝导入")
            return True
        else:
            print_error("应该检测到重复数据，但未检测到")
            return False
    else:
        print_error(f"请求失败: {response.text}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("用户批量导入功能集成测试")
    print("=" * 60)
    
    # 登录
    token = login()
    
    # 执行测试
    results = []
    
    results.append(("下载模板", test_download_template(token)))
    results.append(("预览有效数据", test_preview_valid_data(token)))
    results.append(("预览无效数据", test_preview_invalid_data(token)))
    results.append(("批量导入用户", test_import_users(token)))
    results.append(("导入重复数据", test_import_duplicate(token)))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        if result:
            print_success(f"{name}: 通过")
            passed += 1
        else:
            print_error(f"{name}: 失败")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"总计: {len(results)} 项测试")
    print_success(f"通过: {passed}")
    if failed > 0:
        print_error(f"失败: {failed}")
    print("=" * 60)
    
    # 返回退出码
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
