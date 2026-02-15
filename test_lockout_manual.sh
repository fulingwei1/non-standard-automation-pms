#!/bin/bash

# 账户锁定机制手动测试脚本

echo "========================================"
echo "账户锁定机制手动测试"
echo "========================================"
echo ""

API_BASE="http://localhost:8000/api/v1"
TEST_USERNAME="lockout_test_user_$(date +%s)"
WRONG_PASSWORD="wrongpassword123"

echo "测试用户名: $TEST_USERNAME"
echo ""

echo "步骤1: 5次失败登录..."
for i in {1..5}; do
  echo "  尝试 $i/5..."
  RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=${TEST_USERNAME}&password=${WRONG_PASSWORD}")
  
  STATUS_CODE=$(echo "$RESPONSE" | jq -r '.status_code // 0')
  ERROR_CODE=$(echo "$RESPONSE" | jq -r '.detail.error_code // "unknown"')
  MESSAGE=$(echo "$RESPONSE" | jq -r '.detail.message // .detail // "unknown"')
  
  echo "    状态码: $STATUS_CODE, 错误: $ERROR_CODE"
  echo "    消息: $MESSAGE"
  echo ""
  
  sleep 1
done

echo "步骤2: 第6次尝试（应该被锁定）..."
RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${TEST_USERNAME}&password=${WRONG_PASSWORD}")

STATUS_CODE=$(echo "$RESPONSE" | jq -r '.status_code // 0')
ERROR_CODE=$(echo "$RESPONSE" | jq -r '.detail.error_code // "unknown"')
MESSAGE=$(echo "$RESPONSE" | jq -r '.detail.message // .detail // "unknown"')

echo "  状态码: $STATUS_CODE"
echo "  错误码: $ERROR_CODE"
echo "  消息: $MESSAGE"
echo ""

if [ "$ERROR_CODE" = "ACCOUNT_LOCKED" ]; then
  echo "✅ 测试通过！账户已成功锁定。"
else
  echo "❌ 测试失败！预期锁定但未锁定。"
fi

echo ""
echo "========================================"
echo "测试完成"
echo "========================================"
echo ""
echo "提示：如需测试解锁功能，请使用管理员账户调用："
echo "  POST ${API_BASE}/admin/account-lockout/unlock"
echo "  Body: {\"username\": \"$TEST_USERNAME\"}"
