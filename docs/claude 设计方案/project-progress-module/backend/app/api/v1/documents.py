# ===========================================
# 文档管理模块 API
# 项目文档/图纸版本管理
# ===========================================

from fastapi import APIRouter, Query, Path, Body, UploadFile, File, Form
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter(prefix="/api/v1/documents", tags=["文档管理"])


# ===========================================
# 枚举定义
# ===========================================

class DocumentType(str, Enum):
    DESIGN = "design"            # 设计文档
    DRAWING = "drawing"          # 图纸
    BOM = "bom"                  # BOM清单
    SPECIFICATION = "spec"       # 技术规格书
    MANUAL = "manual"            # 操作手册
    TEST_REPORT = "test_report"  # 测试报告
    ACCEPTANCE = "acceptance"    # 验收文档
    CONTRACT = "contract"        # 合同
    OTHER = "other"              # 其他


class DocumentStatus(str, Enum):
    DRAFT = "draft"              # 草稿
    REVIEWING = "reviewing"      # 审核中
    APPROVED = "approved"        # 已批准
    RELEASED = "released"        # 已发布
    OBSOLETE = "obsolete"        # 已废弃


class ReviewResult(str, Enum):
    APPROVED = "approved"        # 通过
    REJECTED = "rejected"        # 驳回
    REVISE = "revise"           # 需修改


# ===========================================
# 请求/响应模型
# ===========================================

class DocumentCreate(BaseModel):
    """文档创建"""
    document_no: str = Field(..., description="文档编号")
    document_name: str = Field(..., description="文档名称")
    document_type: DocumentType
    
    # 关联
    project_id: Optional[int] = None
    equipment_id: Optional[int] = None
    
    # 分类
    category: Optional[str] = None
    tags: List[str] = []
    
    # 描述
    description: Optional[str] = None


class DocumentUpdate(BaseModel):
    """文档更新"""
    document_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class VersionCreate(BaseModel):
    """版本创建"""
    version_no: str = Field(..., description="版本号")
    change_description: str = Field(..., description="变更说明")
    change_type: str = Field(..., description="变更类型")  # major/minor/patch


class ReviewRequest(BaseModel):
    """审核请求"""
    reviewer_id: int
    review_level: int = 1  # 审核级别
    deadline: Optional[date] = None
    comment: Optional[str] = None


class ReviewSubmit(BaseModel):
    """审核提交"""
    result: ReviewResult
    comment: str
    issues: Optional[List[dict]] = None  # 问题列表


class ShareRequest(BaseModel):
    """分享请求"""
    user_ids: List[int] = []
    department_ids: List[int] = []
    permission: str = "view"  # view/download/edit
    expire_date: Optional[date] = None


# ===========================================
# 文档管理接口
# ===========================================

@router.get("/list")
async def list_documents(
    project_id: Optional[int] = Query(None, description="项目ID"),
    equipment_id: Optional[int] = Query(None, description="设备ID"),
    document_type: Optional[DocumentType] = Query(None),
    status: Optional[DocumentStatus] = Query(None),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取文档列表"""
    return {
        "total": 45,
        "items": [
            {
                "id": 1,
                "document_no": "DOC-2025-001",
                "document_name": "XX汽车传感器测试设备-总体设计方案",
                "document_type": "design",
                "document_type_label": "设计文档",
                "current_version": "V1.2",
                "status": "released",
                "status_label": "已发布",
                "project_name": "XX汽车传感器测试设备项目",
                "file_type": "pdf",
                "file_size": "2.5MB",
                "author_name": "张工",
                "created_at": "2024-11-15",
                "updated_at": "2024-12-18",
                "download_count": 25,
                "tags": ["设计", "方案"]
            },
            {
                "id": 2,
                "document_no": "DWG-2025-001",
                "document_name": "机架装配图",
                "document_type": "drawing",
                "document_type_label": "图纸",
                "current_version": "V1.0",
                "status": "approved",
                "status_label": "已批准",
                "project_name": "XX汽车传感器测试设备项目",
                "file_type": "dwg",
                "file_size": "8.5MB",
                "author_name": "李工",
                "created_at": "2024-11-25",
                "updated_at": "2024-11-28",
                "download_count": 12,
                "tags": ["图纸", "机械"]
            }
        ]
    }


@router.post("/create")
async def create_document(
    document_no: str = Form(...),
    document_name: str = Form(...),
    document_type: DocumentType = Form(...),
    project_id: Optional[int] = Form(None),
    equipment_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...)
):
    """创建文档(含上传文件)"""
    return {
        "id": 10,
        "document_no": document_no,
        "version": "V1.0",
        "message": "文档创建成功"
    }


@router.get("/{document_id}")
async def get_document_detail(document_id: int = Path(..., description="文档ID")):
    """获取文档详情"""
    return {
        "id": document_id,
        "document_no": "DOC-2025-001",
        "document_name": "XX汽车传感器测试设备-总体设计方案",
        "document_type": "design",
        "document_type_label": "设计文档",
        "status": "released",
        "description": "本文档描述了XX汽车传感器测试设备的总体设计方案，包括系统架构、功能设计、技术指标等。",
        
        # 关联
        "project": {"id": 1, "name": "XX汽车传感器测试设备项目"},
        "equipment": {"id": 1, "name": "XX汽车传感器自动测试设备"},
        
        # 分类
        "category": "设计方案",
        "tags": ["设计", "方案", "测试设备"],
        
        # 文件信息
        "file_name": "总体设计方案_V1.2.pdf",
        "file_type": "pdf",
        "file_size": 2621440,
        "file_size_text": "2.5MB",
        
        # 版本信息
        "current_version": "V1.2",
        "version_count": 3,
        
        # 创建信息
        "author": {"id": 1, "name": "张工", "department": "技术部"},
        "created_at": "2024-11-15 10:30:00",
        "updated_at": "2024-12-18 16:45:00",
        
        # 审核信息
        "review_status": "approved",
        "reviewers": [
            {"id": 1, "name": "王主管", "result": "approved", "time": "2024-12-17 10:00:00"}
        ],
        
        # 统计
        "statistics": {
            "view_count": 58,
            "download_count": 25,
            "share_count": 5
        },
        
        # 权限
        "permissions": {
            "can_edit": True,
            "can_delete": False,
            "can_share": True,
            "can_download": True
        }
    }


@router.put("/{document_id}")
async def update_document(
    document_id: int = Path(..., description="文档ID"),
    data: DocumentUpdate = Body(...)
):
    """更新文档信息"""
    return {"message": "更新成功"}


@router.delete("/{document_id}")
async def delete_document(document_id: int = Path(..., description="文档ID")):
    """删除文档"""
    return {"message": "删除成功"}


@router.get("/{document_id}/download")
async def download_document(
    document_id: int = Path(..., description="文档ID"),
    version: Optional[str] = Query(None, description="版本号")
):
    """下载文档"""
    # 实际项目中返回文件流
    return {"download_url": f"/files/documents/{document_id}/download"}


# ===========================================
# 版本管理接口
# ===========================================

@router.get("/{document_id}/versions")
async def get_document_versions(document_id: int = Path(..., description="文档ID")):
    """获取文档版本历史"""
    return {
        "document_id": document_id,
        "current_version": "V1.2",
        "versions": [
            {
                "id": 3,
                "version_no": "V1.2",
                "change_type": "minor",
                "change_description": "优化了测试流程描述，补充了异常处理章节",
                "file_size": "2.5MB",
                "author_name": "张工",
                "created_at": "2024-12-18 16:45:00",
                "status": "released",
                "is_current": True
            },
            {
                "id": 2,
                "version_no": "V1.1",
                "change_type": "minor",
                "change_description": "根据评审意见修改了技术指标部分",
                "file_size": "2.3MB",
                "author_name": "张工",
                "created_at": "2024-12-01 14:20:00",
                "status": "obsolete",
                "is_current": False
            },
            {
                "id": 1,
                "version_no": "V1.0",
                "change_type": "major",
                "change_description": "初始版本",
                "file_size": "2.1MB",
                "author_name": "张工",
                "created_at": "2024-11-15 10:30:00",
                "status": "obsolete",
                "is_current": False
            }
        ]
    }


@router.post("/{document_id}/versions")
async def create_new_version(
    document_id: int = Path(..., description="文档ID"),
    version_no: str = Form(...),
    change_type: str = Form(...),
    change_description: str = Form(...),
    file: UploadFile = File(...)
):
    """上传新版本"""
    return {
        "id": 4,
        "version_no": version_no,
        "message": "新版本上传成功"
    }


@router.get("/{document_id}/versions/{version_id}/download")
async def download_version(
    document_id: int = Path(...),
    version_id: int = Path(...)
):
    """下载指定版本"""
    return {"download_url": f"/files/documents/{document_id}/versions/{version_id}/download"}


@router.get("/{document_id}/versions/compare")
async def compare_versions(
    document_id: int = Path(..., description="文档ID"),
    version1: str = Query(..., description="版本1"),
    version2: str = Query(..., description="版本2")
):
    """版本对比"""
    return {
        "document_id": document_id,
        "version1": {
            "version_no": version1,
            "created_at": "2024-12-01 14:20:00",
            "file_size": "2.3MB"
        },
        "version2": {
            "version_no": version2,
            "created_at": "2024-12-18 16:45:00",
            "file_size": "2.5MB"
        },
        "changes": [
            {"type": "modified", "section": "第3章 技术指标", "description": "更新了测试精度要求"},
            {"type": "added", "section": "第5章 异常处理", "description": "新增异常处理章节"},
            {"type": "deleted", "section": "附录B", "description": "删除了旧版参数表"}
        ]
    }


# ===========================================
# 审核流程接口
# ===========================================

@router.post("/{document_id}/submit-review")
async def submit_for_review(
    document_id: int = Path(..., description="文档ID"),
    data: ReviewRequest = Body(...)
):
    """提交审核"""
    return {
        "review_id": 1,
        "message": "已提交审核，等待审核人处理"
    }


@router.get("/{document_id}/reviews")
async def get_review_history(document_id: int = Path(..., description="文档ID")):
    """获取审核历史"""
    return {
        "document_id": document_id,
        "current_review": {
            "id": 2,
            "status": "approved",
            "submitted_at": "2024-12-16 09:00:00",
            "completed_at": "2024-12-17 10:00:00",
            "reviews": [
                {
                    "reviewer_name": "王主管",
                    "reviewer_role": "技术主管",
                    "result": "approved",
                    "comment": "方案完整，可以发布",
                    "review_time": "2024-12-17 10:00:00"
                }
            ]
        },
        "history": [
            {
                "id": 1,
                "version": "V1.0",
                "status": "approved",
                "submitted_at": "2024-11-16 09:00:00",
                "completed_at": "2024-11-17 15:30:00"
            }
        ]
    }


@router.post("/{document_id}/reviews/{review_id}/submit")
async def submit_review_result(
    document_id: int = Path(...),
    review_id: int = Path(...),
    data: ReviewSubmit = Body(...)
):
    """提交审核结果"""
    return {"message": "审核结果已提交"}


@router.post("/{document_id}/release")
async def release_document(
    document_id: int = Path(..., description="文档ID"),
    version: str = Body(..., embed=True)
):
    """发布文档"""
    return {"message": "文档已发布"}


# ===========================================
# 分享与权限接口
# ===========================================

@router.post("/{document_id}/share")
async def share_document(
    document_id: int = Path(..., description="文档ID"),
    data: ShareRequest = Body(...)
):
    """分享文档"""
    return {
        "share_id": 1,
        "share_link": f"https://system.com/share/doc/{document_id}/abc123",
        "message": "分享成功"
    }


@router.get("/{document_id}/permissions")
async def get_document_permissions(document_id: int = Path(..., description="文档ID")):
    """获取文档权限设置"""
    return {
        "document_id": document_id,
        "owner": {"id": 1, "name": "张工"},
        "permissions": [
            {"type": "user", "id": 2, "name": "李工", "permission": "edit"},
            {"type": "user", "id": 3, "name": "王工", "permission": "view"},
            {"type": "department", "id": 1, "name": "技术部", "permission": "view"}
        ],
        "public": False
    }


@router.put("/{document_id}/permissions")
async def update_permissions(
    document_id: int = Path(..., description="文档ID"),
    permissions: List[dict] = Body(...)
):
    """更新权限设置"""
    return {"message": "权限更新成功"}


# ===========================================
# 文件夹管理接口
# ===========================================

@router.get("/folders")
async def list_folders(
    project_id: Optional[int] = Query(None),
    parent_id: Optional[int] = Query(None)
):
    """获取文件夹列表"""
    return {
        "folders": [
            {
                "id": 1,
                "name": "XX汽车传感器测试设备项目",
                "type": "project",
                "children": [
                    {"id": 11, "name": "设计文档", "type": "category", "document_count": 5},
                    {"id": 12, "name": "图纸", "type": "category", "document_count": 15},
                    {"id": 13, "name": "BOM清单", "type": "category", "document_count": 3},
                    {"id": 14, "name": "测试报告", "type": "category", "document_count": 2}
                ]
            },
            {
                "id": 2,
                "name": "YY新能源电池检测线项目",
                "type": "project",
                "children": [
                    {"id": 21, "name": "设计文档", "type": "category", "document_count": 8},
                    {"id": 22, "name": "图纸", "type": "category", "document_count": 25}
                ]
            }
        ]
    }


@router.post("/folders")
async def create_folder(
    name: str = Body(...),
    parent_id: Optional[int] = Body(None),
    project_id: Optional[int] = Body(None)
):
    """创建文件夹"""
    return {"id": 100, "message": "文件夹创建成功"}


# ===========================================
# 搜索接口
# ===========================================

@router.get("/search")
async def search_documents(
    keyword: str = Query(..., min_length=1),
    document_type: Optional[DocumentType] = Query(None),
    project_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    file_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """全文搜索文档"""
    return {
        "keyword": keyword,
        "total": 5,
        "items": [
            {
                "id": 1,
                "document_name": "XX汽车传感器测试设备-总体设计方案",
                "document_type": "design",
                "highlight": "...本设备用于<em>传感器</em>的自动化<em>测试</em>...",
                "project_name": "XX汽车传感器测试设备项目",
                "updated_at": "2024-12-18"
            }
        ]
    }


# ===========================================
# 统计分析接口
# ===========================================

@router.get("/statistics")
async def get_document_statistics(
    project_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """获取文档统计"""
    return {
        "total_documents": 245,
        "total_versions": 512,
        "total_size": "2.5GB",
        
        "by_type": [
            {"type": "design", "label": "设计文档", "count": 45, "percent": 18.4},
            {"type": "drawing", "label": "图纸", "count": 120, "percent": 49.0},
            {"type": "bom", "label": "BOM清单", "count": 25, "percent": 10.2},
            {"type": "test_report", "label": "测试报告", "count": 30, "percent": 12.2},
            {"type": "manual", "label": "操作手册", "count": 15, "percent": 6.1},
            {"type": "other", "label": "其他", "count": 10, "percent": 4.1}
        ],
        
        "by_status": [
            {"status": "draft", "label": "草稿", "count": 15},
            {"status": "reviewing", "label": "审核中", "count": 8},
            {"status": "approved", "label": "已批准", "count": 45},
            {"status": "released", "label": "已发布", "count": 170},
            {"status": "obsolete", "label": "已废弃", "count": 7}
        ],
        
        "recent_activity": {
            "uploads_today": 5,
            "uploads_this_week": 23,
            "downloads_today": 18,
            "downloads_this_week": 85
        },
        
        "top_downloaded": [
            {"name": "机架装配图", "downloads": 45},
            {"name": "电气原理图", "downloads": 38},
            {"name": "总体设计方案", "downloads": 25}
        ]
    }
