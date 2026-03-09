@echo off
chcp 65001 >nul
:: 非标自动化 PMS 开发环境启动脚本 (Windows)
:: 用法: 双击运行 start-dev.bat

echo 🚀 启动非标自动化 PMS 开发环境...

:: 获取项目目录
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo 📍 项目目录: %PROJECT_DIR%

:: ========== 步骤1: 同步种子数据 ==========
echo.
echo 🌱 步骤1: 同步演示数据...
if exist "scripts\seed_blm_bem.py" (
    echo 运行种子数据脚本...
    python3 scripts\seed_blm_bem.py
    echo ✅ 演示数据同步完成
) else (
    echo ❌ 种子脚本不存在: scripts\seed_blm_bem.py
    pause
    exit /b 1
)

:: ========== 步骤2: 启动后端 ==========
echo.
echo 🔧 步骤2: 启动后端服务 (端口 8002)...

:: 检查端口是否被占用
netstat -ano | findstr :8002 >nul
if %errorlevel% == 0 (
    echo ⚠️  端口 8002 已被占用，尝试关闭现有进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002') do taskkill /PID %%a /F >nul 2>&1
    timeout /t 1 /nobreak >nul
)

:: 启动后端
if exist ".env" (
    for /f "usebackq tokens=*" %%a in (".env") do set "%%a"
)
start "Backend" python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

echo ✅ 后端已启动

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: ========== 步骤3: 启动前端 ==========
echo.
echo 💻 步骤3: 启动前端服务...
cd frontend

:: 检查 node_modules
if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

:: 启动前端
start "Frontend" npm run dev

cd /d "%PROJECT_DIR%"

echo ✅ 前端已启动

:: ========== 完成 ==========
echo.
echo 🎉 所有服务已启动!
echo.
echo 📊 访问地址:
echo    后端 API: http://localhost:8002
echo    API 文档: http://localhost:8002/docs
echo    前端页面: http://localhost:5173 或 http://localhost:5175
echo.
echo 👤 默认登录账户:
echo    fulingwei / admin123 (总经理)
echo    zhangzq / 123456 (销售总监)
echo    limh / 123456 (技术总监)
echo.
echo 按任意键停止所有服务...
pause >nul

:: 停止服务
echo.
echo 🛑 正在停止服务...
taskkill /FI "WINDOWTITLE eq Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend*" /F >nul 2>&1
echo ✅ 服务已停止
