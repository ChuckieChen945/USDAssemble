#!/usr/bin/env python3
"""测试工具函数."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from usdassemble.utils import (
    SUPPORTED_TEXTURE_EXTENSIONS,
    TEXTURE_PATTERNS,
    TextureValidationError,
    ensure_directory,
    find_texture_files_by_pattern,
    get_template_dir,
    validate_texture_files,
)


class TestEnsureDirectory:
    """测试ensure_directory函数."""

    def test_ensure_directory_with_file_path(self, tmp_path):
        """测试传入文件路径时创建父目录."""
        file_path = tmp_path / "subdir" / "file.txt"
        ensure_directory(file_path)
        assert file_path.parent.exists()
        assert file_path.parent.is_dir()

    def test_ensure_directory_with_dir_path(self, tmp_path):
        """测试传入目录路径时创建目录."""
        dir_path = tmp_path / "subdir"
        ensure_directory(dir_path)
        assert dir_path.exists()
        assert dir_path.is_dir()

    def test_ensure_directory_nested_paths(self, tmp_path):
        """测试创建多级嵌套目录."""
        nested_path = tmp_path / "a" / "b" / "c" / "file.txt"
        ensure_directory(nested_path)
        assert nested_path.parent.exists()
        assert nested_path.parent.is_dir()

    def test_ensure_directory_already_exists(self, tmp_path):
        """测试目录已存在时不报错."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        ensure_directory(existing_dir)
        assert existing_dir.exists()


class TestGetTemplateDir:
    """测试get_template_dir函数."""

    def test_get_template_dir_returns_path(self):
        """测试返回正确的模板目录路径."""
        template_dir = get_template_dir()
        assert isinstance(template_dir, Path)
        assert template_dir.name == "template"

    def test_get_template_dir_is_relative_to_utils(self):
        """测试模板目录相对于utils模块的位置."""
        template_dir = get_template_dir()
        # 应该是 src/template
        assert template_dir.parent.name == "src"


class TestFindTextureFilesByPattern:
    """测试find_texture_files_by_pattern函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_texture_files_single_pattern(self):
        """测试单个模式匹配."""
        # 创建测试文件
        (self.temp_dir / "test_base_color.jpg").touch()
        (self.temp_dir / "other_file.png").touch()

        patterns = ["*base_color*"]
        result = find_texture_files_by_pattern(self.temp_dir, patterns)

        assert len(result) == 1
        assert result[0].name == "test_base_color.jpg"

    def test_find_texture_files_multiple_extensions(self):
        """测试多种文件扩展名匹配."""
        # 创建不同扩展名的文件
        (self.temp_dir / "texture_metallic.jpg").touch()
        (self.temp_dir / "texture_metallic.png").touch()
        (self.temp_dir / "texture_metallic.exr").touch()

        patterns = ["*metallic*"]
        result = find_texture_files_by_pattern(self.temp_dir, patterns)

        assert len(result) == 3
        extensions = {f.suffix for f in result}
        assert extensions == {".jpg", ".png", ".exr"}

    def test_find_texture_files_no_matches(self):
        """测试无匹配文件的情况."""
        patterns = ["*nonexistent*"]
        result = find_texture_files_by_pattern(self.temp_dir, patterns)
        assert len(result) == 0

    def test_find_texture_files_multiple_patterns(self):
        """测试多个模式匹配."""
        (self.temp_dir / "mat_base_color.jpg").touch()
        (self.temp_dir / "mat_diffuse.png").touch()

        patterns = ["*base_color*", "*diffuse*"]
        result = find_texture_files_by_pattern(self.temp_dir, patterns)

        assert len(result) == 2


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

    def test_validate_texture_files_missing_directory(self):
        """测试纹理目录不存在的情况."""
        missing_dir = self.temp_dir / "missing_textures"

        with patch("usdassemble.utils.console") as mock_console:
            result = validate_texture_files(missing_dir, "test_component")
            assert result == {}
            mock_console.print.assert_called_once()

    def test_validate_texture_files_valid_textures(self):
        """测试有效纹理文件的情况."""
        # 创建有效的纹理文件
        (self.texture_dir / "test_base_color.jpg").touch()
        (self.texture_dir / "test_metallic.png").touch()
        (self.texture_dir / "test_normal.exr").touch()

        result = validate_texture_files(self.texture_dir, "test_component")

        expected = {
            "base_color": "textures/test_base_color.jpg",
            "metallic": "textures/test_metallic.png",
            "normal": "textures/test_normal.exr",
        }
        assert result == expected

    def test_validate_texture_files_duplicate_textures(self):
        """测试重复纹理文件的错误情况."""
        # 创建重复的base_color文件
        (self.texture_dir / "mat_base_color.jpg").touch()
        (self.texture_dir / "tex_base_color.png").touch()

        with pytest.raises(TextureValidationError) as exc_info:
            validate_texture_files(self.texture_dir, "test_component")

        assert "重复" in str(exc_info.value) or "多个文件" in str(exc_info.value)

    def test_validate_texture_files_unknown_textures(self):
        """测试未知纹理文件的错误情况."""
        # 创建一个有效文件和一个未知文件
        (self.texture_dir / "test_base_color.jpg").touch()
        (self.texture_dir / "unknown_texture.png").touch()

        with pytest.raises(TextureValidationError) as exc_info:
            validate_texture_files(self.texture_dir, "test_component")

        assert "未识别" in str(exc_info.value)

    def test_validate_texture_files_empty_directory(self):
        """测试空纹理目录的情况."""
        result = validate_texture_files(self.texture_dir, "test_component")
        assert result == {}

    def test_validate_texture_files_partial_match(self):
        """测试部分纹理类型匹配的情况."""
        # 只创建部分纹理类型
        (self.texture_dir / "comp_base_color.jpg").touch()
        (self.texture_dir / "comp_roughness.png").touch()

        result = validate_texture_files(self.texture_dir, "test_component")

        expected = {
            "base_color": "textures/comp_base_color.jpg",
            "roughness": "textures/comp_roughness.png",
        }
        assert result == expected


class TestConstants:
    """测试常量定义."""

    def test_supported_texture_extensions(self):
        """测试支持的纹理文件扩展名."""
        assert ".jpg" in SUPPORTED_TEXTURE_EXTENSIONS
        assert ".png" in SUPPORTED_TEXTURE_EXTENSIONS
        assert ".exr" in SUPPORTED_TEXTURE_EXTENSIONS

    def test_texture_patterns_completeness(self):
        """测试纹理模式的完整性."""
        required_types = [
            "base_color",
            "metallic",
            "roughness",
            "normal",
            "specular",
            "diffuse",
            "emissive",
        ]

        for texture_type in required_types:
            assert texture_type in TEXTURE_PATTERNS
            assert len(TEXTURE_PATTERNS[texture_type]) > 0

    def test_texture_patterns_format(self):
        """测试纹理模式的格式."""
        for texture_type, patterns in TEXTURE_PATTERNS.items():
            assert isinstance(patterns, list)
            for pattern in patterns:
                assert isinstance(pattern, str)
                assert "*" in pattern  # 应该包含通配符
