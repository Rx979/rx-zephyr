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

DEFAULT_BANNER = r"""
    .______      ___   ___ ___   ___ ___   ___
    |   _  \     \  \ /  / \  \ /  / \  \ /  /
    |  |_)  |     \  V  /   \  V  /   \  V  / 
    |      /       >   <     >   <     >   <  
    |  |\  \----. /  .  \   /  .  \   /  .  \ 
    | _| `._____|/__/ \__\ /__/ \__\ /__/ \__\
"""

SYSTEM_ENCODING = "utf-8"

DEFAULT_LOGGER_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "()": "zephyr.logging.ZephyrFormatter",
            "fmt": "%(asctime)s %(levelprefix)s [%(threadName)s] - %(name)s [%(lineno)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "()": "zephyr.logging.ZephyrFormatter",
            "fmt": "%(asctime)s - %(levelname)s - [%(threadName)s] - %(name)s [%(lineno)d] - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
        },
        "info": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "encoding": "utf8",
        },
        "error": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/error.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
    "root": {"level": "INFO", "handlers": ["console", "info", "error"]},
}
