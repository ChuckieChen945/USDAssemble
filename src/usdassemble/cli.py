"""
Chessboard USD Asset Assembly Script.

使用 Pixar OpenUSD API 装配棋盘资产
"""

import os

import typer
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt
from rich import print as rprint

app = typer.Typer()


def ensure_directory(file_path):
    """确保目录存在."""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_component_payload(output_path):
    """创建 payload 文件 .usda"""
    prim_name = os.path.basename(os.path.dirname(output_path))
    print(f"Creating {prim_name}_payload.usda...")

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
    print(f"Saved: {output_path}")


def create_component_look(output_path):
    """创建外观文件 _look.usda"""
    print("Creating _look.usda...")

    # 创建一个新的Stage
    stage = Usd.Stage.CreateNew(output_path)
    prim_name = os.path.basename(os.path.dirname(output_path))

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

    # === 创建 Geom/Render，并绑定材质 ===
    render_prim = stage.OverridePrim(f"/{prim_name}/Geom/Render")
    render_prim.ApplyAPI(UsdShade.MaterialBindingAPI)

    # 创建绑定关系：指向 Chessboard/Materials/M_Chessboard
    binding_rel = render_prim.CreateRelationship("material:binding")
    binding_rel.SetTargets([Sdf.Path(f"/{prim_name}/Materials/M_{prim_name}")])

    # 保存文件
    stage.GetRootLayer().Save()


def read_existing_geom_file(geom_file_path):
    """读取已有的几何体文件并获取信息"""
    stage = Usd.Stage.Open(geom_file_path)
    if stage:
        print(f"Successfully read existing geometry file: {geom_file_path}")
        return stage

    return None


def validate_material_file(material_file_path):
    """验证材质文件是否存在"""
    if not os.path.exists(material_file_path):
        print(f"Warning: Material file {material_file_path} not found.")
        return False
    print(f"Material file found: {material_file_path}")
    return True


def validate_texture_files(base_path):
    """验证纹理文件是否存在"""
    texture_files = [
        "chessboard_base_color.jpg",
        "chessboard_metallic.jpg",
        "chessboard_normal.jpg",
        "chessboard_roughness.jpg",
    ]

    tex_path = os.path.join(base_path, "tex")
    missing_files = []

    for texture_file in texture_files:
        full_path = os.path.join(tex_path, texture_file)
        if not os.path.exists(full_path):
            missing_files.append(texture_file)
        else:
            print(f"Texture file found: {full_path}")

    if missing_files:
        print(f"Warning: Missing texture files: {missing_files}")

    return len(missing_files) == 0


def create_component_main(output_path):
    """创建该usd componet asset的主入口文件 .usd"""
    # 创建 stage
    stage = Usd.Stage.CreateNew(output_path)
    prim_name = os.path.basename(os.path.dirname(output_path))

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
    print(f"Saved: {output_path}")


@app.command()
def component(base_path: str = "./") -> None:
    rprint(f"Assembling USD component at [green]{base_path}[/green]...")
    prim_name = os.path.basename(os.path.dirname(base_path))

    # 确保输出目录存在
    if not os.path.exists(base_path):
        os.makedirs(base_path)
        print(f"Created directory: {base_path}")

    # 验证已有文件
    geom_file = os.path.join(base_path, "Chessboard_geom.usd")
    material_file = os.path.join(base_path, "Chessboard_mat.mtlx")

    print("\n=== Validating existing files ===")
    geom_stage = read_existing_geom_file(geom_file)
    material_exists = validate_material_file(material_file)
    textures_exist = validate_texture_files(base_path)

    # 生成需要装配的文件
    print("\n=== Assembling USD files ===")

    # 1. 创建主入口文件
    main_file = os.path.join(base_path, f"{prim_name}.usda")
    ensure_directory(main_file)
    create_component_main(main_file)

    # 2. 创建 payload 文件
    payload_file = os.path.join(base_path, f"{prim_name}_payload.usda")
    create_component_payload(payload_file)

    # 3. 创建外观文件
    look_file = os.path.join(base_path, f"{prim_name}_look.usda")
    create_component_look(look_file)


@app.command()
def subcompoment(path: str = "./") -> None:
    """Assemble USD asset."""
    rprint(f"Assembling USD asset at [green]{path}[/green]...")


@app.command()
def assembly(path: str = "./") -> None:
    rprint(f"Assembling USD asset at [green]{path}[/green]...")


# def test_load_assembled_asset(main_file):
#     """测试加载装配好的资产"""
#     print(f"\n=== Testing assembled asset ===")
#     try:
#         stage = Usd.Stage.Open(main_file)
#         if stage:
#             print(f"✓ Successfully opened: {main_file}")

#             # 检查默认 prim
#             default_prim = stage.GetDefaultPrim()
#             if default_prim:
#                 print(f"✓ Default prim: {default_prim.GetPath()}")

#                 # 检查 payload 是否正确加载
#                 if default_prim.HasPayload():
#                     print("✓ Payload found")

#                 # 加载所有 payload 来测试完整装配
#                 stage.LoadAndUnload(Usd.LoadWithDescendants)
#                 print("✓ Payloads loaded successfully")

#             else:
#                 print("⚠ No default prim found")

#         else:
#             print(f"✗ Failed to open: {main_file}")

#     except Exception as e:
#         print(f"✗ Error testing asset: {e}")
