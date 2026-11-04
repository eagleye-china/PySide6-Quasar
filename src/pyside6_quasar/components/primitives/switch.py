# quasar/components/switch.py
from enum import Enum
from typing import Optional, Union

from PySide6.QtCore import (
    Qt, QPropertyAnimation, Property, QEasingCurve, Signal,
    QRectF, QPointF, QSize
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QPen, QIcon
)
from PySide6.QtWidgets import QWidget

# ★ 引入主题管理器和基类
from ...core.theme import theme_manager, ThemeMode
from ...core.theme.palette import Color
from ...core.theme.contrast import get_contrast_color
from ...core.base import QBaseWidget, QuasarWidgetMixin


class SwitchSize(Enum):
    """对齐 Quasar 标准尺寸"""
    XS = 24
    SM = 32
    MD = 44
    LG = 56
    XL = 68


class SwitchState(Enum):
    OFF = 0
    ON = 1
    INDETERMINATE = 2


# ★ 核心修复 1：QWidget 放前面，ThemedWidget 作为纯 Mixin
class Switch(QWidget, ThemedWidget):
    """
    终极封板开关 (对标 Quasar QToggle)
    完美支持鼠标悬停拉伸、无障碍键盘焦点、以及全局深浅主题切换。
    """
    toggled = Signal(bool)
    stateChanged = Signal(int)

    def __init__(
            self,
            checked: bool = False,
            indeterminate: bool = False,
            color: str = Color.PRIMARY,
            keep_color: bool = False,
            dense: bool = False,
            size: Union[int, SwitchSize, str] = SwitchSize.MD,
            label: str = "",
            left_label: bool = False,
            disable: bool = False,
            toggle_indeterminate: bool = False,
            toggle_order: str = "tf",
            checked_icon: Optional[Union[str, QIcon]] = None,
            unchecked_icon: Optional[Union[str, QIcon]] = None,
            indeterminate_icon: Optional[Union[str, QIcon]] = None,
            parent=None,
    ):
        super().__init__(parent)
        # ★ 核心修复 2：挂载主题监听
        self.setup_theme()

        # 尺寸解析
        if isinstance(size, SwitchSize):
            self._size = size.value
        elif isinstance(size, int):
            self._size = max(20, size)
        elif isinstance(size, str):
            s = size.strip().lower()
            map_size = {"xs": 24, "sm": 32, "md": 44, "lg": 56, "xl": 68}
            self._size = map_size.get(s, 44)
        else:
            self._size = 44

        if dense:
            self._size = max(20, int(self._size * 0.8))

        # 宽高比 2:1
        self._w = self._size
        self._h = self._size // 2

        # 颜色配置
        self._color_on = QColor(color)
        self._keep_color = keep_color
        self._disable = disable

        # ★ 动态拉取关闭状态的颜色（跟随主题）
        self._update_theme_colors()

        # 状态与流转控制
        self._toggle_indeterminate = toggle_indeterminate
        self._toggle_order = toggle_order.lower()

        if indeterminate:
            self._state = SwitchState.INDETERMINATE
        elif checked:
            self._state = SwitchState.ON
        else:
            self._state = SwitchState.OFF

        # 动画进度
        if self._state == SwitchState.ON:
            self._progress = 1.0
        elif self._state == SwitchState.INDETERMINATE:
            self._progress = 0.5
        else:
            self._progress = 0.0

        # 图标
        self._checked_icon = self._coerce_icon(checked_icon)
        self._unchecked_icon = self._coerce_icon(unchecked_icon)
        self._indeterminate_icon = self._coerce_icon(indeterminate_icon)

        # 标签
        self._label = label
        self._left_label = left_label

        self._label_width = 0
        if self._label:
            fm = self.fontMetrics()
            self._label_width = fm.horizontalAdvance(self._label) + 8
            total_w = self._w + (self._label_width if self._label else 0)
            self.setFixedSize(total_w, self._h)
        else:
            self.setFixedSize(self._w, self._h)

        # 动画
        self._anim = QPropertyAnimation(self, b"progress")
        self._anim.setDuration(200 if not dense else 150)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 悬停与焦点状态
        self._is_hovered = False
        self._show_focus_ring = False

        # 交互
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if not disable
            else Qt.CursorShape.ArrowCursor
        )
        self.setFocusPolicy(
            Qt.FocusPolicy.StrongFocus if not disable
            else Qt.FocusPolicy.NoFocus
        )
        self.setEnabled(not disable)
        self.setAccessibleName(label or "Toggle")

    def _update_theme_colors(self):
        """动态拉取并更新颜色"""
        # 关闭状态的轨道底色跟随主题边界色（浅色模式下为浅灰，深色模式下为深灰）
        self._color_off = QColor(theme_manager.get_color("border"))
        # 未确定状态的轨道色（主色稍微提亮或降透明度）
        if theme_manager.is_dark():
            self._color_indeterminate = QColor(self._color_on).lighter(130)
        else:
            self._color_indeterminate = QColor(self._color_on).darker(120)

    def _on_theme_changed(self, mode: ThemeMode):
        """响应全局主题切换"""
        self._update_theme_colors()
        super()._on_theme_changed(mode)

    # ================= 动画属性 =================
    @Property(float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, val: float):
        self._progress = val
        self.update()

    # ================= 悬停与焦点事件 =================
    def enterEvent(self, event):
        if not self._disable:
            self._is_hovered = True
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    def focusInEvent(self, event):
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

    # ================= 公共 API =================
    def isChecked(self) -> bool:
        return self._state == SwitchState.ON

    def isIndeterminate(self) -> bool:
        return self._state == SwitchState.INDETERMINATE

    def getState(self) -> int:
        return self._state.value

    def set_state(self, state: SwitchState):
        if state == self._state:
            return

        self._state = state
        target = 1.0 if state == SwitchState.ON else (0.5 if state == SwitchState.INDETERMINATE else 0.0)

        self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(target)
        self._anim.start()

        self.stateChanged.emit(self._state.value)
        self.toggled.emit(self.isChecked())

        self.setAccessibleDescription(
            "Checked" if state == SwitchState.ON else
            ("Indeterminate" if state == SwitchState.INDETERMINATE else "Unchecked")
        )

    def setChecked(self, checked: bool):
        self.set_state(SwitchState.ON if checked else SwitchState.OFF)

    def setIndeterminate(self, indeterminate: bool):
        self.set_state(SwitchState.INDETERMINATE if indeterminate else SwitchState.OFF)

    # ================= 状态流转逻辑 =================
    def _next_state(self) -> SwitchState:
        states_order = [SwitchState.OFF, SwitchState.ON]
        if self._toggle_order == "ft":
            states_order = [SwitchState.ON, SwitchState.OFF]

        current_idx = states_order.index(self._state) if self._state in states_order else -1

        if self._toggle_indeterminate:
            if self._state == SwitchState.INDETERMINATE:
                return states_order[0]
            elif current_idx == 0:
                return states_order[1]
            else:
                return SwitchState.INDETERMINATE
        else:
            if self._state == SwitchState.INDETERMINATE:
                return states_order[0]
            return states_order[(current_idx + 1) % 2]

    # ================= 交互事件 =================
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._disable:
            self._show_focus_ring = False
            self.set_state(self._next_state())
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter) and not self._disable:
            self.set_state(self._next_state())
        super().keyPressEvent(event)

    # ================= 图标处理 =================
    @staticmethod
    def _coerce_icon(icon: Optional[Union[str, QIcon]]) -> Optional[QIcon]:
        if isinstance(icon, str):
            return QIcon(icon)
        return icon

    # ================= 核心绘制 =================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # ★ 核心修复 1：计算轨道的起始 X 坐标
        track_x = self._label_width if self._left_label else 0

        # 1. 绘制轨道
        track_rect = QRectF(track_x, 0, self._w, self._h)
        radius = self._h / 2.0
        path = QPainterPath()
        path.addRoundedRect(track_rect, radius, radius)

        if self._disable:
            track_color = QColor(theme_manager.get_color("border")).lighter(120)
        elif self._progress <= 0.5:
            ratio = self._progress / 0.5
            track_color = self._interpolate(self._color_off, self._color_indeterminate, ratio)
        else:
            ratio = (self._progress - 0.5) / 0.5
            track_color = self._interpolate(self._color_indeterminate, self._color_on, ratio)

        painter.fillPath(path, track_color)

        # 2. 绘制滑块（包含微拉伸逻辑）
        margin = 2
        dot_radius = radius - margin
        base_w = dot_radius * 2

        # 拉伸宽度（如果悬停，宽度增加 15%）
        current_w = base_w * 1.15 if self._is_hovered else base_w
        current_h = dot_radius * 2

        # ★ 核心修复 2：计算滑块中心时加上 track_x 的偏移
        base_center_x = track_x + dot_radius + margin + (self._w - 2 * dot_radius - 2 * margin) * self._progress
        dot_center_x = base_center_x
        dot_center_y = radius

        # 边界约束（防止拉伸时超出底槽边缘）
        if self._is_hovered:
            left_edge = dot_center_x - current_w / 2
            right_edge = dot_center_x + current_w / 2

            # ★ 核心修复 3：边界约束也要加上 track_x
            if left_edge < track_x + margin:
                dot_center_x += (track_x + margin - left_edge)
            elif right_edge > track_x + self._w - margin:
                dot_center_x -= (right_edge - (track_x + self._w - margin))

        # 阴影（自适应深浅模式）
        if not self._disable:
            painter.setPen(Qt.PenStyle.NoPen)
            shadow_alpha = 60 if theme_manager.is_dark() else 30
            painter.setBrush(QColor(0, 0, 0, shadow_alpha))
            shadow_rect = QRectF(
                dot_center_x - current_w / 2 + 0.5,
                dot_center_y - current_h / 2 + 1.5,
                current_w, current_h
            )
            painter.drawRoundedRect(shadow_rect, current_h / 2, current_h / 2)

        # 主滑块
        knob_color = QColor("#ffffff") if not self._disable else QColor("#9e9e9e")
        painter.setBrush(knob_color)
        knob_rect = QRectF(
            dot_center_x - current_w / 2,
            dot_center_y - current_h / 2,
            current_w, current_h
        )
        painter.drawRoundedRect(knob_rect, current_h / 2, current_h / 2)

        # 3. 绘制内嵌图标 / 状态指示
        self._draw_icon(painter, dot_center_x, dot_center_y, dot_radius)

        # 4. 绘制标签
        if self._label:
            self._draw_label(painter)

        # 5. 绘制键盘焦点环
        self._draw_focus_ring(painter, track_rect, radius)

    @staticmethod
    def _interpolate(c1: QColor, c2: QColor, ratio: float) -> QColor:
        r = int(c1.red() + (c2.red() - c1.red()) * ratio)
        g = int(c1.green() + (c2.green() - c1.green()) * ratio)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * ratio)
        return QColor(r, g, b)

    def _draw_icon(self, painter, cx: float, cy: float, radius: float):
        icon = None
        if self._state == SwitchState.ON and self._checked_icon:
            icon = self._checked_icon
        elif self._state == SwitchState.OFF and self._unchecked_icon:
            icon = self._unchecked_icon
        elif self._state == SwitchState.INDETERMINATE and self._indeterminate_icon:
            icon = self._indeterminate_icon

        if icon and not icon.isNull():
            icon_size = int(radius * 1.2)
            pix = icon.pixmap(QSize(icon_size, icon_size))
            painter.drawPixmap(
                int(cx - icon_size / 2),
                int(cy - icon_size / 2),
                pix
            )
            return

        if self._state == SwitchState.INDETERMINATE and 0.45 <= self._progress <= 0.55:
            # ★ 核心修复：中间横杠的颜色智能适配，深色滑块上用深色横杠，浅色滑块上用浅色横杠
            QColor(get_contrast_color("#ffffff")) if theme_manager.is_dark() else QColor("#ffffff")
            pen = QPen(QColor("#b0bec5"))
            pen.setWidthF(2.0)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(cx - radius * 0.4, cy),
                QPointF(cx + radius * 0.4, cy)
            )

    def _draw_label(self, painter):
        painter.setFont(self.font())
        # ★ 核心修复：标签文字颜色自动跟随全局主题
        text_color = QColor(theme_manager.get_color("text_primary"))
        if self._disable:
            text_color.setAlpha(120)
        painter.setPen(text_color)

        if self._left_label:
            text_rect = QRectF(0, 0, self._label_width, self._h)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                self._label
            )
        else:
            text_rect = QRectF(self._w + 4, 0, self._label_width, self._h)
            painter.drawText(
                text_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self._label
            )

    def _draw_focus_ring(self, painter: QPainter, track_rect: QRectF, radius: float):
        """绘制优雅的键盘焦点环"""
        if self._show_focus_ring and self.hasFocus() and not self._disable:
            painter.save()

            # 使用主色带透明
            color = QColor(self._color_on)
            color.setAlpha(150)

            # 平滑实线
            pen = QPen(color, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # 围绕轨道外侧画一圈
            focus_rect = track_rect.adjusted(-2, -2, 2, 2)
            painter.drawRoundedRect(focus_rect, radius + 2, radius + 2)
            painter.restore()
