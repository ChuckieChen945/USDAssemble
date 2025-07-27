"""模板处理服务."""

from pathlib import Path
from string import Template

from rich.console import Console

from domain.enums import ComponentType
from domain.exceptions import TemplateServiceError
from services.file_service import FileService
from utils.path_utils import get_template_dir

console = Console()


class TemplateService:
    """模板处理服务.

    负责所有的模板文件处理，包括模板读取、变量替换、文件生成等。
    """

    def __init__(self) -> None:
        """初始化模板服务."""
        self.file_service = FileService()

    def get_template_path(
        self,
        component_type: ComponentType,
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

    def get_assembly_template_path(self, template_filename: str) -> Path:
        """获取assembly模板文件路径.

        Args:
            template_filename: 模板文件名

        Returns
        -------
            Path: 模板文件路径
        """
        return get_template_dir() / "{$assembly_or_component_name}" / template_filename

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
            self._raise_error(f"模板文件不存在: {template_path}")

        try:
            # 确保输出目录存在
            self.file_service.ensure_directory_exists(output_path)

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
                self._raise_error(f"模板处理失败: {e}")
            raise

    def _raise_error(self, message: str) -> None:
        """统一的错误抛出函数.

        Args:
            message: 错误消息

        Raises
        ------
            TemplateServiceError: 统一的模板服务错误
        """
        raise TemplateServiceError(message)

    def create_component_payload(
        self,
        output_path: str,
        component_name: str,
        component_type: ComponentType,
    ) -> None:
        """从模板创建payload文件."""
        substitutions = {"component_or_subcomponent_name": component_name}

        self.create_from_template(
            component_type,
            "{$component_or_subcomponent_name}_payload.usd",
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
        substitutions = {"component_or_subcomponent_name": component_name}

        self.create_from_template(
            component_type,
            "{$component_or_subcomponent_name}_look.usd",
            Path(output_path),
            substitutions,
        )

    def create_assembly_main_template(
        self,
        assembly_name: str,
    ) -> str:
        """创建assembly主文件模板内容.

        Args:
            assembly_name: assembly名称

        Returns
        -------
            str: 模板内容

        Raises
        ------
            TemplateServiceError: 当模板文件不存在时
        """
        template_path = self.get_assembly_template_path("{$assembly_or_component_name}.usda")

        if not template_path.exists():
            self._raise_error(f"Assembly模板文件不存在: {template_path}")

        # 读取模板内容
        template_content = self.file_service.read_file(template_path)

        # 进行替换
        template = Template(template_content)
        return template.safe_substitute(assembly_or_component_name=assembly_name)

    def create_component_main_template(
        self,
        component_name: str,
        component_type: ComponentType,
    ) -> str:
        """创建组件主文件模板内容.

        Args:
            component_name: 组件名称
            component_type: 组件类型

        Returns
        -------
            str: 模板内容

        Raises
        ------
            TemplateServiceError: 当模板文件不存在时
        """
        template_path = self.get_template_path(
            component_type,
            "{$component_or_subcomponent_name}.usd",
        )

        if not template_path.exists():
            self._raise_error(f"组件模板文件不存在: {template_path}")

        # 读取模板内容
        template_content = self.file_service.read_file(template_path)

        # 进行替换
        template = Template(template_content)
        return template.safe_substitute(component_or_subcomponent_name=component_name)
