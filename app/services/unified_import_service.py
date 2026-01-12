# -*- coding: utf-8 -*-
"""
统一数据导入服务
支持多种数据类型的Excel导入：项目、用户、工时、任务、物料、BOM
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import io

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.models.organization import Employee
from app.models.timesheet import Timesheet
from app.models.progress import Task
from app.models.material import Material, Supplier, BomHeader, BomItem
from app.services.project_import_service import (
    validate_excel_file,
    parse_excel_data,
    import_projects_from_dataframe
)
from app.services.employee_import_service import import_employees_from_dataframe


class UnifiedImportService:
    """统一数据导入服务"""

    @staticmethod
    def validate_file(filename: str) -> None:
        """验证Excel文件类型"""
        if not filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")

    @staticmethod
    def parse_file(file_content: bytes) -> pd.DataFrame:
        """解析Excel文件"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            df = df.dropna(how='all')
            if len(df) == 0:
                raise HTTPException(status_code=400, detail="文件中没有数据")
            return df
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel文件解析失败: {str(e)}")

    @staticmethod
    def import_user_data(
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入用户数据（使用员工导入服务）
        """
        try:
            result = import_employees_from_dataframe(db, df, current_user_id)
            return (
                result.get('imported', 0),
                result.get('updated', 0),
                [{"row_index": i + 2, "error": err} for i, err in enumerate(result.get('errors', []))]
            )
        except Exception as e:
            return 0, 0, [{"row_index": 0, "error": str(e)}]

    @staticmethod
    def _check_required_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
        """检查必需列是否存在，返回缺失列列表"""
        missing = []
        for col in required_columns:
            if col not in df.columns and col.replace('*', '') not in df.columns:
                missing.append(col)
        return missing

    @staticmethod
    def _parse_work_date(work_date_val) -> Optional[date]:
        """解析工作日期"""
        if isinstance(work_date_val, datetime):
            return work_date_val.date()
        elif isinstance(work_date_val, date):
            return work_date_val
        else:
            return pd.to_datetime(work_date_val).date()

    @staticmethod
    def _parse_hours(hours_val) -> Optional[float]:
        """解析工时，返回None表示无效"""
        hours = float(hours_val)
        if hours <= 0 or hours > 24:
            return None
        return hours

    @staticmethod
    def _parse_progress(row, field_name: str) -> Optional[int]:
        """解析进度字段"""
        val = row.get(field_name)
        if pd.notna(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
        return None

    @staticmethod
    def _create_timesheet_record(
        user: User, index: int, work_date: date, hours: float,
        project_id: Optional[int], project_code: str, project_name: Optional[str],
        task_name: str, overtime_type: str, work_content: str, work_result: str,
        progress_before: Optional[int], progress_after: Optional[int],
        current_user_id: int
    ) -> Timesheet:
        """创建工时记录对象"""
        return Timesheet(
            timesheet_no=f"TS{datetime.now().strftime('%Y%m%d%H%M%S')}{index:03d}",
            user_id=user.id,
            user_name=user.real_name or user.username,
            department_id=user.department_id,
            department_name=user.department if hasattr(user, 'department') else '',
            project_id=project_id,
            project_code=project_code,
            project_name=project_name,
            task_name=task_name,
            work_date=work_date,
            hours=Decimal(str(hours)),
            overtime_type=overtime_type,
            work_content=work_content,
            work_result=work_result,
            progress_before=progress_before,
            progress_after=progress_after,
            status='DRAFT',
            created_by=current_user_id
        )

    @staticmethod
    def import_timesheet_data(
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入工时数据
        """
        required_columns = ['工作日期*', '人员姓名*', '工时(小时)*']
        missing = UnifiedImportService._check_required_columns(df, required_columns)
        if missing:
            raise HTTPException(status_code=400, detail=f"Excel文件缺少必需的列：{', '.join(missing)}")

        imported_count = 0
        updated_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            row_idx = index + 2
            try:
                # 解析必需字段
                work_date_val = row.get('工作日期*') or row.get('工作日期')
                user_name = str(row.get('人员姓名*', '') or row.get('人员姓名', '')).strip()
                hours_val = row.get('工时(小时)*') or row.get('工时(小时)') or row.get('工时')

                if not work_date_val or not user_name or pd.isna(hours_val):
                    failed_rows.append({"row_index": row_idx, "error": "工作日期、人员姓名、工时为必填项"})
                    continue

                # 解析日期和工时
                try:
                    work_date = UnifiedImportService._parse_work_date(work_date_val)
                except (ValueError, TypeError, pd.errors.ParserError):
                    failed_rows.append({"row_index": row_idx, "error": "工作日期格式错误"})
                    continue

                try:
                    hours = UnifiedImportService._parse_hours(hours_val)
                    if hours is None:
                        failed_rows.append({"row_index": row_idx, "error": "工时必须在0-24之间"})
                        continue
                except (ValueError, TypeError):
                    failed_rows.append({"row_index": row_idx, "error": "工时格式错误"})
                    continue

                # 查找用户
                user = db.query(User).filter(
                    (User.real_name == user_name) | (User.username == user_name)
                ).first()
                if not user:
                    failed_rows.append({"row_index": row_idx, "error": f"未找到用户: {user_name}"})
                    continue

                # 解析可选字段
                project_code = str(row.get('项目编码', '') or '').strip()
                project_id, project_name = None, None
                if project_code:
                    project = db.query(Project).filter(Project.project_code == project_code).first()
                    if project:
                        project_id, project_name = project.id, project.project_name

                task_name = str(row.get('任务名称', '') or '').strip()
                work_content = str(row.get('工作内容', '') or '').strip()
                work_result = str(row.get('工作成果', '') or '').strip()
                overtime_type = str(row.get('加班类型', 'NORMAL') or 'NORMAL').strip().upper()
                progress_before = UnifiedImportService._parse_progress(row, '更新前进度(%)')
                progress_after = UnifiedImportService._parse_progress(row, '更新后进度(%)')

                # 检查是否已存在相同记录
                existing = db.query(Timesheet).filter(
                    Timesheet.user_id == user.id,
                    Timesheet.work_date == work_date,
                    Timesheet.project_id == project_id,
                    Timesheet.task_name == task_name
                ).first()

                if existing:
                    if update_existing:
                        existing.hours = hours
                        existing.overtime_type = overtime_type
                        existing.work_content = work_content
                        existing.work_result = work_result
                        existing.progress_before = progress_before
                        existing.progress_after = progress_after
                        updated_count += 1
                    else:
                        failed_rows.append({"row_index": row_idx, "error": "该工时记录已存在"})
                        continue
                else:
                    timesheet = UnifiedImportService._create_timesheet_record(
                        user, index, work_date, hours, project_id, project_code, project_name,
                        task_name, overtime_type, work_content, work_result,
                        progress_before, progress_after, current_user_id
                    )
                    db.add(timesheet)
                    imported_count += 1

            except Exception as e:
                failed_rows.append({"row_index": row_idx, "error": str(e)})

        return imported_count, updated_count, failed_rows

    @staticmethod
    def import_task_data(
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入任务数据
        """
        required_columns = ['任务名称*', '项目编码*']
        missing_columns = []
        for col in required_columns:
            if col not in df.columns and col.replace('*', '') not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
            )

        imported_count = 0
        updated_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            try:
                # 解析必需字段
                task_name = str(row.get('任务名称*', '') or row.get('任务名称', '')).strip()
                project_code = str(row.get('项目编码*', '') or row.get('项目编码', '')).strip()

                if not task_name or not project_code:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": "任务名称和项目编码为必填项"
                    })
                    continue

                # 查找项目
                project = db.query(Project).filter(Project.project_code == project_code).first()
                if not project:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": f"未找到项目: {project_code}"
                    })
                    continue

                # 解析可选字段
                stage = str(row.get('阶段', 'S1') or 'S1').strip().upper()
                owner_name = str(row.get('负责人*', '') or row.get('负责人', '') or '').strip()

                owner_id = None
                if owner_name:
                    owner = db.query(User).filter(
                        (User.real_name == owner_name) | (User.username == owner_name)
                    ).first()
                    if owner:
                        owner_id = owner.id

                # 解析日期
                plan_start = None
                plan_end = None
                if pd.notna(row.get('计划开始日期')):
                    try:
                        plan_start = pd.to_datetime(row.get('计划开始日期')).date()
                    except (ValueError, TypeError, pd.errors.ParserError):
                        pass
                if pd.notna(row.get('计划结束日期')):
                    try:
                        plan_end = pd.to_datetime(row.get('计划结束日期')).date()
                    except (ValueError, TypeError, pd.errors.ParserError):
                        pass

                # 解析权重
                weight = Decimal('1.00')
                if pd.notna(row.get('权重(%)')):
                    try:
                        weight = Decimal(str(row.get('权重(%)'))) / Decimal('100')
                    except (ValueError, TypeError, InvalidOperation):
                        pass

                task_description = str(row.get('任务描述', '') or '').strip()

                # 检查是否已存在
                existing = db.query(Task).filter(
                    Task.project_id == project.id,
                    Task.task_name == task_name
                ).first()

                if existing:
                    if update_existing:
                        existing.stage = stage
                        if owner_id:
                            existing.owner_id = owner_id
                        if plan_start:
                            existing.plan_start = plan_start
                        if plan_end:
                            existing.plan_end = plan_end
                        existing.weight = weight
                        updated_count += 1
                    else:
                        failed_rows.append({
                            "row_index": index + 2,
                            "error": "该任务已存在"
                        })
                        continue
                else:
                    # 创建任务
                    task = Task(
                        project_id=project.id,
                        task_name=task_name,
                        stage=stage,
                        status='TODO',
                        owner_id=owner_id,
                        plan_start=plan_start,
                        plan_end=plan_end,
                        weight=weight,
                        progress_percent=0
                    )
                    db.add(task)
                    imported_count += 1

            except Exception as e:
                failed_rows.append({
                    "row_index": index + 2,
                    "error": str(e)
                })

        return imported_count, updated_count, failed_rows

    @staticmethod
    def import_material_data(
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入物料数据
        """
        required_columns = ['物料编码*', '物料名称*']
        missing_columns = []
        for col in required_columns:
            if col not in df.columns and col.replace('*', '') not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
            )

        imported_count = 0
        updated_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            try:
                # 解析必需字段
                material_code = str(row.get('物料编码*', '') or row.get('物料编码', '')).strip()
                material_name = str(row.get('物料名称*', '') or row.get('物料名称', '')).strip()

                if not material_code or not material_name:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": "物料编码和物料名称为必填项"
                    })
                    continue

                # 解析可选字段
                specification = str(row.get('规格型号', '') or '').strip()
                unit = str(row.get('单位', '件') or '件').strip()
                material_type = str(row.get('物料类型', '') or '').strip()
                supplier_name = str(row.get('默认供应商', '') or '').strip()

                # 解析价格和库存
                standard_price = Decimal('0')
                if pd.notna(row.get('参考价格')):
                    try:
                        standard_price = Decimal(str(row.get('参考价格')))
                    except (ValueError, TypeError, InvalidOperation):
                        pass

                safety_stock = Decimal('0')
                if pd.notna(row.get('安全库存')):
                    try:
                        safety_stock = Decimal(str(row.get('安全库存')))
                    except (ValueError, TypeError, InvalidOperation):
                        pass

                # 查找或创建供应商
                default_supplier_id = None
                if supplier_name:
                    supplier = db.query(Supplier).filter(
                        Supplier.supplier_name == supplier_name
                    ).first()
                    if not supplier:
                        # 自动创建供应商
                        supplier_code = f"SUP{datetime.now().strftime('%Y%m%d%H%M%S')}{index:03d}"
                        supplier = Supplier(
                            supplier_code=supplier_code,
                            supplier_name=supplier_name,
                            status='ACTIVE'
                        )
                        db.add(supplier)
                        db.flush()
                    default_supplier_id = supplier.id

                # 检查是否已存在
                existing = db.query(Material).filter(Material.material_code == material_code).first()

                if existing:
                    if update_existing:
                        existing.material_name = material_name
                        if specification:
                            existing.specification = specification
                        existing.unit = unit
                        if material_type:
                            existing.material_type = material_type
                        existing.standard_price = standard_price
                        existing.safety_stock = safety_stock
                        if default_supplier_id:
                            existing.default_supplier_id = default_supplier_id
                        updated_count += 1
                    else:
                        failed_rows.append({
                            "row_index": index + 2,
                            "error": f"物料编码 {material_code} 已存在"
                        })
                        continue
                else:
                    # 创建物料
                    material = Material(
                        material_code=material_code,
                        material_name=material_name,
                        specification=specification,
                        unit=unit,
                        material_type=material_type,
                        standard_price=standard_price,
                        safety_stock=safety_stock,
                        default_supplier_id=default_supplier_id,
                        is_active=True,
                        created_by=current_user_id
                    )
                    db.add(material)
                    imported_count += 1

            except Exception as e:
                failed_rows.append({
                    "row_index": index + 2,
                    "error": str(e)
                })

        return imported_count, updated_count, failed_rows

    @staticmethod
    def import_bom_data(
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入BOM数据
        """
        required_columns = ['BOM编码*', '项目编码*', '物料编码*', '用量*']
        missing_columns = []
        for col in required_columns:
            if col not in df.columns and col.replace('*', '') not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
            )

        imported_count = 0
        updated_count = 0
        failed_rows = []
        bom_cache = {}  # 缓存BOM头

        for index, row in df.iterrows():
            try:
                # 解析必需字段
                bom_code = str(row.get('BOM编码*', '') or row.get('BOM编码', '')).strip()
                project_code = str(row.get('项目编码*', '') or row.get('项目编码', '')).strip()
                material_code = str(row.get('物料编码*', '') or row.get('物料编码', '')).strip()

                # 解析用量
                quantity_val = row.get('用量*') or row.get('用量')
                if pd.isna(quantity_val):
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": "用量为必填项"
                    })
                    continue

                try:
                    quantity = Decimal(str(quantity_val))
                    if quantity <= 0:
                        failed_rows.append({
                            "row_index": index + 2,
                            "error": "用量必须大于0"
                        })
                        continue
                except (ValueError, TypeError, InvalidOperation):
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": "用量格式错误"
                    })
                    continue

                # 查找项目
                project = db.query(Project).filter(Project.project_code == project_code).first()
                if not project:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": f"未找到项目: {project_code}"
                    })
                    continue

                # 查找物料
                material = db.query(Material).filter(Material.material_code == material_code).first()
                if not material:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": f"未找到物料: {material_code}"
                    })
                    continue

                # 解析可选字段
                machine_code = str(row.get('机台编号', '') or '').strip()
                unit = str(row.get('单位', '件') or '件').strip()
                remark = str(row.get('备注', '') or '').strip()

                # 获取或创建BOM头
                bom_key = (bom_code, project.id)
                if bom_key not in bom_cache:
                    bom_header = db.query(BomHeader).filter(
                        BomHeader.bom_no == bom_code
                    ).first()
                    if not bom_header:
                        bom_header = BomHeader(
                            bom_no=bom_code,
                            bom_name=f"{project.project_name}-BOM",
                            project_id=project.id,
                            version='1.0',
                            status='DRAFT',
                            created_by=current_user_id
                        )
                        db.add(bom_header)
                        db.flush()
                    bom_cache[bom_key] = bom_header
                else:
                    bom_header = bom_cache[bom_key]

                # 检查BOM明细是否已存在
                existing = db.query(BomItem).filter(
                    BomItem.bom_id == bom_header.id,
                    BomItem.material_id == material.id
                ).first()

                if existing:
                    if update_existing:
                        existing.quantity = quantity
                        existing.unit = unit
                        existing.remark = remark
                        updated_count += 1
                    else:
                        failed_rows.append({
                            "row_index": index + 2,
                            "error": "该BOM明细已存在"
                        })
                        continue
                else:
                    # 获取下一行号
                    max_item_no = db.query(BomItem).filter(
                        BomItem.bom_id == bom_header.id
                    ).count()
                    item_no = max_item_no + 1

                    # 创建BOM明细
                    bom_item = BomItem(
                        bom_id=bom_header.id,
                        item_no=item_no,
                        material_id=material.id,
                        material_code=material_code,
                        material_name=material.material_name,
                        specification=material.specification,
                        unit=unit,
                        quantity=quantity,
                        source_type=material.source_type or 'PURCHASE',
                        remark=remark
                    )
                    db.add(bom_item)
                    imported_count += 1

            except Exception as e:
                failed_rows.append({
                    "row_index": index + 2,
                    "error": str(e)
                })

        return imported_count, updated_count, failed_rows

    @staticmethod
    def import_data(
        db: Session,
        file_content: bytes,
        filename: str,
        template_type: str,
        current_user_id: int,
        update_existing: bool = False
    ) -> Dict[str, Any]:
        """
        统一导入入口

        Returns:
            Dict[str, Any]: 导入结果
        """
        # 验证文件
        UnifiedImportService.validate_file(filename)

        # 解析文件
        df = UnifiedImportService.parse_file(file_content)

        # 根据类型导入
        template_type = template_type.upper()
        imported_count = 0
        updated_count = 0
        failed_rows = []

        if template_type == "PROJECT":
            # 调用项目导入服务
            imported_count, updated_count, failed_rows = import_projects_from_dataframe(
                db, df, update_existing
            )
        elif template_type == "USER":
            imported_count, updated_count, failed_rows = UnifiedImportService.import_user_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "TIMESHEET":
            imported_count, updated_count, failed_rows = UnifiedImportService.import_timesheet_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "TASK":
            imported_count, updated_count, failed_rows = UnifiedImportService.import_task_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "MATERIAL":
            imported_count, updated_count, failed_rows = UnifiedImportService.import_material_data(
                db, df, current_user_id, update_existing
            )
        elif template_type == "BOM":
            imported_count, updated_count, failed_rows = UnifiedImportService.import_bom_data(
                db, df, current_user_id, update_existing
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的模板类型: {template_type}")

        return {
            "imported_count": imported_count,
            "updated_count": updated_count,
            "failed_count": len(failed_rows),
            "failed_rows": failed_rows[:20]  # 最多返回20个错误
        }


# 创建单例
unified_import_service = UnifiedImportService()
