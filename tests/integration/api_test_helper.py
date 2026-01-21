# -*- coding: utf-8 -*-
"""
API集成测试基础工具类

提供统一的API测试辅助工具，包括：
- 认证令牌管理
- HTTP请求封装
- 响应断言
- 测试数据清理
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi.testclient import TestClient


class Colors:
    """控制台颜色输出"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    NC = "\033[0m"


class APITestHelper:
    """API测试辅助工具类"""

    def __init__(self, client: TestClient, base_url: str = "/api/v1"):
        """
        初始化API测试辅助工具

        Args:
            client: FastAPI TestClient实例
            base_url: API基础路径
        """
        self.client = client
        self.base_url = base_url
        self.tokens: Dict[str, str] = {}
        self.created_resources: Dict[str, list] = {}

    # -----------------------------------------------------------------------
    # 认证管理
    # -----------------------------------------------------------------------

    def login(self, username: str, password: str) -> Optional[str]:
        """
        登录并获取JWT令牌

        Args:
            username: 用户名
            password: 密码

        Returns:
            JWT令牌，失败返回None
        """
        response = self.client.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password},
        )

        if response.status_code == 200:
            token = response.json().get("access_token")
            self.tokens[username] = token
            return token
        return None

    def get_token(self, username: str, password: str) -> str:
        """
        获取认证令牌（自动登录）

        Args:
            username: 用户名
            password: 密码

        Returns:
            JWT令牌
        """
        if username not in self.tokens:
            token = self.login(username, password)
            if not token:
                raise ValueError(f"登录失败: {username}")
        return self.tokens[username]

    def get_headers(self, username: str, password: str) -> Dict[str, str]:
        """
        获取带认证的请求头

        Args:
            username: 用户名
            password: 密码

        Returns:
            包含Authorization头的字典
        """
        token = self.get_token(username, password)
        return {"Authorization": f"Bearer {token}"}

    # -----------------------------------------------------------------------
    # HTTP请求封装
    # -----------------------------------------------------------------------

    def get(
        self,
        endpoint: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行GET请求

        Args:
            endpoint: API端点（相对路径）
            username: 用户名（用于认证）
            password: 密码
            params: 查询参数
            headers: 额外的请求头

        Returns:
            响应数据字典，包含status_code, data, message等
        """
        request_headers = {}
        if username and password:
            request_headers.update(self.get_headers(username, password))
        if headers:
            request_headers.update(headers)

        url = f"{self.base_url}{endpoint}"
        response = self.client.get(url, params=params, headers=request_headers)

        return {
            "status_code": response.status_code,
            "data": response.json() if response.status_code != 204 else None,
            "text": response.text,
            "headers": response.headers,
        }

    def post(
        self,
        endpoint: str,
        data: Dict,
        username: Optional[str] = None,
        password: Optional[str] = None,
        headers: Optional[Dict] = None,
        json_data: bool = True,
    ) -> Dict[str, Any]:
        """
        执行POST请求

        Args:
            endpoint: API端点
            data: 请求数据
            username: 用户名（用于认证）
            password: 密码
            headers: 额外的请求头
            json_data: 是否使用JSON格式

        Returns:
            响应数据字典
        """
        request_headers = {}
        if username and password:
            request_headers.update(self.get_headers(username, password))
        if headers:
            request_headers.update(headers)

        url = f"{self.base_url}{endpoint}"
        if json_data:
            response = self.client.post(url, json=data, headers=request_headers)
        else:
            response = self.client.post(url, data=data, headers=request_headers)

        return {
            "status_code": response.status_code,
            "data": response.json() if response.status_code != 204 else None,
            "text": response.text,
            "headers": response.headers,
        }

    def put(
        self,
        endpoint: str,
        data: Dict,
        username: Optional[str] = None,
        password: Optional[str] = None,
        headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行PUT请求

        Args:
            endpoint: API端点
            data: 请求数据
            username: 用户名
            password: 密码
            headers: 额外的请求头

        Returns:
            响应数据字典
        """
        request_headers = {}
        if username and password:
            request_headers.update(self.get_headers(username, password))
        if headers:
            request_headers.update(headers)

        url = f"{self.base_url}{endpoint}"
        response = self.client.put(url, json=data, headers=request_headers)

        return {
            "status_code": response.status_code,
            "data": response.json() if response.status_code != 204 else None,
            "text": response.text,
            "headers": response.headers,
        }

    def patch(
        self,
        endpoint: str,
        data: Dict,
        username: Optional[str] = None,
        password: Optional[str] = None,
        headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行PATCH请求

        Args:
            endpoint: API端点
            data: 请求数据
            username: 用户名
            password: 密码
            headers: 额外的请求头

        Returns:
            响应数据字典
        """
        request_headers = {}
        if username and password:
            request_headers.update(self.get_headers(username, password))
        if headers:
            request_headers.update(headers)

        url = f"{self.base_url}{endpoint}"
        response = self.client.patch(url, json=data, headers=request_headers)

        return {
            "status_code": response.status_code,
            "data": response.json() if response.status_code != 204 else None,
            "text": response.text,
            "headers": response.headers,
        }

    def delete(
        self,
        endpoint: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        执行DELETE请求

        Args:
            endpoint: API端点
            username: 用户名
            password: 密码
            headers: 额外的请求头

        Returns:
            响应数据字典
        """
        request_headers = {}
        if username and password:
            request_headers.update(self.get_headers(username, password))
        if headers:
            request_headers.update(headers)

        url = f"{self.base_url}{endpoint}"
        response = self.client.delete(url, headers=request_headers)

        return {
            "status_code": response.status_code,
            "data": response.json() if response.status_code != 204 else None,
            "text": response.text,
            "headers": response.headers,
        }

    # -----------------------------------------------------------------------
    # 响应断言
    # -----------------------------------------------------------------------

    @staticmethod
    def assert_success(response: Dict[str, Any], message: str = "") -> None:
        """
        断言响应成功

        Args:
            response: API响应字典
            message: 自定义断言消息

        Raises:
            AssertionError: 如果响应失败
        """
        status = response.get("status_code")
        if not (200 <= status < 300):
            raise AssertionError(
                f"{message} - 期望2xx状态码，实际: {status}\n"
                f"响应: {response.get('text', '无响应数据')}"
            )

    @staticmethod
    def assert_status(
        response: Dict[str, Any], expected_status: int, message: str = ""
    ) -> None:
        """
        断言特定状态码

        Args:
            response: API响应字典
            expected_status: 期望的状态码
            message: 自定义断言消息

        Raises:
            AssertionError: 如果状态码不匹配
        """
        actual_status = response.get("status_code")
        if actual_status != expected_status:
            raise AssertionError(
                f"{message} - 期望状态码 {expected_status}，实际: {actual_status}\n"
                f"响应: {response.get('text', '无响应数据')}"
            )

    @staticmethod
    def assert_data_not_empty(response: Dict[str, Any], message: str = "") -> None:
        """
        断言响应数据不为空

        Args:
            response: API响应字典
            message: 自定义断言消息

        Raises:
            AssertionError: 如果响应数据为空
        """
        data = response.get("data")
        if not data:
            raise AssertionError(
                f"{message} - 响应数据为空\n响应: {response.get('text', '无响应数据')}"
            )

    @staticmethod
    def assert_field_equals(
        response: Dict[str, Any], field: str, expected_value: Any, message: str = ""
    ) -> None:
        """
        断言响应字段等于期望值

        Args:
            response: API响应字典
            field: 字段名（支持嵌套，如 "data.items.0.id"）
            expected_value: 期望值
            message: 自定义断言消息

        Raises:
            AssertionError: 如果字段值不匹配
        """
        value = response.get("data")

        # 处理嵌套字段
        for key in field.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                value = value[int(key)]
            else:
                raise AssertionError(f"{message} - 字段路径 '{field}' 无效")

        if value != expected_value:
            raise AssertionError(
                f"{message} - 字段 '{field}' 期望值 {expected_value}，实际: {value}"
            )

    # -----------------------------------------------------------------------
    # 测试数据管理
    # -----------------------------------------------------------------------

    def track_resource(self, resource_type: str, resource_id: Any) -> None:
        """
        记录创建的资源ID，用于测试后清理

        Args:
            resource_type: 资源类型（如 "project", "material"）
            resource_id: 资源ID
        """
        if resource_type not in self.created_resources:
            self.created_resources[resource_type] = []
        self.created_resources[resource_type].append(resource_id)

    def get_created_resource_ids(self, resource_type: str) -> list:
        """
        获取创建的资源ID列表

        Args:
            resource_type: 资源类型

        Returns:
            资源ID列表
        """
        return self.created_resources.get(resource_type, [])

    def cleanup_resources(self, cleanup_func: callable) -> None:
        """
        清理创建的测试资源

        Args:
            cleanup_func: 清理函数，签名 (resource_type, resource_id) -> None
        """
        for resource_type, ids in self.created_resources.items():
            for resource_id in ids:
                try:
                    cleanup_func(resource_type, resource_id)
                except Exception as e:
                    print(f"清理资源失败: {resource_type} {resource_id}, 错误: {e}")

        self.created_resources.clear()

    # -----------------------------------------------------------------------
    # 输出辅助
    # -----------------------------------------------------------------------

    @staticmethod
    def print_success(msg: str) -> None:
        """打印成功消息"""
        print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

    @staticmethod
    def print_error(msg: str) -> None:
        """打印错误消息"""
        print(f"{Colors.RED}❌ {msg}{Colors.NC}")

    @staticmethod
    def print_info(msg: str) -> None:
        """打印信息消息"""
        print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")

    @staticmethod
    def print_warning(msg: str) -> None:
        """打印警告消息"""
        print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")

    @staticmethod
    def print_separator(char: str = "=", length: int = 60) -> None:
        """打印分隔线"""
        print(char * length)

    def print_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> None:
        """打印请求信息"""
        print()
        self.print_separator()
        self.print_info(f"请求: {method} {self.base_url}{endpoint}")
        if data:
            print("请求数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))

    def print_response(self, response: Dict[str, Any], show_data: bool = True) -> None:
        """打印响应信息"""
        status = response.get("status_code")
        if 200 <= status < 300:
            self.print_success(f"状态码: {status}")
        else:
            self.print_error(f"状态码: {status}")

        if show_data and response.get("data"):
            print("响应数据:")
            if isinstance(response["data"], dict) and len(response["data"]) < 10:
                print(json.dumps(response["data"], ensure_ascii=False, indent=2))
            else:
                print(f"{response['data']}")
        elif response.get("text"):
            print(f"响应文本: {response['text'][:200]}")


class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def generate_project_code() -> str:
        """生成项目编码"""
        return f"PJ{datetime.now().strftime('%y%m%d%H%M%S')}"

    @staticmethod
    def generate_material_code() -> str:
        """生成物料编码"""
        return f"MAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    def generate_order_no() -> str:
        """生成订单号"""
        return f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    def future_date(days: int = 7) -> str:
        """生成未来日期"""
        return (datetime.now() + timedelta(days=days)).date().isoformat()

    @staticmethod
    def past_date(days: int = 7) -> str:
        """生成过去日期"""
        return (datetime.now() - timedelta(days=days)).date().isoformat()

    @staticmethod
    def generate_email() -> str:
        """生成测试邮箱"""
        return f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
