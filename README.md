[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTE3IDE2VjdsLTYgNU0yIDlWOGwxLTFoMWw0IDMgOC04aDFsNCAyIDEgMXYxNGwtMSAxLTQgMmgtMWwtOC04LTQgM0gzbC0xLTF2LTFsMy0zIi8+PC9zdmc+)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/ChuckieChen945/USDAssemble) [![Open in GitHub Codespaces](https://img.shields.io/static/v1?label=GitHub%20Codespaces&message=Open&color=blue&logo=github)](https://github.com/codespaces/new/ChuckieChen945/USDAssemble)

# USDAssemble

使用 Pixar OpenUSD API 和 MaterialX API 编写的 USD 资产自动化装配工具。

## 功能特点

- 🎯 **自动装配**: 根据目录结构自动生成 USD 文件
- 🎨 **MaterialX 支持**: 自动检测纹理文件并生成 MaterialX 材质
- 🏗️ **多层级支持**: 支持 Assembly、Component、Subcomponent 等 USD 概念
- 🖥️ **命令行接口**: 基于 Typer 的简洁命令行工具
- 🌐 **REST API**: 基于 FastAPI 的 Web 接口
- 📦 **现代化**: 使用 uv 进行包管理

## 安装

```bash
# 使用 uv 安装依赖
uv sync

# 或使用 pip
pip install -e .
```

## 命令行使用

### 主命令

```bash
# 自动检测当前目录类型并执行装配
usdassemble assemble

# 装配 Assembly（包含多个 Component）
usdassemble assembly ./CHESS_SET

# 装配单个 Component
usdassemble component ./CHESS_SET/components/Chessboard

# 装配 Subcomponent
usdassemble subcomponent ./some_subcomponent
```

### 目录结构示例

```
CHESS_SET/
│  chess_set.usda                    # ← 将被生成
│
└─components/
    ├─Bishop/
    │  │  Bishop.usda                # ← 将被生成
    │  │  Bishop_geom.usd            # ← 用户提供
    │  │  Bishop_look.usda           # ← 将被生成
    │  │  Bishop_mat.mtlx            # ← 将被生成
    │  │  Bishop_payload.usda        # ← 将被生成
    │  │
    │  └─textures/
    │          bishop_black_base_color.jpg    # ← 用户提供
    │          bishop_black_normal.jpg        # ← 用户提供
    │          bishop_black_roughness.jpg     # ← 用户提供
    │          bishop_shared_metallic.jpg     # ← 用户提供
    │          ...
    │
    ├─Chessboard/
    │  │  Chessboard.usda            # ← 将被生成
    │  │  Chessboard_geom.usd        # ← 用户提供
    │  │  Chessboard_look.usda       # ← 将被生成
    │  │  Chessboard_mat.mtlx        # ← 将被生成
    │  │  Chessboard_payload.usda    # ← 将被生成
    │  │
    │  └─textures/
    │          chessboard_base_color.jpg      # ← 用户提供
    │          chessboard_metallic.jpg        # ← 用户提供
    │          chessboard_normal.jpg          # ← 用户提供
    │          chessboard_roughness.jpg       # ← 用户提供
    │
    └─...更多棋子组件
```

## REST API 使用

### 启动服务器

```bash
# 开发模式
uvicorn src.usdassemble.api:app --reload --port 8000

# 生产模式
uvicorn src.usdassemble.api:app --host 0.0.0.0 --port 8000
```

### API 端点

#### 1. 获取 API 信息
```http
GET /
```

#### 2. 装配 Assembly
```http
POST /assemble/assembly
Content-Type: application/json

{
    "base_path": "/path/to/CHESS_SET",
    "assembly_name": "chess_set"  // 可选，默认为目录名
}
```

#### 3. 装配 Component
```http
POST /assemble/component
Content-Type: application/json

{
    "base_path": "/path/to/component",
    "component_name": "Chessboard"  // 可选，默认为目录名
}
```

#### 4. 装配 Subcomponent
```http
POST /assemble/subcomponent
Content-Type: application/json

{
    "base_path": "/path/to/subcomponent",
    "subcomponent_name": "SubPart"  // 可选，默认为目录名
}
```

#### 5. 扫描组件
```http
GET /scan/components?base_path=/path/to/assembly
```

#### 6. 获取组件信息
```http
GET /info/component?component_path=/path/to/component
```

#### 7. 下载生成的文件
```http
# 下载 Assembly 文件
GET /download/assembly?base_path=/path/to/assembly

# 下载 Component 文件
GET /download/component?base_path=/path/to/component&component_name=Chessboard
GET /download/payload?base_path=/path/to/component&component_name=Chessboard
GET /download/look?base_path=/path/to/component&component_name=Chessboard
GET /download/material?base_path=/path/to/component&component_name=Chessboard
```

#### 8. 健康检查
```http
GET /health
```

### API 响应示例

#### 装配响应
```json
{
    "success": true,
    "message": "Assembly chess_set 装配完成",
    "generated_files": [
        "components/Chessboard/Chessboard.usda",
        "components/Chessboard/Chessboard_payload.usda",
        "components/Chessboard/Chessboard_look.usda",
        "components/Chessboard/Chessboard_mat.mtlx",
        "chess_set.usda"
    ],
    "components": ["Chessboard", "Bishop", "King", ...]
}
```

#### 组件信息响应
```json
{
    "name": "Chessboard",
    "path": "/path/to/Chessboard",
    "has_geometry": true,
    "texture_files": {
        "base_color": "textures/chessboard_base_color.jpg",
        "metallic": "textures/chessboard_metallic.jpg",
        "roughness": "textures/chessboard_roughness.jpg",
        "normal": "textures/chessboard_normal.jpg"
    },
    "generated_files": [
        "Chessboard.usda",
        "Chessboard_payload.usda",
        "Chessboard_look.usda",
        "Chessboard_mat.mtlx"
    ]
}
```

## 生成的文件内容

### 主入口文件 (Component.usda)
```usda
#usda 1.0
(
    defaultPrim = "Chessboard"
    metersPerUnit = 1
    upAxis = "Y"
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
        asset identifier = @./Chessboard.usda@
        string name = "Chessboard"
    }
    prepend inherits = </__class__/Chessboard>
    kind = "component"
    payload = @./Chessboard_payload.usda@</Chessboard>
)
{
    float3[] extentsHint = [(-0.35270807, 0, -0.35270807), (0.35270807, 0.01851505, 0.35270807)]
}
```

### Payload 文件 (Component_payload.usda)
```usda
#usda 1.0
(
    defaultPrim = "Chessboard"
    metersPerUnit = 1
    subLayers = [
        @./Chessboard_look.usda@,
        @./Chessboard_geom.usd@
    ]
    upAxis = "Y"
)
```

### Look 文件 (Component_look.usda)
```usda
#usda 1.0
(
    defaultPrim = "Chessboard"
    metersPerUnit = 1
    upAxis = "Y"
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

### MaterialX 文件 (Component_mat.mtlx)
```xml
<?xml version="1.0"?>
<materialx version="1.38" colorspace="lin_rec709">
  <nodegraph name="NG_Chessboard">
    <image name="base_color_image" type="color3">
      <input name="file" type="filename" value="textures/chessboard_base_color.jpg" colorspace="srgb_texture" />
    </image>
    <image name="metallic_image" type="float">
      <input name="file" type="filename" value="textures/chessboard_metallic.jpg" />
    </image>
    <image name="roughness_image" type="float">
      <input name="file" type="filename" value="textures/chessboard_roughness.jpg" />
    </image>
    <image name="normal_image" type="vector3">
      <input name="file" type="filename" value="textures/chessboard_normal.jpg" />
    </image>
    <normalmap name="normal_map" type="vector3">
      <input name="in" type="vector3" nodename="normal_image" />
    </normalmap>
    <output name="base_color_output" type="color3" nodename="base_color_image" />
    <output name="metalness_output" type="float" nodename="metallic_image" />
    <output name="roughness_output" type="float" nodename="roughness_image" />
    <output name="normal_output" type="vector3" nodename="normal_map" />
  </nodegraph>

  <standard_surface name="Chessboard" type="surfaceshader">
    <input name="base_color" type="color3" nodegraph="NG_Chessboard" output="base_color_output" />
    <input name="metalness" type="float" nodegraph="NG_Chessboard" output="metalness_output" />
    <input name="specular_roughness" type="float" nodegraph="NG_Chessboard" output="roughness_output" />
    <input name="normal" type="vector3" nodegraph="NG_Chessboard" output="normal_output" />
  </standard_surface>

  <surfacematerial name="M_Chessboard" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="Chessboard" />
  </surfacematerial>
</materialx>
```

## 纹理文件自动检测

工具会自动扫描 `textures/` 或 `tex/` 目录，检测以下类型的纹理文件：

- **Base Color**: `*base_color*`, `*diffuse*`, `*albedo*`, `*color*`
- **Metallic**: `*metallic*`, `*metal*`
- **Roughness**: `*roughness*`, `*rough*`
- **Normal**: `*normal*`, `*norm*`
- **Specular**: `*specular*`, `*spec*`
- **Scattering**: `*scattering*`, `*sss*`

支持的文件格式：`.jpg`, `.png`, `.exr`

## 开发

```bash
# 安装开发依赖
uv sync --dev

# 运行测试
pytest tests/

# 代码格式化
ruff format src/

# 代码检查
ruff check src/
```

## 许可证

MIT License
