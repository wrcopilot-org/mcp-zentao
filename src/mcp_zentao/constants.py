"""
常量定义文件
集中管理禅道 MCP 服务器的常量配置，避免硬编码分散
"""

from typing import Dict, Any

# ===============================
# 排序键映射配置
# ===============================

# 缺陷排序映射
BUG_SORT_KEY_MAPPING: Dict[str, str] = {
    "latest": "id_desc",
    "oldest": "id_asc",
    "priority": "pri_asc"
}

# 任务排序映射  
TASK_SORT_KEY_MAPPING: Dict[str, str] = {
    "latest": "id_desc",
    "oldest": "id_asc",
    "deadline": "deadline_asc"
}

# 项目排序映射
PROJECT_SORT_KEY_MAPPING: Dict[str, str] = {
    "latest": "id_desc",
    "oldest": "id_asc",
    "priority": "pri_desc"
}

# ===============================
# 分页配置
# ===============================

# 默认分页配置
DEFAULT_PAGE_SIZE = 20
MAX_SINGLE_PAGE_SIZE = 2000
MAX_PAGES_LIMIT = 100

# ===============================
# 显示配置
# ===============================

# 历史记录显示限制
MAX_HISTORY_RECORDS = 10

# 文件下载链接模板
FILE_DOWNLOAD_URL_TEMPLATE = "{base_url}file-download-{file_id}.html?zentaosid={session_id}"

# ===============================
# 默认值配置
# ===============================

# 默认工作时间（小时）
DEFAULT_WORK_HOURS = 8.0

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 30.0

# ===============================
# 状态文本分隔符
# ===============================

SECTION_SEPARATOR = "=" * 60
SUBSECTION_SEPARATOR = "-" * 40
ITEM_SEPARATOR = "─" * 50
