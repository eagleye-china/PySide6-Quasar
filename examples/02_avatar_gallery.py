# examples/02_avatar_gallery.py
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QIcon
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from pyside_quasar import (
    Avatar, AvatarGroup, AvatarShape, AvatarSize,
    Button, ButtonVariant, Color,
    theme_manager, ThemeMode,
)

try:
    from resources import resources_rc  # noqa
except ImportError:
    print("[WARN] 未找到 resources_rc，图标可能无法显示。")


def create_demo_pixmap(color1="#4A90E2", color2="#50E3C2", size=200) -> QPixmap:
    """生成一张用于演示的渐变图片"""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 绘制对角线渐变
    from PySide6.QtGui import QLinearGradient
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor(color1))
    gradient.setColorAt(1, QColor(color2))
    p.fillRect(0, 0, size, size, gradient)

    # 绘制一个简单的用户剪影
    p.setBrush(QColor(255, 255, 255, 200))
    p.setPen(Qt.PenStyle.NoPen)
    # 头部
    p.drawEllipse(int(size * 0.35), int(size * 0.25), int(size * 0.3), int(size * 0.3))
    # 身体
    p.drawEllipse(int(size * 0.15), int(size * 0.6), int(size * 0.7), int(size * 0.5))

    p.end()
    return pix


class DemoCard(QFrame):
    """主题感知的卡片容器"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("DemoCard")
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("CardTitle")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.title_lbl)

        # 内容容器
        self.content = QWidget()
        self._layout.addWidget(self.content)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 16, 20, 20)
        self.content_layout.setSpacing(16)

        theme_manager.themeChanged.connect(self._on_theme_changed)
        self._update_theme()

    def _update_theme(self):
        surface = theme_manager.get_color("surface")
        border = theme_manager.get_color("border")
        text_sec = theme_manager.get_color("text_secondary")

        self.setStyleSheet(f"""
            QFrame#DemoCard {{
                background-color: {surface};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QLabel#CardTitle {{
                color: {text_sec};
                font-size: 13px;
                font-weight: bold;
                padding: 12px 20px;
                border-bottom: 1px solid {border};
                background: transparent;
            }}
        """)

    def _on_theme_changed(self):
        self._update_theme()


class DemoAvatar(QWidget):
    """Avatar 企业级演示"""

    def __init__(self):
        super().__init__()
        self.resize(1000, 800)
        self.setWindowTitle("pyside-quasar · Avatar Gallery")

        self._demo_pixmap = create_demo_pixmap()

        theme_manager.themeChanged.connect(self._on_theme_changed)
        self._update_window_bg()

        main_layout = QVBoxLayout(self)  # type: ignore[arg-type]
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(20)

        # 顶部标题栏
        top_bar = QHBoxLayout()
        self.title = QLabel("Avatar 组件演示")
        top_bar.addWidget(self.title)
        top_bar.addStretch()

        btn_toggle = Button("切换主题", color=Color.PRIMARY, variant=ButtonVariant.OUTLINE)
        btn_toggle.clicked.connect(theme_manager.toggle)
        top_bar.addWidget(btn_toggle)
        main_layout.addLayout(top_bar)

        # Section 1: 尺寸与形状
        card1 = DemoCard("1. 尺寸与形状（Size & Shape）")
        row1 = QHBoxLayout()
        row1.setSpacing(30)

        for size_enum in [AvatarSize.XS, AvatarSize.SM, AvatarSize.MD, AvatarSize.LG, AvatarSize.XL]:
            row1.addWidget(self._wrap_with_caption(
                Avatar(text="张", size=size_enum, color=Color.PRIMARY),
                f"{size_enum.name} ({size_enum.value}px)"
            ))

        row1.addStretch()
        row1.addWidget(self._wrap_with_caption(
            Avatar(text="A", shape=AvatarShape.ROUND, size=AvatarSize.XL, color=Color.SECONDARY),
            "ROUND"
        ))
        row1.addWidget(self._wrap_with_caption(
            Avatar(text="B", shape=AvatarShape.SQUARE, size=AvatarSize.XL, color=Color.WARNING),
            "SQUARE"
        ))
        row1.addWidget(self._wrap_with_caption(
            Avatar(text="C", shape=AvatarShape.ROUNDED, size=AvatarSize.XL, color=Color.ACCENT),
            "ROUNDED"
        ))
        row1.addStretch()

        card1.content_layout.addLayout(row1)
        main_layout.addWidget(card1)

        # Section 2: 内容类型
        card2 = DemoCard("2. 内容类型（图片 / 文字 / 图标）")
        row2 = QHBoxLayout()
        row2.setSpacing(30)

        row2.addWidget(self._wrap_with_caption(
            Avatar(image=":/icons/set-up.svg", size=AvatarSize.XL),
            # Avatar(image=self._demo_pixmap, size=AvatarSize.XL),
            "图片头像"
        ))
        row2.addWidget(self._wrap_with_caption(
            Avatar(text="李四", size=AvatarSize.XL, color=Color.INFO),
            "文字头像"
        ))
        row2.addWidget(self._wrap_with_caption(
            Avatar(text="Wang", size=AvatarSize.XL, color=Color.POSITIVE),
            "自动截断 (前2字)"
        ))

        # 用色块模拟图标
        row2.addStretch()
        card2.content_layout.addLayout(row2)
        main_layout.addWidget(card2)

        # Section 3: 状态指示器
        card3 = DemoCard("3. 状态指示器（Status Indicator）")
        row3 = QHBoxLayout()
        row3.setSpacing(30)

        row3.addWidget(self._wrap_with_caption(
            Avatar(text="A", size=AvatarSize.LG, color=Color.PRIMARY, status_color=Color.POSITIVE),
            "在线 (POSITIVE)"
        ))
        row3.addWidget(self._wrap_with_caption(
            Avatar(text="B", size=AvatarSize.LG, color=Color.SECONDARY, status_color=Color.NEGATIVE),
            "忙碌 (NEGATIVE)"
        ))
        row3.addWidget(self._wrap_with_caption(
            Avatar(text="C", size=AvatarSize.LG, color=Color.WARNING, status_color=Color.GREY),
            "离线 (GREY)"
        ))
        row3.addWidget(self._wrap_with_caption(
            Avatar(image=self._demo_pixmap, size=AvatarSize.LG, status_color=Color.POSITIVE),
            "图片 + 状态"
        ))
        row3.addStretch()

        card3.content_layout.addLayout(row3)
        main_layout.addWidget(card3)

        # Section 4: 边框
        card4 = DemoCard("4. 边框样式（Border）")
        row4 = QHBoxLayout()
        row4.setSpacing(30)

        row4.addWidget(self._wrap_with_caption(
            Avatar(text="1", size=AvatarSize.LG, color=Color.PRIMARY),
            "无边框"
        ))
        row4.addWidget(self._wrap_with_caption(
            Avatar(text="2", size=AvatarSize.LG, color=Color.SECONDARY, border_width=2),
            "2px 默认边框"
        ))
        row4.addWidget(self._wrap_with_caption(
            Avatar(
                text="3", size=AvatarSize.LG, color=Color.WARNING,
                border_width=3, border_color=Color.PRIMARY
            ),
            "3px 主色边框"
        ))
        row4.addWidget(self._wrap_with_caption(
            Avatar(
                text="4", size=AvatarSize.LG, color=Color.NEGATIVE,
                border_width=4, border_color=Color.POSITIVE
            ),
            "4px 品牌边框"
        ))
        row4.addStretch()

        card4.content_layout.addLayout(row4)
        main_layout.addWidget(card4)

        # Section 5: AvatarGroup
        card5 = DemoCard("5. 头像组（AvatarGroup）")
        row5 = QHBoxLayout()
        row5.setSpacing(60)

        # 组 1: 标准头像组
        group1 = AvatarGroup(size=AvatarSize.LG)
        for text, color in [
            ("张", Color.PRIMARY),
            ("李", Color.SECONDARY),
            ("王", Color.WARNING),
            ("赵", Color.POSITIVE),
        ]:
            group1.add_avatar(Avatar(text=text, size=AvatarSize.LG, color=color))
        row5.addWidget(self._wrap_with_caption(group1, "标准头像组 (4人)"))

        # 组 2: 溢出显示
        group2 = AvatarGroup(max_count=4, size=AvatarSize.LG)
        names = ["孙", "周", "吴", "郑", "冯", "陈", "褚", "卫"]
        colors = [Color.PRIMARY, Color.SECONDARY, Color.WARNING, Color.POSITIVE,
                  Color.INFO, Color.ACCENT, Color.NEGATIVE, Color.GREY]
        for name, c in zip(names, colors):
            group2.add_avatar(Avatar(text=name, size=AvatarSize.LG, color=c))
        row5.addWidget(self._wrap_with_caption(group2, "溢出模式 (+5 提示)"))

        # 组 3: 不同重叠率
        group3 = AvatarGroup(overlap=0.4, size=AvatarSize.MD)
        for text, color in [("A", Color.PRIMARY), ("B", Color.WARNING), ("C", Color.NEGATIVE)]:
            group3.add_avatar(Avatar(text=text, size=AvatarSize.MD, color=color))
        row5.addWidget(self._wrap_with_caption(group3, "40% 重叠"))

        row5.addStretch()

        card5.content_layout.addLayout(row5)
        main_layout.addWidget(card5)

        main_layout.addStretch()

    @staticmethod
    def _wrap_with_caption(widget: QWidget, caption: str) -> QWidget:
        """辅助：把组件包裹在带标题的容器里"""
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(caption)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color: {theme_manager.get_color('text_secondary')}; font-size: 12px; background: transparent;")
        theme_manager.themeChanged.connect(
            lambda _, l=lbl: l.setStyleSheet(
                f"color: {theme_manager.get_color('text_secondary')}; font-size: 12px; background: transparent;"
            )
        )
        layout.addWidget(lbl)

        return wrapper

    def _update_window_bg(self):
        self.setStyleSheet(f"background-color: {theme_manager.get_color('background')};")

    def _on_theme_changed(self):
        self._update_window_bg()
        self.title.setStyleSheet(
            f"color: {theme_manager.get_color('text_primary')}; font-size: 22px; font-weight: bold;"
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/icons/set-up.svg"))

    # 初始化主题（默认深色）
    from pyside_quasar import theme_manager as tm

    tm.set_mode(ThemeMode.DARK)

    window = DemoAvatar()

    window.show()
    sys.exit(app.exec())
