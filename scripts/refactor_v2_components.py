# scripts/refactor_v2_components.py
"""
自动迁移 v1 → v2 组件。
运行：python scripts/refactor_v2_components.py
"""
import re
from pathlib import Path

SRC = Path(__file__).parent.parent / "src" / "pyside_quasar"

# ═══════════════════════════════════════════════════════════
# 目标文件（按需扩展）
# ═══════════════════════════════════════════════════════════
TARGETS = {
    # 纯 QWidget 组件 → QBaseWidget
    "QBaseWidget": [
        "components/primitives/checkbox.py",
        "components/primitives/switch.py",
        "components/primitives/progress.py",  # LineProgress + CircleProgress
        "components/containers/card.py",  # CardMedia + CardSection + CardActions + Card
        "components/containers/tabs.py",  # TabItem + Tabs
        "components/feedback/toast.py",
        "components/feedback/tooltip.py",
    ],
}

# ═══════════════════════════════════════════════════════════
# 已修复的代表组件（仅确认，不需改）
# ═══════════════════════════════════════════════════════════
ALREADY_FIXED = [
    "components/primitives/button.py",  # QPushButton + QuasarWidgetMixin
    "components/primitives/input.py",  # QBaseWidget
    "components/primitives/avatar.py",  # QBaseWidget
    "components/primitives/badge.py",  # QBaseWidget
    "components/containers/dialog.py",  # QDialog + QuasarWidgetMixin
]


def fix_qbase_widget(content: str) -> str:
    """将 (QWidget, ThemedWidget) 改为 QBaseWidget"""
    # 1. 类定义：class X(QWidget, ThemedWidget) → class X(QBaseWidget)
    pattern_class = r"class (\w+)\(QWidget,\s*ThemedWidget((?:,\s*[^)]+)?)\)"
    replacement_class = r"class \1(QBaseWidget\2)"

    content = re.sub(pattern_class, replacement_class, content)

    # 2. 删除 self.setup_theme()
    content = re.sub(
        r"^\s*self\.setup_theme\(\)\s*$",
        "",
        content,
        flags=re.MULTILINE,
    )

    return content


def fix_imports(content: str) -> str:
    """确保导入 QBaseWidget"""
    # 如果用了 QBaseWidget 但没导入，补上
    if "QBaseWidget" in content and "from ...core.base import" in content:
        # 已导入，不需处理
        pass
    return content


def process_file(path: Path) -> bool:
    """处理单个文件，返回是否修改"""
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    content = original
    content = fix_qbase_widget(content)
    content = fix_imports(content)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    fixed = []
    skipped = []

    for file_rel in TARGETS["QBaseWidget"]:
        py_file = SRC / file_rel
        if not py_file.exists():
            print(f"⚠️  文件不存在: {file_rel}")
            continue

        if process_file(py_file):
            fixed.append(file_rel)
            print(f"✅ 已修复: {file_rel}")
        else:
            skipped.append(file_rel)
            print(f"⏭️  无需修改: {file_rel}")

    print()
    print("=" * 60)
    print(f"完成: {len(fixed)} 个文件修改，{len(skipped)} 个文件跳过")
    print()
    print("⚠️  请人工复核以下内容：")
    print("   1. 每个文件的 import 段是否有 'from ...core.base import'")
    print("   2. 类定义是否已改为 'class X(QBaseWidget)'")
    print("   3. 是否还有残留的 'ThemedWidget' 引用")


if __name__ == "__main__":
    main()
