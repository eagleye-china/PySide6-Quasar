# src/pyside6_quasar/core/base/__init__.py
from .widget import QBaseWidget, QuasarWidgetMixin
# ★ re-export 常用基建，让子组件一行导入
from ...core.theme import theme_manager, ThemeMode
from ..theme.contrast import get_contrast_color
from ..theme.palette import Color

__all__ = [
    "QBaseWidget", "QuasarWidgetMixin",
    "theme_manager", "ThemeMode", "Color", "get_contrast_color",
]
