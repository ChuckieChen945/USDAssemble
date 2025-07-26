[![Open in Dev Containers](https://img.shields.io/static/v1?label=Dev%20Containers&message=Open&color=blue&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0iI2ZmZiIgZD0iTTE3IDE2VjdsLTYgNU0yIDlWOGwxLTFoMWw0IDMgOC04aDFsNCAyIDEgMXYxNGwtMSAxLTQgMmgtMWwtOC04LTQgM0gzbC0xLTF2LTFsMy0zIi8+PC9zdmc+)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/ChuckieChen945/USDAssemble) [![Open in GitHub Codespaces](https://img.shields.io/static/v1?label=GitHub%20Codespaces&message=Open&color=blue&logo=github)](https://github.com/codespaces/new/ChuckieChen945/USDAssemble)

# USDAssemble

使用 Pixar OpenUSD API 和 MaterialX API 编写的 USD 资产自动化装配工具。

## 🎯 功能特点

- **🎨 基于模板**: 使用预定义模板确保一致的USD文件结构
- **🔧 智能替换**: 使用Python string.Template进行动态内容替换
- **🖼️ 纹理检测**: 自动检测并连接纹理文件到MaterialX节点
- **🏗️ 多层级支持**: 支持 Assembly、Component、Subcomponent 等 USD 概念
- **🖥️ 命令行接口**: 基于 Typer 的简洁命令行工具
- **📦 现代化**: 使用 uv 进行包管理

## 📁 模板系统

项目使用模板驱动的方式生成USD文件，模板位于 `src/template/` 目录：

```
src/template/
└── {$assembly_name}/
    ├── {$assembly_name}.usda                    # Assembly主文件模板
    └── components/
        └── {$component_name}/                   # 组件模板目录
            ├── {$component_name}.usd            # 组件主文件模板
            ├── {$component_name}_payload.usd    # Payload文件模板
            ├── {$component_name}_look.usd       # Look文件模板
            └── {$component_name}_mat.mtlx       # MaterialX文件模板
```

### 模板变量

- `{$assembly_name}`: Assembly名称（通常为项目目录名）
- `{$component_name}`: Component名称（组件目录名）

### 模板处理流程

1. **读取模板**: 从 `src/template/` 读取对应的模板文件
2. **变量替换**: 使用 `string.Template` 进行名称和路径替换
3. **内容修改**: 使用 USD API 和 MaterialX API 修改具体内容
4. **纹理连接**: 自动检测纹理文件并连接到MaterialX节点
5. **文件输出**: 生成最终的USD和MaterialX文件

## 🚀 安装

```bash
# 安装依赖（需要先安装 USD 和 MaterialX）
conda install -c conda-forge usd-core materialx

# 使用 uv 安装项目依赖
uv sync

# 或使用 pip
pip install -e .
```

## 💻 命令行使用

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
CHESS_SET/                               # Assembly目录
│  CHESS_SET.usda                        # ← 将被生成（Assembly主文件）
│
└─components/
    ├─Bishop/                            # Component目录
    │  │  Bishop.usd                     # ← 将被生成（组件主文件）
    │  │  Bishop_geom.usd                # ← 用户提供（几何体文件）
    │  │  Bishop_look.usd                # ← 将被生成（外观文件）
    │  │  Bishop_mat.mtlx                # ← 将被生成（MaterialX文件）
    │  │  Bishop_payload.usd             # ← 将被生成（Payload文件）
    │  │
    │  └─textures/                       # 纹理目录
    │          bishop_base_color.jpg      # ← 用户提供
    │          bishop_metallic.jpg        # ← 用户提供
    │          bishop_normal.jpg          # ← 用户提供
    │          bishop_roughness.jpg       # ← 用户提供
    │
    ├─Chessboard/
    │  │  Chessboard.usd                 # ← 将被生成
    │  │  Chessboard_geom.usd            # ← 用户提供
    │  │  Chessboard_look.usd            # ← 将被生成
    │  │  Chessboard_mat.mtlx            # ← 将被生成
    │  │  Chessboard_payload.usd         # ← 将被生成
    │  │
    │  └─textures/
    │          chessboard_base_color.jpg  # ← 用户提供
    │          chessboard_metallic.jpg    # ← 用户提供
    │          chessboard_normal.jpg      # ← 用户提供
    │          chessboard_roughness.jpg   # ← 用户提供
    │
    └─...更多棋子组件
```

## 🖼️ 纹理文件自动检测

工具会自动扫描 `textures/` 或 `tex/` 目录，检测以下类型的纹理文件：

| 纹理类型         | 检测模式         | MaterialX节点类型 |
| ---------------- | ---------------- | ----------------- |
| **Base Color**   | `*base_color*`   | `color3`          |
| **Metallic**     | `*metallic*`     | `float`           |
| **Roughness**    | `*roughness*`    | `float`           |
| **Normal**       | `*normal*`       | `vector3`         |
| **Specular**     | `*specular*`     | `float`           |
| **Diffuse**      | `*diffuse*`      | `color3`          |
| **Emissive**     | `*emissive*`     | `color3`          |
| **Displacement** | `*displacement*` | `float`           |
| **Opacity**      | `*opacity*`      | `float`           |
| **Occlusion**    | `*occlusion*`    | `float`           |

支持的文件格式：`.jpg`, `.png`, `.exr`

## 📄 生成的文件内容示例

### Assembly 主文件 (CHESS_SET.usda)
```usda
#usda 1.0
(
    defaultPrim = "CHESS_SET"
    doc = "Generated from template"
    metersPerUnit = 1
    upAxis = "Y"
)

class "__class__"
{
    class "CHESS_SET"
    {
    }
}

def Xform "CHESS_SET" (
    kind = "assembly"
    prepend inherits = </__class__/CHESS_SET>
)
{
    def Xform "Chessboard" (
        add references = @./components/Chessboard/Chessboard.usd@
    )
    {
    }
    
    def Xform "Bishop" (
        add references = @./components/Bishop/Bishop.usd@
    )
    {
    }
}
```

### Component 主文件 (Chessboard.usd)
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

### MaterialX 文件 (Chessboard_mat.mtlx)
```xml
<?xml version="1.0"?>
<materialx version="1.38" colorspace="lin_rec709">
  <nodegraph name="NG_Chessboard">
    <image name="base_color" type="color3">
      <input name="file" type="filename" value="textures/chessboard_base_color.jpg" colorspace="srgb_texture" />
    </image>
    <image name="metallic" type="float">
      <input name="file" type="filename" value="textures/chessboard_metallic.jpg" />
    </image>
    <image name="roughness" type="float">
      <input name="file" type="filename" value="textures/chessboard_roughness.jpg" />
    </image>
    <image name="normal" type="vector3">
      <input name="file" type="filename" value="textures/chessboard_normal.jpg" />
    </image>
    <normalmap name="mtlxnormalmap12" type="vector3">
      <input name="in" type="vector3" nodename="normal" />
    </normalmap>
    <output name="base_color_output" type="color3" nodename="base_color" />
    <output name="metalness_output" type="float" nodename="metallic" />
    <output name="roughness_output" type="float" nodename="roughness" />
    <output name="normal_output" type="vector3" nodename="mtlxnormalmap12" />
  </nodegraph>

  <open_pbr_surface name="Chessboard" type="surfaceshader">
    <input name="base_color" type="color3" nodegraph="NG_Chessboard" output="base_color_output" />
    <input name="base_metalness" type="float" nodegraph="NG_Chessboard" output="metalness_output" />
    <input name="specular_roughness" type="float" nodegraph="NG_Chessboard" output="roughness_output" />
    <input name="geometry_normal" type="vector3" nodegraph="NG_Chessboard" output="normal_output" />
  </open_pbr_surface>

  <surfacematerial name="M_Chessboard" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="Chessboard" />
  </surfacematerial>
</materialx>
```

## 🧪 测试

运行测试脚本验证模板系统：

```bash
python test_templates.py
```

测试将验证：
- 模板文件存在性
- 纹理检测功能
- 组件装配流程
- Assembly装配流程

## 🛠️ 开发

```bash
# 安装开发依赖
uv sync --dev

# 代码格式化
ruff format src/

# 代码检查
ruff check src/

# 类型检查
mypy src/
```

## 📚 技术架构

### 核心模块

- **`cli.py`**: 命令行接口和主要装配逻辑
- **`mtlx/materialx.py`**: MaterialX文件处理和纹理连接
- **`template/`**: USD文件模板目录

### 处理流程

1. **扫描阶段**: 扫描目录结构，检测组件和纹理文件
2. **模板阶段**: 读取模板文件，进行变量替换
3. **修改阶段**: 使用USD/MaterialX API修改具体内容
4. **输出阶段**: 生成最终的USD和MaterialX文件

### 关键特性

- **模板驱动**: 确保生成文件的一致性和正确性
- **智能检测**: 自动识别目录类型和纹理文件
- **API集成**: 深度集成USD和MaterialX API
- **类型安全**: 全面的类型注解和错误处理

## 📋 TODO

- [ ] 支持更多纹理类型和格式
- [ ] 添加extentsHint自动计算
- [ ] 实现嵌套组件的递归处理
- [ ] 添加自定义模板支持
- [ ] 性能优化和并行处理

## �� 许可证

MIT License
