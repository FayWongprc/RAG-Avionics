@echo off
echo ========================================
echo   启动 FastAPI 后端服务
echo ========================================
echo.

REM 从项目根目录运行，确保能找到 rag_avionics 模块
python backend/main.py

pause
