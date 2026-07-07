from __future__ import annotations

import argparse
import configparser
import csv
import os
import sys
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor


def get_app_dir() -> Path:
	if getattr(sys, "frozen", False):
		return Path(sys.executable).resolve().parent
	return Path(__file__).resolve().parent


DEFAULT_DB_CONFIG = {
	"host": os.getenv("EPM_DB_HOST", "192.168.0.26"),
	"port": int(os.getenv("EPM_DB_PORT", "3306")),
	"user": os.getenv("EPM_DB_USER", "nav_wjp_26"),
	"password": os.getenv("EPM_DB_PASSWORD", "Ne9zSuvuqQ"),
	"database": os.getenv("EPM_DB_NAME", "epm"),
}

TABLE_NAME = "yiwo_operation"
DEFAULT_START_DATE = "2026-06-04"
DEFAULT_END_DATE = "2026-06-10"
DEFAULT_ACTIVITY = ""
DEFAULT_VID_PATTERN = "epm2030_%117"
DEFAULT_VID_PATTERNS = [DEFAULT_VID_PATTERN]
DEFAULT_OUTPUT_FILE = get_app_dir() / "yiwo_operation_20260604_20260610_epm2030_117.csv"
DEFAULT_OUTPUT_DIR = DEFAULT_OUTPUT_FILE.parent
DEFAULT_CONFIG_FILE = get_app_dir() / "get_log_data.ini"


def normalize_vid_patterns(values: list[str] | tuple[str, ...] | None) -> list[str]:
	patterns: list[str] = []
	for value in values or []:
		value = str(value).strip()
		if value and value not in patterns:
			patterns.append(value)
	return patterns or DEFAULT_VID_PATTERNS.copy()


def build_db_config(args: argparse.Namespace) -> dict:
	return {
		"host": args.host,
		"port": args.port,
		"user": args.user,
		"password": args.password,
		"database": args.database,
		"charset": "utf8mb4",
		"cursorclass": DictCursor,
	}


def load_ini_defaults(config_path: Path) -> dict:
	defaults = {
		"host": DEFAULT_DB_CONFIG["host"],
		"port": DEFAULT_DB_CONFIG["port"],
		"user": DEFAULT_DB_CONFIG["user"],
		"password": DEFAULT_DB_CONFIG["password"],
		"database": DEFAULT_DB_CONFIG["database"],
		"start_date": DEFAULT_START_DATE,
		"end_date": DEFAULT_END_DATE,
		"activity": DEFAULT_ACTIVITY,
		"vid_patterns": DEFAULT_VID_PATTERNS.copy(),
		"output_dir": str(DEFAULT_OUTPUT_DIR),
		"output": str(DEFAULT_OUTPUT_FILE),
	}

	if not config_path.exists():
		return defaults

	config = configparser.RawConfigParser()
	config.read(config_path, encoding="utf-8")

	if config.has_section("database"):
		defaults["host"] = config.get("database", "host", fallback=defaults["host"])
		defaults["port"] = config.getint("database", "port", fallback=defaults["port"])
		defaults["user"] = config.get("database", "user", fallback=defaults["user"])
		defaults["password"] = config.get("database", "password", fallback=defaults["password"])
		defaults["database"] = config.get("database", "database", fallback=defaults["database"])

	if config.has_section("export"):
		defaults["start_date"] = config.get("export", "start_date", fallback=defaults["start_date"])
		defaults["end_date"] = config.get("export", "end_date", fallback=defaults["end_date"])
		defaults["activity"] = config.get("export", "activity", fallback=defaults["activity"])
		vid_pattern_keys = sorted(
			(key for key, _ in config.items("export") if key.startswith("vid_pattern")),
			key=lambda key: (key != "vid_pattern", key),
		)
		defaults["vid_patterns"] = normalize_vid_patterns(
			[config.get("export", key) for key in vid_pattern_keys]
		)
		defaults["output_dir"] = config.get("export", "output_dir", fallback=defaults["output_dir"])
		defaults["output"] = config.get("export", "output", fallback=defaults["output"])

	return defaults


def write_ini(args: argparse.Namespace, config_path: Path) -> None:
	config = configparser.RawConfigParser()
	config["database"] = {
		"host": args.host,
		"port": str(args.port),
		"user": args.user,
		"password": args.password,
		"database": args.database,
	}
	export_config = {
		"start_date": args.start_date,
		"end_date": args.end_date,
		"activity": args.activity,
		"output_dir": args.output_dir,
		"output": args.output,
	}
	for index, vid_pattern in enumerate(normalize_vid_patterns(args.vid_patterns), start=1):
		key = "vid_pattern" if index == 1 else f"vid_pattern{index}"
		export_config[key] = vid_pattern
	config["export"] = export_config

	config_path.parent.mkdir(parents=True, exist_ok=True)
	with config_path.open("w", encoding="utf-8") as f:
		config.write(f)


def build_query(vid_pattern_count: int = 1, has_activity: bool = False) -> str:
	vid_conditions = " OR ".join(["`vid` LIKE %s"] * max(vid_pattern_count, 1))
	activity_condition = "\n\t  AND `activity` = %s" if has_activity else ""
	return f"""
	SELECT *
	FROM `{TABLE_NAME}`
	WHERE `timestamp` > UNIX_TIMESTAMP(%s)
	  AND `timestamp` < UNIX_TIMESTAMP(%s)
	  AND ({vid_conditions})
	  {activity_condition}
	"""


def quote_sql_string(value: str) -> str:
	return "'" + value.replace("'", "''") + "'"


def printable_sql(sql: str, params: tuple[str, ...]) -> str:
	result = sql
	for param in params:
		result = result.replace("%s", quote_sql_string(param), 1)
	return result.strip()


def resolve_output_path(output_dir: str, output: str) -> Path:
	output_path = Path(output)
	if output_path.is_absolute():
		return output_path
	return Path(output_dir) / output_path


def fetch_rows(
	db_config: dict,
	start_date: str,
	end_date: str,
	vid_patterns: list[str],
	activity: str = "",
) -> tuple[list[str], list[dict]]:
	vid_patterns = normalize_vid_patterns(vid_patterns)
	activity = activity.strip()
	sql = build_query(len(vid_patterns), bool(activity))
	params = (start_date, end_date, *vid_patterns, *([activity] if activity else []))

	conn = pymysql.connect(**db_config)
	try:
		with conn.cursor() as cur:
			cur.execute(sql, params)
			headers = [field[0] for field in cur.description]
			rows = cur.fetchall()
			return headers, rows
	finally:
		conn.close()


def write_csv(headers: list[str], rows: list[dict], output_path: Path) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", encoding="utf-8-sig", newline="") as f:
		writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
		writer.writeheader()
		writer.writerows(rows)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
	config_parser = argparse.ArgumentParser(add_help=False)
	config_parser.add_argument("config_file", nargs="?", help="输入 INI 参数文件路径")
	config_parser.add_argument("--config", default=str(DEFAULT_CONFIG_FILE), help="输入 INI 参数文件路径")
	config_parser.add_argument("--init-config", action="store_true", help="按当前参数生成输入 INI 后退出")
	config_args, _ = config_parser.parse_known_args(argv)
	if config_args.config_file:
		config_args.config = config_args.config_file

	defaults = load_ini_defaults(Path(config_args.config))

	parser = argparse.ArgumentParser(description="导出 yiwo_operation 表记录到 CSV", parents=[config_parser])
	parser.add_argument("--host", default=defaults["host"], help="MySQL 主机地址")
	parser.add_argument("--port", type=int, default=defaults["port"], help="MySQL 端口")
	parser.add_argument("--user", default=defaults["user"], help="MySQL 账号")
	parser.add_argument("--password", default=defaults["password"], help="MySQL 密码")
	parser.add_argument("--database", default=defaults["database"], help="MySQL 数据库名")
	parser.add_argument("--start-date", default=defaults["start_date"], help="开始日期，不包含边界日期本身")
	parser.add_argument("--end-date", default=defaults["end_date"], help="结束日期，不包含边界日期本身")
	parser.add_argument("--activity", default=defaults["activity"], help="activity 精确匹配值，留空则不限制")
	parser.add_argument("--vid-pattern", action="append", dest="vid_patterns", help="vid LIKE 匹配表达式，可重复传入")
	parser.add_argument("--output-dir", default=defaults["output_dir"], help="CSV 输出目录")
	parser.add_argument("--output", default=defaults["output"], help="输出 CSV 文件路径")
	args, unknown_args = parser.parse_known_args(argv, namespace=config_args)
	if args.vid_patterns is None:
		args.vid_patterns = defaults["vid_patterns"]
	args.vid_patterns = normalize_vid_patterns(args.vid_patterns)
	if unknown_args:
		print(f"Ignored unknown args: {' '.join(unknown_args)}", file=sys.stderr)
	return args


def main() -> None:
	args = parse_args()
	config_path = Path(args.config)
	if args.init_config:
		write_ini(args, config_path)
		print(f"Config: {config_path}")
		return

	output_path = resolve_output_path(args.output_dir, args.output)
	db_config = build_db_config(args)
	vid_patterns = normalize_vid_patterns(args.vid_patterns)
	activity = args.activity.strip()
	sql = build_query(len(vid_patterns), bool(activity))
	params = (args.start_date, args.end_date, *vid_patterns, *([activity] if activity else []))

	print("SQL:")
	print(printable_sql(sql, params))

	headers, rows = fetch_rows(db_config, args.start_date, args.end_date, vid_patterns, activity)
	write_csv(headers, rows, output_path)

	print(f"Rows: {len(rows)}")
	print(f"Output: {output_path}")


if __name__ == "__main__":
	main()