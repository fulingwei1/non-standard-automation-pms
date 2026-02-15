"""
PM介入时机判断API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from app.services.pm_involvement_service import PMInvolvementService


router = APIRouter()


class ProjectDataInput(BaseModel):
    """项目数据输入"""
    项目金额: float = Field(..., description="项目金额（万元）", ge=0)
    项目类型: str = Field(..., description="项目类型（如：SMT贴片生产线）")
    行业: str = Field(..., description="行业（如：汽车电子）")
    是否首次做: bool = Field(False, description="是否首次承接该类型项目")
    历史相似项目数: int = Field(0, description="历史相似项目数量", ge=0)
    失败项目数: int = Field(0, description="相似项目失败数量", ge=0)
    是否有标准方案: bool = Field(False, description="是否有标准化方案模板")
    技术创新点: List[str] = Field(default_factory=list, description="技术创新点列表")


class PMInvolvementResult(BaseModel):
    """PM介入判断结果"""
    建议: str = Field(..., description="PM提前介入 或 PM签约后介入")
    介入阶段: str = Field(..., description="介入阶段说明")
    风险等级: str = Field(..., description="高 或 低")
    风险因素数: int = Field(..., description="风险因素数量")
    原因: List[str] = Field(..., description="原因列表")
    下一步行动: List[str] = Field(..., description="建议的下一步行动")
    需要PM审核: bool = Field(..., description="是否需要PM审核")
    紧急程度: str = Field(..., description="高/中/低")


@router.post("/judge-pm-involvement", response_model=PMInvolvementResult, summary="判断PM介入时机")
async def judge_pm_involvement(project_data: ProjectDataInput):
    """
    判断PM介入时机
    
    根据项目数据自动判断是提前介入还是签约后介入
    
    **判断规则**（符哥2026-02-15确认）：
    - 大项目（≥100万）
    - 以前没做过
    - 有失败经验
    - 相似项目<3个
    - 无标准方案
    - 技术创新
    
    满足 ≥2个 → PM提前介入
    """
    try:
        result = PMInvolvementService.judge_pm_involvement_timing(project_data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"判断失败：{str(e)}")


@router.get("/similar-projects/{project_type}", summary="查询相似项目")
async def get_similar_projects(project_type: str, industry: Optional[str] = None):
    """
    查询历史相似项目数量
    
    返回：
    - 总数
    - 成功数
    - 失败数
    - 成功率
    """
    try:
        result = PMInvolvementService.get_similar_project_count(project_type, industry or "")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/check-standard-solution/{project_type}", summary="检查标准方案")
async def check_standard_solution(project_type: str):
    """
    检查是否有标准方案模板
    """
    try:
        has_solution = PMInvolvementService.check_has_standard_solution(project_type)
        return {
            "项目类型": project_type,
            "有标准方案": has_solution
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.post("/auto-judge/{ticket_id}", response_model=PMInvolvementResult, summary="自动判断（从工单）")
async def auto_judge_from_ticket(ticket_id: int):
    """
    从售前工单自动判断PM介入时机
    
    自动获取工单信息并判断
    """
    try:
        result = PMInvolvementService.auto_judge_from_ticket(ticket_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"判断失败：{str(e)}")


@router.post("/generate-notification", summary="生成通知消息")
async def generate_notification(
    result: PMInvolvementResult,
    ticket_info: Dict
):
    """
    生成PMO通知消息
    
    Args:
        result: 判断结果
        ticket_info: 工单信息（包含项目名称、客户名称、预估金额）
    
    Returns:
        消息文本
    """
    try:
        message = PMInvolvementService.generate_notification_message(
            result.dict(),
            ticket_info
        )
        return {
            "消息类型": "企业微信/钉钉通知",
            "消息内容": message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败：{str(e)}")


# 测试端点
@router.get("/test-examples", summary="获取测试示例")
async def get_test_examples():
    """获取测试数据示例"""
    return {
        "高风险项目示例": {
            "项目金额": 150,
            "项目类型": "SMT贴片生产线",
            "行业": "汽车电子",
            "是否首次做": False,
            "历史相似项目数": 2,
            "失败项目数": 1,
            "是否有标准方案": False,
            "技术创新点": ["视觉检测新算法", "多工位协同"]
        },
        "低风险项目示例": {
            "项目金额": 50,
            "项目类型": "视觉检测系统",
            "行业": "消费电子",
            "是否首次做": False,
            "历史相似项目数": 5,
            "失败项目数": 0,
            "是否有标准方案": True,
            "技术创新点": []
        }
    }
