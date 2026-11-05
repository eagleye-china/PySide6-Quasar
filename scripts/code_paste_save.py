# scripts/code_paste_save.py
"""
剪贴板代码提取写入文件工具 (v2.2 终极体验版)
✅ 优化：按钮面板改为“右上角复选框 + 右下角按钮组”，符合鼠标操作习惯
✅ 修复：监听过于严格导致“复制无反应”的 Bug
✅ 优化：只要剪贴板内容变化，立刻同步到编辑器，体验如丝般顺滑
✅ 增强：防无限死循环、防覆盖提示，内置暗黑标题栏与 Ctrl+S 快捷键
"""
import ctypes
import sys
from pathlib import Path

from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTextEdit, QPushButton, QCheckBox, QSizePolicy, QStatusBar, QMessageBox
)


# ===================== 内置暗色标题栏 =====================
def enable_dark_title_bar(window):
    """Windows 系统专用的暗黑标题栏实现（免外部依赖）"""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(window.winId())
        for attr in (20, 19):
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
            )
            if res == 0:
                break
    except Exception:
        pass


class CodePasteSaver(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("剪贴板代码提取写入文件 (智能监听版)")
        self.resize(1100, 700)

        # 基础变量
        self._base_dir = Path(__file__).resolve().parent.parent
        self._target_abs_path: Path | None = None
        self._code_body = ""
        self._watch_enabled = True
        self._cb = QApplication.clipboard()

        self._setup_ui()
        self._setup_shortcuts()

        # 连接信号
        self._cb.dataChanged.connect(self._on_clipboard_changed)

        # 启动时初始化读取一次
        self.load_from_clipboard(silent=True)

        # 启用暗黑标题栏
        enable_dark_title_bar(self)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ========== 左侧文本编辑区 ==========
        self.txt_view = QTextEdit()
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.txt_view.setFont(font)
        self.txt_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.txt_view.setPlaceholderText("在此粘贴代码，第一行必须是：# src/pyside_quasar/xxx.py")
        # 编辑器内容改变时，禁用保存按钮
        self.txt_view.textChanged.connect(lambda: self.btn_save.setEnabled(False))
        main_layout.addWidget(self.txt_view, stretch=1)

        # ========== 右侧面板 ==========
        right_panel = QWidget()
        right_panel.setFixedWidth(200)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 1. 顶部：监听开关
        self.chk_watch = QCheckBox("🔁 智能监听剪贴板")
        self.chk_watch.setChecked(True)
        self.chk_watch.stateChanged.connect(self.toggle_watch)
        right_layout.addWidget(self.chk_watch)

        # 2. 中间：弹簧（把上面的留白撑开，把按钮挤到右下角）
        right_layout.addStretch()

        # 3. 底部：操作按钮组（从下往上的操作逻辑：清空 -> 保存 -> 解析 -> 读取）
        self.btn_clear = QPushButton("🗑️ 清空编辑器")
        self.btn_clear.clicked.connect(self.clear_all)
        right_layout.addWidget(self.btn_clear)

        self.btn_save = QPushButton("💾 写入文件 (Ctrl+S)")
        self.btn_save.setEnabled(False)
        # 给保存按钮加个高亮色，突出核心功能
        self.btn_save.setStyleSheet(
            "QPushButton:enabled { background-color: #0E639C; color: white; border: 1px solid #1177BB; } QPushButton:enabled:hover { background-color: #1177BB; }")
        self.btn_save.clicked.connect(self.do_save)
        right_layout.addWidget(self.btn_save)

        self.btn_parse = QPushButton("🔍 解析目标路径")
        self.btn_parse.clicked.connect(self.parse_content)
        right_layout.addWidget(self.btn_parse)

        self.btn_paste = QPushButton("📋 手动读取剪贴板")
        self.btn_paste.clicked.connect(self.load_from_clipboard)
        right_layout.addWidget(self.btn_paste)

        # 加一点底部边距，让按钮不要紧贴底边
        right_layout.addSpacing(10)

        main_layout.addWidget(right_panel)

        # ========== 状态栏 ==========
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪，第一行格式：# src/pyside_quasar/xxx.py")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.do_save)
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.parse_content)

    def toggle_watch(self, state):
        self._watch_enabled = bool(state)
        if self._watch_enabled:
            self.status_bar.showMessage("✅ 剪贴板监听已开启（复制任意文本将自动载入）")
        else:
            self.status_bar.showMessage("⏸ 监听已关闭，请手动点击读取")

    def _on_clipboard_changed(self):
        """只要有内容变化就同步，避免因格式不对而静默丢弃"""
        if not self._watch_enabled:
            return

        text = self._cb.text()
        if not text.strip():
            return

        # 防死循环：如果剪贴板内容和编辑器里的一模一样，说明是自己复制自己，忽略
        if text == self.txt_view.toPlainText():
            return

        self._apply_text(text, silent=True)

    def load_from_clipboard(self, silent=False):
        text = self._cb.text()
        if not text.strip():
            if not silent:
                self.status_bar.showMessage("⚠️ 剪贴板为空")
            return
        self._apply_text(text, silent)

    def _apply_text(self, text: str, silent: bool):
        self.txt_view.setPlainText(text)
        self._target_abs_path = None
        self._code_body = ""

        # 自动预判格式，给出提示
        first_line = text.splitlines()[0].strip() if text else ""
        if first_line.startswith("#") and "src/" in first_line:
            self.status_bar.showMessage("✅ 已载入剪贴板内容（格式合法，可解析保存）")
        else:
            self.status_bar.showMessage("⚠️ 已载入文本，但首行缺少 # src/ 格式，请手动补充")

    def parse_content(self):
        raw_text = self.txt_view.toPlainText()
        if not raw_text.strip():
            self.status_bar.showMessage("⚠️ 内容为空！")
            return

        lines = raw_text.splitlines()
        first_line = lines[0].strip()

        if not first_line.startswith("#"):
            self.status_bar.showMessage("❌ 解析失败：首行必须以 # 开头！")
            return

        file_path_str = first_line.lstrip("#").strip()
        if not file_path_str.startswith("src/"):
            self.status_bar.showMessage(f"❌ 路径必须以 src/ 开头，当前：{file_path_str}")
            return

        # 计算绝对路径并做安全校验
        temp_path = (self._base_dir / file_path_str).resolve()

        if not temp_path.is_relative_to(self._base_dir):
            self.status_bar.showMessage("❌ 安全拦截：路径超出项目根目录！")
            return

        self._target_abs_path = temp_path
        self._code_body = raw_text
        self.btn_save.setEnabled(True)
        self.status_bar.showMessage(f"✅ 解析成功，目标：{self._target_abs_path}")

    def do_save(self):
        if self._target_abs_path is None or not self._code_body:
            self.status_bar.showMessage("⚠️ 请先点击【解析】或按 Ctrl+Enter！")
            return

        confirm = QMessageBox.question(
            self, "确认写入",
            f"即将覆盖文件：\n{self._target_abs_path}\n\n是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            self.status_bar.showMessage("ℹ️ 已取消写入")
            return

        try:
            self._target_abs_path.parent.mkdir(parents=True, exist_ok=True)
            final_content = self._code_body.rstrip("\n") + "\n"
            self._target_abs_path.write_text(final_content, encoding="utf-8")

            self.status_bar.showMessage(f"✅ 写入成功：{self._target_abs_path}")
            QMessageBox.information(self, "成功", f"文件已成功写入：\n{self._target_abs_path}")
            # 写入成功后，再次禁用保存按钮，防止重复覆盖
            self.btn_save.setEnabled(False)
        except Exception as e:
            self.status_bar.showMessage("❌ 写入失败，请检查文件是否被占用！")
            QMessageBox.critical(self, "错误", f"写入时发生异常：\n{str(e)}")

    def clear_all(self):
        self.txt_view.clear()
        self._code_body = ""
        self._target_abs_path = None
        self.btn_save.setEnabled(False)
        self.status_bar.showMessage("🗑️ 已清空，等待新代码")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dark_style = """
    QMainWindow, QWidget {
        background-color: #1E1E1E;
        color: #D4D4D4;
    }
    QTextEdit {
        background-color: #252526;
        color: #D4D4D4;
        border: 1px solid #3C3C3C;
        border-radius: 4px;
        selection-background-color: #264F78;
    }
    QPushButton {
        background-color: #323233;
        color: #E0E0E0;
        border: 1px solid #444444;
        border-radius: 4px;
        padding: 8px;
    }
    QPushButton:hover { background-color: #3E3E40; }
    QPushButton:pressed { background-color: #2A2A2B; }
    QPushButton:disabled { background-color: #2A2A2B; color: #666666; border: 1px solid #333333; }
    QCheckBox { color: #D4D4D4; padding: 4px; }
    QStatusBar { background-color: #2D2D30; color: #9CDCFE; font-weight: bold; }
    """
    app.setStyleSheet(dark_style)

    win = CodePasteSaver()
    win.show()
    sys.exit(app.exec())
