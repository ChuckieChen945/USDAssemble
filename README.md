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
- **🔄 变体支持**: 完整的材质变体系统
- **⚙️ 配置管理**: 灵活的配置系统
- **📝 日志系统**: 统一的日志管理

## 📁 模板系统

项目使用模板驱动的方式生成USD文件，模板位于 `src/template/` 目录：

```
src/template/
└── {$assembly_or_component_name}/
    ├── {$assembly_or_component_name}.usda                    # Assembly主文件模板
    └── components_or_subcomponents/
        └── {$component_or_subcomponent_name}/                   # 组件模板目录
            ├── {$component_or_subcomponent_name}.usd            # 组件主文件模板
            ├── {$component_or_subcomponent_name}_payload.usd    # Payload文件模板
            ├── {$component_or_subcomponent_name}_look.usd       # Look文件模板
            └── {$component_or_subcomponent_name}_mat.mtlx       # MaterialX文件模板
```

### 模板变量

- `{$assembly_name}`: Assembly名称
- `{$component_name}`: 组件名称
- `{$subcomponent_name}`: 子组件名称

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/ChuckieChen945/USDAssemble.git
cd USDAssemble

# 安装依赖
uv sync

# 安装开发依赖
uv sync --dev
```

### 基本用法

```bash
# 装配USD资产
python -m src.cli.app assemble /path/to/asset

# 扫描目录结构
python -m src.cli.app scan /path/to/asset

# 验证目录结构
python -m src.cli.app validate /path/to/asset

# 显示工具信息
python -m src.cli.app info
```

### 高级用法

```bash
# 详细输出模式
python -m src.cli.app assemble /path/to/asset --verbose

# 仅扫描，不生成文件
python -m src.cli.app assemble /path/to/asset --dry-run

# 显示详细组件信息
python -m src.cli.app scan /path/to/asset --details
```

## 📋 目录结构

```
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
    │          chessboard_normal.jpg（已存在，由用户放置）
    │          chessboard_roughness.jpg（已存在，由用户放置）
    │
    └─King
        │  King.usda （尚不存在，待装配生成）
        │  King_geom.usd（已存在，由用户放置）
        │  King_look.usda （尚不存在，待装配生成）
        │  King_mat.mtlx（尚不存在，待复制生成）
        │  King_payload.usda （尚不存在，待装配生成）
        │
        └─textures
                king_black_base_color.jpg（已存在，由用户放置）
                king_black_normal.jpg（已存在，由用户放置）
                king_black_roughness.jpg（已存在，由用户放置）
                king_white_base_color.jpg（已存在，由用户放置）
                king_white_normal.jpg（已存在，由用户放置）
                king_white_roughness.jpg（已存在，由用户放置）
```

## 🔧 配置

USDAssemble使用配置文件 `.usdassemble.json` 来管理设置：

```json
{
  "template_dir": "src/template",
  "output_format": "usda",
  "verbose": false,
  "backup_files": true,
  "materialx_settings": {
    "default_format": "mtlx",
    "texture_formats": ["jpg", "png", "exr", "tga"],
    "max_texture_size": 4096
  },
  "usd_settings": {
    "default_up_axis": "Y",
    "meters_per_unit": 1.0,
    "time_code_per_second": 24.0
  }
}
```

## 🏗️ 项目架构

### 核心模块

- **`cli/`**: 命令行接口
- **`core/`**: 核心处理逻辑
  - `assembly.py`: Assembly构建器
  - `component.py`: 组件处理器
  - `variant.py`: 变体处理器
- **`domain/`**: 数据模型和枚举
- **`materialx/`**: MaterialX文件处理
- **`services/`**: 服务层
  - `file_service.py`: 文件操作服务
  - `template_service.py`: 模板处理服务
  - `usd_service.py`: USD文件服务
- **`utils/`**: 工具模块
  - `config.py`: 配置管理
  - `logger.py`: 日志管理
  - `path_utils.py`: 路径工具

### 处理流程

1. **扫描阶段**: 扫描目录结构，检测组件和纹理文件
2. **模板阶段**: 读取模板文件，进行变量替换
3. **修改阶段**: 使用USD/MaterialX API修改具体内容
4. **输出阶段**: 生成最终的USD和MaterialX文件

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_integration.py

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

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

### 核心特性

- **模板驱动**: 确保生成文件的一致性和正确性
- **智能检测**: 自动识别目录类型和纹理文件
- **API集成**: 深度集成USD和MaterialX API
- **类型安全**: 全面的类型注解和错误处理
- **配置管理**: 灵活的配置系统
- **日志系统**: 统一的日志管理

### 错误处理

项目实现了统一的错误处理机制：

- **统一错误类型**: 每种错误都有专门的异常类
- **错误抽象**: 将重复的raise语句抽象到内部函数
- **详细错误信息**: 提供清晰的错误消息和上下文

## 📋 已完成的功能

- [x] 支持更多纹理类型和格式
- [x] 添加extentsHint自动计算
- [x] 实现嵌套组件的递归处理
- [x] 添加自定义模板支持
- [x] 性能优化和并行处理
- [x] 统一的错误处理机制
- [x] 配置管理系统
- [x] 日志管理系统
- [x] 完整的CLI命令集
- [x] 变体支持系统

## 🎯 下一步计划

- [ ] 添加Web界面
- [ ] 支持更多USD文件格式
- [ ] 添加插件系统
- [ ] 支持分布式处理
- [ ] 添加性能监控

## �� 许可证

MIT License
