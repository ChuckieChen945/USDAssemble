"""utils."""

from pathlib import Path

# 模板目录路径
TEMPLATE_DIR = Path(__file__).parent.parent / "template"


def get_template_dir() -> Path:
    """获取模板目录路径."""
    return TEMPLATE_DIR


def ensure_directory(file_path: str | Path) -> None:
    """确保目录存在."""
    directory = Path(file_path).parent
    directory.mkdir(parents=True, exist_ok=True)
