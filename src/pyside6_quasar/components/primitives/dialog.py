# quasar/components/dialog.py
from enum import Enum
from typing import Optional

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QRectF, QPoint
)
from PySide6.QtGui import (
    QPainter, QColor, QPainterPath, QPen, QKeyEvent, QShowEvent
)
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QGraphicsDropShadowEffect, QApplication
)

# ★ 引入主题管理器和基类
from ...core.theme import theme_manager, ThemeMode
from ...core.theme.palette import Color
from ...core.base import QBaseWidget, QuasarWidgetMixin


class DialogPosition(Enum):
    STANDARD = 1  # 居中
    TOP = 2
    BOTTOM = 3
    LEFT = 4
    RIGHT = 5


# ★ 核心修复 1：继承 QDialog 和 ThemedWidget
class Dialog(QDialog, ThemedWidget):
    """
    终极封板模态对话框 (对标 Quasar QDialog)
    支持：Persistent / NoEscDismiss / NoBackdropDismiss / Seamless，
    尺寸定制（Maximized / FullWidth / FullHeight），位置控制，
    以及无障碍焦点管理与完美主题自适应。
    """

    def __init__(
            self,
            title: str = "提示",
            parent=None,
            # --- 行为 ---
            persistent: bool = False,
            no_esc_dismiss: bool = False,
            no_backdrop_dismiss: bool = False,
            auto_close: bool = False,
            seamless: bool = False,
            # --- 尺寸与位置 ---
            maximized: bool = False,
            full_width: bool = False,
            full_height: bool = False,
            position: DialogPosition = DialogPosition.STANDARD,
            square: bool = False,
            min_width: int = 400,
            max_width: int = 600,
            # --- 视觉 ---
            bg_color: Optional[str] = None,  # 如果为 None，跟随主题 surface
            radius: int = 8,
            # --- 动画 ---
            transition_duration: int = 250,
    ):
        super().__init__(parent)
        # ★ 核心修复 2：挂载主题监听
        self.setup_theme()

        # 1. 无边框、模态、背景透明
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Dialog
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        # 行为配置
        self._persistent = persistent
        self._no_esc_dismiss = no_esc_dismiss or persistent
        self._no_backdrop_dismiss = no_backdrop_dismiss or persistent
        self._auto_close = auto_close
        self._seamless = seamless

        # 尺寸与位置
        self._maximized = maximized
        self._full_width = full_width
        self._full_height = full_height
        self._position = position
        self._square = square
        self._min_width = min_width
        self._max_width = max_width

        # 视觉
        self._custom_bg = bg_color
        self._bg_color = QColor()
        self._radius = 0 if square else radius

        # 动画
        self._scale = 0.8
        self._mask_opacity = 0.0
        self._transition_duration = transition_duration

        self._scale_anim = QPropertyAnimation(self, b"scale")
        self._scale_anim.setDuration(transition_duration)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self._mask_anim = QPropertyAnimation(self, b"mask_opacity")
        self._mask_anim.setDuration(int(transition_duration * 0.8))

        # 焦点管理
        self._previous_focus_widget = None
        self._shadow = None

        self._setup_ui(title)
        self._apply_size_and_position()

        # 初始化颜色
        self._update_theme_colors()

    # ================= 动画属性 =================
    @property
    def scale(self) -> float:
        return self._scale

    @scale.setter
    def scale(self, v: float):
        self._scale = v
        self.update()

    @property
    def mask_opacity(self) -> float:
        return self._mask_opacity

    @mask_opacity.setter
    def mask_opacity(self, v: float):
        self._mask_opacity = v
        self.update()

    # ================= UI 构建 =================
    def _setup_ui(self, title: str):
        # 外层布局：承载阴影边距
        self._outer_layout = QVBoxLayout(self)
        shadow_margin = 0 if self._maximized else 20
        self._outer_layout.setContentsMargins(
            shadow_margin, shadow_margin, shadow_margin, shadow_margin
        )
        self._outer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 中心卡片容器
        self._content_widget = QWidget()
        self._content_widget.setObjectName("DialogCard")
        self._content_widget.setMinimumWidth(self._min_width)
        self._content_widget.setMaximumWidth(self._max_width)

        # 阴影（Maximized 时不添加）
        if not self._maximized:
            self._shadow = QGraphicsDropShadowEffect(self._content_widget)
            self._shadow.setBlurRadius(30)
            self._shadow.setOffset(0, 6)
            self._content_widget.setGraphicsEffect(self._shadow)

        card_layout = QVBoxLayout(self._content_widget)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(16)

        # 标题栏
        header_layout = QHBoxLayout()
        self._title_lbl = QLabel(title)
        header_layout.addWidget(self._title_lbl)
        header_layout.addStretch()

        # 关闭按钮
        if not self._persistent:
            self._btn_close = QPushButton("✕")
            self._btn_close.setFixedSize(24, 24)
            self._btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_close.clicked.connect(self.reject)
            header_layout.addWidget(self._btn_close)
        else:
            self._btn_close = None

        card_layout.addLayout(header_layout)

        # 内容区插槽
        self._body_layout = QVBoxLayout()
        card_layout.addLayout(self._body_layout)

        # 操作按钮区插槽
        self._actions_layout = QHBoxLayout()
        self._actions_layout.setContentsMargins(0, 8, 0, 0)
        self._actions_layout.addStretch()
        card_layout.addLayout(self._actions_layout)

        self._outer_layout.addWidget(self._content_widget)

    def _apply_size_and_position(self):
        """根据配置应用尺寸与位置。"""
        if self._maximized:
            self._full_width = True
            self._full_height = True

        if self._full_width or self._full_height:
            parent = self.parentWidget()
            if parent:
                geo = parent.geometry()
            else:
                geo = QApplication.primaryScreen().availableGeometry()

            if self._full_width:
                self._content_widget.setFixedWidth(geo.width() - 40)
            if self._full_height:
                self._content_widget.setMinimumHeight(geo.height() - 40)

        align_map = {
            DialogPosition.STANDARD: Qt.AlignmentFlag.AlignCenter,
            DialogPosition.TOP: Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            DialogPosition.BOTTOM: Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
            DialogPosition.LEFT: Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            DialogPosition.RIGHT: Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
        }
        self._outer_layout.setAlignment(
            align_map.get(self._position, Qt.AlignmentFlag.AlignCenter)
        )

    # ================= 主题颜色更新 =================
    def _update_theme_colors(self):
        """根据当前主题动态拉取颜色"""
        if self._custom_bg:
            self._bg_color = QColor(self._custom_bg)
        else:
            self._bg_color = QColor(theme_manager.get_color("surface"))

        # 更新中心卡片的背景色
        self._content_widget.setStyleSheet(f"""
            QWidget#DialogCard {{
                background-color: {self._bg_color.name()};
                border-radius: {self._radius}px;
            }}
        """)

        # 更新标题颜色
        self._title_lbl.setStyleSheet(
            f"color: {theme_manager.get_color('text_primary')}; "
            "font-size: 16px; font-weight: bold; background: transparent;"
        )

        # 更新关闭按钮样式
        if self._btn_close:
            close_color = theme_manager.get_color("text_secondary")
            self._btn_close.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {close_color}; border: none; font-weight: bold; }}
                QPushButton:hover {{ color: {Color.NEGATIVE}; }}
            """)

        # 更新阴影颜色（亮色模式下阴影要淡，否则像黑眼圈）
        if self._shadow:
            if theme_manager.is_dark():
                self._shadow.setColor(QColor(0, 0, 0, 160))
            else:
                self._shadow.setColor(QColor(0, 0, 0, 40))

    def _on_theme_changed(self, mode: ThemeMode):
        self._update_theme_colors()
        super()._on_theme_changed(mode)

    # ================= 公共 API =================
    def add_widget(self, widget: QWidget):
        # 移除硬编码颜色，让业务层的控件（如我们重构过的 Label）自己处理颜色
        widget.setStyleSheet("background: transparent;")
        self._body_layout.addWidget(widget)

    def add_action(self, widget: QWidget):
        self._actions_layout.addWidget(widget)

    def set_title(self, title: str):
        self._title_lbl.setText(title)

    # ================= 生命周期与事件 =================
    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        self._previous_focus_widget = QApplication.focusWidget()

        self._mask_anim.stop()
        self._mask_anim.setStartValue(0.0)
        self._mask_anim.setEndValue(1.0)
        self._mask_anim.start()

        self._scale_anim.stop()
        self._scale_anim.setStartValue(0.8)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._previous_focus_widget:
            self._previous_focus_widget.setFocus()
        self._previous_focus_widget = None

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            if not self._no_esc_dismiss:
                self.reject()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        # ★ 修复 1：统一转为整数 QPoint，消除类型警告
        pos: QPoint = event.position().toPoint()
        child = self.childAt(pos)

        # ★ 修复 2：修正判断逻辑
        if child is None or (child is self and self._is_outside_card(pos)):
            if self._no_backdrop_dismiss:
                return
            self.reject()
            return

        if self._auto_close:
            self.accept()

    def _is_outside_card(self, pos: QPoint) -> bool:
        """判断坐标是否在卡片外部。"""
        # geometry() 获取的已经是相对于 self 的矩形，直接比对即可
        card_rect = self._content_widget.geometry()
        return not card_rect.contains(pos)

    # ================= 核心绘制 =================
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 绘制半透明遮罩
        if not self._seamless:
            # 亮色模式下遮罩稍微淡一点（120），深色模式用 150
            mask_alpha = 150 if theme_manager.is_dark() else 120
            painter.fillRect(
                self.rect(),
                QColor(0, 0, 0, int(mask_alpha * self._mask_opacity))
            )

        # 2. 缩放绘制
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)

        # 3. 绘制边框
        if not self._maximized:
            card_geo = self._content_widget.geometry()
            path = QPainterPath()
            path.addRoundedRect(QRectF(card_geo), self._radius, self._radius)

            # ★ 核心修复 3：边框颜色跟随主题
            border_color = QColor(theme_manager.get_color("border"))
            border_color.setAlphaF(0.5)  # 稍微透明一点，显得轻盈
            painter.setPen(QPen(border_color, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
