"""USD Assembly 异常定义."""


class AssemblyError(Exception):
    """装配错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ComponentError(Exception):
    """组件处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class FileServiceError(Exception):
    """文件服务错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MaterialXError(Exception):
    """MaterialX处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TemplateServiceError(Exception):
    """模板服务错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TextureValidationError(Exception):
    """纹理文件验证错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UsdServiceError(Exception):
    """USD服务错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class VariantError(Exception):
    """变体处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
