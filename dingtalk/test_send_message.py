"""
测试脚本：查找韦家鹏的钉钉ID并发送测试消息
"""

from dingtalk_client import DingTalkClient


def main():
    client = DingTalkClient()
    print("=== 钉钉自动化测试 ===")
    print(f"Access Token: {client.access_token[:20]}...")

    # 1. 通过搜索API查找用户
    print("\n--- 查找用户: 韦家鹏 ---")
    userid = None

    user_ids = client.search_user("韦家鹏")
    if user_ids:
        userid = user_ids[0]
        print(f"找到用户, userid: {userid}")
    else:
        print("搜索未找到用户 韦家鹏")

    if not userid:
        print("\n未找到用户")
        return

    # 2. 发送测试消息
    print("\n--- 发送测试消息 ---")
    result = client.send_message(
        user_ids=userid,
        msg_type="text",
        content="这是一条来自钉钉自动化的测试消息。",
    )
    print(f"发送结果: {result}")


if __name__ == "__main__":
    main()
