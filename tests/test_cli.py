#!/usr/bin/env python3
"""测试CLI功能."""

import tempfile
from pathlib import Path
from string import Template
from unittest.mock import Mock, call, patch

import pytest
from typer.testing import CliRunner

from usdassemble.cli import (
    AssemblyError,
    app,
    create_assembly_main,
    create_component_look,
    create_component_main,
    create_component_payload,
    create_from_template,
    process_component,
    scan_components,
)


class TestCreateFromTemplate:
    """测试create_from_template函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_from_template_success(self):
        """测试成功从模板创建文件."""
        # 创建模板文件
        template_path = self.temp_dir / "template.txt"
        template_content = "Hello $name, welcome to $project!"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)

        # 创建输出路径
        output_path = self.temp_dir / "output" / "result.txt"
        substitutions = {"name": "测试", "project": "USDAssemble"}

        # 执行函数
        create_from_template(template_path, output_path, substitutions)

        # 验证结果
        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert content == "Hello 测试, welcome to USDAssemble!"

    def test_create_from_template_missing_template(self):
        """测试模板文件不存在的错误情况."""
        template_path = self.temp_dir / "missing_template.txt"
        output_path = self.temp_dir / "output.txt"
        substitutions = {}

        with pytest.raises(AssemblyError) as exc_info:
            create_from_template(template_path, output_path, substitutions)

        assert "模板文件不存在" in str(exc_info.value)

    def test_create_from_template_safe_substitute(self):
        """测试safe_substitute处理缺失变量."""
        # 创建包含未定义变量的模板
        template_path = self.temp_dir / "template.txt"
        template_content = "Name: $name, Project: $undefined_var"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)

        output_path = self.temp_dir / "output.txt"
        substitutions = {"name": "测试"}

        # 执行函数（应该不报错）
        create_from_template(template_path, output_path, substitutions)

        # 验证结果（未定义变量保持原样）
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert content == "Name: 测试, Project: $undefined_var"


class TestScanComponents:
    """测试scan_components函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.components_dir = self.temp_dir / "components"
        self.components_dir.mkdir()

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_components_valid_components(self):
        """测试扫描有效组件."""
        # 创建有效组件
        comp1_dir = self.components_dir / "component1"
        comp1_dir.mkdir()
        (comp1_dir / "component1_geom.usd").touch()

        comp2_dir = self.components_dir / "component2"
        comp2_dir.mkdir()
        (comp2_dir / "component2_geom.usd").touch()

        # 创建无效组件（缺少几何体文件）
        comp3_dir = self.components_dir / "component3"
        comp3_dir.mkdir()

        with patch("usdassemble.cli.console") as mock_console:
            result = scan_components(str(self.temp_dir))
            assert result == ["component1", "component2"]

    def test_scan_components_no_components_dir(self):
        """测试components目录不存在的情况."""
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()

        with pytest.raises(AssemblyError) as exc_info:
            scan_components(str(empty_dir))

        assert "未找到 components 目录" in str(exc_info.value)

    def test_scan_components_no_valid_components(self):
        """测试没有有效组件的情况."""
        # 创建无效组件
        comp_dir = self.components_dir / "invalid_component"
        comp_dir.mkdir()
        # 不创建_geom.usd文件

        with pytest.raises(AssemblyError) as exc_info:
            scan_components(str(self.temp_dir))

        assert "未找到任何有效组件" in str(exc_info.value)

    def test_scan_components_empty_components_dir(self):
        """测试空的components目录."""
        with pytest.raises(AssemblyError) as exc_info:
            scan_components(str(self.temp_dir))

        assert "未找到任何有效组件" in str(exc_info.value)


class TestComponentCreationFunctions:
    """测试组件创建函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("usdassemble.cli.get_template_dir")
    @patch("usdassemble.cli.create_from_template")
    def test_create_component_payload(self, mock_create_from_template, mock_get_template_dir):
        """测试创建组件payload文件."""
        mock_get_template_dir.return_value = Path("/mock/template")

        output_path = str(self.temp_dir / "test_payload.usd")
        component_name = "test_component"

        create_component_payload(output_path, component_name)

        # 验证调用
        expected_template_path = (
            Path("/mock/template")
            / "{$assembly_name}"
            / "components"
            / "{$component_name}"
            / "{$component_name}_payload.usd"
        )
        expected_substitutions = {"component_name": component_name}

        mock_create_from_template.assert_called_once_with(
            expected_template_path,
            Path(output_path),
            expected_substitutions,
        )

    @patch("usdassemble.cli.get_template_dir")
    @patch("usdassemble.cli.create_from_template")
    def test_create_component_look(self, mock_create_from_template, mock_get_template_dir):
        """测试创建组件look文件."""
        mock_get_template_dir.return_value = Path("/mock/template")

        output_path = str(self.temp_dir / "test_look.usd")
        component_name = "test_component"

        create_component_look(output_path, component_name)

        # 验证调用
        expected_template_path = (
            Path("/mock/template")
            / "{$assembly_name}"
            / "components"
            / "{$component_name}"
            / "{$component_name}_look.usd"
        )
        expected_substitutions = {"component_name": component_name}

        mock_create_from_template.assert_called_once_with(
            expected_template_path,
            Path(output_path),
            expected_substitutions,
        )

    @patch("usdassemble.cli.get_template_dir")
    @patch("usdassemble.cli.create_from_template")
    def test_create_component_main(self, mock_create_from_template, mock_get_template_dir):
        """测试创建组件主文件."""
        mock_get_template_dir.return_value = Path("/mock/template")

        output_path = str(self.temp_dir / "test_main.usd")
        component_name = "test_component"

        create_component_main(output_path, component_name)

        # 验证调用
        expected_template_path = (
            Path("/mock/template")
            / "{$assembly_name}"
            / "components"
            / "{$component_name}"
            / "{$component_name}.usd"
        )
        expected_substitutions = {"component_name": component_name}

        mock_create_from_template.assert_called_once_with(
            expected_template_path,
            Path(output_path),
            expected_substitutions,
        )


class TestCreateAssemblyMain:
    """测试create_assembly_main函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("usdassemble.cli.get_template_dir")
    @patch("usdassemble.cli.Usd.Stage.Open")
    def test_create_assembly_main_success(self, mock_stage_open, mock_get_template_dir):
        """测试成功创建assembly主文件."""
        # 模拟模板目录和文件
        template_dir = Path("/mock/template")
        mock_get_template_dir.return_value = template_dir

        template_path = template_dir / "{$assembly_name}" / "{$assembly_name}.usda"
        template_content = """#usda 1.0
(
    defaultPrim = "$assembly_name"
)

def Xform "$assembly_name" (
    kind = "assembly"
)
{
}
"""

        # 模拟文件读取
        with patch("builtins.open", mock_open_read_data(template_content)):
            # 模拟USD Stage
            mock_stage = Mock()
            mock_assembly_prim = Mock()
            mock_stage.GetPrimAtPath.return_value = mock_assembly_prim
            mock_stage.DefinePrim.return_value = Mock()
            mock_stage_open.return_value = mock_stage

            output_path = str(self.temp_dir / "test_assembly.usda")
            assembly_name = "test_assembly"
            components = ["comp1", "comp2"]

            # 执行函数
            create_assembly_main(output_path, assembly_name, components)

            # 验证调用
            mock_stage_open.assert_called_once()
            mock_stage.GetPrimAtPath.assert_called_once_with(f"/{assembly_name}")
            assert mock_stage.DefinePrim.call_count == len(components)
            mock_stage.Export.assert_called_once_with(output_path)

    @patch("usdassemble.cli.get_template_dir")
    def test_create_assembly_main_template_not_found(self, mock_get_template_dir):
        """测试模板文件不存在的情况."""
        mock_get_template_dir.return_value = Path("/nonexistent/template")

        output_path = str(self.temp_dir / "test_assembly.usda")
        assembly_name = "test_assembly"
        components = ["comp1"]

        with pytest.raises(AssemblyError):
            create_assembly_main(output_path, assembly_name, components)


class TestProcessComponent:
    """测试process_component函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.component_dir = self.temp_dir / "component1"
        self.component_dir.mkdir()

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("usdassemble.cli.validate_texture_files")
    @patch("usdassemble.cli.create_materialx_file")
    @patch("usdassemble.cli.create_component_main")
    @patch("usdassemble.cli.create_component_payload")
    @patch("usdassemble.cli.create_component_look")
    @patch("usdassemble.cli.console")
    def test_process_component_with_textures(
        self,
        mock_console,
        mock_create_look,
        mock_create_payload,
        mock_create_main,
        mock_create_materialx,
        mock_validate_textures,
    ):
        """测试处理带纹理的组件."""
        # 模拟纹理验证返回
        texture_files = {"base_color": "textures/test_base_color.jpg"}
        mock_validate_textures.return_value = texture_files

        component_name = "test_component"
        process_component(str(self.component_dir), component_name)

        # 验证调用
        mock_validate_textures.assert_called_once()
        mock_create_materialx.assert_called_once_with(
            component_name,
            texture_files,
            str(self.component_dir / f"{component_name}_mat.mtlx"),
        )
        mock_create_main.assert_called_once()
        mock_create_payload.assert_called_once()
        mock_create_look.assert_called_once()

    @patch("usdassemble.cli.validate_texture_files")
    @patch("usdassemble.cli.create_materialx_file")
    @patch("usdassemble.cli.create_component_main")
    @patch("usdassemble.cli.create_component_payload")
    @patch("usdassemble.cli.create_component_look")
    @patch("usdassemble.cli.console")
    def test_process_component_without_textures(
        self,
        mock_console,
        mock_create_look,
        mock_create_payload,
        mock_create_main,
        mock_create_materialx,
        mock_validate_textures,
    ):
        """测试处理无纹理的组件."""
        # 模拟无纹理返回
        mock_validate_textures.return_value = {}

        component_name = "test_component"
        process_component(str(self.component_dir), component_name)

        # 验证调用
        mock_validate_textures.assert_called_once()
        mock_create_materialx.assert_not_called()  # 无纹理时不创建MaterialX
        mock_create_main.assert_called_once()
        mock_create_payload.assert_called_once()
        mock_create_look.assert_called_once()


class TestCLICommands:
    """测试CLI命令."""

    def test_assembly_command_help(self):
        """测试assembly命令的帮助信息."""
        runner = CliRunner()
        result = runner.invoke(app, ["assembly", "--help"])
        assert result.exit_code == 0
        assert "装配 USD assembly" in result.output

    @patch("usdassemble.cli.scan_components")
    @patch("usdassemble.cli.process_component")
    @patch("usdassemble.cli.create_assembly_main")
    def test_assembly_command_success(
        self, mock_create_assembly, mock_process_component, mock_scan_components
    ):
        """测试assembly命令成功执行."""
        # 模拟扫描组件返回
        mock_scan_components.return_value = ["comp1", "comp2"]

        runner = CliRunner()
        with runner.isolated_filesystem():
            # 创建测试目录结构
            Path("test_project").mkdir()

            result = runner.invoke(app, ["assembly", "test_project"])

            # 验证调用
            mock_scan_components.assert_called_once()
            assert mock_process_component.call_count == 2
            mock_create_assembly.assert_called_once()

            assert result.exit_code == 0

    @patch("usdassemble.cli.scan_components")
    def test_assembly_command_error_handling(self, mock_scan_components):
        """测试assembly命令的错误处理."""
        # 模拟扫描组件失败
        mock_scan_components.side_effect = AssemblyError("测试错误")

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(app, ["assembly", "test_project"])

            assert result.exit_code == 1
            assert "装配失败" in result.output


def mock_open_read_data(data):
    """创建mock的open函数，用于返回指定数据."""
    from unittest.mock import mock_open

    return mock_open(read_data=data)
