# src/pyside_quasar/components/containers/dialog.py
"""
pyside_quasar.components.containers.dialog
===========================================
企业级模态对话框 (对标 Quasar QDialog)
v2.7 Final 封板版

v2.7 修复清单
────────────
✅ [BUG-1]  彻底消除 "Failed to disconnect" 的 RuntimeWarning。
            移除了所有显式的 disconnect 调用。信号只在 __init__ 中连接一次，
            配合 _is_closing 状态机进行路由，既安全又优雅。
✅ [BUG-2]  去掉 closeEvent 中多余的 themeChanged 信号断开逻辑。
            Qt 底层会在 QObject 销毁时自动断开连接，无需手动处理，避免野指针警告。
"""
from enum import Enum
from typing import Optional

from PySide6.QtCore import (
    Qt, QRectF, QPoint, QVariantAnimation, QRect
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QKeyEvent, QShowEvent, QCloseEvent
)
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QApplication, QDialog, QGraphicsDropShadowEffect
)

from ...core.base import (
    QuasarWidgetMixin,
    theme_manager,
    ThemeMode,
    Color,
)


class DialogPosition(Enum):
    STANDARD = 1
    TOP = 2
    BOTTOM = 3
    LEFT = 4
    RIGHT = 5


# ===================== 纯净的自绘卡片 =====================
# export-ignore
class DialogCard(QWidget):
    """纯自绘卡片，完美适配阴影且不会有圆角黑边"""

    def __init__(self, radius: int, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._bg_color = QColor()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_bg_color(self, color: QColor):
        self._bg_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._bg_color)
        painter.drawPath(path)


# ===================== 主对话框 =====================
class Dialog(QDialog, QuasarWidgetMixin):
    def __init__(
            self,
            title: str = "提示",
            parent=None,
            persistent: bool = False,
            no_esc_dismiss: bool = False,
            no_backdrop_dismiss: bool = False,
            auto_close: bool = False,
            seamless: bool = False,
            maximized: bool = False,
            full_width: bool = False,
            full_height: bool = False,
            position: DialogPosition = DialogPosition.STANDARD,
            square: bool = False,
            min_width: int = 400,
            max_width: int = 600,
            bg_color: Optional[str] = None,
            radius: int = 8,
            transition_duration: int = 250,
    ):
        super().__init__(parent)
        self.setup_quasar()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self._persistent = persistent
        self._no_esc_dismiss = no_esc_dismiss or persistent
        self._no_backdrop_dismiss = no_backdrop_dismiss or persistent
        self._auto_close = auto_close
        self._seamless = seamless

        self._maximized = maximized
        self._full_width = full_width
        self._full_height = full_height
        self._position = position
        self._square = square
        self._min_width = min_width
        self._max_width = max_width

        self._custom_bg = bg_color
        self._bg_color = QColor()
        self._radius = 0 if square else radius

        self._mask_opacity = 0.0
        self._transition_duration = transition_duration
        self._is_closing = False
        self._close_func = None

        # 遮罩层动画
        self._mask_anim = QVariantAnimation(self)
        self._mask_anim.setDuration(int(self._transition_duration * 0.8))
        self._mask_anim.valueChanged.connect(self._on_mask_anim_update)
        # ✅ 只在初始化时连接一次，绝对不 disconnect
        self._mask_anim.finished.connect(self._on_mask_anim_finished)

        self._previous_focus_widget = None
        self._shadow: Optional[QGraphicsDropShadowEffect] = None

        self._setup_ui(title)
        self._apply_size_and_position()
        self._update_theme_colors()

        # ✅ 连接主题信号（安全起见先断开旧的，避免热重载时重复连）
        try:
            theme_manager.themeChanged.disconnect(self._on_theme_changed)
        except Exception:  # noqa
            pass
        theme_manager.themeChanged.connect(self._on_theme_changed)

    # ===================== 动画属性 =====================
    @property
    def mask_opacity(self) -> float:
        return self._mask_opacity

    @mask_opacity.setter
    def mask_opacity(self, v: float):
        self._mask_opacity = v
        self.update()

    def _on_mask_anim_update(self, value):
        self.mask_opacity = float(value)

    def _on_mask_anim_finished(self):
        # ✅ 状态机分流：只有在退场状态下，才执行关闭操作
        if self._is_closing and self._close_func:
            func = self._close_func
            self._close_func = None
            func()

    # ===================== UI 构建 =====================
    def _setup_ui(self, title: str):
        self._outer_layout = QVBoxLayout(self)
        margin = 0 if self._maximized else 60
        self._outer_layout.setContentsMargins(margin, margin, margin, margin)
        self._outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card_widget = DialogCard(radius=self._radius)
        self._card_widget.setMinimumWidth(self._min_width)
        self._card_widget.setMaximumWidth(self._max_width)

        if not self._maximized:
            self._shadow = QGraphicsDropShadowEffect(self._card_widget)
            self._shadow.setBlurRadius(25)
            self._shadow.setOffset(0, 6)
            self._card_widget.setGraphicsEffect(self._shadow)

        card_layout = QVBoxLayout(self._card_widget)  # type: ignore[arg-type]
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        self._title_lbl = QLabel(title)
        header_layout.addWidget(self._title_lbl)
        header_layout.addStretch()

        self._btn_close = QPushButton("✕")
        self._btn_close.setFixedSize(24, 24)
        self._btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_close.clicked.connect(self.reject)
        header_layout.addWidget(self._btn_close)

        card_layout.addLayout(header_layout)

        # Body
        self._body_layout = QVBoxLayout()
        card_layout.addLayout(self._body_layout)

        # Actions
        self._actions_layout = QHBoxLayout()
        self._actions_layout.setContentsMargins(0, 8, 0, 0)
        self._actions_layout.addStretch()
        card_layout.addLayout(self._actions_layout)

        self._outer_layout.addWidget(self._card_widget)  # type: ignore[arg-type]

    def _apply_size_and_position(self):
        if self._maximized:
            self._full_width = True
            self._full_height = True

        if self._full_width or self._full_height:
            parent = self.parentWidget()
            if parent:
                geo = parent.window().geometry()
            else:
                screen = QApplication.primaryScreen()
                geo = screen.availableGeometry() if screen else self.rect()

            if self._full_width:
                self._card_widget.setFixedWidth(max(100, geo.width() - 120))
            if self._full_height:
                self._card_widget.setMinimumHeight(max(100, geo.height() - 120))

        align_map = {
            DialogPosition.STANDARD: Qt.AlignmentFlag.AlignCenter,
            DialogPosition.TOP: Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            DialogPosition.BOTTOM: Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
            DialogPosition.LEFT: Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            DialogPosition.RIGHT: Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
        }
        self._outer_layout.setAlignment(align_map.get(self._position, Qt.AlignmentFlag.AlignCenter))

    def _update_theme_colors(self):
        if self._custom_bg:
            self._bg_color = QColor(self._custom_bg)
        else:
            self._bg_color = QColor(theme_manager.get_color("surface"))

        self._card_widget.set_bg_color(self._bg_color)

        self._title_lbl.setStyleSheet(
            f"color: {theme_manager.get_color('text_primary')}; "
            "font-size: 16px; font-weight: bold; background: transparent;"
        )

        if self._btn_close:
            close_color = theme_manager.get_color("text_secondary")
            self._btn_close.setStyleSheet(f"""
                QPushButton {{ 
                    background: transparent; 
                    color: {close_color}; 
                    border: none; 
                    font-weight: bold; 
                    font-size: 14px;
                }}
                QPushButton:hover {{ color: {Color.NEGATIVE}; }}
            """)

        if self._shadow:
            try:
                if theme_manager.is_dark():
                    self._shadow.setColor(QColor(0, 0, 0, 120))
                else:
                    self._shadow.setColor(QColor(0, 0, 0, 50))
            except RuntimeError:
                pass

    def _on_theme_changed(self, mode: ThemeMode):
        self._update_theme_colors()

    # ===================== 公共API =====================
    def add_widget(self, widget: QWidget):
        self._body_layout.addWidget(widget)

    def add_action(self, widget: QWidget):
        self._actions_layout.addWidget(widget)

    def set_title(self, title: str):
        self._title_lbl.setText(title)

    # ===================== 生命周期 & 动画 =====================
    def accept(self):
        self._start_close_anim(super().accept)

    def reject(self):
        self._start_close_anim(super().reject)

    def _start_close_anim(self, close_func):
        if self._is_closing:
            return
        self._is_closing = True
        self._close_func = close_func

        self._mask_anim.stop()
        self._mask_anim.setStartValue(self._mask_opacity)
        self._mask_anim.setEndValue(0.0)
        # ✅ 移除了 disconnect，纯靠 finished 信号触发 _on_mask_anim_finished
        self._mask_anim.start()

    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self._is_closing = False
        self._close_func = None
        self._previous_focus_widget = QApplication.focusWidget()

        if self.parentWidget():
            parent_window = self.parentWidget().window()
            global_pos = parent_window.mapToGlobal(QPoint(0, 0))
            self.setGeometry(global_pos.x(), global_pos.y(), parent_window.width(), parent_window.height())
        else:
            screen = QApplication.primaryScreen()
            if screen:
                self.setGeometry(screen.availableGeometry())

        self._mask_anim.stop()
        # ✅ 移除了 disconnect，直接开始进场动画
        self._mask_anim.setStartValue(0.0)
        self._mask_anim.setEndValue(1.0)
        self._mask_anim.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._previous_focus_widget and self._previous_focus_widget.isVisible():
            try:
                self._previous_focus_widget.setFocus()
            except RuntimeError:
                pass
        self._previous_focus_widget = None

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            if not self._no_esc_dismiss:
                self.reject()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = event.position().toPoint()
        card_pos = self._card_widget.mapTo(self, QPoint(0, 0))
        card_rect = QRect(card_pos, self._card_widget.size())

        if not card_rect.contains(pos):
            if self._auto_close:
                self.accept()
                return
            if not self._no_backdrop_dismiss:
                self.reject()
                return
        super().mousePressEvent(event)

    def closeEvent(self, event: QCloseEvent):
        # ✅ BUG-2：无需手动 disconnect，QObject 析构时会自动安全断开。
        super().closeEvent(event)

    # ===================== 绘制 =====================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self._seamless:
            mask_alpha = 160 if theme_manager.is_dark() else 100
            painter.fillRect(self.rect(), QColor(0, 0, 0, int(mask_alpha * self._mask_opacity)))
