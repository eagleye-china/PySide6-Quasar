# examples/dialog_gallery.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt

from pyside_quasar.components.containers.dialog import Dialog, DialogPosition
from pyside_quasar import Checkbox
from pyside_quasar.core.theme import theme_manager, ThemeMode


class DialogGallery(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyside-quasar - Dialog Gallery")
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # 标题行
        title_row = QHBoxLayout()
        title = QLabel("<h2>Dialog 对话框组件演示</h2>")
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

        # 1. 基础居中对话框
        s1_frame, s1_layout = self._make_section("1. 基础居中对话框（标准）")
        lay1 = QHBoxLayout()
        btn_normal = QPushButton("打开标准Dialog")
        btn_normal.clicked.connect(self._open_dialog_normal)
        lay1.addWidget(btn_normal)
        lay1.addStretch()
        s1_layout.addLayout(lay1)
        scroll_layout.addWidget(s1_frame)

        # 2. 不同弹出位置
        s2_frame, s2_layout = self._make_section("2. 弹出位置：TOP / BOTTOM / LEFT / RIGHT")
        lay2 = QHBoxLayout()
        btn_top = QPushButton("TOP")
        btn_top.clicked.connect(lambda: self._open_dialog_pos(DialogPosition.TOP))
        btn_bottom = QPushButton("BOTTOM")
        btn_bottom.clicked.connect(lambda: self._open_dialog_pos(DialogPosition.BOTTOM))
        btn_left = QPushButton("LEFT")
        btn_left.clicked.connect(lambda: self._open_dialog_pos(DialogPosition.LEFT))
        btn_right = QPushButton("RIGHT")
        btn_right.clicked.connect(lambda: self._open_dialog_pos(DialogPosition.RIGHT))
        lay2.addWidget(btn_top)
        lay2.addWidget(btn_bottom)
        lay2.addWidget(btn_left)
        lay2.addWidget(btn_right)
        lay2.addStretch()
        s2_layout.addLayout(lay2)
        scroll_layout.addWidget(s2_frame)

        # 3. Persistent 持久弹窗（ESC、遮罩都不能关）
        s3_frame, s3_layout = self._make_section("3. Persistent 持久弹窗（只能点关闭按钮）")
        lay3 = QHBoxLayout()
        btn_persist = QPushButton("打开持久Dialog")
        btn_persist.clicked.connect(self._open_dialog_persistent)
        lay3.addWidget(btn_persist)
        lay3.addStretch()
        s3_layout.addLayout(lay3)
        scroll_layout.addWidget(s3_frame)

        # 4. Maximized 最大化弹窗
        s4_frame, s4_layout = self._make_section("4. Maximized 最大化弹窗")
        lay4 = QHBoxLayout()
        btn_max = QPushButton("打开最大化Dialog")
        btn_max.clicked.connect(self._open_dialog_max)
        lay4.addWidget(btn_max)
        lay4.addStretch()
        s4_layout.addLayout(lay4)
        scroll_layout.addWidget(s4_frame)

        # 5. 自定义样式（背景色、圆角）
        s5_frame, s5_layout = self._make_section("5. 自定义背景色 + 大圆角")
        lay5 = QHBoxLayout()
        btn_custom = QPushButton("打开自定义Dialog")
        btn_custom.clicked.connect(self._open_dialog_custom)
        lay5.addWidget(btn_custom)
        lay5.addStretch()
        s5_layout.addLayout(lay5)
        scroll_layout.addWidget(s5_frame)

        scroll_layout.addStretch()

    def _make_section(self, title: str):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        lab = QLabel(f"<b>{title}</b>")
        layout.addWidget(lab)
        return frame, layout

    def _toggle_theme(self):
        if theme_manager.mode == ThemeMode.LIGHT:
            theme_manager.set_mode(ThemeMode.DARK)
        else:
            theme_manager.set_mode(ThemeMode.LIGHT)

    def _open_dialog_normal(self):
        dlg = Dialog(title="标准对话框", parent=self)
        dlg.add_widget(QLabel("这是一个基础居中模态对话框，可以点击遮罩或者ESC关闭。"))
        dlg.add_widget(Checkbox(text="测试内部Checkbox组件", checked=True))
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(dlg.accept)
        dlg.add_action(btn_ok)
        dlg.exec()

    def _open_dialog_pos(self, pos: DialogPosition):
        dlg = Dialog(title=f"位置：{pos.name}", parent=self, position=pos, min_width=320, max_width=400)
        dlg.add_widget(QLabel(f"当前弹出位置：<b>{pos.name}</b>"))
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dlg.reject)
        dlg.add_action(btn_close)
        dlg.exec()

    def _open_dialog_persistent(self):
        dlg = Dialog(title="Persistent 持久弹窗", parent=self, persistent=True)
        dlg.add_widget(QLabel("⚠️ 无法通过ESC、点击背景遮罩关闭，只能点击右上角 × 关闭。"))
        dlg.exec()

    def _open_dialog_max(self):
        dlg = Dialog(title="最大化对话框", parent=self, maximized=True)
        dlg.add_widget(QLabel("Maximized 全屏弹窗，铺满屏幕，无边距。"))
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dlg.reject)
        dlg.add_action(btn_close)
        dlg.exec()

    def _open_dialog_custom(self):
        dlg = Dialog(title="自定义样式", parent=self, bg_color="#E3F2FD", radius=16)
        dlg.add_widget(QLabel("自定义背景色、圆角大小，明暗主题依然可以切换。"))
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(dlg.reject)
        dlg.add_action(btn_close)
        dlg.exec()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from pathlib import Path

    src_dir = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_dir))

    app = QApplication(sys.argv)
    theme_manager.set_mode(ThemeMode.LIGHT)
    w = DialogGallery()
    w.resize(1000, 700)
    w.show()
    sys.exit(app.exec())
