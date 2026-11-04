# quasar/components/progress.py
import math

from PySide6.QtCore import (
    Qt, QPropertyAnimation, Property, QEasingCurve, QRectF
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QFont, QConicalGradient
)
from PySide6.QtWidgets import QWidget

# ★ 引入主题管理器和基类
from ...core.theme import theme_manager, ThemeMode
from ...core.theme.palette import Color
from ...core.theme.contrast import get_contrast_color
from ...core.base import QBaseWidget, QuasarWidgetMixin


# ★ 核心修复 1：继承 QWidget 和 ThemedWidget
class LineProgress(QWidget, QBaseWidget):
    """
    旗舰版 线形进度条。
    支持自定义粗细、平滑过渡动画，以及深浅色模式自动适配轨道底色。
    """

    def __init__(self, value=0, color=Color.PRIMARY, thickness=8,
                 animation_speed=500, parent=None):
        super().__init__(parent)
        # ★ 挂载主题监听
        self.setup_theme()

        self._value = max(0, min(100, value))
        self._color = QColor(color)
        self._thickness = thickness
        self._animation_speed = animation_speed

        # 动态获取轨道背景色
        self._bg_color = QColor(theme_manager.get_color("border"))

        # 动画进度
        self._progress = float(self._value)
        self._anim = QPropertyAnimation(self, b"progress")
        self._anim.setDuration(animation_speed)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 宽度自适应，高度由粗细决定
        self.setMinimumWidth(thickness * 4)
        self.setFixedHeight(thickness)

    @Property(float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, v):
        self._progress = v
        self.update()

    def setValue(self, value: int):
        new_val = max(0, min(100, value))
        if new_val == self._value and self._anim.state() != QPropertyAnimation.State.Running:
            return
        self._value = new_val
        self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(float(self._value))
        self._anim.start()

    def value(self) -> int:
        return self._value

    def _on_theme_changed(self, mode: ThemeMode):
        # ★ 主题切换时自动更新轨道颜色
        self._bg_color = QColor(theme_manager.get_color("border"))
        super()._on_theme_changed(mode)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        radius = h / 2.0

        # 1. 画底槽
        pen_bg = QPen(self._bg_color, h)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawLine(int(radius), int(radius), int(w - radius), int(radius))

        # 2. 画进度
        if self._progress > 0:
            # 确保最小宽度为一个高度（圆点），最大不超过总宽
            progress_w = max(w * (self._progress / 100.0), h)
            progress_w = min(progress_w, w)

            pen_fg = QPen(self._color, h)
            pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_fg)
            painter.drawLine(int(radius), int(radius), int(progress_w - radius), int(radius))


class CircleProgress(QWidget, QBaseWidget):
    """
    企业级 环形进度条 (旗舰版，对标 Quasar QCircularProgress)
    完美版：支持确定/不确定、反转、渐变，且中心文字颜色智能适配主题。
    """

    def __init__(self, value=0, color=Color.PRIMARY, size=64, thickness=6,
                 show_value=True, indeterminate=False, reverse=False,
                 track_color=None, center_color=None, rounded=True,
                 angle=0, animation_speed=500, font_size=0, gradient=False,
                 parent=None):
        super().__init__(parent)
        # ★ 挂载主题监听
        self.setup_theme()

        self.setFixedSize(size, size)  # type: ignore[arg-type]

        self._value = max(0, min(100, value))
        self._color = QColor(color)

        # 如果未指定 track_color，使用主题的 border 颜色
        self._track_custom_color = track_color
        self._bg_color = QColor(track_color) if track_color else QColor(theme_manager.get_color("border"))

        self._center_color = (QColor(center_color) if center_color is not None
                              else QColor(Qt.GlobalColor.transparent))
        self._thickness = thickness
        self._show_value = show_value
        self._indeterminate = indeterminate
        self._reverse = reverse
        self._rounded = rounded
        self._angle = angle % 360
        self._font_size = font_size
        self._gradient = gradient
        self._animation_speed = animation_speed

        # 确定态动画
        self._progress = float(self._value)
        self._anim = QPropertyAnimation(self, b"progress")
        self._anim.setDuration(animation_speed)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 不确定态动画
        self._rotation_angle = 0.0
        self._phase = 0.0

        self._rot_anim = QPropertyAnimation(self, b"rotation_angle")
        self._rot_anim.setDuration(1500)
        self._rot_anim.setStartValue(0.0)
        self._rot_anim.setEndValue(360.0)
        self._rot_anim.setLoopCount(-1)
        self._rot_anim.setEasingCurve(QEasingCurve.Type.Linear)

        self._phase_anim = QPropertyAnimation(self, b"phase")
        self._phase_anim.setDuration(2000)
        self._phase_anim.setStartValue(0.0)
        self._phase_anim.setEndValue(2 * math.pi)
        self._phase_anim.setLoopCount(-1)
        self._phase_anim.setEasingCurve(QEasingCurve.Type.Linear)

        if self._indeterminate:
            self._start_indeterminate_anim()

    # ==========================================================
    # 动画属性
    # ==========================================================
    @Property(float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, v):
        self._progress = v
        self.update()

    @Property(float)
    def rotation_angle(self) -> float:
        return self._rotation_angle

    @rotation_angle.setter
    def rotation_angle(self, v):
        self._rotation_angle = v
        self.update()

    @Property(float)
    def phase(self) -> float:
        return self._phase

    @phase.setter
    def phase(self, v):
        self._phase = v
        self.update()

    # ==========================================================
    # 公共 API
    # ==========================================================
    def setValue(self, value: int):
        if self._indeterminate:
            return
        new_val = max(0, min(100, value))
        if new_val == self._value and self._anim.state() != QPropertyAnimation.State.Running:
            return
        self._value = new_val
        self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(float(self._value))
        self._anim.start()

    def value(self) -> int:
        return self._value

    def setIndeterminate(self, state: bool):
        if self._indeterminate == state:
            return
        self._indeterminate = state
        if state:
            self._start_indeterminate_anim()
        else:
            self._stop_indeterminate_anim()
            self.update()

    def _start_indeterminate_anim(self):
        self._rot_anim.start()
        self._phase_anim.start()

    def _stop_indeterminate_anim(self):
        self._rot_anim.stop()
        self._phase_anim.stop()
        self._rotation_angle = 0.0
        self._phase = 0.0

    def isIndeterminate(self) -> bool:
        return self._indeterminate

    def setReverse(self, state: bool):
        self._reverse = state
        self.update()

    def setThickness(self, t: int):
        self._thickness = t
        self.update()

    def setRounded(self, on: bool):
        self._rounded = on
        self.update()

    def setAngle(self, deg: float):
        self._angle = deg % 360
        self.update()

    def setColor(self, color):
        self._color = QColor(color)
        self.update()

    def setTrackColor(self, color):
        self._track_custom_color = color
        self._bg_color = QColor(color) if color else QColor(theme_manager.get_color("border"))
        self.update()

    def setCenterColor(self, color):
        self._center_color = (QColor(color) if color is not None
                              else QColor(Qt.GlobalColor.transparent))
        self.update()

    def setShowValue(self, on: bool):
        self._show_value = on
        self.update()

    def setFontSize(self, px: int):
        self._font_size = px
        self.update()

    def setAnimationSpeed(self, ms: int):
        self._animation_speed = ms
        self._anim.setDuration(ms)

    def setGradient(self, on: bool):
        self._gradient = on
        self.update()

    # ==========================================================
    # 主题联动
    # ==========================================================
    def _on_theme_changed(self, mode: ThemeMode):
        # ★ 如果用户没有自定义 track_color，则跟随主题更新背景轨道
        if self._track_custom_color is None:
            self._bg_color = QColor(theme_manager.get_color("border"))
        super()._on_theme_changed(mode)

    # ==========================================================
    # 核心绘制
    # ==========================================================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        t = self._thickness
        rect = QRectF(t / 2, t / 2, self.width() - t, self.height() - t)

        # 1. 中心填充
        if self._center_color.alpha() > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._center_color)
            painter.drawEllipse(rect)

        # 2. 背景轨道
        if self._bg_color.alpha() > 0:
            pen_bg = QPen(self._bg_color, t)
            if self._rounded:
                pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_bg)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(rect)

        # 3. 进度弧线
        if self._indeterminate:
            self._draw_indeterminate(painter, rect)
        elif self._progress > 0:
            self._draw_determinate(painter, rect)

        # 4. 中心文字
        if self._show_value and not self._indeterminate:
            self._draw_center_text(painter)

    def _build_pen(self) -> QPen:
        pen = QPen()
        pen.setWidth(self._thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap if self._rounded
                        else Qt.PenCapStyle.FlatCap)
        if self._gradient:
            gradient = QConicalGradient(self.rect().center(), -90)
            gradient.setColorAt(0.0, self._color)
            gradient.setColorAt(0.5, self._color.lighter(130))
            gradient.setColorAt(1.0, self._color)
            pen.setBrush(gradient)
        else:
            pen.setColor(self._color)
        return pen

    def _draw_determinate(self, painter, rect):
        painter.setPen(self._build_pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)

        start_deg = 90 - self._angle
        span_deg = 360.0 * (self._progress / 100.0)

        if self._reverse:
            painter.drawArc(rect, int(start_deg * 16), int(span_deg * 16))
        else:
            painter.drawArc(rect, int(start_deg * 16), int(-span_deg * 16))

    def _draw_indeterminate(self, painter, rect):
        painter.setPen(self._build_pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)

        sin_val = 0.5 + 0.5 * math.sin(self._phase)
        arc_span = 60.0 + 240.0 * sin_val

        if self._reverse:
            start_deg = (90 + self._angle + self._rotation_angle) % 360
            painter.drawArc(rect, int(start_deg * 16), int(arc_span * 16))
        else:
            start_deg = (90 - self._angle - self._rotation_angle) % 360
            painter.drawArc(rect, int(start_deg * 16), int(-arc_span * 16))

    def _draw_center_text(self, painter):
        font = QFont("Arial")
        font.setPixelSize(self._font_size if self._font_size > 0
                          else int(self.width() * 0.22))
        font.setBold(True)
        painter.setFont(font)

        # ★ 核心修复：智能文字颜色
        if self._center_color.alpha() > 0:
            # 如果用户指定了中心填充色，自动计算对比色（黑或白）
            text_color = QColor(get_contrast_color(self._center_color.name()))
        else:
            # 如果中心是透明的，直接使用当前主题的主文字颜色！
            # 这样深色模式下是白字，浅色模式下是深灰/黑字，绝对不会隐形。
            text_color = QColor(theme_manager.get_color("text_primary"))

        painter.setPen(text_color)
        text = f"{int(round(self._progress))}%"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
