"""日志管理模块."""

import logging
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

console = Console()


class USDLogger:
    """USD Logger.

    统一的日志管理类，支持控制台和文件输出。
    """

    def __init__(
        self,
        name: str = "USDAssemble",
        level: int = logging.INFO,
        log_file: Path | None = None,
    ) -> None:
        """初始化日志器.

        Args:
            name: 日志器名称
            level: 日志级别
            log_file: 日志文件路径（可选）
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # 清除现有的处理器
        self.logger.handlers.clear()

        # 创建Rich处理器用于控制台输出
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        rich_handler.setLevel(level)
        self.logger.addHandler(rich_handler)

        # 如果指定了日志文件，添加文件处理器
        if log_file:
            self._add_file_handler(log_file, level)

    def _add_file_handler(self, log_file: Path, level: int) -> None:
        """添加文件处理器."""
        try:
            # 确保日志目录存在
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # 创建文件处理器
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)

            # 设置文件格式
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)

        except Exception as e:
            console.print(f"[yellow]警告: 无法创建日志文件 {log_file}: {e}[/yellow]")

    def debug(self, message: str) -> None:
        """输出调试信息."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """输出信息."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """输出警告."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """输出错误."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """输出严重错误."""
        self.logger.critical(message)

    def success(self, message: str) -> None:
        """输出成功信息."""
        console.print(f"[green]✓ {message}[/green]")

    def progress(self, message: str) -> None:
        """输出进度信息."""
        console.print(f"[blue]→ {message}[/blue]")

    def section(self, title: str) -> None:
        """输出章节标题."""
        console.print(f"\n[bold cyan]{title}[/bold cyan]")
        console.print("[cyan]" + "=" * len(title) + "[/cyan]")

    def subsection(self, title: str) -> None:
        """输出子章节标题."""
        console.print(f"\n[bold blue]{title}[/bold blue]")
        console.print("[blue]" + "-" * len(title) + "[/blue]")

    def table(self, title: str, data: list, headers: list) -> None:
        """输出表格."""
        from rich.table import Table

        table = Table(title=title)
        for header in headers:
            table.add_column(header, style="cyan")

        for row in data:
            table.add_row(*[str(cell) for cell in row])

        console.print(table)

    def code_block(self, code: str, language: str = "python") -> None:
        """输出代码块."""
        from rich.syntax import Syntax

        syntax = Syntax(code, language, theme="monokai")
        console.print(syntax)

    def exception(self, message: str, exc_info: bool = True) -> None:
        """输出异常信息."""
        self.logger.exception(message, exc_info=exc_info)


class ProgressLogger:
    """进度日志器.

    专门用于显示处理进度的日志器。
    """

    def __init__(self, total: int, description: str = "处理中") -> None:
        """初始化进度日志器.

        Args:
            total: 总数量
            description: 描述信息
        """
        from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        )
        self.task = self.progress.add_task(description, total=total)

    def __enter__(self) -> "ProgressLogger":
        """进入上下文管理器."""
        self.progress.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文管理器."""
        self.progress.stop()

    def advance(self, amount: int = 1) -> None:
        """推进进度."""
        self.progress.advance(self.task, amount)

    def update_description(self, description: str) -> None:
        """更新描述信息."""
        self.progress.update(self.task, description=description)

    def complete(self) -> None:
        """完成进度."""
        self.progress.update(self.task, completed=self.progress.tasks[self.task].total)


# 全局日志实例
logger = USDLogger()


# 创建默认的进度日志器
def create_progress(total: int, description: str = "处理中") -> ProgressLogger:
    """创建进度日志器."""
    return ProgressLogger(total, description)
