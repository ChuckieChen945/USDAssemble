根据以下描述，完善本项目：

用 python 结合 pixar usd api （@<https://openusd.org/dev/api/）> 和 materialx api 写一个名为 USDAssemble 的项目用于自动化装配 usd 资产，利用 typer 写命令行、fastapi 写对外接口，用 uv 管理项目包。项目包含一个 assemble 主命令和 assembly、 compoment 、subcomponent 及其它辅助子命令，这些子命令对应 usd 中的 assembly、 compoment 、subcomponent 等概念。运行这些命令时，命令根据传入的目录参数（默认为当目录），扫描目录结构，示例目录结构如下：

CHESS_SET/
│  chess_set.usda （尚不存在，待装配生成）
│
└─components
    ├─Bishop
    │  │  Bishop.usda （尚不存在，待装配生成）
    │  │  Bishop_geom.usd （已存在，由用户放置）
    │  │  Bishop_look.usda （尚不存在，待装配生成）
    │  │  Bishop_mat.mtlx （尚不存在，待复制生成）
    │  │  Bishop_payload.usda （尚不存在，待装配生成）
    │  │
    │  └─textures
    │          bishop_black_base_color.jpg（已存在，由用户放置）
    │          bishop_black_normal.jpg（已存在，由用户放置）
    │          bishop_black_roughness.jpg（已存在，由用户放置）
    │          bishop_shared_metallic.jpg（已存在，由用户放置）
    │          bishop_white_base_color.jpg（已存在，由用户放置）
    │          bishop_white_normal.jpg（已存在，由用户放置）
    │          bishop_white_roughness.jpg（已存在，由用户放置）
    │
    ├─Chessboard
    │  │  Chessboard.usda （尚不存在，待装配生成）
    │  │  Chessboard_geom.usd（已存在，由用户放置）
    │  │  Chessboard_look.usda （尚不存在，待装配生成）
    │  │  Chessboard_mat.mtlx（尚不存在，待复制生成）
    │  │  Chessboard_payload.usda （尚不存在，待装配生成）
    │  │
    │  └─textures
    │          chessboard_base_color.jpg（已存在，由用户放置）
    │          chessboard_metallic.jpg（已存在，由用户放置）
    │          chessboard_normal.jpg（已存在，由用户放置）
    │          chessboard_roughness.jpg（已存在，由用户放置）
    │
    ├─King
    │  │  King.usda （尚不存在，待装配生成）
    │  │  King_geom.usd（已存在，由用户放置）
    │  │  King_look.usda （尚不存在，待装配生成）
    │  │  King_mat.mtlx（尚不存在，待复制生成）
    │  │  King_payload.usda （尚不存在，待装配生成）
    │  │
    │  └─textures
    │          king_black_base_color.jpg（已存在，由用户放置）
    │          king_black_normal.jpg（已存在，由用户放置）
    │          king_black_roughness.jpg（已存在，由用户放置）
    │          king_shared_metallic.jpg（已存在，由用户放置）
    │          king_shared_scattering.jpg（已存在，由用户放置）
    │          king_white_base_color.jpg（已存在，由用户放置）
    │          king_white_normal.jpg（已存在，由用户放置）
    │          king_white_roughness.jpg（已存在，由用户放置）
    │
    ├─Knight
    │  │  Knight.usda （尚不存在，待装配生成）
    │  │  Knight_geom.usd（已存在，由用户放置）
    │  │  Knight_look.usda （尚不存在，待装配生成）
    │  │  Knight_mat.mtlx（尚不存在，待复制生成）
    │  │  Knight_payload.usda （尚不存在，待装配生成）
    │  │
    │  └─textures
    │          knight_black_base_color.jpg（已存在，由用户放置）
    │          knight_black_roughness.jpg（已存在，由用户放置）
    │          knight_shared_normal.jpg（已存在，由用户放置）
    │          knight_white_base_color.jpg（已存在，由用户放置）
    │          knight_white_roughness.jpg（已存在，由用户放置）
    │
    ├─Pawn
    │  │  Pawn.usda （尚不存在，待装配生成）
    │  │  Pawn_geom.usd（已存在，由用户放置）
    │  │  Pawn_look.usda （尚不存在，待装配生成）
    │  │  Pawn_mat.mtlx（尚不存在，待复制生成）
    │  │  Pawn_payload.usda （尚不存在，待装配生成）
    │  │
    │  └─textures
    │          pawn_black_base_color.jpg（已存在，由用户放置）
    │          pawn_shared_metallic.jpg（已存在，由用户放置）
    │          pawn_shared_normal.jpg（已存在，由用户放置）
    │          pawn_shared_roughness.jpg（已存在，由用户放置）
    │          pawn_white_base_color.jpg（已存在，由用户放置）
    │
    ├─Queen
    │  │  Queen.usda （尚不存在，待装配生成）
    │  │  Queen_geom.usd（已存在，由用户放置）
    │  │  Queen_look.usda （尚不存在，待装配生成）
    │  │  Queen_mat.mtlx（尚不存在，待复制生成）
    │  │  Queen_payload.usda （尚不存在，待装配生成）
    │  │
    │  └─textures
    │          queen_black_base_color.jpg（已存在，由用户放置）
    │          queen_black_normal.jpg（已存在，由用户放置）
    │          queen_black_roughness.jpg（已存在，由用户放置）
    │          queen_shared_metallic.jpg（已存在，由用户放置）
    │          queen_shared_scattering.jpg（已存在，由用户放置）
    │          queen_white_base_color.jpg（已存在，由用户放置）
    │          queen_white_normal.jpg（已存在，由用户放置）
    │          queen_white_roughness.jpg（已存在，由用户放置）
    │
    └─Rook
        │  Rook.usda （尚不存在，待装配生成）
        │  Rook_geom.usd（已存在，由用户放置）
        │  Rook_look.usda （尚不存在，待装配生成）
        │  Rook_mat.mtlx（尚不存在，待复制生成）
        │  Rook_payload.usda （尚不存在，待装配生成）
        │
        └─textures
                rook_black_base_color.jpg（已存在，由用户放置）
                rook_shared_metallic.jpg（已存在，由用户放置）
                rook_shared_normal.jpg（已存在，由用户放置）
                rook_shared_roughness.jpg（已存在，由用户放置）
                rook_white_base_color.jpg（已存在，由用户放置）

1. 假设用户输入 assemble assembly 命令，提取当前目录的名称作为 usd assembly 的名称（比如 chess_set），在当前目录下创建一个 chess_set.usda 作为整个资产的入口，在 chess_set.usda 中以 references 的方式引用当前子目录下 components 中的资产。当前子目录下的 components/ 文件夹即为 该 assembly 的组成 components（如 Rook、 Pawn、 Queen、 King、 Knight、 Bishop、 Chessboard 等），对各 component 调用 assemble component 命令。
2. 对每个 component，例如 Chessboard，生成 入口文件 Chessboard.usda ，在 Chessboard.usda 中以 payload 的方式引用 Chessboard_payload.usda。生成 Chessboard_payload.usda，Chessboard_payload.usda 中包含两个 sublayer，分别为 Chessboard_look.usda 和 Chessboard_geom.usd。生成 Chessboard_look.usda 文件，引用 Chessboard_mat.mtlx 中的材质。复制一个自带的 open_pbr.mtlx 模板文件为 Chessboard_mat.mtlx，读取 Chessboard/textures/中的材质贴图，根据贴图名称用 materialx api 连接各贴图。
3. 根据 usd 的定义，component 中还能有 component 文件夹或 subsocmponent 文件夹，项目应能递归处理好这种嵌套
4. 仿照 cli，提供 api 接口

装配出的 usd 文件内容参考：

``` Chessboard.usda
#usda 1.0
(
    defaultPrim = "Chessboard"
    metersPerUnit = 1
    upAxis = "Z"
)

class "__class__"
{
    class "Chessboard"
    {
    }
}

def Xform "Chessboard" (
    prepend apiSchemas = ["GeomModelAPI"]
    assetInfo = {
        asset identifier = @./Chessboard.usd@
        string name = "Chessboard"
    }
    prepend inherits = </__class__/Chessboard>
    kind = "component"
    payload = @./Chessboard_payload.usd@</Chessboard>
)
{
    float3[] extentsHint = [(-0.35270807, 0, -0.35270807), (0.35270807, 0.01851505, 0.35270807)]
}
```

```Chessboard_payload.usd
#usda 1.0
(
    defaultPrim = "Chessboard"
    metersPerUnit = 1
    subLayers = [
        @./Chessboard_look.usd@,
        @./Chessboard_geom.usd@
    ]
    upAxis = "Z"
)
```

```Chessboard_look.usd

#usda 1.0
(
    defaultPrim = "Chessboard"
    metersPerUnit = 1
    upAxis = "Z"
)

over "Chessboard"
{
    def Scope "Materials" (
        prepend references = @./Chessboard_mat.mtlx@</MaterialX/Materials>
    )
    {
    }

    over "Geom"
    {
        over "Render" (
            apiSchemas = ["MaterialBindingAPI"]
        )
        {
            rel material:binding = </Chessboard/Materials/M_Chessboard>
        }
    }
}

```

```Chessboard_geom.usd
#usda 1.0
(
    defaultPrim = "Chessboard"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "Chessboard" (
    kind = "component"
)
{
    def Scope "Geom"
    {
        def Mesh "Render"
        {
            float3[] extent = [(-0.35270807, 0, -0.35270807), (0.35270807, 0.01851505, 0.35270807)]
            int[] faceVertexCounts = []
            int[] faceVertexIndices = []
            uniform token orientation = "leftHanded"
            point3f[] points = []
                interpolation = "vertex"
            )
            texCoord2f[] primvars:st = [
                interpolation = "faceVarying"
            )
            int[] primvars:st:indices = None
        }
    }
}
```

``` Chessboard_mat.mtlx
<?xml version="1.0"?>
<materialx version="1.38" colorspace="lin_rec709" >

  <nodegraph name="NG_ChessBoard">
    <image name="mtlximage13" type="color3">
      <input name="file" type="filename" value="tex/chessboard_base_color.jpg" colorspace="srgb_texture" />
    </image>
    <image name="mtlximage16" type="float">
      <input name="file" type="filename" value="tex/chessboard_metallic.jpg" />
    </image>
    <image name="mtlximage17" type="float">
      <input name="file" type="filename" value="tex/chessboard_roughness.jpg" />
    </image>
    <image name="mtlximage15" type="vector3">
      <input name="file" type="filename" value="tex/chessboard_normal.jpg" />
    </image>
    <normalmap name="mtlxnormalmap12" type="vector3">
      <input name="in" type="vector3" nodename="mtlximage15" />
    </normalmap>
    <output name="base_color_output" type="color3" nodename="mtlximage13" />
    <output name="metalness_output" type="float" nodename="mtlximage16" />
    <output name="roughness_output" type="float" nodename="mtlximage17" />
    <output name="normal_output" type="vector3" nodename="mtlxnormalmap12" />
  </nodegraph>

  <standard_surface name="Chessboard" type="surfaceshader">
    <input name="base_color" type="color3" nodegraph="NG_ChessBoard" output="base_color_output" />
    <input name="metalness" type="float" nodegraph="NG_ChessBoard" output="metalness_output" />
    <input name="specular_roughness" type="float" nodegraph="NG_ChessBoard" output="roughness_output" />
    <input name="normal" type="vector3" nodegraph="NG_ChessBoard" output="normal_output" />
  </standard_surface>

  <surfacematerial name="M_Chessboard" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="Chessboard" />
  </surfacematerial>

</materialx>

```

```open_pbr.mtlx
<?xml version="1.0"?>
<materialx version="1.38" colorspace="lin_rec709" >

  <nodegraph name="compound1">
    <image name="mtlximage13" type="color3" />
    <image name="mtlximage16" type="float" />
    <image name="mtlximage17" type="float" />
    <image name="mtlximage15" type="vector3" />
    <normalmap name="mtlxnormalmap12" type="vector3">
      <input name="in" type="vector3" nodename="mtlximage15" />
    </normalmap>
    <output name="base_color_output" type="color3" nodename="mtlximage13" />
    <output name="metalness_output" type="float" nodename="mtlximage16" />
    <output name="roughness_output" type="float" nodename="mtlximage17" />
    <output name="normal_output" type="vector3" nodename="mtlxnormalmap12" />
  </nodegraph>

  <open_pbr_surface name="open_pbr_surface1" type="surfaceshader">
    <input name="base_color" type="color3" nodegraph="compound1" output="base_color_output" />
    <input name="base_metalness" type="float" nodegraph="compound1" output="metalness_output" />
    <input name="specular_roughness" type="float" nodegraph="compound1" output="roughness_output" />
    <input name="geometry_normal" type="vector3" nodegraph="compound1" output="normal_output" />
  </open_pbr_surface>

  <surfacematerial name="OpenPBR_Surface1" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="open_pbr_surface1" />
  </surfacematerial>

</materialx>

```
