"""
禅道监控 - 查询最近一周已解决的bug，结合SVN提交记录生成报表，并通过钉钉通知

流程：
1. 从禅道数据库查询最近一周已解决的bug → 生成 currentbug.xlsx
2. 从多个SVN仓库提取最近两周的提交记录
3. SVN中未找到 且 解决人职位为RD 的bug → 生成 nocodebug.xlsx
4. 遍历 nocodebug.xlsx，排除已发过消息的bug后，向解决人发送钉钉消息
5. 发送成功的bug记录到 sendmsgbug.xlsx
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
COL_ASSIGNEE = 10       # 当前负责人 realname
COL_RESOLVER = 12       # 解决人 realname
COL_RESOLVED_DATE = 13
COL_RESOLUTION = 14     # 解决方案
COL_RESOLVER_ROLE = 17  # 解决人职位 (因插入resolution列，从16→17)

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

SVN_REPOS = [
    "http://172.17.188.253/svn/diskcopy/01_ProjectArea/_main",
    "http://172.17.188.253/svn/diskcopy/01_ProjectArea/work",
    "http://172.17.188.253/svn/epm2/01_ProjectArea/00_Source/_EPM_main",
    "http://172.17.188.253/svn/epm2/01_ProjectArea/00_Source/_EPM_work",
    "http://172.17.188.253/svn/Toolkit_Shell/01_Project/00_Source/_main",
    "http://172.17.188.253/svn/share_lib/99_PublicLibrary",
]


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
    """从dingtalk-mem.xlsx加载 {姓名: 钉钉号} 映射"""
    member_map = {}
    if not os.path.exists(filepath):
        print(f"  [警告] 未找到钉钉成员映射文件: {filepath}", flush=True)
        return member_map
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        for row_idx in range(2, ws.max_row + 1):  # 跳过表头
            name = ws.cell(row=row_idx, column=1).value
            dingtalk_id = ws.cell(row=row_idx, column=2).value
            if name and dingtalk_id:
                member_map[str(name).strip()] = str(dingtalk_id).strip()
        wb.close()
    except Exception as e:
        print(f"  [警告] 读取dingtalk-mem.xlsx失败: {e}", flush=True)
    return member_map


def send_dingtalk_message(bug_rows, dingtalk_map):
    """向解决人发送钉钉消息，通过钉钉号@指定人，返回发送成功的bug列表"""
    if not bug_rows:
        return []

    # 按解决人分组
    resolver_bugs = {}
    for row in bug_rows:
        resolver = str(row[COL_RESOLVER] or '未知')
        resolver_bugs.setdefault(resolver, []).append(row)

    sent_bugs = []
    for resolver, bugs in resolver_bugs.items():
        # 查找钉钉号
        dingtalk_id = dingtalk_map.get(resolver, '')
        if not dingtalk_id:
            print(f"  [警告] 未找到 {resolver} 的钉钉号，无法@高亮", flush=True)
            continue

        # 构造text消息内容
        bug_lines = []
        has_non_fixed = False  # 是否存在 resolution 非 fixed 的 bug
        non_fixed_assignees = set()  # 非 fixed bug 的当前负责人集合
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

        # 需要 @ 的人列表
        at_mobiles = [dingtalk_id] if dingtalk_id else []
        at_text = f"@{resolver}" if dingtalk_id else resolver

        # resolution 非 fixed 时额外 @当前负责人
        assignee_at_text = ''
        if has_non_fixed and non_fixed_assignees:
            assignee_names = []
            for assignee_name in non_fixed_assignees:
                assignee_dingtalk_id = dingtalk_map.get(assignee_name, '')
                if assignee_dingtalk_id and assignee_dingtalk_id not in at_mobiles:
                    at_mobiles.append(assignee_dingtalk_id)
                assignee_names.append(f"@{assignee_name}")
            assignee_at_text = ' '.join(assignee_names)

        text = (
            f"{at_text} 解决Bug提醒：以下已解决的bug在SVN中未找到关联的代码提交记录，请检查：\n\n"
            + "\n".join(bug_lines)
            + "\n\n请确认是否已提交相关代码，或在SVN提交注释中关联bug编号。"
        )
        if assignee_at_text:
            text += f"\n{assignee_at_text} 请关注以上非fixed解决方案的bug。"

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
                    at_info = f" (@{dingtalk_id})" if dingtalk_id else ""
                    print(f"  钉钉消息发送成功 → {resolver}{at_info} ({len(bugs)} 个bug)", flush=True)
                    sent_bugs.extend(bugs)
                else:
                    print(f"  钉钉消息发送失败 → {resolver}: {result.get('errmsg')}", flush=True)
                    #sent_bugs.extend(bugs)
        except Exception as e:
            print(f"  钉钉消息发送异常 → {resolver}: {e}", flush=True)

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

    all_svn_logs = []
    for repo_url in SVN_REPOS:
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

    if not rd_bugs:
        print("  没有需要通知的bug", flush=True)
    else:
        # 加载钉钉成员映射
        dingtalk_mem_path = os.path.join(output_dir, 'dingtalk-mem.xlsx')
        dingtalk_map = load_dingtalk_member_map(dingtalk_mem_path)
        if dingtalk_map:
            print(f"  已加载钉钉成员映射: {len(dingtalk_map)} 人", flush=True)

        print(f"  待发送通知: {len(rd_bugs)} 条", flush=True)
        for row in rd_bugs:
            print(f"    Bug#{row[COL_BUG_ID]} → {row[COL_RESOLVER]} - {row[COL_TITLE]}", flush=True)

        sent_bugs = send_dingtalk_message(rd_bugs, dingtalk_map)

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


def send_task_dingtalk_message(task_rows, dingtalk_map):
    """Send DingTalk reminders to task finishers."""
    if not task_rows:
        return []

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
            print(f"  [warn] missing dingtalk id for finisher: {finisher}", flush=True)
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

        payload = {
            "msgtype": "text",
            "text": {"content": text},
            "at": {
                "atMobiles": [dingtalk_id],
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
                    print(f"  task reminder sent -> {finisher} ({len(tasks)} tasks)", flush=True)
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

    dingtalk_mem_path = os.path.join(output_dir, 'dingtalk-mem.xlsx')
    dingtalk_map = load_dingtalk_member_map(dingtalk_mem_path)
    if dingtalk_map:
        print(f"loaded dingtalk members: {len(dingtalk_map)}", flush=True)

    sent_tasks = send_task_dingtalk_message(rows, dingtalk_map)
    if sent_tasks:
        append_to_sendmsgbug(columns, sent_tasks, sendmsgtask_path)
        print(f"saved sent task reminders: {sendmsgtask_path}", flush=True)


if __name__ == '__main__':
    MonitorBugs()
    MonitorTasks()
