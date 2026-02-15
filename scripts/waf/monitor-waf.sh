#!/bin/bash
# WAF监控脚本
# 版本: 1.0.0
# 日期: 2026-02-15
# 用途: 实时监控WAF状态和拦截情况

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"
cd "$SCRIPT_DIR"

# 日志文件
ACCESS_LOG="logs/nginx/access.log"
ERROR_LOG="logs/nginx/error.log"
MODSEC_LOG="logs/nginx/modsec_audit.log"
BLOCKED_LOG="logs/nginx/blocked.log"

# 告警配置
ALERT_THRESHOLD=${ALERT_THRESHOLD:-10}  # 每分钟拦截次数阈值
ALERT_WEBHOOK=${ALERT_WEBHOOK_URL:-""}

# 显示头部
show_header() {
    clear
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  WAF实时监控${NC}"
    echo -e "${BLUE}  版本: 1.0.0${NC}"
    echo -e "${BLUE}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 检查容器状态
check_container_status() {
    echo -e "${CYAN}[容器状态]${NC}"
    
    if docker ps | grep -q "pms-waf"; then
        echo -e "${GREEN}✅ WAF容器运行中${NC}"
        
        # 获取容器资源使用
        stats=$(docker stats pms-waf --no-stream --format "CPU: {{.CPUPerc}}, MEM: {{.MemUsage}}")
        echo -e "资源使用: $stats"
    else
        echo -e "${RED}❌ WAF容器未运行${NC}"
        echo "请先启动WAF: bash scripts/waf/deploy-waf.sh"
        exit 1
    fi
    echo ""
}

# 统计访问日志
stats_access_log() {
    echo -e "${CYAN}[访问统计 - 最近1分钟]${NC}"
    
    if [ ! -f "$ACCESS_LOG" ]; then
        echo -e "${YELLOW}⚠️  访问日志不存在${NC}"
        return
    fi
    
    # 最近1分钟的日志
    one_min_ago=$(date -d '1 minute ago' '+%d/%b/%Y:%H:%M' 2>/dev/null || date -v-1M '+%d/%b/%Y:%H:%M')
    recent_logs=$(grep "$one_min_ago" "$ACCESS_LOG" 2>/dev/null || echo "")
    
    if [ -z "$recent_logs" ]; then
        echo "请求数: 0"
    else
        total_requests=$(echo "$recent_logs" | wc -l)
        status_200=$(echo "$recent_logs" | grep -c '" 200 ' || echo 0)
        status_403=$(echo "$recent_logs" | grep -c '" 403 ' || echo 0)
        status_404=$(echo "$recent_logs" | grep -c '" 404 ' || echo 0)
        status_500=$(echo "$recent_logs" | grep -c '" 50[0-9] ' || echo 0)
        
        echo -e "总请求数: ${BLUE}$total_requests${NC}"
        echo -e "  └─ 200 OK: ${GREEN}$status_200${NC}"
        echo -e "  └─ 403 Forbidden: ${RED}$status_403${NC}"
        echo -e "  └─ 404 Not Found: ${YELLOW}$status_404${NC}"
        echo -e "  └─ 5xx Error: ${RED}$status_500${NC}"
    fi
    echo ""
}

# 统计WAF拦截
stats_waf_blocks() {
    echo -e "${CYAN}[WAF拦截统计 - 最近1分钟]${NC}"
    
    if [ ! -f "$BLOCKED_LOG" ]; then
        echo -e "${YELLOW}⚠️  拦截日志不存在${NC}"
        return
    fi
    
    # 最近1分钟的拦截
    one_min_ago=$(date -d '1 minute ago' '+%d/%b/%Y:%H:%M' 2>/dev/null || date -v-1M '+%d/%b/%Y:%H:%M')
    recent_blocks=$(grep "$one_min_ago" "$BLOCKED_LOG" 2>/dev/null || echo "")
    
    if [ -z "$recent_blocks" ]; then
        echo -e "拦截次数: ${GREEN}0${NC}"
    else
        block_count=$(echo "$recent_blocks" | wc -l)
        
        if [ "$block_count" -ge "$ALERT_THRESHOLD" ]; then
            echo -e "拦截次数: ${RED}$block_count (超过阈值 $ALERT_THRESHOLD)${NC}"
            send_alert "WAF拦截次数过高" "$block_count 次/分钟"
        else
            echo -e "拦截次数: ${YELLOW}$block_count${NC}"
        fi
        
        # 分析拦截原因
        echo ""
        echo "拦截原因TOP 5:"
        echo "$recent_blocks" | grep -oP '(?<=msg:)[^,]+' | sort | uniq -c | sort -rn | head -5 | while read count msg; do
            echo -e "  ${RED}$count${NC} - $msg"
        done
    fi
    echo ""
}

# 显示TOP攻击IP
show_top_attackers() {
    echo -e "${CYAN}[TOP攻击IP - 最近1小时]${NC}"
    
    if [ ! -f "$BLOCKED_LOG" ]; then
        echo -e "${YELLOW}⚠️  拦截日志不存在${NC}"
        return
    fi
    
    # 最近1小时的拦截
    one_hour_ago=$(date -d '1 hour ago' '+%d/%b/%Y:%H' 2>/dev/null || date -v-1H '+%d/%b/%Y:%H')
    recent_blocks=$(grep "$one_hour_ago" "$BLOCKED_LOG" 2>/dev/null || echo "")
    
    if [ -z "$recent_blocks" ]; then
        echo "暂无攻击记录"
    else
        echo "$recent_blocks" | awk '{print $1}' | sort | uniq -c | sort -rn | head -10 | while read count ip; do
            echo -e "  ${RED}$count${NC} - $ip"
        done
    fi
    echo ""
}

# 显示最近错误
show_recent_errors() {
    echo -e "${CYAN}[最近错误 - 最新10条]${NC}"
    
    if [ ! -f "$ERROR_LOG" ]; then
        echo -e "${YELLOW}⚠️  错误日志不存在${NC}"
        return
    fi
    
    tail -10 "$ERROR_LOG" | while read line; do
        if echo "$line" | grep -q "error"; then
            echo -e "${RED}$line${NC}"
        else
            echo "$line"
        fi
    done
    echo ""
}

# 显示ModSecurity统计
show_modsecurity_stats() {
    echo -e "${CYAN}[ModSecurity统计 - 最近1小时]${NC}"
    
    if [ ! -f "$MODSEC_LOG" ]; then
        echo -e "${YELLOW}⚠️  ModSecurity日志不存在${NC}"
        return
    fi
    
    # 最近1小时的日志
    one_hour_ago=$(date -d '1 hour ago' '+%d/%b/%Y:%H' 2>/dev/null || date -v-1H '+%d/%b/%Y:%H')
    recent_modsec=$(grep "$one_hour_ago" "$MODSEC_LOG" 2>/dev/null || echo "")
    
    if [ -z "$recent_modsec" ]; then
        echo "暂无ModSecurity事件"
    else
        total_events=$(echo "$recent_modsec" | grep -c "ModSecurity:" || echo 0)
        echo -e "总事件数: ${BLUE}$total_events${NC}"
        
        # 攻击类型统计
        echo ""
        echo "攻击类型分布:"
        echo "$recent_modsec" | grep -oP '(?<=\[tag ")[^"]+' | sort | uniq -c | sort -rn | head -5 | while read count tag; do
            echo -e "  ${YELLOW}$count${NC} - $tag"
        done
    fi
    echo ""
}

# 发送告警
send_alert() {
    local title="$1"
    local message="$2"
    
    if [ -z "$ALERT_WEBHOOK" ]; then
        return
    fi
    
    # 企业微信格式
    if echo "$ALERT_WEBHOOK" | grep -q "qyapi.weixin.qq.com"; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"msgtype\": \"markdown\",
                \"markdown\": {
                    \"content\": \"⚠️ **WAF告警**\n\n**标题**: $title\n**详情**: $message\n**时间**: $(date '+%Y-%m-%d %H:%M:%S')\"
                }
            }" > /dev/null
    fi
    
    # 钉钉格式
    if echo "$ALERT_WEBHOOK" | grep -q "oapi.dingtalk.com"; then
        curl -s -X POST "$ALERT_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"msgtype\": \"markdown\",
                \"markdown\": {
                    \"title\": \"$title\",
                    \"text\": \"⚠️ **WAF告警**\n\n**标题**: $title\n**详情**: $message\n**时间**: $(date '+%Y-%m-%d %H:%M:%S')\"
                }
            }" > /dev/null
    fi
}

# 交互式监控
interactive_monitor() {
    while true; do
        show_header
        check_container_status
        stats_access_log
        stats_waf_blocks
        show_top_attackers
        show_recent_errors
        show_modsecurity_stats
        
        echo -e "${CYAN}[操作]${NC}"
        echo "按 Ctrl+C 退出监控"
        echo "自动刷新中..."
        echo ""
        
        # 每5秒刷新一次
        sleep 5
    done
}

# 单次统计
one_time_stats() {
    show_header
    check_container_status
    stats_access_log
    stats_waf_blocks
    show_top_attackers
    show_recent_errors
    show_modsecurity_stats
}

# 导出报告
export_report() {
    local report_file="logs/waf/waf-report-$(date '+%Y%m%d-%H%M%S').txt"
    mkdir -p logs/waf
    
    echo "生成WAF监控报告..."
    
    {
        echo "========================================"
        echo "WAF监控报告"
        echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================"
        echo ""
        
        check_container_status
        stats_access_log
        stats_waf_blocks
        show_top_attackers
        show_recent_errors
        show_modsecurity_stats
    } > "$report_file"
    
    echo -e "${GREEN}✅ 报告已生成: $report_file${NC}"
}

# 主菜单
show_menu() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  WAF监控工具${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "1. 实时监控（自动刷新）"
    echo "2. 单次统计"
    echo "3. 导出报告"
    echo "4. 查看完整日志"
    echo "5. 退出"
    echo ""
    read -p "请选择操作 [1-5]: " choice
    
    case $choice in
        1)
            interactive_monitor
            ;;
        2)
            one_time_stats
            ;;
        3)
            export_report
            ;;
        4)
            echo ""
            echo "可用日志文件:"
            echo "  1. 访问日志: $ACCESS_LOG"
            echo "  2. 错误日志: $ERROR_LOG"
            echo "  3. WAF拦截日志: $BLOCKED_LOG"
            echo "  4. ModSecurity审计日志: $MODSEC_LOG"
            echo ""
            read -p "选择要查看的日志 [1-4]: " log_choice
            case $log_choice in
                1) tail -f "$ACCESS_LOG" ;;
                2) tail -f "$ERROR_LOG" ;;
                3) tail -f "$BLOCKED_LOG" ;;
                4) tail -f "$MODSEC_LOG" ;;
                *) echo "无效选择" ;;
            esac
            ;;
        5)
            echo "退出监控"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择${NC}"
            show_menu
            ;;
    esac
}

# 主函数
main() {
    # 检查参数
    if [ "$1" = "--watch" ] || [ "$1" = "-w" ]; then
        interactive_monitor
    elif [ "$1" = "--report" ] || [ "$1" = "-r" ]; then
        export_report
    elif [ "$1" = "--stats" ] || [ "$1" = "-s" ]; then
        one_time_stats
    else
        show_menu
    fi
}

# 执行主函数
main "$@"
