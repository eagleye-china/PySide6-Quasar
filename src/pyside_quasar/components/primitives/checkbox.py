# quasar/components/checkbox.py
"""
pyside_quasar.components.checkbox
==================================
企业级复选框 (对标 Quasar QCheckbox)
v2.3 Final 封板版

v2.3 修复清单
────────────
✅ [BUG-1]  修复对勾变成斜线：修正了 QPainterPath.pointAtPercent 的计算逻辑，
            改为分段计算 p1->p2 和 p2->p3 的坐标插值，完美还原对勾形状。
✅ [BUG-2]  优化对勾坐标比例：p1/p2/p3 的坐标更加匀称，视觉更平衡。
✅ [BUG-3]  尺寸解析支持字符串 "xs" / "sm" 等，且严格按 box_size + edge*2 计算高度。
✅ [BUG-4]  Dense 模式紧凑：动态 _edge / _gap，完美瘦身。
✅ [BUG-5]  半选横线按 progress 从中心向两端生长。
"""

from enum import Enum
from typing import Optional, Union

from PySide6.QtCore import (
    Qt, QPropertyAnimation, Property, QEasingCurve, Signal,
    QRectF, QPointF, QSize,
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QFont, QFontMetrics, QIcon, QPen,
)

from ...core.base import QBaseWidget
from ...core.theme import theme_manager, ThemeMode
from ...core.theme.contrast import get_contrast_color
from ...core.theme.palette import Color


# ───────────────────────────── 枚举 ─────────────────────────────
class CheckboxSize(Enum):
    XS = 16
    SM = 18
    MD = 20
    LG = 24
    XL = 28


_SIZE_MAP = {
    "xs": CheckboxSize.XS.value,
    "sm": CheckboxSize.SM.value,
    "md": CheckboxSize.MD.value,
    "lg": CheckboxSize.LG.value,
    "xl": CheckboxSize.XL.value,
}


class CheckboxState(Enum):
    UNCHECKED = 0
    CHECKED = 1
    INDETERMINATE = 2


# ───────────────────────────── 主体 ─────────────────────────────
class Checkbox(QBaseWidget):
    """
    企业级复选框。
    支持三态切换、自定义图标、勾号生长动画、主题自适应、
    键盘焦点环、无障碍支持。
    """
    toggled = Signal(bool)
    stateChanged = Signal(int)

    _FOCUS_RING_WIDTH = 2.0
    _FOCUS_RING_OFFSET = 2.5

    def __init__(
            self,
            text: str = "",
            checked: bool = False,
            color: str = Color.PRIMARY,
            keep_color: bool = False,
            left_label: bool = False,
            dense: bool = False,
            size: Union[int, str, CheckboxSize] = CheckboxSize.MD,
            dark: bool = True,
            disabled: bool = False,
            checked_icon: Optional[Union[str, QIcon]] = None,
            unchecked_icon: Optional[Union[str, QIcon]] = None,
            indeterminate_icon: Optional[Union[str, QIcon]] = None,
            toggle_indeterminate: bool = False,
            toggle_order: str = "tf",
            parent=None,
    ):
        super().__init__(parent)

        # 字段初始化
        self._text = text or ""
        self._color = QColor(color)
        self._keep_color = keep_color
        self._left_label = left_label
        self._dense = dense
        self._dark = dark
        self._disabled = bool(disabled)
        self._hovered = False
        self._toggle_indeterminate = toggle_indeterminate
        self._show_focus_ring = False

        order = (toggle_order or "tf").strip().lower()
        self._toggle_order = order if order in ("tf", "ft") else "tf"

        # 尺寸解析
        if isinstance(size, CheckboxSize):
            self._box_size = size.value
        elif isinstance(size, int):
            self._box_size = max(12, min(40, size))
        elif isinstance(size, str):
            self._box_size = _SIZE_MAP.get(size.strip().lower(), CheckboxSize.MD.value)
        else:
            self._box_size = CheckboxSize.MD.value

        # 图标
        self._checked_icon: Optional[QIcon] = self._coerce_icon(checked_icon)
        self._unchecked_icon: Optional[QIcon] = self._coerce_icon(unchecked_icon)
        self._indeterminate_icon: Optional[QIcon] = self._coerce_icon(indeterminate_icon)

        # 状态
        self._state = CheckboxState.CHECKED if checked else CheckboxState.UNCHECKED
        self._progress = 1.0 if checked else 0.0

        # 字体
        font = QFont("Microsoft YaHei")
        font.setPixelSize(14 if dense else 16)
        self.setFont(font)

        self._update_geometry()

        # 动画
        self._anim: QPropertyAnimation = QPropertyAnimation(self, b"progress", self)
        self._anim.setDuration(200 if not dense else 150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 交互属性
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if not disabled else Qt.CursorShape.ArrowCursor
        )
        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus if not disabled else Qt.FocusPolicy.NoFocus
        )
        self.setEnabled(not disabled)
        self.setAccessibleName(
            text.strip() if text and text.strip() else "Checkbox"
        )

        try:
            theme_manager.themeChanged.disconnect(self._on_theme_changed)
        except (RuntimeError, TypeError):
            pass
        # noinspection PyUnresolvedReferences
        theme_manager.themeChanged.connect(self._on_theme_changed)

    # ────────────────────────── 动态尺寸属性 ──────────────────────────
    @property
    def _edge(self) -> int:
        return 2 if self._dense else 4

    @property
    def _gap(self) -> int:
        return 8 if self._dense else 12

    # ────────────────────────── 属性 ──────────────────────────
    @Property(float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, val: float):
        self._progress = val
        self.update()

    # ────────────────────────── Public API ──────────────────────────
    def isChecked(self) -> bool:
        return self._state == CheckboxState.CHECKED

    def isIndeterminate(self) -> bool:
        return self._state == CheckboxState.INDETERMINATE

    def setChecked(self, checked: bool):
        self._set_state(CheckboxState.CHECKED if checked else CheckboxState.UNCHECKED)

    def setIndeterminate(self, indeterminate: bool):
        self._set_state(CheckboxState.INDETERMINATE if indeterminate else CheckboxState.UNCHECKED)

    def setColor(self, color: Union[str, Color]):
        self._color = QColor(color)
        self.update()

    def setText(self, text: str):
        self._text = text or ""
        self.setAccessibleName(self._text.strip() if self._text.strip() else "Checkbox")
        self._update_geometry()
        self.update()

    def setFont(self, font: QFont):
        super().setFont(font)
        if hasattr(self, "_box_size"):
            self._update_geometry()

    def set_checked_icon(self, icon: Optional[Union[str, QIcon]]):
        self._checked_icon = self._coerce_icon(icon)
        self.update()

    def set_unchecked_icon(self, icon: Optional[Union[str, QIcon]]):
        self._unchecked_icon = self._coerce_icon(icon)
        self.update()

    def set_indeterminate_icon(self, icon: Optional[Union[str, QIcon]]):
        self._indeterminate_icon = self._coerce_icon(icon)
        self.update()

    def set_toggle_order(self, order: str):
        o = (order or "tf").strip().lower()
        self._toggle_order = o if o in ("tf", "ft") else "tf"

    def set_keep_color(self, keep: bool):
        self._keep_color = keep
        self.update()

    def set_left_label(self, left: bool):
        self._left_label = left
        self.update()

    def set_dense(self, dense: bool):
        self._dense = dense
        font = self.font()
        font.setPixelSize(14 if dense else 16)
        self.setFont(font)
        self.update()

    def setDisabled(self, disabled: bool):
        self.setEnabled(not disabled)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        if hasattr(self, "_disabled"):
            self._disabled = not enabled
            if not enabled:
                self._hovered = False
            self.setCursor(
                Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor
            )
            self.update()

    # ────────────────────────── 状态切换 ──────────────────────────
    def _next_state(self) -> CheckboxState:
        states_order = [CheckboxState.UNCHECKED, CheckboxState.CHECKED]
        if self._toggle_order == "ft":
            states_order = [CheckboxState.CHECKED, CheckboxState.UNCHECKED]

        current_idx = states_order.index(self._state) if self._state in states_order else -1

        if self._toggle_indeterminate:
            if self._state == CheckboxState.INDETERMINATE:
                return states_order[0]
            elif current_idx == 0:
                return states_order[1]
            else:
                return CheckboxState.INDETERMINATE
        else:
            if self._state == CheckboxState.INDETERMINATE:
                return states_order[0]
            return states_order[(current_idx + 1) % 2]

    def _set_state(self, new_state: CheckboxState, animate: bool = True):
        if new_state == self._state:
            return

        self._state = new_state

        if animate:
            self._anim.stop()
            if new_state == CheckboxState.INDETERMINATE:
                self._anim.setStartValue(0.0)
            else:
                self._anim.setStartValue(self._progress)
            target = 1.0 if new_state != CheckboxState.UNCHECKED else 0.0
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._progress = 1.0 if new_state != CheckboxState.UNCHECKED else 0.0
            self.update()

        if new_state == CheckboxState.INDETERMINATE:
            self.stateChanged.emit(2)
        else:
            is_checked = new_state == CheckboxState.CHECKED
            self.stateChanged.emit(1 if is_checked else 0)
            self.toggled.emit(is_checked)

    # ────────────────────────── 事件 ──────────────────────────
    def enterEvent(self, event):
        if not self._disabled and not self._hovered:
            self._hovered = True
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._hovered:
            self._hovered = False
            self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._disabled:
            self._show_focus_ring = False
            self._set_state(self._next_state())
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if (event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter)
                and not self._disabled):
            self._set_state(self._next_state())
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        self._show_focus_ring = (event.reason() == Qt.FocusReason.TabFocusReason)
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._show_focus_ring = False
        self.update()
        super().focusOutEvent(event)

    def _on_theme_changed(self, mode: ThemeMode):
        try:
            super()._on_theme_changed(mode)
        except AttributeError:
            pass
        self.update()

    # ────────────────────────── 布局 ──────────────────────────
    def _update_geometry(self):
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(self._text) if self._text else 0
        gap = self._gap if self._text else 0
        edge = self._edge

        total_width = edge * 2 + self._box_size + gap + text_width
        height = self._box_size + edge * 2

        self.setFixedSize(total_width, height)

    @staticmethod
    def _coerce_icon(icon: Optional[Union[str, QIcon]]) -> Optional[QIcon]:
        if isinstance(icon, str):
            return QIcon(icon)
        return icon

    # ────────────────────────── 绘制 ──────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        edge = self._edge
        gap = self._gap

        # 1. 方框矩形
        if not self._left_label:
            box_x = float(edge)
        else:
            box_x = float(self.width() - self._box_size - edge)

        box_y = (self.height() - self._box_size) / 2.0
        box_rect = QRectF(box_x, box_y, self._box_size, self._box_size)
        path_rect = box_rect.adjusted(1, 1, -1, -1)
        radius = 4.0 if self._box_size >= 20 else 3.0

        # 2. 颜色
        active_color = QColor(self._color) if not self._disabled \
            else QColor(self._color).darker(150)
        border_color = QColor(theme_manager.get_color("text_secondary"))

        if (self._hovered and not self._disabled
                and self._state == CheckboxState.UNCHECKED
                and self._progress <= 0):
            border_color = QColor(self._color)

        if self._keep_color:
            border_color = QColor(active_color)
        if self._disabled:
            border_color.setAlpha(120)
            active_color.setAlpha(120)

        # 3. 背景 / 边框
        if self._state == CheckboxState.INDETERMINATE or self._progress > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(active_color)
            painter.drawRoundedRect(path_rect, radius, radius)
        else:
            pen = QPen(border_color, 2.0)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(path_rect, radius, radius)

            if self._unchecked_icon and not self._unchecked_icon.isNull():
                self._draw_icon(painter, box_rect, self._unchecked_icon, opacity=1.0)

        # 4. 勾号 / 横线 / 自定义图标
        if self._state == CheckboxState.INDETERMINATE:
            self._draw_indeterminate(painter, path_rect, active_color)
        elif self._progress > 0:
            self._draw_check_animation(painter, path_rect, active_color)

        # 5. 文字
        if self._text:
            text_color = QColor(theme_manager.get_color("text_primary"))
            if self._disabled:
                text_color.setAlpha(120)
            painter.setPen(text_color)
            painter.setFont(self.font())

            if self._left_label:
                text_x = float(edge)
                text_w = float(self.width() - edge * 2 - self._box_size - gap)
                align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            else:
                text_x = float(edge + self._box_size + gap)
                text_w = float(self.width() - edge * 2 - self._box_size - gap)
                align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

            painter.drawText(
                QRectF(text_x, 0, text_w, self.height()), align, self._text
            )

        # 6. 焦点环
        self._draw_focus_ring(painter, box_rect, radius)

    # ────────────────────────── 绘制辅助 ──────────────────────────
    def _draw_icon(
            self,
            painter: QPainter,
            box_rect: QRectF,
            icon: QIcon,
            opacity: float,
    ):
        icon_size = box_rect.width() * 0.7
        dpr = self.devicePixelRatioF()
        phys = max(1, int(round(icon_size * dpr)))
        pix = icon.pixmap(QSize(phys, phys))
        if pix.isNull():
            return
        if pix.devicePixelRatio() != dpr:
            pix.setDevicePixelRatio(dpr)
        painter.save()
        painter.setOpacity(max(0.0, min(1.0, opacity)))
        painter.drawPixmap(
            QRectF(
                box_rect.center().x() - icon_size / 2,
                box_rect.center().y() - icon_size / 2,
                icon_size, icon_size,
            ),
            pix, QRectF(pix.rect()),
        )
        painter.restore()

    def _draw_check_animation(
            self,
            painter: QPainter,
            box_rect: QRectF,
            active_color: QColor,
    ):
        if self._checked_icon and not self._checked_icon.isNull():
            self._draw_icon(painter, box_rect, self._checked_icon, opacity=self._progress)
            return

        contrast_color = QColor(get_contrast_color(active_color.name()))
        check_pen = QPen(contrast_color)
        check_pen.setWidthF(max(2.0, self._box_size * 0.12))
        check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.save()
        painter.setPen(check_pen)

        w = box_rect.width()
        h = box_rect.height()
        # ✅ BUG-2：更匀称的对勾坐标
        p1 = QPointF(box_rect.left() + w * 0.25, box_rect.top() + h * 0.5)
        p2 = QPointF(box_rect.left() + w * 0.45, box_rect.top() + h * 0.7)
        p3 = QPointF(box_rect.left() + w * 0.75, box_rect.top() + h * 0.3)

        progress = max(0.0, min(1.0, self._progress))
        if progress <= 0:
            painter.restore()
            return

        # ✅ BUG-1：分段插值，画出真正的折线对勾
        anim_path = QPainterPath(p1)
        if progress <= 0.5:
            t = progress / 0.5
            curr_p = QPointF(
                p1.x() + (p2.x() - p1.x()) * t,
                p1.y() + (p2.y() - p1.y()) * t
            )
            anim_path.lineTo(curr_p)
        else:
            t = (progress - 0.5) / 0.5
            curr_p = QPointF(
                p2.x() + (p3.x() - p2.x()) * t,
                p2.y() + (p3.y() - p2.y()) * t
            )
            anim_path.lineTo(p2)
            anim_path.lineTo(curr_p)

        painter.drawPath(anim_path)
        painter.restore()

    def _draw_indeterminate(
            self,
            painter: QPainter,
            box_rect: QRectF,
            active_color: QColor,
    ):
        if self._indeterminate_icon and not self._indeterminate_icon.isNull():
            self._draw_icon(painter, box_rect, self._indeterminate_icon, opacity=self._progress)
            return

        contrast_color = QColor(get_contrast_color(active_color.name()))
        pen = QPen(contrast_color)
        pen.setWidthF(max(2.0, self._box_size * 0.12))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.save()
        painter.setPen(pen)

        progress = max(0.0, min(1.0, self._progress))
        y = box_rect.center().y()
        margin = box_rect.width() * 0.25
        available = box_rect.width() - margin * 2
        half = available / 2.0 * progress
        if half > 0:
            painter.drawLine(
                QPointF(box_rect.center().x() - half, y),
                QPointF(box_rect.center().x() + half, y),
            )
        painter.restore()

    def _draw_focus_ring(
            self,
            painter: QPainter,
            box_rect: QRectF,
            radius: float,
    ):
        if not (self._show_focus_ring and self.hasFocus() and not self._disabled):
            return
        color = QColor(self._color)
        if color.lightnessF() > 0.7 and not theme_manager.is_dark():
            color = QColor(theme_manager.get_color("text_primary"))
        color.setAlpha(160)
        pen = QPen(color, self._FOCUS_RING_WIDTH, Qt.PenStyle.SolidLine)
        painter.save()
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inset = self._FOCUS_RING_OFFSET
        focus_rect = box_rect.adjusted(-inset, -inset, inset, inset)
        painter.drawRoundedRect(focus_rect, radius + inset, radius + inset)
        painter.restore()
