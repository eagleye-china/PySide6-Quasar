# src/pyside_quasar/components/primitives/input.py
"""
pyside_quasar.components.primitives.input
==========================================
企业级输入框组件 (对标 Quasar QInput)
"""

from enum import Enum
from typing import Optional

from PySide6.QtCore import (
    Qt, QRectF, QPropertyAnimation, QEasingCurve, Property,
    QPointF, QEvent, QTimer, Signal
)
from PySide6.QtGui import QPainter, QColor, QPen, QIcon, QPainterPath, QFont
from PySide6.QtWidgets import QLineEdit, QLabel, QHBoxLayout, QPushButton

from ...core.base import (
    QBaseWidget,
    theme_manager,
    ThemeMode,
    Color,
)


class InputDesign(Enum):
    STANDARD = 1
    FILLED = 2
    OUTLINED = 3
    STANDOUT = 4
    BORDERLESS = 5


class Input(QBaseWidget):
    """企业级输入框。QBaseWidget 自动接管主题与焦点管理。"""

    textChanged = Signal(str)
    editingFinished = Signal()

    def __init__(
            self,
            text: str = "",
            placeholder: str = "",
            label: str = "",
            design: InputDesign = InputDesign.FILLED,
            dense: bool = False,
            rounded: bool = False,
            square: bool = False,
            bg_color: Optional[str] = None,
            color: str = Color.PRIMARY,
            clearable: bool = False,
            password: bool = False,
            readonly: bool = False,
            disable: bool = False,
            loading: bool = False,
            icon_left: Optional[str] = None,
            icon_right: Optional[str] = None,
            prefix: str = "",
            suffix: str = "",
            counter: bool = False,
            max_length: Optional[int] = None,
            error: bool = False,
            error_message: str = "",
            warning: bool = False,
            warning_message: str = "",
            success: bool = False,
            success_message: str = "",
            debounce: int = 0,
            parent=None,
    ):
        super().__init__(parent)

        self._design = design
        self._dense = dense
        self._rounded = rounded
        self._square = square
        self._color = QColor(color)
        self._custom_bg = bg_color
        self._bg_color = QColor()

        if dense:
            self._box_h = 36
            self._font_size = 12
            self._label_size = 10
            self._padding = 12
        else:
            self._box_h = 44
            self._font_size = 13
            self._label_size = 11
            self._padding = 16

        self._box_y = 12 if not dense else 8
        self.setFixedHeight(self._box_h + self._box_y + 20)

        self._clearable = clearable
        self._is_password = password
        self._readonly = readonly
        self._disable = disable
        self._loading = loading

        self._label_text = label or placeholder
        self._is_focused = False
        self._has_error = error
        self._has_warning = warning
        self._has_success = success
        self._error_message = error_message
        self._warning_message = warning_message
        self._success_message = success_message

        self._debounce_ms = debounce
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(lambda: self.textChanged.emit(self.get_text()))

        self._label_progress = 1.0 if text else 0.0
        self._anim = QPropertyAnimation(self, b"label_progress")
        self._anim.setDuration(150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._font_normal = QFont("Arial")
        self._font_normal.setPixelSize(self._font_size)
        self._font_small = QFont("Arial")
        self._font_small.setPixelSize(self._label_size)

        self._setup_ui(icon_left, prefix, suffix, counter, max_length)

        if max_length:
            self.line_edit.setMaxLength(max_length)
        if text:
            self.line_edit.setText(text)
            self._animate_label(1.0)
            if counter and max_length:
                self._update_counter()

        self.setEnabled(not disable)
        self.setAccessibleName(label or placeholder or "Input")
        self._update_theme_colors()

    @Property(float)
    def label_progress(self) -> float:
        return self._label_progress

    @label_progress.setter
    def label_progress(self, val: float):
        self._label_progress = val
        self.update()

    def _setup_ui(self, icon_left, prefix, suffix, counter, max_length):
        self._layout = QHBoxLayout(self)
        top_margin = (
            self._box_y + 10
            if self._design in (InputDesign.FILLED, InputDesign.OUTLINED)
            else self._box_y + 4
        )
        self._layout.setContentsMargins(self._padding, top_margin, 12, 8)
        self._layout.setSpacing(6)

        self._left_icon_label = None
        if icon_left:
            self._left_icon_label = QLabel()
            self._left_icon_label.setPixmap(QIcon(icon_left).pixmap(20, 20))
            self._left_icon_label.setStyleSheet("background: transparent;")
            self._layout.addWidget(self._left_icon_label)

        self._prefix_label = None
        if prefix:
            self._prefix_label = QLabel(prefix)
            self._layout.addWidget(self._prefix_label)

        self.line_edit = QLineEdit()
        self.line_edit.setStyleSheet("padding: 0px; border: none; background: transparent;")
        if self._is_password:
            self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.line_edit.installEventFilter(self)
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.returnPressed.connect(self.editingFinished.emit)
        self._layout.addWidget(self.line_edit, stretch=1)

        self._suffix_label = None
        if suffix:
            self._suffix_label = QLabel(suffix)
            self._layout.addWidget(self._suffix_label)

        self._right_btn = QPushButton()
        self._right_btn.setFixedSize(24, 24)
        self._right_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._right_btn.hide()
        self._right_btn.clicked.connect(self._on_right_btn_clicked)
        self._layout.addWidget(self._right_btn)

        self._message_label = QLabel(self)
        self._message_label.hide()
        self._counter_label = QLabel(self)
        self._counter_label.hide()
        if counter and max_length:
            self._counter_label.show()

    def _update_theme_colors(self):
        if self._custom_bg:
            self._bg_color = QColor(self._custom_bg)
        else:
            if self._design in (InputDesign.FILLED, InputDesign.STANDOUT):
                self._bg_color = QColor(theme_manager.get_color("surface"))
            else:
                self._bg_color = QColor(Qt.GlobalColor.transparent)

        text_primary = theme_manager.get_color("text_primary")
        text_secondary = theme_manager.get_color("text_secondary")

        self.line_edit.setStyleSheet(f"""
            QLineEdit {{ 
                background: transparent; border: none; 
                color: {text_primary}; font-size: {self._font_size}px; 
                padding: 0px;
                selection-background-color: {self._color.name()};
                selection-color: {text_primary};
            }}
            QLineEdit:disabled {{ color: {theme_manager.get_color("disabled")}; }}
        """)

        if self._prefix_label:
            self._prefix_label.setStyleSheet(
                f"color: {text_secondary}; font-size: {self._font_size}px; background: transparent;")
        if self._suffix_label:
            self._suffix_label.setStyleSheet(
                f"color: {text_secondary}; font-size: {self._font_size}px; background: transparent;")

        self._right_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {text_secondary}; border: none; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ color: {text_primary}; }}
            QPushButton:disabled {{ color: {theme_manager.get_color("disabled")}; }}
        """)

        self._counter_label.setStyleSheet(f"color: {text_secondary}; font-size: 11px; background: transparent;")
        self._update_message()
        self.update()

    def _on_theme_changed(self, mode: ThemeMode):
        self._update_theme_colors()
        super()._on_theme_changed(mode)

    def eventFilter(self, watched, event):
        if watched == self.line_edit:
            if event.type() == QEvent.Type.FocusIn:
                self._is_focused = True
                self._animate_label(1.0)
                self.update()
            elif event.type() == QEvent.Type.FocusOut:
                self._is_focused = False
                if not self.line_edit.text():
                    self._animate_label(0.0)
                self.update()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        if not self._disable:
            self.line_edit.setFocus()
        super().mousePressEvent(event)

    def _animate_label(self, target: float):
        self._anim.stop()
        self._anim.setStartValue(self._label_progress)
        self._anim.setEndValue(target)
        self._anim.start()

    def _on_text_changed(self, text):
        if self._clearable or self._is_password:
            self._right_btn.setVisible(bool(text) or self._is_password)
            if self._clearable and text:
                self._right_btn.setText("✕")
            elif self._is_password:
                self._right_btn.setText("👁")

        if text and self._label_progress == 0.0:
            self._animate_label(1.0)
        elif not text and not self._is_focused:
            self._animate_label(0.0)

        if self._counter_label.isVisible():
            self._update_counter()

        if self._debounce_ms > 0:
            self._debounce_timer.start(self._debounce_ms)
        else:
            self.textChanged.emit(text)

    def _update_counter(self):
        max_len = self.line_edit.maxLength()
        current = len(self.line_edit.text())
        self._counter_label.setText(f"{current}/{max_len}")
        self._counter_label.adjustSize()
        self._counter_label.move(
            self.width() - self._counter_label.width() - 12,
            self.height() - self._counter_label.height() - 2
        )

    def _on_right_btn_clicked(self):
        if self._clearable and self.line_edit.text():
            self.line_edit.clear()
        elif self._is_password:
            if self.line_edit.echoMode() == QLineEdit.EchoMode.Password:
                self.line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
                self._right_btn.setText("🙈")
            else:
                self.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
                self._right_btn.setText("👁")

    def set_error(self, message: str):
        self._has_error = True
        self._has_warning = False
        self._has_success = False
        self._error_message = message
        self._update_message()
        self.update()

    def set_warning(self, message: str):
        self._has_warning = True
        self._has_error = False
        self._has_success = False
        self._warning_message = message
        self._update_message()
        self.update()

    def set_success(self, message: str = ""):
        self._has_success = True
        self._has_error = False
        self._has_warning = False
        self._success_message = message
        self._update_message()
        self.update()

    def clear_error(self):
        self._has_error = False
        self._has_warning = False
        self._has_success = False
        self._message_label.hide()
        self.update()

    def _update_message(self):
        if self._has_error:
            self._message_label.setText(self._error_message)
            self._message_label.setStyleSheet(f"color: {Color.NEGATIVE}; font-size: 11px; background: transparent;")
        elif self._has_warning:
            self._message_label.setText(self._warning_message)
            self._message_label.setStyleSheet(f"color: {Color.WARNING}; font-size: 11px; background: transparent;")
        elif self._has_success and self._success_message:
            self._message_label.setText(self._success_message)
            self._message_label.setStyleSheet(f"color: {Color.POSITIVE}; font-size: 11px; background: transparent;")
        else:
            self._message_label.hide()
            return
        self._message_label.adjustSize()
        self._message_label.move(self._padding, self._box_y + self._box_h + 2)
        self._message_label.show()

    def get_text(self) -> str:
        return self.line_edit.text()

    def set_text(self, text: str):
        self.line_edit.setText(text)

    def set_placeholder(self, text: str):
        self._label_text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(1, self._box_y, self.width() - 2, self._box_h)
        radius = 0 if self._square else (self._box_h / 2 if self._rounded else 6)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        if self._design == InputDesign.FILLED:
            painter.fillPath(path, self._bg_color)
        elif self._design == InputDesign.STANDOUT:
            painter.fillPath(path, self._bg_color.darker(120))
        elif self._design == InputDesign.BORDERLESS:
            pass
        else:
            painter.fillPath(path, QColor(Qt.GlobalColor.transparent))

        border_color = self._get_border_color()
        border_width = self._get_border_width()

        if self._design in (InputDesign.OUTLINED, InputDesign.STANDOUT):
            pen = QPen(border_color, border_width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
        elif self._design in (InputDesign.STANDARD, InputDesign.FILLED):
            pen = QPen(border_color, border_width if not self._is_focused else 2)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(rect.left(), rect.top() + self._box_h),
                QPointF(rect.right(), rect.top() + self._box_h)
            )

        if self._label_text:
            self._draw_label(painter, rect)

        if self._loading:
            self._draw_loading(painter, rect)

    def _get_border_color(self) -> QColor:
        if self._disable:
            return QColor(theme_manager.get_color("border"))
        if self._has_error:
            return QColor(Color.NEGATIVE)
        if self._has_warning:
            return QColor(Color.WARNING)
        if self._has_success:
            return QColor(Color.POSITIVE)
        if self._is_focused:
            return self._color
        return QColor(theme_manager.get_color("border"))

    def _get_border_width(self) -> float:
        if self._is_focused or self._has_error:
            return 2.0
        return 1.0

    def _draw_label(self, painter, rect):
        start_x = self._padding
        if self._left_icon_label:
            start_x += 26
        if self._prefix_label:
            start_x += self._prefix_label.width() + 6

        if self._label_progress > 0.5:
            painter.setFont(self._font_small)
            if self._has_error:
                color = QColor(Color.NEGATIVE)
            elif self._has_warning:
                color = QColor(Color.WARNING)
            elif self._has_success:
                color = QColor(Color.POSITIVE)
            elif self._is_focused:
                color = self._color
            else:
                color = QColor(theme_manager.get_color("text_secondary"))
        else:
            painter.setFont(self._font_normal)
            color = QColor(theme_manager.get_color("text_secondary"))

        painter.setPen(color)

        fm = painter.fontMetrics()
        text_h = fm.height()
        text_w = fm.horizontalAdvance(self._label_text)

        y_center_in = rect.center().y() - 1
        if self._design in (InputDesign.OUTLINED, InputDesign.STANDOUT):
            y_center_out = rect.top()
        else:
            y_center_out = rect.top() + text_h / 2 + 2

        current_center_y = y_center_in + (y_center_out - y_center_in) * self._label_progress

        if self._label_progress > 0.1 and self._design in (InputDesign.OUTLINED, InputDesign.STANDOUT):
            bg_rect = QRectF(start_x - 4, current_center_y - text_h / 2, text_w + 8, text_h)
            painter.fillRect(bg_rect, QColor(theme_manager.get_color("surface")))

        target_rect = QRectF(start_x, current_center_y - text_h / 2, text_w + 10, text_h)
        painter.drawText(target_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._label_text)

    def _draw_loading(self, painter, rect):
        spinner_size = 18
        cx = rect.right() - 28
        cy = rect.center().y()

        pen = QPen(QColor(theme_manager.get_color("text_secondary")))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(
            QRectF(cx - spinner_size / 2, cy - spinner_size / 2, spinner_size, spinner_size),
            0, 270 * 16
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._message_label.isVisible():
            self._message_label.move(self._padding, self._box_y + self._box_h + 2)
        if self._counter_label.isVisible():
            self._counter_label.move(
                self.width() - self._counter_label.width() - 12,
                self.height() - self._counter_label.height() - 2
            )
