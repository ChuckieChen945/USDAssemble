from pxr import Sdf, Usd, UsdShade


import os


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
