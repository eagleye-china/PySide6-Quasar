# src/pyside6_quasar/components/primitives/button.py
"""
pyside6_quasar.components.primitives.button
===========================================
企业级按钮组件 (对标 Quasar QBtn)
"""

import math
import re
from enum import Enum
from typing import Union, Optional

from PySide6.QtCore import (
    Qt, QTimer, QRectF, QSize, QPropertyAnimation, QEasingCurve,
    Property, QPointF
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QIcon, QPainterPath, QLinearGradient, QBrush,
    QFocusEvent
)
from PySide6.QtWidgets import QPushButton
from typing_extensions import override

from ...core.base import (
    QuasarWidgetMixin,
    theme_manager,
    Color,
    get_contrast_color,
)
from ...core.mixins.badge_mixin import BadgeMixin


# ═══════════════════════════════════════════════════════════════
# 枚举定义
# ═══════════════════════════════════════════════════════════════

class ButtonVariant(Enum):
    FILLED = 1
    OUTLINE = 2
    FLAT = 3
    PUSH = 4


class ButtonShape(Enum):
    RECTANGLE = 1
    ROUNDED = 2
    ROUND = 3
    SQUARE = 4


class ButtonSize(Enum):
    XS = 20
    SM = 24
    MD = 32
    LG = 40
    XL = 48


_SIZE_MAP = {"xs": 20, "sm": 24, "md": 32, "lg": 40, "xl": 48}


def _parse_size(size: Union[int, str, ButtonSize]) -> int:
    if isinstance(size, ButtonSize):
        return size.value
    if isinstance(size, int):
        return size
    if isinstance(size, str):
        s = size.strip().lower()
        if s in _SIZE_MAP:
            return _SIZE_MAP[s]
        m = re.match(r"^(\d+(?:\.\d+)?)\s*(px)?$", s)
        if m:
            return int(float(m.group(1)))
    return ButtonSize.MD.value


# ═══════════════════════════════════════════════════════════════
# Button 主体
# ═══════════════════════════════════════════════════════════════

class Button(QPushButton, QuasarWidgetMixin, BadgeMixin):
    """
    企业级按钮。
    - 原生控件继承：QPushButton + QuasarWidgetMixin
    - 主题/焦点：通过 setup_quasar() 挂载
    """

    def __init__(
            self,
            text: str = "",
            icon: Optional[Union[str, QIcon]] = None,
            icon_right: Optional[Union[str, QIcon]] = None,
            color: str = Color.PRIMARY,
            text_color: Optional[str] = None,
            variant: Union[ButtonVariant, str] = ButtonVariant.FILLED,
            shape: Union[ButtonShape, str] = ButtonShape.ROUNDED,
            size: Union[int, str, ButtonSize] = ButtonSize.MD,
            fab: bool = False,
            fab_mini: bool = False,
            unelevated: bool = False,
            glossy: bool = False,
            stack: bool = False,
            no_caps: bool = False,
            padding: Optional[str] = None,
            ripple: bool = True,
            parent=None,
    ):
        # ★ 只调用一次原生控件初始化
        super().__init__(text, parent)
        # ★ 手动挂载主题与焦点管理
        self.setup_quasar()

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # ─── 字符串 → 枚举 ───
        if isinstance(variant, str):
            try:
                variant = ButtonVariant[variant.upper()]
            except KeyError:
                variant = ButtonVariant.FILLED
        if isinstance(shape, str):
            try:
                shape = ButtonShape[shape.upper()]
            except KeyError:
                shape = ButtonShape.ROUNDED

        self._variant = variant
        self._shape = shape
        self._size_val = _parse_size(size)
        self._fab = fab
        self._fab_mini = fab_mini
        self._unelevated = unelevated
        self._glossy = glossy
        self._stack = stack
        self._no_caps = no_caps
        self._ripple_enabled = ripple

        # ─── 尺寸 ───
        if fab or fab_mini:
            self._size_val = 56 if fab else 40
            self.setFixedSize(self._size_val, self._size_val)
        elif shape == ButtonShape.ROUND:
            self.setFixedSize(self._size_val, self._size_val)
        else:
            self.setMinimumHeight(self._size_val)
            self.setMinimumWidth(self._size_val * 2 if not self._fab else self._size_val)

        self._bg_color = QColor(color)
        self._explicit_text_color = QColor(text_color) if text_color else None

        self._icon_left = self._coerce_icon(icon)
        self._icon_right = self._coerce_icon(icon_right)
        self._custom_padding = self._parse_padding(padding) if padding else None

        # ─── Loading ───
        self._is_loading = False
        self._percentage: Optional[float] = None
        self._loading_angle = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._update_loading)

        # ─── Ripple ───
        self._ripple_pos = QPointF(0, 0)
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self._ripple_anim = QPropertyAnimation(self, b"ripple_radius")
        self._ripple_anim.setDuration(400)
        self._ripple_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        # 彻底屏蔽 Qt 原生虚线焦点框
        self.setStyleSheet("""
            QPushButton { 
                border: none; 
                background: transparent; 
                outline: none; 
            }
        """)
        self.setFlat(True)

    # ═══════════════════════════════════════════════════════════
    # Ripple Property
    # ═══════════════════════════════════════════════════════════

    @Property(float)
    def ripple_radius(self) -> float:
        return self._ripple_radius

    @ripple_radius.setter
    def ripple_radius(self, r: float):
        self._ripple_radius = r
        progress = r / max(1.0, self._max_ripple_radius())
        self._ripple_opacity = max(0.0, 1.0 - progress)
        self.update()

    def _max_ripple_radius(self) -> float:
        return math.hypot(self.width(), self.height())

    # ═══════════════════════════════════════════════════════════
    # 交互与焦点
    # ═══════════════════════════════════════════════════════════

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._show_focus_ring = False
            if not self._is_loading and self._ripple_enabled:
                self._ripple_pos = event.position()
                self._ripple_anim.stop()
                self._ripple_anim.setStartValue(0.0)
                self._ripple_anim.setEndValue(self._max_ripple_radius())
                self._ripple_anim.start()
        super().mousePressEvent(event)

    def focusInEvent(self, event: QFocusEvent):
        self._handle_focus_in(event)
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        self._handle_focus_out(event)
        super().focusOutEvent(event)

    # ═══════════════════════════════════════════════════════════
    # 公共 API
    # ═══════════════════════════════════════════════════════════

    def set_loading(self, loading: bool, percentage: Optional[float] = None):
        self._is_loading = loading
        self._percentage = percentage
        if loading:
            self.setEnabled(False)
            self._loading_timer.start(50)
        else:
            self.setEnabled(True)
            self._loading_timer.stop()
        self.update()

    def set_percentage(self, value: Optional[float]):
        self._percentage = value
        self.update()

    def _update_loading(self):
        self._loading_angle = (self._loading_angle + 30) % 360
        self.update()

    # ═══════════════════════════════════════════════════════════
    # 尺寸提示
    # ═══════════════════════════════════════════════════════════

    @override
    def sizeHint(self) -> QSize:
        if self._fab or self._fab_mini or self._shape == ButtonShape.ROUND:
            return QSize(self._size_val, self._size_val)

        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self._text_with_caps())

        icon_w = 0
        if self._icon_left and not self._icon_left.isNull():
            icon_w += self._icon_px()
        if self._icon_right and not self._icon_right.isNull():
            icon_w += self._icon_px()
        spacing = 6 if icon_w > 0 and text_w > 0 else 0

        pad_h = self._custom_padding[1] if self._custom_padding else 16
        total_w = max(self._size_val * 2, text_w + icon_w + spacing + pad_h * 2)
        return QSize(total_w, self._size_val)

    # ═══════════════════════════════════════════════════════════
    # 绘制主入口
    # ═══════════════════════════════════════════════════════════

    @override
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(self.rect())
        radius = self._get_radius(rect)

        is_hover = self.underMouse()
        is_down = self.isDown()
        is_disabled = not self.isEnabled() and not self._is_loading

        c_bg = QColor(self._bg_color)
        if is_disabled:
            c_bg.setAlpha(120)
        elif is_down and self._variant != ButtonVariant.PUSH:
            c_bg = c_bg.darker(115)
        elif is_hover and self._variant != ButtonVariant.PUSH:
            c_bg = c_bg.lighter(110)

        if self._explicit_text_color:
            c_text = QColor(self._explicit_text_color)
        else:
            c_text = QColor(get_contrast_color(self._bg_color.name()))
        if is_disabled:
            c_text.setAlpha(120)

        # 阴影
        if not self._unelevated and self._variant not in (
                ButtonVariant.FLAT, ButtonVariant.OUTLINE, ButtonVariant.PUSH
        ) and not is_disabled:
            self._draw_shadow(painter, rect, radius, is_down, is_hover)

        # 背景 / 边框 / Push
        if self._variant == ButtonVariant.PUSH:
            self._draw_push_base(painter, rect, radius, c_bg, is_down, is_disabled)
        elif self._variant in (ButtonVariant.FILLED, ButtonVariant.PUSH):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._glossy_brush(rect, c_bg))
            painter.drawRoundedRect(rect, radius, radius)
        elif self._variant == ButtonVariant.OUTLINE:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen = QPen(c_bg, 2)
            if is_hover: pen.setColor(c_bg.lighter(110))
            if is_disabled: pen.setColor(c_bg)
            painter.setPen(pen)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)
            c_text = c_bg
        elif self._variant == ButtonVariant.FLAT:
            if is_hover and not is_disabled:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(theme_manager.get_color("hover")))
                painter.drawRoundedRect(rect, radius, radius)
            c_text = QColor(self._bg_color)

        # Ripple
        if self._ripple_radius > 0 and self._ripple_opacity > 0 and self._ripple_enabled:
            self._draw_ripple(painter, rect, radius)

        # Loading
        if self._is_loading:
            self._draw_loading_overlay(painter, rect, radius, c_text)
            self._draw_focus_ring(painter, rect, radius, is_disabled)
            return

        self._draw_content(painter, rect, c_text)
        self._draw_focus_ring(painter, rect, radius, is_disabled)

    # ═══════════════════════════════════════════════════════════
    # 绘制辅助
    # ═══════════════════════════════════════════════════════════

    def _get_radius(self, rect: QRectF) -> float:
        if self._shape == ButtonShape.ROUND or self._fab or self._fab_mini:
            return rect.height() / 2
        if self._shape in (ButtonShape.SQUARE, ButtonShape.RECTANGLE):
            return 0
        return 4

    def _draw_shadow(self, painter, rect, radius, is_down, is_hover):
        if theme_manager.is_dark():
            base_alpha = 80 if is_hover and not is_down else (40 if is_down else 60)
        else:
            base_alpha = 50 if is_hover and not is_down else (20 if is_down else 30)
        offset = 4 if is_hover and not is_down else (1 if is_down else 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, base_alpha))
        painter.drawRoundedRect(rect.translated(0, offset), radius, radius)

    def _draw_push_base(self, painter, rect, radius, c_bg, is_down, is_disabled):
        base = c_bg.darker(140) if not is_disabled else QColor(0, 0, 0, 50)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(base)
        painter.drawRoundedRect(rect.translated(0, 3), radius, radius)
        top_rect = rect.translated(0, 1) if is_down else rect
        painter.setBrush(self._glossy_brush(top_rect, c_bg))
        painter.drawRoundedRect(top_rect, radius, radius)

    def _glossy_brush(self, rect, base):
        if not self._glossy:
            return QBrush(base)
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0.0, QColor(min(255, base.red() + 40), min(255, base.green() + 40), min(255, base.blue() + 40)))
        grad.setColorAt(0.5, base)
        grad.setColorAt(1.0, base.darker(110))
        return QBrush(grad)

    def _draw_ripple(self, painter, rect, radius):
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)

        if self._variant in (ButtonVariant.OUTLINE, ButtonVariant.FLAT):
            ripple_color = QColor(theme_manager.get_color("text_primary"))
        else:
            ripple_color = QColor(255, 255, 255) if get_contrast_color(
                self._bg_color.name()) == Color.WHITE else QColor(0, 0, 0)

        ripple_color.setAlphaF(self._ripple_opacity * 0.3)
        painter.setBrush(ripple_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self._ripple_pos, self._ripple_radius, self._ripple_radius)
        painter.restore()

    def _draw_loading_overlay(self, painter, rect, radius, c_text):
        if self._percentage is not None:
            pct = max(0.0, min(100.0, self._percentage))
            bar_rect = QRectF(rect.left(), rect.bottom() - 3, rect.width() * (pct / 100.0), 3)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c_text)
            path = QPainterPath()
            path.addRoundedRect(rect, radius, radius)
            painter.save()
            painter.setClipPath(path)
            painter.drawRect(bar_rect)
            painter.restore()

        pen = QPen(c_text)
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(rect.adjusted(10, 10, -10, -10), self._loading_angle * 16, 120 * 16)

    def _draw_content(self, painter, rect, c_text):
        painter.setPen(c_text)
        font = self.font()
        font.setBold(True)
        if self._size_val <= 24:
            font.setPixelSize(11)
        elif self._size_val >= 48:
            font.setPixelSize(18)
        elif self._size_val >= 40:
            font.setPixelSize(16)
        else:
            font.setPixelSize(14)
        painter.setFont(font)

        text = self._text_with_caps()
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(text)
        icon_sz = self._icon_px()

        left_icon = self._icon_left if self._icon_left and not self._icon_left.isNull() else None
        right_icon = self._icon_right if self._icon_right and not self._icon_right.isNull() else None

        if self._stack:
            total_h = icon_sz * 2 + 4 if (left_icon and text_w > 0) else icon_sz
            start_y = (rect.height() - total_h) / 2
            if left_icon:
                pix = left_icon.pixmap(QSize(icon_sz, icon_sz))
                painter.drawPixmap(int((rect.width() - icon_sz) / 2), int(start_y), pix)
                start_y += icon_sz + 4
            if text_w > 0:
                painter.drawText(QRectF(0, start_y, rect.width(), fm.height()),
                                 Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)
        else:
            total_w = 0
            if left_icon: total_w += icon_sz
            if right_icon: total_w += icon_sz
            if text_w > 0 and total_w > 0: total_w += 6
            total_w += text_w

            start_x = (rect.width() - total_w) / 2
            center_y = rect.height() / 2

            if left_icon:
                pix = left_icon.pixmap(QSize(icon_sz, icon_sz))
                painter.drawPixmap(int(start_x), int(center_y - icon_sz / 2), pix)
                start_x += icon_sz + 6
            if text_w > 0:
                painter.drawText(QRectF(start_x, 0, text_w, rect.height()),
                                 Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
                start_x += text_w + 6
            if right_icon:
                pix = right_icon.pixmap(QSize(icon_sz, icon_sz))
                painter.drawPixmap(int(start_x), int(center_y - icon_sz / 2), pix)

    def _draw_focus_ring(self, painter, rect, radius, is_disabled):
        if self._show_focus_ring and self.hasFocus() and not is_disabled:
            painter.save()
            color = QColor(255, 255, 255, 180) if self._variant in (
                ButtonVariant.FILLED, ButtonVariant.PUSH
            ) else QColor(self._bg_color)
            if color != QColor(255, 255, 255, 180):
                color.setAlpha(180)
            pen = QPen(color, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(3, 3, -3, -3), max(0, radius - 2), max(0, radius - 2))
            painter.restore()

    # ═══════════════════════════════════════════════════════════
    # 工具
    # ═══════════════════════════════════════════════════════════

    def _icon_px(self) -> int:
        if self._size_val <= 24: return 14
        if self._size_val >= 48: return 24
        return 18

    def _text_with_caps(self) -> str:
        t = self.text()
        return t if self._no_caps else t.upper()

    @staticmethod
    def _coerce_icon(icon) -> Optional[QIcon]:
        return QIcon(icon) if isinstance(icon, str) else icon

    @staticmethod
    def _parse_padding(padding: str) -> tuple[int, int]:
        parts = padding.strip().lower().split()

        def _one(p: str) -> int:
            if p in _SIZE_MAP: return _SIZE_MAP[p] // 2
            m = re.match(r"(\d+)(px)?", p)
            return int(m.group(1)) if m else 8

        if len(parts) == 1:
            return _one(parts[0]), _one(parts[0])
        return _one(parts[0]), _one(parts[-1])
