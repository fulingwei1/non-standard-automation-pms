#!/bin/bash

# Team 6: 检查其他teams的进度
# 每5分钟检查一次，持续25分钟

WORK_DIR=~/.openclaw/workspace/non-standard-automation-pms
START_TIME=$(date +%s)
CHECK_INTERVAL=300  # 5分钟
MAX_WAIT=1500       # 25分钟

echo "=========================================="
echo "Team 6: 系统健康度报告 - 等待其他teams完成"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# 预期的交付报告文件名模式
TEAM_REPORTS=(
    "*team1*sqlalchemy*"
    "*team1*关系修复*"
    "*team2*api*route*"
    "*team2*路由*"
    "*team3*auth*"
    "*team3*认证*"
    "*team4*core*api*"
    "*team4*核心*"
    "*team5*rate*limit*"
    "*team5*限流*"
)

check_reports() {
    local found=0
    echo "检查时间: $(date '+%H:%M:%S')"
    echo "----------------------------------------"
    
    for pattern in "${TEAM_REPORTS[@]}"; do
        files=$(find "$WORK_DIR" -type f -name "$pattern" -mmin -30 2>/dev/null)
        if [ -n "$files" ]; then
            echo "✅ 发现: $files"
            ((found++))
        fi
    done
    
    echo "已找到: $found 个team报告"
    echo "----------------------------------------"
    echo ""
    
    return $found
}

# 主循环
while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - START_TIME))
    
    echo "已等待: $((elapsed / 60)) 分钟"
    
    check_reports
    reports_found=$?
    
    # 如果找到至少3个reports，或者超过25分钟，则退出
    if [ $reports_found -ge 3 ] || [ $elapsed -ge $MAX_WAIT ]; then
        echo "=========================================="
        if [ $reports_found -ge 3 ]; then
            echo "✅ 已找到足够的team报告，开始整合"
        else
            echo "⏰ 已等待25分钟，开始基于现有信息生成报告"
        fi
        echo "=========================================="
        break
    fi
    
    echo "⏳ 继续等待... (下次检查: 5分钟后)"
    echo ""
    sleep $CHECK_INTERVAL
done

echo ""
echo "检查完成，准备生成最终报告"
