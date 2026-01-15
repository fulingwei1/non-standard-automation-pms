#!/bin/bash
#
# 带登录的 API 冒烟测试（最小关键链路检查）
#
# 你可以把“冒烟测试”理解为：只检查系统最关键的一小组功能是否能跑通，
# 比如：后端能启动、能登录拿到 token、带 token 的核心接口能返回 200。
#
# 用法：
#   bash scripts/smoke_auth_api.sh
#
# 常用参数：
#   --no-seed            不运行 create_demo_users.py（默认会运行，保证演示账号可登录）
#   --no-start           不自动启动后端（默认：后端没跑就自动启动，测试完自动关闭）
#   --base-url URL       默认 http://127.0.0.1:8000
#   --user USER          默认 chairman
#   --password PASS      默认 123456
#
# 也支持环境变量：
#   BASE_URL, SMOKE_USER, SMOKE_PASS
#
set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
SMOKE_USER="${SMOKE_USER:-chairman}"
SMOKE_PASS="${SMOKE_PASS:-123456}"

RUN_SEED=1
ALLOW_START=1

print_help() {
  sed -n '1,80p' "$0"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h)
      print_help
      exit 0
      ;;
    --no-seed)
      RUN_SEED=0
      shift
      ;;
    --no-start)
      ALLOW_START=0
      shift
      ;;
    --base-url)
      BASE_URL="${2:-}"
      if [ -z "$BASE_URL" ]; then
        echo -e "${RED}错误: --base-url 需要一个 URL${NC}" >&2
        exit 2
      fi
      shift 2
      ;;
    --user)
      SMOKE_USER="${2:-}"
      if [ -z "$SMOKE_USER" ]; then
        echo -e "${RED}错误: --user 需要一个用户名${NC}" >&2
        exit 2
      fi
      shift 2
      ;;
    --password)
      SMOKE_PASS="${2:-}"
      if [ -z "$SMOKE_PASS" ]; then
        echo -e "${RED}错误: --password 需要一个密码${NC}" >&2
        exit 2
      fi
      shift 2
      ;;
    *)
      echo -e "${RED}未知参数: $1${NC}" >&2
      echo -e "${YELLOW}提示: 使用 --help 查看用法${NC}" >&2
      exit 2
      ;;
  esac
done

API_V1="$BASE_URL/api/v1"
LOG_DIR="logs"
BACKEND_LOG="$LOG_DIR/smoke_backend_auth.log"
SEED_LOG="$LOG_DIR/smoke_seed_demo_users.log"

mkdir -p "$LOG_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  带登录 API 冒烟测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}目标后端: ${NC}${BASE_URL}"
echo -e "${YELLOW}登录账号: ${NC}${SMOKE_USER}"
echo ""

backend_pid=""
backend_started=0

cleanup() {
  if [ "$backend_started" -eq 1 ] && [ -n "${backend_pid:-}" ]; then
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

wait_for_health() {
  local url="$1"
  for i in {1..80}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
    if [ "$backend_started" -eq 1 ] && [ -n "${backend_pid:-}" ]; then
      if ! kill -0 "$backend_pid" 2>/dev/null; then
        echo -e "${RED}后端进程已退出，查看日志: ${BACKEND_LOG}${NC}" >&2
        tail -n 120 "$BACKEND_LOG" >&2 || true
        return 1
      fi
    fi
  done
  return 1
}

echo -e "${YELLOW}[1/4] 检查后端是否已运行...${NC}"
if curl -fsS "$BASE_URL/health" >/dev/null 2>&1; then
  echo -e "${GREEN}✓ 后端已运行${NC}"
else
  if [ "$ALLOW_START" -ne 1 ]; then
    echo -e "${RED}✗ 后端未运行，且已指定 --no-start（不自动启动）${NC}" >&2
    echo -e "${YELLOW}请先启动后端：python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000${NC}" >&2
    exit 1
  fi

  echo -e "${YELLOW}后端未运行，自动启动中...${NC}"
  echo -e "${BLUE}后端日志: ${BACKEND_LOG}${NC}"
  rm -f "$BACKEND_LOG" 2>/dev/null || true
  ENABLE_SCHEDULER=false DEBUG=true python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning >"$BACKEND_LOG" 2>&1 &
  backend_pid=$!
  backend_started=1

  if ! wait_for_health "$BASE_URL/health"; then
    echo -e "${RED}✗ 后端启动超时/失败，查看日志: ${BACKEND_LOG}${NC}" >&2
    tail -n 160 "$BACKEND_LOG" >&2 || true
    exit 1
  fi
  echo -e "${GREEN}✓ 后端已就绪${NC}"
fi
echo ""

echo -e "${YELLOW}[2/4]（可选）刷新演示账号密码/角色...${NC}"
if [ "$RUN_SEED" -eq 1 ]; then
  if python3 create_demo_users.py >"$SEED_LOG" 2>&1; then
    echo -e "${GREEN}✓ 演示账号已刷新（确保密码可用）${NC}"
  else
    echo -e "${RED}✗ 刷新演示账号失败${NC}" >&2
    echo -e "${YELLOW}日志: ${SEED_LOG}${NC}" >&2
    tail -n 120 "$SEED_LOG" >&2 || true
    exit 1
  fi
else
  echo -e "${YELLOW}跳过（--no-seed）${NC}"
fi
echo ""

echo -e "${YELLOW}[3/4] 登录获取 access_token...${NC}"
login_raw="$(curl -sS -w '\n%{http_code}' -X POST \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=${SMOKE_USER}" \
  --data-urlencode "password=${SMOKE_PASS}" \
  "${API_V1}/auth/login")"
login_body="$(echo "$login_raw" | sed '$d')"
login_code="$(echo "$login_raw" | tail -n 1)"

if [ "$login_code" != "200" ]; then
  echo -e "${RED}✗ 登录失败（HTTP ${login_code}）${NC}" >&2
  echo "$login_body" | python3 -m json.tool 2>/dev/null || echo "$login_body" >&2
  if [ -f "$BACKEND_LOG" ]; then
    echo -e "${YELLOW}后端日志（末尾 80 行）：${NC}" >&2
    tail -n 80 "$BACKEND_LOG" >&2 || true
  fi
  exit 1
fi

token="$(echo "$login_body" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null || true)"
if [ -z "$token" ]; then
  echo -e "${RED}✗ 登录返回里没有 access_token${NC}" >&2
  echo "$login_body" >&2
  exit 1
fi
echo -e "${GREEN}✓ 登录成功${NC}"
echo ""

check_get_200() {
  local name="$1"
  local url="$2"
  local resp body code
  resp="$(curl -sS -w '\n%{http_code}' -H "Authorization: Bearer ${token}" "$url")"
  body="$(echo "$resp" | sed '$d')"
  code="$(echo "$resp" | tail -n 1)"
  if [ "$code" != "200" ]; then
    echo -e "${RED}✗ ${name} 失败（HTTP ${code}）${NC}" >&2
    echo -e "${YELLOW}URL: ${url}${NC}" >&2
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body" >&2
    exit 1
  fi
  echo -e "${GREEN}✓ ${name}${NC}"
}

echo -e "${YELLOW}[4/4] 带 token 调用关键接口...${NC}"
check_get_200 "auth/me（当前用户信息）" "${API_V1}/auth/me"
check_get_200 "roles/my/nav-groups（导航菜单）" "${API_V1}/roles/my/nav-groups"
check_get_200 "users（用户列表）" "${API_V1}/users/?page=1&page_size=2"
check_get_200 "projects（项目列表）" "${API_V1}/projects/?page=1&page_size=1"
check_get_200 "alerts（预警列表）" "${API_V1}/alerts?page=1&page_size=1"
check_get_200 "shortage-alerts（缺料预警列表）" "${API_V1}/shortage-alerts/?page=1&page_size=1"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ 冒烟测试通过（关键链路 OK）${NC}"
echo -e "${GREEN}========================================${NC}"
