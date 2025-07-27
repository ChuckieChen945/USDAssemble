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
            self._raise_error(f"路径不存在: {path}")

        if not path.is_dir():
            self._raise_error(f"路径不是目录: {path}")

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
            self._raise_error(f"文件不存在: {path}")

        try:
            with Path.open(path, encoding=encoding) as f:
                return f.read()
        except Exception as e:
            self._raise_error(f"读取文件失败 {path}: {e}")

    def write_file(self, path: Path, content: str, encoding: str = "utf-8") -> None:
        """写入文件内容.

        Args:
            path: 文件路径
            content: 要写入的内容
            encoding: 文件编码

        Raises
        ------
            FileServiceError: 当写入失败时
        """
        try:
            # 确保目录存在
            self.ensure_directory_exists(path)

            with Path.open(path, "w", encoding=encoding) as f:
                f.write(content)
        except Exception as e:
            self._raise_error(f"写入文件失败 {path}: {e}")

    def copy_file(self, source: Path, destination: Path) -> None:
        """复制文件.

        Args:
            source: 源文件路径
            destination: 目标文件路径

        Raises
        ------
            FileServiceError: 当复制失败时
        """
        if not source.exists():
            self._raise_error(f"源文件不存在: {source}")

        try:
            # 确保目标目录存在
            self.ensure_directory_exists(destination)

            # 复制文件
            import shutil

            shutil.copy2(source, destination)
        except Exception as e:
            self._raise_error(f"复制文件失败 {source} -> {destination}: {e}")

    def copy_directory(self, source: Path, destination: Path) -> None:
        """复制目录.

        Args:
            source: 源目录路径
            destination: 目标目录路径

        Raises
        ------
            FileServiceError: 当复制失败时
        """
        if not source.exists():
            self._raise_error(f"源目录不存在: {source}")

        if not source.is_dir():
            self._raise_error(f"源路径不是目录: {source}")

        try:
            # 确保目标目录存在
            self.ensure_directory_exists(destination)

            # 复制目录
            import shutil

            shutil.copytree(source, destination, dirs_exist_ok=True)
        except Exception as e:
            self._raise_error(f"复制目录失败 {source} -> {destination}: {e}")

    def _raise_error(self, message: str) -> None:
        """统一的错误抛出函数.

        Args:
            message: 错误消息

        Raises
        ------
            FileServiceError: 统一的文件服务错误
        """
        raise FileServiceError(message)
