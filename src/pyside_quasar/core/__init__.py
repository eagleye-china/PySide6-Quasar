# src/pyside_quasar/core/__init__.py
"""
pyside_quasar.core - L0 核心基建层

本层不依赖任何 UI 组件，是所有上层模块的根基。
"""

# ═══════════════════════════════════════════════════════════════
# 注意：本文件位于 core/ 目录内，访问同级子模块请用 1 个点
#      访问 core 的兄弟模块（如 components）请用 2 个点
#      ❌ 绝不能写 3 个点（那是给 components/*/xxx.py 用的）
# ═══════════════════════════════════════════════════════════════

from .base import QBaseWidget, QuasarWidgetMixin
from .router import Router
from .theme import theme_manager, ThemeMode
from .theme.contrast import get_contrast_color
from .theme.palette import Color
from .validation import FormValidator, ValidationRule

__all__ = [
    "theme_manager", "ThemeMode", "Color", "get_contrast_color",
    "QBaseWidget", "QuasarWidgetMixin",
    "Router", "FormValidator", "ValidationRule",
]
