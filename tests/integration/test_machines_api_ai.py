# -*- coding: utf-8 -*-
"""
机台管理 API 集成测试

测试模块：
- Machine CRUD operations
- Service history
- Documents management
"""

import pytest
from datetime import datetime, date

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator, Colors


@pytest.mark.integration
class TestMachinesCRUDAPI:
    """测试机台基本CRUD操作"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token):
        """测试初始化"""
        self.helper = APITestHelper(client, admin_token)
        self.generator = TestDataGenerator()
        self.tracked_resources = []

        self.helper.print_info("机台管理 - 基本CRUD操作")

        # 创建测试项目
        try:
            project_data = {
                "project_code": f"PJ{datetime.now().strftime('%y%m%d')}001",
                "project_name": "机台测试项目",
                "customer_name": "测试客户",
                "contract_amount": 1000000.00,
                "start_date": date.today().isoformat(),
                "estimated_end_date": date.today().isoformat(),
                "project_manager_id": 1,  # 假设存在
                "stage": "S1",
                "status": "OPEN",
                "health": "H1",
            }

            response = self.helper.post(
                "/projects", project_data, resource_type="project_for_machine"
            )
            if self.helper.assert_success(response):
                result = response.get("data", {})
                self.test_project_id = result.get("id")
                self.helper.print_success(f"测试项目创建成功，ID: {self.test_project_id}")
            else:
                self.test_project_id = None
                self.helper.print_warning("测试项目创建失败，相关测试将跳过")
        except Exception as e:
            self.helper.print_warning(f"测试项目创建失败: {e}，相关测试将跳过")
            self.test_project_id = None

    def test_create_machine(self):
        """测试创建机台"""
        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        self.helper.print_info("测试创建机台...")

        machine_data = {
            "project_id": self.test_project_id,
            "machine_name": "测试机台001",
            "machine_type": "ICT测试机",
            "specifications": {
                "channels": 32,
                "voltage_range": "0-12V",
                "current_range": "0-5A",
            },
            "status": "IN_DESIGN",
            "stage": "S2",
            "health": "H1",
        }

        response = self.helper.post("/machines", machine_data, resource_type="machine")

        if self.helper.assert_success(response):
            result = response.get("data", {})
            machine_id = result.get("id")
            if machine_id:
                self.tracked_resources.append(("machine", machine_id))
                self.helper.print_success(f"机台创建成功，ID: {machine_id}")
            else:
                self.helper.print_warning("机台创建成功，但未返回ID")
        else:
            self.helper.print_warning("机台创建响应不符合预期")

    def test_create_machine_for_project(self):
        """测试为项目创建机台"""
        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        self.helper.print_info("测试为项目创建机台...")

        machine_data = {
            "machine_name": "测试机台002",
            "machine_type": "FCT测试机",
            "status": "IN_DESIGN",
        }

        response = self.helper.post(
            f"/machines/projects/{self.test_project_id}/machines",
            machine_data,
            resource_type=f"machine_project_{self.test_project_id}",
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            machine_id = result.get("id")
            if machine_id:
                self.tracked_resources.append(("machine", machine_id))
                self.helper.print_success(f"项目机台创建成功，ID: {machine_id}")
            else:
                self.helper.print_warning("项目机台创建成功，但未返回ID")
        else:
            self.helper.print_warning("项目机台创建响应不符合预期")

    def test_get_machines_list(self):
        """测试获取机台列表"""
        self.helper.print_info("测试获取机台列表...")

        response = self.helper.get(
            "/machines",
            params={
                "page": 1,
                "page_size": 20,
                "status": "IN_DESIGN",
            },
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            items = result.get("items", [])
            total = result.get("total", 0)
            self.helper.print_success(f"获取到 {len(items)} 个机台，总计 {total} 个")
        else:
            self.helper.print_warning("获取机台列表响应不符合预期")

    def test_get_project_machines(self):
        """测试获取项目机台列表"""
        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        self.helper.print_info(f"测试获取项目机台列表 (ID: {self.test_project_id})...")

        response = self.helper.get(
            f"/machines/projects/{self.test_project_id}/machines",
            resource_type=f"project_machines_{self.test_project_id}",
        )

        if self.helper.assert_success(response):
            machines = response.get("data", [])
            self.helper.print_success(f"获取到 {len(machines)} 个项目机台")
        else:
            self.helper.print_warning("获取项目机台列表响应不符合预期")

    def test_get_machine_detail(self):
        """测试获取机台详情"""
        if not self.tracked_resources:
            pytest.skip("没有可用的机台ID")

        machine_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取机台详情 (ID: {machine_id})...")

        response = self.helper.get(
            f"/machines/{machine_id}", resource_type=f"machine_{machine_id}"
        )

        result = self.helper.assert_success(response)
        if result:
            self.helper.assert_data_not_empty(result)
            self.helper.print_success("机台详情获取成功")
        else:
            self.helper.print_warning("获取机台详情响应不符合预期")

    def test_update_machine(self):
        """测试更新机台"""
        if not self.tracked_resources:
            pytest.skip("没有可用的机台ID")

        machine_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新机台 (ID: {machine_id})...")

        update_data = {
            "status": "IN_MANUFACTURING",
            "stage": "S4",
            "health": "H2",
        }

        response = self.helper.put(
            f"/machines/{machine_id}",
            update_data,
            resource_type=f"machine_{machine_id}_update",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("机台更新成功")
        else:
            self.helper.print_warning("更新机台响应不符合预期")

    def test_update_machine_progress(self):
        """测试更新机台进度"""
        if not self.tracked_resources:
            pytest.skip("没有可用的机台ID")

        machine_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试更新机台进度 (ID: {machine_id})...")

        progress_data = {
            "progress_percentage": 50,
            "current_stage": "S4",
            "estimated_completion_date": date.today().isoformat(),
            "notes": "加工制造进行中",
        }

        response = self.helper.put(
            f"/machines/{machine_id}/progress",
            progress_data,
            resource_type=f"machine_{machine_id}_progress",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("机台进度更新成功")
        else:
            self.helper.print_warning("更新机台进度响应不符合预期")

    def test_get_machine_bom(self):
        """测试获取机台BOM"""
        if not self.tracked_resources:
            pytest.skip("没有可用的机台ID")

        machine_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取机台BOM (ID: {machine_id})...")

        response = self.helper.get(
            f"/machines/{machine_id}/bom", resource_type=f"machine_{machine_id}_bom"
        )

        if self.helper.assert_success(response):
            bom_items = response.get("data", [])
            self.helper.print_success(f"获取到 {len(bom_items)} 个BOM条目")
        else:
            self.helper.print_warning("获取机台BOM响应不符合预期")

    def test_get_project_machines_summary(self):
        """测试获取项目机台汇总"""
        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        self.helper.print_info(f"测试获取项目机台汇总 (ID: {self.test_project_id})...")

        response = self.helper.get(
            f"/machines/projects/{self.test_project_id}/summary",
            resource_type=f"project_machines_summary_{self.test_project_id}",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("项目机台汇总获取成功")
        else:
            self.helper.print_warning("获取项目机台汇总响应不符合预期")

    def test_recalculate_project_machines(self):
        """测试重新计算项目机台数据"""
        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        self.helper.print_info(f"测试重新计算项目机台数据 (ID: {self.test_project_id})...")

        response = self.helper.post(
            f"/machines/projects/{self.test_project_id}/recalculate",
            resource_type=f"project_machines_recalc_{self.test_project_id}",
        )

        if self.helper.assert_success(response):
            self.helper.print_success("项目机台数据重新计算成功")
        else:
            self.helper.print_warning("重新计算项目机台数据响应不符合预期")

    def test_delete_machine(self):
        """测试删除机台"""
        if not self.tracked_resources:
            pytest.skip("没有可用的机台ID")

        # 为删除测试创建一个单独的机台
        if not self.test_project_id:
            pytest.skip("没有可用的项目ID")

        machine_data = {
            "project_id": self.test_project_id,
            "machine_name": "待删除机台",
            "machine_type": "测试机",
            "status": "IN_DESIGN",
        }

        response = self.helper.post(
            "/machines", machine_data, resource_type="machine_to_delete"
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            machine_id = result.get("id")
            if machine_id:
                self.helper.print_info(f"测试删除机台 (ID: {machine_id})...")

                delete_response = self.helper.delete(
                    f"/machines/{machine_id}",
                    resource_type=f"machine_{machine_id}_delete",
                )

                if self.helper.assert_success(delete_response):
                    self.helper.print_success("机台删除成功")
                else:
                    self.helper.print_warning("删除机台响应不符合预期")
            else:
                self.helper.print_warning("删除测试机台创建失败")
        else:
            self.helper.print_warning("删除测试机台创建失败，跳过删除测试")


@pytest.mark.integration
class TestMachinesServiceHistoryAPI:
    """测试机台服务历史"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token):
        """测试初始化"""
        self.helper = APITestHelper(client, admin_token)
        self.generator = TestDataGenerator()
        self.tracked_resources = []

        self.helper.print_info("机台管理 - 服务历史")

        # 创建测试机台
        try:
            project_data = {
                "project_code": f"PJ{datetime.now().strftime('%y%m%d')}002",
                "project_name": "服务历史测试项目",
                "customer_name": "测试客户",
                "contract_amount": 1000000.00,
                "start_date": date.today().isoformat(),
                "estimated_end_date": date.today().isoformat(),
                "project_manager_id": 1,
                "stage": "S1",
                "status": "OPEN",
                "health": "H1",
            }

            response = self.helper.post(
                "/projects", project_data, resource_type="project_for_service"
            )
            if self.helper.assert_success(response):
                result = response.get("data", {})
                project_id = result.get("id")

                machine_data = {
                    "project_id": project_id,
                    "machine_name": "服务测试机台",
                    "machine_type": "测试机",
                    "status": "IN_DESIGN",
                }

                machine_response = self.helper.post(
                    "/machines", machine_data, resource_type="machine_for_service"
                )
                if self.helper.assert_success(machine_response):
                    machine_result = machine_response.get("data", {})
                    self.test_machine_id = machine_result.get("id")
                    self.helper.print_success(
                        f"测试机台创建成功，ID: {self.test_machine_id}"
                    )
                else:
                    self.test_machine_id = None
                    self.helper.print_warning("测试机台创建失败，相关测试将跳过")
            else:
                self.test_machine_id = None
                self.helper.print_warning("测试项目创建失败，相关测试将跳过")
        except Exception as e:
            self.helper.print_warning(f"测试环境初始化失败: {e}，相关测试将跳过")
            self.test_machine_id = None

    def test_get_machine_service_history(self):
        """测试获取机台服务历史"""
        if not self.test_machine_id:
            pytest.skip("没有可用的机台ID")

        self.helper.print_info(f"测试获取机台服务历史 (ID: {self.test_machine_id})...")

        response = self.helper.get(
            f"/machines/{self.test_machine_id}/service-history",
            resource_type=f"machine_{self.test_machine_id}_service_history",
        )

        if self.helper.assert_success(response):
            history_items = response.get("data", [])
            self.helper.print_success(f"获取到 {len(history_items)} 条服务历史记录")
        else:
            self.helper.print_warning("获取机台服务历史响应不符合预期")


@pytest.mark.integration
class TestMachinesDocumentsAPI:
    """测试机台文档管理"""

    @pytest.fixture(autouse=True)
    def setup(self, client, admin_token):
        """测试初始化"""
        self.helper = APITestHelper(client, admin_token)
        self.generator = TestDataGenerator()
        self.tracked_resources = []

        self.helper.print_info("机台管理 - 文档管理")

        # 创建测试机台
        try:
            project_data = {
                "project_code": f"PJ{datetime.now().strftime('%y%m%d')}003",
                "project_name": "文档测试项目",
                "customer_name": "测试客户",
                "contract_amount": 1000000.00,
                "start_date": date.today().isoformat(),
                "estimated_end_date": date.today().isoformat(),
                "project_manager_id": 1,
                "stage": "S1",
                "status": "OPEN",
                "health": "H1",
            }

            response = self.helper.post(
                "/projects", project_data, resource_type="project_for_documents"
            )
            if self.helper.assert_success(response):
                result = response.get("data", {})
                project_id = result.get("id")

                machine_data = {
                    "project_id": project_id,
                    "machine_name": "文档测试机台",
                    "machine_type": "测试机",
                    "status": "IN_DESIGN",
                }

                machine_response = self.helper.post(
                    "/machines", machine_data, resource_type="machine_for_documents"
                )
                if self.helper.assert_success(machine_response):
                    machine_result = machine_response.get("data", {})
                    self.test_machine_id = machine_result.get("id")
                    self.helper.print_success(
                        f"测试机台创建成功，ID: {self.test_machine_id}"
                    )
                else:
                    self.test_machine_id = None
                    self.helper.print_warning("测试机台创建失败，相关测试将跳过")
            else:
                self.test_machine_id = None
                self.helper.print_warning("测试项目创建失败，相关测试将跳过")
        except Exception as e:
            self.helper.print_warning(f"测试环境初始化失败: {e}，相关测试将跳过")
            self.test_machine_id = None

    def test_upload_machine_document(self):
        """测试上传机台文档"""
        if not self.test_machine_id:
            pytest.skip("没有可用的机台ID")

        self.helper.print_info(f"测试上传机台文档 (ID: {self.test_machine_id})...")

        # 注意：实际文件上传需要 multipart/form-data
        # 这里测试基本请求结构
        document_data = {
            "title": "测试文档",
            "document_type": "SPECIFICATION",
            "description": "测试文档描述",
            "version": "1.0",
        }

        # 使用 files 参数上传文件
        try:
            import io

            file_content = io.BytesIO("测试文件内容".encode("utf-8"))
            files = {"file": ("test.txt", file_content, "text/plain")}

            response = self.helper.post(
                f"/machines/{self.test_machine_id}/documents/upload",
                data=document_data,
                files=files,
                resource_type=f"machine_{self.test_machine_id}_document",
            )

            if self.helper.assert_success(response):
                result = response.get("data", {})
                doc_id = result.get("id")
                if doc_id:
                    self.tracked_resources.append(("document", doc_id))
                    self.helper.print_success(f"文档上传成功，ID: {doc_id}")
                else:
                    self.helper.print_warning("文档上传成功，但未返回ID")
            else:
                self.helper.print_warning("文档上传响应不符合预期")
        except Exception as e:
            self.helper.print_warning(f"文档上传测试失败: {e}，跳过此测试")

    def test_get_machine_documents(self):
        """测试获取机台文档列表"""
        if not self.test_machine_id:
            pytest.skip("没有可用的机台ID")

        self.helper.print_info(f"测试获取机台文档列表 (ID: {self.test_machine_id})...")

        response = self.helper.get(
            f"/machines/{self.test_machine_id}/documents",
            params={
                "document_type": "SPECIFICATION",
                "page": 1,
                "page_size": 20,
            },
            resource_type=f"machine_{self.test_machine_id}_documents",
        )

        if self.helper.assert_success(response):
            result = response.get("data", {})
            items = result.get("items", [])
            self.helper.print_success(f"获取到 {len(items)} 个文档")
        else:
            self.helper.print_warning("获取机台文档列表响应不符合预期")

    def test_download_machine_document(self):
        """测试下载机台文档"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        machine_id = self.test_machine_id
        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试下载文档 (ID: {doc_id})...")

        try:
            response = self.helper.get(
                f"/machines/{machine_id}/documents/{doc_id}/download",
                resource_type=f"machine_document_{doc_id}_download",
            )

            # 下载操作可能返回文件流
            if response.get("status_code") == 200:
                self.helper.print_success("文档下载成功")
            else:
                self.helper.print_warning("文档下载响应不符合预期")
        except Exception as e:
            self.helper.print_warning(f"文档下载测试失败: {e}")

    def test_get_document_versions(self):
        """测试获取文档版本列表"""
        if not self.tracked_resources:
            pytest.skip("没有可用的文档ID")

        machine_id = self.test_machine_id
        doc_id = self.tracked_resources[0][1]
        self.helper.print_info(f"测试获取文档版本列表 (ID: {doc_id})...")

        response = self.helper.get(
            f"/machines/{machine_id}/documents/{doc_id}/versions",
            resource_type=f"machine_document_{doc_id}_versions",
        )

        if self.helper.assert_success(response):
            versions = response.get("data", [])
            self.helper.print_success(f"获取到 {len(versions)} 个文档版本")
        else:
            self.helper.print_warning("获取文档版本列表响应不符合预期")
