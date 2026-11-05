# scripts/gen_tree.py
import ast
import fnmatch
import shutil
import sys
from pathlib import Path
from typing import Set, List, Tuple

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QCheckBox, QLabel, QFileDialog,
    QRadioButton, QButtonGroup, QMessageBox
)


class TreeGenerator:
    def __init__(self, ignore_dirs=None, ignore_files=None):
        if ignore_dirs is None:
            ignore_dirs = {
                ".git", "__pycache__", "venv", ".venv",
                "build", "dist", ".pytest_cache", ".mypy_cache",
                ".idea", ".vscode"
            }
        if ignore_files is None:
            # ✅ 使用通配符支持 *.pyc, *.pyo 等
            ignore_files = {".DS_Store", "Thumbs.db", "*.pyc", "*.pyo", "*.bak"}
        self.ignore_dirs = set(ignore_dirs)
        self.ignore_files = set(ignore_files)

    def _is_ignored_file(self, name: str) -> bool:
        """使用 fnmatch 支持通配符匹配"""
        return any(fnmatch.fnmatch(name, pattern) for pattern in self.ignore_files)

    def generate_tree(self, root_path: str, show_files: bool = True, show_hidden: bool = False) -> str:
        root = Path(root_path)
        lines = [root.name + "/"]
        self._walk(root, "", lines, show_files, show_hidden)
        return "\n".join(lines)

    def _walk(self, current: Path, prefix: str, lines: list, show_files: bool, show_hidden: bool):
        try:
            entries = list(current.iterdir())
        except PermissionError:
            return

        entries.sort(key=lambda _p: (not _p.is_dir(), _p.name.lower()))
        filtered = []

        for p in entries:
            name = p.name
            if not show_hidden and name.startswith("."):
                continue
            if p.is_dir() and name in self.ignore_dirs:
                continue
            if p.is_file() and self._is_ignored_file(name):
                continue
            if p.is_file() and not show_files:
                continue
            filtered.append(p)

        count = len(filtered)
        for idx, path in enumerate(filtered):
            is_last = (idx == count - 1)
            connector = "└── " if is_last else "├── "
            name = path.name
            if path.is_dir():
                name += "/"
            lines.append(prefix + connector + name)

            if path.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                self._walk(path, new_prefix, lines, show_files, show_hidden)


class InitExporter:
    """扫描子包，收集类、常量，生成子包 __init__.py，【不会触碰顶层 pyside_quasar/__init__.py】"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_root = self.project_root / "src" / "pyside_quasar"
        self.ignore_dirs = {"__pycache__", ".git", "venv", ".venv", "build", "dist"}
        self.skip_packages: Set[str] = set()

    @staticmethod
    def scan_package(pkg_dir: Path) -> Tuple[List[str], List[str]]:
        """扫描单个子包目录，返回 (import_lines, all_list)，自动去重并合并导入"""
        import_map = {}  # {mod_name: [names]}
        all_list = []
        seen_names = set()

        if not (pkg_dir / "__init__.py").exists():
            return [], []

        py_files = list(pkg_dir.glob("*.py"))
        for f in py_files:
            if f.name == "__init__.py" or f.name.endswith(".bak"):
                continue

            mod_name = f.stem
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    source = fp.read()
                    tree = ast.parse(source, filename=str(f))
            except Exception:  # noqa
                continue

            if not isinstance(tree, ast.Module):
                continue

            # ✅ 核心优化：通过注释识别需要忽略的内部类
            for node in tree.body:
                # 判断是否为需要导出的类
                if isinstance(node, ast.ClassDef):
                    cls_name = node.name
                    if cls_name.startswith("_") or cls_name in seen_names:
                        continue

                    # 检查类定义上方是否有 # export-ignore 注释
                    if cls_name in source and "# export-ignore" in \
                       source.split(f"class {cls_name}")[0].splitlines()[-1:][0] if source.split(
                        f"class {cls_name}") else "":
                        # 这个判断逻辑稍微有点简陋，更好的做法是直接取上一行
                        pass

                    # 严谨地获取注释的方法：
                    # 简单起见，我们检查类名上方最近的一行是否是 "# export-ignore"
                    lines = source.splitlines()
                    if node.lineno > 1:
                        prev_line = lines[node.lineno - 2].strip()
                        if prev_line == "# export-ignore":
                            continue

                    seen_names.add(cls_name)
                    import_map.setdefault(mod_name, []).append(cls_name)
                    all_list.append(cls_name)

                # 判断是否为需要导出的常量
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        targets = target.elts if isinstance(target, (ast.Tuple, ast.List)) else [target]
                        for t in targets:
                            if isinstance(t, ast.Name):
                                var_name = t.id
                                if (var_name.startswith("_") or
                                        not var_name.isupper() or
                                        var_name in seen_names):
                                    continue
                                seen_names.add(var_name)
                                import_map.setdefault(mod_name, []).append(var_name)
                                all_list.append(var_name)

        # ✅ 核心优化：对导入的 names 和 __all__ 进行字母排序
        import_lines = []
        for mod_name, names in import_map.items():
            names.sort()
            if names:
                import_lines.append(f"from .{mod_name} import {', '.join(names)}")

        # 对模块的导入顺序也排个序
        import_lines.sort()
        all_list.sort()

        return import_lines, all_list

    def scan_all_packages(self) -> List[Tuple[Path, List[str], List[str]]]:
        """只遍历 src/pyside_quasar 的**直接子目录**，递归扫描子包"""
        result = []
        if not self.src_root.exists():
            return result

        for subdir in self.src_root.iterdir():
            if not subdir.is_dir() or subdir.name in self.ignore_dirs or subdir.name in self.skip_packages:
                continue

            for pkg_dir in subdir.rglob("*"):
                if not pkg_dir.is_dir() or pkg_dir.name in self.ignore_dirs:
                    continue
                if (pkg_dir / "__init__.py").exists():
                    imp, alls = self.scan_package(pkg_dir)
                    result.append((pkg_dir, imp, alls))
        return result

    def generate_preview_text(self) -> str:
        items = self.scan_all_packages()
        out = []
        for pkg_path, imp_lines, all_list in items:
            rel_pkg = pkg_path.relative_to(self.project_root)
            out.append(f"# ===== Package: {rel_pkg} =====")
            if not imp_lines:
                out.append("# 无导出类/常量\n")
                continue
            out.extend(imp_lines)
            all_str = ", ".join(f'"{x}"' for x in all_list)
            out.append(f"__all__ = [{all_str}]")
            out.append("")
        return "\n".join(out)

    def batch_write_init(self) -> str:
        """批量写入子包 __init__.py，备份；异常时回滚，无变化则跳过"""
        items = self.scan_all_packages()
        log = []
        rollback_list = []

        try:
            for pkg_path, imp_lines, all_list in items:
                init_file = pkg_path / "__init__.py"
                bak_file = pkg_path / "__init__.py.bak"

                if not imp_lines:
                    log.append(f"[SKIP] {init_file.relative_to(self.project_root)}: 没有导出项")
                    continue

                # 组装新内容
                content = "# Auto generated by gen_tree.py\n"
                content += "# Warning: auto-overwrite, backup saved to __init__.py.bak\n"
                content += "# 仅子包自动生成，顶层 pyside_quasar/__init__.py 手动维护\n\n"
                content += "\n".join(imp_lines) + "\n\n"
                all_str = ", ".join(f'"{x}"' for x in all_list)
                content += f"__all__ = [{all_str}]\n"

                # ✅ 优化：如果内容无变化，直接跳过不生成备份
                try:
                    with open(init_file, "r", encoding="utf-8") as fp:
                        old_content = fp.read()
                    if old_content == content:
                        log.append(f"[SKIP] {init_file.relative_to(self.project_root)}: 内容无变化")
                        continue
                except Exception:  # noqa
                    pass

                # 备份
                shutil.copy2(init_file, bak_file)
                rollback_list.append((init_file, bak_file))

                # 写入
                with open(init_file, "w", encoding="utf-8") as fp:
                    fp.write(content)
                log.append(f"[WRITE] {init_file.relative_to(self.project_root)}")

        except Exception as e:
            log.append(f"[ERROR] 写入失败: {str(e)}")
            log.append("[ROLLBACK] 正在恢复备份文件 ...")
            for init_file, bak_file in rollback_list:
                if bak_file.exists():
                    shutil.copy2(bak_file, init_file)
                    log.append(f"[RESTORE] {init_file.relative_to(self.project_root)}")
            raise
        return "\n".join(log)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("pyside-quasar - 项目脚手架辅助工具")
        self.resize(1000, 760)

        self.script_file = Path(__file__).resolve()
        self.project_root = self.script_file.parent.parent
        self.gen_tree = TreeGenerator()
        self.gen_init = InitExporter(self.project_root)

        self._setup_ui()
        self.refresh_view()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- 顶部：目录提示 ---
        tip_layout = QHBoxLayout()
        lbl_path = QLabel(f"<b>项目根目录：</b>{self.project_root}")
        tip_layout.addWidget(lbl_path)
        tip_layout.addStretch()
        layout.addLayout(tip_layout)

        # --- 工具栏：模式切换与选项 ---
        mode_layout = QHBoxLayout()
        self.radio_tree = QRadioButton("目录树")
        self.radio_init = QRadioButton("自动生成 __init__.py 预览")
        self.radio_tree.setChecked(True)

        self.btn_group_mode = QButtonGroup(self)
        self.btn_group_mode.addButton(self.radio_tree)
        self.btn_group_mode.addButton(self.radio_init)
        self.btn_group_mode.buttonClicked.connect(self.refresh_view)

        mode_layout.addWidget(self.radio_tree)
        mode_layout.addWidget(self.radio_init)
        mode_layout.addSpacing(20)

        self.chk_show_files = QCheckBox("显示文件")
        self.chk_show_files.setChecked(True)
        self.chk_hidden = QCheckBox("显示隐藏项")
        self.chk_show_files.stateChanged.connect(self.refresh_view)
        self.chk_hidden.stateChanged.connect(self.refresh_view)

        mode_layout.addWidget(self.chk_show_files)
        mode_layout.addWidget(self.chk_hidden)
        mode_layout.addStretch()

        btn_refresh = QPushButton("刷新")
        btn_refresh.setFixedWidth(80)
        btn_refresh.clicked.connect(self.refresh_view)
        mode_layout.addWidget(btn_refresh)
        layout.addLayout(mode_layout)

        # --- 中间：预览框 ---
        self.txt_preview = QTextEdit()
        self.txt_preview.setPlaceholderText("预览内容...")
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.txt_preview.setFont(font)
        self.txt_preview.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.txt_preview)

        # --- 底部：操作按钮 ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_copy = QPushButton("复制到剪贴板")
        btn_copy.clicked.connect(self.copy_clipboard)

        btn_save = QPushButton("保存预览")
        btn_save.clicked.connect(self.save_to_txt)

        btn_apply_init = QPushButton("⚡ 批量写入所有子包 __init__.py")
        btn_apply_init.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #106EBE; }
            QPushButton:pressed { background-color: #005A9E; }
        """)
        btn_apply_init.clicked.connect(self.apply_init_all)

        btn_layout.addWidget(btn_copy)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_apply_init)
        layout.addLayout(btn_layout)

    def refresh_view(self):
        if not self.project_root.is_dir():
            self.txt_preview.setPlainText("❌ 未找到项目根目录，请确认脚本放在 scripts/ 目录下！")
            return

        if self.radio_tree.isChecked():
            show_files = self.chk_show_files.isChecked()
            show_hidden = self.chk_hidden.isChecked()
            tree_text = self.gen_tree.generate_tree(str(self.project_root), show_files, show_hidden)
            self.txt_preview.setPlainText(tree_text)
        else:
            preview_text = self.gen_init.generate_preview_text()
            self.txt_preview.setPlainText(preview_text)

    def copy_clipboard(self):
        text = self.txt_preview.toPlainText()
        if text.strip():
            QApplication.clipboard().setText(text)
            # 可选：用 QToolTip 或在状态栏提示

    def save_to_txt(self):
        content = self.txt_preview.toPlainText()
        if not content.strip():
            return
        default_save = str(self.project_root / "preview.txt")
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存预览", default_save, "Text Files (*.txt)"
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

    def apply_init_all(self):
        # ✅ 遵循 Qt6 强类型枚举规范
        ret = QMessageBox.question(
            self, "确认写入",
            "⚠️ 将会批量覆盖 src/pyside_quasar 下【所有子包】的 __init__.py\n"
            "✅ 顶层 pyside_quasar/__init__.py 不会被触碰\n"
            "原文件自动备份为 __init__.py.bak\n"
            "（内容无变化的包将自动跳过）\n\n确定继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # 默认选中 No 防误触
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        try:
            log_text = self.gen_init.batch_write_init()
            if not log_text.strip():
                log_text = "所有包均无变化，无需写入。"
            QMessageBox.information(self, "执行完成", log_text)
        except Exception as e:
            QMessageBox.critical(self, "写入失败", f"任务异常，已自动回滚备份：\n{str(e)}")
        self.refresh_view()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
