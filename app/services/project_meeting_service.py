# -*- coding: utf-8 -*-
"""
项目会议关联服务
支持会议与项目的关联和查询
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, JSON

from app.models.management_rhythm import StrategicMeeting, MeetingActionItem
from app.models.project import Project


class ProjectMeetingService:
    """项目会议服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_project_meetings(
        self,
        project_id: int,
        status: Optional[str] = None,
        rhythm_level: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[StrategicMeeting]:
        """
        获取项目关联的会议列表
        
        Args:
            project_id: 项目ID
            status: 会议状态（可选）
            rhythm_level: 节律层级（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            
        Returns:
            会议列表
        """
        # 查询主项目关联的会议
        query1 = self.db.query(StrategicMeeting).filter(
            StrategicMeeting.project_id == project_id
        )
        
        # 查询多项目关联的会议（通过 related_project_ids JSON字段）
        # 注意：这里需要根据数据库类型使用不同的JSON查询方式
        # MySQL 5.7+ 使用 JSON_CONTAINS
        # SQLite 需要字符串匹配或使用 JSON1 扩展
        query2 = self.db.query(StrategicMeeting).filter(
            StrategicMeeting.related_project_ids.isnot(None)
        )
        
        # 合并查询结果
        meetings = []
        meeting_ids = set()
        
        # 处理主项目关联
        if status:
            query1 = query1.filter(StrategicMeeting.status == status)
        if rhythm_level:
            query1 = query1.filter(StrategicMeeting.rhythm_level == rhythm_level)
        if start_date:
            query1 = query1.filter(StrategicMeeting.meeting_date >= start_date)
        if end_date:
            query1 = query1.filter(StrategicMeeting.meeting_date <= end_date)
        
        for meeting in query1.all():
            if meeting.id not in meeting_ids:
                meetings.append(meeting)
                meeting_ids.add(meeting.id)
        
        # 处理多项目关联（通过 related_project_ids）
        for meeting in query2.all():
            if meeting.id in meeting_ids:
                continue
            
            related_ids = meeting.related_project_ids
            if related_ids and isinstance(related_ids, list):
                if project_id in related_ids:
                    # 应用筛选条件
                    if status and meeting.status != status:
                        continue
                    if rhythm_level and meeting.rhythm_level != rhythm_level:
                        continue
                    if start_date and meeting.meeting_date < start_date:
                        continue
                    if end_date and meeting.meeting_date > end_date:
                        continue
                    
                    meetings.append(meeting)
                    meeting_ids.add(meeting.id)
        
        # 按日期排序
        meetings.sort(key=lambda m: m.meeting_date, reverse=True)
        
        return meetings
    
    def link_meeting_to_project(
        self,
        meeting_id: int,
        project_id: int,
        is_primary: bool = False
    ) -> bool:
        """
        将会议关联到项目
        
        Args:
            meeting_id: 会议ID
            project_id: 项目ID
            is_primary: 是否设为主项目（如果为True，设置project_id；否则添加到related_project_ids）
            
        Returns:
            是否成功
        """
        meeting = self.db.query(StrategicMeeting).filter(
            StrategicMeeting.id == meeting_id
        ).first()
        
        if not meeting:
            return False
        
        if is_primary:
            # 设为主项目
            meeting.project_id = project_id
        else:
            # 添加到多项目关联列表
            related_ids = meeting.related_project_ids or []
            if not isinstance(related_ids, list):
                related_ids = []
            
            if project_id not in related_ids:
                related_ids.append(project_id)
                meeting.related_project_ids = related_ids
        
        self.db.commit()
        return True
    
    def unlink_meeting_from_project(
        self,
        meeting_id: int,
        project_id: int
    ) -> bool:
        """
        取消会议与项目的关联
        
        Args:
            meeting_id: 会议ID
            project_id: 项目ID
            
        Returns:
            是否成功
        """
        meeting = self.db.query(StrategicMeeting).filter(
            StrategicMeeting.id == meeting_id
        ).first()
        
        if not meeting:
            return False
        
        # 如果是主项目，清空
        if meeting.project_id == project_id:
            meeting.project_id = None
        
        # 从多项目关联列表中移除
        related_ids = meeting.related_project_ids or []
        if isinstance(related_ids, list) and project_id in related_ids:
            related_ids.remove(project_id)
            meeting.related_project_ids = related_ids if related_ids else None
        
        self.db.commit()
        return True
    
    def get_project_meeting_statistics(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取项目会议统计信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            统计信息字典
        """
        meetings = self.get_project_meetings(project_id)
        
        total_meetings = len(meetings)
        completed_meetings = len([m for m in meetings if m.status == 'COMPLETED'])
        scheduled_meetings = len([m for m in meetings if m.status == 'SCHEDULED'])
        cancelled_meetings = len([m for m in meetings if m.status == 'CANCELLED'])
        
        # 统计行动项
        total_action_items = 0
        completed_action_items = 0
        for meeting in meetings:
            action_items = self.db.query(MeetingActionItem).filter(
                MeetingActionItem.meeting_id == meeting.id
            ).all()
            total_action_items += len(action_items)
            completed_action_items += len([
                ai for ai in action_items 
                if ai.status == 'COMPLETED'
            ])
        
        # 按层级统计
        by_level = {}
        for meeting in meetings:
            level = meeting.rhythm_level
            if level not in by_level:
                by_level[level] = {'total': 0, 'completed': 0}
            by_level[level]['total'] += 1
            if meeting.status == 'COMPLETED':
                by_level[level]['completed'] += 1
        
        return {
            'total_meetings': total_meetings,
            'completed_meetings': completed_meetings,
            'scheduled_meetings': scheduled_meetings,
            'cancelled_meetings': cancelled_meetings,
            'completion_rate': (
                completed_meetings / total_meetings * 100 
                if total_meetings > 0 else 0
            ),
            'total_action_items': total_action_items,
            'completed_action_items': completed_action_items,
            'action_completion_rate': (
                completed_action_items / total_action_items * 100
                if total_action_items > 0 else 0
            ),
            'by_level': by_level
        }
