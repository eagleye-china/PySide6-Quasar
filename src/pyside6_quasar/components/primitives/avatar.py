# src/pyside6_quasar/components/primitives/avatar.py
import os
import re
from enum import Enum
from typing import Union

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QFont, QIcon, QPen
)
from typing_extensions import override

# ★ 引入 L0 核心基建
from ...core.base import QBaseWidget
from ...core.mixins.badge_mixin import BadgeMixin
from ...core.theme.contrast import get_contrast_color
from ...core.theme.manager import theme_manager, ThemeMode


class AvatarShape(Enum):
    ROUND = 1
    SQUARE = 2
    ROUNDED = 3


class AvatarSize(Enum):
    """对齐 Quasar 官方命名尺寸规范"""
    XS = 18
    SM = 24
    MD = 32
    LG = 38
    XL = 46


_SIZE_NAME_MAP = {
    "xs": AvatarSize.XS.value,
    "sm": AvatarSize.SM.value,
    "md": AvatarSize.MD.value,
    "lg": AvatarSize.LG.value,
    "xl": AvatarSize.XL.value,
}


def _parse_size(size: Union[int, AvatarSize, str, None]) -> int:
    if isinstance(size, AvatarSize):
        return size.value
    if isinstance(size, int):
        return max(1, size)
    if isinstance(size, str):
        s = size.strip().lower()
        if s in _SIZE_NAME_MAP:
            return _SIZE_NAME_MAP[s]
        m = re.match(r"^(\d+(?:\.\d+)?)\s*(px|rem|em)?$", s)
        if m:
            val = float(m.group(1))
            unit = m.group(2)
            if unit == "rem":
                return max(1, int(val * 16))
            if unit == "em":
                return max(1, int(val * 16))
            return max(1, int(val))
    return AvatarSize.MD.value


class Avatar(QBaseWidget, BadgeMixin):
    """
    企业级头像组件。
    继承自 QBaseWidget，自动接管主题监听与焦点管理。
    """

    def __init__(
            self,
            image: Union[str, QPixmap] = "",
            text: str = "",
            icon: Union[str, QIcon, None] = None,
            color: Union[str, None] = None,
            text_color: Union[str, None] = None,
            size: Union[int, AvatarSize, str] = AvatarSize.MD,
            font_size: Union[int, None] = None,
            shape: AvatarShape = AvatarShape.ROUND,
            border_width: int = 0,
            border_color: Union[str, None] = None,
            status_color: Union[str, None] = None,
            status_border_color: Union[str, None] = None,
            parent=None,
    ):
        # 初始化 QBaseWidget（内部已包含 setup_quasar 逻辑）
        super().__init__(parent)

        self._size = _parse_size(size)
        self._shape = shape
        self._text_color = text_color
        self._font_size = font_size
        self._border_width = border_width
        self._status_color = status_color

        # 动态属性初始化
        self._custom_bg = color
        self._custom_border_color = border_color
        self._custom_status_border_color = status_border_color

        # 状态与颜色将在 _update_theme_colors 中拉取
        self._bg_color = QColor()
        self._border_color = QColor()
        self._status_border_color = QColor()
        self._update_theme_colors()

        # 图片处理
        if isinstance(image, str):
            self._image = QPixmap(image) if image else QPixmap()
        elif isinstance(image, QPixmap):
            self._image = image
        else:
            self._image = QPixmap()

        self._text = text

        # 图标处理
        self._icon = None
        if isinstance(icon, str):
            if icon.startswith("img:"):
                path = icon[4:]
                if os.path.exists(path):
                    self._icon = QIcon(path)
            else:
                self._icon = QIcon(icon)
        elif isinstance(icon, QIcon):
            self._icon = icon

        total_size = self._size + border_width * 2
        self.setFixedSize(total_size, total_size)
        self._target_pixmap = None
        self._process_image()

        self.setAccessibleName(text or "Avatar")
        if not text and self._icon:
            self.setAccessibleDescription("Decorative icon avatar")

    def _update_theme_colors(self):
        """根据当前主题动态拉取颜色"""
        if self._custom_bg:
            self._bg_color = QColor(self._custom_bg)
        else:
            # 默认使用主题的主色调
            self._bg_color = QColor(theme_manager.get_color("primary"))

        if self._custom_border_color:
            self._border_color = QColor(self._custom_border_color)
        else:
            # 默认边框色跟随页面背景（实现“挖空”效果）
            self._border_color = QColor(theme_manager.get_color("background"))

        if self._custom_status_border_color:
            self._status_border_color = QColor(self._custom_status_border_color)
        else:
            self._status_border_color = QColor(theme_manager.get_color("background"))

    @override
    def _on_theme_changed(self, mode: ThemeMode):
        """重写主题切换钩子"""
        self._update_theme_colors()
        self._process_image()  # 强制重绘缓存位图
        super()._on_theme_changed(mode)

    @property
    def border_width(self):
        return self._border_width

    @property
    def shape(self) -> AvatarShape:
        return self._shape

    def set_border(self, width: int, color: Union[str, None] = None):
        self._border_width = width
        self._custom_border_color = color
        self._update_theme_colors()
        self.setFixedSize(self._size + width * 2, self._size + width * 2)
        self._process_image()
        self.update()

    def set_shape(self, shape: AvatarShape):
        if self._shape != shape:
            self._shape = shape
            self._process_image()
            self.update()

    def _get_font_size_px(self, inner_width: float) -> int:
        if self._font_size is not None:
            return max(8, int(self._font_size))
        return max(8, int(inner_width * 0.4))

    def _process_image(self):
        # ★ 核心修复：使用动态 DPR 代替原生的 Screen 获取
        dpr = self.dpr
        actual_size = int(self.width() * dpr)

        self._target_pixmap = QPixmap(actual_size, actual_size)
        self._target_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(self._target_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        bw = self._border_width * dpr
        inner_rect = QRectF(bw, bw, actual_size - bw * 2, actual_size - bw * 2)

        path = QPainterPath()
        if self._shape == AvatarShape.SQUARE:
            path.addRect(inner_rect)
        elif self._shape == AvatarShape.ROUNDED:
            r = inner_rect.width() * 0.28
            path.addRoundedRect(inner_rect, r, r)
        else:
            path.addEllipse(inner_rect)

        painter.setClipPath(path)

        if not self._image.isNull():
            src_w, src_h = self._image.width(), self._image.height()
            crop_size = min(src_w, src_h)
            crop_x = (src_w - crop_size) / 2
            crop_y = (src_h - crop_size) / 2
            cropped = self._image.copy(
                int(crop_x), int(crop_y), int(crop_size), int(crop_size)
            )
            painter.drawPixmap(
                int(bw), int(bw),
                int(inner_rect.width()), int(inner_rect.height()),
                cropped,
            )
        else:
            painter.fillPath(path, self._bg_color)

            if self._text_color:
                contrast_color = QColor(self._text_color)
            else:
                contrast_color = QColor(get_contrast_color(self._bg_color.name()))

            if self._text:
                painter.setPen(contrast_color)
                font_size_px = self._get_font_size_px(inner_rect.width())
                font = QFont("Arial", font_size_px, QFont.Weight.Bold)
                painter.setFont(font)
                painter.drawText(
                    inner_rect, Qt.AlignmentFlag.AlignCenter, self._text[:2]
                )
            elif self._icon and not self._icon.isNull():
                icon_size = int(inner_rect.width() * 0.6)
                pixmap = self._icon.pixmap(icon_size, icon_size)
                painter.drawPixmap(
                    int(inner_rect.center().x() - icon_size / 2),
                    int(inner_rect.center().y() - icon_size / 2),
                    pixmap,
                )

        # 绘制边框
        if self._border_width > 0:
            painter.setClipping(False)
            pen = QPen(self._border_color, bw)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            border_rect = QRectF(
                bw / 2, bw / 2, actual_size - bw, actual_size - bw
            )
            path_border = QPainterPath()
            if self._shape == AvatarShape.SQUARE:
                path_border.addRect(border_rect)
            elif self._shape == AvatarShape.ROUNDED:
                r = border_rect.width() * 0.28
                path_border.addRoundedRect(border_rect, r, r)
            else:
                path_border.addEllipse(border_rect)

            painter.drawPath(path_border)

        painter.end()
        self._target_pixmap.setDevicePixelRatio(dpr)

    @override
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(0, 0, self._target_pixmap)

        # 状态指示灯
        if self._status_color:
            dot_size = max(8, int(self._size * 0.25))
            border_width = 2 if self._size > 32 else 1
            offset = self._border_width
            cx = self.width() - offset - dot_size / 2 - 1
            cy = offset + dot_size / 2 + 1
            painter.setPen(QPen(self._status_border_color, border_width))
            painter.setBrush(QColor(self._status_color))
            painter.drawEllipse(
                QPointF(cx, cy), dot_size / 2, dot_size / 2
            )


class AvatarGroup(QBaseWidget):
    """
    头像组：支持重叠、最大数量限制与统一尺寸/形状控制。
    继承自 QBaseWidget，完美响应主题切换。
    """

    def __init__(
            self,
            max_count: int = 10,
            overlap: Union[int, float] = 0.25,
            size: Union[int, AvatarSize, str, None] = None,
            shape: Union[AvatarShape, None] = None,
            parent=None,
    ):
        super().__init__(parent)

        self._avatars = []
        self._max_count = max_count
        self._overlap = overlap
        self._default_size = size
        self._default_shape = shape
        self._overflow_avatar = None

    @staticmethod
    def _get_group_border_color() -> str:
        """获取头像组重叠边缘的描边色"""
        return theme_manager.get_color("background")

    def add_avatar(self, avatar: Avatar):
        if self._default_shape is not None:
            avatar.set_shape(self._default_shape)

        if avatar.border_width == 0:
            avatar.set_border(2, None)

        avatar.setParent(self)
        self._avatars.append(avatar)
        self._update_layout()
        self.update()

    @override
    def _on_theme_changed(self, mode: ThemeMode):
        """主题切换时，级联刷新所有子头像的边框"""
        if self._overflow_avatar:
            self._overflow_avatar.set_border(2, None)

        # 强制重绘所有子头像
        for av in self._avatars:
            av._update_theme_colors()
            av._process_image()

        self._update_layout()
        super()._on_theme_changed(mode)

    def _get_overlap_px(self) -> int:
        if not self._avatars:
            return 0
        if isinstance(self._overlap, float) and 0 < self._overlap < 1:
            return int(self._avatars[0].width() * self._overlap)
        return int(self._overlap)

    def _update_layout(self):
        if self._overflow_avatar:
            self._overflow_avatar.deleteLater()
            self._overflow_avatar = None

        visible = self._avatars[: self._max_count]
        hidden_count = len(self._avatars) - len(visible)

        if hidden_count > 0 and visible:
            visible = visible[: self._max_count - 1]

        overlap_px = self._get_overlap_px()
        x = 0
        for av in visible:
            av.move(x, 0)
            x += av.width() - overlap_px

        if hidden_count > 0:
            first = visible[0] if visible else self._avatars[0]
            overflow = Avatar(
                text=f"+{hidden_count + (len(self._avatars) - len(visible) - hidden_count)}",
                color="#607D8B",
                size=first.width(),
                shape=first.shape,
            )
            overflow.set_border(2, self._get_group_border_color())
            overflow.setParent(self)
            overflow.move(x, 0)
            self._overflow_avatar = overflow
            x += overflow.width() - overlap_px

        total_width = x + overlap_px if x > 0 else 0
        max_height = max(
            (av.height() for av in visible), default=0
        )
        if self._overflow_avatar:
            max_height = max(max_height, self._overflow_avatar.height())
        self.setFixedSize(max(total_width, 0), max_height)
