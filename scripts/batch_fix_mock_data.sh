#!/bin/bash

# 批量修复Mock数据的Shell脚本

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}开始批量修复Mock数据...${NC}"

# 需要修复的文件列表
FILES=(
  "frontend/src/pages/AdministrativeManagerWorkstation.jsx"
  "frontend/src/pages/AlertCenter.jsx"
  "frontend/src/pages/AlertStatistics.jsx"
  "frontend/src/pages/ArrivalManagement.jsx"
  "frontend/src/pages/ArrivalTrackingList.jsx"
  "frontend/src/pages/BudgetManagement.jsx"
  "frontend/src/pages/CostAnalysis.jsx"
  "frontend/src/pages/CustomerCommunication.jsx"
  "frontend/src/pages/Documents.jsx"
  "frontend/src/pages/ExceptionManagement.jsx"
  "frontend/src/pages/GoodsReceiptDetail.jsx"
  "frontend/src/pages/GoodsReceiptNew.jsx"
  "frontend/src/pages/PurchaseOrderDetail.jsx"
  "frontend/src/pages/PurchaseOrderFromBOM.jsx"
  "frontend/src/pages/PurchaseRequestDetail.jsx"
  "frontend/src/pages/PurchaseRequestList.jsx"
  "frontend/src/pages/PurchaseRequestNew.jsx"
  "frontend/src/pages/ScheduleBoard.jsx"
  "frontend/src/pages/ServiceAnalytics.jsx"
  "frontend/src/pages/ServiceRecord.jsx"
  "frontend/src/pages/ShortageAlert.jsx"
  "frontend/src/pages/SupplierManagementData.jsx"
  "frontend/src/pages/PermissionManagement.jsx"
)

# 统计
TOTAL=${#FILES[@]}
FIXED=0
SKIPPED=0

for FILE in "${FILES[@]}"; do
  if [ -f "$FILE" ]; then
    echo -e "处理: ${GREEN}$FILE${NC}"

    # 使用Python脚本修复单个文件
    python3 scripts/fix_single_file.py "$FILE"

    if [ $? -eq 0 ]; then
      ((FIXED++))
    else
      ((SKIPPED++))
    fi
  else
    echo -e "${RED}文件不存在: $FILE${NC}"
    ((SKIPPED++))
  fi
done

echo ""
echo -e "${GREEN}修复完成！${NC}"
echo "总计: $TOTAL 个文件"
echo -e "已修复: ${GREEN}$FIXED${NC} 个"
echo "跳过: $SKIPPED 个"
