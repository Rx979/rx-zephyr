import json
import logging
import logging.config
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from nacos import NacosClient

from zephyr.config.models import AppConfig, NacosConfig
from zephyr.const import (
    BASE_CONFIGS,
    CONFIG_DIR_PATH,
    DEFAULT_LOGGER_CONFIG,
    EXTRA_CONFIGS,
    LOGGER_CONFIGS,
)
from zephyr.meta import SingletonMeta
from zephyr.utils.yaml_utils import yaml_to_dict


class ConfigManager(metaclass=SingletonMeta):
    # 日志logger
    logger: Optional[logging.Logger] = None

    def __init__(self):
        self.logger = self._initialize_logger()
        self._app_config: Optional[AppConfig] = None
        self.load_config()

    @property
    def app_config(self):
        """Getter for app_config"""
        return self._app_config

    @app_config.setter
    def app_config(self, value: AppConfig):
        """Setter for app_config"""
        if not self._app_config:
            self._app_config = value
        return

    def load_config(self) -> None:
        """
        加载配置文件，支持从 Nacos 或本地配置加载
        """

        # 加载基础配置
        app_base_config_dict = self._load_config_files(BASE_CONFIGS)
        app_base_config = (
            AppConfig(**app_base_config_dict) if app_base_config_dict else AppConfig()
        )

        # 加载用户配置（优先从 Nacos 读取，否则根据环境变量加载）
        if app_base_config.nacos and app_base_config.nacos.enabled:
            self.logger.info(
                f"[加载 Nacos 配置], host: {app_base_config.nacos.host}; namespace: {app_base_config.nacos.namespace}; group: {app_base_config.nacos.group}; data-id: {app_base_config.nacos.data_id}"
            )
            user_config = self._load_nacos_config(nacos_config=app_base_config.nacos)
        else:
            active = os.getenv("active") or app_base_config.active
            if active:
                self.logger.info(f"加载 [{active}] 配置文件")
                extra_config_files = [
                    extra_config_file.format(active=active)
                    for extra_config_file in EXTRA_CONFIGS
                ]
                user_config = self._load_config_files(extra_config_files)
            else:
                user_config = {}

        # 合并基础配置和用户配置
        app_config_dict = app_base_config.model_dump()
        app_config_dict.update(user_config)
        self._app_config = AppConfig(**app_config_dict)

    def _initialize_logger(self):
        """初始化日志配置"""
        logger_config = self._load_config_files(LOGGER_CONFIGS)
        if not logger_config:
            logger_config = DEFAULT_LOGGER_CONFIG

        for handler in logger_config.get("handlers", {}).values():
            filename = handler.get("filename")
            if filename:
                log_path = Path(filename)
                log_path.parent.mkdir(parents=True, exist_ok=True)

        logging.config.dictConfig(logger_config)
        return logging.getLogger(__name__)

    def _load_nacos_config(self, nacos_config: NacosConfig) -> Dict[str, Any]:
        """
        从 Nacos 获取用户配置

        Args:
            nacos_config (NacosConfig): Nacos 配置项

        Returns:
            dict: Nacos 获取到的配置字典
        """
        try:
            # 初始化 Nacos Client
            nacos_client = NacosClient(
                server_addresses=nacos_config.host,
                namespace=nacos_config.namespace,
                username=nacos_config.username,
                password=nacos_config.password,
            )
            # 获取 Nacos 配置
            nacos_user_config = nacos_client.get_config(
                data_id=nacos_config.data_id, group=nacos_config.group, no_snapshot=True
            )
            return json.loads(nacos_user_config) if nacos_user_config else {}
        except Exception as e:
            # 记录错误日志
            self.logger.error(f"加载 Nacos 配置失败: {str(e)}")
            return {}

    @staticmethod
    def _load_config_files(config_files: Union[List[str], str]) -> Dict[str, Any]:
        """
        从配置文件列表中加载配置

        Args:
            config_files (list): 配置文件列表

        Returns:
            dict: 配置字典
        """
        if isinstance(config_files, str):
            config_files = [config_files]

        for config_file in config_files:
            config_file_path = CONFIG_DIR_PATH / config_file
            if config_file_path.exists():
                return yaml_to_dict(str(config_file_path))
        return {}
