#!/usr/bin/env python3
"""
Team 10: 售前AI系统集成 - 验证脚本
验证所有功能是否正常工作
"""
import sys
import requests
from datetime import date
from typing import Dict, Any
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = f"{BASE_URL}/auth/login"
AI_BASE_URL = f"{BASE_URL}/presale/ai"

# 测试用户凭据
TEST_USER = {
    "username": "admin",
    "password": "admin123"
}


class Team10Verifier:
    """Team 10 验证器"""

    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} | {test_name}"
        if message:
            result += f" | {message}"
        print(result)
        self.test_results.append({
            "name": test_name,
            "success": success,
            "message": message
        })

    def authenticate(self) -> bool:
        """认证并获取token"""
        try:
            response = requests.post(
                AUTH_URL,
                data=TEST_USER
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                self.log_test("用户认证", True, f"Token获取成功")
                return True
            else:
                self.log_test("用户认证", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("用户认证", False, str(e))
            return False

    def test_health_check(self) -> bool:
        """测试健康检查"""
        try:
            response = requests.get(
                f"{AI_BASE_URL}/health-check",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                self.log_test("健康检查", status == "healthy", f"状态: {status}")
                return status == "healthy"
            else:
                self.log_test("健康检查", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("健康检查", False, str(e))
            return False

    def test_dashboard_stats(self) -> bool:
        """测试仪表盘统计"""
        try:
            response = requests.get(
                f"{AI_BASE_URL}/dashboard/stats",
                headers=self.headers,
                params={"days": 30}
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_usage", "success_rate", "top_functions", "usage_trend"]
                has_all_fields = all(field in data for field in required_fields)
                self.log_test(
                    "仪表盘统计",
                    has_all_fields,
                    f"总使用: {data.get('total_usage', 0)}, 成功率: {data.get('success_rate', 0)}%"
                )
                return has_all_fields
            else:
                self.log_test("仪表盘统计", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("仪表盘统计", False, str(e))
            return False

    def test_usage_stats(self) -> bool:
        """测试使用统计"""
        try:
            response = requests.get(
                f"{AI_BASE_URL}/usage-stats",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("使用统计", True, f"返回 {len(data)} 条记录")
                return True
            else:
                self.log_test("使用统计", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("使用统计", False, str(e))
            return False

    def test_submit_feedback(self) -> bool:
        """测试提交反馈"""
        try:
            feedback_data = {
                "ai_function": "requirement",
                "rating": 5,
                "feedback_text": "自动化测试反馈"
            }
            
            response = requests.post(
                f"{AI_BASE_URL}/feedback",
                headers=self.headers,
                json=feedback_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("提交反馈", True, f"反馈ID: {data.get('id')}")
                return True
            else:
                self.log_test("提交反馈", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("提交反馈", False, str(e))
            return False

    def test_get_feedback(self) -> bool:
        """测试获取反馈"""
        try:
            response = requests.get(
                f"{AI_BASE_URL}/feedback/requirement",
                headers=self.headers,
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("获取反馈", True, f"返回 {len(data)} 条反馈")
                return True
            else:
                self.log_test("获取反馈", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("获取反馈", False, str(e))
            return False

    def test_start_workflow(self) -> bool:
        """测试启动工作流"""
        try:
            workflow_data = {
                "presale_ticket_id": 9999,
                "initial_data": {"test": "data"},
                "auto_run": True
            }
            
            response = requests.post(
                f"{AI_BASE_URL}/workflow/start",
                headers=self.headers,
                json=workflow_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("启动工作流", True, f"创建 {len(data)} 个步骤")
                return True
            else:
                self.log_test("启动工作流", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("启动工作流", False, str(e))
            return False

    def test_get_workflow_status(self) -> bool:
        """测试获取工作流状态"""
        try:
            response = requests.get(
                f"{AI_BASE_URL}/workflow/status/9999",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                progress = data.get("progress", 0)
                self.log_test("工作流状态", True, f"进度: {progress}%")
                return True
            elif response.status_code == 404:
                # 工作流不存在也是正常的
                self.log_test("工作流状态", True, "工作流不存在（正常）")
                return True
            else:
                self.log_test("工作流状态", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("工作流状态", False, str(e))
            return False

    def test_get_configs(self) -> bool:
        """测试获取配置"""
        try:
            response = requests.get(
                f"{AI_BASE_URL}/config",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("获取配置", True, f"返回 {len(data)} 个配置")
                return True
            else:
                self.log_test("获取配置", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("获取配置", False, str(e))
            return False

    def test_update_config(self) -> bool:
        """测试更新配置"""
        try:
            config_data = {
                "enabled": True,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{AI_BASE_URL}/config/update",
                headers=self.headers,
                json=config_data,
                params={"ai_function": "test_function"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("更新配置", True, f"配置ID: {data.get('id')}")
                return True
            else:
                self.log_test("更新配置", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("更新配置", False, str(e))
            return False

    def test_get_audit_logs(self) -> bool:
        """测试获取审计日志"""
        try:
            response = requests.get(
                f"{AI_BASE_URL}/audit-log",
                headers=self.headers,
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("审计日志", True, f"返回 {len(data)} 条日志")
                return True
            else:
                self.log_test("审计日志", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("审计日志", False, str(e))
            return False

    def test_export_report(self) -> bool:
        """测试导出报告"""
        try:
            export_data = {
                "start_date": "2026-02-01",
                "end_date": "2026-02-15",
                "format": "excel"
            }
            
            response = requests.post(
                f"{AI_BASE_URL}/export-report",
                headers=self.headers,
                json=export_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("导出报告", True, f"文件: {data.get('file_name')}")
                return True
            else:
                self.log_test("导出报告", False, f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("导出报告", False, str(e))
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("Team 10: 售前AI系统集成 - 验证测试")
        print("="*60 + "\n")

        # 认证
        if not self.authenticate():
            print("\n❌ 认证失败，无法继续测试")
            return

        # 运行所有测试
        tests = [
            ("1. 健康检查", self.test_health_check),
            ("2. 仪表盘统计", self.test_dashboard_stats),
            ("3. 使用统计", self.test_usage_stats),
            ("4. 提交反馈", self.test_submit_feedback),
            ("5. 获取反馈", self.test_get_feedback),
            ("6. 启动工作流", self.test_start_workflow),
            ("7. 工作流状态", self.test_get_workflow_status),
            ("8. 获取配置", self.test_get_configs),
            ("9. 更新配置", self.test_update_config),
            ("10. 审计日志", self.test_get_audit_logs),
            ("11. 导出报告", self.test_export_report),
        ]

        print("\n开始测试...")
        print("-"*60 + "\n")

        for test_name, test_func in tests:
            print(f"测试: {test_name}")
            test_func()
            print()

        # 统计结果
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed

        print("\n" + "="*60)
        print("测试结果汇总")
        print("="*60)
        print(f"总测试数: {total}")
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"成功率: {(passed/total*100):.1f}%")
        print("="*60 + "\n")

        if failed > 0:
            print("失败的测试:")
            for r in self.test_results:
                if not r["success"]:
                    print(f"  - {r['name']}: {r['message']}")
            print()

        return failed == 0


def main():
    """主函数"""
    verifier = Team10Verifier()
    success = verifier.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
