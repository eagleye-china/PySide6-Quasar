# src/pyside6_quasar/components/primitives/badge.py
"""
pyside6_quasar.components.primitives.badge
==========================================
企业级徽标组件 (对标 Quasar QBadge)

支持特性:
    - 浮动 / 内联两种定位模式
    - 圆点 / 胶囊 / 多行三种形态
    - 透明 / 轮廓 两种风格
    - 顶部 / 中部 / 底部 三种对齐
    - 智能边框对比度
    - 全局主题响应
    - 目标控件销毁自动清理
"""

from enum import Enum
from typing import Union, Optional, Tuple

from PySide6.QtCore import Qt, QRectF, QEvent, QPoint, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QFont, QPen, QFontMetrics, QPainterPath,
    QPaintEvent
)
from PySide6.QtWidgets import QWidget

# ═══════════════════════════════════════════════════════════════
# 从 core.base 统一导入（re-export 了 theme 相关能力）
# ═══════════════════════════════════════════════════════════════
from ...core.base import (
    QBaseWidget,
    theme_manager,
    ThemeMode,
    Color,
    get_contrast_color,
)


class BadgeAlign(Enum):
    """内联模式下的垂直对齐方式"""
    TOP = 1
    MIDDLE = 2
    BOTTOM = 3


# ═══════════════════════════════════════════════════════════════
# Badge 主体
# ═══════════════════════════════════════════════════════════════

class Badge(QBaseWidget):
    """
    企业级徽标组件。

    设计要点:
        - 自身挂载到顶层窗口，避免被父控件布局裁剪
        - 通过事件过滤器与 target_widget 保持几何同步
        - 不接收焦点、不响应鼠标（透明穿透）
        - 主题切换时自动重绘边框与文字对比色

    Args:
        target_widget: 徽标挂载的目标控件（必填）
        content:       显示内容。int → 数字（超 max_value 显示 N+）；str → 原样显示
        color:         背景色
        text_color:    文字色（None → 自动按背景对比度计算）
        border_color:  边框色（None → 按主题 surface/border 智能计算）
        max_value:     数字上限，超过显示 "{max_value}+"
        is_dot:        是否显示为圆点（无文字）
        offset:        浮动模式下的像素偏移 (x, y)
        floating:      True → 浮动右上角；False → 内联对齐
        rounded:       是否使用圆角胶囊（无文字时自动为椭圆）
        transparent:   背景是否半透明
        outline:       是否为轮廓模式（无填充，仅描边）
        multi_line:    是否允许文字换行（影响尺寸计算）
        align:         内联模式下的垂直对齐方式
    """

    # 尺寸常量（逻辑像素）
    _DOT_SIZE = 14
    _CAPSULE_HEIGHT = 20
    _CAPSULE_PADDING_H = 16
    _MULTILINE_MAX_W = 120
    _MULTILINE_PADDING = (10, 4)  # (水平, 垂直)

    def __init__(
            self,
            target_widget: QWidget,
            content: Union[str, int] = "",
            color: str = Color.NEGATIVE,
            text_color: Optional[str] = None,
            border_color: Optional[str] = None,
            max_value: int = 99,
            is_dot: bool = False,
            offset: Tuple[int, int] = (0, 0),
            floating: bool = True,
            rounded: bool = False,
            transparent: bool = False,
            outline: bool = False,
            multi_line: bool = False,
            align: BadgeAlign = BadgeAlign.MIDDLE,
            parent: Optional[QWidget] = None,
    ):
        # ─── 参数校验 ───
        if target_widget is None:
            raise ValueError("Badge 必须指定 target_widget")

        self._target = target_widget

        # ─── 挂载到顶层窗口（避免被父布局裁剪）───
        top_window = target_widget.window()
        super().__init__(parent or top_window)

        # ─── 不接收焦点、不响应鼠标 ───
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # ─── 反向引用（便于外部通过 target._badge_instance 访问）───
        target_widget._badge_instance = self  # type: ignore[attr-defined]

        # ─── 配置 ───
        self._content = content
        self._color = QColor(color) if not isinstance(color, QColor) else color
        self._explicit_text_color = QColor(text_color) if text_color else None
        self._explicit_border_color = QColor(border_color) if border_color else None
        self._max_value = max_value
        self._is_dot = is_dot
        self._offset = offset
        self._floating = floating
        self._rounded = rounded
        self._transparent = transparent
        self._outline = outline
        self._multi_line = multi_line
        self._align = align

        # ─── 尺寸缓存 ───
        self._w = 0
        self._h = 0

        # ─── 计算初始尺寸 ───
        self._update_size()

        # ─── 监听目标控件事件 ───
        self._target.installEventFilter(self)
        # 目标控件销毁时，自动清理自身
        self._target.destroyed.connect(self._on_target_destroyed)

        # ─── 延迟挂载（等布局完成）───
        QTimer.singleShot(10, self._force_attach)

    # ═══════════════════════════════════════════════════════════
    # 公共 API
    # ═══════════════════════════════════════════════════════════

    def set_content(
            self,
            content: Union[str, int, None] = None,
            is_dot: Optional[bool] = None,
    ) -> None:
        """更新内容（含数字截断）。"""
        self._content = content if content is not None else self._content
        if is_dot is not None:
            self._is_dot = is_dot
        self._update_size()
        self._sync_geometry()
        self.update()

    def set_floating(self, floating: bool) -> None:
        """切换浮动 / 内联模式。"""
        self._floating = floating
        self._sync_geometry()

    def set_rounded(self, rounded: bool) -> None:
        """切换圆角胶囊 / 矩形形态。"""
        self._rounded = rounded
        self._update_size()
        self.update()

    def set_outline(self, outline: bool) -> None:
        """切换轮廓模式。"""
        self._outline = outline
        self.update()

    def set_transparent(self, transparent: bool) -> None:
        """切换透明背景。"""
        self._transparent = transparent
        self.update()

    def detach(self) -> None:
        """从目标控件解绑并自销毁。"""
        if self._target:
            self._target.removeEventFilter(self)
            self._target._badge_instance = None  # type: ignore[attr-defined]
        self.hide()
        self.deleteLater()

    # ═══════════════════════════════════════════════════════════
    # 主题钩子
    # ═══════════════════════════════════════════════════════════

    def _on_theme_changed(self, mode: ThemeMode) -> None:
        """
        主题切换钩子。
        Badge 的所有颜色都在 paintEvent 中实时计算，
        所以这里只需触发重绘即可。
        """
        super()._on_theme_changed(mode)

    # ═══════════════════════════════════════════════════════════
    # 生命周期 & 几何同步
    # ═══════════════════════════════════════════════════════════

    def _on_target_destroyed(self) -> None:
        """目标控件销毁时，自动清理自身（避免悬挂引用）。"""
        self._target = None  # type: ignore[assignment]
        self.deleteLater()

    def _force_attach(self) -> None:
        """延迟挂载到顶层窗口，等待布局完成。"""
        if not self._target or not self.isVisible():
            return

        top_window = self._target.window()
        if self.parentWidget() != top_window:
            self.setParent(top_window)
            self.show()
            self.raise_()

        self._sync_geometry()

    def _sync_geometry(self) -> None:
        """与目标控件同步几何位置。"""
        if (
                not self._target
                or not self._target.isVisible()
                or not self.parentWidget()
        ):
            self.hide()
            return

        self.show()

        # 确保父窗口正确
        top_window = self._target.window()
        if self.parentWidget() != top_window:
            self.setParent(top_window)
            self.show()
            self.raise_()

        # 全局坐标 → 顶层窗口本地坐标
        global_pos = self._target.mapToGlobal(QPoint(0, 0))
        local_pos = top_window.mapFromGlobal(global_pos)

        if self._floating:
            # 浮动模式：右上角锚定
            x = local_pos.x() + self._target.width() - self._w // 2 + self._offset[0]
            y = local_pos.y() - self._h // 2 + self._offset[1]
        else:
            # 内联模式：水平居中，按 align 控制垂直位置
            x = local_pos.x() + (self._target.width() - self._w) // 2
            if self._align == BadgeAlign.TOP:
                y = local_pos.y()
            elif self._align == BadgeAlign.BOTTOM:
                y = local_pos.y() + self._target.height() - self._h
            else:  # MIDDLE
                y = local_pos.y() + (self._target.height() - self._h) // 2

        if self.pos() != QPoint(x, y):
            self.move(x, y)

    def eventFilter(self, watched, event) -> bool:
        """监听目标控件的几何事件，保持同步。"""
        if watched is self._target and event.type() in (
                QEvent.Type.Resize,
                QEvent.Type.Move,
                QEvent.Type.Show,
                QEvent.Type.Paint,
        ):
            self._sync_geometry()
        return super().eventFilter(watched, event)

    # ═══════════════════════════════════════════════════════════
    # 尺寸计算
    # ═══════════════════════════════════════════════════════════

    def _get_display_text(self) -> str:
        """获取用于显示的文字（处理数字截断）。"""
        if self._is_dot or self._content is None or self._content == "":
            return ""

        try:
            val = int(self._content)  # type: ignore[arg-type]
            return f"{self._max_value}+" if val > self._max_value else str(val)
        except (ValueError, TypeError):
            return str(self._content)

    def _get_font(self) -> QFont:
        """
        动态获取字体（跟随 DPR 微调）。
        说明：QFont.setPixelSize 使用逻辑像素，Qt 会自动按 DPR 渲染，
        但在 2x/3x 屏上字号略小更清晰，此处做视觉微调。
        """
        font = QFont("Arial")
        font.setBold(True)
        # 高 DPR 屏上字号微调（-1px 视觉上更精致）
        size = 11 if self.dpr <= 1.5 else 10
        font.setPixelSize(size)
        return font

    def _update_size(self) -> None:
        """根据当前形态重新计算尺寸。"""
        text = self._get_display_text()
        fm = QFontMetrics(self._get_font())

        if not text:
            # 圆点模式
            self._w = self._h = self._DOT_SIZE

        elif self._multi_line:
            # 多行模式
            br = fm.boundingRect(
                QRectF(0, 0, self._MULTILINE_MAX_W, 999).toRect(),
                Qt.TextFlag.TextWordWrap,
                text,
            )
            pad_h, pad_v = self._MULTILINE_PADDING
            self._w = min(self._MULTILINE_MAX_W, br.width() + pad_h * 2)
            self._h = br.height() + pad_v * 2

        else:
            # 单行胶囊模式
            text_w = fm.horizontalAdvance(text)
            self._h = self._CAPSULE_HEIGHT
            self._w = max(self._CAPSULE_HEIGHT, text_w + self._CAPSULE_PADDING_H)

        self.setFixedSize(self._w, self._h)

    # ═══════════════════════════════════════════════════════════
    # 绘制
    # ═══════════════════════════════════════════════════════════

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        text = self._get_display_text()
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        # ─── 颜色计算 ───
        bg = QColor(self._color)
        if self._transparent:
            bg.setAlphaF(0.8)

        # 文字色：显式指定 > 自动对比
        if self._explicit_text_color:
            text_col = QColor(self._explicit_text_color)
        else:
            text_col = QColor(get_contrast_color(self._color.name()))

        # 边框色：显式指定 > 智能主题
        if self._explicit_border_color:
            border_col = QColor(self._explicit_border_color)
        else:
            contrast_bg = get_contrast_color(self._color.name())
            if contrast_bg == Color.WHITE:
                # 深色徽标 → 用浅色边框
                border_col = QColor(theme_manager.get_color("surface"))
            else:
                # 浅色徽标 → 用深色边框
                border_col = QColor(theme_manager.get_color("border"))

        # ─── 形状路径 ───
        path = QPainterPath()
        if not text or self._is_dot:
            path.addEllipse(rect)
        else:
            radius = rect.height() / 2 if self._rounded or True else 4
            # 说明：单行胶囊默认就是胶囊形，radius = 高度的一半
            path.addRoundedRect(rect, radius, radius)

        # ─── 背景 / 轮廓 ───
        if self._outline:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(bg, 1.5))
            text_col = bg  # 轮廓模式文字用主色
        else:
            painter.setBrush(bg)
            border_col.setAlphaF(0.6)  # 弱化边框
            painter.setPen(QPen(border_col, 1.5))

        painter.drawPath(path)

        # ─── 文字 ───
        if text:
            painter.setPen(text_col)
            painter.setFont(self._get_font())

            if self._multi_line:
                painter.drawText(
                    rect.adjusted(6, 2, -6, -2),
                    Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                    text,
                )
            else:
                # 垂直微调 -1px，视觉更居中
                painter.drawText(
                    rect.adjusted(0, -1, 0, 0),
                    Qt.AlignmentFlag.AlignCenter,
                    text,
                )
