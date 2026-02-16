#!/bin/bash

echo "检查各模块的prefix定义："
echo "=" | head -c 60
echo ""

grep -n "router = APIRouter(prefix=" \
  app/api/v1/endpoints/roles.py \
  app/api/v1/endpoints/permissions.py \
  app/api/v1/endpoints/inventory/inventory_router.py \
  app/api/v1/endpoints/shortage/__init__.py \
  app/api/v1/endpoints/rd_project/__init__.py \
  app/api/v1/endpoints/approvals.py \
  app/api/v1/endpoints/presale/__init__.py \
  2>/dev/null | head -20
