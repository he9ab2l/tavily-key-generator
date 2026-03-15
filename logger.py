"""
统一日志模块
格式: [HH:MM:SS] [LEVEL] 消息
同时输出到控制台和日志文件
"""
import os
import sys
import logging
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_logger = logging.getLogger("tavily")
_logger.setLevel(logging.DEBUG)
_logger.propagate = False

# 日志文件
_fh = logging.FileHandler(
    os.path.join(LOG_DIR, "tavily.log"), encoding="utf-8"
)
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
_logger.addHandler(_fh)

# 控制台（带可选颜色）
_COLORS = {
    "DEBUG": "\033[90m",
    "INFO": "\033[0m",
    "SUCCESS": "\033[32m",
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
}
_RESET = "\033[0m"

# 添加自定义 SUCCESS 级别
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


class _ConsoleFormatter(logging.Formatter):
    def __init__(self, use_color=True):
        super().__init__()
        self.use_color = use_color

    def format(self, record):
        ts = datetime.now().strftime("%H:%M:%S")
        level = record.levelname
        msg = record.getMessage()
        if self.use_color:
            color = _COLORS.get(level, "")
            return f"  [{ts}] [{level}] {color}{msg}{_RESET}"
        return f"  [{ts}] [{level}] {msg}"


def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.DEBUG)
_ch.setFormatter(_ConsoleFormatter(use_color=_supports_color()))
_logger.addHandler(_ch)


def debug(msg):
    _logger.debug(msg)


def info(msg):
    _logger.info(msg)


def success(msg):
    _logger.log(SUCCESS_LEVEL, msg)


def warn(msg):
    _logger.warning(msg)


def error(msg):
    _logger.error(msg)
