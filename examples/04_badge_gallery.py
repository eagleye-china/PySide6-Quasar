# examples/04_badge_gallery.py
"""
pyside-quasar Badge Gallery 演示页面
对标 Button Gallery 风格，用于 Badge 封板验收
测试项：浮动/内联、圆点、胶囊/矩形、轮廓、透明、对齐、数字上限、多行、主题切换
"""
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSpacerItem, QSizePolicy, QCheckBox
)

from pyside_quasar.components.primitives.badge import Badge, BadgeAlign
from pyside_quasar.components.primitives.button import Button, ButtonVariant, ButtonSize
from pyside_quasar.core.base import Color, theme_manager, ThemeMode


class DemoCard(QFrame):
    """和Button Gallery保持一致的卡片容器"""
    def __init__(self, title: str):
        super().__init__()
        self.setStyleSheet("""
            DemoCard {
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                background-color: #ffffff;
            }
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)

        title_label = QLabel(f"<b>{title}</b>")
        layout.addWidget(title_label)
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(24)
        self.content_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addLayout(self.content_layout)

    def add_stretch(self):
        self.content_layout.addStretch(1)


class BadgeGalleryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyside-quasar - Badge 徽标组件 (封板验收版)")
        self.resize(1100, 720)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # 头部
        header_layout = QHBoxLayout()
        title = QLabel("<h2>Badge 徽标组件演示</h2>")
        tip = QLabel('<span style="color:#666">测试提示：切换主题、缩放窗口，验证位置跟随、高DPI、自动对比度</span>')
        self.btn_theme = Button("切换主题", variant=ButtonVariant.OUTLINE, size=ButtonSize.SM)
        self.btn_theme.clicked.connect(self._toggle_theme)
        header_layout.addWidget(title)
        header_layout.addWidget(tip)
        header_layout.addStretch(1)
        header_layout.addWidget(self.btn_theme)
        main_layout.addLayout(header_layout)

        # 1. 浮动模式（默认右上角红点徽标）
        card_float = DemoCard("【专项1】浮动模式 Floating（右上角挂载）")
        btn_float_1 = Button("消息", variant=ButtonVariant.FILLED, color=Color.PRIMARY)
        Badge(target_widget=btn_float_1, content=6, color=Color.NEGATIVE)

        btn_float_2 = Button("通知", variant=ButtonVariant.FILLED, color=Color.PRIMARY)
        Badge(target_widget=btn_float_2, content=120, max_value=99, color=Color.NEGATIVE)

        btn_float_dot = Button("圆点", variant=ButtonVariant.FILLED, color=Color.PRIMARY)
        Badge(target_widget=btn_float_dot, is_dot=True, color=Color.NEGATIVE)

        card_float.content_layout.addWidget(self._wrap_caption(btn_float_1, "数字 6"))
        card_float.content_layout.addWidget(self._wrap_caption(btn_float_2, "99+ 上限截断"))
        card_float.content_layout.addWidget(self._wrap_caption(btn_float_dot, "圆点Dot"))
        card_float.add_stretch()
        main_layout.addWidget(card_float)

        # 2. 内联模式 + 三种垂直对齐
        card_inline = DemoCard("【专项2】内联模式 Inline（TOP / MIDDLE / BOTTOM）")
        btn_in_top = Button("TOP", variant=ButtonVariant.FILLED, color=Color.SECONDARY)
        Badge(target_widget=btn_in_top, content="T", floating=False, align=BadgeAlign.TOP, color=Color.POSITIVE)

        btn_in_mid = Button("MIDDLE", variant=ButtonVariant.FILLED, color=Color.SECONDARY)
        Badge(target_widget=btn_in_mid, content="M", floating=False, align=BadgeAlign.MIDDLE, color=Color.POSITIVE)

        btn_in_bot = Button("BOTTOM", variant=ButtonVariant.FILLED, color=Color.SECONDARY)
        Badge(target_widget=btn_in_bot, content="B", floating=False, align=BadgeAlign.BOTTOM, color=Color.POSITIVE)

        card_inline.content_layout.addWidget(self._wrap_caption(btn_in_top, "对齐 TOP"))
        card_inline.content_layout.addWidget(self._wrap_caption(btn_in_mid, "对齐 MIDDLE"))
        card_inline.content_layout.addWidget(self._wrap_caption(btn_in_bot, "对齐 BOTTOM"))
        card_inline.add_stretch()
        main_layout.addWidget(card_inline)

        # 3. 形态：矩形 / 胶囊 rounded
        card_shape = DemoCard("【专项3】形态：矩形 / 胶囊 rounded")
        btn_rect = Button("矩形", variant=ButtonVariant.FILLED, color=Color.WARNING)
        Badge(target_widget=btn_rect, content="R", rounded=False, color=Color.WARNING)

        btn_pill = Button("胶囊", variant=ButtonVariant.FILLED, color=Color.WARNING)
        Badge(target_widget=btn_pill, content="P", rounded=True, color=Color.WARNING)

        card_shape.content_layout.addWidget(self._wrap_caption(btn_rect, "rounded=False 矩形"))
        card_shape.content_layout.addWidget(self._wrap_caption(btn_pill, "rounded=True 胶囊"))
        card_shape.add_stretch()
        main_layout.addWidget(card_shape)

        # 4. Outline 轮廓模式
        card_outline = DemoCard("【专项4】Outline 轮廓模式（无填充，描边）")
        btn_out1 = Button("OUTLINE", variant=ButtonVariant.OUTLINE, color=Color.PRIMARY)
        Badge(target_widget=btn_out1, content=8, outline=True, color=Color.PRIMARY)

        btn_out_dot = Button("轮廓圆点", variant=ButtonVariant.OUTLINE, color=Color.PRIMARY)
        Badge(target_widget=btn_out_dot, is_dot=True, outline=True, color=Color.PRIMARY)

        card_outline.content_layout.addWidget(self._wrap_caption(btn_out1, "数字轮廓徽标"))
        card_outline.content_layout.addWidget(self._wrap_caption(btn_out_dot, "轮廓圆点"))
        card_outline.add_stretch()
        main_layout.addWidget(card_outline)

        # 5. Transparent 半透明模式
        card_trans = DemoCard("【专项5】Transparent 半透明背景")
        btn_t1 = Button("半透明", variant=ButtonVariant.FILLED, color=Color.NEGATIVE)
        Badge(target_widget=btn_t1, content=9, transparent=True, color=Color.NEGATIVE)

        card_trans.content_layout.addWidget(self._wrap_caption(btn_t1, "alpha=0.8"))
        card_trans.add_stretch()
        main_layout.addWidget(card_trans)

        # 6. 多行文本 multi_line
        card_multi = DemoCard("【专项6】MultiLine 多行文本徽标")
        btn_m = Button("多行", variant=ButtonVariant.FLAT, color=Color.INFO)
        Badge(target_widget=btn_m, content="新消息\n3条", multi_line=True, color=Color.INFO)

        card_multi.content_layout.addWidget(self._wrap_caption(btn_m, "自动换行"))
        card_multi.add_stretch()
        main_layout.addWidget(card_multi)

        # 7. 主题色全套
        card_color = DemoCard("【专项7】主题色彩 Color 全套")
        color_list = [
            (Color.PRIMARY, "PRIMARY"),
            (Color.SECONDARY, "SECONDARY"),
            (Color.POSITIVE, "POSITIVE"),
            (Color.WARNING, "WARNING"),
            (Color.NEGATIVE, "NEGATIVE"),
            (Color.INFO, "INFO"),
        ]
        for c, name in color_list:
            b = Button(name, variant=ButtonVariant.FILLED, color=c)
            Badge(target_widget=b, content=5, color=c)
            card_color.content_layout.addWidget(self._wrap_caption(b, name))
        card_color.add_stretch()
        main_layout.addWidget(card_color)

        # 8. 动态API测试：实时更新内容
        card_api = DemoCard("【专项8】动态API测试 set_content / detach")
        self.btn_api = Button("可更新徽标", variant=ButtonVariant.FILLED, color=Color.PRIMARY)
        self.badge_dynamic = Badge(target_widget=self.btn_api, content=1, color=Color.NEGATIVE)

        btn_add = Button("+1", variant=ButtonVariant.FILLED, color=Color.POSITIVE, size=ButtonSize.SM)
        btn_add.clicked.connect(self._badge_inc)
        btn_clear = Button("清空", variant=ButtonVariant.FILLED, color=Color.NEGATIVE, size=ButtonSize.SM)
        btn_clear.clicked.connect(self._badge_clear)
        btn_detach = Button("解绑Detach", variant=ButtonVariant.OUTLINE, size=ButtonSize.SM)
        btn_detach.clicked.connect(self._badge_detach)

        card_api.content_layout.addWidget(self._wrap_caption(self.btn_api, "动态badge"))
        card_api.content_layout.addWidget(btn_add)
        card_api.content_layout.addWidget(btn_clear)
        card_api.content_layout.addWidget(btn_detach)
        card_api.add_stretch()
        main_layout.addWidget(card_api)

        # 底部占位
        main_layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def _wrap_caption(self, widget, caption_text: str):
        """和Button Gallery统一的底部小字说明容器"""
        wrap = QVBoxLayout()
        wrap.setSpacing(4)
        wrap.setAlignment(Qt.AlignCenter)
        wrap.addWidget(widget)
        cap = QLabel(f'<span style="color:#666;font-size:12px">{caption_text}</span>')
        cap.setAlignment(Qt.AlignCenter)
        wrap.addWidget(cap)
        container = QWidget()
        container.setLayout(wrap)
        return container

    def _toggle_theme(self):
        """明暗主题切换"""
        if theme_manager.mode == ThemeMode.LIGHT:
            theme_manager.set_mode(ThemeMode.DARK)
        else:
            theme_manager.set_mode(ThemeMode.LIGHT)

    def _badge_inc(self):
        if self.badge_dynamic._target is None:
            return
        old = self.badge_dynamic._content
        if isinstance(old, int):
            self.badge_dynamic.set_content(old + 1)

    def _badge_clear(self):
        if self.badge_dynamic._target is None:
            return
        self.badge_dynamic.set_content(0)

    def _badge_detach(self):
        self.badge_dynamic.detach()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BadgeGalleryWindow()
    w.show()
    sys.exit(app.exec())
