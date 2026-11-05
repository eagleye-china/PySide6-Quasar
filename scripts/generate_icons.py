# scripts/generate_icons.py
"""
批量将 SVG 图标转换为多尺寸 PNG 和 ICO。
依赖：PySide6（已安装）

用法：
    python scripts/generate_icons.py
"""

import sys
from pathlib import Path

from PySide6.QtCore import QSize
from PySide6.QtGui import QImage, QPainter, QGuiApplication, QIcon
from PySide6.QtSvg import QSvgRenderer

# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

ROOT = Path(__file__).parent.parent
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ASSETS_DIR / "icons"

# 需要的 PNG 尺寸（覆盖 Windows / macOS / Linux 常用尺寸）
SIZES = [16, 24, 32, 48, 64, 128, 256, 512, 1024]

# 需要生成的变体（SVG 文件名 → 输出前缀）
VARIANTS = {
    "pq-icon.svg": "pq",  # 主版本
    "pq-icon-transparent.svg": "pq-transparent",
    "pq-icon-dark.svg": "pq-dark",
}


# ═══════════════════════════════════════════════════════════════
# 核心：SVG → PNG
# ═══════════════════════════════════════════════════════════════

def svg_to_png(svg_path: Path, png_path: Path, size: int) -> bool:
    """将 SVG 渲染为指定尺寸的 PNG"""
    try:
        renderer = QSvgRenderer(str(svg_path))
        if not renderer.isValid():
            print(f"  ❌ SVG 无效: {svg_path}")
            return False

        image = QImage(QSize(size, size), QImage.Format.Format_ARGB32)
        image.fill(0x00000000)  # 透明背景

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        renderer.render(painter)
        painter.end()

        png_path.parent.mkdir(parents=True, exist_ok=True)
        return image.save(str(png_path), "PNG")
    except Exception as e:
        print(f"  ❌ 渲染失败: {e}")
        return False


def generate_ico(png_paths: list[Path], ico_path: Path) -> bool:
    """将多个 PNG 合并为 .ico 文件"""
    try:
        icon = QIcon()
        for png in png_paths:
            if png.exists():
                icon.addFile(str(png))
        # QIcon 不支持直接保存 .ico，用 PIL 或外部工具，这里用 QImage 简单方式
        # 简化方案：只保存最大的 PNG 作为 .ico 占位
        if png_paths:
            largest = max(png_paths, key=lambda p: int(p.stem.split("_")[-1]))
            from PySide6.QtGui import QImage
            img = QImage(str(largest))
            img.save(str(ico_path), "ICO")
            return True
        return False
    except Exception as e:
        print(f"  ❌ ICO 生成失败: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    app = QGuiApplication(sys.argv)

    if not ASSETS_DIR.exists():
        print(f"❌ 资源目录不存在: {ASSETS_DIR}")
        return

    print(f"📂 资源目录: {ASSETS_DIR}")
    print(f"📂 输出目录: {OUTPUT_DIR}")
    print()

    total = 0
    for svg_name, prefix in VARIANTS.items():
        svg_path = ASSETS_DIR / svg_name
        if not svg_path.exists():
            print(f"⚠️  跳过（不存在）: {svg_name}")
            continue

        print(f"🎨 处理: {svg_name}")

        generated_pngs = []
        for size in SIZES:
            png_path = OUTPUT_DIR / f"{prefix}_{size}.png"
            if svg_to_png(svg_path, png_path, size):
                print(f"  ✅ {png_path.name}")
                generated_pngs.append(png_path)
                total += 1

        # 生成 ICO（仅对主版本）
        if prefix == "pq":
            ico_path = OUTPUT_DIR / "pq.ico"
            if generate_ico(generated_pngs, ico_path):
                print(f"  ✅ {ico_path.name}")

        print()

    print("=" * 60)
    print(f"🎉 完成！共生成 {total} 个 PNG 文件")
    print(f"   输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
