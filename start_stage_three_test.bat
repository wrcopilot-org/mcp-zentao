@echo off
echo ==========================================
echo    启动禅道MCP阶段三功能测试服务器
echo ==========================================
echo.

cd /d "%~dp0"

echo 正在启动阶段三测试服务器...
echo 服务器地址: http://localhost:8081
echo 功能特性:
echo   - 产品列表查询
echo   - 通过产品名获取相关项目
echo   - 可视化测试界面
echo   - JSON格式数据展示
echo.
echo 按 Ctrl+C 停止服务器
echo.

python test\test_stage_three_http.py

pause
