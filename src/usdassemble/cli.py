"""USD Asset Assembly Script.

使用 Pixar OpenUSD API 装配USD资产，支持变体
"""

from pathlib import Path
from string import Template

import typer
from pxr import Sdf, Usd, UsdShade
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mtlx.materialx import create_materialx_from_component_info
from usdassemble.utils import (
    ComponentInfo,
    ComponentType,
    VariantError,
    ensure_directory,
    get_component_directory_and_type,
    get_template_dir,
    scan_component_info,
)

app = typer.Typer(help="USD资产自动组装工具")
console = Console()


class AssemblyError(Exception):
    """装配过程中的错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def create_from_template(
    template_path: Path,
    output_path: Path,
    substitutions: dict[str, str],
) -> None:
    """从模板文件创建新文件，使用string.Template进行替换.

    Args:
        template_path: 模板文件路径
        output_path: 输出文件路径
        substitutions: 替换字典

    Raises
    ------
        AssemblyError: 当模板文件不存在或处理失败时
    """
    if not template_path.exists():
        msg = f"模板文件不存在: {template_path}"
        raise AssemblyError(msg)

    # 确保输出目录存在
    ensure_directory(output_path)

    # 读取模板内容
    with Path.open(template_path, encoding="utf-8") as f:
        template_content = f.read()

    # 进行替换
    template = Template(template_content)
    content = template.safe_substitute(**substitutions)

    # 写入输出文件
    with Path.open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    console.print(f"[green]✓ 生成文件: {output_path.name}[/green]")


def create_component_payload(
    output_path: str,
    component_name: str,
    component_type: ComponentType,
) -> None:
    """从模板创建 payload 文件."""
    template_path = (
        get_template_dir()
        / "{$assembly_name}"
        / component_type.directory
        / "{$component_name}"
        / "{$component_name}_payload.usd"
    )

    substitutions = {
        "component_name": component_name,
    }

    create_from_template(template_path, Path(output_path), substitutions)


def create_component_look(
    output_path: str,
    component_name: str,
    component_type: ComponentType,
) -> None:
    """从模板创建外观文件."""
    template_path = (
        get_template_dir()
        / "{$assembly_name}"
        / component_type.directory
        / "{$component_name}"
        / "{$component_name}_look.usd"
    )

    substitutions = {
        "component_name": component_name,
    }

    create_from_template(template_path, Path(output_path), substitutions)


# TODO: `create_component_main_with_variants` is too complex，重构
def create_component_main_with_variants(
    component_info: ComponentInfo,
    output_path: str,
) -> None:
    """创建支持变体的组件主文件.

    Args:
        component_info: 组件信息
        output_path: 输出文件路径

    Raises
    ------
        AssemblyError: 当创建失败时
    """
    try:
        # 首先从模板创建基础文件
        template_path = (
            get_template_dir()
            / "{$assembly_name}"
            / component_info.component_type.directory
            / "{$component_name}"
            / "{$component_name}.usd"
        )

        substitutions = {
            "component_name": component_info.name,
        }

        create_from_template(template_path, Path(output_path), substitutions)

        # 如果有变体，添加变体集
        if component_info.has_variants:
            stage = Usd.Stage.Open(output_path)
            if not stage:
                msg = f"无法打开USD文件: {output_path}"
                raise AssemblyError(msg)

            # 获取组件prim
            component_prim = stage.GetPrimAtPath(f"/{component_info.name}")
            if not component_prim:
                msg = f"未找到组件prim: /{component_info.name}"
                raise AssemblyError(msg)

            # 设置正确的kind值
            model_api = Usd.ModelAPI(component_prim)
            model_api.SetKind(component_info.component_type.kind)

            # 创建变体集
            variant_sets = component_prim.GetVariantSets()
            material_variant_set = variant_sets.AddVariantSet("material_variant")

            # 为每个变体创建变体
            for variant in component_info.variants:
                material_variant_set.AddVariant(variant.name)
                material_variant_set.SetVariantSelection(variant.name)

                # 在变体上下文中修改材质绑定
                with material_variant_set.GetVariantEditContext():
                    # 创建变体特定的材质引用
                    materials_scope = stage.GetPrimAtPath(f"/{component_info.name}/Materials")
                    if materials_scope:
                        # 清除默认引用，添加变体特定的引用
                        materials_scope.GetReferences().ClearReferences()
                        materials_scope.GetReferences().AddReference(
                            f"./{component_info.name}_mat.mtlx",
                            "/MaterialX/Materials",
                        )

                        # 更新材质绑定到变体特定的材质
                        geom_prim = stage.GetPrimAtPath(f"/{component_info.name}/Geom")
                        if geom_prim:
                            render_prim = geom_prim.GetChild("Render")
                            if render_prim:
                                material_binding_api = UsdShade.MaterialBindingAPI(render_prim)
                                variant_material_path = f"/{component_info.name}/Materials/M_{component_info.name}_{variant.name}"
                                material_binding_api.Bind(
                                    UsdShade.Material(stage.GetPrimAtPath(variant_material_path)),
                                )

            # 设置默认变体为第一个变体
            if component_info.variants:
                material_variant_set.SetVariantSelection(component_info.variants[0].name)

            # 保存修改
            stage.Save()

            console.print(
                f"[blue]✓ 设置组件 {component_info.name} 的变体: "
                f"{[v.name for v in component_info.variants]}[/blue]",
            )
        else:
            # 没有变体，只需设置kind值
            stage = Usd.Stage.Open(output_path)
            if stage:
                component_prim = stage.GetPrimAtPath(f"/{component_info.name}")
                if component_prim:
                    model_api = Usd.ModelAPI(component_prim)
                    model_api.SetKind(component_info.component_type.kind)
                    stage.Save()

                    console.print(
                        f"[blue]✓ 设置组件 {component_info.name} 的kind为: "
                        f"{component_info.component_type.kind}[/blue]",
                    )

    except Exception as e:
        msg = f"创建组件主文件失败: {e}"
        raise AssemblyError(msg) from e


def create_component_main(
    output_path: str,
    component_name: str,
    component_type: ComponentType,
) -> None:
    """从模板创建组件主入口文件，根据组件类型设置正确的kind值（兼容接口）."""
    # 创建简单的ComponentInfo用于兼容
    from usdassemble.utils import ComponentInfo

    component_info = ComponentInfo(
        name=component_name,
        component_type=component_type,
        has_geometry=True,
    )

    create_component_main_with_variants(component_info, output_path)


def scan_components(base_path: str) -> list[ComponentInfo]:
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
    table = Table(title=f"扫描到的{component_type.kind}")
    table.add_column("组件名", style="cyan")
    table.add_column("状态", style="green")
    table.add_column("类型", style="blue")
    table.add_column("变体数", style="magenta")
    table.add_column("纹理数", style="yellow")

    for item in components_path.iterdir():
        if item.is_dir():
            try:
                component_info = scan_component_info(item, component_type)

                if component_info.is_valid:
                    components.append(component_info)

                    # 统计信息
                    variant_count = (
                        len(component_info.variants) if component_info.has_variants else 0
                    )
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
                else:
                    table.add_row(
                        item.name,
                        "[yellow]✗ 缺少几何体文件[/yellow]",
                        component_type.kind,
                        "-",
                        "-",
                    )

            except (VariantError, Exception) as e:
                console.print(f"[red]✗ 扫描组件 {item.name} 失败: {e}[/red]")
                table.add_row(
                    item.name,
                    f"[red]✗ 错误: {str(e)[:30]}...[/red]",
                    component_type.kind,
                    "-",
                    "-",
                )

    if table.rows:
        console.print(table)

    if not components:
        msg = f"未找到任何有效{component_type.kind}（需要包含*_geom.usd文件）"
        raise AssemblyError(msg)

    return components


def create_assembly_main(
    output_path: str,
    assembly_name: str,
    components: list[ComponentInfo],
) -> None:
    """从模板创建 assembly 主入口文件.

    Args:
        output_path: 输出文件路径
        assembly_name: 装配名称
        components: 组件信息列表

    Raises
    ------
        AssemblyError: 当创建失败时
    """
    if not components:
        msg = "组件列表为空"
        raise AssemblyError(msg)

    # 所有组件应该是同一类型
    component_type = components[0].component_type

    template_path = get_template_dir() / "{$assembly_name}" / "{$assembly_name}.usda"

    try:
        # 读取模板
        with Path.open(template_path, encoding="utf-8") as f:
            template_content = f.read()

        # 先进行基础替换
        template = Template(template_content)
        content = template.safe_substitute(assembly_name=assembly_name)

        # 使用USD API来正确添加多个组件引用
        # 创建临时文件
        temp_file = Path(output_path).with_suffix(".temp.usda")
        with Path.open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 用USD API加载并修改
        stage = Usd.Stage.Open(str(temp_file))
        if not stage:
            msg = f"无法打开临时USD文件: {temp_file}"
            raise AssemblyError(msg)

        # 获取assembly prim
        assembly_prim = stage.GetPrimAtPath(f"/{assembly_name}")
        if not assembly_prim:
            msg = f"未找到assembly prim: /{assembly_name}"
            raise AssemblyError(msg)

        # 为每个组件创建引用
        for component_info in components:
            component_ref_path = (
                f"./{component_type.directory}/{component_info.name}/{component_info.name}.usd"
            )
            component_prim = stage.OverridePrim(
                Sdf.Path(f"/{assembly_name}/{component_info.name}"),
            )
            component_prim.SetTypeName("Xform")
            component_prim.GetReferences().AddReference(component_ref_path)

        # 保存到最终路径
        stage.GetRootLayer().Export(output_path)

        # 清理临时文件
        temp_file.unlink(missing_ok=True)

        console.print(f"[green]✓ 生成assembly文件: {Path(output_path).name}[/green]")
        console.print(f"[blue]✓ 包含 {len(components)} 个{component_type.kind}引用[/blue]")

    except Exception as e:
        # 清理临时文件
        if "temp_file" in locals():
            temp_file.unlink(missing_ok=True)
        msg = f"创建assembly文件失败: {e}"
        raise AssemblyError(msg) from e


def process_component(component_info: ComponentInfo, component_path: str) -> None:
    """处理单个组件.

    Args:
        component_info: 组件信息
        component_path: 组件路径

    Raises
    ------
        AssemblyError: 当处理失败时
    """
    try:
        # 创建 MaterialX 文件
        if component_info.has_variants or component_info.textures:
            output_mtlx_path = Path(component_path) / f"{component_info.name}_mat.mtlx"
            create_materialx_from_component_info(component_info, str(output_mtlx_path))
        else:
            console.print(
                f"[yellow]⚠ 跳过 {component_info.name} 的 MaterialX 文件创建 (无纹理文件)[/yellow]",
            )

        # 创建主入口文件（带有变体支持）
        main_file = Path(component_path) / f"{component_info.name}.usd"
        create_component_main_with_variants(component_info, str(main_file))

        # 创建 payload 文件
        payload_file = Path(component_path) / f"{component_info.name}_payload.usd"
        create_component_payload(
            str(payload_file),
            component_info.name,
            component_info.component_type,
        )

        # 创建外观文件
        look_file = Path(component_path) / f"{component_info.name}_look.usd"
        create_component_look(
            str(look_file),
            component_info.name,
            component_info.component_type,
        )

        # 输出处理结果
        variant_info = ""
        if component_info.has_variants:
            variant_info = f" (包含{len(component_info.variants)}个变体)"

        console.print(
            f"[green]✓ {component_info.component_type.kind} "
            f"{component_info.name} 处理完成{variant_info}[/green]",
        )

    except Exception as e:
        msg = f"处理{component_info.component_type.kind} {component_info.name} 失败: {e}"
        raise AssemblyError(msg) from e


@app.command()
def assemble(
    base_path: str = typer.Argument("./", help="资产目录路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细信息"),
) -> None:
    """装配 USD assembly，支持components和subcomponents目录，以及变体."""
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
    components = scan_components(str(base_path_obj))
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
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"处理{component_type.kind}...", total=len(components))

        for component_info in components:
            component_path = base_path_obj / component_type.directory / component_info.name
            process_component(component_info, str(component_path))
            progress.advance(task)

    # 创建 assembly 主文件
    console.print("\n[bold blue]生成 Assembly 主文件...[/bold blue]")
    assembly_file = base_path_obj / f"{assembly_name}.usda"
    create_assembly_main(str(assembly_file), assembly_name, components)

    # 完成
    completion_message = "[bold green]✅ Assembly 装配完成![/bold green]\n"
    completion_message += f"[green]包含 {len(components)} 个{component_type.kind}[/green]"

    if total_variants > 0:
        completion_message += f"\n[blue]支持 {total_variants} 个材质变体[/blue]"

    console.print(Panel.fit(completion_message, border_style="green"))


if __name__ == "__main__":
    app()
