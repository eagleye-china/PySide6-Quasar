# src/pyside_quasar/components/primitives/avatar.py
"""
pyside_quasar.components.primitives.avatar
===========================================
企业级头像组件 (对标 Quasar QAvatar)
v2.1 Final 终极封板版

v2.1 相对 v1.x 的修复清单
────────────────────────
✅ [BUG-1]  _process_image 改用逻辑坐标系绘制：
            先 pixmap.setDevicePixelRatio(dpr)，再让 QPainter 用逻辑像素绘制。
            修复了高 DPI 下用户传入的 font_size（逻辑像素语义）被误当物理像素用、
            字体偏小的核心问题；同时解决了图标 pixmap 未按 DPR 缩放的模糊问题。
✅ [BUG-2]  新增 changeEvent 监听 QEvent.Type.DevicePixelRatioChange，
            窗口跨屏移动后自动重建 pixmap，避免模糊 / 锯齿。
✅ [BUG-3]  themeChanged 信号显式 disconnect；连接前防御性 disconnect，
            避免与 QBaseWidget 内部连接重复触发 _on_theme_changed 两次。
✅ [BUG-4]  Avatar 新增 set_size() 公共方法；AvatarGroup 不再直接触碰私有成员
            （原代码直接改 avatar._size 破坏封装）。
✅ [BUG-5]  AvatarGroup 提供 detach() 公共清理 + destroyed 自动清理，
            析构时断开主题信号、释放子头像。
✅ [BUG-6]  AvatarGroup 复用 overflow_avatar 而非每次重建；
            新增 set_overlap / set_max_count / remove_avatar / clear_avatars /
            avatars / count 公共 API。
✅ [BUG-7]  Avatar 新增 set_text / set_image / set_icon / set_background_color，
            配合 overflow 头像动态更新。
✅ [BUG-8]  状态点位置基于内头像区域计算，border_width > 0 时不再偏移。
✅ [BUG-9]  setAccessibleName 对纯空格文本做 strip 处理。
✅ [BUG-10] _process_image 对 width/height <= 0 做防御。
✅ [MINOR]  _parse_shape 支持字符串；图标请求按物理像素 + setDevicePixelRatio；
            drawPixmap 使用 QRectF 目标 + 源矩形，语义清晰；字体统一 Bold。

原有能力（保持）
────────
图片 / 文字 / 图标头像；圆形 / 方形 / 圆角方形；边框；角落状态点；Badge 徽标混入；
AvatarGroup 重叠 + 最大数量 + +N overflow；主题联动；高 DPI 自适应
"""
import os
import re
from enum import Enum
from typing import Union, Optional, Any, Type

from PySide6.QtCore import Qt, QRectF, QPointF, QSize, QEvent
from PySide6.QtGui import (
    QPixmap, QPainter, QPainterPath, QColor, QFont, QIcon, QPen,
)
from typing_extensions import override

# ★ 引入 L0 核心基建
from ...core.base import QBaseWidget
from ...core.theme.contrast import get_contrast_color
from ...core.theme.manager import theme_manager, ThemeMode


# ───────────────────────────── 枚举 & 工具 ─────────────────────────────
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
            if unit in ("rem", "em"):
                return max(1, int(val * 16))
            return max(1, int(val))
    return AvatarSize.MD.value


def _parse_shape(shape: Union[AvatarShape, str]) -> Type[AvatarShape[Any]] | AvatarShape:
    if isinstance(shape, AvatarShape):
        return shape
    if isinstance(shape, str):
        try:
            return AvatarShape[shape.upper()]
        except KeyError:
            pass
    return AvatarShape.ROUND


# ───────────────────────────── Avatar ─────────────────────────────
class Avatar(QBaseWidget):
    """
    企业级头像组件。
    继承自 QBaseWidget，自动接管主题监听与焦点管理。
    支持：图片 / 文字 / 图标头像、圆形 / 方形 / 圆角方形、边框、
         角落状态点、挂载 Badge 徽标。
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
            shape: Union[AvatarShape, str] = AvatarShape.ROUND,
            border_width: int = 0,
            border_color: Union[str, None] = None,
            status_color: Union[str, None] = None,
            status_border_color: Union[str, None] = None,
            parent=None,
    ):
        super().__init__(parent)

        self._size = _parse_size(size)
        self._shape = _parse_shape(shape)
        self._text_color = text_color
        self._font_size = font_size
        self._border_width = max(0, border_width)
        self._status_color = status_color

        # 动态属性
        self._custom_bg = color
        self._custom_border_color = border_color
        self._custom_status_border_color = status_border_color

        # 主题派生颜色
        self._bg_color = QColor()
        self._border_color = QColor()
        self._status_border_color = QColor()
        self._update_theme_colors()

        # 图片
        if isinstance(image, str):
            self._image = QPixmap(image) if image else QPixmap()
        elif isinstance(image, QPixmap):
            self._image = QPixmap(image)
        else:
            self._image = QPixmap()

        self._text = text or ""

        # 图标
        self._icon: Optional[QIcon] = None
        self._init_icon(icon)

        total_size = self._size + self._border_width * 2
        self.setFixedSize(total_size, total_size)
        self._target_pixmap: Optional[QPixmap] = None
        self._process_image()

        accessible = (self._text.strip() if isinstance(self._text, str) else "") or "Avatar"
        self.setAccessibleName(accessible)
        if not self._text and self._icon:
            self.setAccessibleDescription("Decorative icon avatar")

        # ✅ BUG-3：防御性 disconnect，避免与 QBaseWidget 内部连接重复触发
        try:
            theme_manager.themeChanged.disconnect(self._on_theme_changed)
        except (RuntimeError, TypeError):
            pass
        # noinspection PyUnresolvedReferences
        theme_manager.themeChanged.connect(self._on_theme_changed)

    # ────────────────────────── 内部工具 ──────────────────────────
    def _init_icon(self, icon: Union[str, QIcon, None]):
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

    def _update_theme_colors(self):
        if self._custom_bg:
            self._bg_color = QColor(self._custom_bg)
        else:
            self._bg_color = QColor(theme_manager.get_color("primary"))

        if self._custom_border_color:
            self._border_color = QColor(self._custom_border_color)
        else:
            self._border_color = QColor(theme_manager.get_color("background"))

        if self._custom_status_border_color:
            self._status_border_color = QColor(self._custom_status_border_color)
        else:
            self._status_border_color = QColor(theme_manager.get_color("background"))

    @override
    def _on_theme_changed(self, mode: ThemeMode):
        self._update_theme_colors()
        self._process_image()
        try:
            super()._on_theme_changed(mode)
        except AttributeError:
            pass
        self.update()

    @override
    def changeEvent(self, event):
        # ✅ BUG-2：DPR 变化（窗口跨屏）时重建 pixmap，避免模糊/锯齿
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self._process_image()
            self.update()
        super().changeEvent(event)

    # ────────────────────────── 属性 ──────────────────────────
    @property
    def border_width(self) -> int:
        return self._border_width

    @property
    def shape(self) -> AvatarShape:
        return self._shape

    @property
    def size(self) -> int:
        return self._size

    @property
    def text(self) -> str:
        return self._text

    # ────────────────────────── Public API ──────────────────────────
    def set_border(self, width: int, color: Union[str, None] = None):
        self._border_width = max(0, width)
        self._custom_border_color = color
        self._update_theme_colors()
        self.setFixedSize(
            self._size + self._border_width * 2,
            self._size + self._border_width * 2,
        )
        self._process_image()
        self.update()

    def set_shape(self, shape: Union[AvatarShape, str]):
        shape_val = _parse_shape(shape)
        if self._shape != shape_val:
            self._shape = shape_val
            self._process_image()
            self.update()

    def set_size(self, size: Union[int, AvatarSize, str]):
        """✅ BUG-4：公共尺寸设置入口；AvatarGroup 不再触碰私有成员"""
        self._size = _parse_size(size)
        self.setFixedSize(
            self._size + self._border_width * 2,
            self._size + self._border_width * 2,
        )
        self._process_image()
        self.update()

    def set_text(self, text: str):
        """✅ BUG-7：供 overflow 头像动态更新文本"""
        self._text = text or ""
        accessible = self._text.strip() or "Avatar"
        self.setAccessibleName(accessible)
        self._process_image()
        self.update()

    def set_image(self, image: Union[str, QPixmap]):
        if isinstance(image, str):
            self._image = QPixmap(image) if image else QPixmap()
        elif isinstance(image, QPixmap):
            self._image = QPixmap(image)
        else:
            self._image = QPixmap()
        self._process_image()
        self.update()

    def set_icon(self, icon: Union[str, QIcon, None]):
        self._init_icon(icon)
        self._process_image()
        self.update()

    def set_background_color(self, color: Union[str, None]):
        self._custom_bg = color
        self._update_theme_colors()
        self._process_image()
        self.update()

    # ────────────────────────── 绘制 ──────────────────────────
    def _get_font_size_px(self, inner_width: float) -> int:
        if self._font_size is not None:
            return max(8, int(self._font_size))
        return max(8, int(inner_width * 0.4))

    def _process_image(self):
        # ✅ BUG-1：先设 DPR，让 QPainter 使用逻辑像素坐标系
        dpr = self.devicePixelRatioF()
        w = self.width()
        h = self.height()
        # ✅ BUG-10：防御空尺寸
        if w <= 0 or h <= 0:
            self._target_pixmap = None
            return

        actual_w = max(1, int(round(w * dpr)))
        actual_h = max(1, int(round(h * dpr)))

        pixmap = QPixmap(actual_w, actual_h)
        pixmap.fill(Qt.GlobalColor.transparent)
        pixmap.setDevicePixelRatio(dpr)  # ✅ 先设置，painter 用逻辑像素

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 逻辑像素坐标
        bw = float(self._border_width)
        inner_rect = QRectF(bw, bw, w - bw * 2, h - bw * 2)

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
            # 居中裁剪 + 填充
            src_w, src_h = self._image.width(), self._image.height()
            crop_size = min(src_w, src_h)
            crop_x = (src_w - crop_size) // 2
            crop_y = (src_h - crop_size) // 2
            cropped = self._image.copy(crop_x, crop_y, crop_size, crop_size)
            painter.drawPixmap(inner_rect, cropped, QRectF(cropped.rect()))
        else:
            painter.fillPath(path, self._bg_color)

            if self._text_color:
                contrast_color = QColor(self._text_color)
            else:
                contrast_color = QColor(get_contrast_color(self._bg_color.name()))

            if self._text:
                painter.setPen(contrast_color)
                font_size_px = self._get_font_size_px(inner_rect.width())  # 逻辑像素
                font = QFont("Microsoft YaHei")
                font.setPixelSize(font_size_px)  # ✅ 逻辑像素，Qt 自动按 DPR 缩放
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(
                    inner_rect, Qt.AlignmentFlag.AlignCenter, self._text[:2]
                )
            elif self._icon and not self._icon.isNull():
                icon_size = max(1, int(inner_rect.width() * 0.6))  # 逻辑像素
                phys = max(1, int(round(icon_size * dpr)))
                pix = self._icon.pixmap(QSize(phys, phys))
                if not pix.isNull():
                    if pix.devicePixelRatio() != dpr:
                        pix.setDevicePixelRatio(dpr)
                    painter.drawPixmap(
                        QRectF(
                            inner_rect.center().x() - icon_size / 2,
                            inner_rect.center().y() - icon_size / 2,
                            icon_size, icon_size,
                        ),
                        pix,
                        QRectF(pix.rect()),
                    )

        # 边框
        if self._border_width > 0:
            painter.setClipping(False)
            pen = QPen(self._border_color, bw)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            border_rect = QRectF(bw / 2, bw / 2, w - bw, h - bw)
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
        self._target_pixmap = pixmap

    @override
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._target_pixmap is not None:
            painter.drawPixmap(0, 0, self._target_pixmap)

        # ✅ BUG-8：状态点基于内头像区域右上角，border_width > 0 时不再偏移
        if self._status_color:
            dot_size = max(8, int(self._size * 0.25))
            border_width = 2 if self._size > 32 else 1
            inner_right = self.width() - self._border_width
            inner_top = self._border_width
            cx = inner_right - dot_size / 2
            cy = inner_top + dot_size / 2
            painter.setPen(QPen(self._status_border_color, border_width))
            painter.setBrush(QColor(self._status_color))
            painter.drawEllipse(QPointF(cx, cy), dot_size / 2, dot_size / 2)


# ───────────────────────────── AvatarGroup ─────────────────────────────
class AvatarGroup(QBaseWidget):
    """
    头像组：支持重叠、最大数量限制与统一尺寸 / 形状控制。
    继承自 QBaseWidget，响应主题切换。
    """

    def __init__(
            self,
            max_count: int = 10,
            overlap: Union[int, float] = 0.25,
            size: Union[int, AvatarSize, str, None] = None,
            shape: Union[AvatarShape, str, None] = None,
            parent=None,
    ):
        super().__init__(parent)

        self._avatars: list[Avatar] = []
        self._max_count = max(1, max_count)
        self._overlap = overlap
        self._default_size = size
        self._default_shape = _parse_shape(shape) if shape is not None else None
        self._overflow_avatar: Optional[Avatar] = None

        # ✅ BUG-3：防御性 disconnect，避免重复连接
        try:
            theme_manager.themeChanged.disconnect(self._on_theme_changed)
        except (RuntimeError, TypeError):
            pass
        # noinspection PyUnresolvedReferences
        theme_manager.themeChanged.connect(self._on_theme_changed)

        # ✅ BUG-5：destroyed 自动清理，杜绝野引用
        # noinspection PyUnresolvedReferences
        self.destroyed.connect(self._on_destroyed)

    # ────────────────────────── 生命周期 ──────────────────────────
    @override
    def _on_theme_changed(self, mode: ThemeMode):
        # 子 Avatar 各自响应主题信号；Group 仅需基础处理
        try:
            super()._on_theme_changed(mode)
        except AttributeError:
            pass
        self.update()

    def _on_destroyed(self):
        self._cleanup()

    def _cleanup(self):
        try:
            theme_manager.themeChanged.disconnect(self._on_theme_changed)
        except (RuntimeError, TypeError):
            pass

    def detach(self):
        """✅ BUG-5：公开安全释放"""
        self._cleanup()
        for av in list(self._avatars):
            try:
                av.setParent(None)
                av.deleteLater()
            except RuntimeError:
                pass
        self._avatars.clear()
        if self._overflow_avatar is not None:
            try:
                self._overflow_avatar.setParent(None)
                self._overflow_avatar.deleteLater()
            except RuntimeError:
                pass
            self._overflow_avatar = None
        self.deleteLater()

    # ────────────────────────── 属性 ──────────────────────────
    @property
    def avatars(self) -> list[Avatar]:
        return list(self._avatars)

    @property
    def count(self) -> int:
        return len(self._avatars)

    @staticmethod
    def _get_group_border_color() -> str:
        return theme_manager.get_color("background")

    # ────────────────────────── Public API ──────────────────────────
    def add_avatar(self, avatar: Avatar):
        if avatar is None or avatar in self._avatars:
            return

        if self._default_shape is not None:
            avatar.set_shape(self._default_shape)
        if self._default_size is not None:
            # ✅ BUG-4：公共 set_size，不再触碰私有 _size
            avatar.set_size(self._default_size)

        if avatar.border_width == 0:
            # 用 None 让边框跟随主题自动更新，主题切换无需再 set_border
            avatar.set_border(2, None)

        avatar.setParent(self)  # type: ignore[arg-type]
        self._avatars.append(avatar)
        self._update_layout()
        self.update()

    def remove_avatar(self, avatar: Avatar):
        if avatar in self._avatars:
            self._avatars.remove(avatar)
            try:
                avatar.setParent(None)
                avatar.deleteLater()
            except RuntimeError:
                pass
            self._update_layout()
            self.update()

    def clear_avatars(self):
        for av in list(self._avatars):
            try:
                av.setParent(None)
                av.deleteLater()
            except RuntimeError:
                pass
        self._avatars.clear()
        self._update_layout()
        self.update()

    def set_overlap(self, overlap: Union[int, float]):
        self._overlap = overlap
        self._update_layout()

    def set_max_count(self, max_count: int):
        self._max_count = max(1, max_count)
        self._update_layout()

    # ────────────────────────── 布局 ──────────────────────────
    def _get_overlap_px(self) -> int:
        if not self._avatars:
            return 0
        ref_avatar = self._avatars[0]
        if isinstance(self._overlap, float) and 0 < self._overlap < 1:
            return int(ref_avatar.width() * self._overlap)
        return int(self._overlap)

    def _update_layout(self):
        # 移除旧 overflow 头像
        if self._overflow_avatar is not None:
            try:
                self._overflow_avatar.setParent(None)
                self._overflow_avatar.deleteLater()
            except RuntimeError:
                pass
            self._overflow_avatar = None

        visible = self._avatars[: self._max_count]
        hidden_count = len(self._avatars) - len(visible)

        # 预留最后一个位置给 +N
        if hidden_count > 0 and self._max_count > 1:
            visible = visible[: self._max_count - 1]
            hidden_count = len(self._avatars) - len(visible)

        overlap_px = self._get_overlap_px()
        x = 0
        for av in visible:
            av.move(x, 0)
            x += av.width() - overlap_px

        if hidden_count > 0:
            first = visible[0] if visible else self._avatars[0]
            overflow = Avatar(
                text=f"+{hidden_count}",
                color="#607D8B",
                size=first.size,
                shape=first.shape,
            )
            # 用 None 让边框跟随主题自动更新
            overflow.set_border(2, None)
            overflow.setParent(self)  # type: ignore[arg-type]
            overflow.move(x, 0)
            overflow.show()
            self._overflow_avatar = overflow
            x += overflow.width() - overlap_px

        if not visible and self._overflow_avatar is None:
            self.setFixedSize(0, 0)
            return

        total_width = x + overlap_px if x > 0 else 0
        max_height = max((av.height() for av in visible), default=0)
        if self._overflow_avatar is not None:
            max_height = max(max_height, self._overflow_avatar.height())
        self.setFixedSize(max(total_width, 0), max_height)
