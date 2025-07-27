"""USD组件处理器."""

from pathlib import Path

from rich.console import Console

from core.variant import VariantProcessor
from materialx.processor import MaterialXProcessor
from services.file_service import FileService
from services.template_service import TemplateService
from services.usd_service import UsdService
from utils.utils import ComponentInfo

console = Console()


class ComponentError(Exception):
    """组件处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ComponentProcessor:
    """USD组件处理器.

    负责处理单个组件的所有文件生成，包括MaterialX、USD文件等。
    """

    def __init__(
        self,
        file_service: FileService,
        template_service: TemplateService,
        usd_service: UsdService,
    ) -> None:
        """初始化组件处理器.

        Args:
            file_service: 文件服务
            template_service: 模板服务
            usd_service: USD服务
        """
        self.file_service = file_service
        self.template_service = template_service
        self.usd_service = usd_service
        self.materialx_processor = MaterialXProcessor()
        self.variant_processor = VariantProcessor(usd_service)

    def process_component(self, component_info: ComponentInfo, component_path: str) -> None:
        """处理单个组件.

        Args:
            component_info: 组件信息
            component_path: 组件路径

        Raises
        ------
            ComponentError: 当处理失败时
        """
        try:
            component_path_obj = Path(component_path)

            # 确保组件目录存在
            self.file_service.ensure_directory_exists(component_path_obj)

            # 1. 创建MaterialX文件
            self._create_materialx_file(component_info, component_path_obj)

            # 2. 创建主入口文件（带有变体支持）
            self._create_main_file(component_info, component_path_obj)

            # 3. 创建payload文件
            self._create_payload_file(component_info, component_path_obj)

            # 4. 创建外观文件
            self._create_look_file(component_info, component_path_obj)

            # 输出处理结果
            self._display_processing_result(component_info)

        except Exception as e:
            msg = f"处理{component_info.component_type.kind} {component_info.name} 失败: {e}"
            raise ComponentError(msg) from e

    def _create_materialx_file(self, component_info: ComponentInfo, component_path: Path) -> None:
        """创建MaterialX文件."""
        if component_info.has_variants or component_info.textures:
            output_mtlx_path = component_path / f"{component_info.name}_mat.mtlx"
            self.materialx_processor.create_materialx_from_component_info(
                component_info,
                str(output_mtlx_path),
            )
        else:
            console.print(
                f"[yellow]⚠ 跳过 {component_info.name} 的 MaterialX 文件创建 (无纹理文件)[/yellow]",
            )

    def _create_main_file(self, component_info: ComponentInfo, component_path: Path) -> None:
        """创建主入口文件."""
        main_file = component_path / f"{component_info.name}.usd"

        if component_info.has_variants:
            self.variant_processor.create_component_main_with_variants(
                component_info,
                str(main_file),
            )
        else:
            self.usd_service.create_component_main_simple(
                str(main_file),
                component_info.name,
                component_info.component_type,
            )

    def _create_payload_file(self, component_info: ComponentInfo, component_path: Path) -> None:
        """创建payload文件."""
        payload_file = component_path / f"{component_info.name}_payload.usd"
        self.template_service.create_component_payload(
            str(payload_file),
            component_info.name,
            component_info.component_type,
        )

    def _create_look_file(self, component_info: ComponentInfo, component_path: Path) -> None:
        """创建外观文件."""
        look_file = component_path / f"{component_info.name}_look.usd"
        self.template_service.create_component_look(
            str(look_file),
            component_info.name,
            component_info.component_type,
        )

    def _display_processing_result(self, component_info: ComponentInfo) -> None:
        """显示处理结果."""
        variant_info = ""
        if component_info.has_variants:
            variant_info = f" (包含{len(component_info.variants)}个变体)"

        console.print(
            f"[green]✓ {component_info.component_type.kind} "
            f"{component_info.name} 处理完成{variant_info}[/green]",
        )
