@echo off
echo ==========================================
echo    启动禅道MCP阶段四Bug管理测试服务器
echo ==========================================
echo.

cd /d "%~dp0"

echo 正在启动阶段四Bug管理测试服务器...
echo 服务器地址: http://localhost:8082
echo 功能特性:
echo   - Bug列表查询 (支持多种过滤条件)
echo   - 用户列表查询
echo   - 功能模块查询
echo   - 数据统计展示
echo   - 可视化测试界面
echo.
echo 按 Ctrl+C 停止服务器
echo.

python test\test_stage_four_http.py

pause
