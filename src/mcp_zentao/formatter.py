"""
内容格式化工具

将禅道返回的 HTML 内容转换为 Markdown 格式，
支持图片、附件等资源的 URL 拼接。
"""

import re
from typing import Any


def convert_html_to_markdown(html: str | None, base_url: str) -> str:
    """将 HTML 内容转换为 Markdown 格式

    Args:
        html: 包含 HTML 标签的文本内容
        base_url: 禅道服务器基础 URL，用于拼接相对路径

    Returns:
        转换后的 Markdown 文本
    """
    if not html:
        return ""

    base = base_url.rstrip("/")
    result = html

    # 1. 处理图片标签 -> Markdown 图片
    def replace_img(match: re.Match[str]) -> str:
        # 提取 src 和 alt 属性
        tag = match.group(0)
        src_match = re.search(r'src=["\']([^"\']+)["\']', tag)
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', tag)

        if not src_match:
            return ""

        src = src_match.group(1)
        alt = alt_match.group(1) if alt_match else "image"

        # 相对路径转绝对路径
        if src.startswith("/"):
            src = f"{base}{src}"

        return f"![{alt}]({src})"

    result = re.sub(r"<img[^>]*>", replace_img, result, flags=re.IGNORECASE)

    # 2. 处理段落标签
    result = re.sub(r"<p[^>]*>", "\n", result)
    result = result.replace("</p>", "\n")

    # 3. 处理换行标签
    result = result.replace("<br />", "\n").replace("<br>", "\n")

    # 4. 处理 span 标签（移除）
    result = re.sub(r"<span[^>]*>", "", result)
    result = result.replace("</span>", "")

    # 5. 移除其他 HTML 标签
    result = re.sub(r"<[^>]+>", "", result)

    # 6. 处理 HTML 实体
    result = (
        result.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&nbsp;", " ")
        .replace("&quot;", '"')
    )

    # 7. 清理多余空行
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = result.replace("\r\n", "\n").replace("\r", "\n")

    return result.strip()


def format_files(
    files: dict[str, dict[str, Any]] | None, base_url: str
):
    """将附件信息格式化为 Markdown 链接列表

    Args:
        files: 禅道返回的附件字典，key 为文件 ID
        base_url: 禅道服务器基础 URL

    Returns:
        格式化后的附件列表
    """
    raise NotImplementedError
