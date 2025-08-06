@echo off
echo 启动禅道MCP服务器...
echo.

cd /d "%~dp0"

echo 安装依赖包...
python -m pip install -r requirements.txt

echo.
echo 启动SSE模式的MCP服务器...
python src\zentao_mcp_server.py --port 8000 --transport sse

pause
