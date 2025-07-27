#!/usr/bin/env python3
"""USD 变体装配演示示例.

展示如何使用重构后的 USDAssemble 工具创建支持变体的 USD 资产。
"""

import tempfile
from pathlib import Path

from mtlx.materialx import create_materialx_from_component_info
from usdassemble.utils import (
    ComponentInfo,
    ComponentType,
    VariantInfo,
    scan_component_info,
)


def create_example_variant_structure():
    """创建示例变体结构."""
    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())

    # 创建组件目录结构
    component_dir = temp_dir / "components" / "chess_piece"
    component_dir.mkdir(parents=True)

    # 创建几何体文件（空文件用于演示）
    geom_file = component_dir / "chess_piece_geom.usd"
    geom_file.touch()

    # 创建变体纹理目录
    textures_dir = component_dir / "textures"

    # 创建变体1：木质
    wood_variant_dir = textures_dir / "wood"
    wood_variant_dir.mkdir(parents=True)
    (wood_variant_dir / "chess_piece_base_color.jpg").touch()
    (wood_variant_dir / "chess_piece_roughness.jpg").touch()
    (wood_variant_dir / "chess_piece_normal.jpg").touch()

    # 创建变体2：金属
    metal_variant_dir = textures_dir / "metal"
    metal_variant_dir.mkdir(parents=True)
    (metal_variant_dir / "chess_piece_base_color.jpg").touch()
    (metal_variant_dir / "chess_piece_metalness.jpg").touch()
    (metal_variant_dir / "chess_piece_roughness.jpg").touch()
    (metal_variant_dir / "chess_piece_normal.jpg").touch()

    # 创建变体3：石质
    stone_variant_dir = textures_dir / "stone"
    stone_variant_dir.mkdir(parents=True)
    (stone_variant_dir / "chess_piece_base_color.jpg").touch()
    (stone_variant_dir / "chess_piece_roughness.jpg").touch()

    print(f"创建演示目录结构: {temp_dir}")
    return temp_dir, component_dir


def demonstrate_variant_scanning():
    """演示变体扫描功能."""
    print("\n" + "=" * 60)
    print("USD 变体装配演示")
    print("=" * 60)

    # 创建示例结构
    temp_dir, component_dir = create_example_variant_structure()

    try:
        # 扫描组件信息
        print("\n1. 扫描组件信息...")
        component_info = scan_component_info(component_dir, ComponentType.COMPONENT)

        print(f"   组件名称: {component_info.name}")
        print(f"   组件类型: {component_info.component_type.kind}")
        print(f"   有几何体: {component_info.has_geometry}")
        print(f"   有变体: {component_info.has_variants}")

        if component_info.has_variants:
            print(f"   变体数量: {len(component_info.variants)}")
            for i, variant in enumerate(component_info.variants, 1):
                print(f"     变体 {i}: {variant.name}")
                print(f"       纹理数量: {len(variant.textures)}")
                for texture_type, path in variant.textures.items():
                    print(f"         {texture_type}: {path}")

        # 演示 MaterialX 创建
        print("\n2. 创建 MaterialX 文件...")
        output_mtlx = component_dir / f"{component_info.name}_mat.mtlx"
        try:
            create_materialx_from_component_info(component_info, str(output_mtlx))
            print(f"   MaterialX 文件已创建: {output_mtlx.name}")
        except Exception as e:
            print(f"   MaterialX 创建失败: {e}")

    finally:
        # 清理临时文件
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n清理临时目录: {temp_dir}")

    print("\n演示完成!")


def demonstrate_non_variant_component():
    """演示非变体组件功能."""
    print("\n" + "=" * 60)
    print("非变体组件演示")
    print("=" * 60)

    # 创建临时目录
    temp_dir = Path(tempfile.mkdtemp())

    try:
        # 创建组件目录结构
        component_dir = temp_dir / "subcomponents" / "simple_piece"
        component_dir.mkdir(parents=True)

        # 创建几何体文件
        geom_file = component_dir / "simple_piece_geom.usd"
        geom_file.touch()

        # 创建直接纹理文件
        textures_dir = component_dir / "textures"
        textures_dir.mkdir()
        (textures_dir / "simple_piece_base_color.jpg").touch()
        (textures_dir / "simple_piece_roughness.jpg").touch()

        print("\n1. 扫描非变体组件...")
        component_info = scan_component_info(component_dir, ComponentType.SUBCOMPONENT)

        print(f"   组件名称: {component_info.name}")
        print(f"   组件类型: {component_info.component_type.kind}")
        print(f"   有变体: {component_info.has_variants}")
        print(f"   直接纹理数量: {len(component_info.textures)}")

        for texture_type, path in component_info.textures.items():
            print(f"     {texture_type}: {path}")

    finally:
        # 清理临时文件
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n清理临时目录: {temp_dir}")


if __name__ == "__main__":
    demonstrate_variant_scanning()
    demonstrate_non_variant_component()
