#!/usr/bin/env python3
"""
核心业务API功能测试脚本
测试555+ APIs中的核心业务模块
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

# 测试结果统计
test_results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": [],
    "warnings": [],
    "modules": {}
}


class APITester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_data = {}
        
    def log(self, level: str, module: str, message: str):
        """记录测试日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [{module}] {message}")
        
    def test_login(self) -> bool:
        """测试登录并获取token"""
        self.log("INFO", "AUTH", "开始测试登录...")
        
        try:
            response = requests.post(
                f"{API_V1}/auth/login",
                data={
                    "username": "admin",
                    "password": "admin123"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log("PASS", "AUTH", "登录成功")
                return True
            else:
                self.log("FAIL", "AUTH", f"登录失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log("ERROR", "AUTH", f"登录异常: {str(e)}")
            return False
    
    def test_api(self, method: str, endpoint: str, module: str, 
                 test_name: str, data: Optional[Dict] = None,
                 expected_status: int = 200) -> Tuple[bool, Optional[Dict]]:
        """通用API测试方法"""
        test_results["total"] += 1
        
        try:
            url = f"{API_V1}{endpoint}"
            self.log("INFO", module, f"测试: {test_name} - {method} {endpoint}")
            
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, json=data, headers=self.headers)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=self.headers)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 检查状态码
            if response.status_code == expected_status:
                test_results["passed"] += 1
                self.log("PASS", module, f"{test_name} - 状态码: {response.status_code}")
                
                # 尝试解析JSON
                try:
                    result_data = response.json()
                    return True, result_data
                except:
                    return True, None
            else:
                test_results["failed"] += 1
                error_msg = f"{test_name} - 期望状态码{expected_status}, 实际{response.status_code}"
                self.log("FAIL", module, error_msg)
                test_results["errors"].append({
                    "module": module,
                    "test": test_name,
                    "error": error_msg,
                    "response": response.text[:200] if response.text else ""
                })
                return False, None
                
        except Exception as e:
            test_results["failed"] += 1
            error_msg = f"{test_name} - 异常: {str(e)}"
            self.log("ERROR", module, error_msg)
            test_results["errors"].append({
                "module": module,
                "test": test_name,
                "error": error_msg
            })
            return False, None
    
    def test_user_management(self):
        """测试用户管理模块"""
        module = "用户管理"
        self.log("INFO", module, "=" * 50)
        self.log("INFO", module, "开始测试用户管理模块")
        
        module_results = {"total": 0, "passed": 0, "failed": 0}
        
        # 1. 获取用户列表
        success, users = self.test_api("GET", "/users", module, "获取用户列表")
        module_results["total"] += 1
        if success:
            module_results["passed"] += 1
            self.log("INFO", module, f"用户列表数量: {len(users.get('items', [])) if users else 0}")
        else:
            module_results["failed"] += 1
        
        # 2. 创建测试用户
        test_user_data = {
            "username": f"test_user_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "full_name": "测试用户",
            "password": "Test123456!",
            "is_active": True
        }
        
        success, created_user = self.test_api("POST", "/users", module, 
                                               "创建用户", test_user_data, 201)
        module_results["total"] += 1
        if success:
            module_results["passed"] += 1
            self.test_data["user_id"] = created_user.get("id")
            self.log("INFO", module, f"创建用户ID: {self.test_data['user_id']}")
        else:
            module_results["failed"] += 1
            # 尝试使用已存在的用户
            if users and users.get('items'):
                self.test_data["user_id"] = users['items'][0]['id']
                self.log("WARNING", module, f"使用已存在用户ID: {self.test_data['user_id']}")
        
        # 3. 获取用户详情
        if "user_id" in self.test_data:
            user_id = self.test_data["user_id"]
            success, user_detail = self.test_api("GET", f"/users/{user_id}", 
                                                 module, "获取用户详情")
            module_results["total"] += 1
            if success:
                module_results["passed"] += 1
            else:
                module_results["failed"] += 1
            
            # 4. 更新用户
            update_data = {
                "full_name": "更新的测试用户"
            }
            success, _ = self.test_api("PUT", f"/users/{user_id}", 
                                      module, "更新用户", update_data)
            module_results["total"] += 1
            if success:
                module_results["passed"] += 1
            else:
                module_results["failed"] += 1
        
        test_results["modules"][module] = module_results
        self.log("INFO", module, f"模块测试完成: 通过 {module_results['passed']}/{module_results['total']}")
    
    def test_role_permission(self):
        """测试角色权限模块"""
        module = "角色权限"
        self.log("INFO", module, "=" * 50)
        self.log("INFO", module, "开始测试角色权限模块")
        
        module_results = {"total": 0, "passed": 0, "failed": 0}
        
        # 1. 获取角色列表
        success, roles = self.test_api("GET", "/roles", module, "获取角色列表")
        module_results["total"] += 1
        if success:
            module_results["passed"] += 1
            self.log("INFO", module, f"角色数量: {len(roles.get('items', [])) if roles else 0}")
        else:
            module_results["failed"] += 1
        
        # 2. 获取权限列表
        success, permissions = self.test_api("GET", "/permissions", module, "获取权限列表")
        module_results["total"] += 1
        if success:
            module_results["passed"] += 1
            self.log("INFO", module, f"权限数量: {len(permissions.get('items', [])) if permissions else 0}")
        else:
            module_results["failed"] += 1
        
        # 3. 创建测试角色
        test_role_data = {
            "name": f"test_role_{int(time.time())}",
            "description": "测试角色",
            "is_active": True
        }
        
        success, created_role = self.test_api("POST", "/roles", module, 
                                              "创建角色", test_role_data, 201)
        module_results["total"] += 1
        if success:
            module_results["passed"] += 1
            self.test_data["role_id"] = created_role.get("id")
        else:
            module_results["failed"] += 1
            # 使用已存在的角色
            if roles and roles.get('items'):
                self.test_data["role_id"] = roles['items'][0]['id']
                self.log("WARNING", module, f"使用已存在角色ID: {self.test_data['role_id']}")
        
        # 4. 分配权限给角色
        if "role_id" in self.test_data and permissions and permissions.get('items'):
            role_id = self.test_data["role_id"]
            permission_ids = [p['id'] for p in permissions['items'][:5]]  # 分配前5个权限
            
            success, _ = self.test_api("POST", f"/roles/{role_id}/permissions", 
                                      module, "分配权限", {"permission_ids": permission_ids})
            module_results["total"] += 1
            if success:
                module_results["passed"] += 1
            else:
                module_results["failed"] += 1
        
        test_results["modules"][module] = module_results
        self.log("INFO", module, f"模块测试完成: 通过 {module_results['passed']}/{module_results['total']}")
    
    def test_project_management(self):
        """测试项目管理模块（抽样10-15个核心API）"""
        module = "项目管理"
        self.log("INFO", module, "=" * 50)
        self.log("INFO", module, "开始测试项目管理模块")
        
        module_results = {"total": 0, "passed": 0, "failed": 0}
        
        # 核心API测试列表
        project_apis = [
            ("GET", "/projects", "获取项目列表"),
            ("GET", "/projects/statistics", "获取项目统计"),
            ("POST", "/projects", "创建项目"),
            ("GET", "/projects/{id}", "获取项目详情"),
            ("PUT", "/projects/{id}", "更新项目"),
            ("GET", "/projects/{id}/progress", "查询项目进度"),
            ("GET", "/projects/{id}/cost", "项目成本计算"),
            ("GET", "/projects/{id}/members", "获取项目成员"),
            ("POST", "/projects/{id}/tasks", "创建项目任务"),
            ("GET", "/projects/{id}/risks", "项目风险评估"),
            ("GET", "/projects/{id}/timeline", "项目时间轴"),
            ("GET", "/projects/{id}/documents", "项目文档列表"),
        ]
        
        project_id = None
        
        for method, endpoint, test_name in project_apis:
            # 替换路径中的{id}
            if "{id}" in endpoint:
                if not project_id:
                    # 先获取项目列表以获取ID
                    success, projects = self.test_api("GET", "/projects", module, "获取项目列表(临时)")
                    if success and projects and projects.get('items'):
                        project_id = projects['items'][0]['id']
                    else:
                        # 创建测试项目
                        test_project = {
                            "name": f"测试项目_{int(time.time())}",
                            "description": "API测试项目",
                            "status": "planning"
                        }
                        success, created = self.test_api("POST", "/projects", module, 
                                                        "创建测试项目", test_project, 201)
                        if success:
                            project_id = created.get("id")
                
                if project_id:
                    endpoint = endpoint.replace("{id}", str(project_id))
                else:
                    self.log("WARNING", module, f"跳过测试: {test_name} (无可用项目ID)")
                    continue
            
            # 执行测试
            data = None
            if method == "POST" and "tasks" in endpoint:
                data = {
                    "title": "测试任务",
                    "description": "API测试任务"
                }
            elif method == "PUT":
                data = {
                    "description": "更新的项目描述"
                }
            
            success, _ = self.test_api(method, endpoint, module, test_name, data)
            module_results["total"] += 1
            if success:
                module_results["passed"] += 1
            else:
                module_results["failed"] += 1
        
        test_results["modules"][module] = module_results
        self.log("INFO", module, f"模块测试完成: 通过 {module_results['passed']}/{module_results['total']}")
    
    def test_production_management(self):
        """测试生产管理模块（抽样10-15个核心API）"""
        module = "生产管理"
        self.log("INFO", module, "=" * 50)
        self.log("INFO", module, "开始测试生产管理模块")
        
        module_results = {"total": 0, "passed": 0, "failed": 0}
        
        # 核心API测试列表
        production_apis = [
            ("GET", "/production/work-orders", "获取工单列表"),
            ("POST", "/production/work-orders", "创建工单"),
            ("GET", "/production/work-orders/{id}", "获取工单详情"),
            ("PUT", "/production/work-orders/{id}", "更新工单"),
            ("GET", "/production/work-orders/{id}/progress", "工单进度跟踪"),
            ("GET", "/production/quality-checks", "质量检查列表"),
            ("POST", "/production/quality-checks", "创建质量检查"),
            ("GET", "/production/materials", "物料跟踪列表"),
            ("GET", "/production/materials/{id}/tracking", "物料跟踪详情"),
            ("GET", "/production/capacity/analysis", "产能分析"),
            ("GET", "/production/equipment/status", "设备状态"),
            ("GET", "/production/schedule", "生产排程"),
        ]
        
        work_order_id = None
        
        for method, endpoint, test_name in production_apis:
            # 替换路径中的{id}
            if "{id}" in endpoint:
                if not work_order_id:
                    # 先获取工单列表
                    success, orders = self.test_api("GET", "/production/work-orders", 
                                                   module, "获取工单列表(临时)")
                    if success and orders and orders.get('items'):
                        work_order_id = orders['items'][0]['id']
                    else:
                        # 创建测试工单
                        test_order = {
                            "order_no": f"WO{int(time.time())}",
                            "product_name": "测试产品",
                            "quantity": 100
                        }
                        success, created = self.test_api("POST", "/production/work-orders", 
                                                        module, "创建测试工单", test_order, 201)
                        if success:
                            work_order_id = created.get("id")
                
                if work_order_id:
                    endpoint = endpoint.replace("{id}", str(work_order_id))
                else:
                    self.log("WARNING", module, f"跳过测试: {test_name} (无可用工单ID)")
                    continue
            
            # 执行测试
            data = None
            if method == "POST" and "quality-checks" in endpoint:
                data = {
                    "work_order_id": work_order_id,
                    "check_type": "incoming",
                    "result": "pass"
                }
            elif method == "PUT":
                data = {
                    "status": "in_progress"
                }
            
            success, _ = self.test_api(method, endpoint, module, test_name, data)
            module_results["total"] += 1
            if success:
                module_results["passed"] += 1
            else:
                module_results["failed"] += 1
        
        test_results["modules"][module] = module_results
        self.log("INFO", module, f"模块测试完成: 通过 {module_results['passed']}/{module_results['total']}")
    
    def test_sales_management(self):
        """测试销售管理模块（抽样10个核心API）"""
        module = "销售管理"
        self.log("INFO", module, "=" * 50)
        self.log("INFO", module, "开始测试销售管理模块")
        
        module_results = {"total": 0, "passed": 0, "failed": 0}
        
        # 核心API测试列表
        sales_apis = [
            ("GET", "/sales/customers", "客户管理列表"),
            ("POST", "/sales/customers", "创建客户"),
            ("GET", "/sales/customers/{id}", "客户详情"),
            ("GET", "/sales/contracts", "合同管理列表"),
            ("POST", "/sales/contracts", "创建合同"),
            ("GET", "/sales/payments", "回款管理列表"),
            ("POST", "/sales/payments", "创建回款记录"),
            ("GET", "/sales/performance", "销售业绩统计"),
            ("GET", "/sales/opportunities", "销售机会列表"),
            ("GET", "/sales/quotes", "报价单列表"),
        ]
        
        customer_id = None
        
        for method, endpoint, test_name in sales_apis:
            # 替换路径中的{id}
            if "{id}" in endpoint:
                if not customer_id:
                    # 先获取客户列表
                    success, customers = self.test_api("GET", "/sales/customers", 
                                                      module, "获取客户列表(临时)")
                    if success and customers and customers.get('items'):
                        customer_id = customers['items'][0]['id']
                    else:
                        # 创建测试客户
                        test_customer = {
                            "name": f"测试客户_{int(time.time())}",
                            "contact": "张三",
                            "phone": "13800138000"
                        }
                        success, created = self.test_api("POST", "/sales/customers", 
                                                        module, "创建测试客户", test_customer, 201)
                        if success:
                            customer_id = created.get("id")
                
                if customer_id:
                    endpoint = endpoint.replace("{id}", str(customer_id))
                else:
                    self.log("WARNING", module, f"跳过测试: {test_name} (无可用客户ID)")
                    continue
            
            # 执行测试
            data = None
            if method == "POST":
                if "contracts" in endpoint:
                    data = {
                        "customer_id": customer_id,
                        "contract_no": f"CON{int(time.time())}",
                        "amount": 100000
                    }
                elif "payments" in endpoint:
                    data = {
                        "customer_id": customer_id,
                        "amount": 50000,
                        "payment_date": datetime.now().isoformat()
                    }
            
            success, _ = self.test_api(method, endpoint, module, test_name, data)
            module_results["total"] += 1
            if success:
                module_results["passed"] += 1
            else:
                module_results["failed"] += 1
        
        test_results["modules"][module] = module_results
        self.log("INFO", module, f"模块测试完成: 通过 {module_results['passed']}/{module_results['total']}")
    
    def generate_report(self):
        """生成测试报告"""
        report = {
            "test_time": datetime.now().isoformat(),
            "summary": {
                "total_tests": test_results["total"],
                "passed": test_results["passed"],
                "failed": test_results["failed"],
                "success_rate": f"{(test_results['passed'] / test_results['total'] * 100):.2f}%" if test_results['total'] > 0 else "0%"
            },
            "modules": test_results["modules"],
            "errors": test_results["errors"],
            "warnings": test_results["warnings"]
        }
        
        # 保存JSON报告
        report_file = Path("data/test_core_api_report.json")
        report_file.parent.mkdir(exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成Markdown报告
        md_report = self.generate_markdown_report(report)
        md_file = Path("data/test_core_api_report.md")
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_report)
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print(f"总测试数: {report['summary']['total_tests']}")
        print(f"通过: {report['summary']['passed']}")
        print(f"失败: {report['summary']['failed']}")
        print(f"成功率: {report['summary']['success_rate']}")
        print(f"\n报告已保存:")
        print(f"  - JSON: {report_file}")
        print(f"  - Markdown: {md_file}")
        print("=" * 80)
        
        return report
    
    def generate_markdown_report(self, report: Dict) -> str:
        """生成Markdown格式的测试报告"""
        md = []
        md.append("# 核心业务API功能测试报告")
        md.append(f"\n**测试时间:** {report['test_time']}")
        md.append("\n## 测试概要\n")
        md.append("| 指标 | 数值 |")
        md.append("|------|------|")
        md.append(f"| 总测试数 | {report['summary']['total_tests']} |")
        md.append(f"| 通过 | {report['summary']['passed']} |")
        md.append(f"| 失败 | {report['summary']['failed']} |")
        md.append(f"| 成功率 | {report['summary']['success_rate']} |")
        
        md.append("\n## 模块测试结果\n")
        md.append("| 模块 | 总数 | 通过 | 失败 | 通过率 |")
        md.append("|------|------|------|------|--------|")
        
        for module_name, module_result in report['modules'].items():
            total = module_result['total']
            passed = module_result['passed']
            failed = module_result['failed']
            rate = f"{(passed / total * 100):.2f}%" if total > 0 else "0%"
            md.append(f"| {module_name} | {total} | {passed} | {failed} | {rate} |")
        
        if report['errors']:
            md.append("\n## 错误详情\n")
            for i, error in enumerate(report['errors'], 1):
                md.append(f"### 错误 {i}: {error['module']} - {error['test']}\n")
                md.append(f"**错误信息:** {error['error']}\n")
                if error.get('response'):
                    md.append(f"**响应内容:** ```\n{error['response']}\n```\n")
        
        if report['warnings']:
            md.append("\n## 警告信息\n")
            for warning in report['warnings']:
                md.append(f"- {warning}\n")
        
        md.append("\n## 测试覆盖范围\n")
        md.append("### 已测试模块\n")
        md.append("- ✅ 用户管理（CRUD操作）")
        md.append("- ✅ 角色权限管理")
        md.append("- ✅ 项目管理（核心API抽样）")
        md.append("- ✅ 生产管理（核心API抽样）")
        md.append("- ✅ 销售管理（核心API抽样）")
        
        md.append("\n### API覆盖率\n")
        md.append(f"- 总API数: 555+")
        md.append(f"- 已测试核心API: {report['summary']['total_tests']}")
        md.append(f"- 覆盖率: ~{(report['summary']['total_tests'] / 555 * 100):.1f}%")
        
        return "\n".join(md)


def main():
    """主测试流程"""
    print("=" * 80)
    print("核心业务API功能测试")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试服务: {BASE_URL}")
    print("=" * 80)
    
    tester = APITester()
    
    # 1. 登录认证
    if not tester.test_login():
        print("\n❌ 登录失败，无法继续测试")
        sys.exit(1)
    
    print("\n✅ 登录成功，开始测试各模块...\n")
    
    # 2. 测试各个模块
    try:
        tester.test_user_management()
        tester.test_role_permission()
        tester.test_project_management()
        tester.test_production_management()
        tester.test_sales_management()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 3. 生成测试报告
    tester.generate_report()
    
    # 返回退出码
    if test_results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
