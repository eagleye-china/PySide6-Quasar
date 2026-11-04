# scripts/fix_imports_v2.py
"""
批量修复 v1 → v2 迁移后的相对导入路径。
运行：python scripts/fix_imports_v2.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src" / "pyside6_quasar"

# ═══════════════════════════════════════════════════════════
# 路径替换规则（按顺序执行，防止替换冲突）
# ═══════════════════════════════════════════════════════════
RULES = [
    # ---------- theme ----------
    (r"from \.\.theme import theme_manager, Color, ThemeMode, get_contrast_color",
     "from ...core.theme import theme_manager, ThemeMode\nfrom ...core.theme.palette import Color\nfrom ...core.theme.contrast import get_contrast_color"),
    (r"from \.\.theme import theme_manager, Color, ThemeMode",
     "from ...core.theme import theme_manager, ThemeMode\nfrom ...core.theme.palette import Color"),
    (r"from \.\.theme import theme_manager, Color, get_contrast_color",
     "from ...core.theme import theme_manager\nfrom ...core.theme.palette import Color\nfrom ...core.theme.contrast import get_contrast_color"),
    (r"from \.\.theme import (.*)",
     r"from ...core.theme import \1"),

    # ---------- base ----------
    (r"from \.\.utils\.base import ThemedWidget",
     "from ...core.base import QBaseWidget, QuasarWidgetMixin"),
    (r"from \.\.utils\.base import (.*)",
     r"from ...core.base import \1"),

    # ---------- mixin ----------
    (r"from \.\.utils\.mixin import BadgeMixin",
     "from ...core.mixins.badge_mixin import BadgeMixin"),
    (r"from \.\.utils\.mixin import (.*)",
     r"from ...core.mixins import \1"),

    # ---------- 旧组件路径 v1 平铺 → v2 分层 ----------
    (r"from \.\.components import (.*)",
     r"from .. import \1"),
    (r"from \.\.components\.primitives import (.*)",
     r"from ..primitives import \1"),

    # ---------- 内部同包引用 ----------
    (r"from \.theme import",
     "from ...core.theme import"),
    (r"from \.base import",
     "from ...core.base import"),
]


def fix_file(path: Path) -> bool:
    """返回 True 表示文件被修改"""
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False

    content = original
    for pattern, replacement in RULES:
        content = re.sub(pattern, replacement, content)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main():
    if not SRC.exists():
        print(f"❌ 源码目录不存在: {SRC}")
        return

    fixed_files = []
    for py_file in SRC.rglob("*.py"):
        if fix_file(py_file):
            fixed_files.append(py_file.relative_to(ROOT))
            print(f"✅ 已修复: {py_file.relative_to(ROOT)}")

    print()
    if fixed_files:
        print(f"🎉 共修复 {len(fixed_files)} 个文件")
    else:
        print("✨ 所有文件导入路径已正确，无需修复")


if __name__ == "__main__":
    main()
