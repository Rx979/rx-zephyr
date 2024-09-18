from pathlib import Path
from typing import Type, TypeVar

import yaml

T = TypeVar("T", bound=object)


def yaml_to_dict(file_path: str, encoding: str = "utf8") -> dict:
    """yaml转dict

    Args:
        file_path (str): yaml文件路径
        encoding (str, optional): 文件编码. Defaults to 'utf8'.

    Raises:
        FileNotFoundError: 文件不存在

    Returns:
        dict: 字典
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError("请确认yaml文件路径是否正确")

    yaml_content = file_path.read_text(encoding=encoding)
    yaml_dict = yaml.load(yaml_content, Loader=yaml.FullLoader)
    return yaml_dict


def yaml_to_class(file_path: str, class_type: Type[T], encoding: str = "utf8") -> T:
    """yaml转class
    Args:
        file_path (str): yaml文件路径
        class_type (Type[T]): 需要转的类
        encoding (str, optional): 文件编码. Defaults to "utf8".

    Returns:
        T: 类
    """
    yaml_dict = yaml_to_dict(file_path, encoding)

    return class_type(**yaml_dict)
