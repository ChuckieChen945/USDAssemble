"""Chessboard USD Asset Assembly Script.

使用 Pixar OpenUSD API 装配棋盘资产
"""

from pathlib import Path
from string import Template

import typer
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt
from rich import print as rprint
from rich.console import Console

from mtlx.materialx import create_materialx_file

app = typer.Typer()
console = Console()


def ensure_directory(file_path: str) -> None:
    """确保目录存在."""
    directory = Path.parent(file_path)
    if not Path.exists(directory):
        Path.mkdir(directory)


def detect_texture_files(component_path: str, component_name: str) -> dict[str, str]:
    """检测组件目录中的纹理文件."""
    texture_dir = Path(component_path) / "textures"

    if not Path.exists(texture_dir):
        console.print(f"[yellow]警告: 未找到纹理目录 {texture_dir}[/yellow]")
        return {}

    # 常见的纹理文件模式
    texture_patterns = {
        # 键名同时也是.mtlx文件中图像节点的名称
        # https://docs.o3de.org/docs/user-guide/assets/texture-settings/texture-presets/?utm_source=chatgpt.com
        "base_color": ["*base_color*"],  # , "*diffuse*", "*albedo*", "*color*"],
        "metallic": ["*metallic*"],  # , "*metal*"],
        "roughness": ["*roughness*"],  # , "*rough*"],
        "normal": ["*normal*"],  # , "*norm*"],
        "specular": ["*specular*"],  # "*spec*"],
        "scattering": ["*scattering*"],  # "*sss*"],
        "diffuse": ["*diffuse*"],
        "emissive": ["*emissive*"],
        "displacement": ["*displacement*"],
        "opacity": ["*opacity*"],
        "occlusion": ["*occlusion*"],
        "reflection": ["*reflection*"],
        "refraction": ["*refraction*"],
        "sheen": ["*sheen*"],
        "transmission": ["*transmission*"],
    }

    found_textures = {}

    # 扫描纹理文件
    for texture_type, patterns in texture_patterns.items():
        for pattern in patterns:
            files = (
                Path.glob(Path(texture_dir) / f"{pattern}.jpg")
                + Path.glob(Path(texture_dir) / f"{pattern}.png")
                + Path.glob(Path(texture_dir) / f"{pattern}.exr")
            )

            if files:
                # 选择第一个匹配的文件
                relative_path = Path.relative_to(files[0], component_path).replace("\\", "/")
                found_textures[texture_type] = relative_path
                break

    console.print(
        f"[green]为 {component_name} 检测到纹理文件: {list(found_textures.keys())}[/green]",
    )
    # TODO: 检查是否存在重复的纹理文件、没用上的纹理文件,显示警告
    return found_textures


def create_component_payload(output_path: str) -> None:
    """创建 payload 文件 .usda."""
    prim_name = Path.basename(Path.parent(output_path))
    console.print(f"[blue]创建 {prim_name}_payload.usda[/blue]")

    # 创建 stage
    stage = Usd.Stage.CreateNew(output_path)

    # 设置 stage 元数据
    stage.SetDefaultPrim(stage.DefinePrim(Sdf.Path(f"/{prim_name}")))
    stage.SetMetadata("metersPerUnit", 1.0)
    stage.SetMetadata("upAxis", "Y")

    # 设置 subLayers
    stage.GetRootLayer().subLayerPaths = [
        f"./{prim_name}_look.usda",
        f"./{prim_name}_geom.usd",
    ]

    # 保存
    stage.Save()
    console.print(f"[green]保存: {output_path}[/green]")


def create_component_look(output_path: str) -> None:
    """创建外观文件 _look.usda."""
    console.print("[blue]创建 _look.usda[/blue]")

    # 创建一个新的Stage
    stage = Usd.Stage.CreateNew(output_path)
    prim_name = Path.basename(Path.parent(output_path))

    # 设置 stage 元数据
    stage.SetDefaultPrim(stage.DefinePrim(Sdf.Path(f"/{prim_name}")))
    stage.SetMetadata("metersPerUnit", 1.0)
    stage.SetMetadata("upAxis", "Y")

    # === 创建 Materials Scope ===
    materials_scope = stage.OverridePrim(f"/{prim_name}/Materials")
    materials_scope.GetReferences().AddReference(
        f"./{prim_name}_mat.mtlx",  # 外部MaterialX文件
        "/MaterialX/Materials",  # 该文件中要引用的路径
    )

    # === 创建 Geom/Render,并绑定材质 ===
    render_prim = stage.OverridePrim(f"/{prim_name}/Geom/Render")
    render_prim.ApplyAPI(UsdShade.MaterialBindingAPI)

    # 创建绑定关系:指向 component/Materials/M_component
    binding_rel = render_prim.CreateRelationship("material:binding")
    binding_rel.SetTargets([Sdf.Path(f"/{prim_name}/Materials/M_{prim_name}")])

    # 保存文件
    stage.GetRootLayer().Save()
    console.print(f"[green]保存: {output_path}[/green]")


def read_existing_geom_file(geom_file_path: str) -> Usd.Stage | None:
    """读取已有的几何体文件并获取信息."""
    stage = Usd.Stage.Open(geom_file_path)
    if stage:
        console.print(f"[green]成功读取几何体文件: {geom_file_path}[/green]")
        return stage
    return None


def validate_material_file(material_file_path: str) -> bool:
    """验证材质文件是否存在."""
    if not Path.exists(material_file_path):
        console.print(f"[yellow]警告: 材质文件 {material_file_path} 不存在[/yellow]")
        return False
    console.print(f"[green]材质文件存在: {material_file_path}[/green]")
    return True


def validate_texture_files(base_path: str) -> bool:
    """验证纹理文件是否存在."""
    texture_files = [
        "chessboard_base_color.jpg",
        "chessboard_metallic.jpg",
        "chessboard_normal.jpg",
        "chessboard_roughness.jpg",
    ]

    tex_path = Path(base_path) / "tex"
    missing_files = []

    for texture_file in texture_files:
        full_path = Path(tex_path) / texture_file
        if not Path.exists(full_path):
            missing_files.append(texture_file)
        else:
            console.print(f"[green]纹理文件存在: {full_path}[/green]")

    if missing_files:
        console.print(f"[yellow]警告: 缺少纹理文件: {missing_files}[/yellow]")

    return len(missing_files) == 0


def create_component_main(output_path: str) -> None:
    """创建该usd componet asset的主入口文件 .usd."""
    # 创建 stage
    stage = Usd.Stage.CreateNew(output_path)
    prim_name = Path.basename(Path.parent(output_path))

    stage.SetDefaultPrim(stage.DefinePrim(Sdf.Path(f"/{prim_name}")))
    stage.SetMetadata("metersPerUnit", 1.0)
    stage.SetMetadata("upAxis", "Y")

    # 创建 class 定义
    class_prim = stage.CreateClassPrim(Sdf.Path("/__class__"))
    chessboard_class = stage.DefinePrim(Sdf.Path(f"/__class__/{prim_name}"))

    # 创建主 Xform
    chessboard_prim = UsdGeom.Xform.Define(stage, prim_name)
    prim = chessboard_prim.GetPrim()

    # 设置 API schemas
    prim.ApplyAPI(UsdGeom.ModelAPI)

    # 设置 assetInfo
    prim.SetAssetInfo({"identifier": Sdf.AssetPath(f"./{prim_name}.usda"), "name": prim_name})

    # 设置 inherits
    prim.GetInherits().AddInherit(f"/__class__/{prim_name}")

    # 设置 kind
    Usd.ModelAPI(prim).SetKind("component")

    # 设置 payload
    prim.GetPayloads().AddPayload(f"./{prim_name}_payload.usda", f"/{prim_name}")

    # 设置 extentsHint
    extents_attr = prim.CreateAttribute("extentsHint", Sdf.ValueTypeNames.Float3Array)
    # TODO: 根据不同的 usd 文件自动设置不同的 extentsHint
    extents_attr.Set(
        Vt.Vec3fArray(
            [
                Gf.Vec3f(-0.35270807, 0, -0.35270807),
                Gf.Vec3f(0.35270807, 0.01851505, 0.35270807),
            ],
        ),
    )

    # 保存
    stage.Save()
    console.print(f"[green]保存: {output_path}[/green]")


def scan_components(base_path: str) -> list[str]:
    """扫描目录中的组件."""
    components_path = Path(base_path) / "components"

    if not Path.exists(components_path):
        console.print(f"[yellow]警告: 未找到 components 目录: {components_path}[/yellow]")
        return []

    components = []
    for item in Path.iterdir(components_path):
        item_path = Path(components_path) / item
        if Path.is_dir(item_path):
            # 检查是否有几何体文件
            geom_file = Path(item_path) / f"{item}_geom.usd"
            if Path.exists(geom_file):
                components.append(item)
                console.print(f"[green]发现组件: {item}[/green]")
            else:
                console.print(f"[yellow]跳过目录 {item} (未找到几何体文件)[/yellow]")

    return components


def create_assembly_main(output_path: str, assembly_name: str, components: list[str]) -> None:
    """创建 assembly 主入口文件."""
    console.print(f"[blue]创建 assembly 主入口文件: {assembly_name}.usda[/blue]")

    # 创建 stage
    stage = Usd.Stage.CreateNew(output_path)

    # 设置 stage 元数据
    stage.SetDefaultPrim(stage.DefinePrim(Sdf.Path(f"/{assembly_name}")))
    stage.SetMetadata("metersPerUnit", 1.0)
    stage.SetMetadata("upAxis", "Y")

    # 创建 class 定义
    class_prim = stage.CreateClassPrim(Sdf.Path("/__class__"))
    assembly_class = stage.DefinePrim(Sdf.Path(f"/__class__/{assembly_name}"))

    # 创建主 Xform
    assembly_prim = UsdGeom.Xform.Define(stage, assembly_name)
    prim = assembly_prim.GetPrim()

    # 设置 API schemas
    prim.ApplyAPI(UsdGeom.ModelAPI)

    # 设置 assetInfo
    prim.SetAssetInfo(
        {"identifier": Sdf.AssetPath(f"./{assembly_name}.usda"), "name": assembly_name},
    )

    # 设置 inherits
    prim.GetInherits().AddInherit(f"/__class__/{assembly_name}")

    # 设置 kind
    Usd.ModelAPI(prim).SetKind("assembly")

    # 为每个组件创建引用
    for component_name in components:
        component_ref_path = f"./components/{component_name}/{component_name}.usda"
        component_prim = stage.DefinePrim(Sdf.Path(f"/{assembly_name}/{component_name}"))
        component_prim.GetReferences().AddReference(component_ref_path, f"/{component_name}")
        console.print(f"[green]添加组件引用: {component_name}[/green]")

    # 保存
    stage.Save()
    console.print(f"[green]保存: {output_path}[/green]")


def process_component(component_path: str, component_name: str) -> None:
    """处理单个组件."""
    console.print(f"\n[bold blue]=== 处理组件: {component_name} ===[/bold blue]")

    # 检测纹理文件
    texture_files = detect_texture_files(component_path, component_name)

    # 创建 MaterialX 文件
    if texture_files:
        create_materialx_file(component_path, component_name, texture_files)
    else:
        console.print("[yellow]跳过 MaterialX 文件创建 (无纹理文件)[/yellow]")

    # 创建主入口文件
    main_file = Path(component_path) / f"{component_name}.usda"
    create_component_main(main_file)

    # 创建 payload 文件
    payload_file = Path(component_path) / f"{component_name}_payload.usda"
    create_component_payload(payload_file)

    # 创建外观文件
    look_file = Path(component_path) / f"{component_name}_look.usda"
    create_component_look(look_file)


@app.command()
def assembly(base_path: str = "./") -> None:
    """装配 USD assembly."""
    base_path = Path.abspath(base_path)
    assembly_name = Path.basename(base_path)

    console.print(f"[bold blue]=== 装配 USD Assembly: {assembly_name} ===[/bold blue]")
    console.print(f"[blue]路径: {base_path}[/blue]")

    # 扫描组件
    components = scan_components(base_path)

    if not components:
        console.print("[red]错误: 未找到任何组件[/red]")
        return

    console.print(f"[green]找到 {len(components)} 个组件: {components}[/green]")

    # 处理每个组件
    for component_name in components:
        component_path = Path(base_path) / "components" / component_name
        # TODO: 考虑一下这里是否直接复用 component()函数，以简化代码
        process_component(component_path, component_name)

    # 创建 assembly 主文件
    assembly_file = Path(base_path) / f"{assembly_name}.usda"
    create_assembly_main(assembly_file, assembly_name, components)

    console.print("\n[bold green]✓ Assembly 装配完成![/bold green]")
