@echo off
echo 运行禅道MCP服务器测试...
echo.

cd /d "%~dp0"

echo 安装测试依赖包...
python -m pip install pytest

echo.
echo 运行数据库连接测试...
python test\test_zentao_database.py

echo.
echo 运行MCP功能测试...
python test\test_zentao_mcp.py

echo.
echo 运行pytest测试...
python -m pytest test\test_zentao_database.py -v

pause
