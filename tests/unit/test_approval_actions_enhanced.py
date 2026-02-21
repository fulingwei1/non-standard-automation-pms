# -*- coding: utf-8 -*-
"""
ApprovalActionsMixin 增强单元测试
覆盖所有核心方法：add_cc, withdraw, terminate, remind, add_comment
目标覆盖率：70%+
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from app.services.approval_engine.engine.actions import ApprovalActionsMixin
from app.models.approval import (
    ApprovalInstance,
    ApprovalTask,
    ApprovalCarbonCopy,
    ApprovalComment,
)
from app.models.user import User


@pytest.fixture
def db_mock():
    """数据库session mock"""
    mock = MagicMock()
    # 确保commit和flush能正常调用
    mock.commit.return_value = None
    mock.flush.return_value = None
    return mock


@pytest.fixture
def actions_service(db_mock):
    """ApprovalActionsMixin实例（混入到测试类中）"""
    class TestService(ApprovalActionsMixin):
        def __init__(self, db):
            self.db = db
            self.executor = MagicMock()
            self.notify = MagicMock()
            # Mock内部方法
            self._log_action = MagicMock()
            self._get_affected_user_ids = MagicMock(return_value=[1, 2, 3])
            self._call_adapter_callback = MagicMock()
    
    return TestService(db_mock)


@pytest.fixture
def sample_user():
    """示例用户对象"""
    user = MagicMock(spec=User)
    user.id = 100
    user.username = "zhangsan"
    user.real_name = "张三"
    return user


@pytest.fixture
def sample_operator():
    """示例操作人"""
    operator = MagicMock(spec=User)
    operator.id = 200
    operator.username = "lisi"
    operator.real_name = "李四"
    return operator


@pytest.fixture
def sample_instance():
    """示例审批实例"""
    instance = MagicMock(spec=ApprovalInstance)
    instance.id = 1
    instance.instance_no = "AP240101001"
    instance.template_code = "ECN_APPROVAL"
    instance.status = "PENDING"
    instance.initiator_id = 100
    instance.current_node_id = 10
    instance.completed_at = None
    return instance


@pytest.fixture
def sample_task():
    """示例审批任务"""
    task = MagicMock(spec=ApprovalTask)
    task.id = 50
    task.instance_id = 1
    task.status = "PENDING"
    task.approver_id = 200
    task.remind_count = 0
    task.reminded_at = None
    return task


# ================================
# add_cc 测试用例 (6个)
# ================================

class TestAddCC:
    """测试加抄送功能"""
    
    def test_add_cc_success(self, actions_service, db_mock, sample_instance, sample_operator):
        """测试正常加抄送流程"""
        # 准备查询结果
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_operator
        
        db_mock.query.side_effect = [instance_query, user_query]
        
        # 准备抄送记录
        cc_record1 = MagicMock(spec=ApprovalCarbonCopy)
        cc_record1.id = 1
        cc_record1.user_id = 301
        
        cc_record2 = MagicMock(spec=ApprovalCarbonCopy)
        cc_record2.id = 2
        cc_record2.user_id = 302
        
        actions_service.executor.create_cc_records.return_value = [cc_record1, cc_record2]
        
        # 执行
        result = actions_service.add_cc(
            instance_id=1,
            operator_id=200,
            cc_user_ids=[301, 302]
        )
        
        # 验证
        assert len(result) == 2
        assert result[0].user_id == 301
        assert result[1].user_id == 302
        
        # 验证executor调用
        actions_service.executor.create_cc_records.assert_called_once_with(
            instance=sample_instance,
            node_id=10,
            cc_user_ids=[301, 302],
            cc_source="APPROVER",
            added_by=200
        )
        
        # 验证日志记录
        actions_service._log_action.assert_called_once()
        log_call = actions_service._log_action.call_args
        assert log_call[1]['action'] == 'ADD_CC'
        assert log_call[1]['operator_id'] == 200
        
        # 验证通知发送
        assert actions_service.notify.notify_cc.call_count == 2
        actions_service.notify.notify_cc.assert_any_call(cc_record1)
        actions_service.notify.notify_cc.assert_any_call(cc_record2)
        
        # 验证提交
        db_mock.commit.assert_called_once()
    
    def test_add_cc_instance_not_found(self, actions_service, db_mock):
        """测试审批实例不存在"""
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_mock.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            actions_service.add_cc(
                instance_id=999,
                operator_id=200,
                cc_user_ids=[301]
            )
        
        assert "审批实例不存在" in str(exc_info.value)
        db_mock.commit.assert_not_called()
    
    def test_add_cc_empty_cc_list(self, actions_service, db_mock, sample_instance, sample_operator):
        """测试空的抄送人列表"""
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_operator
        
        db_mock.query.side_effect = [instance_query, user_query]
        
        actions_service.executor.create_cc_records.return_value = []
        
        result = actions_service.add_cc(
            instance_id=1,
            operator_id=200,
            cc_user_ids=[]
        )
        
        assert len(result) == 0
        assert actions_service.notify.notify_cc.call_count == 0
        db_mock.commit.assert_called_once()
    
    def test_add_cc_operator_not_found(self, actions_service, db_mock, sample_instance):
        """测试操作人不存在（仍应继续执行）"""
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = None  # 操作人不存在
        
        db_mock.query.side_effect = [instance_query, user_query]
        
        cc_record = MagicMock(spec=ApprovalCarbonCopy)
        actions_service.executor.create_cc_records.return_value = [cc_record]
        
        result = actions_service.add_cc(
            instance_id=1,
            operator_id=999,
            cc_user_ids=[301]
        )
        
        # 应该继续执行
        assert len(result) == 1
        db_mock.commit.assert_called_once()
    
    def test_add_cc_multiple_users(self, actions_service, db_mock, sample_instance, sample_operator):
        """测试批量添加多个抄送人"""
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_operator
        
        db_mock.query.side_effect = [instance_query, user_query]
        
        # 创建5个抄送记录
        cc_records = [MagicMock(spec=ApprovalCarbonCopy, id=i, user_id=300+i) for i in range(5)]
        actions_service.executor.create_cc_records.return_value = cc_records
        
        result = actions_service.add_cc(
            instance_id=1,
            operator_id=200,
            cc_user_ids=[301, 302, 303, 304, 305]
        )
        
        assert len(result) == 5
        assert actions_service.notify.notify_cc.call_count == 5
    
    def test_add_cc_with_operator_real_name(self, actions_service, db_mock, sample_instance):
        """测试带有真实姓名的操作人"""
        operator = MagicMock(spec=User)
        operator.id = 200
        operator.username = "admin"
        operator.real_name = "管理员"
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = operator
        
        db_mock.query.side_effect = [instance_query, user_query]
        
        actions_service.executor.create_cc_records.return_value = []
        
        actions_service.add_cc(
            instance_id=1,
            operator_id=200,
            cc_user_ids=[]
        )
        
        # 验证日志记录使用了真实姓名
        log_call = actions_service._log_action.call_args
        assert log_call[1]['operator_name'] == "管理员"


# ================================
# withdraw 测试用例 (7个)
# ================================

class TestWithdraw:
    """测试撤回审批功能"""
    
    def test_withdraw_success_pending(self, actions_service, db_mock, sample_instance, sample_user):
        """测试正常撤回待审批状态"""
        sample_instance.status = "PENDING"
        sample_instance.initiator_id = 100
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        # Mock任务更新查询
        task_query = MagicMock()
        task_query.filter.return_value.update.return_value = 2  # 更新了2个任务
        
        db_mock.query.side_effect = [instance_query, user_query, task_query]
        
        # 执行
        result = actions_service.withdraw(
            instance_id=1,
            initiator_id=100,
            comment="测试撤回"
        )
        
        # 验证实例状态更新
        assert result.status == "CANCELLED"
        assert result.completed_at is not None
        
        # 验证任务被取消
        task_query.filter.return_value.update.assert_called_once_with(
            {"status": "CANCELLED"},
            synchronize_session=False
        )
        
        # 验证回调被调用
        actions_service._call_adapter_callback.assert_called_once_with(
            sample_instance,
            "on_withdrawn"
        )
        
        # 验证日志记录
        log_call = actions_service._log_action.call_args
        assert log_call[1]['action'] == 'WITHDRAW'
        assert log_call[1]['comment'] == "测试撤回"
        assert log_call[1]['before_status'] == "PENDING"
        assert log_call[1]['after_status'] == "CANCELLED"
        
        # 验证通知
        actions_service.notify.notify_withdrawn.assert_called_once()
        
        db_mock.commit.assert_called_once()
    
    def test_withdraw_success_draft(self, actions_service, db_mock, sample_instance, sample_user):
        """测试撤回草稿状态"""
        sample_instance.status = "DRAFT"
        sample_instance.initiator_id = 100
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        task_query = MagicMock()
        db_mock.query.side_effect = [instance_query, user_query, task_query]
        
        result = actions_service.withdraw(
            instance_id=1,
            initiator_id=100
        )
        
        assert result.status == "CANCELLED"
        db_mock.commit.assert_called_once()
    
    def test_withdraw_instance_not_found(self, actions_service, db_mock):
        """测试撤回不存在的实例"""
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_mock.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            actions_service.withdraw(
                instance_id=999,
                initiator_id=100
            )
        
        assert "审批实例不存在" in str(exc_info.value)
        db_mock.commit.assert_not_called()
    
    def test_withdraw_not_initiator(self, actions_service, db_mock, sample_instance):
        """测试非发起人尝试撤回"""
        sample_instance.initiator_id = 100
        
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_instance
        db_mock.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            actions_service.withdraw(
                instance_id=1,
                initiator_id=999  # 不是发起人
            )
        
        assert "只有发起人可以撤回审批" in str(exc_info.value)
        db_mock.commit.assert_not_called()
    
    def test_withdraw_invalid_status(self, actions_service, db_mock, sample_instance):
        """测试不允许撤回的状态"""
        sample_instance.status = "APPROVED"  # 已批准，不能撤回
        sample_instance.initiator_id = 100
        
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_instance
        db_mock.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            actions_service.withdraw(
                instance_id=1,
                initiator_id=100
            )
        
        assert "当前状态不允许撤回" in str(exc_info.value)
        db_mock.commit.assert_not_called()
    
    def test_withdraw_without_comment(self, actions_service, db_mock, sample_instance, sample_user):
        """测试不带评论的撤回"""
        sample_instance.status = "PENDING"
        sample_instance.initiator_id = 100
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        task_query = MagicMock()
        db_mock.query.side_effect = [instance_query, user_query, task_query]
        
        result = actions_service.withdraw(
            instance_id=1,
            initiator_id=100
            # 不传comment参数
        )
        
        assert result.status == "CANCELLED"
        log_call = actions_service._log_action.call_args
        assert log_call[1]['comment'] is None
    
    def test_withdraw_affected_users_notification(self, actions_service, db_mock, sample_instance, sample_user):
        """测试撤回时获取受影响用户并通知"""
        sample_instance.status = "PENDING"
        sample_instance.initiator_id = 100
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        task_query = MagicMock()
        db_mock.query.side_effect = [instance_query, user_query, task_query]
        
        # Mock返回受影响的用户ID
        actions_service._get_affected_user_ids.return_value = [201, 202, 203]
        
        actions_service.withdraw(
            instance_id=1,
            initiator_id=100
        )
        
        # 验证获取受影响用户
        actions_service._get_affected_user_ids.assert_called_once_with(sample_instance)
        
        # 验证通知包含受影响用户
        notify_call = actions_service.notify.notify_withdrawn.call_args
        assert notify_call[0][0] == sample_instance
        assert notify_call[0][1] == [201, 202, 203]


# ================================
# terminate 测试用例 (6个)
# ================================

class TestTerminate:
    """测试终止审批功能"""
    
    def test_terminate_success(self, actions_service, db_mock, sample_instance, sample_operator):
        """测试正常终止审批流程"""
        sample_instance.status = "PENDING"
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_operator
        
        task_query = MagicMock()
        task_query.filter.return_value.update.return_value = 3
        
        db_mock.query.side_effect = [instance_query, user_query, task_query]
        
        # 执行
        result = actions_service.terminate(
            instance_id=1,
            operator_id=200,
            comment="紧急终止"
        )
        
        # 验证实例状态更新
        assert result.status == "TERMINATED"
        assert result.completed_at is not None
        
        # 验证任务被取消
        task_query.filter.return_value.update.assert_called_once()
        
        # 验证回调
        actions_service._call_adapter_callback.assert_called_once_with(
            sample_instance,
            "on_terminated"
        )
        
        # 验证日志
        log_call = actions_service._log_action.call_args
        assert log_call[1]['action'] == 'TERMINATE'
        assert log_call[1]['comment'] == "紧急终止"
        assert log_call[1]['operator_id'] == 200
        
        db_mock.commit.assert_called_once()
    
    def test_terminate_instance_not_found(self, actions_service, db_mock):
        """测试终止不存在的实例"""
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_mock.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            actions_service.terminate(
                instance_id=999,
                operator_id=200,
                comment="终止"
            )
        
        assert "审批实例不存在" in str(exc_info.value)
        db_mock.commit.assert_not_called()
    
    def test_terminate_invalid_status(self, actions_service, db_mock, sample_instance):
        """测试不允许终止的状态"""
        sample_instance.status = "APPROVED"  # 已完成，不能终止
        
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_instance
        db_mock.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            actions_service.terminate(
                instance_id=1,
                operator_id=200,
                comment="终止"
            )
        
        assert "当前状态不允许终止" in str(exc_info.value)
        db_mock.commit.assert_not_called()
    
    def test_terminate_operator_without_real_name(self, actions_service, db_mock, sample_instance):
        """测试操作人没有真实姓名"""
        sample_instance.status = "PENDING"
        
        operator = MagicMock(spec=User)
        operator.id = 200
        operator.username = "admin"
        operator.real_name = None  # 没有真实姓名
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = operator
        
        task_query = MagicMock()
        db_mock.query.side_effect = [instance_query, user_query, task_query]
        
        actions_service.terminate(
            instance_id=1,
            operator_id=200,
            comment="终止"
        )
        
        # 验证使用username作为操作人名称
        log_call = actions_service._log_action.call_args
        assert log_call[1]['operator_name'] == "admin"
    
    def test_terminate_operator_not_found(self, actions_service, db_mock, sample_instance):
        """测试操作人不存在（仍应执行）"""
        sample_instance.status = "PENDING"
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = None  # 操作人不存在
        
        task_query = MagicMock()
        db_mock.query.side_effect = [instance_query, user_query, task_query]
        
        result = actions_service.terminate(
            instance_id=1,
            operator_id=999,
            comment="终止"
        )
        
        # 应该继续执行
        assert result.status == "TERMINATED"
        db_mock.commit.assert_called_once()
    
    def test_terminate_updates_all_pending_tasks(self, actions_service, db_mock, sample_instance, sample_operator):
        """测试终止时更新所有待处理任务"""
        sample_instance.status = "PENDING"
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_operator
        
        # Mock任务更新，返回更新数量
        task_query = MagicMock()
        task_filter = MagicMock()
        task_query.filter.return_value = task_filter
        task_filter.update.return_value = 5  # 更新了5个任务
        
        db_mock.query.side_effect = [instance_query, user_query, task_query]
        
        actions_service.terminate(
            instance_id=1,
            operator_id=200,
            comment="终止"
        )
        
        # 验证查询条件正确
        assert task_query.filter.call_count >= 1


# ================================
# remind 测试用例 (6个)
# ================================

class TestRemind:
    """测试催办功能"""
    
    def test_remind_success(self, actions_service, db_mock, sample_task, sample_operator):
        """测试正常催办流程"""
        sample_task.remind_count = 0
        
        task_query = MagicMock()
        task_query.filter.return_value.first.return_value = sample_task
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_operator
        
        db_mock.query.side_effect = [task_query, user_query]
        
        # 执行
        result = actions_service.remind(
            task_id=50,
            reminder_id=200
        )
        
        # 验证返回值
        assert result is True
        
        # 验证催办次数增加
        assert sample_task.remind_count == 1
        assert sample_task.reminded_at is not None
        
        # 验证日志记录
        log_call = actions_service._log_action.call_args
        assert log_call[1]['action'] == 'REMIND'
        assert log_call[1]['task_id'] == 50
        assert log_call[1]['operator_id'] == 200
        
        # 验证通知发送
        actions_service.notify.notify_remind.assert_called_once_with(
            sample_task,
            reminder_id=200,
            reminder_name="李四"
        )
        
        db_mock.commit.assert_called_once()
    
    def test_remind_multiple_times(self, actions_service, db_mock, sample_task, sample_operator):
        """测试多次催办"""
        sample_task.remind_count = 2  # 已经催办过2次
        
        task_query = MagicMock()
        task_query.filter.return_value.first.return_value = sample_task
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_operator
        
        db_mock.query.side_effect = [task_query, user_query]
        
        actions_service.remind(
            task_id=50,
            reminder_id=200
        )
        
        # 验证催办次数递增
        assert sample_task.remind_count == 3
    
    def test_remind_task_not_found(self, actions_service, db_mock):
        """测试催办不存在的任务"""
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = None
        db_mock.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            actions_service.remind(
                task_id=999,
                reminder_id=200
            )
        
        assert "任务不存在" in str(exc_info.value)
        db_mock.commit.assert_not_called()
    
    def test_remind_non_pending_task(self, actions_service, db_mock, sample_task):
        """测试催办非待处理任务"""
        sample_task.status = "APPROVED"  # 已处理
        
        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = sample_task
        db_mock.query.return_value = query_mock
        
        with pytest.raises(ValueError) as exc_info:
            actions_service.remind(
                task_id=50,
                reminder_id=200
            )
        
        assert "只能催办待处理的任务" in str(exc_info.value)
        db_mock.commit.assert_not_called()
    
    def test_remind_first_time(self, actions_service, db_mock, sample_task, sample_operator):
        """测试首次催办（remind_count为None）"""
        sample_task.remind_count = None  # 首次催办
        
        task_query = MagicMock()
        task_query.filter.return_value.first.return_value = sample_task
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_operator
        
        db_mock.query.side_effect = [task_query, user_query]
        
        actions_service.remind(
            task_id=50,
            reminder_id=200
        )
        
        # 验证从None变为1
        assert sample_task.remind_count == 1
    
    def test_remind_reminder_without_real_name(self, actions_service, db_mock, sample_task):
        """测试催办人没有真实姓名"""
        sample_task.remind_count = 0
        
        reminder = MagicMock(spec=User)
        reminder.id = 200
        reminder.username = "reminder_user"
        reminder.real_name = None
        
        task_query = MagicMock()
        task_query.filter.return_value.first.return_value = sample_task
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = reminder
        
        db_mock.query.side_effect = [task_query, user_query]
        
        actions_service.remind(
            task_id=50,
            reminder_id=200
        )
        
        # 验证通知使用username
        notify_call = actions_service.notify.notify_remind.call_args
        assert notify_call[1]['reminder_name'] == "reminder_user"


# ================================
# add_comment 测试用例 (10个)
# ================================

class TestAddComment:
    """测试添加评论功能"""
    
    def test_add_comment_simple(self, actions_service, db_mock, sample_user):
        """测试简单添加评论"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = MagicMock(spec=ApprovalInstance)
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        # 执行
        result = actions_service.add_comment(
            instance_id=1,
            user_id=100,
            content="测试评论"
        )
        
        # 验证添加到数据库
        db_mock.add.assert_called_once()
        added_comment = db_mock.add.call_args[0][0]
        assert added_comment.instance_id == 1
        assert added_comment.user_id == 100
        assert added_comment.content == "测试评论"
        assert added_comment.user_name == "张三"
        
        # 验证flush
        db_mock.flush.assert_called_once()
        
        # 验证日志
        log_call = actions_service._log_action.call_args
        assert log_call[1]['action'] == 'COMMENT'
        assert log_call[1]['comment'] == "测试评论"
        
        db_mock.commit.assert_called_once()
    
    def test_add_comment_with_reply(self, actions_service, db_mock, sample_user):
        """测试回复评论"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = MagicMock(spec=ApprovalInstance)
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        result = actions_service.add_comment(
            instance_id=1,
            user_id=100,
            content="回复内容",
            parent_id=10,
            reply_to_user_id=200
        )
        
        added_comment = db_mock.add.call_args[0][0]
        assert added_comment.parent_id == 10
        assert added_comment.reply_to_user_id == 200
    
    def test_add_comment_with_mentions(self, actions_service, db_mock, sample_user, sample_instance):
        """测试@提及用户"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        mentioned_users = [201, 202, 203]
        
        result = actions_service.add_comment(
            instance_id=1,
            user_id=100,
            content="@所有人 请关注",
            mentioned_user_ids=mentioned_users
        )
        
        added_comment = db_mock.add.call_args[0][0]
        assert added_comment.mentioned_user_ids == mentioned_users
        
        # 验证发送通知
        actions_service.notify.notify_comment.assert_called_once()
        notify_call = actions_service.notify.notify_comment.call_args
        assert notify_call[0][0] == sample_instance
        assert notify_call[1]['mentioned_user_ids'] == mentioned_users
    
    def test_add_comment_with_attachments(self, actions_service, db_mock, sample_user):
        """测试带附件的评论"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = MagicMock(spec=ApprovalInstance)
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        attachments = [
            {"name": "file1.pdf", "url": "http://example.com/file1.pdf"},
            {"name": "file2.jpg", "url": "http://example.com/file2.jpg"}
        ]
        
        result = actions_service.add_comment(
            instance_id=1,
            user_id=100,
            content="请查看附件",
            attachments=attachments
        )
        
        added_comment = db_mock.add.call_args[0][0]
        assert added_comment.attachments == attachments
    
    def test_add_comment_user_without_real_name(self, actions_service, db_mock):
        """测试用户没有真实姓名"""
        user = MagicMock(spec=User)
        user.id = 100
        user.username = "testuser"
        user.real_name = None
        
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = MagicMock(spec=ApprovalInstance)
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        actions_service.add_comment(
            instance_id=1,
            user_id=100,
            content="评论"
        )
        
        added_comment = db_mock.add.call_args[0][0]
        assert added_comment.user_name == "testuser"
    
    def test_add_comment_user_not_found(self, actions_service, db_mock):
        """测试用户不存在（仍应执行）"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = None
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = MagicMock(spec=ApprovalInstance)
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        actions_service.add_comment(
            instance_id=1,
            user_id=999,
            content="评论"
        )
        
        added_comment = db_mock.add.call_args[0][0]
        assert added_comment.user_name is None
        db_mock.commit.assert_called_once()
    
    def test_add_comment_instance_not_found_no_notification(self, actions_service, db_mock, sample_user):
        """测试实例不存在时不发送通知"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = None  # 实例不存在
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        actions_service.add_comment(
            instance_id=999,
            user_id=100,
            content="评论",
            mentioned_user_ids=[201]
        )
        
        # 应该不发送通知
        actions_service.notify.notify_comment.assert_not_called()
        db_mock.commit.assert_called_once()
    
    def test_add_comment_no_mentions_no_notification(self, actions_service, db_mock, sample_user, sample_instance):
        """测试没有@提及时不发送通知"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        actions_service.add_comment(
            instance_id=1,
            user_id=100,
            content="普通评论"
            # 不传mentioned_user_ids
        )
        
        # 不应发送通知
        actions_service.notify.notify_comment.assert_not_called()
    
    def test_add_comment_empty_mentions_no_notification(self, actions_service, db_mock, sample_user, sample_instance):
        """测试空的@提及列表不发送通知"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        actions_service.add_comment(
            instance_id=1,
            user_id=100,
            content="评论",
            mentioned_user_ids=[]  # 空列表
        )
        
        # 不应发送通知
        actions_service.notify.notify_comment.assert_not_called()
    
    def test_add_comment_complete_flow(self, actions_service, db_mock, sample_user, sample_instance):
        """测试完整的评论流程（所有参数）"""
        user_query = MagicMock()
        user_query.filter.return_value.first.return_value = sample_user
        
        instance_query = MagicMock()
        instance_query.filter.return_value.first.return_value = sample_instance
        
        db_mock.query.side_effect = [user_query, instance_query]
        
        result = actions_service.add_comment(
            instance_id=1,
            user_id=100,
            content="完整的评论内容",
            parent_id=5,
            reply_to_user_id=200,
            mentioned_user_ids=[201, 202],
            attachments=[{"name": "doc.pdf", "url": "http://example.com/doc.pdf"}]
        )
        
        # 验证所有字段
        added_comment = db_mock.add.call_args[0][0]
        assert added_comment.instance_id == 1
        assert added_comment.user_id == 100
        assert added_comment.content == "完整的评论内容"
        assert added_comment.parent_id == 5
        assert added_comment.reply_to_user_id == 200
        assert added_comment.mentioned_user_ids == [201, 202]
        assert len(added_comment.attachments) == 1
        
        # 验证通知
        actions_service.notify.notify_comment.assert_called_once()
        
        # 验证提交
        db_mock.commit.assert_called_once()
