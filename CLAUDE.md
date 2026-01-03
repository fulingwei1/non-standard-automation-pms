# CLAUDE.md - AI Assistant Guide for 非标自动化项目管理系统

## Project Overview

This is a **Non-Standard Automation Project Management System** (非标自动化项目管理系统) designed for companies manufacturing custom automation equipment, including:
- ICT/FCT/EOL testing equipment
- Burning/aging equipment
- Vision inspection equipment
- Automated assembly lines

The system manages the complete project lifecycle from contract signing to after-sales service.

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend Framework | FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite (development) / MySQL (production) |
| Validation | Pydantic / pydantic-settings |
| Authentication | JWT (python-jose) |
| Password Hashing | passlib with bcrypt |
| ASGI Server | Uvicorn |

## Project Structure

```
non-standard-automation-pms/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API routes
│   │   ├── deps.py               # Dependency injection (get_db)
│   │   └── v1/
│   │       ├── api.py            # API router aggregation
│   │       └── endpoints/        # API endpoint modules
│   │           └── projects.py   # Project CRUD endpoints
│   ├── core/                     # Core configuration
│   │   ├── config.py             # Application settings (pydantic-settings)
│   │   └── security.py           # JWT auth, password hashing, permissions
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── base.py               # Base model, engine, session management
│   │   ├── enums.py              # All enum definitions
│   │   ├── user.py               # User, Role, Permission models
│   │   ├── project.py            # Project, Machine, Stage, Milestone models
│   │   ├── material.py           # Material, BOM, Supplier models
│   │   ├── purchase.py           # Purchase order models
│   │   ├── ecn.py                # Engineering Change Notice models
│   │   ├── acceptance.py         # Acceptance/validation models
│   │   ├── outsourcing.py        # Outsourcing vendor/order models
│   │   ├── alert.py              # Alert and exception models
│   │   └── organization.py       # Department organization models
│   └── schemas/                  # Pydantic schemas for API validation
│       ├── common.py             # Common response schemas
│       ├── auth.py               # Authentication schemas
│       ├── project.py            # Project request/response schemas
│       ├── material.py           # Material schemas
│       ├── purchase.py           # Purchase schemas
│       ├── ecn.py                # ECN schemas
│       ├── acceptance.py         # Acceptance schemas
│       ├── outsourcing.py        # Outsourcing schemas
│       └── alert.py              # Alert schemas
├── migrations/                   # SQL migration files
│   ├── *_sqlite.sql              # SQLite-specific migrations
│   └── *_mysql.sql               # MySQL-specific migrations
├── data/                         # SQLite database storage
│   └── app.db                    # SQLite database file
├── templates/                    # HTML templates (if any)
├── docs/                         # Additional documentation
├── attachments/                  # Diagrams and attachments
├── claude 设计方案/              # Design documents and specifications
├── init_db.py                    # Database initialization script
├── requirements.txt              # Python dependencies
└── *.md                          # Module design documentation (Chinese)
```

## Key Business Modules

### 1. Project Management (项目管理)
- **Models**: `Project`, `Machine`, `ProjectStage`, `ProjectStatus`, `ProjectMilestone`, `ProjectMember`, `ProjectCost`, `ProjectDocument`
- Projects follow a 9-stage lifecycle (S1-S9):
  - S1: Requirements Entry (需求进入)
  - S2: Solution Design (方案设计)
  - S3: Procurement (采购备料)
  - S4: Manufacturing (加工制造)
  - S5: Assembly & Testing (装配调试)
  - S6: Factory Acceptance Test - FAT (出厂验收)
  - S7: Packaging & Shipping (包装发运)
  - S8: Site Acceptance Test - SAT (现场安装)
  - S9: Warranty Close-out (质保结项)

### 2. Health Status (健康度)
- H1: Normal (Green)
- H2: At Risk (Yellow)
- H3: Blocked (Red)
- H4: Completed (Gray)

### 3. Material & Procurement (采购与物料)
- **Models**: `Material`, `MaterialCategory`, `Supplier`, `BomHeader`, `BomItem`, `PurchaseOrder`, `PurchaseOrderItem`, `GoodsReceipt`
- Material types: Standard, Mechanical, Electrical, Pneumatic, etc.

### 4. Engineering Change Notice - ECN (变更管理)
- **Models**: `Ecn`, `EcnEvaluation`, `EcnApproval`, `EcnTask`, `EcnAffectedMaterial`
- Change types: Design, Material, Process, Specification, Schedule

### 5. Acceptance Management (验收管理)
- **Models**: `AcceptanceTemplate`, `AcceptanceOrder`, `AcceptanceOrderItem`, `AcceptanceIssue`
- Types: FAT (Factory), SAT (Site), Final

### 6. Outsourcing (外协管理)
- **Models**: `OutsourcingVendor`, `OutsourcingOrder`, `OutsourcingDelivery`, `OutsourcingInspection`

### 7. Alerts & Exceptions (预警与异常)
- **Models**: `AlertRule`, `AlertRecord`, `ExceptionEvent`, `AlertStatistics`, `ProjectHealthSnapshot`
- Alert levels: Info, Warning, Critical, Urgent

## Development Commands

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database (creates data/app.db)
python3 init_db.py
```

### Running the Application
```bash
# Using uvicorn directly
uvicorn app.main:app --reload

# Or using python module
python3 -m app.main
```

### API Access
- API Base URL: `http://127.0.0.1:8000`
- OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Check: `GET /health`
- API Prefix: `/api/v1`

## Database Management

### Engine Configuration (`app/models/base.py`)
- Uses SQLite with `check_same_thread=False` and `StaticPool` for development
- MySQL support with connection pooling for production
- Foreign keys enabled via PRAGMA for SQLite

### Session Management
```python
from app.models.base import get_db_session

with get_db_session() as session:
    # Your database operations
    session.query(Project).all()
```

### Migration Naming Convention
- Format: `YYYYMMDD_module_name_{mysql|sqlite}.sql`
- Example: `20250712_project_management_sqlite.sql`

## Coding Conventions

### Models
- All models inherit from `Base` and optionally `TimestampMixin`
- Use `Column` with explicit `comment` parameter for Chinese documentation
- Define relationships with explicit `back_populates`
- Add database indexes via `__table_args__`

### Enums
- All enums defined in `app/models/enums.py`
- Inherit from both `str` and `Enum` for JSON serialization
- Use English keys with Chinese comments

### API Endpoints
- Use FastAPI's `APIRouter`
- Inject database session via `Depends(deps.get_db)`
- Return Pydantic response models
- Use HTTP status codes appropriately

### Schemas
- Use `from_attributes = True` (formerly `orm_mode`) for ORM compatibility
- Separate Create, Update, and Response schemas
- Use `Optional` for nullable fields

## Authentication & Authorization

### JWT Token Flow
1. Login via `/api/v1/auth/login` (to be implemented)
2. Token stored in Authorization header: `Bearer <token>`
3. Token decoded via `get_current_user` dependency

### Permission Checking
```python
from app.core.security import require_permission

@router.get("/protected")
async def protected_route(user = Depends(require_permission("project:read"))):
    pass
```

## Configuration

Environment variables can be set in `.env` file:
```
DEBUG=true
DATABASE_URL=mysql://user:pass@host:3306/dbname
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]
```

Key settings in `app/core/config.py`:
- `API_V1_PREFIX`: `/api/v1`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 1440 (24 hours)
- `DEFAULT_PAGE_SIZE`: 20
- `MAX_PAGE_SIZE`: 100
- `MAX_UPLOAD_SIZE`: 10MB

## Domain-Specific Terminology (中英对照)

| English | Chinese | Description |
|---------|---------|-------------|
| Project | 项目 | Main work unit |
| Machine | 设备/机台 | Equipment being built |
| BOM | 物料清单 | Bill of Materials |
| FAT | 出厂验收 | Factory Acceptance Test |
| SAT | 现场验收 | Site Acceptance Test |
| ECN | 工程变更通知 | Engineering Change Notice |
| PMC | 生产物料控制 | Production Material Control |
| Outsourcing | 外协 | External processing |
| Milestone | 里程碑 | Key project checkpoint |
| Health | 健康度 | Project status indicator |

## Design Documentation

Detailed design documents are available in Chinese:
- `非标自动化项目管理系统_设计文档.md` - System overview
- `项目管理模块_详细设计文档.md` - Project management module
- `采购与物料管理模块_详细设计文档.md` - Procurement module
- `变更管理模块_详细设计文档.md` - ECN module
- `验收管理模块_详细设计文档.md` - Acceptance module
- `外协管理模块_详细设计文档.md` - Outsourcing module
- `预警与异常管理模块_详细设计文档.md` - Alert module
- `权限管理模块_详细设计文档.md` - Permission module
- `角色管理模块_详细设计文档.md` - Role management

## Important Notes for AI Assistants

1. **Language**: Code uses English identifiers, but comments and documentation are in Chinese
2. **Date Format**: Use `YYYY-MM-DD` format consistently
3. **Amount Precision**: Use `Numeric(14, 2)` for monetary values
4. **Soft Delete**: Many models use `is_active` boolean rather than hard delete
5. **Timestamps**: All models with `TimestampMixin` have `created_at` and `updated_at`
6. **Project Codes**: Format is `PJyymmddxxx` (e.g., `PJ250708001`)
7. **Machine Codes**: Format is `PNxxx` (e.g., `PN001`)

## Testing

Currently no test suite is configured. When adding tests:
- Use pytest as the test framework
- Create `tests/` directory following the same structure as `app/`
- Use `reset_engine()` from `app/models/base.py` for test isolation

## Future Development Areas

Based on design documents, planned features include:
- Sales management (Lead to Cash flow)
- Progress tracking module
- Performance management
- Cost management
- Full API implementation for all modules
