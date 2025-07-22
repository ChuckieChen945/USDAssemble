#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chessboard USD Asset Assembly Script
使用 Pixar OpenUSD API 装配棋盘资产
"""

import os

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt


def ensure_directory(file_path):
    """确保目录存在"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def create_chessboard_main(output_path):
    """创建主入口文件 Chessboard.usd"""
    print("Creating Chessboard.usd...")

    # 创建 stage
    stage = Usd.Stage.CreateNew(output_path)

    # 设置 stage 元数据
    stage.SetDefaultPrim(stage.DefinePrim(Sdf.Path("/Chessboard")))
    stage.SetMetadata("metersPerUnit", 1.0)
    stage.SetMetadata("upAxis", "Y")

    # 创建 class 定义
    class_prim = stage.CreateClassPrim(Sdf.Path("/__class__"))
    chessboard_class = stage.DefinePrim(Sdf.Path("/__class__/Chessboard"))

    # 创建主 Xform
    chessboard_prim = UsdGeom.Xform.Define(stage, "/Chessboard")
    prim = chessboard_prim.GetPrim()

    # 设置 API schemas
    prim.ApplyAPI(UsdGeom.ModelAPI)

    # 设置 assetInfo
    prim.SetAssetInfo(
        {"identifier": Sdf.AssetPath("./Chessboard.usd"), "name": "Chessboard"}
    )

    # 设置 inherits
    prim.GetInherits().AddInherit("/__class__/Chessboard")

    # 设置 kind
    Usd.ModelAPI(prim).SetKind("component")

    # 设置 payload
    prim.GetPayloads().AddPayload("./Chessboard_payload.usd", "/Chessboard")

    # 设置 extentsHint
    extents_attr = prim.CreateAttribute("extentsHint", Sdf.ValueTypeNames.Float3Array)
    extents_attr.Set(
        Vt.Vec3fArray(
            [
                Gf.Vec3f(-0.35270807, 0, -0.35270807),
                Gf.Vec3f(0.35270807, 0.01851505, 0.35270807),
            ]
        )
    )

    # 保存
    stage.Save()
    print(f"Saved: {output_path}")


def create_chessboard_payload(output_path):
    """创建 payload 文件 Chessboard_payload.usd"""
    print("Creating Chessboard_payload.usd...")

    # 创建 stage
    stage = Usd.Stage.CreateNew(output_path)

    # 设置 stage 元数据
    stage.SetDefaultPrim(stage.DefinePrim(Sdf.Path("/Chessboard")))
    stage.SetMetadata("metersPerUnit", 1.0)
    stage.SetMetadata("upAxis", "Y")

    # 设置 subLayers
    stage.GetRootLayer().subLayerPaths = [
        "./Chessboard_look.usd",
        "./Chessboard_geom.usd",
    ]

    # 保存
    stage.Save()
    print(f"Saved: {output_path}")


def create_chessboard_look(output_path, base_path):
    """创建外观文件 Chessboard_look.usd"""
    print("Creating Chessboard_look.usd...")

    # 首先创建 MaterialX 包装文件
    wrapper_file = create_materialx_wrapper(base_path)
    if not wrapper_file:
        print("Warning: Failed to create MaterialX wrapper, using fallback")

    # 创建 stage
    stage = Usd.Stage.CreateNew(output_path)

    # 设置 stage 元数据
    stage.SetDefaultPrim(stage.DefinePrim(Sdf.Path("/Chessboard")))
    stage.SetMetadata("metersPerUnit", 1.0)
    stage.SetMetadata("upAxis", "Y")

    # 创建 over "Chessboard"
    chessboard_prim = stage.OverridePrim("/Chessboard")

    # 创建 Materials Scope
    materials_scope = UsdGeom.Scope.Define(stage, "/Chessboard/Materials")
    materials_prim = materials_scope.GetPrim()

    # 引用材质包装文件或 MaterialX 文件
    if wrapper_file and os.path.exists(wrapper_file):
        wrapper_filename = os.path.basename(wrapper_file)
        materials_prim.GetReferences().AddReference(
            f"./{wrapper_filename}", "/Materials"
        )
        print(f"Added reference to MaterialX wrapper: {wrapper_filename}")
    else:
        # 直接创建材质定义
        create_material_definition(stage, "/Chessboard/Materials")

    # 创建 Geom over
    geom_prim = stage.OverridePrim("/Chessboard/Geom")

    # 创建 Render over 并应用 MaterialBindingAPI
    render_prim = stage.OverridePrim("/Chessboard/Geom/Render")
    render_prim.ApplyAPI(UsdShade.MaterialBindingAPI)

    # 绑定材质 - 使用 relationship 方式
    binding_api = UsdShade.MaterialBindingAPI(render_prim)
    material_rel = binding_api.GetDirectBindingRel()
    material_rel.SetTargets([Sdf.Path("/Chessboard/Materials/M_Chessboard")])

    # 保存
    stage.Save()
    print(f"Saved: {output_path}")


def create_material_definition(stage, materials_path):
    """在 USD stage 中创建材质定义"""
    # 创建材质 prim
    material = UsdShade.Material.Define(stage, f"{materials_path}/M_Chessboard")

    # 创建 surface shader
    shader = UsdShade.Shader.Define(
        stage, f"{materials_path}/M_Chessboard/PreviewSurface"
    )
    shader.CreateIdAttr("UsdPreviewSurface")

    # 创建纹理相关的输入
    diffuse_input = shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
    metallic_input = shader.CreateInput("metallic", Sdf.ValueTypeNames.Float)
    roughness_input = shader.CreateInput("roughness", Sdf.ValueTypeNames.Float)
    normal_input = shader.CreateInput("normal", Sdf.ValueTypeNames.Normal3f)

    # 创建纹理节点
    create_texture_nodes(
        stage,
        f"{materials_path}/M_Chessboard",
        shader,
        diffuse_input,
        metallic_input,
        roughness_input,
        normal_input,
    )

    # 连接 shader 到 material
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    print("Created material definition with textures")


def create_materialx_wrapper(base_path):
    """创建 MaterialX 的 USD 包装文件"""
    wrapper_file = os.path.join(base_path, "Chessboard_mat_wrapper.usd")
    print(f"Creating MaterialX wrapper: {wrapper_file}")

    try:
        stage = Usd.Stage.CreateNew(wrapper_file)

        # 设置默认 prim 为 Materials
        stage.SetDefaultPrim(stage.DefinePrim(Sdf.Path("/Materials")))
        stage.SetMetadata("upAxis", "Y")

        # 创建 Materials scope
        materials_scope = UsdGeom.Scope.Define(stage, "/Materials")

        # 创建 M_Chessboard 材质
        material = UsdShade.Material.Define(stage, "/Materials/M_Chessboard")

        # 创建 surface shader (使用 UsdPreviewSurface 作为示例)
        shader = UsdShade.Shader.Define(stage, "/Materials/M_Chessboard/PreviewSurface")
        shader.CreateIdAttr("UsdPreviewSurface")

        # 创建纹理相关的输入
        diffuse_input = shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
        metallic_input = shader.CreateInput("metallic", Sdf.ValueTypeNames.Float)
        roughness_input = shader.CreateInput("roughness", Sdf.ValueTypeNames.Float)
        normal_input = shader.CreateInput("normal", Sdf.ValueTypeNames.Normal3f)

        # 创建纹理节点
        create_texture_nodes(
            stage,
            "/Materials/M_Chessboard",
            shader,
            diffuse_input,
            metallic_input,
            roughness_input,
            normal_input,
        )

        # 连接 shader 到 material
        material.CreateSurfaceOutput().ConnectToSource(
            shader.ConnectableAPI(), "surface"
        )

        stage.Save()
        print(f"Saved MaterialX wrapper: {wrapper_file}")
        return wrapper_file

    except Exception as e:
        print(f"Error creating MaterialX wrapper: {e}")
        return None


def create_texture_nodes(
    stage,
    material_path,
    shader,
    diffuse_input,
    metallic_input,
    roughness_input,
    normal_input,
):
    """创建纹理节点"""
    # Base Color 纹理
    base_color_tex = UsdShade.Shader.Define(stage, f"{material_path}/BaseColorTexture")
    base_color_tex.CreateIdAttr("UsdUVTexture")
    base_color_tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(
        "tex/chessboard_base_color.jpg"
    )
    base_color_tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")

    # 连接到 diffuse
    diffuse_input.ConnectToSource(base_color_tex.ConnectableAPI(), "rgb")

    # Metallic 纹理
    metallic_tex = UsdShade.Shader.Define(stage, f"{material_path}/MetallicTexture")
    metallic_tex.CreateIdAttr("UsdUVTexture")
    metallic_tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(
        "tex/chessboard_metallic.jpg"
    )
    metallic_tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("raw")

    # 连接到 metallic
    metallic_input.ConnectToSource(metallic_tex.ConnectableAPI(), "r")

    # Roughness 纹理
    roughness_tex = UsdShade.Shader.Define(stage, f"{material_path}/RoughnessTexture")
    roughness_tex.CreateIdAttr("UsdUVTexture")
    roughness_tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(
        "tex/chessboard_roughness.jpg"
    )
    roughness_tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("raw")

    # 连接到 roughness
    roughness_input.ConnectToSource(roughness_tex.ConnectableAPI(), "r")

    # Normal 纹理
    normal_tex = UsdShade.Shader.Define(stage, f"{material_path}/NormalTexture")
    normal_tex.CreateIdAttr("UsdUVTexture")
    normal_tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(
        "tex/chessboard_normal.jpg"
    )
    normal_tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("raw")

    # 连接到 normal
    normal_input.ConnectToSource(normal_tex.ConnectableAPI(), "rgb")


def read_existing_geom_file(geom_file_path):
    """读取已有的几何体文件并获取信息"""
    if not os.path.exists(geom_file_path):
        print(
            f"Warning: Geometry file {geom_file_path} not found. Creating placeholder..."
        )
        return None

    try:
        stage = Usd.Stage.Open(geom_file_path)
        if stage:
            print(f"Successfully read existing geometry file: {geom_file_path}")
            return stage
    except Exception as e:
        print(f"Error reading geometry file: {e}")

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


def assemble_chessboard_asset(base_path="./CHESSBOARD"):
    """装配完整的棋盘资产"""
    print("Starting Chessboard USD Asset Assembly...")
    print(f"Base path: {base_path}")

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
    main_file = os.path.join(base_path, "Chessboard.usd")
    ensure_directory(main_file)
    create_chessboard_main(main_file)

    # 2. 创建 payload 文件
    payload_file = os.path.join(base_path, "Chessboard_payload.usd")
    create_chessboard_payload(payload_file)

    # 3. 创建外观文件
    look_file = os.path.join(base_path, "Chessboard_look.usd")
    create_chessboard_look(look_file, base_path)

    print("\n=== Assembly Summary ===")
    print(f"✓ Created: {main_file}")
    print(f"✓ Created: {payload_file}")
    print(f"✓ Created: {look_file}")

    if geom_stage:
        print(f"✓ Found existing: {geom_file}")
    else:
        print(f"⚠ Missing: {geom_file}")

    if material_exists:
        print(f"✓ Found existing: {material_file}")
    else:
        print(f"⚠ Missing: {material_file}")

    if textures_exist:
        print("✓ All texture files found")
    else:
        print("⚠ Some texture files missing")

    print("\n=== Asset Structure ===")
    print(f"{base_path}/")
    print("├── Chessboard.usd          (✓ Generated - Main entry point)")
    print("├── Chessboard_payload.usd  (✓ Generated - Payload file)")
    print("├── Chessboard_look.usd     (✓ Generated - Look/shading)")
    print("├── Chessboard_geom.usd     (Existing geometry)")
    print("├── Chessboard_mat.mtlx     (Existing material)")
    print("└── tex/")
    print("    ├── chessboard_base_color.jpg")
    print("    ├── chessboard_metallic.jpg")
    print("    ├── chessboard_normal.jpg")
    print("    └── chessboard_roughness.jpg")

    print(f"\nAsset assembly complete! Main USD file: {main_file}")
    return main_file


def test_load_assembled_asset(main_file):
    """测试加载装配好的资产"""
    print(f"\n=== Testing assembled asset ===")
    try:
        stage = Usd.Stage.Open(main_file)
        if stage:
            print(f"✓ Successfully opened: {main_file}")

            # 检查默认 prim
            default_prim = stage.GetDefaultPrim()
            if default_prim:
                print(f"✓ Default prim: {default_prim.GetPath()}")

                # 检查 payload 是否正确加载
                if default_prim.HasPayload():
                    print("✓ Payload found")

                # 加载所有 payload 来测试完整装配
                stage.LoadAndUnload(Usd.LoadWithDescendants)
                print("✓ Payloads loaded successfully")

            else:
                print("⚠ No default prim found")

        else:
            print(f"✗ Failed to open: {main_file}")

    except Exception as e:
        print(f"✗ Error testing asset: {e}")


if __name__ == "__main__":
    # 设置基础路径
    base_path = "./CHESSBOARD"

    try:
        # 装配资产
        main_file = assemble_chessboard_asset(base_path)

        # 测试装配结果
        test_load_assembled_asset(main_file)

        print("\n🎉 Chessboard USD asset assembly completed successfully!")
        print(f"📁 Asset location: {os.path.abspath(main_file)}")

    except Exception as e:
        print(f"❌ Error during assembly: {e}")
        import traceback

        traceback.print_exc()
        import traceback

        traceback.print_exc()
