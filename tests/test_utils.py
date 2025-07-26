#!/usr/bin/env python3
"""测试工具函数."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from usdassemble.utils import (
    ComponentType,
    TextureValidationError,
    ensure_directory,
    find_texture_files_by_pattern,
    get_component_directory_and_type,
    get_template_dir,
    validate_texture_files,
)


class TestComponentType:
    """测试ComponentType枚举."""

    def test_component_type_values(self):
        """测试ComponentType的值."""
        assert ComponentType.COMPONENT.kind == "component"
        assert ComponentType.COMPONENT.directory == "components"
        assert ComponentType.SUBCOMPONENT.kind == "subcomponent"
        assert ComponentType.SUBCOMPONENT.directory == "subcomponents"

    def test_from_directory(self):
        """测试从目录名获取组件类型."""
        assert ComponentType.from_directory("components") == ComponentType.COMPONENT
        assert ComponentType.from_directory("subcomponents") == ComponentType.SUBCOMPONENT

    def test_from_directory_invalid(self):
        """测试无效目录名."""
        with pytest.raises(ValueError, match="不支持的组件目录类型: invalid"):
            ComponentType.from_directory("invalid")

    def test_detect_from_path(self):
        """测试从路径检测组件类型."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            # 没有组件目录
            assert ComponentType.detect_from_path(base_path) is None

            # 创建components目录
            (base_path / "components").mkdir()
            assert ComponentType.detect_from_path(base_path) == ComponentType.COMPONENT

            # 删除components，创建subcomponents
            (base_path / "components").rmdir()
            (base_path / "subcomponents").mkdir()
            assert ComponentType.detect_from_path(base_path) == ComponentType.SUBCOMPONENT

            # 两个目录都存在时，应该返回第一个找到的（COMPONENT优先）
            (base_path / "components").mkdir()
            assert ComponentType.detect_from_path(base_path) == ComponentType.COMPONENT


class TestGetComponentDirectoryAndType:
    """测试get_component_directory_and_type函数."""

    def test_success_components(self):
        """测试成功获取components目录和类型."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            components_dir = base_path / "components"
            components_dir.mkdir()

            result_dir, result_type = get_component_directory_and_type(base_path)
            assert result_dir == components_dir
            assert result_type == ComponentType.COMPONENT

    def test_success_subcomponents(self):
        """测试成功获取subcomponents目录和类型."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            subcomponents_dir = base_path / "subcomponents"
            subcomponents_dir.mkdir()

            result_dir, result_type = get_component_directory_and_type(base_path)
            assert result_dir == subcomponents_dir
            assert result_type == ComponentType.SUBCOMPONENT

    def test_no_component_directory(self):
        """测试未找到组件目录时抛出异常."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            with pytest.raises(ValueError, match="未找到支持的组件目录"):
                get_component_directory_and_type(base_path)


class TestEnsureDirectory:
    """测试ensure_directory函数."""

    def test_ensure_directory_from_file_path(self):
        """测试从文件路径确保目录存在."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "subdir" / "file.txt"
            ensure_directory(file_path)
            assert file_path.parent.exists()

    def test_ensure_directory_from_dir_path(self):
        """测试从目录路径确保目录存在."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir) / "subdir"
            ensure_directory(dir_path)
            assert dir_path.exists()


class TestGetTemplateDir:
    """测试get_template_dir函数."""

    def test_get_template_dir(self):
        """测试获取模板目录路径."""
        template_dir = get_template_dir()
        expected_path = Path(__file__).parent.parent / "src" / "template"
        assert template_dir == expected_path


class TestFindTextureFilesByPattern:
    """测试find_texture_files_by_pattern函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_texture_files_success(self):
        """测试成功查找纹理文件."""
        # 创建测试文件
        test_files = [
            "test_base_color.jpg",
            "test_base_color_01.png",
            "other_file.exr",
        ]
        for filename in test_files:
            (self.temp_dir / filename).touch()

        patterns = ["*base_color*"]
        found_files = find_texture_files_by_pattern(self.temp_dir, patterns)

        assert len(found_files) == 2
        found_names = {f.name for f in found_files}
        assert "test_base_color.jpg" in found_names
        assert "test_base_color_01.png" in found_names

    def test_find_texture_files_no_matches(self):
        """测试没有找到匹配文件."""
        # 创建不匹配的文件
        (self.temp_dir / "other_file.jpg").touch()

        patterns = ["*base_color*"]
        found_files = find_texture_files_by_pattern(self.temp_dir, patterns)

        assert len(found_files) == 0


class TestValidateTextureFiles:
    """测试validate_texture_files函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.texture_dir = self.temp_dir / "textures"
        self.texture_dir.mkdir()

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_texture_files_success(self):
        """测试成功验证纹理文件."""
        # 创建有效的纹理文件
        test_files = [
            "component_base_color.jpg",
            "component_metallic.png",
            "component_roughness.exr",
        ]
        for filename in test_files:
            (self.texture_dir / filename).touch()

        result = validate_texture_files(self.texture_dir, "component")

        assert len(result) == 3
        assert "base_color" in result
        assert "metallic" in result
        assert "roughness" in result

    def test_validate_texture_files_no_texture_dir(self):
        """测试纹理目录不存在."""
        non_existent_dir = self.temp_dir / "non_existent"
        result = validate_texture_files(non_existent_dir, "component")
        assert result == {}

    def test_validate_texture_files_duplicate_type(self):
        """测试纹理类型重复."""
        # 创建重复类型的文件
        (self.texture_dir / "component_base_color.jpg").touch()
        (self.texture_dir / "component_base_color.png").touch()

        with pytest.raises(TextureValidationError, match="纹理类型 'base_color' 匹配到多个文件"):
            validate_texture_files(self.texture_dir, "component")

    def test_validate_texture_files_unknown_files(self):
        """测试存在未知纹理文件."""
        # 创建已知和未知文件
        (self.texture_dir / "component_base_color.jpg").touch()
        (self.texture_dir / "unknown_file.jpg").touch()

        with pytest.raises(TextureValidationError, match="发现未识别的纹理文件"):
            validate_texture_files(self.texture_dir, "component")

    def test_validate_texture_files_empty_dir(self):
        """测试空纹理目录."""
        result = validate_texture_files(self.texture_dir, "component")
        assert result == {}
