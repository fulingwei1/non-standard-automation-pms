"""
企业微信通知服务
"""
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WechatConfig:
    """企业微信配置"""
    corp_id: str  # 企业ID
    agent_id: int  # 应用ID
    secret: str  # 应用Secret
    base_url: str = "https://qyapi.weixin.qq.com/cgi-bin"


class WechatWorkService:
    """企业微信服务"""
    
    def __init__(self, config: WechatConfig):
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    def get_access_token(self) -> str:
        """获取access_token"""
        # 检查缓存的token是否有效
        if self._access_token and self._token_expires:
            if datetime.now() < self._token_expires:
                return self._access_token
        
        # 获取新token
        url = f"{self.config.base_url}/gettoken"
        params = {
            "corpid": self.config.corp_id,
            "corpsecret": self.config.secret
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                self._access_token = result["access_token"]
                # token有效期2小时，提前5分钟过期
                from datetime import timedelta
                self._token_expires = datetime.now() + timedelta(seconds=result["expires_in"] - 300)
                return self._access_token
            else:
                logger.error(f"获取access_token失败: {result}")
                raise Exception(f"获取access_token失败: {result.get('errmsg')}")
        except Exception as e:
            logger.error(f"获取access_token异常: {e}")
            raise
    
    def send_text_message(
        self,
        user_ids: List[str],
        content: str,
        safe: int = 0
    ) -> bool:
        """
        发送文本消息
        
        Args:
            user_ids: 用户ID列表
            content: 消息内容
            safe: 是否保密消息 0否 1是
        """
        access_token = self.get_access_token()
        url = f"{self.config.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": "|".join(user_ids),
            "msgtype": "text",
            "agentid": self.config.agent_id,
            "text": {
                "content": content
            },
            "safe": safe
        }
        
        return self._send_message(url, data)
    
    def send_card_message(
        self,
        user_ids: List[str],
        title: str,
        description: str,
        url: str,
        btn_txt: str = "详情"
    ) -> bool:
        """
        发送卡片消息（文本卡片）
        
        Args:
            user_ids: 用户ID列表
            title: 标题
            description: 描述（支持换行，可包含<div class="gray">灰色</div>等样式）
            url: 点击跳转链接
            btn_txt: 按钮文字
        """
        access_token = self.get_access_token()
        api_url = f"{self.config.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": "|".join(user_ids),
            "msgtype": "textcard",
            "agentid": self.config.agent_id,
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": btn_txt
            }
        }
        
        return self._send_message(api_url, data)
    
    def send_markdown_message(
        self,
        user_ids: List[str],
        content: str
    ) -> bool:
        """
        发送Markdown消息
        
        Args:
            user_ids: 用户ID列表
            content: Markdown内容
        
        Markdown支持的语法:
            标题: # 一级标题 ~ ###### 六级标题
            加粗: **bold**
            链接: [link](url)
            行内代码: `code`
            引用: > 引用文字
            字体颜色: <font color="info">绿色</font> / warning橙红 / comment灰色
        """
        access_token = self.get_access_token()
        url = f"{self.config.base_url}/message/send?access_token={access_token}"
        
        data = {
            "touser": "|".join(user_ids),
            "msgtype": "markdown",
            "agentid": self.config.agent_id,
            "markdown": {
                "content": content
            }
        }
        
        return self._send_message(url, data)
    
    def _send_message(self, url: str, data: dict) -> bool:
        """发送消息通用方法"""
        try:
            response = requests.post(
                url,
                json=data,
                timeout=10
            )
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"消息发送成功: {data.get('touser')}")
                return True
            else:
                logger.error(f"消息发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"消息发送异常: {e}")
            return False


class ProgressNotificationService:
    """进度通知服务 - 封装具体业务场景的通知"""
    
    def __init__(self, wechat_service: WechatWorkService, base_url: str):
        self.wechat = wechat_service
        self.base_url = base_url  # 系统访问地址
    
    def notify_task_assigned(
        self,
        user_id: str,
        task_name: str,
        project_name: str,
        deadline: str,
        assigner_name: str
    ):
        """
        通知任务分配
        """
        content = f"""## 📋 任务分配通知

**任务名称**: {task_name}
**所属项目**: {project_name}
**截止日期**: <font color="warning">{deadline}</font>
**分配人**: {assigner_name}

请及时处理，[点击查看详情]({self.base_url}/my-tasks)"""
        
        return self.wechat.send_markdown_message([user_id], content)
    
    def notify_task_due_soon(
        self,
        user_id: str,
        task_name: str,
        project_name: str,
        deadline: str,
        days_left: int,
        progress: float
    ):
        """
        通知任务即将到期
        """
        color = "warning" if days_left <= 1 else "comment"
        content = f"""## ⏰ 任务即将到期

**任务名称**: {task_name}
**所属项目**: {project_name}
**截止日期**: <font color="{color}">{deadline}（还剩{days_left}天）</font>
**当前进度**: {progress}%

请加快进度，[点击查看详情]({self.base_url}/my-tasks)"""
        
        return self.wechat.send_markdown_message([user_id], content)
    
    def notify_task_overdue(
        self,
        user_ids: List[str],
        task_name: str,
        project_name: str,
        deadline: str,
        overdue_days: int,
        owner_name: str
    ):
        """
        通知任务逾期
        """
        content = f"""## 🚨 任务逾期预警

**任务名称**: {task_name}
**所属项目**: {project_name}
**计划截止**: {deadline}
**已逾期**: <font color="warning">{overdue_days}天</font>
**负责人**: {owner_name}

请立即处理，[点击查看详情]({self.base_url}/projects)"""
        
        return self.wechat.send_markdown_message(user_ids, content)
    
    def notify_progress_delay(
        self,
        user_ids: List[str],
        project_name: str,
        project_code: str,
        actual_progress: float,
        plan_progress: float,
        spi: float
    ):
        """
        通知进度滞后
        """
        level = "🔴 严重滞后" if spi < 0.8 else "🟡 进度滞后"
        content = f"""## {level}

**项目**: {project_code} {project_name}
**实际进度**: {actual_progress}%
**计划进度**: {plan_progress}%
**SPI指数**: <font color="warning">{spi}</font>

请关注并采取措施，[点击查看详情]({self.base_url}/projects/{project_code})"""
        
        return self.wechat.send_markdown_message(user_ids, content)
    
    def notify_milestone_risk(
        self,
        user_ids: List[str],
        project_name: str,
        milestone_name: str,
        milestone_date: str,
        incomplete_tasks: List[str]
    ):
        """
        通知里程碑风险
        """
        tasks_text = "\n".join([f"- {t}" for t in incomplete_tasks[:5]])
        if len(incomplete_tasks) > 5:
            tasks_text += f"\n- ...等共{len(incomplete_tasks)}个任务"
        
        content = f"""## ⚠️ 里程碑风险预警

**项目**: {project_name}
**里程碑**: {milestone_name}
**计划日期**: <font color="warning">{milestone_date}</font>

**未完成任务**:
{tasks_text}

请确认能否按时达成，[点击查看详情]({self.base_url}/projects)"""
        
        return self.wechat.send_markdown_message(user_ids, content)
    
    def notify_workload_overload(
        self,
        user_id: str,
        user_name: str,
        workload_rate: float,
        task_count: int,
        manager_id: str
    ):
        """
        通知工程师负荷过高
        """
        # 通知工程师本人
        content1 = f"""## 📊 负荷预警

您本周负荷率为 <font color="warning">{workload_rate}%</font>
当前有 **{task_count}** 个任务进行中

请与上级沟通调整工作安排，[查看我的任务]({self.base_url}/my-tasks)"""
        
        self.wechat.send_markdown_message([user_id], content1)
        
        # 通知部门经理
        content2 = f"""## 📊 团队成员负荷预警

**员工**: {user_name}
**负荷率**: <font color="warning">{workload_rate}%</font>
**任务数**: {task_count}个

请关注并协助调整，[查看团队负荷]({self.base_url}/workload)"""
        
        return self.wechat.send_markdown_message([manager_id], content2)
    
    def notify_daily_summary(
        self,
        user_id: str,
        today_tasks: int,
        completed_tasks: int,
        overdue_tasks: int,
        workload_rate: float
    ):
        """
        每日工作汇总
        """
        status_emoji = "✅" if overdue_tasks == 0 else "⚠️"
        content = f"""## {status_emoji} 每日工作汇总

**今日任务**: {today_tasks}个
**已完成**: <font color="info">{completed_tasks}个</font>
**已逾期**: <font color="warning">{overdue_tasks}个</font>
**本周负荷**: {workload_rate}%

[查看详情]({self.base_url}/my-tasks) | [填报工时]({self.base_url}/timesheet)"""
        
        return self.wechat.send_markdown_message([user_id], content)
    
    def notify_weekly_report_reminder(
        self,
        user_id: str,
        project_name: str
    ):
        """
        周报提醒
        """
        content = f"""## 📝 周报提醒

项目 **{project_name}** 本周进度报告待编写

请在今日下班前完成，[开始编写]({self.base_url}/reports/weekly)"""
        
        return self.wechat.send_markdown_message([user_id], content)


# ============== 使用示例 ==============

def get_notification_service() -> ProgressNotificationService:
    """获取通知服务实例"""
    config = WechatConfig(
        corp_id="your_corp_id",  # 从配置文件读取
        agent_id=1000002,
        secret="your_secret"
    )
    wechat = WechatWorkService(config)
    return ProgressNotificationService(
        wechat_service=wechat,
        base_url="https://your-domain.com"
    )


# ============== Celery 异步任务 ==============

# from celery import shared_task
# 
# @shared_task
# def send_task_assigned_notification(user_id, task_name, project_name, deadline, assigner_name):
#     """异步发送任务分配通知"""
#     service = get_notification_service()
#     service.notify_task_assigned(user_id, task_name, project_name, deadline, assigner_name)
# 
# @shared_task
# def check_and_send_overdue_alerts():
#     """定时任务：检查并发送逾期预警"""
#     # 查询所有逾期任务
#     # 发送通知
#     pass
# 
# @shared_task  
# def send_daily_summary():
#     """定时任务：发送每日汇总（每天18:00）"""
#     pass
