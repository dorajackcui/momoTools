import os

ERROR_TITLE = "错误"
WARNING_TITLE = "警告"
SUCCESS_TITLE = "完成"
CONFIRM_TITLE = "确认操作"

DEFAULT_FILE_TEXT = "未选择文件"
DEFAULT_FOLDER_TEXT = "未选择文件夹"
DEFAULT_OUTPUT_TEXT = "未选择输出文件"

SELECTED_PREFIX = "已选择："
OUTPUT_PREFIX = "输出: "

REQUIRE_MASTER_TARGET = "请先选择 Master 文件和目标文件夹！"
REQUIRE_TARGET_FOLDER = "请先选择目标文件夹！"
REQUIRE_SOURCE_TARGET = "请先选择源文件夹和目标文件夹！"
REQUIRE_STATS_FOLDER = "请先选择小表文件夹！"
REQUIRE_OUTPUT_FILE = "请先选择输出文件！"

VALIDATION_CONFIG_PREFIX = "列配置错误："
VALIDATION_MATCH_PREFIX = "匹配列设置错误："
VALIDATION_COLUMN_PREFIX = "列号设置错误："


def selected_path_text(path):
    return f"{SELECTED_PREFIX}{os.path.basename(path)}"


def output_path_text(path):
    return f"{OUTPUT_PREFIX}{os.path.basename(path)}"

