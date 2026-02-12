# -*- coding: utf-8 -*-
"""
AI提示词构建模块
提供AI分析提示词的构建和响应解析功能
"""

import json
import re
from datetime import date
from typing import Any, Dict, List



class AIPromptMixin:
    """AI提示词构建功能混入类"""

    def _build_ai_prompt(
        self,
        content: str,
        user_projects: List[Dict[str, Any]],
        work_date: date
    ) -> str:
        """构建AI分析提示词"""
        # 构建项目列表文本（供AI参考）
        projects_text = "\n".join([
            f"- {p['code']} - {p['name']}" for p in user_projects[:10]  # 只取前10个最常用的项目
        ])

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
        return prompt

    def _parse_ai_response(
        self,
        ai_response: str,
        user_projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """解析AI响应并补充项目信息"""
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
