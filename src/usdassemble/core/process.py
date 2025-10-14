"""USDAssemble Core Process.

Returns
-------
    _type_: _description_
"""

from pathlib import Path

from pxr import Sdf


def list_usd_dependencies(usd_path: Path, seen: set[Path] | None = None) -> list[Path]:
    """
    Recursively list all USD dependencies including subLayers and external references.

    Args:
        usd_path: Path to the USD file.
        seen: Set of already visited paths to avoid circular references.

    Returns
    -------
        List of absolute Path objects for all dependencies.
    """
    # 已经处理过的文件集合，防止循环引用
    if seen is None:
        seen = set()

    usd_path_resolved = usd_path.resolve()
    if usd_path_resolved in seen:
        return []

    seen.add(usd_path_resolved)
    # 包含自身
    dependencies: list[Path] = [usd_path_resolved]

    layer = Sdf.Layer.FindOrOpen(str(usd_path_resolved))
    if not layer:
        return dependencies

    # Process subLayers
    for sub_layer in layer.subLayerPaths:
        sub_layer_abs = (usd_path_resolved.parent / sub_layer).resolve()
        dependencies += list_usd_dependencies(sub_layer_abs, seen)

    # Process external references (reference / payload)
    for ref in layer.externalReferences:
        ref_abs = (usd_path_resolved.parent / ref).resolve()
        dependencies += list_usd_dependencies(ref_abs, seen)

    return dependencies
