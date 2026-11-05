# examples/checkbox_gallery.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame
)
from PySide6.QtCore import Qt

from pyside_quasar import Checkbox, CheckboxSize
from pyside_quasar.core.theme import theme_manager, ThemeMode


class CheckboxGallery(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyside-quasar - Checkbox Gallery")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # 标题行
        title_row = QHBoxLayout()
        title = QLabel("<h2>Checkbox 组件演示</h2>")
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.btn_theme = QPushButton("切换主题")
        self.btn_theme.clicked.connect(self._toggle_theme)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.btn_theme)
        main_layout.addLayout(title_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(14)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # 1. 尺寸 Size
        section1_frame, section1_layout = self._make_section("1. 尺寸 (Size)")
        lay1 = QHBoxLayout()
        for sz in [CheckboxSize.XS, CheckboxSize.SM, CheckboxSize.MD, CheckboxSize.LG, CheckboxSize.XL]:
            cb = Checkbox(text=sz.name, size=sz)
            lay1.addWidget(cb)
        lay1.addStretch()
        section1_layout.addLayout(lay1)
        scroll_layout.addWidget(section1_frame)

        # 2. 状态：选中 / 未选中 / 半选 indeterminate
        section2_frame, section2_layout = self._make_section("2. 状态 (State)")
        lay2 = QHBoxLayout()
        cb_unchecked = Checkbox(text="未选中", checked=False)
        cb_checked = Checkbox(text="选中", checked=True)
        cb_indet = Checkbox(text="半选(indeterminate)", toggle_indeterminate=True)
        cb_indet.setIndeterminate(True)
        lay2.addWidget(cb_unchecked)
        lay2.addWidget(cb_checked)
        lay2.addWidget(cb_indet)
        lay2.addStretch()
        section2_layout.addLayout(lay2)
        scroll_layout.addWidget(section2_frame)

        # 3. 文字位置 left_label
        section3_frame, section3_layout = self._make_section("3. 文字位置 (Left Label)")
        lay3 = QHBoxLayout()
        cb_normal = Checkbox(text="文字在右侧", left_label=False)
        cb_left = Checkbox(text="文字在左侧", left_label=True)
        lay3.addWidget(cb_normal)
        lay3.addWidget(cb_left)
        lay3.addStretch()
        section3_layout.addLayout(lay3)
        scroll_layout.addWidget(section3_frame)

        # 4. dense 紧凑模式 + 多色
        section4_frame, section4_layout = self._make_section("4. Dense紧凑模式 + 自定义颜色")
        lay4 = QHBoxLayout()
        cb_dense = Checkbox(text="dense", dense=True, color="#00BFA5")
        cb_color1 = Checkbox(text="Secondary", color="#90CAF9")
        cb_color2 = Checkbox(text="Warning", color="#FFC107")
        lay4.addWidget(cb_dense)
        lay4.addWidget(cb_color1)
        lay4.addWidget(cb_color2)
        lay4.addStretch()
        section4_layout.addLayout(lay4)
        scroll_layout.addWidget(section4_frame)

        # 5. 禁用态 disabled
        section5_frame, section5_layout = self._make_section("5. 禁用状态 Disabled")
        lay5 = QHBoxLayout()
        cb_dis_off = Checkbox(text="禁用-未选", disabled=True)
        cb_dis_on = Checkbox(text="禁用-选中", disabled=True, checked=True)
        cb_dis_indet = Checkbox(text="禁用-半选", disabled=True)
        cb_dis_indet.setIndeterminate(True)
        lay5.addWidget(cb_dis_off)
        lay5.addWidget(cb_dis_on)
        lay5.addWidget(cb_dis_indet)
        lay5.addStretch()
        section5_layout.addLayout(lay5)
        scroll_layout.addWidget(section5_frame)

        # 6. 三态循环 toggle_indeterminate
        section6_frame, section6_layout = self._make_section("6. 三态循环（toggle_indeterminate=True）")
        lay6 = QHBoxLayout()
        cb_tri = Checkbox(text="点击循环：未选→选中→半选", toggle_indeterminate=True)
        lay6.addWidget(cb_tri)
        lay6.addStretch()
        section6_layout.addLayout(lay6)
        scroll_layout.addWidget(section6_frame)

        # 7. 自定义图标分支（无资源先注释）
        section7_frame, section7_layout = self._make_section("7. 自定义图标（checked / unchecked / indeterminate icon）")
        lay7 = QHBoxLayout()
        # cb_icon = Checkbox(
        #     text="自定义图标",
        #     checked=True,
        #     checked_icon=":/icons/check",
        #     unchecked_icon=":/icons/close",
        #     indeterminate_icon=":/icons/minus"
        # )
        # lay7.addWidget(cb_icon)
        lay7.addStretch()
        section7_layout.addLayout(lay7)
        scroll_layout.addWidget(section7_frame)

        scroll_layout.addStretch()

    def _make_section(self, title: str):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        lab = QLabel(f"<b>{title}</b>")
        layout.addWidget(lab)
        # 返回 frame 和它内部的layout，外面往这个layout追加内容
        return frame, layout

    def _toggle_theme(self):
        if theme_manager.mode == ThemeMode.LIGHT:
            theme_manager.set_mode(ThemeMode.DARK)
        else:
            theme_manager.set_mode(ThemeMode.LIGHT)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from pathlib import Path
    # 自动把src加入路径，直接在examples目录运行也ok
    src_dir = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_dir))

    app = QApplication(sys.argv)
    theme_manager.set_mode(ThemeMode.LIGHT)
    w = CheckboxGallery()
    w.resize(1000, 700)
    w.show()
    sys.exit(app.exec())
