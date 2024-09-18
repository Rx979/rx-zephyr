# Rx-Zephyr

## Description
Rx-Zephyr 是一个基于 FastAPI 的基础模板，它包含了配置管理器和数据源管理器。目前支持 MySQL、PostgreSQL、Redis 和 MongoDB。它旨在帮助开发者快速启动和运行新的 FastAPI 项目，无需从头开始搭建配置和数据源管理。

## Features
- 内置配置管理器，方便项目配置，支持Nacos。
- 数据源管理器支持多种数据库（MySQL、PostgreSQL、Redis、MongoDB）。
- 使用 Poetry 进行依赖管理，确保项目依赖的稳定性和一致性。
- 集成了代码格式化工具（isort、black），帮助维护代码风格。

## Setup the environment
### 安装依赖
确保您的系统已安装 Python 3.10 或更高版本。

```shell
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
. venv/bin/activate

# 更新 pip（可选）
pip install --upgrade pip

# 安装 Poetry
pip install poetry

# 安装项目依赖
poetry install