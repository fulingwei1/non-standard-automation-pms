from typing import Any, List, Optional, Dict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import io

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
import pandas as pd

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.organization import Department, Employee, EmployeeHrProfile
from app.models.staff_matching import HrEmployeeProfile, HrTagDict, HrEmployeeTagEvaluation
from app.schemas.organization import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeResponse,
    EmployeeHrProfileCreate,
    EmployeeHrProfileUpdate,
    EmployeeHrProfileResponse,
    EmployeeWithHrProfileResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


def build_department_tree(departments: List[Department], parent_id: Optional[int] = None) -> List[Dict]:
    """构建部门树结构"""
    tree = []
    for dept in departments:
        if dept.parent_id == parent_id:
            children = build_department_tree(departments, dept.id)
            dept_dict = {
                "id": dept.id,
                "dept_code": dept.dept_code,
                "dept_name": dept.dept_name,
                "parent_id": dept.parent_id,
                "level": dept.level,
                "sort_order": dept.sort_order,
                "is_active": dept.is_active,
                "manager_id": dept.manager_id,
                "manager_name": dept.manager.name if dept.manager else None,
                "children": children if children else None,
            }
            tree.append(dept_dict)
    return sorted(tree, key=lambda x: x.get("sort_order", 0))

# ==================== 部门 ====================


@router.get("/departments", response_model=List[DepartmentResponse])
def read_departments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取部门列表
    """
    query = db.query(Department)
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    departments = query.order_by(Department.sort_order, Department.dept_code).offset(skip).limit(limit).all()
    return departments


@router.get("/departments/tree", response_model=List[Dict])
def get_department_tree(
    db: Session = Depends(deps.get_db),
    is_active: Optional[bool] = Query(None, description="是否只显示启用的部门"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取部门树结构
    """
    query = db.query(Department)
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    departments = query.order_by(Department.sort_order, Department.dept_code).all()
    tree = build_department_tree(departments)
    return tree


@router.post("/departments", response_model=DepartmentResponse)
def create_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_in: DepartmentCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建新部门
    """
    # 检查部门编码是否已存在
    department = (
        db.query(Department).filter(Department.dept_code == dept_in.dept_code).first()
    )
    if department:
        raise HTTPException(
            status_code=400,
            detail="该部门编码已存在",
        )
    
    # 检查同一父部门下部门名称是否重复
    query = db.query(Department).filter(Department.dept_name == dept_in.dept_name)
    if dept_in.parent_id:
        query = query.filter(Department.parent_id == dept_in.parent_id)
    else:
        query = query.filter(Department.parent_id.is_(None))
    
    existing_dept = query.first()
    if existing_dept:
        raise HTTPException(
            status_code=400,
            detail=f"该部门名称已存在（{existing_dept.dept_code}）",
        )
    
    # 检查部门名称是否包含父部门名称（避免创建"父部门-子部门"这种冗余命名）
    if dept_in.parent_id:
        parent = db.query(Department).filter(Department.id == dept_in.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="父部门不存在")
        
        # 如果部门名称包含父部门名称，提示用户
        if parent.dept_name in dept_in.dept_name and dept_in.dept_name != parent.dept_name:
            raise HTTPException(
                status_code=400,
                detail=f"部门名称不应包含父部门名称。建议使用：{dept_in.dept_name.replace(parent.dept_name + '-', '').replace(parent.dept_name, '')}",
            )
        
        level = parent.level + 1
    else:
        level = 1
    
    department = Department(**dept_in.model_dump())
    department.level = level
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.get("/departments/{dept_id}", response_model=DepartmentResponse)
def read_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
) -> Any:
    """
    Get department by ID.
    """
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.put("/departments/{dept_id}", response_model=DepartmentResponse)
def update_department(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    dept_in: DepartmentUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新部门信息
    """
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")

    update_data = dept_in.model_dump(exclude_unset=True)
    
    # 如果更新了部门名称，检查是否与同级部门重复
    if 'dept_name' in update_data:
        new_name = update_data['dept_name']
        parent_id = update_data.get('parent_id', department.parent_id)
        
        query = db.query(Department).filter(
            Department.dept_name == new_name,
            Department.id != dept_id
        )
        if parent_id:
            query = query.filter(Department.parent_id == parent_id)
        else:
            query = query.filter(Department.parent_id.is_(None))
        
        existing_dept = query.first()
        if existing_dept:
            raise HTTPException(
                status_code=400,
                detail=f"该部门名称已存在（{existing_dept.dept_code}）",
            )
        
        # 检查部门名称是否包含父部门名称
        if parent_id:
            parent = db.query(Department).filter(Department.id == parent_id).first()
            if parent and parent.dept_name in new_name and new_name != parent.dept_name:
                raise HTTPException(
                    status_code=400,
                    detail=f"部门名称不应包含父部门名称。建议使用：{new_name.replace(parent.dept_name + '-', '').replace(parent.dept_name, '')}",
                )
    
    # 如果更新了父部门，需要重新计算层级
    if 'parent_id' in update_data and update_data['parent_id'] != department.parent_id:
        if update_data['parent_id']:
            parent = db.query(Department).filter(Department.id == update_data['parent_id']).first()
            if not parent:
                raise HTTPException(status_code=404, detail="父部门不存在")
            # 检查是否会造成循环引用
            if parent.id == dept_id:
                raise HTTPException(status_code=400, detail="不能将部门设置为自己的子部门")
            department.level = parent.level + 1
        else:
            department.level = 1
    
    for field, value in update_data.items():
        if field != 'parent_id':  # parent_id已经在上面处理了
            setattr(department, field, value)

    db.add(department)
    db.commit()
    db.refresh(department)
    return department


@router.get("/departments/{dept_id}/users", response_model=PaginatedResponse)
def get_department_users(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    keyword: Optional[str] = Query(None, description="关键词搜索（用户名/姓名/工号）"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取部门人员列表
    """
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")
    
    # 查询该部门的用户（通过department字段匹配）
    query = db.query(User).filter(User.department == department.dept_name)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                User.username.contains(keyword),
                User.real_name.contains(keyword),
                User.employee_no.contains(keyword),
            )
        )
    
    # 启用状态筛选
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    total = query.count()
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    
    # 设置roles字段
    for u in users:
        u.roles = [ur.role.role_name for ur in u.roles] if u.roles else []
    
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 员工 ====================


@router.get("/employees", response_model=List[EmployeeResponse])
def read_employees(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve employees.
    """
    employees = db.query(Employee).offset(skip).limit(limit).all()
    return employees


@router.post("/employees", response_model=EmployeeResponse)
def create_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_in: EmployeeCreate,
) -> Any:
    """
    Create new employee.
    """
    employee = (
        db.query(Employee)
        .filter(Employee.employee_code == emp_in.employee_code)
        .first()
    )
    if employee:
        raise HTTPException(
            status_code=400,
            detail="Employee with this code already exists.",
        )
    employee = Employee(**emp_in.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("/employees/{emp_id}", response_model=EmployeeResponse)
def read_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_id: int,
) -> Any:
    """
    Get employee by ID.
    """
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(
    *,
    db: Session = Depends(deps.get_db),
    emp_id: int,
    emp_in: EmployeeUpdate,
) -> Any:
    """
    Update an employee.
    """
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    update_data = emp_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(employee, field, value)

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


# ==================== 员工批量导入 ====================

def _clean_name(name) -> Optional[str]:
    """清理姓名中的特殊字符"""
    if pd.isna(name):
        return None
    return str(name).replace('\n', '').strip()


def _clean_phone(phone) -> Optional[str]:
    """清理电话号码"""
    if pd.isna(phone):
        return None
    phone_str = str(phone)
    if 'e' in phone_str.lower() or '.' in phone_str:
        try:
            phone_str = str(int(float(phone)))
        except (ValueError, TypeError, OverflowError):
            pass
    return phone_str.strip()


def _get_department_name(row, dept_cols: List[str]) -> Optional[str]:
    """组合部门名称"""
    parts = []
    for col in dept_cols:
        val = row.get(col)
        if pd.notna(val) and str(val).strip() not in ['/', 'NaN', '']:
            parts.append(str(val).strip())
    return '-'.join(parts) if parts else None


def _is_active_employee(status) -> bool:
    """判断是否在职"""
    if pd.isna(status):
        return True
    status_str = str(status).strip()
    if status_str in ['离职', '已离职']:
        return False
    return True


def _generate_employee_code(index: int, existing_codes: set) -> str:
    """生成员工编码"""
    code = f"EMP{index:04d}"
    while code in existing_codes:
        index += 1
        code = f"EMP{index:04d}"
    return code


@router.post("/employees/import")
async def import_employees_from_excel(
    file: UploadFile = File(..., description="Excel文件（支持企业微信导出格式）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    从Excel文件批量导入员工数据

    支持的Excel格式：
    - 企业微信导出的通讯录
    - 人事系统导出的员工信息表

    必需列：姓名
    可选列：一级部门、二级部门、三级部门、部门、职务、联系方式、手机、在职离职状态

    系统会自动：
    - 跳过已存在的员工（按姓名+部门判断）
    - 更新已存在员工的信息
    - 为新员工生成工号
    - 创建员工档案
    """
    from app.services.employee_import_service import (
        validate_excel_file,
        import_employees_from_dataframe
    )
    
    # 验证文件类型
    validate_excel_file(file.filename)
    
    # 读取Excel文件
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取Excel文件失败: {str(e)}")
    
    # 导入数据
    result = import_employees_from_dataframe(db, df, current_user.id)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"导入完成：新增 {result['imported']} 人，更新 {result['updated']} 人，跳过 {result['skipped']} 条",
        "imported": result['imported'],
        "updated": result['updated'],
        "skipped": result['skipped'],
        "errors": result['errors']
    }


@router.get("/employees/import/template")
async def download_import_template(
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    获取员工导入模板说明

    返回导入模板的列说明，用户可以参考此格式准备数据
    """
    return {
        "template_columns": [
            {"name": "姓名", "required": True, "description": "员工姓名（必填）"},
            {"name": "一级部门", "required": False, "description": "一级部门名称"},
            {"name": "二级部门", "required": False, "description": "二级部门名称"},
            {"name": "三级部门", "required": False, "description": "三级部门名称"},
            {"name": "职务", "required": False, "description": "职务/岗位名称"},
            {"name": "联系方式", "required": False, "description": "手机号码"},
            {"name": "在职离职状态", "required": False, "description": "在职/离职/试用期等"},
        ],
        "supported_formats": [".xlsx", ".xls"],
        "notes": [
            "系统会根据 姓名+部门 判断员工是否已存在",
            "已存在的员工会更新其信息，不会重复创建",
            "支持直接导入企业微信导出的通讯录Excel",
            "部门会自动按 一级部门-二级部门-三级部门 格式组合"
        ]
    }


# ==================== 人事档案 ====================


@router.get("/hr-profiles")
def get_hr_profiles(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    keyword: Optional[str] = Query(None, description="搜索关键词（姓名/工号/部门）"),
    dept_level1: Optional[str] = Query(None, description="一级部门筛选"),
    employment_status: Optional[str] = Query(None, description="在职状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    获取人事档案列表（分页）
    """
    query = db.query(Employee).outerjoin(EmployeeHrProfile)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Employee.name.contains(keyword),
                Employee.employee_code.contains(keyword),
                Employee.department.contains(keyword),
            )
        )

    # 一级部门筛选
    if dept_level1:
        query = query.filter(EmployeeHrProfile.dept_level1 == dept_level1)

    # 在职状态筛选
    if employment_status:
        query = query.filter(Employee.employment_status == employment_status)

    total = query.count()
    offset = (page - 1) * page_size
    employees = query.order_by(Employee.created_at.desc()).offset(offset).limit(page_size).all()

    # 转换为字典格式
    items = []
    for emp in employees:
        profile = emp.hr_profile
        item = {
            "id": emp.id,
            "employee_code": emp.employee_code,
            "name": emp.name,
            "department": emp.department,
            "role": emp.role,
            "phone": emp.phone,
            "is_active": emp.is_active,
            "employment_status": emp.employment_status,
            "employment_type": emp.employment_type,
            "id_card": emp.id_card,
            "hr_profile": None
        }
        if profile:
            item["hr_profile"] = {
                "id": profile.id,
                "dept_level1": profile.dept_level1,
                "dept_level2": profile.dept_level2,
                "dept_level3": profile.dept_level3,
                "position": profile.position,
                "job_level": profile.job_level,
                "hire_date": str(profile.hire_date) if profile.hire_date else None,
                "is_confirmed": profile.is_confirmed,
                "gender": profile.gender,
                "age": profile.age,
                "ethnicity": profile.ethnicity,
                "education_level": profile.education_level,
                "graduate_school": profile.graduate_school,
                "major": profile.major,
            }
        items.append(item)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/hr-profiles/{emp_id}", response_model=EmployeeWithHrProfileResponse)
def get_hr_profile(
    emp_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取指定员工的人事档案详情
    """
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")
    return employee


@router.put("/hr-profiles/{emp_id}", response_model=EmployeeHrProfileResponse)
def update_hr_profile(
    emp_id: int,
    profile_in: EmployeeHrProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新员工人事档案
    """
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="员工不存在")

    # 获取或创建人事档案
    profile = db.query(EmployeeHrProfile).filter(EmployeeHrProfile.employee_id == emp_id).first()
    if not profile:
        profile = EmployeeHrProfile(employee_id=emp_id)
        db.add(profile)

    # 更新字段
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


def _parse_date(date_val) -> Optional[datetime]:
    """解析日期值"""
    if pd.isna(date_val):
        return None
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str):
        date_str = str(date_val).strip()
        if not date_str or date_str in ['/', 'NaN', '无试用期']:
            return None
        # 尝试多种日期格式
        for fmt in ['%Y/%m/%d', '%Y-%m-%d', '%Y.%m.%d', '%Y年%m月%d日']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
    return None


def _clean_str(val) -> Optional[str]:
    """清理字符串值"""
    if pd.isna(val):
        return None
    result = str(val).replace('\n', '').strip()
    if result in ['/', 'NaN', '']:
        return None
    return result


def _clean_decimal(val) -> Optional[Decimal]:
    """清理数值"""
    if pd.isna(val):
        return None
    try:
        return Decimal(str(val))
    except (ValueError, TypeError, InvalidOperation):
        return None


@router.post("/hr-profiles/import")
async def import_hr_profiles(
    file: UploadFile = File(..., description="人事档案Excel文件"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    批量导入人事档案数据

    从Excel文件导入完整的人事档案信息，包括：
    - 基本信息（姓名、部门、职务等）
    - 入职信息（入职时间、转正日期、合同期限等）
    - 个人信息（性别、年龄、民族、政治面貌等）
    - 联系信息（地址、紧急联系人等）
    - 教育背景（毕业院校、专业、学历等）
    - 财务社保（银行卡、社保号、公积金号等）

    系统会根据姓名匹配员工，已存在的员工会更新档案，不存在的会新建员工和档案。
    """
    from app.services.hr_profile_import_service import (
        validate_excel_file,
        validate_required_columns,
        import_hr_profiles_from_dataframe
    )
    
    # 验证文件类型
    validate_excel_file(file.filename)
    
    # 读取Excel文件
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取Excel文件失败: {str(e)}")
    
    # 检查必需列
    validate_required_columns(df)
    
    # 导入数据
    result = import_hr_profiles_from_dataframe(db, df)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"导入完成：新增 {result['imported']} 人，更新 {result['updated']} 人，跳过 {result['skipped']} 条",
        "imported": result['imported'],
        "updated": result['updated'],
        "skipped": result['skipped'],
        "errors": result['errors']
    }


@router.get("/hr-profiles/statistics/overview")
def get_hr_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Dict[str, Any]:
    """
    获取人事统计概览
    """
    # 总人数
    total = db.query(Employee).filter(Employee.is_active == True).count()

    # 按部门统计
    dept_stats = db.query(
        EmployeeHrProfile.dept_level1,
        func.count(EmployeeHrProfile.id)
    ).join(Employee).filter(Employee.is_active == True).group_by(
        EmployeeHrProfile.dept_level1
    ).all()

    # 按在职状态统计
    status_stats = db.query(
        Employee.employment_status,
        func.count(Employee.id)
    ).group_by(Employee.employment_status).all()

    # 试用期员工数
    probation_count = db.query(Employee).filter(
        Employee.is_active == True,
        Employee.employment_type == 'probation'
    ).count()

    return {
        "total_active": total,
        "probation_count": probation_count,
        "by_department": [{"department": d[0] or "未分配", "count": d[1]} for d in dept_stats],
        "by_status": [{"status": s[0] or "未知", "count": s[1]} for s in status_stats],
    }
