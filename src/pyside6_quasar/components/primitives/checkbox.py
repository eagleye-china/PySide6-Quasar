# quasar/components/checkbox.py
from enum import Enum
from typing import Optional, Union

from PySide6.QtCore import (
    Qt, QPropertyAnimation, Property, QEasingCurve, Signal,
    QRectF, QPointF, QSize
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QFont, QIcon, QPen
)
from PySide6.QtWidgets import QWidget

from ...core.theme import theme_manager, ThemeMode
from ...core.theme.palette import Color
from ...core.theme.contrast import get_contrast_color
from ...core.base import QBaseWidget, QuasarWidgetMixin


class CheckboxSize(Enum):
    XS = 16
    SM = 18
    MD = 20
    LG = 24
    XL = 28


class CheckboxState(Enum):
    UNCHECKED = 0
    CHECKED = 1
    INDETERMINATE = 2


# ★ 核心修复 1：QWidget 放在前面，ThemedWidget 作为纯 Mixin
class Checkbox(QWidget, ThemedWidget):
    """
    终极封板复选框 (对标 Quasar QCheckbox)
    支持三态、自定义图标、勾号生长动画、主题自适应与键盘焦点环。
    """
    toggled = Signal(bool)
    stateChanged = Signal(int)

    def __init__(
            self,
            text: str = "",
            checked: bool = False,
            color: str = Color.PRIMARY,
            keep_color: bool = False,
            left_label: bool = False,
            dense: bool = False,
            size: Union[int, CheckboxSize] = CheckboxSize.MD,
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
        # ★ 核心修复 2：挂载主题监听
        self.setup_theme()

        self._text = text
        self._color = QColor(color)
        self._keep_color = keep_color
        self._left_label = left_label
        self._dense = dense
        self._dark = dark  # 保留该参数，但实际颜色渲染将根据 theme_manager 走
        self._disabled = disabled
        self._toggle_indeterminate = toggle_indeterminate
        self._toggle_order = toggle_order.lower()

        # 尺寸
        if isinstance(size, CheckboxSize):
            self._box_size = size.value
        elif isinstance(size, int):
            self._box_size = max(12, min(40, size))
        else:
            self._box_size = CheckboxSize.MD.value

        # 图标
        self._checked_icon = self._coerce_icon(checked_icon)
        self._unchecked_icon = self._coerce_icon(unchecked_icon)
        self._indeterminate_icon = self._coerce_icon(indeterminate_icon)

        # 状态
        self._state = CheckboxState.CHECKED if checked else CheckboxState.UNCHECKED
        self._progress = 1.0 if checked else 0.0

        # 字体
        font = QFont("Arial")
        font.setPixelSize(14 if dense else 16)
        self.setFont(font)

        self._update_geometry()

        # 动画
        self._anim = QPropertyAnimation(self, b"progress")
        self._anim.setDuration(200 if not dense else 150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.setCursor(Qt.CursorShape.PointingHandCursor if not disabled else Qt.CursorShape.ArrowCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus if not disabled else Qt.FocusPolicy.NoFocus)
        self.setEnabled(not disabled)
        self.setAccessibleName(text or "Checkbox")

        # 焦点环状态（鼠标点击不显示，键盘 Tab 切入显示）
        self._show_focus_ring = False

    @Property(float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, val: float):
        self._progress = val
        self.update()

    def isChecked(self) -> bool:
        return self._state == CheckboxState.CHECKED

    def isIndeterminate(self) -> bool:
        return self._state == CheckboxState.INDETERMINATE

    def setChecked(self, checked: bool):
        self._set_state(CheckboxState.CHECKED if checked else CheckboxState.UNCHECKED)

    def setIndeterminate(self, indeterminate: bool):
        self._set_state(CheckboxState.INDETERMINATE if indeterminate else CheckboxState.UNCHECKED)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._disabled = not enabled
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor)
        self.update()

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._disabled:
            self._show_focus_ring = False  # 鼠标点击取消焦点环
            self._set_state(self._next_state())
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter) and not self._disabled:
            self._set_state(self._next_state())
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        # ★ 核心修复 3：只响应键盘焦点，鼠标点击不显示
        if event.reason() != Qt.FocusReason.MouseFocusReason:
            self._show_focus_ring = True
        else:
            self._show_focus_ring = False
        self.update()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self._show_focus_ring = False
        self.update()
        super().focusOutEvent(event)

    def _update_geometry(self):
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self._text) if self._text else 0
        gap = 12 if self._text else 0  # 舒适的文字间距
        total_width = self._box_size + gap + text_width + 8  # 增加一点边距给焦点环预留空间
        height = max(self._box_size + 8, 24 if not self._dense else 20)
        self.setFixedSize(total_width, height)

    @staticmethod
    def _coerce_icon(icon: Optional[Union[str, QIcon]]) -> Optional[QIcon]:
        if isinstance(icon, str):
            return QIcon(icon)
        return icon

    def _on_theme_changed(self, mode: ThemeMode):
        # 主题切换时重绘，自动更新文字和边框颜色
        self.update()
        super()._on_theme_changed(mode)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. 计算方框矩形
        box_x = 4 if not self._left_label else self.width() - self._box_size - 4
        box_y = (self.height() - self._box_size) / 2
        box_rect = QRectF(box_x, box_y, self._box_size, self._box_size)

        # 内缩 1px 保证边框绝对平滑不越界
        path_rect = box_rect.adjusted(1, 1, -1, -1)
        radius = 4 if self._box_size >= 20 else 3

        # 2. 确定颜色（动态从主题拉取）
        active_color = QColor(self._color) if not self._disabled else QColor(self._color).darker(150)

        # 未选中时的边框色：跟随主题的次级文字色
        border_color = QColor(theme_manager.get_color("text_secondary"))

        if self._keep_color:
            border_color = active_color
        if self._disabled:
            border_color.setAlpha(120)
            active_color.setAlpha(120)

        # 3. 绘制背景/边框
        if self._state == CheckboxState.INDETERMINATE or self._progress > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(active_color)
            painter.drawRoundedRect(path_rect, radius, radius)
        else:
            pen = QPen(border_color, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(path_rect, radius, radius)

        # 4. 绘制勾号 / 半选 / 自定义图标
        if self._state == CheckboxState.INDETERMINATE:
            self._draw_indeterminate(painter, path_rect, active_color)
        elif self._progress > 0:
            self._draw_check_animation(painter, path_rect, active_color)

        # 5. 绘制文字
        if self._text:
            # ★ 核心修复 4：文字颜色自动跟随主题主文本色
            text_color = QColor(theme_manager.get_color("text_primary"))
            if self._disabled:
                text_color.setAlpha(120)
            painter.setPen(text_color)

            if self._left_label:
                text_rect = QRectF(4, 0, self.width() - self._box_size - 12 - 4, self.height())
                align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            else:
                text_rect = QRectF(self._box_size + 12 + 4, 0, self.width() - self._box_size - 12 - 8, self.height())
                align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

            painter.drawText(text_rect, align, self._text)

        # 6. 绘制键盘焦点环
        self._draw_focus_ring(painter, box_rect, radius)

    def _draw_check_animation(self, painter: QPainter, box_rect: QRectF, active_color: QColor):
        if self._checked_icon and not self._checked_icon.isNull():
            icon_size = int(box_rect.width() * 0.7)
            pix = self._checked_icon.pixmap(QSize(icon_size, icon_size))
            painter.drawPixmap(
                int(box_rect.center().x() - icon_size / 2),
                int(box_rect.center().y() - icon_size / 2),
                pix
            )
            return

        # ★ 核心修复 5：勾号颜色根据背景色智能判断，如果是亮色背景（如黄色）则用黑勾
        contrast_color = get_contrast_color(active_color.name())
        check_pen = QPen(QColor(contrast_color))

        check_pen.setWidth(max(2, int(self._box_size * 0.12)))
        check_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        check_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(check_pen)

        # 黄金比例勾号坐标
        w = box_rect.width()
        h = box_rect.height()
        p1 = QPointF(box_rect.left() + w * 0.28, box_rect.top() + h * 0.52)
        p2 = QPointF(box_rect.left() + w * 0.45, box_rect.top() + h * 0.70)
        p3 = QPointF(box_rect.left() + w * 0.72, box_rect.top() + h * 0.32)

        check_path = QPainterPath(p1)
        check_path.lineTo(p2)
        check_path.lineTo(p3)

        anim_path = QPainterPath()
        anim_path.moveTo(p1)

        if self._progress < 0.5:
            target = check_path.pointAtPercent(0.5 * (self._progress / 0.5))
            anim_path.lineTo(target)
        else:
            anim_path.lineTo(p2)
            target = check_path.pointAtPercent(0.5 + 0.5 * ((self._progress - 0.5) / 0.5))
            anim_path.lineTo(target)

        painter.drawPath(anim_path)

    def _draw_indeterminate(self, painter: QPainter, box_rect: QRectF, active_color: QColor):
        if self._indeterminate_icon and not self._indeterminate_icon.isNull():
            icon_size = int(box_rect.width() * 0.7)
            pix = self._indeterminate_icon.pixmap(QSize(icon_size, icon_size))
            painter.drawPixmap(
                int(box_rect.center().x() - icon_size / 2),
                int(box_rect.center().y() - icon_size / 2),
                pix
            )
            return

        contrast_color = get_contrast_color(active_color.name())
        pen = QPen(QColor(contrast_color))
        pen.setWidth(max(2, int(self._box_size * 0.12)))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        y = box_rect.center().y()
        margin = box_rect.width() * 0.25
        painter.drawLine(
            QPointF(box_rect.left() + margin, y),
            QPointF(box_rect.right() - margin, y)
        )

    def _draw_focus_ring(self, painter: QPainter, box_rect: QRectF, radius: float):
        """绘制优雅的键盘焦点环"""
        if self._show_focus_ring and self.hasFocus() and not self._disabled:
            painter.save()

            # 使用主色带透明
            color = QColor(self._color)
            color.setAlpha(150)

            # 平滑实线
            pen = QPen(color, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # 在方框外侧画一圈
            focus_rect = box_rect.adjusted(-1, -1, 1, 1)
            painter.drawRoundedRect(focus_rect, radius + 1, radius + 1)
            painter.restore()
