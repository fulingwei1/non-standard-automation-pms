# -*- coding: utf-8 -*-
"""
AI 辅助战略管理 API 端点
提供战略分析、战略分解、年度经营计划、部门工作分解等 AI 辅助功能
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.dependencies import get_db
from app.models.user import User

router = APIRouter(prefix="/api/v1/ai-strategy", tags=["ai-strategy"])

# ============================================
# 大模型 API 配置
# ============================================

API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
MODEL = "qwen-plus"

# 如果环境变量为空，尝试从配置文件读取
if not API_KEY:
    config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if os.path.exists(config_path):
        try:
            with open(config_path) as f:
                config = json.load(f)
                for p in config.get("providers", []):
                    if p.get("id") == "bailian":
                        API_KEY = p.get("apiKey", "")
                        break
        except Exception:
            pass

# DB 路径（5 个 parent 到项目根目录）
DB_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "app.db"


# ============================================
# 辅助函数
# ============================================

def _get_api_key() -> str:
    """获取 API Key"""
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="大模型 API Key 未配置，请设置 DASHSCOPE_API_KEY 环境变量或检查配置文件"
        )
    return API_KEY


def _call_llm(messages: List[Dict[str, str]], timeout: int = 60) -> str:
    """调用大模型 API"""
    api_key = _get_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if "choices" not in result or len(result["choices"]) == 0:
                raise ValueError("AI 返回格式异常，无 choices 字段")
            
            content = result["choices"][0]["message"]["content"]
            return content.strip()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI 请求超时，请稍后重试"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 服务响应错误：{e.response.status_code}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 调用失败：{str(e)}"
        )


def _parse_json_response(content: str) -> Dict[str, Any]:
    """从 AI 响应中解析 JSON"""
    # 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # 尝试提取 ```json 块
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试提取 ``` 块
    code_match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 尝试直接找 { 开头
    brace_start = content.find('{')
    brace_end = content.rfind('}')
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(content[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"无法从 AI 响应中解析 JSON: {content[:200]}...")


# ============================================
# API 端点
# ============================================

@router.post(
    "/analyze",
    summary="AI 战略分析",
    description="基于公司信息进行 SWOT 分析，提供战略定位建议和核心竞争力分析"
)
async def ai_strategy_analyze(
    company_info: str,
    financial_data: Optional[str] = None,
    market_info: Optional[str] = None,
    challenges: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    AI 战略分析
    
    输入：
    - company_info: 公司简介
    - financial_data: 财务数据（营收/利润等）
    - market_info: 市场信息
    - challenges: 当前挑战
    
    输出：
    - SWOT 分析（优势、劣势、机会、威胁）
    - 战略定位建议
    - 核心竞争力分析
    - 3-5 条战略方向建议
    """
    
    system_prompt = """你是一位资深战略管理咨询顾问，专注于非标自动化测试设备行业。
请基于用户提供的公司信息，进行专业的战略分析。

**重要要求**：
1. 必须返回严格的 JSON 格式，不要有任何额外文字
2. JSON 结构如下：
{
    "swot": {
        "strengths": ["优势 1", "优势 2", ...],
        "weaknesses": ["劣势 1", "劣势 2", ...],
        "opportunities": ["机会 1", "机会 2", ...],
        "threats": ["威胁 1", "威胁 2", ...]
    },
    "strategic_positioning": "战略定位描述",
    "core_competencies": ["核心竞争力 1", "核心竞争力 2", ...],
    "strategic_directions": [
        {"direction": "战略方向 1", "description": "详细描述"},
        {"direction": "战略方向 2", "description": "详细描述"},
        ...
    ]
}
3. 分析要结合非标自动化测试设备行业特点（ICT/FCT/EOL/烧录/老化/视觉检测等）
4. 战略方向建议 3-5 条，要具体可执行"""

    user_prompt = f"""请对以下公司进行战略分析：

**公司简介**：
{company_info}

**财务数据**：
{financial_data or "暂无"}

**市场信息**：
{market_info or "暂无"}

**当前挑战**：
{challenges or "暂无"}

请按照系统 prompt 中的 JSON 格式返回分析结果。"""

    try:
        content = _call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        result = _parse_json_response(content)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 响应解析失败：{str(e)}"
        )


@router.post(
    "/decompose",
    summary="AI 战略分解",
    description="基于战略信息进行 BSC 四维度分解，生成 CSF 和 KPI"
)
async def ai_strategy_decompose(
    strategy_name: str,
    strategy_vision: str,
    strategy_year: int,
    industry: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    AI 战略分解
    
    输入：
    - strategy_name: 战略名称
    - strategy_vision: 战略愿景
    - strategy_year: 战略年度
    - industry: 行业（可选）
    
    输出：
    - BSC 四维度 CSF（每维度 2-3 个）
    - 每个 CSF 下 2-3 个 KPI（含目标值、单位、评分标准）
    """
    
    system_prompt = """你是一位资深战略管理专家，精通平衡计分卡（BSC）方法论。
请将战略分解为关键成功要素（CSF）和关键绩效指标（KPI）。

**BSC 四维度**：
- FINANCIAL（财务维度）
- CUSTOMER（客户维度）
- INTERNAL（内部流程维度）
- LEARNING（学习与成长维度）

**重要要求**：
1. 必须返回严格的 JSON 格式
2. JSON 结构如下：
{
    "csfs": [
        {
            "dimension": "FINANCIAL",
            "code": "CSF-F-001",
            "name": "CSF 名称",
            "description": "详细描述",
            "weight": 25.0,
            "kpis": [
                {
                    "code": "KPI-F-001",
                    "name": "KPI 名称",
                    "description": "指标描述",
                    "ipooc_type": "OUTPUT",
                    "unit": "%",
                    "direction": "UP",
                    "target_value": 20,
                    "baseline_value": 15,
                    "excellent_threshold": 25,
                    "good_threshold": 20,
                    "warning_threshold": 15
                }
            ]
        }
    ]
}
3. 每个维度 2-3 个 CSF，每个 CSF 下 2-3 个 KPI
4. KPI 的 ipooc_type 为 INPUT/PROCESS/OUTPUT/OUTCOME 之一
5. direction 为 UP（越大越好）或 DOWN（越小越好）
6. 结合非标自动化测试设备行业特点"""

    user_prompt = f"""请将以下战略进行 BSC 分解：

**战略名称**：{strategy_name}
**战略愿景**：{strategy_vision}
**战略年度**：{strategy_year}
**行业**：{industry or "非标自动化测试设备"}

请按照系统 prompt 中的 JSON 格式返回分解结果。"""

    try:
        content = _call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        result = _parse_json_response(content)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 响应解析失败：{str(e)}"
        )


@router.post(
    "/annual-plan",
    summary="AI 年度经营计划",
    description="基于战略和 CSF 生成年度重点工作"
)
async def ai_annual_plan(
    company_info: str,
    year: int,
    revenue_target: float,
    strategy_id: Optional[int] = None,
    additional_info: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    AI 年度经营计划
    
    输入：
    - strategy_id: 战略 ID（可选，从 DB 读战略和 CSF）
    - company_info: 公司信息
    - year: 年度
    - revenue_target: 营收目标
    - additional_info: 补充信息
    
    输出：
    - 6-8 项年度重点工作（名称、描述、目标、时间、预算建议、优先级、关联 CSF）
    """
    
    system_prompt = """你是一位资深经营管理专家，擅长制定年度经营计划。
请基于战略和营收目标，生成年度重点工作。

**重要要求**：
1. 必须返回严格的 JSON 格式
2. JSON 结构如下：
{
    "annual_works": [
        {
            "code": "AKW-2026-001",
            "name": "重点工作名称",
            "description": "工作描述",
            "target": "目标描述",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "budget": 1000000,
            "priority": "HIGH",
            "csf_code": "CSF-F-001",
            "voc_source": "SHAREHOLDER",
            "pain_point": "痛点描述",
            "solution": "解决方案",
            "risk_description": "风险描述"
        }
    ]
}
3. 生成 6-8 项年度重点工作
4. priority 为 HIGH/MEDIUM/LOW 之一
5. voc_source 为 SHAREHOLDER/CUSTOMER/EMPLOYEE/COMPLIANCE 之一
6. 结合非标自动化测试设备行业特点"""

    strategy_context = ""
    if strategy_id:
        strategy_context = f"（基于战略 ID: {strategy_id}，请从数据库中读取相关战略和 CSF 信息）"
    
    user_prompt = f"""请制定{year}年度经营计划{strategy_context}：

**公司信息**：
{company_info}

**年度营收目标**：{revenue_target} 万元

**补充信息**：
{additional_info or "暂无"}

请按照系统 prompt 中的 JSON 格式返回年度重点工作。"""

    try:
        content = _call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        result = _parse_json_response(content)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 响应解析失败：{str(e)}"
        )


@router.post(
    "/dept-objectives",
    summary="AI 部门工作分解",
    description="基于战略生成部门 OKR 目标"
)
async def ai_dept_objectives(
    department_name: str,
    department_role: str,
    year: int,
    strategy_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    AI 部门工作分解
    
    输入：
    - strategy_id: 战略 ID（可选）
    - department_name: 部门名称
    - department_role: 部门职能描述
    - year: 年度
    
    输出：
    - 3-5 个部门目标（OKR 格式：Objective + 3 Key Results）
    - 每个目标关联的 KPI 指标
    """
    
    system_prompt = """你是一位资深 OKR 教练，擅长将战略分解为部门 OKR。
请为指定部门生成 OKR 目标。

**重要要求**：
1. 必须返回严格的 JSON 格式
2. JSON 结构如下：
{
    "objectives": [
        {
            "objective": "Objective 描述（鼓舞人心的目标）",
            "key_results": [
                "KR1: 可量化的关键结果 1",
                "KR2: 可量化的关键结果 2",
                "KR3: 可量化的关键结果 3"
            ],
            "related_kpis": [
                {
                    "kpi_name": "关联 KPI 名称",
                    "kpi_description": "KPI 描述",
                    "target_value": 100,
                    "unit": "%",
                    "weight": 30.0
                }
            ],
            "weight": 30.0
        }
    ]
}
3. 生成 3-5 个部门目标
4. 每个目标包含 3 个 Key Results
5. weight 总和应为 100
6. 结合非标自动化测试设备行业特点"""

    strategy_context = ""
    if strategy_id:
        strategy_context = f"（基于战略 ID: {strategy_id}）"
    
    user_prompt = f"""请为以下部门制定{year}年度 OKR{strategy_context}：

**部门名称**：{department_name}
**部门职能**：{department_role}

请按照系统 prompt 中的 JSON 格式返回部门 OKR 目标。"""

    try:
        content = _call_llm([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        
        result = _parse_json_response(content)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 响应解析失败：{str(e)}"
        )


@router.post(
    "/apply",
    summary="应用 AI 生成结果到数据库",
    description="将 AI 生成的 CSF/KPI/年度工作/部门目标写入数据库"
)
async def ai_apply(
    type: str,  # csf/kpi/annual_work/dept_objective
    data: Dict[str, Any],
    strategy_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    将 AI 生成的结果写入数据库
    
    输入：
    - type: 类型（csf/kpi/annual_work/dept_objective）
    - data: AI 生成的 JSON 数据
    - strategy_id: 战略 ID
    
    输出：
    - 写入结果统计
    """
    import sqlite3
    
    if type not in ["csf", "kpi", "annual_work", "dept_objective"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的类型：{type}"
        )
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        result = {"success": True, "created_count": 0, "details": []}
        
        if type == "csf":
            # 写入 CSF
            csfs = data.get("csfs", []) if isinstance(data, dict) else data
            for csf in csfs:
                csf_id = _insert_csf(cursor, csf, strategy_id)
                result["created_count"] += 1
                result["details"].append({"type": "csf", "id": csf_id, "name": csf.get("name")})
                
                # 同时写入关联的 KPI
                for kpi in csf.get("kpis", []):
                    kpi_id = _insert_kpi(cursor, kpi, csf_id)
                    result["created_count"] += 1
                    result["details"].append({"type": "kpi", "id": kpi_id, "name": kpi.get("name")})
        
        elif type == "kpi":
            # 单独写入 KPI（需要 csf_id）
            csf_id = data.get("csf_id") or strategy_id
            kpis = data.get("kpis", []) if isinstance(data, dict) else [data]
            for kpi in kpis:
                kpi_id = _insert_kpi(cursor, kpi, csf_id)
                result["created_count"] += 1
                result["details"].append({"type": "kpi", "id": kpi_id, "name": kpi.get("name")})
        
        elif type == "annual_work":
            # 写入年度重点工作
            works = data.get("annual_works", []) if isinstance(data, dict) else [data]
            for work in works:
                work_id = _insert_annual_work(cursor, work, strategy_id)
                result["created_count"] += 1
                result["details"].append({"type": "annual_work", "id": work_id, "name": work.get("name")})
        
        elif type == "dept_objective":
            # 写入部门目标
            objectives = data.get("objectives", []) if isinstance(data, dict) else [data]
            dept_id = data.get("department_id")
            if not dept_id:
                # 尝试根据部门名称查找
                dept_name = data.get("department_name")
                if dept_name:
                    cursor.execute("SELECT id FROM departments WHERE name = ?", (dept_name,))
                    row = cursor.fetchone()
                    if row:
                        dept_id = row["id"]
            
            if dept_id:
                for obj in objectives:
                    obj_id = _insert_dept_objective(cursor, obj, strategy_id, dept_id)
                    result["created_count"] += 1
                    result["details"].append({"type": "dept_objective", "id": obj_id, "objective": obj.get("objective")})
        
        conn.commit()
        conn.close()
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库写入失败：{str(e)}"
        )


# ============================================
# 数据库操作辅助函数
# ============================================

def _insert_csf(cursor, csf: Dict[str, Any], strategy_id: int) -> int:
    """插入 CSF 记录"""
    import uuid
    
    cursor.execute("""
        INSERT INTO csfs (
            strategy_id, dimension, code, name, description,
            derivation_method, weight, sort_order, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (
        strategy_id,
        csf.get("dimension", "FINANCIAL"),
        csf.get("code", f"CSF-{uuid.uuid4().hex[:8].upper()}"),
        csf.get("name", ""),
        csf.get("description", ""),
        csf.get("derivation_method"),
        csf.get("weight", 0),
        csf.get("sort_order", 0),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    return cursor.lastrowid


def _insert_kpi(cursor, kpi: Dict[str, Any], csf_id: int) -> int:
    """插入 KPI 记录"""
    import uuid
    
    cursor.execute("""
        INSERT INTO kpis (
            csf_id, code, name, description, ipooc_type,
            unit, direction, target_value, baseline_value,
            excellent_threshold, good_threshold, warning_threshold,
            data_source_type, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'MANUAL', 1, ?, ?)
    """, (
        csf_id,
        kpi.get("code", f"KPI-{uuid.uuid4().hex[:8].upper()}"),
        kpi.get("name", ""),
        kpi.get("description", ""),
        kpi.get("ipooc_type", "OUTPUT"),
        kpi.get("unit", ""),
        kpi.get("direction", "UP"),
        kpi.get("target_value"),
        kpi.get("baseline_value"),
        kpi.get("excellent_threshold"),
        kpi.get("good_threshold"),
        kpi.get("warning_threshold"),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    return cursor.lastrowid


def _insert_annual_work(cursor, work: Dict[str, Any], strategy_id: int) -> int:
    """插入年度重点工作记录"""
    import uuid
    
    # 从 CSF 编码查找 csf_id
    csf_id = work.get("csf_id")
    if not csf_id and work.get("csf_code"):
        cursor.execute("SELECT id FROM csfs WHERE code = ? AND strategy_id = ?", 
                      (work.get("csf_code"), strategy_id))
        row = cursor.fetchone()
        if row:
            csf_id = row["id"]
    
    if not csf_id:
        # 如果没有 CSF 关联，使用 strategy_id 查找第一个 CSF
        cursor.execute("SELECT id FROM csfs WHERE strategy_id = ? LIMIT 1", (strategy_id,))
        row = cursor.fetchone()
        if row:
            csf_id = row["id"]
    
    cursor.execute("""
        INSERT INTO annual_key_works (
            csf_id, code, name, description, voc_source,
            pain_point, solution, target, year,
            start_date, end_date, priority, budget,
            risk_description, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
    """, (
        csf_id,
        work.get("code", f"AKW-{uuid.uuid4().hex[:8].upper()}"),
        work.get("name", ""),
        work.get("description", ""),
        work.get("voc_source", "SHAREHOLDER"),
        work.get("pain_point", ""),
        work.get("solution", ""),
        work.get("target", ""),
        work.get("year", datetime.now().year),
        work.get("start_date"),
        work.get("end_date"),
        work.get("priority", "MEDIUM"),
        work.get("budget"),
        work.get("risk_description", ""),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    return cursor.lastrowid


def _insert_dept_objective(cursor, obj: Dict[str, Any], strategy_id: int, dept_id: int) -> int:
    """插入部门目标记录"""
    import json
    
    cursor.execute("""
        INSERT INTO department_objectives (
            strategy_id, department_id, year, objectives, key_results,
            kpis_config, status, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'DRAFT', 1, ?, ?)
    """, (
        strategy_id,
        dept_id,
        datetime.now().year,
        json.dumps([obj], ensure_ascii=False),
        json.dumps(obj.get("key_results", []), ensure_ascii=False),
        json.dumps(obj.get("related_kpis", []), ensure_ascii=False),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    return cursor.lastrowid
