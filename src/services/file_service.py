"""文件操作服务."""

from pathlib import Path

from domain.exceptions import FileServiceError


class FileService:
    """文件操作服务.

    负责所有的文件和目录操作，包括创建、读取、写入等。
    """

    def ensure_directory_exists(self, path: Path) -> None:
        """确保目录存在.

        Args:
            path: 目录路径
        """
        # 如果路径存在且是文件，或者路径有文件扩展名（暗示这是一个文件路径）
        if (path.exists() and path.is_file()) or (not path.exists() and path.suffix):
            path = path.parent
        path.mkdir(parents=True, exist_ok=True)

    def list_directories(self, path: Path) -> list[Path]:
        """列出指定路径下的所有目录.

        Args:
            path: 要扫描的路径

        Returns
        -------
            List[Path]: 目录列表

        Raises
        ------
            FileServiceError: 当路径不存在时
        """
        if not path.exists():
            msg = f"路径不存在: {path}"
            raise FileServiceError(msg)

        if not path.is_dir():
            msg = f"路径不是目录: {path}"
            raise FileServiceError(msg)

        return [item for item in path.iterdir() if item.is_dir()]

    def read_file(self, path: Path, encoding: str = "utf-8") -> str:
        """读取文件内容.

        Args:
            path: 文件路径
            encoding: 文件编码

        Returns
        -------
            str: 文件内容

        Raises
        ------
            FileServiceError: 当文件不存在或读取失败时
        """
        if not path.exists():
            msg = f"文件不存在: {path}"
            raise FileServiceError(msg)

        try:
            with Path.open(path, encoding=encoding) as f:
                return f.read()
        except Exception as e:
            msg = f"读取文件失败 {path}: {e}"
            raise FileServiceError(msg) from e

    def write_file(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """写入文件内容.

        Args:
            path: 文件路径
            content: 文件内容
            encoding: 文件编码

        Raises
        ------
            FileServiceError: 当写入失败时
        """
        try:
            # 确保父目录存在
            self.ensure_directory_exists(path.parent)

            with Path.open(path, "w", encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            msg = f"写入文件失败 {path}: {e}"
            raise FileServiceError(msg) from e

    def file_exists(self, path: Path) -> bool:
        """检查文件是否存在.

        Args:
            path: 文件路径

        Returns
        -------
            bool: 文件是否存在
        """
        return path.exists() and path.is_file()

    def directory_exists(self, path: Path) -> bool:
        """检查目录是否存在.

        Args:
            path: 目录路径

        Returns
        -------
            bool: 目录是否存在
        """
        return path.exists() and path.is_dir()
