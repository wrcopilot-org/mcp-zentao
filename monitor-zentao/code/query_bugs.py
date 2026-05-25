"""
禅道监控 - 查询最近一周已解决的bug，结合SVN提交记录生成报表，并通过钉钉通知

流程：
1. 从禅道数据库查询最近一周已解决的bug → 生成 currentbug.xlsx
2. 从多个SVN仓库提取最近两周的提交记录
3. SVN中未找到 且 解决人职位为RD 的bug → 生成 nocodebug.xlsx
4. 遍历 nocodebug.xlsx，排除已发过消息的bug后，向解决人发送钉钉消息
5. 查询最近一周测试指派的active bug，通知当前被指派人
6. 发送成功的bug记录到 sendmsgbug.xlsx / sendmsg_assignee.xlsx
"""

import pymysql
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime, timedelta
import os
import subprocess
import re
import json
import xml.etree.ElementTree as ET
import urllib.request
import urllib.error
import urllib.parse
import time
import hmac
import hashlib
import base64


import sys

try:
    from dingtalk_client import DingTalkClient
    _dingtalk_client = None

    def get_dingtalk_client():
        global _dingtalk_client
        if _dingtalk_client is None:
            try:
                _dingtalk_client = DingTalkClient()
            except (ValueError, RuntimeError) as e:
                print(f"  [警告] DingTalkClient初始化失败: {e}", flush=True)
        return _dingtalk_client
except ImportError:
    print("[警告] 无法导入DingTalkClient，将仅使用群机器人发送", flush=True)
    def get_dingtalk_client():
        return None


def get_app_dir():
    """获取应用所在目录（兼容PyInstaller打包后的exe和普通py运行）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_db_connection():
    """连接禅道MySQL数据库"""
    return pymysql.connect(
        host='192.168.2.84',
        port=3306,
        user='dev',
        passwd='123456',
        db='zentao',
        charset='utf8'
    )


def query_recent_resolved_bugs(conn):
    """查询最近一周内解决的bug（包含解决人职位信息）"""
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    sql = """
    SELECT
        b.id              AS 'Bug编号',
        p.name            AS '所属产品',
        pj.name           AS '所属项目',
        m.name            AS '功能模块',
        b.title           AS 'Bug标题',
        b.severity        AS '严重程度',
        b.pri             AS '优先级',
        b.status          AS '状态',
        opener.realname   AS '创建人',
        b.openedDate      AS '创建时间',
        assignee.realname AS '当前负责人',
        b.assignedDate    AS '指派时间',
        resolver.realname AS '解决人',
        b.resolvedDate    AS '解决时间',
        b.resolution      AS '解决方案',
        closer.realname   AS '关闭人',
        b.closedDate      AS '关闭时间',
        resolver.role     AS '解决人职位'
    FROM zt_bug b
    LEFT JOIN zt_product p   ON b.product = p.id
    LEFT JOIN zt_project pj  ON b.project = pj.id
    LEFT JOIN zt_module m    ON b.module = m.id
    LEFT JOIN zt_user opener   ON b.openedBy = opener.account
    LEFT JOIN zt_user assignee ON b.assignedTo = assignee.account
    LEFT JOIN zt_user resolver ON b.resolvedBy = resolver.account
    LEFT JOIN zt_user closer   ON b.closedBy = closer.account
    WHERE b.resolvedDate >= %s
    ORDER BY b.resolvedDate DESC
    """

    cursor = conn.cursor()
    cursor.execute(sql, (one_week_ago,))
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return columns, rows

# 列索引常量 (与SQL SELECT顺序对应)
COL_BUG_ID = 0
COL_PRODUCT = 1
COL_PROJECT = 2
COL_MODULE = 3
COL_TITLE = 4
COL_SEVERITY = 5       # 严重程度
COL_PRI = 6            # 优先级
COL_STATUS = 7          # 状态
COL_OPENER = 8          # 创建人 realname
COL_ASSIGNEE = 10       # 当前负责人 realname
COL_ASSIGNED_DATE = 11  # 指派时间
COL_RESOLVER = 12       # 解决人 realname
COL_RESOLVED_DATE = 13
COL_RESOLUTION = 14     # 解决方案
COL_RESOLVER_ROLE = 17  # 解决人职位 (因插入resolution列，从16→17)
COL_ASSIGNER = 18       # 指派人 realname (仅指派通知查询使用)
COL_ASSIGNER_ROLE = 19  # 指派人职位
COL_ASSIGN_ACTION = 20  # 指派动作
COL_OPENER_ROLE = 21    # 创建人职位
COL_ASSIGNEE_ROLE = 22  # 当前负责人职位
COL_OPENED_COUNT = 23   # zt_action 中 action=opened 的次数

TEST_ASSIGNER_ROLES = {'qa', 'qd', 'sqa', 'test', 'tester'}
DEV_ASSIGNEE_ROLES = {'dev'}

# 解决方案取值映射
RESOLUTION_MAP = {
    'fixed':      '已解决',
    'bydesign':   '设计如此',
    'duplicate':  '重复Bug',
    'external':   '外部原因',
    'notrepro':   '无法重现',
    'postponed':  '延期处理',
    'willnotfix': '不予解决',
}


def generate_excel(columns, rows, output_path):
    """生成Excel报表"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "最近一周已解决Bug"

    # 表头样式
    header_font = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # 写入表头
    for col_idx, col_name in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    # 数据样式
    data_font = Font(name='微软雅黑', size=10)
    data_alignment = Alignment(vertical='center', wrap_text=True)

    # 写入数据
    for row_idx, row_data in enumerate(rows, 2):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=str(value) if value else '')
            cell.font = data_font
            cell.alignment = data_alignment
            cell.border = thin_border

    # 自动调整列宽
    for col_idx, col_name in enumerate(columns, 1):
        max_len = len(col_name) * 2  # 中文字符宽度
        for row_idx in range(2, len(rows) + 2):
            cell_value = str(ws.cell(row=row_idx, column=col_idx).value or '')
            max_len = max(max_len, len(cell_value))
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = min(max_len + 4, 40)

    # 冻结首行
    ws.freeze_panes = 'A2'

    wb.save(output_path)
    return output_path


# ============================================================
# SVN 相关功能
# ============================================================

def load_svn_repos(filepath):
    """Load svn repo urls from xlsx config."""
    if not os.path.exists(filepath):
        print(f"  [warn] svn repo config not found: {filepath}", flush=True)
        return []

    repo_urls = []
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        for row_idx in range(2, ws.max_row + 1):
            repo_url = ws.cell(row=row_idx, column=1).value
            if repo_url:
                repo_url = str(repo_url).strip()
                if repo_url:
                    repo_urls.append(repo_url)
        wb.close()
    except Exception as e:
        print(f"  [warn] failed to load svn repo config: {e}", flush=True)
        return []

    if not repo_urls:
        print(f"  [warn] svn repo config is empty: {filepath}", flush=True)
        return []

    print(f"loaded svn repos from config: {len(repo_urls)}", flush=True)
    return repo_urls


def get_svn_logs(repo_url, days=14):
    """获取指定SVN仓库最近N天的提交记录，返回 [(revision, author, date, message), ...]"""
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    cmd = [
        'svn', 'log', repo_url,
        '--non-interactive',
        '--xml',
        '-r', f'{{{since_date}}}:HEAD',
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
        if result.returncode != 0:
            print(f"  [警告] 获取失败: {result.stderr.strip()}", flush=True)
            return []
        return parse_svn_xml(result.stdout)
    except subprocess.TimeoutExpired:
        print(f"  [警告] 超时: {repo_url}", flush=True)
        return []
    except Exception as e:
        print(f"  [警告] 异常: {e}", flush=True)
        return []


def parse_svn_xml(xml_str):
    """解析svn log --xml的输出"""
    entries = []
    try:
        root = ET.fromstring(xml_str)
        for logentry in root.findall('logentry'):
            revision = logentry.get('revision', '')
            author = logentry.findtext('author', '')
            date = logentry.findtext('date', '')
            msg = logentry.findtext('msg', '')
            entries.append((revision, author, date, msg or ''))
    except ET.ParseError as e:
        print(f"  [警告] XML解析失败: {e}", flush=True)
    return entries


def extract_bug_ids_from_svn_logs(all_logs):
    """从SVN提交注释中提取所有bug编号，返回 set(int)
    
    匹配模式：
    - Bug#123, bug#123, BUG#123
    - Bug 123, bug 123
    - Bug:123, bug:123
    - #123 (单独的数字引用)
    - 纯数字（如提交注释中直接写bug编号如 "12345"）
    """
    bug_ids = set()
    # 匹配常见的bug引用模式
    pattern = re.compile(
        r'(?:bug|Bug|BUG)\s*[#:：]?\s*(\d+)'  # Bug#123, Bug 123, Bug:123
        r'|#(\d+)'                               # #123
        ,
        re.IGNORECASE
    )
    for revision, author, date, msg in all_logs:
        for match in pattern.finditer(msg):
            # 取第一个非空的捕获组
            bug_id_str = match.group(1) or match.group(2)
            if bug_id_str:
                bug_ids.add(int(bug_id_str))
    return bug_ids


def filter_bugs_by_svn(bug_rows, all_svn_logs):
    """在SVN提交注释中直接搜索bug编号字符串，找到即认为有SVN记录"""
    # 将所有SVN日志的注释拼成一个大字符串，便于查找
    all_messages = "\n".join(msg for _, _, _, msg in all_svn_logs)

    found_in_svn = []
    not_found_in_svn = []
    for row in bug_rows:
        bug_id = str(row[COL_BUG_ID]) if row[COL_BUG_ID] else ''
        if bug_id and bug_id in all_messages:
            found_in_svn.append(row)
        else:
            not_found_in_svn.append(row)
    return found_in_svn, not_found_in_svn


def filter_rd_bugs(bug_rows):
    """筛选解决人职位为RD的bug"""
    rd_bugs = []
    non_rd_bugs = []
    for row in bug_rows:
        role = str(row[COL_RESOLVER_ROLE] or '').strip().lower()
        if role == 'dev':
            rd_bugs.append(row)
        else:
            non_rd_bugs.append(row)
    return rd_bugs, non_rd_bugs


def get_row_value(row, index, default=''):
    """安全读取扩展列，兼容旧查询结果。"""
    return row[index] if len(row) > index else default


def is_test_role(role):
    """判断禅道用户角色是否属于测试侧。"""
    return str(role or '').strip().lower() in TEST_ASSIGNER_ROLES


def is_dev_role(role):
    """判断禅道用户角色是否属于开发侧。"""
    return str(role or '').strip().lower() in DEV_ASSIGNEE_ROLES


def get_opened_count(row):
    """获取bug被打开次数，无法解析时按0处理。"""
    try:
        return int(get_row_value(row, COL_OPENED_COUNT, 0) or 0)
    except (TypeError, ValueError):
        return 0


def is_multi_open_bug(row):
    """多次打开的bug。"""
    return get_opened_count(row) >= 2


def is_multi_open_dev_bug(row):
    """多次打开且当前指派给开发人员的bug。"""
    return is_dev_role(get_row_value(row, COL_ASSIGNEE_ROLE)) and is_multi_open_bug(row)


def filter_test_assigned_bugs(bug_rows):
    """筛选测试人员指派给当前负责人的active bug。

    最近一次指派动作能匹配到动作表时，以指派动作为准；新建bug没有单独
    assigned动作时，用创建人角色兜底。
    """
    test_assigned = []
    other_assigned = []
    for row in bug_rows:
        assigner_role = get_row_value(row, COL_ASSIGNER_ROLE)
        assign_action = str(get_row_value(row, COL_ASSIGN_ACTION) or '').strip().lower()
        opener_role = get_row_value(row, COL_OPENER_ROLE)

        if is_test_role(assigner_role):
            test_assigned.append(row)
        elif (not assigner_role or assign_action == 'opened') and is_test_role(opener_role):
            test_assigned.append(row)
        else:
            other_assigned.append(row)
    return test_assigned, other_assigned


# ============================================================
# 钉钉通知功能
# ============================================================

DINGTALK_WEBHOOK_URL = (
    "https://oapi.dingtalk.com/robot/send"
    "?access_token=396a5f0855df4f121d2e6eda7270c6868bf6abcf9f7ee038c8cd2e88f0662570"
)
DINGTALK_SECRET = "SECbeaacac4ece00e63018fbed88a16e64be36a381cfa154c988a83d87a89324179"


def get_dingtalk_signed_url():
    """生成带签名的钉钉Webhook URL"""
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f'{timestamp}\n{DINGTALK_SECRET}'
    hmac_code = hmac.new(
        DINGTALK_SECRET.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return f"{DINGTALK_WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"


def load_dingtalk_member_map(filepath):
    """从dingtalk-mem.xlsx加载成员映射
    
    Excel格式: 列1=姓名, 列2=钉钉号(userid), 列3=职务, 列4=小组(多个小组用逗号分隔)
    加载时如果钉钉号为空，则通过API获取userid并填入保存。
    返回: (member_map, member_group_map, group_supervisors)
        member_map: {姓名: 钉钉userid}
        member_group_map: {姓名: [小组名列表]}
        group_supervisors: {小组名: [主管姓名列表]}
    """
    member_map = {}
    member_group_map = {}
    group_supervisors = {}
    if not os.path.exists(filepath):
        print(f"  [警告] 未找到钉钉成员映射文件: {filepath}", flush=True)
        return member_map, member_group_map, group_supervisors
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        need_save = False
        for row_idx in range(2, ws.max_row + 1):  # 跳过表头
            name = ws.cell(row=row_idx, column=1).value
            dingtalk_id = ws.cell(row=row_idx, column=2).value
            role = ws.cell(row=row_idx, column=3).value
            group = ws.cell(row=row_idx, column=4).value
            if not name:
                continue
            name_str = str(name).strip()
            if not name_str:
                continue
            # 钉钉号为空时，获取userid并填入
            if not dingtalk_id or not str(dingtalk_id).strip():
                userid = get_userid_by_name(name_str)
                if userid:
                    dingtalk_id = userid
                    ws.cell(row=row_idx, column=2, value=userid)
                    need_save = True
                    print(f"  [填充] {name_str} 的钉钉userid: {userid}", flush=True)
                else:
                    # 写入FAILED标记，避免每次运行都重复尝试
                    ws.cell(row=row_idx, column=2, value="FAILED")
                    need_save = True
                    print(f"  [警告] 无法获取 {name_str} 的钉钉userid，已标记FAILED", flush=True)
                    continue
            if str(dingtalk_id).strip() == "FAILED":
                continue
            member_map[name_str] = str(dingtalk_id).strip()
            group_str = str(group).strip() if group else ''
            if group_str:
                # 支持逗号分隔的多个小组
                groups = [g.strip() for g in group_str.replace('，', ',').split(',') if g.strip()]
                member_group_map[name_str] = groups
                if role and str(role).strip() == '主管':
                    for g in groups:
                        group_supervisors.setdefault(g, []).append(name_str)
            else:
                member_group_map[name_str] = []
        if need_save:
            wb.save(filepath)
            print(f"  [保存] dingtalk-mem.xlsx 已更新", flush=True)
        wb.close()
    except Exception as e:
        print(f"  [警告] 读取dingtalk-mem.xlsx失败: {e}", flush=True)
    return member_map, member_group_map, group_supervisors


# 全局钉钉成员缓存，只加载一次
_dingtalk_member_cache = None


def get_dingtalk_members():
    """获取钉钉成员映射（全局缓存，只加载一次）"""
    global _dingtalk_member_cache
    if _dingtalk_member_cache is None:
        dingtalk_mem_path = os.path.join(get_app_dir(), 'dingtalk-mem.xlsx')
        _dingtalk_member_cache = load_dingtalk_member_map(dingtalk_mem_path)
        dingtalk_map, _, group_supervisors = _dingtalk_member_cache
        if dingtalk_map:
            print(f"  已加载钉钉成员映射: {len(dingtalk_map)} 人, 小组主管: {group_supervisors}", flush=True)
    return _dingtalk_member_cache


def get_supervisors_for_person(name, member_group_map, group_supervisors):
    """获取某人所在小组的主管列表（去重）"""
    groups = member_group_map.get(name, [])
    if not groups:
        return []
    supervisors = []
    seen = set()
    for group in groups:
        for sup in group_supervisors.get(group, []):
            if sup not in seen:
                seen.add(sup)
                supervisors.append(sup)
    return supervisors


def log_dingtalk_send(recipients, content, method="direct"):
    """记录钉钉发送记录到 dingtalk-send-log.xlsx"""
    log_path = os.path.join(get_app_dir(), 'dingtalk-send-log.xlsx')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    recipients_str = ', '.join(recipients) if isinstance(recipients, (list, tuple)) else str(recipients)
    try:
        if os.path.exists(log_path):
            wb = openpyxl.load_workbook(log_path)
            ws = wb.active
        else:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(['发送时间', '接收人', '发送方式', '内容'])
        ws.append([now_str, recipients_str, method, content])
        wb.save(log_path)
        wb.close()
    except Exception as e:
        print(f"  [警告] 记录发送日志失败: {e}", flush=True)


def send_direct_message(user_ids, text):
    """通过DingTalkClient直接发送消息给用户，成功返回True"""
    client = get_dingtalk_client()
    if not client:
        return False
    try:
        client.send_message(user_ids=user_ids, msg_type="text", content=text)
        return True
    except Exception as e:
        print(f"  [警告] 直接消息发送失败: {e}", flush=True)
        return False


def get_userid_by_name(name):
    """通过姓名获取钉钉userid"""
    client = get_dingtalk_client()
    if not client:
        return None
    try:
        user = client.find_user_by_name(name)
        if user:
            return user.get('userid')
    except Exception as e:
        print(f"  [警告] 获取 {name} userid失败: {e}", flush=True)
    return None


def send_dingtalk_message(bug_rows, dingtalk_map, member_group_map=None, group_supervisors=None):
    """向解决人发送钉钉消息，优先直接发送，失败则走群机器人，返回发送成功的bug列表"""
    if not bug_rows:
        return []

    member_group_map = member_group_map or {}
    group_supervisors = group_supervisors or {}

    # 按解决人分组
    resolver_bugs = {}
    for row in bug_rows:
        resolver = str(row[COL_RESOLVER] or '未知')
        resolver_bugs.setdefault(resolver, []).append(row)

    sent_bugs = []
    for resolver, bugs in resolver_bugs.items():
        # 确认名字在dingtalk-mem中，不在则跳过
        dingtalk_id = dingtalk_map.get(resolver, '')
        if not dingtalk_id:
            print(f"  [跳过] {resolver} 不在dingtalk-mem.xlsx中", flush=True)
            continue

        # 构造text消息内容
        bug_lines = []
        has_non_fixed = False
        non_fixed_assignees = set()
        for row in bugs:
            bug_id = row[COL_BUG_ID]
            title = row[COL_TITLE]
            product = row[COL_PRODUCT] or ''
            resolved_date = str(row[COL_RESOLVED_DATE] or '')
            resolution = str(row[COL_RESOLUTION] or '').strip().lower()
            resolution_label = RESOLUTION_MAP.get(resolution, resolution)

            line = f"  - Bug#{bug_id} [{product}] {title} (解决时间: {resolved_date}"
            if resolution and resolution != 'fixed':
                has_non_fixed = True
                line += f", 解决方案: {resolution_label}"
                assignee = str(row[COL_ASSIGNEE] or '').strip()
                if assignee and assignee != resolver:
                    non_fixed_assignees.add(assignee)
            line += ")"
            bug_lines.append(line)

        text = (
            f"@{resolver} 解决Bug提醒：以下已解决的bug在SVN中未找到关联的代码提交记录，请检查：\n\n"
            + "\n".join(bug_lines)
            + "\n\n请确认是否已提交相关代码，或在SVN提交注释中关联bug编号。"
        )

        if has_non_fixed and non_fixed_assignees:
            assignee_at_text = ' '.join(f"@{n}" for n in non_fixed_assignees)
            text += f"\n{assignee_at_text} 请关注以上非fixed解决方案的bug。"

        # 尝试直接发送消息给userid
        direct_sent = False
        userid = dingtalk_map.get(resolver, '')
        if userid:
            # 收集所有需要发送的userid（解决人 + 对应小组主管）
            all_user_ids = [userid]
            resolver_supervisors = get_supervisors_for_person(resolver, member_group_map, group_supervisors)
            for sup_name in resolver_supervisors:
                if sup_name != resolver:
                    sup_userid = dingtalk_map.get(sup_name, '')
                    if sup_userid:
                        all_user_ids.append(sup_userid)
            direct_sent = True #send_direct_message(all_user_ids, text)
            if direct_sent:
                print(f"  直接消息发送成功 → {resolver} ({len(bugs)} 个bug)", flush=True)
                log_dingtalk_send(resolver, text, "direct")
                sent_bugs.extend(bugs)

        # 直接发送失败，回退到群机器人
        if not direct_sent:
            at_mobiles = [dingtalk_id]
            # 加入对应小组主管的钉钉号
            resolver_supervisors = get_supervisors_for_person(resolver, member_group_map, group_supervisors)
            for sup_name in resolver_supervisors:
                sup_dingtalk_id = dingtalk_map.get(sup_name, '')
                if sup_dingtalk_id and sup_dingtalk_id not in at_mobiles:
                    at_mobiles.append(sup_dingtalk_id)
            # 加入非fixed负责人
            if has_non_fixed and non_fixed_assignees:
                for assignee_name in non_fixed_assignees:
                    assignee_dingtalk_id = dingtalk_map.get(assignee_name, '')
                    if assignee_dingtalk_id and assignee_dingtalk_id not in at_mobiles:
                        at_mobiles.append(assignee_dingtalk_id)

            payload = {
                "msgtype": "text",
                "text": {"content": text},
                "at": {
                    "atMobiles": at_mobiles,
                    "isAtAll": False
                }
            }

            try:
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                signed_url = get_dingtalk_signed_url()
                req = urllib.request.Request(
                    signed_url,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                    if result.get('errcode') == 0:
                        print(f"  群机器人消息发送成功 → {resolver} ({len(bugs)} 个bug)", flush=True)
                        log_dingtalk_send(resolver, text, "robot")
                        sent_bugs.extend(bugs)
                    else:
                        print(f"  群机器人消息发送失败 → {resolver}: {result.get('errmsg')}", flush=True)
            except Exception as e:
                print(f"  钉钉消息发送异常 → {resolver}: {e}", flush=True)

    return sent_bugs


def query_recently_assigned_bugs(conn):
    """查询最近一周指派时间变化的、仍处于active状态的bug。"""
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

    sql = """
    SELECT
        b.id              AS 'Bug编号',
        p.name            AS '所属产品',
        pj.name           AS '所属项目',
        m.name            AS '功能模块',
        b.title           AS 'Bug标题',
        b.severity        AS '严重程度',
        b.pri             AS '优先级',
        b.status          AS '状态',
        opener.realname   AS '创建人',
        b.openedDate      AS '创建时间',
        assignee.realname AS '当前负责人',
        b.assignedDate    AS '指派时间',
        resolver.realname AS '解决人',
        b.resolvedDate    AS '解决时间',
        b.resolution      AS '解决方案',
        closer.realname   AS '关闭人',
        b.closedDate      AS '关闭时间',
        resolver.role     AS '解决人职位',
        assigner.realname AS '指派人',
        assigner.role     AS '指派人职位',
        assign_action.action AS '指派动作',
        opener.role       AS '创建人职位',
        assignee.role     AS '当前负责人职位',
        (
            SELECT COUNT(*)
            FROM zt_action opened_action
            WHERE opened_action.objectType = 'bug'
              AND opened_action.objectID = b.id
              AND opened_action.action = 'opened'
        ) AS '打开次数'
    FROM zt_bug b
    LEFT JOIN zt_product p   ON b.product = p.id
    LEFT JOIN zt_project pj  ON b.project = pj.id
    LEFT JOIN zt_module m    ON b.module = m.id
    LEFT JOIN zt_user opener   ON b.openedBy = opener.account
    LEFT JOIN zt_user assignee ON b.assignedTo = assignee.account
    LEFT JOIN zt_user resolver ON b.resolvedBy = resolver.account
    LEFT JOIN zt_user closer   ON b.closedBy = closer.account
    LEFT JOIN zt_action assign_action ON assign_action.id = (
        SELECT MAX(a.id)
        FROM zt_action a
        WHERE a.objectType = 'bug'
          AND a.objectID = b.id
          AND a.action IN ('assigned', 'opened', 'activated')
          AND a.date = b.assignedDate
    )
    LEFT JOIN zt_user assigner ON assign_action.actor = assigner.account
    WHERE b.assignedDate >= %s
      AND b.status = 'active'
      AND b.deleted = '0'
      AND b.assignedTo <> ''
    ORDER BY b.assignedDate DESC
    """

    cursor = conn.cursor()
    cursor.execute(sql, (one_week_ago,))
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return columns, rows


def load_sent_assignee_records(filepath):
    """加载已发送指派通知的记录，返回 {(bug_id, assigned_date_str)} 集合"""
    sent_keys = set()
    if not os.path.exists(filepath):
        return sent_keys
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        for row_idx in range(2, ws.max_row + 1):
            bug_id = ws.cell(row=row_idx, column=1).value
            assigned_date = ws.cell(row=row_idx, column=2).value
            if bug_id and assigned_date:
                sent_keys.add((str(bug_id).strip(), str(assigned_date).strip()))
        wb.close()
    except Exception as e:
        print(f"  [警告] 读取sendmsg_assignee.xlsx失败: {e}", flush=True)
    return sent_keys


def append_to_sent_assignee_records(sent_rows, filepath):
    """将发送成功的指派通知记录追加到文件
    
    格式: Bug编号 | 指派时间 | 被指派人 | Bug标题 | 解决人 | 通知发送时间 | 打开次数 | 通知类型
    """
    if not sent_rows:
        return

    headers = ['Bug编号', '指派时间', '被指派人', 'Bug标题', '解决人', '通知发送时间', '打开次数', '通知类型']
    if os.path.exists(filepath):
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        for col_idx, h in enumerate(headers, 1):
            if not ws.cell(row=1, column=col_idx).value:
                ws.cell(row=1, column=col_idx, value=h)
        start_row = ws.max_row + 1
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "指派通知记录"
        for col_idx, h in enumerate(headers, 1):
            ws.cell(row=1, column=col_idx, value=h)
        start_row = 2

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for row_idx, row in enumerate(sent_rows, start_row):
        ws.cell(row=row_idx, column=1, value=str(row[COL_BUG_ID]))
        ws.cell(row=row_idx, column=2, value=str(row[COL_ASSIGNED_DATE] or ''))
        ws.cell(row=row_idx, column=3, value=str(row[COL_ASSIGNEE] or ''))
        ws.cell(row=row_idx, column=4, value=str(row[COL_TITLE] or ''))
        ws.cell(row=row_idx, column=5, value=str(row[COL_RESOLVER] or ''))
        ws.cell(row=row_idx, column=6, value=now_str)
        ws.cell(row=row_idx, column=7, value=get_opened_count(row))
        ws.cell(
            row=row_idx,
            column=8,
            value='多次打开质量提醒' if is_multi_open_bug(row) else '普通指派通知'
        )

    wb.save(filepath)


def send_assignee_notification(bug_rows, dingtalk_map, member_group_map=None, group_supervisors=None, record_filepath=None):
    """通知被指派人：测试侧已将active bug指派给你。
    
    使用单独的记录文件，以 (bug_id, assignedDate) 为key避免重复通知。
    只处理active状态的bug。
    """
    if not bug_rows:
        return []

    member_group_map = member_group_map or {}
    group_supervisors = group_supervisors or {}

    # 加载已发送记录
    sent_keys = set()
    if record_filepath:
        sent_keys = load_sent_assignee_records(record_filepath)
        if sent_keys:
            print(f"  已有指派通知记录: {len(sent_keys)} 条", flush=True)

    # 筛选：active + 未发过通知的(bug_id, assignedDate)组合
    new_bugs = []
    for row in bug_rows:
        status = str(row[COL_STATUS] or '').strip().lower()
        if status != 'active':
            continue
        bug_id = str(row[COL_BUG_ID])
        assigned_date = str(row[COL_ASSIGNED_DATE] or '').strip()
        if (bug_id, assigned_date) in sent_keys:
            continue
        new_bugs.append(row)

    if not new_bugs:
        print("  没有新的指派通知需要发送", flush=True)
        return []

    print(f"  需发送指派通知: {len(new_bugs)} 条", flush=True)

    # 按被指派人分组
    assignee_bugs = {}
    for row in new_bugs:
        assignee = str(row[COL_ASSIGNEE] or '').strip()
        if assignee:
            assignee_bugs.setdefault(assignee, []).append(row)

    if not assignee_bugs:
        print("  没有可通知的被指派人", flush=True)
        return []

    sent_bugs = []
    for assignee, bugs in assignee_bugs.items():
        dingtalk_id = dingtalk_map.get(assignee, '')
        if not dingtalk_id:
            print(f"  [跳过指派通知] {assignee} 不在dingtalk-mem.xlsx中", flush=True)
            continue

        def format_assignee_bug_line(row):
            bug_id = row[COL_BUG_ID]
            title = row[COL_TITLE]
            product = row[COL_PRODUCT] or ''
            project = row[COL_PROJECT] or ''
            pri = row[COL_PRI] if len(row) > COL_PRI else ''
            severity = row[COL_SEVERITY] if len(row) > COL_SEVERITY else ''
            assigned_date = str(row[COL_ASSIGNED_DATE] or '')
            assigner = str(get_row_value(row, COL_ASSIGNER) or row[COL_OPENER] or '').strip()
            assigner_text = f", 指派人: {assigner}" if assigner else ''
            opened_count = get_opened_count(row)
            line = (
                f"  - Bug#{bug_id} [{product}/{project}] {title} "
                f"(优先级: {pri}, 严重程度: {severity}, 打开次数: {opened_count}, "
                f"指派时间: {assigned_date}{assigner_text})"
            )
            return line

        def append_supervisor_users(user_ids):
            assignee_supervisors = get_supervisors_for_person(assignee, member_group_map, group_supervisors)
            for sup_name in assignee_supervisors:
                if sup_name != assignee:
                    sup_userid = dingtalk_map.get(sup_name, '')
                    if sup_userid and sup_userid not in user_ids:
                        user_ids.append(sup_userid)

        def append_supervisor_mobiles(at_mobiles):
            assignee_supervisors = get_supervisors_for_person(assignee, member_group_map, group_supervisors)
            for sup_name in assignee_supervisors:
                sup_dingtalk_id = dingtalk_map.get(sup_name, '')
                if sup_dingtalk_id and sup_dingtalk_id not in at_mobiles:
                    at_mobiles.append(sup_dingtalk_id)

        def send_assignment_batch(batch_bugs, text, include_supervisors):
            # 打开次数>=2的质量提醒才发给主管；普通指派只发被指派人。
            direct_sent = False
            userid = dingtalk_map.get(assignee, '')
            if userid:
                all_user_ids = [userid]
                if include_supervisors:
                    append_supervisor_users(all_user_ids)
                direct_sent = send_direct_message(all_user_ids, text)
                if direct_sent:
                    print(f"  指派通知直接发送成功 → {assignee} ({len(batch_bugs)} 个bug)", flush=True)
                    log_dingtalk_send(assignee, text, "direct")
                    sent_bugs.extend(batch_bugs)

            if direct_sent:
                return

            at_mobiles = [dingtalk_id]
            if include_supervisors:
                append_supervisor_mobiles(at_mobiles)

            payload = {
                "msgtype": "text",
                "text": {"content": text},
                "at": {
                    "atMobiles": at_mobiles,
                    "isAtAll": False
                }
            }

            try:
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                signed_url = get_dingtalk_signed_url()
                req = urllib.request.Request(
                    signed_url,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                    if result.get('errcode') == 0:
                        print(f"  指派通知群机器人发送成功 → {assignee} ({len(batch_bugs)} 个bug)", flush=True)
                        log_dingtalk_send(assignee, text, "robot")
                        sent_bugs.extend(batch_bugs)
                    else:
                        print(f"  指派通知发送失败 → {assignee}: {result.get('errmsg')}", flush=True)
            except Exception as e:
                print(f"  指派通知发送异常 → {assignee}: {e}", flush=True)

        quality_bugs = [row for row in bugs if is_multi_open_bug(row)]
        normal_bugs = [row for row in bugs if not is_multi_open_bug(row)]

        if quality_bugs:
            quality_bug_lines = [format_assignee_bug_line(row) for row in quality_bugs]
            text = (
                f"@{assignee} 多次打开Bug质量提醒：以下bug已再次指派给你。"
                "请重点关注开发质量，修复后做好自测试，再提交测试验证。\n\n"
                + "\n".join(quality_bug_lines)
            )
            send_assignment_batch(quality_bugs, text, include_supervisors=True)

        if normal_bugs:
            normal_bug_lines = [format_assignee_bug_line(row) for row in normal_bugs]
            text = (
                f"@{assignee} 测试指派Bug通知：以下active bug已指派给你，请及时处理：\n\n"
                + "\n".join(normal_bug_lines)
            )
            send_assignment_batch(normal_bugs, text, include_supervisors=False)

    # 记录已发送
    if sent_bugs and record_filepath:
        append_to_sent_assignee_records(sent_bugs, record_filepath)
        print(f"  已记录 {len(sent_bugs)} 条指派通知到: {record_filepath}", flush=True)

    return sent_bugs


def load_sent_bug_ids(filepath):
    """从sendmsgbug.xlsx中加载已发送消息的bug编号集合"""
    sent_ids = set()
    if not os.path.exists(filepath):
        return sent_ids
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        for row_idx in range(2, ws.max_row + 1):
            val = ws.cell(row=row_idx, column=1).value
            if val:
                try:
                    sent_ids.add(int(val))
                except (ValueError, TypeError):
                    pass
        wb.close()
    except Exception as e:
        print(f"  [警告] 读取sendmsgbug.xlsx失败: {e}", flush=True)
    return sent_ids


def append_to_sendmsgbug(columns, bug_rows, filepath):
    """将bug追加到sendmsgbug.xlsx（如果文件已存在则追加，不存在则新建）"""
    if not bug_rows:
        return

    if os.path.exists(filepath):
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        start_row = ws.max_row + 1
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "已发送通知的Bug"
        # 写入表头 + 发送时间列
        send_columns = list(columns) + ['通知发送时间']
        for col_idx, col_name in enumerate(send_columns, 1):
            ws.cell(row=1, column=col_idx, value=col_name)
        start_row = 2

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for row_idx, row_data in enumerate(bug_rows, start_row):
        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=row_idx, column=col_idx, value=str(value) if value else '')
        # 最后一列写入发送时间
        ws.cell(row=row_idx, column=len(row_data) + 1, value=now_str)

    wb.save(filepath)
    return filepath


def MonitorBugs():
    output_dir = get_app_dir()
    currentbug_path = os.path.join(output_dir, 'currentbug.xlsx')
    nocodebug_path = os.path.join(output_dir, 'nocodebug.xlsx')
    sendmsgbug_path = os.path.join(output_dir, 'sendmsgbug.xlsx')
    svn_repo_config_path = os.path.join(output_dir, 'svn_repos.xlsx')

    # ---- 第1步：查询数据库，排除已通知的bug ----
    print("=" * 60, flush=True)
    print("第1步：查询禅道数据库最近一周已解决的bug", flush=True)
    print("=" * 60, flush=True)

    conn = get_db_connection()
    print("数据库连接成功", flush=True)

    try:
        columns, rows = query_recent_resolved_bugs(conn)
        print(f"查询到 {len(rows)} 条已解决的bug", flush=True)
    finally:
        conn.close()

    if not rows:
        print("最近一周没有已解决的bug记录，程序结束", flush=True)
        return

    # 先排除已发过消息的bug
    sent_ids = load_sent_bug_ids(sendmsgbug_path)
    if sent_ids:
        print(f"已发过消息的bug: {len(sent_ids)} 条", flush=True)
    rows = [row for row in rows if int(row[COL_BUG_ID]) not in sent_ids]
    if not rows:
        print("排除已通知的bug后没有新bug，程序结束", flush=True)
        return
    print(f"排除后剩余新bug: {len(rows)} 条", flush=True)

    # currentbug.xlsx 不含"解决人职位"列 (最后一列)
    display_columns = columns[:-1]
    display_rows = [row[:-1] for row in rows]
    generate_excel(display_columns, display_rows, currentbug_path)
    print(f"全部新bug已保存: {currentbug_path}", flush=True)

    # ---- 第2步：查询SVN提交记录 ----
    print(flush=True)
    print("=" * 60, flush=True)
    print("第2步：查询SVN仓库最近两周的提交记录", flush=True)
    print("=" * 60, flush=True)

    svn_repos = load_svn_repos(svn_repo_config_path)
    if not svn_repos:
        print("未配置可用的SVN仓库，程序结束", flush=True)
        return

    all_svn_logs = []
    for repo_url in svn_repos:
        print(f"  查询: {repo_url}", flush=True)
        logs = get_svn_logs(repo_url, days=14)
        print(f"    获取到 {len(logs)} 条提交记录", flush=True)
        all_svn_logs.extend(logs)

    print(f"SVN总计: {len(all_svn_logs)} 条提交记录", flush=True)

    # ---- 第3步：筛选未在SVN关联 且 解决人为RD → nocodebug.xlsx ----
    print(flush=True)
    print("=" * 60, flush=True)
    print("第3步：筛选未提交代码的RD bug", flush=True)
    print("=" * 60, flush=True)

    found_in_svn, not_found_in_svn = filter_bugs_by_svn(rows, all_svn_logs)
    print(f"  SVN已关联: {len(found_in_svn)} 条", flush=True)
    print(f"  SVN未关联: {len(not_found_in_svn)} 条", flush=True)

    # 再按解决人职位过滤，只保留RD
    rd_bugs, non_rd_bugs = filter_rd_bugs(not_found_in_svn)
    print(f"  其中解决人为RD: {len(rd_bugs)} 条", flush=True)
    print(f"  其中解决人非RD: {len(non_rd_bugs)} 条 (跳过)", flush=True)

    if rd_bugs:
        nocode_display = [row[:-1] for row in rd_bugs]
        generate_excel(display_columns, nocode_display, nocodebug_path)
        print(f"  已保存: {nocodebug_path}", flush=True)
    else:
        print("  无符合条件的bug，不生成 nocodebug.xlsx", flush=True)

    # ---- 第4步：发送钉钉通知 ----
    print(flush=True)
    print("=" * 60, flush=True)
    print("第4步：发送钉钉通知", flush=True)
    print("=" * 60, flush=True)

    # 加载钉钉成员映射
    dingtalk_map, member_group_map, group_supervisors = get_dingtalk_members()

    # 4a: 给解决人发送SVN未关联提醒（仅SVN未关联的RD bug）
    if not rd_bugs:
        print("  没有需要SVN提醒的bug", flush=True)
    else:
        print(f"  待发送SVN未关联通知: {len(rd_bugs)} 条", flush=True)
        for row in rd_bugs:
            print(f"    Bug#{row[COL_BUG_ID]} → {row[COL_RESOLVER]} - {row[COL_TITLE]}", flush=True)

        sent_bugs = send_dingtalk_message(rd_bugs, dingtalk_map, member_group_map, group_supervisors)

        if sent_bugs:
            append_to_sendmsgbug(columns, sent_bugs, sendmsgbug_path)
            print(f"  已记录 {len(sent_bugs)} 条到: {sendmsgbug_path}", flush=True)

    # ---- 汇总 ----
    print(flush=True)
    print("=" * 60, flush=True)
    print("汇总", flush=True)
    print("=" * 60, flush=True)
    print(f"  全部bug:         {len(rows)} 条 → currentbug.xlsx", flush=True)
    print(f"  SVN已关联:       {len(found_in_svn)} 条", flush=True)
    print(f"  SVN未关联(RD):   {len(rd_bugs)} 条 → nocodebug.xlsx", flush=True)
    print(f"  SVN未关联(非RD): {len(non_rd_bugs)} 条 (不处理)", flush=True)


def MonitorBugAssignments():
    """监控测试侧最近指派的active bug，并通知当前被指派人。"""
    output_dir = get_app_dir()
    sendmsg_assignee_path = os.path.join(output_dir, 'sendmsg_assignee.xlsx')

    print(flush=True)
    print("=" * 60, flush=True)
    print("Bug monitor: testing-assigned active bugs", flush=True)
    print("=" * 60, flush=True)

    conn = get_db_connection()
    try:
        _, assigned_rows = query_recently_assigned_bugs(conn)
        print(f"  最近一周active且指派变化的bug: {len(assigned_rows)} 条", flush=True)
    finally:
        conn.close()

    if not assigned_rows:
        print("  没有需要指派通知的bug", flush=True)
        return

    test_assigned_bugs, other_assigned_bugs = filter_test_assigned_bugs(assigned_rows)
    print(f"  其中测试侧指派: {len(test_assigned_bugs)} 条", flush=True)
    print(f"  其中非测试侧指派: {len(other_assigned_bugs)} 条", flush=True)

    # 所有active bug都发送通知，不限于测试侧指派
    all_bugs_to_notify = assigned_rows
    if not all_bugs_to_notify:
        print("  没有需要通知的bug", flush=True)
        return

    dingtalk_map, member_group_map, group_supervisors = get_dingtalk_members()
    sent_bugs = send_assignee_notification(
        all_bugs_to_notify,
        dingtalk_map,
        member_group_map,
        group_supervisors,
        record_filepath=sendmsg_assignee_path,
    )
    print(f"  本次指派通知发送成功: {len(sent_bugs)} 条", flush=True)


def query_recent_finished_integration_tasks(conn):
    """Query recently finished integration tasks."""
    half_month_ago = (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d %H:%M:%S')
    task_name_keyword = '%开发集成%'

    sql = """
    SELECT
        t.id                AS '任务编号',
        pj.name             AS '所属项目',
        t.name              AS '任务名称',
        t.status            AS '任务状态',
        assignee.realname   AS '当前负责人',
        finisher.realname   AS '完成人',
        t.finishedDate      AS '完成时间',
        finisher.role       AS '完成人职位'
    FROM zt_task t
    LEFT JOIN zt_project pj    ON t.project = pj.id
    LEFT JOIN zt_user assignee ON t.assignedTo = assignee.account
    LEFT JOIN zt_user finisher ON t.finishedBy = finisher.account
    WHERE t.deleted = '0'
      AND t.finishedDate IS NOT NULL
      AND t.finishedDate >= %s
      AND t.name LIKE %s
    ORDER BY t.finishedDate DESC
    """

    print("task query sql:", flush=True)
    print(sql.strip(), flush=True)
    print(f"task query params: finishedDate>='{half_month_ago}', name like '{task_name_keyword}'", flush=True)

    cursor = conn.cursor()
    cursor.execute(sql, (half_month_ago, task_name_keyword))
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return columns, rows


TASK_COL_ID = 0
TASK_COL_PROJECT = 1
TASK_COL_NAME = 2
TASK_COL_ASSIGNEE = 4
TASK_COL_FINISHER = 5
TASK_COL_FINISHED_DATE = 6


def send_task_dingtalk_message(task_rows, dingtalk_map, member_group_map=None, group_supervisors=None):
    """Send DingTalk reminders to task finishers."""
    if not task_rows:
        return []

    member_group_map = member_group_map or {}
    group_supervisors = group_supervisors or {}

    finisher_tasks = {}
    for row in task_rows:
        finisher = str(row[TASK_COL_FINISHER] or '').strip()
        if not finisher:
            continue
        finisher_tasks.setdefault(finisher, []).append(row)

    sent_tasks = []
    for finisher, tasks in finisher_tasks.items():
        dingtalk_id = dingtalk_map.get(finisher, '')
        if not dingtalk_id:
            print(f"  [跳过] {finisher} 不在dingtalk-mem.xlsx中", flush=True)
            continue

        task_lines = []
        for row in tasks:
            task_id = row[TASK_COL_ID]
            project = row[TASK_COL_PROJECT] or ''
            task_name = row[TASK_COL_NAME] or ''
            assignee = row[TASK_COL_ASSIGNEE] or ''
            finished_date = str(row[TASK_COL_FINISHED_DATE] or '')
            task_lines.append(
                f"  - Task#{task_id} [{project}] {task_name} (负责人: {assignee}, 完成时间: {finished_date})"
            )

        text = (
            f"提测邮件：@{finisher} 完成以下“开发集成”任务，请及时发送提测邮件。\n\n"
            + "\n".join(task_lines)
        )

        # 尝试直接发送
        direct_sent = False
        userid = dingtalk_map.get(finisher, '')
        if userid:
            all_user_ids = [userid]
            finisher_supervisors = get_supervisors_for_person(finisher, member_group_map, group_supervisors)
            for sup_name in finisher_supervisors:
                if sup_name != finisher:
                    sup_userid = dingtalk_map.get(sup_name, '')
                    if sup_userid:
                        all_user_ids.append(sup_userid)
            direct_sent = send_direct_message(all_user_ids, text)
            if direct_sent:
                print(f"  直接消息发送成功 → {finisher} ({len(tasks)} tasks)", flush=True)
                log_dingtalk_send(finisher, text, "direct")
                sent_tasks.extend(tasks)

        # 回退到群机器人
        if not direct_sent:
            at_mobiles = [dingtalk_id]
            finisher_supervisors = get_supervisors_for_person(finisher, member_group_map, group_supervisors)
            for sup_name in finisher_supervisors:
                sup_dingtalk_id = dingtalk_map.get(sup_name, '')
                if sup_dingtalk_id and sup_dingtalk_id not in at_mobiles:
                    at_mobiles.append(sup_dingtalk_id)

            payload = {
                "msgtype": "text",
                "text": {"content": text},
                "at": {
                    "atMobiles": at_mobiles,
                    "isAtAll": False
                }
            }

            try:
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                signed_url = get_dingtalk_signed_url()
                req = urllib.request.Request(
                    signed_url,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                    if result.get('errcode') == 0:
                        print(f"  群机器人消息发送成功 → {finisher} ({len(tasks)} tasks)", flush=True)
                        log_dingtalk_send(finisher, text, "robot")
                        sent_tasks.extend(tasks)
                    else:
                        print(f"  task reminder failed -> {finisher}: {result.get('errmsg')}", flush=True)
            except Exception as e:
                print(f"  task reminder exception -> {finisher}: {e}", flush=True)

    return sent_tasks


def MonitorTasks():
    output_dir = get_app_dir()
    currenttask_path = os.path.join(output_dir, 'currenttask.xlsx')
    sendmsgtask_path = os.path.join(output_dir, 'sendmsgtask.xlsx')

    print(flush=True)
    print("=" * 60, flush=True)
    print("Task monitor: recently finished integration tasks", flush=True)
    print("=" * 60, flush=True)

    conn = get_db_connection()
    try:
        columns, rows = query_recent_finished_integration_tasks(conn)
        print(f"queried tasks: {len(rows)}", flush=True)
    finally:
        conn.close()

    if not rows:
        print("no recently finished integration tasks", flush=True)
        return

    sent_ids = load_sent_bug_ids(sendmsgtask_path)
    if sent_ids:
        print(f"already reminded tasks: {len(sent_ids)}", flush=True)

    rows = [row for row in rows if int(row[TASK_COL_ID]) not in sent_ids]
    if not rows:
        print("no new tasks after excluding previously reminded tasks", flush=True)
        return

    generate_excel(columns[:-1], [row[:-1] for row in rows], currenttask_path)
    print(f"saved current tasks: {currenttask_path}", flush=True)

    dingtalk_map, member_group_map, group_supervisors = get_dingtalk_members()

    sent_tasks = send_task_dingtalk_message(rows, dingtalk_map, member_group_map, group_supervisors)
    if sent_tasks:
        append_to_sendmsgbug(columns, sent_tasks, sendmsgtask_path)
        print(f"saved sent task reminders: {sendmsgtask_path}", flush=True)


def load_sent_record_time_map(filepath, id_col=1, sent_time_col=None):
    """Load last sent time map from an excel file."""
    sent_time_map = {}
    if not os.path.exists(filepath):
        return sent_time_map

    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        last_col = sent_time_col or ws.max_column
        for row_idx in range(2, ws.max_row + 1):
            item_id = ws.cell(row=row_idx, column=id_col).value
            sent_time_value = ws.cell(row=row_idx, column=last_col).value
            if not item_id or not sent_time_value:
                continue

            try:
                item_id = int(item_id)
            except (TypeError, ValueError):
                continue

            if isinstance(sent_time_value, datetime):
                sent_time = sent_time_value
            else:
                try:
                    sent_time = datetime.strptime(str(sent_time_value), '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

            prev_time = sent_time_map.get(item_id)
            if prev_time is None or sent_time > prev_time:
                sent_time_map[item_id] = sent_time
        wb.close()
    except Exception as e:
        print(f"  [warn] failed to load send record time map: {e}", flush=True)

    return sent_time_map


def query_delayed_waiting_tasks(conn):
    """Query tasks whose estimated start date is overdue by more than one day and still waiting."""
    one_month_ago = (datetime.now() - timedelta(days=30)).date()
    one_day_ago = (datetime.now() - timedelta(days=1)).date()

    sql = """
    SELECT
        t.id                AS '任务编号',
        pj.name             AS '所属项目',
        t.name              AS '任务名称',
        t.status            AS '任务状态',
        assignee.realname   AS '负责人',
        t.estStarted        AS '预计开始时间',
        t.deadline          AS '截止日期',
        t.assignedDate      AS '指派时间',
        assignee.account    AS '负责人账号'
    FROM zt_task t
    LEFT JOIN zt_project pj    ON t.project = pj.id
    LEFT JOIN zt_user assignee ON t.assignedTo = assignee.account
    WHERE t.deleted = '0'
      AND t.status = 'wait'
      AND t.estStarted IS NOT NULL
      AND t.estStarted <> '0000-00-00'
      AND t.estStarted >= %s
      AND t.estStarted < %s
    ORDER BY t.estStarted ASC, t.id ASC
    """

    print("delay task query sql:", flush=True)
    print(sql.strip(), flush=True)
    print(
        f"delay task query params: estStarted>='{one_month_ago}', estStarted<'{one_day_ago}', status='wait'",
        flush=True
    )

    cursor = conn.cursor()
    final_sql = sql.replace('%s', "'%s'") % (one_month_ago, one_day_ago)
    print(f"delay task final sql:\n{final_sql.strip()}", flush=True)
    cursor.execute(sql, (one_month_ago, one_day_ago))
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return columns, rows


DELAY_TASK_COL_ID = 0
DELAY_TASK_COL_PROJECT = 1
DELAY_TASK_COL_NAME = 2
DELAY_TASK_COL_STATUS = 3
DELAY_TASK_COL_ASSIGNEE = 4
DELAY_TASK_COL_EST_STARTED = 5
DELAY_TASK_COL_DEADLINE = 6


def filter_delay_tasks_by_remind_interval(task_rows, last_sent_time_map, interval_days=2):
    """Keep only tasks that have never been reminded or were reminded before the interval."""
    now = datetime.now()
    interval = timedelta(days=interval_days)
    filtered_rows = []
    skipped_rows = []

    for row in task_rows:
        task_id = int(row[DELAY_TASK_COL_ID])
        last_sent_time = last_sent_time_map.get(task_id)
        if last_sent_time and now - last_sent_time < interval:
            skipped_rows.append(row)
            continue
        filtered_rows.append(row)

    return filtered_rows, skipped_rows


def send_delay_task_dingtalk_message(task_rows, dingtalk_map, member_group_map=None, group_supervisors=None):
    """Send DingTalk reminders for delayed waiting tasks."""
    if not task_rows:
        return []

    member_group_map = member_group_map or {}
    group_supervisors = group_supervisors or {}

    assignee_tasks = {}
    for row in task_rows:
        assignee = str(row[DELAY_TASK_COL_ASSIGNEE] or '').strip()
        if not assignee:
            continue
        assignee_tasks.setdefault(assignee, []).append(row)

    sent_tasks = []
    for assignee, tasks in assignee_tasks.items():
        dingtalk_id = dingtalk_map.get(assignee, '')
        if not dingtalk_id:
            print(f"  [跳过] {assignee} 不在dingtalk-mem.xlsx中", flush=True)
            continue

        task_lines = []
        for row in tasks:
            task_id = row[DELAY_TASK_COL_ID]
            project = row[DELAY_TASK_COL_PROJECT] or ''
            task_name = row[DELAY_TASK_COL_NAME] or ''
            est_started = str(row[DELAY_TASK_COL_EST_STARTED] or '')
            deadline = str(row[DELAY_TASK_COL_DEADLINE] or '')
            task_lines.append(
                f"  - Task#{task_id} [{project}] {task_name} (预计开始: {est_started}, 截止日期: {deadline})"
            )

        text = (
            f"任务延迟：@{assignee} 以下任务已超过预计开始时间且状态仍为wait，请及时更新任务状态。\n\n"
            + "\n".join(task_lines)
        )

        # 尝试直接发送
        direct_sent = False
        userid = dingtalk_map.get(assignee, '')
        if userid:
            all_user_ids = [userid]
            assignee_supervisors = get_supervisors_for_person(assignee, member_group_map, group_supervisors)
            for sup_name in assignee_supervisors:
                if sup_name != assignee:
                    sup_userid = dingtalk_map.get(sup_name, '')
                    if sup_userid:
                        all_user_ids.append(sup_userid)
            direct_sent = send_direct_message(all_user_ids, text)
            if direct_sent:
                print(f"  直接消息发送成功 → {assignee} ({len(tasks)} tasks)", flush=True)
                log_dingtalk_send(assignee, text, "direct")
                sent_tasks.extend(tasks)

        # 回退到群机器人
        if not direct_sent:
            at_mobiles = [dingtalk_id]
            assignee_supervisors = get_supervisors_for_person(assignee, member_group_map, group_supervisors)
            for sup_name in assignee_supervisors:
                sup_dingtalk_id = dingtalk_map.get(sup_name, '')
                if sup_dingtalk_id and sup_dingtalk_id not in at_mobiles:
                    at_mobiles.append(sup_dingtalk_id)

            payload = {
                "msgtype": "text",
                "text": {"content": text},
                "at": {
                    "atMobiles": at_mobiles,
                    "isAtAll": False
                }
            }

            try:
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                signed_url = get_dingtalk_signed_url()
                req = urllib.request.Request(
                    signed_url,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                    if result.get('errcode') == 0:
                        print(f"  群机器人消息发送成功 → {assignee} ({len(tasks)} tasks)", flush=True)
                        log_dingtalk_send(assignee, text, "robot")
                        sent_tasks.extend(tasks)
                    else:
                        print(f"  delay task reminder failed -> {assignee}: {result.get('errmsg')}", flush=True)
            except Exception as e:
                print(f"  delay task reminder exception -> {assignee}: {e}", flush=True)

    return sent_tasks


def MonitorDelayedTasks():
    output_dir = get_app_dir()
    current_delay_task_path = os.path.join(output_dir, 'currentdelaytask.xlsx')
    sendmsg_delay_task_path = os.path.join(output_dir, 'sendmsgdelaytask.xlsx')

    print(flush=True)
    print("=" * 60, flush=True)
    print("Task monitor: delayed waiting tasks", flush=True)
    print("=" * 60, flush=True)

    conn = get_db_connection()
    try:
        columns, rows = query_delayed_waiting_tasks(conn)
        print(f"queried delayed tasks: {len(rows)}", flush=True)
    finally:
        conn.close()

    if not rows:
        print("no delayed waiting tasks", flush=True)
        return

    last_sent_time_map = load_sent_record_time_map(sendmsg_delay_task_path)
    if last_sent_time_map:
        print(f"loaded delayed task send records: {len(last_sent_time_map)}", flush=True)

    rows, skipped_rows = filter_delay_tasks_by_remind_interval(rows, last_sent_time_map, interval_days=2)
    print(f"delayed tasks to remind: {len(rows)}", flush=True)
    print(f"delayed tasks skipped by 2-day interval: {len(skipped_rows)}", flush=True)
    if not rows:
        print("no delayed tasks need reminding right now", flush=True)
        return

    generate_excel(columns[:-1], [row[:-1] for row in rows], current_delay_task_path)
    print(f"saved current delayed tasks: {current_delay_task_path}", flush=True)

    dingtalk_map, member_group_map, group_supervisors = get_dingtalk_members()

    sent_tasks = send_delay_task_dingtalk_message(rows, dingtalk_map, member_group_map, group_supervisors)
    if sent_tasks:
        append_to_sendmsgbug(columns, sent_tasks, sendmsg_delay_task_path)
        print(f"saved delayed task reminders: {sendmsg_delay_task_path}", flush=True)


def query_overdue_deadline_tasks(conn):
    """Query tasks whose deadline is overdue by more than one day, estStarted is within one month, and status is wait/doing."""
    one_month_ago = (datetime.now() - timedelta(days=30)).date()
    one_day_ago = (datetime.now() - timedelta(days=1)).date()

    sql = """
    SELECT
        t.id                AS '任务编号',
        pj.name             AS '所属项目',
        t.name              AS '任务名称',
        t.status            AS '任务状态',
        assignee.realname   AS '负责人',
        t.estStarted        AS '预计开始时间',
        t.deadline          AS '截止日期',
        t.assignedDate      AS '指派时间',
        assignee.account    AS '负责人账号'
    FROM zt_task t
    LEFT JOIN zt_project pj    ON t.project = pj.id
    LEFT JOIN zt_user assignee ON t.assignedTo = assignee.account
    WHERE t.deleted = '0'
      AND t.status IN ('0000', 'doing')
      AND t.estStarted IS NOT NULL
      AND t.estStarted <> '0000-00-00'
      AND t.estStarted >= %s
      AND t.deadline IS NOT NULL
      AND t.deadline <> '0000-00-00'
      AND t.deadline < %s
    ORDER BY t.deadline ASC, t.id ASC
    """

    print("deadline task query sql:", flush=True)
    print(sql.strip(), flush=True)
    print(
        f"deadline task query params: estStarted>='{one_month_ago}', deadline<'{one_day_ago}', status in ('wait','doing')",
        flush=True
    )

    cursor = conn.cursor()
    cursor.execute(sql, (one_month_ago, one_day_ago))
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return columns, rows


def send_deadline_task_dingtalk_message(task_rows, dingtalk_map, member_group_map=None, group_supervisors=None):
    """Send DingTalk reminders for overdue deadline tasks."""
    if not task_rows:
        return []

    member_group_map = member_group_map or {}
    group_supervisors = group_supervisors or {}

    assignee_tasks = {}
    for row in task_rows:
        assignee = str(row[DELAY_TASK_COL_ASSIGNEE] or '').strip()
        if not assignee:
            continue
        assignee_tasks.setdefault(assignee, []).append(row)

    sent_tasks = []
    for assignee, tasks in assignee_tasks.items():
        dingtalk_id = dingtalk_map.get(assignee, '')
        if not dingtalk_id:
            print(f"  [跳过] {assignee} 不在dingtalk-mem.xlsx中", flush=True)
            continue

        task_lines = []
        for row in tasks:
            task_id = row[DELAY_TASK_COL_ID]
            project = row[DELAY_TASK_COL_PROJECT] or ''
            task_name = row[DELAY_TASK_COL_NAME] or ''
            status = str(row[DELAY_TASK_COL_STATUS] or '')
            est_started = str(row[DELAY_TASK_COL_EST_STARTED] or '')
            deadline = str(row[DELAY_TASK_COL_DEADLINE] or '')
            task_lines.append(
                f"  - Task#{task_id} [{project}] {task_name} (状态: {status}, 预计开始: {est_started}, 截止日期: {deadline})"
            )

        text = (
            f"任务-延迟：@{assignee} 以下任务已超过截止日期，请及时更新任务状态。\n\n"
            + "\n".join(task_lines)
        )

        # 尝试直接发送
        direct_sent = False
        userid = dingtalk_map.get(assignee, '')
        if userid:
            all_user_ids = [userid]
            assignee_supervisors = get_supervisors_for_person(assignee, member_group_map, group_supervisors)
            for sup_name in assignee_supervisors:
                if sup_name != assignee:
                    sup_userid = dingtalk_map.get(sup_name, '')
                    if sup_userid:
                        all_user_ids.append(sup_userid)
            direct_sent = send_direct_message(all_user_ids, text)
            if direct_sent:
                print(f"  直接消息发送成功 → {assignee} ({len(tasks)} tasks)", flush=True)
                log_dingtalk_send(assignee, text, "direct")
                sent_tasks.extend(tasks)

        # 回退到群机器人
        if not direct_sent:
            at_mobiles = [dingtalk_id]
            assignee_supervisors = get_supervisors_for_person(assignee, member_group_map, group_supervisors)
            for sup_name in assignee_supervisors:
                sup_dingtalk_id = dingtalk_map.get(sup_name, '')
                if sup_dingtalk_id and sup_dingtalk_id not in at_mobiles:
                    at_mobiles.append(sup_dingtalk_id)

            payload = {
                "msgtype": "text",
                "text": {"content": text},
                "at": {
                    "atMobiles": at_mobiles,
                    "isAtAll": False
                }
            }

            try:
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                signed_url = get_dingtalk_signed_url()
                req = urllib.request.Request(
                    signed_url,
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                    if result.get('errcode') == 0:
                        print(f"  群机器人消息发送成功 → {assignee} ({len(tasks)} tasks)", flush=True)
                        log_dingtalk_send(assignee, text, "robot")
                        sent_tasks.extend(tasks)
                    else:
                        sent_tasks.extend(tasks)
                        print(f"  deadline task reminder failed -> {assignee}: {result.get('errmsg')}", flush=True)
            except Exception as e:
                print(f"  deadline task reminder exception -> {assignee}: {e}", flush=True)

    return sent_tasks


def MonitorDeadlineTasks():
    output_dir = get_app_dir()
    current_deadline_task_path = os.path.join(output_dir, 'currentdeadlinetask.xlsx')
    sendmsg_deadline_task_path = os.path.join(output_dir, 'sendmsgdeadlinetask.xlsx')

    print(flush=True)
    print("=" * 60, flush=True)
    print("Task monitor: overdue deadline tasks", flush=True)
    print("=" * 60, flush=True)

    conn = get_db_connection()
    try:
        columns, rows = query_overdue_deadline_tasks(conn)
        print(f"queried overdue deadline tasks: {len(rows)}", flush=True)
    finally:
        conn.close()

    if not rows:
        print("no overdue deadline tasks", flush=True)
        return

    last_sent_time_map = load_sent_record_time_map(sendmsg_deadline_task_path)
    if last_sent_time_map:
        print(f"loaded deadline task send records: {len(last_sent_time_map)}", flush=True)

    rows, skipped_rows = filter_delay_tasks_by_remind_interval(rows, last_sent_time_map, interval_days=2)
    print(f"deadline tasks to remind: {len(rows)}", flush=True)
    print(f"deadline tasks skipped by 2-day interval: {len(skipped_rows)}", flush=True)
    if not rows:
        print("no overdue deadline tasks need reminding right now", flush=True)
        return

    generate_excel(columns[:-1], [row[:-1] for row in rows], current_deadline_task_path)
    print(f"saved current deadline tasks: {current_deadline_task_path}", flush=True)

    dingtalk_map, member_group_map, group_supervisors = get_dingtalk_members()

    sent_tasks = send_deadline_task_dingtalk_message(rows, dingtalk_map, member_group_map, group_supervisors)
    if sent_tasks:
        append_to_sendmsgbug(columns, sent_tasks, sendmsg_deadline_task_path)
        print(f"saved deadline task reminders: {sendmsg_deadline_task_path}", flush=True)


def load_project_report_config(filepath):
    """从project-report.xlsx加载要统计的项目列表。
    
    格式: 列1=负责人, 列2=项目名称
    返回: [(负责人, 项目名称), ...]
    """
    projects = []
    if not os.path.exists(filepath):
        print(f"  [错误] 未找到项目报告配置文件: {filepath}", flush=True)
        return projects
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        for row_idx in range(2, ws.max_row + 1):
            owner = ws.cell(row=row_idx, column=1).value
            project_name = ws.cell(row=row_idx, column=2).value
            if owner and project_name:
                projects.append((str(owner).strip(), str(project_name).strip()))
        wb.close()
    except Exception as e:
        print(f"  [错误] 读取project-report.xlsx失败: {e}", flush=True)
    return projects


def query_project_ids_by_names(conn, project_names):
    """根据项目名称查询项目ID，返回 {项目名称: 项目ID}"""
    if not project_names:
        return {}
    cursor = conn.cursor()
    placeholders = ','.join(['%s'] * len(project_names))
    sql = f"SELECT id, name FROM zt_project WHERE name IN ({placeholders}) AND deleted='0'"
    cursor.execute(sql, project_names)
    result = {}
    for row in cursor.fetchall():
        result[row[1]] = row[0]
    cursor.close()
    return result


def query_project_bug_stats(conn, project_id):
    """统计项目相关的bug情况。
    
    返回: {
        'today_opened': 当日新增数,
        'today_resolved': 当日解决数,
        'today_closed': 当日关闭数,
        'total_active': 总激活数,
        'total_resolved': 总的解决数,
        'reactivated': 被二次激活数量,
        'active_details': [(id, title, days, opened_count), ...] 激活bug详情
    }
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    cursor = conn.cursor()

    # 当日新增数 (openedDate在今天)
    cursor.execute(
        "SELECT COUNT(*) FROM zt_bug WHERE project=%s AND deleted='0' AND DATE(openedDate)=%s",
        (project_id, today_str)
    )
    today_opened = cursor.fetchone()[0]

    # 当日解决数 (resolvedDate在今天)
    cursor.execute(
        "SELECT COUNT(*) FROM zt_bug WHERE project=%s AND deleted='0' AND DATE(resolvedDate)=%s",
        (project_id, today_str)
    )
    today_resolved = cursor.fetchone()[0]

    # 当日关闭数 (closedDate在今天)
    cursor.execute(
        "SELECT COUNT(*) FROM zt_bug WHERE project=%s AND deleted='0' AND DATE(closedDate)=%s",
        (project_id, today_str)
    )
    today_closed = cursor.fetchone()[0]

    # 总激活数 (status='active')
    cursor.execute(
        "SELECT COUNT(*) FROM zt_bug WHERE project=%s AND deleted='0' AND status='active'",
        (project_id,)
    )
    total_active = cursor.fetchone()[0]

    # 总的解决数 (status='resolved' 或 status='closed')
    cursor.execute(
        "SELECT COUNT(*) FROM zt_bug WHERE project=%s AND deleted='0' AND status IN ('resolved','closed')",
        (project_id,)
    )
    total_resolved = cursor.fetchone()[0]

    # 总关闭数 (status='closed')
    cursor.execute(
        "SELECT COUNT(*) FROM zt_bug WHERE project=%s AND deleted='0' AND status='closed'",
        (project_id,)
    )
    total_closed = cursor.fetchone()[0]

    # 被二次激活数量：在zt_action中同一个bug被activated两次以上
    cursor.execute(
        """SELECT COUNT(*) FROM (
            SELECT a.objectID
            FROM zt_action a
            INNER JOIN zt_bug b ON a.objectID = b.id AND b.project=%s AND b.deleted='0'
            WHERE a.objectType='bug' AND a.action='activated'
            GROUP BY a.objectID
            HAVING COUNT(*) >= 2
        ) AS reactivated_bugs""",
        (project_id,)
    )
    reactivated = cursor.fetchone()[0]

    # 激活bug详情：id, 标题, 已生成的天数, opened次数, 被指派人
    cursor.execute(
        """SELECT b.id, b.title, b.openedDate,
            (SELECT COUNT(*) FROM zt_action a
             WHERE a.objectType='bug' AND a.objectID=b.id AND a.action='opened'
            ) AS opened_count,
            IFNULL(u.realname, b.assignedTo) AS assignee_name
        FROM zt_bug b
        LEFT JOIN zt_user u ON b.assignedTo = u.account
        WHERE b.project=%s AND b.deleted='0' AND b.status='active'
        ORDER BY b.openedDate ASC""",
        (project_id,)
    )
    active_details = []
    for row in cursor.fetchall():
        bug_id = row[0]
        title = row[1]
        opened_date = row[2]
        opened_count = row[3]
        assignee = row[4] or ''
        if isinstance(opened_date, datetime):
            days = (now - opened_date).days
        else:
            days = 0
        active_details.append((bug_id, title, days, opened_count, assignee))

    cursor.close()
    return {
        'today_opened': today_opened,
        'today_resolved': today_resolved,
        'today_closed': today_closed,
        'total_active': total_active,
        'total_resolved': total_resolved,
        'total_closed': total_closed,
        'reactivated': reactivated,
        'active_details': active_details,
    }


def query_project_task_stats(conn, project_id):
    """统计项目相关的任务情况。
    
    返回: {
        'today_finished': 今日完成任务数,
        'delayed_tasks': [(任务名称, 截止日期), ...] 延期任务,
        'project_end': 发布日期(项目结束时间)
    }
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor = conn.cursor()

    # 今日完成任务数
    cursor.execute(
        "SELECT COUNT(*) FROM zt_task WHERE project=%s AND deleted='0' AND DATE(finishedDate)=%s",
        (project_id, today_str)
    )
    today_finished = cursor.fetchone()[0]

    # 延期任务：deadline已过且status不是done/closed/cancel
    cursor.execute(
        """SELECT t.name, t.deadline, IFNULL(u.realname, t.assignedTo) AS assignee_name
        FROM zt_task t
        LEFT JOIN zt_user u ON t.assignedTo = u.account
        WHERE t.project=%s AND t.deleted='0'
          AND t.deadline IS NOT NULL AND t.deadline <> '0000-00-00'
          AND t.deadline < %s
          AND t.status IN ('wait', 'doing', 'pause')
        ORDER BY t.deadline ASC""",
        (project_id, today_str)
    )
    delayed_tasks = [(row[0], str(row[1]), row[2] or '') for row in cursor.fetchall()]

    # 发布日期（项目结束时间）
    cursor.execute("SELECT `end` FROM zt_project WHERE id=%s", (project_id,))
    row = cursor.fetchone()
    project_end = str(row[0]) if row else ''

    cursor.close()
    return {
        'today_finished': today_finished,
        'delayed_tasks': delayed_tasks,
        'project_end': project_end,
    }


def generate_project_report(project_stats, output_path):
    """生成项目统计报告Excel。
    
    project_stats: [(负责人, 项目名称, bug_stats, task_stats), ...]
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "项目统计报告"

    headers = [
        '负责人', '项目名称', '发布日期',
        '当日新增Bug', '当日解决Bug', '当日关闭Bug',
        '总激活Bug', '总解决Bug', '总关闭Bug', '二次激活Bug',
        '今日完成任务', '延期任务数', '延期任务明细'
    ]

    # 表头样式
    header_font = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    data_font = Font(name='微软雅黑', size=10)
    data_alignment = Alignment(vertical='center', wrap_text=True)

    for row_idx, (owner, project_name, bug_stats, task_stats) in enumerate(project_stats, 2):
        delayed_detail = '\n'.join(
            f"{item[0]}(截止:{item[1]}, 负责人:{item[2]})" for item in task_stats['delayed_tasks']
        ) if task_stats['delayed_tasks'] else '无'

        row_data = [
            owner,
            project_name,
            task_stats['project_end'],
            bug_stats['today_opened'],
            bug_stats['today_resolved'],
            bug_stats['today_closed'],
            bug_stats['total_active'],
            bug_stats['total_resolved'],
            bug_stats['total_closed'],
            bug_stats['reactivated'],
            task_stats['today_finished'],
            len(task_stats['delayed_tasks']),
            delayed_detail,
        ]

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.alignment = data_alignment
            cell.border = thin_border

    # 调整列宽
    col_widths = [10, 20, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 40]
    for col_idx, width in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = width

    ws.freeze_panes = 'A2'

    # 激活bug详情sheet
    ws2 = wb.create_sheet(title="激活Bug详情")
    detail_headers = ['负责人', '项目名称', 'Bug编号', 'Bug标题', '已生成天数', 'Opened次数', '被指派人']
    for col_idx, h in enumerate(detail_headers, 1):
        cell = ws2.cell(row=1, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border

    detail_row = 2
    for owner, project_name, bug_stats, task_stats in project_stats:
        for bug_id, title, days, opened_count, assignee in bug_stats.get('active_details', []):
            row_data = [owner, project_name, bug_id, title, days, opened_count, assignee]
            for col_idx, value in enumerate(row_data, 1):
                cell = ws2.cell(row=detail_row, column=col_idx, value=value)
                cell.font = data_font
                cell.alignment = data_alignment
                cell.border = thin_border
            detail_row += 1

    detail_widths = [10, 20, 10, 50, 12, 12, 12]
    for col_idx, width in enumerate(detail_widths, 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = width
    ws2.freeze_panes = 'A2'

    wb.save(output_path)
    return output_path


def evaluate_project_health(bug_stats, task_stats):
    """根据bug和任务数据对项目整体情况做评定。"""
    issues = []
    total_active = bug_stats['total_active']
    reactivated = bug_stats['reactivated']
    delayed_count = len(task_stats['delayed_tasks'])

    if total_active > 10:
        issues.append(f"激活Bug较多({total_active}个)")
    if reactivated > 3:
        issues.append(f"二次激活Bug较多({reactivated}个)，需关注开发质量")
    if delayed_count > 5:
        issues.append(f"延期任务较多({delayed_count}个)，进度风险较高")
    elif delayed_count > 0:
        issues.append(f"存在{delayed_count}个延期任务")

    if bug_stats['today_opened'] > bug_stats['today_resolved'] + bug_stats['today_closed']:
        issues.append("今日新增Bug多于解决+关闭数，Bug积压趋势")

    if not issues:
        return "✅ 项目整体状况良好"
    elif len(issues) <= 1:
        return "⚠️ " + issues[0]
    else:
        return "⚠️ 风险提示:\n  " + "\n  ".join(issues)


def send_project_report_dingtalk(project_stats, dingtalk_map):
    """按负责人和项目分组，每个项目发送一条包含bug和任务统计的钉钉消息。"""
    # 按负责人分组
    owner_stats = {}
    for owner, project_name, bug_stats, task_stats in project_stats:
        owner_stats.setdefault(owner, []).append((project_name, bug_stats, task_stats))

    for owner, items in owner_stats.items():
        dingtalk_id = dingtalk_map.get(owner, '')
        if not dingtalk_id:
            print(f"  [跳过报告通知] {owner} 不在dingtalk-mem.xlsx中", flush=True)
            continue

        userid = dingtalk_map.get(owner, '')
        if not userid:
            continue

        # 每个项目发送一条消息
        for project_name, bug_stats, task_stats in items:
            lines = []
            lines.append(f"【{project_name}】项目统计 (发布日期: {task_stats['project_end']})")
            lines.append("")
            # Bug统计部分
            lines.append("▶ Bug情况:")
            lines.append(
                f"  今日新增: {bug_stats['today_opened']}, "
                f"今日解决: {bug_stats['today_resolved']}, "
                f"今日关闭: {bug_stats['today_closed']}"
            )
            lines.append(
                f"  总激活: {bug_stats['total_active']}, "
                f"总解决: {bug_stats['total_resolved']}, "
                f"总关闭: {bug_stats['total_closed']}, "
                f"二次激活: {bug_stats['reactivated']}"
            )
            # 激活bug详情
            active_details = bug_stats.get('active_details', [])
            if active_details:
                lines.append(f"  激活Bug详情({len(active_details)}个):")
                for bug_id, title, days, opened_count, assignee in active_details[:20]:
                    lines.append(
                        f"    Bug#{bug_id} {title} ({days}天, opened{opened_count}次, 指派:{assignee})"
                    )
                if len(active_details) > 20:
                    lines.append(f"    ...共{len(active_details)}个，仅显示前20个")

            lines.append("")
            # 任务统计部分
            lines.append("▶ 任务情况:")
            lines.append(f"  今日完成任务: {task_stats['today_finished']}")
            delayed = task_stats['delayed_tasks']
            if delayed:
                lines.append(f"  延期任务({len(delayed)}个):")
                for item in delayed[:20]:
                    name, date, assignee = item[0], item[1], item[2]
                    lines.append(f"    - {name} (截止: {date}, 负责人: {assignee})")
                if len(delayed) > 20:
                    lines.append(f"    ...共{len(delayed)}个，仅显示前20个")
            else:
                lines.append("  延期任务: 无")

            # 项目整体评定
            lines.append("")
            lines.append("▶ 整体评定:")
            lines.append(f"  {evaluate_project_health(bug_stats, task_stats)}")

            text = f"{project_name}项目统计：\n\n" + "\n".join(lines)

            sent = send_direct_message([userid], text)
            if sent:
                print(f"  项目统计消息发送成功 → {owner} [{project_name}]", flush=True)
                log_dingtalk_send(owner, text, "direct")
            else:
                print(f"  项目统计消息发送失败 → {owner} [{project_name}]", flush=True)


def MonitorProjectReport():
    """功能6：项目bug和任务统计报告"""
    output_dir = get_app_dir()
    config_path = os.path.join(output_dir, 'project-report.xlsx')
    report_path = os.path.join(output_dir, f'project-report-{datetime.now().strftime("%Y%m%d")}.xlsx')

    print(flush=True)
    print("=" * 60, flush=True)
    print("项目统计报告", flush=True)
    print("=" * 60, flush=True)

    # 加载项目配置
    projects = load_project_report_config(config_path)
    if not projects:
        print("未配置要统计的项目，程序结束", flush=True)
        return

    print(f"已加载 {len(projects)} 个项目配置", flush=True)

    conn = get_db_connection()
    try:
        # 获取项目ID
        project_names = list(set(name for _, name in projects))
        name_id_map = query_project_ids_by_names(conn, project_names)
        print(f"匹配到 {len(name_id_map)} 个项目", flush=True)

        # 统计每个项目
        project_stats = []
        for owner, project_name in projects:
            project_id = name_id_map.get(project_name)
            if not project_id:
                print(f"  [跳过] 未找到项目: {project_name}", flush=True)
                project_stats.append((owner, project_name,
                    {'today_opened': 0, 'today_resolved': 0, 'today_closed': 0,
                     'total_active': 0, 'total_resolved': 0, 'reactivated': 0},
                    {'today_finished': 0, 'delayed_tasks': [], 'project_end': '未找到'}))
                continue

            print(f"  统计项目: {project_name} (ID={project_id}, 负责人={owner})", flush=True)
            bug_stats = query_project_bug_stats(conn, project_id)
            task_stats = query_project_task_stats(conn, project_id)
            project_stats.append((owner, project_name, bug_stats, task_stats))

            print(f"    Bug: 今日新增={bug_stats['today_opened']}, 今日解决={bug_stats['today_resolved']}, "
                  f"今日关闭={bug_stats['today_closed']}, 总激活={bug_stats['total_active']}, "
                  f"总解决={bug_stats['total_resolved']}, 总关闭={bug_stats['total_closed']}, "
                  f"二次激活={bug_stats['reactivated']}", flush=True)
            print(f"    任务: 今日完成={task_stats['today_finished']}, "
                  f"延期={len(task_stats['delayed_tasks'])}, 发布日期={task_stats['project_end']}", flush=True)

    finally:
        conn.close()

    # 生成报告
    generate_project_report(project_stats, report_path)
    print(f"\n报告已生成: {report_path}", flush=True)

    # 发送钉钉消息给负责人
    print(flush=True)
    print("=" * 60, flush=True)
    print("发送项目统计钉钉消息", flush=True)
    print("=" * 60, flush=True)
    dingtalk_map, _, _ = get_dingtalk_members()
    send_project_report_dingtalk(project_stats, dingtalk_map)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'report':
        MonitorProjectReport()
    else:
        MonitorBugs()
        MonitorBugAssignments()
        MonitorTasks()
        MonitorDelayedTasks()
        MonitorDeadlineTasks()
