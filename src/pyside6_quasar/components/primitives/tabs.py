# quasar/components/tabs.py
from enum import Enum
from typing import Optional, Union, List

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property,
    QRectF, QPointF, QSize, Signal
)
from PySide6.QtGui import (
    QPainter, QColor, QFont, QIcon, QFontMetrics, QPen
)
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSizePolicy
)

from ...core.theme import theme_manager, Color
from ...core.base import QBaseWidget, QuasarWidgetMixin


class TabsAlign(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class TabsIndicatorPosition(Enum):
    BOTTOM = "bottom"
    TOP = "top"
    LEFT = "left"
    RIGHT = "right"


# ★ 核心修复 1：继承链加入 QWidget 和 ThemedWidget
class TabItem(QWidget, ThemedWidget):
    """
    企业级单选项卡控件 (对标 Quasar Tab)
    支持图标、标签、警告红点、气泡徽标及紧凑模式，完美适配主题。
    """
    clicked = Signal(str)

    def __init__(
            self,
            name: str,
            label: str = "",
            icon: Optional[Union[str, QIcon]] = None,
            alert: Union[bool, str] = False,
            alert_icon: Optional[Union[str, QIcon]] = None,
            color: str = Color.PRIMARY,
            dense: bool = False,
            inline_label: bool = False,
            parent=None,
    ):
        super().__init__(parent)
        # ★ 挂载主题监听
        self.setup_theme()

        self._name = name
        self._label = label
        self._color = QColor(color)
        self._alert = alert
        self._alert_icon = alert_icon
        self._dense = dense
        self._inline_label = inline_label
        self._is_active = False
        self._is_hovered = False
        self._show_focus_ring = False  # 焦点环状态

        # 图标解析
        self._icon = QIcon(icon) if isinstance(icon, str) else icon

        # 尺寸与策略计算
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._compute_size()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(label or name)

    @property
    def name(self) -> str:
        return self._name

    def set_active(self, active: bool):
        if self._is_active != active:
            self._is_active = active
            self.update()

    def _compute_size(self):
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self._label) if self._label else 0
        icon_sz = 16 if self._dense else 20
        icon_w = icon_sz if (self._icon and not self._icon.isNull()) else 0
        spacing = 6 if (icon_w > 0 and text_w > 0 and self._inline_label) else 0

        # 气泡预留空间
        alert_w = 0
        if self._alert:
            if isinstance(self._alert, str) and self._alert:
                alert_font = QFont("Arial", 8, QFont.Weight.Bold)
                alert_fm = QFontMetrics(alert_font)
                alert_w = max(16, alert_fm.horizontalAdvance(self._alert) + 8) + 4
            else:
                alert_w = 6 + 4

        base_w = 32 if not self._dense else 20
        total_w = text_w + icon_w + spacing + alert_w + base_w

        if not self._label and not self._alert and icon_w > 0:
            total_w = max(total_w, 40)

        self.setMinimumSize(total_w, 40 if not self._dense else 32)

    def enterEvent(self, event):
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._show_focus_ring = False
            self.clicked.emit(self._name)
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.clicked.emit(self._name)
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # 1. 悬停背景 (使用主题 hover token)
        if self._is_hovered and not self._is_active:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme_manager.get_color("hover")))
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(4, 4, -4, -4), 6, 6)

        # 2. 字体与颜色
        if self._is_active:
            text_color = self._color
            font = QFont("Arial")
            font.setBold(True)
        else:
            # 未选中时使用次级文字色，焦点态使用主文字色
            if self.hasFocus():
                text_color = QColor(theme_manager.get_color("text_primary"))
            else:
                text_color = QColor(theme_manager.get_color("text_secondary"))
            font = QFont("Arial")

        font.setPixelSize(13 if not self._dense else 11)
        painter.setFont(font)
        fm = painter.fontMetrics()

        # 3. 重新计算居中内容块
        text_w = fm.horizontalAdvance(self._label) if self._label else 0
        icon_sz = 16 if self._dense else 20
        icon_w = icon_sz if (self._icon and not self._icon.isNull()) else 0
        spacing = 6 if (icon_w > 0 and text_w > 0 and self._inline_label) else 0

        alert_w = 0
        if self._alert:
            if isinstance(self._alert, str) and self._alert:
                alert_font = QFont("Arial", 8, QFont.Weight.Bold)
                alert_fm = QFontMetrics(alert_font)
                alert_w = max(16, alert_fm.horizontalAdvance(self._alert) + 8) + 6
            else:
                alert_w = 6 + 6

        total_content_w = icon_w + spacing + text_w + alert_w
        start_x = (self.width() - total_content_w) / 2
        start_y = (self.height() - icon_sz) / 2 if icon_w > 0 else 0

        # 4. 绘制图标
        if icon_w > 0:
            pix = self._icon.pixmap(QSize(icon_sz, icon_sz))
            painter.drawPixmap(int(start_x), int(start_y), pix)
            start_x += icon_w + spacing

        # 5. 绘制标签文字
        if text_w > 0:
            painter.setPen(text_color)
            text_y = (self.height() - fm.height()) / 2
            painter.drawText(QPointF(start_x, text_y + fm.ascent()), self._label)
            start_x += text_w

        # 6. 绘制警告红点 / 徽标
        if self._alert:
            self._draw_alert(painter, start_x + 6, (self.height() - 14) / 2)

        # 7. 绘制键盘焦点环
        if self._show_focus_ring and self.hasFocus():
            painter.save()
            ring_color = QColor(theme_manager.get_color("text_primary"))
            ring_color.setAlpha(100)
            pen = QPen(ring_color, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(2, 2, -2, -2), 6, 6)
            painter.restore()

    def _draw_alert(self, painter, x, y):
        """绘制警告气泡或红点"""
        painter.setPen(Qt.PenStyle.NoPen)
        if isinstance(self._alert, str) and self._alert:
            # 气泡模式
            painter.setBrush(QColor(Color.NEGATIVE))
            alert_font = QFont("Arial", 8, QFont.Weight.Bold)
            fm = QFontMetrics(alert_font)
            w = max(16, fm.horizontalAdvance(self._alert) + 8)
            r = QRectF(x, y, w, 14)
            painter.drawRoundedRect(r, 7, 7)

            painter.setPen(QColor("#ffffff"))
            painter.setFont(alert_font)
            painter.drawText(r, Qt.AlignmentFlag.AlignCenter, self._alert)
        else:
            # 纯红点模式
            painter.setBrush(QColor(Color.NEGATIVE))
            painter.drawEllipse(QPointF(x + 3, y + 7), 3, 3)


# ★ 核心修复 2：继承链加入 QWidget 和 ThemedWidget
class Tabs(QWidget, ThemedWidget):
    """
    企业级 Tabs 容器 (对标 Quasar Tabs)
    """
    tabChanged = Signal(str)

    def __init__(
            self,
            tabs: Optional[List[TabItem]] = None,
            color: str = Color.PRIMARY,
            vertical: bool = False,
            dense: bool = False,
            stretch: bool = False,
            align: TabsAlign = TabsAlign.LEFT,
            indicator_color: Optional[str] = None,
            indicator_position: TabsIndicatorPosition = TabsIndicatorPosition.BOTTOM,
            narrow_indicator: bool = False,
            no_caps: bool = False,
            animation_duration: int = 250,
            parent=None,
    ):
        super().__init__(parent)
        # ★ 挂载主题监听
        self.setup_theme()

        self._color = QColor(color)
        self._indicator_color = QColor(indicator_color) if indicator_color else self._color
        self._vertical = vertical
        self._dense = dense
        self._stretch = stretch
        self._align = align
        self._indicator_position = indicator_position
        self._narrow_indicator = narrow_indicator
        self._animation_duration = animation_duration

        # 布局配置
        if vertical:
            self._layout = QVBoxLayout(self)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        else:
            self._layout = QHBoxLayout(self)
            self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._tabs: List[TabItem] = []
        self._active_name: Optional[str] = None

        # 指示器动画
        self._indicator_rect = QRectF(0, 0, 0, 0)
        self._indicator_target = QRectF(0, 0, 0, 0)
        self._indicator_anim = QPropertyAnimation(self, b"indicator_geometry")
        self._indicator_anim.setDuration(animation_duration)
        self._indicator_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 注册标签
        if tabs:
            for t in tabs:
                self.add_tab(t)

        self._apply_alignment_spacers()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Tabs")

    def _apply_alignment_spacers(self):
        if self._stretch:
            return

        if self._align == TabsAlign.LEFT:
            self._layout.addStretch(1)
        elif self._align == TabsAlign.RIGHT:
            self._layout.insertStretch(0, 1)
        elif self._align == TabsAlign.CENTER:
            self._layout.insertStretch(0, 1)
            self._layout.addStretch(1)

    # ================= 动画属性 =================
    @Property(QRectF)
    def indicator_geometry(self) -> QRectF:
        return self._indicator_rect

    @indicator_geometry.setter
    def indicator_geometry(self, rect: QRectF):
        self._indicator_rect = rect
        self.update()

    # ================= 公共 API =================
    def add_tab(self, tab: TabItem):
        self._tabs.append(tab)
        tab.clicked.connect(self.set_active_tab)

        insert_idx = self._layout.count()
        if self._align in (TabsAlign.CENTER, TabsAlign.RIGHT) and not self._stretch:
            insert_idx = 1 if self._align == TabsAlign.CENTER else 0

        self._layout.insertWidget(insert_idx, tab)

        if self._stretch:
            self._layout.setStretchFactor(tab, 1)

        if self._active_name is None:
            self.set_active_tab(tab.name, animate=False)

    def set_active_tab(self, name: str, animate: bool = True):
        target_tab = None
        for t in self._tabs:
            if t.name == name:
                t.set_active(True)
                target_tab = t
            else:
                t.set_active(False)

        if not target_tab or self._active_name == name:
            if target_tab and self._active_name is None:
                self._active_name = name
                self._update_indicator(animate=False)
            return

        self._active_name = name
        self._update_indicator(animate=animate)
        self.tabChanged.emit(name)

    def _update_indicator(self, animate: bool = True):
        target_tab = next((t for t in self._tabs if t.name == self._active_name), None)
        if not target_tab:
            return

        tab_pos = target_tab.pos()
        target_rect = QRectF(tab_pos.x(), tab_pos.y(), target_tab.width(), target_tab.height())

        if self._vertical:
            thickness = 3 if not self._dense else 2
            margin_y = 8
            if self._indicator_position == TabsIndicatorPosition.RIGHT:
                self._indicator_target = QRectF(
                    self.width() - thickness, target_rect.top() + margin_y,
                    thickness, target_rect.height() - margin_y * 2
                )
            else:
                self._indicator_target = QRectF(
                    0, target_rect.top() + margin_y,
                    thickness, target_rect.height() - margin_y * 2
                )
        else:
            thickness = 3 if not self._dense else 2
            tab_w = target_rect.width()
            tab_x = target_rect.x()

            if self._narrow_indicator:
                w = tab_w * 0.4
                x = tab_x + (tab_w - w) / 2
            else:
                w = tab_w
                x = tab_x

            if self._indicator_position == TabsIndicatorPosition.TOP:
                self._indicator_target = QRectF(x, 0, w, thickness)
            else:
                self._indicator_target = QRectF(x, self.height() - thickness, w, thickness)

        if animate and self._indicator_rect.width() > 0.0 and self._indicator_rect.height() > 0:
            self._indicator_anim.stop()
            self._indicator_anim.setStartValue(self._indicator_rect)
            self._indicator_anim.setEndValue(self._indicator_target)
            self._indicator_anim.start()
        else:
            self._indicator_rect = self._indicator_target
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_indicator(animate=False)

    # ================= 键盘无障碍导航 =================
    def keyPressEvent(self, event):
        if not self._tabs:
            return

        curr_idx = next((i for i, t in enumerate(self._tabs) if t.name == self._active_name), 0)

        if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            next_idx = (curr_idx + 1) % len(self._tabs)
            self._tabs[next_idx].setFocus()
            self.set_active_tab(self._tabs[next_idx].name)
        elif event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            prev_idx = (curr_idx - 1 + len(self._tabs)) % len(self._tabs)
            self._tabs[prev_idx].setFocus()
            self.set_active_tab(self._tabs[prev_idx].name)
        elif event.key() == Qt.Key.Key_Home:
            self._tabs[0].setFocus()
            self.set_active_tab(self._tabs[0].name)
        elif event.key() == Qt.Key.Key_End:
            self._tabs[-1].setFocus()
            self.set_active_tab(self._tabs[-1].name)
        else:
            super().keyPressEvent(event)

    # ================= 绘制 =================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制滑动指示器
        if self._indicator_rect.width() > 0 and self._indicator_rect.height() > 0:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self._indicator_color)

            radius = min(self._indicator_rect.width(), self._indicator_rect.height()) / 2.0
            painter.drawRoundedRect(self._indicator_rect, radius, radius)
