"""
工程师进度管理系统 - 单元测试模板
使用此模板编写全面的单元测试

运行测试：
    # 运行全部测试
    pytest

    # 运行特定标记的测试
    pytest -m unit
    pytest -m engineer
    pytest -m aggregation

    # 运行特定测试文件
    pytest tests/test_engineers_template.py

    # 查看覆盖率
    pytest --cov=app --cov-report=html
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.task_center import TaskUnified, TaskApprovalWorkflow, TaskCompletionProof
from app.models.enums import TaskImportance, TaskStatus, TaskPriority, ApprovalDecision
from app.services.progress_aggregation_service import ProgressAggregationService


# ==================== 模块1: 工程师端 - 项目查询 ====================

@pytest.mark.unit
@pytest.mark.engineer
class TestGetMyProjects:
    """测试获取我的项目列表"""

    def test_get_my_projects_success(self, client: TestClient, auth_headers: dict, mock_project):
        """成功获取项目列表"""
        response = client.get(
            "/api/v1/engineers/my-projects?page=1&page_size=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证分页结构
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data

        # 验证至少有一个项目
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_get_my_projects_pagination(self, client: TestClient, auth_headers: dict):
        """测试分页功能"""
        response = client.get(
            "/api/v1/engineers/my-projects?page=2&page_size=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    def test_get_my_projects_unauthorized(self, client: TestClient):
        """未认证访问应返回401"""
        response = client.get("/api/v1/engineers/my-projects")
        assert response.status_code == 401


# ==================== 模块2: 工程师端 - 任务创建 ====================

@pytest.mark.unit
@pytest.mark.engineer
class TestCreateTask:
    """测试创建任务"""

    def test_create_general_task_success(
        self, client: TestClient, auth_headers: dict, mock_project, db_session: Session
    ):
        """创建一般任务成功（无需审批）"""
        task_data = {
            "project_id": mock_project.id,
            "title": "单元测试任务",
            "task_importance": "GENERAL",
            "priority": "MEDIUM",
            "estimated_hours": 10.0,
        }

        response = client.post(
            "/api/v1/engineers/tasks",
            json=task_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证任务编码生成
        assert "task_code" in data
        assert data["task_code"].startswith("TASK-")

        # 验证状态为ACCEPTED（一般任务自动接受）
        assert data["status"] == "ACCEPTED"

        # 验证任务重要性
        assert data["task_importance"] == "GENERAL"

        # 验证数据库记录
        task = db_session.query(TaskUnified).filter(
            TaskUnified.task_code == data["task_code"]
        ).first()
        assert task is not None
        assert task.title == "单元测试任务"

    def test_create_important_task_requires_approval(
        self, client: TestClient, auth_headers: dict, mock_project, db_session: Session
    ):
        """创建重要任务需要审批"""
        task_data = {
            "project_id": mock_project.id,
            "title": "重要任务",
            "task_importance": "IMPORTANT",
            "justification": "这是重要任务的理由",
            "priority": "HIGH",
            "estimated_hours": 40.0,
        }

        response = client.post(
            "/api/v1/engineers/tasks",
            json=task_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证状态为PENDING_APPROVAL
        assert data["status"] == "PENDING_APPROVAL"

        # 验证审批工作流已创建
        task_id = data["id"]
        approval = db_session.query(TaskApprovalWorkflow).filter(
            TaskApprovalWorkflow.task_id == task_id
        ).first()
        assert approval is not None
        assert approval.decision == "PENDING"
        assert approval.approver_id == mock_project.pm_id

    def test_create_important_task_without_justification_fails(
        self, client: TestClient, auth_headers: dict, mock_project
    ):
        """创建重要任务但未提供理由应失败"""
        task_data = {
            "project_id": mock_project.id,
            "title": "重要任务",
            "task_importance": "IMPORTANT",
            # 缺少 justification
            "priority": "HIGH",
            "estimated_hours": 40.0,
        }

        response = client.post(
            "/api/v1/engineers/tasks",
            json=task_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "必须说明必要性" in response.json()["detail"]

    def test_create_task_invalid_project(self, client: TestClient, auth_headers: dict):
        """创建任务时项目不存在应失败"""
        task_data = {
            "project_id": 99999,  # 不存在的项目ID
            "title": "测试任务",
            "task_importance": "GENERAL",
            "priority": "MEDIUM",
        }

        response = client.post(
            "/api/v1/engineers/tasks",
            json=task_data,
            headers=auth_headers
        )

        assert response.status_code == 404

    @pytest.mark.slow
    def test_task_code_uniqueness(
        self, client: TestClient, auth_headers: dict, mock_project
    ):
        """验证任务编码唯一性"""
        task_data = {
            "project_id": mock_project.id,
            "title": "任务1",
            "task_importance": "GENERAL",
            "priority": "MEDIUM",
        }

        # 创建多个任务，验证编码递增
        codes = []
        for i in range(5):
            task_data["title"] = f"任务{i + 1}"
            response = client.post(
                "/api/v1/engineers/tasks",
                json=task_data,
                headers=auth_headers
            )
            assert response.status_code == 200
            codes.append(response.json()["task_code"])

        # 验证所有编码唯一
        assert len(codes) == len(set(codes))


# ==================== 模块3: 工程师端 - 进度更新 ====================

@pytest.mark.unit
@pytest.mark.engineer
@pytest.mark.aggregation
class TestUpdateTaskProgress:
    """测试更新任务进度（核心功能：实时聚合）"""

    def test_update_progress_success(
        self, client: TestClient, auth_headers: dict, mock_task, db_session: Session
    ):
        """成功更新进度"""
        progress_data = {
            "progress": 50,
            "actual_hours": 5.0,
            "progress_note": "已完成一半",
        }

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_task.id}/progress",
            json=progress_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证进度更新
        assert data["progress"] == 50
        assert data["actual_hours"] == 5.0
        assert data["progress_note"] == "已完成一半"

        # ⭐ 验证项目进度已聚合（痛点2解决方案）
        assert "project_progress_updated" in data
        assert data["project_progress_updated"] is True

        # 验证数据库
        db_session.refresh(mock_task)
        assert mock_task.progress == 50
        assert mock_task.status == "IN_PROGRESS"  # 应自动转为IN_PROGRESS

    def test_update_progress_auto_status_change(
        self, client: TestClient, auth_headers: dict, mock_task, db_session: Session
    ):
        """进度>0时自动改变状态为IN_PROGRESS"""
        # 确保初始状态为ACCEPTED
        mock_task.status = TaskStatus.ACCEPTED
        db_session.commit()

        progress_data = {"progress": 10}

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_task.id}/progress",
            json=progress_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "IN_PROGRESS"

    def test_update_progress_invalid_range(
        self, client: TestClient, auth_headers: dict, mock_task
    ):
        """进度范围验证（0-100）"""
        # 测试负数
        response = client.put(
            f"/api/v1/engineers/tasks/{mock_task.id}/progress",
            json={"progress": -10},
            headers=auth_headers
        )
        assert response.status_code == 400

        # 测试超过100
        response = client.put(
            f"/api/v1/engineers/tasks/{mock_task.id}/progress",
            json={"progress": 150},
            headers=auth_headers
        )
        assert response.status_code == 400

    def test_update_progress_permission_denied(
        self, client: TestClient, auth_headers: dict, mock_task, db_session: Session
    ):
        """只能更新自己的任务"""
        # 修改任务归属为其他用户
        mock_task.assignee_id = 999
        db_session.commit()

        progress_data = {"progress": 50}

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_task.id}/progress",
            json=progress_data,
            headers=auth_headers
        )

        assert response.status_code == 403
        assert "只能更新分配给自己的任务" in response.json()["detail"]

    def test_update_progress_wrong_status(
        self, client: TestClient, auth_headers: dict, mock_task, db_session: Session
    ):
        """已完成或已拒绝的任务不能更新进度"""
        mock_task.status = TaskStatus.COMPLETED
        db_session.commit()

        progress_data = {"progress": 60}

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_task.id}/progress",
            json=progress_data,
            headers=auth_headers
        )

        assert response.status_code == 400


# ==================== 模块4: 工程师端 - 任务完成 ====================

@pytest.mark.unit
@pytest.mark.engineer
class TestCompleteTask:
    """测试完成任务"""

    def test_complete_task_with_proof_success(
        self, client: TestClient, auth_headers: dict, mock_task, db_session: Session
    ):
        """有证明材料时成功完成任务"""
        # 先上传证明材料
        proof = TaskCompletionProof(
            task_id=mock_task.id,
            file_path="/uploads/test.jpg",
            file_size=1024,
            uploaded_by=1,
        )
        db_session.add(proof)
        db_session.commit()

        completion_data = {
            "completion_note": "任务已完成",
        }

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_task.id}/complete",
            json=completion_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证状态和进度
        assert data["status"] == "COMPLETED"
        assert data["progress"] == 100
        assert data["completed_at"] is not None

        # 验证项目进度已聚合
        assert data["project_progress_updated"] is True

    def test_complete_task_without_proof_fails(
        self, client: TestClient, auth_headers: dict, mock_task
    ):
        """没有证明材料时完成任务应失败"""
        completion_data = {"completion_note": "完成"}

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_task.id}/complete",
            json=completion_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "需要上传至少一个完成证明" in response.json()["detail"]


# ==================== 模块5: PM审批端 ====================

@pytest.mark.unit
@pytest.mark.pm
class TestPMApproval:
    """测试PM审批功能"""

    def test_get_pending_approval_tasks(
        self, client: TestClient, pm_auth_headers: dict, mock_important_task
    ):
        """PM获取待审批任务列表"""
        response = client.get(
            "/api/v1/engineers/tasks/pending-approval",
            headers=pm_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert len(data["items"]) >= 1

        # 验证返回的是待审批任务
        for item in data["items"]:
            assert item["status"] == "PENDING_APPROVAL"

    def test_approve_task_success(
        self, client: TestClient, pm_auth_headers: dict, mock_important_task, db_session: Session
    ):
        """PM批准任务成功"""
        approval_data = {
            "comment": "任务合理，批准执行",
        }

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_important_task.id}/approve",
            json=approval_data,
            headers=pm_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证任务状态变为ACCEPTED
        assert data["status"] == "ACCEPTED"

        # 验证审批工作流
        approval = db_session.query(TaskApprovalWorkflow).filter(
            TaskApprovalWorkflow.task_id == mock_important_task.id
        ).first()
        assert approval.decision == "APPROVED"
        assert approval.comment == "任务合理，批准执行"
        assert approval.approved_at is not None

    def test_reject_task_success(
        self, client: TestClient, pm_auth_headers: dict, mock_important_task, db_session: Session
    ):
        """PM拒绝任务成功"""
        rejection_data = {
            "reason": "不符合项目优先级",
        }

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_important_task.id}/reject",
            json=rejection_data,
            headers=pm_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证任务状态变为REJECTED
        assert data["status"] == "REJECTED"

        # 验证审批工作流
        approval = db_session.query(TaskApprovalWorkflow).filter(
            TaskApprovalWorkflow.task_id == mock_important_task.id
        ).first()
        assert approval.decision == "REJECTED"
        assert approval.comment == "不符合项目优先级"

    def test_non_pm_cannot_approve(
        self, client: TestClient, auth_headers: dict, mock_important_task
    ):
        """非PM用户不能审批"""
        approval_data = {"comment": "批准"}

        response = client.put(
            f"/api/v1/engineers/tasks/{mock_important_task.id}/approve",
            json=approval_data,
            headers=auth_headers  # 使用普通工程师token
        )

        assert response.status_code == 403


# ==================== 模块6: 跨部门进度视图 ====================

@pytest.mark.unit
@pytest.mark.engineer
@pytest.mark.integration
class TestCrossDepartmentProgressVisibility:
    """测试跨部门进度可见性（痛点1解决方案）"""

    def test_get_progress_visibility_success(
        self, client: TestClient, auth_headers: dict, mock_project, mock_task
    ):
        """成功获取跨部门进度视图"""
        response = client.get(
            f"/api/v1/engineers/projects/{mock_project.id}/progress-visibility",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # ⭐ 验证数据结构（痛点1解决方案）
        assert "overall_progress" in data  # 项目整体进度
        assert "department_progress" in data  # 部门维度进度
        assert "assignee_progress" in data  # 人员维度进度
        assert "stage_progress" in data  # 阶段维度进度
        assert "active_delays" in data  # 活跃延期

    def test_progress_visibility_shows_all_departments(
        self,
        client: TestClient,
        auth_headers: dict,
        mock_project,
        db_session: Session,
        mock_user,
        create_test_task,
    ):
        """验证跨部门视图包含所有部门数据"""
        # 创建不同部门的任务
        departments = ["机械部", "电气部", "软件部"]
        for dept in departments:
            create_test_task(
                db=db_session,
                task_code=f"TASK-TEST-{dept}",
                project_id=mock_project.id,
                title=f"{dept}任务",
                task_importance="GENERAL",
                status="IN_PROGRESS",
                progress=30,
                assignee_id=mock_user.id,
                created_by=mock_user.id,
                estimated_hours=10.0,
                is_active=True,
            )

        response = client.get(
            f"/api/v1/engineers/projects/{mock_project.id}/progress-visibility",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # 验证所有部门都显示（不限于当前用户部门）
        dept_progress = data["department_progress"]
        # 应该有数据（具体数量取决于mock数据）
        assert len(dept_progress) >= 1


# ==================== 模块7: 进度聚合算法单元测试 ====================

@pytest.mark.unit
@pytest.mark.aggregation
class TestProgressAggregationService:
    """测试进度聚合服务（核心算法）"""

    def test_aggregate_project_progress_weighted_average(
        self, db_session: Session, mock_project, mock_user, create_test_task
    ):
        """测试加权平均算法准确性"""
        # 创建测试任务
        # 任务1: 10小时, 50%进度 => 贡献5小时
        create_test_task(
            db=db_session,
            task_code="TASK-AGG-001",
            project_id=mock_project.id,
            title="任务1",
            task_importance="GENERAL",
            status="IN_PROGRESS",
            progress=50,
            assignee_id=mock_user.id,
            created_by=mock_user.id,
            estimated_hours=10.0,
            is_active=True,
        )

        # 任务2: 20小时, 75%进度 => 贡献15小时
        create_test_task(
            db=db_session,
            task_code="TASK-AGG-002",
            project_id=mock_project.id,
            title="任务2",
            task_importance="GENERAL",
            status="IN_PROGRESS",
            progress=75,
            assignee_id=mock_user.id,
            created_by=mock_user.id,
            estimated_hours=20.0,
            is_active=True,
        )

        # 任务3: 10小时, 100%进度 => 贡献10小时
        create_test_task(
            db=db_session,
            task_code="TASK-AGG-003",
            project_id=mock_project.id,
            title="任务3",
            task_importance="GENERAL",
            status="COMPLETED",
            progress=100,
            assignee_id=mock_user.id,
            created_by=mock_user.id,
            estimated_hours=10.0,
            is_active=True,
        )

        # 手工计算预期值
        # 总进度 = (5 + 15 + 10) / (10 + 20 + 10) = 30 / 40 = 75%

        # 执行聚合
        result = ProgressAggregationService.aggregate_project_progress(
            project_id=mock_project.id, db=db_session
        )

        # 验证结果
        assert result["overall_progress"] == 75.0
        assert result["total_tasks"] == 3
        assert result["completed_tasks"] == 1

    def test_aggregate_handles_zero_hours(
        self, db_session: Session, mock_project, mock_user, create_test_task
    ):
        """测试零工时边界情况"""
        # 创建没有预估工时的任务
        create_test_task(
            db=db_session,
            task_code="TASK-ZERO",
            project_id=mock_project.id,
            title="零工时任务",
            task_importance="GENERAL",
            status="IN_PROGRESS",
            progress=50,
            assignee_id=mock_user.id,
            created_by=mock_user.id,
            estimated_hours=None,  # 无工时估计
            is_active=True,
        )

        # 执行聚合（不应崩溃）
        result = ProgressAggregationService.aggregate_project_progress(
            project_id=mock_project.id, db=db_session
        )

        # 验证不会除以零
        assert result is not None
        assert "overall_progress" in result

    def test_aggregate_excludes_inactive_tasks(
        self, db_session: Session, mock_project, mock_user, create_test_task
    ):
        """测试聚合时排除非活跃任务"""
        # 活跃任务: 50%进度
        create_test_task(
            db=db_session,
            task_code="TASK-ACTIVE",
            project_id=mock_project.id,
            title="活跃任务",
            task_importance="GENERAL",
            status="IN_PROGRESS",
            progress=50,
            assignee_id=mock_user.id,
            created_by=mock_user.id,
            estimated_hours=10.0,
            is_active=True,
        )

        # 非活跃任务: 100%进度（应被排除）
        create_test_task(
            db=db_session,
            task_code="TASK-INACTIVE",
            project_id=mock_project.id,
            title="非活跃任务",
            task_importance="GENERAL",
            status="COMPLETED",
            progress=100,
            assignee_id=mock_user.id,
            created_by=mock_user.id,
            estimated_hours=10.0,
            is_active=False,  # 非活跃
        )

        result = ProgressAggregationService.aggregate_project_progress(
            project_id=mock_project.id, db=db_session
        )

        # 只应统计活跃任务
        assert result["total_tasks"] == 1
        assert result["overall_progress"] == 50.0


# ==================== 模块8: 安全性测试 ====================

@pytest.mark.unit
@pytest.mark.security
class TestSecurity:
    """安全性测试"""

    def test_sql_injection_prevention(self, client: TestClient, auth_headers: dict):
        """测试SQL注入防护"""
        malicious_input = "'; DROP TABLE task_unified; --"

        task_data = {
            "project_id": 1,
            "title": malicious_input,
            "task_importance": "GENERAL",
            "priority": "MEDIUM",
        }

        # 应该安全处理，不会执行SQL注入
        response = client.post(
            "/api/v1/engineers/tasks",
            json=task_data,
            headers=auth_headers
        )

        # 即使创建失败，也不应导致数据库被破坏
        # 数据库应该仍然正常（通过后续查询验证）

    def test_file_upload_size_limit(self, client: TestClient, auth_headers: dict, mock_task):
        """测试文件上传大小限制"""
        # TODO: 实现文件上传测试
        # 验证 MAX_FILE_SIZE = 10MB 限制
        pass

    def test_file_type_whitelist(self, client: TestClient, auth_headers: dict, mock_task):
        """测试文件类型白名单"""
        # TODO: 实现文件类型验证测试
        # 验证 ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"}
        pass


# ==================== 运行说明 ====================

"""
测试运行指南：

1. 安装测试依赖：
   pip install pytest pytest-cov httpx

2. 运行全部测试：
   pytest

3. 运行特定类别：
   pytest -m unit          # 单元测试
   pytest -m engineer      # 工程师端测试
   pytest -m pm            # PM审批端测试
   pytest -m aggregation   # 聚合算法测试
   pytest -m security      # 安全性测试

4. 查看覆盖率：
   pytest --cov=app --cov-report=html
   open htmlcov/index.html

5. 运行特定测试：
   pytest tests/test_engineers_template.py::TestCreateTask::test_create_general_task_success

6. 并行运行（需要pytest-xdist）：
   pytest -n auto

7. 查看详细输出：
   pytest -v -s

注意事项：
- 所有测试使用内存数据库（SQLite :memory:）
- 每个测试函数独立，互不影响
- Mock数据通过fixtures自动创建和清理
- 当前employee_id约束问题需要先解决（见conftest.py的TODO）
"""
