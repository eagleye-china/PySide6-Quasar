"""
pyside6-quasar
==============
The Quasar Framework for PySide6.

Material Design components · Pure QPainter · Zero QSS · Global Theming

Design Philosophy
-----------------
    - L0 Core:      Theme, Router, Validation, State (无 UI 依赖)
    - L1 Primitive: Button, Input, Checkbox... (纯 QPainter 自绘)
    - L2 Container: Card, Tabs, Dialog... (组合 L1)
    - L3 Data:      Table, Select, Tree... (Model/View 架构)
    - L4 Template:  LoginPage, DashboardPage... (业务骨架)

Quick Start
-----------
    >>> from pyside6_quasar import Button, Card, theme_manager, Color
    >>> btn = Button("Click me", color=Color.PRIMARY)
    >>> theme_manager.toggle()

Homepage: https://github.com/your-org/pyside6-quasar
Docs:     https://your-org.github.io/pyside6-quasar
License:  MIT
"""

from __future__ import annotations

import warnings
from importlib.metadata import version, PackageNotFoundError
from typing import Any, Dict, Tuple

# ═══════════════════════════════════════════════════════════════
# 📌 元信息 (Metadata)
# ═══════════════════════════════════════════════════════════════

try:
    __version__: str = version("pyside6-quasar")
except PackageNotFoundError:
    # 开发模式兜底（未 pip install -e . 时）
    __version__ = "0.1.0-dev"

# 语义化版本元组，便于版本比较：
# if pyside6_quasar.__version_info__ >= (1, 0, 0): ...
try:
    __version_info__: Tuple[int, ...] = tuple(
        int(x) for x in __version__.split("-")[0].split(".") if x.isdigit()
    )
except (ValueError, IndexError):
    __version_info__ = (0, 0, 0)

__author__ = "PySide6-Quasar Team"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 PySide6-Quasar Team"
__url__ = "https://github.com/your-org/pyside6-quasar"

# ═══════════════════════════════════════════════════════════════
# 📦 L0 核心基建（强制导入 - 框架根基）
# ═══════════════════════════════════════════════════════════════

from .core.theme import theme_manager, ThemeMode
from .core.theme.palette import Color
from .core.base import QBaseWidget, QuasarWidgetMixin
from .core.router import Router
from .core.validation import FormValidator, ValidationRule

# ═══════════════════════════════════════════════════════════════
# 🧱 L1 基础组件（当前已实现）
# ═══════════════════════════════════════════════════════════════

from .components.primitives import (
    # --- Button ---
    Button, ButtonVariant, ButtonSize, ButtonShape,
    # --- 表单录入 ---
    Input, Checkbox, Switch,
    # --- 展示 ---
    Avatar, AvatarShape, AvatarSize, AvatarShape,  # noqa: F811 - 兼容旧导入
    Badge, BadgeAlign,
    # --- 进度指示 ---
    LineProgress, CircleProgress,
)

# ═══════════════════════════════════════════════════════════════
# 🗂️ L2 容器组件（当前已实现）
# ═══════════════════════════════════════════════════════════════

from .components.containers import (
    # --- Card 系列 ---
    Card, CardSection, CardActions, CardMedia,
    # --- Tabs 系列 ---
    Tabs, TabItem, TabsAlign, TabsIndicatorPosition,
    # --- Dialog ---
    Dialog,
)

# ═══════════════════════════════════════════════════════════════
# 💬 反馈组件（当前已实现）
# ═══════════════════════════════════════════════════════════════

from .components.feedback import (
    Toast, ToastType, ToastPosition,
    Tooltip, TooltipPosition, TooltipTransition,
)

# ═══════════════════════════════════════════════════════════════
# 🚀 未来组件（懒加载 + 友好提示）
# ═══════════════════════════════════════════════════════════════

# 已规划但尚未实现的组件映射表
# 格式：{ 组件名: (子模块相对路径, 类名, 计划版本) }
_LAZY_COMPONENTS: Dict[str, Tuple[str, str, str]] = {
    # ---------- L1 规划中 ----------
    "Radio": ("components.primitives.radio", "Radio", "v0.2.0"),
    "Slider": ("components.primitives.slider", "Slider", "v0.2.0"),
    "Chip": ("components.primitives.chip", "Chip", "v0.2.0"),

    # ---------- L2 规划中 ----------
    "Drawer": ("components.containers.drawer", "Drawer", "v0.3.0"),
    "Collapse": ("components.containers.collapse", "Collapse", "v0.3.0"),

    # ---------- L3 规划中 ----------
    "Table": ("components.data.table", "Table", "v0.4.0"),
    "TableColumn": ("components.data.table", "TableColumn", "v0.4.0"),
    "Select": ("components.data.select", "Select", "v0.4.0"),
    "ListView": ("components.data.list_view", "ListView", "v0.4.0"),
    "TreeView": ("components.data.tree_view", "TreeView", "v0.4.0"),

    # ---------- 反馈规划中 ----------
    "Notification": ("components.feedback.notification", "Notification", "v0.5.0"),

    # ---------- 布局与模板规划中 ----------
    "MainLayout": ("layouts.main_layout", "MainLayout", "v0.6.0"),
    "AuthLayout": ("layouts.auth_layout", "AuthLayout", "v0.6.0"),
    "BlankLayout": ("layouts.blank_layout", "BlankLayout", "v0.6.0"),
    "LoginPage": ("templates.login_page", "LoginPage", "v0.6.0"),
    "DashboardPage": ("templates.dashboard_page", "DashboardPage", "v0.6.0"),
    "SettingsPage": ("templates.settings_page", "SettingsPage", "v0.6.0"),

    # ---------- Core 规划中 ----------
    "app_store": ("core.state", "app_store", "v0.3.0"),
    "translator": ("core.i18n", "translator", "v0.5.0"),
    "t": ("core.i18n", "t", "v0.5.0"),
    "Token": ("core.theme.tokens", "Token", "v0.2.0"),
}


def __getattr__(name: str) -> Any:
    """
    PEP 562: 模块级懒加载（Lazy Import）。

    只有当用户显式访问 `pyside6_quasar.Table` 时，才会尝试导入对应子模块。
    这样即使组件未实现，也不会影响 `import pyside6_quasar` 本身。
    """
    # 1. 检查是否在"未来组件"名单中
    if name in _LAZY_COMPONENTS:
        module_path, class_name, planned_version = _LAZY_COMPONENTS[name]
        try:
            import importlib
            module = importlib.import_module(f".{module_path}", __name__)
            attr = getattr(module, class_name)
            # 缓存到模块字典，后续访问零开销
            globals()[name] = attr
            return attr
        except (ImportError, AttributeError):
            raise AttributeError(
                f"\n"
                f"╔══════════════════════════════════════════════════════════╗\n"
                f"║  '{name}' is not yet available in pyside6-quasar          \n"
                f"║  Current version: {__version__:<40}\n"
                f"║  Planned in:      {planned_version:<40}\n"
                f"║  Status:          🚧 In Development                       \n"
                f"║  Track progress:  {__url__}/releases                     \n"
                f"╚══════════════════════════════════════════════════════════╝\n"
            ) from None

    # 2. 未知属性，抛出标准错误
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}. "
        f"Did you mean one of: {', '.join(sorted(__all__)[:5])}...?"
    )


def __dir__() -> list[str]:
    """让 IDE 和 `dir(pyside6_quasar)` 能看到所有规划中的组件，方便自动补全。"""
    return sorted(list(__all__) + list(globals().keys()))


# ═══════════════════════════════════════════════════════════════
# 📋 完整愿景清单（IDE 自动补全 & 文档生成用）
# ═══════════════════════════════════════════════════════════════

__all__ = [
    # ============ 元信息 ============
    "__version__", "__version_info__",
    "__author__", "__license__", "__url__",

    # ============ L0 核心基建（已实现）============
    "theme_manager", "ThemeMode", "Color",
    "QBaseWidget", "QuasarWidgetMixin",
    "Router", "FormValidator", "ValidationRule",

    # ============ L1 基础组件（已实现）============
    "Button", "ButtonVariant", "ButtonSize", "ButtonShape",
    "Input", "Checkbox", "Switch",
    "Avatar", "AvatarShape", "AvatarSize",
    "Badge", "BadgeAlign",
    "LineProgress", "CircleProgress",

    # ============ L2 容器组件（已实现）============
    "Card", "CardSection", "CardActions", "CardMedia",
    "Tabs", "TabItem", "TabsAlign", "TabsIndicatorPosition",
    "Dialog",

    # ============ 反馈组件（已实现）============
    "Toast", "ToastType", "ToastPosition",
    "Tooltip", "TooltipPosition", "TooltipTransition",

    # ============ 规划中（懒加载）============
    # L0
    "app_store", "translator", "t", "Token",
    # L1
    "Radio", "Slider", "Chip",
    # L2
    "Drawer", "Collapse",
    # L3
    "Table", "TableColumn", "Select", "ListView", "TreeView",
    # Feedback
    "Notification",
    # Layouts & Templates
    "MainLayout", "AuthLayout", "BlankLayout",
    "LoginPage", "DashboardPage", "SettingsPage",
]


# ═══════════════════════════════════════════════════════════════
# 🔧 辅助工具函数
# ═══════════════════════════════════════════════════════════════

def get_available_components() -> Dict[str, bool]:
    """
    返回所有组件当前是否可用的字典。用于程序化检查或自检脚本。

    >>> from pyside6_quasar import get_available_components
    >>> avail = get_available_components()
    >>> [name for name, ok in avail.items() if ok]
    ['Button', 'Card', 'Input', ...]
    """
    result: Dict[str, bool] = {}
    for name in __all__:
        if name.startswith("__"):
            continue
        try:
            getattr(__import__(__name__), name)
            result[name] = True
        except AttributeError:
            result[name] = False
    return result


# ═══════════════════════════════════════════════════════════════
# 🛡️ 开发期自检（仅 __debug__ 模式下运行）
# ═══════════════════════════════════════════════════════════════

if __debug__:
    # 检查 __all__ 中每个名称要么可导入、要么在 _LAZY_COMPONENTS 中
    _missing = []
    for _name in __all__:
        if _name.startswith("__"):
            continue
        if _name not in _LAZY_COMPONENTS and _name not in globals():
            _missing.append(_name)

    if _missing:
        warnings.warn(
            f"pyside6_quasar: 以下组件既未导入也未在 _LAZY_COMPONENTS 中注册: "
            f"{_missing}\n"
            f"请检查 __init__.py 的导出清单是否与实际模块一致。",
            stacklevel=2,
        )
