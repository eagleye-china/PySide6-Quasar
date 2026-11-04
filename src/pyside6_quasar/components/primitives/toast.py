# quasar/components/toast.py
from enum import Enum
from typing import Optional, Union

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRectF,
    QSize, QPointF
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QFont, QPen, QGuiApplication,
    QIcon, QPixmap, QFontMetrics
)
from PySide6.QtWidgets import QWidget

from ...core.theme import theme_manager, ThemeMode
from ...core.theme.palette import Color
from ...core.theme.contrast import get_contrast_color
from ...core.base import QBaseWidget, QuasarWidgetMixin


class ToastType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    WARNING = "warning"
    INFO = "info"
    ONGOING = "ongoing"
    CUSTOM = "custom"


class ToastPosition(Enum):
    TOP_LEFT = "top-left"
    TOP = "top"
    TOP_RIGHT = "top-right"
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM = "bottom"
    BOTTOM_RIGHT = "bottom-right"


_TOAST_REGISTRY: dict = {}


class Toast(QWidget, ThemedWidget):
    """
    旗舰版通知组件，对标 Quasar Notify 插件。
    完美支持浅色/深色主题自适应，尺寸智能测量与自动折行。
    """

    def __init__(
            self,
            message: str = "",
            toast_type: Union[str, ToastType] = ToastType.INFO,
            caption: str = "",
            icon: Optional[Union[str, QIcon]] = None,
            avatar: Optional[str] = None,
            spinner: bool = False,
            spinner_color: str = Color.PRIMARY,
            multi_line: bool = False,
            html: bool = False,
            position: ToastPosition = ToastPosition.BOTTOM,
            timeout: int = 2000,
            group: Union[bool, str, int] = True,
            progress: bool = False,
            actions: Optional[list] = None,
            color: Optional[str] = None,
            text_color: Optional[str] = None,
            parent=None,
    ):
        super().__init__(parent)
        self.setup_theme()

        self._progress_update_time = None
        self._message = message
        self._caption = caption

        if isinstance(toast_type, str):
            t_lower = toast_type.lower()
            if t_lower == "success":
                toast_type = "positive"
            elif t_lower == "error":
                toast_type = "negative"

        self._toast_type = toast_type if isinstance(toast_type, ToastType) else ToastType(toast_type)
        self._position = position if isinstance(position, ToastPosition) else ToastPosition(position)
        self._timeout = timeout
        self._multi_line = multi_line
        self._html = html

        self._custom_color = color
        self._custom_text_color = text_color
        self._bg_color = QColor()
        self._fg_color = QColor()
        self._update_theme_colors()

        self._icon = self._coerce_icon(icon)
        self._avatar = avatar
        self._spinner = spinner
        self._spinner_color = QColor(spinner_color)

        self._actions = actions or []

        self._group_key = self._compute_group_key(group)
        self._group_badge_count = 0

        self._show_progress = progress and timeout > 0
        self._progress_value = 1.0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.ToolTip |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._compute_size()

        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(300)

        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self.dismiss)

        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(16)
        self._progress_timer.timeout.connect(self._update_progress)

        self._spinner_angle = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(50)
        self._spinner_timer.timeout.connect(lambda: self._update_spinner())
        if self._spinner:
            self._spinner_timer.start()

        self.setAccessibleName(message or "Notification")

    def _update_theme_colors(self):
        if self._custom_color:
            self._bg_color = QColor(self._custom_color)
            self._fg_color = QColor(get_contrast_color(self._custom_color))
        elif self._toast_type == ToastType.POSITIVE:
            self._bg_color = QColor(Color.POSITIVE)
            self._fg_color = QColor(get_contrast_color(Color.POSITIVE))
        elif self._toast_type == ToastType.NEGATIVE:
            self._bg_color = QColor(Color.NEGATIVE)
            self._fg_color = QColor(get_contrast_color(Color.NEGATIVE))
        elif self._toast_type == ToastType.WARNING:
            self._bg_color = QColor(Color.WARNING)
            self._fg_color = QColor(get_contrast_color(Color.WARNING))
        elif self._toast_type == ToastType.INFO:
            self._bg_color = QColor(Color.INFO)
            self._fg_color = QColor(get_contrast_color(Color.INFO))
        else:
            self._bg_color = QColor(theme_manager.get_color("surface"))
            self._fg_color = QColor(theme_manager.get_color("text_primary"))

        if self._custom_text_color:
            self._fg_color = QColor(self._custom_text_color)

    def _on_theme_changed(self, mode: ThemeMode):
        self._update_theme_colors()
        super()._on_theme_changed(mode)

    def show_toast(self):
        self.show()
        self._apply_position()

        self._fade_anim.stop()
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.start()

        if self._timeout > 0:
            self._timeout_timer.start(self._timeout)
            if self._show_progress:
                self._progress_timer.start()
                self._progress_value = 1.0
                self._progress_update_time = self._timeout

    def dismiss(self):
        self._timeout_timer.stop()
        self._progress_timer.stop()
        self._spinner_timer.stop()

        self._fade_anim.stop()
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_anim.finished.connect(self._on_fade_out_finished)
        self._fade_anim.start()

    def update_message(self, message: str, caption: str = ""):
        self._message = message
        self._caption = caption
        self._compute_size()
        self._apply_position()
        self.update()

    def update_progress(self, value: float):
        self._progress_value = max(0.0, min(1.0, value))
        self.update()

    def set_type(self, toast_type: Union[str, ToastType]):
        self._toast_type = toast_type if isinstance(toast_type, ToastType) else ToastType(toast_type)
        self._update_theme_colors()
        self.update()

    def _on_fade_out_finished(self):
        if self._group_key in _TOAST_REGISTRY:
            del _TOAST_REGISTRY[self._group_key]
        self.close()

    def _compute_group_key(self, group: Union[bool, str, int]) -> Union[str, int, None]:
        if group is False:
            return None
        if group is True:
            key = f"{self._message}_{self._caption}_{self._multi_line}_{self._position.value}"
            for act in self._actions:
                key += f"_{act.get('label', '')}"
            return key
        return group

    # ================= 核心修复：精确测量尺寸与智能折行 =================
    def _compute_size(self):
        fm_msg = QFontMetrics(QFont("Arial", 11, QFont.Weight.Bold))
        fm_cap = QFontMetrics(QFont("Arial", 9))

        icon_w = 0
        if self._spinner or self._avatar or self._icon:
            icon_w = 32
        elif self._toast_type != ToastType.CUSTOM:
            icon_w = 26  # ★ 适度微调图标占位
        padding_x = 32 + icon_w

        text_w = fm_msg.horizontalAdvance(self._message)
        caption_w = fm_cap.horizontalAdvance(self._caption) if self._caption else 0
        content_w = max(text_w, caption_w)

        # ★ 稍微放宽最大宽度到 380，给长文本多一点喘息空间
        max_allowed_w = 380
        if content_w + padding_x > max_allowed_w:
            self._w = max_allowed_w
            self._multi_line = True
            self._h = 80
        else:
            self._w = max(200, content_w + padding_x)
            self._h = 80 if self._multi_line else 52

        self.setFixedSize(int(self._w), int(self._h))

    def _apply_position(self):
        screen = QGuiApplication.primaryScreen().availableGeometry()
        parent = self.parent()
        if parent:
            global_pos = parent.mapToGlobal(QPoint(0, 0))
            base_x = global_pos.x()
            base_y = global_pos.y()
            w, h = parent.width(), parent.height()
        else:
            base_x = screen.x()
            base_y = screen.y()
            w, h = screen.width(), screen.height()

        margin = 20
        pos = self._position

        if pos == ToastPosition.TOP_LEFT:
            x = base_x + margin
            y = base_y + margin
        elif pos == ToastPosition.TOP:
            x = base_x + (w - self._w) // 2
            y = base_y + margin
        elif pos == ToastPosition.TOP_RIGHT:
            x = base_x + w - self._w - margin
            y = base_y + margin
        elif pos == ToastPosition.LEFT:
            x = base_x + margin
            y = base_y + (h - self._h) // 2
        elif pos == ToastPosition.CENTER:
            x = base_x + (w - self._w) // 2
            y = base_y + (h - self._h) // 2
        elif pos == ToastPosition.RIGHT:
            x = base_x + w - self._w - margin
            y = base_y + (h - self._h) // 2
        elif pos == ToastPosition.BOTTOM_LEFT:
            x = base_x + margin
            y = base_y + h - self._h - margin
        elif pos == ToastPosition.BOTTOM_RIGHT:
            x = base_x + w - self._w - margin
            y = base_y + h - self._h - margin
        else:
            x = base_x + (w - self._w) // 2
            y = base_y + h - self._h - margin

        self.move(x, y)

    def _update_progress(self):
        elapsed = self._timeout - self._timeout_timer.remainingTime()
        if self._timeout > 0:
            self._progress_value = max(0.0, 1.0 - elapsed / self._timeout)
        self.update()

    def _update_spinner(self):
        self._spinner_angle = (self._spinner_angle + 30) % 360
        self.update()

    @staticmethod
    def _coerce_icon(icon: Optional[Union[str, QIcon]]) -> Optional[QIcon]:
        if isinstance(icon, str):
            return QIcon(icon)
        return icon

    # ================= 绘制 =================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = 12 if not self._multi_line else 8
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        painter.fillPath(path, self._bg_color)

        border_color = QColor(theme_manager.get_color("border"))
        border_color.setAlphaF(0.5)
        painter.setPen(QPen(border_color, 1))
        painter.drawPath(path)

        left_margin = 16
        icon_y = self._h // 2
        icon_size = 24

        if self._spinner:
            painter.setPen(QPen(self._spinner_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            spinner_rect = QRectF(
                left_margin, icon_y - icon_size // 2,
                icon_size, icon_size
            )
            painter.drawArc(spinner_rect, self._spinner_angle * 16, 270 * 16)
            left_margin += icon_size + 12

        elif self._avatar:
            pixmap = QPixmap(self._avatar)
            if not pixmap.isNull():
                avatar_path = QPainterPath()
                avatar_path.addEllipse(left_margin, icon_y - icon_size // 2, icon_size, icon_size)
                painter.setClipPath(avatar_path)
                painter.drawPixmap(
                    left_margin, icon_y - icon_size // 2,
                    icon_size, icon_size, pixmap
                )
                painter.setClipping(False)
            left_margin += icon_size + 12

        elif self._icon and not self._icon.isNull():
            pix = self._icon.pixmap(QSize(icon_size, icon_size))
            painter.drawPixmap(
                left_margin, icon_y - icon_size // 2, pix
            )
            left_margin += icon_size + 12

        elif self._toast_type != ToastType.CUSTOM:
            self._draw_type_icon(painter, left_margin, icon_y)
            left_margin += 28

        # 消息文本
        text_x = left_margin
        text_w = self._w - text_x - 20

        fm_msg = QFontMetrics(QFont("Arial", 11, QFont.Weight.Bold))

        if self._multi_line and self._caption:
            painter.setPen(self._fg_color)
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            msg_rect = QRectF(text_x, 12, text_w, 24)
            painter.drawText(
                msg_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self._message
            )

            caption_color = QColor(self._fg_color)
            caption_color.setAlphaF(0.7)
            painter.setPen(caption_color)
            painter.setFont(QFont("Arial", 9))
            cap_rect = QRectF(text_x, 36, text_w, 24)
            painter.drawText(
                cap_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                self._caption
            )
        else:
            painter.setPen(self._fg_color)
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))

            # 核心修复：支持长文本自动折行
            is_wrap = self._multi_line or fm_msg.horizontalAdvance(self._message) > (text_w - 10)
            align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            if is_wrap:
                align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                text_rect = QRectF(text_x, 10, text_w, self._h - 20)
            else:
                text_rect = QRectF(text_x, 0, text_w, self._h)

            painter.drawText(
                text_rect,
                align | Qt.TextFlag.TextWordWrap,
                self._message
            )

        if self._actions:
            self._draw_actions(painter)

        if self._group_badge_count > 1:
            self._draw_badge(painter)

        if self._show_progress and self._progress_value > 0:
            self._draw_progress(painter, path)

    # ================= 核心修复：抛弃隐身圆盘，直接画高对比度符号 =================
    def _draw_type_icon(self, painter, x: float, cy: float):
        # 图标颜色完全跟随文字颜色，保证在彩色背景上绝对清晰
        color = QColor(self._fg_color)
        r = 8
        cx = x + r

        # 1. 画线框圆底
        pen = QPen(color, 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # 2. 画内部符号（加粗一点点，显得饱满）
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        if self._toast_type == ToastType.INFO:
            # 信息 i：上面一点，下面一竖
            painter.drawPoint(QPointF(cx, cy - 3.5))
            painter.drawLine(QPointF(cx, cy - 1), QPointF(cx, cy + 4))

        elif self._toast_type == ToastType.WARNING:
            # 叹号 !
            painter.drawLine(QPointF(cx, cy - 4), QPointF(cx, cy + 1))
            painter.drawPoint(QPointF(cx, cy + 4))

        elif self._toast_type == ToastType.POSITIVE:
            # 勾 √ （这里修复了缺少的括号）
            painter.drawLine(QPointF(cx - 3, cy), QPointF(cx - 1, cy + 2))
            painter.drawLine(QPointF(cx - 1, cy + 2), QPointF(cx + 4, cy - 3))

        elif self._toast_type == ToastType.NEGATIVE:
            # 叉 ×
            painter.drawLine(QPointF(cx - 3, cy - 3), QPointF(cx + 3, cy + 3))
            painter.drawLine(QPointF(cx - 3, cy + 3), QPointF(cx + 3, cy - 3))

    def _draw_actions(self, painter):
        n = len(self._actions)
        btn_w = 60
        total_w = n * btn_w + (n - 1) * 8
        start_x = self._w - total_w - 16
        cy = self._h // 2

        for i, act in enumerate(self._actions):
            x = start_x + i * (btn_w + 8)
            rect = QRectF(x, cy - 14, btn_w, 28)

            btn_bg = QColor(self._fg_color)
            btn_bg.setAlphaF(0.15)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(btn_bg)
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(self._fg_color)
            font = QFont("Arial", 10, QFont.Weight.Bold)
            painter.setFont(font)
            label = act.get("label", "OK")
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)

    def _draw_badge(self, painter):
        text = str(self._group_badge_count)
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(text)
        badge_w = max(18, text_w + 10)
        badge_h = 18

        x = self._w - badge_w - 8
        y = 4

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(Color.NEGATIVE))
        painter.drawEllipse(QRectF(x, y, badge_w, badge_h))

        painter.setPen(QColor("#ffffff"))
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(x, y, badge_w, badge_h),
            Qt.AlignmentFlag.AlignCenter,
            text
        )

    def _draw_progress(self, painter, path):
        bar_h = 3
        bar_rect = QRectF(
            0, self._h - bar_h,
               self._w * self._progress_value, bar_h
        )
        painter.save()
        painter.setClipPath(path)
        painter.setPen(Qt.PenStyle.NoPen)

        if self._spinner:
            painter.setBrush(self._spinner_color)
        else:
            prog_color = QColor(self._fg_color)
            prog_color.setAlphaF(0.4)
            painter.setBrush(prog_color)

        painter.drawRect(bar_rect)
        painter.restore()

    # ================= 类方法 =================
    @classmethod
    def create(cls, **kwargs) -> "Toast":
        toast = cls(**kwargs)
        toast.show_toast()
        return toast

    @classmethod
    def positive(cls, message: str, **kwargs) -> "Toast":
        return cls.create(message=message, toast_type=ToastType.POSITIVE, **kwargs)

    @classmethod
    def negative(cls, message: str, **kwargs) -> "Toast":
        return cls.create(message=message, toast_type=ToastType.NEGATIVE, **kwargs)

    @classmethod
    def warning(cls, message: str, **kwargs) -> "Toast":
        return cls.create(message=message, toast_type=ToastType.WARNING, **kwargs)

    @classmethod
    def info(cls, message: str, **kwargs) -> "Toast":
        return cls.create(message=message, toast_type=ToastType.INFO, **kwargs)
