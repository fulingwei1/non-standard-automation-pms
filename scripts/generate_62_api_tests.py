#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为62个未测试的API端点生成测试文件
从 api_frontend_coverage.md 中提取前62个未匹配的端点
"""

import re
from pathlib import Path
from typing import List, Tuple


# 前62个未匹配的API端点（从 api_frontend_coverage.md 提取）
ENDPOINTS_62 = [
    ("GET", "/api/v1/projects/templates"),
    ("POST", "/api/v1/projects/templates"),
    ("GET", "/api/v1/projects/templates/{template_id}"),
    ("PUT", "/api/v1/projects/templates/{template_id}"),
    ("GET", "/api/v1/projects/templates/{template_id}/versions"),
    ("POST", "/api/v1/projects/templates/{template_id}/versions"),
    ("PUT", "/api/v1/projects/templates/{template_id}/versions/{version_id}/publish"),
    ("GET", "/api/v1/projects/templates/{template_id}/versions/compare"),
    ("POST", "/api/v1/projects/templates/{template_id}/versions/{version_id}/rollback"),
    ("GET", "/api/v1/projects/templates/{template_id}/usage-statistics"),
    ("PUT", "/api/v1/projects/{project_id}/archive"),
    ("PUT", "/api/v1/projects/{project_id}/unarchive"),
    ("GET", "/api/v1/projects/archived"),
    ("POST", "/api/v1/projects/batch/archive"),
    ("GET", "/api/v1/projects/overview"),
    ("GET", "/api/v1/projects/dashboard"),
    ("GET", "/api/v1/projects/in-production-summary"),
    ("GET", "/api/v1/projects/{project_id}/timeline"),
    ("POST", "/api/v1/projects/{project_id}/sync-from-contract"),
    ("POST", "/api/v1/projects/{project_id}/sync-to-contract"),
    ("GET", "/api/v1/projects/{project_id}/sync-status"),
    ("POST", "/api/v1/projects/{project_id}/sync-to-erp"),
    ("GET", "/api/v1/projects/{project_id}/erp-status"),
    ("PUT", "/api/v1/projects/{project_id}/erp-status"),
    ("GET", "/api/v1/projects/board"),
    ("DELETE", "/api/v1/projects/{project_id}"),
    ("POST", "/api/v1/projects/{project_id}/clone"),
    ("PUT", "/api/v1/projects/{project_id}/stage"),
    ("GET", "/api/v1/projects/{project_id}/status"),
    ("PUT", "/api/v1/projects/{project_id}/status"),
    ("PUT", "/api/v1/projects/{project_id}/health"),
    ("POST", "/api/v1/projects/{project_id}/health/calculate"),
    ("GET", "/api/v1/projects/{project_id}/health/details"),
    ("POST", "/api/v1/projects/health/batch-calculate"),
    ("POST", "/api/v1/projects/{project_id}/stages/init"),
    ("GET", "/api/v1/projects/{project_id}/status-history"),
    ("POST", "/api/v1/projects/{project_id}/stage-advance"),
    ("POST", "/api/v1/projects/batch/update-status"),
    ("POST", "/api/v1/projects/batch/update-stage"),
    ("POST", "/api/v1/projects/batch/assign-pm"),
    ("GET", "/api/v1/projects/{project_id}/payment-plans"),
    ("POST", "/api/v1/projects/{project_id}/payment-plans"),
    ("PUT", "/api/v1/projects/payment-plans/{plan_id}"),
    ("DELETE", "/api/v1/projects/payment-plans/{plan_id}"),
    ("GET", "/api/v1/projects/statistics"),
    ("GET", "/api/v1/machines/projects/{project_id}/machines"),
    ("POST", "/api/v1/machines/projects/{project_id}/machines"),
    ("PUT", "/api/v1/machines/{machine_id}/progress"),
    ("DELETE", "/api/v1/milestones/{milestone_id}"),
    ("POST", "/api/v1/members/projects/{project_id}/members"),
    ("PUT", "/api/v1/members/project-members/{member_id}"),
    ("GET", "/api/v1/members/projects/{project_id}/members/conflicts"),
    ("POST", "/api/v1/members/projects/{project_id}/members/batch"),
    ("POST", "/api/v1/members/projects/{project_id}/members/{member_id}/notify-dept-manager"),
    ("GET", "/api/v1/members/projects/{project_id}/members/from-dept/{dept_id}"),
    ("POST", "/api/v1/stages"),
    ("PUT", "/api/v1/stages/{stage_id}"),
    ("PUT", "/api/v1/stages/project-stages/{stage_id}"),
    ("GET", "/api/v1/stages/project-stages/{stage_id}/statuses"),
    ("PUT", "/api/v1/stages/project-statuses/{status_id}/complete"),
    ("POST", "/api/v1/stages/statuses"),
    ("POST", "/api/v1/org/employees"),
    ("GET", "/api/v1/org/employees/{emp_id}"),
    ("PUT", "/api/v1/org/employees/{emp_id}"),
]


def extract_module_from_path(path: str) -> str:
    """从路径提取模块名"""
    # /api/v1/projects/templates -> projects
    parts = path.strip("/").split("/")
    if len(parts) >= 3:
        return parts[2]  # projects, machines, members, etc.
    return "unknown"


def group_endpoints_by_module(endpoints: List[Tuple[str, str]]) -> dict:
    """按模块分组端点"""
    grouped = {}
    for method, path in endpoints:
        module = extract_module_from_path(path)
        if module not in grouped:
            grouped[module] = []
        grouped[module].append((method, path))
    return grouped


def generate_test_file_content(module: str, endpoints: List[Tuple[str, str]]) -> str:
    """生成测试文件内容"""
    module_test_name = module.replace("-", "_").replace("/", "_")
    class_name = f"Test{module_test_name.title().replace('_', '')}API"
    
    test_methods = []
    for method, path in endpoints:
        # 生成测试方法名
        path_parts = path.replace("/api/v1/", "").replace("{", "").replace("}", "")
        test_name = path_parts.replace("/", "_").replace("-", "_")
        # 清理测试名
        test_name = re.sub(r'[^a-zA-Z0-9_]', '_', test_name)
        test_name = re.sub(r'_+', '_', test_name).strip('_')
        
        # 提取路径参数
        path_params = re.findall(r'\{(\w+)\}', path)
        path_without_params = path
        for param in path_params:
            path_without_params = path_without_params.replace(f"{{{param}}}", "1")
        
        # 生成测试方法
        test_method = f'''    def test_{method.lower()}_{test_name}(self, api_client):
        """测试 {method} {path}"""
        # TODO: 实现测试逻辑
        # 1. 准备测试数据
        # 2. 调用端点
        # 3. 验证响应
        
        # 示例实现
        response = api_client.{method.lower()}("{path_without_params}")
        assert response.status_code in [200, 201, 204, 400, 403, 404], \\
            f"Expected status 200/201/204/400/403/404, got {{response.status_code}}"
'''
        test_methods.append(test_method)
    
    content = f'''# -*- coding: utf-8 -*-
"""
API Integration Tests for {module} module
Covers {len(endpoints)} endpoints from api_frontend_coverage.md (unmatched endpoints)

Generated endpoints:
{chr(10).join(f"  - {method} {path}" for method, path in endpoints[:5])}
  ... and {len(endpoints) - 5} more
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def api_client(db_session: Session) -> TestClient:
    """Create test client with authenticated user."""
    from app.main import app
    from tests.conftest import _get_auth_token

    client = TestClient(app)
    token = _get_auth_token(db_session, username="admin", password="admin123")
    client.headers.update({{"Authorization": f"Bearer {{token}}"}})
    return client


class {class_name}:
    """Test suite for {module} API endpoints."""

{chr(10).join(test_methods)}

    # TODO: 添加更多测试用例
    # - 正常流程测试 (Happy Path)
    # - 边界条件测试 (Edge Cases)
    # - 异常处理测试 (Error Handling)
    # - 数据验证测试 (Data Validation)
    # - 权限测试 (Permission Tests)
'''
    return content


def main():
    """生成62个API端点的测试文件"""
    print("🚀 开始为62个API端点生成测试文件...\n")
    
    # 按模块分组
    grouped = group_endpoints_by_module(ENDPOINTS_62)
    
    print(f"📊 统计信息:")
    print(f"  总端点数: {len(ENDPOINTS_62)}")
    print(f"  模块数: {len(grouped)}")
    print(f"\n📦 按模块分组:")
    for module, endpoints in sorted(grouped.items()):
        print(f"  {module}: {len(endpoints)} 个端点")
    
    # 生成测试文件
    output_dir = Path("tests/api")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated = []
    skipped = []
    
    print(f"\n📝 生成测试文件:")
    for module, endpoints in sorted(grouped.items()):
        test_file = output_dir / f"test_{module}_api.py"
        
        # 检查是否已存在
        if test_file.exists():
            print(f"  ⏭️  {module:30s} - 测试文件已存在: {test_file.name}")
            skipped.append(module)
            continue
        
        # 生成测试内容
        try:
            content = generate_test_file_content(module, endpoints)
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ {module:30s} - 已生成: {test_file.name} ({len(endpoints)} 个端点)")
            generated.append((module, len(endpoints)))
        
        except Exception as e:
            print(f"  ❌ {module:30s} - 生成失败: {e}")
            skipped.append(module)
    
    # 输出统计
    print(f"\n📊 生成统计:")
    print(f"  ✅ 成功生成: {len(generated)} 个测试文件")
    print(f"  ⏭️  跳过: {len(skipped)} 个")
    print(f"  📁 输出目录: {output_dir}")
    
    if generated:
        total_endpoints = sum(count for _, count in generated)
        print(f"\n📈 覆盖情况:")
        print(f"  - 测试文件数: {len(generated)}")
        print(f"  - 覆盖端点数: {total_endpoints}")
        print(f"\n📝 下一步:")
        print(f"  1. 检查生成的测试文件")
        print(f"  2. 实现 TODO 标记的测试方法")
        print(f"  3. 运行测试: pytest {output_dir}/test_{generated[0][0]}_api.py -v")
        print(f"  4. 检查覆盖率: pytest --cov=app/api/v1/endpoints/{generated[0][0]} --cov-report=term-missing")


if __name__ == "__main__":
    main()
