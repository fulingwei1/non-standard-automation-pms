from fastapi import APIRouter
from app.api.v1.endpoints import (
    projects,
    customers,
    machines,
    milestones,
    members,
    stages,
    organization,
    auth,
    costs,
    documents,
    users,
    roles,
)

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(machines.router, prefix="/machines", tags=["machines"])
api_router.include_router(milestones.router, prefix="/milestones", tags=["milestones"])
api_router.include_router(members.router, prefix="/members", tags=["members"])
api_router.include_router(stages.router, prefix="/stages", tags=["stages"])
api_router.include_router(organization.router, prefix="/org", tags=["organization"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(costs.router, prefix="/costs", tags=["costs"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
