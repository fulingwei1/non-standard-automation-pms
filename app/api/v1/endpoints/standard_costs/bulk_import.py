# -*- coding: utf-8 -*-
"""
标准成本批量导入端点
"""

import io
import os
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.standard_cost import StandardCost, StandardCostHistory
from app.models.user import User
from app.schemas.standard_cost import StandardCostImportResult

router = APIRouter()


def _validate_cost_category(category: str) -> bool:
    """验证成本类别"""
    valid_categories = ['MATERIAL', 'LABOR', 'OVERHEAD']
    return category in valid_categories


def _validate_cost_source(source: str) -> bool:
    """验证成本来源"""
    valid_sources = ['HISTORICAL_AVG', 'INDUSTRY_STANDARD', 'EXPERT_ESTIMATE', 'VENDOR_QUOTE']
    return source in valid_sources


@router.get("/template", response_class=StreamingResponse)
def download_import_template(
    current_user: User = Depends(security.require_permission("cost:manage")),
) -> Any:
    """
    下载标准成本导入模板
    
    返回Excel格式的导入模板文件
    权限要求：cost:manage
    """
    # 创建模板数据
    template_data = {
        '成本项编码*': ['MAT-001', 'LAB-001', 'OVH-001'],
        '成本项名称*': ['钢板Q235', '高级工程师', '设备折旧'],
        '成本类别*': ['MATERIAL', 'LABOR', 'OVERHEAD'],
        '规格型号': ['8mm厚度', '5年以上经验', '按台时分摊'],
        '单位*': ['kg', '人天', '台时'],
        '标准成本*': [4.50, 1200.00, 50.00],
        '币种': ['CNY', 'CNY', 'CNY'],
        '成本来源*': ['HISTORICAL_AVG', 'EXPERT_ESTIMATE', 'EXPERT_ESTIMATE'],
        '来源说明': ['基于过去6个月平均价格', '基于市场薪酬水平', '基于设备原值和折旧年限'],
        '生效日期*': ['2026-01-01', '2026-01-01', '2026-01-01'],
        '失效日期': ['', '', ''],
        '成本说明': ['普通碳素结构钢板', '高级技术人员日工资标准', '机器设备折旧费用'],
        '备注': ['', '', '']
    }
    
    df = pd.DataFrame(template_data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='标准成本导入模板', index=False)
        
        # 添加说明sheet
        instructions = pd.DataFrame({
            '字段说明': [
                '成本项编码*：唯一标识，不能重复',
                '成本项名称*：成本项名称',
                '成本类别*：MATERIAL(物料) / LABOR(人工) / OVERHEAD(制造费用)',
                '规格型号：可选，物料规格或人员等级等',
                '单位*：kg、件、人天、台时等',
                '标准成本*：数值，支持小数',
                '币种：默认CNY',
                '成本来源*：HISTORICAL_AVG(历史平均) / INDUSTRY_STANDARD(行业标准) / EXPERT_ESTIMATE(专家估计) / VENDOR_QUOTE(供应商报价)',
                '来源说明：可选，描述成本来源',
                '生效日期*：格式：YYYY-MM-DD',
                '失效日期：可选，格式：YYYY-MM-DD，为空表示长期有效',
                '成本说明：可选',
                '备注：可选'
            ]
        })
        instructions.to_excel(writer, sheet_name='导入说明', index=False)
    
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': f'attachment; filename=standard_cost_template_{datetime.now().strftime("%Y%m%d")}.xlsx'
        }
    )


@router.post("/import", response_model=StandardCostImportResult)
async def import_standard_costs(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(security.require_permission("cost:manage")),
) -> Any:
    """
    批量导入标准成本
    
    支持Excel和CSV格式
    权限要求：cost:manage
    """
    # 验证文件格式
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.xlsx', '.xls', '.csv']:
        raise HTTPException(
            status_code=400,
            detail="不支持的文件格式，请上传Excel(.xlsx/.xls)或CSV文件"
        )
    
    try:
        # 读取文件
        content = await file.read()
        
        if file_ext == '.csv':
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content), sheet_name=0)
        
        # 列名映射
        column_mapping = {
            '成本项编码*': 'cost_code',
            '成本项编码': 'cost_code',
            '成本项名称*': 'cost_name',
            '成本项名称': 'cost_name',
            '成本类别*': 'cost_category',
            '成本类别': 'cost_category',
            '规格型号': 'specification',
            '单位*': 'unit',
            '单位': 'unit',
            '标准成本*': 'standard_cost',
            '标准成本': 'standard_cost',
            '币种': 'currency',
            '成本来源*': 'cost_source',
            '成本来源': 'cost_source',
            '来源说明': 'source_description',
            '生效日期*': 'effective_date',
            '生效日期': 'effective_date',
            '失效日期': 'expiry_date',
            '成本说明': 'description',
            '备注': 'notes'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 验证必填字段
        required_fields = ['cost_code', 'cost_name', 'cost_category', 'unit', 'standard_cost', 'cost_source', 'effective_date']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"缺少必填字段：{', '.join(missing_fields)}"
            )
        
        # 处理导入
        success_count = 0
        error_count = 0
        errors = []
        warnings = []
        
        for idx, row in df.iterrows():
            try:
                row_num = idx + 2  # Excel行号（从2开始，因为第1行是表头）
                
                # 验证成本编码
                cost_code = str(row['cost_code']).strip()
                if not cost_code or cost_code == 'nan':
                    errors.append({
                        'row': row_num,
                        'field': 'cost_code',
                        'message': '成本项编码不能为空'
                    })
                    error_count += 1
                    continue
                
                # 检查是否已存在
                existing = db.query(StandardCost).filter(
                    StandardCost.cost_code == cost_code,
                    StandardCost.is_active == True
                ).first()
                
                if existing:
                    warnings.append({
                        'row': row_num,
                        'cost_code': cost_code,
                        'message': f'成本编码 {cost_code} 已存在，将跳过'
                    })
                    continue
                
                # 验证成本类别
                cost_category = str(row['cost_category']).strip().upper()
                if not _validate_cost_category(cost_category):
                    errors.append({
                        'row': row_num,
                        'field': 'cost_category',
                        'message': f'无效的成本类别：{cost_category}，必须是 MATERIAL/LABOR/OVERHEAD'
                    })
                    error_count += 1
                    continue
                
                # 验证成本来源
                cost_source = str(row['cost_source']).strip().upper()
                if not _validate_cost_source(cost_source):
                    errors.append({
                        'row': row_num,
                        'field': 'cost_source',
                        'message': f'无效的成本来源：{cost_source}'
                    })
                    error_count += 1
                    continue
                
                # 转换日期
                try:
                    if isinstance(row['effective_date'], str):
                        effective_date = datetime.strptime(row['effective_date'], '%Y-%m-%d').date()
                    else:
                        effective_date = pd.to_datetime(row['effective_date']).date()
                except Exception as e:
                    errors.append({
                        'row': row_num,
                        'field': 'effective_date',
                        'message': f'无效的生效日期格式：{row["effective_date"]}'
                    })
                    error_count += 1
                    continue
                
                # 处理失效日期
                expiry_date = None
                if pd.notna(row.get('expiry_date')) and str(row.get('expiry_date')).strip():
                    try:
                        if isinstance(row['expiry_date'], str):
                            expiry_date = datetime.strptime(row['expiry_date'], '%Y-%m-%d').date()
                        else:
                            expiry_date = pd.to_datetime(row['expiry_date']).date()
                    except:
                        warnings.append({
                            'row': row_num,
                            'field': 'expiry_date',
                            'message': '失效日期格式错误，将设为空'
                        })
                
                # 创建标准成本
                cost = StandardCost(
                    cost_code=cost_code,
                    cost_name=str(row['cost_name']).strip(),
                    cost_category=cost_category,
                    specification=str(row.get('specification', '')).strip() if pd.notna(row.get('specification')) else None,
                    unit=str(row['unit']).strip(),
                    standard_cost=Decimal(str(row['standard_cost'])),
                    currency=str(row.get('currency', 'CNY')).strip(),
                    cost_source=cost_source,
                    source_description=str(row.get('source_description', '')).strip() if pd.notna(row.get('source_description')) else None,
                    effective_date=effective_date,
                    expiry_date=expiry_date,
                    description=str(row.get('description', '')).strip() if pd.notna(row.get('description')) else None,
                    notes=str(row.get('notes', '')).strip() if pd.notna(row.get('notes')) else None,
                    version=1,
                    is_active=True,
                    created_by=current_user.id
                )
                db.add(cost)
                db.flush()
                
                # 创建历史记录
                history = StandardCostHistory(
                    standard_cost_id=cost.id,
                    change_type="CREATE",
                    change_date=date.today(),
                    new_cost=cost.standard_cost,
                    new_effective_date=cost.effective_date,
                    change_reason="批量导入",
                    change_description=f"批量导入创建成本项：{cost.cost_name}",
                    changed_by=current_user.id,
                    changed_by_name=current_user.real_name
                )
                db.add(history)
                
                success_count += 1
                
            except Exception as e:
                errors.append({
                    'row': row_num,
                    'message': str(e)
                })
                error_count += 1
        
        # 提交事务
        if success_count > 0:
            db.commit()
        
        return StandardCostImportResult(
            success_count=success_count,
            error_count=error_count,
            errors=errors,
            warnings=warnings
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"导入失败：{str(e)}"
        )
