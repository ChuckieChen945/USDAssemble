"""USD Assembly构建器."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.utils.path_utils import get_component_directory_and_type
from src.utils.utils import scan_component_info

from core.component import ComponentProcessor
from domain.enums import ComponentType
from domain.exceptions import AssemblyError
from domain.models import ComponentInfo
from services.file_service import FileService
from services.template_service import TemplateService
from services.usd_service import UsdService

console = Console()


class AssemblyBuilder:
    """USD Assembly构建器.

    负责协调整个装配过程，包括组件扫描、处理和装配文件生成。
    """

    def __init__(self) -> None:
        """初始化Assembly构建器."""
        self.file_service = FileService()
        self.template_service = TemplateService()
        self.usd_service = UsdService()
        self.component_processor = ComponentProcessor(
            self.file_service,
            self.template_service,
            self.usd_service,
        )

    def scan_components(self, base_path: str) -> list[ComponentInfo]:
        """扫描目录中的组件，返回ComponentInfo列表.

        Args:
            base_path: 基础路径

        Returns
        -------
            List[ComponentInfo]: 有效组件信息列表

        Raises
        ------
            AssemblyError: 当未找到任何组件时
        """
        try:
            base_path_obj = Path(base_path)
            components_path, component_type = get_component_directory_and_type(base_path_obj)
        except ValueError as e:
            raise AssemblyError(str(e)) from e

        components = []

        # 使用文件服务来扫描组件
        component_dirs = self.file_service.list_directories(components_path)

        for component_dir in component_dirs:
            try:
                component_info = scan_component_info(component_dir, component_type)
                if component_info.is_valid:
                    components.append(component_info)
            except Exception as e:
                console.print(f"[red]✗ 扫描组件 {component_dir.name} 失败: {e}[/red]")

        if not components:
            msg = f"未找到任何有效{component_type.kind}（需要包含*_geom.usd文件）"
            raise AssemblyError(msg)

        self._display_scan_results(components, component_type)
        return components

    def _display_scan_results(
        self,
        components: list[ComponentInfo],
        component_type: ComponentType,
    ) -> None:
        """显示扫描结果."""
        from rich.table import Table

        table = Table(title=f"扫描到的{component_type.kind}")
        table.add_column("组件名", style="cyan")
        table.add_column("状态", style="green")
        table.add_column("类型", style="blue")
        table.add_column("变体数", style="magenta")
        table.add_column("纹理数", style="yellow")

        for component_info in components:
            variant_count = len(component_info.variants) if component_info.has_variants else 0
            texture_count = (
                len(component_info.textures)
                if not component_info.has_variants
                else sum(len(v.textures) for v in component_info.variants)
            )

            table.add_row(
                component_info.name,
                "✓ 有效",
                component_type.kind,
                str(variant_count) if variant_count > 0 else "-",
                str(texture_count) if texture_count > 0 else "-",
            )

        console.print(table)

    def build_assembly(self, base_path: str) -> None:
        """构建USD装配.

        Args:
            base_path: 资产目录路径

        Raises
        ------
            AssemblyError: 当构建失败时
        """
        base_path_obj = Path(base_path).resolve()
        assembly_name = base_path_obj.name

        # 显示标题
        console.print(
            Panel.fit(
                f"[bold blue]USD Assembly 装配工具[/bold blue]\n"
                f"[blue]项目: {assembly_name}[/blue]\n"
                f"[blue]路径: {base_path_obj}[/blue]",
                border_style="blue",
            ),
        )

        # 扫描组件
        components = self.scan_components(str(base_path_obj))
        component_type = components[0].component_type

        # 统计信息
        total_variants = sum(len(c.variants) for c in components if c.has_variants)
        components_with_variants = sum(1 for c in components if c.has_variants)

        console.print(f"\n[green]找到 {len(components)} 个有效{component_type.kind}[/green]")
        if total_variants > 0:
            console.print(
                f"[blue]其中 {components_with_variants} 个组件包含总计 {total_variants} 个变体[/blue]",
            )

        # 处理每个组件
        self._process_components(components, base_path_obj, component_type)

        # 创建assembly主文件
        self._create_assembly_main_file(components, assembly_name, base_path_obj)

        # 显示完成信息
        self._display_completion_message(components, total_variants, component_type)

    def _process_components(
        self,
        components: list[ComponentInfo],
        base_path: Path,
        component_type: ComponentType,
    ) -> None:
        """处理所有组件."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"处理{component_type.kind}...", total=len(components))

            for component_info in components:
                component_path = base_path / component_type.directory / component_info.name
                self.component_processor.process_component(component_info, str(component_path))
                progress.advance(task)

    def _create_assembly_main_file(
        self,
        components: list[ComponentInfo],
        assembly_name: str,
        base_path: Path,
    ) -> None:
        """创建assembly主文件."""
        console.print("\n[bold blue]生成 Assembly 主文件...[/bold blue]")
        assembly_file = base_path / f"{assembly_name}.usda"

        self.usd_service.create_assembly_main(
            str(assembly_file),
            assembly_name,
            components,
        )

    def _display_completion_message(
        self,
        components: list[ComponentInfo],
        total_variants: int,
        component_type: ComponentType,
    ) -> None:
        """显示完成信息."""
        completion_message = "[bold green]✅ Assembly 装配完成![/bold green]\n"
        completion_message += f"[green]包含 {len(components)} 个{component_type.kind}[/green]"

        if total_variants > 0:
            completion_message += f"\n[blue]支持 {total_variants} 个材质变体[/blue]"

        console.print(Panel.fit(completion_message, border_style="green"))
