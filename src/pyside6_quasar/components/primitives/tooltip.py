# quasar/components/tooltip.py
from enum import Enum
from typing import Optional, Union, Tuple

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QTimer, QPoint, QRectF, QEvent,
    QEasingCurve, QParallelAnimationGroup
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QFont, QPen, QGuiApplication,
    QPaintEvent
)
from PySide6.QtWidgets import QWidget

# ★ 引入主题管理器和基类
from ...core.theme import theme_manager, ThemeMode
from ...core.base import QBaseWidget, QuasarWidgetMixin


class TooltipTransition(Enum):
    JUMP = 1
    SLIDE = 2
    FADE = 3


class TooltipPosition(Enum):
    TOP_LEFT = ("top", "left")
    TOP_MIDDLE = ("top", "middle")
    TOP_RIGHT = ("top", "right")
    TOP_START = ("top", "start")
    TOP_END = ("top", "end")
    CENTER_LEFT = ("center", "left")
    CENTER_MIDDLE = ("center", "middle")
    CENTER_RIGHT = ("center", "right")
    CENTER_START = ("center", "start")
    CENTER_END = ("center", "end")
    BOTTOM_LEFT = ("bottom", "left")
    BOTTOM_MIDDLE = ("bottom", "middle")
    BOTTOM_RIGHT = ("bottom", "right")
    BOTTOM_START = ("bottom", "start")
    BOTTOM_END = ("bottom", "end")


# ★ 核心修复 1：继承 QWidget 和 ThemedWidget
class Tooltip(QWidget, ThemedWidget):
    def __init__(
            self,
            text: str = "",
            target: Optional[QWidget] = None,
            anchor: Union[str, TooltipPosition] = "bottom middle",
            self_anchor: Union[str, TooltipPosition] = "top middle",
            offset: Tuple[int, int] = (14, 14),
            show_delay: int = 0,
            hide_delay: int = 0,
            transition: TooltipTransition = TooltipTransition.JUMP,
            transition_duration: int = 300,
            max_width: int = 300,
            content_widget: Optional[QWidget] = None,
            parent=None,
    ):
        super().__init__(parent)
        # ★ 挂载主题监听
        self.setup_theme()

        self._text = text
        self._target = None
        self._content_widget = content_widget

        self._anchor = self._parse_anchor(anchor)
        self._self_anchor = self._parse_anchor(self_anchor)

        self._offset = offset
        self._arrow_size = 6
        self._radius = 4
        self._max_width = max_width

        self._transition = transition
        self._transition_duration = transition_duration

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.ToolTip |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.setFont(QFont("Arial", 9))
        self._update_size()

        self._show_timer = QTimer(self)
        self._show_timer.setSingleShot(True)
        self._show_timer.timeout.connect(self._do_show)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._do_hide)

        self._show_delay = show_delay
        self._hide_delay = hide_delay

        self._current_anim_group = None

        if target:
            self.set_target(target)

        self.setAccessibleName(text or "Tooltip")

    # ==========================================================
    # 公共 API
    # ==========================================================
    def set_text(self, text: str):
        self._text = text
        if not self._content_widget:
            self._update_size()
        self.update()

    def set_content(self, widget: QWidget):
        self._content_widget = widget
        if widget:
            self._text = ""
            self._update_size()
        self.update()

    def set_target(self, target: QWidget):
        if self._target == target:
            return
        if self._target:
            self._target.removeEventFilter(self)
        self._target = target
        if self._target:
            self._target.installEventFilter(self)

    def set_anchor(self, anchor: Union[str, TooltipPosition],
                   self_anchor: Union[str, TooltipPosition]):
        self._anchor = self._parse_anchor(anchor)
        self._self_anchor = self._parse_anchor(self_anchor)
        if self.isVisible():
            self._update_position()

    def set_offset(self, offset: Tuple[int, int]):
        self._offset = offset
        if self.isVisible():
            self._update_position()

    def set_delay(self, show_delay: int, hide_delay: int = 0):
        self._show_delay = show_delay
        self._hide_delay = hide_delay

    def set_transition(self, transition: TooltipTransition, duration: int = 300):
        self._transition = transition
        self._transition_duration = duration

    def _on_theme_changed(self, mode: ThemeMode):
        # ★ 主题切换时重绘
        self.update()
        super()._on_theme_changed(mode)

    # ==========================================================
    # 内部逻辑
    # ==========================================================
    def _parse_anchor(self, anchor: Union[str, TooltipPosition]) -> Tuple[str, str]:
        if isinstance(anchor, TooltipPosition):
            return anchor.value
        parts = anchor.lower().split()
        v = parts[0] if len(parts) > 0 else "middle"
        h = parts[1] if len(parts) > 1 else "middle"
        if v not in ("top", "center", "bottom"):
            v = "middle"
        if h not in ("left", "middle", "right", "start", "end"):
            h = "middle"
        return (v, h)

    def _update_size(self):
        if self._content_widget:
            self._content_widget.adjustSize()
            self._w = self._content_widget.width() + 20
            self._h = self._content_widget.height() + 10
        else:
            fm = self.fontMetrics()
            text_w = fm.horizontalAdvance(self._text)
            self._w = min(text_w + 20, self._max_width)
            self._h = fm.height() + 10

        v_anchor, h_anchor = self._anchor

        if v_anchor in ("top", "bottom") or v_anchor == "middle":
            self.setFixedSize(self._w, self._h + self._arrow_size)
        else:
            self.setFixedSize(self._w + self._arrow_size, self._h)

        if self._content_widget:
            self._content_widget.setParent(self)
            offset_x = self._arrow_size if h_anchor in ("left", "start") else 0
            offset_y = self._arrow_size if v_anchor == "top" else 0
            self._content_widget.move(10 + offset_x, 5 + offset_y)

    def eventFilter(self, watched, event):
        if watched == self._target:
            if event.type() == QEvent.Type.Enter:
                self._on_enter()
            elif event.type() == QEvent.Type.Leave:
                self._on_leave()
        return super().eventFilter(watched, event)

    def _on_enter(self):
        self._hide_timer.stop()
        if self._show_delay > 0:
            self._show_timer.start(self._show_delay)
        else:
            self._do_show()

    def _on_leave(self):
        self._show_timer.stop()
        if self._hide_delay > 0:
            self._hide_timer.start(self._hide_delay)
        else:
            self._do_hide()

    def _do_show(self):
        if not self._target:
            return
        self._update_position()
        self.show()
        self.raise_()
        self._apply_transition_show()

    def _do_hide(self):
        self._apply_transition_hide()

    # ==========================================================
    # 过渡动画
    # ==========================================================
    def _apply_transition_show(self):
        if self._current_anim_group:
            self._current_anim_group.stop()

        self._current_anim_group = QParallelAnimationGroup(self)

        start_opacity = 0.0 if self._transition == TooltipTransition.FADE else 1.0
        self.setWindowOpacity(start_opacity)

        opacity_anim = QPropertyAnimation(self, b"windowOpacity", self._current_anim_group)
        opacity_anim.setStartValue(start_opacity)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setDuration(self._transition_duration)
        self._current_anim_group.addAnimation(opacity_anim)

        if self._transition == TooltipTransition.JUMP:
            start_pos = self.pos() + QPoint(0, -10 if "bottom" in self._anchor[0] else 10)
            self.move(start_pos)

            pos_anim = QPropertyAnimation(self, b"pos", self._current_anim_group)
            pos_anim.setStartValue(start_pos)
            pos_anim.setEndValue(self.pos())
            pos_anim.setDuration(self._transition_duration)
            pos_anim.setEasingCurve(QEasingCurve.Type.OutBack)
            self._current_anim_group.addAnimation(pos_anim)

        elif self._transition == TooltipTransition.SLIDE:
            start_pos = self.pos() + QPoint(0, -20 if "bottom" in self._anchor[0] else 20)
            self.move(start_pos)

            pos_anim = QPropertyAnimation(self, b"pos", self._current_anim_group)
            pos_anim.setStartValue(start_pos)
            pos_anim.setEndValue(self.pos())
            pos_anim.setDuration(self._transition_duration)
            pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._current_anim_group.addAnimation(pos_anim)

        self._current_anim_group.start()

    def _apply_transition_hide(self):
        if self._current_anim_group:
            self._current_anim_group.stop()

        self._current_anim_group = QParallelAnimationGroup(self)

        opacity_anim = QPropertyAnimation(self, b"windowOpacity", self._current_anim_group)
        opacity_anim.setStartValue(self.windowOpacity())
        opacity_anim.setEndValue(0.0)
        opacity_anim.setDuration(self._transition_duration // 2)
        self._current_anim_group.addAnimation(opacity_anim)

        self._current_anim_group.finished.connect(self.hide)
        self._current_anim_group.start()

    # ==========================================================
    # 核心：Anchor / Self 定位算法
    # ==========================================================
    @staticmethod
    def _get_point(rect: QRectF, point: Tuple[str, str], is_rtl: bool = False) -> QPoint:
        v, h = point
        if h == "start":
            h = "right" if is_rtl else "left"
        elif h == "end":
            h = "left" if is_rtl else "right"

        if h == "left":
            x = rect.left()
        elif h == "right":
            x = rect.right()
        else:
            x = rect.center().x()

        if v == "top":
            y = rect.top()
        elif v == "bottom":
            y = rect.bottom()
        else:
            y = rect.center().y()

        return QPoint(int(x), int(y))

    def _update_position(self):
        if not self._target:
            return

        target_rect = QRectF(self._target.mapToGlobal(QPoint(0, 0)), self._target.size())
        expanded_rect = target_rect.adjusted(-self._offset[0], -self._offset[1],
                                             self._offset[0], self._offset[1])

        anchor_pt = self._get_point(expanded_rect, self._anchor)
        tooltip_rect = QRectF(0, 0, self.width(), self.height())
        self_pt = self._get_point(tooltip_rect, self._self_anchor)

        x = anchor_pt.x() - self_pt.x()
        y = anchor_pt.y() - self_pt.y()

        screen = QGuiApplication.screenAt(anchor_pt)
        if not screen:
            screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        margin = 4

        if x + self.width() > geo.right() - margin:
            flipped_x = anchor_pt.x() - self.width() + (self_pt.x() - tooltip_rect.left())
            if flipped_x >= geo.left() + margin:
                x = flipped_x
            else:
                x = geo.right() - self.width() - margin
        elif x < geo.left() + margin:
            x = geo.left() + margin

        if y + self.height() > geo.bottom() - margin:
            flipped_y = anchor_pt.y() - self.height() + (self_pt.y() - tooltip_rect.top())
            if flipped_y >= geo.top() + margin:
                y = flipped_y
            else:
                y = geo.bottom() - self.height() - margin
        elif y < geo.top() + margin:
            y = geo.top() + margin

        self.move(x, y)

    # ==========================================================
    # 绘制
    # ==========================================================
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ★ 核心修复 2：动态拉取主题颜色，半透明磨砂质感
        if theme_manager.is_dark():
            bg_color = QColor(30, 39, 46, 240)
            border_color = QColor(255, 255, 255, 30)
            text_color = QColor("#ffffff")
        else:
            bg_color = QColor(255, 255, 255, 240)
            border_color = QColor(0, 0, 0, 30)
            text_color = QColor("#333333")

        v_anchor, h_anchor = self._anchor

        arrow_on_top = (v_anchor == "bottom")
        arrow_on_bottom = (v_anchor == "top")
        arrow_on_left = (h_anchor in ("right", "end"))
        arrow_on_right = (h_anchor in ("left", "start"))

        body_x = self._arrow_size if arrow_on_left else 0
        body_y = self._arrow_size if arrow_on_top else 0
        body_w = self.width() - (self._arrow_size if arrow_on_right else 0) - body_x
        body_h = self.height() - (self._arrow_size if arrow_on_bottom else 0) - body_y

        body_rect = QRectF(body_x, body_y, body_w, body_h)

        path = QPainterPath()
        path.addRoundedRect(body_rect, self._radius, self._radius)
        painter.fillPath(path, bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)

        self._draw_arrow(painter, bg_color, border_color, arrow_on_top, arrow_on_bottom, arrow_on_left, arrow_on_right)

        if self._text and not self._content_widget:
            painter.setPen(text_color)
            painter.drawText(
                body_rect.adjusted(10, 0, -10, 0),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self._text
            )

    def _draw_arrow(self, painter: QPainter, bg_color: QColor, border_color: QColor,
                    arrow_on_top: bool, arrow_on_bottom: bool, arrow_on_left: bool, arrow_on_right: bool):
        arrow_size = self._arrow_size
        cx = self.width() // 2
        cy = self.height() // 2

        points = []
        if arrow_on_top:
            points = [
                QPoint(cx, 0),
                QPoint(cx - arrow_size, arrow_size),
                QPoint(cx + arrow_size, arrow_size)
            ]
        elif arrow_on_bottom:
            points = [
                QPoint(cx, self.height()),
                QPoint(cx - arrow_size, self.height() - arrow_size),
                QPoint(cx + arrow_size, self.height() - arrow_size)
            ]
        elif arrow_on_left:
            points = [
                QPoint(0, cy),
                QPoint(arrow_size, cy - arrow_size),
                QPoint(arrow_size, cy + arrow_size)
            ]
        elif arrow_on_right:
            points = [
                QPoint(self.width(), cy),
                QPoint(self.width() - arrow_size, cy - arrow_size),
                QPoint(self.width() - arrow_size, cy + arrow_size)
            ]

        if not points:
            return

        arrow_path = QPainterPath()
        arrow_path.moveTo(points[0])
        arrow_path.lineTo(points[1])
        arrow_path.lineTo(points[2])
        arrow_path.closeSubpath()

        painter.fillPath(arrow_path, bg_color)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(arrow_path)
