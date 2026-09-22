@echo off
chcp 65001 >nul
REM ============================================================
REM  eufy AI HomeCare 一键启动脚本（Windows）
REM  先启动后端，等待 3 秒，再启动前端
REM ============================================================

set "ROOT=%~dp0"
set "BACKEND=%ROOT%rebucca-main\rebucca-main"
set "FRONTEND=%ROOT%frontend"

echo [1/2] 启动后端 Django ^(http://localhost:8000^) ...
start "eufy Backend :8000" cmd /k "cd /d "%BACKEND%" && python manage.py runserver 0.0.0.0:8000"

echo 等待 3 秒 ...
timeout /t 3 /nobreak >nul

echo [2/2] 启动前端 Vite ^(http://localhost:5173^) ...
start "eufy Frontend :5173" cmd /k "cd /d "%FRONTEND%" && npm run dev"

echo.
echo ============================================================
echo  后端地址 : http://localhost:8000
echo  接口文档 : http://localhost:8000/docs
echo  ReDoc    : http://localhost:8000/redoc
echo  前端地址 : http://localhost:5173
echo  默认账号 : admin / admin888
echo ============================================================
echo.
pause
