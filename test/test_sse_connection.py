"""
简单的SSE连接测试脚本
"""
import asyncio
import aiohttp
import json


async def test_sse_connection():
    """测试SSE连接"""
    url = "http://127.0.0.1:8000/"
    
    print(f"正在测试SSE连接: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache',
            }
            
            async with session.get(url, headers=headers) as response:
                print(f"响应状态: {response.status}")
                print(f"响应头: {dict(response.headers)}")
                
                if response.status == 200:
                    print("✅ SSE连接成功！")
                    
                    # 读取前几个事件
                    count = 0
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line:
                            print(f"收到数据: {line}")
                            count += 1
                            if count >= 5:  # 只读取前5个事件
                                break
                else:
                    print(f"❌ SSE连接失败: {response.status}")
                    text = await response.text()
                    print(f"响应内容: {text}")
                    
    except Exception as e:
        print(f"❌ 连接错误: {e}")


async def test_status_endpoint():
    """测试状态端点"""
    url = "http://127.0.0.1:8000/status"
    
    print(f"\n正在测试状态端点: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"响应状态: {response.status}")
                text = await response.text()
                print(f"响应内容: {text}")
                
                if response.status == 200:
                    print("✅ 状态端点正常！")
                else:
                    print(f"❌ 状态端点异常: {response.status}")
                    
    except Exception as e:
        print(f"❌ 状态端点错误: {e}")


async def main():
    """主测试函数"""
    print("开始测试Zentao MCP Server的SSE连接...")
    print("=" * 50)
    
    # 首先测试状态端点
    await test_status_endpoint()
    
    # 然后测试SSE连接
    await test_sse_connection()
    
    print("\n" + "=" * 50)
    print("测试完成")


if __name__ == "__main__":
    asyncio.run(main())
