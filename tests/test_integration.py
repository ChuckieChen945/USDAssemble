#!/usr/bin/env python3
"""集成测试 - 测试完整的USD装配工作流程."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from usdassemble.cli import app


class TestIntegrationWorkflow:
    """测试完整的USD装配工作流程."""

    def setup_method(self) -> None:
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / "test_project"
        self.project_dir.mkdir()

        # 创建components目录
        self.components_dir = self.project_dir / "components"
        self.components_dir.mkdir()

    def teardown_method(self) -> None:
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_component(self, component_name: str, with_textures: bool = True):
        """创建测试组件."""
        comp_dir = self.components_dir / component_name
        comp_dir.mkdir()

        # 创建几何体文件（必需）
        geom_file = comp_dir / f"{component_name}_geom.usd"
        geom_file.touch()

        if with_textures:
            # 创建纹理目录和文件
            texture_dir = comp_dir / "textures"
            texture_dir.mkdir()

            (texture_dir / f"{component_name}_base_color.jpg").touch()
            (texture_dir / f"{component_name}_metallic.png").touch()
            (texture_dir / f"{component_name}_roughness.exr").touch()

    @patch("usdassemble.cli.create_materialx_file")
    @patch("usdassemble.cli.create_from_template")
    @patch("usdassemble.cli.Usd.Stage.Open")
    def test_complete_assembly_workflow(
        self,
        mock_stage_open,
        mock_create_from_template,
        mock_create_materialx,
    ):
        """测试完整的装配工作流程."""
        # 创建测试组件
        self.create_test_component("chess_piece", with_textures=True)
        self.create_test_component("board_square", with_textures=True)
        self.create_test_component("frame", with_textures=False)

        # 模拟USD Stage
        mock_stage = mock_stage_open.return_value
        mock_stage.GetPrimAtPath.return_value = True
        mock_stage.DefinePrim.return_value = True

        # 执行assembly命令
        runner = CliRunner()
        result = runner.invoke(app, ["assembly", str(self.project_dir)])

        # 验证成功执行
        assert result.exit_code == 0
        assert "Assembly 装配完成" in result.output

        # 验证组件被正确识别
        assert "chess_piece" in result.output
        assert "board_square" in result.output
        assert "frame" in result.output

        # 验证模板创建被调用（每个组件创建3个文件：main、payload、look）
        expected_template_calls = 3 * 3  # 3个组件 × 3个文件
        assert mock_create_from_template.call_count == expected_template_calls

        # 验证MaterialX文件创建（只有带纹理的组件才创建）
        assert mock_create_materialx.call_count == 2  # chess_piece和board_square

        # 验证assembly主文件创建
        mock_stage.Export.assert_called_once()

    def test_assembly_with_invalid_components(self):
        """测试包含无效组件的情况."""
        # 创建无效组件（缺少几何体文件）
        invalid_comp_dir = self.components_dir / "invalid_component"
        invalid_comp_dir.mkdir()
        # 不创建_geom.usd文件

        runner = CliRunner()
        result = runner.invoke(app, ["assembly", str(self.project_dir)])

        # 验证失败
        assert result.exit_code == 1
        assert "装配失败" in result.output

    def test_assembly_with_texture_conflicts(self):
        """测试纹理文件冲突的情况."""
        # 创建带冲突纹理的组件
        comp_dir = self.components_dir / "conflict_component"
        comp_dir.mkdir()
        (comp_dir / "conflict_component_geom.usd").touch()

        texture_dir = comp_dir / "textures"
        texture_dir.mkdir()

        # 创建重复的base_color文件
        (texture_dir / "mat_base_color.jpg").touch()
        (texture_dir / "tex_base_color.png").touch()

        runner = CliRunner()
        result = runner.invoke(app, ["assembly", str(self.project_dir)])

        # 验证失败并显示纹理验证错误
        assert result.exit_code == 1
        assert "装配失败" in result.output

    @patch("usdassemble.cli.create_materialx_file")
    @patch("usdassemble.cli.create_from_template")
    @patch("usdassemble.cli.Usd.Stage.Open")
    def test_assembly_with_mixed_components(
        self,
        mock_stage_open,
        mock_create_from_template,
        mock_create_materialx,
    ):
        """测试混合组件（有纹理和无纹理）的情况."""
        # 创建混合组件
        self.create_test_component("textured_comp", with_textures=True)
        self.create_test_component("simple_comp", with_textures=False)

        # 模拟USD Stage
        mock_stage = mock_stage_open.return_value
        mock_stage.GetPrimAtPath.return_value = True
        mock_stage.DefinePrim.return_value = True

        runner = CliRunner()
        result = runner.invoke(app, ["assembly", str(self.project_dir)])

        # 验证成功执行
        assert result.exit_code == 0
        assert "Assembly 装配完成" in result.output

        # 验证MaterialX只为有纹理的组件创建
        assert mock_create_materialx.call_count == 1

        # 验证跳过MaterialX的信息
        assert "跳过" in result.output and "MaterialX" in result.output

    def test_assembly_empty_project(self):
        """测试空项目的情况."""
        empty_project = self.temp_dir / "empty_project"
        empty_project.mkdir()

        runner = CliRunner()
        result = runner.invoke(app, ["assembly", str(empty_project)])

        # 验证失败
        assert result.exit_code == 1
        assert "装配失败" in result.output

    def test_assembly_verbose_mode(self):
        """测试详细模式."""
        self.create_test_component("test_comp", with_textures=True)

        with patch("usdassemble.cli.create_materialx_file"):
            with patch("usdassemble.cli.create_from_template"):
                with patch("usdassemble.cli.Usd.Stage.Open") as mock_stage_open:
                    mock_stage = mock_stage_open.return_value
                    mock_stage.GetPrimAtPath.return_value = True
                    mock_stage.DefinePrim.return_value = True

                    runner = CliRunner()
                    result = runner.invoke(app, ["assembly", str(self.project_dir), "--verbose"])

                    # 验证成功执行
                    assert result.exit_code == 0

    def test_assembly_nonexistent_path(self):
        """测试不存在的路径."""
        nonexistent_path = self.temp_dir / "nonexistent"

        runner = CliRunner()
        result = runner.invoke(app, ["assembly", str(nonexistent_path)])

        # 验证失败
        assert result.exit_code == 1
        assert "装配失败" in result.output


class TestWorkflowEdgeCases:
    """测试工作流程的边界情况."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_assembly_with_unicode_names(self):
        """测试包含Unicode字符的组件名."""
        project_dir = self.temp_dir / "unicode_project"
        project_dir.mkdir()

        components_dir = project_dir / "components"
        components_dir.mkdir()

        # 创建包含Unicode字符的组件（使用英文名以避免文件系统问题）
        comp_dir = components_dir / "unicode_component"
        comp_dir.mkdir()
        (comp_dir / "unicode_component_geom.usd").touch()

        with patch("usdassemble.cli.create_materialx_file"):
            with patch("usdassemble.cli.create_from_template"):
                with patch("usdassemble.cli.Usd.Stage.Open") as mock_stage_open:
                    mock_stage = mock_stage_open.return_value
                    mock_stage.GetPrimAtPath.return_value = True
                    mock_stage.DefinePrim.return_value = True

                    runner = CliRunner()
                    result = runner.invoke(app, ["assembly", str(project_dir)])

                    # 验证成功处理
                    assert result.exit_code == 0

    def test_assembly_with_many_components(self):
        """测试大量组件的情况."""
        project_dir = self.temp_dir / "large_project"
        project_dir.mkdir()

        components_dir = project_dir / "components"
        components_dir.mkdir()

        # 创建多个组件
        component_count = 10
        for i in range(component_count):
            comp_name = f"component_{i:02d}"
            comp_dir = components_dir / comp_name
            comp_dir.mkdir()
            (comp_dir / f"{comp_name}_geom.usd").touch()

        with patch("usdassemble.cli.create_materialx_file"):
            with patch("usdassemble.cli.create_from_template"):
                with patch("usdassemble.cli.Usd.Stage.Open") as mock_stage_open:
                    mock_stage = mock_stage_open.return_value
                    mock_stage.GetPrimAtPath.return_value = True
                    mock_stage.DefinePrim.return_value = True

                    runner = CliRunner()
                    result = runner.invoke(app, ["assembly", str(project_dir)])

                    # 验证成功处理所有组件
                    assert result.exit_code == 0
                    assert f"找到 {component_count} 个有效组件" in result.output
