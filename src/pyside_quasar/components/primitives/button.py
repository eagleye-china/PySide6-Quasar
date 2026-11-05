# src/pyside_quasar/components/primitives/button.py
"""
pyside_quasar.components.primitives.button
===========================================
企业级按钮组件 (对标 Quasar QBtn)
v2.1 Final 终极封板版

v2.1 相对 v2.0 的修复清单
────────────────────────
✅ [BUG-1] 焦点环原来向外 expand 导致被 widget 裁剪 → 改为向内 inset 半个笔宽 + 1px 留白
✅ [BUG-2] OUTLINE / FLAT 文字色用 contrast(base) → 浅色主题白字白底不可见 → 改为直接用 base 色本身
✅ [BUG-3] 全组件所有 /dpr 操作导致高 DPI 下视觉缩水、QPen width 变 0 加载圈消失 → 全部改回逻辑像素；笔宽改用 setWidthF
✅ [BUG-4] ripple 动画并发 → 持有 _ripple_anim 引用并在新动画前 stop 旧的
✅ [BUG-5] stack 模式仅文字时垂直居中错误（total_h 用 icon_sz 而非 fm.height）→ 三支分支独立处理
✅ [BUG-6] stack 模式 elide 宽度错误 → 独立用 content 全宽
✅ [BUG-7] set_loading 强制 setEnabled(False) 会吞掉用户原本的禁用状态 → 改为内部 _is_loading 拦截交互，不再改 isEnabled
✅ [BUG-8] _custom_padding 只在 sizeHint 生效 → 绘制时收窄 contentRect，padding 语义完整
✅ [BUG-9] drawPixmap 未指定逻辑尺寸 → 统一用 QRectF 目标 + pix.rect() 源
✅ [BUG-10] _resolve_colors 不再对 OUTLINE / FLAT 使用 hover_tok / pressed_tok（会变成几乎透明的浅灰）
✅ [MINOR] 删除无意义的 destroy() 覆写；accessibleName 用 strip()；图标像素梯度更平滑；暴露 is_loading 属性

原有能力
────────
尺寸 / Variant / Shape / FAB / ripple / loading / badge / 图标前置后置 / ellipsis / 高 DPI
焦点环可控：focus_ring_width / focus_color / focus_ring_enabled / keep_focus_ring_on_click
"""
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional

from PySide6.QtCore import (
    Qt, QTimer, QRectF, QSize, QPointF, QPropertyAnimation, QEasingCurve, Property,
)
from PySide6.QtGui import (
    QPainter, QColor, QPen, QIcon, QPainterPath, QLinearGradient, QBrush,
    QFocusEvent, QFontMetrics,
)
from PySide6.QtWidgets import QPushButton
from typing_extensions import override

from ...core.base import (
    QuasarWidgetMixin,
    theme_manager,
    Color,
    get_contrast_color,
)


# ───────────────────────────── 枚举定义 ─────────────────────────────
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
        return max(8, size.value)
    if isinstance(size, int):
        return max(8, size)
    if isinstance(size, str):
        s = size.strip().lower()
        if s in _SIZE_MAP:
            return max(8, _SIZE_MAP[s])
        m = re.match(r"^(\d+(?:\.\d+)?)\s*(px)?$", s)
        if m:
            return max(8, int(float(m.group(1))))
    return ButtonSize.MD.value


# export-ignore
@dataclass
class ButtonPaintState:
    """绘制状态上下文，focus仅用于绘制焦点环，不参与颜色计算"""
    hover: bool
    pressed: bool
    focused: bool
    disabled: bool


# ───────────────────────────── Button 主体 ─────────────────────────────
class Button(QPushButton, QuasarWidgetMixin):
    """
    企业级按钮。
    - 原生控件继承：QPushButton + QuasarWidgetMixin + BadgeMixin
    - 焦点规则：默认仅 Tab 键盘焦点显示外圈焦点环，不改按钮底色；鼠标点击是否保留由 keep_focus_ring_on_click 控制
    - 焦点属性：focus_ring_width / focus_color / focus_ring_enabled / keep_focus_ring_on_click
    - 能力：超长文本省略、高 DPI 适配、ripple、loading、badge、多变体、图标、FAB
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
            ellipsis: bool = True,
            # 焦点环属性
            focus_ring_width: int = 2,
            focus_color: Optional[str] = None,
            focus_ring_enabled: bool = True,
            keep_focus_ring_on_click: bool = False,
            parent=None,
    ):
        super().__init__(text, parent)
        self._show_focus_ring = False
        self._is_hovered = False
        self._ellipsis = ellipsis

        # 焦点环配置
        self._focus_ring_width = max(1, focus_ring_width)
        self._focus_color_str = focus_color
        self._focus_ring_enabled = focus_ring_enabled
        self._keep_focus_ring_on_click = keep_focus_ring_on_click

        self.setup_quasar()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)

        # 字符串转枚举
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

        # 尺寸策略
        if fab or fab_mini:
            self._size_val = 56 if fab else 40
            self.setFixedSize(self._size_val, self._size_val)
        elif shape == ButtonShape.ROUND:
            self.setFixedSize(self._size_val, self._size_val)
        else:
            self.setMinimumHeight(self._size_val)
            self.setMinimumWidth(self._size_val * 2)

        self._bg_color = QColor(color)
        self._explicit_text_color = QColor(text_color) if text_color else None

        self._icon_left = self._coerce_icon(icon)
        self._icon_right = self._coerce_icon(icon_right)
        self._custom_padding = self._parse_padding(padding) if padding else None

        # Loading
        self._is_loading = False
        self._percentage: Optional[float] = None
        self._loading_angle = 0
        self._loading_timer = QTimer(self)
        self._loading_timer.setInterval(50)
        self._loading_timer.timeout.connect(self._update_loading)

        # Ripple 状态
        self._ripple_pos = QPointF(0, 0)
        self._ripple_radius = 0.0
        self._ripple_opacity = 0.0
        self._ripple_anim: Optional[QPropertyAnimation] = None

        # 屏蔽 Qt 原生焦点虚线框
        self.setStyleSheet(""" 
            QPushButton {
                border: none;
                background: transparent;
                outline: none;
            }
        """)
        self.setFlat(True)
        self.setAccessibleName(text.strip() if text and text.strip() else "button")

    # ============ Public 只读属性 ============
    @property
    def is_loading(self) -> bool:
        return self._is_loading

    # ============ ellipsis 文本省略开关 ============
    @Property(bool)
    def ellipsis(self) -> bool:
        return self._ellipsis

    @ellipsis.setter
    def ellipsis(self, val: bool):
        self._ellipsis = val
        self.update()

    # ============ 焦点环属性 Getter / Setter ============
    @Property(int)
    def focus_ring_width(self) -> int:
        return self._focus_ring_width

    @focus_ring_width.setter
    def focus_ring_width(self, val: int):
        self._focus_ring_width = max(1, val)
        self.update()

    @Property(str)
    def focus_color(self) -> str:
        if self._focus_color_str:
            return self._focus_color_str
        return theme_manager.get_color("focus")

    @focus_color.setter
    def focus_color(self, val: str):
        self._focus_color_str = val
        self.update()

    @Property(bool)
    def focus_ring_enabled(self) -> bool:
        return self._focus_ring_enabled

    @focus_ring_enabled.setter
    def focus_ring_enabled(self, val: bool):
        self._focus_ring_enabled = val
        if not val:
            self._show_focus_ring = False
        self.update()

    @Property(bool)
    def keep_focus_ring_on_click(self) -> bool:
        return self._keep_focus_ring_on_click

    @keep_focus_ring_on_click.setter
    def keep_focus_ring_on_click(self, val: bool):
        self._keep_focus_ring_on_click = val
        self.update()

    # 消除 PyCharm 静态检查波浪报错
    ellipsis: bool
    focus_ring_width: int
    focus_color: str
    focus_ring_enabled: bool
    keep_focus_ring_on_click: bool

    # ============ Ripple 动画 ============
    @Property(float)
    def ripple_radius(self) -> float:
        return self._ripple_radius

    @ripple_radius.setter
    def ripple_radius(self, r: float):
        self._ripple_radius = r
        max_r = max(1.0, self._max_ripple_radius())
        progress = r / max_r
        self._ripple_opacity = max(0.0, 1.0 - progress)
        self.update()

    def _max_ripple_radius(self) -> float:
        return max(1.0, math.hypot(self.width(), self.height()))

    def _start_ripple(self, pos: QPointF):
        if not self._ripple_enabled or self._is_loading:
            return
        # ✅ 修复 BUG-4：先停旧动画，避免并发叠加
        if self._ripple_anim is not None:
            self._ripple_anim.stop()
            self._ripple_anim = None

        self._ripple_pos = QPointF(pos)
        self._ripple_radius = 0.0

        anim = QPropertyAnimation(self, b"ripple_radius", self)
        anim.setDuration(400)
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.setStartValue(0.0)
        anim.setEndValue(self._max_ripple_radius())
        anim.finished.connect(self._on_ripple_finished)
        self._ripple_anim = anim
        anim.start()

    def _on_ripple_finished(self):
        if self._ripple_anim is not None:
            self._ripple_anim.deleteLater()
            self._ripple_anim = None

    # -------- 鼠标、焦点、键盘事件 --------
    @override
    def enterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    @override
    def leaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)

    @override
    def mousePressEvent(self, event):
        if self._is_loading:
            # ✅ 修复 BUG-7：loading 时直接拦截，不再依赖 setEnabled(False)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._keep_focus_ring_on_click:
                self._show_focus_ring = False
            self._start_ripple(event.position())
        super().mousePressEvent(event)

    @override
    def mouseReleaseEvent(self, event):
        if self._is_loading:
            event.accept()
            return
        super().mouseReleaseEvent(event)

    @override
    def keyPressEvent(self, event):
        if self._is_loading:
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._start_ripple(QPointF(self.width() / 2, self.height() / 2))
        super().keyPressEvent(event)

    @override
    def focusInEvent(self, event: QFocusEvent):
        if not self._focus_ring_enabled:
            self._show_focus_ring = False
        else:
            if event.reason() == Qt.FocusReason.TabFocusReason:
                self._show_focus_ring = True
            else:
                self._show_focus_ring = self._keep_focus_ring_on_click
        self.update()
        super().focusInEvent(event)

    @override
    def focusOutEvent(self, event: QFocusEvent):
        self._show_focus_ring = False
        self.update()
        super().focusOutEvent(event)

    # -------- Public API --------
    def set_loading(self, loading: bool, percentage: Optional[float] = None):
        """
        切换加载态。
        注意：v2.1 起不再内部调用 setEnabled(False)，避免覆盖用户已有的禁用状态；
              loading 期间通过 mousePressEvent / keyPressEvent 拦截交互。
        """
        self._is_loading = loading
        self._percentage = percentage
        if loading:
            self._loading_timer.start()
        else:
            self._loading_timer.stop()
        self.update()

    def set_percentage(self, value: Optional[float]):
        self._percentage = value
        self.update()

    def _update_loading(self):
        self._loading_angle = (self._loading_angle + 30) % 360
        self.update()

    # -------- SizeHint --------
    @override
    def sizeHint(self) -> QSize:
        if self._fab or self._fab_mini or self._shape == ButtonShape.ROUND:
            return QSize(self._size_val, self._size_val)

        fm = QFontMetrics(self.font())
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

    @override
    def minimumSizeHint(self) -> QSize:
        return QSize(self._size_val, self._size_val)

    # -------- Paint 核心 --------
    @override
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = QRectF(self.rect())
        radius = self._get_radius(rect)
        state = ButtonPaintState(
            hover=self._is_hovered,
            pressed=self.isDown() and not self._is_loading,
            focused=self.hasFocus(),
            disabled=not self.isEnabled() and not self._is_loading,
        )

        bg_color, fg_color, pen_color = self._resolve_colors(state)

        # 阴影
        if (not self._unelevated
                and self._variant not in (ButtonVariant.FLAT, ButtonVariant.OUTLINE, ButtonVariant.PUSH)
                and not state.disabled):
            self._draw_shadow(painter, rect, radius, state)

        # 背景 / 边框
        if self._variant == ButtonVariant.PUSH:
            self._draw_push_base(painter, rect, radius, bg_color, state)
        elif self._variant == ButtonVariant.FILLED:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._glossy_brush(rect, bg_color))
            painter.drawRoundedRect(rect, radius, radius)
        elif self._variant == ButtonVariant.OUTLINE:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(pen_color, 2))
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)
        elif self._variant == ButtonVariant.FLAT:
            if state.hover and not state.disabled:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(theme_manager.get_color("hover")))
                painter.drawRoundedRect(rect, radius, radius)

        # Ripple
        if (self._ripple_radius > 0 and self._ripple_opacity > 0
                and self._ripple_enabled and not state.disabled):
            self._draw_ripple(painter, rect, radius, fg_color)

        # Loading
        if self._is_loading:
            self._draw_loading_overlay(painter, rect, radius, fg_color)
            self._draw_focus_ring(painter, rect, radius, state)
            return

        self._draw_content(painter, rect, fg_color)
        self._draw_focus_ring(painter, rect, radius, state)

    def _resolve_colors(self, state: ButtonPaintState):
        """
        ✅ 修复 BUG-2 / BUG-10：
        - OUTLINE / FLAT 的前景使用 base 色本身（不是 contrast，否则浅色主题不可见）
        - OUTLINE / FLAT 的边框 hover 不再用主题 hover_tok（那几乎是透明的浅灰）
        - 只有 FILLED / PUSH 使用 contrast(base) 作为前景
        """
        base = QColor(self._bg_color)
        is_flat_or_outline = self._variant in (ButtonVariant.OUTLINE, ButtonVariant.FLAT)

        if is_flat_or_outline:
            if self._explicit_text_color:
                fg = QColor(self._explicit_text_color)
            else:
                fg = QColor(base)
            if state.disabled:
                fg.setAlpha(120)

            if self._variant == ButtonVariant.FLAT and state.hover and not state.disabled:
                bg = QColor(theme_manager.get_color("hover"))
            else:
                bg = QColor(0, 0, 0, 0)

            if state.disabled:
                pen = QColor(theme_manager.get_color("disabled"))
            elif state.pressed:
                pen = base.darker(130)
            elif state.hover:
                pen = base.lighter(115) if theme_manager.is_dark() else base.darker(115)
            else:
                pen = QColor(base)
            return bg, fg, pen

        # FILLED / PUSH
        if self._explicit_text_color:
            fg = QColor(self._explicit_text_color)
        else:
            fg = QColor(get_contrast_color(base.name()))
        if state.disabled:
            fg.setAlpha(120)

        if state.disabled:
            bg = QColor(theme_manager.get_color("disabled"))
        elif state.pressed:
            bg = QColor(theme_manager.get_color("pressed"))
        else:
            bg = QColor(base)

        return bg, fg, QColor(bg)

    def _get_radius(self, rect: QRectF) -> float:
        if self._shape == ButtonShape.ROUND or self._fab or self._fab_mini:
            return rect.height() / 2.0
        if self._shape in (ButtonShape.SQUARE, ButtonShape.RECTANGLE):
            return 0.0
        return 4.0

    # -------- 阴影 / Push --------
    @staticmethod
    def _draw_shadow(painter: QPainter, rect: QRectF, radius: float, state: ButtonPaintState):
        # ✅ 修复 BUG-3：全部使用逻辑像素，不再 /dpr
        dark = theme_manager.is_dark()
        if dark:
            base_alpha = 80 if (state.hover and not state.pressed) else (40 if state.pressed else 60)
        else:
            base_alpha = 50 if (state.hover and not state.pressed) else (20 if state.pressed else 30)
        offset = 4 if (state.hover and not state.pressed) else (1 if state.pressed else 2)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, base_alpha))
        painter.drawRoundedRect(rect.translated(0, offset), radius, radius)

    def _draw_push_base(self, painter: QPainter, rect: QRectF, radius: float,
                        c_bg: QColor, state: ButtonPaintState):
        is_down = state.pressed
        is_disabled = state.disabled
        base = c_bg.darker(140) if not is_disabled else QColor(0, 0, 0, 50)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(base)
        painter.drawRoundedRect(rect.translated(0, 3), radius, radius)
        top_rect = rect.translated(0, 1) if is_down else rect
        painter.setBrush(self._glossy_brush(top_rect, c_bg))
        painter.drawRoundedRect(top_rect, radius, radius)

    def _glossy_brush(self, rect: QRectF, base: QColor) -> QBrush:
        if not self._glossy:
            return QBrush(base)
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        grad.setColorAt(0.0, QColor(
            min(255, base.red() + 40),
            min(255, base.green() + 40),
            min(255, base.blue() + 40),
        ))
        grad.setColorAt(0.5, base)
        grad.setColorAt(1.0, base.darker(110))
        return QBrush(grad)

    # -------- Ripple --------
    def _draw_ripple(self, painter: QPainter, rect: QRectF, radius: float, fg_color: QColor):
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.setClipPath(path)

        ripple_color = QColor(fg_color)
        ripple_color.setAlphaF(self._ripple_opacity * 0.28)
        painter.setBrush(ripple_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self._ripple_pos, self._ripple_radius, self._ripple_radius)
        painter.restore()

    # -------- Loading --------
    def _draw_loading_overlay(self, painter: QPainter, rect: QRectF, radius: float, c_text: QColor):
        # ✅ 修复 BUG-3：进度条与环全部使用逻辑像素，环笔宽用 setWidthF
        if self._percentage is not None:
            pct = max(0.0, min(100.0, self._percentage))
            bar_h = 3.0
            bar_rect = QRectF(rect.left(), rect.bottom() - bar_h,
                              rect.width() * (pct / 100.0), bar_h)

            path = QPainterPath()
            path.addRoundedRect(rect, radius, radius)
            painter.save()
            painter.setClipPath(path)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c_text)
            painter.drawRect(bar_rect)
            painter.restore()

        pen = QPen(c_text)
        pen.setWidthF(3.0)  # ✅ 用 setWidthF，避免 int(3/dpr) 变 0
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(rect.adjusted(10, 10, -10, -10),
                        self._loading_angle * 16, 120 * 16)

    # -------- 内容绘制 --------
    def _draw_content(self, painter: QPainter, rect: QRectF, c_text: QColor):
        # ✅ 修复 BUG-8：把 padding 语义落到 contentRect 上，让绘制与 sizeHint 一致
        content = rect
        if self._custom_padding:
            pad_v, pad_h = self._custom_padding
            candidate = rect.adjusted(pad_h, pad_v, -pad_h, -pad_v)
            if candidate.width() > 0 and candidate.height() > 0:
                content = candidate

        painter.setPen(c_text)
        font = self.font()
        font.setBold(True)
        # 平滑的像素字号梯度（不再抖动）
        if self._size_val <= 24:
            font.setPixelSize(11)
        elif self._size_val <= 32:
            font.setPixelSize(13)
        elif self._size_val <= 40:
            font.setPixelSize(15)
        else:
            font.setPixelSize(17)
        painter.setFont(font)

        raw_text = self._text_with_caps()
        fm = QFontMetrics(font)
        icon_sz = self._icon_px()
        pad_inner = 6.0

        left_icon = self._icon_left if (self._icon_left and not self._icon_left.isNull()) else None
        right_icon = self._icon_right if (self._icon_right and not self._icon_right.isNull()) else None

        # ✅ 修复 BUG-6：stack 与非 stack 用不同的 elide 可用宽度
        if self._stack:
            avail_text_w = max(0.0, content.width() - pad_inner * 2)
        else:
            avail_text_w = content.width()
            if left_icon:
                avail_text_w -= icon_sz + pad_inner
            if right_icon:
                avail_text_w -= icon_sz + pad_inner
            avail_text_w = max(0.0, avail_text_w)

        if self._ellipsis:
            display_text = fm.elidedText(raw_text, Qt.TextElideMode.ElideRight, int(avail_text_w))
        else:
            display_text = raw_text
        text_w = fm.horizontalAdvance(display_text) if display_text else 0

        # ---- Stack 模式：三支独立分支 ----
        if self._stack:
            self._draw_stack_content(painter, content, fm, display_text, text_w,
                                     left_icon, icon_sz, pad_inner)
            return

        # ---- 横排模式 ----
        total_w = 0.0
        if left_icon:
            total_w += icon_sz
        if right_icon:
            total_w += icon_sz
        if text_w > 0 and total_w > 0:
            total_w += pad_inner
        total_w += text_w

        start_x = content.left() + (content.width() - total_w) / 2.0
        center_y = content.top() + content.height() / 2.0

        if left_icon:
            pix = left_icon.pixmap(QSize(icon_sz, icon_sz))
            # ✅ 修复 BUG-9：显式 QRectF 目标尺寸，源用 pix.rect()
            painter.drawPixmap(
                QRectF(start_x, center_y - icon_sz / 2.0, icon_sz, icon_sz),
                pix, QRectF(pix.rect()),
            )
            start_x += icon_sz + pad_inner

        if text_w > 0:
            painter.drawText(
                QRectF(start_x, content.top(), text_w, content.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                display_text,
            )
            start_x += text_w + pad_inner

        if right_icon:
            pix = right_icon.pixmap(QSize(icon_sz, icon_sz))
            painter.drawPixmap(
                QRectF(start_x, center_y - icon_sz / 2.0, icon_sz, icon_sz),
                pix, QRectF(pix.rect()),
            )

    @staticmethod
    def _draw_stack_content(painter: QPainter, content: QRectF, fm: QFontMetrics,
                            display_text: str, text_w: int,
                            left_icon: Optional[QIcon], icon_sz: int, pad_inner: float):
        """✅ 修复 BUG-5：stack 模式三支独立处理，垂直居中都以实际行高计算。"""
        cx = content.left() + content.width() / 2.0
        cy = content.top() + content.height() / 2.0

        if left_icon and text_w > 0:
            # 图标上 + 文字下
            text_h = fm.height()
            gap = 4.0
            total_h = icon_sz + gap + text_h
            start_y = cy - total_h / 2.0

            pix = left_icon.pixmap(QSize(icon_sz, icon_sz))
            painter.drawPixmap(
                QRectF(cx - icon_sz / 2.0, start_y, icon_sz, icon_sz),
                pix, QRectF(pix.rect()),
            )
            start_y += icon_sz + gap
            painter.drawText(
                QRectF(content.left(), start_y, content.width(), text_h),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                display_text,
            )
        elif left_icon:
            # 仅图标：真正居中
            pix = left_icon.pixmap(QSize(icon_sz, icon_sz))
            painter.drawPixmap(
                QRectF(cx - icon_sz / 2.0, cy - icon_sz / 2.0, icon_sz, icon_sz),
                pix, QRectF(pix.rect()),
            )
        elif text_w > 0:
            # 仅文字：真正居中
            painter.drawText(content, Qt.AlignmentFlag.AlignCenter, display_text)

    # -------- 焦点环 --------
    def _draw_focus_ring(self, painter: QPainter, rect: QRectF, radius: float, state: ButtonPaintState):
        """
        ✅ 修复 BUG-1：
        - 原实现向 rect 外扩，会被 QPainter 默认 clip 裁剪
        - 改为向内 inset：inset = pen_width/2 + 1，确保完整绘制在 widget 内部
        - 直接读取私有 _focus_color_str，避免 @Property 递归
        """
        if not (self._show_focus_ring and self._focus_ring_enabled
                and state.focused and not state.disabled):
            return

        painter.save()
        if self._focus_color_str:
            focus_color = QColor(self._focus_color_str)
        else:
            focus_color = QColor(theme_manager.get_color("focus"))
        focus_color.setAlpha(180)

        pen_width = float(max(1, self._focus_ring_width))
        pen = QPen(focus_color, pen_width, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        inset = pen_width / 2.0 + 1.0
        inner_rect = rect.adjusted(inset, inset, -inset, -inset)
        inner_radius = max(0.0, radius - inset)
        painter.drawRoundedRect(inner_rect, inner_radius, inner_radius)
        painter.restore()

    # -------- 工具函数 --------
    def _icon_px(self) -> int:
        # 更平滑的图标像素梯度
        if self._size_val <= 20:
            return 12
        if self._size_val <= 24:
            return 14
        if self._size_val <= 32:
            return 18
        if self._size_val <= 40:
            return 20
        return 24

    def _text_with_caps(self) -> str:
        t = self.text()
        return t if self._no_caps else t.upper()

    @staticmethod
    def _coerce_icon(icon: Optional[Union[str, QIcon]]) -> Optional[QIcon]:
        if icon is None:
            return None
        if isinstance(icon, str):
            return QIcon(icon)
        return icon

    @staticmethod
    def _parse_padding(padding: str) -> tuple[int, int]:
        """返回 (pad_v, pad_h)。"""
        parts = padding.strip().lower().split()

        def _one(p: str) -> int:
            if p in _SIZE_MAP:
                return _SIZE_MAP[p] // 2
            m = re.match(r"(\d+)(px)?", p)
            return int(m.group(1)) if m else 8

        if len(parts) == 1:
            v = h = _one(parts[0])
            return v, h
        return _one(parts[0]), _one(parts[-1])
