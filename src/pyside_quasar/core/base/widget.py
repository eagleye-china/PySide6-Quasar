# src/pyside_quasar/core/base/widget.py
from PySide6.QtCore import Qt
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QWidget

from ..theme.manager import theme_manager, ThemeMode
from ..utils.dpr import get_dpr


class QuasarWidgetMixin:
    """
    Quasar 组件混入类 (Mixin)。
    为了兼容原生控件（如 QPushButton）的多重继承，这个类不继承 QWidget。
    """

    def setup_quasar(self):
        """所有组件在 __init__ 时必须手动调用此方法以挂载主题和焦点管理"""
        theme_manager.themeChanged.connect(self._on_theme_changed)
        if isinstance(self, QWidget):
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._show_focus_ring = False

    def _on_theme_changed(self, mode: ThemeMode):
        """收到主题切换信号时触发，子类可重写，但必须调用 super()"""
        if hasattr(self, "update"):
            self.update()
        self.refresh_theme_qss()

    def refresh_theme_qss(self):
        """供子类重写：用于更新内部原生控件（如 QLineEdit）的 QSS"""
        pass

    def _handle_focus_in(self, event: QFocusEvent):
        if event.reason() != Qt.FocusReason.MouseFocusReason:
            self._show_focus_ring = True
        if hasattr(self, "update"):
            self.update()

    def _handle_focus_out(self, event: QFocusEvent):  # noqa
        self._show_focus_ring = False
        if hasattr(self, "update"):
            self.update()


class QBaseWidget(QWidget, QuasarWidgetMixin):
    """
    PyQuasar 纯自绘组件的终极基类（用于 Card, Tabs, Progress 等）。
    注意：对于 Button, Input 等原生控件，请继承原生控件 + QuasarWidgetMixin。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_quasar()

    @property
    def dpr(self) -> float:
        """动态获取当前屏幕的 DPR，支持跨屏幕拖拽时保持高清"""
        return get_dpr(self)

    def px(self, logical_px: int) -> int:
        """逻辑像素转物理像素（用于精细绘制）"""
        return int(logical_px * self.dpr)

    def focusInEvent(self, event: QFocusEvent):
        self._handle_focus_in(event)
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        self._handle_focus_out(event)
        super().focusOutEvent(event)
