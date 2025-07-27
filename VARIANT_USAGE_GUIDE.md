# USD 变体功能使用指南

## 快速开始

### 1. 目录结构设置

```
my_asset/
├── components/                    # 或 subcomponents/
│   └── chess_piece/
│       ├── chess_piece_geom.usd   # 必需：几何体文件
│       └── textures/
│           ├── wood/              # 变体1：木质
│           │   ├── chess_piece_base_color.jpg
│           │   ├── chess_piece_roughness.jpg
│           │   └── chess_piece_normal.jpg
│           ├── metal/             # 变体2：金属
│           │   ├── chess_piece_base_color.jpg
│           │   ├── chess_piece_metalness.jpg
│           │   ├── chess_piece_roughness.jpg
│           │   └── chess_piece_normal.jpg
│           └── stone/             # 变体3：石质
│               ├── chess_piece_base_color.jpg
│               └── chess_piece_roughness.jpg
```

### 2. 运行装配

```bash
# 装配支持变体的资产
python -m src.main assemble ./my_asset

# 输出示例:
# 扫描到的component
# ┌─────────────┬──────┬───────────┬──────┬──────┐
# │ 组件名      │ 状态 │ 类型      │ 变体数│ 纹理数│
# ├─────────────┼──────┼───────────┼──────┼──────┤
# │ chess_piece │ ✓ 有效│ component │  3   │  8   │
# └─────────────┴──────┴───────────┴──────┴──────┘
# 
# ✓ 找到 1 个有效component
# ✓ 其中 1 个组件包含总计 3 个变体
# ✓ Assembly 装配完成! 支持 3 个材质变体
```

### 3. 生成的文件

```
my_asset/
├── my_asset.usda                  # 主装配文件
└── components/
    └── chess_piece/
        ├── chess_piece.usd        # 组件主文件（含变体集）
        ├── chess_piece_mat.mtlx   # MaterialX 文件（含所有变体）
        ├── chess_piece_look.usd   # 外观文件
        ├── chess_piece_payload.usd # 载荷文件
        ├── chess_piece_geom.usd   # 几何体文件（用户提供）
        └── textures/              # 纹理目录（用户提供）
```

## 支持的纹理类型

```python
# 基础PBR纹理
base_color    # 漫反射/反照率：*base_color*, *basecolor*, *diffuse*, *albedo*
metalness     # 金属度：*metalness*, *metallic*, *metal*
roughness     # 粗糙度：*roughness*, *rough*
normal        # 法线：*normal*, *norm*, *bump*

# 高级纹理
specular      # 镜面反射：*specular*, *spec*
emissive      # 自发光：*emissive*, *emit*, *glow*
displacement  # 置换：*displacement*, *disp*, *height*
opacity       # 不透明度：*opacity*, *alpha*, *transparency*
occlusion     # 环境光遮蔽：*occlusion*, *ao*, *ambient*

# 其他类型
scattering, reflection, refraction, sheen, transmission
```

## 支持的文件格式

- `.jpg`, `.png` - 标准图像格式
- `.exr` - 高动态范围
- `.tif`, `.tiff` - 高质量图像

## 变体命名规则

1. **变体目录名** 将成为 USD 中的变体名称
2. **纹理文件** 必须包含组件名前缀
3. **变体切换** 通过 USD 的变体选择器实现

示例：
```
textures/wood/chess_piece_base_color.jpg
         ^^^^  ^^^^^^^^^^^
         变体名  组件名前缀（必需）
```

## 程序化使用

```python
from src.usdassemble.utils import scan_component_info, ComponentType
from src.mtlx.materialx import create_materialx_from_component_info

# 扫描组件
component_info = scan_component_info(component_path, ComponentType.COMPONENT)

# 检查是否有变体
if component_info.has_variants:
    print(f"发现 {len(component_info.variants)} 个变体:")
    for variant in component_info.variants:
        print(f"  - {variant.name}: {len(variant.textures)} 个纹理")

# 创建 MaterialX 文件
create_materialx_from_component_info(component_info, "output.mtlx")
```

## 故障排除

### 常见问题

1. **变体未检测到**
   - 确保 `textures/` 目录下有子目录
   - 检查子目录中的纹理文件命名

2. **纹理文件未识别**
   - 确保文件名包含组件名前缀
   - 检查文件扩展名是否支持
   - 确保命名模式匹配（如 `*base_color*`）

3. **MaterialX 生成失败**
   - 检查模板文件是否存在
   - 确保 MaterialX 库正确安装

### 调试模式

运行演示脚本查看详细信息：

```bash
python examples/variant_example.py
```

## 最佳实践

1. **组织结构**
   - 为每个材质变体使用描述性的目录名
   - 保持纹理文件命名一致性

2. **性能优化**
   - 使用适当的纹理分辨率
   - 考虑使用 `.exr` 格式的 HDR 纹理

3. **工作流程**
   - 先创建几何体文件
   - 再组织纹理目录结构
   - 最后运行装配命令

## 下一步

- 查看 `REFACTOR_SUMMARY.md` 了解完整功能
- 运行 `test_refactor.py` 验证安装
- 使用 `examples/variant_example.py` 学习更多用法 
