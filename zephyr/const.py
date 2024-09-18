from pathlib import Path

# 项目路径
BASE_PATH = Path.cwd()

# 配置文件文件夹名称
CONFIG_DIR = "config"

# 配置文件文件夹路径
CONFIG_DIR_PATH = BASE_PATH / CONFIG_DIR

# 基础配置文件的名称
BASE_CONFIGS = ["app.yml", "app.yaml"]

# 额外的配置文件名称
EXTRA_CONFIGS = ["app-{active}.yml", "app-{active}.yaml"]

# 日志配置文件名称
LOGGER_CONFIGS = ["logging.yml", "logging.yaml"]

BANNER_FILES = ["banner.txt", "banner"]

# 系统编码
SYSTEM_ENCODING = "utf-8"

DEFAULT_LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "detailed",
            "filename": "app.log",
            "mode": "a",
        },
    },
    "root": {"level": "DEBUG", "handlers": ["console", "file"]},
}
