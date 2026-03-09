#!/bin/bash
# 数据库同步脚本 - 多电脑数据同步方案
# 用法: ./sync-db.sh [export|import|auto|status]

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_PATH="$PROJECT_DIR/data/app.db"
BACKUP_DIR="$PROJECT_DIR/db-backups"
BACKUP_SQL="$BACKUP_DIR/backup-latest.sql"
BACKUP_ZIP="$BACKUP_DIR/backup-latest.zip"
METADATA_FILE="$BACKUP_DIR/backup-metadata.json"

# 确保备份目录存在
mkdir -p "$BACKUP_DIR"

# 显示帮助
show_help() {
    echo "数据库同步脚本 - 多电脑数据同步"
    echo ""
    echo "用法: ./sync-db.sh [命令]"
    echo ""
    echo "命令:"
    echo "  export     导出当前数据库到 db-backups/"
    echo "  import     从 db-backups/ 导入数据库"
    echo "  auto       自动模式：有更新则导出，无则跳过"
    echo "  status     显示数据库状态"
    echo "  clean      清理旧备份（保留最近5个）"
    echo "  help       显示帮助"
    echo ""
    echo "示例:"
    echo "  ./sync-db.sh export    # 主电脑：导出数据"
    echo "  git add db-backups/ && git commit -m '更新数据库'"
    echo "  git push"
    echo ""
    echo "  ./sync-db.sh import    # 另一台电脑：导入数据"
}

# 获取数据库信息
get_db_info() {
    if [ ! -f "$DB_PATH" ]; then
        echo "null"
        return
    fi
    
    local size=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null)
    local hash=$(md5 -q "$DB_PATH" 2>/dev/null || md5sum "$DB_PATH" 2>/dev/null | cut -d' ' -f1)
    local tables=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
    local records=$(sqlite3 "$DB_PATH" "SELECT SUM(count) FROM (SELECT COUNT(*) as count FROM sqlite_master WHERE type='table' UNION ALL SELECT 0);" 2>/dev/null || echo "0")
    
    echo "{\"size\":$size,\"hash\":\"$hash\",\"tables\":$tables,\"timestamp\":$(date +%s)}"
}

# 导出数据库
export_db() {
    echo -e "${BLUE}📤 导出数据库...${NC}"
    
    if [ ! -f "$DB_PATH" ]; then
        echo -e "${RED}❌ 数据库不存在: $DB_PATH${NC}"
        exit 1
    fi
    
    # 创建带时间戳的备份
    local timestamp=$(date +"%Y%m%d-%H%M%S")
    local dated_backup="$BACKUP_DIR/backup-$timestamp.sql"
    local dated_zip="$BACKUP_DIR/backup-$timestamp.zip"
    
    echo "  导出 SQL..."
    sqlite3 "$DB_PATH" ".dump" > "$dated_backup"
    
    echo "  压缩备份..."
    zip -j "$dated_zip" "$dated_backup" -x "*.zip" >/dev/null 2>&1
    
    # 更新 latest 链接
    cp "$dated_backup" "$BACKUP_SQL"
    cp "$dated_zip" "$BACKUP_ZIP"
    
    # 保存元数据
    local db_info=$(get_db_info)
    echo "{\"exported_at\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"file\":\"backup-$timestamp.sql\",\"db_info\":$db_info}" > "$METADATA_FILE"
    
    # 清理旧备份
    clean_old_backups
    
    local size=$(du -h "$dated_zip" | cut -f1)
    echo -e "${GREEN}✅ 导出完成: backup-$timestamp.zip ($size)${NC}"
    echo ""
    echo "下一步:"
    echo "  git add db-backups/"
    echo "  git commit -m 'sync: 更新数据库备份 $(date +%Y-%m-%d)'"
    echo "  git push"
}

# 导入数据库
import_db() {
    echo -e "${BLUE}📥 导入数据库...${NC}"
    
    if [ ! -f "$BACKUP_SQL" ]; then
        echo -e "${RED}❌ 备份文件不存在: $BACKUP_SQL${NC}"
        echo "请先在其他电脑上执行: ./sync-db.sh export"
        exit 1
    fi
    
    # 备份当前数据库
    if [ -f "$DB_PATH" ]; then
        local backup_name="data/app.db.backup-$(date +%Y%m%d-%H%M%S)"
        echo "  备份当前数据库 -> $backup_name"
        cp "$DB_PATH" "$PROJECT_DIR/$backup_name"
    fi
    
    # 导入新数据库
    echo "  导入 SQL..."
    rm -f "$DB_PATH"
    sqlite3 "$DB_PATH" < "$BACKUP_SQL"
    
    echo -e "${GREEN}✅ 导入完成${NC}"
    
    # 显示导入后的统计
    show_status
}

# 自动模式
auto_sync() {
    echo -e "${BLUE}🔄 自动同步模式...${NC}"
    
    # 检查是否有本地变更需要导出
    if [ -f "$DB_PATH" ] && [ -f "$METADATA_FILE" ]; then
        local current_hash=$(md5 -q "$DB_PATH" 2>/dev/null || md5sum "$DB_PATH" 2>/dev/null | cut -d' ' -f1)
        local last_hash=$(cat "$METADATA_FILE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('db_info',{}).get('hash',''))" 2>/dev/null)
        
        if [ "$current_hash" != "$last_hash" ]; then
            echo "检测到本地数据库变更，执行导出..."
            export_db
            echo ""
            echo -e "${YELLOW}⚠️  请手动提交到 GitHub:${NC}"
            echo "  git add db-backups/"
            echo "  git commit -m 'sync: 更新数据库'"
            echo "  git push"
        else
            echo -e "${GREEN}✅ 数据库未变更，跳过导出${NC}"
        fi
    else
        echo "首次运行，导出当前数据库..."
        export_db
    fi
    
    # 检查是否有远程更新需要导入
    if [ -f "$BACKUP_SQL" ]; then
        local backup_time=$(stat -f%m "$BACKUP_SQL" 2>/dev/null || stat -c%Y "$BACKUP_SQL" 2>/dev/null)
        local db_time=$(stat -f%m "$DB_PATH" 2>/dev/null || stat -c%Y "$DB_PATH" 2>/dev/null)
        
        if [ "$backup_time" -gt "$db_time" ]; then
            echo "检测到备份文件比当前数据库新，建议导入"
            echo "运行: ./sync-db.sh import"
        fi
    fi
}

# 显示状态
show_status() {
    echo -e "${BLUE}📊 数据库状态${NC}"
    echo ""
    
    if [ -f "$DB_PATH" ]; then
        local size=$(du -h "$DB_PATH" | cut -f1)
        echo -e "当前数据库: ${GREEN}$DB_PATH${NC}"
        echo "  大小: $size"
        
        # 统计表数量
        local tables=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "0")
        echo "  表数量: $tables"
        
        # 统计主要业务表的数据量
        echo ""
        echo "业务数据概览:"
        for table in users customers projects sales_orders opportunities quotes; do
            local count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
            printf "  %-20s %5s 条记录\n" "$table:" "$count"
        done
    else
        echo -e "${YELLOW}⚠️  数据库不存在${NC}"
    fi
    
    echo ""
    
    if [ -f "$BACKUP_SQL" ]; then
        local backup_size=$(du -h "$BACKUP_SQL" | cut -f1)
        local backup_time=$(stat -f%Sm "$BACKUP_SQL" 2>/dev/null || stat -c%y "$BACKUP_SQL" 2>/dev/null)
        echo -e "最新备份: ${GREEN}$BACKUP_SQL${NC}"
        echo "  大小: $backup_size"
        echo "  时间: $backup_time"
    else
        echo -e "${YELLOW}⚠️  备份文件不存在${NC}"
    fi
}

# 清理旧备份
clean_old_backups() {
    echo "  清理旧备份（保留最近5个）..."
    cd "$BACKUP_DIR"
    ls -t backup-*.sql 2>/dev/null | tail -n +6 | xargs -r rm -f
    ls -t backup-*.zip 2>/dev/null | tail -n +6 | xargs -r rm -f
    cd "$PROJECT_DIR"
}

# 主逻辑
case "${1:-auto}" in
    export|e)
        export_db
        ;;
    import|i)
        import_db
        ;;
    auto|a)
        auto_sync
        ;;
    status|s)
        show_status
        ;;
    clean|c)
        clean_old_backups
        echo -e "${GREEN}✅ 清理完成${NC}"
        ;;
    help|h|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}未知命令: $1${NC}"
        show_help
        exit 1
        ;;
esac
