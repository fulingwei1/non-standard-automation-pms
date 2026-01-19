# -*- coding: utf-8 -*-
"""
工作日志AI分析服务
使用AI分析工作日志内容，自动提取工作项、工时和项目关联
"""

import os
import json
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.timesheet import Timesheet
from app.models.work_log import WorkLog
from app.models.holiday import HolidayService

logger = logging.getLogger(__name__)

# AI API配置（支持多种AI服务）
ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "")
ALIBABA_MODEL = os.getenv("ALIBABA_MODEL", "qwen-plus")
ALIBABA_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

# 如果未配置AI服务，使用规则引擎作为fallback
USE_AI = bool(ALIBABA_API_KEY)


class WorkLogAIService:
    """工作日志AI分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.use_ai = USE_AI
    
    def analyze_work_log(
        self,
        content: str,
        user_id: int,
        work_date: date
    ) -> Dict[str, Any]:
        """
        分析工作日志内容，提取工作项、工时和项目关联（同步版本）
        
        Args:
            content: 工作日志内容
            user_id: 用户ID
            work_date: 工作日期
            
        Returns:
            分析结果字典，包含：
            - work_items: 工作项列表（每个包含工作内容、工时、项目ID等）
            - suggested_projects: 建议的项目列表
            - total_hours: 总工时
            - confidence: 置信度（0-1）
        """
        # 获取用户参与的项目列表
        user_projects = self._get_user_projects(user_id)
        
        if self.use_ai:
            # 使用AI分析（同步版本）
            try:
                result = self._analyze_with_ai_sync(content, user_projects, work_date)
                return result
            except Exception as e:
                logger.warning(f"AI分析失败，使用规则引擎: {str(e)}")
                # Fallback到规则引擎
                return self._analyze_with_rules(content, user_projects, work_date)
        else:
            # 使用规则引擎分析
            return self._analyze_with_rules(content, user_projects, work_date)
    
    def _get_user_projects(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户参与的项目列表
        
        Returns:
            项目列表，包含项目ID、编码、名称等信息
        """
        # 查询用户作为成员的项目
        members = self.db.query(ProjectMember).filter(
            ProjectMember.user_id == user_id,
            ProjectMember.is_active == True
        ).all()
        
        project_ids = [m.project_id for m in members]
        
        # 查询项目详情
        projects = self.db.query(Project).filter(
            Project.id.in_(project_ids),
            Project.is_active == True
        ).all()
        
        # 构建项目列表（包含历史填报频率，用于智能推荐）
        project_list = []
        for project in projects:
            # 查询用户在该项目的历史工时记录数（用于推荐排序）
            timesheet_count = self.db.query(Timesheet).filter(
                Timesheet.user_id == user_id,
                Timesheet.project_id == project.id,
                Timesheet.status == 'APPROVED'
            ).count()
            
            project_list.append({
                'id': project.id,
                'code': project.project_code,
                'name': project.project_name,
                'timesheet_count': timesheet_count,  # 历史填报次数，用于推荐排序
                'keywords': self._extract_project_keywords(project)  # 提取关键词用于匹配
            })
        
        # 按历史填报频率排序（最常用的项目排在前面）
        project_list.sort(key=lambda x: x['timesheet_count'], reverse=True)
        
        return project_list
    
    def _extract_project_keywords(self, project: Project) -> List[str]:
        """提取项目关键词用于匹配"""
        keywords = []
        
        # 项目名称关键词
        if project.project_name:
            # 提取项目名称中的关键词（去除常见词）
            name_words = project.project_name.replace('设备', '').replace('测试', '').replace('系统', '')
            keywords.extend([w for w in name_words.split() if len(w) > 1])
        
        # 项目编码
        if project.project_code:
            keywords.append(project.project_code)
        
        # 客户名称（如果有）
        if project.customer_name:
            keywords.append(project.customer_name)
        
        return keywords
    
    def _analyze_with_ai_sync(
        self,
        content: str,
        user_projects: List[Dict[str, Any]],
        work_date: date
    ) -> Dict[str, Any]:
        """
        使用AI分析工作日志内容（同步版本）
        
        Args:
            content: 工作日志内容
            user_projects: 用户参与的项目列表
            work_date: 工作日期
            
        Returns:
            分析结果
        """
        try:
            import httpx
        except ImportError:
            logger.error("httpx未安装，无法使用AI分析功能")
            raise ValueError("AI分析功能需要安装httpx库")
        
        # 构建项目列表文本（供AI参考）
        projects_text = "\n".join([
            f"- {p['code']} - {p['name']}" for p in user_projects[:10]  # 只取前10个最常用的项目
        ])
        
        # 构建AI提示词
        prompt = f"""
你是一个专业的工时分析助手。请分析以下工作日志内容，提取工作项、工时和项目关联信息。

### 工作日志内容
{content}

### 工作日期
{work_date.strftime('%Y-%m-%d')}

### 该工程师参与的项目列表（按使用频率排序）
{projects_text if projects_text else "暂无项目"}

### 分析要求
1. **提取工作项**：从工作日志中识别出具体的工作任务（如"完成机械结构设计"、"3D建模"、"测试调试"等）
2. **估算工时**：为每个工作项估算合理的工时（小时），总工时不应超过12小时
3. **匹配项目**：根据工作内容匹配到最相关的项目（从上面的项目列表中选择，或标记为"未分配项目"）
4. **识别工作类型**：判断是正常工时（NORMAL）、加班（OVERTIME）、周末（WEEKEND）还是节假日（HOLIDAY）

### 输出格式（JSON）
请严格按照以下JSON格式输出，不要添加任何其他文字：

{{
  "work_items": [
    {{
      "work_content": "具体的工作内容描述",
      "hours": 工时数（数字，如4.5）,
      "project_code": "项目编码（如PJ250108001，如果无法匹配则返回null）",
      "project_name": "项目名称（如果无法匹配则返回null）",
      "work_type": "NORMAL/OVERTIME/WEEKEND/HOLIDAY",
      "confidence": 置信度（0-1之间的数字）
    }}
  ],
  "total_hours": 总工时数,
  "confidence": 整体置信度（0-1之间的数字）,
  "analysis_notes": "分析说明（可选）"
}}

### 注意事项
- 如果工作日志中提到多个项目，应该拆分为多个工作项
- 如果工作日志中没有明确提到项目，尝试根据工作内容关键词匹配项目
- 工时估算要合理，单日总工时不应超过12小时
- 如果无法确定项目，project_code和project_name设为null
- 必须输出有效的JSON格式
"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ALIBABA_API_KEY}",
        }
        
        payload = {
            "model": ALIBABA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的工时分析助手，擅长从工作日志中提取工作项、工时和项目关联信息。请严格按照JSON格式输出结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # 降低温度，提高准确性
        }
        
        # 使用同步HTTP客户端
        with httpx.Client(timeout=30.0) as client:
            response = client.post(ALIBABA_BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                ai_response = data["choices"][0]["message"]["content"]
                
                # 解析JSON响应
                try:
                    # 尝试直接解析
                    result = json.loads(ai_response)
                except json.JSONDecodeError:
                    # 如果解析失败，尝试提取JSON部分
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        raise ValueError("AI返回的不是有效的JSON格式")
                
                # 验证和补充项目信息
                work_items = result.get('work_items', [])
                for item in work_items:
                    project_code = item.get('project_code')
                    if project_code:
                        # 查找项目ID
                        project = next(
                            (p for p in user_projects if p['code'] == project_code),
                            None
                        )
                        if project:
                            item['project_id'] = project['id']
                            item['project_name'] = project['name']
                        else:
                            # 项目编码不匹配，尝试通过名称匹配
                            project_name = item.get('project_name')
                            if project_name:
                                project = next(
                                    (p for p in user_projects if project_name in p['name'] or p['name'] in project_name),
                                    None
                                )
                                if project:
                                    item['project_id'] = project['id']
                                    item['project_code'] = project['code']
                                    item['project_name'] = project['name']
                                else:
                                    # 无法匹配，清除项目信息
                                    item['project_id'] = None
                                    item['project_code'] = None
                                    item['project_name'] = None
                    else:
                        item['project_id'] = None
                
                return result
            else:
                raise ValueError(f"AI API返回格式异常: {data}")
    
    async def _analyze_with_ai(
        self,
        content: str,
        user_projects: List[Dict[str, Any]],
        work_date: date
    ) -> Dict[str, Any]:
        """
        使用AI分析工作日志内容
        
        Args:
            content: 工作日志内容
            user_projects: 用户参与的项目列表
            work_date: 工作日期
            
        Returns:
            分析结果
        """
        import httpx
        
        # 构建项目列表文本（供AI参考）
        projects_text = "\n".join([
            f"- {p['code']} - {p['name']}" for p in user_projects[:10]  # 只取前10个最常用的项目
        ])
        
        # 构建AI提示词
        prompt = f"""
你是一个专业的工时分析助手。请分析以下工作日志内容，提取工作项、工时和项目关联信息。

### 工作日志内容
{content}

### 工作日期
{work_date.strftime('%Y-%m-%d')}

### 该工程师参与的项目列表（按使用频率排序）
{projects_text if projects_text else "暂无项目"}

### 分析要求
1. **提取工作项**：从工作日志中识别出具体的工作任务（如"完成机械结构设计"、"3D建模"、"测试调试"等）
2. **估算工时**：为每个工作项估算合理的工时（小时），总工时不应超过12小时
3. **匹配项目**：根据工作内容匹配到最相关的项目（从上面的项目列表中选择，或标记为"未分配项目"）
4. **识别工作类型**：判断是正常工时（NORMAL）、加班（OVERTIME）、周末（WEEKEND）还是节假日（HOLIDAY）

### 输出格式（JSON）
请严格按照以下JSON格式输出，不要添加任何其他文字：

{{
  "work_items": [
    {{
      "work_content": "具体的工作内容描述",
      "hours": 工时数（数字，如4.5）,
      "project_code": "项目编码（如PJ250108001，如果无法匹配则返回null）",
      "project_name": "项目名称（如果无法匹配则返回null）",
      "work_type": "NORMAL/OVERTIME/WEEKEND/HOLIDAY",
      "confidence": 置信度（0-1之间的数字）
    }}
  ],
  "total_hours": 总工时数,
  "confidence": 整体置信度（0-1之间的数字）,
  "analysis_notes": "分析说明（可选）"
}}

### 注意事项
- 如果工作日志中提到多个项目，应该拆分为多个工作项
- 如果工作日志中没有明确提到项目，尝试根据工作内容关键词匹配项目
- 工时估算要合理，单日总工时不应超过12小时
- 如果无法确定项目，project_code和project_name设为null
- 必须输出有效的JSON格式
"""
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ALIBABA_API_KEY}",
        }
        
        payload = {
            "model": ALIBABA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的工时分析助手，擅长从工作日志中提取工作项、工时和项目关联信息。请严格按照JSON格式输出结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # 降低温度，提高准确性
            "response_format": {"type": "json_object"}  # 强制JSON输出
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(ALIBABA_BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                ai_response = data["choices"][0]["message"]["content"]
                
                # 解析JSON响应
                try:
                    # 尝试直接解析
                    result = json.loads(ai_response)
                except json.JSONDecodeError:
                    # 如果解析失败，尝试提取JSON部分
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        raise ValueError("AI返回的不是有效的JSON格式")
                
                # 验证和补充项目信息
                work_items = result.get('work_items', [])
                for item in work_items:
                    project_code = item.get('project_code')
                    if project_code:
                        # 查找项目ID
                        project = next(
                            (p for p in user_projects if p['code'] == project_code),
                            None
                        )
                        if project:
                            item['project_id'] = project['id']
                            item['project_name'] = project['name']
                        else:
                            # 项目编码不匹配，尝试通过名称匹配
                            project_name = item.get('project_name')
                            if project_name:
                                project = next(
                                    (p for p in user_projects if project_name in p['name'] or p['name'] in project_name),
                                    None
                                )
                                if project:
                                    item['project_id'] = project['id']
                                    item['project_code'] = project['code']
                                    item['project_name'] = project['name']
                                else:
                                    # 无法匹配，清除项目信息
                                    item['project_id'] = None
                                    item['project_code'] = None
                                    item['project_name'] = None
                    else:
                        item['project_id'] = None
                
                return result
            else:
                raise ValueError(f"AI API返回格式异常: {data}")
    
    def _analyze_with_rules(
        self,
        content: str,
        user_projects: List[Dict[str, Any]],
        work_date: date
    ) -> Dict[str, Any]:
        """
        使用规则引擎分析工作日志内容（AI不可用时的fallback）
        
        Args:
            content: 工作日志内容
            user_projects: 用户参与的项目列表
            work_date: 工作日期
            
        Returns:
            分析结果
        """
        work_items = []
        total_hours = Decimal("0")
        
        # 1. 尝试提取工时信息（使用正则表达式）
        # 匹配模式：如"6小时"、"4.5h"、"工作8小时"等
        hour_patterns = [
            r'(\d+\.?\d*)\s*小时',
            r'(\d+\.?\d*)\s*h',
            r'工作\s*(\d+\.?\d*)\s*小时',
            r'耗时\s*(\d+\.?\d*)\s*小时',
        ]
        
        extracted_hours = []
        for pattern in hour_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    hours = float(match)
                    if 0 < hours <= 12:  # 合理的工时范围
                        extracted_hours.append(hours)
                except ValueError:
                    continue
        
        # 2. 尝试匹配项目
        matched_project = None
        for project in user_projects:
            # 检查项目编码是否在工作日志中
            if project['code'] in content:
                matched_project = project
                break
            
            # 检查项目名称关键词是否在工作日志中
            for keyword in project['keywords']:
                if keyword and keyword in content:
                    matched_project = project
                    break
            
            if matched_project:
                break
        
        # 3. 如果没有明确提到项目，使用最常用的项目
        if not matched_project and user_projects:
            matched_project = user_projects[0]  # 使用最常用的项目
        
        # 4. 判断工作类型（使用节假日服务）
        work_type = HolidayService.get_work_type(self.db, work_date)
        
        # 5. 构建工作项
        if extracted_hours:
            # 如果有明确的工时信息，使用提取的工时
            for hours in extracted_hours:
                work_items.append({
                    "work_content": content[:100],  # 截取前100字作为工作内容
                    "hours": float(hours),
                    "project_id": matched_project['id'] if matched_project else None,
                    "project_code": matched_project['code'] if matched_project else None,
                    "project_name": matched_project['name'] if matched_project else None,
                    "work_type": work_type,
                    "confidence": 0.7  # 规则引擎的置信度较低
                })
                total_hours += Decimal(str(hours))
        else:
            # 如果没有明确的工时信息，根据内容长度和复杂度估算
            # 简单规则：内容越长，工时越多（但不超过8小时）
            estimated_hours = min(8.0, max(2.0, len(content) / 50))  # 每50字约1小时，最少2小时，最多8小时
            
            work_items.append({
                "work_content": content,
                "hours": estimated_hours,
                "project_id": matched_project['id'] if matched_project else None,
                "project_code": matched_project['code'] if matched_project else None,
                "project_name": matched_project['name'] if matched_project else None,
                "work_type": work_type,
                "confidence": 0.5  # 估算的置信度更低
            })
            total_hours = Decimal(str(estimated_hours))
        
        return {
            "work_items": work_items,
            "total_hours": float(total_hours),
            "confidence": 0.6,  # 规则引擎的整体置信度
            "analysis_notes": "使用规则引擎分析（AI服务未配置）",
            "suggested_projects": [p for p in user_projects[:5]]  # 推荐前5个最常用的项目
        }
    
    def get_user_projects_for_suggestion(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户参与的项目列表（用于前端显示建议）
        
        Returns:
            项目列表，包含ID、编码、名称、历史填报次数
        """
        return self._get_user_projects(user_id)


# 便捷函数
def analyze_work_log_content(
    db: Session,
    content: str,
    user_id: int,
    work_date: date
) -> Dict[str, Any]:
    """
    分析工作日志内容的便捷函数
    
    Args:
        db: 数据库会话
        content: 工作日志内容
        user_id: 用户ID
        work_date: 工作日期
        
    Returns:
        分析结果
    """
    service = WorkLogAIService(db)
    
    # 如果是异步环境，使用await
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，使用同步方式（规则引擎）
            return service._analyze_with_rules(
                content,
                service._get_user_projects(user_id),
                work_date
            )
        else:
            # 如果事件循环未运行，可以创建新的
            return loop.run_until_complete(
                service.analyze_work_log(content, user_id, work_date)
            )
    except RuntimeError:
        # 没有事件循环，使用同步方式（规则引擎）
        return service._analyze_with_rules(
            content,
            service._get_user_projects(user_id),
            work_date
        )
