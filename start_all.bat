@echo off
chcp 65001 >nul
title 社交匹配系统

set PROJECT_DIR=C:\Users\18151\Desktop\xiangmu\social-match-system
set PYTHON=C:\Users\18151\AppData\Local\Programs\Python\Python311\python.exe

echo =====================================
echo   社交匹配系统 — 一键启动
echo =====================================
echo.

:: 检查目录
if not exist "%PROJECT_DIR%" (
    echo [错误] 找不到项目目录: %PROJECT_DIR%
    pause
    exit /b 1
)

:: 关闭旧的 python 进程（确保是当前项目相关的）
echo [1/3] 清理旧进程...
for /f "tokens=2 delims=," %%a in ('tasklist /fi "imagename eq python.exe" /fo csv /nh 2^>nul') do (
    taskkill /F /PID %%a /T >nul 2>nul
)
timeout /t 1 /nobreak >nul

:: 启动后端
echo [2/3] 启动后端 (port 8001)...
start "SocialMatch-Backend" /D "%PROJECT_DIR%" "%PYTHON%" -m uvicorn backend.app:app --host 0.0.0.0 --port 8001
timeout /t 4 /nobreak >nul

:: 启动前端
echo [3/3] 启动前端 (port 8501)...
set STREAMLIT_SERVER_HEADLESS=true
start "SocialMatch-Frontend" /D "%PROJECT_DIR%" "%PYTHON%" -m streamlit run frontend/app.py --server.headless=true --server.port 8501

echo.
echo =====================================
echo   启动完成！
echo =====================================
echo.
echo   前端页面: http://localhost:8501
echo   后端 API: http://localhost:8001
echo.
echo   关闭新弹出的命令行窗口即可停止服务
echo.
echo   正在打开浏览器...
timeout /t 4 /nobreak >nul
start http://localhost:8501
