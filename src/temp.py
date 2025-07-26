from pxr import Sdf, Usd, UsdGeom, UsdShade

# 创建一个新的Stage
stage = Usd.Stage.CreateNew("Chessboard.usda")

# 设置Stage的元信息
stage.SetDefaultPrim(stage.DefinePrim("/Chessboard", "Xform"))
stage.SetMetadata("metersPerUnit", 1.0)
stage.SetMetadata("upAxis", "Y")

# === 创建 Materials Scope ===
materials_scope = stage.OverridePrim("/Chessboard/Materials")
materials_scope.GetReferences().AddReference(
    "./Chessboard_mat.mtlx",  # 外部MaterialX文件
    "/MaterialX/Materials",  # 该文件中要引用的路径
)

# === 创建 Geom/Render，并绑定材质 ===
render_prim = stage.OverridePrim("/Chessboard/Geom/Render")
render_prim.ApplyAPI(UsdShade.MaterialBindingAPI)

# 创建绑定关系：指向 Chessboard/Materials/M_Chessboard
binding_rel = render_prim.CreateRelationship("material:binding")
binding_rel.SetTargets([Sdf.Path("/Chessboard/Materials/M_Chessboard")])

# 保存文件
stage.GetRootLayer().Save()
