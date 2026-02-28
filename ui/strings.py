import os

ERROR_TITLE = "Error"
WARNING_TITLE = "Warning"
SUCCESS_TITLE = "Done"
CONFIRM_TITLE = "Confirm"

DEFAULT_FILE_TEXT = "No file selected"
DEFAULT_FOLDER_TEXT = "No folder selected"
DEFAULT_OUTPUT_TEXT = "No output selected"

SELECTED_PREFIX = "Selected: "
OUTPUT_PREFIX = "Output: "

REQUIRE_MASTER_TARGET = "Please select master file and target folder first."
REQUIRE_TARGET_FOLDER = "Please select target folder first."
REQUIRE_SOURCE_TARGET = "Please select source and target folders first."
REQUIRE_STATS_FOLDER = "Please select stats source folder first."
REQUIRE_OUTPUT_FILE = "Please select output file first."
REQUIRE_TERMINOLOGY_INPUT = "Please select input folder, rule config, and output file."
TASK_ALREADY_RUNNING = "A task is already running. Please wait."
VIEW_LOGS_BUTTON = "View Logs"
LOG_WINDOW_TITLE = "Execution Logs"

VALIDATION_CONFIG_PREFIX = "列配置错误："
VALIDATION_MATCH_PREFIX = "匹配列设置错误："
VALIDATION_COLUMN_PREFIX = "列号设置错误："


def selected_path_text(path):
    return f"{SELECTED_PREFIX}{os.path.basename(path)}"


def output_path_text(path):
    return f"{OUTPUT_PREFIX}{os.path.basename(path)}"
