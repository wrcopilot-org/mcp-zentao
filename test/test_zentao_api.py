# -*- coding=utf-8 -*-
#!/usr/bin/env python3


import os, json, logging, httpx


ZENTAO_HOST = httpx.Client(base_url="http://192.168.2.84/zentao/")

# 1. 获取 SessionID
def test_get_session_id():
    resp = ZENTAO_HOST.get("/api-getSessionID.json")
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "success"
    assert "data" in result
    data = json.loads(result["data"])
    assert "sessionID" in data
    return data["sessionID"]


# 2. 用户登录
def test_user_login_with_sessionid():
    sessionid = test_get_session_id()
    params = {
        "account": os.getenv("ZENTAO_ACCOUNT", "lianping"),
        "password": os.getenv("ZENTAO_PASSWORD", "123456"),
        # "verifyRand": data.get("rand")
        # "keepLogin": 0
    }
    resp = ZENTAO_HOST.get(f"/user-login-{sessionid}.json", params=params)
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "success"
    assert "user" in result
    return result["user"]
    logging.info(f"User company: {result['user']['company']}")
    logging.info(f"User realname: {result['user']['realname']}")


# 3. Project
def test_get_project():
    user = test_user_login_with_sessionid()

    resp = ZENTAO_HOST.get(f"/my-project.json")
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "success"
    assert "data" in result
    data = json.loads(result["data"])
    assert "projects" in data
    logging.info(f"Projects: {data['projects']}")


# 4. Task
def test_get_task():
    user = test_user_login_with_sessionid()

    resp = ZENTAO_HOST.get(f"/my-task.json")
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "success"
    assert "data" in result
    data = json.loads(result["data"])
    assert "tasks" in data
    logging.info(f"Tasks: {data['tasks']}")


# 5. Bug
def test_get_bug():
    user = test_user_login_with_sessionid()

    resp = ZENTAO_HOST.get(f"/my-bug.json")
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "success"
    assert "data" in result
    data = json.loads(result["data"])
    assert "bugs" in data
    logging.info(f"Bugs: {data['bugs']}")