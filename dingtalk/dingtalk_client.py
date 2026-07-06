"""
钉钉自动化客户端
功能：获取人员钉钉ID，发送DING消息
"""

import os
import requests


class DingTalkClient:
    """钉钉内部机器人客户端"""

    TOKEN_URL = "https://oapi.dingtalk.com/gettoken"
    DEPT_LIST_URL = "https://oapi.dingtalk.com/topapi/v2/department/listsub"
    DEPT_GET_URL = "https://oapi.dingtalk.com/topapi/v2/department/get"
    USER_LIST_URL = "https://oapi.dingtalk.com/topapi/v2/user/list"
    USER_GET_BY_MOBILE_URL = "https://oapi.dingtalk.com/topapi/v2/user/getbymobile"
    USER_SEARCH_URL = "https://api.dingtalk.com/v1.0/contact/users/search"
    USER_GET_URL = "https://oapi.dingtalk.com/topapi/v2/user/get"
    ROBOT_SEND_URL = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"

    def __init__(self):
        self.app_key = os.environ.get("DINGTALK_APP_KEY")
        self.app_secret = os.environ.get("DINGTALK_APP_SECRET")
        self.robot_code = os.environ.get("DINGTALK_ROBOT_CODE")
        if not self.app_key or not self.app_secret:
            raise ValueError("环境变量 DINGTALK_APP_KEY 和 DINGTALK_APP_SECRET 未设置")
        self._access_token = None

    @property
    def access_token(self):
        if self._access_token is None:
            self._access_token = self._get_access_token()
        return self._access_token

    def _get_access_token(self):
        """获取企业内部应用 access_token"""
        resp = requests.get(self.TOKEN_URL, params={
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }, timeout=10)
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"获取token失败: {data.get('errmsg')}")
        return data["access_token"]

    def get_department_list(self, dept_id=1):
        """获取子部门列表，dept_id=1 为根部门"""
        resp = requests.post(self.DEPT_LIST_URL, params={
            "access_token": self.access_token,
        }, json={"dept_id": dept_id}, timeout=10)
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"获取部门列表失败: {data.get('errmsg')}")
        return data.get("result", [])

    def get_department_detail(self, dept_id):
        """获取部门详情（含部门名称）"""
        resp = requests.post(self.DEPT_GET_URL, params={
            "access_token": self.access_token,
        }, json={"dept_id": dept_id}, timeout=10)
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"获取部门详情失败: {data.get('errmsg')}")
        return data.get("result", {})

    def get_all_departments(self, dept_id=1):
        """递归获取所有部门（含子部门）"""
        departments = []
        sub_depts = self.get_department_list(dept_id)
        for dept in sub_depts:
            departments.append(dept)
            departments.extend(self.get_all_departments(dept["dept_id"]))
        return departments

    def get_department_users(self, dept_id, cursor=0, size=100):
        """获取部门下的用户列表"""
        resp = requests.post(self.USER_LIST_URL, params={
            "access_token": self.access_token,
        }, json={
            "dept_id": dept_id,
            "cursor": cursor,
            "size": size,
        }, timeout=10)
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"获取用户列表失败: {data.get('errmsg')}")
        result = data.get("result", {})
        users = result.get("list", [])
        if result.get("has_more"):
            users.extend(self.get_department_users(dept_id, result["next_cursor"], size))
        return users

    def find_user_by_mobile(self, mobile):
        """通过手机号查找用户userid"""
        resp = requests.post(self.USER_GET_BY_MOBILE_URL, params={
            "access_token": self.access_token,
        }, json={"mobile": mobile}, timeout=10)
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"根据手机号查找用户失败: {data.get('errmsg')}")
        return data.get("result", {}).get("userid")

    def search_user(self, name):
        """通过姓名搜索用户，返回userid列表"""
        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json",
        }
        resp = requests.post(self.USER_SEARCH_URL, headers=headers, json={
            "queryWord": name,
            "offset": 0,
            "size": 10,
        }, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"搜索用户失败: HTTP {resp.status_code}, {resp.text}")
        data = resp.json()
        return data.get("list", [])

    def get_user_detail(self, userid):
        """获取用户详情（含部门信息）"""
        resp = requests.post(self.USER_GET_URL, params={
            "access_token": self.access_token,
        }, json={"userid": userid}, timeout=10)
        data = resp.json()
        if data.get("errcode") != 0:
            raise RuntimeError(f"获取用户详情失败: {data.get('errmsg')}")
        return data.get("result", {})

    def find_user_by_name(self, name, dept_id=None):
        """通过姓名查找用户，返回用户信息（含userid和部门）
        
        优先使用搜索API，若失败则回退到遍历部门方式。
        
        Args:
            name: 用户姓名
            dept_id: 指定部门ID搜索，None则搜索所有部门
        """
        # 优先使用搜索API（不需要部门列表权限）
        try:
            results = self.search_user(name)
            if results:
                # search_user 返回 userid 列表，取第一个
                userid = results[0] if isinstance(results[0], str) else results[0].get("userid")
                if userid:
                    # 获取用户详情（含部门）
                    try:
                        return self.get_user_detail(userid)
                    except RuntimeError:
                        return {"userid": userid, "name": name}
        except RuntimeError:
            pass

        # 回退到遍历部门方式
        if dept_id:
            dept_ids = [dept_id]
        else:
            all_depts = self.get_all_departments()
            dept_ids = [d["dept_id"] for d in all_depts]
            dept_ids.insert(0, 1)  # 包含根部门

        for did in dept_ids:
            try:
                users = self.get_department_users(did)
                for user in users:
                    if user.get("name") == name:
                        return user
            except RuntimeError:
                continue
        return None

    def send_message(self, user_ids, msg_type="text", content=None):
        """通过企业内部机器人发送消息
        
        Args:
            user_ids: 用户ID列表
            msg_type: 消息类型，支持 text, markdown 等
            content: 消息内容字典
        """
        if isinstance(user_ids, str):
            user_ids = [user_ids]

        if msg_type == "text" and isinstance(content, str):
            msg_body = {"text": {"content": content}}
        elif msg_type == "markdown" and isinstance(content, dict):
            msg_body = {"markdown": content}
        else:
            msg_body = {msg_type: content}

        payload = {
            "robotCode": self.robot_code,
            "userIds": user_ids,
            "msgKey": f"sampleText" if msg_type == "text" else f"sampleMarkdown",
            "msgParam": str(content) if msg_type == "text" else str(content),
        }

        # 使用新版API格式
        import json
        if msg_type == "text":
            payload["msgKey"] = "sampleText"
            payload["msgParam"] = json.dumps({"content": content if isinstance(content, str) else str(content)})
        elif msg_type == "markdown":
            payload["msgKey"] = "sampleMarkdown"
            payload["msgParam"] = json.dumps(content)

        headers = {
            "x-acs-dingtalk-access-token": self.access_token,
            "Content-Type": "application/json",
        }

        resp = requests.post(self.ROBOT_SEND_URL, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data
        else:
            raise RuntimeError(f"发送消息失败: HTTP {resp.status_code}, {resp.text}")


if __name__ == "__main__":
    client = DingTalkClient()
    print(f"Access Token 获取成功: {client.access_token[:20]}...")

    # 查找用户列表
    names = ["韦家鹏", "李波", "杨光雪"]
    #names = ["韦家鹏"]
    for name in names:
        user = client.find_user_by_name(name)
        if user:
            dept_ids = user.get('dept_id_list', [])
            print(f"找到用户: {user.get('name')}, userid: {user.get('userid')}, 部门ID: {dept_ids}")

            client.send_message(user_ids=user.get('userid'), msg_type="text", content=f"你好，{user.get('name')}！这是一个测试消息。")
        else:
            print(f"未找到用户: {name}")
