"""
项目进度管理模块 - FastAPI 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入路由
from app.api.v1 import project, task, timesheet, workload
from app.api.v1 import auth, system, data_import, reports, performance, task_center, reminder, batch_operations, presale, pmo, production, bom

app = FastAPI(
    title="项目进度管理系统",
    description="非标自动化项目进度管理API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1", tags=["认证管理"])
app.include_router(system.router, prefix="/api/v1", tags=["系统管理"])
app.include_router(data_import.router, prefix="/api/v1", tags=["数据导入导出"])
app.include_router(reports.router, prefix="/api/v1", tags=["报表模块"])
app.include_router(performance.router, prefix="/api/v1", tags=["绩效报告"])
app.include_router(task_center.router, prefix="/api/v1", tags=["任务中心"])
app.include_router(reminder.router, prefix="/api/v1", tags=["任务提醒"])
app.include_router(batch_operations.router, prefix="/api/v1", tags=["批量操作"])
app.include_router(presale.router, prefix="/api/v1", tags=["售前技术支持"])
app.include_router(pmo.router, prefix="/api/v1", tags=["项目管理部"])
app.include_router(production.router, prefix="/api/v1", tags=["生产管理"])
app.include_router(bom.router, prefix="/api/v1", tags=["BOM管理"])
app.include_router(project.router, prefix="/api/v1/projects", tags=["项目管理"])
app.include_router(task.router, prefix="/api/v1/tasks", tags=["任务管理"])
app.include_router(timesheet.router, prefix="/api/v1/timesheets", tags=["工时管理"])
app.include_router(workload.router, prefix="/api/v1/workload", tags=["负荷管理"])


@app.get("/")
async def root():
    return {"message": "项目进度管理系统 API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
