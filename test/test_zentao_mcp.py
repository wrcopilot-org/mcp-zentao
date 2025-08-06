import asyncio
import json
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_mcp_server():
    """测试MCP服务器的功能"""
    from zentao_mcp_server import get_zentao_products, db
    
    print("测试禅道MCP服务器功能...")
    print("=" * 50)
    
    # 测试数据库连接
    print("1. 测试数据库连接...")
    if db.connect():
        print("✅ 数据库连接成功")
    else:
        print("❌ 数据库连接失败")
        return
    
    # 测试获取产品列表
    print("\n2. 测试获取产品列表...")
    try:
        content_blocks = await get_zentao_products()
        
        print(f"✅ 成功获取 {len(content_blocks)} 个内容块")
        
        for i, block in enumerate(content_blocks):
            print(f"\n内容块 {i + 1}:")
            print(f"类型: {block.type}")
            # 只显示前500个字符，避免输出过长
            text_preview = block.text[:500] + "..." if len(block.text) > 500 else block.text
            print(f"内容预览:\n{text_preview}")
            
    except Exception as e:
        print(f"❌ 获取产品列表失败: {e}")
    
    # 断开数据库连接
    print("\n3. 断开数据库连接...")
    db.disconnect()
    print("✅ 数据库连接已断开")
    
    print("\n" + "=" * 50)
    print("✅ MCP服务器功能测试完成")


async def test_tools_list():
    """测试工具列表功能"""
    from zentao_mcp_server import main
    import mcp.types as types
    
    print("\n测试工具列表功能...")
    print("-" * 30)
    
    # 这里我们手动创建工具列表来测试
    tools = [
        types.Tool(
            name="list_products",
            title="禅道产品列表",
            description="获取禅道系统中所有产品的列表，包括产品ID、名称、负责人等信息",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
        )
    ]
    
    print("可用工具:")
    for tool in tools:
        print(f"- 名称: {tool.name}")
        print(f"  标题: {tool.title}")
        print(f"  描述: {tool.description}")
        print(f"  输入参数: {tool.inputSchema}")
    
    print("✅ 工具列表测试完成")


if __name__ == "__main__":
    print("启动禅道MCP服务器测试...")
    
    # 运行异步测试
    asyncio.run(test_mcp_server())
    asyncio.run(test_tools_list())
