"""模板处理服务."""

from pathlib import Path
from string import Template

from rich.console import Console

from services.file_service import FileService
from utils.utils import ComponentType, ensure_directory, get_template_dir

console = Console()


class TemplateServiceError(Exception):
    """模板服务错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TemplateService:
    """模板处理服务.

    负责所有的模板文件处理，包括模板读取、变量替换、文件生成等。
    """

    def __init__(self) -> None:
        """初始化模板服务."""
        self.file_service = FileService()

    def get_template_path(
        self,
        template_filename: str,
    ) -> Path:
        """获取模板文件路径.

        Args:
            component_type: 组件类型
            template_filename: 模板文件名

        Returns
        -------
            Path: 模板文件路径
        """
        return (
            get_template_dir()
            / "{$assembly_or_component_name}"
            / "components_or_subcomponents"
            / "{$component_or_subcomponent_name}"
            / template_filename
        )

    def create_from_template(
        self,
        component_type: ComponentType,
        template_filename: str,
        output_path: Path,
        substitutions: dict[str, str],
    ) -> None:
        """从模板文件创建新文件，使用string.Template进行替换.

        Args:
            component_type: 组件类型
            template_filename: 模板文件名
            output_path: 输出文件路径
            substitutions: 替换字典

        Raises
        ------
            TemplateServiceError: 当模板文件不存在或处理失败时
        """
        template_path = self.get_template_path(component_type, template_filename)

        if not template_path.exists():
            msg = f"模板文件不存在: {template_path}"
            raise TemplateServiceError(msg)

        try:
            # 确保输出目录存在
            ensure_directory(output_path)

            # 读取模板内容
            template_content = self.file_service.read_file(template_path)

            # 进行替换
            template = Template(template_content)
            content = template.safe_substitute(**substitutions)

            # 写入输出文件
            self.file_service.write_file(output_path, content)

            console.print(f"[green]✓ 生成文件: {output_path.name}[/green]")

        except Exception as e:
            if not isinstance(e, TemplateServiceError):
                msg = f"模板处理失败: {e}"
                raise TemplateServiceError(msg) from e
            raise

    def create_component_payload(
        self,
        output_path: str,
        component_name: str,
        component_type: ComponentType,
    ) -> None:
        """从模板创建payload文件."""
        substitutions = {"component_name": component_name}

        self.create_from_template(
            component_type,
            "{$component_name}_payload.usd",
            Path(output_path),
            substitutions,
        )

    def create_component_look(
        self,
        output_path: str,
        component_name: str,
        component_type: ComponentType,
    ) -> None:
        """从模板创建外观文件."""
        substitutions = {"component_name": component_name}

        self.create_from_template(
            component_type,
            "{$component_name}_look.usd",
            Path(output_path),
            substitutions,
        )
