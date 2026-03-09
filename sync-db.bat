@echo off
chcp 65001 >nul
:: 数据库同步脚本 - Windows版本
:: 用法: sync-db.bat [export|import|status]

setlocal enabledelayedexpansion

:: 配置
set "PROJECT_DIR=%~dp0"
set "DB_PATH=%PROJECT_DIR%data\app.db"
set "BACKUP_DIR=%PROJECT_DIR%db-backups"
set "BACKUP_SQL=%BACKUP_DIR%\backup-latest.sql"
set "METADATA_FILE=%BACKUP_DIR%\backup-metadata.json"

cd /d "%PROJECT_DIR%"

:: 确保备份目录存在
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: 显示帮助
if "%~1"=="help" goto :show_help
if "%~1"=="h" goto :show_help
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1"=="" goto :show_help

:: 主逻辑
goto :main

:show_help
echo 数据库同步脚本 - 多电脑数据同步
echo.
echo 用法: sync-db.bat [命令]
echo.
echo 命令:
echo   export     导出当前数据库到 db-backups\
echo   import     从 db-backups\ 导入数据库
echo   status     显示数据库状态
echo   help       显示帮助
echo.
echo 示例:
echo   sync-db.bat export    主电脑：导出数据
echo   git add db-backups\ ^&^& git commit -m "更新数据库"
echo   git push
echo.
echo   sync-db.bat import    另一台电脑：导入数据
goto :eof

:main
if "%~1"=="export" goto :export_db
if "%~1"=="e" goto :export_db
if "%~1"=="import" goto :import_db
if "%~1"=="i" goto :import_db
if "%~1"=="status" goto :show_status
if "%~1"=="s" goto :show_status
echo 未知命令: %~1
goto :show_help

:export_db
echo 📤 导出数据库...

if not exist "%DB_PATH%" (
    echo ❌ 数据库不存在: %DB_PATH%
    exit /b 1
)

:: 创建带时间戳的备份
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set mytime=%%a%%b)
set "timestamp=!mydate!-!mytime!"
set "dated_backup=%BACKUP_DIR%\backup-!timestamp!.sql"

:: 注意：Windows 需要 sqlite3.exe，如果没有需要先安装
echo   导出 SQL...
if exist "C:\Program Files\SQLite3\sqlite3.exe" (
    "C:\Program Files\SQLite3\sqlite3.exe" "%DB_PATH%" ".dump" > "!dated_backup!"
) else if exist "sqlite3.exe" (
    sqlite3.exe "%DB_PATH%" ".dump" > "!dated_backup!"
) else (
    echo ⚠️  未找到 sqlite3，尝试使用 Python...
    python3 -c "import sqlite3; conn = sqlite3.connect('%DB_PATH%'); print('\n'.join(conn.iterdump()))" > "!dated_backup!"
)

:: 更新 latest 链接
copy "!dated_backup!" "%BACKUP_SQL%" >nul

echo ✅ 导出完成: backup-!timestamp!.sql
echo.
echo 下一步:
echo   git add db-backups\
echo   git commit -m "sync: 更新数据库"
echo   git push
goto :eof

:import_db
echo 📥 导入数据库...

if not exist "%BACKUP_SQL%" (
    echo ❌ 备份文件不存在: %BACKUP_SQL%
    echo 请先在其他电脑上执行: sync-db.bat export
    exit /b 1
)

:: 备份当前数据库
if exist "%DB_PATH%" (
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set mytime=%%a%%b)
    set "backup_name=data\app.db.backup-!mydate!-!mytime!"
    echo   备份当前数据库 -^> !backup_name!
    copy "%DB_PATH%" "!backup_name!" >nul
)

:: 导入新数据库
echo   导入 SQL...
del /f "%DB_PATH%" 2>nul

if exist "C:\Program Files\SQLite3\sqlite3.exe" (
    "C:\Program Files\SQLite3\sqlite3.exe" "%DB_PATH%" < "%BACKUP_SQL%"
) else if exist "sqlite3.exe" (
    sqlite3.exe "%DB_PATH%" < "%BACKUP_SQL%"
) else (
    echo ⚠️  未找到 sqlite3，请手动导入或使用 Python
    echo Python 导入命令:
    echo   python3 -c "import sqlite3; conn = sqlite3.connect('%DB_PATH%'); f = open('%BACKUP_SQL%'); conn.executescript(f.read()); conn.close()"
)

echo ✅ 导入完成
goto :show_status

:show_status
echo 📊 数据库状态
echo.

if exist "%DB_PATH%" (
    for %%I in ("%DB_PATH%") do (
        echo 当前数据库: %%~nxI
        echo   大小: %%~zI bytes
    )
    
    :: 统计表数量（如果有 sqlite3）
    if exist "C:\Program Files\SQLite3\sqlite3.exe" (
        for /f %%a in ('"C:\Program Files\SQLite3\sqlite3.exe" "%DB_PATH%" "SELECT COUNT(*) FROM sqlite_master WHERE type=\'table\';"') do (
            echo   表数量: %%a
        )
    )
) else (
    echo ⚠️  数据库不存在
)

echo.

if exist "%BACKUP_SQL%" (
    for %%I in ("%BACKUP_SQL%") do (
        echo 最新备份: %%~nxI
        echo   大小: %%~zI bytes
    )
) else (
    echo ⚠️  备份文件不存在
)
goto :eof
