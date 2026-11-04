# quasar/components/card.py
from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy,
    QGraphicsDropShadowEffect
)

# 使用相对导入，彻底解决循环引用问题
from ...core.theme import theme_manager, ThemeMode
from ...core.theme.palette import Color
from ...core.base import QBaseWidget, QuasarWidgetMixin


# ★ 核心修复 1：所有组件继承链加入 QWidget，并把 ThemedWidget 作为 Mixin 放在后面
class CardMedia(QWidget, ThemedWidget):
    """媒体组件：Cover 模式图片绘制"""

    def __init__(self, pixmap: QPixmap, parent=None):
        # ★ 核心修复 2：调用 QWidget 初始化，并手动挂载主题监听
        super().__init__(parent)
        self.setup_theme()

        self._pixmap = pixmap
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(100)
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        if self._pixmap.isNull() or self.width() <= 0 or self.height() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()
        src_w, src_h = self._pixmap.width(), self._pixmap.height()
        scale = max(rect.width() / src_w, rect.height() / src_h)
        new_w, new_h = src_w * scale, src_h * scale
        draw_x = (rect.width() - new_w) / 2
        draw_y = (rect.height() - new_h) / 2
        painter.drawPixmap(int(draw_x), int(draw_y), int(new_w), int(new_h), self._pixmap)


class CardSection(QWidget, ThemedWidget):
    """卡片内容区"""

    def __init__(self, horizontal: bool = False, padding: int = 16, parent=None):
        super().__init__(parent)
        self.setup_theme()

        self._layout = QHBoxLayout(self) if horizontal else QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(8)
        self.setStyleSheet("background: transparent;")

    def add_widget(self, widget: QWidget):
        if not isinstance(widget, (QPushButton,)):
            widget.setStyleSheet("background: transparent;")
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)


class CardActions(QWidget, ThemedWidget):
    """卡片操作区"""

    def __init__(self, align: str = "right", vertical: bool = False, parent=None):
        super().__init__(parent)
        self.setup_theme()

        self._align = align
        self._vertical = vertical
        self._layout = QVBoxLayout(self) if vertical else QHBoxLayout(self)
        self._layout.setContentsMargins(16, 8, 16, 16)
        self._layout.setSpacing(8)
        self.setStyleSheet("background: transparent;")
        self._actions = []

    def add_action(self, widget: QWidget):
        widget.setStyleSheet("background: transparent;")
        self._actions.append(widget)
        self._rebuild()

    def _rebuild(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.spacerItem():
                del item

        if not self._actions:
            return

        if self._align in ("right", "center", "evenly", "around"):
            self._layout.addStretch()

        for i, act in enumerate(self._actions):
            self._layout.addWidget(act)
            if self._align in ("between", "evenly") and i < len(self._actions) - 1:
                self._layout.addStretch()

        if self._align in ("left", "center", "evenly", "around"):
            self._layout.addStretch()


class Card(QWidget, ThemedWidget):
    """
    终极封板卡片容器
    支持整卡点击、悬停阴影浮现、以及完美的主题联动。
    """
    closed = Signal()
    clicked = Signal()

    def __init__(
            self,
            flat: bool = False,
            square: bool = False,
            bordered: bool = True,
            horizontal: bool = False,
            closable: bool = False,
            clickable: bool = False,
            bg_color: str | None = None,
            border_color: str | None = None,
            hover_border_color: str = Color.PRIMARY,
            parent=None,
    ):
        super().__init__(parent)
        self.setup_theme()

        self._flat = flat
        self._square = square
        self._bordered = bordered
        self._horizontal = horizontal
        self._clickable = clickable
        self._hovered = False

        self._custom_bg = bg_color
        self._custom_border = border_color
        self._hover_border_color = QColor(hover_border_color)
        self._radius = 0 if square else 8

        self._update_theme_colors()
        self._setup_shadow()

        if self._clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 根布局
        self._main_layout = QHBoxLayout(self) if horizontal else QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # 关闭按钮
        self._btn_close = None
        if closable:
            self._btn_close = QPushButton("✕", self)
            self._btn_close.setFixedSize(24, 24)
            self._btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_close.clicked.connect(self._on_close_clicked)
            self._update_close_btn_style()

    def _setup_shadow(self):
        """设置底层的 DropShadowEffect"""
        if self._flat:
            return
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(15)
        self._shadow.setOffset(0, 4)
        self.setGraphicsEffect(self._shadow)
        self._update_shadow_color()

    def _update_shadow_color(self):
        """根据主题和悬停状态更新阴影"""
        if self._flat or not hasattr(self, '_shadow'):
            return

        # 暗色模式需要更深的阴影，亮色模式需要极淡的阴影
        if theme_manager.is_dark():
            base_color = QColor(0, 0, 0, 120 if self._hovered else 60)
        else:
            base_color = QColor(0, 0, 0, 40 if self._hovered else 15)

        self._shadow.setColor(base_color)

    def _update_theme_colors(self):
        if self._custom_bg:
            self._bg_color = QColor(self._custom_bg)
        else:
            self._bg_color = QColor(theme_manager.get_color("surface"))

        if self._custom_border:
            self._border_color = QColor(self._custom_border)
        elif self._bordered:
            self._border_color = QColor(theme_manager.get_color("border"))
        else:
            self._border_color = QColor(Qt.GlobalColor.transparent)

        self._current_border_color = QColor(self._border_color)

    def _update_close_btn_style(self):
        if not self._btn_close:
            return
        text_color = theme_manager.get_color("text_primary")
        bg_color = "rgba(0,0,0,0.5)" if theme_manager.is_dark() else "rgba(0,0,0,0.1)"

        self._btn_close.setStyleSheet(f"""
            QPushButton {{ 
                background: {bg_color}; 
                color: {text_color}; 
                border: none; 
                border-radius: 12px; 
                font-weight: bold;
            }}
            QPushButton:hover {{ 
                background: #ef5350; 
                color: white;
            }}
        """)

    def _on_theme_changed(self, mode: ThemeMode):
        self._update_theme_colors()
        self._update_close_btn_style()
        self._update_shadow_color()
        super()._on_theme_changed(mode)

    def add_section(self, section: CardSection):
        self._main_layout.addWidget(section)

    def add_media(self, media: CardMedia):
        self._main_layout.addWidget(media)

    def add_actions(self, actions: CardActions):
        self._main_layout.addWidget(actions)

    def _on_close_clicked(self):
        self.closed.emit()
        self.hide()

    def mousePressEvent(self, event):
        """整卡点击事件"""
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._btn_close:
            self._btn_close.move(self.width() - 32, 8)

    def enterEvent(self, event):
        self._hovered = True
        if self._bordered:
            self._current_border_color = self._hover_border_color
        self._update_shadow_color()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if self._bordered:
            self._current_border_color = self._border_color
        self._update_shadow_color()
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)

        painter.fillPath(path, self._bg_color)
        painter.setClipPath(path)

        if self._bordered:
            pen = QPen(self._current_border_color)
            pen.setWidthF(1.5)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
