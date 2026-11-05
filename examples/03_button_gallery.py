# examples/03_button_gallery.py
import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QLayout
)

from pyside_quasar import (
    Button,
    ButtonVariant,
    ButtonShape,
    ButtonSize,
    Color,
    theme_manager,
    ThemeMode,
)

try:
    from resources import resources_rc  # noqa
except ImportError:
    print("[WARN] 未找到 resources_rc，图标可能无法显示。")


class DemoCard(QFrame):
    """主题感知卡片容器，自适应窗口大小"""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("DemoCard")
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("CardTitle")
        self.title_lbl.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(120)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addWidget(self.title_lbl)

        self.content = QWidget()
        self.content.setObjectName("CardContent")
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._layout.addWidget(self.content)

        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 16, 20, 20)
        self.content_layout.setSpacing(16)

        theme_manager.themeChanged.connect(self._update_theme)
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
                font-family: "Microsoft YaHei", sans-serif;
                font-size: 13px;
                font-weight: bold;
                padding: 12px 20px;
                border-bottom: 1px solid {border};
                background: transparent;
            }}
        """)


class DemoButtonGallery(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 920)
        self.setWindowTitle("PySide6‑Quasar · Button Gallery (焦点环 / Ellipsis / 高DPI 验证版)")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        theme_manager.themeChanged.connect(self._on_theme_changed)
        self._update_window_bg()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(20)
        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)

        # 顶部标题栏 + 测试提示
        top_bar = QHBoxLayout()
        self.title = QLabel("Button 按钮组件演示")
        self.title.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        top_bar.addWidget(self.title)

        tip_label = QLabel("💡 测试提示：按 Tab 切换键盘焦点，观察焦点环；缩放窗口/高DPI屏幕验证清晰度")
        tip_label.setFont(QFont("Microsoft YaHei", 9))
        top_bar.addWidget(tip_label)

        top_bar.addStretch()

        btn_toggle = Button(
            "切换主题",
            color=Color.PRIMARY,
            variant=ButtonVariant.OUTLINE
        )
        btn_toggle.clicked.connect(theme_manager.toggle)
        top_bar.addWidget(btn_toggle)
        main_layout.addLayout(top_bar)

        # 1. 【重点验证】焦点环 Focus Ring 专项测试
        card_focus = DemoCard("【专项1】焦点环 FocusRing 测试（Tab切换焦点）")
        row_focus = QHBoxLayout()
        row_focus.setSpacing(24)
        row_focus.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 默认：仅Tab焦点才显示焦点环，点击不保留
        btn_focus_default = Button("默认焦点规则", color=Color.PRIMARY)
        # 点击后也保留焦点环
        btn_focus_keep = Button("点击保持焦点环", color=Color.POSITIVE, keep_focus_ring_on_click=True)
        # 自定义焦点颜色 + 粗细
        btn_focus_custom = Button("自定义焦点(红，3px)", color=Color.NEGATIVE, focus_color="#FF2222", focus_ring_width=3)
        # 关闭焦点环
        btn_focus_off = Button("关闭焦点环", color=Color.WARNING, focus_ring_enabled=False)
        # OUTLINE变体焦点环
        btn_focus_outline = Button("Outline变体焦点", variant=ButtonVariant.OUTLINE, color=Color.INFO, focus_color="#00DDFF")

        row_focus.addWidget(self._wrap_with_caption(btn_focus_default, "默认：仅Tab获得焦点显示"))
        row_focus.addWidget(self._wrap_with_caption(btn_focus_keep, "keep_focus_ring_on_click=True"))
        row_focus.addWidget(self._wrap_with_caption(btn_focus_custom, "自定义颜色+宽度"))
        row_focus.addWidget(self._wrap_with_caption(btn_focus_off, "focus_ring_enabled=False"))
        row_focus.addWidget(self._wrap_with_caption(btn_focus_outline, "Outline变体焦点"))
        row_focus.addStretch(1)
        card_focus.content_layout.addLayout(row_focus)
        main_layout.addWidget(card_focus)

        # 2. 【重点验证】Ellipsis 文本省略专项测试
        # 2. 【重点验证】Ellipsis 文本省略专项测试
        card_ellipsis = DemoCard("【专项2】Ellipsis 文本省略测试（ellipsis=True / False）")
        row_ellipsis = QHBoxLayout()
        row_ellipsis.setSpacing(24)
        row_ellipsis.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        long_text = "这是一段很长很长的测试文本，用来验证文本自动省略效果"
        btn_ellipsis_on = Button(long_text, variant=ButtonVariant.FILLED, color=Color.PRIMARY, ellipsis=True)
        btn_ellipsis_off = Button(long_text, variant=ButtonVariant.FILLED, color=Color.PRIMARY, ellipsis=False)
        btn_ellipsis_small = Button(long_text, variant=ButtonVariant.FLAT, color=Color.SECONDARY, ellipsis=True,
                                    size=ButtonSize.SM)

        # ========== 新增：限制最大宽度，防止最大化后被拉宽，ellipsis稳定复现 ==========
        ellipsis_test_max_w = 220
        btn_ellipsis_on.setMaximumWidth(ellipsis_test_max_w)
        btn_ellipsis_off.setMaximumWidth(ellipsis_test_max_w)
        btn_ellipsis_small.setMaximumWidth(ellipsis_test_max_w)

        row_ellipsis.addWidget(self._wrap_with_caption(btn_ellipsis_on, "ellipsis=True 自动省略"))
        row_ellipsis.addWidget(self._wrap_with_caption(btn_ellipsis_off, "ellipsis=False 不省略，文字溢出"))
        row_ellipsis.addWidget(self._wrap_with_caption(btn_ellipsis_small, "小号按钮长文本省略"))
        row_ellipsis.addStretch(1)
        card_ellipsis.content_layout.addLayout(row_ellipsis)
        main_layout.addWidget(card_ellipsis)

        # 3. Size 尺寸 XS / SM / MD / LG / XL（高DPI验证）
        card1 = DemoCard("3. 按钮尺寸 Size (XS / SM / MD / LG / XL) — 高DPI验证")
        row1 = QHBoxLayout()
        row1.setSpacing(24)
        row1.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for size_enum in [ButtonSize.XS, ButtonSize.SM, ButtonSize.MD, ButtonSize.LG, ButtonSize.XL]:
            b = Button(
                size_enum.name,
                size=size_enum,
                variant=ButtonVariant.FILLED,
                color=Color.PRIMARY
            )
            row1.addWidget(self._wrap_with_caption(b, f"{size_enum.name}({size_enum.value}px)"))
        row1.addStretch(1)
        card1.content_layout.addLayout(row1)
        main_layout.addWidget(card1)

        # 4. Variant 变体 FILLED / OUTLINE / FLAT / PUSH
        card2 = DemoCard("4. 按钮变体 Variant (FILLED / OUTLINE / FLAT / PUSH)")
        row2 = QHBoxLayout()
        row2.setSpacing(24)
        row2.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for var_enum in [ButtonVariant.FILLED, ButtonVariant.OUTLINE, ButtonVariant.FLAT, ButtonVariant.PUSH]:
            b = Button(
                var_enum.name,
                variant=var_enum,
                color=Color.PRIMARY
            )
            row2.addWidget(self._wrap_with_caption(b, var_enum.name))
        row2.addStretch(1)
        card2.content_layout.addLayout(row2)
        main_layout.addWidget(card2)

        # 5. 主题色彩 Color
        card3 = DemoCard("5. 主题色彩 Color")
        row3 = QHBoxLayout()
        row3.setSpacing(24)
        row3.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        color_items = [
            (Color.PRIMARY, "PRIMARY"),
            (Color.SECONDARY, "SECONDARY"),
            (Color.POSITIVE, "POSITIVE"),
            (Color.WARNING, "WARNING"),
            (Color.NEGATIVE, "NEGATIVE"),
            (Color.INFO, "INFO"),
        ]
        for color_val, label in color_items:
            b = Button(
                label,
                variant=ButtonVariant.FILLED,
                color=color_val
            )
            row3.addWidget(self._wrap_with_caption(b, label))
        row3.addStretch(1)
        card3.content_layout.addLayout(row3)
        main_layout.addWidget(card3)

        # 6. Shape 形状 RECTANGLE / ROUNDED / ROUND / SQUARE
        card4 = DemoCard("6. 按钮形状 Shape")
        row4 = QHBoxLayout()
        row4.setSpacing(24)
        row4.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for shape_enum in [ButtonShape.RECTANGLE, ButtonShape.ROUNDED, ButtonShape.ROUND, ButtonShape.SQUARE]:
            b = Button(
                shape_enum.name,
                variant=ButtonVariant.FILLED,
                color=Color.PRIMARY,
                shape=shape_enum,
                size=ButtonSize.LG
            )
            row4.addWidget(self._wrap_with_caption(b, shape_enum.name))
        row4.addStretch(1)
        card4.content_layout.addLayout(row4)
        main_layout.addWidget(card4)

        # 7. Normal / Disabled 状态
        card5 = DemoCard("7. 交互状态 Normal / Disabled")
        row5 = QHBoxLayout()
        row5.setSpacing(24)
        row5.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        btn_normal = Button("正常", variant=ButtonVariant.FILLED, color=Color.PRIMARY)
        btn_disabled = Button("禁用", variant=ButtonVariant.FILLED, color=Color.PRIMARY)
        btn_disabled.setDisabled(True)
        row5.addWidget(self._wrap_with_caption(btn_normal, "Normal"))
        row5.addWidget(self._wrap_with_caption(btn_disabled, "Disabled"))
        row5.addStretch(1)
        card5.content_layout.addLayout(row5)
        main_layout.addWidget(card5)

        # 8. 图标：icon(左), icon_right(右), 仅图标
        card6 = DemoCard("8. 图标按钮：前置图标 / 后置图标 / 纯图标")
        row6 = QHBoxLayout()
        row6.setSpacing(24)
        row6.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        btn_icon_left = Button(
            "确认",
            icon=":/icons/check.svg",
            variant=ButtonVariant.FILLED,
            color=Color.POSITIVE
        )
        btn_icon_right = Button(
            "下一步",
            icon_right=":/icons/arrow-right.svg",
            variant=ButtonVariant.OUTLINE,
            color=Color.PRIMARY
        )
        btn_icon_only = Button(
            "",
            icon=":/icons/heart.svg",
            variant=ButtonVariant.FILLED,
            color=Color.NEGATIVE,
            shape=ButtonShape.ROUND,
            size=ButtonSize.LG
        )
        row6.addWidget(self._wrap_with_caption(btn_icon_left, "icon前置"))
        row6.addWidget(self._wrap_with_caption(btn_icon_right, "icon_right后置"))
        row6.addWidget(self._wrap_with_caption(btn_icon_only, "纯图标圆形"))
        row6.addStretch(1)
        card6.content_layout.addLayout(row6)
        main_layout.addWidget(card6)

        # 9. Loading加载状态演示（含百分比进度条）
        card8 = DemoCard("9. Loading加载状态（点击切换，支持百分比进度）")
        row8 = QHBoxLayout()
        row8.setSpacing(24)
        row8.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.btn_loading_demo = Button(
            "点击进入Loading",
            variant=ButtonVariant.FILLED,
            color=Color.INFO
        )
        self.btn_loading_pct = Button(
            "带进度Loading",
            variant=ButtonVariant.FILLED,
            color=Color.POSITIVE
        )
        self._loading_toggle_flag = False
        self._loading_pct_flag = False

        def toggle_loading():
            self._loading_toggle_flag = not self._loading_toggle_flag
            self.btn_loading_demo.set_loading(self._loading_toggle_flag)
            if self._loading_toggle_flag:
                self.btn_loading_demo.setText("加载中…")
            else:
                self.btn_loading_demo.setText("点击进入Loading")

        def toggle_loading_pct():
            self._loading_pct_flag = not self._loading_pct_flag
            if self._loading_pct_flag:
                self.btn_loading_pct.set_loading(True, percentage=65.0)
                self.btn_loading_pct.setText("65%")
            else:
                self.btn_loading_pct.set_loading(False)
                self.btn_loading_pct.setText("带进度Loading")

        self.btn_loading_demo.clicked.connect(toggle_loading)
        self.btn_loading_pct.clicked.connect(toggle_loading_pct)
        row8.addWidget(self._wrap_with_caption(self.btn_loading_demo, "旋转Loading"))
        row8.addWidget(self._wrap_with_caption(self.btn_loading_pct, "带进度条Loading"))
        row8.addStretch(1)
        card8.content_layout.addLayout(row8)
        main_layout.addWidget(card8)

        # 10. FAB / FAB‑MINI
        card9 = DemoCard("10. FAB悬浮按钮 (fab / fab_mini)")
        row9 = QHBoxLayout()
        row9.setSpacing(24)
        row9.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        fab_normal = Button(icon=":/icons/plus.svg", fab=True, color=Color.PRIMARY)
        fab_mini = Button(icon=":/icons/plus.svg", fab_mini=True, color=Color.SECONDARY)
        row9.addWidget(self._wrap_with_caption(fab_normal, "fab=True"))
        row9.addWidget(self._wrap_with_caption(fab_mini, "fab_mini=True"))
        row9.addStretch(1)
        card9.content_layout.addLayout(row9)
        main_layout.addWidget(card9)

        main_layout.addStretch(1)

    @staticmethod
    def _wrap_with_caption(widget: QWidget, caption: str) -> QWidget:
        wrapper = QWidget()
        wrapper.setStyleSheet("background: transparent;")
        wrapper.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)

        lbl = QLabel(caption)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Microsoft YaHei", 9))
        lbl.setObjectName("CaptionLabel")
        layout.addWidget(lbl)
        return wrapper

    def _update_window_bg(self):
        bg = theme_manager.get_color('background')
        text_pri = theme_manager.get_color('text_primary')
        text_sec = theme_manager.get_color('text_secondary')
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg};
                font-family: "Microsoft YaHei", sans-serif;
            }}
            QLabel {{
                color: {text_pri};
            }}
            QLabel#CaptionLabel {{
                color: {text_sec};
                font-size: 12px;
            }}
        """)

    def _on_theme_changed(self):
        self._update_window_bg()
        self.title.setStyleSheet("")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/icons/check.svg"))

    from pyside_quasar import theme_manager as tm
    tm.set_mode(ThemeMode.DARK)

    win = DemoButtonGallery()
    win.show()
    sys.exit(app.exec())
